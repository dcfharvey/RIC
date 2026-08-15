from datetime import datetime, timezone

from vivarium.cognition_call_ledger import CognitionCallLedgerService
from vivarium.cognitive_flow import CognitiveFlowRequest, CognitiveFlowScheduler, flow_failure_state
from vivarium.cognition_policy import CognitionCallLimits, CognitionCallPolicy, CognitionCallRecord, CognitionCallRequest
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.util import to_iso


class Clock:
    def now(self):
        return datetime(2026, 8, 14, 12, tzinfo=timezone.utc)

    def now_iso(self):
        return to_iso(self.now())


def request(source: str) -> CognitionCallRequest:
    return CognitionCallRequest("sophie", "planned_reflection", source, "2026-08-14T12:00:00+00:00")


def record(index: int) -> CognitionCallRecord:
    return CognitionCallRecord(
        "sophie", "direct_event", f"event_{index}", "2026-08-14T11:59:00+00:00"
    )


def test_normal_runtime_policy_does_not_reject_legitimate_calls_after_old_activity():
    history = tuple(record(index) for index in range(20))
    verdict = CognitionCallPolicy.evaluate(
        request("idle_21"), history, CognitionCallLimits(0, 3_600, None)
    )
    assert verdict.eligible


def test_scheduler_waits_and_rotates_by_resident_and_category():
    scheduler = CognitiveFlowScheduler()
    first = CognitiveFlowRequest(1, "chuu", "direct_event", "event_1", "t0")
    second = CognitiveFlowRequest(1, "sophie", "direct_event", "event_2", "t0")
    third = CognitiveFlowRequest(1, "chuu", "planned_reflection", "idle_3", "t0")

    scheduler.begin_tick()
    assert scheduler.offer(first).state == "ready"
    scheduler.complete(first.idempotency_key)
    assert scheduler.offer(second).state == "queued"
    assert scheduler.offer(third).state == "queued"
    assert scheduler.pending_count() == 2

    scheduler.begin_tick()
    assert scheduler.offer(second).state == "ready"
    scheduler.complete(second.idempotency_key)
    scheduler.begin_tick()
    assert scheduler.offer(third).state == "ready"
    scheduler.complete(third.idempotency_key)
    assert scheduler.pending_count() == 0


def test_same_pending_opportunity_is_coalesced_and_never_dispatched_twice():
    scheduler = CognitiveFlowScheduler()
    first = CognitiveFlowRequest(1, "chuu", "direct_event", "event_3", "t0")
    request_value = CognitiveFlowRequest(1, "sophie", "planned_reflection", "idle_4", "t0")
    scheduler.begin_tick()
    assert scheduler.offer(first).state == "ready"
    assert scheduler.offer(request_value).state == "queued"
    assert scheduler.offer(request_value).state == "coalesced"
    scheduler.complete(first.idempotency_key)
    scheduler.begin_tick()
    assert scheduler.offer(request_value).state == "ready"
    scheduler.complete(request_value.idempotency_key)
    assert scheduler.pending_count() == 0


def test_causal_lineage_fuse_is_distinct_from_a_normal_hourly_quota():
    scheduler = CognitiveFlowScheduler(max_lineage_requests=2)
    scheduler.begin_tick()
    first = CognitiveFlowRequest(1, "sophie", "direct_event", "event_20", "t0", parent_event_seq=7)
    assert scheduler.offer(first).state == "ready"
    scheduler.complete(first.idempotency_key)
    scheduler.begin_tick()
    second = CognitiveFlowRequest(1, "sophie", "planned_reflection", "idle_21", "t0", parent_event_seq=7)
    assert scheduler.offer(second).state == "ready"
    scheduler.complete(second.idempotency_key)
    scheduler.begin_tick()
    third = CognitiveFlowRequest(1, "sophie", "social_interpretation", "trace_22", "t0", parent_event_seq=7)
    offer = scheduler.offer(third)
    assert offer.state == "runaway_guard"
    assert offer.reason_code == "causal_lineage_limit"


def test_provider_timeout_has_a_distinct_technical_issue_class():
    assert flow_failure_state("provider_timeout") == "timeout"
    assert flow_failure_state("provider_unavailable") == "provider_error"


def test_ledger_without_normal_quota_keeps_admission_and_telemetry_distinct():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = Clock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    try:
        scheduler = CognitiveFlowScheduler()
        scheduler.begin_tick()
        ledger = CognitionCallLedgerService(conn, clock=clock, flow_scheduler=scheduler)
        limits = CognitionCallLimits(0, 3_600, None)

        first = ledger.admit(world_id, "sophie", "direct_event", "event_1", limits)
        assert first.verdict.eligible
        # The old eight-call condition is irrelevant in the normal runtime.
        for index in range(2, 12):
            scheduler.begin_tick()
            admission = ledger.admit(world_id, "sophie", "direct_event", f"event_{index}", limits)
            assert admission.verdict.eligible

        states = [row[0] for row in conn.execute(
            "SELECT state FROM cognition_flow_event WHERE world_id=? ORDER BY id", (world_id,)
        )]
        assert states.count("opportunity") == 11
        assert states.count("admitted") == 11
        assert conn.execute(
            "SELECT COUNT(*) FROM cognition_call_admission WHERE world_id=?", (world_id,)
        ).fetchone()[0] == 11
    finally:
        conn.close()
