import pytest
from vivarium.beliefs import BeliefError, BeliefService
from vivarium.cognition import CognitionContextService
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import subjective_belief_audit, subjective_belief_digest
from vivarium.subjective_memory import SubjectiveMemoryService
from vivarium.traversal import TraversalEngine

@pytest.fixture
def setup():
 c=connect_database(':memory:'); ensure_schema(c); w=IntegrationWorldService(c).create_initial_world()['id']; yield c,w; c.close()

def test_belief_requires_private_trace_and_keeps_revision(setup):
 c,w=setup; seq=c.execute('SELECT MAX(seq) FROM canonical_event WHERE world_id=?',(w,)).fetchone()[0]+1; TraversalEngine(c).traverse_character(w,'sophie','porte_entree','salon'); SubjectiveMemoryService(c).encode_direct_event(w,'sophie','saw_move',seq)
 b=BeliefService(c); first=b.adopt(w,'sophie','sophie_is_in_salon',question_key='sophie_location',proposition={'character':'sophie','location':'salon'},polarity='true',confidence_milli=600,trace_request_key='saw_move'); assert first['status']=='active'
 revised=b.adopt(w,'sophie','sophie_location_unknown',question_key='sophie_location',proposition={'character':'sophie','location':'unknown'},polarity='uncertain',confidence_milli=400,trace_request_key='saw_move',revision_of_key='sophie_is_in_salon'); assert revised['polarity']=='uncertain'
 assert [x['status'] for x in reversed(b.list(w,'sophie'))]==['contested','active']
 with pytest.raises(BeliefError) as err: b.adopt(w,'erika','steal',question_key='x',proposition={},polarity='true',confidence_milli=1,trace_request_key='saw_move')
 assert err.value.code=='belief_source_not_accessible'

def test_belief_revision_and_evidence_cannot_be_silently_mutated(setup):
 c,w=setup; seq=c.execute('SELECT MAX(seq) FROM canonical_event WHERE world_id=?',(w,)).fetchone()[0]+1; TraversalEngine(c).traverse_character(w,'sophie','porte_entree','salon'); SubjectiveMemoryService(c).encode_direct_event(w,'sophie','saw_move',seq)
 belief=BeliefService(c); belief.adopt(w,'sophie','sophie_is_in_salon',question_key='sophie_location',proposition={'character':'sophie','location':'salon'},polarity='true',confidence_milli=600,trace_request_key='saw_move')
 row=c.execute('SELECT id FROM subjective_belief WHERE world_id=?',(w,)).fetchone()
 with pytest.raises(Exception): c.execute("UPDATE subjective_belief SET confidence_milli=1 WHERE id=?",(row['id'],))
 with pytest.raises(Exception): c.execute('DELETE FROM subjective_belief_evidence WHERE belief_id=?',(row['id'],))

def test_belief_digest_and_audit_stay_separate_from_canonical_truth(setup):
 c,w=setup; seq=c.execute('SELECT MAX(seq) FROM canonical_event WHERE world_id=?',(w,)).fetchone()[0]+1; TraversalEngine(c).traverse_character(w,'sophie','porte_entree','salon'); SubjectiveMemoryService(c).encode_direct_event(w,'sophie','saw_move',seq)
 BeliefService(c).adopt(w,'sophie','sophie_is_in_salon',question_key='sophie_location',proposition={'character':'sophie','location':'salon'},polarity='true',confidence_milli=600,trace_request_key='saw_move')
 digest=subjective_belief_digest(c,w)
 assert digest['sophie'][0]['evidence'][0]['source_trace']=='saw_move'
 assert subjective_belief_audit(c,w)==[]

def test_cognition_context_receives_only_its_own_bounded_beliefs(setup):
 c,w=setup; seq=c.execute('SELECT MAX(seq) FROM canonical_event WHERE world_id=?',(w,)).fetchone()[0]+1; TraversalEngine(c).traverse_character(w,'sophie','porte_entree','salon'); SubjectiveMemoryService(c).encode_direct_event(w,'sophie','saw_move',seq)
 BeliefService(c).adopt(w,'sophie','sophie_is_in_salon',question_key='sophie_location',proposition={'character':'sophie','location':'salon'},polarity='true',confidence_milli=600,trace_request_key='saw_move')
 assert CognitionContextService(c).build(w,'sophie').beliefs[0]['belief_key']=='sophie_is_in_salon'
 assert CognitionContextService(c).build(w,'erika').beliefs==()
