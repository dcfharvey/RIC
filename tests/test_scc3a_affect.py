from datetime import datetime, timezone
import pytest

from vivarium.affect import AffectService
from vivarium.cognition_policy import CognitionCallLimits
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.scenes import SocialSceneService
from vivarium.scc1c import FixedAdmissionPolicy
from vivarium.scc3a_affect import SCC3AAffectError
from vivarium.scc3a_affect_provider import DeterministicSCC3AAffectProvider, SCC3AAffectContextBuilder, SCC3AAffectLLMService
from vivarium.social_appraisal_provider import DeterministicAppraisalProvider
from vivarium.social_cognition_runtime import LiveSocialCognitionService
from vivarium.social_interpretation_provider import DeterministicInterpretationProvider
from vivarium.util import Clock, to_iso

class FakeClock(Clock):
    def __init__(self): self.current=datetime(2026,8,10,12,tzinfo=timezone.utc)
    def now(self): return self.current
    def now_iso(self): return to_iso(self.current)

@pytest.fixture
def setup():
    c=connect_database(':memory:'); ensure_schema(c); clock=FakeClock(); w=IntegrationWorldService(c,clock=clock).create_initial_world()['id']; SocialSceneService(c,clock=clock).open(w,'scc3a_scene',('sophie','erika','luna')); SocialSceneService(c,clock=clock).speak(w,'scc3a_scene','speech_1','sophie',act_kind='inform',content='Sophie partage une parole.',recipient_key='erika'); yield c,w,clock; c.close()

def _source(setup, appraisal):
    c,w,clock=setup; ip=DeterministicInterpretationProvider({'schema_version':2,'understanding_status':'clear','meaning_hypotheses':['Lecture subjective']},model_id='fake-qwen3-14b'); ap=DeterministicAppraisalProvider({'schema_version':1,'appraisal_status':'relevant','qualitative_meaning':'defavorable','importance':'high','bases':['interpretation:primary'],'candidates':[{'candidate_key':appraisal,'domain':'affect','basis_refs':['interpretation:primary'],'justification':'Cet épisode peut être examiné par le domaine affectif.'}]})
    LiveSocialCognitionService(c,ip,clock=clock,admission_policy=FixedAdmissionPolicy('selected'),appraisal_provider=ap).process_speech(w,'scc3a_scene','speech_1',CognitionCallLimits(0,3600,30)); return c,w,clock

def _run(setup, proposal, owner='erika', candidate='affect_case'):
    c,w,clock=_source(setup,candidate); provider=DeterministicSCC3AAffectProvider(proposal,model_id='fake-qwen3-14b'); return c,w,clock,SCC3AAffectLLMService(c,provider,clock=clock).run(w,owner,candidate,provider_turn_id='scc3a_test_1')

def test_no_change_is_valid_and_does_not_create_episode_or_mood(setup):
    c,w,clock,result=_run(setup,{'decision':'no_change','family':None,'qualitative_intensity':None,'target_ref':None,'support_refs':[]})
    assert result['decision']=='no_change'; assert c.execute("SELECT COUNT(*) FROM emotion_episode").fetchone()[0]==0; assert c.execute("SELECT COUNT(*) FROM mood_state").fetchone()[0]==0
    assert c.execute("SELECT COUNT(*) FROM scc3a_decision WHERE decision='no_change'").fetchone()[0]==1

def test_start_episode_uses_affect_owner_and_private_trace(setup):
    c,w,clock,result=_run(setup,{'decision':'start_episode','family':'sadness','qualitative_intensity':'moderate','target_ref':'sophie','support_refs':['candidate:primary','appraisal:primary','interpretation:primary','trace:primary']})
    assert result['decision']=='start_episode'; episode=AffectService(c,clock=clock).active_episodes(w,'erika')[0]; assert episode['family']=='sadness' and episode['intensity_milli']==500 and episode['action_tendency']=='none' and episode['expression_milli']==0 and episode['target_character_key']=='sophie'
    assert c.execute("SELECT COUNT(*) FROM mood_state").fetchone()[0]==0; assert c.execute("SELECT COUNT(*) FROM subjective_belief").fetchone()[0]==0; assert c.execute("SELECT COUNT(*) FROM relationship_view").fetchone()[0]==0

def test_snapshot_is_owner_scoped_and_target_is_allowlisted(setup):
    c,w,clock=_source(setup,'affect_case'); snap=SCC3AAffectContextBuilder(c).build(w,'erika','affect_case'); assert snap.data['owner']['character_key']=='erika'; assert set(snap.data['allowed_targets'])=={'sophie','erika'}; assert 'luna_private' not in snap.wire
    with pytest.raises(SCC3AAffectError): SCC3AAffectLLMService(c,DeterministicSCC3AAffectProvider({'decision':'start_episode','family':'anger','qualitative_intensity':'high','target_ref':'luna','support_refs':['candidate:primary']}),clock=clock).run(w,'erika','affect_case',provider_turn_id='bad_target')

def test_invalid_family_action_hidden_motive_and_partial_write_are_rejected(setup):
    for proposal in ({'decision':'start_episode','family':'surprise','qualitative_intensity':'low','target_ref':None,'support_refs':['candidate:primary']},{'decision':'start_episode','family':'anger','qualitative_intensity':'low','target_ref':None,'support_refs':['confronter Sophie']},{'decision':'start_episode','family':'anger','qualitative_intensity':'low','target_ref':None,'support_refs':['candidate:primary'],'action':'confront'}):
        c,w,clock=_source(setup,'affect_case'); before=c.execute('SELECT COUNT(*) FROM emotion_episode').fetchone()[0]
        with pytest.raises(SCC3AAffectError): SCC3AAffectLLMService(c,DeterministicSCC3AAffectProvider(proposal),clock=clock).run(w,'erika','affect_case',provider_turn_id='invalid')
        assert c.execute('SELECT COUNT(*) FROM emotion_episode').fetchone()[0]==before

def test_idempotence_and_ambiguity_can_end_no_change(setup):
    proposal={'decision':'no_change','family':None,'qualitative_intensity':None,'target_ref':None,'support_refs':[]}; c,w,clock,result=_run(setup,proposal); again=SCC3AAffectLLMService(c,DeterministicSCC3AAffectProvider(proposal),clock=clock).run(w,'erika','affect_case',provider_turn_id='scc3a_test_1'); assert again['decision']=='no_change'; assert c.execute('SELECT COUNT(*) FROM scc3a_decision').fetchone()[0]==1

def test_live_scc3a_runs_only_for_affect_candidate_and_stops(setup):
    c,w,clock=_source(setup,'affect_case'); ip=DeterministicInterpretationProvider({'schema_version':2,'understanding_status':'unresolved','meaning_hypotheses':[]},model_id='fake-qwen3-14b'); ap=DeterministicAppraisalProvider({'schema_version':1,'appraisal_status':'relevant','qualitative_meaning':'neutral','importance':'low','bases':['interpretation:primary'],'candidates':[{'candidate_key':'affect_live','domain':'affect','basis_refs':['interpretation:primary'],'justification':'Examen affectif possible.'}]}); ep=DeterministicSCC3AAffectProvider({'decision':'start_episode','family':'affection','qualitative_intensity':'low','target_ref':None,'support_refs':['candidate:primary']})
    service=LiveSocialCognitionService(c,ip,clock=clock,admission_policy=FixedAdmissionPolicy('selected'),appraisal_provider=ap,affect_provider=ep); assert service.retry_one_pending(w,CognitionCallLimits(0,3600,30)) is None
    SocialSceneService(c,clock=clock).speak(w,'scc3a_scene','speech_2','sophie',act_kind='inform',content='Nouvelle parole.',recipient_key='erika')
    outcomes=service.process_speech(w,'scc3a_scene','speech_2',CognitionCallLimits(0,3600,30)); assert sum(x.affect_statuses.count('applied') for x in outcomes)==3; assert c.execute('SELECT COUNT(*) FROM emotion_episode').fetchone()[0]==3
