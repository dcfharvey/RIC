from datetime import datetime, timezone

import pytest

from vivarium.containment import ContainmentService
from vivarium.db import connect_database
from vivarium.migrations import ensure_schema
from vivarium.objects import ObjectError, ObjectService
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.util import to_iso
from vivarium.world import WorldEngine


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
    world_id = WorldEngine(conn, clock=clock).init_world(name="Objets")["id"]
    yield conn, world_id, ObjectService(conn, clock=clock), ContainmentService(conn, clock=clock)
    conn.close()


def test_object_service_creates_portable_container_with_event(setup):
    conn, world_id, objects, _containment = setup
    before = max_seq(conn, world_id)

    sheet = objects.create_object(
        world_id, "sac", "Sac", "container", "salon", portable=True, container_capacity=3
    )

    assert sheet == {
        "key": "sac", "name": "Sac", "kind": "container", "state": "present",
        "portable": True, "container_capacity": 3, "contained_count": 0,
        "location": "salon", "parent": None,
    }
    assert max_seq(conn, world_id) == before + 1
    event = conn.execute(
        "SELECT event_type, source_kind FROM canonical_event WHERE world_id = ? ORDER BY seq DESC LIMIT 1",
        (world_id,),
    ).fetchone()
    assert dict(event) == {"event_type": "world_object_created", "source_kind": "owner"}


def test_fixed_installation_cannot_move_and_refusal_is_atomic(setup):
    conn, world_id, objects, _containment = setup
    objects.create_object(world_id, "armoire", "Armoire", "furniture", "salon")
    before_state = canonical_state_digest(conn, world_id)
    before_seq = max_seq(conn, world_id)

    with pytest.raises(ObjectError) as raised:
        objects.move_object(world_id, "armoire", "cuisine")

    assert raised.value.code == "object_fixed"
    assert canonical_state_digest(conn, world_id) == before_state
    assert max_seq(conn, world_id) == before_seq


def test_containment_sets_effective_location_and_lists_direct_contents(setup):
    _conn, world_id, objects, containment = setup
    objects.create_object(
        world_id, "boite", "Boîte", "container", "cuisine", portable=True, container_capacity=1
    )
    objects.create_object(world_id, "bille", "Bille", "toy", "salon", portable=True)

    result = containment.put_inside(world_id, "bille", "boite")

    assert result["parent"] == "boite"
    assert result["location"] == "cuisine"
    assert containment.contents(world_id, "boite") == [result]


def test_containment_capacity_refuses_without_partial_write(setup):
    conn, world_id, objects, containment = setup
    objects.create_object(
        world_id, "boite", "Boîte", "container", "cuisine", portable=True, container_capacity=1
    )
    objects.create_object(world_id, "bille_1", "Bille 1", "toy", "salon", portable=True)
    objects.create_object(world_id, "bille_2", "Bille 2", "toy", "salon", portable=True)
    containment.put_inside(world_id, "bille_1", "boite")
    before_state = canonical_state_digest(conn, world_id)
    before_seq = max_seq(conn, world_id)

    with pytest.raises(ObjectError) as raised:
        containment.put_inside(world_id, "bille_2", "boite")

    assert raised.value.code == "container_full"
    assert canonical_state_digest(conn, world_id) == before_state
    assert max_seq(conn, world_id) == before_seq


def test_cycle_is_refused_without_partial_write(setup):
    conn, world_id, objects, containment = setup
    objects.create_object(
        world_id, "outer", "Outer", "container", "salon", portable=True, container_capacity=2
    )
    objects.create_object(
        world_id, "inner", "Inner", "container", "salon", portable=True, container_capacity=2
    )
    containment.put_inside(world_id, "inner", "outer")
    before_state = canonical_state_digest(conn, world_id)
    before_seq = max_seq(conn, world_id)

    with pytest.raises(ObjectError) as raised:
        containment.put_inside(world_id, "outer", "inner")

    assert raised.value.code == "containment_cycle"
    assert canonical_state_digest(conn, world_id) == before_state
    assert max_seq(conn, world_id) == before_seq


def test_moving_container_relocates_entire_subtree_once(setup):
    conn, world_id, objects, containment = setup
    objects.create_object(
        world_id, "sac", "Sac", "container", "salon", portable=True, container_capacity=2
    )
    objects.create_object(
        world_id, "pochette", "Pochette", "container", "salon", portable=True, container_capacity=2
    )
    objects.create_object(world_id, "piece", "Pièce", "token", "salon", portable=True)
    containment.put_inside(world_id, "pochette", "sac")
    containment.put_inside(world_id, "piece", "pochette")
    before_seq = max_seq(conn, world_id)

    result = objects.move_object(world_id, "sac", "cuisine")

    assert result["location"] == "cuisine"
    assert objects.object_sheet(world_id, "pochette")["location"] == "cuisine"
    assert objects.object_sheet(world_id, "piece")["location"] == "cuisine"
    assert max_seq(conn, world_id) == before_seq + 1
    payload = conn.execute(
        "SELECT payload FROM canonical_event WHERE world_id = ? ORDER BY seq DESC LIMIT 1", (world_id,)
    ).fetchone()["payload"]
    assert '"moved_subtree_count":3' in payload


def test_remove_from_container_relocates_nested_contents(setup):
    _conn, world_id, objects, containment = setup
    objects.create_object(
        world_id, "sac", "Sac", "container", "salon", portable=True, container_capacity=2
    )
    objects.create_object(
        world_id, "pochette", "Pochette", "container", "salon", portable=True, container_capacity=2
    )
    objects.create_object(world_id, "piece", "Pièce", "token", "salon", portable=True)
    containment.put_inside(world_id, "pochette", "sac")
    containment.put_inside(world_id, "piece", "pochette")

    result = containment.remove_to_location(world_id, "pochette", "cour")

    assert result["parent"] is None
    assert result["location"] == "cour"
    assert objects.object_sheet(world_id, "piece")["location"] == "cour"
    assert objects.object_sheet(world_id, "piece")["parent"] == "pochette"


def test_recursive_contents_exposes_deterministic_depth(setup):
    _conn, world_id, objects, containment = setup
    objects.create_object(
        world_id, "sac", "Sac", "container", "salon", portable=True, container_capacity=2
    )
    objects.create_object(
        world_id, "pochette", "Pochette", "container", "salon", portable=True, container_capacity=2
    )
    objects.create_object(world_id, "piece", "Pièce", "token", "salon", portable=True)
    containment.put_inside(world_id, "pochette", "sac")
    containment.put_inside(world_id, "piece", "pochette")

    assert [(item["key"], item["depth"]) for item in containment.contents(
        world_id, "sac", recursive=True
    )] == [("pochette", 1), ("piece", 2)]


def test_database_rejects_forced_containment_cycle(setup):
    conn, world_id, objects, containment = setup
    objects.create_object(
        world_id, "outer", "Outer", "container", "salon", portable=True, container_capacity=2
    )
    objects.create_object(
        world_id, "inner", "Inner", "container", "salon", portable=True, container_capacity=2
    )
    containment.put_inside(world_id, "inner", "outer")
    outer_id = conn.execute(
        "SELECT id FROM world_object WHERE world_id = ? AND key = 'outer'", (world_id,)
    ).fetchone()["id"]
    inner_id = conn.execute(
        "SELECT id FROM world_object WHERE world_id = ? AND key = 'inner'", (world_id,)
    ).fetchone()["id"]
    before = canonical_state_digest(conn, world_id)

    with pytest.raises(Exception, match="object containment cycle"):
        conn.execute("UPDATE world_object SET parent_object_id = ? WHERE id = ?", (inner_id, outer_id))

    assert canonical_state_digest(conn, world_id) == before


def test_database_rejects_cross_world_object_location(setup):
    conn, world_id, objects, _containment = setup
    other_world_id = WorldEngine(conn, clock=FakeClock()).init_world(name="Autre", seed=False)["id"]
    salon_id = conn.execute(
        "SELECT id FROM location WHERE world_id = ? AND key = 'salon'", (world_id,)
    ).fetchone()["id"]
    before = canonical_state_digest(conn, other_world_id)

    with pytest.raises(Exception, match="object location must be in same world"):
        conn.execute(
            "INSERT INTO world_object (public_id, world_id, location_id, key, name, kind, state, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("a" * 36, other_world_id, salon_id, "illegal", "Illegal", "toy", "present", T0.isoformat()),
        )

    assert canonical_state_digest(conn, other_world_id) == before
