import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from vivarium.attention import AttentionService
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.mvp_preflight import inspect_mvp_preflight
from vivarium.repro import (
    canonical_state_digest,
    max_seq,
    social_interpretation_audit,
    social_interpretation_digest,
)
from vivarium.scenes import SocialSceneService
from vivarium.social_interpretation import SocialInterpretationError, SocialInterpretationService
from vivarium.subjective_memory import SubjectiveMemoryService
from vivarium.traversal import TraversalEngine
from vivarium.util import to_iso


class FakeClock:
    def __init__(self):
        self.current = datetime(2026, 8, 8, 12, tzinfo=timezone.utc)

    def now(self):
        return self.current

    def now_iso(self):
        return to_iso(self.current)

    def advance(self, seconds=1):
        self.current += timedelta(seconds=seconds)


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    assert ensure_schema(conn) == 46
    clock = FakeClock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    yield conn, world_id, clock
    conn.close()


def _at_salon(conn, world_id, *keys, clock=None):
    traversal = TraversalEngine(conn, clock=clock)
    for key in keys:
        traversal.traverse_character(world_id, key, "porte_entree", "salon")


def _social_source(setup, *, recipient="erika"):
    conn, world_id, clock = setup
    _at_salon(conn, world_id, "sophie", "erika", "luna", clock=clock)
    scenes = SocialSceneService(conn, clock=clock)
    scenes.open(world_id, "interpretation_scene", ("sophie", "erika", "luna"))
    scenes.speak(
        world_id, "interpretation_scene", "speech_1", "sophie", act_kind="inform",
        content="Sophie exprime une accusation.", recipient_key=recipient,
    )
    memory = SubjectiveMemoryService(conn, clock=clock)
    erika_trace = memory.encode_social_speech(
        world_id, "erika", "erika_speech_1", "interpretation_scene", "speech_1"
    )
    luna_trace = memory.encode_social_speech(
        world_id, "luna", "luna_speech_1", "interpretation_scene", "speech_1"
    )
    return conn, world_id, clock, scenes, memory, erika_trace, luna_trace


def test_same_expression_has_private_owner_scoped_interpretations(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    service = SocialInterpretationService(conn, clock=clock)
    erika = service.create(
        world_id, "erika", "erika_reading", "erika_speech_1",
        understanding_status="clear", meaning_hypotheses=["Sophie accuse quelqu'un."],
    )
    luna = service.create(
        world_id, "luna", "luna_reading", "luna_speech_1",
        understanding_status="ambiguous", meaning_hypotheses=["Sophie accuse quelqu'un.", "Sophie plaisante."],
    )
    assert erika["character_id"] != luna["character_id"]
    assert erika["source_trace_request_key"] == "erika_speech_1"
    assert luna["source_trace_request_key"] == "luna_speech_1"
    assert service.list(world_id, "erika")[0]["interpretation_key"] == "erika_reading"
    assert service.list(world_id, "luna")[0]["interpretation_key"] == "luna_reading"


def test_interaction_role_is_derived_not_provider_supplied(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    memory.encode_social_speech(world_id, "sophie", "sophie_speech_1", "interpretation_scene", "speech_1")
    service = SocialInterpretationService(conn, clock=clock)
    assert service.create(world_id, "sophie", "speaker_reading", "sophie_speech_1", understanding_status="unresolved")["interaction_role"] == "speaker"
    assert service.create(world_id, "erika", "addressee_reading", "erika_speech_1", understanding_status="unresolved")["interaction_role"] == "addressee"
    assert service.create(world_id, "luna", "side_reading", "luna_speech_1", understanding_status="unresolved")["interaction_role"] == "side_participant"


def test_ambiguous_and_unresolved_are_valid_without_forced_selection(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    service = SocialInterpretationService(conn, clock=clock)
    ambiguous = service.create(
        world_id, "erika", "ambiguous", "erika_speech_1", understanding_status="ambiguous",
        meaning_hypotheses=["Une accusation.", "Une plaisanterie."],
    )
    unresolved = service.create(
        world_id, "luna", "unresolved", "luna_speech_1", understanding_status="unresolved",
    )
    assert len(ambiguous["meaning_hypotheses"]) == 2
    assert unresolved["meaning_hypotheses"] == []


def test_hypotheses_are_trimmed_and_duplicates_do_not_satisfy_ambiguity(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    service = SocialInterpretationService(conn, clock=clock)
    with pytest.raises(SocialInterpretationError) as raised:
        service.create(
            world_id, "erika", "blank", "erika_speech_1", understanding_status="clear",
            meaning_hypotheses=["   "],
        )
    assert raised.value.code == "invalid_interpretation"
    with pytest.raises(SocialInterpretationError) as raised:
        service.create(
            world_id, "erika", "duplicate", "erika_speech_1", understanding_status="ambiguous",
            meaning_hypotheses=[" elle plaisante ", "elle plaisante"],
        )
    assert raised.value.code == "invalid_interpretation"
    normalized = service.create(
        world_id, "erika", "normalized", "erika_speech_1", understanding_status="clear",
        meaning_hypotheses=["  elle plaisante  "],
    )
    assert normalized["meaning_hypotheses"] == ["elle plaisante"]


def test_assertion_does_not_become_belief_or_actual_intent(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    service = SocialInterpretationService(conn, clock=clock)
    interpretation = service.create(
        world_id, "erika", "motive", "erika_speech_1", understanding_status="clear",
        meaning_hypotheses=["Sophie accuse Luna."],
    )
    assert "actual_intent" not in interpretation
    assert conn.execute("SELECT COUNT(*) FROM subjective_belief").fetchone()[0] == 0


def test_bad_provenance_is_rejected_without_partial_write(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    state_item = AttentionService(conn, clock=clock).snapshot(world_id, "erika").selected[0]
    memory.encode_attention(world_id, "erika", "ordinary_state", state_item)
    service = SocialInterpretationService(conn, clock=clock)
    before = conn.execute("SELECT COUNT(*) FROM social_interpretation").fetchone()[0]
    with pytest.raises(SocialInterpretationError) as raised:
        service.create(world_id, "erika", "bad", "ordinary_state", understanding_status="unresolved")
    assert raised.value.code == "source_not_accessible"
    with pytest.raises(SocialInterpretationError):
        service.create(world_id, "erika", "missing", "missing", understanding_status="unresolved")
    assert conn.execute("SELECT COUNT(*) FROM social_interpretation").fetchone()[0] == before


def test_revision_preserves_prior_entry_and_records_supporting_trace(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    service = SocialInterpretationService(conn, clock=clock)
    first = service.create(
        world_id, "erika", "first", "erika_speech_1", understanding_status="ambiguous",
        meaning_hypotheses=["Une accusation.", "Une plaisanterie."],
    )
    clock.advance(2)
    state_item = AttentionService(conn, clock=clock).snapshot(world_id, "erika").selected[0]
    observation = memory.encode_attention(world_id, "erika", "erika_observation", state_item)
    revised = service.create(
        world_id, "erika", "second", "erika_speech_1", understanding_status="clear",
        meaning_hypotheses=["Sophie plaisante."], revision_of_key="first",
        supporting_trace_request_keys=["erika_observation"],
    )
    assert revised["revision_of_key"] == "first"
    assert revised["source_trace_request_key"] == "erika_speech_1"
    assert revised["supporting_trace_request_keys"] == ("erika_observation",)
    assert service.get(world_id, "erika", "first")["revision_of_key"] is None
    primary = conn.execute(
        "SELECT fact_type, source_social_speech_act_id FROM subjective_trace WHERE id = ?",
        (first["source_trace_id"],),
    ).fetchone()
    support = conn.execute(
        "SELECT trace.fact_type, trace.source_social_speech_act_id "
        "FROM social_interpretation_support support JOIN subjective_trace trace ON trace.id = support.trace_id "
        "JOIN social_interpretation interpretation ON interpretation.id = support.interpretation_id "
        "WHERE interpretation.world_id = ? AND interpretation.interpretation_key = ?",
        (world_id, "second"),
    ).fetchone()
    assert primary["fact_type"] == "social_speech_act" and primary["source_social_speech_act_id"] is not None
    assert support["fact_type"] != "social_speech_act" and support["source_social_speech_act_id"] is None
    assert observation["source_event_seq"] is None


def test_revision_requires_same_source_and_additional_evidence(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    service = SocialInterpretationService(conn, clock=clock)
    service.create(world_id, "erika", "first", "erika_speech_1", understanding_status="unresolved")
    with pytest.raises(SocialInterpretationError) as raised:
        service.create(world_id, "erika", "second", "erika_speech_1", understanding_status="unresolved", revision_of_key="first")
    assert raised.value.code == "revision_support_required"


def test_interpretation_is_idempotent_and_conflicts_explicitly(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    service = SocialInterpretationService(conn, clock=clock)
    first = service.create(world_id, "erika", "same", "erika_speech_1", understanding_status="clear", meaning_hypotheses=["Une accusation."])
    assert service.create(world_id, "erika", "same", "erika_speech_1", understanding_status="clear", meaning_hypotheses=["Une accusation."]) == first
    with pytest.raises(SocialInterpretationError) as raised:
        service.create(world_id, "erika", "same", "erika_speech_1", understanding_status="clear", meaning_hypotheses=["Autre lecture."])
    assert raised.value.code == "interpretation_key_conflict"


def test_owner_scope_and_digest_do_not_leak_other_character_interpretations(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    service = SocialInterpretationService(conn, clock=clock)
    service.create(world_id, "erika", "private", "erika_speech_1", understanding_status="unresolved")
    with pytest.raises(SocialInterpretationError):
        service.get(world_id, "luna", "private")
    assert service.list(world_id, "luna") == ()
    digest = social_interpretation_digest(conn, world_id)
    assert set(digest) == {"erika"}


def test_creation_and_revision_do_not_change_causal_states_or_canon(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    service = SocialInterpretationService(conn, clock=clock)
    protected = (
        "subjective_belief", "mood_state", "emotion_episode", "relationship_view",
        "situational_permission", "personal_boundary", "subjective_goal", "subjective_intention",
    )
    before = {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in protected}
    before_digest, before_seq = canonical_state_digest(conn, world_id), max_seq(conn, world_id)
    service.create(world_id, "erika", "safe", "erika_speech_1", understanding_status="unresolved")
    after = {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in protected}
    assert after == before
    assert canonical_state_digest(conn, world_id) == before_digest and max_seq(conn, world_id) == before_seq


def test_interpretation_time_is_not_source_time(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    clock.advance(10)
    interpretation = SocialInterpretationService(conn, clock=clock).create(
        world_id, "erika", "later", "erika_speech_1", understanding_status="unresolved"
    )
    assert interpretation["created_at"] > erika_trace["fact_occurred_at"]


def test_trace_does_not_trigger_interpretation_automatically_and_audit_preflight_are_clean(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    assert SocialInterpretationService(conn, clock=clock).list(world_id, "erika") == ()
    assert social_interpretation_audit(conn, world_id) == []
    assert inspect_mvp_preflight(conn).healthy


def test_interpretation_persists_across_reopen_and_remains_append_only(tmp_path):
    db_path = tmp_path / "scc1a.sqlite"
    conn = connect_database(str(db_path))
    assert ensure_schema(conn) == 46
    clock = FakeClock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    _at_salon(conn, world_id, "sophie", "erika", clock=clock)
    scenes = SocialSceneService(conn, clock=clock)
    scenes.open(world_id, "persistence_scene", ("sophie", "erika"))
    scenes.speak(
        world_id, "persistence_scene", "speech_1", "sophie", act_kind="inform",
        content="Sophie exprime une accusation.", recipient_key="erika",
    )
    memory = SubjectiveMemoryService(conn, clock=clock)
    memory.encode_social_speech(world_id, "erika", "erika_speech_1", "persistence_scene", "speech_1")
    state_item = AttentionService(conn, clock=clock).snapshot(world_id, "erika").selected[0]
    memory.encode_attention(world_id, "erika", "erika_observation", state_item)
    service = SocialInterpretationService(conn, clock=clock)
    created = service.create(
        world_id, "erika", "persistent", "erika_speech_1", understanding_status="clear",
        meaning_hypotheses=["Une accusation."], supporting_trace_request_keys=["erika_observation"],
    )
    conn.close()

    reopened = connect_database(str(db_path))
    assert ensure_schema(reopened) == 46
    persisted = SocialInterpretationService(reopened, clock=clock).get(world_id, "erika", "persistent")
    assert persisted == created
    assert social_interpretation_audit(reopened, world_id) == []
    assert inspect_mvp_preflight(reopened).healthy
    with pytest.raises(sqlite3.DatabaseError, match="immutable"):
        reopened.execute("UPDATE social_interpretation SET understanding_status = 'unresolved' WHERE id = 1")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        reopened.execute("DELETE FROM social_interpretation WHERE id = 1")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        reopened.execute("UPDATE social_interpretation_support SET created_at = 'changed' WHERE id = 1")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        reopened.execute("DELETE FROM social_interpretation_support WHERE id = 1")
    reopened.close()
