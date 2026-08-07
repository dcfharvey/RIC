from datetime import datetime, timezone

import pytest

from vivarium.character import CharacterEngine
from vivarium.activities import ActivityEngine
from vivarium.arrival_cycle import InitialArrivalCycle
from vivarium.cognition import CognitionDecision
from vivarium.cognition_policy import CognitionCallLimits
from vivarium.connectors import WorldConnectorService
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.mvp_runtime import MVPRuntime, MVPRuntimeError
from vivarium.scenes import SocialSceneService
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


class ActivityProvider:
    def decide(self, context):
        if context.character_key == "chuu":
            return CognitionDecision("start_activity", None, "entree_exterieure", "photography")
        return CognitionDecision("no_action")


class CountingProvider:
    def __init__(self):
        self.calls = 0

    def decide(self, context):
        self.calls += 1
        return CognitionDecision("no_action")


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


def test_runtime_preserves_idle_social_opportunity_before_autonomy_consumes_it(setup):
    """Régression vivante : le social observe l'idle avant son remplacement."""
    conn, world_id, clock = setup
    limits = CognitionCallLimits(0, 3600, 100)
    arrival = InitialArrivalCycle(conn, CognitionProvider(), clock=clock)
    for _ in range(4):
        arrival.tick(world_id, limits)

    scenes = SocialSceneService(conn, clock=clock)
    scenes.open(world_id, "prior_scene", ("chuu", "erika"))
    scenes.close(world_id, "prior_scene", reason="test_closed")
    activities = ActivityEngine(conn, clock=clock)
    activities.start_activity(
        world_id, "chuu", "idle", "entree_exterieure", duration_seconds=600
    )
    activities.start_activity(
        world_id, "erika", "idle", "entree_exterieure", duration_seconds=600
    )

    report = MVPRuntime(
        conn, world_id, cognition_provider=ActivityProvider(),
        scene_provider=SceneProvider(), limits=limits,
    ).run_once()

    assert report.social is not None and report.social.opened_scene_keys
    assert report.social.turn is not None
    assert ActivityEngine(conn).activity_sheet(world_id, "chuu")["type"] == "photography"


def test_runtime_yields_to_determinism_when_social_latency_crosses_a_boundary(setup, monkeypatch):
    """Aucune cognition n'est lancee apres qu'une scene a franchi une echeance."""
    conn, world_id, clock = setup
    limits = CognitionCallLimits(0, 3600, 100)
    arrival = InitialArrivalCycle(conn, CognitionProvider(), clock=clock)
    for _ in range(4):
        arrival.tick(world_id, limits)
    activities = ActivityEngine(conn, clock=clock)
    activities.start_activity(
        world_id, "chuu", "idle", "entree_exterieure", duration_seconds=600
    )
    activities.start_activity(
        world_id, "erika", "idle", "entree_exterieure", duration_seconds=600
    )

    due_checks = iter((False, True))
    monkeypatch.setattr(MVPRuntime, "_simulation_due", lambda _self, _target: next(due_checks))
    cognition = CountingProvider()
    report = MVPRuntime(
        conn, world_id, cognition_provider=cognition,
        scene_provider=SceneProvider(), limits=limits,
    ).run_once()

    assert report.social is not None
    assert report.autonomy is None and report.cognition is None
    assert cognition.calls == 0


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
