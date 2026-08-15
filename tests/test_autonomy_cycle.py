from datetime import datetime, timedelta, timezone

from vivarium.activities import ActivityEngine
from vivarium.autonomy_cycle import AutonomyCycle
from vivarium.cognition import CognitionDecision
from vivarium.cognition_call_ledger import CognitionCallLedgerService
from vivarium.cognitive_flow import CognitiveFlowScheduler
from vivarium.cognition_policy import CognitionCallLimits
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.orchestrator import VivariumOrchestrator
from vivarium.util import to_iso


class Clock:
    def now(self): return datetime(2026, 8, 6, 12, tzinfo=timezone.utc)
    def now_iso(self): return to_iso(self.now())


class AdvancingClock(Clock):
    def __init__(self): self.current = datetime(2026, 8, 6, 12, tzinfo=timezone.utc)
    def now(self): return self.current
    def advance(self, seconds): self.current += timedelta(seconds=seconds)


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


def test_invalid_llm_response_is_retried_after_a_bounded_delay():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = AdvancingClock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    try:
        ActivityEngine(conn, clock=clock).start_activity(
            world_id, "luna", "idle", "entree_exterieure", duration_seconds=28800
        )

        class FlakyProvider:
            def __init__(self): self.calls = 0
            def decide(self, context):
                self.calls += 1
                if self.calls == 1:
                    clock.advance(20)
                    return {"not": "a CognitionDecision"}
                return CognitionDecision("start_activity", None, "salon", "socialize")

        provider = FlakyProvider()
        cycle = AutonomyCycle(conn, provider, clock=clock)
        limits = CognitionCallLimits(0, 3600, 8)

        first = cycle.tick(world_id, limits)
        assert first.detail_code == "invalid_llm_response"
        retry_idle = ActivityEngine(conn).activity_sheet(world_id, "luna")
        assert retry_idle["type"] == "idle"
        assert retry_idle["started_at"] == first.routed.admission.admitted_at
        assert provider.calls == 1

        assert cycle.tick(world_id, limits).character_key is None
        assert provider.calls == 1
        clock.advance(301)

        retried = cycle.tick(world_id, limits)
        assert retried.routed is not None and retried.routed.turn is not None
        assert retried.routed.turn.validation.status == "accepted"
        assert provider.calls == 2
        assert ActivityEngine(conn).activity_sheet(world_id, "luna")["type"] == "socialize"
    finally:
        conn.close()


def test_budget_deferred_idle_is_explicit_until_its_budget_window_reopens():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = AdvancingClock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    try:
        ActivityEngine(conn, clock=clock).start_activity(
            world_id, "sophie", "idle", "entree_exterieure", duration_seconds=7_200
        )
        limits = CognitionCallLimits(0, 3_600, 1)
        CognitionCallLedgerService(conn, clock=clock).admit(
            world_id, "sophie", "direct_event", "preexisting_call", limits,
        )
        provider = Provider()

        # Une occasion refusée ne doit plus disparaître silencieusement, même
        # lorsque ce test exerce encore explicitement l'ancien quota.
        for _ in range(3):
            outcome = AutonomyCycle(conn, provider, clock=clock).tick(world_id, limits)
            assert outcome.character_key == "sophie"
            assert outcome.routed is not None
            assert outcome.routed.admission.verdict.reason_code == "budget_exhausted"
        assert provider.calls == []

        clock.advance(3_600)
        recovered = AutonomyCycle(conn, provider, clock=clock).tick(world_id, limits)
        assert recovered.character_key == "sophie" and recovered.routed is not None
        assert recovered.routed.attempted and recovered.routed.turn is not None
        assert provider.calls and ActivityEngine(conn).activity_sheet(world_id, "sophie")["type"] == "photography"
    finally:
        conn.close()


def test_budget_silence_for_one_idle_does_not_starve_another_resident():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = AdvancingClock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    try:
        activities = ActivityEngine(conn, clock=clock)
        activities.start_activity(world_id, "chuu", "idle", "entree_exterieure", duration_seconds=7_200)
        activities.start_activity(world_id, "sophie", "idle", "entree_exterieure", duration_seconds=7_200)
        limits = CognitionCallLimits(0, 3_600, 1)
        CognitionCallLedgerService(conn, clock=clock).admit(
            world_id, "chuu", "direct_event", "preexisting_chuu_call", limits,
        )

        provider = Provider()
        outcome = AutonomyCycle(conn, provider, clock=clock).tick(world_id, limits)

        assert outcome.character_key == "sophie" and outcome.routed is not None and outcome.routed.attempted
        assert [context.character_key for context in provider.calls] == ["sophie"]
        assert activities.activity_sheet(world_id, "sophie")["type"] == "photography"
    finally:
        conn.close()


def test_planned_reflection_is_not_rejected_after_eight_normal_calls():
    conn, world_id, clock = _setup()
    try:
        activities = ActivityEngine(conn, clock=clock)
        activities.start_activity(
            world_id, "sophie", "idle", "entree_exterieure", duration_seconds=7_200
        )
        normal_limits = CognitionCallLimits(0, 3_600, None)
        ledger = CognitionCallLedgerService(conn, clock=clock)
        for index in range(8):
            admission = ledger.admit(
                world_id, "sophie", "direct_event", f"normal_call_{index}", normal_limits,
            )
            assert admission.verdict.eligible

        provider = Provider()
        cycle = AutonomyCycle(
            conn, provider, clock=clock, flow_scheduler=CognitiveFlowScheduler()
        )
        outcome = cycle.tick(world_id, normal_limits)

        assert outcome.character_key == "sophie"
        assert outcome.routed is not None and outcome.routed.attempted
        assert outcome.routed.turn is not None
        assert len(provider.calls) == 1
    finally:
        conn.close()
