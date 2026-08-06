import pytest
from vivarium.cognition import CognitionDecision, CognitionError
from vivarium.cognition_policy import CognitionCallLimits
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.orchestrator import VivariumOrchestrator
from vivarium.traversal import TraversalEngine

class Provider:
 def __init__(self,error=None):self.calls=[];self.error=error
 def decide(self,context):
  self.calls.append(context)
  if self.error:raise CognitionError('indisponible',code=self.error)
  return CognitionDecision('no_action')

@pytest.fixture
def setup():
 c=connect_database(':memory:');ensure_schema(c);wid=IntegrationWorldService(c).create_initial_world()['id'];yield c,wid;c.close()
def _limits():return CognitionCallLimits(0,86400,100)

def test_tick_routes_only_perceptible_snapshot_events_and_advances_cursor(setup):
 c,w=setup;TraversalEngine(c).traverse_character(w,'sophie','porte_entree','salon');p=Provider();o=VivariumOrchestrator(c,p)
 warmup=o.tick(w,_limits(),max_events_per_character=20);first=o.tick(w,_limits(),max_events_per_character=20)
 assert first.through_event_seq>0 and len(p.calls)>0
 count=len(p.calls);second=o.tick(w,_limits(),max_events_per_character=20)
 assert second.outcomes==() and len(p.calls)==count
 assert c.execute('SELECT COUNT(*) FROM orchestrator_run_event WHERE world_id=?',(w,)).fetchone()[0]==len(warmup.outcomes)+len(first.outcomes)

def test_provider_failure_is_degraded_and_does_not_retry_same_source_forever(setup):
 c,w=setup;TraversalEngine(c).traverse_character(w,'sophie','porte_entree','salon');p=Provider('llm_unavailable');o=VivariumOrchestrator(c,p)
 o.tick(w,_limits(),max_events_per_character=20);first=o.tick(w,_limits(),max_events_per_character=20)
 assert any(item.outcome=='provider_degraded' for item in first.outcomes)
 assert o.tick(w,_limits(),max_events_per_character=20).outcomes==()
