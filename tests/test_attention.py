from datetime import datetime, timezone

import pytest

from vivarium.attention import AttentionError, AttentionService
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.injury import InjuryEngine
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.resources import ResourceEngine
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
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    yield conn, world_id, clock
    conn.close()


def _types(snapshot):
    return [item.fact.event_type for item in snapshot.selected]


def test_attention_is_pure_bounded_and_does_not_expose_chuus_internal_state_to_sophie(setup):
    conn, world_id, clock = setup
    before_state = canonical_state_digest(conn, world_id)
    before_seq = max_seq(conn, world_id)

    snapshot = AttentionService(conn, clock=clock).snapshot(world_id, "sophie")

    assert snapshot.observer_key == "sophie"
    assert len(snapshot.selected) == 5
    assert all(item.observer_key == "sophie" for item in snapshot.available)
    assert "resource_context_signal" not in _types(snapshot)
    assert all(
        item.fact.payload.get("character") != "chuu"
        for item in snapshot.available
        if item.fact.event_type not in {"character_present"}
    )
    with pytest.raises(TypeError):
        snapshot.selected[0].fact.payload["character"] = "mutated"  # type: ignore[index]
    assert canonical_state_digest(conn, world_id) == before_state
    assert max_seq(conn, world_id) == before_seq


def test_attention_exposes_chuus_own_resource_effects_without_special_case(setup):
    conn, world_id, clock = setup
    snapshot = AttentionService(conn, clock=clock).snapshot(world_id, "chuu")

    signals = [item for item in snapshot.available if item.fact.event_type == "resource_context_signal"]
    assert [(item.fact.payload["resource"], item.fact.payload["signal"], item.fact.payload["value_milli"])
            for item in signals] == [("hydration", "cognition.clarity", 80000)]
    assert all(item.fact.payload["character"] == "chuu" for item in signals)
    assert signals[0] in snapshot.selected


def test_resource_capability_loss_has_deterministic_priority_and_remains_read_only(setup):
    conn, world_id, clock = setup
    resources = ResourceEngine(conn, clock=clock)
    resources.adjust_resource(world_id, "chuu", "hydration", -85000, clock.now_iso(), "test_dehydration")
    before_state = canonical_state_digest(conn, world_id)
    before_seq = max_seq(conn, world_id)

    snapshot = AttentionService(conn, clock=clock).snapshot(world_id, "chuu")

    capabilities = [item for item in snapshot.selected if item.fact.event_type == "resource_capability_state"]
    assert [(item.fact.payload["capability"], item.fact.payload["availability"], item.priority_milli)
            for item in capabilities] == [
        ("cognition.complex_reasoning", "unavailable", 95000),
        ("form.humanoid", "unavailable", 95000),
    ]
    assert canonical_state_digest(conn, world_id) == before_state
    assert max_seq(conn, world_id) == before_seq


def test_injury_and_need_signals_are_derived_from_the_canonical_instant(setup):
    conn, world_id, clock = setup
    target = to_iso(datetime(2026, 8, 7, 0, 0, 0, tzinfo=timezone.utc))
    WorldEngine(conn, clock=clock).set_simulated_time(world_id, target)
    InjuryEngine(conn, clock=clock).inflict_injury(world_id, "sophie", 90000)
    before_state = canonical_state_digest(conn, world_id)
    before_seq = max_seq(conn, world_id)

    snapshot = AttentionService(conn, clock=clock).snapshot(world_id, "sophie")

    assert snapshot.observed_at == target
    assert snapshot.selected[0].fact.event_type == "injury_active"
    assert snapshot.selected[0].fact.payload["severity_milli"] == 90000
    needs = [item.fact.payload["need"] for item in snapshot.available if item.fact.event_type == "need_below_threshold"]
    assert needs == ["satiete", "repos"]
    assert canonical_state_digest(conn, world_id) == before_state
    assert max_seq(conn, world_id) == before_seq


def test_attention_rejects_invalid_limit_without_writing(setup):
    conn, world_id, clock = setup
    before_state = canonical_state_digest(conn, world_id)
    before_seq = max_seq(conn, world_id)

    with pytest.raises(AttentionError) as raised:
        AttentionService(conn, clock=clock).snapshot(world_id, "sophie", limit=0)

    assert raised.value.code == "invalid_limit"
    assert canonical_state_digest(conn, world_id) == before_state
    assert max_seq(conn, world_id) == before_seq
