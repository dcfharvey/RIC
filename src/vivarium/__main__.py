"""Point d'entrée minimal du vivarium (Python -m vivarium).

Phase 0 : affiche la version et la configuration. Aucun service n'est
encore démarré.
"""

from __future__ import annotations

import logging

from . import __version__
from .logging_setup import configure_logging
from .settings import Settings

log = logging.getLogger("vivarium")


def main() -> int:
    settings = Settings()
    configure_logging(settings)
    log.info("Vivarium social artificiel, version %s", __version__)
    log.info("Données  : %s", settings.data_dir)
    log.info("Journaux : %s", settings.log_dir)
    log.info("Config   : %s", settings.config_dir)
    print(f"vivarium-social {__version__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
