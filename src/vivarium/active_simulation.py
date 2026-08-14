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
from .action_arbitration_runtime import ActionArbitrationService, CausalArbitrationBuilder
from .character import CharacterEngine, CharacterError
from .character_capabilities import is_sapient
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
from .location_plans import LocationPlanService
from .autonomy_cycle import RETRY_IDLE_SECONDS

_POST_BOUNDARY_IDLE_ORIGIN = "wo95_post_boundary_idle"

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
        self._conn,self._clock=conn,clock or Clock();self._activities=ActivityEngine(conn,clock=self._clock);self._physiology=SleepPhysiologyService(conn,clock=self._clock);self._arbitration=CausalArbitrationBuilder(conn,clock=self._clock);self._arbiter=ActionArbitrationService()
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
        plan_at = LocationPlanService(self._conn, clock=self._clock).next_due_at(
            world_id, after=state.anchor_at, until=limit
        )
        if plan_at is not None:
            candidates.append((plan_at, "location_plan"))
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
        reassess=self._arbitration.next_reassessment_at(world_id,character_key)
        if parse_iso(state.anchor_at)<parse_iso(reassess)<=parse_iso(limit):candidates.append((reassess,"arbitration_reassessment"))
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
    def _arbitrate(self,world_id:int,key:str,at:str)->None:
        current=self._arbitration.current_action_key(world_id,key)
        frame=self._arbitration.build_owner_backed(
            world_id,key,canonical_at=at,current_action_key=current
        )
        decision,validation=self._arbiter.execute(self._conn,frame,clock=self._clock)
        self._arbitration.audit_decision(frame,decision,validation=validation)

    def _ensure_post_boundary_idle(self, world_id: int, key: str, at: str) -> None:
        """Installe l'attente bornée lorsque la frontière n'a aucun successeur."""
        if not is_sapient(self._conn, world_id, key):
            return
        proposal_id = f"wo95_idle_{world_id}_{key}_{at}"
        with transaction(self._conn):
            if self._activities.activity_sheet(world_id, key) is not None:
                return
            existing = self._conn.execute(
                "SELECT 1 FROM canonical_event "
                "WHERE world_id=? AND event_type='activity_started' "
                "AND json_extract(payload,'$.character')=? "
                "AND json_extract(payload,'$.activity')='idle' "
                "AND json_extract(payload,'$.action_provenance.proposal_id')=? "
                "AND json_extract(payload,'$.action_provenance.origin')=? LIMIT 1",
                (world_id, key, proposal_id, _POST_BOUNDARY_IDLE_ORIGIN),
            ).fetchone()
            if existing is not None:
                return
            location = self._conn.execute(
                "SELECT l.key FROM character c JOIN location l ON l.id=c.current_location_id "
                "WHERE c.world_id=? AND c.key=?",
                (world_id, key),
            ).fetchone()
            if location is None:
                raise ActiveSimulationError(
                    "position canonique absente pour l'idle post-frontière",
                    code="canonical_position_missing",
                )
            self._activities.start_activity(
                world_id,
                key,
                "idle",
                location["key"],
                sim_now=at,
                duration_seconds=RETRY_IDLE_SECONDS,
                _reanchor_clock=False,
                action_provenance={
                    "proposal_id": proposal_id,
                    "origin": _POST_BOUNDARY_IDLE_ORIGIN,
                },
            )
    def _resolve_location_plans(self, world_id: int, key: str, at: str) -> None:
        plans = [p for p in LocationPlanService(self._conn, clock=self._clock).due(world_id, at)
                 if p["character_key"] == key]
        for plan in plans:
            service = LocationPlanService(self._conn, clock=self._clock)
            active = self._activities.activity_sheet(world_id, key)
            if active is not None and active["type"] == "idle":
                idle_origin = self._conn.execute(
                    "SELECT 1 FROM canonical_event "
                    "WHERE world_id=? AND event_type='activity_started' "
                    "AND occurred_at=? "
                    "AND json_extract(payload,'$.character')=? "
                    "AND json_extract(payload,'$.activity')='idle' "
                    "AND json_extract(payload,'$.planned_end_at')=? "
                    "AND json_extract(payload,'$.action_provenance.origin')=? LIMIT 1",
                    (world_id, active["started_at"], key, active["planned_end_at"],
                     _POST_BOUNDARY_IDLE_ORIGIN),
                ).fetchone()
                if idle_origin is not None:
                    self._activities.abort_activity(
                        world_id,
                        key,
                        sim_now=at,
                        reason_code="location_plan_due",
                        _reanchor_clock=False,
                    )
                    active = self._activities.activity_sheet(world_id, key)
            current = self._conn.execute(
                "SELECT l.key FROM character c JOIN location l ON l.id=c.current_location_id "
                "WHERE c.world_id=? AND c.key=?", (world_id, key)
            ).fetchone()
            if current is None:
                service.resolve(world_id, plan["id"], outcome="refused", resolved_at=at,
                                reason_code="character_not_found")
                continue
            if active is not None:
                service.resolve(world_id, plan["id"], outcome="refused", resolved_at=at,
                                reason_code="activity_active", details={"activity": active["type"]})
                continue
            if current["key"] == plan["target_location_key"]:
                service.resolve(world_id, plan["id"], outcome="fulfilled", resolved_at=at,
                                reason_code="already_at_target", details={"target": current["key"]})
                continue
            try:
                with transaction(self._conn) as c:
                    path = self._activities._path(world_id, current["key"], plan["target_location_key"])
                    engine = CharacterEngine(self._conn, clock=self._clock)
                    for step in path[1:]:
                        engine._move(c, world_id, key, step, sim_now=at)
                    service.resolve(world_id, plan["id"], outcome="fulfilled", resolved_at=at,
                                    reason_code="canonical_traversal", details={"path": path})
            except (CharacterError, ValueError) as exc:
                service.resolve(world_id, plan["id"], outcome="refused", resolved_at=at,
                                reason_code=getattr(exc, "code", "transition_rejected"),
                                details={"error": str(exc)})
    def _process(self,world_id:int,boundary:ActiveBoundary)->None:
        key,at=boundary.character_key,boundary.at;reasons=set(boundary.reasons)
        # Materialize exactly once under causes that held before this boundary.
        self._physiology.materialize_owner_backed(world_id,key,at)
        should_arbitrate=bool({"arbitration_reassessment","light_change"}&reasons)
        active=self._activities.activity_sheet(world_id,key)
        if "wake_stability_critical" in reasons and active is not None and self._sustained(world_id,active["type"]):
            if self._physiology.read_state(world_id,key).previous_stability_band=="critical":
                self._activities.abort_activity(world_id,key,sim_now=at,reason_code="wake_stability_critical",_reanchor_clock=False);should_arbitrate=True
        active=self._activities.activity_sheet(world_id,key)
        if active is not None and active["type"]=="sleep" and ({"sleep_checkpoint","sleep_hard_cap"}&reasons):
            before=active["id"];self._sleep_checkpoint(world_id,key,at);after=self._activities.activity_sheet(world_id,key);should_arbitrate=should_arbitrate or after is None or after.get("id")!=before
        active=self._activities.activity_sheet(world_id,key)
        if active is not None and active["type"]!="sleep" and "activity_end" in reasons:
            self._activities.advance_to(world_id,key,at,_reanchor_clock=False);should_arbitrate=True
        if "location_plan" in reasons:
            self._resolve_location_plans(world_id, key, at)
        if should_arbitrate:self._arbitrate(world_id,key,at)
        self._ensure_post_boundary_idle(world_id, key, at)
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
