"""Faits initiaux partagés, immuables et lisibles par la future cognition."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from .db import transaction
from .util import Clock, new_uuid
from .world import SOURCE_SYSTEM, WorldEngine, append_event as _append_event


class InitialContextError(ValueError):
    """Contexte initial invalide ou déjà fixé."""


class InitialContextService:
    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def _world_id(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise InitialContextError("monde invalide")
        return value

    @staticmethod
    def _facts(value: Any) -> tuple[dict[str, Any], str]:
        if not isinstance(value, dict) or not value:
            raise InitialContextError("faits initiaux invalides")
        if any(not isinstance(key, str) or not key for key in value):
            raise InitialContextError("faits initiaux invalides")
        try:
            encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise InitialContextError("faits initiaux invalides") from exc
        return json.loads(encoded), encoded

    def set_shared_facts(self, world_id: Any, facts: Any) -> dict[str, Any]:
        """Fixe une unique base de connaissance commune à la naissance du monde."""
        world_id = self._world_id(world_id)
        facts, facts_json = self._facts(facts)
        with transaction(self._conn) as conn:
            if conn.execute("SELECT 1 FROM worlds WHERE id = ?", (world_id,)).fetchone() is None:
                raise InitialContextError("monde introuvable")
            if conn.execute("SELECT 1 FROM world_initial_context WHERE world_id = ?", (world_id,)).fetchone() is not None:
                raise InitialContextError("contexte initial déjà fixé")
            canonical_now = WorldEngine(conn, clock=self._clock).read_canonical_time(world_id)
            now = self._clock.now_iso()
            conn.execute(
                "INSERT INTO world_initial_context (world_id, public_id, facts_json, created_at) VALUES (?, ?, ?, ?)",
                (world_id, new_uuid(), facts_json, now),
            )
            _append_event(
                conn, world_id, SOURCE_SYSTEM, "world_initial_context_set",
                {"fact_keys": sorted(facts)}, occurred_at=canonical_now, recorded_at=now,
            )
        return self.shared_facts(world_id)

    def shared_facts(self, world_id: Any) -> dict[str, Any]:
        world_id = self._world_id(world_id)
        row = self._conn.execute(
            "SELECT facts_json FROM world_initial_context WHERE world_id = ?", (world_id,)
        ).fetchone()
        if row is None:
            raise InitialContextError("contexte initial introuvable")
        return json.loads(row["facts_json"])
