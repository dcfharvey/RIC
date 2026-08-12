from datetime import datetime, timedelta, timezone

import pytest

from vivarium.cognition_call_ledger import CognitionCallLedgerService
from vivarium.cognition_policy import CognitionCallLimits, CALL_TRIGGER_SOCIAL_INTERPRETATION
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, scc1c_admission_audit, social_interpretation_audit
from vivarium.scenes import SocialSceneService
from vivarium.scene_turn import SceneTurnDecision
from vivarium.scc1c import FixedAdmissionPolicy
from vivarium.social_cognition_runtime import LiveSocialCognitionService
from vivarium.social_cycle import SocialSceneCycle
from vivarium.social_interpretation_provider import DeterministicInterpretationProvider, SocialInterpretationProviderError
from vivarium.util import to_iso


class Clock:
    def __init__(self):
        self.current = datetime(2026, 8, 10, 12, tzinfo=timezone.utc)

    def now(self):
        return self.current

    def now_iso(self):
        return to_iso(self.current)

    def advance(self, seconds):
        self.current += timedelta(seconds=seconds)


class SpeakingProvider:
    def decide(self, context):
        return SceneTurnDecision("speak", "inform", "Sophie partage une parole.", "erika")


class FlakyInterpretationProvider:
    model_id = "fake-qwen3-14b"
    provider_version = "fake-scc1b-v1"

    def __init__(self):
        self.calls = 0

    def propose(self, snapshot):
        self.calls += 1
        if self.calls == 1:
            raise SocialInterpretationProviderError("provider down", code="provider_unavailable")
        return {"schema_version": 2, "understanding_status": "unresolved", "meaning_hypotheses": []}


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    assert ensure_schema(conn) == 50
    clock = Clock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    scenes = SocialSceneService(conn, clock=clock)
    scenes.open(world_id, "live_scene", ("sophie", "erika", "luna"))
    scenes.speak(
        world_id, "live_scene", "speech_1", "sophie", act_kind="inform",
        content="Sophie partage une parole.", recipient_key="erika",
    )
    yield conn, world_id, clock
    conn.close()


def _service(setup, provider=None, policy=None):
    conn, world_id, clock = setup
    return LiveSocialCognitionService(
        conn,
        provider or DeterministicInterpretationProvider(
            {"schema_version": 2, "understanding_status": "unresolved", "meaning_hypotheses": []},
            model_id="fake-qwen3-14b",
        ),
        clock=clock,
        admission_policy=policy or FixedAdmissionPolicy("selected"),
    )


def test_r1_r3_live_event_encodes_each_owner_and_interprets_selected(setup):
    conn, world_id, clock = setup
    provider = DeterministicInterpretationProvider(
        {"schema_version": 2, "understanding_status": "unresolved", "meaning_hypotheses": []},
        model_id="fake-qwen3-14b",
    )
    outcomes = LiveSocialCognitionService(
        conn, provider, clock=clock, admission_policy=FixedAdmissionPolicy("selected")
    ).process_speech(world_id, "live_scene", "speech_1", CognitionCallLimits(0, 3600, 8))
    assert len(outcomes) == 3
    assert all(item.admission == "selected" and item.technical_status == "interpreted" for item in outcomes)
    assert provider.calls == 3
    assert conn.execute("SELECT COUNT(*) FROM subjective_trace").fetchone()[0] == 3
    assert conn.execute("SELECT COUNT(*) FROM social_interpretation").fetchone()[0] == 3
    assert {row[0] for row in conn.execute("SELECT DISTINCT character_id FROM social_interpretation")}.__len__() == 3


def test_r2_not_selected_stops_before_technical_gate_or_provider(setup):
    conn, world_id, clock = setup
    provider = DeterministicInterpretationProvider(
        {"schema_version": 2, "understanding_status": "unresolved", "meaning_hypotheses": []},
    )
    outcomes = LiveSocialCognitionService(
        conn, provider, clock=clock, admission_policy=FixedAdmissionPolicy("not_selected")
    ).process_speech(world_id, "live_scene", "speech_1", CognitionCallLimits(0, 3600, 8))
    assert all(item.admission == "not_selected" and item.technical_status is None for item in outcomes)
    assert provider.calls == 0
    assert conn.execute("SELECT COUNT(*) FROM cognition_call_admission").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM social_interpretation").fetchone()[0] == 0


def test_r4_only_scene_participants_receive_a_trace(setup):
    conn, world_id, clock = setup
    provider = DeterministicInterpretationProvider(
        {"schema_version": 2, "understanding_status": "unresolved", "meaning_hypotheses": []},
    )
    LiveSocialCognitionService(conn, provider, clock=clock).process_speech(
        world_id, "live_scene", "speech_1", CognitionCallLimits(0, 3600, 8)
    )
    assert conn.execute(
        "SELECT COUNT(*) FROM subjective_trace trace JOIN character ch ON ch.id=trace.character_id "
        "WHERE ch.key='patoune'"
    ).fetchone()[0] == 0


def test_r5_budget_deferred_keeps_selected(setup):
    conn, world_id, clock = setup
    limits = CognitionCallLimits(0, 3600, 1)
    CognitionCallLedgerService(conn, clock=clock).admit(
        world_id, "erika", CALL_TRIGGER_SOCIAL_INTERPRETATION, "preexisting_call", limits
    )
    outcomes = _service(setup).process_speech(world_id, "live_scene", "speech_1", limits)
    erika = next(item for item in outcomes if item.character_key == "erika")
    assert erika.admission == "selected" and erika.technical_status == "deferred"
    assert erika.detail_code == "budget_exhausted"


def test_r6_provider_failure_is_degraded_without_partial_interpretation(setup):
    conn, world_id, clock = setup
    provider = FlakyInterpretationProvider()
    outcomes = LiveSocialCognitionService(
        conn, provider, clock=clock, admission_policy=FixedAdmissionPolicy("selected")
    ).process_speech(world_id, "live_scene", "speech_1", CognitionCallLimits(0, 3600, 8))
    assert sum(item.technical_status == "provider_unavailable" for item in outcomes) == 1
    assert sum(item.technical_status == "interpreted" for item in outcomes) == 2
    assert conn.execute("SELECT COUNT(*) FROM social_interpretation").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM scc1c_attempt WHERE outcome='provider_unavailable'").fetchone()[0] == 1


def test_r8_retry_is_explicit_bounded_and_creates_one_interpretation(setup, monkeypatch):
    conn, world_id, clock = setup
    provider = FlakyInterpretationProvider()
    service = LiveSocialCognitionService(
        conn, provider, clock=clock, admission_policy=FixedAdmissionPolicy("selected")
    )
    service.process_speech(world_id, "live_scene", "speech_1", CognitionCallLimits(0, 3600, 8))
    monkeypatch.setattr("vivarium.social_cognition_runtime.RETRY_DELAY_SECONDS", 0)
    retry = service.retry(world_id, "sophie", "live_trace_speech_1_sophie", CognitionCallLimits(0, 3600, 8))
    assert retry.technical_status == "interpreted"
    assert conn.execute("SELECT COUNT(*) FROM social_interpretation WHERE character_id=(SELECT id FROM character WHERE key='sophie')").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM scc1c_admission WHERE trace_id=(SELECT id FROM subjective_trace WHERE request_key='live_trace_speech_1_sophie')").fetchone()[0] == 1


def test_scc1c_provider_retry_uses_wall_time_when_canonical_clock_is_skewed(setup):
    conn, world_id, clock = setup
    conn.execute(
        "UPDATE canonical_clock SET simulated_now=?, real_updated_at=?, runtime_state='running' WHERE world_id=?",
        ("2026-08-10T08:00:00+00:00", clock.now_iso(), world_id),
    )
    conn.commit()
    provider = FlakyInterpretationProvider()
    service = LiveSocialCognitionService(
        conn, provider, clock=clock, admission_policy=FixedAdmissionPolicy("selected"),
    )
    service.process_speech(world_id, "live_scene", "speech_1", CognitionCallLimits(0, 3600, 8))

    assert service.retry(world_id, "sophie", "live_trace_speech_1_sophie", CognitionCallLimits(0, 3600, 8)).detail_code == "retry_backoff"
    clock.advance(29)
    assert service.retry(world_id, "sophie", "live_trace_speech_1_sophie", CognitionCallLimits(0, 3600, 8)).detail_code == "retry_backoff"
    assert conn.execute("SELECT COUNT(*) FROM scc1c_attempt WHERE outcome='provider_unavailable'").fetchone()[0] == 1

    clock.advance(1)
    recovered = service.retry(world_id, "sophie", "live_trace_speech_1_sophie", CognitionCallLimits(0, 3600, 8))
    assert recovered.technical_status == "interpreted"
    assert conn.execute("SELECT COUNT(*) FROM scc1c_attempt WHERE outcome='interpreted'").fetchone()[0] == 3


def test_due_scc1c_retry_is_not_starved_by_a_due_scc2a_retry(setup):
    conn, world_id, clock = setup

    class FlakyAppraisalProvider:
        model_id = "fake-qwen3-14b"
        provider_version = "fake-scc2a-v1"

        def __init__(self):
            self.calls = 0

        def propose(self, snapshot):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("provider down")
            return {
                "schema_version": 1,
                "appraisal_status": "not_relevant",
                "qualitative_meaning": "neutral",
                "importance": "low",
                "bases": ["interpretation:primary"],
                "candidates": [],
            }

    interpretation_provider = FlakyInterpretationProvider()
    appraisal_provider = FlakyAppraisalProvider()
    service = LiveSocialCognitionService(
        conn, interpretation_provider, clock=clock,
        admission_policy=FixedAdmissionPolicy("selected"),
        appraisal_provider=appraisal_provider,
    )
    service.process_speech(world_id, "live_scene", "speech_1", CognitionCallLimits(0, 3_600, 20))
    assert conn.execute("SELECT COUNT(*) FROM scc1c_attempt WHERE outcome='provider_unavailable'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM scc2a_attempt WHERE outcome='provider_unavailable'").fetchone()[0] == 1

    clock.current += timedelta(seconds=30)
    retried = service.retry_one_pending(world_id, CognitionCallLimits(0, 3_600, 20))

    assert retried is not None and retried.character_key == "sophie"
    assert retried.technical_status == "interpreted"
    assert interpretation_provider.calls == 4
    assert appraisal_provider.calls == 3  # nouvel appraisal de Sophie, pas retry d'Erika
    assert conn.execute(
        "SELECT COUNT(*) FROM scc2a_attempt a JOIN character c ON c.id=a.character_id "
        "WHERE c.key='erika'"
    ).fetchone()[0] == 1


def test_r9_idempotent_duplicate_event_does_not_call_provider_twice(setup):
    conn, world_id, clock = setup
    provider = DeterministicInterpretationProvider(
        {"schema_version": 2, "understanding_status": "unresolved", "meaning_hypotheses": []},
    )
    service = LiveSocialCognitionService(conn, provider, clock=clock, admission_policy=FixedAdmissionPolicy("selected"))
    service.process_speech(world_id, "live_scene", "speech_1", CognitionCallLimits(0, 3600, 8))
    service.process_speech(world_id, "live_scene", "speech_1", CognitionCallLimits(0, 3600, 8))
    assert provider.calls == 3
    assert conn.execute("SELECT COUNT(*) FROM scc1c_admission").fetchone()[0] == 3
    assert conn.execute("SELECT COUNT(*) FROM social_interpretation").fetchone()[0] == 3


def test_r10_restart_does_not_create_admissions_from_old_traces(setup):
    conn, world_id, clock = setup
    provider = DeterministicInterpretationProvider(
        {"schema_version": 2, "understanding_status": "unresolved", "meaning_hypotheses": []},
    )
    service = LiveSocialCognitionService(conn, provider, clock=clock, admission_policy=FixedAdmissionPolicy("not_selected"))
    service.process_speech(world_id, "live_scene", "speech_1", CognitionCallLimits(0, 3600, 8))
    reopened = LiveSocialCognitionService(conn, provider, clock=clock, admission_policy=FixedAdmissionPolicy("selected"))
    assert reopened.retry_one_pending(world_id, CognitionCallLimits(0, 3600, 8)) is None
    assert conn.execute("SELECT COUNT(*) FROM scc1c_admission").fetchone()[0] == 3


def test_r11_r12_audits_and_causal_state_remain_isolated(setup):
    conn, world_id, clock = setup
    before = canonical_state_digest(conn, world_id)
    service = _service(setup)
    service.process_speech(world_id, "live_scene", "speech_1", CognitionCallLimits(0, 3600, 8))
    assert canonical_state_digest(conn, world_id) == before
    assert social_interpretation_audit(conn, world_id) == []
    assert scc1c_admission_audit(conn, world_id) == []
    for table in ("subjective_belief", "mood_state", "emotion_episode", "relationship_view", "situational_permission", "personal_boundary", "subjective_goal", "subjective_intention"):
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_r14_social_cycle_calls_live_pipeline_after_accepted_speech(setup):
    conn, world_id, clock = setup
    provider = DeterministicInterpretationProvider(
        {"schema_version": 2, "understanding_status": "unresolved", "meaning_hypotheses": []},
    )
    outcome = SocialSceneCycle(
        conn, SpeakingProvider(), clock=clock, interpretation_provider=provider,
        admission_policy=FixedAdmissionPolicy("selected"),
    ).tick(world_id, CognitionCallLimits(0, 3600, 8))
    assert outcome.turn is not None and outcome.turn.speech is not None
    assert len(outcome.cognition) == 3
    assert provider.calls == 3
