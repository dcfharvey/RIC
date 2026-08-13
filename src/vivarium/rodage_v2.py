"""Bootstrap propre et reproductible du monde de rodage V2.

Ce module décrit un scénario initial; il ne spécialise aucun moteur au nom d'un
personnage. Les différences Sophie/Erika/Luna/Chuu/Patoune sont des faits T0
produits par les services génériques de RIC (lieux, activités, possession,
ressources, physiologie), puis les moteurs ordinaires reprennent la main.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from .action_arbitration import ActionArbitrationFoundationService
from .activities import ActivityEngine, upgrade_dev_activities
from .circadian_model import RegulationState, calibration_profiles, wake_stability
from .environment_archetypes import EnvironmentArchetypeService
from .environment_blueprints import EnvironmentBlueprintService
from .initial_context import SharedInitialContextService
from .initial_residence import INITIAL_RESIDENCE_BLUEPRINT, install_initial_residence_catalog
from .instances import CharacterInstanceService
from .mvp_chuu import install_chuu_hydration
from .mvp_preflight import inspect_mvp_preflight
from .mvp_templates import install_mvp_templates_v4
from .objects import ObjectService
from .possession import PossessionService
from .resources import ResourceEngine
from .runtime_session import RuntimeSessionService
from .sleep_physiology import (
    ADDITIVE_MODEL_KEY,
    InitialPhysiologyManifestEntry,
    SleepPhysiologyFoundationService,
    SleepPhysiologyService,
    V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY,
)
from .sleep_termination import SleepTerminationFoundationService
from .util import Clock, to_iso
from .world_rules import install_standard_residence_rules


RODAGE_V2_BLUEPRINT_KEY = "residence.rodage_v2"
RODAGE_V2_MANIFEST_KEY = "rodage_v2.t0"


def _place(name: str, functions: tuple[str, ...], slots: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        "name": name,
        "medium": "air",
        "functions": list(functions),
        "max_occupancy": None,
        "installation_slots": list(slots),
    }


RODAGE_V2_ARCHETYPES = (
    ("place", "workplace", _place("Lieu de travail extérieur", ("work", "arrive", "depart"))),
    ("connector", "commute_route", {
        "name": "Trajet externe",
        "traversal_modes": ["walk"],
        "directions": "bidirectional",
        "features": ["open", "exterior", "offsite"],
    }),
)


def _rodage_blueprint() -> tuple[str, dict[str, Any]]:
    definition = deepcopy(INITIAL_RESIDENCE_BLUEPRINT[1])
    definition["name"] = "Résidence — Rodage V2"
    definition["locations"].append({
        "key": "lieu_travail",
        "name": "Lieu de travail",
        "archetype": {"key": "workplace", "version": 1},
    })
    definition["connectors"].append({
        "key": "trajet_travail",
        "from": "stationnement",
        "to": "lieu_travail",
        "archetype": {"key": "commute_route", "version": 1},
        "initial_state": "available",
    })
    return RODAGE_V2_BLUEPRINT_KEY, definition


RODAGE_V2_BLUEPRINT = _rodage_blueprint()

# Ce sont des données de scénario, pas des règles comportementales.
RODAGE_V2_INITIAL_LOCATIONS = {
    "sophie": "lieu_travail",
    "erika": "salon",
    "luna": "entree_exterieure",
    "chuu": "salle_de_bain",
    "patoune": "salon",
}

# Asymétrie physiologique T0 volontaire et bornée. Les valeurs sont des choix
# de scénario à l'intérieur des régions de calibration, pas des traits de personnalité.
RODAGE_V2_T0_STATE = {
    "sophie": (47_000, 720_000, 78_000),
    "erika": (53_000, 760_000, 72_000),
    "luna": (44_000, 700_000, 84_000),
    "chuu": (50_000, 790_000, 77_000),
    "patoune": (58_000, 740_000, 80_000),
}


class FrozenClock(Clock):
    """Horloge de bootstrap : tous les faits initiaux partagent exactement T0."""

    def __init__(self, instant: datetime) -> None:
        if instant.tzinfo is None:
            raise ValueError("T0 doit être timezone-aware")
        self._instant = instant.astimezone(timezone.utc)

    def now(self) -> datetime:
        return self._instant


class RodageV2Error(RuntimeError):
    pass


class RodageV2Service:
    """Construit une nouvelle résidence de rodage sans lire ni migrer le legacy."""

    def __init__(self, conn, clock: Clock | None = None) -> None:
        self._conn = conn
        source_clock = clock or Clock()
        self._t0 = source_clock.now().astimezone(timezone.utc)
        self._clock = FrozenClock(self._t0)

    @property
    def t0(self) -> str:
        return to_iso(self._t0)

    @staticmethod
    def _profile_payload(profile_key: str) -> dict[str, Any]:
        candidate = asdict(calibration_profiles()[profile_key])
        for key in ("profile_key", "version", "evidence_class"):
            candidate.pop(key)
        return {"model_key": ADDITIVE_MODEL_KEY, "parameters": candidate}

    def _install_environment(self) -> None:
        install_initial_residence_catalog(self._conn)
        EnvironmentArchetypeService(self._conn).install_published_catalog(RODAGE_V2_ARCHETYPES)
        EnvironmentBlueprintService(self._conn).install_published_catalog((RODAGE_V2_BLUEPRINT,))
        install_mvp_templates_v4(self._conn)

    def _instantiate_cast(self, world_id: int) -> None:
        instances = CharacterInstanceService(self._conn, clock=self._clock)
        for key in ("sophie", "erika", "luna", "chuu", "patoune"):
            instances.instantiate(
                world_id,
                key,
                4,
                key,
                RODAGE_V2_INITIAL_LOCATIONS[key],
                source="system",
            )

        resources = ResourceEngine(self._conn, clock=self._clock)
        install_chuu_hydration(resources, world_id, "chuu")

        objects = ObjectService(self._conn, clock=self._clock)
        possession = PossessionService(self._conn, clock=self._clock)
        for character in ("sophie", "erika", "luna", "chuu"):
            location = RODAGE_V2_INITIAL_LOCATIONS[character]
            phone = f"telephone_{character}"
            objects.create_object(
                world_id, phone, f"Téléphone de {character.capitalize()}", "phone", location,
                portable=True, source="system",
            )
            possession.pick_up(world_id, character, phone, source="system")

        objects.create_object(
            world_id,
            "sac_voyage_luna",
            "Sac de voyage de Luna",
            "travel_bag",
            "entree_exterieure",
            portable=True,
            container_capacity=12,
            source="system",
        )
        possession.pick_up(world_id, "luna", "sac_voyage_luna", source="system")

        context = SharedInitialContextService(self._conn, clock=self._clock)
        context.set_shared_fact(world_id, "proprietaire_superieur", "Francis", source="system")
        context.set_shared_fact(world_id, "statut_residentes", "residentes", source="system")

    def _configure_activity_catalog(self, world_id: int) -> None:
        upgrade_dev_activities(self._conn, world_id, clock=self._clock)
        # La table reste le propriétaire du mapping actif; la constante V1 rend
        # explicite la calibration d'ingénierie actuellement retenue.
        definitions = {
            row["activity_type"]
            for row in self._conn.execute(
                "SELECT activity_type FROM activity_definition WHERE world_id=?", (world_id,)
            )
        }
        if definitions != set(V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY):
            missing = sorted(definitions.symmetric_difference(V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY))
            raise RodageV2Error(f"catalogue activité/P désynchronisé: {missing}")
        for activity_type, load_class in V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY.items():
            self._conn.execute(
                "UPDATE activity_definition SET physical_load_class=? "
                "WHERE world_id=? AND activity_type=?",
                (load_class, world_id, activity_type),
            )

    def _configure_private_policies(self, world_id: int) -> SleepPhysiologyFoundationService:
        physiology = SleepPhysiologyFoundationService(self._conn, clock=self._clock)

        # 20:00–06:00 EDT = 00:00–10:00 UTC. Le calendrier est un choix de
        # résidence, pas une affirmation universelle sur la lumière naturelle.
        physiology.register_light_schedule("rodage_v2.edt_day.v1", 1, {
            "schema_version": 1,
            "segments": [
                {"start_second": 0, "end_second": 36_000, "environmental_light_milli": 0},
                {"start_second": 36_000, "end_second": 86_400, "environmental_light_milli": 90_000},
            ],
        })
        for key, exposure, kind in (
            ("rodage_v2.indoor.v1", 30_000, "indoor"),
            ("rodage_v2.outdoor.v1", 100_000, "outdoor"),
            ("rodage_v2.work.v1", 55_000, "workplace"),
        ):
            physiology.register_location_light_profile(key, 1, exposure, {"kind": kind})

        human = self._profile_payload("human_reference_candidate.v1")
        feline = self._profile_payload("generic_feline_hypothesis.v1")
        physiology.register_biology_profile("rodage_v2.human.v1", 1, "human_reference", human)
        physiology.register_biology_profile("rodage_v2.feline.v1", 1, "generic_feline", feline)
        # Luna et Chuu sont fictionnelles. Réutiliser la forme quantitative
        # humaine V1 est explicitement une hypothèse de modélisation provisoire,
        # jamais une loi biologique sur une louve anthro ou un slime.
        physiology.register_biology_profile("rodage_v2.luna_fictional.v1", 1, "fictional_canon", human)
        physiology.register_biology_profile("rodage_v2.chuu_fictional.v1", 1, "fictional_canon", human)

        physiology.register_physical_capacity_policy("rodage_v2.capacity.v1", 1, {
            "schema_version": 1,
            "activity_cost_per_hour_milli": {
                "none": 3_600, "light": 7_200, "moderate": 10_800, "vigorous": 18_000,
            },
            "minimum_capacity_milli": {
                "none": 0, "light": 10_000, "moderate": 25_000, "vigorous": 45_000,
            },
            "traversal_cost_per_edge_milli": 250,
            "recovery_per_hour_milli": {"rest": 7_200, "sleep": 10_800},
        }, "rodage_v2_engineering")

        physiology.assign_light_schedule(world_id, "rodage_v2.edt_day.v1", 1, self.t0, "rodage_v2")
        outdoor = {"entree_exterieure", "stationnement", "cour_arriere", "piscine", "remise"}
        for row in self._conn.execute("SELECT key FROM location WHERE world_id=? ORDER BY key", (world_id,)):
            location = row["key"]
            profile = (
                "rodage_v2.work.v1" if location == "lieu_travail"
                else "rodage_v2.outdoor.v1" if location in outdoor
                else "rodage_v2.indoor.v1"
            )
            physiology.assign_location_light_profile(world_id, location, profile, 1, self.t0, "rodage_v2")

        biology = {
            "sophie": "rodage_v2.human.v1",
            "erika": "rodage_v2.human.v1",
            "luna": "rodage_v2.luna_fictional.v1",
            "chuu": "rodage_v2.chuu_fictional.v1",
            "patoune": "rodage_v2.feline.v1",
        }
        for character, profile in biology.items():
            physiology.assign_biology_profile(world_id, character, profile, 1, "rodage_v2")
        physiology.assign_physical_capacity_policy(world_id, "rodage_v2.capacity.v1", 1, "rodage_v2")

        termination = SleepTerminationFoundationService(self._conn, clock=self._clock)
        termination.register_policy("rodage_v2.sleep_termination.v1", 1, {
            "schema_version": 1,
            "checkpoint_interval_seconds": 900,
            "hard_cap_seconds": 28_800,
            "wake_admissible_enter_milli": 65_000,
            "wake_admissible_exit_milli": 55_000,
        }, "rodage_v2_engineering")
        termination.assign_policy(world_id, "rodage_v2.sleep_termination.v1", 1, "rodage_v2")

        arbitration = ActionArbitrationFoundationService(self._conn, clock=self._clock)
        arbitration.register_policy("rodage_v2.action_arbitration.v1", 1, {
            "schema_version": 1,
            "source_mappings": {
                "sleep_regulation": {"transform": "identity_milli.v1", "correlation_group": "sleep"},
                "physical_recovery": {"transform": "identity_milli.v1", "correlation_group": "recovery"},
                "subjective_intention": {"transform": "identity_milli.v1", "correlation_group": "subjective"},
            },
            "correlation_groups": {"kind": "declared_by_source_mapping.v1"},
            "aggregation": {"kind": "max_per_group_then_saturating_sum.v1"},
            "current_action_inertia": {"max_bonus_milli": 0},
            "quasi_equality": {"band_milli": 1_000},
            "reassessment": {"interval_seconds": 60},
        }, "rodage_v2_engineering")
        arbitration.assign_policy(world_id, "rodage_v2.action_arbitration.v1", 1, "rodage_v2")

        physiology.register_initial_physiology_policy("rodage_v2.initial.v1", 1, {
            "schema_version": 1,
            "model_key": ADDITIVE_MODEL_KEY,
            "model_version": 1,
            "homeostatic_load_region": {"min_milli": 35_000, "max_milli": 70_000},
            "physical_capacity_region": {"min_milli": 60_000, "max_milli": 95_000},
            "bootstrap_rule": "wake_stability.scenario_seed.v1",
            "residue_rule": "zero_at_t0.v1",
        }, "rodage_v2_engineering")
        physiology.register_t0_phase_rule("rodage_v2.phase.v1", 1, {
            "schema_version": 1,
            "rule_kind": "schedule_light_phase_windows.v1",
            "light_phase_windows": [[100_000, 550_000]],
            "dark_phase_windows": [[650_000, 850_000]],
        }, "rodage_v2_engineering")
        return physiology

    def _seal_and_activate_physiology(
        self, world_id: int, physiology: SleepPhysiologyFoundationService
    ) -> dict[str, Any]:
        physiology.create_initial_physiology_manifest(
            world_id,
            RODAGE_V2_MANIFEST_KEY,
            1,
            "rodage_v2.initial.v1",
            1,
            "rodage_v2.phase.v1",
            1,
            self.t0,
            "rodage_v2",
            "états T0 asymétriques explicites du nouveau monde de rodage",
        )

        profile_by_character = {
            "sophie": "rodage_v2.human.v1",
            "erika": "rodage_v2.human.v1",
            "luna": "rodage_v2.luna_fictional.v1",
            "chuu": "rodage_v2.chuu_fictional.v1",
            "patoune": "rodage_v2.feline.v1",
        }
        reader = SleepPhysiologyService(self._conn, clock=self._clock)
        for character in sorted(RODAGE_V2_T0_STATE):
            h, phase, p = RODAGE_V2_T0_STATE[character]
            source = reader.resolve_light_source_owner_backed(
                world_id, character, at_time=self.t0
            ).source
            parameters = reader.parameters_for_character(world_id, character)
            state = RegulationState(h / 100_000.0, phase / 999_999.0, p / 100_000.0)
            band = wake_stability(state, source, parameters, previous_band="stable").band
            physiology.append_initial_physiology_manifest_entry(
                world_id,
                RODAGE_V2_MANIFEST_KEY,
                1,
                InitialPhysiologyManifestEntry(
                    character,
                    profile_by_character[character],
                    1,
                    h,
                    phase,
                    p,
                    band,
                    "rodage_v2",
                    "différence T0 de scénario, sans script comportemental",
                ),
            )
        physiology.seal_initial_physiology_manifest(world_id, RODAGE_V2_MANIFEST_KEY, 1)
        physiology.prepare_world(world_id, ADDITIVE_MODEL_KEY, 1, "rodage_v2")
        return physiology.activate_world_from_initial_manifest(
            world_id, RODAGE_V2_MANIFEST_KEY, 1, "rodage_v2"
        )

    def _start_initial_scene(self, world_id: int) -> None:
        activities = ActivityEngine(self._conn, clock=self._clock)
        activities.start_activity(world_id, "sophie", "work", "lieu_travail", sim_now=self.t0)
        activities.start_activity(world_id, "erika", "gaming", "salon", sim_now=self.t0)
        activities.start_activity(world_id, "chuu", "bathe", "salle_de_bain", sim_now=self.t0)
        activities.start_activity(world_id, "patoune", "sleep", "salon", sim_now=self.t0)

        # Chuu est déjà très hydratée au T0 (95 %). Le bain produit ici un seul
        # apport canonique de 5 %, via le mécanisme de ressource générique.
        ResourceEngine(self._conn, clock=self._clock).adjust_resource(
            world_id, "chuu", "hydration", 5_000, self.t0, "bath_contact_hydration"
        )

    def create_world(self) -> dict[str, Any]:
        """Crée Rodage V2 à côté du legacy; ne lit ni ne modifie aucune ancienne DB."""
        self._install_environment()
        world = EnvironmentBlueprintService(self._conn, clock=self._clock).instantiate(
            RODAGE_V2_BLUEPRINT_KEY, 1
        )
        world_id = int(world["id"])
        install_standard_residence_rules(self._conn, world_id)
        self._instantiate_cast(world_id)
        self._configure_activity_catalog(world_id)

        # Figer T0 après tous les faits structurels et avant les données privées
        # de physiologie. Aucune session réelle ne reste ouverte.
        sessions = RuntimeSessionService(self._conn, clock=self._clock)
        frozen_session = sessions.start(world_id)
        sessions.stop(frozen_session.session_id)

        physiology = self._configure_private_policies(world_id)
        activation = self._seal_and_activate_physiology(world_id, physiology)
        self._start_initial_scene(world_id)

        report = inspect_mvp_preflight(self._conn, world_id=world_id)
        failures = tuple(check.key for check in report.checks if not check.passed)
        if failures:
            raise RodageV2Error("prévol Rodage V2 refusé: " + ",".join(failures))

        return {
            "world_id": world_id,
            "world_name": world["name"],
            "t0": self.t0,
            "physiology": activation,
            "preflight": "pass",
            "initial_locations": dict(RODAGE_V2_INITIAL_LOCATIONS),
            "initial_activities": {
                key: (
                    ActivityEngine(self._conn, clock=self._clock).activity_sheet(world_id, key) or {}
                ).get("type")
                for key in sorted(RODAGE_V2_INITIAL_LOCATIONS)
            },
        }
