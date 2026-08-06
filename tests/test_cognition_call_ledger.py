from datetime import datetime, timezone

import pytest

from vivarium.cognition_call_ledger import CognitionCallLedgerError, CognitionCallLedgerService
from vivarium.cognition_policy import CognitionCallLimits
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.util import to_iso


class Clock:
    def now(self): return datetime(2026, 8, 6, 12, tzinfo=timezone.utc)
    def now_iso(self): return to_iso(self.now())


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
