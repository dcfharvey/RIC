"""Couche de lecture administrative (Phase 4.1A).

`AdminReadService` fournit des vues de lecture pures du moteur canonique,
indépendantes de HTTP. Elle compose les lectures des moteurs et confine les
requêtes SQL de lecture (journal, séquence canonique) dans cette abstraction.

Garanties :
- aucune écriture, aucune matérialisation, aucun événement ;
- aucune modification d'ancre temporelle ;
- les vues composées ouvrent une transaction de lecture SQLite (snapshot
  cohérent) si aucune transaction n'est déjà active ;
- le SQL de lecture n'est dispersé nulle part hors de cette classe.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from typing import Any

from .activities import ActivityEngine, recovery_regime
from .character import CharacterEngine, CharacterError
from .injury import InjuryEngine
from .needs import NeedsEngine
from .util import Clock
from .world import WorldEngine

# Limite maximale de la pagination du journal (lecture bornée).
MAX_JOURNAL_LIMIT = 200


class AdminReadError(RuntimeError):
    """Erreur de lecture administrative (monde ou personnage introuvable)."""


class AdminReadService:
    """Frontière de lecture administrative. Reçoit une connexion SQLite ouverte."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    # --- transaction de lecture (snapshot cohérent) --------------------------

    @contextmanager
    def _read_snapshot(self):
        """Ouvre une transaction de lecture SQLite si aucune n'est active.

        Garantit un snapshot cohérent si un autre processus/connexion écrit
        pendant la construction d'une vue composée. Ne crée pas de transaction
        imbriquée si la connexion est déjà dans une transaction (appelant).
        """
        if self._conn.in_transaction:
            yield
            return
        self._conn.execute("BEGIN")
        try:
            yield
        finally:
            self._conn.execute("ROLLBACK")

    # --- helpers -------------------------------------------------------------

    def _world_engine(self) -> WorldEngine:
        return WorldEngine(self._conn, clock=self._clock)

    def _require_world(self, world_id: int) -> None:
        try:
            self._world_engine().get_world(world_id)
        except KeyError:
            raise AdminReadError(f"monde introuvable : {world_id}") from None

    def _max_seq(self, world_id: int) -> int:
        row = self._conn.execute(
            "SELECT COALESCE(MAX(seq), 0) AS m FROM canonical_event WHERE world_id = ?",
            (world_id,),
        ).fetchone()
        return row["m"] if row else 0

    def _character_view(
        self, world_id: int, character_key: str, observed: str
    ) -> dict[str, Any]:
        """Fiche administrative d'un personnage à l'instant `observed` déjà capturé.

        La blessure est dérivée au régime de récupération réellement applicable
        (régime de l'activité active, `passive` sinon) via `InjuryEngine`.
        """
        ce = CharacterEngine(self._conn, clock=self._clock)
        try:
            sheet = ce.character_sheet(world_id, character_key)
        except CharacterError:
            raise AdminReadError(
                f"personnage introuvable : {character_key!r}"
            ) from None
        needs = NeedsEngine(self._conn, clock=self._clock).derive_character(
            world_id, character_key, observed
        )
        energy = needs.get("energie", {}).get("value_milli")
        activity = ActivityEngine(self._conn, clock=self._clock).activity_sheet(
            world_id, character_key
        )
        regime = recovery_regime(activity["type"]) if activity else "passive"
        injury = InjuryEngine(self._conn, clock=self._clock).injury_sheet_at(
            world_id, character_key, observed, regime
        )
        return {
            "character": {
                "id": sheet["id"],
                "key": sheet["key"],
                "name": sheet["name"],
                "location": sheet["location_key"],
            },
            "needs": needs,
            "energy": energy,
            "activity": activity,
            "injury": injury,
            "observed_canonical_at": observed,
        }

    # --- lectures ------------------------------------------------------------

    def list_worlds(self) -> list[dict[str, Any]]:
        """Liste des mondes disponibles (lecture pure)."""
        return self._world_engine().list_worlds()

    def dashboard(self, world_id: int) -> dict[str, Any]:
        """État général d'un monde + instant canonique observé + dernière séquence."""
        with self._read_snapshot():
            self._require_world(world_id)
            we = self._world_engine()
            observed = we.read_canonical_time(world_id)
            return {
                "world": we.get_world(world_id),
                "observed_canonical_at": observed,
                "last_seq": self._max_seq(world_id),
            }

    def list_character_views(self, world_id: int) -> list[dict[str, Any]]:
        """Vues administratives de tous les personnages, à un instant commun.

        Un seul snapshot de lecture, un seul `observed_canonical_at` pour toute la
        liste, chaque fiche construite à cet instant.
        """
        with self._read_snapshot():
            self._require_world(world_id)
            observed = self._world_engine().read_canonical_time(world_id)
            chars = CharacterEngine(self._conn, clock=self._clock).list_characters(
                world_id
            )
            return [self._character_view(world_id, c["key"], observed) for c in chars]

    def character_view(self, world_id: int, character_key: str) -> dict[str, Any]:
        """Fiche administrative d'un personnage (données réellement disponibles)."""
        with self._read_snapshot():
            self._require_world(world_id)
            observed = self._world_engine().read_canonical_time(world_id)
            return self._character_view(world_id, character_key, observed)

    def journal_view(
        self,
        world_id: int,
        limit: int,
        offset: int = 0,
        include_payload: bool = False,
    ) -> list[dict[str, Any]]:
        """Journal canonique paginé (ordre par seq, borné, sans écriture).

        Lève `AdminReadError` si le monde n'existe pas ; retourne une liste vide
        pour une page au-delà de la dernière séquence. `include_payload=False` par
        défaut ; le payload brut n'est fourni que sur demande explicite.
        """
        # Pagination par OFFSET : acceptable pour le petit journal local du MVP ;
        # pourra être remplacée par une pagination par curseur si le volume devient
        # important (limite documentée A-3, non construite dans 4.1A).
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            raise ValueError("limit doit être un entier strictement positif")
        if limit > MAX_JOURNAL_LIMIT:
            raise ValueError(f"limit ne peut pas dépasser {MAX_JOURNAL_LIMIT}")
        if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
            raise ValueError("offset doit être un entier >= 0")
        with self._read_snapshot():
            self._require_world(world_id)
            rows = self._conn.execute(
                "SELECT seq, event_type, occurred_at, recorded_at, source_kind, payload "
                "FROM canonical_event WHERE world_id = ? ORDER BY seq LIMIT ? OFFSET ?",
                (world_id, limit, offset),
            ).fetchall()
            out: list[dict[str, Any]] = []
            for r in rows:
                payload = json.loads(r["payload"])
                item: dict[str, Any] = {
                    "seq": r["seq"],
                    "event_type": r["event_type"],
                    "occurred_at": r["occurred_at"],
                    "recorded_at": r["recorded_at"],
                    "summary": self._event_summary(r["event_type"], payload),
                    "actor": self._event_actor(payload),
                }
                if include_payload:
                    item["payload"] = payload
                out.append(item)
            return out

    # --- résumés déterministes -----------------------------------------------

    @staticmethod
    def _event_summary(event_type: str, payload: dict[str, Any]) -> str:
        """Résumé administratif déterministe ; générique sûr pour type inconnu."""
        summaries = {
            "world_created": "Monde créé",
            "world_seeded": "Monde peuplé",
            "world_paused": "Monde mis en pause",
            "world_resumed": "Monde repris",
            "world_renamed": "Monde renommé",
            "character_created": "Personnage créé",
            "character_moved": "Personnage déplacé",
            "needs_materialized": "Besoins matérialisés",
            "activity_started": "Activité démarrée",
            "activity_completed": "Activité terminée",
            "activity_aborted": "Activité abandonnée",
            "scripted_accident": "Accident scripté",
            "injury_occurred": "Blessure apparue",
            "injury_materialized": "Blessure matérialisée",
            "injury_healed": "Blessure guérie",
            "clock_updated": "Horloge ajustée",
            "link_added": "Passage ajouté",
            "link_removed": "Passage retiré",
        }
        return summaries.get(event_type, f"Événement {event_type}")

    @staticmethod
    def _event_actor(payload: dict[str, Any]) -> str | None:
        """Acteur/personnage concerné lorsque l'information est présente."""
        for key in ("character", "character_key"):
            if key in payload and isinstance(payload[key], str):
                return payload[key]
        return None
