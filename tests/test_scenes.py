import pytest
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.scenes import SceneError, SocialSceneService
from vivarium.traversal import TraversalEngine

@pytest.fixture
def setup():
 c=connect_database(':memory:');ensure_schema(c);wid=IntegrationWorldService(c).create_initial_world()['id'];yield c,wid,SocialSceneService(c);c.close()

def test_scene_requires_colocation_and_keeps_speech_as_noncanonical_expression(setup):
 c,w,s=setup
 TraversalEngine(c).traverse_character(w,'sophie','porte_entree','salon')
 with pytest.raises(SceneError) as err:s.open(w,'arrival_chat',['sophie','erika'])
 assert err.value.code=='scene_participants_not_colocated'
 TraversalEngine(c).traverse_character(w,'erika','porte_entree','salon')
 scene=s.open(w,'arrival_chat',['sophie','erika']);assert scene['status']=='active'
 act=s.speak(w,'arrival_chat','hello','sophie',act_kind='greet',content='Salut.',recipient_key='erika',payload={'tone':'neutral'})
 assert act['content']=='Salut.' and c.execute('SELECT COUNT(*) FROM social_speech_act').fetchone()[0]==1
 assert s.speak(w,'arrival_chat','hello','sophie',act_kind='greet',content='différent',recipient_key='erika')==act
 assert s.close(w,'arrival_chat',reason='goodbye')['status']=='closed'
 with pytest.raises(SceneError):s.speak(w,'arrival_chat','late','sophie',act_kind='inform',content='Non.')

def test_restart_interrupts_scene_without_inventing_next_speech(setup):
 c,w,s=setup
 TraversalEngine(c).traverse_character(w,'sophie','porte_entree','salon');TraversalEngine(c).traverse_character(w,'erika','porte_entree','salon')
 s.open(w,'interrupted',['sophie','erika']);s.speak(w,'interrupted','ask','sophie',act_kind='ask',content='Ça va?')
 assert s.interrupt_active(w)==1
 sheet=s.sheet(w,'interrupted');assert sheet['status']=='interrupted' and len(sheet['acts'])==1 and sheet['close_reason']=='service_restart'


def test_scene_refuses_new_speech_when_a_participant_left_the_scene_location(setup):
 c,w,s=setup
 TraversalEngine(c).traverse_character(w,'sophie','porte_entree','salon');TraversalEngine(c).traverse_character(w,'erika','porte_entree','salon')
 s.open(w,'left_scene',['sophie','erika'])
 TraversalEngine(c).traverse_character(w,'erika','porte_entree','entree_exterieure')
 with pytest.raises(SceneError) as err:s.speak(w,'left_scene','late','sophie',act_kind='inform',content='Tu es partie.')
 assert err.value.code=='scene_participants_not_colocated'
