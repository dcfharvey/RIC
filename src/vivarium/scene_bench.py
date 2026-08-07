"""Banc jetable d'une courte conversation, pilotée par occasions bornées."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from .cognition_policy import CognitionCallLimits
from .db import connect_database
from .integration_world import IntegrationWorldService
from .migrations import ensure_schema
from .scene_scheduler import SceneTurnOpportunity, SceneTurnScheduler
from .scene_turn import SceneTurnProvider, SceneTurnResult, SceneTurnService
from .scenes import SocialSceneService
from .traversal import TraversalEngine
from .util import Clock, to_iso


_BENCH_TIME = datetime(2026, 8, 6, 23, 30, tzinfo=timezone.utc)


class _SceneBenchClock(Clock):
    def now(self) -> datetime:
        return _BENCH_TIME

    def now_iso(self) -> str:
        return to_iso(self.now())


@dataclass(frozen=True)
class SceneBenchTurn:
    opportunity: SceneTurnOpportunity
    result: SceneTurnResult


@dataclass(frozen=True)
class SceneBenchReport:
    turns: tuple[SceneBenchTurn, ...]
    final_scene: dict[str, Any]

    @property
    def healthy(self) -> bool:
        return bool(self.turns) and all(
            turn.result.provider_error_code is None and turn.result.validation_error_code is None
            for turn in self.turns
        )


def run_scene_bench(
    provider: SceneTurnProvider,
    limits: CognitionCallLimits,
    *,
    max_turns: int = 4,
    on_turn: Callable[[SceneBenchTurn], None] | None = None,
) -> SceneBenchReport:
    """Déroule au plus ``max_turns`` occasions, sans disque ni monde partagé."""
    conn: sqlite3.Connection = connect_database(":memory:")
    try:
        ensure_schema(conn)
        clock = _SceneBenchClock()
        world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
        for character_key in ("sophie", "erika"):
            TraversalEngine(conn, clock=clock).traverse_character(world_id, character_key, "porte_entree", "salon")
        scenes = SocialSceneService(conn, clock=clock)
        scenes.open(world_id, "arrival_chat", ["sophie", "erika"])
        scheduler, service = SceneTurnScheduler(conn), SceneTurnService(conn, provider, clock=clock)
        turns: list[SceneBenchTurn] = []
        while opportunity := scheduler.next_opportunity(world_id, "arrival_chat", max_turns=max_turns):
            result = service.run(world_id, opportunity.scene_key, opportunity.speaker_key, opportunity.turn_key, limits)
            turn = SceneBenchTurn(opportunity, result)
            turns.append(turn)
            if on_turn is not None:
                on_turn(turn)
            if result.provider_error_code is not None or result.validation_error_code is not None:
                break
        return SceneBenchReport(tuple(turns), scenes.sheet(world_id, "arrival_chat"))
    finally:
        conn.close()
