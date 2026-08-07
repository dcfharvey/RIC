from datetime import datetime, timezone

import pytest

from vivarium.character import CharacterEngine
from vivarium.cognition import CognitionDecision
from vivarium.connectors import WorldConnectorService
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.mvp_runtime import MVPRuntime, MVPRuntimeError
from vivarium.scene_turn import SceneTurnDecision
from vivarium.simulation import SimulationEngine
from vivarium.traversal import TraversalEngine
from vivarium.util import to_iso
from vivarium.world import WorldEngine


class Clock:
    def now(self):
        return datetime(2026, 8, 6, 12, tzinfo=timezone.utc)

    def now_iso(self):
        return to_iso(self.now())


class CognitionProvider:
    def decide(self, context):
        return CognitionDecision("no_action")


class ArrivalTraversalProvider:
    def decide(self, context):
        if context.character_key in {"chuu", "erika", "luna", "sophie"}:
            return CognitionDecision("traverse", "porte_entree", "salon")
        return CognitionDecision("no_action")


class SceneProvider:
    def decide(self, context):
        return SceneTurnDecision("no_action")


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = Clock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    yield conn, world_id, clock
    conn.close()


def test_runtime_progresses_deterministic_world_without_a_model(setup):
    conn, world_id, _ = setup

    report = MVPRuntime(conn, world_id).run_once()

    assert report.status == "active"
    assert report.simulation is not None
    assert report.cognition is None and report.social is None


def test_runtime_does_not_materialize_needs_on_each_wall_clock_tick(setup, monkeypatch):
    """Une activité active n'est rejouée qu'à sa vraie échéance planifiée."""
    conn, world_id, clock = setup
    target = clock.now_iso()
    monkeypatch.setattr(WorldEngine, "read_canonical_time", lambda _self, _wid: target)
    runtime = MVPRuntime(conn, world_id)

    first = runtime.run_once()
    seq_after_first = conn.execute(
        "SELECT MAX(seq) FROM canonical_event WHERE world_id = ?", (world_id,)
    ).fetchone()[0]
    second = runtime.run_once()
    seq_after_second = conn.execute(
        "SELECT MAX(seq) FROM canonical_event WHERE world_id = ?", (world_id,)
    ).fetchone()[0]

    assert first.simulation is not None
    assert second.simulation is None
    assert seq_after_second == seq_after_first


def test_runtime_respects_pause_without_starting_new_activity(setup):
    conn, world_id, _ = setup
    WorldEngine(conn).pause_world(world_id)

    report = MVPRuntime(conn, world_id).run_once()

    assert report.status == "paused"
    assert report.simulation is None


def test_runtime_can_open_and_process_a_bounded_social_scene(setup):
    conn, world_id, clock = setup
    TraversalEngine(conn, clock=clock).traverse_character(world_id, "erika", "porte_entree", "salon")
    CharacterEngine(conn, clock=clock).move_character(world_id, "sophie", "salon")

    report = MVPRuntime(
        conn, world_id, cognition_provider=CognitionProvider(), scene_provider=SceneProvider()
    ).run_once()

    assert report.social is not None
    assert report.social.opened_scene_keys
    assert report.social.turn is not None


def test_runtime_rejects_half_configured_model_layer(setup):
    conn, world_id, _ = setup
    with pytest.raises(MVPRuntimeError, match="ensemble"):
        MVPRuntime(conn, world_id, cognition_provider=CognitionProvider())


def test_runtime_finishes_bounded_arrival_before_starting_activities(setup):
    conn, world_id, _ = setup
    runtime = MVPRuntime(
        conn, world_id, cognition_provider=ArrivalTraversalProvider(), scene_provider=SceneProvider()
    )

    first = runtime.run_once()
    second = runtime.run_once()
    third = runtime.run_once()
    fourth = runtime.run_once()

    assert first.simulation is None and first.arrival and first.arrival.pending
    assert second.simulation is None and second.arrival and second.arrival.pending
    assert third.simulation is None and third.arrival and third.arrival.pending
    assert fourth.simulation is not None and fourth.arrival and not fourth.arrival.pending
    rows = conn.execute(
        "SELECT c.key, l.key FROM character c JOIN location l ON l.id = c.current_location_id "
        "WHERE c.world_id = ? ORDER BY c.key", (world_id,)
    ).fetchall()
    assert dict(rows) == {
        "chuu": "salon", "erika": "salon", "luna": "salon", "patoune": "entree_exterieure", "sophie": "salon"
    }
