from datetime import datetime, timezone

import pytest

from vivarium.connectors import ConnectorError, WorldConnectorService
from vivarium.db import connect_database
from vivarium.environment_archetypes import EnvironmentArchetypeService
from vivarium.environment_blueprints import EnvironmentBlueprintService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.spatial import GraphEngine
from vivarium.util import to_iso


T0 = datetime(2026, 8, 6, 16, 0, tzinfo=timezone.utc)


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
    archetypes.create_place_draft("room", {
        "name": "Pièce", "medium": "air", "functions": ["socialize"],
        "max_occupancy": 4, "installation_slots": [],
    })
    archetypes.publish("place", "room", 1)
    archetypes.create_connector_draft("door", {
        "name": "Porte", "traversal_modes": ["walk"],
        "directions": "bidirectional", "features": ["closable"],
    })
    archetypes.publish("connector", "door", 1)
    definition = {
        "name": "Connecteurs", "topology": {"policy": "strong_anchor", "anchor": "a"},
        "locations": [
            {"key": "a", "name": "A", "archetype": {"key": "room", "version": 1}},
            {"key": "b", "name": "B", "archetype": {"key": "room", "version": 1}},
        ],
        "connectors": [{"key": "door_ab", "from": "a", "to": "b", "archetype": {"key": "door", "version": 1}}],
        "objects": [],
    }
    blueprints = EnvironmentBlueprintService(conn, clock=FakeClock())
    blueprints.create_draft("connector_world", definition)
    blueprints.publish("connector_world", 1)
    world_id = blueprints.instantiate("connector_world", 1)["id"]
    yield conn, world_id, WorldConnectorService(conn, clock=FakeClock())
    conn.close()


def test_blueprint_connector_has_identity_and_state(setup):
    conn, world_id, connectors = setup

    sheet = connectors.connector_sheet(world_id, "door_ab")

    assert sheet["state"] == "available"
    assert sheet["directions"] == "bidirectional"
    assert sheet["features"] == ["closable"]
    assert conn.execute("SELECT connector_id FROM location_link WHERE world_id = ?", (world_id,)).fetchone()[0] is not None


def test_closing_connector_blocks_its_permission_query_and_is_audited(setup):
    conn, world_id, connectors = setup
    before = max_seq(conn, world_id)

    result = connectors.set_state(world_id, "door_ab", "closed")

    assert result["state"] == "closed"
    assert connectors.can_traverse(world_id, "door_ab", "a", "b") is False
    assert GraphEngine(conn).can_traverse(world_id, "a", "b") is True
    assert max_seq(conn, world_id) == before + 1
    assert canonical_state_digest(conn, world_id)["world_connector"]["door_ab"]["state"] == "closed"


def test_non_closable_connector_refusal_is_atomic(setup):
    conn, world_id, connectors = setup
    # Un second monde utilise une arche non fermable, sans modifier le contrat
    # déjà publié de la porte du premier monde.
    archetypes = EnvironmentArchetypeService(conn)
    archetypes.create_connector_draft("arch", {
        "name": "Arche", "traversal_modes": ["walk"],
        "directions": "bidirectional", "features": ["open"],
    })
    archetypes.publish("connector", "arch", 1)
    definition = {
        "name": "Arche", "topology": {"policy": "none"},
        "locations": [{"key": "x", "name": "X", "archetype": {"key": "room", "version": 1}}, {"key": "y", "name": "Y", "archetype": {"key": "room", "version": 1}}],
        "connectors": [{"key": "arch_xy", "from": "x", "to": "y", "archetype": {"key": "arch", "version": 1}}], "objects": [],
    }
    blueprints = EnvironmentBlueprintService(conn, clock=FakeClock())
    blueprints.create_draft("arch_world", definition)
    blueprints.publish("arch_world", 1)
    other_world = blueprints.instantiate("arch_world", 1)["id"]
    other = WorldConnectorService(conn, clock=FakeClock())
    before = canonical_state_digest(conn, other_world)

    with pytest.raises(ConnectorError) as raised:
        other.set_state(other_world, "arch_xy", "closed")

    assert raised.value.code == "connector_not_closable"
    assert canonical_state_digest(conn, other_world) == before
