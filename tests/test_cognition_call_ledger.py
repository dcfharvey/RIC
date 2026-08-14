from datetime import datetime, timedelta, timezone

import pytest

from vivarium.cognition_call_ledger import CognitionCallLedgerError, CognitionCallLedgerService
from vivarium.cognition_policy import CognitionCallLimits
from vivarium.activities import ActivityEngine
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.util import to_iso


class Clock:
    def now(self): return datetime(2026, 8, 6, 12, tzinfo=timezone.utc)
    def now_iso(self): return to_iso(self.now())


class AdvancingClock(Clock):
    def __init__(self): self.current = datetime(2026, 8, 6, 12, tzinfo=timezone.utc)
    def now(self): return self.current
    def advance(self, seconds): self.current += timedelta(seconds=seconds)


@pytest.fixture
def setup():
    conn = connect_database(":memory:"); ensure_schema(conn); clock = Clock()
    wid = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    yield conn, wid, clock
    conn.close()


def test_admission_is_idempotent_append_only_and_not_canonical(setup):
    conn, wid, clock = setup
    ledger = CognitionCallLedgerService(conn, clock=clock)
    limits = CognitionCallLimits(0, 3_600, 2)
    before_state, before_seq = canonical_state_digest(conn, wid), max_seq(conn, wid)

    first = ledger.admit(wid, "sophie", "direct_event", "event_42", limits)
    replay = ledger.admit(wid, "sophie", "direct_event", "event_42", limits)

    assert first.verdict.eligible and first.admission_id and first.admitted_at
    assert not replay.verdict.eligible and replay.verdict.reason_code == "duplicate_call"
    assert replay.admission_id is None
    assert len(ledger.history(wid, "sophie")) == 1
    assert canonical_state_digest(conn, wid) == before_state and max_seq(conn, wid) == before_seq
    with pytest.raises(Exception, match="immutable"):
        conn.execute("UPDATE cognition_call_admission SET source_key = 'event_99'")


def test_budget_is_per_resident_and_deferred_requests_do_not_write(setup):
    conn, wid, clock = setup
    ledger = CognitionCallLedgerService(conn, clock=clock)
    limits = CognitionCallLimits(0, 3_600, 1)

    assert ledger.admit(wid, "sophie", "direct_event", "event_42", limits).verdict.eligible
    refused = ledger.admit(wid, "sophie", "direct_event", "event_43", limits)
    luna = ledger.admit(wid, "luna", "direct_event", "event_42", limits)

    assert refused.verdict.reason_code == "budget_exhausted" and refused.admission_id is None
    assert luna.verdict.eligible
    assert len(ledger.history(wid, "sophie")) == 1 and len(ledger.history(wid, "luna")) == 1


def test_technical_idle_reserves_existing_budget_slot_for_planned_reflection(setup):
    conn, wid, clock = setup
    ActivityEngine(conn, clock=clock).start_activity(
        wid, "sophie", "idle", "entree_exterieure", duration_seconds=600,
        action_provenance={
            "proposal_id": "wo95_idle_test", "origin": "wo95_post_boundary_idle",
        },
    )
    idle_seq = conn.execute(
        "SELECT seq FROM canonical_event WHERE world_id=? AND event_type='activity_started' "
        "AND json_extract(payload, '$.character')='sophie' ORDER BY seq DESC LIMIT 1",
        (wid,),
    ).fetchone()[0]
    ledger = CognitionCallLedgerService(conn, clock=clock)
    limits = CognitionCallLimits(0, 3_600, 2)

    social = ledger.admit(wid, "sophie", "scene_turn", "scene_turn_1", limits)
    planned = ledger.admit(
        wid, "sophie", "planned_reflection", f"idle_{idle_seq}", limits
    )

    assert social.verdict.eligible
    assert planned.verdict.eligible
    assert len(ledger.history(wid, "sophie")) == 2
    assert ledger.admit(wid, "sophie", "social_interpretation", "trace_2", limits).verdict.reason_code == "budget_exhausted"


def test_unknown_trigger_and_unknown_character_are_refused_without_trace(setup):
    conn, wid, clock = setup
    ledger = CognitionCallLedgerService(conn, clock=clock)
    limits = CognitionCallLimits(0, 3_600, 1)
    with pytest.raises(CognitionCallLedgerError) as raised:
        ledger.admit(wid, "sophie", "free_text", "event_42", limits)
    assert raised.value.code == "unknown_cognition_call_trigger"
    with pytest.raises(CognitionCallLedgerError) as raised:
        ledger.admit(wid, "nobody", "direct_event", "event_42", limits)
    assert raised.value.code == "character_not_found"
    assert conn.execute("SELECT COUNT(*) FROM cognition_call_admission").fetchone()[0] == 0


def test_retry_domains_keep_provider_wall_time_separate_from_canonical_budget_time():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = AdvancingClock()
    wid = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    try:
        # Le monde est volontairement quatre heures derriere l'horloge technique.
        conn.execute(
            "UPDATE canonical_clock SET simulated_now=?, real_updated_at=?, runtime_state='running' WHERE world_id=?",
            ("2026-08-06T08:00:00+00:00", clock.now_iso(), wid),
        )
        conn.commit()
        ledger = CognitionCallLedgerService(conn, clock=clock)
        limits = CognitionCallLimits(0, 3_600, 1)
        attempted_at = clock.now_iso()

        assert not ledger.retry_due(wid, "sophie", limits, attempted_at=attempted_at, reason_code="provider_unavailable", retry_delay_seconds=30)
        clock.advance(29)
        assert not ledger.retry_due(wid, "sophie", limits, attempted_at=attempted_at, reason_code="provider_unavailable", retry_delay_seconds=30)
        clock.advance(1)
        assert ledger.retry_due(wid, "sophie", limits, attempted_at=attempted_at, reason_code="provider_unavailable", retry_delay_seconds=30)

        assert ledger.admit(wid, "sophie", "direct_event", "budget_origin", limits).verdict.eligible
        assert not ledger.retry_due(wid, "sophie", limits, attempted_at=clock.now_iso(), reason_code="budget_exhausted", retry_delay_seconds=30)
        clock.advance(3_570)
        assert not ledger.retry_due(wid, "sophie", limits, attempted_at=clock.now_iso(), reason_code="budget_exhausted", retry_delay_seconds=30)
        clock.advance(30)
        assert ledger.retry_due(wid, "sophie", limits, attempted_at=clock.now_iso(), reason_code="budget_exhausted", retry_delay_seconds=30)
    finally:
        conn.close()
