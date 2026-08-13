"""Plans canoniques de déplacement futurs, sans mutation implicite de position."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from .db import transaction
from .registry import _KEY_RE
from .util import Clock, new_uuid
from .world import SOURCE_ENGINE, SOURCE_SYSTEM, WorldEngine, _append_event


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
            "SELECT p.id,p.plan_kind,p.planned_at,p.status,p.provenance,c.key AS character_key,l.key AS target_location_key, "
            "r.outcome AS resolution_outcome,r.resolved_at,r.reason_code AS resolution_reason "
            "FROM character_location_plan p JOIN character c ON c.id=p.character_id "
            "JOIN location l ON l.id=p.target_location_id "
            "LEFT JOIN character_location_plan_resolution r ON r.world_id=p.world_id AND r.plan_id=p.id "
            "WHERE p.world_id=? AND p.id=?",
            (world_id, plan_id),
        ).fetchone()
        if row is None:
            raise LocationPlanError("plan introuvable", code="not_found")
        return dict(row)

    def list_for_character(self, world_id: int, character_key: str) -> list[dict[str, Any]]:
        character_key = self._key(character_key, "personnage")
        rows = self._conn.execute(
            "SELECT p.id,p.plan_kind,p.planned_at,p.status,p.provenance,c.key AS character_key,l.key AS target_location_key, "
            "r.outcome AS resolution_outcome,r.resolved_at,r.reason_code AS resolution_reason "
            "FROM character_location_plan p JOIN character c ON c.id=p.character_id "
            "JOIN location l ON l.id=p.target_location_id "
            "LEFT JOIN character_location_plan_resolution r ON r.world_id=p.world_id AND r.plan_id=p.id "
            "WHERE p.world_id=? AND c.key=? ORDER BY p.planned_at,p.id",
            (world_id, character_key),
        ).fetchall()
        return [dict(row) for row in rows]

    def due(self, world_id: int, at_time: str) -> list[dict[str, Any]]:
        """Retourne les engagements échus et encore sans résolution."""
        rows = self._conn.execute(
            "SELECT p.id,p.plan_kind,p.planned_at,p.provenance,c.key AS character_key, "
            "l.key AS target_location_key FROM character_location_plan p "
            "JOIN character c ON c.world_id=p.world_id AND c.id=p.character_id "
            "JOIN location l ON l.world_id=p.world_id AND l.id=p.target_location_id "
            "LEFT JOIN character_location_plan_resolution r ON r.world_id=p.world_id AND r.plan_id=p.id "
            "WHERE p.world_id=? AND p.status='planned' AND r.id IS NULL AND p.planned_at<=? "
            "ORDER BY p.planned_at,c.key,p.id",
            (world_id, at_time),
        ).fetchall()
        return [dict(row) for row in rows]

    def next_due_at(self, world_id: int, *, after: str, until: str) -> str | None:
        rows = self._conn.execute(
            "SELECT p.planned_at FROM character_location_plan p "
            "LEFT JOIN character_location_plan_resolution r ON r.world_id=p.world_id AND r.plan_id=p.id "
            "WHERE p.world_id=? AND p.status='planned' AND r.id IS NULL AND p.planned_at<=? "
            "ORDER BY p.planned_at,p.id",
            (world_id, until),
        ).fetchall()
        if not rows:
            return None
        return max(rows[0]["planned_at"], after, key=lambda value: value)

    def resolve(
        self, world_id: int, plan_id: int, *, outcome: str, resolved_at: str,
        reason_code: str, details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Ajoute une résolution idempotente sans muter le plan original."""
        if outcome not in {"fulfilled", "refused", "cancelled", "deferred"}:
            raise LocationPlanError("issue de résolution invalide")
        if not isinstance(reason_code, str) or not reason_code.strip():
            raise LocationPlanError("motif de résolution invalide")
        payload = details or {}
        if not isinstance(payload, dict):
            raise LocationPlanError("détails de résolution invalides")
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        with transaction(self._conn) as conn:
            plan = conn.execute(
                "SELECT id FROM character_location_plan WHERE world_id=? AND id=?",
                (world_id, plan_id),
            ).fetchone()
            if plan is None:
                raise LocationPlanError("plan introuvable", code="not_found")
            existing = conn.execute(
                "SELECT outcome,resolved_at,reason_code,details_json FROM character_location_plan_resolution "
                "WHERE world_id=? AND plan_id=?", (world_id, plan_id)
            ).fetchone()
            if existing is not None:
                return dict(existing)
            now = self._clock.now_iso()
            conn.execute(
                "INSERT INTO character_location_plan_resolution "
                "(public_id,world_id,plan_id,outcome,resolved_at,reason_code,details_json,created_at) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (new_uuid(), world_id, plan_id, outcome, resolved_at, reason_code, encoded, now),
            )
            _append_event(
                conn, world_id, SOURCE_ENGINE, "character_location_plan_resolved",
                {"plan_id": plan_id, "outcome": outcome, "reason_code": reason_code,
                 "details": payload}, occurred_at=resolved_at, recorded_at=now,
            )
            return {"outcome": outcome, "resolved_at": resolved_at,
                    "reason_code": reason_code, "details_json": encoded}
