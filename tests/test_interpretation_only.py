import pytest

from vivarium.interpretation_only import (
    B_SYSTEM_PROMPT, CONDITIONS, CONTROL_KEYS, CORRECTED_SCENARIOS, HISTORIC_EXCLUDED,
    PLANNED_CALLS, VALID_HELD_OUT, _fixture_for, parse_interpretation_only,
    resolve_control_scenarios,
)
from vivarium.social_interpretation_provider import LMStudioSocialInterpretationProvider, parse_provider_proposal


def valid_b(status="clear", meanings=None):
    return {"schema_version": 1, "understanding_status": status, "meaning_hypotheses": meanings if meanings is not None else ["x"]}


def test_b_schema_is_strict_and_excludes_motive_hypotheses():
    assert set(valid_b()) == {"schema_version", "understanding_status", "meaning_hypotheses"}
    with pytest.raises(Exception): parse_interpretation_only({**valid_b(), "motive_hypotheses": []})
    with pytest.raises(Exception): parse_interpretation_only({**valid_b(), "unknown": 1})
    with pytest.raises(Exception): parse_interpretation_only(valid_b("unresolved", ["x"]))
    with pytest.raises(Exception): parse_interpretation_only(valid_b("clear", []))
    with pytest.raises(Exception): parse_interpretation_only(valid_b("ambiguous", ["x"]))
    with pytest.raises(Exception): parse_interpretation_only(valid_b("clear", ["x"] * 4))
    with pytest.raises(Exception): parse_interpretation_only(valid_b("clear", ["x" * 281]))


def test_a_uses_production_parser_and_b_prompt_is_bench_only():
    assert parse_provider_proposal({"schema_version":1,"understanding_status":"clear","meaning_hypotheses":["x"],"motive_hypotheses":[]})
    assert "motive_hypotheses" not in B_SYSTEM_PROMPT
    assert "parole" in B_SYSTEM_PROMPT and "instruction" in B_SYSTEM_PROMPT
    assert "Une interprétation implicite est permise" in B_SYSTEM_PROMPT


def test_preregistered_call_count():
    assert PLANNED_CALLS == 174


def test_all_control_variants_resolve_and_preserve_distinct_roles():
    resolved = resolve_control_scenarios()
    assert set(resolved) == set(CONTROL_KEYS)
    assert resolved[("B02", "underspecified")].scenario_id == "B02"
    assert resolved[("B02", "underspecified")].variant_id == "underspecified"
    assert resolved[("B11", "addressee")].variant_id != resolved[("B11", "side_participant")].variant_id
    assert resolved[("B15", "initial")].revision is False
    assert resolved[("B16", "clarified")].revision is True


def test_experimental_fixture_sets_and_a_b_snapshot_identity_are_unchanged():
    assert {item.scenario_id for item in VALID_HELD_OUT}.isdisjoint(HISTORIC_EXCLUDED)
    assert [item.scenario_id for item in CORRECTED_SCENARIOS] == ["G01", "G02", "G04", "G05", "G09"]
    scenario = resolved = resolve_control_scenarios()[("B02", "underspecified")]
    fixture_a, snapshot_a = _fixture_for(scenario)
    fixture_b, snapshot_b = _fixture_for(scenario)
    try:
        assert snapshot_a.fingerprint == snapshot_b.fingerprint
        assert snapshot_a.wire == snapshot_b.wire
    finally:
        fixture_a.conn.close()
        fixture_b.conn.close()
