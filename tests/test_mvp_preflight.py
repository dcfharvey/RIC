"""Prévol MVP : contrôles de lecture, jamais un mécanisme de réparation."""

import pytest

from vivarium.db import connect_database
from vivarium.character import CharacterEngine
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.mvp_preflight import MVPPreflightError, inspect_mvp_preflight


@pytest.fixture
def conn():
    database = connect_database(":memory:")
    ensure_schema(database)
    try:
        yield database
    finally:
        database.close()


def test_preflight_accepts_a_clean_initial_integration_world_without_writing(conn):
    world = IntegrationWorldService(conn).create_initial_world()
    before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world["id"],)
    ).fetchone()[0]

    report = inspect_mvp_preflight(conn)

    after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world["id"],)
    ).fetchone()[0]
    assert report.healthy
    assert report.world_id == world["id"]
    assert not report.failures
    assert before == after


def test_preflight_reports_missing_cast_instead_of_repairing_it(conn):
    world = IntegrationWorldService(conn).create_initial_world()
    # On ajoute une identité non attendue via le moteur. Le prévol ne répare
    # pas cette dérive : il la rend seulement visible avant activation.
    CharacterEngine(conn).create_character(
        world["id"], "resident.test", "Test", "entree_exterieure"
    )

    report = inspect_mvp_preflight(conn)

    assert not report.healthy
    assert [check.key for check in report.failures] == ["mvp_cast"]


def test_preflight_requires_an_explicit_selection_for_multiple_worlds(conn):
    first = IntegrationWorldService(conn).create_initial_world(name="Premier")
    second = IntegrationWorldService(conn).create_initial_world(name="Second")

    ambiguous = inspect_mvp_preflight(conn)
    selected = inspect_mvp_preflight(conn, world_id=second["id"])

    assert not ambiguous.healthy
    assert ambiguous.failures[0].key == "single_world_selected"
    assert selected.healthy
    assert selected.world_id != first["id"]


def test_preflight_rejects_invalid_or_unknown_world_ids(conn):
    with pytest.raises(MVPPreflightError, match="strictement positif"):
        inspect_mvp_preflight(conn, world_id=True)
    with pytest.raises(MVPPreflightError, match="introuvable"):
        inspect_mvp_preflight(conn, world_id=999)


def test_active_physiology_fails_closed_on_missing_classes_and_legacy_consumers(conn):
    world = IntegrationWorldService(conn).create_initial_world()
    conn.execute(
        "INSERT INTO world_physiology_system (public_id,world_id,status,prepared_model_key,prepared_model_version,"
        "prepared_at,prepared_by,activated_at,activated_by,created_at,updated_at) "
        "VALUES ('preflight-active',?,'active','ric.sleep.additive.v1',1,"
        "'2026-08-11T12:00:00.000+00:00','test','2026-08-11T12:00:00.000+00:00','test',"
        "'2026-08-11T12:00:00.000+00:00','2026-08-11T12:00:00.000+00:00')",
        (world["id"],)
    )
    conn.execute(
        "UPDATE world_physiology_system SET status='active', prepared_model_key='ric.sleep.additive.v1', "
        "prepared_model_version=1, prepared_at='2026-08-11T12:00:00.000+00:00', "
        "prepared_by='test', activated_at='2026-08-11T12:00:00.000+00:00', activated_by='test' "
        "WHERE world_id=?", (world["id"],)
    )
    report = inspect_mvp_preflight(conn, world_id=world["id"])
    failures = {check.key for check in report.failures}
    assert "physical_load_classes" in failures
    assert "legacy_runtime_guard" in failures
    assert "owner_backed_contracts" not in failures
