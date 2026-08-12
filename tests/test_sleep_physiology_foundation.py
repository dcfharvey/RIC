"""Fondations inactives du futur domaine circadien/veille-sommeil."""

import pytest

from vivarium.db import connect_database, transaction
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema, load_migrations, split_sql_statements
from vivarium.mvp_preflight import inspect_mvp_preflight
from vivarium.runtime_session import RuntimeSessionService
from vivarium.sleep_physiology import (
    ADDITIVE_MODEL_KEY,
    InitialPhysiologyState,
    SleepPhysiologyError,
    SleepPhysiologyFoundationService,
)


@pytest.fixture
def prepared_world():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world = IntegrationWorldService(conn).create_initial_world()
    service = SleepPhysiologyFoundationService(conn)
    try:
        yield conn, world["id"], service
    finally:
        conn.close()


def _configure_all(conn, world_id, service):
    service.register_light_schedule("residence.day.v1", 1, {"segments": []})
    service.register_location_light_profile("residence.interior.v1", 1, 25000, {"kind": "interior"})
    service.register_biology_profile("human.reference.v1", 1, "human_reference", {"phase": "pending"})
    service.assign_light_schedule(
        world_id, "residence.day.v1", 1, "2026-08-11T12:00:00+00:00", "operator_configuration"
    )
    for row in conn.execute("SELECT key FROM location WHERE world_id = ? ORDER BY key", (world_id,)):
        service.assign_location_light_profile(
            world_id, row["key"], "residence.interior.v1", 1,
            "2026-08-11T12:00:00+00:00", "operator_configuration",
        )
    for row in conn.execute("SELECT key FROM character WHERE world_id = ? ORDER BY key", (world_id,)):
        service.assign_biology_profile(
            world_id, row["key"], "human.reference.v1", 1, "operator_configuration"
        )


def test_foundation_preparation_is_inactive_and_creates_no_lived_event(prepared_world):
    conn, world_id, service = prepared_world
    _configure_all(conn, world_id, service)
    before_events = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)
    ).fetchone()[0]

    prepared = service.prepare_world(world_id, ADDITIVE_MODEL_KEY, 1, "operator_review")

    assert prepared == {"world_id": world_id, "status": "prepared", "model_key": ADDITIVE_MODEL_KEY, "model_version": 1}
    assert service.system_status(world_id) == "prepared"
    assert conn.execute("SELECT COUNT(*) FROM sleep_regulation_state").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM physical_capacity_state").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM sleep_physiology_audit").fetchone()[0] == 0
    assert conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)
    ).fetchone()[0] == before_events


def test_preparation_requires_complete_light_and_biology_configuration(prepared_world):
    conn, world_id, service = prepared_world
    service.register_light_schedule("residence.day.v1", 1, {"segments": []})
    service.assign_light_schedule(
        world_id, "residence.day.v1", 1, "2026-08-11T12:00:00+00:00", "operator_configuration"
    )

    with pytest.raises(SleepPhysiologyError) as caught:
        service.prepare_world(world_id, ADDITIVE_MODEL_KEY, 1, "operator_review")
    assert caught.value.code == "location_light_missing"
    assert service.system_status(world_id) == "inactive"


def test_preparation_refuses_an_open_runtime_session(prepared_world):
    conn, world_id, service = prepared_world
    _configure_all(conn, world_id, service)
    session = RuntimeSessionService(conn).start(world_id)
    try:
        with pytest.raises(SleepPhysiologyError) as caught:
            service.prepare_world(world_id, ADDITIVE_MODEL_KEY, 1, "operator_review")
        assert caught.value.code == "runtime_session_open"
    finally:
        RuntimeSessionService(conn).stop(session.session_id)


def test_profile_catalogues_and_assignments_are_immutable(prepared_world):
    conn, world_id, service = prepared_world
    service.register_light_schedule("residence.day.v1", 1, {"segments": []})
    service.assign_light_schedule(
        world_id, "residence.day.v1", 1, "2026-08-11T12:00:00+00:00", "operator_configuration"
    )
    profile_id = conn.execute("SELECT id FROM light_schedule_profile").fetchone()[0]
    assignment_id = conn.execute("SELECT id FROM world_light_schedule_assignment").fetchone()[0]

    with pytest.raises(Exception, match="immutable"):
        conn.execute("UPDATE light_schedule_profile SET schedule_json = '{}' WHERE id = ?", (profile_id,))
    with pytest.raises(Exception, match="append-only"):
        conn.execute("DELETE FROM world_light_schedule_assignment WHERE id = ?", (assignment_id,))


def test_initial_state_validation_is_read_only_and_requires_every_character(prepared_world):
    conn, world_id, service = prepared_world
    characters = [row["key"] for row in conn.execute(
        "SELECT key FROM character WHERE world_id = ? ORDER BY key", (world_id,)
    )]
    values = {
        key: InitialPhysiologyState(50000, index * 1000, 75000)
        for index, key in enumerate(characters)
    }
    before = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("sleep_regulation_state", "physical_capacity_state", "sleep_physiology_audit", "canonical_event")
    }

    assert service.validate_initial_states(world_id, values) == tuple(characters)
    assert {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in before
    } == before

    values.pop(characters[0])
    with pytest.raises(SleepPhysiologyError) as caught:
        service.validate_initial_states(world_id, values)
    assert caught.value.code == "incomplete_initial_state"


def test_no_character_identity_is_interpreted_by_the_biology_owner(prepared_world):
    _conn, world_id, service = prepared_world
    service.register_biology_profile("generic.feline.v1", 1, "generic_feline", {"phase": "pending"})
    service.assign_biology_profile(world_id, "patoune", "generic.feline.v1", 1, "operator_configuration")
    profile = service.biology_profile("generic.feline.v1", 1)
    assert profile["evidence_class"] == "generic_feline"


def test_forward_migration_from_schema_44_preserves_history_and_leaves_persistence_inactive():
    conn = connect_database(":memory:")
    try:
        conn.execute(
            "CREATE TABLE migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL, checksum TEXT NOT NULL)"
        )
        for migration in load_migrations():
            if migration.version > 44:
                continue
            with transaction(conn):
                for statement in split_sql_statements(migration.sql):
                    conn.execute(statement)
                conn.execute(
                    "INSERT INTO migrations (version, name, applied_at, checksum) VALUES (?, ?, ?, ?)",
                    (migration.version, migration.name, "2026-08-11T12:00:00+00:00", migration.checksum),
                )
        world = IntegrationWorldService(conn).create_initial_world()
        before = conn.execute(
            "SELECT COUNT(*), MAX(seq) FROM canonical_event WHERE world_id = ?", (world["id"],)
        ).fetchone()

        assert ensure_schema(conn) == 49

        after = conn.execute(
            "SELECT COUNT(*), MAX(seq) FROM canonical_event WHERE world_id = ?", (world["id"],)
        ).fetchone()
        assert tuple(after) == tuple(before)
        assert SleepPhysiologyFoundationService(conn).system_status(world["id"]) == "inactive"
        assert conn.execute("SELECT COUNT(*) FROM sleep_wake_hysteresis_state").fetchone()[0] == 0
        assert inspect_mvp_preflight(conn).healthy
    finally:
        conn.close()
