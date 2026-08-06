"""Essai réel, isolé et jetable de la frontière LLM locale.

Ce module n'est pas le banc d'essai canonique : il vérifie un fournisseur réel
chargé localement, donc son résultat peut varier. Il ne crée qu'une base SQLite
en mémoire et ne touche jamais au monde de développement ou au futur MVP.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .cognition import CognitionError, LMStudioProvider, LocalLLMSettings
from .cognition_policy import CognitionCallLimits
from .cognition_router import CognitionCallRouter
from .db import connect_database
from .integration_world import IntegrationWorldService
from .migrations import ensure_schema
from .repro import max_seq
from .traversal import TraversalEngine
from .util import Clock, to_iso


_SMOKE_TIME = datetime(2026, 8, 6, 20, 45, tzinfo=timezone.utc)


class _SmokeClock(Clock):
    """Horloge fixe : le contexte canonique de l'essai est reproductible."""

    def now(self) -> datetime:
        return _SMOKE_TIME

    def now_iso(self) -> str:
        return to_iso(self.now())


@dataclass(frozen=True)
class CognitionSmokeReport:
    """Rapport minimal d'un seul tour LLM sans effet durable."""

    model_id: str
    character_key: str
    observed_at: str
    decision: str
    connector_key: str | None
    target_location_key: str | None
    validation_status: str | None
    validation_reason: str | None
    event_type: str | None
    schema_version: int = 1

    @property
    def healthy(self) -> bool:
        """Un refus moteur est sain : il reste une décision validée, pas un crash."""
        return self.decision == "no_action" or self.validation_status in {"accepted", "refused"}

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "model_id": self.model_id,
            "character_key": self.character_key,
            "observed_at": self.observed_at,
            "decision": self.decision,
            "connector_key": self.connector_key,
            "target_location_key": self.target_location_key,
            "validation_status": self.validation_status,
            "validation_reason": self.validation_reason,
            "event_type": self.event_type,
            "healthy": self.healthy,
        }


def run_local_cognition_smoke(
    settings: LocalLLMSettings, *, character_key: str = "sophie"
) -> CognitionSmokeReport:
    """Appelle le LLM une fois, dans un monde d'intégration entièrement jetable."""
    conn: sqlite3.Connection = connect_database(":memory:")
    try:
        ensure_schema(conn)
        clock = _SmokeClock()
        world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
        TraversalEngine(conn, clock=clock).traverse_character(
            world_id, character_key, "porte_entree", "salon"
        )
        source_key = f"event_{max_seq(conn, world_id)}"
        routed = CognitionCallRouter(conn, LMStudioProvider(settings), clock=clock).run(
            world_id, character_key, "direct_event", source_key,
            f"smoke_{character_key}_direct", CognitionCallLimits(0, 3_600, 1),
        )
        if routed.provider_error_code is not None:
            raise CognitionError("essai LLM local indisponible", code=routed.provider_error_code)
        if routed.turn is None:
            raise CognitionError("essai LLM local non admis", code=routed.admission.verdict.reason_code)
        result, validation = routed.turn, routed.turn.validation
        return CognitionSmokeReport(
            model_id=settings.model_id,
            character_key=character_key,
            observed_at=result.context.observed_at,
            decision=result.decision.action,
            connector_key=result.decision.connector_key,
            target_location_key=result.decision.target_location_key,
            validation_status=validation.status if validation else None,
            validation_reason=validation.reason_code if validation else None,
            event_type=validation.facts[0].event_type if validation and validation.facts else None,
        )
    finally:
        conn.close()
