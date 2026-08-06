import pytest

from vivarium.db import connect_database
from vivarium.migrations import ensure_schema
from vivarium.mvp_catalog import MVP_COMPONENT_CATALOG, install_mvp_component_catalog
from vivarium.registry import RegistryError, RegistryService


@pytest.fixture
def conn():
    database = connect_database(":memory:")
    ensure_schema(database)
    yield database
    database.close()


def test_catalog_is_published_complete_and_idempotent(conn):
    installed = install_mvp_component_catalog(conn)

    assert [item["key"] for item in installed] == [entry[1] for entry in MVP_COMPONENT_CATALOG]
    assert all(item["status"] == "published" and item["version"] == 1 for item in installed)
    assert install_mvp_component_catalog(conn) == installed
    assert conn.execute("SELECT COUNT(*) FROM registry_definition_version").fetchone()[0] == 6


def test_catalog_rejects_a_conflicting_existing_definition_atomically(conn):
    registry = RegistryService(conn)
    registry.create_draft("component", "body.morphology", {"title": "incompatible"})
    registry.publish("component", "body.morphology", 1)

    with pytest.raises(RegistryError, match="catalogue incompatible"):
        install_mvp_component_catalog(conn)

    assert conn.execute("SELECT COUNT(*) FROM registry_definition WHERE key = 'cognition.profile'").fetchone()[0] == 0
