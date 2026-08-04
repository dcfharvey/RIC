"""Simulateur déterministe (Sous-lot 3.2C).

Fait avancer les quatre habitantes de **borne canonique en borne canonique**
(jamais par minute). Chaque transition est une transaction atomique individuelle.
Une garde limite le nombre de transitions d'un `run_to` et, en cas de dépassement,
les transitions déjà validées sont conservées et le rapport explique la
progression partielle (sans prétendre avoir atteint l'heure cible).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from .activities import ActivityEngine, ActivityError, upgrade_dev_activities
from .character import CharacterEngine
from .db import connect_database
from .needs import NeedsEngine, upgrade_dev_needs
from .policy import DeterministicPolicy, PolicyContext
from .seed import SEED_PROFILES
from .spatial import GraphEngine
from .util import Clock, now_utc, parse_iso, to_iso
from .world import WorldEngine

NEED_KEYS = ("satiete", "repos", "energie", "hygiene")
ACTIVITY_TYPES = ("idle", "eat", "clean", "sleep", "rest")
DEFAULT_MAX_TRANSITIONS = 2000
DEFAULT_FALLBACK_LIMIT = 50


@dataclass
class SimulationReport:
    reached_target: bool
    target_time: str
    last_time: str
    transitions: int
    active_activities: list[str] = field(default_factory=list)


class SimulationLimitError(RuntimeError):
    """Garde de transitions atteinte : progression partielle, heure cible non atteinte."""

    def __init__(self, world_id, last_time, transitions, character, reason):
        self.world_id = world_id
        self.last_time = last_time
        self.transitions = transitions
        self.character = character
        self.reason = reason
        super().__init__(
            f"limite de transitions atteinte (dernière heure {last_time}, "
            f"{transitions} transitions, personnage {character}) : {reason}"
        )


class SimulationEngine:
    """Orchestration déterministe des décisions et activités."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()
        self._policy = DeterministicPolicy()
        self._ae = ActivityEngine(conn, clock=self._clock)

    # --- Constructions de contexte (données pures) ------------------------------

    def _world(self) -> WorldEngine:
        return WorldEngine(self._conn, clock=self._clock)

    def _characters_sorted(self, world_id: int) -> list[str]:
        rows = self._conn.execute(
            "SELECT key FROM character WHERE world_id = ? ORDER BY key", (world_id,)
        ).fetchall()
        return [r["key"] for r in rows]

    def _profile(self, world_id: int, char: str) -> dict[str, int]:
        row = self._conn.execute(
            "SELECT * FROM character_profile cp "
            "JOIN character ch ON ch.world_id = cp.world_id AND ch.id = cp.character_id "
            "WHERE ch.world_id = ? AND ch.key = ?",
            (world_id, char),
        ).fetchone()
        if row is None:
            return {k: (1000 if k in DeterministicPolicy.PROFILE_KEYS[:4] else 0 if k in (
                "rest_preference_milli",) else 0) for k in DeterministicPolicy.PROFILE_KEYS}
        return {k: row[k] for k in DeterministicPolicy.PROFILE_KEYS}

    def _effective_thresholds(self, world_id: int, char: str) -> dict[str, int]:
        prof = self._profile(world_id, char)
        base = {
            r["need_key"]: r["threshold_milli"]
            for r in self._conn.execute(
                "SELECT need_key, threshold_milli FROM need_definition WHERE world_id = ?",
                (world_id,),
            )
        }
        mult = {
            "satiete": prof["satiete_threshold_mult_milli"],
            "repos": prof["repos_threshold_mult_milli"],
            "energie": prof["energie_threshold_mult_milli"],
            "hygiene": prof["hygiene_threshold_mult_milli"],
        }
        return {k: (base[k] * mult[k]) // 1000 for k in NEED_KEYS}

    def _current_location(self, world_id: int, char: str) -> str:
        row = self._conn.execute(
            "SELECT l.key FROM character ch JOIN location l ON l.id = ch.current_location_id "
            "WHERE ch.world_id = ? AND ch.key = ?",
            (world_id, char),
        ).fetchone()
        return row["key"]

    def _accessible(self, world_id: int, char: str) -> dict[str, dict[str, int]]:
        cur = self._current_location(world_id, char)
        graph = GraphEngine(self._conn)
        out: dict[str, dict[str, int]] = {"idle": {cur: 0}}
        for atype in ACTIVITY_TYPES:
            if atype == "idle":
                continue
            dests: dict[str, int] = {}
            for key in self._ae.allowed_locations(world_id, atype):
                path = graph.find_path(world_id, cur, key)
                if path is not None:
                    dests[key] = len(path) - 1  # nombre d'arêtes (0 si déjà sur place)
            out[atype] = dests
        return out

    def _context(self, world_id: int, char: str, sim_now: str) -> PolicyContext:
        needs = {
            k: v["value_milli"]
            for k, v in NeedsEngine(self._conn, clock=self._clock)
            .derive_character(world_id, char, sim_now).items()
        }
        return PolicyContext(
            character_key=char,
            needs=needs,
            effective_thresholds=self._effective_thresholds(world_id, char),
            current_location=self._current_location(world_id, char),
            profile=self._profile(world_id, char),
            accessible=self._accessible(world_id, char),
        )

    # --- Décision + démarrage avec gardes --------------------------------------

    def _active_for(self, world_id: int, char: str) -> Any | None:
        return self._ae.activity_sheet(world_id, char)

    def _start_decision(self, world_id: int, char: str, sim_now: str, fallback: dict) -> bool:
        ctx = self._context(world_id, char, sim_now)
        dec = self._policy.decide(ctx)
        try:
            self._ae.start_activity(
                world_id, char, dec.intent.activity_type,
                dec.intent.target_location_key, sim_now=sim_now,
            )
        except ActivityError:
            current = ctx.current_location
            self._ae.start_activity(world_id, char, "idle", current, sim_now=sim_now)
            self._guard_fallback(world_id, char, ctx, dec, fallback)
            return True
        if dec.intent.activity_type == "idle" and dec.reason_code == "no_accessible_destination":
            self._guard_fallback(world_id, char, ctx, dec, fallback)
        else:
            self._reset_fallback(fallback, char)
        return True

    def _guard_fallback(self, world_id, char, ctx, dec, fallback):
        identity = (
            char,
            dec.trigger_need,
            dec.reason_code,
            frozenset(ctx.accessible.get("sleep", {}).keys()),
        )
        prev = fallback.get(char)
        if prev is not None and prev[0] == identity:
            fallback[char] = (identity, prev[1] + 1)
            if prev[1] + 1 > DEFAULT_FALLBACK_LIMIT:
                now = self._world().read_canonical_time(world_id)
                raise SimulationLimitError(
                    world_id, now, -1, char, "replis identiques répétés"
                )
        else:
            fallback[char] = (identity, 1)

    def _reset_fallback(self, fallback, char):
        fallback.pop(char, None)

    # --- Boucle run_to ---------------------------------------------------------

    def run_to(
        self,
        world_id: int,
        target_time: str,
        max_transitions: int = DEFAULT_MAX_TRANSITIONS,
    ) -> SimulationReport:
        if max_transitions <= 0:
            raise ValueError("max_transitions doit être strictement positif")
        chars = self._characters_sorted(world_id)
        transitions = 0
        fallback: dict[str, tuple] = {}
        current = self._world().read_canonical_time(world_id)
        last_time = current
        target = parse_iso(target_time)

        # décision initiale de chaque personnage
        for char in chars:
            if self._active_for(world_id, char) is None:
                self._start_decision(world_id, char, current, fallback)
                transitions += 1

        while True:
            if transitions >= max_transitions:
                raise SimulationLimitError(
                    world_id, last_time, transitions, chars[-1], "max_transitions"
                )
            active = self._active_all(world_id)
            if not active:
                for char in chars:
                    if self._active_for(world_id, char) is None:
                        self._start_decision(world_id, char, current, fallback)
                        transitions += 1
                active = self._active_all(world_id)
                if not active:
                    raise SimulationLimitError(
                        world_id, last_time, transitions, "?", "aucune activité possible"
                    )
            next_boundary = min(parse_iso(a["planned_end_at"]) for a in active)
            if next_boundary > target:
                # heure cible au milieu d'une activité : on progresse jusqu'à target
                for char in chars:
                    if self._active_for(world_id, char) is not None:
                        self._ae.advance_to(world_id, char, target_time)
                active_now = [
                    f"{a['character']}:{a['type']}"
                    for a in sorted(self._active_all(world_id), key=lambda x: x["character"])
                ]
                return SimulationReport(
                    reached_target=True, target_time=target_time, last_time=target_time,
                    transitions=transitions, active_activities=active_now,
                )

            # borne atteinte (certaines activités échues)
            ending = sorted(
                [a for a in active if parse_iso(a["planned_end_at"]) == next_boundary],
                key=lambda a: a["character"],
            )
            boundary_iso = to_iso(next_boundary)
            for a in ending:  # clôtures dans l'ordre stable de character.key
                self._ae.advance_to(world_id, a["character"], boundary_iso)
                transitions += 1
            current = boundary_iso
            last_time = boundary_iso
            # nouvelles décisions (toujours dans l'ordre stable)
            for char in chars:
                if self._active_for(world_id, char) is None:
                    self._start_decision(world_id, char, current, fallback)
                    transitions += 1

    def _active_all(self, world_id: int) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT a.id, a.type, a.planned_end_at, ch.key AS character "
            "FROM activity a JOIN character ch ON ch.world_id = a.world_id AND ch.id = a.character_id "
            "WHERE a.world_id = ? AND a.status = 'active'",
            (world_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def upgrade_dev_profiles(conn: sqlite3.Connection, world_id: int) -> int:
    """Profile neutre seedé pour chaque habitante (mise à niveau idempotente)."""
    existing = {
        r["key"]
        for r in conn.execute(
            "SELECT ch.key FROM character_profile cp JOIN character ch "
            "ON ch.world_id = cp.world_id AND ch.id = cp.character_id "
            "WHERE cp.world_id = ?",
            (world_id,),
        )
    }
    chars = conn.execute(
        "SELECT id, key FROM character WHERE world_id = ? ORDER BY key", (world_id,)
    ).fetchall()
    created = 0
    now = now_utc()
    for ch in chars:
        if ch["key"] in existing:
            continue
        defaults = SEED_PROFILES[0]
        conn.execute(
            "INSERT INTO character_profile (character_id, world_id, "
            "satiete_threshold_mult_milli, repos_threshold_mult_milli, "
            "energie_threshold_mult_milli, hygiene_threshold_mult_milli, "
            "rest_preference_milli, idle_tolerance_milli, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                ch["id"], world_id, defaults["satiete_threshold_mult_milli"],
                defaults["repos_threshold_mult_milli"],
                defaults["energie_threshold_mult_milli"],
                defaults["hygiene_threshold_mult_milli"],
                defaults["rest_preference_milli"], defaults["idle_tolerance_milli"], now,
            ),
        )
        created += 1
    return created
