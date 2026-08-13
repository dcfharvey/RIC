"""Assemblage pré-rodage V2 composable et jetable.

Ce service orchestre uniquement des services canoniques existants. Il ne crée
aucune histoire spéciale à un personnage : le scénario fournit explicitement
les lieux, activités, objets et plans qu'il souhaite représenter.
"""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Any, Iterable

from .activities import ActivityEngine
from .db import transaction
from .external_locations import ExternalLocationService
from .location_plans import LocationPlanService
from .objects import ObjectService
from .possession import PossessionService
from .util import Clock


@dataclass(frozen=True)
class ExternalPlaceSpec:
    key: str
    name: str
    boundary_key: str
    kind: str = "external"
    capacity: int | None = None


@dataclass(frozen=True)
class ActivityStartSpec:
    character_key: str
    activity_type: str
    location_key: str
    duration_seconds: int | None = None


@dataclass(frozen=True)
class CarriedObjectSpec:
    character_key: str
    object_key: str
    name: str
    kind: str = "personal_effects"


class RodageV2BootstrapService:
    """Prépare un scénario T0 sur une base neuve sans ouvrir une histoire officielle."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def add_external_places(self, world_id: int, places: Iterable[ExternalPlaceSpec]) -> tuple[dict[str, Any], ...]:
        service = ExternalLocationService(self._conn, clock=self._clock)
        with transaction(self._conn):
            return tuple(
                service.add(
                    world_id, place.key, place.name, boundary_key=place.boundary_key,
                    kind=place.kind, capacity=place.capacity,
                )
                for place in places
            )

    def start_activities(self, world_id: int, activities: Iterable[ActivityStartSpec]) -> tuple[dict[str, Any], ...]:
        engine = ActivityEngine(self._conn, clock=self._clock)
        with transaction(self._conn):
            return tuple(
                engine.start_activity(
                    world_id, item.character_key, item.activity_type, item.location_key,
                    duration_seconds=item.duration_seconds,
                )
                for item in activities
            )

    def plan_locations(self, world_id: int, plans: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
        service = LocationPlanService(self._conn, clock=self._clock)
        with transaction(self._conn):
            return tuple(service.plan(world_id, **plan) for plan in plans)

    def give_carried_objects(self, world_id: int, objects: Iterable[CarriedObjectSpec]) -> tuple[dict[str, Any], ...]:
        object_service = ObjectService(self._conn, clock=self._clock)
        possession = PossessionService(self._conn, clock=self._clock)
        result = []
        with transaction(self._conn):
            for item in objects:
                character = self._conn.execute(
                    "SELECT l.key FROM character c JOIN location l ON l.id=c.current_location_id "
                    "WHERE c.world_id=? AND c.key=?", (world_id, item.character_key)
                ).fetchone()
                if character is None:
                    raise ValueError(f"personnage introuvable : {item.character_key}")
                object_service.create_object(
                    world_id, item.object_key, item.name, item.kind, character["key"],
                    portable=True,
                )
                result.append(possession.pick_up(world_id, item.character_key, item.object_key))
        return tuple(result)
