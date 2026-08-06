import pytest

from vivarium.cognition_call_bench import (
    CognitionCallBenchError,
    CognitionCallSignal,
    run_call_policy_bench,
)
from vivarium.cognition_policy import CALL_TRIGGER_DIRECT_EVENT, CognitionCallLimits


LIMITS = CognitionCallLimits(debounce_seconds=30, budget_window_seconds=3_600, max_calls_per_window=2)


def signal(source, at, character="sophie"):
    return CognitionCallSignal(character, CALL_TRIGGER_DIRECT_EVENT, source, at)


def test_bench_replays_per_character_and_reports_each_reason_without_writes():
    report = run_call_policy_bench(
        (
            signal("event_1", "2026-08-06T12:00:00+00:00"),
            signal("event_2", "2026-08-06T12:00:10+00:00"),
            signal("event_3", "2026-08-06T12:00:40+00:00"),
            signal("event_4", "2026-08-06T12:00:50+00:00"),
            signal("event_5", "2026-08-06T12:01:20+00:00"),
            signal("event_1", "2026-08-06T12:00:00+00:00", character="luna"),
        ),
        LIMITS,
    )

    assert report.admitted_count == 3 and report.deferred_count == 3
    assert report.reason_counts == {"budget_exhausted": 1, "debounced": 2, "eligible": 3}
    assert report.as_dict()["limits"]["max_calls_per_window"] == 2


def test_bench_is_repeatable_and_does_not_share_history_between_runs():
    signals = (signal("event_1", "2026-08-06T12:00:00+00:00"), signal("event_2", "2026-08-06T12:01:00+00:00"))
    left = run_call_policy_bench(signals, LIMITS)
    right = run_call_policy_bench(signals, LIMITS)
    assert left.as_dict() == right.as_dict()


def test_bench_refuses_invalid_or_backwards_chronology_before_model_use():
    with pytest.raises(CognitionCallBenchError) as raised:
        run_call_policy_bench((signal("event_1", "2026-08-06T12:01:00+00:00"), object()), LIMITS)
    assert raised.value.code == "invalid_cognition_call_bench"
    with pytest.raises(CognitionCallBenchError) as raised:
        run_call_policy_bench(
            (signal("event_1", "2026-08-06T12:01:00+00:00"), signal("event_2", "2026-08-06T12:00:00+00:00")),
            LIMITS,
        )
    assert raised.value.code == "non_chronological_cognition_call_bench"
