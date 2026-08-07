"""Catalogue initial minimal des composants du MVP.

Les contrats descriptifs ne donnent encore aucune capacité au moteur : ils
servent à créer des gabarits explicites et à éviter les branchements par espèce.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from .registry import RegistryService

MVP_COMPONENT_CATALOG: tuple[tuple[str, str, dict[str, Any]], ...] = (
    (
        "component",
        "body.morphology",
        {
            "title": "Morphologie déclarée",
            "engine_status": "descriptive_only",
            "config_schema": {
                "required": ["body_plan"],
                "properties": {
                    "body_plan": {
                        "type": "string",
                        "enum": ["bipedal", "quadrupedal", "amorphous"],
                    }
                },
                "additional_properties": False,
            },
        },
    ),
    (
        "component",
        "cognition.profile",
        {
            "title": "Profil cognitif déclaré",
            "engine_status": "descriptive_only",
            "config_schema": {
                "required": ["level"],
                "properties": {
                    "level": {"type": "string", "enum": ["sapient", "non_sapient"]}
                },
                "additional_properties": False,
            },
        },
    ),
    (
        "component",
        "behavior.non_sapient_agency",
        {
            "title": "Agence autonome non sapiente",
            "engine_status": "implemented_cat0",
            "config_schema": {
                "required": [
                    "policy", "wake_interval_seconds", "max_obstacle_retries",
                    "preferred_location_functions",
                ],
                "properties": {
                    "policy": {"type": "string", "enum": ["reactive_associative"]},
                    "wake_interval_seconds": {"type": "integer"},
                    "max_obstacle_retries": {"type": "integer"},
                    "preferred_location_functions": {"type": "array"},
                },
                "additional_properties": False,
            },
        },
    ),
    (
        "component",
        "needs.standard",
        {
            "title": "Besoins standards du moteur MVP",
            "engine_status": "implemented_need_state",
            "config_schema": {
                "required": [],
                "properties": {},
                "additional_properties": False,
            },
        },
    ),
    (
        "component",
        "appearance.descriptive",
        {
            "title": "Apparence descriptive",
            "engine_status": "descriptive_only",
            "config_schema": {
                "required": ["summary"],
                "properties": {"summary": {"type": "string"}},
                "additional_properties": False,
            },
        },
    ),
    (
        "component",
        "personality.initial_dispositions",
        {
            "title": "Dispositions initiales",
            "engine_status": "descriptive_only",
            "config_schema": {
                "required": ["summary"],
                "properties": {"summary": {"type": "string"}},
                "additional_properties": False,
            },
        },
    ),
    (
        "component",
        "personality.big_five_attachment",
        {
            "title": "Disposition Big Five et attachement général",
            "engine_status": "implemented_canonical_disposition",
            "config_schema": {
                "required": ["traits", "attachment"],
                "properties": {
                    "traits": {"type": "object"},
                    "attachment": {"type": "object"},
                },
                "additional_properties": False,
            },
        },
    ),
    (
        "component",
        "values.hierarchy",
        {"title": "Hiérarchie de valeurs", "engine_status": "implemented_canonical_values",
         "config_schema": {"required": ["ranked_value_keys"], "properties": {"ranked_value_keys": {"type": "array"}}, "additional_properties": False}},
    ),
    (
        "component",
        "preferences.initial",
        {"title": "Préférences initiales", "engine_status": "implemented_canonical_preferences",
         "config_schema": {"required": ["items"], "properties": {"items": {"type": "array"}}, "additional_properties": False}},
    ),
    (
        "component",
        "physiology.resource_dependent_state",
        {
            "title": "État dépendant d'une ressource physiologique",
            "engine_status": "future_canonical_state",
            "config_schema": {
                "required": ["resource_key", "high_state", "low_state"],
                "properties": {
                    "resource_key": {"type": "string"},
                    "high_state": {"type": "string"},
                    "low_state": {"type": "string"},
                },
                "additional_properties": False,
            },
        },
    ),
)


def install_mvp_component_catalog(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Installe le catalogue MVP de manière idempotente et sans écrasement."""
    return RegistryService(conn).install_published_catalog(MVP_COMPONENT_CATALOG)
