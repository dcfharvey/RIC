"""Scheduler du runtime physiologique actif (WO88D/E).

Le scheduler avance uniquement de frontière causale en frontière causale. Il
ne lit jamais ``repos``/``energie`` et ne reconstruit jamais un historique à
partir d'un résultat. Les transitions intermédiaires gardent leur ``occurred_at``
exact; l'horloge dérivée est réancrée une seule fois à la cible capturée afin
de préserver le temps réel lors d'un rattrapage.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Literal

from .activities import ActivityEngine
from .db import transaction
from .injury import InjuryEngine
from .needs import NeedsEngine
from .simulation import SimulationReport
from .sleep_physiology import SleepPhysiologyFoundationService, SleepPhysiologyService
from .sleep_termination import (
    SleepTerminationFoundationService, SleepTerminationError, evaluate_sleep_checkpoint,
)
from .util import Clock, parse_iso, to_iso
from .world import WorldEngine

_ACTIVE_NEEDS=frozenset({"satiete","hygiene"})

@dataclass(frozen=True)
class ActiveBoundary:
    at:str
    character_key:str
    reasons:tuple[str,...]

class ActiveSimulationError(RuntimeError):
    def __init__(self,message:str,*,code:str):super().__init__(message);self.code=code

class ActiveSimulationEngine:
    def __init__(self,conn:sqlite3.Connection,clock:Clock|None=None)->None:
        self._conn,self._clock=conn,clock or Clock();self._activities=ActivityEngine(conn,clock=self._clock);self._physiology=SleepPhysiologyService(conn,clock=self._clock)
    def _require_active(self,world_id:int)->None:
        if SleepPhysiologyFoundationService(self._conn,clock=self._clock).system_status(world_id)!="active":
            raise ActiveSimulationError("scheduler actif exige physiology=active",code="physiology_not_active")
    def _characters(self,world_id:int)->tuple[str,...]:
        return tuple(r["key"] for r in self._conn.execute("SELECT key FROM character WHERE world_id=? ORDER BY key",(world_id,)))
    def _sustained(self,world_id:int,activity_type:str)->bool:
        row=self._conn.execute("SELECT requires_sustained_wakefulness FROM activity_definition WHERE world_id=? AND activity_type=?",(world_id,activity_type)).fetchone();return bool(row and row[0])
    def next_boundary(self,world_id:int,character_key:str,*,until:str)->ActiveBoundary|None:
        self._require_active(world_id);limit=to_iso(parse_iso(until));state=self._physiology.read_state(world_id,character_key);candidates=[]
        active=self._activities.activity_sheet(world_id,character_key)
        if active is not None:
            if active["type"]=="sleep":
                cp=self._activities.sleep_checkpoint(world_id,character_key)
                if cp is None or cp["status"]!="active":raise ActiveSimulationError("sommeil actif sans checkpoint",code="sleep_checkpoint_missing")
                for value,reason in ((cp["next_reassessment_at"],"sleep_checkpoint"),(cp["hard_cap_at"],"sleep_hard_cap")):
                    if parse_iso(state.anchor_at)<parse_iso(value)<=parse_iso(limit):candidates.append((value,reason))
            elif parse_iso(state.anchor_at)<parse_iso(active["planned_end_at"])<=parse_iso(limit):
                candidates.append((active["planned_end_at"],"activity_end"))
        light=self._physiology.next_light_boundary_owner_backed(world_id,character_key,until=limit)
        if light is not None:candidates.append((light,"light_change"))
        if active is not None and active["type"] not in {"sleep","rest"} and self._sustained(world_id,active["type"]):
            horizon=min([parse_iso(limit)]+[parse_iso(v) for v,_ in candidates if parse_iso(v)>parse_iso(state.anchor_at)])
            critical=self._physiology.next_critical_boundary_owner_backed(
                world_id,character_key,until=to_iso(horizon)
            )
            if critical is not None and parse_iso(critical)>parse_iso(state.anchor_at):candidates.append((critical,"wake_stability_critical"))
        if not candidates:return None
        first=min(parse_iso(v) for v,_ in candidates);at=to_iso(first)
        return ActiveBoundary(at,character_key,tuple(sorted(r for v,r in candidates if parse_iso(v)==first)))
    def is_due(self,world_id:int,target_time:str)->bool:
        self._require_active(world_id);target=to_iso(parse_iso(target_time));characters=self._characters(world_id)
        # Wall time is not a causal boundary. Owner-backed H/phi/P stay persisted
        # at their last processed cause boundary until one is actually due.
        return any(self.next_boundary(world_id,key,until=target) is not None for key in characters)
    def _passive_to(self,world_id:int,key:str,at:str)->None:
        self._physiology.materialize_owner_backed(world_id,key,at)
        with transaction(self._conn) as c:
            NeedsEngine(self._conn,clock=self._clock).materialize_selected_needs(world_id,key,at,"active_passive",_ACTIVE_NEEDS,_conn=c)
            InjuryEngine(self._conn,clock=self._clock)._materialize_injury_sim(world_id,key,at,"passive",_conn=c)
    def _sleep_checkpoint(self,world_id:int,key:str,at:str)->None:
        self._physiology.materialize_owner_backed(world_id,key,at)
        cp=self._activities.sleep_checkpoint(world_id,key)
        if cp is None or cp["status"]!="active":raise ActiveSimulationError("checkpoint actif absent",code="sleep_checkpoint_missing")
        projection=self._physiology.project_wake_viability_owner_backed(world_id,key,at_time=at)
        elapsed=int((parse_iso(at)-parse_iso(cp["started_at"])).total_seconds());termination=SleepTerminationFoundationService(self._conn,clock=self._clock);policy=termination.world_policy(world_id)
        evaluation=evaluate_sleep_checkpoint(policy,elapsed_seconds=elapsed,wake_viability_milli=projection.value_milli,previous_band=cp["previous_band"],external_wake_accessible=False)
        if evaluation.completion_eligible:
            termination.authorize_completion_owner_backed(world_id,key,at_time=at)
            self._activities.complete_sleep_from_checkpoint(world_id,key,at_time=at,_reanchor_clock=False);return
        if evaluation.hard_cap_reached:
            self._activities.report_sleep_hard_cap(world_id,key,at_time=at);return
        assert evaluation.next_reassessment_after_seconds is not None
        self._activities.advance_sleep_checkpoint(world_id,key,at_time=at,next_reassessment_at=to_iso(parse_iso(at)+timedelta(seconds=evaluation.next_reassessment_after_seconds)),previous_band=evaluation.band)
    def _process(self,world_id:int,boundary:ActiveBoundary)->None:
        key,at=boundary.character_key,boundary.at;reasons=set(boundary.reasons)
        # Materialize exactly once under causes that held before this boundary.
        self._physiology.materialize_owner_backed(world_id,key,at)
        active=self._activities.activity_sheet(world_id,key)
        if "wake_stability_critical" in reasons and active is not None and self._sustained(world_id,active["type"]):
            if self._physiology.read_state(world_id,key).previous_stability_band=="critical":
                self._activities.abort_activity(world_id,key,sim_now=at,reason_code="wake_stability_critical",_reanchor_clock=False);return
        active=self._activities.activity_sheet(world_id,key)
        if active is not None and active["type"]=="sleep" and ({"sleep_checkpoint","sleep_hard_cap"}&reasons):
            self._sleep_checkpoint(world_id,key,at);return
        if active is not None and active["type"]!="sleep" and "activity_end" in reasons:
            self._activities.advance_to(world_id,key,at,_reanchor_clock=False)
    def run_to(self,world_id:int,target_time:str,max_transitions:int=1000)->SimulationReport:
        self._require_active(world_id)
        if not isinstance(max_transitions,int) or isinstance(max_transitions,bool) or max_transitions<1:raise ActiveSimulationError("borne invalide",code="invalid_transition_limit")
        captured=to_iso(max(parse_iso(target_time),parse_iso(WorldEngine(self._conn,clock=self._clock).read_canonical_time(world_id))))
        transitions=0;chars=self._characters(world_id)
        while True:
            boundaries=[b for key in chars if (b:=self.next_boundary(world_id,key,until=captured)) is not None]
            if not boundaries:break
            first=min(parse_iso(b.at) for b in boundaries);due=sorted((b for b in boundaries if parse_iso(b.at)==first),key=lambda b:b.character_key)
            for boundary in due:
                if transitions>=max_transitions:raise ActiveSimulationError("limite de transitions active atteinte",code="transition_limit")
                self._process(world_id,boundary);transitions+=1
        # The world clock may reanchor to the captured real-time target, but the
        # physiology is never materialized merely because wall time passed.
        # Persisted H/phi/P therefore remain at the last processed causal boundary.
        with transaction(self._conn) as c:WorldEngine(self._conn,clock=self._clock)._advance_clock(world_id,captured,c)
        active_now=[f"{r['character']}:{r['type']}" for r in self._conn.execute("SELECT c.key AS character,a.type FROM activity a JOIN character c ON c.id=a.character_id WHERE a.world_id=? AND a.status='active' ORDER BY c.key",(world_id,))]
        return SimulationReport(True,captured,captured,transitions,active_now)
