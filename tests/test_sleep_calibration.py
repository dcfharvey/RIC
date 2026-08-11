import json

from vivarium.cli import main
from vivarium.sleep_calibration import run_reference_calibration


def test_reference_calibration_reports_all_minimal_inactive_falsifications():
    report = run_reference_calibration()
    assert report.passed
    values = {item.name: item.value for item in report.observations}
    assert values["partition_invariant"]
    assert values["free_running_observable"]
    assert values["phase_dependent_light"]
    assert values["sleep_occlusion_attenuates_light"]
    assert values["normal_night_is_plausible"]
    assert values["daytime_nap_and_post_deprivation_sleep_are_possible"]
    assert values["voluntary_postponement_degrades_physiology"]
    assert values["entrainment_is_progressive"]
    assert values["reentrainment_is_progressive"]
    assert values["rest_and_sleep_separate_h_and_p"]
    assert values["critical_stability_is_bounded"]
    assert values["repeated_restriction_accumulates_during_protocol"]
    assert values["complete_state_convergence_is_markovian"]
    assert values["generic_feline_opportunities_allow_multiple_episodes"]


def test_cli_runs_sleep_calibration_without_a_database_or_llm(capsys):
    assert main(["sleep-calibration-bench"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True
    assert payload["profile_key"] == "human_reference_candidate.v1"


def test_calibration_profile_error_is_explicit(capsys):
    assert main(["sleep-calibration-bench", "--profile", "unknown"]) == 2
    assert "invalid_request" in capsys.readouterr().err
