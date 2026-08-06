"""Gabarits initiaux du casting MVP, sans instanciation de monde."""

from __future__ import annotations

import sqlite3
from typing import Any

from .mvp_catalog import install_mvp_component_catalog
from .templates import CharacterTemplateService


def _component(key: str, config: dict[str, Any]) -> dict[str, Any]:
    return {"key": key, "version": 1, "config": config}


MVP_CHARACTER_TEMPLATES: tuple[tuple[str, dict[str, Any], tuple[dict[str, Any], ...]], ...] = (
    (
        "resident.sophie",
        {"name": "Sophie", "adult": True},
        (
            _component("body.morphology", {"body_plan": "bipedal"}),
            _component("cognition.profile", {"level": "sapient"}),
            _component("needs.standard", {}),
            _component("appearance.descriptive", {"summary": "femme humaine"}),
            _component(
                "personality.initial_dispositions",
                {"summary": "photoreporter tsundere, sarcastique et sèche"},
            ),
        ),
    ),
    (
        "resident.erika",
        {"name": "Erika", "adult": True},
        (
            _component("body.morphology", {"body_plan": "bipedal"}),
            _component("cognition.profile", {"level": "sapient"}),
            _component("needs.standard", {}),
            _component("appearance.descriptive", {"summary": "femme humaine"}),
            _component(
                "personality.initial_dispositions",
                {"summary": "spontanée, sans inhibition marquée, vit au jour le jour et aime le gaming"},
            ),
        ),
    ),
    (
        "resident.luna",
        {"name": "Luna", "adult": True},
        (
            _component("body.morphology", {"body_plan": "bipedal"}),
            _component("cognition.profile", {"level": "sapient"}),
            _component("needs.standard", {}),
            _component(
                "appearance.descriptive",
                {"summary": "louve anthropomorphe, grande et forte"},
            ),
            _component(
                "personality.initial_dispositions",
                {"summary": "edgy assumée, sportive et bagarreuse; apprécie secrètement les choses girly"},
            ),
        ),
    ),
    (
        "resident.chuu",
        {"name": "Chuu", "adult": True},
        (
            _component("body.morphology", {"body_plan": "amorphous"}),
            _component("cognition.profile", {"level": "sapient"}),
            _component("needs.standard", {}),
            _component("appearance.descriptive", {"summary": "slime à apparence féminine"}),
            _component(
                "physiology.resource_dependent_state",
                {
                    "resource_key": "hydration",
                    "high_state": "brilliant",
                    "low_state": "puddle_simple",
                },
            ),
        ),
    ),
    (
        "resident.patoune",
        {"name": "Patoune", "adult": True},
        (
            _component("body.morphology", {"body_plan": "quadrupedal"}),
            _component("cognition.profile", {"level": "non_sapient"}),
            _component("needs.standard", {}),
            _component(
                "appearance.descriptive",
                {"summary": "chatte noire dont seuls les yeux sont visibles dans le noir"},
            ),
        ),
    ),
)


def install_mvp_character_templates(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Installe les gabarits du casting après le catalogue de composants."""
    install_mvp_component_catalog(conn)
    return CharacterTemplateService(conn).install_published_catalog(MVP_CHARACTER_TEMPLATES)
