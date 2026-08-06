"""Validation canonique d'une traversée de personnage par connecteur."""

from __future__ import annotations

import sqlite3
from typing import Any

from .character import CharacterEngine, CharacterError
from .connectors import AVAILABLE, BLOCKED, CLOSED, ConnectorError, WorldConnectorService
from .db import transaction
from .registry import _KEY_RE
from .util import Clock


class TraversalError(ValueError):
    """Tentative de traversée refusée avec un code stable pour la cognition."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class TraversalEngine:
    """Transforme une tentative de franchissement en déplacement canonique."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def _world_id(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise TraversalError("monde invalide", code="invalid_world")
        return value

    @staticmethod
    def _key(value: Any, label: str) -> str:
        if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
            raise TraversalError(f"{label} invalide", code="invalid_key")
        return value

    def _assert_traversable(
        self, world_id: int, character_key: str, connector_key: str, target_key: str
    ) -> dict[str, Any]:
        character = self._conn.execute(
            "SELECT l.key AS location_key FROM character ch JOIN location l ON l.id = ch.current_location_id "
            "WHERE ch.world_id = ? AND ch.key = ?", (world_id, character_key)
        ).fetchone()
        if character is None:
            raise TraversalError("personnage introuvable", code="character_not_found")
        try:
            connector = WorldConnectorService(self._conn, clock=self._clock).connector_sheet(world_id, connector_key)
        except ConnectorError as exc:
            raise TraversalError(str(exc), code=exc.code) from exc
        current = character["location_key"]
        if current != connector["from"] and current != connector["to"]:
            raise TraversalError("personnage absent des extremites du connecteur", code="character_not_at_connector")
        if current == connector["to"] and connector["directions"] != "bidirectional":
            raise TraversalError("connecteur interdit dans ce sens", code="connector_wrong_direction")
        expected_target = connector["to"] if current == connector["from"] else connector["from"]
        if target_key != expected_target:
            raise TraversalError("destination incompatible avec ce connecteur", code="connector_destination_mismatch")
        if connector["state"] == CLOSED:
            raise TraversalError("connecteur ferme", code="connector_closed")
        if connector["state"] == BLOCKED:
            raise TraversalError("connecteur bloque", code="connector_blocked")
        if connector["state"] != AVAILABLE:
            raise TraversalError("connecteur indisponible", code="connector_unavailable")
        edge = self._conn.execute(
            "SELECT 1 FROM location_link ll JOIN world_connector c ON c.id = ll.connector_id "
            "JOIN location f ON f.id = ll.from_location_id JOIN location t ON t.id = ll.to_location_id "
            "WHERE ll.world_id = ? AND c.key = ? AND f.key = ? AND t.key = ?",
            (world_id, connector_key, current, target_key),
        ).fetchone()
        if edge is None:
            raise TraversalError("connecteur incoherent avec la topologie", code="connector_topology_mismatch")
        return {"from": current, "to": target_key, "connector": connector_key}

    def preview(self, world_id: Any, character_key: Any, connector_key: Any, target_key: Any) -> dict[str, Any]:
        """Prévisualise une traversée sans écriture, utile au planificateur futur."""
        world_id = self._world_id(world_id)
        character_key = self._key(character_key, "cle de personnage")
        connector_key = self._key(connector_key, "cle de connecteur")
        target_key = self._key(target_key, "destination")
        try:
            return {"allowed": True, "reason": None, **self._assert_traversable(world_id, character_key, connector_key, target_key)}
        except TraversalError as exc:
            return {"allowed": False, "reason": exc.code, "connector": connector_key, "to": target_key}

    def traverse_character(
        self, world_id: Any, character_key: Any, connector_key: Any, target_key: Any
    ) -> dict[str, Any]:
        """Franchit un connecteur réel ou annule entièrement la tentative."""
        world_id = self._world_id(world_id)
        character_key = self._key(character_key, "cle de personnage")
        connector_key = self._key(connector_key, "cle de connecteur")
        target_key = self._key(target_key, "destination")
        with transaction(self._conn) as conn:
            self._assert_traversable(world_id, character_key, connector_key, target_key)
            try:
                result = CharacterEngine(conn, clock=self._clock)._move(
                    conn, world_id, character_key, target_key, connector_key=connector_key
                )
            except CharacterError as exc:
                raise TraversalError(str(exc), code=exc.code or "character_move_refused") from exc
        return result
