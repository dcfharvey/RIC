import json

import pytest

from vivarium.social_interpretation_bench import (
    BenchError,
    BenchScenario,
    get_scenarios,
    run_bench,
    run_trial,
)
from vivarium.social_interpretation_provider import DeterministicInterpretationProvider


VALID = {"schema_version": 1, "understanding_status": "ambiguous",
         "meaning_hypotheses": ["A", "B"], "motive_hypotheses": []}


def test_declarative_matrix_and_t0_are_json_serializable():
    report = run_bench(DeterministicInterpretationProvider(VALID), level="T0", trials=1)
    payload = report.as_dict()
    assert len(report.trials) == 30
    assert payload["trial_count"] == 30
    assert payload["structural_valid_rate"] == 1
    assert payload["uncertainty_preserving_rate"] == 1
    json.dumps(payload)


def test_invalid_scenario_and_trial_count_are_rejected_before_trials():
    provider = DeterministicInterpretationProvider(VALID)
    with pytest.raises(BenchError) as unknown:
        run_bench(provider, scenario_ids=("B99",))
    assert unknown.value.code == "invalid_scenario"
    with pytest.raises(BenchError) as count:
        run_bench(provider, trials=0)
    assert count.value.code == "invalid_trial_count"
    with pytest.raises(BenchError) as level:
        run_bench(provider, level="T2")
    assert level.value.code == "t2_not_enabled"


def test_trial_world_is_independent_and_fingerprint_is_reproducible():
    provider = DeterministicInterpretationProvider(VALID)
    scenario = get_scenarios(("B01",))[0]
    first = run_trial(scenario, provider, 1, timer=iter((0.0, 0.125)).__next__)
    second = run_trial(scenario, provider, 2, timer=iter((0.0, 0.125)).__next__)
    assert first.snapshot_fingerprint == second.snapshot_fingerprint
    assert first.causal_effect_absent and second.causal_effect_absent
    assert provider.calls == 2


class ProviderFailure:
    model_id = "fake"
    provider_version = "test"

    def propose(self, snapshot):
        error = ValueError("offline")
        error.code = "llm_unavailable"
        raise error


def test_provider_error_is_reported_without_partial_result():
    result = run_trial(get_scenarios(("B01",))[0], ProviderFailure(), 1)
    assert result.outcome == "provider_error"
    assert result.provider_error_code == "llm_unavailable"
    assert result.snapshot_fingerprint


def test_parse_and_semantic_errors_have_distinct_outcomes():
    parse = run_trial(get_scenarios(("B01",))[0], DeterministicInterpretationProvider("{}"), 1)
    assert parse.outcome == "parse_error"
    invalid = {"schema_version": 1, "understanding_status": "unresolved",
               "meaning_hypotheses": ["not allowed"], "motive_hypotheses": []}
    semantic = run_trial(get_scenarios(("B01",))[0], DeterministicInterpretationProvider(invalid), 1)
    assert semantic.outcome == "semantic_validation_reject"
    assert semantic.validation_error_code == "invalid_interpretation"


def test_t0_never_accepts_a_real_provider():
    with pytest.raises(BenchError) as raised:
        run_bench(object(), level="T0")
    assert raised.value.code == "t0_requires_fake_provider"
