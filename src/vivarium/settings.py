"""Configuration de base du vivarium (Phase 0).

Lit l'environnement et fournit des valeurs par défaut. Aucune logique
métier ici ; il s'agit seulement des réglages d'infrastructure.
Bibliothèque standard uniquement, sans dépendance externe.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Réglages d'infrastructure du vivarium, chargés depuis l'environnement."""

    # Répertoires (valeurs par défaut relatives au dépôt).
    data_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("VIVARIUM_DATA_DIR", "data")
        ).resolve()
    )
    log_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("VIVARIUM_LOG_DIR", "logs")
        ).resolve()
    )
    config_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("VIVARIUM_CONFIG_DIR", "config")
        ).resolve()
    )

    # Niveau de journalisation (ex. "INFO", "DEBUG").
    log_level: str = field(
        default_factory=lambda: os.environ.get("VIVARIUM_LOG_LEVEL", "INFO")
    )

    def ensure_directories(self) -> None:
        """Crée les répertoires de travail s'ils n'existent pas."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    @property
    def resolved_log_level(self) -> int:
        """Niveau de journalisation résolu vers un entier logging."""
        return getattr(logging, self.log_level.upper(), logging.INFO)
