"""Tests de l'interface en ligne de commande (init / status)."""

import pytest

from vivarium.cli import main


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


def test_cli_llm_status_reports_a_missing_local_configuration(monkeypatch, capsys):
    monkeypatch.delenv("VIVARIUM_LLM_MODEL", raising=False)
    assert main(["llm-status"]) == 2
    assert "missing_llm_model" in capsys.readouterr().err
