"""Calibration déclarative de Chuu pour le monde d'intégration MVP.

Cette donnée est une configuration de personnage, jamais une branche du
moteur. Tout futur personnage dépendant d'une ressource utilisera le même
chemin générique de ``ResourceEngine.register_resource_profile``.
"""

from __future__ import annotations

from typing import Any

from .resources import ResourceEngine


CHUU_HYDRATION_PROFILE: dict[str, Any] = {
    "resource_key": "hydration",
    "name": "Hydratation",
    "initial_value_milli": 95000,
    # 100 % à 0 % en 27 h 46 min 40 s, sans apport d'eau.
    "rate_num": -1,
    "rate_den": 1,
    "bands": (
        {"state_key": "puddle_simple", "min_milli": 0, "max_milli": 14999},
        {"state_key": "dehydrated", "min_milli": 15000, "max_milli": 39999},
        {"state_key": "hydrated", "min_milli": 40000, "max_milli": 79999},
        {"state_key": "brilliant", "min_milli": 80000, "max_milli": 100000},
    ),
    "effects_by_state": {
        "puddle_simple": (
            {
                "effect_type": "capability_availability",
                "effect_key": "form.humanoid",
                "availability": "unavailable",
            },
            {
                "effect_type": "capability_availability",
                "effect_key": "cognition.complex_reasoning",
                "availability": "unavailable",
            },
            {
                "effect_type": "context_signal",
                "effect_key": "cognition.clarity",
                "value_milli": -80000,
            },
        ),
        "dehydrated": (
            {
                "effect_type": "capability_availability",
                "effect_key": "form.humanoid",
                "availability": "limited",
            },
            {
                "effect_type": "capability_availability",
                "effect_key": "cognition.complex_reasoning",
                "availability": "limited",
            },
            {
                "effect_type": "context_signal",
                "effect_key": "cognition.clarity",
                "value_milli": -40000,
            },
        ),
        "hydrated": (
            {
                "effect_type": "capability_availability",
                "effect_key": "form.humanoid",
                "availability": "available",
            },
            {
                "effect_type": "capability_availability",
                "effect_key": "cognition.complex_reasoning",
                "availability": "available",
            },
            {
                "effect_type": "context_signal",
                "effect_key": "cognition.clarity",
                "value_milli": 0,
            },
        ),
        "brilliant": (
            {
                "effect_type": "capability_availability",
                "effect_key": "form.humanoid",
                "availability": "available",
            },
            {
                "effect_type": "capability_availability",
                "effect_key": "cognition.complex_reasoning",
                "availability": "available",
            },
            {
                "effect_type": "context_signal",
                "effect_key": "cognition.clarity",
                "value_milli": 80000,
            },
        ),
    },
}


def install_chuu_hydration(
    resources: ResourceEngine, world_id: int, character_key: str = "chuu"
) -> dict[str, Any]:
    """Installe la calibration MVP de Chuu via le mécanisme générique."""
    profile = CHUU_HYDRATION_PROFILE
    return resources.register_resource_profile(
        world_id,
        character_key,
        profile["resource_key"],
        profile["name"],
        profile["initial_value_milli"],
        profile["rate_num"],
        profile["rate_den"],
        profile["bands"],
        profile["effects_by_state"],
    )
