"""Fondations canoniques inactives de la physiologie veille-sommeil.

Ce module possède les registres de lumière, les profils biologiques et la
préparation technique d'un futur cutover. Il ne calcule pas encore une formule
circadienne, n'ouvre aucune activité et n'est volontairement appelé par aucun
cycle runtime : tant que ``world_physiology_system`` n'est pas cut over dans un
lot ultérieur, le monde conserve intégralement son comportement legacy.

La phase circadienne sera le premier état intégrateur de l'histoire lumineuse.
Si la fonction quantitative retenue exige davantage d'histoire récente, elle
devra soit la reconstruire depuis les causes canoniques, soit ajouter un état
intégrateur minimal owned par ce service. Une lecture ne pourra jamais créer
cette histoire rétroactivement.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Mapping

from .db import transaction
from .util import Clock, new_uuid, parse_iso, to_iso


class SleepPhysiologyError(ValueError):
    """Entrée ou état de fondation physiologique invalide."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class InitialPhysiologyState:
    """Valeurs à valider pour le futur cutover atomique, sans les écrire."""

    homeostatic_load_milli: int
    circadian_phase_milli: int
    physical_capacity_milli: int


def _json(value: Any, *, field: str) -> str:
    if not isinstance(value, Mapping):
        raise SleepPhysiologyError(f"{field} doit être un objet", code="invalid_configuration")
    try:
        return json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise SleepPhysiologyError(f"{field} invalide", code="invalid_configuration") from exc


def _key(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 120:
        raise SleepPhysiologyError(f"{field} invalide", code="invalid_configuration")
    return value


def _version(value: Any, *, field: str = "version") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SleepPhysiologyError(f"{field} invalide", code="invalid_configuration")
    return value


def _at(value: Any) -> str:
    if not isinstance(value, str):
        raise SleepPhysiologyError("instant canonique invalide", code="invalid_canonical_time")
    try:
        return to_iso(parse_iso(value))
    except (TypeError, ValueError) as exc:
        raise SleepPhysiologyError("instant canonique invalide", code="invalid_canonical_time") from exc


class SleepPhysiologyFoundationService:
    """Unique propriétaire des fondations persistantes non comportementales.

    Le statut ``prepared`` est une configuration opérateur sans effet runtime.
    Il ne signifie jamais que la physiologie est active. Le futur lot de
    cutover devra étendre ce contrat, écrire les états initiaux et basculer le
    gate dans une unique transaction hors session runtime.
    """

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _now(self) -> str:
        return self._clock.now_iso()

    @staticmethod
    def _world_id(value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise SleepPhysiologyError("monde invalide", code="invalid_world")
        return value

    def _require_world(self, world_id: int) -> None:
        if self._conn.execute("SELECT 1 FROM worlds WHERE id = ?", (world_id,)).fetchone() is None:
            raise SleepPhysiologyError("monde introuvable", code="world_not_found")

    def _character_id(self, world_id: int, character_key: Any) -> int:
        key = _key(character_key, field="personnage")
        row = self._conn.execute(
            "SELECT id FROM character WHERE world_id = ? AND key = ?", (world_id, key)
        ).fetchone()
        if row is None:
            raise SleepPhysiologyError("personnage introuvable", code="character_not_found")
        return int(row["id"])

    def register_light_schedule(
        self,
        profile_key: Any,
        version: Any,
        schedule: Any,
    ) -> dict[str, Any]:
        """Ajoute un calendrier 24 h immuable, sans l'assigner à un monde."""
        key = _key(profile_key, field="profil lumineux")
        ver = _version(version)
        payload = _json(schedule, field="horaire lumineux")
        now = self._now()
        try:
            with transaction(self._conn) as conn:
                conn.execute(
                    "INSERT INTO light_schedule_profile "
                    "(public_id, profile_key, version, cycle_seconds, schedule_json, created_at) "
                    "VALUES (?, ?, ?, 86400, ?, ?)",
                    (new_uuid(), key, ver, payload, now),
                )
        except sqlite3.IntegrityError as exc:
            raise SleepPhysiologyError("profil lumineux déjà enregistré", code="duplicate_profile") from exc
        return self.light_schedule(key, ver)

    def light_schedule(self, profile_key: Any, version: Any) -> dict[str, Any]:
        key = _key(profile_key, field="profil lumineux")
        ver = _version(version)
        row = self._conn.execute(
            "SELECT profile_key, version, cycle_seconds, schedule_json, created_at "
            "FROM light_schedule_profile WHERE profile_key = ? AND version = ?",
            (key, ver),
        ).fetchone()
        if row is None:
            raise SleepPhysiologyError("profil lumineux introuvable", code="profile_not_found")
        return {
            "profile_key": row["profile_key"], "version": row["version"],
            "cycle_seconds": row["cycle_seconds"], "schedule": json.loads(row["schedule_json"]),
            "created_at": row["created_at"],
        }

    def register_location_light_profile(
        self,
        profile_key: Any,
        version: Any,
        exposure_milli: Any,
        properties: Any,
    ) -> dict[str, Any]:
        """Ajoute une propriété d'exposition, jamais un état lumineux actuel."""
        key = _key(profile_key, field="profil d'exposition")
        ver = _version(version)
        if isinstance(exposure_milli, bool) or not isinstance(exposure_milli, int) or not 0 <= exposure_milli <= 100000:
            raise SleepPhysiologyError("exposition invalide", code="invalid_configuration")
        payload = _json(properties, field="propriétés d'exposition")
        now = self._now()
        try:
            with transaction(self._conn) as conn:
                conn.execute(
                    "INSERT INTO location_light_profile "
                    "(public_id, profile_key, version, exposure_milli, properties_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (new_uuid(), key, ver, exposure_milli, payload, now),
                )
        except sqlite3.IntegrityError as exc:
            raise SleepPhysiologyError("profil d'exposition déjà enregistré", code="duplicate_profile") from exc
        return self.location_light_profile(key, ver)

    def location_light_profile(self, profile_key: Any, version: Any) -> dict[str, Any]:
        key = _key(profile_key, field="profil d'exposition")
        ver = _version(version)
        row = self._conn.execute(
            "SELECT profile_key, version, exposure_milli, properties_json, created_at "
            "FROM location_light_profile WHERE profile_key = ? AND version = ?",
            (key, ver),
        ).fetchone()
        if row is None:
            raise SleepPhysiologyError("profil d'exposition introuvable", code="profile_not_found")
        return {
            "profile_key": row["profile_key"], "version": row["version"],
            "exposure_milli": row["exposure_milli"], "properties": json.loads(row["properties_json"]),
            "created_at": row["created_at"],
        }

    def register_biology_profile(
        self,
        profile_key: Any,
        version: Any,
        evidence_class: Any,
        parameters: Any,
    ) -> dict[str, Any]:
        key = _key(profile_key, field="profil biologique")
        ver = _version(version)
        if evidence_class not in {"human_reference", "generic_feline", "fictional_canon"}:
            raise SleepPhysiologyError("classe biologique invalide", code="invalid_configuration")
        payload = _json(parameters, field="paramètres biologiques")
        now = self._now()
        try:
            with transaction(self._conn) as conn:
                conn.execute(
                    "INSERT INTO sleep_biology_profile "
                    "(public_id, profile_key, version, evidence_class, parameters_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (new_uuid(), key, ver, evidence_class, payload, now),
                )
        except sqlite3.IntegrityError as exc:
            raise SleepPhysiologyError("profil biologique déjà enregistré", code="duplicate_profile") from exc
        return self.biology_profile(key, ver)

    def biology_profile(self, profile_key: Any, version: Any) -> dict[str, Any]:
        key = _key(profile_key, field="profil biologique")
        ver = _version(version)
        row = self._conn.execute(
            "SELECT profile_key, version, evidence_class, parameters_json, created_at "
            "FROM sleep_biology_profile WHERE profile_key = ? AND version = ?",
            (key, ver),
        ).fetchone()
        if row is None:
            raise SleepPhysiologyError("profil biologique introuvable", code="profile_not_found")
        return {
            "profile_key": row["profile_key"], "version": row["version"],
            "evidence_class": row["evidence_class"], "parameters": json.loads(row["parameters_json"]),
            "created_at": row["created_at"],
        }

    def assign_light_schedule(
        self, world_id: Any, profile_key: Any, version: Any, effective_at: Any, provenance: Any
    ) -> None:
        world = self._world_id(world_id)
        self._require_world(world)
        profile = self.light_schedule(profile_key, version)
        at = _at(effective_at)
        origin = _key(provenance, field="provenance")
        profile_id = self._conn.execute(
            "SELECT id FROM light_schedule_profile WHERE profile_key = ? AND version = ?",
            (profile["profile_key"], profile["version"]),
        ).fetchone()["id"]
        try:
            with transaction(self._conn) as conn:
                conn.execute(
                    "INSERT INTO world_light_schedule_assignment "
                    "(public_id, world_id, profile_id, effective_at, provenance, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (new_uuid(), world, profile_id, at, origin, self._now()),
                )
        except sqlite3.IntegrityError as exc:
            raise SleepPhysiologyError("assignation lumineuse déjà présente", code="duplicate_assignment") from exc

    def assign_location_light_profile(
        self, world_id: Any, location_key: Any, profile_key: Any, version: Any,
        effective_at: Any, provenance: Any,
    ) -> None:
        world = self._world_id(world_id)
        self._require_world(world)
        location_key = _key(location_key, field="lieu")
        profile = self.location_light_profile(profile_key, version)
        at = _at(effective_at)
        origin = _key(provenance, field="provenance")
        location = self._conn.execute(
            "SELECT id FROM location WHERE world_id = ? AND key = ?", (world, location_key)
        ).fetchone()
        if location is None:
            raise SleepPhysiologyError("lieu introuvable", code="location_not_found")
        profile_id = self._conn.execute(
            "SELECT id FROM location_light_profile WHERE profile_key = ? AND version = ?",
            (profile["profile_key"], profile["version"]),
        ).fetchone()["id"]
        try:
            with transaction(self._conn) as conn:
                conn.execute(
                    "INSERT INTO world_location_light_assignment "
                    "(public_id, world_id, location_id, profile_id, effective_at, provenance, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (new_uuid(), world, location["id"], profile_id, at, origin, self._now()),
                )
        except sqlite3.IntegrityError as exc:
            raise SleepPhysiologyError("assignation d'exposition déjà présente", code="duplicate_assignment") from exc

    def assign_biology_profile(
        self, world_id: Any, character_key: Any, profile_key: Any, version: Any, provenance: Any
    ) -> None:
        world = self._world_id(world_id)
        self._require_world(world)
        character_id = self._character_id(world, character_key)
        profile = self.biology_profile(profile_key, version)
        origin = _key(provenance, field="provenance")
        profile_id = self._conn.execute(
            "SELECT id FROM sleep_biology_profile WHERE profile_key = ? AND version = ?",
            (profile["profile_key"], profile["version"]),
        ).fetchone()["id"]
        try:
            with transaction(self._conn) as conn:
                conn.execute(
                    "INSERT INTO character_sleep_biology_assignment "
                    "(public_id, world_id, character_id, profile_id, assigned_at, provenance, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (new_uuid(), world, character_id, profile_id, self._now(), origin, self._now()),
                )
        except sqlite3.IntegrityError as exc:
            raise SleepPhysiologyError("profil biologique déjà assigné", code="duplicate_assignment") from exc

    def system_status(self, world_id: Any) -> str:
        world = self._world_id(world_id)
        self._require_world(world)
        row = self._conn.execute(
            "SELECT status FROM world_physiology_system WHERE world_id = ?", (world,)
        ).fetchone()
        return "inactive" if row is None else row["status"]

    def prepare_world(self, world_id: Any, model_key: Any, model_version: Any, prepared_by: Any) -> dict[str, Any]:
        """Marque une configuration complète comme prête, sans l'activer.

        Le futur cutover doit encore vérifier l'absence de session ouverte,
        écrire les états initiaux et basculer tous les consommateurs dans la
        même transaction. Cette méthode ne peut donc pas provoquer un état
        hybride d'exécution.
        """
        world = self._world_id(world_id)
        self._require_world(world)
        key = _key(model_key, field="modèle physiologique")
        ver = _version(model_version, field="version de modèle")
        operator = _key(prepared_by, field="préparé par")
        self._assert_preparable(world)
        now = self._now()
        with transaction(self._conn) as conn:
            row = conn.execute(
                "SELECT status FROM world_physiology_system WHERE world_id = ?", (world,)
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO world_physiology_system "
                    "(public_id, world_id, status, prepared_model_key, prepared_model_version, "
                    "prepared_at, prepared_by, created_at, updated_at) "
                    "VALUES (?, ?, 'prepared', ?, ?, ?, ?, ?, ?)",
                    (new_uuid(), world, key, ver, now, operator, now, now),
                )
            elif row["status"] == "prepared":
                raise SleepPhysiologyError("monde déjà préparé", code="already_prepared")
            else:  # défense explicite si un futur schéma ajoute d'autres états.
                raise SleepPhysiologyError("état physiologique incompatible", code="invalid_system_status")
        return {"world_id": world, "status": "prepared", "model_key": key, "model_version": ver}

    def validate_initial_states(
        self, world_id: Any, states: Mapping[str, InitialPhysiologyState]
    ) -> tuple[str, ...]:
        """Valide des valeurs de cutover sans les persister ni créer d'audit."""
        world = self._world_id(world_id)
        self._require_world(world)
        if not isinstance(states, Mapping):
            raise SleepPhysiologyError("états initiaux invalides", code="invalid_initial_state")
        characters = tuple(
            row["key"] for row in self._conn.execute(
                "SELECT key FROM character WHERE world_id = ? ORDER BY key", (world,)
            )
        )
        if set(states) != set(characters):
            raise SleepPhysiologyError("états initiaux incomplets", code="incomplete_initial_state")
        for character_key in characters:
            state = states[character_key]
            if not isinstance(state, InitialPhysiologyState):
                raise SleepPhysiologyError("état initial invalide", code="invalid_initial_state")
            for value, maximum in (
                (state.homeostatic_load_milli, 100000),
                (state.physical_capacity_milli, 100000),
                (state.circadian_phase_milli, 999999),
            ):
                if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
                    raise SleepPhysiologyError("valeur initiale hors bornes", code="invalid_initial_state")
        return characters

    def _assert_preparable(self, world_id: int) -> None:
        if self._conn.execute(
            "SELECT 1 FROM runtime_session WHERE world_id = ? AND stopped_at IS NULL", (world_id,)
        ).fetchone() is not None:
            raise SleepPhysiologyError("session runtime ouverte", code="runtime_session_open")
        if self._conn.execute(
            "SELECT 1 FROM world_light_schedule_assignment WHERE world_id = ?", (world_id,)
        ).fetchone() is None:
            raise SleepPhysiologyError("calendrier lumineux absent", code="light_schedule_missing")
        locations = self._conn.execute(
            "SELECT id FROM location WHERE world_id = ?", (world_id,)
        ).fetchall()
        assigned = {
            int(row["location_id"])
            for row in self._conn.execute(
                "SELECT DISTINCT location_id FROM world_location_light_assignment WHERE world_id = ?", (world_id,)
            )
        }
        missing_locations = {int(row["id"]) for row in locations} - assigned
        if missing_locations:
            raise SleepPhysiologyError("profils d'exposition incomplets", code="location_light_missing")
        characters = self._conn.execute(
            "SELECT id FROM character WHERE world_id = ?", (world_id,)
        ).fetchall()
        assigned_characters = {
            int(row["character_id"])
            for row in self._conn.execute(
                "SELECT character_id FROM character_sleep_biology_assignment WHERE world_id = ?", (world_id,)
            )
        }
        missing_characters = {int(row["id"]) for row in characters} - assigned_characters
        if missing_characters:
            raise SleepPhysiologyError("profils biologiques incomplets", code="biology_profile_missing")
