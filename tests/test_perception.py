from datetime import datetime, timezone

import pytest

from vivarium.connectors import CLOSED, WorldConnectorService
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.perception import PerceptionError, PerceptionService
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.resources import ResourceEngine
from vivarium.traversal import TraversalEngine
from vivarium.util import to_iso


T0 = datetime(2026, 8, 6, 12, 0, 0, tzinfo=timezone.utc)


class FakeClock:
    def now(self):
        return T0

    def now_iso(self):
        return to_iso(self.now())


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    yield conn, world_id, clock
    conn.close()


def _facts(snapshot, event_type):
    return [candidate.fact.payload for candidate in snapshot.candidates if candidate.fact.event_type == event_type]


def test_snapshot_exposes_only_local_facts_and_is_read_only(setup):
    conn, world_id, clock = setup
    before_state = canonical_state_digest(conn, world_id)
    before_seq = max_seq(conn, world_id)

    snapshot = PerceptionService(conn, clock=clock).snapshot(world_id, "sophie")

    assert snapshot.observer_key == "sophie"
    assert _facts(snapshot, "character_location") == [{"character": "sophie", "location": "entree_exterieure"}]
    assert _facts(snapshot, "character_present") == [
        {"character": "chuu", "location": "entree_exterieure"},
        {"character": "erika", "location": "entree_exterieure"},
        {"character": "luna", "location": "entree_exterieure"},
        {"character": "patoune", "location": "entree_exterieure"},
    ]
    local_objects = _facts(snapshot, "object_present")
    assert {item["object"] for item in local_objects} == {"boite_aux_lettres"}
    assert "telephone_sophie" not in {item["object"] for item in local_objects}
    assert _facts(snapshot, "connector_adjacent") == [
        {"connector": "passage_stationnement", "destination": "stationnement", "state": "available", "directions": "bidirectional"},
        {"connector": "porte_entree", "destination": "salon", "state": "available", "directions": "bidirectional"},
    ]
    with pytest.raises(TypeError):
        snapshot.candidates[0].fact.payload["location"] = "mutated"  # type: ignore[index]
    assert canonical_state_digest(conn, world_id) == before_state
    assert max_seq(conn, world_id) == before_seq


def test_snapshot_tracks_current_local_connector_state_without_leaking_other_rooms(setup):
    conn, world_id, clock = setup
    WorldConnectorService(conn, clock=clock).set_state(world_id, "porte_entree", CLOSED)

    snapshot = PerceptionService(conn, clock=clock).snapshot(world_id, "sophie")

    connector_facts = {item["connector"]: item for item in _facts(snapshot, "connector_adjacent")}
    assert connector_facts["porte_entree"]["state"] == CLOSED
    all_payloads = [candidate.fact.payload for candidate in snapshot.candidates]
    assert all("cuisine" not in payload.values() for payload in all_payloads)


def test_snapshot_stops_exposing_a_character_once_they_leave_the_location(setup):
    conn, world_id, clock = setup
    TraversalEngine(conn, clock=clock).traverse_character(world_id, "erika", "porte_entree", "salon")

    snapshot = PerceptionService(conn, clock=clock).snapshot(world_id, "sophie")

    assert {item["character"] for item in _facts(snapshot, "character_present")} == {
        "chuu", "luna", "patoune"
    }


def test_snapshot_rejects_unknown_observer_without_writing(setup):
    conn, world_id, clock = setup
    before_state = canonical_state_digest(conn, world_id)
    before_seq = max_seq(conn, world_id)

    with pytest.raises(PerceptionError) as raised:
        PerceptionService(conn, clock=clock).snapshot(world_id, "ghost")

    assert raised.value.code == "observer_not_found"
    assert canonical_state_digest(conn, world_id) == before_state
    assert max_seq(conn, world_id) == before_seq


def test_direct_event_feed_is_cursor_based_curated_and_read_only(setup):
    conn, world_id, clock = setup
    cursor = max_seq(conn, world_id)
    TraversalEngine(conn, clock=clock).traverse_character(world_id, "sophie", "porte_entree", "salon")
    TraversalEngine(conn, clock=clock).traverse_character(world_id, "erika", "porte_entree", "salon")
    before_state = canonical_state_digest(conn, world_id)
    before_seq = max_seq(conn, world_id)

    feed = PerceptionService(conn, clock=clock).events_since(world_id, "sophie", cursor)

    assert feed.after_seq == cursor
    assert feed.latest_seq == before_seq
    assert [(candidate.access_kind, candidate.fact.event_type, candidate.fact.event_seq, dict(candidate.fact.payload))
            for candidate in feed.candidates] == [
        ("self_event", "character_moved", cursor + 1,
         {"character": "sophie", "from": "entree_exterieure", "to": "salon", "connector": "porte_entree"}),
    ]
    assert canonical_state_digest(conn, world_id) == before_state
    assert max_seq(conn, world_id) == before_seq


def test_event_feed_refuses_impossible_cursor_without_writing(setup):
    conn, world_id, clock = setup
    before_state = canonical_state_digest(conn, world_id)
    before_seq = max_seq(conn, world_id)

    with pytest.raises(PerceptionError) as raised:
        PerceptionService(conn, clock=clock).events_since(world_id, "sophie", before_seq + 1)

    assert raised.value.code == "invalid_cursor"
    assert canonical_state_digest(conn, world_id) == before_state
    assert max_seq(conn, world_id) == before_seq


def test_direct_event_feed_curates_own_resource_adjustment(setup):
    conn, world_id, clock = setup
    cursor = max_seq(conn, world_id)
    ResourceEngine(conn, clock=clock).adjust_resource(
        world_id, "chuu", "hydration", -100, clock.now_iso(), "test_adjustment"
    )

    feed = PerceptionService(conn, clock=clock).events_since(world_id, "chuu", cursor)

    assert [dict(candidate.fact.payload) for candidate in feed.candidates] == [{
        "character": "chuu", "resource": "hydration", "delta_milli": -100,
        "new_value_milli": 94900, "new_state": "brilliant",
    }]
    assert "reason" not in feed.candidates[0].fact.payload
