from datetime import datetime, timezone

from vivarium.activities import ActivityEngine
from vivarium.autonomy_cycle import AutonomyCycle
from vivarium.cognition import CognitionDecision
from vivarium.cognition_policy import CognitionCallLimits
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.orchestrator import VivariumOrchestrator
from vivarium.util import to_iso


class Clock:
    def now(self): return datetime(2026, 8, 6, 12, tzinfo=timezone.utc)
    def now_iso(self): return to_iso(self.now())


class Provider:
    def __init__(self): self.calls = []
    def decide(self, context):
        self.calls.append(context)
        if context.character_key == "sophie":
            return CognitionDecision("start_activity", None, "entree_exterieure", "photography")
        return CognitionDecision("no_action")


def _setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = Clock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    return conn, world_id, clock


def test_idle_event_opens_one_bounded_activity_decision_and_is_idempotent():
    conn, world_id, clock = _setup()
    try:
        ActivityEngine(conn, clock=clock).start_activity(
            world_id, "sophie", "idle", "entree_exterieure", duration_seconds=600
        )
        provider = Provider()
        cycle = AutonomyCycle(conn, provider, clock=clock)
        limits = CognitionCallLimits(0, 3600, 8)

        first = cycle.tick(world_id, limits)
        second = cycle.tick(world_id, limits)

        assert first.character_key == "sophie" and first.routed and first.routed.attempted
        assert first.routed.turn is not None
        assert first.routed.turn.context.allowed_activities
        assert first.routed.turn.validation.status == "accepted"
        assert ActivityEngine(conn).activity_sheet(world_id, "sophie")["type"] == "photography"
        assert second.character_key is None and len(provider.calls) == 1
    finally:
        conn.close()


def test_direct_event_orchestrator_never_calls_cognition_for_patoune():
    conn, world_id, clock = _setup()
    try:
        provider = Provider()
        tick = VivariumOrchestrator(conn, provider, clock=clock).tick(
            world_id, CognitionCallLimits(0, 3600, 100), max_events_per_character=1
        )
        assert "patoune" not in {outcome.character_key for outcome in tick.outcomes}
        assert all(context.character_key != "patoune" for context in provider.calls)
    finally:
        conn.close()
