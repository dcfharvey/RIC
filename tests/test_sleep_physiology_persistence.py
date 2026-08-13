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


def _phase_distance(left, right):
    delta = abs(left - right)
    return min(delta, 1.0 - delta)


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

        assert ensure_schema(conn) == 57

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

        assert ensure_schema(conn) == 57

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
