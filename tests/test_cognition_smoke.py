from vivarium.cognition import CognitionDecision, LocalLLMSettings
from vivarium.cognition_smoke import run_local_cognition_smoke


class Provider:
    def __init__(self, settings): pass
    def decide(self, context): return CognitionDecision("traverse", "porte_entree", "salon")


def test_smoke_runs_in_memory_and_routes_a_valid_decision(monkeypatch):
    monkeypatch.setattr("vivarium.cognition_smoke.LMStudioProvider", Provider)

    report = run_local_cognition_smoke(
        LocalLLMSettings("http://127.0.0.1:1234", "gemma-local", None, 12)
    )

    assert report.healthy
    assert report.decision == "traverse"
    assert report.validation_status == "accepted"
    assert report.event_type == "character_moved"
