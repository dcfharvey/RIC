from datetime import datetime, timezone

import pytest

from vivarium.attention import AttentionService
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.subjective_memory import SubjectiveMemoryError, SubjectiveMemoryService
from vivarium.traversal import TraversalEngine
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


def test_attention_trace_is_validated_immutable_and_not_canonical(setup):
    conn, wid, clock = setup
    item = AttentionService(conn, clock=clock).snapshot(wid, "sophie").selected[0]
    before_state, before_seq = canonical_state_digest(conn, wid), max_seq(conn, wid)
    memory = SubjectiveMemoryService(conn, clock=clock)
    trace = memory.encode_attention(wid, "sophie", "notice_entry", item, fidelity="partial")
    assert trace["source_kind"] == "state" and trace["fidelity"] == "partial"
    assert memory.encode_attention(wid, "sophie", "notice_entry", item, fidelity="partial") == trace
    assert conn.execute("SELECT COUNT(*) FROM subjective_trace_event").fetchone()[0] == 1
    assert canonical_state_digest(conn, wid) == before_state and max_seq(conn, wid) == before_seq
    with pytest.raises(Exception, match="immutable"):
        conn.execute("UPDATE subjective_trace SET fidelity = 'complete'")


def test_direct_event_cannot_be_encoded_by_another_character(setup):
    conn, wid, clock = setup
    seq = max_seq(conn, wid) + 1
    TraversalEngine(conn, clock=clock).traverse_character(wid, "sophie", "porte_entree", "salon")
    memory = SubjectiveMemoryService(conn, clock=clock)
    trace = memory.encode_direct_event(wid, "sophie", "notice_move", seq)
    assert trace["source_event_seq"] == seq and trace["fact_type"] == "character_moved"
    with pytest.raises(SubjectiveMemoryError) as raised:
        memory.encode_direct_event(wid, "erika", "steal_move", seq)
    assert raised.value.code == "source_not_accessible"
