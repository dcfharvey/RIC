"""Test de fumée de la Phase 0 : import du package et version."""

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
    assert __version__ == "0.1.0"
