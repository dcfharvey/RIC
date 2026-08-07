"""Essai réel et jetable d'un unique tour de parole dans une scène."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .cognition import LocalLLMSettings
from .cognition_policy import CognitionCallLimits
from .db import connect_database
from .integration_world import IntegrationWorldService
from .migrations import ensure_schema
from .scene_turn import LMStudioSceneTurnProvider, SceneTurnService
from .scenes import SocialSceneService
from .traversal import TraversalEngine
from .util import Clock, to_iso


_SMOKE_TIME = datetime(2026, 8, 6, 22, 15, tzinfo=timezone.utc)


class _SceneSmokeClock(Clock):
    def now(self) -> datetime:
        return _SMOKE_TIME

    def now_iso(self) -> str:
        return to_iso(self.now())


@dataclass(frozen=True)
class SceneTurnSmokeReport:
    model_id: str
    decision: str | None
    act_kind: str | None
    content: str | None
    provider_error_code: str | None
    validation_error_code: str | None
    deferred_reason_code: str | None
    schema_version: int = 1

    @property
    def healthy(self) -> bool:
        return self.decision is not None and self.provider_error_code is None and self.validation_error_code is None

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "model_id": self.model_id,
            "decision": self.decision,
            "act_kind": self.act_kind,
            "content": self.content,
            "provider_error_code": self.provider_error_code,
            "validation_error_code": self.validation_error_code,
            "deferred_reason_code": self.deferred_reason_code,
            "healthy": self.healthy,
        }


def run_local_scene_turn_smoke(settings: LocalLLMSettings) -> SceneTurnSmokeReport:
    """Construit une mini-scène Sophie-Erika, sans toucher aucun monde sur disque."""
    conn: sqlite3.Connection = connect_database(":memory:")
    try:
        ensure_schema(conn)
        clock = _SceneSmokeClock()
        world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
        for character_key in ("sophie", "erika"):
            TraversalEngine(conn, clock=clock).traverse_character(
                world_id, character_key, "porte_entree", "salon"
            )
        SocialSceneService(conn, clock=clock).open(world_id, "arrival_chat", ["sophie", "erika"])
        result = SceneTurnService(
            conn, LMStudioSceneTurnProvider(settings), clock=clock
        ).run(
            world_id,
            "arrival_chat",
            "sophie",
            "arrival_sophie_turn_1",
            CognitionCallLimits(0, 3_600, 1),
        )
        return SceneTurnSmokeReport(
            settings.model_id,
            None if result.decision is None else result.decision.action,
            None if result.decision is None else result.decision.act_kind,
            None if result.speech is None else result.speech["content"],
            result.provider_error_code,
            result.validation_error_code,
            result.deferred_reason_code,
        )
    finally:
        conn.close()
