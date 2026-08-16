from datetime import datetime, timedelta, timezone

import pytest

from vivarium.attention import AttentionService
from vivarium.cognition import CognitionContextService
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.subjective_memory import SubjectiveMemoryError, SubjectiveMemoryService
from vivarium.traversal import TraversalEngine
from vivarium.util import to_iso


class MutableClock:
    def __init__(self):
        self.current = datetime(2026, 8, 6, 12, tzinfo=timezone.utc)

    def now(self):
        return self.current

    def now_iso(self):
        return to_iso(self.current)

    def advance(self, seconds: int):
        self.current += timedelta(seconds=seconds)


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = MutableClock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    yield conn, world_id, clock
    conn.close()


def _trace_id(conn, request_key):
    return conn.execute(
        "SELECT id FROM subjective_trace WHERE request_key = ?", (request_key,)
    ).fetchone()[0]


def _direct_trace(conn, world_id, clock, request_key, connector_key, target_key):
    event_seq = max_seq(conn, world_id) + 1
    TraversalEngine(conn, clock=clock).traverse_character(
        world_id, "sophie", connector_key, target_key
    )
    return SubjectiveMemoryService(conn, clock=clock).encode_direct_event(
        world_id, "sophie", request_key, event_seq
    )


def test_episode_is_distinct_from_trace_and_keeps_support_audit(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)
    item = AttentionService(conn, clock=clock).snapshot(world_id, "sophie").selected[0]
    trace = memory.encode_attention(world_id, "sophie", "notice_entry", item)
    trace_id = _trace_id(conn, "notice_entry")
    before_canon = canonical_state_digest(conn, world_id)

    episode = memory.form_episode(
        world_id,
        "sophie",
        "episode-entry",
        [trace_id],
        importance_milli=700,
        accessibility_milli=800,
    )

    assert episode["episode_key"] == "episode-entry"
    assert episode["support_trace_ids"] == (trace_id,)
    assert episode["gist"]["kind"] == "supported_trace_projection"
    assert episode["gist"]["support_count"] == 1
    assert episode["source_attribution"] == {"kind": "unresolved"}
    assert episode["participants"] == ("chuu",)
    assert "erika" not in episode["participants"]
    assert episode["recovery_cues"]
    assert episode["importance_milli"] == 700
    assert episode["accessibility_milli"] == 800
    assert memory.recall_recent(world_id, "sophie")[0]["request_key"] == "notice_entry"
    assert memory.recall_autobiographical(
        world_id, "sophie", context={"cues": ["adjacent_connector"]}
    )[0]["episode_key"] == "episode-entry"
    assert conn.execute("SELECT COUNT(*) FROM autobiographical_episode").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM autobiographical_episode_support").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM autobiographical_episode_event").fetchone()[0] == 1
    assert canonical_state_digest(conn, world_id) == before_canon

    audit = conn.execute(
        "SELECT trace.source_kind, trace.access_kind, trace.fidelity "
        "FROM autobiographical_episode_support support "
        "JOIN subjective_trace trace ON trace.id = support.trace_id "
        "WHERE support.episode_id = ("
        "SELECT id FROM autobiographical_episode WHERE episode_key = ?"
        ")",
        ("episode-entry",),
    ).fetchone()
    assert audit["source_kind"]
    assert audit["access_kind"]
    assert audit["fidelity"] == "complete"

    recalled = memory.recall_autobiographical(
        world_id, "sophie", context={"cues": ["adjacent_connector"]}
    )[0]
    assert recalled["source_attribution"] == {"kind": "unresolved"}
    assert "source_kinds" not in recalled["context"]
    assert "access_kinds" not in recalled["context"]
    assert all(
        key not in support
        for support in recalled["details"]["supports"]
        for key in ("source_kind", "access_kind", "fidelity")
    )

    with pytest.raises(Exception, match="immutable"):
        conn.execute("UPDATE autobiographical_episode SET importance_milli = 1")

    with pytest.raises(TypeError):
        memory.form_episode(
            world_id, "sophie", "unsupported-content", [trace_id],
            context={"unsupported_fact": "erika acted"},
        )
    with pytest.raises(TypeError):
        memory.form_episode(
            world_id, "sophie", "unsupported-participant", [trace_id],
            participants=["erika"],
        )

    second_trace = memory.encode_attention(
        world_id, "sophie", "notice_entry_2", item
    )
    second_trace_id = _trace_id(conn, "notice_entry_2")
    multi = memory.form_episode(
        world_id, "sophie", "episode-with-two-supports",
        [trace_id, second_trace_id],
    )
    assert multi["gist"]["support_count"] == 2
    assert len(multi["details"]["supports"]) == 2
    assert multi["support_trace_ids"] == (trace_id, second_trace_id)


def test_episode_requires_owned_subjective_support_and_not_a_canonical_shortcut(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)
    item = AttentionService(conn, clock=clock).snapshot(world_id, "sophie").selected[0]
    memory.encode_attention(world_id, "sophie", "sophie_trace", item)
    trace_id = _trace_id(conn, "sophie_trace")

    with pytest.raises(SubjectiveMemoryError) as raised:
        memory.form_episode(
            world_id, "luna", "cross-owner", [trace_id],
        )
    assert raised.value.code == "source_not_accessible"

    with pytest.raises(SubjectiveMemoryError) as raised:
        memory.form_episode(
            world_id, "sophie", "without-trace", [],
        )
    assert raised.value.code == "invalid_source"

    assert conn.execute("SELECT COUNT(*) FROM autobiographical_episode").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM subjective_belief").fetchone()[0] == 0


def test_retrieval_is_contextual_bounded_deterministic_and_read_only(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)
    old_trace = _direct_trace(
        conn, world_id, clock, "old_move", "porte_entree", "salon"
    )
    clock.advance(3600)
    recent_item = AttentionService(conn, clock=clock).snapshot(
        world_id, "sophie"
    ).selected[0]
    recent_trace = memory.encode_attention(
        world_id, "sophie", "recent_state", recent_item
    )
    old_id, recent_id = _trace_id(conn, "old_move"), _trace_id(conn, "recent_state")

    memory.form_episode(
        world_id, "sophie", "old-relevant", [old_id],
        importance_milli=100,
    )
    memory.form_episode(
        world_id, "sophie", "recent-irrelevant", [recent_id],
        importance_milli=100,
    )
    for index in range(6):
        memory.form_episode(
            world_id, "sophie", f"bounded-{index}", [old_id],
        )

    before = (
        canonical_state_digest(conn, world_id),
        conn.execute("SELECT COUNT(*) FROM subjective_trace").fetchone()[0],
        conn.execute("SELECT COUNT(*) FROM autobiographical_episode").fetchone()[0],
        conn.execute("SELECT COUNT(*) FROM subjective_belief").fetchone()[0],
    )
    first = memory.recall_autobiographical(
        world_id, "sophie", context={"cues": ["character_moved"]}, limit=3
    )
    second = memory.recall_autobiographical(
        world_id, "sophie", context={"cues": ["character_moved"]}, limit=3
    )

    assert len(first) == 3
    assert first == second
    assert first[0]["episode_key"] == "old-relevant"
    assert all("support_trace_ids" not in item for item in first)
    assert memory.recall_autobiographical(world_id, "erika") == ()
    assert (
        canonical_state_digest(conn, world_id),
        conn.execute("SELECT COUNT(*) FROM subjective_trace").fetchone()[0],
        conn.execute("SELECT COUNT(*) FROM autobiographical_episode").fetchone()[0],
        conn.execute("SELECT COUNT(*) FROM subjective_belief").fetchone()[0],
    ) == before


def test_cognition_receives_separate_autobiographical_working_set(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)
    item = AttentionService(conn, clock=clock).snapshot(world_id, "sophie").selected[0]
    memory.encode_attention(world_id, "sophie", "cognition_source", item)
    trace_id = _trace_id(conn, "cognition_source")
    memory.form_episode(
        world_id, "sophie", "cognition-episode", [trace_id],
    )

    context = CognitionContextService(conn, clock=clock).build(world_id, "sophie")
    assert context.memories[0]["fact_type"]
    assert "request_key" not in context.memories[0]
    assert context.autobiographical_memories[0]["episode_key"] == "cognition-episode"
    assert "autobiographical_memories" in context.wire()
    assert "support_trace_ids" not in context.wire()["autobiographical_memories"][0]
    cognitive_memory = context.wire()["autobiographical_memories"][0]
    assert cognitive_memory["source_attribution"] == {"kind": "unresolved"}
    assert "source_kinds" not in cognitive_memory["context"]
    assert "access_kinds" not in cognitive_memory["context"]
    assert CognitionContextService(conn, clock=clock).build(
        world_id, "erika"
    ).autobiographical_memories == ()


def test_append_only_lifecycle_keeps_history_and_retrieves_only_current(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)

    trace_a = _direct_trace(
        conn, world_id, clock, "lifecycle-a", "porte_entree", "salon"
    )
    trace_a_id = _trace_id(conn, "lifecycle-a")
    episode_zero = memory.form_episode(
        world_id, "sophie", "lifecycle-e0", [trace_a_id],
        importance_milli=640, accessibility_milli=720,
    )
    episode_zero_before = memory.get_episode(world_id, "sophie", "lifecycle-e0")

    attention_item = AttentionService(conn, clock=clock).snapshot(
        world_id, "sophie"
    ).selected[0]
    trace_b = memory.encode_attention(
        world_id, "sophie", "lifecycle-b", attention_item
    )
    trace_b_id = _trace_id(conn, "lifecycle-b")
    revision_one = memory.revise_episode(
        world_id, "sophie", "lifecycle-e0", "lifecycle-e1", [trace_b_id],
        request_key="lifecycle-revision-1",
    )

    assert revision_one["successor"]["episode_key"] == "lifecycle-e1"
    assert revision_one["successor"]["support_trace_ids"] == (trace_a_id, trace_b_id)
    assert revision_one["successor"]["importance_milli"] == 640
    assert revision_one["successor"]["accessibility_milli"] == 720
    assert memory.get_episode(world_id, "sophie", "lifecycle-e0") == episode_zero_before
    assert memory.get_current_episode(
        world_id, "sophie", "lifecycle-e0"
    )["episode_key"] == "lifecycle-e1"

    history_one = memory.get_episode_history(world_id, "sophie", "lifecycle-e1")
    assert tuple(item["episode_key"] for item in history_one) == (
        "lifecycle-e0", "lifecycle-e1"
    )
    assert history_one[0]["is_current"] is False
    assert history_one[1]["is_current"] is True
    assert history_one[1]["revision_from_predecessor"]["new_support_trace_ids"] == (
        trace_b_id,
    )
    recalled = memory.recall_autobiographical(
        world_id, "sophie", context={"cues": ["character_moved"]}
    )
    assert tuple(item["episode_key"] for item in recalled) == ("lifecycle-e1",)
    cognitive = CognitionContextService(conn, clock=clock).build(world_id, "sophie")
    assert tuple(item["episode_key"] for item in cognitive.autobiographical_memories) == (
        "lifecycle-e1",
    )
    assert "revision_from_predecessor" not in cognitive.wire()["autobiographical_memories"][0]

    trace_c = memory.encode_attention(
        world_id, "sophie", "lifecycle-c", attention_item
    )
    trace_c_id = _trace_id(conn, "lifecycle-c")
    revision_two = memory.revise_episode(
        world_id, "sophie", "lifecycle-e1", "lifecycle-e2", [trace_c_id],
        request_key="lifecycle-revision-2",
    )
    assert revision_two["successor"]["episode_key"] == "lifecycle-e2"
    assert tuple(item["episode_key"] for item in memory.recall_autobiographical(
        world_id, "sophie", context={"cues": ["character_moved"]}
    )) == ("lifecycle-e2",)
    assert tuple(item["episode_key"] for item in memory.get_episode_history(
        world_id, "sophie", "lifecycle-e0"
    )) == ("lifecycle-e0", "lifecycle-e1", "lifecycle-e2")


def test_append_only_lifecycle_rejects_forks_cross_owner_and_cycles(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)
    item = AttentionService(conn, clock=clock).snapshot(world_id, "sophie").selected[0]
    memory.encode_attention(world_id, "sophie", "fork-a", item)
    a_id = _trace_id(conn, "fork-a")
    memory.form_episode(world_id, "sophie", "fork-e0", [a_id])
    memory.encode_attention(world_id, "sophie", "fork-b", item)
    b_id = _trace_id(conn, "fork-b")
    memory.revise_episode(
        world_id, "sophie", "fork-e0", "fork-e1", [b_id],
        request_key="fork-revision-1",
    )

    with pytest.raises(SubjectiveMemoryError) as raised:
        memory.revise_episode(
            world_id, "sophie", "fork-e0", "fork-e-other", [b_id],
            request_key="fork-revision-2",
        )
    assert raised.value.code == "episode_not_current"

    erika_item = AttentionService(conn, clock=clock).snapshot(world_id, "erika").selected[0]
    memory.encode_attention(world_id, "erika", "fork-erika", erika_item)
    erika_trace_id = _trace_id(conn, "fork-erika")
    with pytest.raises(SubjectiveMemoryError) as raised:
        memory.revise_episode(
            world_id, "sophie", "fork-e1", "fork-cross-owner", [erika_trace_id],
            request_key="fork-cross-owner-request",
        )
    assert raised.value.code == "source_not_accessible"

    episode_zero_id = conn.execute(
        "SELECT id FROM autobiographical_episode WHERE episode_key = 'fork-e0'"
    ).fetchone()[0]
    episode_one_id = conn.execute(
        "SELECT id FROM autobiographical_episode WHERE episode_key = 'fork-e1'"
    ).fetchone()[0]
    with pytest.raises(Exception, match="cycle"):
        conn.execute(
            "INSERT INTO autobiographical_episode_revision "
            "(public_id, world_id, character_id, request_key, predecessor_episode_id, "
            "successor_episode_id, reason_code, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "cycle-public-id", world_id,
                conn.execute(
                    "SELECT id FROM character WHERE world_id = ? AND key = 'sophie'",
                    (world_id,),
                ).fetchone()[0],
                "cycle-request", episode_one_id, episode_zero_id,
                "test_cycle", clock.now_iso(),
            ),
        )


def test_append_only_lifecycle_is_immutable_and_retry_idempotent(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)
    item = AttentionService(conn, clock=clock).snapshot(world_id, "sophie").selected[0]
    memory.encode_attention(world_id, "sophie", "immutable-a", item)
    a_id = _trace_id(conn, "immutable-a")
    memory.form_episode(world_id, "sophie", "immutable-e0", [a_id])
    memory.encode_attention(world_id, "sophie", "immutable-b", item)
    b_id = _trace_id(conn, "immutable-b")
    first = memory.revise_episode(
        world_id, "sophie", "immutable-e0", "immutable-e1", [b_id],
        request_key="immutable-revision",
    )
    counts_before = tuple(
        conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in (
            "autobiographical_episode",
            "autobiographical_episode_revision",
            "autobiographical_episode_revision_support",
        )
    )
    second = memory.revise_episode(
        world_id, "sophie", "immutable-e0", "immutable-e1", [b_id],
        request_key="immutable-revision",
    )
    counts_after = tuple(
        conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in (
            "autobiographical_episode",
            "autobiographical_episode_revision",
            "autobiographical_episode_revision_support",
        )
    )
    assert first == second
    assert counts_after == counts_before

    with pytest.raises(Exception, match="append-only"):
        conn.execute(
            "UPDATE autobiographical_episode_revision SET reason_code = 'changed'"
        )
    with pytest.raises(Exception, match="append-only"):
        conn.execute("DELETE FROM autobiographical_episode_revision")
