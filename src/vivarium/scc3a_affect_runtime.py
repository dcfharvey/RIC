"""Raccordement technique borne SCC-2A affect -> AffectService."""
from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from typing import Any
from .cognition_call_ledger import CognitionCallLedgerService
from .cognition_policy import CALL_TRIGGER_SOCIAL_AFFECT, CognitionCallLimits
from .scc3a_affect import SCC3AAffectError, SCC3AAffectService
from .scc3a_affect_provider import SCC3AAffectLLMService
from .util import Clock, new_uuid


RETRY_DELAY_SECONDS = 30

@dataclass(frozen=True)
class LiveSCC3AAffectOutcome:
    character_key:str; candidate_id:int; technical_status:str; decision:str|None=None; episode_key:str|None=None; detail_code:str|None=None

class LiveSCC3AAffectService:
    def __init__(self,conn:sqlite3.Connection,provider:Any,clock:Clock|None=None): self.conn,self.provider,self.clock=conn,provider,clock or Clock(); self.ledger=CognitionCallLedgerService(conn,clock=self.clock)
    def _candidates(self,wid:int,owner:str,interpretation_key:str):
        return self.conn.execute("SELECT c.id,c.character_id FROM social_appraisal_candidate c JOIN social_appraisal a ON a.id=c.appraisal_id JOIN social_interpretation i ON i.id=a.source_interpretation_id JOIN character ch ON ch.id=c.character_id WHERE c.world_id=? AND ch.key=? AND i.interpretation_key=? AND c.domain='affect' ORDER BY c.id",(wid,owner,interpretation_key)).fetchall()
    def _attempt(self,wid,owner,candidate_id,key,outcome,detail=None):
        row=self.conn.execute('SELECT id FROM character WHERE world_id=? AND key=?',(wid,owner)).fetchone(); self.conn.execute('INSERT INTO scc3a_attempt (public_id,world_id,character_id,candidate_id,attempt_key,outcome,detail_code,recorded_at) VALUES (?,?,?,?,?,?,?,?)',(new_uuid(),wid,row['id'],candidate_id,key,outcome,detail,self.clock.now_iso())); self.conn.commit()
    def process_candidate(self,wid:int,owner:str,candidate_id:int,limits:CognitionCallLimits,*,retry=False)->LiveSCC3AAffectOutcome:
        row=self.conn.execute('SELECT c.id FROM social_appraisal_candidate c JOIN character ch ON ch.id=c.character_id WHERE c.id=? AND c.world_id=? AND ch.key=? AND c.domain=\'affect\'',(candidate_id,wid,owner)).fetchone()
        if row is None: raise SCC3AAffectError('candidate affect inaccessible',code='candidate_not_found')
        decision=self.conn.execute('SELECT decision,episode_key FROM scc3a_decision WHERE candidate_id=?',(candidate_id,)).fetchone()
        if decision is not None: return LiveSCC3AAffectOutcome(owner,candidate_id,'applied' if decision['decision']=='start_episode' else decision['decision'],decision['decision'],decision['episode_key'])
        latest=self.conn.execute('SELECT outcome,detail_code FROM scc3a_attempt WHERE candidate_id=? ORDER BY id DESC LIMIT 1',(candidate_id,)).fetchone()
        attempt_no=self.conn.execute('SELECT COUNT(*) FROM scc3a_attempt WHERE candidate_id=?',(candidate_id,)).fetchone()[0]+1
        technical=self.ledger.admit(wid,owner,CALL_TRIGGER_SOCIAL_AFFECT,f'scc3a_candidate_{candidate_id}_attempt_{attempt_no}',limits)
        key=f'live_scc3a_attempt_{candidate_id}_{attempt_no}'
        if not technical.verdict.eligible:
            self._attempt(wid,owner,candidate_id,key,'deferred',technical.verdict.reason_code); return LiveSCC3AAffectOutcome(owner,candidate_id,'deferred',detail_code=technical.verdict.reason_code)
        try:
            result=SCC3AAffectLLMService(self.conn,self.provider,clock=self.clock).run(wid,owner,candidate_id,decision_key=f'live_scc3a_{candidate_id}',provider_turn_id=f'scc3a_{candidate_id}_{attempt_no}')
        except SCC3AAffectError as exc:
            self._attempt(wid,owner,candidate_id,key,'rejected_invalid' if exc.code in {'invalid_provider_output','invalid_scc3a','invalid_provenance'} else 'provider_unavailable',exc.code); return LiveSCC3AAffectOutcome(owner,candidate_id,'rejected_invalid' if exc.code in {'invalid_provider_output','invalid_scc3a','invalid_provenance'} else 'provider_unavailable',detail_code=exc.code)
        self._attempt(wid,owner,candidate_id,key,'no_change' if result['decision']=='no_change' else 'applied'); return LiveSCC3AAffectOutcome(owner,candidate_id,'no_change' if result['decision']=='no_change' else 'applied',result['decision'],result['episode_key'])
    def process_interpretation(self,wid:int,owner:str,interpretation_key:str,limits:CognitionCallLimits)->tuple[LiveSCC3AAffectOutcome,...]:
        return tuple(self.process_candidate(wid,owner,row['id'],limits) for row in self._candidates(wid,owner,interpretation_key) if self.conn.execute('SELECT 1 FROM scc3a_decision WHERE candidate_id=?',(row['id'],)).fetchone() is None)

    def next_pending_retry(self,wid:int,limits:CognitionCallLimits):
        rows=self.conn.execute("SELECT c.key AS owner,a.candidate_id,a.recorded_at,a.id,a.detail_code FROM scc3a_attempt a JOIN character c ON c.id=a.character_id WHERE a.world_id=? AND a.outcome IN ('deferred','provider_unavailable') AND NOT EXISTS (SELECT 1 FROM scc3a_attempt newer WHERE newer.candidate_id=a.candidate_id AND newer.id>a.id) ORDER BY a.recorded_at,a.id",(wid,)).fetchall()
        for row in rows:
            if self.ledger.retry_due(
                wid,row['owner'],limits,attempted_at=row['recorded_at'],
                reason_code=row['detail_code'] or 'technical_failure',
                retry_delay_seconds=RETRY_DELAY_SECONDS,
            ):
                return row
        return None

    def retry_one_pending(self,wid:int,limits:CognitionCallLimits)->LiveSCC3AAffectOutcome|None:
        row=self.next_pending_retry(wid,limits)
        return None if row is None else self.process_candidate(wid,row['owner'],row['candidate_id'],limits,retry=True)
