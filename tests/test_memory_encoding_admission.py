from datetime import datetime, timezone

import pytest

from vivarium.attention import AttentionService
from vivarium.cognition import CognitionContextService
from vivarium.cognition_policy import CognitionCallLimits
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.mvp_runtime import MVPRuntime
from vivarium.repro import canonical_state_digest
from vivarium.scenes import SocialSceneService
from vivarium.social_cognition_runtime import LiveSocialCognitionService
from vivarium.social_interpretation_provider import DeterministicInterpretationProvider
from vivarium.subjective_memory import SubjectiveMemoryError, SubjectiveMemoryService
from vivarium.util import to_iso


class Clock:
    def now(self):
        return datetime(2026, 8, 15, 12, tzinfo=timezone.utc)

    def now_iso(self):
        return to_iso(self.now())


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = Clock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    yield conn, world_id, clock
    conn.close()


def test_f1_f2_accessible_is_not_memory_and_selected_is_not_copied(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)
    snapshot = AttentionService(conn, clock=clock).snapshot(world_id, "sophie")

    assert len(snapshot.available) > len(snapshot.selected)
    decisions = memory.admit_current_attention(world_id)

    assert any(item["decision"]["outcome"] == "encoded" for item in decisions)
    assert any(item["decision"]["outcome"] == "not_encoded" for item in decisions)
    assert conn.execute(
        "SELECT COUNT(*) FROM subjective_trace WHERE world_id = ? AND "
        "character_id = (SELECT id FROM character WHERE world_id = ? AND key = 'sophie')",
        (world_id, world_id),
    ).fetchone()[0] < len(snapshot.available)


def test_f3_attention_trace_can_remain_trace_only(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)
    item = AttentionService(conn, clock=clock).snapshot(world_id, "sophie").selected[0]

    trace = memory.encode_attention(world_id, "sophie", "attention-trace-only", item)
    decision = conn.execute(
        "SELECT outcome, reason_code FROM autobiographical_episode_seed_decision "
        "WHERE trace_id = (SELECT id FROM subjective_trace WHERE request_key = ?)",
        ("attention-trace-only",),
    ).fetchone()

    assert trace["fact_type"]
    assert tuple(decision) == ("trace_only", "attention_state_not_episode_unit")
    assert conn.execute("SELECT COUNT(*) FROM autobiographical_episode").fetchone()[0] == 0


def test_f4_admission_is_reasoned_without_global_salience_score(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)
    memory.admit_current_attention(world_id)

    columns = {
        row["name"] for row in conn.execute(
            "PRAGMA table_info(subjective_memory_encoding_admission)"
        )
    }
    reasons = {
        row[0] for row in conn.execute(
            "SELECT DISTINCT reason_code FROM subjective_memory_encoding_admission"
        )
    }
    assert "memory_score" not in columns
    assert "salience_score" not in columns
    assert "attention_primary_candidate" in reasons
    assert "attention_not_primary_candidate" in reasons or "attention_not_selected" in reasons


def test_f5_trace_cognitive_projection_excludes_audit_provenance(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)
    item = AttentionService(conn, clock=clock).snapshot(world_id, "sophie").selected[0]
    memory.encode_attention(world_id, "sophie", "projection-trace", item)

    context = CognitionContextService(conn, clock=clock).build(world_id, "sophie")
    projected = context.memories[0]
    assert "public_id" not in projected
    assert "request_key" not in projected
    assert "source_kind" not in projected
    assert "access_kind" not in projected
    assert "source_event_seq" not in projected


def test_f6_never_encoded_content_has_no_trace_or_episode(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)
    snapshot = AttentionService(conn, clock=clock).snapshot(world_id, "sophie")
    not_selected = snapshot.available[-1]
    result = memory.admit_attention(world_id, "sophie", "never-encoded", not_selected)

    assert result["decision"]["outcome"] == "not_encoded"
    assert result["trace"] is None
    assert conn.execute(
        "SELECT COUNT(*) FROM subjective_trace WHERE request_key = 'never-encoded'"
    ).fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM autobiographical_episode").fetchone()[0] == 0


def test_f7_temporal_proximity_does_not_merge_state_traces(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)
    item = AttentionService(conn, clock=clock).snapshot(world_id, "sophie").selected[0]

    memory.encode_attention(world_id, "sophie", "near-trace-a", item)
    memory.encode_attention(world_id, "sophie", "near-trace-b", item)

    assert conn.execute("SELECT COUNT(*) FROM subjective_trace").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM autobiographical_episode").fetchone()[0] == 0


def test_f8_owner_isolation_for_admission_and_seeding(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)
    item = AttentionService(conn, clock=clock).snapshot(world_id, "sophie").selected[0]
    memory.encode_attention(world_id, "sophie", "private-trace", item)
    trace_id = conn.execute(
        "SELECT id FROM subjective_trace WHERE request_key = 'private-trace'"
    ).fetchone()[0]

    with pytest.raises(SubjectiveMemoryError) as raised:
        memory.seed_episode_for_trace(world_id, "luna", trace_id)
    assert raised.value.code == "source_not_accessible"
    assert conn.execute(
        "SELECT COUNT(*) FROM autobiographical_episode WHERE character_id = "
        "(SELECT id FROM character WHERE key = 'luna')"
    ).fetchone()[0] == 0


def test_f9_memory_work_does_not_change_canon(setup):
    conn, world_id, clock = setup
    before = canonical_state_digest(conn, world_id)
    memory = SubjectiveMemoryService(conn, clock=clock)
    memory.admit_current_attention(world_id)
    after = canonical_state_digest(conn, world_id)
    assert after == before


def test_f10_runtime_memory_retry_is_idempotent(setup):
    conn, world_id, clock = setup
    memory = SubjectiveMemoryService(conn, clock=clock)
    first = memory.admit_current_attention(world_id)
    counts_before = tuple(
        conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("subjective_memory_encoding_admission", "subjective_trace", "autobiographical_episode")
    )
    second = memory.admit_current_attention(world_id)
    counts_after = tuple(
        conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("subjective_memory_encoding_admission", "subjective_trace", "autobiographical_episode")
    )
    assert first == second
    assert counts_after == counts_before


def test_runtime_social_path_seeds_episode_and_cognition_can_recall_it(setup):
    conn, world_id, clock = setup
    runtime_report = MVPRuntime(conn, world_id, clock=clock).run_once()
    assert runtime_report.status == "active"
    assert conn.execute(
        "SELECT COUNT(*) FROM subjective_memory_encoding_admission"
    ).fetchone()[0] > 0
    assert conn.execute("SELECT COUNT(*) FROM subjective_trace").fetchone()[0] > 0
    assert conn.execute(
        "SELECT COUNT(*) FROM subjective_trace trace "
        "JOIN character ch ON ch.id = trace.character_id WHERE ch.key = 'patoune'"
    ).fetchone()[0] == 0

    scenes = SocialSceneService(conn, clock=clock)
    scenes.open(world_id, "memory-scene", ("sophie", "erika"))
    scenes.speak(
        world_id, "memory-scene", "memory-speech", "sophie", act_kind="inform",
        content="Sophie partage une parole.", recipient_key="erika",
    )
    provider = DeterministicInterpretationProvider(
        {"schema_version": 2, "understanding_status": "unresolved", "meaning_hypotheses": []},
    )

    outcomes = LiveSocialCognitionService(conn, provider, clock=clock).process_speech(
        world_id, "memory-scene", "memory-speech", CognitionCallLimits(0, 3600, 8),
    )

    assert len(outcomes) == 2
    assert conn.execute(
        "SELECT COUNT(*) FROM autobiographical_episode WHERE world_id = ?",
        (world_id,),
    ).fetchone()[0] == 2
    context = CognitionContextService(conn, clock=clock).build(world_id, "erika")
    assert context.autobiographical_memories
    assert context.autobiographical_memories[0]["source_attribution"] == {"kind": "unresolved"}
