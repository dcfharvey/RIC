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
        gist={"text": "Je me rappelle avoir remarqué l'entrée."},
        details={"fidelity": "complete"},
        context={"location_key": "porte_entree"},
        participants=["sophie"],
        source_attribution={"kind": "seen", "confidence": "bounded"},
        recovery_cues=["entry"],
        importance_milli=700,
        accessibility_milli=800,
    )

    assert episode["episode_key"] == "episode-entry"
    assert episode["support_trace_ids"] == (trace_id,)
    assert episode["source_attribution"]["kind"] == "seen"
    assert episode["importance_milli"] == 700
    assert episode["accessibility_milli"] == 800
    assert memory.recall_recent(world_id, "sophie")[0]["request_key"] == "notice_entry"
    assert memory.recall_autobiographical(
        world_id, "sophie", context={"cues": ["entry"]}
    )[0]["episode_key"] == "episode-entry"
    assert conn.execute("SELECT COUNT(*) FROM autobiographical_episode").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM autobiographical_episode_support").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM autobiographical_episode_event").fetchone()[0] == 1
    assert canonical_state_digest(conn, world_id) == before_canon

    with pytest.raises(Exception, match="immutable"):
        conn.execute("UPDATE autobiographical_episode SET importance_milli = 1")


def test_episode_requires_owned_subjective_support_and_not_a_canonical_shortcut(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)
    item = AttentionService(conn, clock=clock).snapshot(world_id, "sophie").selected[0]
    memory.encode_attention(world_id, "sophie", "sophie_trace", item)
    trace_id = _trace_id(conn, "sophie_trace")

    with pytest.raises(SubjectiveMemoryError) as raised:
        memory.form_episode(
            world_id, "luna", "cross-owner", [trace_id],
            gist={"text": "interdit"},
        )
    assert raised.value.code == "source_not_accessible"

    with pytest.raises(SubjectiveMemoryError) as raised:
        memory.form_episode(
            world_id, "sophie", "without-trace", [],
            gist={"text": "aucune source"},
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
    recent_trace = _direct_trace(
        conn, world_id, clock, "recent_move", "porte_entree", "entree_exterieure"
    )
    old_id, recent_id = _trace_id(conn, "old_move"), _trace_id(conn, "recent_move")

    memory.form_episode(
        world_id, "sophie", "old-relevant", [old_id],
        gist={"text": "ancienne entrée"},
        context={"location_key": "porte_entree"},
        recovery_cues=["entry-context"], importance_milli=100,
    )
    memory.form_episode(
        world_id, "sophie", "recent-irrelevant", [recent_id],
        gist={"text": "événement récent"},
        context={"location_key": "salon"},
        recovery_cues=["other-context"], importance_milli=100,
    )
    for index in range(6):
        memory.form_episode(
            world_id, "sophie", f"bounded-{index}", [old_id],
            gist={"text": f"borné {index}"}, recovery_cues=[f"bound-{index}"],
        )

    before = (
        canonical_state_digest(conn, world_id),
        conn.execute("SELECT COUNT(*) FROM subjective_trace").fetchone()[0],
        conn.execute("SELECT COUNT(*) FROM autobiographical_episode").fetchone()[0],
        conn.execute("SELECT COUNT(*) FROM subjective_belief").fetchone()[0],
    )
    first = memory.recall_autobiographical(
        world_id, "sophie", context={"cues": ["entry-context"]}, limit=3
    )
    second = memory.recall_autobiographical(
        world_id, "sophie", context={"cues": ["entry-context"]}, limit=3
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
        gist={"text": "souvenir pour la cognition"},
        recovery_cues=[item.fact.event_type],
    )

    context = CognitionContextService(conn, clock=clock).build(world_id, "sophie")
    assert context.memories[0]["request_key"] == "cognition_source"
    assert context.autobiographical_memories[0]["episode_key"] == "cognition-episode"
    assert "autobiographical_memories" in context.wire()
    assert "support_trace_ids" not in context.wire()["autobiographical_memories"][0]
    assert CognitionContextService(conn, clock=clock).build(
        world_id, "erika"
    ).autobiographical_memories == ()
