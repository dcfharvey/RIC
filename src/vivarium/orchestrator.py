"""Boucle bornée entre événements perceptibles, admission LLM et moteur.

Le curseur est technique. Les appels restent dédupliqués par le ledger et les
actions éventuelles passent toujours par ``ActionOrchestrator`` via le routeur.
"""
from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from typing import Any
from .cognition import CognitionProvider
from .cognition_policy import CognitionCallLimits, CALL_TRIGGER_DIRECT_EVENT
from .cognitive_flow import CognitiveFlowScheduler
from .cognition_router import CognitionCallRouter, CognitionCallRouterError
from .character_capabilities import sapient_character_keys
from .db import transaction
from .util import Clock, new_uuid

class OrchestratorError(ValueError):
 def __init__(self,message:str,*,code:str)->None:super().__init__(message);self.code=code
@dataclass(frozen=True)
class OrchestratorOutcome:
 character_key:str;source_event_seq:int;outcome:str;detail_code:str|None
@dataclass(frozen=True)
class OrchestratorTick:
 world_id:int;through_event_seq:int;outcomes:tuple[OrchestratorOutcome,...]

class VivariumOrchestrator:
 def __init__(self,conn:sqlite3.Connection,provider:CognitionProvider,clock:Clock|None=None,flow_scheduler:CognitiveFlowScheduler|None=None)->None:self._conn,self._provider,self._clock=conn,provider,clock or Clock();self._flow_scheduler=flow_scheduler
 def _characters(self,wid:int):
  keys=sapient_character_keys(self._conn,wid)
  if not keys:return ()
  return self._conn.execute(
   f'SELECT id,key FROM character WHERE world_id=? AND key IN ({",".join("?" for _ in keys)}) ORDER BY key',
   (wid,*keys),
  ).fetchall()
 def _cursor(self,wid:int,cid:int)->int:
  row=self._conn.execute('SELECT last_event_seq FROM orchestrator_cursor WHERE world_id=? AND character_id=?',(wid,cid)).fetchone();return 0 if row is None else row['last_event_seq']
 def _save(self,wid:int,cid:int,seq:int)->None:
  now=self._clock.now_iso()
  with transaction(self._conn) as c:c.execute('INSERT INTO orchestrator_cursor (world_id,character_id,last_event_seq,updated_at) VALUES (?,?,?,?) ON CONFLICT(world_id,character_id) DO UPDATE SET last_event_seq=excluded.last_event_seq,updated_at=excluded.updated_at',(wid,cid,seq,now))
 def _record(self,wid:int,cid:int,seq:int,outcome:str,detail:str|None)->None:
  with transaction(self._conn) as c:c.execute('INSERT OR IGNORE INTO orchestrator_run_event (public_id,world_id,character_id,source_event_seq,outcome,detail_code,recorded_at) VALUES (?,?,?,?,?,?,?)',(new_uuid(),wid,cid,seq,outcome,detail,self._clock.now_iso()))
 def tick(self,wid:Any,limits:Any,*,max_events_per_character:Any=3)->OrchestratorTick:
  if not isinstance(wid,int) or isinstance(wid,bool) or wid<1:raise OrchestratorError('monde invalide',code='invalid_orchestrator')
  if not isinstance(limits,CognitionCallLimits):raise OrchestratorError('limites invalides',code='invalid_orchestrator')
  limits.validated()
  if not isinstance(max_events_per_character,int) or isinstance(max_events_per_character,bool) or not 1<=max_events_per_character<=20:raise OrchestratorError('borne d’événements invalide',code='invalid_orchestrator')
  maximum=self._conn.execute('SELECT COALESCE(MAX(seq),0) FROM canonical_event WHERE world_id=?',(wid,)).fetchone()[0];out=[];router=CognitionCallRouter(self._conn,self._provider,clock=self._clock,flow_scheduler=self._flow_scheduler)
  for character in self._characters(wid):
   cursor=self._cursor(wid,character['id']);rows=self._conn.execute('SELECT seq FROM canonical_event WHERE world_id=? AND seq>? AND seq<=? ORDER BY seq LIMIT ?',(wid,cursor,maximum,max_events_per_character)).fetchall()
   for row in rows:
    seq=row['seq'];outcome='unperceived';detail=None
    try:
     routed=router.run(wid,character['key'],CALL_TRIGGER_DIRECT_EVENT,f'event_{seq}',f'orch_{character["key"]}_{seq}',limits)
     if routed.provider_error_code is not None:outcome,detail='provider_degraded',routed.provider_error_code
     elif routed.admission.verdict.eligible:outcome,detail='routed',None
     else:outcome,detail='deferred',routed.admission.verdict.reason_code
    except CognitionCallRouterError as exc:detail=exc.code
    self._record(wid,character['id'],seq,outcome,detail);out.append(OrchestratorOutcome(character['key'],seq,outcome,detail))
    if detail in {'provider_busy','provider_dispatch_pending','already_queued','cognitive_queue_full'}:
     break
    if detail == 'fairness_wait':
     continue
    self._save(wid,character['id'],seq)
  return OrchestratorTick(wid,maximum,tuple(out))
