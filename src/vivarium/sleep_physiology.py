"""Fondations canoniques inactives de la physiologie veille-sommeil.

Ce module possède les registres de lumière, les profils biologiques et la
préparation technique d'un futur cutover. Son raccord persistant peut relire
des états et projeter le noyau sélectionné, mais n'ouvre aucune activité,
n'intègre aucun intervalle et n'est volontairement appelé par aucun cycle
runtime : tant que ``world_physiology_system`` n'est pas cut over dans un lot
ultérieur, le monde conserve intégralement son comportement legacy.

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
from datetime import timedelta, timezone
from typing import Any, Literal, Mapping

from .circadian_model import (
    CircadianModelError,
    CircadianParameters,
    PHASE_TURNS,
    Propensity,
    RegulationInput,
    RegulationState,
    WakeStability,
    advance_regulation,
    sleep_propensity,
    wake_stability,
)
from .db import transaction
from .util import Clock, new_uuid, parse_iso, to_iso


ADDITIVE_MODEL_KEY = "ric.sleep.additive.v1"
_STABILITY_BANDS = {"stable", "fragile", "critical"}
_PHYSICAL_LOAD_CLASSES = frozenset({"none", "light", "moderate", "vigorous"})
# Quantum de banc, lié à la résolution canonique de ce raccord synthétique.
# Il garantit que l'hystérésis n'est pas fonction du découpage demandé par
# l'appelant. Ce n'est ni une cadence runtime ni une constante biologique.
SYNTHETIC_INTEGRATION_QUANTUM_SECONDS = 1


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


@dataclass(frozen=True)
class PersistedPhysiologyState:
    """État physiologique matérialisé, lu sans jamais le faire progresser."""

    model_key: str
    model_version: int
    regulation: RegulationState
    anchor_at: str
    physical_capacity_remainder: int
    homeostatic_load_residue: float
    circadian_phase_residue: float
    previous_stability_band: Literal["stable", "fragile", "critical"]


@dataclass(frozen=True)
class PhysiologyProjection:
    """Projections explicables, dérivées et non persistées."""

    state: PersistedPhysiologyState
    propensity: Propensity
    stability: WakeStability


@dataclass(frozen=True)
class SyntheticMaterialization:
    """Résultat d'un segment de banc ; jamais une activité ou un événement."""

    projection: PhysiologyProjection
    changed: bool


@dataclass(frozen=True)
class SyntheticRegulationSegment:
    """Cause de banc constante jusqu'à une frontière canonique explicite."""

    end_at: str
    source: RegulationInput


@dataclass(frozen=True)
class PhysicalCapacityPolicy:
    """Politique P versionnée, validée mais jamais exécutée dans ce lot.

    Les coefficients sont des entrées de calibration [C/D] du catalogue. Ce
    type n'installe aucune valeur par défaut et ne matérialise jamais P.
    """

    policy_key: str
    version: int
    activity_cost_per_hour_milli: Mapping[str, int]
    minimum_capacity_milli: Mapping[str, int]
    traversal_cost_per_edge_milli: int
    recovery_per_hour_milli: Mapping[str, int]
    provenance: str
    created_at: str


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


def _capacity_milli(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100000:
        raise SleepPhysiologyError(f"{field} invalide", code="invalid_configuration")
    return value


def _physical_capacity_policy_payload(value: Any) -> dict[str, Any]:
    """Valide le contrat de forme sans choisir de calibration.

    La politique ne contient que des coefficients explicitement fournis. Les
    noms de classes sont un vocabulaire de contrat; leurs valeurs restent des
    paramètres versionnés, jamais des constantes cachées du moteur.
    """
    if not isinstance(value, Mapping):
        raise SleepPhysiologyError("politique de capacité invalide", code="invalid_configuration")
    required = {
        "schema_version", "activity_cost_per_hour_milli", "minimum_capacity_milli",
        "traversal_cost_per_edge_milli", "recovery_per_hour_milli",
    }
    if set(value) != required or value["schema_version"] != 1:
        raise SleepPhysiologyError("politique de capacité invalide", code="invalid_configuration")
    activity_cost = value["activity_cost_per_hour_milli"]
    minimum = value["minimum_capacity_milli"]
    recovery = value["recovery_per_hour_milli"]
    if not isinstance(activity_cost, Mapping) or set(activity_cost) != _PHYSICAL_LOAD_CLASSES:
        raise SleepPhysiologyError("coûts d'activité incomplets", code="invalid_configuration")
    if not isinstance(minimum, Mapping) or set(minimum) != _PHYSICAL_LOAD_CLASSES:
        raise SleepPhysiologyError("seuils physiques incomplets", code="invalid_configuration")
    if not isinstance(recovery, Mapping) or set(recovery) != {"rest", "sleep"}:
        raise SleepPhysiologyError("récupérations physiques incomplètes", code="invalid_configuration")
    return {
        "schema_version": 1,
        "activity_cost_per_hour_milli": {
            key: _capacity_milli(activity_cost[key], field=f"coût {key}")
            for key in sorted(_PHYSICAL_LOAD_CLASSES)
        },
        "minimum_capacity_milli": {
            key: _capacity_milli(minimum[key], field=f"seuil {key}")
            for key in sorted(_PHYSICAL_LOAD_CLASSES)
        },
        "traversal_cost_per_edge_milli": _capacity_milli(
            value["traversal_cost_per_edge_milli"], field="coût de traversée"
        ),
        "recovery_per_hour_milli": {
            key: _capacity_milli(recovery[key], field=f"récupération {key}")
            for key in ("rest", "sleep")
        },
    }


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

    def register_physical_capacity_policy(
        self, policy_key: Any, version: Any, policy: Any, provenance: Any
    ) -> PhysicalCapacityPolicy:
        """Ajoute une politique P immutable sans l'assigner ni l'exécuter."""
        key = _key(policy_key, field="politique de capacité")
        ver = _version(version)
        payload = _physical_capacity_policy_payload(policy)
        origin = _key(provenance, field="provenance")
        now = self._now()
        try:
            with transaction(self._conn) as conn:
                conn.execute(
                    "INSERT INTO physical_capacity_policy "
                    "(public_id, policy_key, version, policy_json, provenance, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (new_uuid(), key, ver, _json(payload, field="politique de capacité"), origin, now),
                )
        except sqlite3.IntegrityError as exc:
            raise SleepPhysiologyError("politique de capacité déjà enregistrée", code="duplicate_profile") from exc
        return self.physical_capacity_policy(key, ver)

    def physical_capacity_policy(self, policy_key: Any, version: Any) -> PhysicalCapacityPolicy:
        key = _key(policy_key, field="politique de capacité")
        ver = _version(version)
        row = self._conn.execute(
            "SELECT policy_key, version, policy_json, provenance, created_at "
            "FROM physical_capacity_policy WHERE policy_key = ? AND version = ?", (key, ver)
        ).fetchone()
        if row is None:
            raise SleepPhysiologyError("politique de capacité introuvable", code="profile_not_found")
        payload = _physical_capacity_policy_payload(json.loads(row["policy_json"]))
        return PhysicalCapacityPolicy(
            policy_key=row["policy_key"], version=int(row["version"]),
            activity_cost_per_hour_milli=payload["activity_cost_per_hour_milli"],
            minimum_capacity_milli=payload["minimum_capacity_milli"],
            traversal_cost_per_edge_milli=payload["traversal_cost_per_edge_milli"],
            recovery_per_hour_milli=payload["recovery_per_hour_milli"],
            provenance=row["provenance"], created_at=row["created_at"],
        )

    def assign_physical_capacity_policy(
        self, world_id: Any, policy_key: Any, version: Any, provenance: Any
    ) -> PhysicalCapacityPolicy:
        """Lie un monde à une politique P, sans modifier H/phi/P ni le canon."""
        world = self._world_id(world_id)
        self._require_world(world)
        policy = self.physical_capacity_policy(policy_key, version)
        origin = _key(provenance, field="provenance")
        policy_id = self._conn.execute(
            "SELECT id FROM physical_capacity_policy WHERE policy_key = ? AND version = ?",
            (policy.policy_key, policy.version),
        ).fetchone()["id"]
        now = self._now()
        try:
            with transaction(self._conn) as conn:
                conn.execute(
                    "INSERT INTO world_physical_capacity_policy_assignment "
                    "(public_id, world_id, policy_id, assigned_at, provenance, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (new_uuid(), world, policy_id, now, origin, now),
                )
        except sqlite3.IntegrityError as exc:
            raise SleepPhysiologyError("politique de capacité déjà assignée", code="duplicate_assignment") from exc
        return policy

    def world_physical_capacity_policy(self, world_id: Any) -> PhysicalCapacityPolicy:
        world = self._world_id(world_id)
        self._require_world(world)
        row = self._conn.execute(
            "SELECT p.policy_key, p.version FROM world_physical_capacity_policy_assignment a "
            "JOIN physical_capacity_policy p ON p.id = a.policy_id WHERE a.world_id = ?", (world,)
        ).fetchone()
        if row is None:
            raise SleepPhysiologyError("politique de capacité absente", code="physical_policy_missing")
        return self.physical_capacity_policy(row["policy_key"], int(row["version"]))

    def validate_physical_capacity_configuration(self, world_id: Any) -> PhysicalCapacityPolicy:
        """Valide purement le futur contrat P d'un monde non activé.

        Cette lecture n'active aucun gate, ne matérialise aucun état et ne
        déduit jamais une charge physique de `energie` ou d'un type d'activité.
        """
        policy = self.world_physical_capacity_policy(world_id)
        world = self._world_id(world_id)
        rows = self._conn.execute(
            "SELECT activity_type, requires_sustained_wakefulness, physical_load_class "
            "FROM activity_definition WHERE world_id = ?", (world,)
        ).fetchall()
        for row in rows:
            if row["requires_sustained_wakefulness"] not in (0, 1):
                raise SleepPhysiologyError(
                    "classification de veille absente", code="activity_wakefulness_missing"
                )
            load_class = row["physical_load_class"]
            if load_class not in _PHYSICAL_LOAD_CLASSES:
                raise SleepPhysiologyError(
                    "classification physique absente", code="activity_physical_class_missing"
                )
            if load_class not in policy.activity_cost_per_hour_milli:
                raise SleepPhysiologyError(
                    "classe physique sans politique", code="physical_policy_class_missing"
                )
        return policy

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
        if key != ADDITIVE_MODEL_KEY or ver != 1:
            raise SleepPhysiologyError(
                "modèle physiologique V1 non sélectionné", code="invalid_model"
            )
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


class SleepPhysiologyService:
    """Raccord persistant, déterministe et encore sans branchement runtime.

    Le service est le seul lecteur normalisé des états H/phase/P et de la
    mémoire d'hystérésis. Il n'expose aucune activation, aucune intégration et
    aucune écriture : ces opérations appartiennent à des lots ultérieurs et
    restent bloquées tant que le cutover atomique n'est pas approuvé.
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

    def _character(self, world_id: int, character_key: Any) -> sqlite3.Row:
        key = _key(character_key, field="personnage")
        row = self._conn.execute(
            "SELECT id, key, current_location_id FROM character WHERE world_id = ? AND key = ?",
            (world_id, key),
        ).fetchone()
        if row is None:
            raise SleepPhysiologyError("personnage introuvable", code="character_not_found")
        return row

    def _active_system(self, world_id: int) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT status, prepared_model_key, prepared_model_version "
            "FROM world_physiology_system WHERE world_id = ?",
            (world_id,),
        ).fetchone()
        if row is None or row["status"] != "active":
            raise SleepPhysiologyError("physiologie inactive", code="physiology_inactive")
        if row["prepared_model_key"] != ADDITIVE_MODEL_KEY:
            raise SleepPhysiologyError("modèle physiologique non sélectionné", code="invalid_model")
        return row

    @staticmethod
    def _parameters_from_row(row: sqlite3.Row) -> CircadianParameters:
        try:
            payload = json.loads(row["parameters_json"])
        except (TypeError, ValueError) as exc:
            raise SleepPhysiologyError("profil biologique illisible", code="invalid_profile") from exc
        if not isinstance(payload, Mapping) or payload.get("model_key") != ADDITIVE_MODEL_KEY:
            raise SleepPhysiologyError("profil biologique non additif", code="invalid_model")
        parameters = payload.get("parameters")
        if not isinstance(parameters, Mapping):
            raise SleepPhysiologyError("paramètres biologiques invalides", code="invalid_profile")
        try:
            return CircadianParameters(
                profile_key=row["profile_key"],
                version=int(row["version"]),
                evidence_class=row["evidence_class"],
                **dict(parameters),
            )
        except (CircadianModelError, TypeError, ValueError) as exc:
            raise SleepPhysiologyError("paramètres biologiques invalides", code="invalid_profile") from exc

    def parameters_for_character(self, world_id: Any, character_key: Any) -> CircadianParameters:
        """Lit un profil immuable et impose le modèle production sélectionné."""
        world = self._world_id(world_id)
        character = self._character(world, character_key)
        row = self._conn.execute(
            "SELECT p.profile_key, p.version, p.evidence_class, p.parameters_json "
            "FROM character_sleep_biology_assignment a "
            "JOIN sleep_biology_profile p ON p.id = a.profile_id "
            "WHERE a.world_id = ? AND a.character_id = ?",
            (world, character["id"]),
        ).fetchone()
        if row is None:
            raise SleepPhysiologyError("profil biologique absent", code="biology_profile_missing")
        return self._parameters_from_row(row)

    def read_state(self, world_id: Any, character_key: Any) -> PersistedPhysiologyState:
        """Relit H/phase/P et l'hystérésis sans les matérialiser."""
        world = self._world_id(world_id)
        system = self._active_system(world)
        character = self._character(world, character_key)
        row = self._conn.execute(
            "SELECT r.model_key, r.model_version, r.homeostatic_load_milli, "
            "r.circadian_phase_milli, r.anchor_at AS regulation_anchor_at, "
            "p.capacity_milli, p.rate_remainder, p.anchor_at AS capacity_anchor_at, "
            "h.previous_band, h.anchor_at AS hysteresis_anchor_at, "
            "i.homeostatic_load_residue, i.circadian_phase_residue, "
            "i.anchor_at AS precision_anchor_at "
            "FROM sleep_regulation_state r "
            "JOIN physical_capacity_state p ON p.world_id = r.world_id AND p.character_id = r.character_id "
            "LEFT JOIN sleep_wake_hysteresis_state h ON h.world_id = r.world_id AND h.character_id = r.character_id "
            "LEFT JOIN sleep_regulation_precision_state i "
            "ON i.world_id = r.world_id AND i.character_id = r.character_id "
            "WHERE r.world_id = ? AND r.character_id = ?",
            (world, character["id"]),
        ).fetchone()
        if row is None:
            raise SleepPhysiologyError("état physiologique absent", code="physiology_state_missing")
        if row["model_key"] != ADDITIVE_MODEL_KEY or row["model_key"] != system["prepared_model_key"]:
            raise SleepPhysiologyError("modèle d'état incompatible", code="invalid_model")
        if int(row["model_version"]) != int(system["prepared_model_version"]):
            raise SleepPhysiologyError("version d'état incompatible", code="invalid_model")
        if row["regulation_anchor_at"] != row["capacity_anchor_at"]:
            raise SleepPhysiologyError("ancres physiologiques désalignées", code="inconsistent_anchor")
        if row["previous_band"] is None:
            raise SleepPhysiologyError(
                "mémoire d'hystérésis absente", code="hysteresis_state_missing"
            )
        if row["regulation_anchor_at"] != row["hysteresis_anchor_at"]:
            raise SleepPhysiologyError(
                "ancre d'hystérésis désalignée", code="inconsistent_hysteresis_anchor"
            )
        if row["precision_anchor_at"] is None:
            raise SleepPhysiologyError(
                "résidu d'intégration absent", code="precision_state_missing"
            )
        if row["regulation_anchor_at"] != row["precision_anchor_at"]:
            raise SleepPhysiologyError(
                "ancre de précision désalignée", code="inconsistent_precision_anchor"
            )
        band = row["previous_band"]
        if band not in _STABILITY_BANDS:
            raise SleepPhysiologyError("hystérésis invalide", code="invalid_hysteresis")
        try:
            homeostatic_residue = float(row["homeostatic_load_residue"])
            phase_residue = float(row["circadian_phase_residue"])
            if abs(homeostatic_residue) > 0.5 / 100000.0 + 1e-12:
                raise ValueError("résidu homéostatique hors représentation")
            if abs(phase_residue) > 0.5 / (PHASE_TURNS - 1) + 1e-12:
                raise ValueError("résidu de phase hors représentation")
            regulation = RegulationState(
                int(row["homeostatic_load_milli"]) / 100000.0 + homeostatic_residue,
                (int(row["circadian_phase_milli"]) / (PHASE_TURNS - 1) + phase_residue) % 1.0,
                int(row["capacity_milli"]) / 100000.0,
            )
        except (CircadianModelError, TypeError, ValueError) as exc:
            raise SleepPhysiologyError("état physiologique invalide", code="invalid_physiology_state") from exc
        return PersistedPhysiologyState(
            model_key=row["model_key"],
            model_version=int(row["model_version"]),
            regulation=regulation,
            anchor_at=row["regulation_anchor_at"],
            physical_capacity_remainder=int(row["rate_remainder"]),
            homeostatic_load_residue=homeostatic_residue,
            circadian_phase_residue=phase_residue,
            previous_stability_band=band,
        )

    @staticmethod
    def _schedule_light(schedule: Any, at: str) -> int:
        if not isinstance(schedule, Mapping) or schedule.get("schema_version") != 1:
            raise SleepPhysiologyError("calendrier lumineux invalide", code="invalid_light_schedule")
        segments = schedule.get("segments")
        if not isinstance(segments, list) or not segments:
            raise SleepPhysiologyError("calendrier lumineux incomplet", code="invalid_light_schedule")
        expected_start = 0
        normalized: list[tuple[int, int, int]] = []
        for segment in segments:
            if not isinstance(segment, Mapping):
                raise SleepPhysiologyError("segment lumineux invalide", code="invalid_light_schedule")
            start = segment.get("start_second")
            end = segment.get("end_second")
            light = segment.get("environmental_light_milli")
            if any(isinstance(value, bool) or not isinstance(value, int) for value in (start, end, light)):
                raise SleepPhysiologyError("segment lumineux invalide", code="invalid_light_schedule")
            if start != expected_start or not start < end <= 86400 or not 0 <= light <= 100000:
                raise SleepPhysiologyError("segments lumineux discontinus", code="invalid_light_schedule")
            normalized.append((start, end, light))
            expected_start = end
        if expected_start != 86400:
            raise SleepPhysiologyError("calendrier lumineux incomplet", code="invalid_light_schedule")
        moment = parse_iso(at).astimezone(timezone.utc)
        second = moment.hour * 3600 + moment.minute * 60 + moment.second
        for start, end, light in normalized:
            if start <= second < end:
                return light
        raise SleepPhysiologyError("calendrier lumineux hors plage", code="invalid_light_schedule")

    def resolve_light_source_synthetic(
        self,
        world_id: Any,
        location_key: Any,
        at_time: Any,
        *,
        state: Literal["wake", "rest", "sleep"],
        occluded: bool = False,
        stimulation: float = 0.0,
    ) -> RegulationInput:
        """Résout une cause lumineuse de banc sans dépendre du runtime.

        Ce lecteur accepte un lieu et une frontière canonique explicites. Il ne
        déduit pas un « maintenant » et ne rend pas l'assignation de profil
        rétroactive.
        """
        world = self._world_id(world_id)
        location = _key(location_key, field="lieu")
        at = _at(at_time)
        schedule = self._conn.execute(
            "SELECT p.schedule_json FROM world_light_schedule_assignment a "
            "JOIN light_schedule_profile p ON p.id = a.profile_id "
            "WHERE a.world_id = ? AND a.effective_at <= ? "
            "ORDER BY a.effective_at DESC, a.id DESC LIMIT 1",
            (world, at),
        ).fetchone()
        if schedule is None:
            raise SleepPhysiologyError("calendrier lumineux absent", code="light_schedule_missing")
        profile = self._conn.execute(
            "SELECT p.exposure_milli FROM world_location_light_assignment a "
            "JOIN location l ON l.id = a.location_id AND l.world_id = a.world_id "
            "JOIN location_light_profile p ON p.id = a.profile_id "
            "WHERE a.world_id = ? AND l.key = ? AND a.effective_at <= ? "
            "ORDER BY a.effective_at DESC, a.id DESC LIMIT 1",
            (world, location, at),
        ).fetchone()
        if profile is None:
            raise SleepPhysiologyError("profil d'exposition absent", code="location_light_missing")
        try:
            schedule_payload = json.loads(schedule["schedule_json"])
        except (TypeError, ValueError) as exc:
            raise SleepPhysiologyError("calendrier lumineux illisible", code="invalid_light_schedule") from exc
        return RegulationInput(
            state=state,
            environmental_light_milli=self._schedule_light(schedule_payload, at),
            location_exposure_milli=int(profile["exposure_milli"]),
            occluded=occluded,
            stimulation=stimulation,
        )

    def project_synthetic(
        self, world_id: Any, character_key: Any, source: RegulationInput
    ) -> PhysiologyProjection:
        """Projette propension additive et stabilité sans modifier l'ancre."""
        state = self.read_state(world_id, character_key)
        parameters = self.parameters_for_character(world_id, character_key)
        return PhysiologyProjection(
            state=state,
            propensity=sleep_propensity(state.regulation, parameters, family="additive"),
            stability=wake_stability(
                state.regulation,
                source,
                parameters,
                previous_band=state.previous_stability_band,
            ),
        )

    @staticmethod
    def _seconds_between(anchor_at: str, target_at: str) -> int:
        seconds = (parse_iso(target_at) - parse_iso(anchor_at)).total_seconds()
        if seconds < 0:
            raise SleepPhysiologyError("retour temporel physiologique interdit", code="time_reversal")
        if not seconds.is_integer():
            raise SleepPhysiologyError(
                "frontière physiologique non entière", code="non_integral_canonical_interval"
            )
        return int(seconds)

    @staticmethod
    def _capacity_rate_milli_per_hour(source: RegulationInput, parameters: CircadianParameters) -> int:
        if source.state == "sleep":
            return round(parameters.sleep_capacity_recovery_per_hour * 100000)
        if source.state == "rest":
            return round(parameters.rest_capacity_recovery_per_hour * 100000)
        return -round(parameters.active_capacity_cost_per_hour * 100000)

    @classmethod
    def _advance_capacity(
        cls,
        capacity_milli: int,
        remainder: int,
        source: RegulationInput,
        duration_seconds: int,
        parameters: CircadianParameters,
    ) -> tuple[int, int]:
        """Avance P en milli-unités avec reste rationnel et bornes explicites."""
        if not 0 <= remainder < 3600:
            raise SleepPhysiologyError("reste de capacité invalide", code="invalid_capacity_remainder")
        numerator = (
            cls._capacity_rate_milli_per_hour(source, parameters) * duration_seconds
            + remainder
        )
        delta, remainder = divmod(numerator, 3600)
        next_capacity = capacity_milli + delta
        if next_capacity <= 0:
            return 0, 0
        if next_capacity >= 100000:
            return 100000, 0
        return next_capacity, remainder

    @staticmethod
    def _precision_projection(regulation: RegulationState) -> tuple[int, int, float, float]:
        """Sépare la projection milli-unitaire de son résidu de reprise exact."""
        homeostatic_milli = regulation.homeostatic_load_milli
        phase_milli = regulation.circadian_phase_milli
        homeostatic_residue = regulation.homeostatic_load - homeostatic_milli / 100000.0
        phase = regulation.circadian_phase % 1.0
        phase_residue = phase - phase_milli / (PHASE_TURNS - 1)
        return homeostatic_milli, phase_milli, homeostatic_residue, phase_residue

    def materialize_synthetic(
        self,
        world_id: Any,
        character_key: Any,
        at_time: Any,
        source: RegulationInput,
    ) -> SyntheticMaterialization:
        """Matérialise un segment de banc dans un monde synthétique ``active``.

        Cette API est explicitement hors runtime. Ses causes libres sont
        admissibles seulement pour les bancs : le futur raccord causal devra
        recevoir lumière, activité, occlusion et stimulation de leurs owners
        objectifs/moteur respectifs.
        """
        world = self._world_id(world_id)
        target = _at(at_time)
        with transaction(self._conn) as conn:
            state = self.read_state(world, character_key)
            duration = self._seconds_between(state.anchor_at, target)
            if duration == 0:
                return SyntheticMaterialization(self.project_synthetic(world, character_key, source), False)
            parameters = self.parameters_for_character(world, character_key)
            regulation = state.regulation
            capacity_milli = regulation.physical_capacity_milli
            remainder = state.physical_capacity_remainder
            band = state.previous_stability_band
            stability = wake_stability(regulation, source, parameters, previous_band=band)
            remaining = duration
            while remaining:
                quantum = min(SYNTHETIC_INTEGRATION_QUANTUM_SECONDS, remaining)
                advanced = advance_regulation(regulation, source, quantum, parameters)
                capacity_milli, remainder = self._advance_capacity(
                    capacity_milli, remainder, source, quantum, parameters
                )
                regulation = RegulationState(
                    advanced.homeostatic_load,
                    advanced.circadian_phase,
                    capacity_milli / 100000.0,
                )
                stability = wake_stability(regulation, source, parameters, previous_band=band)
                band = stability.band
                remaining -= quantum
            (
                homeostatic_milli,
                phase_milli,
                homeostatic_residue,
                phase_residue,
            ) = self._precision_projection(regulation)
            character = self._character(world, character_key)
            now = self._now()
            conn.execute(
                "UPDATE sleep_regulation_state SET homeostatic_load_milli = ?, "
                "circadian_phase_milli = ?, anchor_at = ?, updated_at = ? "
                "WHERE world_id = ? AND character_id = ?",
                (
                    homeostatic_milli,
                    phase_milli,
                    target,
                    now,
                    world,
                    character["id"],
                ),
            )
            conn.execute(
                "UPDATE physical_capacity_state SET capacity_milli = ?, rate_remainder = ?, "
                "anchor_at = ?, updated_at = ? WHERE world_id = ? AND character_id = ?",
                (capacity_milli, remainder, target, now, world, character["id"]),
            )
            updated = conn.execute(
                "UPDATE sleep_wake_hysteresis_state SET previous_band = ?, anchor_at = ?, updated_at = ? "
                "WHERE world_id = ? AND character_id = ?",
                (band, target, now, world, character["id"]),
            )
            if updated.rowcount != 1:
                raise SleepPhysiologyError(
                    "mémoire d'hystérésis absente", code="hysteresis_state_missing"
                )
            precision = conn.execute(
                "UPDATE sleep_regulation_precision_state SET homeostatic_load_residue = ?, "
                "circadian_phase_residue = ?, anchor_at = ?, updated_at = ? "
                "WHERE world_id = ? AND character_id = ?",
                (homeostatic_residue, phase_residue, target, now, world, character["id"]),
            )
            if precision.rowcount != 1:
                raise SleepPhysiologyError(
                    "résidu d'intégration absent", code="precision_state_missing"
                )
        return SyntheticMaterialization(
            PhysiologyProjection(
                state=PersistedPhysiologyState(
                    model_key=state.model_key,
                    model_version=state.model_version,
                    regulation=regulation,
                    anchor_at=target,
                    physical_capacity_remainder=remainder,
                    homeostatic_load_residue=homeostatic_residue,
                    circadian_phase_residue=phase_residue,
                    previous_stability_band=band,
                ),
                propensity=sleep_propensity(regulation, parameters, family="additive"),
                stability=stability,
            ),
            True,
        )

    def materialize_segments_synthetic(
        self,
        world_id: Any,
        character_key: Any,
        segments: tuple[SyntheticRegulationSegment, ...],
    ) -> tuple[SyntheticMaterialization, ...]:
        """Applique explicitement des frontières causales de banc dans l'ordre."""
        if not isinstance(segments, tuple):
            raise SleepPhysiologyError("segments synthétiques invalides", code="invalid_segments")
        results: list[SyntheticMaterialization] = []
        for segment in segments:
            if not isinstance(segment, SyntheticRegulationSegment):
                raise SleepPhysiologyError("segment synthétique invalide", code="invalid_segments")
            results.append(
                self.materialize_synthetic(world_id, character_key, segment.end_at, segment.source)
            )
        return tuple(results)

    def next_critical_boundary_synthetic(
        self,
        world_id: Any,
        character_key: Any,
        source: RegulationInput,
        until: Any,
    ) -> str | None:
        """Cherche, sans écrire, une entrée ``critical`` sous causes constantes.

        Le quantum est identique à celui de matérialisation : le résultat ne
        dépend donc pas du partitionnement de l'appelant. Il reste un choix
        numérique de banc, non une cadence runtime ni une règle physiologique.
        """
        state = self.read_state(world_id, character_key)
        target = _at(until)
        remaining = self._seconds_between(state.anchor_at, target)
        parameters = self.parameters_for_character(world_id, character_key)
        regulation = state.regulation
        band = state.previous_stability_band
        cursor = parse_iso(state.anchor_at)
        if band == "critical":
            return state.anchor_at
        while remaining:
            duration = min(SYNTHETIC_INTEGRATION_QUANTUM_SECONDS, remaining)
            advanced = advance_regulation(regulation, source, duration, parameters)
            regulation = RegulationState(
                advanced.homeostatic_load,
                advanced.circadian_phase,
                regulation.physical_capacity,
            )
            stability = wake_stability(regulation, source, parameters, previous_band=band)
            cursor += timedelta(seconds=duration)
            if band != "critical" and stability.band == "critical":
                return to_iso(cursor)
            band = stability.band
            remaining -= duration
        return None
