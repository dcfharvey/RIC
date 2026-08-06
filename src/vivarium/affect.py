"""Etats affectifs subjectifs, causés et auditables.

Le module conserve les épisodes et l'humeur sans leur attribuer le statut de
faits canoniques. Les propositions ultérieures du LLM devront passer par ces
contrats, avec une source privée accessible, avant toute écriture.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Mapping

from .db import transaction
from .registry import _KEY_RE
from .util import Clock, new_uuid


_FAMILIES = frozenset({"joy", "relief", "sadness", "anger", "fear", "shame", "guilt", "affection"})
_STATUSES = frozenset({"active", "resolved", "transformed"})


class AffectError(ValueError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _world_id(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise AffectError("monde invalide", code="invalid_affect")
    return value


def _key(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise AffectError(f"{label} invalide", code="invalid_affect")
    return value


def _milli(value: Any, label: str, *, signed: bool = False) -> int:
    low = -1000 if signed else 0
    if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= 1000:
        raise AffectError(f"{label} invalide", code="invalid_affect")
    return value


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise AffectError(f"{label} invalide", code="invalid_affect")
    return {str(key): item for key, item in value.items()}


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class AffectService:
    """Gère l'humeur diffuse et les épisodes causés d'un sujet seulement."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _character_id(self, world_id: int, character_key: str) -> int:
        row = self._conn.execute(
            "SELECT id FROM character WHERE world_id = ? AND key = ?", (world_id, character_key)
        ).fetchone()
        if row is None:
            raise AffectError("personnage introuvable", code="character_not_found")
        return row["id"]

    @staticmethod
    def _mood_sheet(row: sqlite3.Row) -> dict[str, Any]:
        return {"valence_milli": row["valence_milli"], "activation_milli": row["activation_milli"]}

    @staticmethod
    def _episode_sheet(row: sqlite3.Row, target_key: str | None) -> dict[str, Any]:
        return {
            "episode_key": row["episode_key"], "family": row["family"], "target_character_key": target_key,
            "appraisal": json.loads(row["appraisal_json"]), "intensity_milli": row["intensity_milli"],
            "action_tendency": row["action_tendency"], "expression_milli": row["expression_milli"],
            "status": row["status"],
        }

    def set_mood(
        self, world_id: Any, character_key: Any, *, valence_milli: Any, activation_milli: Any,
        reason: Any,
    ) -> dict[str, Any]:
        """Initialise ou modifie l'humeur via un événement audité explicite."""
        world_id = _world_id(world_id)
        character_key = _key(character_key, "personnage")
        valence_milli = _milli(valence_milli, "valence", signed=True)
        activation_milli = _milli(activation_milli, "activation", signed=True)
        reason = _key(reason, "raison")
        character_id = self._character_id(world_id, character_key)
        now = self._clock.now_iso()
        with transaction(self._conn) as conn:
            row = conn.execute(
                "SELECT * FROM mood_state WHERE world_id = ? AND character_id = ?", (world_id, character_id)
            ).fetchone()
            if row is None:
                cur = conn.execute(
                    "INSERT INTO mood_state (public_id, world_id, character_id, valence_milli, activation_milli, last_event_id, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, NULL, ?, ?)",
                    (new_uuid(), world_id, character_id, valence_milli, activation_milli, now, now),
                )
                mood_id, event_type = cur.lastrowid, "mood_initialized"
            else:
                mood_id, event_type = row["id"], "mood_changed"
            event = conn.execute(
                "INSERT INTO mood_event (world_id, character_id, mood_id, event_type, payload_json, recorded_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (world_id, character_id, mood_id, event_type, _json({"reason": reason, "valence_milli": valence_milli, "activation_milli": activation_milli}), now),
            )
            conn.execute(
                "UPDATE mood_state SET valence_milli = ?, activation_milli = ?, last_event_id = ?, updated_at = ? WHERE id = ?",
                (valence_milli, activation_milli, event.lastrowid, now, mood_id),
            )
        row = self._conn.execute("SELECT * FROM mood_state WHERE id = ?", (mood_id,)).fetchone()
        assert row is not None
        return self._mood_sheet(row)

    def mood(self, world_id: Any, character_key: Any) -> dict[str, Any] | None:
        world_id = _world_id(world_id)
        character_id = self._character_id(world_id, _key(character_key, "personnage"))
        row = self._conn.execute(
            "SELECT * FROM mood_state WHERE world_id = ? AND character_id = ?", (world_id, character_id)
        ).fetchone()
        return None if row is None else self._mood_sheet(row)

    def start_episode(
        self,
        world_id: Any,
        character_key: Any,
        episode_key: Any,
        *,
        family: Any,
        appraisal: Any,
        cause_trace_key: Any,
        intensity_milli: Any,
        action_tendency: Any,
        expression_milli: Any,
        target_character_key: Any = None,
    ) -> dict[str, Any]:
        world_id = _world_id(world_id)
        character_key = _key(character_key, "personnage")
        episode_key = _key(episode_key, "épisode")
        if family not in _FAMILIES:
            raise AffectError("famille émotionnelle invalide", code="invalid_affect")
        appraisal = _object(appraisal, "évaluation")
        cause_trace_key = _key(cause_trace_key, "source")
        intensity_milli = _milli(intensity_milli, "intensité")
        action_tendency = _key(action_tendency, "tendance d'action")
        expression_milli = _milli(expression_milli, "expression")
        if target_character_key is not None:
            target_character_key = _key(target_character_key, "cible")
        character_id = self._character_id(world_id, character_key)
        target_id = None if target_character_key is None else self._character_id(world_id, target_character_key)
        now = self._clock.now_iso()
        with transaction(self._conn) as conn:
            trace = conn.execute(
                "SELECT id FROM subjective_trace WHERE world_id = ? AND character_id = ? AND request_key = ?",
                (world_id, character_id, cause_trace_key),
            ).fetchone()
            if trace is None:
                raise AffectError("cause émotionnelle non accessible", code="affect_source_not_accessible")
            existing = conn.execute(
                "SELECT episode.id, target.key AS target_key FROM emotion_episode episode "
                "LEFT JOIN character target ON target.id = episode.target_character_id "
                "WHERE episode.world_id = ? AND episode.character_id = ? AND episode.episode_key = ?",
                (world_id, character_id, episode_key),
            ).fetchone()
            if existing is not None:
                row = conn.execute("SELECT * FROM emotion_episode WHERE id = ?", (existing["id"],)).fetchone()
                assert row is not None
                return self._episode_sheet(row, existing["target_key"])
            cur = conn.execute(
                "INSERT INTO emotion_episode "
                "(public_id, world_id, character_id, episode_key, family, target_character_id, appraisal_json, cause_trace_id, "
                "intensity_milli, action_tendency, expression_milli, status, last_event_id, created_at, resolved_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', NULL, ?, NULL)",
                (new_uuid(), world_id, character_id, episode_key, family, target_id, _json(appraisal), trace["id"], intensity_milli, action_tendency, expression_milli, now),
            )
            episode_id = cur.lastrowid
            event = conn.execute(
                "INSERT INTO emotion_event (world_id, character_id, episode_id, event_type, payload_json, recorded_at) "
                "VALUES (?, ?, ?, 'emotion_started', ?, ?)",
                (world_id, character_id, episode_id, _json({"episode_key": episode_key, "cause_trace": cause_trace_key}), now),
            )
            conn.execute("UPDATE emotion_episode SET last_event_id = ? WHERE id = ?", (event.lastrowid, episode_id))
        row = self._conn.execute("SELECT * FROM emotion_episode WHERE id = ?", (episode_id,)).fetchone()
        assert row is not None
        return self._episode_sheet(row, target_character_key)

    def resolve_episode(self, world_id: Any, character_key: Any, episode_key: Any, *, reason: Any) -> dict[str, Any]:
        world_id = _world_id(world_id)
        character_key = _key(character_key, "personnage")
        episode_key = _key(episode_key, "épisode")
        reason = _key(reason, "raison")
        character_id = self._character_id(world_id, character_key)
        now = self._clock.now_iso()
        with transaction(self._conn) as conn:
            row = conn.execute(
                "SELECT episode.*, target.key AS target_key FROM emotion_episode episode "
                "LEFT JOIN character target ON target.id = episode.target_character_id "
                "WHERE episode.world_id = ? AND episode.character_id = ? AND episode.episode_key = ?",
                (world_id, character_id, episode_key),
            ).fetchone()
            if row is None:
                raise AffectError("épisode introuvable", code="emotion_not_found")
            if row["status"] != "active":
                return self._episode_sheet(row, row["target_key"])
            event = conn.execute(
                "INSERT INTO emotion_event (world_id, character_id, episode_id, event_type, payload_json, recorded_at) "
                "VALUES (?, ?, ?, 'emotion_resolved', ?, ?)",
                (world_id, character_id, row["id"], _json({"reason": reason}), now),
            )
            conn.execute(
                "UPDATE emotion_episode SET status = 'resolved', last_event_id = ?, resolved_at = ? WHERE id = ?",
                (event.lastrowid, now, row["id"]),
            )
        row = self._conn.execute(
            "SELECT episode.*, target.key AS target_key FROM emotion_episode episode "
            "LEFT JOIN character target ON target.id = episode.target_character_id WHERE episode.id = ?", (row["id"],)
        ).fetchone()
        assert row is not None
        return self._episode_sheet(row, row["target_key"])

    def active_episodes(self, world_id: Any, character_key: Any, *, limit: int = 10) -> tuple[dict[str, Any], ...]:
        world_id = _world_id(world_id)
        character_id = self._character_id(world_id, _key(character_key, "personnage"))
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
            raise AffectError("limite d'épisodes invalide", code="invalid_affect")
        rows = self._conn.execute(
            "SELECT episode.*, target.key AS target_key FROM emotion_episode episode "
            "LEFT JOIN character target ON target.id = episode.target_character_id "
            "WHERE episode.world_id = ? AND episode.character_id = ? AND episode.status = 'active' "
            "ORDER BY episode.created_at DESC, episode.id DESC LIMIT ?",
            (world_id, character_id, limit),
        ).fetchall()
        return tuple(self._episode_sheet(row, row["target_key"]) for row in rows)
