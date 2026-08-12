"""Catalogue P inactif : validation, provenance et absence de comportement."""

from datetime import datetime, timezone

import pytest

from vivarium.db import connect_database, transaction
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema, load_migrations, split_sql_statements
from vivarium.sleep_physiology import SleepPhysiologyError, SleepPhysiologyFoundationService
from vivarium.util import to_iso


T0 = datetime(2026, 8, 11, 12, tzinfo=timezone.utc)


class FakeClock:
    def now(self):
        return T0

    def now_iso(self):
        return to_iso(self.now())


def _candidate_policy():
    """Fixture synthétique seulement; ce n'est pas une calibration RIC."""
    return {
        "schema_version": 1,
        "activity_cost_per_hour_milli": {
            "none": 0, "light": 100, "moderate": 300, "vigorous": 600,
        },
        "minimum_capacity_milli": {
            "none": 0, "light": 100, "moderate": 300, "vigorous": 600,
        },
        "traversal_cost_per_edge_milli": 25,
        "recovery_per_hour_milli": {"rest": 100, "sleep": 200},
    }


def _apply_through(conn, version):
    conn.execute(
        "CREATE TABLE migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, "
        "applied_at TEXT NOT NULL, checksum TEXT NOT NULL)"
    )
    for migration in load_migrations():
        if migration.version > version:
            continue
        with transaction(conn):
            for statement in split_sql_statements(migration.sql):
                conn.execute(statement)
            conn.execute(
                "INSERT INTO migrations (version, name, applied_at, checksum) VALUES (?, ?, ?, ?)",
                (migration.version, migration.name, to_iso(T0), migration.checksum),
            )


@pytest.fixture
def configured_world():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    service = SleepPhysiologyFoundationService(conn, clock=clock)
    policy = service.register_physical_capacity_policy(
        "synthetic.capacity.v1", 1, _candidate_policy(), "test_calibration_only"
    )
    try:
        yield conn, world_id, service, policy
    finally:
        conn.close()


def test_policy_catalogue_is_versioned_immutable_and_assignment_preserves_provenance(configured_world):
    conn, world_id, service, policy = configured_world
    before_events = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)
    ).fetchone()[0]

    assigned = service.assign_physical_capacity_policy(
        world_id, policy.policy_key, policy.version, "synthetic_world_setup"
    )

    assert assigned == policy
    row = conn.execute(
        "SELECT a.provenance AS assignment_provenance, p.provenance AS policy_provenance "
        "FROM world_physical_capacity_policy_assignment a "
        "JOIN physical_capacity_policy p ON p.id = a.policy_id WHERE a.world_id = ?", (world_id,)
    ).fetchone()
    assert tuple(row) == ("synthetic_world_setup", "test_calibration_only")
    assert service.world_physical_capacity_policy(world_id) == policy
    assert conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)
    ).fetchone()[0] == before_events
    assert conn.execute("SELECT COUNT(*) FROM physical_capacity_state").fetchone()[0] == 0

    with pytest.raises(Exception, match="immutable"):
        conn.execute("UPDATE physical_capacity_policy SET provenance = 'mutated'")
    with pytest.raises(Exception, match="append-only"):
        conn.execute("DELETE FROM world_physical_capacity_policy_assignment WHERE world_id = ?", (world_id,))
    with pytest.raises(SleepPhysiologyError) as duplicate:
        service.assign_physical_capacity_policy(
            world_id, policy.policy_key, policy.version, "second_assignment"
        )
    assert duplicate.value.code == "duplicate_assignment"


def test_policy_shape_is_complete_but_contains_no_default_calibration(configured_world):
    _conn, _world_id, service, _policy = configured_world
    incomplete = _candidate_policy()
    incomplete["activity_cost_per_hour_milli"].pop("vigorous")

    with pytest.raises(SleepPhysiologyError) as raised:
        service.register_physical_capacity_policy(
            "synthetic.incomplete.v1", 1, incomplete, "test_calibration_only"
        )
    assert raised.value.code == "invalid_configuration"


def test_validation_requires_explicit_activity_metadata_without_writing_p_or_canon(configured_world):
    conn, world_id, service, policy = configured_world
    service.assign_physical_capacity_policy(
        world_id, policy.policy_key, policy.version, "synthetic_world_setup"
    )
    before = (
        conn.execute("SELECT COUNT(*) FROM physical_capacity_state").fetchone()[0],
        conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)).fetchone()[0],
    )

    with pytest.raises(SleepPhysiologyError) as raised:
        service.validate_physical_capacity_configuration(world_id)
    assert raised.value.code == "activity_physical_class_missing"

    # Données de banc synthétique : elles vérifient le validateur mais ne sont
    # ni une calibration livrée ni une conversion depuis `energie`.
    conn.execute("UPDATE activity_definition SET physical_load_class = 'none' WHERE world_id = ?", (world_id,))
    assert service.validate_physical_capacity_configuration(world_id) == policy
    conn.execute(
        "UPDATE activity_definition SET requires_sustained_wakefulness = NULL "
        "WHERE world_id = ? AND activity_type = 'eat'", (world_id,)
    )
    with pytest.raises(SleepPhysiologyError) as missing_wakefulness:
        service.validate_physical_capacity_configuration(world_id)
    assert missing_wakefulness.value.code == "activity_wakefulness_missing"
    assert (
        conn.execute("SELECT COUNT(*) FROM physical_capacity_state").fetchone()[0],
        conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)).fetchone()[0],
    ) == before


def test_forward_migration_from_49_creates_no_policy_or_canonical_history():
    conn = connect_database(":memory:")
    try:
        _apply_through(conn, 49)
        world = IntegrationWorldService(conn, clock=FakeClock()).create_initial_world()
        before = conn.execute(
            "SELECT COUNT(*), MAX(seq) FROM canonical_event WHERE world_id = ?", (world["id"],)
        ).fetchone()

        assert ensure_schema(conn) == 54

        assert conn.execute("SELECT COUNT(*) FROM physical_capacity_policy").fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM world_physical_capacity_policy_assignment"
        ).fetchone()[0] == 0
        after = conn.execute(
            "SELECT COUNT(*), MAX(seq) FROM canonical_event WHERE world_id = ?", (world["id"],)
        ).fetchone()
        assert tuple(after) == tuple(before)
    finally:
        conn.close()
