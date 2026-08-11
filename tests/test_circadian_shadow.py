"""Falsifications du lot 4 : compatibilité et shadow sans cutover."""

from dataclasses import replace

from vivarium.circadian_model import (
    RegulationInput,
    RegulationState,
    advance_regulation,
    calibration_profiles,
    sleep_propensity,
    wake_stability,
)
from vivarium.circadian_shadow import (
    ArbitrationOption,
    SleepMotiveProjection,
    SyntheticActivityEngine,
    VoluntaryArbitrationFrame,
    arbitrate_voluntary,
    audit_legacy_consumers,
    sleep_motive_projection,
    wake_stability_eligibility,
)


def test_legacy_audit_is_exhaustive_and_declares_coordinated_switches():
    report = audit_legacy_consumers()
    assert report.complete
    assert {group.key for group in report.cutover_groups} == {
        "behavioral_cutover",
        "physical_capacity_cutover",
        "observability_cutover",
        "legacy_preservation",
    }
    behavioral = next(group for group in report.cutover_groups if group.key == "behavioral_cutover")
    assert "DecisionPolicy" in behavioral.switches
    assert "ActivityEngine" in behavioral.switches


def test_legacy_audit_discovers_unlisted_composed_identifiers(tmp_path):
    source_root = tmp_path / "src" / "vivarium"
    source_root.mkdir(parents=True)
    (source_root / "forgotten_consumer.py").write_text(
        "repos_rate = -60\nenergie_rate = -50\nCRIT_REPOS = 100\nSLEEP_ENERGIE_TARGET = 95\n",
        encoding="utf-8",
    )
    (source_root / "unrelated.py").write_text("repose = 'verb'\n", encoding="utf-8")

    report = audit_legacy_consumers(tmp_path)

    assert "src/vivarium/forgotten_consumer.py" in report.unlisted_hits
    assert "src/vivarium/unrelated.py" not in report.unlisted_hits


def test_p_never_generates_sleep_motive_and_repos_energie_are_not_inputs():
    parameters = calibration_profiles()["human_reference_candidate.v1"]
    low_capacity = RegulationState(0.75, 0.5, 0.05)
    high_capacity = replace(low_capacity, physical_capacity=0.95)
    low = sleep_propensity(low_capacity, parameters)
    high = sleep_propensity(high_capacity, parameters)
    assert low == high
    assert SleepMotiveProjection.from_propensity(low) == SleepMotiveProjection.from_propensity(high)
    assert sleep_motive_projection(low_capacity, parameters) == sleep_motive_projection(high_capacity, parameters)


def test_each_side_can_win_without_legacy_category_priority():
    motive = SleepMotiveProjection("sleep_regulation", "sleep", 0.80, "synthetic")
    intention = ArbitrationOption("finish_report", "intention", "work", 0.90)
    assert arbitrate_voluntary(
        VoluntaryArbitrationFrame(active_intention=intention, sleep_motive=motive)
    ).winner_kind == "intention"

    stronger_motive = SleepMotiveProjection("sleep_regulation", "sleep", 0.95, "synthetic")
    assert arbitrate_voluntary(
        VoluntaryArbitrationFrame(active_intention=intention, sleep_motive=stronger_motive)
    ).winner_kind == "sleep_motive"

    tie = ArbitrationOption("sleep_like_other", "alternative", "sleep", 0.95)
    result = arbitrate_voluntary(
        VoluntaryArbitrationFrame(active_intention=intention, sleep_motive=stronger_motive, alternatives=(tie,))
    )
    assert result.winner_kind == "none"
    assert result.reason == "tie_requires_reassessment"


def test_critical_stability_is_bounded_motor_eligibility_not_direct_sleep():
    parameters = calibration_profiles()["human_reference_candidate.v1"]
    stability = wake_stability(
        RegulationState(1.0, 0.5, 0.9), RegulationInput("wake", 0, 100_000), parameters
    )
    eligibility = wake_stability_eligibility(
        stability, activity_id="activity-1", requires_sustained_wakefulness=True
    )
    assert eligibility.eligible
    motor = SyntheticActivityEngine({"activity-1": "active"})
    first = motor.apply_stability_eligibility(eligibility)
    repeat = motor.apply_stability_eligibility(eligibility)
    assert first.applied and not first.duplicate
    assert not repeat.applied and repeat.duplicate
    assert motor.events == (("activity-1", "aborted", "wake_stability_critical"),)
    restarted = SyntheticActivityEngine.from_snapshot(motor.snapshot())
    after_restart = restarted.apply_stability_eligibility(eligibility)
    assert after_restart.duplicate and not after_restart.applied
    assert restarted.events == ()


def test_stimulation_protects_manifestation_only_and_does_not_erase_h_phi_or_p():
    parameters = calibration_profiles()["human_reference_candidate.v1"]
    initial = RegulationState(0.72, 0.37, 0.81)
    wake = RegulationInput("wake", 0, 100_000)
    stimulated = replace(wake, stimulation=1.0)
    plain_next = advance_regulation(initial, wake, 4 * 3_600, parameters)
    stimulated_next = advance_regulation(initial, stimulated, 4 * 3_600, parameters)
    assert stimulated_next == plain_next
    plain_stability = wake_stability(plain_next, wake, parameters)
    stimulated_stability = wake_stability(plain_next, stimulated, parameters)
    assert stimulated_stability.instability <= plain_stability.instability
    assert stimulated_next.homeostatic_load > initial.homeostatic_load
    assert stimulated_next.circadian_phase != initial.circadian_phase
    assert stimulated_next.physical_capacity < initial.physical_capacity
