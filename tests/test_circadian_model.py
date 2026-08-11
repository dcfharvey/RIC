"""Falsifications déterministes du noyau circadien inactif."""

import pytest

from vivarium.circadian_model import (
    CircadianModelError,
    RegulationInput,
    RegulationState,
    StabilityGateState,
    advance_regulation,
    calibration_profiles,
    effective_light_drive,
    sleep_propensity,
    stability_consequence,
    wake_stability,
)


@pytest.fixture
def human():
    return calibration_profiles()["human_reference_candidate.v1"]


def test_homeostasis_is_segment_invariant_and_rest_is_awake(human):
    initial = RegulationState(0.4, 0.2, 0.5)
    wake = RegulationInput("wake", 0, 100_000)
    one = advance_regulation(initial, wake, 6 * 3_600, human)
    split = advance_regulation(advance_regulation(initial, wake, 2 * 3_600, human), wake, 4 * 3_600, human)
    assert one.homeostatic_load == pytest.approx(split.homeostatic_load)
    assert one.circadian_phase == pytest.approx(split.circadian_phase)
    rest = advance_regulation(initial, RegulationInput("rest", 0, 100_000), 3 * 3_600, human)
    sleep = advance_regulation(initial, RegulationInput("sleep", 0, 100_000), 3 * 3_600, human)
    assert rest.homeostatic_load > initial.homeostatic_load
    assert sleep.homeostatic_load < initial.homeostatic_load


def test_zero_duration_is_an_offline_freeze(human):
    state = RegulationState(0.4, 0.2, 0.5)
    assert advance_regulation(state, RegulationInput("wake", 90_000, 100_000), 0, human) == state


def test_light_is_phase_dependent_saturating_and_occluded_during_sleep(human):
    source = RegulationInput("wake", 100_000, 100_000)
    early_start = RegulationState(0.5, 0.125, 0.5)
    late_start = RegulationState(0.5, 0.625, 0.5)
    early = advance_regulation(early_start, source, 2 * 3_600, human)
    late = advance_regulation(late_start, source, 2 * 3_600, human)
    early_dark = advance_regulation(early_start, RegulationInput("wake", 0, 100_000), 2 * 3_600, human)
    late_dark = advance_regulation(late_start, RegulationInput("wake", 0, 100_000), 2 * 3_600, human)
    assert (early.circadian_phase - early_dark.circadian_phase) * (late.circadian_phase - late_dark.circadian_phase) < 0
    dim = effective_light_drive(RegulationInput("wake", 30_000, 100_000), human)
    bright = effective_light_drive(source, human)
    assert 0 < dim < bright <= 1
    assert effective_light_drive(RegulationInput("sleep", 100_000, 100_000, occluded=True), human) < bright


def test_capacity_is_independent_from_sleep_propensity_and_rest_recovers_only_capacity(human):
    rested = RegulationState(0.7, 0.3, 0.1)
    capable = RegulationState(0.7, 0.3, 0.9)
    assert sleep_propensity(rested, human).sleep_propensity == sleep_propensity(capable, human).sleep_propensity
    rest = advance_regulation(rested, RegulationInput("rest", 0, 100_000), 2 * 3_600, human)
    assert rest.physical_capacity > rested.physical_capacity
    assert rest.homeostatic_load > rested.homeostatic_load


def test_two_propensity_families_are_available_for_bench_comparison_not_runtime_selection(human):
    state = RegulationState(0.50, 0.25, 0.8)
    additive = sleep_propensity(state, human, family="additive")
    modulated = sleep_propensity(state, human, family="threshold_modulated")
    assert additive.family == "additive" and modulated.family == "threshold_modulated"
    assert additive.sleep_propensity != modulated.sleep_propensity


def test_stability_uses_hysteresis_bounded_stimulation_and_one_interruption_per_activity(human):
    state = RegulationState(0.98, 0.5, 0.9)
    unstable = wake_stability(state, RegulationInput("wake", 0, 100_000), human)
    stimulated = wake_stability(state, RegulationInput("wake", 0, 100_000, stimulation=1.0), human)
    assert unstable.band == "critical"
    assert 0 < stimulated.instability < unstable.instability
    first = stability_consequence(unstable, activity_id="a1", requires_sustained_wakefulness=True, gate_state=StabilityGateState())
    repeat = stability_consequence(unstable, activity_id="a1", requires_sustained_wakefulness=True, gate_state=first.next_gate_state)
    assert first.should_interrupt and not repeat.should_interrupt


def test_feline_candidate_is_explicitly_a_calibration_hypothesis_not_a_named_character_rule():
    feline = calibration_profiles()["generic_feline_hypothesis.v1"]
    assert feline.evidence_class == "generic_feline"
    assert "patoune" not in feline.profile_key


def test_invalid_profile_cannot_allow_unbounded_stimulation():
    profile = calibration_profiles()["human_reference_candidate.v1"]
    with pytest.raises(CircadianModelError):
        type(profile)(**{**profile.__dict__, "max_stimulation_relief": 1.0})
