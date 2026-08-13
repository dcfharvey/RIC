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
