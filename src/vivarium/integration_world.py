"""Assemblage atomique du premier monde d'intégration, sans seed spécial."""

from __future__ import annotations

import sqlite3
from typing import Any

from .db import transaction
from .environment_blueprints import EnvironmentBlueprintService
from .initial_context import InitialContextService
from .initial_residence import install_initial_residence_catalog
from .instances import CharacterInstanceService
from .mvp_chuu import install_chuu_hydration
from .mvp_templates import install_mvp_character_templates
from .resources import ResourceEngine
from .util import Clock
from .world_rules import WorldRuleService


INITIAL_SHARED_FACTS = {
    "residency": {
        "voluntary": True,
        "shared_residence": True,
        "expenses_covered": True,
        "personal_allowance": True,
    },
    "prior_relationships": {"shared_history_known": False},
    "administration": {"purpose_known": False, "administrator_identity_known": False},
    "knowledge_boundary": {"only_declared_facts": True},
}

INITIAL_RESIDENTS = (
    ("resident.sophie", "sophie"),
    ("resident.erika", "erika"),
    ("resident.luna", "luna"),
    ("resident.chuu", "chuu"),
    ("resident.patoune", "patoune"),
)


class IntegrationWorldService:
    """Crée le monde de validation MVP : tout est créé ou tout est annulé."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def create_initial_world(
        self, name: Any = "Résidence d'intégration", *, shared_facts: Any = INITIAL_SHARED_FACTS
    ) -> dict[str, Any]:
        """Assemble environnement, règles, résidentes, Chuu et contexte commun."""
        with transaction(self._conn):
            install_initial_residence_catalog(self._conn)
            install_mvp_character_templates(self._conn)
            world = EnvironmentBlueprintService(self._conn, clock=self._clock).instantiate(
                "residence.initial", 1, world_name=name
            )
            world_id = world["id"]
            WorldRuleService(self._conn, clock=self._clock).install_standard_residence_rules(world_id)
            instances = CharacterInstanceService(self._conn, clock=self._clock)
            for template_key, character_key in INITIAL_RESIDENTS:
                instances.instantiate(world_id, template_key, 1, character_key, "entree_exterieure")
            install_chuu_hydration(ResourceEngine(self._conn, clock=self._clock), world_id)
            InitialContextService(self._conn, clock=self._clock).set_shared_facts(world_id, shared_facts)
        return world
