"""Gabarits initiaux du casting MVP, sans instanciation de monde."""

from __future__ import annotations

import sqlite3
from typing import Any

from .mvp_catalog import install_mvp_component_catalog
from .templates import CharacterTemplateService, TemplateError


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


def _distribution(mean: int, variability: int, inertia: int, **signatures: int) -> dict[str, Any]:
    return {
        "mean_milli": mean,
        "variability_milli": variability,
        "inertia_milli": inertia,
        "situation_signatures": signatures,
    }


def _personality(
    *, extraversion: int, agreeableness: int, conscientiousness: int, openness: int,
    stress_reactivity: int, attachment_anxiety: int, attachment_avoidance: int,
) -> dict[str, Any]:
    """Calibration MVP révisable, fondée sur les descriptions gelées du casting."""
    return {
        "traits": {
            "extraversion": _distribution(extraversion, 180, 760, social_context=120),
            "agreeableness": _distribution(agreeableness, 140, 800, interpersonal_conflict=-100),
            "conscientiousness": _distribution(conscientiousness, 130, 820, planned_routine=80),
            "openness": _distribution(openness, 190, 700, novel_option=100),
            "stress_reactivity": _distribution(stress_reactivity, 170, 720, threat_or_uncertainty=140),
        },
        "attachment": {"general": {
            "anxiety_milli": attachment_anxiety, "avoidance_milli": attachment_avoidance,
        }},
    }


_MVP_PERSONALITY_CONFIGS = {
    "resident.sophie": _personality(
        extraversion=330, agreeableness=350, conscientiousness=730, openness=700,
        stress_reactivity=600, attachment_anxiety=420, attachment_avoidance=620,
    ),
    "resident.erika": _personality(
        extraversion=790, agreeableness=600, conscientiousness=260, openness=720,
        stress_reactivity=360, attachment_anxiety=320, attachment_avoidance=350,
    ),
    "resident.luna": _personality(
        extraversion=610, agreeableness=430, conscientiousness=640, openness=470,
        stress_reactivity=540, attachment_anxiety=380, attachment_avoidance=520,
    ),
    "resident.chuu": _personality(
        extraversion=620, agreeableness=710, conscientiousness=360, openness=800,
        stress_reactivity=480, attachment_anxiety=450, attachment_avoidance=350,
    ),
}


def _mvp_v2_template(
    key: str, definition: dict[str, Any], components: tuple[dict[str, Any], ...]
) -> tuple[str, dict[str, Any], tuple[dict[str, Any], ...]]:
    profile = _MVP_PERSONALITY_CONFIGS.get(key)
    if profile is None:
        return key, definition, components
    return key, definition, (*components, _component("personality.big_five_attachment", profile))


MVP_CHARACTER_TEMPLATES_V2 = tuple(_mvp_v2_template(*entry) for entry in MVP_CHARACTER_TEMPLATES)


def install_mvp_character_templates(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Installe les gabarits du casting après le catalogue de composants."""
    install_mvp_component_catalog(conn)
    return CharacterTemplateService(conn).install_published_catalog(MVP_CHARACTER_TEMPLATES)


def install_mvp_personality_templates(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Publie les versions 2 exécutables sans altérer les gabarits v1 gelés."""
    install_mvp_character_templates(conn)
    service = CharacterTemplateService(conn)
    installed: list[dict[str, Any]] = []
    for key, definition, components in MVP_CHARACTER_TEMPLATES_V2:
        try:
            existing = service.get_version(key, 2)
        except TemplateError as exc:
            if "modèle introuvable" not in str(exc):
                raise
            existing = None
        if existing is None:
            draft = service.create_draft(key, definition, components)
            installed.append(service.publish(key, draft["version"]))
            continue
        expected = {"definition": definition, "components": list(components)}
        actual = {"definition": existing["definition"], "components": existing["components"]}
        if existing["status"] != "published" or actual != expected:
            raise RuntimeError(f"version 2 de gabarit MVP incompatible : {key}")
        installed.append(existing)
    return installed
