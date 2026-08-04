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
from .seed import SEED_CHARACTERS
from .util import Clock, new_uuid
from .world import SOURCE_ENGINE, SOURCE_SYSTEM, _append_event
from .spatial import GraphEngine


class CharacterError(RuntimeError):
    """Erreur de personnage (personnage ou lieu introuvable, mouvement refusé)."""


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
                recorded_at=now,
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
        self, c: sqlite3.Connection, world_id: int, key: str, target_key: str
    ) -> dict[str, Any]:
        """Préparation interne du déplacement, à exécuter dans une transaction
        déjà ouverte (c) — utilisée aussi par le démarrage atomique d'activité.

        - refus si le monde est en pause (la pause gèle toute la simulation) ;
        - refus d'un déplacement vers le lieu actuel ;
        - validation d'une seule arête dirigée via `GraphEngine` ;
        - met à jour la position et enregistre `character_moved` dans `c`.
        """
        status = self._conn.execute(
            "SELECT status FROM worlds WHERE id = ?", (world_id,)
        ).fetchone()
        if status is None:
            raise CharacterError(f"monde introuvable : {world_id}")
        if status["status"] == "paused":
            raise CharacterError("le monde est en pause : aucun déplacement possible")

        current = self._conn.execute(
            "SELECT ch.current_location_id, l.key AS cur_key "
            "FROM character ch JOIN location l ON l.id = ch.current_location_id "
            "WHERE ch.world_id = ? AND ch.key = ?",
            (world_id, key),
        ).fetchone()
        if current is None:
            raise CharacterError(f"personnage introuvable : {key!r}")
        cur_key = current["cur_key"]
        if cur_key == target_key:
            raise CharacterError(f"{key!r} est déjà dans {cur_key!r}")

        graph = GraphEngine(self._conn)
        if not graph.can_traverse(world_id, cur_key, target_key):
            raise CharacterError(
                f"pas d'arête dirigée {cur_key!r} → {target_key!r} (déplacement refusé)"
            )

        now = self._now_iso()
        target_id = self._location_id(world_id, target_key)
        c.execute(
            "UPDATE character SET current_location_id = ?, updated_at = ? "
            "WHERE world_id = ? AND key = ?",
            (target_id, now, world_id, key),
        )
        _append_event(
            c,
            world_id,
            SOURCE_ENGINE,
            "character_moved",
            {"character": key, "from": cur_key, "to": target_key},
            recorded_at=now,
        )
        return self.character_sheet(world_id, key)


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
