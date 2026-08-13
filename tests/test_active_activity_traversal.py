"""WO88B/C : activités et traversées actives ne causent plus repos/energie."""

from dataclasses import asdict
from datetime import datetime, timezone

import pytest

from vivarium.activities import ActivityEngine
from vivarium.circadian_model import calibration_profiles
from vivarium.db import connect_database, transaction
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.sleep_physiology import (
    ADDITIVE_MODEL_KEY, SleepPhysiologyFoundationService, SleepPhysiologyService,
)
from vivarium.sleep_termination import SleepTerminationFoundationService
from vivarium.traversal import TraversalEngine, TraversalError
from vivarium.util import Clock, to_iso

T0_DT = datetime(2026, 8, 12, 21, 0, tzinfo=timezone.utc)
T0 = to_iso(T0_DT)
T30_DT = datetime(2026, 8, 12, 21, 0, 30, tzinfo=timezone.utc)
T30 = to_iso(T30_DT)


class FakeClock(Clock):
    def __init__(self):
        self.current = T0_DT

    def now(self):
        return self.current


def _profile_payload():
    payload = asdict(calibration_profiles()["human_reference_candidate.v1"])
    for key in ("profile_key", "version", "evidence_class"):
        payload.pop(key)
    return {"model_key": ADDITIVE_MODEL_KEY, "parameters": payload}


def _world():
    clock = FakeClock()
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    f = SleepPhysiologyFoundationService(conn, clock=clock)
    f.register_light_schedule("active.day.v1", 1, {
        "schema_version": 1,
        "segments": [{"start_second": 0, "end_second": 86400, "environmental_light_milli": 50000}],
    })
    f.register_location_light_profile("active.interior.v1", 1, 25000, {"kind": "interior"})
    f.register_biology_profile("active.human.v1", 1, "human_reference", _profile_payload())
    f.register_physical_capacity_policy("active.capacity.v1", 1, {
        "schema_version": 1,
        "activity_cost_per_hour_milli": {
            "none": 3600, "light": 7200, "moderate": 10800, "vigorous": 18000,
        },
        "minimum_capacity_milli": {
            "none": 0, "light": 10000, "moderate": 25000, "vigorous": 45000,
        },
        "traversal_cost_per_edge_milli": 250,
        "recovery_per_hour_milli": {"rest": 7200, "sleep": 10800},
    }, "test")
    f.assign_light_schedule(world_id, "active.day.v1", 1, T0, "test")
    for row in conn.execute("SELECT key FROM location WHERE world_id=? ORDER BY key", (world_id,)):
        f.assign_location_light_profile(world_id, row["key"], "active.interior.v1", 1, T0, "test")
    for row in conn.execute("SELECT key FROM character WHERE world_id=? ORDER BY key", (world_id,)):
        f.assign_biology_profile(world_id, row["key"], "active.human.v1", 1, "test")
    f.assign_physical_capacity_policy(world_id, "active.capacity.v1", 1, "test")
    conn.execute("UPDATE activity_definition SET physical_load_class='none' WHERE world_id=?", (world_id,))
    conn.execute("UPDATE activity_definition SET physical_load_class='light' WHERE world_id=? AND activity_type='gaming'", (world_id,))
    term = SleepTerminationFoundationService(conn, clock=clock)
    term.register_policy("active.sleep.v1", 1, {
        "schema_version": 1, "checkpoint_interval_seconds": 900,
        "hard_cap_seconds": 28800, "wake_admissible_enter_milli": 65000,
        "wake_admissible_exit_milli": 55000,
    }, "test")
    term.assign_policy(world_id, "active.sleep.v1", 1, "test")
    f.prepare_world(world_id, ADDITIVE_MODEL_KEY, 1, "test")
    with transaction(conn) as tx:
        tx.execute(
            "UPDATE world_physiology_system SET status='active',activated_at=?,activated_by=?,updated_at=? WHERE world_id=?",
            (T0, "test", T0, world_id),
        )
        for row in tx.execute("SELECT id FROM character WHERE world_id=? ORDER BY id", (world_id,)):
            cid = row["id"]
            tx.execute(
                "INSERT INTO sleep_regulation_state (public_id,world_id,character_id,model_key,model_version,homeostatic_load_milli,circadian_phase_milli,anchor_at,updated_at) VALUES (?,?,?,?,1,50000,250000,?,?)",
                (f"reg-{cid}", world_id, cid, ADDITIVE_MODEL_KEY, T0, T0),
            )
            tx.execute(
                "INSERT INTO physical_capacity_state (public_id,world_id,character_id,capacity_milli,rate_remainder,anchor_at,updated_at) VALUES (?,?,?,70000,0,?,?)",
                (f"cap-{cid}", world_id, cid, T0, T0),
            )
            tx.execute(
                "INSERT INTO sleep_wake_hysteresis_state (public_id,world_id,character_id,previous_band,anchor_at,updated_at) VALUES (?,?,?,'fragile',?,?)",
                (f"hys-{cid}", world_id, cid, T0, T0),
            )
            tx.execute(
                "INSERT INTO sleep_regulation_precision_state (public_id,world_id,character_id,homeostatic_load_residue,circadian_phase_residue,anchor_at,updated_at) VALUES (?,?,?,0.0,0.0,?,?)",
                (f"pre-{cid}", world_id, cid, T0, T0),
            )
    return conn, world_id, clock


def _legacy_rest_energy(conn, world_id, character):
    return tuple(
        tuple(row) for row in conn.execute(
            "SELECT need_key,value_milli,rate_remainder,anchor_at FROM need_state ns "
            "JOIN character c ON c.id=ns.character_id WHERE ns.world_id=? AND c.key=? "
            "AND ns.need_key IN ('repos','energie') ORDER BY ns.need_key",
            (world_id, character),
        )
    )


def _first_connector(conn, world_id, character):
    return conn.execute(
        "SELECT wc.key AS connector,t.key AS target FROM character c "
        "JOIN location_link ll ON ll.world_id=c.world_id AND ll.from_location_id=c.current_location_id "
        "JOIN world_connector wc ON wc.id=ll.connector_id "
        "JOIN location t ON t.id=ll.to_location_id "
        "WHERE c.world_id=? AND c.key=? AND wc.state='available' ORDER BY wc.key LIMIT 1",
        (world_id, character),
    ).fetchone()


def test_active_traversal_debits_p_and_never_touches_legacy_energy():
    conn, world_id, clock = _world()
    try:
        edge = _first_connector(conn, world_id, "sophie")
        assert edge is not None
        before_legacy = _legacy_rest_energy(conn, world_id, "sophie")
        before_p = SleepPhysiologyService(conn, clock=clock).read_state(
            world_id, "sophie"
        ).regulation.physical_capacity_milli
        result = TraversalEngine(conn, clock=clock).traverse_character(
            world_id, "sophie", edge["connector"], edge["target"], sim_now=T0
        )
        after_p = SleepPhysiologyService(conn, clock=clock).read_state(
            world_id, "sophie"
        ).regulation.physical_capacity_milli
        assert result["location_key"] == edge["target"]
        assert before_p - after_p == 250
        assert _legacy_rest_energy(conn, world_id, "sophie") == before_legacy
        payload = conn.execute(
            "SELECT payload FROM canonical_event WHERE world_id=? AND event_type='character_moved' "
            "ORDER BY seq DESC LIMIT 1", (world_id,),
        ).fetchone()["payload"]
        assert '"physical_capacity_cost_milli":250' in payload
        assert '"total_energy_cost":0' in payload
    finally:
        conn.close()


def test_active_activity_path_and_ongoing_segment_use_p_without_repos_energy():
    conn, world_id, clock = _world()
    try:
        before_legacy = _legacy_rest_energy(conn, world_id, "erika")
        activity = ActivityEngine(conn, clock=clock).start_activity(
            world_id, "erika", "gaming", "salon", sim_now=T0
        )
        assert activity["type"] == "gaming"
        p_after_start = SleepPhysiologyService(conn, clock=clock).read_state(
            world_id, "erika"
        ).regulation.physical_capacity_milli
        assert p_after_start < 70000  # trajet discret vers le salon
        clock.current = T30_DT
        ActivityEngine(conn, clock=clock).advance_to(world_id, "erika", T30)
        p_after_30 = SleepPhysiologyService(conn, clock=clock).read_state(
            world_id, "erika"
        ).regulation.physical_capacity_milli
        assert p_after_30 < p_after_start  # débit light versionné
        assert _legacy_rest_energy(conn, world_id, "erika") == before_legacy
    finally:
        conn.close()


def test_active_sleep_ignores_legacy_sleep_targets_and_uses_checkpoint_hard_cap():
    conn, world_id, clock = _world()
    try:
        conn.execute(
            "UPDATE need_state SET value_milli=100000 WHERE world_id=? AND character_id="
            "(SELECT id FROM character WHERE world_id=? AND key='luna') "
            "AND need_key IN ('repos','energie')", (world_id, world_id),
        )
        before_legacy = _legacy_rest_energy(conn, world_id, "luna")
        activities = ActivityEngine(conn, clock=clock)
        sleep_location = sorted(activities.allowed_locations(world_id, "sleep"))[0]
        activity = activities.start_activity(
            world_id, "luna", "sleep", sleep_location, sim_now=T0
        )
        assert activity["type"] == "sleep"
        checkpoint = ActivityEngine(conn, clock=clock).sleep_checkpoint(world_id, "luna")
        assert checkpoint is not None
        assert checkpoint["next_reassessment_at"] > T0
        assert checkpoint["hard_cap_at"] == activity["planned_end_at"]
        assert _legacy_rest_energy(conn, world_id, "luna") == before_legacy
    finally:
        conn.close()


def test_insufficient_p_refuses_traversal_atomically_without_legacy_fallback():
    conn, world_id, clock = _world()
    try:
        char_id = conn.execute(
            "SELECT id FROM character WHERE world_id=? AND key='chuu'", (world_id,)
        ).fetchone()["id"]
        conn.execute(
            "UPDATE physical_capacity_state SET capacity_milli=100 WHERE world_id=? AND character_id=?",
            (world_id, char_id),
        )
        edge = _first_connector(conn, world_id, "chuu")
        before_legacy = _legacy_rest_energy(conn, world_id, "chuu")
        before_location = conn.execute(
            "SELECT current_location_id FROM character WHERE id=?", (char_id,)
        ).fetchone()[0]
        with pytest.raises(TraversalError) as caught:
            TraversalEngine(conn, clock=clock).traverse_character(
                world_id, "chuu", edge["connector"], edge["target"], sim_now=T0
            )
        assert caught.value.code == "insufficient_physical_capacity"
        assert conn.execute("SELECT current_location_id FROM character WHERE id=?", (char_id,)).fetchone()[0] == before_location
        assert _legacy_rest_energy(conn, world_id, "chuu") == before_legacy
        assert SleepPhysiologyService(conn, clock=clock).read_state(
            world_id, "chuu"
        ).regulation.physical_capacity_milli == 100
    finally:
        conn.close()
