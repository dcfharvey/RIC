"""Instances canonique de connecteurs et leurs états simples."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from .db import transaction
from .registry import KEY_RE as _KEY_RE
from .util import Clock
from .world import SOURCE_OWNER, WorldEngine, append_event as _append_event

AVAILABLE = "available"
CLOSED = "closed"
BLOCKED = "blocked"
_STATES = frozenset({AVAILABLE, CLOSED, BLOCKED})


class ConnectorError(ValueError):
    """Etat ou usage d'un connecteur invalide, sans écriture partielle."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class WorldConnectorService:
    """Lit et modifie les connecteurs instanciés par un blueprint."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def _world_id(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ConnectorError("monde invalide", code="invalid_world")
        return value

    @staticmethod
    def _key(value: Any, label: str) -> str:
        if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
            raise ConnectorError(f"{label} invalide", code="invalid_key")
        return value

    def _row(self, world_id: int, connector_key: str) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT c.id, c.key, c.archetype_version, c.directions, c.state, "
            "a.key AS archetype_key, av.contract_json, f.key AS from_key, t.key AS to_key "
            "FROM world_connector c JOIN environment_archetype a ON a.id = c.archetype_id "
            "JOIN environment_archetype_version av ON av.archetype_id = c.archetype_id "
            "AND av.version = c.archetype_version "
            "JOIN location f ON f.id = c.from_location_id JOIN location t ON t.id = c.to_location_id "
            "WHERE c.world_id = ? AND c.key = ?",
            (world_id, connector_key),
        ).fetchone()
        if row is None:
            raise ConnectorError("connecteur introuvable", code="connector_not_found")
        return row

    @staticmethod
    def _sheet(row: sqlite3.Row) -> dict[str, Any]:
        contract = json.loads(row["contract_json"])
        return {
            "key": row["key"], "archetype": row["archetype_key"],
            "archetype_version": row["archetype_version"], "from": row["from_key"],
            "to": row["to_key"], "directions": row["directions"], "state": row["state"],
            "traversal_modes": contract["traversal_modes"], "features": contract["features"],
        }

    def connector_sheet(self, world_id: Any, connector_key: Any) -> dict[str, Any]:
        world_id = self._world_id(world_id)
        connector_key = self._key(connector_key, "cle de connecteur")
        return self._sheet(self._row(world_id, connector_key))

    def list_connectors(self, world_id: Any) -> list[dict[str, Any]]:
        world_id = self._world_id(world_id)
        rows = self._conn.execute(
            "SELECT key FROM world_connector WHERE world_id = ? ORDER BY key", (world_id,)
        ).fetchall()
        return [self.connector_sheet(world_id, row["key"]) for row in rows]

    def set_state(self, world_id: Any, connector_key: Any, state: Any) -> dict[str, Any]:
        """Change un état fini, avec une trace et sans sémantique inventée."""
        world_id = self._world_id(world_id)
        connector_key = self._key(connector_key, "cle de connecteur")
        if state not in _STATES:
            raise ConnectorError("etat de connecteur invalide", code="invalid_state")
        with transaction(self._conn) as conn:
            row = self._row(world_id, connector_key)
            if row["state"] == state:
                raise ConnectorError("connecteur deja dans cet etat", code="state_unchanged")
            contract = json.loads(row["contract_json"])
            if state == CLOSED and "closable" not in contract["features"]:
                raise ConnectorError("ce connecteur ne peut pas etre ferme", code="connector_not_closable")
            try:
                canonical_now = WorldEngine(conn, clock=self._clock).read_canonical_time(world_id)
            except KeyError as exc:
                raise ConnectorError("monde introuvable", code="world_not_found") from exc
            recorded_now = self._clock.now_iso()
            conn.execute("UPDATE world_connector SET state = ? WHERE id = ?", (state, row["id"]))
            _append_event(
                conn, world_id, SOURCE_OWNER, "connector_state_changed",
                {"connector": connector_key, "from_state": row["state"], "to_state": state},
                occurred_at=canonical_now, recorded_at=recorded_now,
            )
        return self.connector_sheet(world_id, connector_key)

    def can_traverse(self, world_id: Any, connector_key: Any, from_key: Any, to_key: Any) -> bool:
        """Lecture pure de permission structurelle d'un connecteur.

        La validation complète d'une action de personnage viendra avec
        `TraversalEngine`; ici, seuls l'état et le sens du connecteur comptent.
        """
        world_id = self._world_id(world_id)
        connector_key = self._key(connector_key, "cle de connecteur")
        from_key = self._key(from_key, "origine")
        to_key = self._key(to_key, "destination")
        row = self._row(world_id, connector_key)
        if row["state"] != AVAILABLE:
            return False
        if row["from_key"] == from_key and row["to_key"] == to_key:
            return True
        return row["directions"] == "bidirectional" and row["from_key"] == to_key and row["to_key"] == from_key
