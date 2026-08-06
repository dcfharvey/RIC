import pytest

from vivarium.motivation import MotivationError, MotivationService
from vivarium.policy import PolicyContext


def context(needs, accessible=None):
    return PolicyContext(
        character_key="sophie",
        needs=needs,
        need_remainders={key: 0 for key in needs},
        effective_thresholds={key: 50000 for key in needs},
        current_location="salon",
        profile={},
        rates={key: 1 for key in needs},
        accessible=accessible or {},
    )


def test_only_known_deficits_become_bounded_candidates():
    candidates = MotivationService().candidates(
        context(
            {"satiete": 40000, "hygiene": 50000, "repos": 30000, "energie": 50000},
            {"eat": {"cuisine": 1}, "sleep": {"chambre": 1}},
        )
    )

    assert [item.target_need for item in candidates] == ["repos", "satiete"]
    repos, satiete = candidates
    assert repos.urgency_milli == repos.pressure_milli == repos.importance_milli == 400
    assert repos.possible_actions == ("sleep",)
    assert satiete.possible_actions == ("eat",)
    assert repos.expected_pleasure_milli is None and repos.estimated_cost_milli is None


def test_critical_need_gets_urgency_without_changing_its_pressure():
    candidates = MotivationService().candidates(
        context(
            {"satiete": 50000, "hygiene": 50000, "repos": 10000, "energie": 50000},
            {"sleep": {"chambre": 1}},
        )
    )
    assert len(candidates) == 1
    assert candidates[0].target_need == "repos"
    assert candidates[0].pressure_milli == 800 and candidates[0].urgency_milli == 1000


def test_motive_survives_without_a_current_action_but_has_no_fabricated_affordance():
    candidates = MotivationService().candidates(
        context({"satiete": 10000, "hygiene": 50000, "repos": 50000, "energie": 50000})
    )
    assert len(candidates) == 1 and candidates[0].possible_actions == ()


def test_invalid_context_is_rejected_before_any_decision():
    with pytest.raises(MotivationError) as raised:
        MotivationService().candidates(object())
    assert raised.value.code == "invalid_motivation_context"
