import pytest

from vivarium.interpretation_only import (
    B_SYSTEM_PROMPT, CONDITIONS, PLANNED_CALLS, parse_interpretation_only,
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
