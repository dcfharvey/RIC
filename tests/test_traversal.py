from datetime import datetime, timezone

import pytest

from vivarium.character import CharacterEngine, CharacterError
from vivarium.connectors import WorldConnectorService
from vivarium.db import connect_database
from vivarium.environment_archetypes import EnvironmentArchetypeService
from vivarium.environment_blueprints import EnvironmentBlueprintService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.traversal import TraversalEngine, TraversalError
from vivarium.util import to_iso


T0 = datetime(2026, 8, 6, 17, 0, tzinfo=timezone.utc)


class FakeClock:
    def now(self):
        return T0

    def now_iso(self):
        return to_iso(self.now())


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    archetypes = EnvironmentArchetypeService(conn)
    archetypes.create_place_draft("room", {"name": "Pièce", "medium": "air", "functions": ["socialize"], "max_occupancy": 4, "installation_slots": []})
    archetypes.publish("place", "room", 1)
    archetypes.create_connector_draft("door", {"name": "Porte", "traversal_modes": ["walk"], "directions": "bidirectional", "features": ["closable"]})
    archetypes.publish("connector", "door", 1)
    blueprint = EnvironmentBlueprintService(conn, clock=FakeClock())
    blueprint.create_draft("route", {
        "name": "Route", "topology": {"policy": "strong_anchor", "anchor": "a"},
        "locations": [{"key": "a", "name": "A", "archetype": {"key": "room", "version": 1}}, {"key": "b", "name": "B", "archetype": {"key": "room", "version": 1}}],
        "connectors": [{"key": "door_ab", "from": "a", "to": "b", "archetype": {"key": "door", "version": 1}}], "objects": [],
    })
    blueprint.publish("route", 1)
    world_id = blueprint.instantiate("route", 1)["id"]
    CharacterEngine(conn, clock=FakeClock()).create_character(world_id, "test_person", "Test", "a")
    yield conn, world_id, TraversalEngine(conn, clock=FakeClock())
    conn.close()


def test_traversal_moves_by_named_connector_and_records_cause(setup):
    conn, world_id, traversal = setup

    result = traversal.traverse_character(world_id, "test_person", "door_ab", "b")

    assert result["location_key"] == "b"
    payload = conn.execute(
        "SELECT payload FROM canonical_event WHERE world_id = ? AND event_type = 'character_moved' ORDER BY seq DESC LIMIT 1", (world_id,)
    ).fetchone()["payload"]
    assert '"connector":"door_ab"' in payload


def test_closed_door_refuses_preview_and_real_traversal_atomically(setup):
    conn, world_id, traversal = setup
    WorldConnectorService(conn, clock=FakeClock()).set_state(world_id, "door_ab", "closed")
    before_state, before_seq = canonical_state_digest(conn, world_id), max_seq(conn, world_id)

    assert traversal.preview(world_id, "test_person", "door_ab", "b") == {
        "allowed": False, "reason": "connector_closed", "connector": "door_ab", "to": "b"
    }
    with pytest.raises(TraversalError) as raised:
        traversal.traverse_character(world_id, "test_person", "door_ab", "b")

    assert raised.value.code == "connector_closed"
    assert canonical_state_digest(conn, world_id) == before_state
    assert max_seq(conn, world_id) == before_seq


def test_legacy_move_also_refuses_a_closed_instanced_connector(setup):
    conn, world_id, _traversal = setup
    WorldConnectorService(conn, clock=FakeClock()).set_state(world_id, "door_ab", "closed")
    before = canonical_state_digest(conn, world_id)

    with pytest.raises(CharacterError) as raised:
        CharacterEngine(conn, clock=FakeClock()).move_character(world_id, "test_person", "b")

    assert raised.value.code == "connector_closed"
    assert canonical_state_digest(conn, world_id) == before


def test_traversal_requires_the_character_to_be_at_that_connector(setup):
    _conn, world_id, traversal = setup

    with pytest.raises(TraversalError) as raised:
        traversal.traverse_character(world_id, "test_person", "door_ab", "a")

    assert raised.value.code == "connector_destination_mismatch"
