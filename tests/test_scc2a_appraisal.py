from datetime import datetime, timedelta, timezone
import pytest

from vivarium.cognition_policy import CognitionCallLimits
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import social_appraisal_audit
from vivarium.scenes import SocialSceneService
from vivarium.scc1c import FixedAdmissionPolicy
from vivarium.social_appraisal import SocialAppraisalError
from vivarium.social_appraisal_provider import DeterministicAppraisalProvider, SocialAppraisalContextBuilder, SocialAppraisalLLMService
from vivarium.social_cognition_runtime import LiveSocialCognitionService
from vivarium.social_interpretation_provider import DeterministicInterpretationProvider
from vivarium.util import Clock, to_iso

class FakeClock(Clock):
    def __init__(self): self.current=datetime(2026,8,10,12,tzinfo=timezone.utc)
    def now(self): return self.current
    def now_iso(self): return to_iso(self.current)
    def advance(self, seconds): self.current += timedelta(seconds=seconds)

@pytest.fixture
def setup():
    c=connect_database(':memory:'); ensure_schema(c); clock=FakeClock(); w=IntegrationWorldService(c,clock=clock).create_initial_world()['id']; SocialSceneService(c,clock=clock).open(w,'scc2a_scene',('sophie','erika','luna')); SocialSceneService(c,clock=clock).speak(w,'scc2a_scene','speech_1','sophie',act_kind='inform',content='Sophie partage une parole.',recipient_key='erika'); yield c,w,clock; c.close()

def _interpret(setup, *, status='clear', hypotheses=None):
    c,w,clock=setup; p=DeterministicInterpretationProvider({'schema_version':2,'understanding_status':status,'meaning_hypotheses':hypotheses or (['Lecture subjective'] if status=='clear' else [])},model_id='fake-qwen3-14b'); return LiveSocialCognitionService(c,p,clock=clock,admission_policy=FixedAdmissionPolicy('selected')).process_speech(w,'scc2a_scene','speech_1',CognitionCallLimits(0,3600,20))

def _proposal(status='relevant', *, bases=None, candidates=None):
    return {'schema_version':1,'appraisal_status':status,'qualitative_meaning':'uncertain' if status in {'ambiguous','unresolved'} else 'neutral','importance':'uncertain' if status=='unresolved' else 'low','bases':bases or ([] if status=='unresolved' else ['interpretation:primary']),'candidates':candidates or []}

def test_contract_unresolved_and_zero_candidate_are_valid(setup):
    c,w,clock=setup; _interpret(setup); p=DeterministicAppraisalProvider(_proposal('unresolved')); sheet=SocialAppraisalLLMService(c,p,clock=clock).run(w,'erika','a_unresolved','live_scc1b_2',provider_turn_id='t1')
    assert sheet['appraisal_status']=='unresolved' and sheet['candidates']==() and p.calls==1
    p2=DeterministicAppraisalProvider(_proposal('not_relevant')); sheet2=SocialAppraisalLLMService(c,p2,clock=clock).run(w,'luna','a_banal','live_scc1b_3',provider_turn_id='t2')
    assert sheet2['appraisal_status']=='not_relevant' and sheet2['candidates']==()

def test_snapshot_is_owner_scoped_and_context_refs_are_engine_owned(setup):
    c,w,clock=setup; _interpret(setup)
    snap=SocialAppraisalContextBuilder(c).build(w,'erika','live_scc1b_2')
    assert snap.data['owner']['character_key']=='erika'
    assert set(snap.data['allowed_base_refs'])=={'interpretation:primary'}
    assert 'subjective_belief' not in snap.wire and 'sophie_private' not in snap.wire

def test_valid_candidates_are_independent_and_no_mutation_fields(setup):
    c,w,clock=setup; _interpret(setup)
    candidates=[{'candidate_key':'affect_review','domain':'affect','basis_refs':['interpretation:primary'],'justification':'Le domaine affectif pourrait examiner cet episode.'},{'candidate_key':'relation_review','domain':'relationship','basis_refs':['interpretation:primary'],'justification':'Le domaine relationnel pourrait examiner cet episode.'}]
    sheet=SocialAppraisalLLMService(c,DeterministicAppraisalProvider(_proposal(bases=['interpretation:primary'],candidates=candidates)),clock=clock).run(w,'erika','a_candidates','live_scc1b_2',provider_turn_id='t3')
    assert len(sheet['candidates'])==2
    assert social_appraisal_audit(c,w) == []
    for table in ('mood_state','emotion_episode','subjective_belief','relationship_view','subjective_goal'):
        assert c.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]==0

def test_invalid_reference_and_hidden_intent_are_rejected_without_partial_write(setup):
    c,w,clock=setup; _interpret(setup); before=c.execute('SELECT COUNT(*) FROM social_appraisal').fetchone()[0]
    bad=_proposal(bases=['goal:invented'],candidates=[])
    with pytest.raises(SocialAppraisalError): SocialAppraisalLLMService(c,DeterministicAppraisalProvider(bad),clock=clock).run(w,'erika','a_bad','live_scc1b_2',provider_turn_id='t4')
    hidden=_proposal(bases=['interpretation:primary'],candidates=[{'candidate_key':'x','domain':'belief','basis_refs':['interpretation:primary'],'justification':'Sophie voulait blesser Erika.'}])
    with pytest.raises(SocialAppraisalError): SocialAppraisalLLMService(c,DeterministicAppraisalProvider(hidden),clock=clock).run(w,'erika','a_hidden','live_scc1b_2',provider_turn_id='t5')
    assert c.execute('SELECT COUNT(*) FROM social_appraisal').fetchone()[0]==before

def test_live_chain_stops_at_appraisal_and_is_idempotent(setup):
    c,w,clock=setup; ip=DeterministicInterpretationProvider({'schema_version':2,'understanding_status':'clear','meaning_hypotheses':['Lecture subjective']},model_id='fake-qwen3-14b'); ap=DeterministicAppraisalProvider(_proposal('not_relevant'))
    outcomes=LiveSocialCognitionService(c,ip,clock=clock,admission_policy=FixedAdmissionPolicy('selected'),appraisal_provider=ap).process_speech(w,'scc2a_scene','speech_1',CognitionCallLimits(0,3600,20))
    assert sum(x.appraisal_status=='not_relevant' for x in outcomes)==3 and ap.calls==3
    LiveSocialCognitionService(c,ip,clock=clock,admission_policy=FixedAdmissionPolicy('selected'),appraisal_provider=ap).process_speech(w,'scc2a_scene','speech_1',CognitionCallLimits(0,3600,20))
    assert ap.calls==3 and c.execute('SELECT COUNT(*) FROM social_appraisal').fetchone()[0]==3

def test_provider_failure_is_technical_and_retry_is_bounded(setup):
    c,w,clock=setup; ip=DeterministicInterpretationProvider({'schema_version':2,'understanding_status':'unresolved','meaning_hypotheses':[]},model_id='fake-qwen3-14b')
    class Flaky:
        model_id='fake-qwen3-14b'; provider_version='fake-scc2a-v1'
        def __init__(self): self.calls=0
        def propose(self,snapshot):
            self.calls+=1
            if self.calls==1: raise RuntimeError('LM Studio indisponible')
            return _proposal('not_relevant')
    ap=Flaky(); service=LiveSocialCognitionService(c,ip,clock=clock,admission_policy=FixedAdmissionPolicy('selected'),appraisal_provider=ap); out=service.process_speech(w,'scc2a_scene','speech_1',CognitionCallLimits(0,3600,20)); assert sum(x.appraisal_technical_status=='provider_unavailable' for x in out)==1
    clock.advance(30)
    pending=service.retry_one_pending(w,CognitionCallLimits(0,3600,20)); assert pending is not None
    assert c.execute('SELECT COUNT(*) FROM social_appraisal').fetchone()[0]==3 and c.execute('SELECT COUNT(*) FROM scc2a_attempt WHERE outcome="appraised"').fetchone()[0]==3

def test_scc2a_provider_retry_uses_wall_time_when_canonical_clock_is_skewed(setup):
    c,w,clock=setup
    c.execute("UPDATE canonical_clock SET simulated_now=?, real_updated_at=?, runtime_state='running' WHERE world_id=?",('2026-08-10T08:00:00+00:00',clock.now_iso(),w)); c.commit()
    ip=DeterministicInterpretationProvider({'schema_version':2,'understanding_status':'unresolved','meaning_hypotheses':[]},model_id='fake-qwen3-14b')
    class Flaky:
        model_id='fake-qwen3-14b'; provider_version='fake-scc2a-v1'
        def __init__(self): self.calls=0
        def propose(self,snapshot):
            self.calls+=1
            if self.calls==1: raise RuntimeError('LM Studio indisponible')
            return _proposal('not_relevant')
    ap=Flaky(); service=LiveSocialCognitionService(c,ip,clock=clock,admission_policy=FixedAdmissionPolicy('selected'),appraisal_provider=ap)
    service.process_speech(w,'scc2a_scene','speech_1',CognitionCallLimits(0,3600,20))
    assert service.retry_one_pending(w,CognitionCallLimits(0,3600,20)) is None
    clock.advance(29)
    assert service.retry_one_pending(w,CognitionCallLimits(0,3600,20)) is None
    assert c.execute("SELECT COUNT(*) FROM scc2a_attempt WHERE outcome='provider_unavailable'").fetchone()[0]==1
    clock.advance(1)
    assert service.retry_one_pending(w,CognitionCallLimits(0,3600,20)).technical_status=='appraised'
    assert c.execute('SELECT COUNT(*) FROM scc2a_attempt').fetchone()[0]==4

def test_pending_scc2a_retry_is_not_persisted_at_every_pulse_and_recovers(setup):
    c,w,clock=setup
    ip=DeterministicInterpretationProvider({'schema_version':2,'understanding_status':'unresolved','meaning_hypotheses':[]},model_id='fake-qwen3-14b')
    class Flaky:
        model_id='fake-qwen3-14b'; provider_version='fake-scc2a-v1'
        def __init__(self): self.calls=0
        def propose(self,snapshot):
            self.calls+=1
            if self.calls==1: raise RuntimeError('LM Studio indisponible')
            return _proposal('not_relevant')
    ap=Flaky()
    service=LiveSocialCognitionService(c,ip,clock=clock,admission_policy=FixedAdmissionPolicy('selected'),appraisal_provider=ap)
    service.process_speech(w,'scc2a_scene','speech_1',CognitionCallLimits(0,3600,20))
    assert c.execute('SELECT COUNT(*) FROM scc2a_attempt').fetchone()[0]==3
    for _ in range(4):
        assert service.retry_one_pending(w,CognitionCallLimits(0,3600,20)) is None
    assert c.execute('SELECT COUNT(*) FROM scc2a_attempt').fetchone()[0]==3
    assert ap.calls==3
    clock.advance(30)
    assert service.retry_one_pending(w,CognitionCallLimits(0,3600,20)).technical_status=='appraised'
    assert c.execute('SELECT COUNT(*) FROM scc2a_attempt').fetchone()[0]==4
    assert ap.calls==4

def test_budget_deferred_scc2a_is_not_recounted_until_the_budget_reopens(setup):
    c,w,clock=setup
    ip=DeterministicInterpretationProvider({'schema_version':2,'understanding_status':'unresolved','meaning_hypotheses':[]},model_id='fake-qwen3-14b')
    ap=DeterministicAppraisalProvider(_proposal('not_relevant'))
    service=LiveSocialCognitionService(c,ip,clock=clock,admission_policy=FixedAdmissionPolicy('selected'),appraisal_provider=ap)
    limits=CognitionCallLimits(0,3600,1)
    service.process_speech(w,'scc2a_scene','speech_1',limits)
    assert c.execute("SELECT COUNT(*) FROM scc2a_attempt WHERE outcome='deferred' AND detail_code='budget_exhausted'").fetchone()[0]==3
    for _ in range(4):
        assert service.retry_one_pending(w,limits) is None
    assert c.execute('SELECT COUNT(*) FROM scc2a_attempt').fetchone()[0]==3
    assert ap.calls==0
    clock.advance(3600)
    assert service.retry_one_pending(w,limits).technical_status=='appraised'
    assert c.execute('SELECT COUNT(*) FROM scc2a_attempt').fetchone()[0]==4
    assert ap.calls==1

def test_pending_scc2a_retry_survives_restart_without_duplicate_attempt(setup):
    c,w,clock=setup
    ip=DeterministicInterpretationProvider({'schema_version':2,'understanding_status':'unresolved','meaning_hypotheses':[]},model_id='fake-qwen3-14b')
    class Flaky:
        model_id='fake-qwen3-14b'; provider_version='fake-scc2a-v1'
        def __init__(self): self.calls=0
        def propose(self,snapshot):
            self.calls+=1
            if self.calls==1: raise RuntimeError('LM Studio indisponible')
            return _proposal('not_relevant')
    ap=Flaky()
    LiveSocialCognitionService(c,ip,clock=clock,admission_policy=FixedAdmissionPolicy('selected'),appraisal_provider=ap).process_speech(w,'scc2a_scene','speech_1',CognitionCallLimits(0,3600,20))
    restarted=LiveSocialCognitionService(c,ip,clock=clock,admission_policy=FixedAdmissionPolicy('selected'),appraisal_provider=ap)
    assert restarted.retry_one_pending(w,CognitionCallLimits(0,3600,20)) is None
    assert c.execute('SELECT COUNT(*) FROM scc2a_attempt').fetchone()[0]==3
    clock.advance(30)
    assert restarted.retry_one_pending(w,CognitionCallLimits(0,3600,20)).technical_status=='appraised'
