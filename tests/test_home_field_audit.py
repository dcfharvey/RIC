import json

import pytest

from vivarium.home_field_audit import (
    HOME_FIELD_CONDITIONS,
    HOME_FIELD_MAX_CALLS,
    HOME_FIELD_SCENARIOS,
    _planned_items,
    normalize_outer_json_fence,
    _validate_without_persistence,
)


VALID = {"schema_version": 2, "understanding_status": "ambiguous",
         "meaning_hypotheses": ["A", "B"]}


def test_preregistered_plan_is_held_out_and_has_180_calls():
    assert [item.scenario_id for item in HOME_FIELD_SCENARIOS] == [f"H{i:02d}" for i in range(1, 17)]
    assert len(_planned_items()) == 18
    assert HOME_FIELD_MAX_CALLS == 5 * 2 * 18
    assert HOME_FIELD_CONDITIONS == ("C1_NATIVE_STRICT", "C2_OUTER_FENCE_NORMALIZED")


def test_condition_b_removes_only_one_complete_outer_fence():
    raw = '```json\n{"schema_version":2,"understanding_status":"clear","meaning_hypotheses":["A"]}\n```'
    normalized, applied, kind = normalize_outer_json_fence(raw)
    assert applied is True and kind == "single_outer_code_fence"
    assert normalized.startswith('{"schema_version"')


@pytest.mark.parametrize("raw", [
    "prefix ```json\n{}\n```",
    "```json\n{}\n``` suffix",
    "```json\n{\"a\":1}\n```\n```json\n{\"b\":2}\n```",
])
def test_condition_b_refuses_text_outside_or_multiple_fences(raw):
    normalized, applied, kind = normalize_outer_json_fence(raw)
    assert normalized == raw and applied is False and kind is None


def test_condition_b_never_repairs_invalid_json_and_raw_is_independent():
    raw = "```json\n{not json}\n```"
    normalized, applied, _ = normalize_outer_json_fence(raw)
    assert applied is True
    with pytest.raises((ValueError, json.JSONDecodeError)):
        _validate_without_persistence(json.loads(normalized))
    assert raw != normalized


def test_strict_fenced_json_is_a_parse_error_in_c1():
    fenced = "```json\\n" + json.dumps(VALID) + "\\n```"
    with pytest.raises(ValueError) as exc:
        _validate_without_persistence(fenced)
    assert getattr(exc.value, "code", None) == "invalid_provider_output"


def test_strict_parser_and_semantic_contract_are_unchanged():
    assert _validate_without_persistence(VALID)["understanding_status"] == "ambiguous"
    with pytest.raises(ValueError):
        _validate_without_persistence({**VALID, "extra": True})
    with pytest.raises(ValueError):
        _validate_without_persistence({**VALID, "understanding_status": "clear", "meaning_hypotheses": []})
