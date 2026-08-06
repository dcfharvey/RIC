"""Personnages et présence canonique (Lot 3.1).

`CharacterEngine` encapsule la logique des personnages mais **n'est pas une
seconde autorité canonique** : toutes ses écritures passent par la même
infrastructure transactionnelle (`db.transaction`) et événementielle
(`world._append_event`) que le moteur canonique, et les déplacements sont
validés par `GraphEngine` (lectures pures). Une seule couche contrôle les
modifications de l'état canonique.

Convention des sources (cohérente avec le journal) :
- création / seed initial : `system` ;
- déplacement automatique normal : `engine` (le "moteur" de la convention) ;
- intervention administrative explicite : `owner` (aucune API ici : le protocole
  INV-011 n'est pas encore implémenté).
"""

from __future__ import annotations

import sqlite3
from typing import Any

from .db import transaction
from .injury import InjuryEngine, MOVEMENT_SURCHARGE_MILLI, level
from .needs import NeedsEngine
from .objects import relocate_subtree
from .seed import SEED_CHARACTERS
from .util import Clock, new_uuid
from .world import SOURCE_ENGINE, SOURCE_SYSTEM, WorldEngine, _append_event
from .spatial import GraphEngine


class CharacterError(RuntimeError):
    """Erreur de personnage (personnage ou lieu introuvable, mouvement refusé).

    Porte un `code` stable facultatif pour la traduction par la couche
    application (jamais par analyse du texte du message).
    """

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class CharacterEngine:
    """Moteur des personnages. Écritures uniquement via la couche canonique."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _now_iso(self) -> str:
        return self._clock.now_iso()

    def _location_id(self, world_id: int, key: str) -> int:
        row = self._conn.execute(
            "SELECT id FROM location WHERE world_id = ? AND key = ?", (world_id, key)
        ).fetchone()
        if row is None:
            raise CharacterError(f"lieu introuvable : {key!r}")
        return row["id"]

    # --- Création (initialisation / seed) ---------------------------------------

    def create_character(
        self,
        world_id: int,
        key: str,
        name: str,
        location_key: str,
        *,
        source: str = SOURCE_SYSTEM,
    ) -> dict[str, Any]:
        """Crée un personnage adulte avec sa position initiale directe.

        La position initiale est définie à la création (ce n'est pas une
        téléportation). État + événement `character_created` dans la même
        transaction.
        """
        loc_id = self._location_id(world_id, location_key)
        with transaction(self._conn) as c:
            now = self._now_iso()
            canonical = self._canonical_time(world_id)
            c.execute(
                "INSERT INTO character "
                "(public_id, world_id, key, name, adult, current_location_id, "
                " created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (new_uuid(), world_id, key, name, 1, loc_id, now, now),
            )
            _append_event(
                c,
                world_id,
                source,
                "character_created",
                {"character": key, "name": name, "location": location_key},
                occurred_at=canonical, recorded_at=now,
            )
        return self.character_sheet(world_id, key)

    # --- Lecture pure -----------------------------------------------------------

    def character_sheet(self, world_id: int, key: str) -> dict[str, Any]:
        """Fiche structurelle minimale (lecture pure : aucune écriture)."""
        row = self._conn.execute(
            "SELECT ch.id, ch.public_id, ch.world_id, ch.key, ch.name, ch.adult, "
            "       l.key AS location_key, ch.created_at, ch.updated_at "
            "FROM character ch "
            "JOIN location l ON l.id = ch.current_location_id "
            "WHERE ch.world_id = ? AND ch.key = ?",
            (world_id, key),
        ).fetchone()
        if row is None:
            raise CharacterError(f"personnage introuvable : {key!r}")
        return dict(row)

    def list_characters(self, world_id: int) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT ch.key, ch.name, l.key AS location_key FROM character ch "
            "JOIN location l ON l.id = ch.current_location_id "
            "WHERE ch.world_id = ? ORDER BY ch.key",
            (world_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Déplacement ------------------------------------------------------------

    def move_character(self, world_id: int, key: str, target_key: str) -> dict[str, Any]:
        """Déplace un personnage d'une **arête dirigée** à la fois (transaction propre)."""
        with transaction(self._conn) as c:
            return self._move(c, world_id, key, target_key)

    def _move(
        self,
        c: sqlite3.Connection,
        world_id: int,
        key: str,
        target_key: str,
        *,
        sim_now: str | None = None,
        connector_key: str | None = None,
    ) -> dict[str, Any]:
        """Préparation interne du déplacement, à exécuter dans une transaction
        déjà ouverte (c) — utilisée aussi par le démarrage atomique d'activité.

        - refus si le monde est en pause (la pause gèle toute la simulation) ;
        - refus d'un déplacement vers le lieu actuel ;
        - validation d'une seule arête dirigée via `GraphEngine` ;
        - matérialisation canonique de la blessure à `sim_now` (heure simulée
          courante, ou cible fournie par le simulateur) avant classification ;
        - met à jour la position et enregistre `character_moved` dans `c`.
        """
        status = self._conn.execute(
            "SELECT status FROM worlds WHERE id = ?", (world_id,)
        ).fetchone()
        if status is None:
            raise CharacterError(
                f"monde introuvable : {world_id}", code="world_not_found"
            )
        if status["status"] == "paused":
            raise CharacterError(
                "le monde est en pause : aucun déplacement possible",
                code="world_paused",
            )

        # --- garde C-1 : aucun déplacement pendant une activité active ---
        # Une API publique ne doit jamais pouvoir créer une divergence entre la
        # position du personnage et le lieu de son activité active. Refus sans
        # interruption silencieuse : ni position, ni énergie, ni blessure, ni
        # horloge, ni journal ne sont modifiés (rollback de la transaction).
        if self._active_activity_type(world_id, key) is not None:
            raise CharacterError(
                f"déplacement refusé pour {key!r} : une activité est active",
                code="activity_active",
            )

        current = self._conn.execute(
            "SELECT ch.current_location_id, l.key AS cur_key "
            "FROM character ch JOIN location l ON l.id = ch.current_location_id "
            "WHERE ch.world_id = ? AND ch.key = ?",
            (world_id, key),
        ).fetchone()
        if current is None:
            raise CharacterError(
                f"personnage introuvable : {key!r}", code="character_not_found"
            )
        cur_key = current["cur_key"]
        if cur_key == target_key:
            raise CharacterError(
                f"{key!r} est déjà dans {cur_key!r}", code="invalid_destination"
            )

        graph = GraphEngine(self._conn)
        if not graph.can_traverse(world_id, cur_key, target_key):
            raise CharacterError(
                f"pas d'arête dirigée {cur_key!r} → {target_key!r} (déplacement refusé)",
                code="invalid_destination",
            )

        target_id = self._location_id(world_id, target_key)
        connector = None
        if WorldEngine._has_table(self._conn, "world_connector"):
            connector = self._conn.execute(
                "SELECT c.key, c.state FROM location_link ll JOIN world_connector c ON c.id = ll.connector_id "
                "WHERE ll.world_id = ? AND ll.from_location_id = ? AND ll.to_location_id = ?",
                (world_id, current["current_location_id"], target_id),
            ).fetchone()
        if connector_key is not None and (connector is None or connector["key"] != connector_key):
            raise CharacterError("connecteur incompatible avec le déplacement", code="connector_mismatch")
        if connector is not None:
            if connector["state"] == "closed":
                raise CharacterError("connecteur fermé", code="connector_closed")
            if connector["state"] == "blocked":
                raise CharacterError("connecteur bloqué", code="connector_blocked")
            if connector["state"] != "available":
                raise CharacterError("connecteur indisponible", code="connector_unavailable")
            connector_key = connector["key"]

        # --- blessure : matérialisation canonique avant classification (3.3B2) ---
        # La blessure est matérialisée à l'heure simulée courante, dans la même
        # transaction, avec le régime réellement actif (récupération pendant une
        # activité active ; passif sinon). Un refus annule aussi ces matérialisations.
        from_simulator = sim_now is not None
        sim_now = sim_now or self._canonical_time(world_id)
        ie = InjuryEngine(self._conn, clock=self._clock)
        active = ie.active_injury_row(world_id, key)
        surcharge = 0
        effect_level = None
        if active is not None:
            regime = self._active_recovery_regime(world_id, key)
            if from_simulator:
                ie._materialize_injury_sim(world_id, key, sim_now, regime, _conn=c)
            else:
                ie.materialize_injury(world_id, key, sim_now, regime, _conn=c)
            row = ie.active_injury_row(world_id, key)
            sev = row["severity_milli"]
            effect_level = level(sev)
            if effect_level == "severe":
                raise CharacterError(
                    f"blessure sévère : déplacement refusé pour {key!r}",
                    code="injury_severe",
                )
            if effect_level == "moderate":
                ne = NeedsEngine(self._conn, clock=self._clock)
                e_val, e_rem = ne.derive_need(world_id, key, "energie", sim_now)
                if e_val < MOVEMENT_SURCHARGE_MILLI:
                    raise CharacterError(
                        f"énergie insuffisante pour le déplacement "
                        f"(blessure modérée, {key!r})",
                        code="insufficient_energy",
                    )
                new_val = e_val - MOVEMENT_SURCHARGE_MILLI
                new_rem = e_rem if new_val > 0 else 0
                c.execute(
                    "UPDATE need_state SET value_milli = ?, rate_remainder = ?, "
                    "anchor_at = ?, updated_at = ? "
                    "WHERE world_id = ? AND character_id = "
                    "(SELECT id FROM character WHERE world_id = ? AND key = ?) "
                    "AND need_key = 'energie'",
                    (new_val, new_rem, sim_now, self._now_iso(),
                     world_id, world_id, key),
                )
                surcharge = MOVEMENT_SURCHARGE_MILLI

        # Les objets directement portes restent materialises au lieu effectif du
        # porteur. Ce sont des consequences du meme deplacement, pas des
        # deplacements autonomes et donc pas des evenements supplementaires.
        if WorldEngine._has_table(c, "character_carried_object"):
            carried = c.execute(
                "SELECT object_id FROM character_carried_object WHERE world_id = ? AND character_id = "
                "(SELECT id FROM character WHERE world_id = ? AND key = ?)",
                (world_id, world_id, key),
            ).fetchall()
            for carried_row in carried:
                relocate_subtree(c, world_id, carried_row["object_id"], target_id)

        now = self._now_iso()
        c.execute(
            "UPDATE character SET current_location_id = ?, updated_at = ? "
            "WHERE world_id = ? AND key = ?",
            (target_id, now, world_id, key),
        )
        # Contrat stable de `character_moved` : les cinq champs de coût/blessure
        # sont toujours présents, avec des valeurs neutres en l'absence d'effet.
        payload = {
            "character": key,
            "from": cur_key,
            "to": target_key,
            "base_energy_cost": 0,
            "injury_energy_surcharge": surcharge,
            "edge_count": 1,
            "total_energy_cost": surcharge,
            "injury_effect_level": effect_level or "none",
        }
        if connector_key is not None:
            payload["connector"] = connector_key
        _append_event(
            c,
            world_id,
            SOURCE_ENGINE,
            "character_moved",
            payload,
            occurred_at=sim_now, recorded_at=now,
        )
        return self.character_sheet(world_id, key)

    def _canonical_time(self, world_id: int) -> str:
        from .world import WorldEngine  # évite un cycle d'import

        return WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id)

    def _active_activity_type(self, world_id: int, key: str) -> str | None:
        row = self._conn.execute(
            "SELECT a.type FROM activity a "
            "JOIN character ch ON ch.id = a.character_id "
            "WHERE a.world_id = ? AND ch.key = ? AND a.status = 'active' "
            "ORDER BY a.id DESC LIMIT 1",
            (world_id, key),
        ).fetchone()
        return row["type"] if row else None

    def _active_recovery_regime(self, world_id: int, key: str) -> str:
        from .activities import recovery_regime  # lazy, évite le cycle d'import

        atype = self._active_activity_type(world_id, key)
        return recovery_regime(atype) if atype else "passive"


def upgrade_development_world(
    conn: sqlite3.Connection,
    world_id: int,
    clock: Clock | None = None,
) -> list[str]:
    """Procédure de mise à niveau **non destructive** (Lot 3.1).

    Ajoute, dans le monde donné, uniquement les habitantes provisoires manquantes
    (par clé). Idempotente ; refuse de modifier ou remplacer un personnage
    existant ; ne supprime ni monde, ni horloge, ni lieux, ni objets, ni liens,
    ni événements. N'écrit rien si les quatre existent déjà.
    """
    engine = CharacterEngine(conn, clock=clock)
    existing = {r["key"] for r in engine.list_characters(world_id)}
    added: list[str] = []
    for key, name, loc in SEED_CHARACTERS:
        if key in existing:
            continue  # refus de modifier/remplacer un personnage existant
        engine.create_character(world_id, key, name, loc)
        added.append(key)
    return added
