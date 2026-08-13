"""WO88A : noyau P commun et matérialisation owner-backed."""

from dataclasses import asdict
from datetime import datetime, timezone

import pytest

from vivarium.circadian_model import calibration_profiles
from vivarium.db import connect_database, transaction
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.physical_capacity import (
    PhysicalCapacityError, PhysicalRequest, advance_physical_capacity,
    evaluate_physical_request,
)
from vivarium.sleep_physiology import (
    ADDITIVE_MODEL_KEY, SleepPhysiologyFoundationService, SleepPhysiologyService,
)
from vivarium.world import WorldEngine

ANCHOR = "2026-08-11T12:00:00.000000Z"
T30 = "2026-08-11T12:00:30.000000Z"
T60 = "2026-08-11T12:01:00.000000Z"


def _profile_payload():
    payload = asdict(calibration_profiles()["human_reference_candidate.v1"])
    for key in ("profile_key", "version", "evidence_class"):
        payload.pop(key)
    return {"model_key": ADDITIVE_MODEL_KEY, "parameters": payload}


def _policy():
    return {
        "schema_version": 1,
        "activity_cost_per_hour_milli": {
            "none": 3600, "light": 7200, "moderate": 10800, "vigorous": 18000,
        },
        "minimum_capacity_milli": {
            "none": 0, "light": 10000, "moderate": 25000, "vigorous": 45000,
        },
        "traversal_cost_per_edge_milli": 250,
        "recovery_per_hour_milli": {"rest": 7200, "sleep": 10800},
    }


def test_activity_rate_and_traversal_cost_are_distinct_contracts():
    class Policy:
        activity_cost_per_hour_milli = _policy()["activity_cost_per_hour_milli"]
        minimum_capacity_milli = _policy()["minimum_capacity_milli"]
        traversal_cost_per_edge_milli = 250
        recovery_per_hour_milli = _policy()["recovery_per_hour_milli"]

    activity = evaluate_physical_request(
        Policy(), PhysicalRequest("activity", physical_load_class="moderate"),
        capacity_milli=30_000,
    )
    traversal = evaluate_physical_request(
        Policy(), PhysicalRequest("traversal", edge_count=3), capacity_milli=30_000,
    )
    assert activity.activity_rate_milli_per_hour == 10_800
    assert activity.traversal_cost_milli is None
    assert traversal.activity_rate_milli_per_hour is None
    assert traversal.traversal_cost_milli == 750


def test_capacity_time_integration_is_partition_stable_and_saturation_resets_remainder():
    class Policy:
        activity_cost_per_hour_milli = _policy()["activity_cost_per_hour_milli"]
        minimum_capacity_milli = _policy()["minimum_capacity_milli"]
        traversal_cost_per_edge_milli = 250
        recovery_per_hour_milli = _policy()["recovery_per_hour_milli"]

    single = advance_physical_capacity(
        Policy(), capacity_milli=70_000, rate_remainder=0, state="wake",
        physical_load_class="moderate", duration_seconds=61,
    )
    first = advance_physical_capacity(
        Policy(), capacity_milli=70_000, rate_remainder=0, state="wake",
        physical_load_class="moderate", duration_seconds=17,
    )
    split = advance_physical_capacity(
        Policy(), capacity_milli=first[0], rate_remainder=first[1], state="wake",
        physical_load_class="moderate", duration_seconds=44,
    )
    assert split == single
    assert advance_physical_capacity(
        Policy(), capacity_milli=99_999, rate_remainder=3599, state="sleep",
        physical_load_class="none", duration_seconds=1,
    ) == (100_000, 0)
    with pytest.raises(PhysicalCapacityError):
        PhysicalRequest("traversal", edge_count=0)


def _active_world():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world_id = IntegrationWorldService(conn).create_initial_world()["id"]
    foundation = SleepPhysiologyFoundationService(conn)
    foundation.register_light_schedule("active.day.v1", 1, {
        "schema_version": 1,
        "segments": [{"start_second": 0, "end_second": 86400, "environmental_light_milli": 50000}],
    })
    foundation.register_location_light_profile("active.interior.v1", 1, 25000, {"kind": "interior"})
    foundation.register_biology_profile("active.human.v1", 1, "human_reference", _profile_payload())
    foundation.register_physical_capacity_policy("active.capacity.v1", 1, _policy(), "test")
    foundation.assign_light_schedule(world_id, "active.day.v1", 1, ANCHOR, "test")
    for row in conn.execute("SELECT key FROM location WHERE world_id=? ORDER BY key", (world_id,)):
        foundation.assign_location_light_profile(world_id, row["key"], "active.interior.v1", 1, ANCHOR, "test")
    for row in conn.execute("SELECT key FROM character WHERE world_id=? ORDER BY key", (world_id,)):
        foundation.assign_biology_profile(world_id, row["key"], "active.human.v1", 1, "test")
    foundation.assign_physical_capacity_policy(world_id, "active.capacity.v1", 1, "test")
    # Explicit metadata belongs to the activity catalogue, even though this test
    # leaves every character without an active activity.
    conn.execute(
        "UPDATE activity_definition SET physical_load_class='none' WHERE world_id=?", (world_id,)
    )
    foundation.prepare_world(world_id, ADDITIVE_MODEL_KEY, 1, "test")
    with transaction(conn) as tx:
        tx.execute(
            "UPDATE world_physiology_system SET status='active',activated_at=?,activated_by=?,updated_at=? WHERE world_id=?",
            (ANCHOR, "test", ANCHOR, world_id),
        )
        for row in tx.execute("SELECT id FROM character WHERE world_id=? ORDER BY id", (world_id,)):
            cid = row["id"]
            tx.execute(
                "INSERT INTO sleep_regulation_state (public_id,world_id,character_id,model_key,model_version,homeostatic_load_milli,circadian_phase_milli,anchor_at,updated_at) VALUES (?,?,?,?,1,50000,250000,?,?)",
                (f"reg-{cid}", world_id, cid, ADDITIVE_MODEL_KEY, ANCHOR, ANCHOR),
            )
            tx.execute(
                "INSERT INTO physical_capacity_state (public_id,world_id,character_id,capacity_milli,rate_remainder,anchor_at,updated_at) VALUES (?,?,?,70000,0,?,?)",
                (f"cap-{cid}", world_id, cid, ANCHOR, ANCHOR),
            )
            tx.execute(
                "INSERT INTO sleep_wake_hysteresis_state (public_id,world_id,character_id,previous_band,anchor_at,updated_at) VALUES (?,?,?,'fragile',?,?)",
                (f"hys-{cid}", world_id, cid, ANCHOR, ANCHOR),
            )
            tx.execute(
                "INSERT INTO sleep_regulation_precision_state (public_id,world_id,character_id,homeostatic_load_residue,circadian_phase_residue,anchor_at,updated_at) VALUES (?,?,?,0.0,0.0,?,?)",
                (f"pre-{cid}", world_id, cid, ANCHOR, ANCHOR),
            )
    return conn, world_id


def test_owner_backed_materialization_uses_policy_p_and_is_partition_stable():
    conn, world_id = _active_world()
    try:
        service = SleepPhysiologyService(conn)
        with transaction(conn) as tx:
            WorldEngine(conn)._advance_clock(world_id, T30, tx)
        first = service.materialize_owner_backed(world_id, "sophie", T30)
        assert first.changed and first.physical_load_class == "none"
        assert first.projection.state.regulation.physical_capacity_milli == 69_970
        with transaction(conn) as tx:
            WorldEngine(conn)._advance_clock(world_id, T60, tx)
        split = service.materialize_owner_backed(world_id, "sophie", T60)
        single = service.materialize_owner_backed(world_id, "erika", T60)
        assert split.projection.state.regulation.physical_capacity_milli == 69_940
        assert single.projection.state.regulation.physical_capacity_milli == 69_940
        assert split.projection.state.regulation.homeostatic_load_milli == single.projection.state.regulation.homeostatic_load_milli
        assert split.projection.state.regulation.circadian_phase_milli == single.projection.state.regulation.circadian_phase_milli
        again = service.materialize_owner_backed(world_id, "sophie", T60)
        assert not again.changed
    finally:
        conn.close()
