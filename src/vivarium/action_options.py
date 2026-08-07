"""Projection d'options immédiatement légales, distincte de leur choix.

Une affordance visible n'est pas encore une option présentée au modèle : la
projection vérifie une dernière fois le connecteur réel, son sens et son état.
Cette étape ne classe pas les options, ne modifie pas le monde et ne transforme
pas l'option en intention. Elle réduit simplement l'espace de choix au possible
actuel, conformément au contrat moteur--cognition.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .traversal import TraversalEngine
from .spatial import GraphEngine


AUTONOMOUS_ACTIVITY_TYPES = frozenset({
    "gaming", "photography", "sport", "girly_care", "watch_tv", "socialize",
})


@dataclass(frozen=True)
class ActionOption:
    action_kind: str
    connector_key: str
    target_location_key: str

    def wire(self) -> dict[str, str]:
        return {
            "action_kind": self.action_kind,
            "connector_key": self.connector_key,
            "target_location_key": self.target_location_key,
        }


@dataclass(frozen=True)
class ActivityOption:
    activity_type: str
    target_location_key: str
    duration_seconds: int

    def wire(self) -> dict[str, str | int]:
        return {
            "activity_type": self.activity_type,
            "target_location_key": self.target_location_key,
            "duration_seconds": self.duration_seconds,
        }


class ActionOptionService:
    """Transforme des passages déjà perceptibles en options encore légales."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def visible_traversals(
        self, world_id: int, character_key: str, visible: Iterable[Mapping[str, Any]]
    ) -> tuple[ActionOption, ...]:
        active = self._conn.execute(
            "SELECT 1 FROM activity a JOIN character c ON c.id = a.character_id "
            "WHERE a.world_id = ? AND c.key = ? AND a.status = 'active' LIMIT 1",
            (world_id, character_key),
        ).fetchone()
        # CharacterEngine refuse aussi ce cas. Le filtrer ici évite de présenter
        # au modèle une traversée qui serait immédiatement refusée.
        if active is not None:
            return ()
        candidates: set[tuple[str, str]] = set()
        for item in visible:
            connector = item.get("connector_key", item.get("connector"))
            destination = item.get("target_location_key", item.get("destination"))
            if isinstance(connector, str) and isinstance(destination, str):
                candidates.add((connector, destination))
        engine = TraversalEngine(self._conn)
        options: list[ActionOption] = []
        for connector, destination in sorted(candidates):
            preview = engine.preview(world_id, character_key, connector, destination)
            if preview["allowed"]:
                options.append(ActionOption("traverse", connector, destination))
        return tuple(options)

    def available_activities(self, world_id: int, character_key: str) -> tuple[ActivityOption, ...]:
        """Projette les loisirs atteignables pendant une reservation ``idle``.

        La liste blanche est un vocabulaire moteur, pas une liste generee par
        le modele. Le chemin, le lieu autorise et la duree canonique sont relus
        avant que l'option soit exposee.
        """
        row = self._conn.execute(
            "SELECT a.type, l.key AS current_location FROM character c "
            "JOIN location l ON l.id = c.current_location_id "
            "LEFT JOIN activity a ON a.character_id = c.id AND a.world_id = c.world_id "
            "AND a.status = 'active' WHERE c.world_id = ? AND c.key = ?",
            (world_id, character_key),
        ).fetchone()
        if row is None or row["type"] not in {None, "idle"}:
            return ()
        from .activities import ActivityEngine

        engine = ActivityEngine(self._conn)
        graph = GraphEngine(self._conn)
        options: list[ActivityOption] = []
        for activity_type in sorted(AUTONOMOUS_ACTIVITY_TYPES):
            definition = self._conn.execute(
                "SELECT min_duration_seconds FROM activity_definition "
                "WHERE world_id = ? AND activity_type = ?",
                (world_id, activity_type),
            ).fetchone()
            if definition is None:
                continue
            for destination in sorted(engine.allowed_locations(world_id, activity_type)):
                # ``preview`` ne couvre qu'un connecteur. Ici une activite peut
                # demander un trajet; GraphEngine est deja la source BFS de
                # ActivityEngine et start_activity le reverifiera atomiquement.
                if graph.find_path(world_id, row["current_location"], destination) is not None:
                    options.append(ActivityOption(activity_type, destination, definition["min_duration_seconds"]))
        return tuple(options)
