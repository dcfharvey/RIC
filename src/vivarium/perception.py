"""Projection factuelle minimale du canon vers un observateur situé.

Cette couche ne crée ni souvenir, ni croyance, ni certitude subjective. Elle
énumère seulement des candidats accessibles selon des règles explicites de
co-présence et de proximité. Tout ce qui n'est pas projeté reste inconnu.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from .action_contract import PerceptionCandidate, WorldFact
from .registry import _KEY_RE
from .util import Clock
from .world import WorldEngine


class PerceptionError(ValueError):
    """Lecture perceptive invalide, sans effet sur le monde."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class PerceptionSnapshot:
    """Vue pure et déterministe d'un observateur à une heure canonique donnée."""

    observer_key: str
    observed_at: str
    candidates: tuple[PerceptionCandidate, ...]


@dataclass(frozen=True)
class PerceptionEventFeed:
    """Événements propres exportables après un curseur canonique exclusif."""

    observer_key: str
    after_seq: int
    latest_seq: int
    observed_at: str
    candidates: tuple[PerceptionCandidate, ...]


class PerceptionService:
    """Expose une vue locale minimale; aucune donnée interne d'autrui ne fuit."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def _world_id(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise PerceptionError("monde invalide", code="invalid_world")
        return value

    @staticmethod
    def _key(value: Any) -> str:
        if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
            raise PerceptionError("observateur invalide", code="invalid_observer")
        return value

    @staticmethod
    def _after_seq(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise PerceptionError("curseur d'événement invalide", code="invalid_cursor")
        return value

    @staticmethod
    def _self_event_payload(event_type: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Réduit un événement propre au fait pertinent pour son personnage.

        Une projection ne propage ni provenance d'action, ni source admin, ni
        détails techniques de matérialisation. Les événements d'autrui ne sont
        pas encore reconstruits a posteriori : cette règle demandera une
        chronologie spatiale explicite plutôt qu'une supposition sur leur lieu
        actuel.
        """
        fields = {
            "character_moved": ("character", "from", "to", "connector"),
            "activity_started": ("character", "activity", "location", "planned_end_at"),
            "activity_completed": ("character", "activity", "ended_at"),
            "activity_aborted": ("character", "activity"),
            "injury_occurred": ("character", "kind", "severity", "location"),
            "injury_healed": ("character", "kind", "healed_at"),
            "resource_adjusted": ("character", "resource", "delta_milli", "new_value_milli", "new_state"),
        }.get(event_type)
        if fields is None or any(field not in payload for field in fields):
            return None
        return {field: payload[field] for field in fields}

    def snapshot(self, world_id: Any, observer_key: Any) -> PerceptionSnapshot:
        """Retourne les seuls candidats actuellement accessibles à l'observateur."""
        world_id = self._world_id(world_id)
        observer_key = self._key(observer_key)
        observer = self._conn.execute(
            "SELECT ch.id, ch.key, l.id AS location_id, l.key AS location_key "
            "FROM character ch JOIN location l ON l.id = ch.current_location_id "
            "WHERE ch.world_id = ? AND ch.key = ?",
            (world_id, observer_key),
        ).fetchone()
        if observer is None:
            raise PerceptionError("observateur introuvable", code="observer_not_found")
        observed_at = WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id)
        candidates: list[PerceptionCandidate] = [
            PerceptionCandidate(
                observer_key, "self_location",
                WorldFact.state(
                    world_id, "character_location", observed_at,
                    {"character": observer_key, "location": observer["location_key"]},
                ),
            )
        ]

        for row in self._conn.execute(
            "SELECT key FROM character WHERE world_id = ? AND current_location_id = ? "
            "AND id <> ? ORDER BY key",
            (world_id, observer["location_id"], observer["id"]),
        ):
            candidates.append(PerceptionCandidate(
                observer_key, "co_presence",
                WorldFact.state(
                    world_id, "character_present", observed_at,
                    {"character": row["key"], "location": observer["location_key"]},
                ),
            ))

        # Seuls les objets top-level non transportés sont publiquement visibles.
        # Un téléphone dans une poche n'est pas supposé visible sans futur contrat
        # d'équipement, d'exposition ou de fouille.
        for row in self._conn.execute(
            "SELECT o.key, o.kind, o.state, o.portable FROM world_object o "
            "WHERE o.world_id = ? AND o.location_id = ? AND o.parent_object_id IS NULL "
            "AND NOT EXISTS (SELECT 1 FROM character_carried_object co WHERE co.object_id = o.id) "
            "ORDER BY o.key",
            (world_id, observer["location_id"]),
        ):
            candidates.append(PerceptionCandidate(
                observer_key, "local_object",
                WorldFact.state(
                    world_id, "object_present", observed_at,
                    {
                        "object": row["key"], "kind": row["kind"], "state": row["state"],
                        "portable": bool(row["portable"]), "location": observer["location_key"],
                    },
                ),
            ))

        for row in self._conn.execute(
            "SELECT c.key, c.state, c.directions, "
            "CASE WHEN c.from_location_id = ? THEN destination.key ELSE origin.key END AS destination_key "
            "FROM world_connector c "
            "JOIN location origin ON origin.id = c.from_location_id "
            "JOIN location destination ON destination.id = c.to_location_id "
            "WHERE c.world_id = ? AND (? = c.from_location_id OR ? = c.to_location_id) "
            "ORDER BY c.key",
            (observer["location_id"], world_id, observer["location_id"], observer["location_id"]),
        ):
            candidates.append(PerceptionCandidate(
                observer_key, "adjacent_connector",
                WorldFact.state(
                    world_id, "connector_adjacent", observed_at,
                    {
                        "connector": row["key"], "destination": row["destination_key"],
                        "state": row["state"], "directions": row["directions"],
                    },
                ),
            ))

        return PerceptionSnapshot(observer_key, observed_at, tuple(candidates))

    def events_since(
        self, world_id: Any, observer_key: Any, after_seq: Any = 0
    ) -> PerceptionEventFeed:
        """Retourne les changements directs d'une résidente depuis un curseur.

        Le curseur peut avancer jusqu'à `latest_seq` même quand aucun fait n'a
        été exporté; les événements futurs auront nécessairement une séquence
        plus grande. La lecture reste sans écriture ni accusé de réception
        persistant : la future cognition gardera son propre curseur révisable.
        """
        world_id = self._world_id(world_id)
        observer_key = self._key(observer_key)
        after_seq = self._after_seq(after_seq)
        # Valide l'existence de l'observateur et fixe l'instant sans fabriquer
        # d'état perceptif ou de mémoire.
        snapshot = self.snapshot(world_id, observer_key)
        latest_row = self._conn.execute(
            "SELECT COALESCE(MAX(seq), 0) AS latest_seq FROM canonical_event WHERE world_id = ?",
            (world_id,),
        ).fetchone()
        latest_seq = latest_row["latest_seq"]
        if after_seq > latest_seq:
            raise PerceptionError("curseur d'événement au-delà du journal", code="invalid_cursor")

        candidates: list[PerceptionCandidate] = []
        rows = self._conn.execute(
            "SELECT seq, event_type, occurred_at, payload FROM canonical_event "
            "WHERE world_id = ? AND seq > ? ORDER BY seq",
            (world_id, after_seq),
        )
        for row in rows:
            payload = json.loads(row["payload"])
            if payload.get("character") != observer_key:
                continue
            public_payload = self._self_event_payload(row["event_type"], payload)
            if public_payload is None:
                continue
            candidates.append(PerceptionCandidate(
                observer_key,
                "self_event",
                WorldFact.event(
                    world_id,
                    row["seq"],
                    row["event_type"],
                    row["occurred_at"],
                    public_payload,
                ),
            ))
        return PerceptionEventFeed(
            observer_key, after_seq, latest_seq, snapshot.observed_at, tuple(candidates)
        )
