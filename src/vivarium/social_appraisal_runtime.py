"""Orchestration technique bornee de SCC-2A apres SCC-1B."""
from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from typing import Any
from .cognition_call_ledger import CognitionCallLedgerService
from .cognitive_flow import CognitiveFlowRequest, CognitiveFlowScheduler, CognitiveFlowTelemetry, flow_failure_state
from .diagnostics import DiagnosticRecorder
from .cognition_policy import CALL_TRIGGER_SOCIAL_APPRAISAL, CognitionCallLimits
from .social_appraisal import SocialAppraisalError, SocialAppraisalService
from .social_appraisal_provider import SocialAppraisalLLMService
from .util import Clock, new_uuid


RETRY_DELAY_SECONDS = 30

@dataclass(frozen=True)
class LiveSocialAppraisalOutcome:
    character_key:str; interpretation_key:str; technical_status:str; appraisal_status:str|None=None; candidate_count:int=0; detail_code:str|None=None

class LiveSocialAppraisalService:
    def __init__(self,conn:sqlite3.Connection,provider:Any,clock:Clock|None=None,diagnostics:DiagnosticRecorder|None=None,flow_scheduler:CognitiveFlowScheduler|None=None): self.conn,self.provider,self.clock,self.diagnostics=conn,provider,clock or Clock(),diagnostics; self.flow_scheduler=flow_scheduler; self.flow_telemetry=CognitiveFlowTelemetry(conn,clock=self.clock); self.ledger=CognitionCallLedgerService(conn,clock=self.clock,flow_scheduler=flow_scheduler)
    def _row(self,wid,owner,ikey):
        return self.conn.execute('SELECT i.id,i.interpretation_key FROM social_interpretation i JOIN character c ON c.id=i.character_id WHERE i.world_id=? AND c.key=? AND i.interpretation_key=?',(wid,owner,ikey)).fetchone()
    def process(self,wid:int,owner:str,ikey:str,limits:CognitionCallLimits,*,retry=False)->LiveSocialAppraisalOutcome:
        src=self._row(wid,owner,ikey)
        if src is None: raise SocialAppraisalError('interpretation introuvable',code='source_not_accessible')
        existing=self.conn.execute('SELECT outcome,detail_code FROM scc2a_attempt WHERE world_id=? AND source_interpretation_id=? ORDER BY id DESC LIMIT 1',(wid,src['id'])).fetchone()
        if existing is not None and existing['outcome']=='appraised' and not retry:
            row=self.conn.execute('SELECT appraisal_key,appraisal_status FROM social_appraisal WHERE world_id=? AND source_interpretation_id=?',(wid,src['id'])).fetchone(); sheet=SocialAppraisalService(self.conn).get(wid,owner,row['appraisal_key']); return LiveSocialAppraisalOutcome(owner,ikey,'appraised',sheet['appraisal_status'],len(sheet['candidates']))
        attempt_no=self.conn.execute('SELECT COUNT(*) FROM scc2a_attempt WHERE source_interpretation_id=?',(src['id'],)).fetchone()[0]+1
        source_key=f'social_appraisal_{src["id"]}_attempt_{attempt_no}'
        technical=self.ledger.admit(wid,owner,CALL_TRIGGER_SOCIAL_APPRAISAL,source_key,limits)
        attempt_key=f'live_scc2a_attempt_{src["id"]}_{attempt_no}'
        if not technical.verdict.eligible:
            self._record(wid,owner,src['id'],attempt_key,'deferred',technical.verdict.reason_code); return LiveSocialAppraisalOutcome(owner,ikey,'deferred',detail_code=technical.verdict.reason_code)
        flow_request=CognitiveFlowRequest(wid,owner,CALL_TRIGGER_SOCIAL_APPRAISAL,source_key,technical.admitted_at or self.clock.now_iso())
        provider_started=self.clock.now_iso()
        if self.flow_scheduler is not None: self.flow_telemetry.record(flow_request,'executing',canonical_at=technical.admitted_at,provider_started_at=provider_started)
        try:
            sheet=SocialAppraisalLLMService(self.conn,self.provider,clock=self.clock,diagnostics=self.diagnostics).run(wid,owner,f'live_scc2a_{src["id"]}',ikey,provider_turn_id=f'scc2a_{src["id"]}_{attempt_no}')
        except Exception as exc:
            if self.flow_scheduler is not None: self.flow_telemetry.record(flow_request,flow_failure_state(getattr(exc,'code','provider_failed')),reason_code=getattr(exc,'code','provider_failed'),canonical_at=technical.admitted_at,provider_started_at=provider_started,provider_finished_at=self.clock.now_iso())
            self._record(wid,owner,src['id'],attempt_key,'provider_unavailable',getattr(exc,'code','provider_failed')); return LiveSocialAppraisalOutcome(owner,ikey,'provider_unavailable',detail_code=getattr(exc,'code','provider_failed'))
        if self.flow_scheduler is not None: self.flow_telemetry.record(flow_request,'completed',canonical_at=technical.admitted_at,provider_started_at=provider_started,provider_finished_at=self.clock.now_iso())
        self._record(wid,owner,src['id'],attempt_key,'appraised'); return LiveSocialAppraisalOutcome(owner,ikey,'appraised',sheet['appraisal_status'],len(sheet['candidates']))
    def _record(self,wid,owner,source_id,key,outcome,detail=None):
        row=self.conn.execute('SELECT id FROM character WHERE world_id=? AND key=?',(wid,owner)).fetchone(); now=self.clock.now_iso(); self.conn.execute('INSERT INTO scc2a_attempt (public_id,world_id,character_id,source_interpretation_id,attempt_key,outcome,detail_code,recorded_at) VALUES (?,?,?,?,?,?,?,?)',(new_uuid(),wid,row['id'],source_id,key,outcome,detail,now)); self.conn.commit()
    def retry(self,wid:int,owner:str,ikey:str,limits:CognitionCallLimits)->LiveSocialAppraisalOutcome:
        row=self._row(wid,owner,ikey)
        if row is None: raise SocialAppraisalError('interpretation introuvable',code='source_not_accessible')
        latest=self.conn.execute('SELECT outcome,detail_code,recorded_at FROM scc2a_attempt WHERE source_interpretation_id=? ORDER BY id DESC LIMIT 1',(row['id'],)).fetchone()
        if latest is None or latest['outcome']=='appraised': return self.process(wid,owner,ikey,limits)
        if not self.ledger.retry_due(
            wid, owner, limits, attempted_at=latest['recorded_at'],
            reason_code=latest['detail_code'] or 'technical_failure',
            retry_delay_seconds=RETRY_DELAY_SECONDS,
        ):
            return LiveSocialAppraisalOutcome(owner,ikey,'deferred',detail_code='retry_backoff')
        return self.process(wid,owner,ikey,limits,retry=True)

    def next_pending_retry(self,wid:int,limits:CognitionCallLimits):
        rows=self.conn.execute("SELECT c.key AS owner,i.interpretation_key,a.recorded_at,a.id,a.detail_code FROM scc2a_attempt a JOIN social_interpretation i ON i.id=a.source_interpretation_id JOIN character c ON c.id=a.character_id WHERE a.world_id=? AND a.outcome IN ('deferred','provider_unavailable') AND NOT EXISTS (SELECT 1 FROM scc2a_attempt newer WHERE newer.source_interpretation_id=a.source_interpretation_id AND newer.id>a.id) ORDER BY a.recorded_at,a.id",(wid,)).fetchall()
        for row in rows:
            if self.ledger.retry_due(
                wid,row['owner'],limits,attempted_at=row['recorded_at'],
                reason_code=row['detail_code'] or 'technical_failure',
                retry_delay_seconds=RETRY_DELAY_SECONDS,
            ):
                return row
        return None

    def retry_one_pending(self,wid:int,limits:CognitionCallLimits)->LiveSocialAppraisalOutcome|None:
        row=self.next_pending_retry(wid,limits)
        return None if row is None else self.retry(wid,row['owner'],row['interpretation_key'],limits)
