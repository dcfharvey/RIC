import json

import pytest

from vivarium.attention import AttentionService
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.social_interpretation import SocialInterpretationError
from vivarium.social_interpretation_provider import (
    DeterministicInterpretationProvider,
    SocialInterpretationContextBuilder,
    SocialInterpretationLLMService,
    SocialInterpretationProviderError,
    parse_provider_proposal,
)
from vivarium.subjective_memory import SubjectiveMemoryService

from test_social_interpretation import FakeClock, _social_source


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    assert ensure_schema(conn) == 39
    clock = FakeClock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    yield conn, world_id, clock
    conn.close()


def test_snapshot_uses_subjective_payload_and_is_closed(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    snapshot = SocialInterpretationContextBuilder(conn).build(world_id, "erika", "erika_speech_1")
    assert snapshot.data["primary_trace"]["payload"] == erika_trace["payload"]
    before = snapshot.wire, snapshot.fingerprint
    AttentionService(conn, clock=clock).snapshot(world_id, "erika")
    assert (snapshot.wire, snapshot.fingerprint) == before


def test_snapshot_owner_scope_and_explicit_selection(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    item = AttentionService(conn, clock=clock).snapshot(world_id, "erika").selected[0]
    memory.encode_attention(world_id, "erika", "erika_state", item)
    snapshot = SocialInterpretationContextBuilder(conn).build(world_id, "erika", "erika_speech_1", selected_trace_request_keys=("erika_state",))
    assert [row["request_key"] for row in snapshot.data["selected_context_traces"]] == ["erika_state"]
    with pytest.raises(SocialInterpretationProviderError) as raised:
        SocialInterpretationContextBuilder(conn).build(world_id, "erika", "erika_speech_1", selected_trace_request_keys=("luna_speech_1",))
    assert raised.value.code == "context_trace_not_accessible"


def test_provider_output_is_strict_and_service_validates(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    bad = DeterministicInterpretationProvider(json.dumps({"schema_version": 1, "understanding_status": "clear", "meaning_hypotheses": ["x"], "motive_hypotheses": [], "actual_intent": "x"}))
    with pytest.raises(SocialInterpretationProviderError):
        SocialInterpretationLLMService(conn, bad).run(world_id, "erika", "bad", "erika_speech_1")
    assert conn.execute("SELECT COUNT(*) FROM social_interpretation").fetchone()[0] == 0


def test_llm_proposal_persists_provenance_and_has_no_consequences(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    before = canonical_state_digest(conn, world_id), max_seq(conn, world_id)
    fake = DeterministicInterpretationProvider({"schema_version": 1, "understanding_status": "clear", "meaning_hypotheses": ["Une lecture."], "motive_hypotheses": []})
    result = SocialInterpretationLLMService(conn, fake).run(world_id, "erika", "llm_reading", "erika_speech_1")
    assert result["origin_kind"] == "llm" and result["snapshot_fingerprint"]
    assert result["model_id"] is None and result["provider_version"] == "scc1b1-native-v1"
    assert (canonical_state_digest(conn, world_id), max_seq(conn, world_id)) == before


def test_llm_replay_and_conflict_do_not_call_provider(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    fake = DeterministicInterpretationProvider({"schema_version": 1, "understanding_status": "unresolved", "meaning_hypotheses": [], "motive_hypotheses": []})
    service = SocialInterpretationLLMService(conn, fake)
    service.run(world_id, "erika", "same", "erika_speech_1")
    service.run(world_id, "erika", "same", "erika_speech_1")
    assert fake.calls == 1
    with pytest.raises(SocialInterpretationError) as raised:
        service.run(world_id, "erika", "same", "erika_speech_1", provider_turn_id="different")
    assert raised.value.code == "interpretation_key_conflict" and fake.calls == 1


def test_llm_revision_keeps_lineage_and_support_audited(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    item = AttentionService(conn, clock=clock).snapshot(world_id, "erika").selected[0]
    memory.encode_attention(world_id, "erika", "clarification", item)
    first_provider = DeterministicInterpretationProvider({"schema_version": 1, "understanding_status": "ambiguous", "meaning_hypotheses": ["A", "B"], "motive_hypotheses": []})
    SocialInterpretationLLMService(conn, first_provider).run(world_id, "erika", "first", "erika_speech_1")
    second_provider = DeterministicInterpretationProvider({"schema_version": 1, "understanding_status": "clear", "meaning_hypotheses": ["B"], "motive_hypotheses": []})
    revised = SocialInterpretationLLMService(conn, second_provider).run(world_id, "erika", "second", "erika_speech_1", revision_of_key="first", selected_trace_request_keys=("clarification",))
    assert revised["revision_of_key"] == "first"
    assert revised["supporting_trace_request_keys"] == ("clarification",)


def test_invalid_semantic_combination_is_not_repaired_or_persisted(setup):
    conn, world_id, clock, scenes, memory, erika_trace, luna_trace = _social_source(setup)
    fake = DeterministicInterpretationProvider({"schema_version": 1, "understanding_status": "unresolved", "meaning_hypotheses": ["invented"], "motive_hypotheses": []})
    with pytest.raises(SocialInterpretationError) as raised:
        SocialInterpretationLLMService(conn, fake).run(world_id, "erika", "invalid", "erika_speech_1")
    assert raised.value.code == "invalid_interpretation"
    assert conn.execute("SELECT COUNT(*) FROM social_interpretation").fetchone()[0] == 0


def test_parser_rejects_non_object_and_unknown_fields():
    with pytest.raises(SocialInterpretationProviderError):
        parse_provider_proposal("not json")
