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
from .spatial import GraphError
from .util import Clock
from .world import WorldEngine, WorldError

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
            "world_object_created": "Objet créé",
            "world_object_moved": "Objet déplacé",
            "object_contained": "Objet placé dans un conteneur",
            "object_removed_from_container": "Objet retiré d'un conteneur",
            "environment_blueprint_instantiated": "Environnement instancié",
            "connector_state_changed": "État de connecteur modifié",
        }
        return summaries.get(event_type, f"Événement {event_type}")

    @staticmethod
    def _event_actor(payload: dict[str, Any]) -> str | None:
        """Acteur/personnage concerné lorsque l'information est présente."""
        for key in ("character", "character_key"):
            if key in payload and isinstance(payload[key], str):
                return payload[key]


class AdminCommandService:
    """Commandes administratives sûres (couche application, indépendante de HTTP).

    Dispatcher fermé aux quatre commandes `pause`, `resume`, `rename`, `move`.
    Toute erreur métier est traduite en un code stable ; aucun événement ni
    mutation en cas de refus. Aucun SQL d'écriture, aucun appel à `_append_event`,
    aucun Prepared Change, aucune logique HTTP.
    """

    COMMANDS = frozenset({"pause", "resume", "rename", "move"})

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _world(self) -> WorldEngine:
        return WorldEngine(self._conn, clock=self._clock)

    # --- format de réponse stable -------------------------------------------

    @staticmethod
    def _ok(command: str, data: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "command": command, "data": data, "error": None}

    @staticmethod
    def _err(command: str, code: str, message: str) -> dict[str, Any]:
        return {
            "ok": False,
            "command": command,
            "data": None,
            "error": {"code": code, "message": message},
        }

    # --- validation des paramètres ------------------------------------------

    @staticmethod
    def _require_world_id(world_id: Any) -> None:
        # bool est une sous-classe de int : refuser True/False.
        if isinstance(world_id, bool) or not isinstance(world_id, int):
            raise ValueError("world_id invalide")

    @staticmethod
    def _require_str(value: Any, name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} invalide")

    # --- commandes -----------------------------------------------------------

    def pause(self, world_id: Any) -> dict[str, Any]:
        try:
            self._require_world_id(world_id)
        except ValueError:
            return self._err("pause", "invalid_parameters", "Paramètres invalides.")
        try:
            result = self._world().pause_world(world_id)
        except KeyError:
            return self._err("pause", "world_not_found", "Monde introuvable.")
        except WorldError as e:
            return self._err("pause", e.code, str(e))
        except Exception:
            return self._err("pause", "internal", "Erreur interne.")
        return self._ok("pause", {
            "world_id": result["id"],
            "status": result["status"],
            "observed_canonical_at": self._world().read_canonical_time(world_id),
        })

    def resume(self, world_id: Any) -> dict[str, Any]:
        try:
            self._require_world_id(world_id)
        except ValueError:
            return self._err("resume", "invalid_parameters", "Paramètres invalides.")
        try:
            result = self._world().resume_world(world_id)
        except KeyError:
            return self._err("resume", "world_not_found", "Monde introuvable.")
        except WorldError as e:
            return self._err("resume", e.code, str(e))
        except Exception:
            return self._err("resume", "internal", "Erreur interne.")
        return self._ok("resume", {
            "world_id": result["id"],
            "status": result["status"],
            "observed_canonical_at": self._world().read_canonical_time(world_id),
        })

    def rename(self, world_id: Any, name: Any) -> dict[str, Any]:
        try:
            self._require_world_id(world_id)
            # Prévalidation ergonomique : `name` doit être une chaîne. Les cas
            # vide / espaces / trop long sont laissés au moteur (invalid_name).
            if not isinstance(name, str):
                raise ValueError("name invalide")
        except ValueError:
            return self._err("rename", "invalid_parameters", "Paramètres invalides.")
        try:
            result = self._world().rename_world(world_id, name)
        except KeyError:
            return self._err("rename", "world_not_found", "Monde introuvable.")
        except WorldError as e:
            return self._err("rename", e.code, str(e))
        except Exception:
            return self._err("rename", "internal", "Erreur interne.")
        return self._ok("rename", {
            "world_id": result["id"],
            "name": result["name"],
        })

    def move(
        self, world_id: Any, character_key: Any, destination: Any
    ) -> dict[str, Any]:
        try:
            self._require_world_id(world_id)
            self._require_str(character_key, "character_key")
            self._require_str(destination, "destination")
        except ValueError:
            return self._err("move", "invalid_parameters", "Paramètres invalides.")
        try:
            self._world().get_world(world_id)
        except KeyError:
            return self._err("move", "world_not_found", "Monde introuvable.")
        ce = CharacterEngine(self._conn, clock=self._clock)
        try:
            origin = ce.character_sheet(world_id, character_key)["location_key"]
        except CharacterError:
            return self._err("move", "character_not_found", "Personnage introuvable.")
        except KeyError:
            return self._err("move", "world_not_found", "Monde introuvable.")
        try:
            result = ce.move_character(world_id, character_key, destination)
        except KeyError:
            return self._err("move", "world_not_found", "Monde introuvable.")
        except GraphError:
            return self._err(
                "move", "destination_not_found", "Destination inexistante."
            )
        except CharacterError as e:
            code = e.code if e.code else "character_error"
            return self._err("move", code, str(e))
        except Exception:
            return self._err("move", "internal", "Erreur interne.")
        return self._ok("move", {
            "character": result["key"],
            "from": origin,
            "to": result["location_key"],
            "energy_cost": self._last_move_cost(world_id, character_key),
        })

    def _last_move_cost(self, world_id: int, character_key: str) -> int:
        """Coût énergétique du dernier déplacement (lecture, aucun effet de bord)."""
        row = self._conn.execute(
            "SELECT payload FROM canonical_event WHERE world_id = ? "
            "AND event_type = 'character_moved' "
            "AND json_extract(payload, '$.character') = ? ORDER BY seq DESC LIMIT 1",
            (world_id, character_key),
        ).fetchone()
        if row is None:
            return 0
        return json.loads(row["payload"]).get("total_energy_cost", 0)

    # --- dispatcher fermé ----------------------------------------------------

    def execute(self, command: str, params: Any) -> dict[str, Any]:
        """Route vers l'une des quatre commandes ; aucune résolution dynamique."""
        if not isinstance(params, dict):
            return self._err(command, "invalid_parameters", "Paramètres invalides.")
        if command == "pause":
            return self.pause(params.get("world_id"))
        if command == "resume":
            return self.resume(params.get("world_id"))
        if command == "rename":
            return self.rename(params.get("world_id"), params.get("name"))
        if command == "move":
            return self.move(
                params.get("world_id"),
                params.get("character_key"),
                params.get("destination"),
            )
        return self._err(command, "unknown_command", "Commande inconnue.")
