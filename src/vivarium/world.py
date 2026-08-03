"""Moteur canonique : seule autorité d'écriture du monde (Phase 1).

Toute modification de l'état canonique est réalisée par le moteur et produit
sa trace canonique (événement `canonical_event`) **dans la même transaction**.
Aucune sortie textuelle, aucun journal applicatif et aucune future réponse de
modèle ne peuvent écrire directement un fait canonique.

Le journal `canonical_event` est une trace append-only et d'audit, mais il ne
constitue pas à lui seul tout l'état du monde : l'état vit dans les tables
d'état, le journal le retrace.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from .db import transaction
from .seed import SEED_LOCATIONS, SEED_OBJECTS
from .util import new_uuid, now_utc

WORLD_DEFAULT_NAME = "Monde de développement (Phase 1)"

# Types de source du journal (extensibles ; non limités à `engine`).
SOURCE_SYSTEM = "system"
SOURCE_ENGINE = "engine"
SOURCE_OWNER = "owner"


def _append_event(
    conn: sqlite3.Connection,
    world_id: int,
    source_kind: str,
    event_type: str,
    payload: dict[str, Any],
    *,
    occurred_at: str | None = None,
) -> int:
    """Insère un événement canonique dans la transaction en cours."""
    seq = conn.execute(
        "SELECT COALESCE(MAX(seq), 0) + 1 FROM canonical_event WHERE world_id = ?",
        (world_id,),
    ).fetchone()[0]
    recorded = now_utc()
    occurred = occurred_at or recorded
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    cur = conn.execute(
        "INSERT INTO canonical_event "
        "(public_id, world_id, seq, occurred_at, recorded_at, source_kind, "
        " event_type, payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            new_uuid(),
            world_id,
            seq,
            occurred,
            recorded,
            source_kind,
            event_type,
            payload_json,
        ),
    )
    return cur.lastrowid


class WorldEngine:
    """Moteur canonique. Unique chemin de modification des données du monde."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # --- Création / destruction -------------------------------------------------

    def init_world(self, name: str | None = None, seed: bool = True) -> dict[str, Any]:
        """Crée un monde de développement avec sa résidence et son horloge."""
        name = name or WORLD_DEFAULT_NAME
        with transaction(self._conn) as c:
            now = now_utc()
            cur = c.execute(
                "INSERT INTO worlds (public_id, name, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (new_uuid(), name, "active", now, now),
            )
            world_id = cur.lastrowid
            c.execute(
                "INSERT INTO canonical_clock "
                "(public_id, world_id, simulated_now, real_updated_at) VALUES (?, ?, ?, ?)",
                (new_uuid(), world_id, now, now),
            )
            # L'état créé ci-dessus et sa trace canonique partagent la même transaction.
            _append_event(
                c,
                world_id,
                SOURCE_SYSTEM,
                "world_created",
                {"name": name, "seeded": seed},
                occurred_at=now,
            )
            if seed:
                self._seed_world(c, world_id, now)
        return self.get_world(world_id)

    def _seed_world(self, c: sqlite3.Connection, world_id: int, now: str) -> None:
        location_ids: dict[str, int] = {}
        for key, name, kind, capacity in SEED_LOCATIONS:
            cur = c.execute(
                "INSERT INTO location "
                "(public_id, world_id, key, name, kind, capacity, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (new_uuid(), world_id, key, name, kind, capacity, now),
            )
            location_ids[key] = cur.lastrowid
        for key, name, kind, loc_key in SEED_OBJECTS:
            c.execute(
                "INSERT INTO world_object "
                "(public_id, world_id, location_id, key, name, kind, state, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (new_uuid(), world_id, location_ids[loc_key], key, name, kind, "present", now),
            )
        _append_event(
            c,
            world_id,
            SOURCE_SYSTEM,
            "world_seeded",
            {
                "locations": len(SEED_LOCATIONS),
                "objects": len(SEED_OBJECTS),
            },
            occurred_at=now,
        )

    def destroy_world(self, world_id: int) -> None:
        """Supprime un monde et ses données (développement uniquement).

        Le journal canonical est append-only : pour un reset complet du monde
        de développement, la base est reconstruite au niveau fichier (préférable
        à la suppression d'un journal d'audit).
        """
        with transaction(self._conn) as c:
            c.execute("DELETE FROM world_object WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM location WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM canonical_clock WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM worlds WHERE id = ?", (world_id,))

    # --- Écritures d'état + trace canonique (même transaction) -----------------

    def append_event(
        self,
        world_id: int,
        source_kind: str,
        event_type: str,
        payload: dict[str, Any],
        *,
        occurred_at: str | None = None,
    ) -> int:
        """Ajoute un événement canonique seul (trace d'audit dédiée)."""
        with transaction(self._conn) as c:
            return _append_event(c, world_id, source_kind, event_type, payload, occurred_at=occurred_at)

    def rename_world(self, world_id: int, new_name: str) -> dict[str, Any]:
        """Renomme un monde et trace l'événement dans la même transaction."""
        with transaction(self._conn) as c:
            now = now_utc()
            old = c.execute(
                "SELECT name FROM worlds WHERE id = ?", (world_id,)
            ).fetchone()
            if old is None:
                raise KeyError(f"monde introuvable : {world_id}")
            c.execute(
                "UPDATE worlds SET name = ?, updated_at = ? WHERE id = ?",
                (new_name, now, world_id),
            )
            _append_event(c, world_id, SOURCE_OWNER, "world_renamed",
                          {"from": old["name"], "to": new_name}, occurred_at=now)
        return self.get_world(world_id)

    def set_canonical_time(self, world_id: int, simulated_now: str) -> None:
        """Met à jour l'horloge canonique persistante (moteur uniquement)."""
        with transaction(self._conn) as c:
            now = now_utc()
            c.execute(
                "UPDATE canonical_clock SET simulated_now = ?, real_updated_at = ? "
                "WHERE world_id = ?",
                (simulated_now, now, world_id),
            )
            _append_event(c, world_id, SOURCE_SYSTEM, "clock_updated",
                          {"simulated_now": simulated_now}, occurred_at=simulated_now)

    # --- Lectures ---------------------------------------------------------------

    def get_world(self, world_id: int) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT * FROM worlds WHERE id = ?", (world_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"monde introuvable : {world_id}")
        return dict(row)

    def list_worlds(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self._conn.execute("SELECT * FROM worlds ORDER BY id")]


def get_status(conn: sqlite3.Connection, world_id: int | None = None) -> dict[str, Any]:
    """État général d'un monde pour inspection (intégrité, version, horloge, compteurs).

    Inclut : `PRAGMA integrity_check`, `PRAGMA foreign_key_check`, version des
    migrations, état de l'horloge, nombres de lieux/objets/événements.
    """
    engine = WorldEngine(conn)
    worlds = engine.list_worlds()
    if not worlds:
        return {"world": None, "present": False, "message": "aucun monde initialisé"}
    if world_id is None:
        world = worlds[0]
    else:
        world = engine.get_world(world_id)

    integrity = [r[0] for r in conn.execute("SELECT * FROM pragma_integrity_check")]
    fk_violations = conn.execute("SELECT * FROM pragma_foreign_key_check").fetchall()
    clock = conn.execute(
        "SELECT simulated_now FROM canonical_clock WHERE world_id = ?", (world["id"],)
    ).fetchone()
    counts = {
        "locations": conn.execute(
            "SELECT COUNT(*) FROM location WHERE world_id = ?", (world["id"],)
        ).fetchone()[0],
        "objects": conn.execute(
            "SELECT COUNT(*) FROM world_object WHERE world_id = ?", (world["id"],)
        ).fetchone()[0],
        "events": conn.execute(
            "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world["id"],)
        ).fetchone()[0],
    }
    from .migrations import current_version

    return {
        "present": True,
        "world": world,
        "schema_version": current_version(conn),
        "clock": dict(clock) if clock else None,
        "integrity_check": integrity,
        "foreign_key_check": [dict(r) for r in fk_violations],
        "counts": counts,
    }
