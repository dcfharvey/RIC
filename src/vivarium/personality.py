"""Disposition de personnalité canonique, sans décision comportementale.

Le premier contrat couvre les Big Five continus et l'attachement général.
Une disposition décrit une tendance (moyenne, variabilité, inertie et
signatures de situation); elle ne choisit ni action ni dialogue. La conception
de soi et la réputation d'autrui restent des représentations subjectives
séparées, à ajouter seulement avec leurs sources (croyances et perceptions).
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Mapping

from .db import transaction
from .registry import _KEY_RE
from .util import Clock


PERSONALITY_SCHEMA_VERSION = 1
PERSONALITY_COMPONENT_KEY = "personality.big_five_attachment"
TRAIT_KEYS = (
    "extraversion",
    "agreeableness",
    "conscientiousness",
    "openness",
    "stress_reactivity",
)
ATTACHMENT_KEYS = ("anxiety_milli", "avoidance_milli")


class PersonalityError(ValueError):
    """Profil de personnalité invalide, sans écriture partielle."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _milli(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 1000:
        raise PersonalityError(f"{label} invalide", code="invalid_personality_profile")
    return value


def _key(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise PersonalityError(f"{label} invalide", code="invalid_personality_request")
    return value


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def normalize_profile(config: Any) -> dict[str, Any]:
    """Valide le contrat complet avant toute instanciation de personnage."""
    if not isinstance(config, Mapping) or set(config) != {"traits", "attachment"}:
        raise PersonalityError("profil de personnalité invalide", code="invalid_personality_profile")
    raw_traits = config["traits"]
    if not isinstance(raw_traits, Mapping) or set(raw_traits) != set(TRAIT_KEYS):
        raise PersonalityError("traits de personnalité incomplets", code="invalid_personality_profile")
    traits: dict[str, Any] = {}
    for trait_key in TRAIT_KEYS:
        trait = raw_traits[trait_key]
        if not isinstance(trait, Mapping) or set(trait) != {
            "mean_milli", "variability_milli", "inertia_milli", "situation_signatures"
        }:
            raise PersonalityError("distribution de trait invalide", code="invalid_personality_profile")
        signatures = trait["situation_signatures"]
        if not isinstance(signatures, Mapping):
            raise PersonalityError("signatures situationnelles invalides", code="invalid_personality_profile")
        normalized_signatures: dict[str, int] = {}
        for situation_key, adjustment in signatures.items():
            situation_key = _key(situation_key, "signature situationnelle")
            if not isinstance(adjustment, int) or isinstance(adjustment, bool) or not -1000 <= adjustment <= 1000:
                raise PersonalityError("ajustement situationnel invalide", code="invalid_personality_profile")
            normalized_signatures[situation_key] = adjustment
        traits[trait_key] = {
            "mean_milli": _milli(trait["mean_milli"], "moyenne de trait"),
            "variability_milli": _milli(trait["variability_milli"], "variabilité de trait"),
            "inertia_milli": _milli(trait["inertia_milli"], "inertie de trait"),
            "situation_signatures": dict(sorted(normalized_signatures.items())),
        }

    attachment = config["attachment"]
    if not isinstance(attachment, Mapping) or set(attachment) != {"general"}:
        raise PersonalityError("attachement invalide", code="invalid_personality_profile")
    general = attachment["general"]
    if not isinstance(general, Mapping) or set(general) != set(ATTACHMENT_KEYS):
        raise PersonalityError("attachement général invalide", code="invalid_personality_profile")
    return {
        "traits": traits,
        "attachment": {
            "general": {key: _milli(general[key], "attachement") for key in ATTACHMENT_KEYS}
        },
    }


class PersonalityService:
    """Stocke et lit la disposition, sans l'interpréter comme une volonté."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def profile_component(bindings: Any) -> dict[str, Any] | None:
        if not isinstance(bindings, list):
            raise PersonalityError("liaisons de gabarit invalides", code="invalid_personality_profile")
        matches = [binding for binding in bindings if isinstance(binding, Mapping) and binding.get("key") == PERSONALITY_COMPONENT_KEY]
        if len(matches) > 1:
            raise PersonalityError("composant de personnalité dupliqué", code="invalid_personality_profile")
        if not matches:
            return None
        component = matches[0]
        if component.get("version") != 1:
            raise PersonalityError("version de personnalité non supportée", code="unsupported_personality_version")
        return normalize_profile(component.get("config"))

    def initialize_from_template(
        self, world_id: int, character_id: int, bindings: Any, *, _conn: sqlite3.Connection | None = None
    ) -> dict[str, Any] | None:
        """Initialise une seule disposition depuis le gabarit publié d'une instance."""
        profile = self.profile_component(bindings)
        if profile is None:
            return None
        target = _conn or self._conn
        existing = target.execute(
            "SELECT traits_json, attachment_json FROM character_personality_disposition "
            "WHERE world_id = ? AND character_id = ?", (world_id, character_id)
        ).fetchone()
        if existing is not None:
            if (existing["traits_json"], existing["attachment_json"]) != (
                _canonical_json(profile["traits"]), _canonical_json(profile["attachment"])
            ):
                raise PersonalityError("disposition existante incompatible", code="personality_profile_conflict")
            return self.read(world_id, character_id)
        now = self._clock.now_iso()
        target.execute(
            "INSERT INTO character_personality_disposition "
            "(world_id, character_id, schema_version, traits_json, attachment_json, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (world_id, character_id, PERSONALITY_SCHEMA_VERSION, _canonical_json(profile["traits"]),
             _canonical_json(profile["attachment"]), now, now),
        )
        return self.read(world_id, character_id)

    def read(self, world_id: Any, character_key_or_id: Any) -> dict[str, Any] | None:
        if not isinstance(world_id, int) or isinstance(world_id, bool) or world_id < 1:
            raise PersonalityError("monde invalide", code="invalid_personality_request")
        if isinstance(character_key_or_id, int) and not isinstance(character_key_or_id, bool) and character_key_or_id > 0:
            row = self._conn.execute(
                "SELECT * FROM character_personality_disposition WHERE world_id = ? AND character_id = ?",
                (world_id, character_key_or_id),
            ).fetchone()
        else:
            character_key = _key(character_key_or_id, "personnage")
            row = self._conn.execute(
                "SELECT p.* FROM character_personality_disposition p JOIN character ch "
                "ON ch.world_id = p.world_id AND ch.id = p.character_id "
                "WHERE p.world_id = ? AND ch.key = ?", (world_id, character_key),
            ).fetchone()
        if row is None:
            return None
        return {
            "schema_version": row["schema_version"], "traits": json.loads(row["traits_json"]),
            "attachment": json.loads(row["attachment_json"]), "created_at": row["created_at"],
        }

    def situation_modulation(self, world_id: Any, character_key: Any, situation_key: Any) -> dict[str, int]:
        """Expose des ajustements déclaratifs, jamais une action ou une préférence finale."""
        situation_key = _key(situation_key, "situation")
        profile = self.read(world_id, character_key)
        if profile is None:
            return {}
        return {
            trait: data["situation_signatures"].get(situation_key, 0)
            for trait, data in profile["traits"].items()
        }
