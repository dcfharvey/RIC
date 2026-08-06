import pytest

from vivarium.db import connect_database
from vivarium.environment_archetypes import (
    CONNECTOR,
    PLACE,
    EnvironmentArchetypeError,
    EnvironmentArchetypeService,
)
from vivarium.migrations import ensure_schema


PLACE_CONTRACT = {
    "name": "Onsen", "medium": "water", "functions": ["bathe", "rest"],
    "max_occupancy": 4, "installation_slots": ["water_source", "seating"],
}
CONNECTOR_CONTRACT = {
    "name": "Échelle", "traversal_modes": ["climb"],
    "directions": "bidirectional", "features": ["vertical"],
}


@pytest.fixture
def service():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    yield conn, EnvironmentArchetypeService(conn)
    conn.close()


def test_place_draft_then_publish_is_versioned_and_immutable(service):
    conn, archetypes = service

    draft = archetypes.create_place_draft("onsen", PLACE_CONTRACT)
    published = archetypes.publish(PLACE, "onsen", 1)

    assert draft["status"] == "draft"
    assert published["status"] == "published"
    assert published["contract"] == PLACE_CONTRACT
    with pytest.raises(EnvironmentArchetypeError, match="seul un brouillon"):
        archetypes.publish(PLACE, "onsen", 1)
    with pytest.raises(Exception, match="published environment archetype is immutable"):
        conn.execute("UPDATE environment_archetype_version SET contract_json = '{}' WHERE id = 1")


def test_new_draft_creates_new_version_without_overwriting_published(service):
    _conn, archetypes = service
    archetypes.create_place_draft("room", PLACE_CONTRACT)
    archetypes.publish(PLACE, "room", 1)
    changed = {**PLACE_CONTRACT, "max_occupancy": None}

    draft_v2 = archetypes.create_place_draft("room", changed)

    assert draft_v2["version"] == 2
    assert archetypes.get_version(PLACE, "room", 1)["contract"] == PLACE_CONTRACT


def test_invalid_contract_is_refused_before_any_write(service):
    conn, archetypes = service
    invalid = {**PLACE_CONTRACT, "functions": ["bathe", "bathe"]}

    with pytest.raises(EnvironmentArchetypeError, match="doublon"):
        archetypes.create_place_draft("bad_onsen", invalid)

    assert conn.execute("SELECT COUNT(*) FROM environment_archetype").fetchone()[0] == 0


def test_connector_contract_is_distinct_and_publication_is_listed_deterministically(service):
    _conn, archetypes = service
    archetypes.create_connector_draft("ladder", CONNECTOR_CONTRACT)
    archetypes.create_connector_draft(
        "arch", {"name": "Arche", "traversal_modes": ["walk"],
                 "directions": "bidirectional", "features": ["open"]}
    )
    archetypes.publish(CONNECTOR, "ladder", 1)
    archetypes.publish(CONNECTOR, "arch", 1)

    assert [(item["key"], item["version"]) for item in archetypes.list_published(CONNECTOR)] == [
        ("arch", 1), ("ladder", 1)
    ]


def test_place_and_connector_may_share_a_key_without_being_conflated(service):
    _conn, archetypes = service
    archetypes.create_place_draft("passage", PLACE_CONTRACT)
    archetypes.create_connector_draft("passage", CONNECTOR_CONTRACT)

    assert archetypes.get_version(PLACE, "passage", 1)["kind"] == PLACE
    assert archetypes.get_version(CONNECTOR, "passage", 1)["kind"] == CONNECTOR


def test_connector_requires_a_real_traversal_mode(service):
    _conn, archetypes = service
    invalid = {**CONNECTOR_CONTRACT, "traversal_modes": []}

    with pytest.raises(EnvironmentArchetypeError, match="modes de traversee"):
        archetypes.create_draft(CONNECTOR, "sealed_door", invalid)
