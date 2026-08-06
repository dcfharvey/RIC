from datetime import datetime, timezone

import pytest

from vivarium.db import connect_database
from vivarium.environment_archetypes import EnvironmentArchetypeService
from vivarium.environment_blueprints import BlueprintError, EnvironmentBlueprintService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.spatial import GraphEngine
from vivarium.util import to_iso
from vivarium.world import WorldEngine


T0 = datetime(2026, 8, 6, 15, 0, tzinfo=timezone.utc)


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
        "max_occupancy": 4, "installation_slots": ["furniture"],
    })
    archetypes.publish("place", "room", 1)
    archetypes.create_connector_draft("door", {
        "name": "Porte", "traversal_modes": ["walk"],
        "directions": "bidirectional", "features": ["closable"],
    })
    archetypes.publish("connector", "door", 1)
    yield conn, EnvironmentBlueprintService(conn, clock=FakeClock())
    conn.close()


BLUEPRINT = {
    "name": "Petite résidence", "topology": {"policy": "strong_anchor", "anchor": "salon"},
    "locations": [
        {"key": "salon", "name": "Salon", "archetype": {"key": "room", "version": 1}},
        {"key": "cuisine", "name": "Cuisine", "archetype": {"key": "room", "version": 1}},
    ],
    "connectors": [
        {"key": "porte_salon_cuisine", "from": "salon", "to": "cuisine", "archetype": {"key": "door", "version": 1}},
    ],
    "objects": [
        {"key": "table", "name": "Table", "kind": "furniture", "location": "cuisine", "portable": False, "container_capacity": None, "state": "present"},
    ],
}


def test_published_blueprint_instantiates_atomic_world_with_provenance(setup):
    conn, blueprints = setup
    blueprints.create_draft("small_home", BLUEPRINT)
    blueprints.publish("small_home", 1)

    world = blueprints.instantiate("small_home", 1)

    assert world["name"] == "Petite résidence"
    world_id = world["id"]
    assert GraphEngine(conn).find_path(world_id, "salon", "cuisine") == ["salon", "cuisine"]
    assert conn.execute("SELECT policy_key FROM world_topology_policy WHERE world_id = ?", (world_id,)).fetchone()[0] == "strong_anchor"
    assert conn.execute("SELECT COUNT(*) FROM world_location_origin WHERE world_id = ?", (world_id,)).fetchone()[0] == 2
    origin = blueprints.origin(world_id)
    assert origin["blueprint_key"] == "small_home"
    assert origin["resolved_definition"]["connectors"][0]["archetype_contract"]["name"] == "Porte"
    assert "archetype_id" not in origin["resolved_definition"]["locations"][0]
    assert canonical_state_digest(conn, world_id)["world_environment_origin"]["blueprint_key"] == "small_home"
    assert max_seq(conn, world_id) == 2


def test_unpublished_blueprint_cannot_create_a_partial_world(setup):
    conn, blueprints = setup
    blueprints.create_draft("draft_only", BLUEPRINT)
    before = conn.execute("SELECT COUNT(*) FROM worlds").fetchone()[0]

    with pytest.raises(BlueprintError, match="publie"):
        blueprints.instantiate("draft_only", 1)

    assert conn.execute("SELECT COUNT(*) FROM worlds").fetchone()[0] == before


def test_publish_refuses_missing_published_archetype_without_mutating_blueprint(setup):
    conn, blueprints = setup
    invalid = {
        **BLUEPRINT,
        "locations": [{"key": "salon", "name": "Salon", "archetype": {"key": "missing", "version": 1}}],
        "connectors": [], "topology": {"policy": "none"}, "objects": [],
    }
    blueprints.create_draft("invalid", invalid)
    before = conn.execute("SELECT status FROM environment_blueprint_version").fetchone()[0]

    with pytest.raises(BlueprintError, match="archetype publie introuvable"):
        blueprints.publish("invalid", 1)

    assert conn.execute("SELECT status FROM environment_blueprint_version").fetchone()[0] == before == "draft"


def test_strong_anchor_rejects_disconnected_blueprint(setup):
    _conn, blueprints = setup
    disconnected = {
        **BLUEPRINT,
        "locations": [
            {"key": "salon", "name": "Salon", "archetype": {"key": "room", "version": 1}},
            {"key": "annexe", "name": "Annexe", "archetype": {"key": "room", "version": 1}},
        ],
        "connectors": [], "objects": [],
    }
    blueprints.create_draft("disconnected", disconnected)

    with pytest.raises(BlueprintError, match="strong_anchor non connexe"):
        blueprints.publish("disconnected", 1)


def test_destroying_blueprint_world_is_refused_by_append_only_history(setup):
    conn, blueprints = setup
    blueprints.create_draft("destroyable", BLUEPRINT)
    blueprints.publish("destroyable", 1)
    world = blueprints.instantiate("destroyable", 1)

    before = canonical_state_digest(conn, world["id"])

    with pytest.raises(Exception, match="FOREIGN KEY constraint failed"):
        WorldEngine(conn, clock=FakeClock()).destroy_world(world["id"])

    assert canonical_state_digest(conn, world["id"]) == before


def test_blueprint_can_initialize_a_closable_connector_closed(setup):
    conn, blueprints = setup
    closed = {
        **BLUEPRINT,
        "connectors": [{
            **BLUEPRINT["connectors"][0], "initial_state": "closed",
        }],
    }
    blueprints.create_draft("closed_door", closed)
    blueprints.publish("closed_door", 1)

    world = blueprints.instantiate("closed_door", 1)

    assert conn.execute(
        "SELECT state FROM world_connector WHERE world_id = ? AND key = 'porte_salon_cuisine'",
        (world["id"],),
    ).fetchone()[0] == "closed"
    assert GraphEngine(conn).find_path(world["id"], "salon", "cuisine") == ["salon", "cuisine"]


def test_blueprint_refuses_closed_initial_state_for_non_closable_connector(setup):
    conn, blueprints = setup
    archetypes = EnvironmentArchetypeService(conn)
    archetypes.create_connector_draft("arch", {
        "name": "Arche", "traversal_modes": ["walk"],
        "directions": "bidirectional", "features": ["open"],
    })
    archetypes.publish("connector", "arch", 1)
    invalid = {
        **BLUEPRINT,
        "connectors": [{
            **BLUEPRINT["connectors"][0],
            "archetype": {"key": "arch", "version": 1},
            "initial_state": "closed",
        }],
    }
    blueprints.create_draft("closed_arch", invalid)

    with pytest.raises(BlueprintError, match="ferme non fermable"):
        blueprints.publish("closed_arch", 1)

    assert conn.execute(
        "SELECT status FROM environment_blueprint_version WHERE blueprint_id = "
        "(SELECT id FROM environment_blueprint WHERE key = 'closed_arch')"
    ).fetchone()[0] == "draft"


def test_resolve_treats_legacy_connector_without_initial_state_as_available(setup):
    conn, blueprints = setup
    blueprints.create_draft("legacy", BLUEPRINT)
    row = conn.execute(
        "SELECT id, definition_json FROM environment_blueprint_version WHERE blueprint_id = "
        "(SELECT id FROM environment_blueprint WHERE key = 'legacy')"
    ).fetchone()
    legacy_json = row["definition_json"].replace(',"initial_state":"available"', '')
    conn.execute(
        "UPDATE environment_blueprint_version SET definition_json = ? WHERE id = ?",
        (legacy_json, row["id"]),
    )
    blueprints.publish("legacy", 1)

    world = blueprints.instantiate("legacy", 1)

    assert conn.execute(
        "SELECT state FROM world_connector WHERE world_id = ?", (world["id"],)
    ).fetchone()[0] == "available"
