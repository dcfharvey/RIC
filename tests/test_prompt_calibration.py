from vivarium.prompt_calibration import (
    BASELINE_SYSTEM_PROMPT,
    CALIBRATION_PARAGRAPH,
    CONDITIONS,
    CONTROL_KEYS,
    PLANNED_CALLS,
    PromptCalibrationProvider,
    system_prompt,
)
from vivarium.social_interpretation_provider import LMStudioSocialInterpretationProvider


def test_a_is_the_frozen_production_prompt_and_b_only_appends_calibration():
    assert system_prompt(CONDITIONS[0]) == BASELINE_SYSTEM_PROMPT
    assert system_prompt(CONDITIONS[1]) == BASELINE_SYSTEM_PROMPT + "\n\n" + CALIBRATION_PARAGRAPH
    assert "motive_hypotheses" not in CALIBRATION_PARAGRAPH
    assert "puzzle" not in CALIBRATION_PARAGRAPH.lower()
    assert "sculpture" not in CALIBRATION_PARAGRAPH.lower()
    assert "dossier" not in CALIBRATION_PARAGRAPH.lower()


def test_a_matches_the_current_production_provider_prompt(monkeypatch):
    captured = {}

    def fake_request(settings, *, system_prompt, input_text):
        captured["system_prompt"] = system_prompt
        return {"schema_version": 1, "understanding_status": "clear", "meaning_hypotheses": ["x"], "motive_hypotheses": []}

    monkeypatch.setattr("vivarium.social_interpretation_provider.request_local_model", fake_request)
    from vivarium.cognition import LocalLLMSettings
    provider = LMStudioSocialInterpretationProvider(LocalLLMSettings("http://localhost:1234", "model", None, 10))
    provider.propose(type("Snapshot", (), {"wire": '{"same":true}'})())
    assert captured["system_prompt"] == BASELINE_SYSTEM_PROMPT


def test_request_contract_changes_only_system_prompt(monkeypatch):
    calls = []

    def fake_request(settings, *, system_prompt, input_text):
        calls.append((settings, system_prompt, input_text))
        return {"schema_version": 1, "understanding_status": "clear", "meaning_hypotheses": ["x"], "motive_hypotheses": []}

    monkeypatch.setattr("vivarium.prompt_calibration.request_local_model", fake_request)
    class Snapshot:
        wire = '{"same":true}'
    from vivarium.cognition import LocalLLMSettings
    settings = LocalLLMSettings("http://localhost:1234", "model", None, 10)
    PromptCalibrationProvider(settings, "A_BASELINE").propose(Snapshot())
    PromptCalibrationProvider(settings, "B_CALIBRATED").propose(Snapshot())
    assert calls[0][0] == calls[1][0]
    assert calls[0][2] == calls[1][2]
    assert calls[0][1] == BASELINE_SYSTEM_PROMPT
    assert calls[1][1] == BASELINE_SYSTEM_PROMPT + "\n\n" + CALIBRATION_PARAGRAPH


def test_preregistered_call_count_and_controls_are_fixed():
    assert len(CONTROL_KEYS) == 13
    assert PLANNED_CALLS == 186
