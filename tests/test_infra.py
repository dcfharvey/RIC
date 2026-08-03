"""Tests de la configuration et des journaux (Phase 0)."""

import logging
import os

from vivarium.logging_setup import configure_logging
from vivarium.settings import Settings


def test_settings_par_defaut(monkeypatch):
    # Neutralise l'environnement hérité pour un résultat déterministe.
    for var in ("VIVARIUM_DATA_DIR", "VIVARIUM_LOG_DIR", "VIVARIUM_CONFIG_DIR"):
        monkeypatch.delenv(var, raising=False)
    s = Settings()
    assert s.log_level == "INFO"
    assert "logs" in str(s.log_dir)


def test_settings_lecture_environnement(monkeypatch, tmp_path):
    monkeypatch.setenv("VIVARIUM_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("VIVARIUM_LOG_DIR", str(tmp_path))
    s = Settings()
    assert s.log_level == "DEBUG"
    assert s.resolved_log_level == logging.DEBUG
    assert s.log_dir == tmp_path.resolve()


def test_ensure_directories_est_idempotent(monkeypatch, tmp_path):
    monkeypatch.setenv("VIVARIUM_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("VIVARIUM_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("VIVARIUM_CONFIG_DIR", str(tmp_path / "config"))
    s = Settings()
    s.ensure_directories()
    s.ensure_directories()  # ne doit pas lever
    assert (tmp_path / "data").is_dir()


def test_configure_logging_est_idempotent(monkeypatch, tmp_path):
    monkeypatch.setenv("VIVARIUM_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("VIVARIUM_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("VIVARIUM_CONFIG_DIR", str(tmp_path / "config"))
    logger1 = configure_logging(Settings())
    logger2 = configure_logging(Settings())
    # Deux appels ne doivent pas dupliquer les handlers.
    assert logger1 is logger2
    assert len(logger1.handlers) >= 2  # console + fichier
