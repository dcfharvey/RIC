"""Disposable deterministic patch generator for WO88D/E."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def insert_before(path: str, marker: str, content: str) -> None:
    replace_once(path, marker, content + marker)


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Activity transitions: a catch-up scheduler may suppress intermediate clock
# re-anchoring; events still keep their exact occurred_at. Public defaults stay
# unchanged for all existing callers.
# ---------------------------------------------------------------------------
replace_once(
    "src/vivarium/activities.py",
    '''    def advance_to(self, world_id: int, character_key: str, at_time: str) -> dict[str, Any] | None:\n''',
    '''    def advance_to(\n        self, world_id: int, character_key: str, at_time: str, *,\n        _reanchor_clock: bool = True,\n    ) -> dict[str, Any] | None:\n''',
)
replace_once(
    "src/vivarium/activities.py",
    '''            return self._advance_to_active(world_id, character_key, at_time)\n''',
    '''            return self._advance_to_active(\n                world_id, character_key, at_time, _reanchor_clock=_reanchor_clock\n            )\n''',
)
# Legacy path: preserve behavior by conditionalizing its only final reanchor.
replace_once(
    "src/vivarium/activities.py",
    '''            # avancement de l'horloge canonique à l'instant atteint\n            self._world()._advance_clock(world_id, at_time, c)\n        return self.activity_sheet(world_id, character_key)\n\n    def _advance_to_active(\n        self, world_id: int, character_key: str, at_time: str\n''',
    '''            # avancement de l'horloge canonique à l'instant atteint\n            if _reanchor_clock:\n                self._world()._advance_clock(world_id, at_time, c)\n        return self.activity_sheet(world_id, character_key)\n\n    def _advance_to_active(\n        self, world_id: int, character_key: str, at_time: str, *,\n        _reanchor_clock: bool = True,\n''',
)
# Active path has four possible reanchors; guard all exact strings in that method.
active_old = '''                self._world()._advance_clock(world_id, target_iso, c)\n                return self.activity_sheet(world_id, character_key)\n'''
active_new = '''                if _reanchor_clock:\n                    self._world()._advance_clock(world_id, target_iso, c)\n                return self.activity_sheet(world_id, character_key)\n'''
replace_once("src/vivarium/activities.py", active_old, active_new)
replace_once(
    "src/vivarium/activities.py",
    '''                self._world()._advance_clock(world_id, boundary, c)\n                if parse_iso(at_time) > parse_iso(boundary):\n''',
    '''                if _reanchor_clock:\n                    self._world()._advance_clock(world_id, boundary, c)\n                if parse_iso(at_time) > parse_iso(boundary):\n''',
)
replace_once(
    "src/vivarium/activities.py",
    '''                    self._world()._advance_clock(world_id, at_time, c)\n            else:\n''',
    '''                    if _reanchor_clock:\n                        self._world()._advance_clock(world_id, at_time, c)\n            else:\n''',
)
replace_once(
    "src/vivarium/activities.py",
    '''                self._world()._advance_clock(world_id, at_time, c)\n        return self.activity_sheet(world_id, character_key)\n\n    def abort_activity(\n''',
    '''                if _reanchor_clock:\n                    self._world()._advance_clock(world_id, at_time, c)\n        return self.activity_sheet(world_id, character_key)\n\n    def abort_activity(\n''',
)
# Abort route.
replace_once(
    "src/vivarium/activities.py",
    '''        reason_code: str | None = None,\n    ) -> dict[str, Any] | None:\n''',
    '''        reason_code: str | None = None,\n        _reanchor_clock: bool = True,\n    ) -> dict[str, Any] | None:\n''',
)
replace_once(
    "src/vivarium/activities.py",
    '''                world_id, character_key, sim_now=sim_now, reason_code=reason_code\n            )\n''',
    '''                world_id, character_key, sim_now=sim_now, reason_code=reason_code,\n                _reanchor_clock=_reanchor_clock,\n            )\n''',
)
# legacy abort final reanchor
replace_once(
    "src/vivarium/activities.py",
    '''            # avancement de l'horloge canonique à l'instant d'abandon\n            self._world()._advance_clock(world_id, canonical, c)\n        return self.activity_sheet(world_id, character_key)\n\n    def _abort_activity_active(\n''',
    '''            # avancement de l'horloge canonique à l'instant d'abandon\n            if _reanchor_clock:\n                self._world()._advance_clock(world_id, canonical, c)\n        return self.activity_sheet(world_id, character_key)\n\n    def _abort_activity_active(\n''',
)
replace_once(
    "src/vivarium/activities.py",
    '''        reason_code: str | None = None,\n    ) -> dict[str, Any] | None:\n        from .sleep_physiology import SleepPhysiologyService\n''',
    '''        reason_code: str | None = None,\n        _reanchor_clock: bool = True,\n    ) -> dict[str, Any] | None:\n        from .sleep_physiology import SleepPhysiologyService\n''',
)
replace_once(
    "src/vivarium/activities.py",
    '''            self._world()._advance_clock(world_id, canonical, c)\n        return self.activity_sheet(world_id, character_key)\n\n    # --- Frontieres de sommeil synthetiques''',
    '''            if _reanchor_clock:\n                self._world()._advance_clock(world_id, canonical, c)\n        return self.activity_sheet(world_id, character_key)\n\n    # --- Frontieres de sommeil synthetiques''',
)
# checkpoint completion
replace_once(
    "src/vivarium/activities.py",
    '''    def complete_sleep_from_checkpoint(\n        self, world_id: int, character_key: str, *, at_time: str\n    ) -> dict[str, Any] | None:\n''',
    '''    def complete_sleep_from_checkpoint(\n        self, world_id: int, character_key: str, *, at_time: str,\n        _reanchor_clock: bool = True,\n    ) -> dict[str, Any] | None:\n''',
)
replace_once(
    "src/vivarium/activities.py",
    '''            self._world()._advance_clock(world_id, at, c)\n        return self.activity_sheet(world_id, character_key)\n\n    def _active_row''',
    '''            if _reanchor_clock:\n                self._world()._advance_clock(world_id, at, c)\n        return self.activity_sheet(world_id, character_key)\n\n    def _active_row''',
)

# ---------------------------------------------------------------------------
# Owner-backed light boundary helper. The scheduler splits before any change of
# schedule/profile so materialize_owner_backed always sees constant causes.
# ---------------------------------------------------------------------------
insert_before(
    "src/vivarium/sleep_physiology.py",
    "    def project_synthetic(\n",
    '''    def next_light_boundary_owner_backed(\n        self, world_id: Any, character_key: Any, *, until: Any\n    ) -> str | None:\n        """Retourne la prochaine frontière lumineuse après l'ancre physiologique.\n\n        Couvre le changement de segment quotidien et toute nouvelle assignment\n        de calendrier/profil du lieu courant. La méthode est pure.\n        """\n        world = self._world_id(world_id)\n        character = _key(character_key, field="personnage")\n        state = self.read_state(world, character)\n        anchor = _at(state.anchor_at)\n        limit = _at(until)\n        if parse_iso(limit) <= parse_iso(anchor):\n            return None\n        source = self.resolve_light_source_owner_backed(\n            world, character, at_time=anchor\n        )\n        schedule = source.assignment_metadata["schedule_assignment"]["schedule"]\n        segments = schedule.get("segments") if isinstance(schedule, Mapping) else None\n        if not isinstance(segments, list) or not segments:\n            raise SleepPhysiologyError("calendrier lumineux invalide", code="invalid_light_schedule")\n        moment = parse_iso(anchor).astimezone(timezone.utc)\n        second = moment.hour * 3600 + moment.minute * 60 + moment.second\n        candidates: list[str] = []\n        for segment in segments:\n            if not isinstance(segment, Mapping):\n                continue\n            start, end = segment.get("start_second"), segment.get("end_second")\n            if isinstance(start, int) and isinstance(end, int) and start <= second < end:\n                day_start = moment.replace(hour=0, minute=0, second=0, microsecond=0)\n                boundary = day_start + timedelta(seconds=end)\n                if boundary <= moment:\n                    boundary += timedelta(days=1)\n                candidates.append(to_iso(boundary))\n                break\n        location = self._conn.execute(\n            "SELECT l.id FROM character c JOIN location l ON l.id=c.current_location_id "\n            "WHERE c.world_id=? AND c.key=?", (world, character)\n        ).fetchone()\n        if location is None:\n            raise SleepPhysiologyError("position canonique absente", code="canonical_position_missing")\n        future_schedule = self._conn.execute(\n            "SELECT effective_at FROM world_light_schedule_assignment "\n            "WHERE world_id=? AND effective_at>? ORDER BY effective_at,id LIMIT 1",\n            (world, anchor),\n        ).fetchone()\n        future_location = self._conn.execute(\n            "SELECT effective_at FROM world_location_light_assignment "\n            "WHERE world_id=? AND location_id=? AND effective_at>? ORDER BY effective_at,id LIMIT 1",\n            (world, location["id"], anchor),\n        ).fetchone()\n        for row in (future_schedule, future_location):\n            if row is not None:\n                candidates.append(row["effective_at"])\n        eligible = [value for value in candidates if parse_iso(anchor) < parse_iso(value) <= parse_iso(limit)]\n        return None if not eligible else to_iso(min(parse_iso(value) for value in eligible))\n\n''',
)

# ---------------------------------------------------------------------------
# Active decision frame: no SimulationEngine/PolicyContext/legacy motivation.
# Physiological cues remain derived and non-canonical, with explicit owner.
# ---------------------------------------------------------------------------
replace_once(
    "src/vivarium/decision.py",
    '''from .simulation import SimulationEngine\n''',
    '''from .simulation import SimulationEngine\nfrom .sleep_physiology import SleepPhysiologyFoundationService, SleepPhysiologyService\n''',
)
replace_once(
    "src/vivarium/decision.py",
    ''' def build_current(self,world_id:Any,character_key:Any)->DecisionFrame:\n  return self.build(world_id,character_key,SimulationEngine(self._conn).policy_context(world_id,character_key))\n''',
    ''' def build_current(self,world_id:Any,character_key:Any)->DecisionFrame:\n  if SleepPhysiologyFoundationService(self._conn).system_status(world_id)=="active":\n   goals=GoalService(self._conn).goals(world_id,character_key);active=GoalService(self._conn).active_intention(world_id,character_key)\n   physiology=SleepPhysiologyService(self._conn);state=physiology.read_state(world_id,character_key)\n   source=physiology.resolve_light_source_owner_backed(world_id,character_key,at_time=state.anchor_at)\n   projection=physiology.project_synthetic(world_id,character_key,source.source)\n   sleep_pressure=max(0,min(1000,round(projection.propensity.sleep_propensity*1000)))\n   recovery=max(0,min(1000,round((1.0-state.regulation.physical_capacity)*1000)))\n   motives=[]\n   if sleep_pressure:\n    motives.append(MotiveCandidate(character_key,"motive_sleep_regulation","physiology_owner_backed","sleep_regulation","regulate",sleep_pressure,sleep_pressure,sleep_pressure,("sleep",)))\n   if recovery:\n    motives.append(MotiveCandidate(character_key,"motive_physical_capacity","physiology_owner_backed","physical_capacity","restore",recovery,recovery,recovery,("rest",)))\n   motives.sort(key=lambda item:(-item.urgency_milli,-item.pressure_milli,item.candidate_key));motives=tuple(motives)\n   if active is not None:return DecisionFrame(character_key,active,goals,motives,"active_intention",active["intention_key"])\n   if motives:return DecisionFrame(character_key,None,goals,motives,"physiology",motives[0].candidate_key)\n   candidates=[goal for goal in goals if goal["status"] in {"candidate","adopted"}]\n   if candidates:\n    best=max(candidates,key=lambda goal:(goal["urgency_milli"],goal["importance_milli"],goal["goal_key"]));return DecisionFrame(character_key,None,goals,motives,"goal",best["goal_key"])\n   return DecisionFrame(character_key,None,goals,motives,None,None)\n  return self.build(world_id,character_key,SimulationEngine(self._conn).policy_context(world_id,character_key))\n''',
)

# ---------------------------------------------------------------------------
# Active scheduler. It never imports DeterministicPolicy or MotivationService.
# ---------------------------------------------------------------------------
write(
    "src/vivarium/active_simulation.py",
    '''"""Scheduler du runtime physiologique actif (WO88D/E).\n\nLe scheduler avance uniquement de frontière causale en frontière causale. Il\nne lit jamais ``repos``/``energie`` et ne reconstruit jamais un historique à\npartir d'un résultat. Les transitions intermédiaires gardent leur ``occurred_at``\nexact; l'horloge dérivée est réancrée une seule fois à la cible capturée afin\nde préserver le temps réel lors d'un rattrapage.\n"""\nfrom __future__ import annotations\n\nimport sqlite3\nfrom dataclasses import dataclass\nfrom datetime import timedelta\nfrom typing import Any, Literal\n\nfrom .activities import ActivityEngine\nfrom .db import transaction\nfrom .injury import InjuryEngine\nfrom .needs import NeedsEngine\nfrom .simulation import SimulationReport\nfrom .sleep_physiology import SleepPhysiologyFoundationService, SleepPhysiologyService\nfrom .sleep_termination import (\n    SleepTerminationFoundationService, SleepTerminationError, evaluate_sleep_checkpoint,\n)\nfrom .util import Clock, parse_iso, to_iso\nfrom .world import WorldEngine\n\n_ACTIVE_NEEDS=frozenset({"satiete","hygiene"})\n\n@dataclass(frozen=True)\nclass ActiveBoundary:\n    at:str\n    character_key:str\n    reasons:tuple[str,...]\n\nclass ActiveSimulationError(RuntimeError):\n    def __init__(self,message:str,*,code:str):super().__init__(message);self.code=code\n\nclass ActiveSimulationEngine:\n    def __init__(self,conn:sqlite3.Connection,clock:Clock|None=None)->None:\n        self._conn,self._clock=conn,clock or Clock();self._activities=ActivityEngine(conn,clock=self._clock);self._physiology=SleepPhysiologyService(conn,clock=self._clock)\n    def _require_active(self,world_id:int)->None:\n        if SleepPhysiologyFoundationService(self._conn,clock=self._clock).system_status(world_id)!="active":\n            raise ActiveSimulationError("scheduler actif exige physiology=active",code="physiology_not_active")\n    def _characters(self,world_id:int)->tuple[str,...]:\n        return tuple(r["key"] for r in self._conn.execute("SELECT key FROM character WHERE world_id=? ORDER BY key",(world_id,)))\n    def _sustained(self,world_id:int,activity_type:str)->bool:\n        row=self._conn.execute("SELECT requires_sustained_wakefulness FROM activity_definition WHERE world_id=? AND activity_type=?",(world_id,activity_type)).fetchone();return bool(row and row[0])\n    def next_boundary(self,world_id:int,character_key:str,*,until:str)->ActiveBoundary|None:\n        self._require_active(world_id);limit=to_iso(parse_iso(until));state=self._physiology.read_state(world_id,character_key);candidates=[]\n        active=self._activities.activity_sheet(world_id,character_key)\n        if active is not None:\n            if active["type"]=="sleep":\n                cp=self._activities.sleep_checkpoint(world_id,character_key)\n                if cp is None or cp["status"]!="active":raise ActiveSimulationError("sommeil actif sans checkpoint",code="sleep_checkpoint_missing")\n                for value,reason in ((cp["next_reassessment_at"],"sleep_checkpoint"),(cp["hard_cap_at"],"sleep_hard_cap")):\n                    if parse_iso(state.anchor_at)<parse_iso(value)<=parse_iso(limit):candidates.append((value,reason))\n            elif parse_iso(state.anchor_at)<parse_iso(active["planned_end_at"])<=parse_iso(limit):\n                candidates.append((active["planned_end_at"],"activity_end"))\n        light=self._physiology.next_light_boundary_owner_backed(world_id,character_key,until=limit)\n        if light is not None:candidates.append((light,"light_change"))\n        if active is not None and active["type"] not in {"sleep","rest"} and self._sustained(world_id,active["type"]):\n            horizon=min([parse_iso(limit)]+[parse_iso(v) for v,_ in candidates if parse_iso(v)>parse_iso(state.anchor_at)])\n            source=self._physiology.resolve_light_source_owner_backed(world_id,character_key,at_time=state.anchor_at)\n            critical=self._physiology.next_critical_boundary_synthetic(world_id,character_key,source.source,to_iso(horizon))\n            if critical is not None and parse_iso(critical)>parse_iso(state.anchor_at):candidates.append((critical,"wake_stability_critical"))\n        if not candidates:return None\n        first=min(parse_iso(v) for v,_ in candidates);at=to_iso(first)\n        return ActiveBoundary(at,character_key,tuple(sorted(r for v,r in candidates if parse_iso(v)==first)))\n    def is_due(self,world_id:int,target_time:str)->bool:\n        self._require_active(world_id);target=to_iso(parse_iso(target_time))\n        return any(self.next_boundary(world_id,key,until=target) is not None for key in self._characters(world_id))\n    def _passive_to(self,world_id:int,key:str,at:str)->None:\n        self._physiology.materialize_owner_backed(world_id,key,at)\n        with transaction(self._conn) as c:\n            NeedsEngine(self._conn,clock=self._clock).materialize_selected_needs(world_id,key,at,"active_passive",_ACTIVE_NEEDS,_conn=c)\n            InjuryEngine(self._conn,clock=self._clock)._materialize_injury_sim(world_id,key,at,"passive",_conn=c)\n    def _sleep_checkpoint(self,world_id:int,key:str,at:str)->None:\n        self._physiology.materialize_owner_backed(world_id,key,at)\n        cp=self._activities.sleep_checkpoint(world_id,key)\n        if cp is None or cp["status"]!="active":raise ActiveSimulationError("checkpoint actif absent",code="sleep_checkpoint_missing")\n        projection=self._physiology.project_wake_viability_owner_backed(world_id,key,at_time=at)\n        elapsed=int((parse_iso(at)-parse_iso(cp["started_at"])).total_seconds());termination=SleepTerminationFoundationService(self._conn,clock=self._clock);policy=termination.world_policy(world_id)\n        evaluation=evaluate_sleep_checkpoint(policy,elapsed_seconds=elapsed,wake_viability_milli=projection.value_milli,previous_band=cp["previous_band"],external_wake_accessible=False)\n        if evaluation.completion_eligible:\n            termination.authorize_completion_owner_backed(world_id,key,at_time=at)\n            self._activities.complete_sleep_from_checkpoint(world_id,key,at_time=at,_reanchor_clock=False);return\n        if evaluation.hard_cap_reached:\n            self._activities.report_sleep_hard_cap(world_id,key,at_time=at);return\n        assert evaluation.next_reassessment_after_seconds is not None\n        self._activities.advance_sleep_checkpoint(world_id,key,at_time=at,next_reassessment_at=to_iso(parse_iso(at)+timedelta(seconds=evaluation.next_reassessment_after_seconds)),previous_band=evaluation.band)\n    def _process(self,world_id:int,boundary:ActiveBoundary)->None:\n        key,at=boundary.character_key,boundary.at;reasons=set(boundary.reasons)\n        # Materialize exactly once under causes that held before this boundary.\n        self._physiology.materialize_owner_backed(world_id,key,at)\n        active=self._activities.activity_sheet(world_id,key)\n        if "wake_stability_critical" in reasons and active is not None and self._sustained(world_id,active["type"]):\n            if self._physiology.read_state(world_id,key).previous_stability_band=="critical":\n                self._activities.abort_activity(world_id,key,sim_now=at,reason_code="wake_stability_critical",_reanchor_clock=False);return\n        active=self._activities.activity_sheet(world_id,key)\n        if active is not None and active["type"]=="sleep" and ({"sleep_checkpoint","sleep_hard_cap"}&reasons):\n            self._sleep_checkpoint(world_id,key,at);return\n        if active is not None and active["type"]!="sleep" and "activity_end" in reasons:\n            self._activities.advance_to(world_id,key,at,_reanchor_clock=False)\n    def run_to(self,world_id:int,target_time:str,max_transitions:int=1000)->SimulationReport:\n        self._require_active(world_id)\n        if not isinstance(max_transitions,int) or isinstance(max_transitions,bool) or max_transitions<1:raise ActiveSimulationError("borne invalide",code="invalid_transition_limit")\n        captured=to_iso(max(parse_iso(target_time),parse_iso(WorldEngine(self._conn,clock=self._clock).read_canonical_time(world_id))))\n        transitions=0;chars=self._characters(world_id)\n        while True:\n            boundaries=[b for key in chars if (b:=self.next_boundary(world_id,key,until=captured)) is not None]\n            if not boundaries:break\n            first=min(parse_iso(b.at) for b in boundaries);due=sorted((b for b in boundaries if parse_iso(b.at)==first),key=lambda b:b.character_key)\n            for boundary in due:\n                if transitions>=max_transitions:raise ActiveSimulationError("limite de transitions active atteinte",code="transition_limit")\n                self._process(world_id,boundary);transitions+=1\n        # Final materialization at the captured real-time target. No historical\n        # decision is invented while catching up.\n        for key in chars:\n            active=self._activities.activity_sheet(world_id,key)\n            if active is None:self._passive_to(world_id,key,captured)\n            else:self._activities.advance_to(world_id,key,captured,_reanchor_clock=False)\n        with transaction(self._conn) as c:WorldEngine(self._conn,clock=self._clock)._advance_clock(world_id,captured,c)\n        active_now=[f"{r['character']}:{r['type']}" for r in self._conn.execute("SELECT c.key AS character,a.type FROM activity a JOIN character c ON c.id=a.character_id WHERE a.world_id=? AND a.status='active' ORDER BY c.key",(world_id,))]\n        return SimulationReport(True,captured,captured,transitions,active_now)\n''',
)

# ---------------------------------------------------------------------------
# MVPRuntime routes active physiology exclusively through ActiveSimulationEngine.
# ---------------------------------------------------------------------------
replace_once(
    "src/vivarium/mvp_runtime.py",
    '''from .simulation import SimulationReport, SimulationEngine\n''',
    '''from .simulation import SimulationReport, SimulationEngine\nfrom .active_simulation import ActiveSimulationEngine\nfrom .sleep_physiology import SleepPhysiologyFoundationService\n''',
)
replace_once(
    "src/vivarium/mvp_runtime.py",
    '''            simulation = SimulationEngine(self._conn, clock=self._clock).run_to(\n                self.world_id, target, max_transitions=self._max_transitions\n            )\n''',
    '''            if self._physiology_active():\n                simulation = ActiveSimulationEngine(self._conn, clock=self._clock).run_to(\n                    self.world_id, target, max_transitions=self._max_transitions\n                )\n            else:\n                simulation = SimulationEngine(self._conn, clock=self._clock).run_to(\n                    self.world_id, target, max_transitions=self._max_transitions\n                )\n''',
)
insert_before(
    "src/vivarium/mvp_runtime.py",
    "    def _simulation_due(self, target_time: str) -> bool:\n",
    '''    def _physiology_active(self) -> bool:\n        return SleepPhysiologyFoundationService(\n            self._conn, clock=self._clock\n        ).system_status(self.world_id) == "active"\n\n''',
)
replace_once(
    "src/vivarium/mvp_runtime.py",
    '''        row = self._conn.execute(\n            "SELECT MIN(planned_end_at) AS next_end FROM activity "\n''',
    '''        if self._physiology_active():\n            return ActiveSimulationEngine(\n                self._conn, clock=self._clock\n            ).is_due(self.world_id, target_time)\n        row = self._conn.execute(\n            "SELECT MIN(planned_end_at) AS next_end FROM activity "\n''',
)

# ---------------------------------------------------------------------------
# World pause: active worlds materialize the correct owners, never repos/energie.
# ---------------------------------------------------------------------------
replace_once(
    "src/vivarium/world.py",
    '''            from .needs import NeedsEngine  # import local pour éviter un cycle\n\n            needs = NeedsEngine(self._conn, clock=self._clock)\n            char_keys = [\n''',
    '''            from .needs import NeedsEngine  # import local pour éviter un cycle\n            from .sleep_physiology import SleepPhysiologyFoundationService, SleepPhysiologyService\n            from .injury import InjuryEngine\n\n            needs = NeedsEngine(self._conn, clock=self._clock)\n            physiology_active = SleepPhysiologyFoundationService(\n                self._conn, clock=self._clock\n            ).system_status(world_id) == "active"\n            char_keys = [\n''',
)
replace_once(
    "src/vivarium/world.py",
    '''            for key in char_keys:\n                needs.materialize_character_needs(\n                    world_id, key, frozen, "pause", _conn=c\n                )\n''',
    '''            for key in char_keys:\n                if physiology_active:\n                    SleepPhysiologyService(self._conn, clock=self._clock).materialize_owner_backed(\n                        world_id, key, frozen\n                    )\n                    needs.materialize_selected_needs(\n                        world_id, key, frozen, "pause", frozenset({"satiete", "hygiene"}), _conn=c\n                    )\n                    InjuryEngine(self._conn, clock=self._clock)._materialize_injury_sim(\n                        world_id, key, frozen, "passive", _conn=c\n                    )\n                else:\n                    needs.materialize_character_needs(\n                        world_id, key, frozen, "pause", _conn=c\n                    )\n''',
)

write(
    "tests/test_active_runtime_cutover.py",
    '''"""WO88D/E : scheduler actif, catch-up et falsification legacy."""\nfrom dataclasses import asdict\nfrom datetime import datetime,timezone,timedelta\n\nimport pytest\n\nfrom vivarium.activities import ActivityEngine\nfrom vivarium.active_simulation import ActiveSimulationEngine\nfrom vivarium.circadian_model import calibration_profiles\nfrom vivarium.db import connect_database,transaction\nfrom vivarium.decision import DecisionFrameService\nfrom vivarium.integration_world import IntegrationWorldService\nfrom vivarium.migrations import ensure_schema\nfrom vivarium.simulation import SimulationEngine\nfrom vivarium.sleep_physiology import ADDITIVE_MODEL_KEY,SleepPhysiologyFoundationService,SleepPhysiologyService,V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY\nfrom vivarium.sleep_termination import SleepTerminationFoundationService\nfrom vivarium.util import Clock,to_iso\nfrom vivarium.world import WorldEngine\n\nT0_DT=datetime(2026,8,12,21,0,tzinfo=timezone.utc);T0=to_iso(T0_DT)\nclass FakeClock(Clock):\n def __init__(self):self.current=T0_DT\n def now(self):return self.current\n\ndef profile():\n p=asdict(calibration_profiles()["human_reference_candidate.v1"]);[p.pop(k) for k in ("profile_key","version","evidence_class")];return {"model_key":ADDITIVE_MODEL_KEY,"parameters":p}\n\ndef active_world():\n clock=FakeClock();conn=connect_database(":memory:");ensure_schema(conn);wid=IntegrationWorldService(conn,clock=clock).create_initial_world()["id"];f=SleepPhysiologyFoundationService(conn,clock=clock)\n f.register_light_schedule("runtime.day.v1",1,{"schema_version":1,"segments":[{"start_second":0,"end_second":75660,"environmental_light_milli":50000},{"start_second":75660,"end_second":86400,"environmental_light_milli":0}]});f.register_location_light_profile("runtime.indoor.v1",1,25000,{"kind":"indoor"});f.register_biology_profile("runtime.human.v1",1,"human_reference",profile())\n f.register_physical_capacity_policy("runtime.p.v1",1,{"schema_version":1,"activity_cost_per_hour_milli":{"none":3600,"light":7200,"moderate":10800,"vigorous":18000},"minimum_capacity_milli":{"none":0,"light":10000,"moderate":25000,"vigorous":45000},"traversal_cost_per_edge_milli":250,"recovery_per_hour_milli":{"rest":7200,"sleep":10800}},"test")\n f.assign_light_schedule(wid,"runtime.day.v1",1,T0,"test")\n for r in conn.execute("SELECT key FROM location WHERE world_id=?",(wid,)):f.assign_location_light_profile(wid,r["key"],"runtime.indoor.v1",1,T0,"test")\n for r in conn.execute("SELECT key FROM character WHERE world_id=?",(wid,)):f.assign_biology_profile(wid,r["key"],"runtime.human.v1",1,"test")\n f.assign_physical_capacity_policy(wid,"runtime.p.v1",1,"test")\n for typ,load in V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY.items():conn.execute("UPDATE activity_definition SET physical_load_class=? WHERE world_id=? AND activity_type=?",(load,wid,typ))\n term=SleepTerminationFoundationService(conn,clock=clock);term.register_policy("runtime.sleep.v1",1,{"schema_version":1,"checkpoint_interval_seconds":30,"hard_cap_seconds":300,"wake_admissible_enter_milli":65000,"wake_admissible_exit_milli":55000},"test");term.assign_policy(wid,"runtime.sleep.v1",1,"test");f.prepare_world(wid,ADDITIVE_MODEL_KEY,1,"test")\n with transaction(conn) as tx:\n  tx.execute("UPDATE world_physiology_system SET status='active',activated_at=?,activated_by=?,updated_at=? WHERE world_id=?",(T0,"test",T0,wid))\n  for r in tx.execute("SELECT id FROM character WHERE world_id=?",(wid,)):\n   cid=r["id"];tx.execute("INSERT INTO sleep_regulation_state (public_id,world_id,character_id,model_key,model_version,homeostatic_load_milli,circadian_phase_milli,anchor_at,updated_at) VALUES (?,?,?,?,1,50000,250000,?,?)",(f"r{cid}",wid,cid,ADDITIVE_MODEL_KEY,T0,T0));tx.execute("INSERT INTO physical_capacity_state (public_id,world_id,character_id,capacity_milli,rate_remainder,anchor_at,updated_at) VALUES (?,?,?,70000,0,?,?)",(f"p{cid}",wid,cid,T0,T0));tx.execute("INSERT INTO sleep_wake_hysteresis_state (public_id,world_id,character_id,previous_band,anchor_at,updated_at) VALUES (?,?,?,'fragile',?,?)",(f"h{cid}",wid,cid,T0,T0));tx.execute("INSERT INTO sleep_regulation_precision_state (public_id,world_id,character_id,homeostatic_load_residue,circadian_phase_residue,anchor_at,updated_at) VALUES (?,?,?,0,0,?,?)",(f"x{cid}",wid,cid,T0,T0))\n return conn,wid,clock\n\ndef legacy_snapshot(conn,wid):return tuple(tuple(r) for r in conn.execute("SELECT character_id,need_key,value_milli,rate_remainder,anchor_at FROM need_state WHERE world_id=? AND need_key IN ('repos','energie') ORDER BY character_id,need_key",(wid,)))\n\ndef test_active_decision_frame_never_calls_legacy_policy_context(monkeypatch):\n conn,wid,clock=active_world()\n try:\n  monkeypatch.setattr(SimulationEngine,"policy_context",lambda *a,**k:(_ for _ in ()).throw(AssertionError("legacy")))\n  frame=DecisionFrameService(conn).build_current(wid,"character_1");assert frame.character_key=="character_1";assert all(m.target_need in {"sleep_regulation","physical_capacity"} for m in frame.motives)\n finally:conn.close()\n\ndef test_catchup_crosses_activity_end_and_light_boundary_without_losing_real_time():\n conn,wid,clock=active_world()\n try:\n  act=ActivityEngine(conn,clock=clock);act.start_activity(wid,"character_1","gaming","salon",sim_now=T0)\n  # make the activity end before the light boundary and the wall target after both\n  conn.execute("UPDATE activity SET planned_end_at=? WHERE world_id=? AND character_id=(SELECT id FROM character WHERE world_id=? AND key='character_1') AND status='active'",(to_iso(T0_DT+timedelta(seconds=30)),wid,wid))\n  clock.current=T0_DT+timedelta(seconds=90);target=to_iso(clock.current);before=legacy_snapshot(conn,wid)\n  report=ActiveSimulationEngine(conn,clock=clock).run_to(wid,target)\n  assert report.reached_target and report.last_time==target;assert WorldEngine(conn,clock=clock).read_canonical_time(wid)==target\n  assert all(SleepPhysiologyService(conn,clock=clock).read_state(wid,k).anchor_at==target for k in ("character_1","character_2","character_3","character_4"));assert legacy_snapshot(conn,wid)==before\n finally:conn.close()\n\ndef test_active_runtime_falsifies_legacy_simulation_use(monkeypatch):\n conn,wid,clock=active_world()\n try:\n  monkeypatch.setattr(SimulationEngine,"run_to",lambda *a,**k:(_ for _ in ()).throw(AssertionError("legacy run")));clock.current=T0_DT+timedelta(seconds=10);before=legacy_snapshot(conn,wid);ActiveSimulationEngine(conn,clock=clock).run_to(wid,to_iso(clock.current));assert legacy_snapshot(conn,wid)==before\n finally:conn.close()\n''',
)
