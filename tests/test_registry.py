import pytest

from vivarium.db import connect_database
from vivarium.migrations import ensure_schema
from vivarium.registry import RegistryError, RegistryService


@pytest.fixture
def service():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    yield RegistryService(conn)
    conn.close()


def test_draft_then_publish_is_immutable(service):
    draft = service.create_draft("component", "body.biological", {"title": "Corps"})
    assert draft["status"] == "draft"
    published = service.publish("component", "body.biological", 1)
    assert published["status"] == "published"
    with pytest.raises(Exception, match="immutable"):
        service._conn.execute(
            "UPDATE registry_definition_version SET contract_json = '{}' WHERE version = 1"
        )


def test_new_version_never_overwrites_published_contract(service):
    service.create_draft("unit", "unit.second", {"symbol": "s"})
    service.publish("unit", "unit.second", 1)
    v2 = service.create_draft("unit", "unit.second", {"symbol": "sec"})
    assert v2["version"] == 2
    assert service.get_version("unit", "unit.second", 1)["contract"] == {"symbol": "s"}


def test_publish_refuses_unknown_dependency_without_partial_write(service):
    service.create_draft("capability", "move.walk", {}, dependencies=["body.missing"])
    with pytest.raises(RegistryError, match="non publiée"):
        service.publish("capability", "move.walk", 1)
    assert service.get_version("capability", "move.walk", 1)["status"] == "draft"


def test_invalid_contracts_are_refused(service):
    with pytest.raises(RegistryError, match="key invalide"):
        service.create_draft("component", "Bad Key", {})
    with pytest.raises(RegistryError, match="contract"):
        service.create_draft("component", "body.test", [])
    with pytest.raises(RegistryError, match="doublon"):
        service.create_draft("component", "body.test", {}, dependencies=["unit.s", "unit.s"])


def test_schema_requires_structured_json_types(service):
    service._conn.execute(
        "INSERT INTO registry_definition (public_id, kind, key, created_at) "
        "VALUES ('raw-id', 'component', 'body.raw', 'now')"
    )
    with pytest.raises(Exception, match="CHECK constraint failed"):
        service._conn.execute(
            "INSERT INTO registry_definition_version "
            "(definition_id, version, status, contract_json, dependencies_json, "
            "incompatibilities_json, created_at) "
            "VALUES (1, 1, 'draft', '[]', '[]', '[]', 'now')"
        )
