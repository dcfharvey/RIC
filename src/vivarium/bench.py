"""Banc d'essai reproductible du moteur canonique.

Ce module est un outil de validation, jamais une seconde simulation ni un
chemin d'ecriture alternatif. Un :class:`BenchScenario` declare un monde de
depart, une horloge fixe et des actions explicites. Chaque execution cree sa
propre base SQLite temporaire, applique les migrations puis passe uniquement
par les API du moteur. La base temporaire est detruite a la fin du run.

Le LLM et l'interface n'interviennent pas ici. Le banc sert autant aux tests
automatises qu'aux futurs essais ``what if`` : un refus attendu reste visible
dans le rapport, tandis qu'un refus inattendu fait echouer le scenario.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Mapping

from .activities import ActivityEngine
from .character import CharacterEngine
from .db import connect_database
from .injury import InjuryEngine
from .migrations import ensure_schema
from .repro import (
    canonical_state_digest,
    materialization_chain_audit,
    raw_canonical_event_log,
    semantic_event_digest,
    structural_event_audit,
)
from .simulation import DEFAULT_MAX_TRANSITIONS, SimulationEngine, SimulationReport
from .spatial import GraphEngine
from .util import Clock, parse_iso, to_iso
from .world import WorldEngine


class BenchScenarioError(ValueError):
    """Scenario declaratif invalide ou resultat different de son contrat."""


class BenchClock(Clock):
    """Horloge strictement controlee, avancee par les bornes du scenario."""

    def __init__(self, start_at: str) -> None:
        self._now = parse_iso(start_at)

    def now(self) -> datetime:
        return self._now

    def now_iso(self) -> str:
        return to_iso(self._now)

    def advance_to(self, target_at: str) -> None:
        target = parse_iso(target_at)
        if target < self._now:
            raise BenchScenarioError("l'horloge du banc ne peut pas reculer")
        self._now = target


@dataclass(frozen=True)
class BenchAction:
    """Une injection autorisee, situee a une heure canonique precise.

    ``expected`` rend les refus testables sans les dissimuler. Les seules
    actions admises sont volontairement listees dans ``_apply_action`` : un
    scenario ne peut donc pas appeler arbitrairement SQLite ou du code Python.
    """

    at: str
    kind: str
    params: Mapping[str, Any] = field(default_factory=dict)
    expected: Literal["applied", "refused"] = "applied"


@dataclass(frozen=True)
class BenchScenario:
    """Description complete d'une experience deterministe isolee."""

    name: str
    start_at: str
    target_at: str
    actions: tuple[BenchAction, ...] = ()
    world_name: str = "Banc d'essai temporaire"
    seed: bool = True
    max_transitions: int = DEFAULT_MAX_TRANSITIONS


@dataclass(frozen=True)
class BenchActionResult:
    at: str
    kind: str
    outcome: Literal["applied", "refused"]
    error_type: str | None = None
    error_code: str | None = None
    error_message: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "at": self.at,
            "kind": self.kind,
            "outcome": self.outcome,
            "error_type": self.error_type,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }


@dataclass(frozen=True)
class BenchRunReport:
    """Trace non canonique, JSON-serialisable, d'une execution de banc."""

    scenario_name: str
    schema_version: int
    start_at: str
    target_at: str
    final_time: str
    simulation_segments: tuple[SimulationReport, ...]
    action_results: tuple[BenchActionResult, ...]
    canonical_state: dict[str, Any]
    semantic_events: list[tuple]
    raw_events: list[tuple]
    structural_audit: dict[str, Any]
    materialization_findings: list[tuple[int, str, str]]
    sqlite_integrity: tuple[str, ...]
    foreign_key_violations: tuple[tuple, ...]

    @property
    def refusals(self) -> tuple[BenchActionResult, ...]:
        return tuple(result for result in self.action_results if result.outcome == "refused")

    @property
    def is_healthy(self) -> bool:
        return (
            all(self.structural_audit[key] for key in (
                "seq_continuous_1_to_n", "no_holes", "no_duplicate_seq",
                "occurred_at_monotonic", "payloads_valid_json", "causality_valid",
            ))
            and not self.materialization_findings
            and self.sqlite_integrity == ("ok",)
            and not self.foreign_key_violations
        )

    def as_dict(self) -> dict[str, Any]:
        """Projection stable et lisible, utilisable par un test ou une future UI."""
        return {
            "scenario_name": self.scenario_name,
            "schema_version": self.schema_version,
            "start_at": self.start_at,
            "target_at": self.target_at,
            "final_time": self.final_time,
            "simulation_segments": [
                {
                    "reached_target": segment.reached_target,
                    "target_time": segment.target_time,
                    "last_time": segment.last_time,
                    "transitions": segment.transitions,
                    "active_activities": segment.active_activities,
                }
                for segment in self.simulation_segments
            ],
            "actions": [result.as_dict() for result in self.action_results],
            "refusals": [result.as_dict() for result in self.refusals],
            "canonical_state": self.canonical_state,
            "semantic_events": self.semantic_events,
            "raw_events": self.raw_events,
            "structural_audit": self.structural_audit,
            "materialization_findings": self.materialization_findings,
            "sqlite_integrity": list(self.sqlite_integrity),
            "foreign_key_violations": [list(row) for row in self.foreign_key_violations],
            "healthy": self.is_healthy,
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), ensure_ascii=False, sort_keys=True, indent=2)


@dataclass(frozen=True)
class BenchComparison:
    """Comparaison explicite de deux experiences, sans masquer les differences."""

    same_canonical_state: bool
    same_semantic_events: bool
    same_refusals: bool
    left_healthy: bool
    right_healthy: bool

    @property
    def identical(self) -> bool:
        return (
            self.same_canonical_state
            and self.same_semantic_events
            and self.same_refusals
            and self.left_healthy
            and self.right_healthy
        )


def _validate_scenario(scenario: BenchScenario) -> None:
    if not isinstance(scenario.name, str) or not scenario.name.strip():
        raise BenchScenarioError("le nom du scenario est obligatoire")
    if not isinstance(scenario.world_name, str) or not scenario.world_name.strip():
        raise BenchScenarioError("le nom du monde temporaire est obligatoire")
    if not isinstance(scenario.seed, bool):
        raise BenchScenarioError("seed doit etre un booleen")
    if not isinstance(scenario.max_transitions, int) or isinstance(scenario.max_transitions, bool):
        raise BenchScenarioError("max_transitions doit etre un entier")
    if scenario.max_transitions <= 0:
        raise BenchScenarioError("max_transitions doit etre strictement positif")
    start = parse_iso(scenario.start_at)
    target = parse_iso(scenario.target_at)
    if target < start:
        raise BenchScenarioError("target_at ne peut pas preceder start_at")
    previous = start
    for action in scenario.actions:
        if not isinstance(action, BenchAction):
            raise BenchScenarioError("actions doit contenir uniquement des BenchAction")
        at = parse_iso(action.at)
        if at < start or at > target:
            raise BenchScenarioError("une action doit etre dans l'intervalle du scenario")
        if at < previous:
            raise BenchScenarioError("les actions doivent etre declarees dans l'ordre temporel")
        previous = at
        if action.expected not in {"applied", "refused"}:
            raise BenchScenarioError("expected doit valoir 'applied' ou 'refused'")
        if not isinstance(action.params, Mapping):
            raise BenchScenarioError("params doit etre un mapping")


def _require_params(action: BenchAction, required: set[str], optional: set[str] = set()) -> dict[str, Any]:
    params = dict(action.params)
    missing = required - set(params)
    unexpected = set(params) - required - optional
    if missing or unexpected:
        raise BenchScenarioError(
            f"parametres invalides pour {action.kind!r}: manquants={sorted(missing)}, "
            f"inattendus={sorted(unexpected)}"
        )
    return params


def _apply_action(conn: sqlite3.Connection, clock: BenchClock, world_id: int, action: BenchAction) -> None:
    """Execute une action autorisee par son API publique canonique."""
    world = WorldEngine(conn, clock=clock)
    if action.kind == "pause_world":
        _require_params(action, set())
        world.pause_world(world_id)
    elif action.kind == "resume_world":
        _require_params(action, set())
        world.resume_world(world_id)
    elif action.kind == "rename_world":
        params = _require_params(action, {"name"})
        world.rename_world(world_id, params["name"])
    elif action.kind == "move_character":
        params = _require_params(action, {"character_key", "target_location_key"})
        CharacterEngine(conn, clock=clock).move_character(
            world_id, params["character_key"], params["target_location_key"]
        )
    elif action.kind == "start_activity":
        params = _require_params(
            action, {"character_key", "activity_type", "location_key"}, {"duration_seconds"}
        )
        ActivityEngine(conn, clock=clock).start_activity(
            world_id,
            params["character_key"],
            params["activity_type"],
            params["location_key"],
            sim_now=action.at,
            duration_seconds=params.get("duration_seconds"),
        )
    elif action.kind == "abort_activity":
        params = _require_params(action, {"character_key"})
        ActivityEngine(conn, clock=clock).abort_activity(world_id, params["character_key"])
    elif action.kind == "inflict_injury":
        params = _require_params(
            action, {"character_key", "severity_milli"}, {"injury_kind", "description"}
        )
        InjuryEngine(conn, clock=clock).inflict_injury(
            world_id,
            params["character_key"],
            params["severity_milli"],
            injury_kind=params.get("injury_kind", "mobility"),
            description=params.get("description", ""),
            sim_now=action.at,
        )
    elif action.kind == "add_link":
        params = _require_params(action, {"from_location_key", "to_location_key"}, {"bidirectional", "kind"})
        GraphEngine(conn, clock=clock).add_link(
            world_id,
            params["from_location_key"],
            params["to_location_key"],
            bidirectional=params.get("bidirectional", True),
            kind=params.get("kind", "door"),
        )
    elif action.kind == "remove_link":
        params = _require_params(
            action, {"from_location_key", "to_location_key"}, {"bidirectional"}
        )
        GraphEngine(conn, clock=clock).remove_link(
            world_id,
            params["from_location_key"],
            params["to_location_key"],
            bidirectional=params.get("bidirectional", True),
        )
    else:
        raise BenchScenarioError(f"action de banc inconnue : {action.kind!r}")


def _result_for_action(conn: sqlite3.Connection, clock: BenchClock, world_id: int, action: BenchAction) -> BenchActionResult:
    try:
        _apply_action(conn, clock, world_id, action)
    except BenchScenarioError:
        raise
    except Exception as exc:
        code = getattr(exc, "code", None)
        result = BenchActionResult(
            at=action.at,
            kind=action.kind,
            outcome="refused",
            error_type=type(exc).__name__,
            error_code=code if isinstance(code, str) else None,
            error_message=str(exc),
        )
        if action.expected != "refused":
            raise BenchScenarioError(
                f"action {action.kind!r} refusee de maniere inattendue a {action.at}: {exc}"
            ) from exc
        return result
    if action.expected == "refused":
        raise BenchScenarioError(
            f"action {action.kind!r} appliquee alors qu'un refus etait attendu a {action.at}"
        )
    return BenchActionResult(at=action.at, kind=action.kind, outcome="applied")


def _run_segment(
    conn: sqlite3.Connection, clock: BenchClock, world_id: int, target_at: str, max_transitions: int
) -> SimulationReport:
    """Avance le simulateur jusqu'a une borne, a partir de l'horloge fixee."""
    clock.advance_to(target_at)
    return SimulationEngine(conn, clock=clock).run_to(world_id, target_at, max_transitions)


def run_bench(scenario: BenchScenario) -> BenchRunReport:
    """Execute un scenario dans une base jetable, sans toucher aux mondes existants."""
    _validate_scenario(scenario)
    clock = BenchClock(scenario.start_at)
    with tempfile.TemporaryDirectory(prefix="vivarium-bench-") as directory:
        db_path = Path(directory) / "scenario.sqlite"
        conn = connect_database(db_path)
        try:
            schema_version = ensure_schema(conn)
            world = WorldEngine(conn, clock=clock).init_world(
                name=scenario.world_name, seed=scenario.seed
            )
            world_id = world["id"]
            segments: list[SimulationReport] = []
            results: list[BenchActionResult] = []
            for action in scenario.actions:
                engine = WorldEngine(conn, clock=clock)
                current_at = engine.read_canonical_time(world_id)
                if action.at != current_at:
                    if engine.get_world(world_id)["status"] == "paused":
                        raise BenchScenarioError(
                            "une action future ne peut pas etre atteinte pendant une pause ; "
                            "reprendre le monde a la meme heure canonique avant de progresser"
                        )
                    segments.append(_run_segment(conn, clock, world_id, action.at, scenario.max_transitions))
                else:
                    clock.advance_to(action.at)
                results.append(_result_for_action(conn, clock, world_id, action))
            engine = WorldEngine(conn, clock=clock)
            if scenario.target_at != engine.read_canonical_time(world_id):
                if engine.get_world(world_id)["status"] == "paused":
                    raise BenchScenarioError(
                        "la cible ne peut pas etre atteinte pendant une pause ; "
                        "reprendre le monde avant de progresser"
                    )
                segments.append(_run_segment(conn, clock, world_id, scenario.target_at, scenario.max_transitions))
            else:
                clock.advance_to(scenario.target_at)
            structural = structural_event_audit(conn, world_id)
            materialization = materialization_chain_audit(conn, world_id)
            integrity = tuple(row[0] for row in conn.execute("PRAGMA integrity_check"))
            fk = tuple(tuple(row) for row in conn.execute("PRAGMA foreign_key_check"))
            return BenchRunReport(
                scenario_name=scenario.name,
                schema_version=schema_version,
                start_at=scenario.start_at,
                target_at=scenario.target_at,
                final_time=WorldEngine(conn, clock=clock).read_canonical_time(world_id),
                simulation_segments=tuple(segments),
                action_results=tuple(results),
                canonical_state=canonical_state_digest(conn, world_id),
                semantic_events=semantic_event_digest(conn, world_id),
                raw_events=raw_canonical_event_log(conn, world_id),
                structural_audit=structural,
                materialization_findings=materialization,
                sqlite_integrity=integrity,
                foreign_key_violations=fk,
            )
        finally:
            conn.close()


def compare_bench_runs(left: BenchRunReport, right: BenchRunReport) -> BenchComparison:
    """Compare deux rapports selon les preuves pertinentes, pas les UUIDs."""
    return BenchComparison(
        same_canonical_state=left.canonical_state == right.canonical_state,
        same_semantic_events=left.semantic_events == right.semantic_events,
        same_refusals=tuple(result.as_dict() for result in left.refusals)
        == tuple(result.as_dict() for result in right.refusals),
        left_healthy=left.is_healthy,
        right_healthy=right.is_healthy,
    )
