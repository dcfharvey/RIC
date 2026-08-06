"""Possession physique canonique : un objet portable suit un personnage.

Ce contrat ne decide ni si un objet est porte comme vetement, ni s'il est tenu
dans une main. Il garantit uniquement le fait observable qu'un personnage
possede un objet portable top-level, qui suit alors sa position materielle.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from .db import transaction
from .objects import ObjectError, ObjectService, object_row, require_key, require_world_id
from .util import Clock
from .world import SOURCE_OWNER, WorldEngine, _append_event


def _character_row(conn: sqlite3.Connection, world_id: int, character_key: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT ch.id, ch.key, l.id AS location_id, l.key AS location_key "
        "FROM character ch JOIN location l ON l.id = ch.current_location_id "
        "WHERE ch.world_id = ? AND ch.key = ?",
        (world_id, character_key),
    ).fetchone()
    if row is None:
        raise ObjectError("personnage introuvable", code="character_not_found")
    return row


def direct_carrier_key(
    conn: sqlite3.Connection, world_id: int, object_id: int
) -> str | None:
    """Retourne le porteur direct d'un objet top-level, s'il existe."""
    if not WorldEngine._has_table(conn, "character_carried_object"):
        return None
    row = conn.execute(
        "SELECT ch.key FROM character_carried_object co "
        "JOIN character ch ON ch.id = co.character_id "
        "WHERE co.world_id = ? AND co.object_id = ?",
        (world_id, object_id),
    ).fetchone()
    return None if row is None else row["key"]


def carrier_key(conn: sqlite3.Connection, world_id: int, object_id: int) -> str | None:
    """Retourne le porteur, y compris si l'objet est dans un sac porte."""
    if not WorldEngine._has_table(conn, "character_carried_object"):
        return None
    row = conn.execute(
        "WITH RECURSIVE ancestors(id, parent_object_id, depth, path) AS ("
        " SELECT id, parent_object_id, 0, ',' || id || ',' FROM world_object WHERE id = ? "
        " UNION ALL "
        " SELECT o.id, o.parent_object_id, a.depth + 1, a.path || o.id || ',' "
        " FROM world_object o JOIN ancestors a ON a.parent_object_id = o.id "
        " WHERE o.world_id = ? AND instr(a.path, ',' || o.id || ',') = 0"
        ") "
        "SELECT ch.key FROM ancestors a "
        "JOIN character_carried_object co ON co.object_id = a.id "
        "JOIN character ch ON ch.id = co.character_id "
        "WHERE co.world_id = ? ORDER BY a.depth DESC LIMIT 1",
        (object_id, world_id, world_id),
    ).fetchone()
    return None if row is None else row["key"]


class PossessionService:
    """Prend, pose et lit les objets transportes, sans equipement implicite."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _canonical_now(self, world_id: int) -> str:
        try:
            return WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id)
        except KeyError as exc:
            raise ObjectError("monde introuvable", code="world_not_found") from exc

    def pick_up(
        self,
        world_id: Any,
        character_key: Any,
        object_key: Any,
        *,
        source: str = SOURCE_OWNER,
    ) -> dict[str, Any]:
        """Fait prendre un objet portable present au meme lieu que le personnage."""
        world_id = require_world_id(world_id)
        character_key = require_key(character_key, "cle de personnage")
        object_key = require_key(object_key, "cle d'objet")
        with transaction(self._conn) as conn:
            character = _character_row(conn, world_id, character_key)
            obj = object_row(conn, world_id, object_key)
            if not obj["portable"]:
                raise ObjectError("une installation fixe ne peut pas etre portee", code="object_fixed")
            if obj["parent_object_id"] is not None:
                raise ObjectError("retirer l'objet de son conteneur avant de le porter", code="object_contained")
            carrier = direct_carrier_key(conn, world_id, obj["id"])
            if carrier is not None:
                code = "object_already_carried" if carrier == character_key else "object_carried_by_other"
                raise ObjectError("objet deja porte", code=code)
            if obj["location_id"] != character["location_id"]:
                raise ObjectError("objet hors de portee du personnage", code="object_not_accessible")
            canonical_now = self._canonical_now(world_id)
            recorded_now = self._clock.now_iso()
            conn.execute(
                "INSERT INTO character_carried_object (world_id, character_id, object_id, acquired_at) "
                "VALUES (?, ?, ?, ?)",
                (world_id, character["id"], obj["id"], recorded_now),
            )
            _append_event(
                conn, world_id, source, "object_picked_up",
                {"character": character_key, "object": object_key, "location": character["location_key"]},
                occurred_at=canonical_now, recorded_at=recorded_now,
            )
        return ObjectService(self._conn, clock=self._clock).object_sheet(world_id, object_key)

    def put_down(
        self,
        world_id: Any,
        character_key: Any,
        object_key: Any,
        *,
        source: str = SOURCE_OWNER,
    ) -> dict[str, Any]:
        """Pose un objet directement porte au lieu courant du personnage."""
        world_id = require_world_id(world_id)
        character_key = require_key(character_key, "cle de personnage")
        object_key = require_key(object_key, "cle d'objet")
        with transaction(self._conn) as conn:
            character = _character_row(conn, world_id, character_key)
            obj = object_row(conn, world_id, object_key)
            carrier = direct_carrier_key(conn, world_id, obj["id"])
            if carrier is None:
                raise ObjectError("objet non porte", code="object_not_carried")
            if carrier != character_key:
                raise ObjectError("objet porte par un autre personnage", code="object_carried_by_other")
            canonical_now = self._canonical_now(world_id)
            recorded_now = self._clock.now_iso()
            conn.execute(
                "DELETE FROM character_carried_object WHERE world_id = ? AND object_id = ?",
                (world_id, obj["id"]),
            )
            _append_event(
                conn, world_id, source, "object_put_down",
                {"character": character_key, "object": object_key, "location": character["location_key"]},
                occurred_at=canonical_now, recorded_at=recorded_now,
            )
        return ObjectService(self._conn, clock=self._clock).object_sheet(world_id, object_key)

    def carried_objects(self, world_id: Any, character_key: Any) -> list[dict[str, Any]]:
        """Liste deterministe des objets directement portes (sacs inclus, contenus exclus)."""
        world_id = require_world_id(world_id)
        character_key = require_key(character_key, "cle de personnage")
        character = _character_row(self._conn, world_id, character_key)
        rows = self._conn.execute(
            "SELECT o.key FROM character_carried_object co JOIN world_object o ON o.id = co.object_id "
            "WHERE co.world_id = ? AND co.character_id = ? ORDER BY o.key",
            (world_id, character["id"]),
        ).fetchall()
        objects = ObjectService(self._conn, clock=self._clock)
        return [objects.object_sheet(world_id, row["key"]) for row in rows]
