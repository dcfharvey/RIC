from vivarium.cognition_policy import (
    CALL_TRIGGER_DIRECT_EVENT,
    CALL_TRIGGER_OWNER_INTERVENTION,
    CognitionCallLimits,
    CognitionCallPolicy,
    CognitionCallPolicyError,
    CognitionCallRecord,
    CognitionCallRequest,
)


NOW = "2026-08-06T12:00:00+00:00"
LIMITS = CognitionCallLimits(debounce_seconds=30, budget_window_seconds=3_600, max_calls_per_window=2)


def request(trigger=CALL_TRIGGER_DIRECT_EVENT, source="event_42", at=NOW):
    return CognitionCallRequest("sophie", trigger, source, at)


def record(source, at, trigger=CALL_TRIGGER_DIRECT_EVENT):
    return CognitionCallRecord("sophie", trigger, source, at)


def test_first_closed_trigger_is_eligible_without_side_effects():
    verdict = CognitionCallPolicy.evaluate(request(), (), LIMITS)
    assert verdict.eligible and verdict.reason_code == "eligible"
    assert verdict.idempotency_key == "sophie:direct_event:event_42"


def test_same_source_is_deduplicated_even_after_its_budget_window():
    history = (record("event_42", "2026-08-06T10:00:00+00:00"),)
    verdict = CognitionCallPolicy.evaluate(request(), history, LIMITS)
    assert not verdict.eligible and verdict.reason_code == "duplicate_call"


def test_nearby_distinct_signal_is_debounced_before_budget_is_considered():
    history = (record("event_41", "2026-08-06T11:59:45+00:00"), record("event_40", "2026-08-06T11:10:00+00:00"))
    verdict = CognitionCallPolicy.evaluate(request(), history, LIMITS)
    assert not verdict.eligible and verdict.reason_code == "debounced"


def test_budget_is_scoped_to_its_explicit_window():
    history = (record("event_41", "2026-08-06T11:10:00+00:00"), record("event_40", "2026-08-06T11:00:01+00:00"))
    verdict = CognitionCallPolicy.evaluate(request(), history, LIMITS)
    assert not verdict.eligible and verdict.reason_code == "budget_exhausted"
    expired = (record("event_41", "2026-08-06T10:00:00+00:00"),)
    assert CognitionCallPolicy.evaluate(request(), expired, LIMITS).eligible


def test_owner_intervention_is_closed_but_not_an_implicit_budget_bypass():
    history = (record("event_41", "2026-08-06T11:10:00+00:00"), record("event_40", "2026-08-06T11:00:01+00:00"))
    verdict = CognitionCallPolicy.evaluate(request(CALL_TRIGGER_OWNER_INTERVENTION, "admin_1"), history, LIMITS)
    assert not verdict.eligible and verdict.reason_code == "budget_exhausted"


def test_invalid_or_future_data_is_refused_before_any_provider_can_be_called():
    try:
        CognitionCallPolicy.evaluate(request("invented_trigger"), (), LIMITS)
    except CognitionCallPolicyError as raised:
        assert raised.code == "unknown_cognition_call_trigger"
    else:
        raise AssertionError("le motif libre doit être refusé")
    future = (record("event_41", "2026-08-06T12:01:00+00:00"),)
    try:
        CognitionCallPolicy.evaluate(request(), future, LIMITS)
    except CognitionCallPolicyError as raised:
        assert raised.code == "invalid_cognition_call_history"
    else:
        raise AssertionError("une trace future doit être refusée")


def test_history_from_another_character_is_refused_not_shared_as_budget():
    history = (CognitionCallRecord("luna", CALL_TRIGGER_DIRECT_EVENT, "event_41", "2026-08-06T11:00:00+00:00"),)
    try:
        CognitionCallPolicy.evaluate(request(), history, LIMITS)
    except CognitionCallPolicyError as raised:
        assert raised.code == "invalid_cognition_call_history"
    else:
        raise AssertionError("l'historique ne doit jamais croiser deux personnages")
