import json
from datetime import datetime, timezone

import pytest

from vivarium.cognition import CognitionDecision, CognitionError, CognitionProviderTrace
from vivarium.cognition_policy import CognitionCallLimits
from vivarium.cognitive_flow import CognitiveFlowScheduler
from vivarium.cognition_router import CognitionCallRouter, CognitionCallRouterError
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.traversal import TraversalEngine
from vivarium.util import to_iso
from vivarium.world import WorldEngine


class Clock:
    def now(self): return datetime(2026, 8, 6, 12, tzinfo=timezone.utc)
    def now_iso(self): return to_iso(self.now())


class Provider:
    def __init__(self, decision): self.decision, self.calls, self.context = decision, 0, None
    def decide(self, context): self.calls += 1; self.context = context; return self.decision


class TracedProvider:
    def __init__(self, decision):
        self.decision = decision
        self.last_call = None

    def decide(self, context):
        self.last_call = CognitionProviderTrace(
            model_id="test-model",
            request_body={
                "model": "test-model",
                "system_prompt": "system",
                "input": context.wire(),
                "temperature": 0.2,
                "store": False,
            },
            raw_response_body='{"output":[{"type":"message","content":"raw"}]}',
            raw_message='{"schema_version":8,"action":"no_action"}',
            parsed_response={"schema_version": 8, "action": "no_action"},
            status="completed",
            duration_ms=3,
        )
        return self.decision


@pytest.fixture
def setup():
    conn = connect_database(":memory:"); ensure_schema(conn); clock = Clock()
    wid = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    yield conn, wid, clock
    conn.close()


def direct_event_for_sophie(conn, wid, clock):
    TraversalEngine(conn, clock=clock).traverse_character(wid, "sophie", "porte_entree", "salon")
    return f"event_{max_seq(conn, wid)}"


def test_routed_perceived_event_is_admitted_then_calls_provider_once(setup):
    conn, wid, clock = setup
    source_key = direct_event_for_sophie(conn, wid, clock)
    provider = Provider(CognitionDecision("no_action"))
    router = CognitionCallRouter(conn, provider, clock=clock)
    result = router.run(wid, "sophie", "direct_event", source_key, "proposal_42", CognitionCallLimits(0, 3_600, 2))

    assert result.attempted and result.turn and result.turn.decision.action == "no_action"
    assert result.provider_error_code is None and provider.calls == 1
    assert any(item["event_seq"] == int(source_key.removeprefix("event_")) for item in result.turn.context.direct_events)


def test_replay_is_stopped_before_provider_and_unseen_event_is_refused(setup):
    conn, wid, clock = setup
    source_key = direct_event_for_sophie(conn, wid, clock)
    provider = Provider(CognitionDecision("no_action"))
    router = CognitionCallRouter(conn, provider, clock=clock)
    limits = CognitionCallLimits(0, 3_600, 2)

    assert router.run(wid, "sophie", "direct_event", source_key, "proposal_42", limits).attempted
    replay = router.run(wid, "sophie", "direct_event", source_key, "proposal_43", limits)
    assert not replay.attempted and replay.admission.verdict.reason_code == "duplicate_call" and provider.calls == 1

    TraversalEngine(conn, clock=clock).traverse_character(wid, "erika", "porte_entree", "salon")
    with pytest.raises(CognitionCallRouterError) as raised:
        router.run(wid, "sophie", "direct_event", f"event_{max_seq(conn, wid)}", "proposal_44", limits)
    assert raised.value.code == "cognition_call_source_not_perceived"


def test_initial_arrival_is_sourced_once_and_exposes_only_shared_context(setup):
    conn, wid, clock = setup
    source_seq = conn.execute(
        "SELECT seq FROM canonical_event WHERE world_id = ? AND event_type = 'world_initial_context_set'",
        (wid,),
    ).fetchone()[0]
    provider = Provider(CognitionDecision("traverse", "porte_entree", "salon"))
    router = CognitionCallRouter(conn, provider, clock=clock)
    limits = CognitionCallLimits(0, 3_600, 2)

    result = router.run(wid, "sophie", "initial_arrival", f"arrival_{source_seq}", "arrival_sophie", limits)

    assert result.attempted and result.turn is not None
    assert result.turn.validation is not None and result.turn.validation.status == "accepted"
    assert result.turn.context.decision_cue["trigger"] == "initial_arrival"
    assert result.turn.context.decision_cue["initial_shared_facts"]["residency"]["voluntary"] is True
    replay = router.run(wid, "sophie", "initial_arrival", f"arrival_{source_seq}", "arrival_sophie_retry", limits)
    assert not replay.attempted and replay.admission.verdict.reason_code == "duplicate_call"
    assert provider.calls == 1


def test_initial_arrival_is_refused_after_a_real_departure(setup):
    conn, wid, clock = setup
    source_seq = conn.execute(
        "SELECT seq FROM canonical_event WHERE world_id = ? AND event_type = 'world_initial_context_set'",
        (wid,),
    ).fetchone()[0]
    TraversalEngine(conn, clock=clock).traverse_character(wid, "sophie", "porte_entree", "salon")

    with pytest.raises(CognitionCallRouterError) as raised:
        CognitionCallRouter(conn, Provider(CognitionDecision("no_action")), clock=clock).run(
            wid, "sophie", "initial_arrival", f"arrival_{source_seq}", "arrival_sophie", CognitionCallLimits(0, 3_600, 2)
        )
    assert raised.value.code == "cognition_call_source_not_available"


def test_provider_failure_is_explicit_after_admission_but_cannot_mutate_canon(setup):
    conn, wid, clock = setup
    source_key = direct_event_for_sophie(conn, wid, clock)

    class OfflineProvider:
        def decide(self, context): raise CognitionError("hors ligne", code="llm_unavailable")

    before_state, before_seq = canonical_state_digest(conn, wid), max_seq(conn, wid)
    result = CognitionCallRouter(conn, OfflineProvider(), clock=clock).run(
        wid, "sophie", "direct_event", source_key, "proposal_42", CognitionCallLimits(0, 3_600, 2)
    )
    assert result.attempted and result.turn is None and result.provider_error_code == "llm_unavailable"
    assert canonical_state_digest(conn, wid) == before_state and max_seq(conn, wid) == before_seq


def test_planned_reflection_requires_a_current_idle_source_before_admission(setup):
    conn, wid, clock = setup
    provider = Provider(CognitionDecision("no_action"))
    with pytest.raises(CognitionCallRouterError) as raised:
        CognitionCallRouter(conn, provider, clock=clock).run(
            wid, "sophie", "planned_reflection", "plan_42", "proposal_42", CognitionCallLimits(0, 3_600, 2)
        )
    assert raised.value.code == "invalid_cognition_call_source"
    assert conn.execute("SELECT COUNT(*) FROM cognition_call_admission").fetchone()[0] == 0


def test_flow_observation_reconstructs_context_raw_output_and_accepted_consequence(setup):
    conn, wid, clock = setup
    source_seq = conn.execute(
        "SELECT seq FROM canonical_event WHERE world_id = ? "
        "AND event_type = 'world_initial_context_set'",
        (wid,),
    ).fetchone()[0]
    source_key = f"arrival_{source_seq}"
    provider = TracedProvider(CognitionDecision("traverse", "porte_entree", "salon"))
    router = CognitionCallRouter(
        conn, provider, clock=clock, flow_scheduler=CognitiveFlowScheduler()
    )
    result = router.run(
        wid, "sophie", "initial_arrival", source_key, "proposal_observed",
        CognitionCallLimits(0, 3_600, None),
    )

    assert result.attempted and result.turn is not None
    row = conn.execute(
        "SELECT state, details_json FROM cognition_flow_event "
        "WHERE world_id = ? AND opportunity_id = ? ORDER BY id DESC LIMIT 1",
        (wid, f"sophie:initial_arrival:{source_key}"),
    ).fetchone()
    details = json.loads(row["details_json"])
    assert row["state"] == "completed"
    assert details["provider_call_attempted"] is True
    assert details["canonical_input"]["source_key"] == source_key
    assert details["llm_context"]["wire"]["character"]["key"] == "sophie"
    assert details["options_presented"]["traversals"] == details["llm_context"]["wire"]["allowed_traversals"]
    assert details["provider"]["raw_message"] != details["interpretation"]["decision"]
    assert details["provider"]["model_id"] == "test-model"
    assert details["provider"]["generation_parameters"]["temperature"] == 0.2
    assert details["engine_validation"]["status"] == "accepted"
    assert details["canonical_consequence"][0]["event_type"] == "character_moved"


def test_flow_observation_keeps_no_action_distinct_from_raw_provider_output(setup):
    conn, wid, clock = setup
    source_key = direct_event_for_sophie(conn, wid, clock)
    provider = TracedProvider(CognitionDecision("no_action"))
    result = CognitionCallRouter(
        conn, provider, clock=clock, flow_scheduler=CognitiveFlowScheduler()
    ).run(
        wid, "sophie", "direct_event", source_key, "proposal_no_action_observed",
        CognitionCallLimits(0, 3_600, None),
    )

    assert result.turn is not None and result.turn.validation is None
    row = conn.execute(
        "SELECT details_json FROM cognition_flow_event "
        "WHERE world_id = ? AND opportunity_id = ? ORDER BY id DESC LIMIT 1",
        (wid, f"sophie:direct_event:{source_key}"),
    ).fetchone()
    details = json.loads(row["details_json"])
    assert details["interpretation"]["status"] == "no_action"
    assert details["interpretation"]["decision"]["action"] == "no_action"
    assert details["engine_validation"] is None
    assert details["canonical_consequence"] == []
    assert details["provider"]["raw_message"]


def test_flow_observation_preserves_refused_proposal_reason(setup):
    conn, wid, clock = setup
    source_key = direct_event_for_sophie(conn, wid, clock)
    provider = TracedProvider(CognitionDecision("traverse", "porte_patio", "cour"))
    result = CognitionCallRouter(
        conn, provider, clock=clock, flow_scheduler=CognitiveFlowScheduler()
    ).run(
        wid, "sophie", "direct_event", source_key, "proposal_refused_observed",
        CognitionCallLimits(0, 3_600, None),
    )

    assert result.turn is None and result.provider_error_code == "llm_action_not_perceived"
    row = conn.execute(
        "SELECT state, reason_code, details_json FROM cognition_flow_event "
        "WHERE world_id = ? AND opportunity_id = ? ORDER BY id DESC LIMIT 1",
        (wid, f"sophie:direct_event:{source_key}"),
    ).fetchone()
    details = json.loads(row["details_json"])
    assert row["state"] == "provider_error"
    assert row["reason_code"] == "llm_action_not_perceived"
    assert details["provider_call_attempted"] is True
    assert details["provider"]["raw_message"]
    assert details["interpretation"]["error_code"] == "llm_action_not_perceived"
    assert details["engine_validation"] is None


def test_flow_observation_preserves_engine_refusal_and_is_passive(setup):
    conn, wid, clock = setup
    source_seq = conn.execute(
        "SELECT seq FROM canonical_event WHERE world_id = ? "
        "AND event_type = 'world_initial_context_set'",
        (wid,),
    ).fetchone()[0]
    source_key = f"arrival_{source_seq}"
    before_digest, before_seq = canonical_state_digest(conn, wid), max_seq(conn, wid)

    class StaleTracedProvider(TracedProvider):
        def decide(self, context):
            super().decide(context)
            option = context.allowed_traversals[0]
            self.decision = CognitionDecision(
                "traverse", option["connector_key"], option["target_location_key"],
            )
            WorldEngine(conn, clock=clock).rename_world(wid, "Concurrent change")
            return self.decision

    provider = StaleTracedProvider(CognitionDecision("no_action"))
    result = CognitionCallRouter(
        conn, provider, clock=clock, flow_scheduler=CognitiveFlowScheduler()
    ).run(
        wid, "sophie", "initial_arrival", source_key, "proposal_stale_observed",
        CognitionCallLimits(0, 3_600, None),
    )

    assert result.turn is not None
    assert result.turn.validation is not None
    assert result.turn.validation.status == "refused"
    assert result.turn.validation.reason_code == "stale_decision_context"
    assert canonical_state_digest(conn, wid) != before_digest
    assert max_seq(conn, wid) > before_seq
    row = conn.execute(
        "SELECT state, details_json FROM cognition_flow_event "
        "WHERE world_id = ? AND opportunity_id = ? ORDER BY id DESC LIMIT 1",
        (wid, f"sophie:initial_arrival:{source_key}"),
    ).fetchone()
    details = json.loads(row["details_json"])
    assert row["state"] == "stale"
    assert details["engine_validation"] == {
        "proposal_id": "proposal_stale_observed",
        "status": "refused",
        "reason_code": "stale_decision_context",
    }
    assert details["canonical_consequence"] == []
    assert details["provider"]["raw_message"]
