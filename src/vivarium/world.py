"""Moteur canonique : seule autorité d'écriture du monde.

Toute modification de l'état canonique est réalisée par le moteur et produit
sa trace canonique (événement `canonical_event`) **dans la même transaction**.
Aucune sortie textuelle, aucun journal applicatif et aucune future réponse de
modèle ne peuvent écrire directement un fait canonique.

## Horloge canonique (Lot 2.1)

L'heure simulée est **dérivée**, non écrite à chaque consultation :

- `canonical_clock.simulated_now` = heure simulée au dernier ancrage ;
- `canonical_clock.real_updated_at` = heure réelle correspondant à cet ancrage ;
- monde actif : heure simulée courante = `simulated_now` + temps réel écoulé
  depuis `real_updated_at` ;
- monde en pause : heure simulée = `simulated_now` (gelée).

Une simple lecture ne produit aucune écriture, aucun événement, ne modifie
aucune transaction et ne fait grossir aucun journal.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from .db import transaction
from .seed import SEED_CHARACTERS, SEED_LINKS, SEED_LOCATIONS, SEED_NEEDS, SEED_OBJECTS
from .util import Clock, ClockError, new_uuid, now_utc, parse_iso, to_iso

WORLD_DEFAULT_NAME = "Monde de développement (Phase 1)"

# Types de source du journal (extensibles ; non limités à `engine`).
SOURCE_SYSTEM = "system"
SOURCE_ENGINE = "engine"
SOURCE_OWNER = "owner"

# Statuts de monde (contraints par les déclencheurs de la migration 0002).
STATUS_ACTIVE = "active"
STATUS_PAUSED = "paused"


def _append_event(
    conn: sqlite3.Connection,
    world_id: int,
    source_kind: str,
    event_type: str,
    payload: dict[str, Any],
    *,
    occurred_at: str | None = None,
    recorded_at: str | None = None,
) -> int:
    """Insère un événement canonique dans la transaction en cours."""
    seq = conn.execute(
        "SELECT COALESCE(MAX(seq), 0) + 1 FROM canonical_event WHERE world_id = ?",
        (world_id,),
    ).fetchone()[0]
    # Par défaut, l'heure d'enregistrement est l'heure réelle courante ; le
    # moteur peut la fournir explicitement (horloge injectée) pour les tests.
    recorded = recorded_at or now_utc()
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

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _now_iso(self) -> str:
        return self._clock.now_iso()

    # --- Création / destruction -------------------------------------------------

    def init_world(self, name: str | None = None, seed: bool = True) -> dict[str, Any]:
        """Crée un monde de développement avec sa résidence et son horloge."""
        name = name or WORLD_DEFAULT_NAME
        with transaction(self._conn) as c:
            now = self._now_iso()
            cur = c.execute(
                "INSERT INTO worlds (public_id, name, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (new_uuid(), name, STATUS_ACTIVE, now, now),
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
                recorded_at=now,
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
        # Passages physiques du graphe (chaque paire → deux arêtes réciproques).
        for a_key, b_key in SEED_LINKS:
            self._seed_link(c, world_id, location_ids[a_key], location_ids[b_key], now)
        # Quatre habitantes provisoires (positions initiales directes, chambres 1..4).
        character_ids: dict[str, int] = {}
        for key, name, loc_key in SEED_CHARACTERS:
            cur = c.execute(
                "INSERT INTO character "
                "(public_id, world_id, key, name, adult, current_location_id, "
                " created_at, updated_at) VALUES (?, ?, ?, ?, 1, ?, ?, ?)",
                (new_uuid(), world_id, key, name, location_ids[loc_key], now, now),
            )
            character_ids[key] = cur.lastrowid
            _append_event(
                c,
                world_id,
                SOURCE_SYSTEM,
                "character_created",
                {"character": key, "name": name, "location": loc_key},
                occurred_at=now,
                recorded_at=now,
            )
        # Besoins : définitions + états initiaux par personnage, ancrés à l'heure
        # simulée canonique `now` (jamais l'heure système).
        need_ids: dict[str, int] = {}
        for key, name, initial, num, den, thr in SEED_NEEDS:
            cur = c.execute(
                "INSERT INTO need_definition "
                "(public_id, world_id, need_key, name, min_milli, max_milli, "
                " rate_num, rate_den, threshold_milli, created_at) "
                "VALUES (?, ?, ?, ?, 0, 100000, ?, ?, ?, ?)",
                (new_uuid(), world_id, key, name, num, den, thr, now),
            )
            need_ids[key] = cur.lastrowid
        for char_key, char_id in character_ids.items():
            for key, name, initial, num, den, thr in SEED_NEEDS:
                c.execute(
                    "INSERT INTO need_state "
                    "(public_id, world_id, character_id, need_key, value_milli, "
                    " rate_remainder, anchor_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, 0, ?, ?)",
                    (new_uuid(), world_id, char_id, key, initial, now, now),
                )
        _append_event(
            c,
            world_id,
            SOURCE_SYSTEM,
            "world_seeded",
            {
                "locations": len(SEED_LOCATIONS),
                "objects": len(SEED_OBJECTS),
                "links_pairs": len(SEED_LINKS),
                "characters": len(SEED_CHARACTERS),
                "needs": len(SEED_NEEDS),
            },
            occurred_at=now,
            recorded_at=now,
        )

    def _seed_link(self, c: sqlite3.Connection, world_id: int, from_id: int, to_id: int, now: str) -> None:
        """Insère un passage bidirectionnel (deux arêtes réciproques) dans la
        transaction de seed en cours."""
        for a, b in ((from_id, to_id), (to_id, from_id)):
            c.execute(
                "INSERT INTO location_link "
                "(public_id, world_id, from_location_id, to_location_id, kind, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (new_uuid(), world_id, a, b, "door", now),
            )

    def destroy_world(self, world_id: int) -> None:
        """Supprime un monde et ses données (développement uniquement).

        Le journal canonical est append-only : pour un reset complet du monde
        de développement, la base est reconstruite au niveau fichier (préférable
        à la suppression d'un journal d'audit).
        """
        with transaction(self._conn) as c:
            c.execute("DELETE FROM need_state WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM world_object WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM location_link WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM character WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM location WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM need_definition WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM canonical_clock WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM worlds WHERE id = ?", (world_id,))

    # --- Horloge canonique dérivée ----------------------------------------------

    def read_canonical_time(self, world_id: int) -> str:
        """Heure simulée courante, calculée (lecture pure, sans écriture).

        Monde actif : `simulated_now` + écoulé réel depuis `real_updated_at`.
        Monde en pause : `simulated_now` (gelée).
        Lève `ClockError` si l'horloge réelle serait antérieure à l'ancre.
        """
        row = self._conn.execute(
            "SELECT w.status AS status, c.simulated_now AS sim, c.real_updated_at AS real "
            "FROM worlds w JOIN canonical_clock c ON c.world_id = w.id "
            "WHERE w.id = ?",
            (world_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"monde introuvable : {world_id}")
        if row["status"] == STATUS_PAUSED:
            return row["sim"]
        anchor_sim = parse_iso(row["sim"])
        anchor_real = parse_iso(row["real"])
        elapsed = self._clock.now() - anchor_real
        if elapsed.total_seconds() < 0:
            raise ClockError(
                "horloge réelle antérieure à l'ancre : heure simulée incohérente"
            )
        return to_iso(anchor_sim + elapsed)

    def pause_world(self, world_id: int) -> dict[str, Any]:
        """Gèle le temps : matérialise l'heure courante puis fige.

        Calcule l'heure simulée courante, la fixe comme nouveau `simulated_now`,
        repose `real_updated_at` et passe le monde en `paused`. État + événement
        canonique dans la même transaction.
        """
        frozen = self.read_canonical_time(world_id)
        from .needs import NeedsEngine  # évite un cycle d'import

        needs = NeedsEngine(self._conn, clock=self._clock)
        char_keys = [
            r["key"]
            for r in self._conn.execute(
                "SELECT key FROM character WHERE world_id = ?", (world_id,)
            )
        ]
        with transaction(self._conn) as c:
            now = self._now_iso()
            # Matérialiser les besoins à l'heure simulée figée, dans la même
            # transaction que le gel de l'horloge et du statut (atomique).
            for key in char_keys:
                needs.materialize_character_needs(
                    world_id, key, frozen, "pause", _conn=c
                )
            c.execute(
                "UPDATE canonical_clock SET simulated_now = ?, real_updated_at = ? "
                "WHERE world_id = ?",
                (frozen, now, world_id),
            )
            c.execute(
                "UPDATE worlds SET status = ?, updated_at = ? WHERE id = ?",
                (STATUS_PAUSED, now, world_id),
            )
            _append_event(
                c, world_id, SOURCE_SYSTEM, "world_paused",
                {"simulated_now": frozen}, occurred_at=frozen, recorded_at=now,
            )
        return self.get_world(world_id)

    def resume_world(self, world_id: int) -> dict[str, Any]:
        """Reprend le temps actif sans rattraper la durée de la pause.

        Conserve exactement l'heure simulée gelée, repose `real_updated_at` à
        l'heure réelle de reprise et remet le statut à `active`.
        """
        with transaction(self._conn) as c:
            now = self._now_iso()
            frozen = c.execute(
                "SELECT simulated_now FROM canonical_clock WHERE world_id = ?",
                (world_id,),
            ).fetchone()
            if frozen is None:
                raise KeyError(f"monde introuvable : {world_id}")
            frozen = frozen["simulated_now"]
            c.execute(
                "UPDATE canonical_clock SET real_updated_at = ? WHERE world_id = ?",
                (now, world_id),
            )
            c.execute(
                "UPDATE worlds SET status = ?, updated_at = ? WHERE id = ?",
                (STATUS_ACTIVE, now, world_id),
            )
            _append_event(
                c, world_id, SOURCE_SYSTEM, "world_resumed",
                {"simulated_now": frozen}, occurred_at=frozen, recorded_at=now,
            )
        return self.get_world(world_id)

    def set_simulated_time(self, world_id: int, new_sim: str) -> dict[str, Any]:
        """Modification administrative explicite de l'heure simulée (tracée).

        Rejette toute heure antérieure à l'heure simulée courante (incohérente)
        et enregistre un événement `clock_updated` dans la même transaction.
        """
        current = self.read_canonical_time(world_id)
        if parse_iso(new_sim) < parse_iso(current):
            raise ClockError(
                f"heure simulée {new_sim} antérieure à l'heure courante {current} : incohérente"
            )
        with transaction(self._conn) as c:
            now = self._now_iso()
            c.execute(
                "UPDATE canonical_clock SET simulated_now = ?, real_updated_at = ? "
                "WHERE world_id = ?",
                (new_sim, now, world_id),
            )
            _append_event(
                c, world_id, SOURCE_OWNER, "clock_updated",
                {"simulated_now": new_sim}, occurred_at=new_sim, recorded_at=now,
            )
        return self.get_world(world_id)

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
        recorded = self._now_iso()
        with transaction(self._conn) as c:
            return _append_event(
                c, world_id, source_kind, event_type, payload,
                occurred_at=occurred_at, recorded_at=recorded,
            )

    def rename_world(self, world_id: int, new_name: str) -> dict[str, Any]:
        """Renomme un monde et trace l'événement dans la même transaction."""
        with transaction(self._conn) as c:
            now = self._now_iso()
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
                          {"from": old["name"], "to": new_name}, occurred_at=now,
                          recorded_at=now)
        return self.get_world(world_id)

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

    L'horloge affichée est l'heure simulée **courante dérivée** (pas l'ancre).
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
    counts = {
        "locations": conn.execute(
            "SELECT COUNT(*) FROM location WHERE world_id = ?", (world["id"],)
        ).fetchone()[0],
        "objects": conn.execute(
            "SELECT COUNT(*) FROM world_object WHERE world_id = ?", (world["id"],)
        ).fetchone()[0],
        "characters": conn.execute(
            "SELECT COUNT(*) FROM character WHERE world_id = ?", (world["id"],)
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
        "clock": {"simulated_now": engine.read_canonical_time(world["id"])},
        "integrity_check": integrity,
        "foreign_key_check": [dict(r) for r in fk_violations],
        "counts": counts,
    }
