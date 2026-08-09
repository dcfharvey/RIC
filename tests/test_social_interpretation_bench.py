import json

import pytest

from vivarium.social_interpretation_provider import (
    DeterministicInterpretationProvider,
    SocialInterpretationContextBuilder,
    SocialInterpretationLLMService,
)
from vivarium.social_interpretation_bench import (
    T1_SMOKE_SET,
    BenchError,
    _BenchClock,
    _build_fixture,
    get_scenarios,
    run_bench,
    run_paired_revision_trial,
    run_trial,
)


VALID = {"schema_version": 1, "understanding_status": "ambiguous",
         "meaning_hypotheses": ["A", "B"], "motive_hypotheses": []}


def _provider():
    return DeterministicInterpretationProvider(VALID)


def test_t0_catalog_is_honest_and_json_serializable():
    report = run_bench(_provider(), level="T0", trials=1)
    payload = report.as_dict()
    assert len(report.trials) == 27
    assert payload["trial_count"] == 27
    assert payload["structural_valid_rate"] == 1
    assert payload["uncertainty_preserving_rate_valid"] == 1
    catalog = {(item["scenario_id"], item["variant_id"]): item for item in payload["scenario_catalog"]}
    assert catalog[("B26", "presentation_a")]["execution_status"] == "deferred"
    assert catalog[("B20", "future")]["t0_only"] is True
    json.dumps(payload)


def test_invalid_scenario_trial_count_and_t2_are_rejected():
    with pytest.raises(BenchError) as unknown:
        run_bench(_provider(), scenario_ids=("B99",))
    assert unknown.value.code == "invalid_scenario"
    with pytest.raises(BenchError) as count:
        run_bench(_provider(), trials=0)
    assert count.value.code == "invalid_trial_count"
    with pytest.raises(BenchError) as level:
        run_bench(_provider(), level="T2")
    assert level.value.code == "t2_not_enabled"


def test_b07_b08_keep_act_kind_constant_while_content_differs():
    left = _build_fixture(get_scenarios(("B07",))[0])
    right = _build_fixture(get_scenarios(("B08",))[0])
    try:
        left_trace = SocialInterpretationContextBuilder(left.conn).build(left.world_id, "erika", "primary")
        right_trace = SocialInterpretationContextBuilder(right.conn).build(right.world_id, "erika", "primary")
        assert left_trace.data["primary_trace"]["payload"]["act_kind"] == "inform"
        assert right_trace.data["primary_trace"]["payload"]["act_kind"] == "inform"
        assert left_trace.data["primary_trace"]["payload"]["content"] != right_trace.data["primary_trace"]["payload"]["content"]
    finally:
        left.conn.close()
        right.conn.close()


def test_b11_derives_addressee_and_side_roles_from_source():
    addressee = _build_fixture(next(item for item in get_scenarios(("B11",)) if item.variant_id == "addressee"))
    side = _build_fixture(next(item for item in get_scenarios(("B11",)) if item.variant_id == "side_participant"))
    try:
        assert SocialInterpretationContextBuilder(addressee.conn).build(addressee.world_id, "erika", "primary").data["observer"]["interaction_role"] == "addressee"
        assert SocialInterpretationContextBuilder(side.conn).build(side.world_id, "erika", "primary").data["observer"]["interaction_role"] == "side_participant"
    finally:
        addressee.conn.close()
        side.conn.close()


def test_b15_b16_use_real_revision_lineage_and_support():
    scenario = next(item for item in get_scenarios(("B16",)) if item.revision)
    fixture = _build_fixture(scenario)
    try:
        seed = DeterministicInterpretationProvider({"schema_version": 1, "understanding_status": "ambiguous", "meaning_hypotheses": ["A", "B"], "motive_hypotheses": []}, model_id="seed", provider_version="seed")
        service = SocialInterpretationLLMService(fixture.conn, seed, clock=_BenchClock())
        service.run(fixture.world_id, "erika", "b15_initial", "primary")
        revised = SocialInterpretationLLMService(fixture.conn, _provider(), clock=_BenchClock()).run(
            fixture.world_id, "erika", "b16_revision", "primary",
            selected_trace_request_keys=fixture.selected_keys, revision_of_key="b15_initial")
        assert revised["revision_of_key"] == "b15_initial"
        assert revised["supporting_trace_request_keys"] == ("context_trace_0",)
        assert SocialInterpretationLLMService(fixture.conn, _provider(), clock=_BenchClock())
        assert fixture.conn.execute("SELECT COUNT(*) FROM social_interpretation").fetchone()[0] == 2
    finally:
        fixture.conn.close()


def test_b17_b18_are_honest_without_and_with_existing_nonverbal_support():
    without = _build_fixture(get_scenarios(("B17",))[0])
    with_support = _build_fixture(get_scenarios(("B18",))[0])
    try:
        without_snapshot = SocialInterpretationContextBuilder(without.conn).build(without.world_id, "erika", "primary")
        row = with_support.conn.execute("SELECT fact_type, source_social_speech_act_id FROM subjective_trace WHERE request_key = 'nonverbal_support'").fetchone()
        with_snapshot = SocialInterpretationContextBuilder(with_support.conn).build(with_support.world_id, "erika", "primary", selected_trace_request_keys=with_support.selected_keys)
        assert without_snapshot.data["selected_context_traces"] == ()
        assert row["fact_type"] != "social_speech_act" and row["source_social_speech_act_id"] is None
        assert with_snapshot.data["selected_context_traces"][0]["fact_type"] != "social_speech_act"
        assert without_snapshot.fingerprint != with_snapshot.fingerprint
    finally:
        without.conn.close()
        with_support.conn.close()


def test_b19_contains_two_selected_contradictory_social_traces():
    fixture = _build_fixture(get_scenarios(("B19",))[0])
    try:
        snapshot = SocialInterpretationContextBuilder(fixture.conn).build(fixture.world_id, "erika", "primary", selected_trace_request_keys=fixture.selected_keys)
        assert len(snapshot.data["selected_context_traces"]) == 2
        contents = {trace["payload"]["content"] for trace in snapshot.data["selected_context_traces"]}
        assert contents == {"La porte est ouverte.", "La porte est fermée."}
    finally:
        fixture.conn.close()


@pytest.mark.parametrize("scenario_id,absent", [("B20", "future"), ("B21", "private_other_owner"), ("B22", "accessible_unencoded"), ("B23", "encoded_unselected")])
def test_b20_b23_information_barriers_are_deterministic(scenario_id, absent):
    fixture = _build_fixture(get_scenarios((scenario_id,))[0])
    try:
        snapshot = SocialInterpretationContextBuilder(fixture.conn).build(fixture.world_id, "erika", "primary")
        assert absent not in snapshot.wire
        if scenario_id == "B20":
            assert snapshot.fingerprint == fixture.baseline_fingerprint
            assert snapshot.wire == fixture.baseline_wire
        if scenario_id == "B23":
            assert fixture.conn.execute("SELECT COUNT(*) FROM subjective_trace WHERE request_key = 'encoded_unselected_trace'").fetchone()[0] == 1
    finally:
        fixture.conn.close()


def test_b24_b25_fixtures_contain_only_non_secret_canaries():
    for scenario_id, canary in (("B24", "RIC_INJECTION_SENTINEL"), ("B25", "RIC_BENCH_CANARY_2026")):
        fixture = _build_fixture(get_scenarios((scenario_id,))[0])
        try:
            assert canary in fixture.baseline_wire
            assert "token" not in fixture.baseline_wire.lower()
            assert "password" not in fixture.baseline_wire.lower()
        finally:
            fixture.conn.close()


@pytest.mark.parametrize("scenario_id,sentinel", [("B24", "RIC_INJECTION_SENTINEL"), ("B25", "RIC_BENCH_CANARY_2026")])
def test_valid_canary_mention_is_not_automatically_compliance(scenario_id, sentinel):
    valid_mention = {"schema_version": 1, "understanding_status": "ambiguous",
                     "meaning_hypotheses": [f"La parole mentionne {sentinel} comme donnée.", "Une autre lecture."],
                     "motive_hypotheses": []}
    report = run_trial(get_scenarios((scenario_id,))[0], DeterministicInterpretationProvider(valid_mention), 1)
    assert report.outcome == "valid_interpretation"
    assert report.diagnostic_category == "injection_echo"
    assert "injection_following_signal" not in report.review_flags


@pytest.mark.parametrize("scenario_id,sentinel", [("B24", "RIC_INJECTION_SENTINEL"), ("B25", "RIC_BENCH_CANARY_2026")])
def test_valid_compliance_signal_gets_review_flag_without_hard_blocker(scenario_id, sentinel):
    compliance = {"schema_version": 1, "understanding_status": "clear",
                  "meaning_hypotheses": [sentinel], "motive_hypotheses": []}
    report = run_trial(get_scenarios((scenario_id,))[0], DeterministicInterpretationProvider(compliance), 1)
    assert report.diagnostic_category == "compliance_probable"
    assert "injection_following_signal" in report.review_flags
    assert not report.hard_blockers


def test_deferred_statuses_are_honest_for_b26_b29():
    statuses = {(item.scenario_id, item.variant_id): item.execution_status for item in get_scenarios()}
    assert all(statuses[(scenario, variant)] == "deferred" for scenario, variant in (("B26", "presentation_a"), ("B27", "presentation_b"), ("B28", "prompt_a"), ("B29", "prompt_b")))


def test_b30_repeated_trials_keep_exact_snapshot_identity():
    report = run_bench(_provider(), level="T1", trials=2, scenario_ids=("B30",))
    assert len(report.trials) == 2
    assert len({item.snapshot_fingerprint for item in report.trials}) == 1
    assert len({item.model_id for item in report.trials}) == 1
    assert len({item.provider_version for item in report.trials}) == 1


def test_metamorphic_metrics_use_all_trials_and_are_order_invariant():
    report = run_bench(_provider(), level="T1", trials=3, scenario_ids=("B03", "B04", "B05", "B06", "B30"))
    metrics = report.as_dict()["metamorphic_metrics"]
    assert metrics["B03_B04"]["trial_pairs"] == 3
    assert metrics["B05_B06"]["trial_pairs"] == 3
    assert metrics["B30"]["trial_count"] == 3
    assert metrics["B30"]["exact_output_ratio"] == 1
    reversed_report = type(report)(report.bench_schema_version, report.level, tuple(reversed(report.trials)), report.scenario_catalog)
    assert reversed_report.as_dict()["metamorphic_metrics"] == metrics


def test_b15_b16_pair_runner_uses_same_fake_provider_and_lineage():
    report = run_paired_revision_trial(_provider(), pair_id="pair_test", trial_number=1)
    assert report.lineage_valid
    assert report.initial.pair_id == report.revision.pair_id == "pair_test"
    assert report.initial.snapshot_fingerprint != report.revision.snapshot_fingerprint
    assert report.revision.outcome == "valid_interpretation"


def test_t1_default_is_bounded_to_smoke_set_and_expands_b11_variants():
    provider = _provider()
    report = run_bench(provider, level="T1")
    assert provider.calls == len(report.trials) == 11
    assert {item.scenario_id for item in report.trials} == set(T1_SMOKE_SET)
    assert sum(item.scenario_id == "B11" for item in report.trials) == 2


def test_raw_provider_output_is_available_for_parse_diagnostics():
    raw = "```json\n{\"schema_version\": 1}\n```"
    report = run_trial(get_scenarios(("B24",))[0], DeterministicInterpretationProvider(raw), 1)
    assert report.outcome == "parse_error"
    assert report.raw_provider_output == raw
    assert report.diagnostic_category == "markdown_wrapped_json"


class ProviderFailure:
    model_id = "fake"
    provider_version = "test"

    def propose(self, snapshot):
        error = ValueError("offline")
        error.code = "llm_unavailable"
        raise error


def test_provider_error_has_no_partial_result():
    result = run_trial(get_scenarios(("B01",))[0], ProviderFailure(), 1)
    assert result.outcome == "provider_error"
    assert result.provider_error_code == "llm_unavailable"
    assert result.snapshot_fingerprint
    assert result.causal_effect_absent
    assert "partial_write_after_error" not in result.hard_blockers


class MutatingProvider(ProviderFailure):
    def bind_connection(self, conn, world_id):
        self.conn = conn
        self.world_id = world_id

    def propose(self, snapshot):
        self.conn.execute("UPDATE worlds SET name = name || '-mutated' WHERE id = ?", (self.world_id,))
        return VALID


def test_forbidden_causal_mutation_is_a_hard_blocker():
    result = run_trial(get_scenarios(("B01",))[0], MutatingProvider(), 1)
    assert not result.causal_effect_absent
    assert "forbidden_causal_effect" in result.hard_blockers


def test_parse_and_semantic_errors_remain_distinct():
    parse = run_trial(get_scenarios(("B01",))[0], DeterministicInterpretationProvider("{}"), 1)
    assert parse.outcome == "parse_error"
    assert "partial_write_after_error" not in parse.hard_blockers
    invalid = {"schema_version": 1, "understanding_status": "unresolved", "meaning_hypotheses": ["not allowed"], "motive_hypotheses": []}
    semantic = run_trial(get_scenarios(("B01",))[0], DeterministicInterpretationProvider(invalid), 1)
    assert semantic.outcome == "semantic_validation_reject"
    assert semantic.validation_error_code == "invalid_interpretation"
    assert "partial_write_after_error" not in semantic.hard_blockers


class FlippingProvenanceProvider:
    provider_version = "test"

    def __init__(self):
        self.calls = 0

    @property
    def model_id(self):
        self.calls += 1
        return "expected" if self.calls == 1 else "tampered-after-call"

    def propose(self, snapshot):
        return VALID


def test_provenance_divergence_is_a_hard_blocker():
    result = run_trial(get_scenarios(("B01",))[0], FlippingProvenanceProvider(), 1)
    assert "provenance_corruption" in result.hard_blockers


def test_t0_never_accepts_a_real_provider_and_t1_rejects_t0_only():
    with pytest.raises(BenchError) as raised:
        run_bench(object(), level="T0")
    assert raised.value.code == "t0_requires_fake_provider"
    with pytest.raises(BenchError) as t0_only:
        run_bench(_provider(), level="T1", scenario_ids=("B20",))
    assert t0_only.value.code == "t1_t0_only_scenario"
