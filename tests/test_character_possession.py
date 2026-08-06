from datetime import datetime, timezone

import pytest

from vivarium.containment import ContainmentService
from vivarium.db import connect_database
from vivarium.migrations import ensure_schema
from vivarium.objects import ObjectError, ObjectService
from vivarium.possession import PossessionService
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.util import to_iso
from vivarium.world import WorldEngine
from vivarium.character import CharacterEngine


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
    world_id = WorldEngine(conn, clock=clock).init_world(name="Possession") ["id"]
    yield (
        conn, world_id, CharacterEngine(conn, clock=clock), ObjectService(conn, clock=clock),
        PossessionService(conn, clock=clock), ContainmentService(conn, clock=clock),
    )
    conn.close()


def test_pickup_follows_character_and_putdown_is_traced(setup):
    conn, world_id, characters, objects, possession, _containment = setup
    objects.create_object(world_id, "telephone", "Telephone", "phone", "chambre_1", portable=True)

    picked = possession.pick_up(world_id, "character_1", "telephone")

    assert picked["carrier"] == "character_1"
    assert possession.carried_objects(world_id, "character_1") == [picked]
    characters.move_character(world_id, "character_1", "couloir")
    assert objects.object_sheet(world_id, "telephone")["location"] == "couloir"
    assert objects.object_sheet(world_id, "telephone")["carrier"] == "character_1"

    put_down = possession.put_down(world_id, "character_1", "telephone")

    assert put_down["carrier"] is None
    events = [row["event_type"] for row in conn.execute(
        "SELECT event_type FROM canonical_event WHERE world_id = ? ORDER BY seq", (world_id,)
    )]
    assert events[-3:] == ["object_picked_up", "character_moved", "object_put_down"]


def test_carried_container_relocates_contents_and_exposes_indirect_carrier(setup):
    _conn, world_id, characters, objects, possession, containment = setup
    objects.create_object(
        world_id, "sac", "Sac", "container", "chambre_1", portable=True, container_capacity=2
    )
    objects.create_object(world_id, "cle", "Cle", "key", "chambre_1", portable=True)
    containment.put_inside(world_id, "cle", "sac")
    possession.pick_up(world_id, "character_1", "sac")

    characters.move_character(world_id, "character_1", "couloir")

    assert objects.object_sheet(world_id, "sac")["location"] == "couloir"
    assert objects.object_sheet(world_id, "cle")["location"] == "couloir"
    assert objects.object_sheet(world_id, "cle")["carrier"] == "character_1"


@pytest.mark.parametrize(
    ("operation", "expected_code"),
    [
        (lambda possession, objects, containment, world_id: possession.pick_up(world_id, "character_1", "fixe"), "object_fixed"),
        (lambda possession, objects, containment, world_id: possession.pick_up(world_id, "character_2", "loin"), "object_not_accessible"),
        (lambda possession, objects, containment, world_id: objects.move_object(world_id, "portable", "couloir"), "object_carried"),
        (lambda possession, objects, containment, world_id: containment.put_inside(world_id, "portable", "sac"), "object_carried"),
    ],
)
def test_refusals_leave_possession_state_and_journal_unchanged(setup, operation, expected_code):
    conn, world_id, _characters, objects, possession, containment = setup
    objects.create_object(world_id, "fixe", "Fixe", "furniture", "chambre_1")
    objects.create_object(world_id, "portable", "Portable", "token", "chambre_1", portable=True)
    objects.create_object(world_id, "loin", "Loin", "token", "chambre_1", portable=True)
    objects.create_object(
        world_id, "sac", "Sac", "container", "chambre_1", portable=True, container_capacity=1
    )
    possession.pick_up(world_id, "character_1", "portable")
    before_state = canonical_state_digest(conn, world_id)
    before_seq = max_seq(conn, world_id)

    with pytest.raises(ObjectError) as raised:
        operation(possession, objects, containment, world_id)

    assert raised.value.code == expected_code
    assert canonical_state_digest(conn, world_id) == before_state
    assert max_seq(conn, world_id) == before_seq


def test_database_rejects_cross_world_or_nonportable_possession(setup):
    conn, world_id, _characters, objects, _possession, _containment = setup
    objects.create_object(world_id, "fixe", "Fixe", "furniture", "chambre_1")
    objects.create_object(world_id, "portable", "Portable", "token", "chambre_1", portable=True)
    character_id = conn.execute(
        "SELECT id FROM character WHERE world_id = ? AND key = 'character_1'", (world_id,)
    ).fetchone()["id"]
    object_id = conn.execute(
        "SELECT id FROM world_object WHERE world_id = ? AND key = 'fixe'", (world_id,)
    ).fetchone()["id"]

    with pytest.raises(Exception, match="carried object must be portable and top level"):
        conn.execute(
            "INSERT INTO character_carried_object (world_id, character_id, object_id, acquired_at) "
            "VALUES (?, ?, ?, ?)",
            (world_id, character_id, object_id, T0.isoformat()),
        )

    portable_id = conn.execute(
        "SELECT id FROM world_object WHERE world_id = ? AND key = 'portable'", (world_id,)
    ).fetchone()["id"]
    other_world_id = WorldEngine(conn, clock=FakeClock()).init_world(name="Autre", seed=False)["id"]
    with pytest.raises(Exception, match="carried object must be in same world"):
        conn.execute(
            "INSERT INTO character_carried_object (world_id, character_id, object_id, acquired_at) "
            "VALUES (?, ?, ?, ?)",
            (other_world_id, character_id, portable_id, T0.isoformat()),
        )
