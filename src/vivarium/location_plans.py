"""Plans canoniques de déplacement futurs, sans mutation implicite de position."""

from __future__ import annotations

import sqlite3
from typing import Any

from .db import transaction
from .registry import _KEY_RE
from .util import Clock, new_uuid
from .world import SOURCE_SYSTEM, WorldEngine, _append_event


class LocationPlanError(ValueError):
    """Plan de lieu invalide ou incompatible."""

    def __init__(self, message: str, *, code: str = "invalid_location_plan") -> None:
        super().__init__(message)
        self.code = code


class LocationPlanService:
    """Propriétaire générique des plans de lieu append-only."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def _key(value: Any, label: str) -> str:
        if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
            raise LocationPlanError(f"{label} invalide")
        return value

    def plan(
        self,
        world_id: int,
        character_key: str,
        target_location_key: str,
        planned_at: str,
        *,
        plan_kind: str = "return",
        provenance: str = "bootstrap.t0.v1",
    ) -> dict[str, Any]:
        if not isinstance(world_id, int) or isinstance(world_id, bool) or world_id < 1:
            raise LocationPlanError("monde invalide")
        character_key = self._key(character_key, "personnage")
        target_location_key = self._key(target_location_key, "lieu cible")
        if plan_kind not in {"return", "arrival", "relocation"}:
            raise LocationPlanError("type de plan invalide")
        if not isinstance(planned_at, str) or not planned_at:
            raise LocationPlanError("heure planifiée invalide")
        if not isinstance(provenance, str) or not provenance.strip():
            raise LocationPlanError("provenance invalide")
        with transaction(self._conn) as conn:
            character = conn.execute(
                "SELECT id FROM character WHERE world_id=? AND key=?",
                (world_id, character_key),
            ).fetchone()
            location = conn.execute(
                "SELECT id FROM location WHERE world_id=? AND key=?",
                (world_id, target_location_key),
            ).fetchone()
            if character is None or location is None:
                raise LocationPlanError("personnage ou lieu introuvable", code="not_found")
            now = self._clock.now_iso()
            canonical_at = WorldEngine(conn, clock=self._clock).read_canonical_time(world_id)
            cur = conn.execute(
                "INSERT INTO character_location_plan "
                "(public_id,world_id,character_id,target_location_id,plan_kind,planned_at,status,provenance,created_at) "
                "VALUES (?,?,?,?,?,?,?, ?,?)",
                (new_uuid(), world_id, character["id"], location["id"], plan_kind, planned_at, "planned", provenance, now),
            )
            _append_event(
                conn, world_id, SOURCE_SYSTEM, "character_location_plan_created",
                {"character": character_key, "target_location": target_location_key,
                 "plan_kind": plan_kind, "planned_at": planned_at, "provenance": provenance},
                occurred_at=canonical_at, recorded_at=now,
            )
            plan_id = cur.lastrowid
        return self.read(world_id, plan_id)

    def read(self, world_id: int, plan_id: int) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT p.id,p.plan_kind,p.planned_at,p.status,p.provenance,c.key AS character_key,l.key AS target_location_key "
            "FROM character_location_plan p JOIN character c ON c.id=p.character_id "
            "JOIN location l ON l.id=p.target_location_id WHERE p.world_id=? AND p.id=?",
            (world_id, plan_id),
        ).fetchone()
        if row is None:
            raise LocationPlanError("plan introuvable", code="not_found")
        return dict(row)

    def list_for_character(self, world_id: int, character_key: str) -> list[dict[str, Any]]:
        character_key = self._key(character_key, "personnage")
        rows = self._conn.execute(
            "SELECT p.id,p.plan_kind,p.planned_at,p.status,p.provenance,c.key AS character_key,l.key AS target_location_key "
            "FROM character_location_plan p JOIN character c ON c.id=p.character_id "
            "JOIN location l ON l.id=p.target_location_id WHERE p.world_id=? AND c.key=? ORDER BY p.planned_at,p.id",
            (world_id, character_key),
        ).fetchall()
        return [dict(row) for row in rows]
