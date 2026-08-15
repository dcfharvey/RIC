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
from .seed import (
    SEED_ACTIVITIES,
    SEED_ACTIVITY_ALLOWED,
    SEED_CHARACTERS,
    SEED_LINKS,
    SEED_LOCATIONS,
    SEED_NEEDS,
    SEED_OBJECTS,
    SEED_PROFILES,
)
from .util import Clock, ClockError, new_uuid, now_utc, parse_iso, to_iso

WORLD_DEFAULT_NAME = "Monde de développement (Phase 1)"

# Types de source du journal (extensibles ; non limités à `engine`).
SOURCE_SYSTEM = "system"
SOURCE_ENGINE = "engine"
SOURCE_OWNER = "owner"

# Statuts de monde (contraints par les déclencheurs de la migration 0002).
STATUS_ACTIVE = "active"
STATUS_PAUSED = "paused"

# Longueur maximale du nom d'un monde (validation autoritative de rename_world).
WORLD_NAME_MAX_LEN = 120


class WorldError(RuntimeError):
    """Erreur métier de monde (nom invalide, transition d'état invalide).

    Porte un `code` stable pour la traduction par la couche application.
    """

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def append_event(
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


# Compatibility alias for code that still calls the helper inside this owner.
_append_event = append_event


class WorldEngine:
    """Moteur canonique. Unique chemin de modification des données du monde."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _now_iso(self) -> str:
        return self._clock.now_iso()

    @staticmethod
    def _has_topology_policy_table(conn: sqlite3.Connection) -> bool:
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'world_topology_policy'"
        ).fetchone() is not None

    @staticmethod
    def has_table(conn: sqlite3.Connection, name: str) -> bool:
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
        ).fetchone() is not None

    _has_table = has_table

    @staticmethod
    def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
        return any(
            row["name"] == column
            for row in conn.execute(f"PRAGMA table_info({table})")
        )

    def create_empty_world_in_transaction(
        self, c: sqlite3.Connection, name: str, *, seeded: bool
    ) -> tuple[int, str]:
        """Crée monde, horloge et premier fait dans une transaction appelante."""
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
        _append_event(
            c, world_id, SOURCE_SYSTEM, "world_created", {"name": name, "seeded": seeded},
            occurred_at=now, recorded_at=now,
        )
        if not seeded and self._has_topology_policy_table(c):
            c.execute(
                "INSERT INTO world_topology_policy "
                "(world_id, policy_key, anchor_location_id, configured_at) "
                "VALUES (?, 'none', NULL, ?)",
                (world_id, now),
            )
        return world_id, now

    _create_empty_world_in_transaction = create_empty_world_in_transaction

    # --- Création / destruction -------------------------------------------------

    def init_world(self, name: str | None = None, seed: bool = True) -> dict[str, Any]:
        """Crée un monde de développement avec sa résidence et son horloge."""
        name = name or WORLD_DEFAULT_NAME
        with transaction(self._conn) as c:
            world_id, now = self._create_empty_world_in_transaction(c, name, seeded=seed)
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
        if self._has_topology_policy_table(c):
            c.execute(
                "INSERT INTO world_topology_policy "
                "(world_id, policy_key, anchor_location_id, configured_at) "
                "VALUES (?, 'strong_anchor', ?, ?)",
                (world_id, location_ids["salon"], now),
            )
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
        # Profils individuels neutres (aucune différence canonique).
        for i, (char_key, char_id) in enumerate(sorted(character_ids.items())):
            p = SEED_PROFILES[i]
            c.execute(
                "INSERT INTO character_profile "
                "(character_id, world_id, satiete_threshold_mult_milli, "
                " repos_threshold_mult_milli, energie_threshold_mult_milli, "
                " hygiene_threshold_mult_milli, rest_preference_milli, "
                " idle_tolerance_milli, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    char_id, world_id, p["satiete_threshold_mult_milli"],
                    p["repos_threshold_mult_milli"],
                    p["energie_threshold_mult_milli"],
                    p["hygiene_threshold_mult_milli"],
                    p["rest_preference_milli"], p["idle_tolerance_milli"], now,
                ),
            )
        # Catalogue d'activités (taux nets /36) + lieux autorisés.
        for typ, min_d, max_d, s, rp, e, h, sustained_wakefulness in SEED_ACTIVITIES:
            if self._has_column(c, "activity_definition", "requires_sustained_wakefulness"):
                c.execute(
                    "INSERT INTO activity_definition "
                    "(public_id, world_id, activity_type, min_duration_seconds, "
                    " max_duration_seconds, satiete_rate, repos_rate, energie_rate, "
                    " hygiene_rate, requires_sustained_wakefulness, physical_load_class, "
                    " created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        new_uuid(), world_id, typ, min_d, max_d, s, rp, e, h,
                        int(sustained_wakefulness), None, now,
                    ),
                )
            else:
                c.execute(
                    "INSERT INTO activity_definition "
                    "(public_id, world_id, activity_type, min_duration_seconds, "
                    " max_duration_seconds, satiete_rate, repos_rate, energie_rate, "
                    " hygiene_rate, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (new_uuid(), world_id, typ, min_d, max_d, s, rp, e, h, now),
                )
        for typ, key, kind in SEED_ACTIVITY_ALLOWED:
            c.execute(
                "INSERT INTO activity_allowed_location "
                "(public_id, world_id, activity_type, location_key, location_kind, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (new_uuid(), world_id, typ, key, kind, now),
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
                "activities": len(SEED_ACTIVITIES),
                "profiles": len(SEED_PROFILES),
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
            if self._has_table(c, "world_location_origin"):
                c.execute("DELETE FROM world_location_origin WHERE world_id = ?", (world_id,))
            if self._has_table(c, "world_environment_origin"):
                c.execute("DELETE FROM world_environment_origin WHERE world_id = ?", (world_id,))
            if self._has_topology_policy_table(c):
                c.execute("DELETE FROM world_topology_policy WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM need_state WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM character_profile WHERE world_id = ?", (world_id,))
            c.execute(
                "DELETE FROM resource_state_effect WHERE resource_state_band_id IN "
                "(SELECT b.id FROM resource_state_band b JOIN resource_state s "
                "ON s.id = b.resource_state_id WHERE s.world_id = ?)",
                (world_id,),
            )
            c.execute(
                "DELETE FROM resource_state_band WHERE resource_state_id IN "
                "(SELECT id FROM resource_state WHERE world_id = ?)",
                (world_id,),
            )
            c.execute("DELETE FROM resource_state WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM resource_definition WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM character_instance_origin WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM world_object WHERE world_id = ?", (world_id,))
            c.execute("DELETE FROM location_link WHERE world_id = ?", (world_id,))
            if self._has_table(c, "world_connector"):
                c.execute("DELETE FROM world_connector WHERE world_id = ?", (world_id,))
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
        runtime_select = (
            "c.runtime_state"
            if self._has_column(self._conn, "canonical_clock", "runtime_state")
            else "'running'"
        )
        row = self._conn.execute(
            "SELECT w.status AS status, c.simulated_now AS sim, c.real_updated_at AS real, "
            f"{runtime_select} AS runtime_state "
            "FROM worlds w JOIN canonical_clock c ON c.world_id = w.id "
            "WHERE w.id = ?",
            (world_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"monde introuvable : {world_id}")
        if row["status"] == STATUS_PAUSED or row["runtime_state"] == "stopped":
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

        Transition atomique : lecture du statut, validation, calcul temporel,
        mutation et événement dans la même transaction. Une pause d'un monde déjà
        `paused` est refusée (`WorldError already_paused`) sans aucune mutation,
        modification d'horloge ni événement.
        """
        from .needs import NeedsEngine  # évite un cycle d'import
        from .sleep_physiology import SleepPhysiologyFoundationService, SleepPhysiologyService
        from .injury import InjuryEngine
        from .character import CharacterEngine

        with transaction(self._conn) as c:
            now = self._now_iso()
            status = c.execute(
                "SELECT status FROM worlds WHERE id = ?", (world_id,)
            ).fetchone()
            if status is None:
                raise KeyError(f"monde introuvable : {world_id}")
            if status["status"] == STATUS_PAUSED:
                raise WorldError(
                    "le monde est déjà en pause", code="already_paused"
                )
            frozen = self.read_canonical_time(world_id)
            needs = NeedsEngine(self._conn, clock=self._clock)
            physiology_active = SleepPhysiologyFoundationService(
                self._conn, clock=self._clock
            ).system_status(world_id) == "active"
            char_keys = [
                r["key"]
                for r in c.execute(
                    "SELECT key FROM character WHERE world_id = ?", (world_id,)
                )
            ]
            # En mode actif, repos/energie sont des colonnes legacy de schéma,
            # jamais des owners causaux. H/phi/P + satiété/hygiène sont figés.
            for key in char_keys:
                if physiology_active:
                    SleepPhysiologyService(self._conn, clock=self._clock).materialize_owner_backed(
                        world_id, key, frozen
                    )
                    needs.materialize_selected_needs(
                        world_id, key, frozen, "pause", frozenset({"satiete", "hygiene"}), _conn=c
                    )
                    injury_regime = CharacterEngine(
                        self._conn, clock=self._clock
                    ).active_recovery_regime(world_id, key)
                    InjuryEngine(self._conn, clock=self._clock).materialize_injury_sim(
                        world_id, key, frozen, injury_regime, _conn=c
                    )
                else:
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

        Transition atomique : lecture du statut, validation, mutation et événement
        dans la même transaction. Une reprise d'un monde déjà `active` est
        refusée (`WorldError already_active`) sans aucune mutation ni événement.
        """
        with transaction(self._conn) as c:
            now = self._now_iso()
            status = c.execute(
                "SELECT status FROM worlds WHERE id = ?", (world_id,)
            ).fetchone()
            if status is None:
                raise KeyError(f"monde introuvable : {world_id}")
            if status["status"] == STATUS_ACTIVE:
                raise WorldError(
                    "le monde est déjà actif", code="already_active"
                )
            frozen = c.execute(
                "SELECT simulated_now FROM canonical_clock WHERE world_id = ?",
                (world_id,),
            ).fetchone()
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

    def advance_clock_in_transaction(
        self, world_id: int, target_at: str, conn: sqlite3.Connection
    ) -> None:
        """Avance l'horloge canonique à `target_at` dans la transaction en cours.

        Pose atomiquement `simulated_now = target_at` et `real_updated_at =
        Clock.now` (heure murale), dans la transaction `conn` déjà ouverte.
        Réservé aux transitions temporelles du simulateur (`start_activity`,
        `advance_to`, `abort_activity`) : ce contrat n'ouvre pas de transaction
        et n'émet pas d'événement `clock_updated`. Un rollback de la transaction
        annule aussi cette mise à jour; la progression du run est tracée par ses
        propres événements.
        """
        conn.execute(
            "UPDATE canonical_clock SET simulated_now = ?, real_updated_at = ? "
            "WHERE world_id = ?",
            (target_at, self._now_iso(), world_id),
        )

    _advance_clock = advance_clock_in_transaction

    # --- Écritures d'état + trace canonique (même transaction) -----------------

    @staticmethod
    def normalize_world_name(new_name: Any) -> str:
        """Valide et normalise le nom d'un monde sans effectuer d'écriture."""
        if not isinstance(new_name, str):
            raise WorldError(
                "le nom du monde doit être une chaîne", code="invalid_name"
            )
        normalized = new_name.strip()
        if not normalized:
            raise WorldError(
                "le nom du monde ne peut pas être vide", code="invalid_name"
            )
        if len(normalized) > WORLD_NAME_MAX_LEN:
            raise WorldError(
                f"le nom du monde ne peut pas dépasser {WORLD_NAME_MAX_LEN} caractères",
                code="invalid_name",
            )
        return normalized

    def _rename_world_in_transaction(
        self,
        conn: sqlite3.Connection,
        world_id: int,
        normalized_name: str,
        *,
        admin_change_id: str | None = None,
    ) -> dict[str, Any]:
        """Applique un renommage dans une transaction déjà ouverte.

        Réservé aux commandes canoniques composées. La validation du nom doit
        avoir eu lieu avant l'appel. Un identifiant de plan, lorsqu'il existe,
        rattache le fait canonique à l'audit administratif sans transformer cet
        audit en source de vérité du monde.
        """
        now = self._now_iso()
        canonical = self.read_canonical_time(world_id)
        old = conn.execute(
            "SELECT name FROM worlds WHERE id = ?", (world_id,)
        ).fetchone()
        if old is None:
            raise KeyError(f"monde introuvable : {world_id}")
        conn.execute(
            "UPDATE worlds SET name = ?, updated_at = ? WHERE id = ?",
            (normalized_name, now, world_id),
        )
        payload: dict[str, Any] = {"from": old["name"], "to": normalized_name}
        if admin_change_id is not None:
            payload["admin_change_id"] = admin_change_id
        _append_event(
            conn,
            world_id,
            SOURCE_OWNER,
            "world_renamed",
            payload,
            occurred_at=canonical,
            recorded_at=now,
        )
        return {"id": world_id, "name": normalized_name, "canonical_at": canonical}

    def rename_world_in_transaction(
        self,
        conn: sqlite3.Connection,
        world_id: int,
        normalized_name: str,
        *,
        admin_change_id: str | None = None,
    ) -> dict[str, Any]:
        """Applique un renommage dans une transaction déjà ouverte."""
        return self._rename_world_in_transaction(
            conn,
            world_id,
            normalized_name,
            admin_change_id=admin_change_id,
        )

    def rename_world(self, world_id: int, new_name: str) -> dict[str, Any]:
        """Renomme un monde et trace l'événement dans la même transaction.

        Validation autoritative du nom (avant toute mutation) : chaîne, non vide
        après suppression des espaces périphériques, longueur ≤ WORLD_NAME_MAX_LEN.
        La valeur enregistrée est la valeur normalisée. L'événement est situé dans
        le temps canonique du monde (`read_canonical_time`), jamais à l'heure murale.
        """
        normalized = self.normalize_world_name(new_name)
        with transaction(self._conn) as c:
            self._rename_world_in_transaction(c, world_id, normalized)
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
