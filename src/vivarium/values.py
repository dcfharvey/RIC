"""Valeurs hiérarchisées et préférences initiales, sans commande d'action."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Mapping

from .registry import _KEY_RE
from .util import Clock


VALUES_COMPONENT_KEY = "values.hierarchy"
PREFERENCES_COMPONENT_KEY = "preferences.initial"
VALUES_SCHEMA_VERSION = 1
VALUE_KEYS = (
    "autonomy", "loyalty", "benevolence", "justice", "honesty", "respect_boundaries",
    "duty_responsibility", "achievement", "security_stability", "exploration_freedom",
    "tradition_belonging", "power_status",
)
PREFERENCE_TARGET_KINDS = frozenset({"activity", "object", "person", "context", "social_format"})


class ValuesError(ValueError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _key(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise ValuesError(f"{label} invalide", code="invalid_values_profile")
    return value


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def normalize_value_ranking(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) != len(VALUE_KEYS) or set(value) != set(VALUE_KEYS):
        raise ValuesError("hiérarchie de valeurs incomplète", code="invalid_values_profile")
    return tuple(value)


def normalize_preferences(value: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise ValuesError("préférences invalides", code="invalid_preferences_profile")
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in value:
        if not isinstance(item, Mapping) or set(item) != {"target_kind", "target_key", "valence_milli"}:
            raise ValuesError("préférence invalide", code="invalid_preferences_profile")
        kind = item["target_kind"]
        if kind not in PREFERENCE_TARGET_KINDS:
            raise ValuesError("type de préférence invalide", code="invalid_preferences_profile")
        target = _key(item["target_key"], "cible de préférence")
        valence = item["valence_milli"]
        if not isinstance(valence, int) or isinstance(valence, bool) or not -1000 <= valence <= 1000:
            raise ValuesError("valence de préférence invalide", code="invalid_preferences_profile")
        if (kind, target) in seen:
            raise ValuesError("préférence dupliquée", code="invalid_preferences_profile")
        seen.add((kind, target)); items.append({"target_kind": kind, "target_key": target, "valence_milli": valence})
    return tuple(sorted(items, key=lambda item: (item["target_kind"], item["target_key"])))


class ValuesService:
    """Initialise et lit deux structures subjectives explicitement distinctes."""
    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn, self._clock = conn, clock or Clock()

    @staticmethod
    def _components(bindings: Any) -> tuple[tuple[str, Any], tuple[dict[str, Any], ...]] | None:
        if not isinstance(bindings, list):
            raise ValuesError("liaisons de gabarit invalides", code="invalid_values_profile")
        value = [b for b in bindings if isinstance(b, Mapping) and b.get("key") == VALUES_COMPONENT_KEY]
        preference = [b for b in bindings if isinstance(b, Mapping) and b.get("key") == PREFERENCES_COMPONENT_KEY]
        if not value and not preference:
            return None
        if len(value) != 1 or len(preference) != 1 or value[0].get("version") != 1 or preference[0].get("version") != 1:
            raise ValuesError("composants valeurs/préférences invalides", code="invalid_values_profile")
        return normalize_value_ranking(value[0].get("config", {}).get("ranked_value_keys")), normalize_preferences(preference[0].get("config", {}).get("items"))

    def initialize_from_template(self, world_id: int, character_id: int, bindings: Any, *, _conn: sqlite3.Connection | None = None) -> None:
        components = self._components(bindings)
        if components is None:
            return
        ranking, preferences = components; conn = _conn or self._conn
        if conn.execute("SELECT 1 FROM character_value_profile WHERE world_id = ? AND character_id = ?", (world_id, character_id)).fetchone() is not None:
            raise ValuesError("profil de valeurs déjà présent", code="values_profile_conflict")
        now = self._clock.now_iso()
        conn.execute("INSERT INTO character_value_profile (world_id, character_id, schema_version, ranked_value_keys_json, created_at) VALUES (?, ?, ?, ?, ?)", (world_id, character_id, VALUES_SCHEMA_VERSION, _json(ranking), now))
        conn.execute("INSERT INTO character_preference_profile (world_id, character_id, schema_version, items_json, created_at) VALUES (?, ?, ?, ?, ?)", (world_id, character_id, VALUES_SCHEMA_VERSION, _json(preferences), now))

    def read(self, world_id: int, character_key: str) -> dict[str, Any] | None:
        if not isinstance(world_id, int) or isinstance(world_id, bool) or world_id < 1:
            raise ValuesError("monde invalide", code="invalid_values_request")
        character_key = _key(character_key, "personnage")
        row = self._conn.execute(
            "SELECT v.schema_version, v.ranked_value_keys_json, p.items_json FROM character_value_profile v "
            "JOIN character_preference_profile p ON p.world_id = v.world_id AND p.character_id = v.character_id "
            "JOIN character c ON c.id = v.character_id WHERE v.world_id = ? AND c.key = ?", (world_id, character_key)
        ).fetchone()
        if row is None: return None
        return {"schema_version": row["schema_version"], "ranked_value_keys": json.loads(row["ranked_value_keys_json"]), "preferences": json.loads(row["items_json"])}
