"""Projection factuelle minimale du canon vers un observateur situé.

Cette couche ne crée ni souvenir, ni croyance, ni certitude subjective. Elle
énumère seulement des candidats accessibles selon des règles explicites de
co-présence et de proximité. Tout ce qui n'est pas projeté reste inconnu.
"""

from __future__ import annotations

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
