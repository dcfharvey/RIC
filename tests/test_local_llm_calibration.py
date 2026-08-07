import pytest

from vivarium.cognition import CognitionDecision, CognitionError
from vivarium.local_llm_calibration import (
    LocalCalibrationError,
    run_local_cognition_calibration,
)


class Provider:
    def __init__(self, decisions):
        self.decisions = iter(decisions)
        self.contexts = []

    def decide(self, context):
        self.contexts.append(context)
        return next(self.decisions)


def test_local_calibration_rebuilds_an_independent_perceived_turn_each_time():
    provider = Provider((
        CognitionDecision("no_action"),
        CognitionDecision("traverse", "porte_entree", "entree_exterieure"),
        CognitionDecision("no_action"),
    ))
    readings = iter((10.0, 10.011, 20.0, 20.023, 30.0, 30.017))

    report = run_local_cognition_calibration(
        provider, "gemma-local", trials=3, timer=lambda: next(readings)
    )

    assert report.healthy
    assert report.decision_counts == {"no_action": 2, "traverse": 1}
    assert report.outcome_counts == {"routed": 3}
    assert [trial.elapsed_ms for trial in report.trials] == [11, 23, 17]
    assert report.median_elapsed_ms == 17
    assert len(provider.contexts) == 3
    assert all(context.character_key == "sophie" for context in provider.contexts)
    assert all(any(event["event_seq"] > 0 for event in context.direct_events) for context in provider.contexts)
    assert provider.contexts[0].wire() == provider.contexts[1].wire() == provider.contexts[2].wire()


def test_local_calibration_reports_provider_failure_without_escaping_the_bench():
    class Offline:
        def decide(self, context):
            raise CognitionError("hors ligne", code="llm_unavailable")

    report = run_local_cognition_calibration(Offline(), "gemma-local", trials=1)

    assert not report.healthy
    assert report.trials[0].outcome == "provider_error"
    assert report.trials[0].provider_error_code == "llm_unavailable"


@pytest.mark.parametrize("trials", (0, 21, True, "3"))
def test_local_calibration_refuses_invalid_bounds_before_a_provider_call(trials):
    class Never:
        def decide(self, context):
            raise AssertionError("le fournisseur ne doit pas être appelé")

    with pytest.raises(LocalCalibrationError) as raised:
        run_local_cognition_calibration(Never(), "gemma-local", trials=trials)
    assert raised.value.code == "invalid_local_calibration"
