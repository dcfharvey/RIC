from dataclasses import asdict
from datetime import datetime, timezone

from vivarium.activities import ActivityEngine
from vivarium.action_arbitration import ActionArbitrationFoundationService
from vivarium.circadian_model import calibration_profiles
from vivarium.db import connect_database
from vivarium.external_locations import ExternalLocationService
from vivarium.integration_world import IntegrationWorldService
from vivarium.location_plans import LocationPlanService
from vivarium.migrations import ensure_schema
from vivarium.perception import PerceptionService
from vivarium.resources import ResourceEngine
from vivarium.mvp_preflight import inspect_mvp_preflight
from vivarium.runtime_session import RuntimeSessionService
from vivarium.rodage_v2_bootstrap import (
    ActivityStartSpec,
    CarriedObjectSpec,
    ExternalPlaceSpec,
    RodageV2BootstrapService,
)
from vivarium.spatial import GraphEngine
from vivarium.sleep_physiology import (
    ADDITIVE_MODEL_KEY,
    InitialPhysiologyManifestEntry,
    SleepPhysiologyFoundationService,
    V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY,
)
from vivarium.sleep_termination import SleepTerminationFoundationService
from vivarium.observation import HuginMuninObservationService, ObservationQuery
from vivarium.util import Clock, to_iso


class FakeClock(Clock):
    def __init__(self):
        self.current = datetime(2026, 8, 13, 15, 0, tzinfo=timezone.utc)

    def now(self):
        return self.current


def test_external_topology_sleep_hygiene_and_return_plan_are_generic():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    try:
        world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
        bootstrap = RodageV2BootstrapService(conn, clock=clock)
        bootstrap.add_external_places(world_id, (
            ExternalPlaceSpec("espace_exterieur", "Espace extérieur", "entree_exterieure"),
            ExternalPlaceSpec("lieu_travail", "Lieu de travail", "espace_exterieur", kind="external"),
        ))

        assert GraphEngine(conn).find_path(world_id, "entree_exterieure", "lieu_travail") == [
            "entree_exterieure", "espace_exterieur", "lieu_travail"
        ]
        # La topologie canonique existe, mais aucun connecteur perceptif n'est
        # créé par l'extension externe : elle ne produit pas d'omniscience.
        visible = PerceptionService(conn, clock=clock).snapshot(world_id, "erika")
        assert all(item.fact.payload.get("location") != "lieu_travail" for item in visible.candidates)

        # Le banc legacy exige une dette de sommeil pour ouvrir l'activité;
        # le T0 officiel utilisera le chemin physiologique H/φ/P.
        conn.execute(
            "UPDATE need_state SET value_milli=10000 WHERE world_id=? "
            "AND character_id=(SELECT id FROM character WHERE world_id=? AND key='patoune') "
            "AND need_key IN ('repos','energie')", (world_id, world_id)
        )

        bootstrap.start_activities(world_id, (
            ActivityStartSpec("sophie", "photography", "lieu_travail"),
            ActivityStartSpec("erika", "gaming", "salon"),
            ActivityStartSpec("patoune", "sleep", "salon"),
            ActivityStartSpec("chuu", "clean", "salle_de_bain"),
        ))
        assert ActivityEngine(conn, clock=clock).activity_sheet(world_id, "patoune")["location_key"] == "salon"
        assert ActivityEngine(conn, clock=clock).activity_sheet(world_id, "chuu")["location_key"] == "salle_de_bain"
        assert ActivityEngine(conn, clock=clock).activity_sheet(world_id, "sophie")["location_key"] == "lieu_travail"
        assert ResourceEngine(conn, clock=clock).read_resource(
            world_id, "chuu", "hydration", to_iso(clock.current)
        )["resource_key"] == "hydration"

        return_at = "2026-08-13T20:00:00.000+00:00"
        plan = LocationPlanService(conn, clock=clock).plan(
            world_id, "sophie", "entree_exterieure", return_at,
            provenance="t0.schedule.v1",
        )
        assert plan["planned_at"] == return_at
        assert plan["target_location_key"] == "entree_exterieure"

        # Le sommeil dans le salon et l'hygiène dans la salle de bain sont des
        # effets d'activités génériques, sans jauge persistante de confort.
        assert conn.execute(
            "SELECT 1 FROM need_definition WHERE world_id=? AND need_key='confort'", (world_id,)
        ).fetchone() is None
    finally:
        conn.close()


def test_bootstrap_carries_lunas_undifferentiated_personal_bag():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    try:
        world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
        result = RodageV2BootstrapService(conn, clock=clock).give_carried_objects(
            world_id, (CarriedObjectSpec("luna", "sac_luna", "Sac d'effets personnels"),)
        )
        assert result[0]["key"] == "sac_luna"
        assert result[0]["carrier"] == "luna"
        assert result[0]["kind"] == "personal_effects"
    finally:
        conn.close()


def test_disposable_t0_has_active_h_phi_p_preflight_and_observation():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    try:
        world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
        bootstrap = RodageV2BootstrapService(conn, clock=clock)
        bootstrap.add_external_places(world_id, (
            ExternalPlaceSpec("espace_exterieur", "Espace extérieur", "entree_exterieure"),
            ExternalPlaceSpec("lieu_travail", "Lieu de travail", "espace_exterieur"),
        ))
        conn.execute(
            "UPDATE need_state SET value_milli=10000 WHERE world_id=? "
            "AND character_id=(SELECT id FROM character WHERE world_id=? AND key='patoune') "
            "AND need_key IN ('repos','energie')", (world_id, world_id)
        )
        bootstrap.start_activities(world_id, (
            ActivityStartSpec("sophie", "photography", "lieu_travail"),
            ActivityStartSpec("erika", "gaming", "salon"),
            ActivityStartSpec("patoune", "sleep", "salon"),
            ActivityStartSpec("chuu", "clean", "salle_de_bain"),
        ))
        bootstrap.give_carried_objects(
            world_id, (CarriedObjectSpec("luna", "sac_luna", "Sac d'effets personnels"),)
        )
        anchor = to_iso(clock.current)
        session = RuntimeSessionService(conn, clock=clock).start(world_id)
        RuntimeSessionService(conn, clock=clock).stop(session.session_id)

        physiology = SleepPhysiologyFoundationService(conn, clock=clock)
        physiology.register_light_schedule("wo90.day.v1", 1, {
            "schema_version": 1,
            "segments": [
                {"start_second": 0, "end_second": 86400, "environmental_light_milli": 50000},
            ],
        })
        physiology.register_location_light_profile("wo90.external.v1", 1, 25000, {"kind": "external"})
        profile = asdict(calibration_profiles()["human_reference_candidate.v1"])
        for key in ("profile_key", "version", "evidence_class"):
            profile.pop(key)
        physiology.register_biology_profile(
            "wo90.human.v1", 1, "human_reference",
            {"model_key": ADDITIVE_MODEL_KEY, "parameters": profile},
        )
        physiology.register_initial_physiology_policy("wo90.regions.v1", 1, {
            "schema_version": 1, "model_key": ADDITIVE_MODEL_KEY, "model_version": 1,
            "homeostatic_load_region": {"min_milli": 40000, "max_milli": 60000},
            "physical_capacity_region": {"min_milli": 70000, "max_milli": 90000},
            "bootstrap_rule": "wake_stability.stable_seed.v1", "residue_rule": "zero_at_t0.v1",
        }, "wo90")
        physiology.register_t0_phase_rule("wo90.phase.v1", 1, {
            "schema_version": 1, "rule_kind": "schedule_light_phase_windows.v1",
            "light_phase_windows": [[0, 999999]], "dark_phase_windows": [[0, 999999]],
        }, "wo90")
        physiology.register_physical_capacity_policy("wo90.p.v1", 1, {
            "schema_version": 1,
            "activity_cost_per_hour_milli": {"none": 3600, "light": 7200, "moderate": 10800, "vigorous": 18000},
            "minimum_capacity_milli": {"none": 0, "light": 10000, "moderate": 25000, "vigorous": 45000},
            "traversal_cost_per_edge_milli": 250,
            "recovery_per_hour_milli": {"rest": 7200, "sleep": 10800},
        }, "wo90")
        physiology.assign_light_schedule(world_id, "wo90.day.v1", 1, anchor, "wo90")
        for row in conn.execute("SELECT key FROM location WHERE world_id=?", (world_id,)):
            physiology.assign_location_light_profile(world_id, row["key"], "wo90.external.v1", 1, anchor, "wo90")
        for row in conn.execute("SELECT key FROM character WHERE world_id=?", (world_id,)):
            physiology.assign_biology_profile(world_id, row["key"], "wo90.human.v1", 1, "wo90")
        physiology.assign_physical_capacity_policy(world_id, "wo90.p.v1", 1, "wo90")
        for activity_type, load in V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY.items():
            conn.execute(
                "UPDATE activity_definition SET physical_load_class=? WHERE world_id=? AND activity_type=?",
                (load, world_id, activity_type),
            )
        term = SleepTerminationFoundationService(conn, clock=clock)
        term.register_policy("wo90.sleep.v1", 1, {
            "schema_version": 1, "checkpoint_interval_seconds": 30, "hard_cap_seconds": 300,
            "wake_admissible_enter_milli": 65000, "wake_admissible_exit_milli": 55000,
        }, "wo90")
        term.assign_policy(world_id, "wo90.sleep.v1", 1, "wo90")
        arb = ActionArbitrationFoundationService(conn, clock=clock)
        policy = arb.register_policy("wo90.arb.v1", 1, {
            "schema_version": 1,
            "source_mappings": {
                "sleep_regulation": {"transform": "linear_clamped_milli.v1", "correlation_group": "sleep", "input_low_milli": 60000, "input_high_milli": 100000, "direction": "ascending"},
                "physical_recovery": {"transform": "linear_clamped_milli.v1", "correlation_group": "recovery", "input_low_milli": 20000, "input_high_milli": 80000, "direction": "descending"},
                "subjective_intention": {"transform": "linear_clamped_milli.v1", "correlation_group": "subjective", "input_low_milli": 0, "input_high_milli": 100000, "direction": "ascending"},
            },
            "correlation_groups": {"kind": "declared_by_source_mapping.v1"},
            "aggregation": {"kind": "max_per_group_then_saturating_sum.v1"},
            "current_action_inertia": {"max_bonus_milli": 0},
            "quasi_equality": {"band_milli": 100000}, "reassessment": {"interval_seconds": 60},
        }, "wo90")
        arb.assign_policy(world_id, policy.policy_key, policy.version, "wo90")
        physiology.prepare_world(world_id, ADDITIVE_MODEL_KEY, 1, "wo90")
        manifest = physiology.create_initial_physiology_manifest(
            world_id, "wo90.t0.v1", 1, "wo90.regions.v1", 1, "wo90.phase.v1", 1,
            anchor, "wo90", "disposable T0 qualification",
        )
        for row in conn.execute("SELECT key FROM character WHERE world_id=? ORDER BY key", (world_id,)):
            physiology.append_initial_physiology_manifest_entry(
                world_id, manifest["manifest_key"], 1,
                InitialPhysiologyManifestEntry(
                    row["key"], "wo90.human.v1", 1, 50000, 250000, 75000, "fragile",
                    "wo90", "disposable T0 qualification",
                ),
            )
        physiology.seal_initial_physiology_manifest(world_id, "wo90.t0.v1", 1)
        physiology.activate_world_from_initial_manifest(world_id, "wo90.t0.v1", 1, "wo90")

        report = inspect_mvp_preflight(conn, world_id=world_id)
        assert report.healthy, report.failures
        observed = HuginMuninObservationService(conn, clock=clock).report(
            world_id, ObservationQuery(
                mode="hugin", subject_keys=("sophie", "erika", "patoune", "chuu", "luna"),
                focus="current_state",
            )
        )
        current = [item["data"] for item in observed["evidence"] if item["ref"] == "current_character:sophie"][0]
        assert current["physiology"]["status"] == "active"
        assert current["physiology"]["persisted"] is not None
        assert conn.execute("SELECT COUNT(*) FROM worlds").fetchone()[0] == 1
    finally:
        conn.close()
