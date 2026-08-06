from datetime import datetime, timedelta, timezone

import pytest

from vivarium.db import connect_database
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest
from vivarium.resources import ResourceEngine, ResourceError
from vivarium.util import to_iso
from vivarium.world import WorldEngine


T0 = datetime(2026, 8, 1, 8, 0, 0, tzinfo=timezone.utc)


class FakeClock:
    def __init__(self, now=T0):
        self.now_value = now

    def now(self):
        return self.now_value

    def now_iso(self):
        return to_iso(self.now())


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    world = WorldEngine(conn, clock=clock).init_world(name="Resources")
    yield conn, world["id"], ResourceEngine(conn, clock=clock), clock
    conn.close()


BANDS = [
    {"state_key": "low", "min_milli": 0, "max_milli": 19999},
    {"state_key": "normal", "min_milli": 20000, "max_milli": 79999},
    {"state_key": "high", "min_milli": 80000, "max_milli": 100000},
]


def test_resource_derives_and_materializes_state_atomically(setup):
    conn, world_id, resources, _clock = setup
    resources.register_resource(
        world_id, "character_1", "hydration", "Hydratation", 80000, -1, 1, BANDS
    )
    target = to_iso(T0 + timedelta(seconds=60001))

    pure = resources.read_resource(world_id, "character_1", "hydration", target)
    assert pure["value_milli"] == 19999
    assert pure["state_key"] == "low"
    before = conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)).fetchone()[0]
    materialized = resources.materialize_resource(
        world_id, "character_1", "hydration", target, "test"
    )
    assert materialized["state_key"] == "low"
    assert conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)).fetchone()[0] == before + 1


def test_resource_refuses_non_exhaustive_bands_without_partial_write(setup):
    conn, world_id, resources, _clock = setup
    with pytest.raises(ResourceError, match="non exhaustives"):
        resources.register_resource(
            world_id,
            "character_1",
            "mana",
            "Mana",
            10,
            0,
            1,
            [{"state_key": "only", "min_milli": 0, "max_milli": 99999}],
        )
    assert conn.execute("SELECT COUNT(*) FROM resource_state").fetchone()[0] == 0


def test_resource_is_included_in_reproducibility_digest(setup):
    conn, world_id, resources, _clock = setup
    before = canonical_state_digest(conn, world_id)
    resources.register_resource(
        world_id, "character_1", "ammo", "Munitions", 100000, -1, 1, BANDS
    )
    after = canonical_state_digest(conn, world_id)
    assert before != after
    assert after["resource_state"]["character_1"]["ammo"]["value_milli"] == 100000
