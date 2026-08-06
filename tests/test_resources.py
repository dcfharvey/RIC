from datetime import datetime, timedelta, timezone
import json

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


def test_band_effects_are_read_from_the_active_band_without_writing(setup):
    conn, world_id, resources, _clock = setup
    resources.register_resource(
        world_id, "character_1", "ammo", "Munitions", 100000, -1, 1, BANDS
    )
    resources.declare_band_effects(
        world_id,
        "character_1",
        "ammo",
        "high",
        [{"effect_type": "capability_availability", "effect_key": "action.fire", "availability": "available"}],
    )
    resources.declare_band_effects(
        world_id,
        "character_1",
        "ammo",
        "low",
        [
            {"effect_type": "capability_availability", "effect_key": "action.fire", "availability": "unavailable"},
            {"effect_type": "context_signal", "effect_key": "ammo_urgency", "value_milli": 80000},
        ],
    )
    before = conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)).fetchone()[0]
    target = to_iso(T0 + timedelta(seconds=90000))
    active = resources.active_effects(world_id, "character_1", "ammo", target)
    assert active == {
        "resource_key": "ammo",
        "value_milli": 10000,
        "state_key": "low",
        "effects": [
            {"effect_type": "capability_availability", "effect_key": "action.fire", "availability": "unavailable", "value_milli": None},
            {"effect_type": "context_signal", "effect_key": "ammo_urgency", "availability": None, "value_milli": 80000},
        ],
    }
    assert conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)).fetchone()[0] == before


def test_effect_declaration_is_immutable_and_rejects_partial_conflicts(setup):
    conn, world_id, resources, _clock = setup
    resources.register_resource(
        world_id, "character_1", "mana", "Mana", 100000, 0, 1, BANDS
    )
    with pytest.raises(ResourceError, match="effet dupliqué"):
        resources.declare_band_effects(
            world_id,
            "character_1",
            "mana",
            "high",
            [
                {"effect_type": "context_signal", "effect_key": "focus", "value_milli": 1},
                {"effect_type": "context_signal", "effect_key": "focus", "value_milli": 2},
            ],
    )
    assert conn.execute("SELECT COUNT(*) FROM resource_state_effect").fetchone()[0] == 0
    resources.declare_band_effects(
        world_id,
        "character_1",
        "mana",
        "high",
        [{"effect_type": "context_signal", "effect_key": "focus", "value_milli": 1000}],
    )
    with pytest.raises(Exception, match="immutable"):
        conn.execute("UPDATE resource_state_effect SET value_milli = 1")
    digest = canonical_state_digest(conn, world_id)
    assert digest["resource_rules"]["character_1"]["mana"][2]["effects"][0]["effect_key"] == "focus"


def test_resource_adjustment_derives_then_applies_exact_delta_with_one_event(setup):
    conn, world_id, resources, _clock = setup
    resources.register_resource(
        world_id, "character_1", "hydration", "Hydratation", 50000, -1, 1, BANDS
    )
    target = to_iso(T0 + timedelta(seconds=10))
    before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)
    ).fetchone()[0]

    adjusted = resources.adjust_resource(
        world_id, "character_1", "hydration", 3000, target, "water_absorbed"
    )

    assert adjusted == {
        "resource_key": "hydration",
        "value_milli": 52990,
        "rate_remainder": 0,
        "state_key": "normal",
        "anchor_at": target,
    }
    event = conn.execute(
        "SELECT event_type, payload FROM canonical_event WHERE world_id = ? ORDER BY seq DESC LIMIT 1",
        (world_id,),
    ).fetchone()
    assert event["event_type"] == "resource_adjusted"
    assert json.loads(event["payload"])["previous_value_milli"] == 49990
    assert json.loads(event["payload"])["new_value_milli"] == 52990
    assert conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)
    ).fetchone()[0] == before + 1


def test_resource_adjustment_refuses_out_of_bounds_without_partial_write(setup):
    conn, world_id, resources, _clock = setup
    resources.register_resource(
        world_id, "character_1", "hydration", "Hydratation", 99000, 0, 1, BANDS
    )
    target = to_iso(T0 + timedelta(seconds=1))
    before = resources.read_resource(world_id, "character_1", "hydration", target)
    before_events = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)
    ).fetchone()[0]

    with pytest.raises(ResourceError, match="hors limites"):
        resources.adjust_resource(
            world_id, "character_1", "hydration", 2000, target, "water_absorbed"
        )

    assert resources.read_resource(world_id, "character_1", "hydration", target) == before
    assert conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)
    ).fetchone()[0] == before_events


def test_resource_adjustment_preserves_derived_rate_remainder(setup):
    _conn, world_id, resources, _clock = setup
    resources.register_resource(
        world_id, "character_1", "hydration", "Hydratation", 50000, -1, 2, BANDS
    )
    first = to_iso(T0 + timedelta(seconds=1))
    resources.adjust_resource(
        world_id, "character_1", "hydration", 1000, first, "water_absorbed"
    )

    second = to_iso(T0 + timedelta(seconds=2))
    assert resources.read_resource(world_id, "character_1", "hydration", second) == {
        "resource_key": "hydration",
        "value_milli": 50999,
        "rate_remainder": 0,
        "state_key": "normal",
        "anchor_at": first,
    }


def test_resource_profile_installs_bands_and_effects_atomically(setup):
    conn, world_id, resources, _clock = setup
    effects = {
        "low": [
            {"effect_type": "context_signal", "effect_key": "clarity", "value_milli": -50000}
        ],
        "normal": [
            {"effect_type": "context_signal", "effect_key": "clarity", "value_milli": 0}
        ],
        "high": [
            {"effect_type": "context_signal", "effect_key": "clarity", "value_milli": 50000}
        ],
    }

    active = resources.register_resource_profile(
        world_id, "character_1", "hydration", "Hydratation", 80000, -1, 1, BANDS, effects
    )

    assert active["state_key"] == "high"
    assert active["effects"] == [
        {"effect_type": "context_signal", "effect_key": "clarity", "availability": None, "value_milli": 50000}
    ]
    assert conn.execute("SELECT COUNT(*) FROM resource_state WHERE world_id = ?", (world_id,)).fetchone()[0] == 1
    assert conn.execute(
        "SELECT COUNT(*) FROM resource_state_effect WHERE resource_state_band_id IN "
        "(SELECT id FROM resource_state_band)"
    ).fetchone()[0] == 3


def test_resource_profile_rejects_incomplete_effects_without_partial_write(setup):
    conn, world_id, resources, _clock = setup
    with pytest.raises(ResourceError, match="incomplets"):
        resources.register_resource_profile(
            world_id,
            "character_1",
            "hydration",
            "Hydratation",
            80000,
            -1,
            1,
            BANDS,
            {"high": []},
        )
    assert conn.execute("SELECT COUNT(*) FROM resource_state WHERE world_id = ?", (world_id,)).fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM resource_state_effect").fetchone()[0] == 0
