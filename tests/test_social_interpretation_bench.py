import json

import pytest

from vivarium.social_interpretation_provider import (
    DeterministicInterpretationProvider,
    LMStudioSocialInterpretationProvider,
    SocialInterpretationContextBuilder,
    SocialInterpretationLLMService,
)
from vivarium.cognition import LocalLLMSettings
from vivarium.social_interpretation_bench import (
    BenchAggregateReport,
    BenchT2aCampaignReport,
    BenchScreen47Report,
    BenchPairedRevisionReport,
    BenchTrialReport,
    SCREEN47_P1_KEYS,
    SCREEN47_THREE_OBSERVATION_KEYS,
    T2_CHARACTERIZATION_SET,
    T1_SMOKE_SET,
    BenchError,
    _BenchClock,
    _build_fixture,
    _safe_model_id,
    get_scenarios,
    inspect_screen_deployment,
    run_bench,
    run_paired_revision_trial,
    run_screen47,
    run_trial,
    screen47_call_plan,
    write_t2a_paired_report,
    build_model_inventory,
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


def test_invalid_scenario_trial_count_and_t2_requires_real_provider():
    with pytest.raises(BenchError) as unknown:
        run_bench(_provider(), scenario_ids=("B99",))
    assert unknown.value.code == "invalid_scenario"
    with pytest.raises(BenchError) as count:
        run_bench(_provider(), trials=0)
    assert count.value.code == "invalid_trial_count"
    with pytest.raises(BenchError) as level:
        run_bench(_provider(), level="T2")
    assert level.value.code == "t2_requires_real_provider"


def test_t2_characterization_matrix_is_exactly_bounded():
    assert len(T2_CHARACTERIZATION_SET) == 21
    assert not {scenario_id for scenario_id, _ in T2_CHARACTERIZATION_SET} & {"B15", "B16", "B20", "B21", "B22", "B23"}


def test_screen47_plan_is_exactly_41_generic_calls_plus_three_pairs():
    plan = screen47_call_plan()
    assert len(plan) == 41
    assert len(SCREEN47_P1_KEYS) == 11
    assert len(SCREEN47_THREE_OBSERVATION_KEYS) == 13
    assert sum(number == 1 for _, _, number in plan) == 15


def test_t2_accepts_non_gemma_provider_identity_without_scoring(monkeypatch):
    provider = LMStudioSocialInterpretationProvider(
        LocalLLMSettings("http://127.0.0.1:1234", "model_B", None, 12))
    expected = BenchTrialReport(2, "B01", "base", 1, "model_B", "scc1b1-native-v2", "b" * 64, 1,
                                "valid_interpretation", "real_provider_ready")
    monkeypatch.setattr("vivarium.social_interpretation_bench.run_trial", lambda *args, **kwargs: expected)
    report = run_bench(provider, level="T2", trials=1, scenario_ids=("B01",))
    assert report.trials[0].model_id == "model_B"
    campaign = BenchT2aCampaignReport(report, (), 1)
    assert campaign.as_dict()["model_id"] == "model_B"


def test_screen_deployment_distinguishes_model_key_and_instance_id():
    base = {"key": "model_A", "loaded_instances": [{"id": "instance-17", "config": {"context_length": 8192}}]}
    deployment = inspect_screen_deployment(base)
    assert deployment["screen_status"] == "ready"
    assert deployment["requested_model_key"] == "model_A"
    assert deployment["loaded_model_instance_id"] == "instance-17"
    assert inspect_screen_deployment({"key": "model_A", "loaded_instances": []})["error_code"] == "deployment_failed"
    assert inspect_screen_deployment({"key": "model_A", "loaded_instances": [base["loaded_instances"][0], base["loaded_instances"][0]]})["error_code"] == "multiple_loaded_instances"
    mismatch = inspect_screen_deployment({"key": "model_A", "loaded_instances": [{"id": "i", "config": {"context_length": 16384}}]})
    assert mismatch["screen_status"] == "deployment_config_mismatch"
    assert mismatch["actual_load_config"]["actual_context_length"] == 16384


def test_safe_model_id_is_collision_resistant():
    assert _safe_model_id("a/b") != _safe_model_id("a-b")


def test_inventory_preserves_official_identity_fields_without_invention(monkeypatch):
    record = {"type": "llm", "publisher": "vendor", "key": "model_A", "display_name": "A",
              "architecture": "arch", "quantization": {"name": "Q4"}, "size_bytes": 123,
              "params_string": "8B", "max_context_length": 8192, "format": "gguf",
              "capabilities": ["vision"], "loaded_instances": [{"id": "instance-1", "config": {"context_length": 8192}}]}
    monkeypatch.setattr("vivarium.social_interpretation_bench.LMStudioProvider.list_model_records", lambda self: (record,))
    inventory = build_model_inventory(LocalLLMSettings("http://127.0.0.1:1234", "model_A", None, 12))
    model = inventory["models"][0]
    assert model["size_bytes"] == 123 and model["params_string"] == "8B"
    assert model["quantization"] == {"name": "Q4"} and model["max_context_length"] == 8192
    assert model["loaded_instances"][0]["id"] == "instance-1"


def test_screen_warmup_failure_is_non_success_and_not_cognitive_blocker(monkeypatch):
    provider = LMStudioSocialInterpretationProvider(LocalLLMSettings("http://127.0.0.1:1234", "model_A", None, 12))
    def fail(_snapshot):
        raise RuntimeError("warmup")
    monkeypatch.setattr(provider, "propose", fail)
    report = run_screen47(provider)
    payload = report.as_dict()
    assert payload["screen_status"] == "warmup_failed"
    assert payload["warmup"]["scored"] is False
    assert payload["calls_attempted"] == 0
    assert payload["hard_blockers"] == []


def test_screen47_aggregate_excludes_warmup_and_contains_promised_sections(monkeypatch):
    provider = LMStudioSocialInterpretationProvider(LocalLLMSettings("http://127.0.0.1:1234", "model_A", None, 12))
    monkeypatch.setattr(provider, "propose", lambda _snapshot: VALID)
    trial = BenchTrialReport(2, "B01", "base", 1, "model_A", "scc1b1-native-v2", "b" * 64, 1,
                             "valid_interpretation", "real_provider_ready", understanding_status="ambiguous")
    pair = BenchPairedRevisionReport("screen", 1, trial, trial, True)
    monkeypatch.setattr("vivarium.social_interpretation_bench.run_trial", lambda *args, **kwargs: trial)
    monkeypatch.setattr("vivarium.social_interpretation_bench.run_paired_revision_trial", lambda *args, **kwargs: pair)
    payload = run_screen47(provider).as_dict()
    assert payload["calls_attempted"] == 47
    assert payload["generic_calls"] == 41 and payload["paired_calls"] == 6
    assert payload["warmup"]["scored"] is False
    assert payload["median_scored_latency_ms"] == 1
    assert "metamorphic_metrics" in payload and "revision" in payload and "injection" in payload


def test_paired_writer_uses_real_model_identity_and_no_gemma_label(tmp_path):
    trial = BenchTrialReport(2, "B15_B16", "initial", 1, "model_A", "scc1b1-native-v2", "a" * 64, 1,
                             "valid_interpretation", "real_provider_ready",
                             provenance_expected={"model_id": "model_A"}, provenance_actual={"model_id": "model_A"})
    pair = type("Pair", (), {"pair_id": "p", "trial_number": 1, "initial": trial,
                              "revision": trial, "lineage_valid": True,
                              "as_dict": lambda self: {"pair_id": self.pair_id, "trial_number": self.trial_number,
                                                        "lineage_valid": self.lineage_valid,
                                                        "initial": self.initial.as_dict(), "revision": self.revision.as_dict()}})()
    path = tmp_path / "paired_model_a.json"
    write_t2a_paired_report((pair,), path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["baseline"]["model_id"] == "model_A"
    assert "gemma" not in path.read_text(encoding="utf-8").lower()


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
    assert report.initial.hard_blockers == ()
    assert report.revision.hard_blockers == ()
    assert report.initial.provenance_expected == report.initial.provenance_actual
    assert report.revision.provenance_expected == report.revision.provenance_actual
    assert report.initial.causal_effect_absent is True
    assert report.revision.causal_effect_absent is True


def test_b05_b06_different_stochastic_wording_keeps_raw_metric_without_review_flag():
    report = run_bench(_provider(), level="T0", trials=2, scenario_ids=("B05", "B06"))
    assert "irrelevant_context_changed_output" not in report.as_dict()["review_flags"]


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
