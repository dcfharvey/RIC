import json

from vivarium.cli import main
from vivarium.sleep_calibration import run_calibration_selection, run_reference_calibration


def test_reference_calibration_reports_all_minimal_inactive_falsifications():
    report = run_reference_calibration()
    assert report.passed
    values = {item.name: item.value for item in report.observations}
    assert values["partition_numerically_converges"]
    assert values["free_running_observable"]
    assert values["phase_dependent_light"]
    assert values["sleep_occlusion_attenuates_light"]
    assert values["normal_night_is_plausible"]
    assert values["daytime_sleep_equation_dissipates_h"]
    assert values["post_deprivation_daytime_sleep_propensity_accessible"]
    assert values["voluntary_postponement_degrades_physiology"]
    assert values["stable_zeitgeber_phase_locks"]
    assert values["shifted_zeitgeber_reentrains_to_different_lock"]
    assert values["rest_and_sleep_separate_h_and_p"]
    assert values["critical_stability_is_bounded"]
    assert values["propensity_families_not_trivially_equivalent"]
    assert values["repeated_restriction_accumulates_during_protocol"]
    assert values["complete_state_convergence_is_markovian"]
    assert values["generic_feline_opportunities_allow_multiple_episodes"]
    trajectories = {item.name: item.values for item in report.trajectories}
    assert len(trajectories["stable_zeitgeber_daily_phase"]) > 3
    assert trajectories["stable_zeitgeber_daily_phase"][-1] != trajectories["stable_zeitgeber_daily_phase"][0]
    assert trajectories["shifted_zeitgeber_daily_phase"][-1] != trajectories["stable_zeitgeber_daily_phase"][-1]


def test_cli_runs_sleep_calibration_without_a_database_or_llm(capsys):
    assert main(["sleep-calibration-bench"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True
    assert payload["profile_key"] == "human_reference_candidate.v1"
    assert main(["sleep-calibration-bench", "--selection"]) == 0
    selection = json.loads(capsys.readouterr().out)
    assert selection["passed"] is True
    assert selection["recommended_family"] == "additive"


def test_calibration_profile_error_is_explicit(capsys):
    assert main(["sleep-calibration-bench", "--profile", "unknown"]) == 2
    assert "invalid_request" in capsys.readouterr().err


def test_selection_bench_prefers_parsimony_and_exposes_robustness_boundaries():
    report = run_calibration_selection()
    assert report.recommended_family == "additive"
    assert report.shared_physiology_passed
    scenarios = {item.name: item for item in report.family_scenarios}
    assert scenarios["moderate_h_sleep_favorable"].additive_milli > (
        scenarios["moderate_h_sleep_favorable"].sensitivity_modulated_milli
    )
    sweeps = {item.parameter_key: item for item in report.parameter_sweeps}
    assert "24h40" in sweeps["intrinsic_period_seconds"].failing_values
    assert "0.65" in sweeps["homeostatic_stability_weight"].failing_values
    assert "high" in sweeps["stability_bands"].failing_values
    assert "24h10/5000" in report.period_forcing_sweep.passed_cells
    assert "24h00/5000" in report.period_forcing_sweep.failed_cells
    assert all(item.opportunity_episode_count >= 2 for item in report.feline_sandbox)
