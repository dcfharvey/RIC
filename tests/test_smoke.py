"""Test de fumée : import du package et cohérence de version."""

import tomllib
from pathlib import Path

import vivarium
from vivarium import __version__


def test_version_est_une_chaine_non_vide():
    assert isinstance(__version__, str)
    assert __version__


def test_package_importable():
    # Importe un module réel pour vérifier que le paquet est câblé.
    from vivarium import settings  # noqa: F401

    assert settings is not None


def test_version_package_coherente():
    metadata_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with metadata_path.open("rb") as source:
        metadata = tomllib.load(source)
    assert __version__ == metadata["project"]["version"] == "0.1.0a1"
