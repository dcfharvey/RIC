"""Utilitaires standard du vivarium (Phase 1)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


def new_uuid() -> str:
    """Identifiant public UUID (bibliothèque standard)."""
    return str(uuid.uuid4())


def now_utc() -> str:
    """Horodatage UTC ISO 8601 (chaîne triable et persistante)."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
