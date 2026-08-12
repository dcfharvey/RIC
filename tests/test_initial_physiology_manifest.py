"""Fondations inactives du manifeste physiologique initial T0."""

from dataclasses import asdict, replace

import pytest

from vivarium.circadian_model import calibration_profiles
from vivarium.db import connect_database, transaction
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema, load_migrations, split_sql_statements
from vivarium.runtime_session import RuntimeSessionService
from vivarium.sleep_physiology import (
    ADDITIVE_MODEL_KEY,
    InitialPhysiologyManifestEntry,
    SleepPhysiologyError,
    SleepPhysiologyFoundationService,
)


ANCHOR = "2026-08-11T12:00:00+00:00"
POLICY = {
    "schema_version": 1,
    "model_key": ADDITIVE_MODEL_KEY,
    "model_version": 1,
    "homeostatic_load_region": {"min_milli": 40_000, "max_milli": 60_000},
    "physical_capacity_region": {"min_milli": 70_000, "max_milli": 90_000},
    "bootstrap_rule": "wake_stability.stable_seed.v1",
    "residue_rule": "zero_at_t0.v1",
}
PHASE_RULE = {
    "schema_version": 1,
    "rule_kind": "schedule_light_phase_windows.v1",
    "light_phase_windows": [[200_000, 300_000]],
    "dark_phase_windows": [[700_000, 800_000]],
}
SCHEDULE = {
    "schema_version": 1,
    "segments": [
        {"start_second": 0, "end_second": 21600, "environmental_light_milli": 0},
        {"start_second": 21600, "end_second": 72000, "environmental_light_milli": 90000},
        {"start_second": 72000, "end_second": 86400, "environmental_light_milli": 0},
    ],
}


def _profile_payload():
    payload = asdict(calibration_profiles()["human_reference_candidate.v1"])
    for key in ("profile_key", "version", "evidence_class"):
        payload.pop(key)
    return {"model_key": ADDITIVE_MODEL_KEY, "parameters": payload}


@pytest.fixture
def manifest_world():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world_id = IntegrationWorldService(conn).create_initial_world()["id"]
    service = SleepPhysiologyFoundationService(conn)
    service.register_light_schedule("manifest.day.v1", 1, SCHEDULE)
    service.register_location_light_profile("manifest.interior.v1", 1, 25_000, {"kind": "interior"})
    service.register_biology_profile("manifest.human.v1", 1, "human_reference", _profile_payload())
    service.register_initial_physiology_policy("manifest.regions.v1", 1, POLICY, "calibration_candidate")
    service.register_t0_phase_rule("manifest.light_phase.v1", 1, PHASE_RULE, "design_t0_relation")
    service.assign_light_schedule(world_id, "manifest.day.v1", 1, ANCHOR, "test_configuration")
    for row in conn.execute("SELECT key FROM location WHERE world_id=? ORDER BY key", (world_id,)):
        service.assign_location_light_profile(world_id, row["key"], "manifest.interior.v1", 1, ANCHOR, "test_configuration")
    for row in conn.execute("SELECT key FROM character WHERE world_id=? ORDER BY key", (world_id,)):
        service.assign_biology_profile(world_id, row["key"], "manifest.human.v1", 1, "test_configuration")
    try:
        yield conn, world_id, service
    finally:
        conn.close()


def _create_manifest(service, world_id):
    return service.create_initial_physiology_manifest(
        world_id, "residence.t0.v1", 1, "manifest.regions.v1", 1,
        "manifest.light_phase.v1", 1, ANCHOR, "post_migration_initialization", "condition initiale de modele approuvee",
    )


def _entry(character_key, **changes):
    return replace(InitialPhysiologyManifestEntry(
        character_key, "manifest.human.v1", 1, 50_000, 250_000, 75_000, "fragile",
        "initial_manifest", "region T0 de calibration",
    ), **changes)


def test_manifest_is_complete_immutable_and_never_materializes_physiology(manifest_world):
    conn, world_id, service = manifest_world
    manifest = _create_manifest(service, world_id)
    before = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("sleep_regulation_state", "physical_capacity_state", "sleep_physiology_audit", "canonical_event")
    }
    characters = [row["key"] for row in conn.execute("SELECT key FROM character WHERE world_id=? ORDER BY key", (world_id,))]
    for key in characters:
        service.append_initial_physiology_manifest_entry(world_id, "residence.t0.v1", 1, _entry(key))

    assert service.validate_initial_physiology_manifest(world_id, "residence.t0.v1", 1) == tuple(characters)
    sealed = service.seal_initial_physiology_manifest(world_id, "residence.t0.v1", 1)
    assert sealed["sealed_at"] is not None and sealed["entry_count"] == len(characters)
    assert {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in before
    } == before

    manifest_id = manifest["manifest_id"]
    entry_id = conn.execute("SELECT id FROM initial_physiology_manifest_entry WHERE manifest_id=? LIMIT 1", (manifest_id,)).fetchone()[0]
    with pytest.raises(Exception, match="immutable"):
        conn.execute("UPDATE initial_physiology_manifest SET anchor_at=? WHERE id=?", ("2026-08-12T12:00:00+00:00", manifest_id))
    with pytest.raises(Exception, match="immutable"):
        conn.execute("UPDATE initial_physiology_manifest_entry SET homeostatic_load_milli=1 WHERE id=?", (entry_id,))
    with pytest.raises(SleepPhysiologyError) as caught:
        service.append_initial_physiology_manifest_entry(world_id, "residence.t0.v1", 1, _entry("sophie"))
    assert caught.value.code == "manifest_sealed"


def test_manifest_rejects_inconsistent_band_phase_regions_and_pre_t0_residues(manifest_world):
    _conn, world_id, service = manifest_world
    _create_manifest(service, world_id)
    invalid = (
        _entry("sophie", previous_band="stable"),
        _entry("sophie", circadian_phase_milli=500_000),
        _entry("sophie", homeostatic_load_milli=30_000),
        _entry("sophie", physical_capacity_milli=95_000),
        _entry("sophie", homeostatic_load_residue=0.000001),
    )
    expected_codes = (
        "initial_band_mismatch", "t0_phase_light_mismatch", "invalid_initial_manifest",
        "invalid_initial_manifest", "invalid_initial_manifest",
    )
    for entry, expected in zip(invalid, expected_codes):
        with pytest.raises(SleepPhysiologyError) as caught:
            service.append_initial_physiology_manifest_entry(world_id, "residence.t0.v1", 1, entry)
        assert caught.value.code == expected

    service.append_initial_physiology_manifest_entry(
        world_id, "residence.t0.v1", 1,
        _entry("sophie", circadian_phase_milli=500_000, phase_override_provenance="explicit_t0_override", phase_override_justification="cas documente"),
    )


def test_manifest_requires_complete_coverage_and_the_assigned_biology_profile(manifest_world):
    conn, world_id, service = manifest_world
    _create_manifest(service, world_id)
    service.append_initial_physiology_manifest_entry(world_id, "residence.t0.v1", 1, _entry("sophie"))
    with pytest.raises(SleepPhysiologyError) as caught:
        service.seal_initial_physiology_manifest(world_id, "residence.t0.v1", 1)
    assert caught.value.code == "incomplete_initial_manifest"

    service.register_biology_profile("manifest.other.v1", 1, "human_reference", _profile_payload())
    with pytest.raises(SleepPhysiologyError) as caught:
        service.append_initial_physiology_manifest_entry(
            world_id, "residence.t0.v1", 1, _entry("erika", biology_profile_key="manifest.other.v1")
        )
    assert caught.value.code == "biology_profile_mismatch"
    assert conn.execute("SELECT COUNT(*) FROM initial_physiology_manifest_completion").fetchone()[0] == 0


def test_manifest_refuses_an_open_runtime_session_without_touching_it(manifest_world):
    _conn, world_id, service = manifest_world
    session = RuntimeSessionService(_conn).start(world_id)
    try:
        with pytest.raises(SleepPhysiologyError) as caught:
            _create_manifest(service, world_id)
        assert caught.value.code == "runtime_session_open"
    finally:
        RuntimeSessionService(_conn).stop(session.session_id)


def test_forward_migration_from_schema_53_preserves_history_and_creates_no_manifest_or_state():
    conn = connect_database(":memory:")
    try:
        conn.execute("CREATE TABLE migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL, checksum TEXT NOT NULL)")
        for migration in load_migrations():
            if migration.version > 53:
                continue
            with transaction(conn):
                for statement in split_sql_statements(migration.sql):
                    conn.execute(statement)
                conn.execute("INSERT INTO migrations (version,name,applied_at,checksum) VALUES (?,?,?,?)", (migration.version, migration.name, ANCHOR, migration.checksum))
        world_id = IntegrationWorldService(conn).create_initial_world()["id"]
        before = conn.execute("SELECT COUNT(*),MAX(seq) FROM canonical_event WHERE world_id=?", (world_id,)).fetchone()

        assert ensure_schema(conn) == 54
        assert tuple(conn.execute("SELECT COUNT(*),MAX(seq) FROM canonical_event WHERE world_id=?", (world_id,)).fetchone()) == tuple(before)
        for table in ("initial_physiology_manifest", "initial_physiology_manifest_entry", "sleep_regulation_state", "physical_capacity_state"):
            assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    finally:
        conn.close()
