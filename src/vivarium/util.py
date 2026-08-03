"""Utilitaires standard du vivarium : UUID, heures et horloge injectable."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    pass


class ClockError(RuntimeError):
    """Heure incohérente (horloge réelle antérieure à l'ancre, ou set invalide)."""


def new_uuid() -> str:
    """Identifiant public UUID (bibliothèque standard)."""
    return str(uuid.uuid4())


def now_utc() -> str:
    """Horodatage UTC ISO 8601 (chaîne triable et persistante)."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def parse_iso(value: str) -> datetime:
    """Analyse une date ISO 8601 ; une date naive est traitée comme UTC."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def to_iso(dt: datetime) -> str:
    """Sérialise une date en ISO 8601 UTC (millisecondes)."""
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds")


class Clock:
    """Source d'heure injectable ; par défaut l'horloge réelle UTC.

    Les tests injectent un `Clock` déterministe (FakeClock) pour valider le
    comportement de l'horloge canonique sans attendre réellement.
    """

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def now_iso(self) -> str:
        return to_iso(self.now())
