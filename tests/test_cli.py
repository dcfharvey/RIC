"""Tests de l'interface en ligne de commande (init / status)."""

import pytest

from vivarium.cli import main
from vivarium.cognition import LocalLLMSettings
from vivarium.social_interpretation_provider import LMStudioSocialInterpretationProvider
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema


def test_cli_init_et_status(tmp_path, capsys):
    db = tmp_path / "world.cli.sqlite"
    rc = main(["init", "--name", "Monde CLI", "--db", str(db)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Monde initialisé" in out

    rc2 = main(["status", "--db", str(db)])
    assert rc2 == 0
    out2 = capsys.readouterr().out
    assert "Version de schéma" in out2
    assert "lieux=9" in out2
    assert "objets=3" in out2
    assert "personnages=4" in out2
    assert "Integrity check : ok" in out2
    assert "aucune violation" in out2


def test_cli_init_refuse_reinitialisation_sans_force(tmp_path, capsys):
    db = tmp_path / "world2.sqlite"
    assert main(["init", "--name", "Un", "--db", str(db)]) == 0
    rc = main(["init", "--name", "Deux", "--db", str(db)])
    assert rc == 2
    assert "existe déjà" in capsys.readouterr().err


def test_cli_init_force_reinitialise(tmp_path, capsys):
    db = tmp_path / "world3.sqlite"
    assert main(["init", "--name", "Un", "--db", str(db)]) == 0
    assert main(["init", "--name", "Deux", "--force", "--db", str(db)]) == 0
    out = capsys.readouterr().out
    assert "Deux" in out


def test_cli_sans_commande_affiche_version(capsys):
    assert main([]) == 0
    assert "vivarium-social" in capsys.readouterr().out


def test_cli_upgrade_dev_idempotent(tmp_path, capsys):
    db = tmp_path / "upg.sqlite"
    assert main(["init", "--db", str(db)]) == 0
    # init a déjà seedé les 4 habitantes : upgrade-dev ne doit rien ré-écrire
    rc = main(["upgrade-dev", "--db", str(db)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "existent déjà" in out


def test_cli_llm_status_lists_models_before_a_model_is_configured(monkeypatch, capsys, tmp_path):
    class Provider:
        def __init__(self, settings): pass
        def list_models(self): return ("gemma-local",)

    monkeypatch.delenv("VIVARIUM_LLM_MODEL", raising=False)
    monkeypatch.setenv("VIVARIUM_CONFIG_DIR", str(tmp_path / "empty-config"))
    monkeypatch.setattr("vivarium.cognition.LMStudioProvider", Provider)
    assert main(["llm-status"]) == 1
    captured = capsys.readouterr()
    assert "gemma-local" in captured.out and "VIVARIUM_LLM_MODEL" in captured.err


def test_cli_screen_instantiates_real_scc_provider_without_network(monkeypatch, capsys, tmp_path):
    settings = LocalLLMSettings("http://127.0.0.1:1234", "model_A", None, 12)

    class InventoryProvider:
        def __init__(self, received):
            assert received.model_id == "model_A"

        def list_model_records(self):
            return ({"key": "model_A", "display_name": "A", "loaded_instances": [
                {"id": "instance-1", "config": {"context_length": 8192}}
            ]},)

    class Report:
        def as_dict(self):
            return {"screen_schema_version": 1, "screen_status": "completed", "model_id": "model_A", "calls_attempted": 0,
                    "calls_completed": 0, "hard_blockers": []}

    captured = {}
    def fake_runner(provider, **kwargs):
        assert isinstance(provider, LMStudioSocialInterpretationProvider)
        assert provider.settings.model_id == "model_A"
        assert kwargs["deployment"]["loaded_model_instance_id"] == "instance-1"
        captured["provider"] = provider
        return Report()

    monkeypatch.setattr("vivarium.cognition.LocalLLMSettings.from_environment", classmethod(lambda cls, require_model=False: settings))
    monkeypatch.setattr("vivarium.cognition.LMStudioProvider", InventoryProvider)
    monkeypatch.setattr("vivarium.social_interpretation_bench.run_screen47", fake_runner)
    monkeypatch.setattr("vivarium.social_interpretation_bench.write_screen47_report", lambda *args, **kwargs: None)

    assert main(["social-interpretation-screen", "--model-id", "model_A",
                 "--report", str(tmp_path / "screen.json")]) == 0
    assert isinstance(captured["provider"], LMStudioSocialInterpretationProvider)
    assert "model_A" in capsys.readouterr().out


def test_cli_screen_default_report_namespace_is_stable(monkeypatch, tmp_path):
    settings = LocalLLMSettings("http://127.0.0.1:1234", "model_A", None, 12)

    class InventoryProvider:
        def __init__(self, received): pass

        def list_model_records(self):
            return ({"key": "model_A", "loaded_instances": [{"id": "instance-1", "config": {"context_length": 8192}}]},)

    class Report:
        def as_dict(self):
            return {"screen_schema_version": 1, "screen_status": "completed", "model_id": "model_A", "calls_attempted": 0,
                    "calls_completed": 0, "hard_blockers": []}

    paths = {}
    monkeypatch.setattr("vivarium.cognition.LocalLLMSettings.from_environment", classmethod(lambda cls, require_model=False: settings))
    monkeypatch.setattr("vivarium.cognition.LMStudioProvider", InventoryProvider)
    monkeypatch.setattr("vivarium.social_interpretation_bench.run_screen47", lambda provider, **kwargs: Report())
    monkeypatch.setattr("vivarium.social_interpretation_bench.write_screen47_report",
                        lambda report, principal, review, *, paired_path=None: paths.update(
                            principal=principal, review=review, paired=paired_path))

    assert main(["social-interpretation-screen", "--model-id", "model_A"]) == 0
    assert paths["principal"].name.startswith("screen_model_a_")
    assert paths["principal"].suffix == ".json"
    assert paths["review"].name == f"{paths['principal'].stem}_review.json"
    assert paths["paired"].name == f"{paths['principal'].stem}_paired.json"


def test_cli_screen_custom_reports_use_distinct_atomic_namespaces(monkeypatch, tmp_path):
    settings = LocalLLMSettings("http://127.0.0.1:1234", "model_A", None, 12)

    class InventoryProvider:
        def __init__(self, received): pass

        def list_model_records(self):
            return ({"key": "model_A", "loaded_instances": [{"id": "instance-1", "config": {"context_length": 8192}}]},)

    class Report:
        def as_dict(self):
            return {"screen_schema_version": 1, "screen_status": "completed", "model_id": "model_A", "calls_attempted": 0,
                    "calls_completed": 0, "hard_blockers": []}

    calls = []
    monkeypatch.setattr("vivarium.cognition.LocalLLMSettings.from_environment", classmethod(lambda cls, require_model=False: settings))
    monkeypatch.setattr("vivarium.cognition.LMStudioProvider", InventoryProvider)
    monkeypatch.setattr("vivarium.social_interpretation_bench.run_screen47", lambda provider, **kwargs: Report())
    monkeypatch.setattr("vivarium.social_interpretation_bench.write_screen47_report",
                        lambda report, principal, review, *, paired_path=None: calls.append((principal, review, paired_path)))

    first = tmp_path / "candidate_one.json"
    second = tmp_path / "candidate_two.json"
    assert main(["social-interpretation-screen", "--model-id", "model_A", "--report", str(first)]) == 0
    assert main(["social-interpretation-screen", "--model-id", "model_A", "--report", str(second)]) == 0
    assert [(p.name, r.name, q.name) for p, r, q in calls] == [
        ("candidate_one.json", "candidate_one_review.json", "candidate_one_paired.json"),
        ("candidate_two.json", "candidate_two_review.json", "candidate_two_paired.json"),
    ]


def test_cli_llm_smoke_reports_a_healthy_ephemeral_run(monkeypatch, capsys):
    class Report:
        model_id = "gemma-local"; character_key = "sophie"; decision = "traverse"
        connector_key = "porte_entree"; target_location_key = "salon"
        validation_status = "accepted"; validation_reason = None; event_type = "character_moved"
        healthy = True

    monkeypatch.setattr("vivarium.cognition_smoke.run_local_cognition_smoke", lambda settings, character_key: Report())
    assert main(["llm-smoke"]) == 0
    output = capsys.readouterr().out
    assert "porte_entree -> salon" in output and "base mémoire jetable" in output


def test_cli_llm_calibrate_reports_a_healthy_ephemeral_series(monkeypatch, capsys):
    class Trial:
        number = 1; outcome = "routed"; elapsed_ms = 12; decision = "no_action"
        validation_status = None; validation_reason = None; provider_error_code = None

    class Report:
        model_id = "gemma-local"; character_key = "sophie"; trials = (Trial(),)
        median_elapsed_ms = 12; outcome_counts = {"routed": 1}; decision_counts = {"no_action": 1}; healthy = True

    monkeypatch.setattr(
        "vivarium.local_llm_calibration.run_local_cognition_calibration",
        lambda provider, model_id, trials, character_key: Report(),
    )
    assert main(["llm-calibrate", "--trials", "1"]) == 0
    output = capsys.readouterr().out
    assert "Calibration LLM jetable" in output and "Médiane : 12 ms" in output


def test_cli_scene_smoke_reports_a_healthy_ephemeral_turn(monkeypatch, capsys):
    class Report:
        model_id = "gemma-local"; decision = "speak"; act_kind = "greet"; content = "Salut."
        provider_error_code = None; validation_error_code = None; deferred_reason_code = None; healthy = True

    monkeypatch.setattr("vivarium.scene_turn_smoke.run_local_scene_turn_smoke", lambda settings: Report())
    assert main(["scene-smoke"]) == 0
    output = capsys.readouterr().out
    assert "Essai de scène jetable" in output and "parole        : Salut." in output


def test_cli_scene_bench_reports_a_healthy_ephemeral_conversation(monkeypatch, capsys):
    class Opportunity:
        turn_number = 1; speaker_key = "sophie"
    class Result:
        decision = type("Decision", (), {"action": "speak"})(); speech = {"content": "Salut."}
        provider_error_code = None; validation_error_code = None; deferred_reason_code = None
    class Report:
        turns = (type("Turn", (), {"opportunity": Opportunity(), "result": Result()})(),)
        final_scene = {"acts": ({"content": "Salut."},)}; healthy = True

    monkeypatch.setattr("vivarium.scene_bench.run_scene_bench", lambda provider, limits, max_turns: Report())
    assert main(["scene-bench", "--max-turns", "1"]) == 0
    output = capsys.readouterr().out
    assert "Banc de scène jetable" in output and "tour 1: sophie" in output


def test_cli_mvp_preflight_reads_a_candidate_without_modifying_it(tmp_path, capsys):
    db = tmp_path / "candidate.sqlite"
    conn = connect_database(db)
    try:
        ensure_schema(conn)
        IntegrationWorldService(conn).create_initial_world()
    finally:
        conn.close()
    before = db.read_bytes()

    assert main(["mvp-preflight", "--db", str(db)]) == 0
    output = capsys.readouterr().out
    assert "Prévol MVP" in output
    assert "prêt structurellement" in output
    assert db.read_bytes() == before


def test_cli_mvp_preflight_refuses_a_missing_database(tmp_path, capsys):
    missing = tmp_path / "missing.sqlite"

    assert main(["mvp-preflight", "--db", str(missing)]) == 2
    assert "base introuvable" in capsys.readouterr().err


def test_cli_mvp_init_builds_a_new_preflight_ready_candidate(tmp_path, capsys):
    db = tmp_path / "mvp.sqlite"

    assert main(["mvp-init", "--db", str(db), "--name", "MVP test"]) == 0
    assert db.is_file()
    output = capsys.readouterr().out
    assert "Prévol : prêt structurellement" in output
    assert main(["mvp-init", "--db", str(db)]) == 2
    assert "existe déjà" in capsys.readouterr().err


def test_cli_mvp_run_starts_and_stops_a_valid_candidate(tmp_path, capsys):
    db = tmp_path / "mvp-run.sqlite"
    assert main(["mvp-init", "--db", str(db)]) == 0

    assert main([
        "mvp-run", "--db", str(db), "--port", "0", "--tick-seconds", "0.25", "--max-ticks", "1",
    ]) == 0

    output = capsys.readouterr().out
    assert "tableau de contrôle" in output and "arrêté proprement" in output
