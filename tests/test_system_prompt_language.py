import json

import pytest

from vivarium.system_prompt_language import (
    CONDITIONS, CONTROL_KEYS, EN_SYSTEM_PROMPT, FR_SYSTEM_PROMPT, HELD_OUT_IDS,
    MODELS, PLANNED_CALLS, _scenario_units, validate_interpretation_only,
)
from vivarium.social_interpretation_provider import SocialInterpretationProviderError


def test_preregistered_shape_and_call_count():
    assert MODELS == ("google/gemma-4-12b-qat", "qwen3-8b", "qwen3-14b")
    assert CONDITIONS == ("FR_SYSTEM_PROMPT", "EN_SYSTEM_PROMPT")
    assert len(_scenario_units()) == 27
    assert PLANNED_CALLS == 162
    ids = [item[0] for item in _scenario_units()]
    assert {"G01", "G02", "G04", "G05", "G09"}.issubset(ids)
    assert set(HELD_OUT_IDS).issubset(ids)


def test_prompts_are_frozen_and_only_language_differs():
    assert "motive_hypotheses" not in FR_SYSTEM_PROMPT
    assert "motive_hypotheses" not in EN_SYSTEM_PROMPT
    for prompt in (FR_SYSTEM_PROMPT, EN_SYSTEM_PROMPT):
        assert '"schema_version":1' in prompt
        assert '"understanding_status":"clear|ambiguous|unresolved"' in prompt
        assert '"meaning_hypotheses":["..."]' in prompt
        assert "280" in prompt and "Maximum" in prompt
        assert "ambiguous" in prompt and "unresolved" in prompt
        assert "additional fields" in prompt.lower() or "champ supplémentaire" in prompt
    assert FR_SYSTEM_PROMPT != EN_SYSTEM_PROMPT


def test_strict_interpretation_only_parser():
    assert validate_interpretation_only({"schema_version": 1, "understanding_status": "clear", "meaning_hypotheses": ["x"]})["understanding_status"] == "clear"
    with pytest.raises(SocialInterpretationProviderError):
        validate_interpretation_only({"schema_version": 1, "understanding_status": "clear", "meaning_hypotheses": ["x"], "motive_hypotheses": []})
    with pytest.raises(SocialInterpretationProviderError):
        validate_interpretation_only({"schema_version": 1, "understanding_status": "ambiguous", "meaning_hypotheses": ["x"]})
    with pytest.raises(SocialInterpretationProviderError):
        validate_interpretation_only({"schema_version": 1, "understanding_status": "unresolved", "meaning_hypotheses": ["x"]})


def test_controls_resolve_with_exact_variants_and_b11_is_distinct():
    control_units = [(sid, variant) for sid, variant, _ in _scenario_units() if sid.startswith("B")]
    assert control_units == list(CONTROL_KEYS)
    assert ("B11", "addressee") in control_units
    assert ("B11", "side_participant") in control_units


def test_preregistration_contains_exact_prompts():
    prereg = json.loads(open("data/bench/system_prompt_language/preregistration.json", encoding="utf-8").read())
    assert prereg["planned_calls"] == 162
    assert prereg["prompt_fr"] == FR_SYSTEM_PROMPT
    assert prereg["prompt_en"] == EN_SYSTEM_PROMPT
