"""Cycle de vie persistant du runtime et gel sûr de l'horloge hors ligne.

La session est un registre opérationnel mutable (battement et fermeture), pas
une seconde vérité du monde. Ses transitions de cycle de vie sont recopiées
dans un journal append-only. L'horloge canonique reste l'autorité temporelle.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .db import transaction
from .util import Clock, new_uuid, parse_iso, to_iso
from .world import WorldEngine


@dataclass(frozen=True)
class RuntimeSessionStart:
    session_id: int
    public_id: str
    canonical_at: str
    recovered_session_id: int | None


class RuntimeSessionService:
    """Ouvre, ponctue et ferme une session d'exécution d'un monde."""

    def __init__(self, conn: sqlite3.Connection, *, clock: Clock | None = None):
        self._conn = conn
        self._clock = clock or Clock()

    def _now_iso(self) -> str:
        return to_iso(self._clock.now())

    @staticmethod
    def _latest_durable_canonical(conn: sqlite3.Connection, world_id: int) -> str:
        values: list[str] = []
        clock = conn.execute(
            "SELECT simulated_now FROM canonical_clock WHERE world_id = ?", (world_id,)
        ).fetchone()
        if clock is None:
            raise KeyError(f"monde introuvable : {world_id}")
        values.append(clock["simulated_now"])
        event = conn.execute(
            "SELECT MAX(occurred_at) AS at FROM canonical_event WHERE world_id = ?",
            (world_id,),
        ).fetchone()
        if event and event["at"]:
            values.append(event["at"])
        session = conn.execute(
            "SELECT last_canonical_at FROM runtime_session "
            "WHERE world_id = ? ORDER BY id DESC LIMIT 1",
            (world_id,),
        ).fetchone()
        if session:
            values.append(session["last_canonical_at"])
        return to_iso(max(parse_iso(value) for value in values))

    def start(self, world_id: int) -> RuntimeSessionStart:
        """Démarre sans rattrapage hors ligne et récupère un crash éventuel."""
        now = self._now_iso()
        with transaction(self._conn) as conn:
            open_row = conn.execute(
                "SELECT id FROM runtime_session WHERE world_id = ? AND stopped_at IS NULL",
                (world_id,),
            ).fetchone()
            canonical_at = self._latest_durable_canonical(conn, world_id)
            recovered_id = None
            if open_row is not None:
                recovered_id = open_row["id"]
                conn.execute(
                    "UPDATE runtime_session SET stopped_at = ?, stop_kind = 'crash_recovered', "
                    "last_heartbeat_at = ?, last_canonical_at = ? WHERE id = ?",
                    (now, now, canonical_at, recovered_id),
                )
                self._append_event(
                    conn, world_id, recovered_id, "crash_recovered", canonical_at, now
                )
            conn.execute(
                "UPDATE canonical_clock SET simulated_now = ?, real_updated_at = ?, "
                "runtime_state = 'running' WHERE world_id = ?",
                (canonical_at, now, world_id),
            )
            public_id = new_uuid()
            cur = conn.execute(
                "INSERT INTO runtime_session "
                "(public_id, world_id, started_at, last_heartbeat_at, last_canonical_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (public_id, world_id, now, now, canonical_at),
            )
            session_id = int(cur.lastrowid)
            self._append_event(conn, world_id, session_id, "started", canonical_at, now)
        return RuntimeSessionStart(session_id, public_id, canonical_at, recovered_id)

    def heartbeat(self, session_id: int) -> str:
        """Matérialise un point de reprise technique, sans événement canonique."""
        canonical_at = WorldEngine(self._conn, clock=self._clock).read_canonical_time(
            self._world_id(session_id)
        )
        now = self._now_iso()
        with transaction(self._conn) as conn:
            changed = conn.execute(
                "UPDATE runtime_session SET last_heartbeat_at = ?, last_canonical_at = ? "
                "WHERE id = ? AND stopped_at IS NULL",
                (now, canonical_at, session_id),
            ).rowcount
            if changed != 1:
                raise RuntimeError("session runtime absente ou déjà fermée")
        return canonical_at

    def stop(self, session_id: int, *, protective: bool = False) -> str:
        """Gèle l'horloge exactement au moment d'un arrêt maîtrisé."""
        world_id = self._world_id(session_id)
        canonical_at = WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id)
        now = self._now_iso()
        stop_kind = "protective" if protective else "clean"
        event_kind = "protective_stop" if protective else "clean_stop"
        with transaction(self._conn) as conn:
            changed = conn.execute(
                "UPDATE runtime_session SET stopped_at = ?, stop_kind = ?, "
                "last_heartbeat_at = ?, last_canonical_at = ? "
                "WHERE id = ? AND stopped_at IS NULL",
                (now, stop_kind, now, canonical_at, session_id),
            ).rowcount
            if changed != 1:
                raise RuntimeError("session runtime absente ou déjà fermée")
            conn.execute(
                "UPDATE canonical_clock SET simulated_now = ?, real_updated_at = ?, "
                "runtime_state = 'stopped' WHERE world_id = ?",
                (canonical_at, now, world_id),
            )
            self._append_event(conn, world_id, session_id, event_kind, canonical_at, now)
        return canonical_at

    def _world_id(self, session_id: int) -> int:
        row = self._conn.execute(
            "SELECT world_id FROM runtime_session WHERE id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"session runtime introuvable : {session_id}")
        return int(row["world_id"])

    @staticmethod
    def _append_event(
        conn: sqlite3.Connection,
        world_id: int,
        session_id: int,
        event_kind: str,
        canonical_at: str,
        recorded_at: str,
    ) -> None:
        conn.execute(
            "INSERT INTO runtime_session_event "
            "(public_id, world_id, session_id, event_kind, canonical_at, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (new_uuid(), world_id, session_id, event_kind, canonical_at, recorded_at),
        )
