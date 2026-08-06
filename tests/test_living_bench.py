from vivarium.cognition import CognitionDecision, CognitionError
from vivarium.cognition_policy import CognitionCallLimits
from vivarium.living_bench import run_living_bench
class Provider:
 def __init__(self,error=None):self.error=error;self.calls=0
 def decide(self,context):
  self.calls+=1
  if self.error:raise CognitionError('offline',code=self.error)
  return CognitionDecision('no_action')
def test_living_bench_is_jetable_and_exercises_a_routed_turn():
 p=Provider();report=run_living_bench(p,CognitionCallLimits(0,86400,100))
 assert p.calls>0 and all(v for k,v in report.audit_findings.items() if k!='bad_causes') and report.audit_findings['bad_causes']==[] and any(item.outcome=='routed' for item in report.provider_outcomes)
def test_living_bench_reports_degraded_provider_without_corrupting_world():
 report=run_living_bench(Provider('llm_unavailable'),CognitionCallLimits(0,86400,100))
 assert any(item.outcome=='provider_degraded' for item in report.provider_outcomes) and all(v for k,v in report.audit_findings.items() if k!='bad_causes') and report.audit_findings['bad_causes']==[]

def test_living_bench_calls_observer_for_each_tick():
 ticks=[]
 run_living_bench(Provider(),CognitionCallLimits(0,86400,100),on_tick=ticks.append)
 assert ticks and ticks[-1].outcomes==()
