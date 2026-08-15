"""Objets canoniques : installations fixes et objets portables.

Un objet possede toujours un lieu effectif materialise. La contenance
objet-a-objet est traitee par ``vivarium.containment``; ce module ne deplace
donc directement que les objets au niveau d'un lieu.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from .db import transaction
from .registry import KEY_RE as _KEY_RE
from .util import Clock, new_uuid
from .world import SOURCE_OWNER, WorldEngine, append_event as _append_event


class ObjectError(ValueError):
    """Refus metier stable pour les objets canoniques."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def require_world_id(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ObjectError("monde invalide", code="invalid_world")
    return value


def require_key(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise ObjectError(f"{label} invalide", code="invalid_key")
    return value


def object_row(conn: sqlite3.Connection, world_id: int, key: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT o.id, o.key, o.name, o.kind, o.state, o.portable, "
        "o.container_capacity, o.parent_object_id, l.id AS location_id, l.key AS location_key, "
        "p.key AS parent_key "
        "FROM world_object o JOIN location l ON l.id = o.location_id "
        "LEFT JOIN world_object p ON p.id = o.parent_object_id "
        "WHERE o.world_id = ? AND o.key = ?",
        (world_id, key),
    ).fetchone()
    if row is None:
        raise ObjectError("objet introuvable", code="object_not_found")
    return row


def location_row(conn: sqlite3.Connection, world_id: int, key: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT id, key FROM location WHERE world_id = ? AND key = ?", (world_id, key)
    ).fetchone()
    if row is None:
        raise ObjectError("lieu introuvable", code="location_not_found")
    return row


def subtree_rows(conn: sqlite3.Connection, world_id: int, root_id: int) -> list[sqlite3.Row]:
    """Retourne une sous-arborescence en ordre parent puis enfants.

    Le chemin protege aussi la lecture contre une ancienne base corrompue : le
    service ne boucle jamais, meme si un cycle illicite avait ete force avant
    l'ajout des contraintes actuelles.
    """
    return conn.execute(
        "WITH RECURSIVE subtree(id, depth, path) AS ("
        " SELECT ?, 0, ',' || ? || ',' "
        " UNION ALL "
        " SELECT o.id, s.depth + 1, s.path || o.id || ',' "
        " FROM world_object o JOIN subtree s ON o.parent_object_id = s.id "
        " WHERE o.world_id = ? AND instr(s.path, ',' || o.id || ',') = 0"
        ") "
        "SELECT id, depth FROM subtree ORDER BY depth, id",
        (root_id, root_id, world_id),
    ).fetchall()


def relocate_subtree(
    conn: sqlite3.Connection,
    world_id: int,
    root_id: int,
    location_id: int,
    *,
    include_root: bool = True,
) -> int:
    """Materialise le nouveau lieu du sous-arbre, dans l'ordre sur."""
    rows = subtree_rows(conn, world_id, root_id)
    start = 0 if include_root else 1
    for row in rows[start:]:
        conn.execute("UPDATE world_object SET location_id = ? WHERE id = ?", (location_id, row["id"]))
    return len(rows)


def object_carrier_key(conn: sqlite3.Connection, world_id: int, object_id: int) -> str | None:
    """Lit le porteur d'un objet sans imposer la couche de possession aux vieilles bases."""
    from .possession import carrier_key  # import tardif : pas de cycle au chargement

    return carrier_key(conn, world_id, object_id)


class ObjectService:
    """Cree, inspecte et deplace les installations et objets portables."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def _name(value: Any) -> str:
        if not isinstance(value, str) or not (clean := value.strip()):
            raise ObjectError("nom d'objet invalide", code="invalid_name")
        return clean

    @staticmethod
    def _capacity(value: Any) -> int | None:
        if value is None:
            return None
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ObjectError("capacite de contenance invalide", code="invalid_capacity")
        return value

    @staticmethod
    def _portable(value: Any) -> bool:
        if not isinstance(value, bool):
            raise ObjectError("portable doit etre un booleen", code="invalid_portable")
        return value

    def _canonical_now(self, world_id: int) -> str:
        try:
            return WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id)
        except KeyError as exc:
            raise ObjectError("monde introuvable", code="world_not_found") from exc

    def object_sheet(self, world_id: Any, object_key: Any) -> dict[str, Any]:
        """Fiche de lecture pure d'un objet et de sa position effective."""
        world_id = require_world_id(world_id)
        object_key = require_key(object_key, "cle d'objet")
        row = object_row(self._conn, world_id, object_key)
        contained_count = self._conn.execute(
            "SELECT COUNT(*) FROM world_object WHERE world_id = ? AND parent_object_id = ?",
            (world_id, row["id"]),
        ).fetchone()[0]
        return {
            "key": row["key"],
            "name": row["name"],
            "kind": row["kind"],
            "state": row["state"],
            "portable": bool(row["portable"]),
            "container_capacity": row["container_capacity"],
            "contained_count": contained_count,
            "location": row["location_key"],
            "parent": row["parent_key"],
            "carrier": object_carrier_key(self._conn, world_id, row["id"]),
        }

    def list_objects(self, world_id: Any, *, location_key: Any | None = None) -> list[dict[str, Any]]:
        """Liste les objets du monde, eventuellement par lieu effectif."""
        world_id = require_world_id(world_id)
        if location_key is not None:
            location_key = require_key(location_key, "cle de lieu")
            location_row(self._conn, world_id, location_key)
        rows = self._conn.execute(
            "SELECT o.key FROM world_object o JOIN location l ON l.id = o.location_id "
            "WHERE o.world_id = ? AND (? IS NULL OR l.key = ?) ORDER BY o.key",
            (world_id, location_key, location_key),
        ).fetchall()
        return [self.object_sheet(world_id, row["key"]) for row in rows]

    def create_object(
        self,
        world_id: Any,
        object_key: Any,
        name: Any,
        kind: Any,
        location_key: Any,
        *,
        portable: Any = False,
        container_capacity: Any = None,
        state: Any = "present",
        source: str = SOURCE_OWNER,
    ) -> dict[str, Any]:
        """Cree un objet top-level et trace ce nouveau fait dans le journal."""
        world_id = require_world_id(world_id)
        object_key = require_key(object_key, "cle d'objet")
        name = self._name(name)
        kind = require_key(kind, "type d'objet")
        location_key = require_key(location_key, "cle de lieu")
        portable = self._portable(portable)
        container_capacity = self._capacity(container_capacity)
        state = require_key(state, "etat d'objet")

        with transaction(self._conn) as conn:
            canonical_now = self._canonical_now(world_id)
            location = location_row(conn, world_id, location_key)
            if conn.execute(
                "SELECT 1 FROM world_object WHERE world_id = ? AND key = ?", (world_id, object_key)
            ).fetchone() is not None:
                raise ObjectError("cle d'objet deja utilisee", code="duplicate_object_key")
            recorded_now = self._clock.now_iso()
            conn.execute(
                "INSERT INTO world_object (public_id, world_id, location_id, key, name, kind, state, "
                "created_at, portable, container_capacity, parent_object_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                (
                    new_uuid(), world_id, location["id"], object_key, name, kind, state,
                    recorded_now, int(portable), container_capacity,
                ),
            )
            _append_event(
                conn,
                world_id,
                source,
                "world_object_created",
                {
                    "object": object_key,
                    "name": name,
                    "kind": kind,
                    "location": location_key,
                    "portable": portable,
                    "container_capacity": container_capacity,
                    "state": state,
                },
                occurred_at=canonical_now,
                recorded_at=recorded_now,
            )
        return self.object_sheet(world_id, object_key)

    def move_object(self, world_id: Any, object_key: Any, location_key: Any) -> dict[str, Any]:
        """Deplace un objet portable top-level, avec tous ses contenus."""
        world_id = require_world_id(world_id)
        object_key = require_key(object_key, "cle d'objet")
        location_key = require_key(location_key, "cle de lieu")
        with transaction(self._conn) as conn:
            obj = object_row(conn, world_id, object_key)
            if not obj["portable"]:
                raise ObjectError("une installation fixe ne peut pas etre deplacee", code="object_fixed")
            if obj["parent_object_id"] is not None:
                raise ObjectError("retirer l'objet de son conteneur avant de le deplacer", code="object_contained")
            if object_carrier_key(conn, world_id, obj["id"]) is not None:
                raise ObjectError("un objet porte doit etre pose avant de le deplacer", code="object_carried")
            location = location_row(conn, world_id, location_key)
            if obj["location_id"] == location["id"]:
                raise ObjectError("objet deja dans ce lieu", code="object_already_there")
            canonical_now = self._canonical_now(world_id)
            recorded_now = self._clock.now_iso()
            moved_subtree_count = relocate_subtree(conn, world_id, obj["id"], location["id"])
            _append_event(
                conn,
                world_id,
                SOURCE_OWNER,
                "world_object_moved",
                {
                    "object": object_key,
                    "from_location": obj["location_key"],
                    "to_location": location_key,
                    "moved_subtree_count": moved_subtree_count,
                },
                occurred_at=canonical_now,
                recorded_at=recorded_now,
            )
        return self.object_sheet(world_id, object_key)
