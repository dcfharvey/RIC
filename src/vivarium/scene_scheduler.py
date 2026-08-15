"""Occasions de parole déterministes et bornées pour une scène active."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from .registry import KEY_RE as _KEY_RE
from .scenes import SceneError, SocialSceneService


class SceneSchedulerError(ValueError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _key(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise SceneSchedulerError(f"{label} invalide", code="invalid_scene_scheduler")
    return value


def _world_id(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise SceneSchedulerError("monde invalide", code="invalid_scene_scheduler")
    return value


def _max_turns(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 20:
        raise SceneSchedulerError("borne de tours invalide", code="invalid_scene_scheduler")
    return value


@dataclass(frozen=True)
class SceneTurnOpportunity:
    scene_key: str
    turn_number: int
    speaker_key: str
    turn_key: str


class SceneTurnScheduler:
    """Offre à tour de rôle une occasion, sans imposer de parole.

    La rotation est une convention d'orchestration reproductible, pas une
    psychologie : la résidente peut toujours retourner `no_action`. La borne
    par scène prévient une boucle de dialogue incontrôlée.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @staticmethod
    def _prefix(scene_key: str) -> str:
        return f"scene-{scene_key}-turn-"

    def _used_turns(self, world_id: int, scene_key: str) -> tuple[int, ...]:
        prefix = self._prefix(scene_key)
        rows = self._conn.execute(
            "SELECT source_key FROM cognition_call_admission WHERE world_id = ? AND trigger = 'scene_turn'",
            (world_id,),
        ).fetchall()
        numbers: list[int] = []
        for row in rows:
            suffix = row["source_key"].removeprefix(prefix)
            if row["source_key"].startswith(prefix) and suffix.isdecimal() and int(suffix) >= 1:
                numbers.append(int(suffix))
        return tuple(sorted(set(numbers)))

    def next_opportunity(self, world_id: Any, scene_key: Any, *, max_turns: Any = 4) -> SceneTurnOpportunity | None:
        world_id, scene_key, max_turns = _world_id(world_id), _key(scene_key, "scène"), _max_turns(max_turns)
        try:
            sheet = SocialSceneService(self._conn).sheet(world_id, scene_key)
        except SceneError as exc:
            raise SceneSchedulerError(str(exc), code=exc.code) from exc
        if sheet["status"] != "active":
            return None
        used = self._used_turns(world_id, scene_key)
        turn_number = (max(used) if used else 0) + 1
        if turn_number > max_turns:
            return None
        participants = sheet["participants"]
        if not participants:
            raise SceneSchedulerError("scène sans participante", code="invalid_scene_scheduler")
        speaker_key = participants[(turn_number - 1) % len(participants)]
        try:
            SocialSceneService(self._conn).turn_context(world_id, scene_key, speaker_key)
        except SceneError as exc:
            raise SceneSchedulerError(str(exc), code=exc.code) from exc
        return SceneTurnOpportunity(scene_key, turn_number, speaker_key, self._prefix(scene_key) + str(turn_number))
