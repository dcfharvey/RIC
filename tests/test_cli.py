"""Tests de l'interface en ligne de commande (init / status)."""

import pytest

from vivarium.cli import main
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
