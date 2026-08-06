"""Contenance canonique d'objets, distincte de la topologie des lieux.

Portee initiale volontairement etroite : objet portable dans objet-conteneur.
Le port par un personnage, les liquides et Chuu dans un seau attendent leurs
contrats de forme et de traversee; ils ne sont pas simules ici.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from .db import transaction
from .objects import (
    ObjectError,
    location_row,
    object_row,
    object_carrier_key,
    relocate_subtree,
    require_key,
    require_world_id,
    subtree_rows,
)
from .util import Clock
from .world import SOURCE_OWNER, WorldEngine, _append_event


class ContainmentService:
    """Place et retire des objets sans jamais laisser un sous-arbre incoherent."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _canonical_now(self, world_id: int) -> str:
        try:
            return WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id)
        except KeyError as exc:
            raise ObjectError("monde introuvable", code="world_not_found") from exc

    @staticmethod
    def _require_container(row: sqlite3.Row) -> int:
        capacity = row["container_capacity"]
        if capacity is None:
            raise ObjectError("l'objet cible n'est pas un conteneur", code="not_a_container")
        return capacity

    def put_inside(self, world_id: Any, object_key: Any, container_key: Any) -> dict[str, Any]:
        """Place un objet portable dans un conteneur, capacite directe incluse."""
        world_id = require_world_id(world_id)
        object_key = require_key(object_key, "cle d'objet")
        container_key = require_key(container_key, "cle de conteneur")
        with transaction(self._conn) as conn:
            obj = object_row(conn, world_id, object_key)
            container = object_row(conn, world_id, container_key)
            if obj["id"] == container["id"]:
                raise ObjectError("un objet ne peut pas se contenir lui-meme", code="containment_cycle")
            if not obj["portable"]:
                raise ObjectError("une installation fixe ne peut pas etre contenue", code="object_fixed")
            capacity = self._require_container(container)
            if obj["parent_object_id"] == container["id"]:
                raise ObjectError("objet deja dans ce conteneur", code="already_contained")
            if object_carrier_key(conn, world_id, obj["id"]) is not None:
                raise ObjectError("un objet porte doit etre pose avant d'etre range", code="object_carried")
            descendant_ids = {row["id"] for row in subtree_rows(conn, world_id, obj["id"])}
            if container["id"] in descendant_ids:
                raise ObjectError("cette operation creerait un cycle de contenance", code="containment_cycle")
            occupied = conn.execute(
                "SELECT COUNT(*) FROM world_object WHERE world_id = ? AND parent_object_id = ?",
                (world_id, container["id"]),
            ).fetchone()[0]
            if occupied >= capacity:
                raise ObjectError("capacite du conteneur atteinte", code="container_full")
            canonical_now = self._canonical_now(world_id)
            recorded_now = self._clock.now_iso()
            previous_parent = obj["parent_key"]
            previous_location = obj["location_key"]
            conn.execute(
                "UPDATE world_object SET parent_object_id = ?, location_id = ? WHERE id = ?",
                (container["id"], container["location_id"], obj["id"]),
            )
            moved_subtree_count = relocate_subtree(
                conn, world_id, obj["id"], container["location_id"], include_root=False
            )
            _append_event(
                conn,
                world_id,
                SOURCE_OWNER,
                "object_contained",
                {
                    "object": object_key,
                    "container": container_key,
                    "from_parent": previous_parent,
                    "from_location": previous_location,
                    "to_location": container["location_key"],
                    "moved_subtree_count": moved_subtree_count,
                },
                occurred_at=canonical_now,
                recorded_at=recorded_now,
            )
        return self.object_sheet(world_id, object_key)

    def remove_to_location(self, world_id: Any, object_key: Any, location_key: Any) -> dict[str, Any]:
        """Sort un objet d'un conteneur et le pose dans un lieu explicite."""
        world_id = require_world_id(world_id)
        object_key = require_key(object_key, "cle d'objet")
        location_key = require_key(location_key, "cle de lieu")
        with transaction(self._conn) as conn:
            obj = object_row(conn, world_id, object_key)
            if obj["parent_object_id"] is None:
                raise ObjectError("objet non contenu", code="not_contained")
            location = location_row(conn, world_id, location_key)
            canonical_now = self._canonical_now(world_id)
            recorded_now = self._clock.now_iso()
            previous_parent = obj["parent_key"]
            previous_location = obj["location_key"]
            conn.execute(
                "UPDATE world_object SET parent_object_id = NULL, location_id = ? WHERE id = ?",
                (location["id"], obj["id"]),
            )
            moved_subtree_count = relocate_subtree(
                conn, world_id, obj["id"], location["id"], include_root=False
            )
            _append_event(
                conn,
                world_id,
                SOURCE_OWNER,
                "object_removed_from_container",
                {
                    "object": object_key,
                    "from_container": previous_parent,
                    "from_location": previous_location,
                    "to_location": location_key,
                    "moved_subtree_count": moved_subtree_count,
                },
                occurred_at=canonical_now,
                recorded_at=recorded_now,
            )
        return self.object_sheet(world_id, object_key)

    def object_sheet(self, world_id: Any, object_key: Any) -> dict[str, Any]:
        """Fiche de lecture pure, sans dependance cyclique vers ObjectService."""
        world_id = require_world_id(world_id)
        object_key = require_key(object_key, "cle d'objet")
        row = object_row(self._conn, world_id, object_key)
        contained_count = self._conn.execute(
            "SELECT COUNT(*) FROM world_object WHERE world_id = ? AND parent_object_id = ?",
            (world_id, row["id"]),
        ).fetchone()[0]
        return {
            "key": row["key"], "name": row["name"], "kind": row["kind"],
            "state": row["state"], "portable": bool(row["portable"]),
            "container_capacity": row["container_capacity"], "contained_count": contained_count,
            "location": row["location_key"], "parent": row["parent_key"],
            "carrier": object_carrier_key(self._conn, world_id, row["id"]),
        }

    def contents(
        self, world_id: Any, container_key: Any, *, recursive: Any = False
    ) -> list[dict[str, Any]]:
        """Liste les contenus directs, ou tout le sous-arbre avec sa profondeur."""
        world_id = require_world_id(world_id)
        container_key = require_key(container_key, "cle de conteneur")
        if not isinstance(recursive, bool):
            raise ObjectError("recursive doit etre un booleen", code="invalid_recursive")
        container = object_row(self._conn, world_id, container_key)
        self._require_container(container)
        if recursive:
            rows = subtree_rows(self._conn, world_id, container["id"])[1:]
            items: list[dict[str, Any]] = []
            for row in rows:
                key_row = self._conn.execute(
                    "SELECT key FROM world_object WHERE world_id = ? AND id = ?",
                    (world_id, row["id"]),
                ).fetchone()
                if key_row is None:  # Defensive only: descendants come from this table.
                    raise ObjectError("objet introuvable", code="object_not_found")
                items.append({**self.object_sheet(world_id, key_row["key"]), "depth": row["depth"]})
            return items
        rows = self._conn.execute(
            "SELECT key FROM world_object WHERE world_id = ? AND parent_object_id = ? ORDER BY key",
            (world_id, container["id"]),
        ).fetchall()
        return [self.object_sheet(world_id, row["key"]) for row in rows]
