"""Mise en place des journaux du vivarium (Phase 0).

Utilise uniquement le module standard `logging`. Fournit une sortie console
et une sortie fichier dans le répertoire de journaux.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .settings import Settings

_LOGGER_NAME = "vivarium"


def configure_logging(settings: Settings | None = None) -> logging.Logger:
    """Configure et retourne le logger racine du vivarium.

    Appelée une seule fois au démarrage du processus. Idempotente : les
    appels ultérieurs ne dupliquent pas les handlers.
    """
    settings = settings or Settings()
    settings.ensure_directories()

    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:  # déjà configuré
        return logger

    logger.setLevel(settings.resolved_log_level)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    file_handler = logging.FileHandler(
        Path(settings.log_dir) / "vivarium.log", encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger
