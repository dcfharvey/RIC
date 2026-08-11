import json
import pytest

from vivarium.cognition import LocalLLMSettings
from vivarium.cognition_policy import CognitionCallLimits
from vivarium.db import connect_database
from vivarium.diagnostics import DiagnosticRecorder
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest
from vivarium.scene_turn import LMStudioSceneTurnProvider, SceneTurnContextService, SceneTurnService
from vivarium.scenes import SocialSceneService
from vivarium.scc1c import FixedAdmissionPolicy
from vivarium.social_appraisal_provider import DeterministicAppraisalProvider, SocialAppraisalLLMService
from vivarium.social_cognition_runtime import LiveSocialCognitionService
from vivarium.social_interpretation_provider import DeterministicInterpretationProvider
from vivarium.util import Clock


def _world():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = Clock()
    wid = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    SocialSceneService(conn, clock=clock).open(wid, "diag_scene", ("sophie", "erika"))
    SocialSceneService(conn, clock=clock).speak(wid, "diag_scene", "speech_1", "sophie",
        act_kind="inform", content="Une parole de diagnostic.", recipient_key="erika")
    return conn, wid, clock


def _read(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_recorder_disabled_is_inert_and_enabled_retention_survives_restart(tmp_path):
    path = tmp_path / "diagnostics.jsonl"
    disabled = DiagnosticRecorder(path, enabled=False)
    assert disabled.record("x", {"secret": "no"}) is None and not path.exists()
    recorder = DiagnosticRecorder(path, enabled=True, max_records=3, max_bytes=8192)
    for index in range(6):
        recorder.record("test", {"index": index, "api_token": "must-not-appear"})
    records = _read(path)
    assert len(records) == 3 and [item["payload"]["index"] for item in records] == [3, 4, 5]
    assert "must-not-appear" not in path.read_text(encoding="utf-8")
    restarted = DiagnosticRecorder(path, enabled=True, max_records=3, max_bytes=8192)
    restarted.record("test", {"index": 6})
    assert len(_read(path)) == 3 and _read(path)[-1]["payload"]["index"] == 6


def test_scene_turn_diagnostic_captures_exact_context_and_raw_output(tmp_path, monkeypatch):
    conn, wid, clock = _world()
    path = tmp_path / "diag.jsonl"
    recorder = DiagnosticRecorder(path, enabled=True)
    context = SceneTurnContextService(conn, clock=clock).build(wid, "diag_scene", "sophie")
    raw = '{"schema_version":2,"action":"no_action"}'
    monkeypatch.setattr("vivarium.scene_turn.request_local_model", lambda *args, **kwargs: raw)
    settings = LocalLLMSettings("http://127.0.0.1:1234", "qwen3-14b", None, 1)
    provider = LMStudioSceneTurnProvider(settings, diagnostics=recorder)
    before = canonical_state_digest(conn, wid)
    assert provider.decide(context).action == "no_action"
    after = canonical_state_digest(conn, wid)
    assert before == after
    item = _read(path)[0]
    assert item["kind"] == "scene_turn_provider"
    assert item["payload"]["raw_output"] == raw
    assert item["payload"]["context_wire"] == context.wire()


def test_invalid_appraisal_keeps_snapshot_raw_output_and_rejection_code(tmp_path):
    conn, wid, clock = _world()
    ip = DeterministicInterpretationProvider(
        {"schema_version": 2, "understanding_status": "clear", "meaning_hypotheses": ["Lecture"]})
    LiveSocialCognitionService(conn, ip, clock=clock, admission_policy=FixedAdmissionPolicy("selected")).process_speech(
        wid, "diag_scene", "speech_1", CognitionCallLimits(0, 3600, 20))
    path = tmp_path / "diag.jsonl"
    recorder = DiagnosticRecorder(path, enabled=True)
    bad = {"schema_version": 1, "appraisal_status": "relevant", "qualitative_meaning": "neutral",
           "importance": "low", "bases": ["interpretation:primary"], "candidates": [
               {"candidate_key": "bad", "domain": "affect", "basis_refs": ["interpretation:primary"],
                "justification": "motif invente"}]}
    provider = DeterministicAppraisalProvider(bad, model_id="qwen3-14b")
    with pytest.raises(Exception) as exc:
        SocialAppraisalLLMService(conn, provider, clock=clock, diagnostics=recorder).run(
            wid, "erika", "diag_bad", "live_scc1b_2", provider_turn_id="diag-turn-1")
    assert getattr(exc.value, "code", None) == "invalid_appraisal"
    item = _read(path)[0]
    assert item["kind"] == "scc2a_appraisal"
    assert item["payload"]["raw_output"] == bad
    assert item["payload"]["snapshot_wire"]
    assert item["payload"]["validation_code"] == "invalid_appraisal"
    assert conn.execute("SELECT COUNT(*) FROM social_appraisal").fetchone()[0] == 0


def test_scene_service_diagnostic_link_contains_turn_key_without_world_write(tmp_path):
    conn, wid, clock = _world()
    path = tmp_path / "diag.jsonl"
    recorder = DiagnosticRecorder(path, enabled=True)

    class Provider:
        def decide(self, context):
            return __import__("vivarium.scene_turn", fromlist=["SceneTurnDecision"]).SceneTurnDecision("no_action")

    before = canonical_state_digest(conn, wid)
    result = SceneTurnService(conn, Provider(), clock=clock, diagnostics=recorder).run(
        wid, "diag_scene", "sophie", "turn-1", CognitionCallLimits(0, 3600, 20))
    assert result.decision.action == "no_action"
    assert canonical_state_digest(conn, wid) == before
    result_record = next(item for item in _read(path) if item["kind"] == "scene_turn_result")
    assert result_record["payload"]["turn_key"] == "turn-1"
