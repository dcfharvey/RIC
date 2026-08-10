import json
from pathlib import Path

import pytest

from vivarium.final_language_qualification import (
    CONDITIONS, CONTROL_KEYS, PLANNED_CALLS, SCENARIO_IDS, TRANSLATION_AUDIT,
    TRANSLATIONS, _snapshot, _translated_snapshot, _units,
)
from vivarium.social_interpretation_provider import SocialInterpretationProviderError
from vivarium.system_prompt_language import EN_SYSTEM_PROMPT, FR_SYSTEM_PROMPT, validate_interpretation_only


def test_exact_preregistered_unit_count_and_lineage_ids():
    units = _units()
    assert len(units) == 17
    assert PLANNED_CALLS == 102
    assert [x[0] for x in units] == list(SCENARIO_IDS)
    assert ("B15", "initial") in [(x[0], x[1]) for x in units]
    assert ("B16", "clarified") in [(x[0], x[1]) for x in units]


def test_translation_is_frozen_and_b13_uses_stole():
    assert TRANSLATIONS["X a volé mon téléphone."] == "X stole my phone."
    assert "stole" in TRANSLATIONS["X a volé mon téléphone."]
    assert CONDITIONS == ("FR_FR", "EN_EN")
    assert "motive_hypotheses" not in FR_SYSTEM_PROMPT
    assert "motive_hypotheses" not in EN_SYSTEM_PROMPT


def test_translation_audit_has_every_stimulus():
    assert {row[0] for row in TRANSLATION_AUDIT} == {"G01", "G05", "G09", "H03", "H07", "H08", "H10", "H12", "H13", "H15/H16", "B04", "B10", "B13", "B15/B16", "B19"}
    assert all(row[4] in {"PASS", "LIMITED", "FAIL"} and row[5] in {"PASS", "LIMITED", "FAIL"} for row in TRANSLATION_AUDIT)


def test_interpretation_only_parser_remains_strict():
    good = {"schema_version": 1, "understanding_status": "clear", "meaning_hypotheses": ["x"]}
    assert validate_interpretation_only(good)["meaning_hypotheses"] == ["x"]
    with pytest.raises(SocialInterpretationProviderError):
        validate_interpretation_only({**good, "motive_hypotheses": []})


def test_preregistration_call_count_is_explicit():
    p = Path("data/bench/final_language_qualification/preregistration.json")
    assert json.loads(p.read_text(encoding="utf-8"))["planned_calls"] == 102


def test_mappingproxy_translation_is_non_mutating_and_structurally_safe():
    _, _, item = _units()[0]
    fixture, fr = _snapshot(item)
    try:
        fr_wire_before = fr.wire
        en = _translated_snapshot(fr)
        assert fr.wire == fr_wire_before
        assert en.data.keys() == fr.data.keys()
        assert en.data["observer"] == fr.data["observer"]
        assert en.data["primary_trace"]["request_key"] == fr.data["primary_trace"]["request_key"]
        assert en.data["primary_trace"]["payload"]["content"] == "Yes, that works for me."
        assert en.fingerprint != fr.fingerprint
    finally:
        fixture.conn.close()


def test_translated_snapshot_keeps_h07_h08_and_b13_lexical_contracts():
    by_id = {x[0]: x[2] for x in _units()}
    for sid, expected in (("H07", "Erika told me: \"Luna broke the cup.\""), ("H08", "Erika thinks the door is locked, but I don't know."), ("B13", "X stole my phone.")):
        fixture, fr = _snapshot(by_id[sid])
        try:
            en = _translated_snapshot(fr)
            content = en.data["primary_trace"]["payload"]["content"]
            assert content == expected
        finally:
            fixture.conn.close()
