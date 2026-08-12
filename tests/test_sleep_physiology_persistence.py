"""Raccord persistant inactif : lectures, gate et ownership."""

from dataclasses import asdict

import pytest

from vivarium.circadian_model import (
    RegulationInput,
    advance_regulation,
    calibration_profiles,
    effective_light_drive,
)
from vivarium.db import connect_database, transaction
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema, load_migrations, split_sql_statements
from vivarium.mvp_preflight import inspect_mvp_preflight
from vivarium.sleep_physiology import (
    ADDITIVE_MODEL_KEY,
    SleepPhysiologyError,
    SleepPhysiologyFoundationService,
    SleepPhysiologyService,
    SyntheticRegulationSegment,
)


ANCHOR = "2026-08-11T00:00:00+00:00"
DAY = "2026-08-11T12:00:00+00:00"
NIGHT = "2026-08-11T01:00:00+00:00"


def _profile_payload():
    candidate = asdict(calibration_profiles()["human_reference_candidate.v1"])
    for key in ("profile_key", "version", "evidence_class"):
        candidate.pop(key)
    return {"model_key": ADDITIVE_MODEL_KEY, "parameters": candidate}


def _schedule():
    return {
        "schema_version": 1,
        "segments": [
            {"start_second": 0, "end_second": 21600, "environmental_light_milli": 0},
            {"start_second": 21600, "end_second": 72000, "environmental_light_milli": 90000},
            {"start_second": 72000, "end_second": 86400, "environmental_light_milli": 0},
        ],
    }


@pytest.fixture
def wired_world():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world_id = IntegrationWorldService(conn).create_initial_world()["id"]
    foundation = SleepPhysiologyFoundationService(conn)
    foundation.register_light_schedule("test.day.v1", 1, _schedule())
    foundation.register_location_light_profile("test.interior.v1", 1, 25000, {"kind": "interior"})
    foundation.register_biology_profile(
        "test.human.v1", 1, "human_reference", _profile_payload()
    )
    foundation.assign_light_schedule(world_id, "test.day.v1", 1, ANCHOR, "test_configuration")
    for row in conn.execute("SELECT key FROM location WHERE world_id = ? ORDER BY key", (world_id,)):
        foundation.assign_location_light_profile(
            world_id, row["key"], "test.interior.v1", 1, ANCHOR, "test_configuration"
        )
    for row in conn.execute("SELECT key FROM character WHERE world_id = ? ORDER BY key", (world_id,)):
        foundation.assign_biology_profile(
            world_id, row["key"], "test.human.v1", 1, "test_configuration"
        )
    foundation.prepare_world(world_id, ADDITIVE_MODEL_KEY, 1, "test_operator")
    try:
        yield conn, world_id
    finally:
        conn.close()


def _activate_synthetic(conn, world_id):
    """Fixture test-only : le produit n'expose encore aucune activation."""
    with transaction(conn) as tx:
        tx.execute(
            "UPDATE world_physiology_system "
            "SET status='active', activated_at=?, activated_by=?, updated_at=? "
            "WHERE world_id=?",
            (ANCHOR, "synthetic_test", ANCHOR, world_id),
        )
        for row in tx.execute("SELECT id FROM character WHERE world_id=? ORDER BY id", (world_id,)):
            tx.execute(
                "INSERT INTO sleep_regulation_state "
                "(public_id, world_id, character_id, model_key, model_version, "
                "homeostatic_load_milli, circadian_phase_milli, anchor_at, updated_at) "
                "VALUES (?, ?, ?, ?, 1, 50000, 250000, ?, ?)",
                (f"regulation-{row['id']}", world_id, row["id"], ADDITIVE_MODEL_KEY, ANCHOR, ANCHOR),
            )
            tx.execute(
                "INSERT INTO physical_capacity_state "
                "(public_id, world_id, character_id, capacity_milli, rate_remainder, anchor_at, updated_at) "
                "VALUES (?, ?, ?, 70000, 0, ?, ?)",
                (f"capacity-{row['id']}", world_id, row["id"], ANCHOR, ANCHOR),
            )
            tx.execute(
                "INSERT INTO sleep_wake_hysteresis_state "
                "(public_id, world_id, character_id, previous_band, anchor_at, updated_at) "
                "VALUES (?, ?, ?, 'fragile', ?, ?)",
                (f"hysteresis-{row['id']}", world_id, row["id"], ANCHOR, ANCHOR),
            )
            tx.execute(
                "INSERT INTO sleep_regulation_precision_state "
                "(public_id, world_id, character_id, homeostatic_load_residue, "
                "circadian_phase_residue, anchor_at, updated_at) "
                "VALUES (?, ?, ?, 0.0, 0.0, ?, ?)",
                (f"precision-{row['id']}", world_id, row["id"], ANCHOR, ANCHOR),
            )


def _physiology_snapshot(conn):
    return {
        table: tuple(
            tuple(row)
            for row in conn.execute(f"SELECT * FROM {table} ORDER BY id")
        )
        for table in (
            "sleep_regulation_state",
            "physical_capacity_state",
            "sleep_regulation_precision_state",
            "sleep_wake_hysteresis_state",
            "canonical_event",
        )
    }


def _set_synthetic_state(
    conn,
    world_id,
    character_key,
    *,
    homeostatic_load_milli,
    circadian_phase_milli,
    physical_capacity_milli=70000,
    previous_band="stable",
):
    """Prépare une trajectoire synthétique sans créer de fait canonique."""
    character_id = conn.execute(
        "SELECT id FROM character WHERE world_id = ? AND key = ?", (world_id, character_key)
    ).fetchone()[0]
    with transaction(conn) as tx:
        tx.execute(
            "UPDATE sleep_regulation_state SET homeostatic_load_milli = ?, "
            "circadian_phase_milli = ?, anchor_at = ? WHERE world_id = ? AND character_id = ?",
            (homeostatic_load_milli, circadian_phase_milli, ANCHOR, world_id, character_id),
        )
        tx.execute(
            "UPDATE physical_capacity_state SET capacity_milli = ?, rate_remainder = 0, "
            "anchor_at = ? WHERE world_id = ? AND character_id = ?",
            (physical_capacity_milli, ANCHOR, world_id, character_id),
        )
        tx.execute(
            "UPDATE sleep_wake_hysteresis_state SET previous_band = ?, anchor_at = ? "
            "WHERE world_id = ? AND character_id = ?",
            (previous_band, ANCHOR, world_id, character_id),
        )
        tx.execute(
            "UPDATE sleep_regulation_precision_state SET homeostatic_load_residue = 0.0, "
            "circadian_phase_residue = 0.0, anchor_at = ? "
            "WHERE world_id = ? AND character_id = ?",
            (ANCHOR, world_id, character_id),
        )


def test_persistent_reader_is_gated_until_a_synthetic_active_world(wired_world):
    conn, world_id = wired_world
    service = SleepPhysiologyService(conn)

    with pytest.raises(SleepPhysiologyError) as caught:
        service.read_state(world_id, "sophie")
    assert caught.value.code == "physiology_inactive"

    _activate_synthetic(conn, world_id)
    before = _physiology_snapshot(conn)
    source = service.resolve_light_source_synthetic(world_id, "salon", DAY, state="wake")
    projection = service.project_synthetic(world_id, "sophie", source)

    assert projection.state.anchor_at == ANCHOR
    assert projection.state.previous_stability_band == "fragile"
    assert projection.propensity.family == "additive"
    assert projection.stability.band in {"stable", "fragile", "critical"}
    assert _physiology_snapshot(conn) == before


def test_light_resolution_uses_effective_canonical_assignments_and_sleep_occlusion(wired_world):
    conn, world_id = wired_world
    foundation = SleepPhysiologyFoundationService(conn)
    service = SleepPhysiologyService(conn)
    foundation.register_location_light_profile("test.dark.v2", 2, 10000, {"kind": "interior"})
    foundation.assign_location_light_profile(
        world_id, "salon", "test.dark.v2", 2, "2026-08-11T13:00:00+00:00", "test_configuration"
    )

    daytime = service.resolve_light_source_synthetic(world_id, "salon", DAY, state="wake")
    nighttime = service.resolve_light_source_synthetic(world_id, "salon", NIGHT, state="wake")
    after_change = service.resolve_light_source_synthetic(
        world_id, "salon", "2026-08-11T13:00:00+00:00", state="wake"
    )
    sleeping = service.resolve_light_source_synthetic(world_id, "salon", DAY, state="sleep", occluded=True)
    parameters = service.parameters_for_character(world_id, "sophie")

    assert daytime.environmental_light_milli == 90000
    assert nighttime.environmental_light_milli == 0
    assert after_change.location_exposure_milli == 10000
    assert effective_light_drive(sleeping, parameters) < effective_light_drive(daytime, parameters)


def test_light_resolution_rejects_a_foundation_schedule_that_is_not_operational(wired_world):
    conn, world_id = wired_world
    foundation = SleepPhysiologyFoundationService(conn)
    service = SleepPhysiologyService(conn)
    foundation.register_light_schedule("test.invalid.v1", 1, {"segments": []})
    foundation.assign_light_schedule(
        world_id, "test.invalid.v1", 1, "2026-08-11T14:00:00+00:00", "test_configuration"
    )

    with pytest.raises(SleepPhysiologyError) as caught:
        service.resolve_light_source_synthetic(world_id, "salon", "2026-08-11T14:00:00+00:00", state="wake")
    assert caught.value.code == "invalid_light_schedule"


def test_preflight_reports_prepared_system_without_materializing_states(wired_world):
    conn, world_id = wired_world

    report = inspect_mvp_preflight(conn, world_id=world_id)

    physiology = next(check for check in report.checks if check.key == "sleep_physiology")
    assert physiology.passed
    assert physiology.detail == "prepared complet et toujours inactif"
    assert conn.execute("SELECT COUNT(*) FROM sleep_regulation_state").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM physical_capacity_state").fetchone()[0] == 0


def test_prepared_rejects_an_unselected_model_and_preflight_falsifies_one(wired_world):
    conn, world_id = wired_world
    foundation = SleepPhysiologyFoundationService(conn)

    with pytest.raises(SleepPhysiologyError) as caught:
        foundation.prepare_world(world_id, "ric.sleep.sensitivity_modulated.v1", 1, "test_operator")
    assert caught.value.code == "invalid_model"

    conn.execute(
        "UPDATE world_physiology_system SET prepared_model_key = ? WHERE world_id = ?",
        ("ric.sleep.sensitivity_modulated.v1", world_id),
    )
    report = inspect_mvp_preflight(conn, world_id=world_id)
    physiology = next(check for check in report.checks if check.key == "sleep_physiology")
    assert not physiology.passed


def test_active_state_requires_dense_hysteresis_memory(wired_world):
    conn, world_id = wired_world
    _activate_synthetic(conn, world_id)
    service = SleepPhysiologyService(conn)
    character_id = conn.execute(
        "SELECT id FROM character WHERE world_id = ? AND key = 'sophie'", (world_id,)
    ).fetchone()[0]
    conn.execute(
        "DELETE FROM sleep_wake_hysteresis_state WHERE world_id = ? AND character_id = ?",
        (world_id, character_id),
    )

    with pytest.raises(SleepPhysiologyError) as caught:
        service.read_state(world_id, "sophie")
    assert caught.value.code == "hysteresis_state_missing"
    report = inspect_mvp_preflight(conn, world_id=world_id)
    physiology = next(check for check in report.checks if check.key == "sleep_physiology")
    assert not physiology.passed


def test_persistent_reader_rejects_desynchronized_hysteresis_anchor(wired_world):
    conn, world_id = wired_world
    _activate_synthetic(conn, world_id)
    service = SleepPhysiologyService(conn)
    character_id = conn.execute(
        "SELECT id FROM character WHERE world_id = ? AND key = 'sophie'", (world_id,)
    ).fetchone()[0]
    conn.execute(
        "UPDATE sleep_wake_hysteresis_state SET anchor_at = ? "
        "WHERE world_id = ? AND character_id = ?",
        ("2026-08-11T00:00:01+00:00", world_id, character_id),
    )

    with pytest.raises(SleepPhysiologyError) as caught:
        service.read_state(world_id, "sophie")
    assert caught.value.code == "inconsistent_hysteresis_anchor"


def test_persistent_reader_rejects_desynchronized_precision_anchor(wired_world):
    conn, world_id = wired_world
    _activate_synthetic(conn, world_id)
    service = SleepPhysiologyService(conn)
    character_id = conn.execute(
        "SELECT id FROM character WHERE world_id = ? AND key = 'sophie'", (world_id,)
    ).fetchone()[0]
    conn.execute(
        "UPDATE sleep_regulation_precision_state SET anchor_at = ? "
        "WHERE world_id = ? AND character_id = ?",
        ("2026-08-11T00:00:01+00:00", world_id, character_id),
    )

    with pytest.raises(SleepPhysiologyError) as caught:
        service.read_state(world_id, "sophie")
    assert caught.value.code == "inconsistent_precision_anchor"


def test_synthetic_materialization_is_partition_stable_restart_safe_and_noncanonical(wired_world):
    conn, world_id = wired_world
    _activate_synthetic(conn, world_id)
    source = RegulationInput("wake", 0, 25000)
    service = SleepPhysiologyService(conn)
    before_events = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)
    ).fetchone()[0]

    single = service.materialize_synthetic(world_id, "sophie", "2026-08-11T06:00:00+00:00", source)
    segmented = service.materialize_segments_synthetic(
        world_id,
        "erika",
        (
            SyntheticRegulationSegment("2026-08-11T00:01:01+00:00", source),
            SyntheticRegulationSegment("2026-08-11T06:00:00+00:00", source),
        ),
    )
    restarted = SleepPhysiologyService(conn)
    snapshot = _physiology_snapshot(conn)
    repeated = restarted.materialize_synthetic(world_id, "sophie", "2026-08-11T06:00:00+00:00", source)

    assert single.changed
    assert all(result.changed for result in segmented)
    assert not repeated.changed
    assert _physiology_snapshot(conn) == snapshot
    assert abs(
        single.projection.state.regulation.homeostatic_load_milli
        - segmented[-1].projection.state.regulation.homeostatic_load_milli
    ) <= 1
    assert abs(
        single.projection.state.regulation.physical_capacity_milli
        - segmented[-1].projection.state.regulation.physical_capacity_milli
    ) <= 1
    phase_delta = abs(
        single.projection.state.regulation.circadian_phase_milli
        - segmented[-1].projection.state.regulation.circadian_phase_milli
    )
    assert min(phase_delta, 1_000_000 - phase_delta) <= 2
    assert conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)
    ).fetchone()[0] == before_events


def test_synthetic_hysteresis_is_partition_stable_through_fragile_band(wired_world):
    conn, world_id = wired_world
    _activate_synthetic(conn, world_id)
    service = SleepPhysiologyService(conn)
    source = RegulationInput("wake", 0, 25000)
    for character_key in ("sophie", "erika"):
        _set_synthetic_state(
            conn,
            world_id,
            character_key,
            homeostatic_load_milli=5000,
            circadian_phase_milli=300000,
            previous_band="stable",
        )

    single = service.materialize_synthetic(world_id, "sophie", "2026-08-11T15:00:00+00:00", source)
    partitioned = service.materialize_segments_synthetic(
        world_id,
        "erika",
        (
            SyntheticRegulationSegment("2026-08-11T00:01:01+00:00", source),
            SyntheticRegulationSegment("2026-08-11T05:38:14+00:00", source),
            SyntheticRegulationSegment("2026-08-11T15:00:00+00:00", source),
        ),
    )

    assert single.projection.state.previous_stability_band == "fragile"
    assert partitioned[-1].projection.state.previous_stability_band == "fragile"
    assert (
        single.projection.state.regulation.homeostatic_load_milli,
        single.projection.state.regulation.circadian_phase_milli,
        single.projection.state.regulation.physical_capacity_milli,
        single.projection.state.previous_stability_band,
    ) == (
        partitioned[-1].projection.state.regulation.homeostatic_load_milli,
        partitioned[-1].projection.state.regulation.circadian_phase_milli,
        partitioned[-1].projection.state.regulation.physical_capacity_milli,
        partitioned[-1].projection.state.previous_stability_band,
    )
    assert abs(
        single.projection.state.regulation.homeostatic_load
        - partitioned[-1].projection.state.regulation.homeostatic_load
    ) < 1e-12
    assert _phase_distance(
        single.projection.state.regulation.circadian_phase,
        partitioned[-1].projection.state.regulation.circadian_phase,
    ) < 1e-12


def test_synthetic_hysteresis_is_partition_stable_through_critical_entry_and_exit(wired_world):
    conn, world_id = wired_world
    _activate_synthetic(conn, world_id)
    service = SleepPhysiologyService(conn)
    wake = RegulationInput("wake", 0, 25000)
    sleep = RegulationInput("sleep", 0, 25000, occluded=True)
    for character_key in ("sophie", "erika"):
        _set_synthetic_state(
            conn,
            world_id,
            character_key,
            homeostatic_load_milli=95000,
            circadian_phase_milli=300000,
            previous_band="stable",
        )

    sophie_wake = service.materialize_synthetic(world_id, "sophie", "2026-08-11T01:00:00+00:00", wake)
    sophie_final = service.materialize_synthetic(world_id, "sophie", "2026-08-11T13:00:00+00:00", sleep)
    erika_segments = service.materialize_segments_synthetic(
        world_id,
        "erika",
        (
            SyntheticRegulationSegment("2026-08-11T00:01:01+00:00", wake),
            SyntheticRegulationSegment("2026-08-11T01:00:00+00:00", wake),
            SyntheticRegulationSegment("2026-08-11T01:01:13+00:00", sleep),
            SyntheticRegulationSegment("2026-08-11T13:00:00+00:00", sleep),
        ),
    )

    assert sophie_wake.projection.stability.band == "critical"
    assert erika_segments[1].projection.stability.band == "critical"
    assert sophie_final.projection.stability.band == "stable"
    assert erika_segments[-1].projection.stability.band == "stable"
    assert (
        sophie_final.projection.state.regulation.homeostatic_load_milli,
        sophie_final.projection.state.regulation.circadian_phase_milli,
        sophie_final.projection.state.regulation.physical_capacity_milli,
        sophie_final.projection.state.previous_stability_band,
    ) == (
        erika_segments[-1].projection.state.regulation.homeostatic_load_milli,
        erika_segments[-1].projection.state.regulation.circadian_phase_milli,
        erika_segments[-1].projection.state.regulation.physical_capacity_milli,
        erika_segments[-1].projection.state.previous_stability_band,
    )
    assert abs(
        sophie_final.projection.state.regulation.homeostatic_load
        - erika_segments[-1].projection.state.regulation.homeostatic_load
    ) < 1e-12
    assert _phase_distance(
        sophie_final.projection.state.regulation.circadian_phase,
        erika_segments[-1].projection.state.regulation.circadian_phase,
    ) < 1e-12


def _phase_distance(left, right):
    delta = abs(left - right)
    return min(delta, 1.0 - delta)


def test_synthetic_materialization_preserves_long_h_wake_and_sleep_trajectories(wired_world):
    conn, world_id = wired_world
    _activate_synthetic(conn, world_id)
    service = SleepPhysiologyService(conn)
    wake = RegulationInput("wake", 0, 25000)
    sleep = RegulationInput("sleep", 0, 25000, occluded=True)
    for character_key, load in (("sophie", 50000), ("erika", 95000)):
        _set_synthetic_state(
            conn,
            world_id,
            character_key,
            homeostatic_load_milli=load,
            circadian_phase_milli=300000,
        )

    wake_initial = service.read_state(world_id, "sophie")
    wake_expected = advance_regulation(
        wake_initial.regulation, wake, 24 * 3600, service.parameters_for_character(world_id, "sophie")
    )
    wake_result = service.materialize_synthetic(
        world_id, "sophie", "2026-08-12T00:00:00+00:00", wake
    )
    sleep_initial = service.read_state(world_id, "erika")
    sleep_expected = advance_regulation(
        sleep_initial.regulation, sleep, 12 * 3600, service.parameters_for_character(world_id, "erika")
    )
    sleep_result = service.materialize_synthetic(
        world_id, "erika", "2026-08-11T12:00:00+00:00", sleep
    )

    assert wake_result.projection.state.regulation.homeostatic_load > 0.85
    assert abs(wake_result.projection.state.regulation.homeostatic_load - wake_expected.homeostatic_load) < 1e-10
    assert sleep_result.projection.state.regulation.homeostatic_load < 0.02
    assert abs(sleep_result.projection.state.regulation.homeostatic_load - sleep_expected.homeostatic_load) < 1e-10


def test_synthetic_materialization_preserves_free_running_phase_across_irregular_partitions(wired_world):
    conn, world_id = wired_world
    _activate_synthetic(conn, world_id)
    service = SleepPhysiologyService(conn)
    source = RegulationInput("wake", 0, 25000)
    for character_key in ("sophie", "erika"):
        _set_synthetic_state(
            conn,
            world_id,
            character_key,
            homeostatic_load_milli=50000,
            circadian_phase_milli=300000,
        )

    duration = 7 * 24 * 3600
    expected = advance_regulation(
        service.read_state(world_id, "sophie").regulation,
        source,
        duration,
        service.parameters_for_character(world_id, "sophie"),
    )
    single = service.materialize_synthetic(world_id, "sophie", "2026-08-18T00:00:00+00:00", source)
    partitioned = service.materialize_segments_synthetic(
        world_id,
        "erika",
        (
            SyntheticRegulationSegment("2026-08-11T00:01:01+00:00", source),
            SyntheticRegulationSegment("2026-08-13T05:38:14+00:00", source),
            SyntheticRegulationSegment("2026-08-18T00:00:00+00:00", source),
        ),
    )[-1]

    assert _phase_distance(single.projection.state.regulation.circadian_phase, expected.circadian_phase) < 1e-9
    assert _phase_distance(partitioned.projection.state.regulation.circadian_phase, expected.circadian_phase) < 1e-9
    assert _phase_distance(
        single.projection.state.regulation.circadian_phase,
        partitioned.projection.state.regulation.circadian_phase,
    ) < 1e-12
    assert abs(
        single.projection.state.regulation.homeostatic_load
        - partitioned.projection.state.regulation.homeostatic_load
    ) < 1e-12


def test_synthetic_segments_preserve_h_p_separation_and_hysteresis_anchor(wired_world):
    conn, world_id = wired_world
    _activate_synthetic(conn, world_id)
    service = SleepPhysiologyService(conn)
    wake = RegulationInput("wake", 0, 25000)
    rest = RegulationInput("rest", 0, 25000)
    sleep = RegulationInput("sleep", 0, 25000, occluded=True)

    after_wake = service.materialize_synthetic(world_id, "sophie", "2026-08-11T02:00:00+00:00", wake)
    after_rest = service.materialize_synthetic(world_id, "sophie", "2026-08-11T03:00:00+00:00", rest)
    after_sleep = service.materialize_synthetic(world_id, "sophie", "2026-08-11T04:00:00+00:00", sleep)
    hysteresis = conn.execute(
        "SELECT previous_band, anchor_at FROM sleep_wake_hysteresis_state h "
        "JOIN character c ON c.id = h.character_id AND c.world_id = h.world_id "
        "WHERE h.world_id = ? AND c.key = 'sophie'",
        (world_id,),
    ).fetchone()

    assert after_rest.projection.state.regulation.homeostatic_load_milli > after_wake.projection.state.regulation.homeostatic_load_milli
    assert after_rest.projection.state.regulation.physical_capacity_milli > after_wake.projection.state.regulation.physical_capacity_milli
    assert after_sleep.projection.state.regulation.homeostatic_load_milli < after_rest.projection.state.regulation.homeostatic_load_milli
    assert tuple(hysteresis) == (after_sleep.projection.stability.band, "2026-08-11T04:00:00.000+00:00")


def test_synthetic_scheduler_finds_a_critical_boundary_without_writing(wired_world):
    conn, world_id = wired_world
    _activate_synthetic(conn, world_id)
    service = SleepPhysiologyService(conn)
    source = RegulationInput("wake", 0, 25000)
    before = _physiology_snapshot(conn)

    boundary = service.next_critical_boundary_synthetic(
        world_id, "sophie", source, "2026-08-12T00:00:00+00:00"
    )

    assert boundary is not None
    assert ANCHOR < boundary <= "2026-08-12T00:00:00+00:00"
    assert _physiology_snapshot(conn) == before


def test_hysteresis_memory_is_physiological_but_interruption_marker_is_not_a_table():
    conn = connect_database(":memory:")
    try:
        ensure_schema(conn)
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(sleep_wake_hysteresis_state)")
        }
        assert "previous_band" in columns
        assert "interrupted_activity_id" not in columns
    finally:
        conn.close()


def test_0047_and_0048_preserve_prepared_foundation_and_canonical_history():
    conn = connect_database(":memory:")
    try:
        conn.execute(
            "CREATE TABLE migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL, checksum TEXT NOT NULL)"
        )
        for migration in load_migrations():
            if migration.version > 46:
                continue
            with transaction(conn):
                for statement in split_sql_statements(migration.sql):
                    conn.execute(statement)
                conn.execute(
                    "INSERT INTO migrations (version, name, applied_at, checksum) VALUES (?, ?, ?, ?)",
                    (migration.version, migration.name, ANCHOR, migration.checksum),
                )
        world_id = IntegrationWorldService(conn).create_initial_world()["id"]
        foundation = SleepPhysiologyFoundationService(conn)
        foundation.register_light_schedule("migration.day.v1", 1, _schedule())
        foundation.register_location_light_profile("migration.interior.v1", 1, 25000, {"kind": "interior"})
        foundation.register_biology_profile("migration.human.v1", 1, "human_reference", _profile_payload())
        foundation.assign_light_schedule(world_id, "migration.day.v1", 1, ANCHOR, "migration_test")
        for row in conn.execute("SELECT key FROM location WHERE world_id = ?", (world_id,)):
            foundation.assign_location_light_profile(
                world_id, row["key"], "migration.interior.v1", 1, ANCHOR, "migration_test"
            )
        for row in conn.execute("SELECT key FROM character WHERE world_id = ?", (world_id,)):
            foundation.assign_biology_profile(
                world_id, row["key"], "migration.human.v1", 1, "migration_test"
            )
        foundation.prepare_world(world_id, ADDITIVE_MODEL_KEY, 1, "migration_test")
        before = tuple(
            tuple(row)
            for row in conn.execute(
                "SELECT seq, event_type, occurred_at, payload FROM canonical_event WHERE world_id = ? ORDER BY seq",
                (world_id,),
            )
        )

        assert ensure_schema(conn) == 51

        prepared = conn.execute(
            "SELECT status, activated_at, activated_by FROM world_physiology_system WHERE world_id = ?",
            (world_id,),
        ).fetchone()
        after = tuple(
            tuple(row)
            for row in conn.execute(
                "SELECT seq, event_type, occurred_at, payload FROM canonical_event WHERE world_id = ? ORDER BY seq",
                (world_id,),
            )
        )
        assert tuple(prepared) == ("prepared", None, None)
        assert after == before
        assert conn.execute("SELECT COUNT(*) FROM sleep_wake_hysteresis_state").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM sleep_regulation_precision_state").fetchone()[0] == 0
    finally:
        conn.close()


def test_0048_backfills_zero_precision_residues_without_canonical_history():
    conn = connect_database(":memory:")
    try:
        conn.execute(
            "CREATE TABLE migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL, checksum TEXT NOT NULL)"
        )
        for migration in load_migrations():
            if migration.version > 47:
                continue
            with transaction(conn):
                for statement in split_sql_statements(migration.sql):
                    conn.execute(statement)
                conn.execute(
                    "INSERT INTO migrations (version, name, applied_at, checksum) VALUES (?, ?, ?, ?)",
                    (migration.version, migration.name, ANCHOR, migration.checksum),
                )
        world_id = IntegrationWorldService(conn).create_initial_world()["id"]
        character_id = conn.execute(
            "SELECT id FROM character WHERE world_id = ? AND key = 'sophie'", (world_id,)
        ).fetchone()[0]
        conn.execute(
            "UPDATE world_physiology_system SET status = 'active', prepared_model_key = ?, "
            "prepared_model_version = 1, prepared_at = ?, prepared_by = 'test', "
            "activated_at = ?, activated_by = 'test' WHERE world_id = ?",
            (ADDITIVE_MODEL_KEY, ANCHOR, ANCHOR, world_id),
        )
        conn.execute(
            "INSERT INTO sleep_regulation_state "
            "(public_id, world_id, character_id, model_key, model_version, homeostatic_load_milli, "
            "circadian_phase_milli, anchor_at, updated_at) "
            "VALUES ('regulation-test', ?, ?, ?, 1, 50000, 250000, ?, ?)",
            (world_id, character_id, ADDITIVE_MODEL_KEY, ANCHOR, ANCHOR),
        )
        conn.execute(
            "INSERT INTO physical_capacity_state "
            "(public_id, world_id, character_id, capacity_milli, rate_remainder, anchor_at, updated_at) "
            "VALUES ('capacity-test', ?, ?, 70000, 0, ?, ?)",
            (world_id, character_id, ANCHOR, ANCHOR),
        )
        conn.execute(
            "INSERT INTO sleep_wake_hysteresis_state "
            "(public_id, world_id, character_id, previous_band, anchor_at, updated_at) "
            "VALUES ('hysteresis-test', ?, ?, 'stable', ?, ?)",
            (world_id, character_id, ANCHOR, ANCHOR),
        )
        before = tuple(
            tuple(row)
            for row in conn.execute(
                "SELECT seq, event_type, occurred_at, payload FROM canonical_event "
                "WHERE world_id = ? ORDER BY seq",
                (world_id,),
            )
        )

        assert ensure_schema(conn) == 51

        precision = conn.execute(
            "SELECT homeostatic_load_residue, circadian_phase_residue, anchor_at "
            "FROM sleep_regulation_precision_state WHERE world_id = ? AND character_id = ?",
            (world_id, character_id),
        ).fetchone()
        after = tuple(
            tuple(row)
            for row in conn.execute(
                "SELECT seq, event_type, occurred_at, payload FROM canonical_event "
                "WHERE world_id = ? ORDER BY seq",
                (world_id,),
            )
        )
        assert tuple(precision) == (0.0, 0.0, ANCHOR)
        assert after == before
    finally:
        conn.close()
