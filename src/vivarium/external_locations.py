"""Extension canonique et générique de la topologie hors propriété."""

from __future__ import annotations

import sqlite3
from typing import Any

from .db import transaction
from .registry import KEY_RE as _KEY_RE
from .spatial import GraphEngine
from .util import Clock, new_uuid
from .world import SOURCE_SYSTEM, WorldEngine, append_event as _append_event


class ExternalLocationError(ValueError):
    """Lieu extérieur invalide ou déjà présent."""


class ExternalLocationService:
    """Ajoute des lieux hors propriété sans les rendre perceptibles d'office."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def _key(value: Any, label: str) -> str:
        if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
            raise ExternalLocationError(f"{label} invalide")
        return value

    def add(
        self,
        world_id: int,
        key: str,
        name: str,
        *,
        boundary_key: str,
        kind: str = "external",
        capacity: int | None = None,
    ) -> dict[str, Any]:
        key = self._key(key, "clé de lieu")
        boundary_key = self._key(boundary_key, "frontière")
        if not isinstance(name, str) or not name.strip():
            raise ExternalLocationError("nom de lieu invalide")
        if not isinstance(kind, str) or not _KEY_RE.fullmatch(kind):
            raise ExternalLocationError("type de lieu invalide")
        if capacity is not None and (not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 0):
            raise ExternalLocationError("capacité invalide")
        with transaction(self._conn) as conn:
            world = conn.execute("SELECT 1 FROM worlds WHERE id=?", (world_id,)).fetchone()
            boundary = conn.execute(
                "SELECT id FROM location WHERE world_id=? AND key=?", (world_id, boundary_key)
            ).fetchone()
            if world is None or boundary is None:
                raise ExternalLocationError("monde ou frontière introuvable")
            if conn.execute("SELECT 1 FROM location WHERE world_id=? AND key=?", (world_id, key)).fetchone():
                raise ExternalLocationError("lieu déjà présent")
            now = self._clock.now_iso()
            canonical_at = WorldEngine(conn, clock=self._clock).read_canonical_time(world_id)
            cur = conn.execute(
                "INSERT INTO location (public_id,world_id,key,name,kind,capacity,created_at) VALUES (?,?,?,?,?,?,?)",
                (new_uuid(), world_id, key, name.strip(), kind, capacity, now),
            )
            GraphEngine(conn, clock=self._clock)._insert_edge(conn, world_id, boundary["id"], cur.lastrowid, "external")
            GraphEngine(conn, clock=self._clock)._insert_edge(conn, world_id, cur.lastrowid, boundary["id"], "external")
            _append_event(
                conn, world_id, SOURCE_SYSTEM, "external_location_created",
                {"location": key, "name": name.strip(), "kind": kind, "boundary": boundary_key},
                occurred_at=canonical_at, recorded_at=now,
            )
        return {"world_id": world_id, "key": key, "name": name.strip(), "kind": kind, "boundary": boundary_key}
