"""Orchestration technique bornee de SCC-2A apres SCC-1B."""
from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from typing import Any
from .cognition_call_ledger import CognitionCallLedgerService
from .cognition_policy import CALL_TRIGGER_SOCIAL_APPRAISAL, CognitionCallLimits
from .social_appraisal import SocialAppraisalError, SocialAppraisalService
from .social_appraisal_provider import SocialAppraisalLLMService
from .util import Clock, new_uuid

@dataclass(frozen=True)
class LiveSocialAppraisalOutcome:
    character_key:str; interpretation_key:str; technical_status:str; appraisal_status:str|None=None; candidate_count:int=0; detail_code:str|None=None

class LiveSocialAppraisalService:
    def __init__(self,conn:sqlite3.Connection,provider:Any,clock:Clock|None=None): self.conn,self.provider,self.clock=conn,provider,clock or Clock(); self.ledger=CognitionCallLedgerService(conn,clock=self.clock)
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
        try:
            sheet=SocialAppraisalLLMService(self.conn,self.provider,clock=self.clock).run(wid,owner,f'live_scc2a_{src["id"]}',ikey,provider_turn_id=f'scc2a_{src["id"]}_{attempt_no}')
        except Exception as exc:
            self._record(wid,owner,src['id'],attempt_key,'provider_unavailable',getattr(exc,'code','provider_failed')); return LiveSocialAppraisalOutcome(owner,ikey,'provider_unavailable',detail_code=getattr(exc,'code','provider_failed'))
        self._record(wid,owner,src['id'],attempt_key,'appraised'); return LiveSocialAppraisalOutcome(owner,ikey,'appraised',sheet['appraisal_status'],len(sheet['candidates']))
    def _record(self,wid,owner,source_id,key,outcome,detail=None):
        row=self.conn.execute('SELECT id FROM character WHERE world_id=? AND key=?',(wid,owner)).fetchone(); now=self.clock.now_iso(); self.conn.execute('INSERT INTO scc2a_attempt (public_id,world_id,character_id,source_interpretation_id,attempt_key,outcome,detail_code,recorded_at) VALUES (?,?,?,?,?,?,?,?)',(new_uuid(),wid,row['id'],source_id,key,outcome,detail,now)); self.conn.commit()
    def retry(self,wid:int,owner:str,ikey:str,limits:CognitionCallLimits)->LiveSocialAppraisalOutcome:
        row=self._row(wid,owner,ikey)
        if row is None: raise SocialAppraisalError('interpretation introuvable',code='source_not_accessible')
        latest=self.conn.execute('SELECT outcome FROM scc2a_attempt WHERE source_interpretation_id=? ORDER BY id DESC LIMIT 1',(row['id'],)).fetchone()
        if latest is None or latest['outcome']=='appraised': return self.process(wid,owner,ikey,limits)
        return self.process(wid,owner,ikey,limits,retry=True)
    def retry_one_pending(self,wid:int,limits:CognitionCallLimits)->LiveSocialAppraisalOutcome|None:
        row=self.conn.execute("SELECT c.key AS owner,i.interpretation_key FROM scc2a_attempt a JOIN social_interpretation i ON i.id=a.source_interpretation_id JOIN character c ON c.id=a.character_id WHERE a.outcome IN ('deferred','provider_unavailable') AND NOT EXISTS (SELECT 1 FROM scc2a_attempt newer WHERE newer.source_interpretation_id=a.source_interpretation_id AND newer.id>a.id) ORDER BY a.recorded_at,a.id LIMIT 1").fetchone()
        return None if row is None else self.retry(wid,row['owner'],row['interpretation_key'],limits)
