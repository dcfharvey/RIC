from vivarium.cognition import CognitionDecision, LocalLLMSettings
from vivarium.scene_turn import SceneTurnDecision
from vivarium.scene_turn_smoke import run_local_scene_turn_smoke


def test_scene_smoke_is_jetable_and_reports_a_no_action(monkeypatch):
    class Provider:
        def __init__(self, settings):
            self.settings = settings

        def decide(self, context):
            return SceneTurnDecision("no_action")

    monkeypatch.setattr("vivarium.scene_turn_smoke.LMStudioSceneTurnProvider", Provider)
    report = run_local_scene_turn_smoke(LocalLLMSettings("http://127.0.0.1:1234", "gemma-local", None, 12))

    assert report.healthy and report.decision == "no_action"
    assert report.content is None and report.provider_error_code is None
