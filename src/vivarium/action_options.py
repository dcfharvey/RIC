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


class ActionOptionService:
    """Transforme des passages déjà perceptibles en options encore légales."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def visible_traversals(
        self, world_id: int, character_key: str, visible: Iterable[Mapping[str, Any]]
    ) -> tuple[ActionOption, ...]:
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
