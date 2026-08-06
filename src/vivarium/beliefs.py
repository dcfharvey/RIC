"""Croyances privées sourcées, distinctes de la vérité canonique.

Ce premier lot implémente l'adoption et la révision traçable d'une
croyance. Il ne prétend pas encore modéliser les hypothèses concurrentes,
les modèles sociaux de source ou la pertinence sémantique d'une preuve : ces
extensions ne doivent pas être simulées par une confiance inventée.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Mapping

from .db import transaction
from .registry import _KEY_RE
from .util import Clock, new_uuid


_POLARITIES = frozenset({"true", "false", "uncertain"})
_VISIBILITIES = frozenset({"private", "shared", "declared"})


class BeliefError(ValueError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _key(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise BeliefError(f"{label} invalide", code="invalid_belief")
    return value


def _world_id(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise BeliefError("monde invalide", code="invalid_belief")
    return value


def _milli(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 1000:
        raise BeliefError(f"{label} invalide", code="invalid_belief")
    return value


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise BeliefError(f"{label} invalide", code="invalid_belief")
    return {str(key): item for key, item in value.items()}


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class BeliefService:
    """Crée des croyances seulement à partir d'une trace du même sujet."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _character_id(self, world_id: int, character_key: str) -> int:
        row = self._conn.execute(
            "SELECT id FROM character WHERE world_id = ? AND key = ?", (world_id, character_key)
        ).fetchone()
        if row is None:
            raise BeliefError("personnage introuvable", code="character_not_found")
        return row["id"]

    @staticmethod
    def _sheet(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "belief_key": row["belief_key"],
            "question_key": row["question_key"],
            "proposition": json.loads(row["proposition_json"]),
            "polarity": row["polarity"],
            "confidence_milli": row["confidence_milli"],
            "status": row["status"],
            "visibility": row["visibility"],
        }

    def adopt(
        self,
        world_id: Any,
        character_key: Any,
        belief_key: Any,
        *,
        question_key: Any,
        proposition: Any,
        polarity: Any,
        confidence_milli: Any,
        trace_request_key: Any,
        diagnosticity_milli: Any = 500,
        source_reliability_milli: Any = 500,
        visibility: Any = "private",
        revision_of_key: Any = None,
    ) -> dict[str, Any]:
        world_id = _world_id(world_id)
        character_key = _key(character_key, "personnage")
        belief_key = _key(belief_key, "croyance")
        question_key = _key(question_key, "question")
        trace_request_key = _key(trace_request_key, "source")
        proposition = _object(proposition, "proposition")
        confidence_milli = _milli(confidence_milli, "confiance")
        diagnosticity_milli = _milli(diagnosticity_milli, "diagnosticité")
        source_reliability_milli = _milli(source_reliability_milli, "fiabilité")
        if polarity not in _POLARITIES or visibility not in _VISIBILITIES:
            raise BeliefError("statut de croyance invalide", code="invalid_belief")
        if revision_of_key is not None:
            revision_of_key = _key(revision_of_key, "révision")

        character_id = self._character_id(world_id, character_key)
        now = self._clock.now_iso()
        with transaction(self._conn) as conn:
            trace = conn.execute(
                "SELECT id FROM subjective_trace WHERE world_id = ? AND character_id = ? AND request_key = ?",
                (world_id, character_id, trace_request_key),
            ).fetchone()
            if trace is None:
                raise BeliefError("source non accessible", code="belief_source_not_accessible")

            prior = None
            if revision_of_key is not None:
                prior = conn.execute(
                    "SELECT id, status FROM subjective_belief WHERE world_id = ? AND character_id = ? AND belief_key = ?",
                    (world_id, character_id, revision_of_key),
                ).fetchone()
                if prior is None:
                    raise BeliefError("croyance à réviser introuvable", code="belief_revision_not_found")
                if prior["status"] != "active":
                    raise BeliefError("croyance à réviser non active", code="belief_revision_not_active")

            cur = conn.execute(
                "INSERT INTO subjective_belief "
                "(public_id, world_id, character_id, belief_key, question_key, proposition_json, polarity, "
                "confidence_milli, status, visibility, revision_of_id, created_at, revised_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)",
                (
                    new_uuid(), world_id, character_id, belief_key, question_key, _json(proposition), polarity,
                    confidence_milli, visibility, None if prior is None else prior["id"], now, now,
                ),
            )
            belief_id = cur.lastrowid
            conn.execute(
                "INSERT INTO subjective_belief_evidence "
                "(belief_id, trace_id, polarity, diagnosticity_milli, source_reliability_milli, created_at) "
                "VALUES (?, ?, 'support', ?, ?, ?)",
                (belief_id, trace["id"], diagnosticity_milli, source_reliability_milli, now),
            )
            conn.execute(
                "INSERT INTO subjective_belief_event "
                "(world_id, character_id, belief_id, event_type, payload_json, recorded_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    world_id, character_id, belief_id,
                    "belief_revised" if prior is not None else "belief_adopted",
                    _json({"belief_key": belief_key, "source_trace": trace_request_key}), now,
                ),
            )
            if prior is not None:
                # La migration autorise ce seul changement après que la révision a
                # été écrite et auditée dans la même transaction.
                conn.execute(
                    "UPDATE subjective_belief SET status = 'contested', revised_at = ? WHERE id = ?",
                    (now, prior["id"]),
                )

        row = self._conn.execute("SELECT * FROM subjective_belief WHERE id = ?", (belief_id,)).fetchone()
        assert row is not None
        return self._sheet(row)

    def list(self, world_id: Any, character_key: Any, *, limit: int = 50) -> tuple[dict[str, Any], ...]:
        world_id = _world_id(world_id)
        character_key = _key(character_key, "personnage")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
            raise BeliefError("limite de croyances invalide", code="invalid_belief")
        character_id = self._character_id(world_id, character_key)
        rows = self._conn.execute(
            "SELECT * FROM subjective_belief WHERE world_id = ? AND character_id = ? "
            "ORDER BY created_at DESC, id DESC LIMIT ?",
            (world_id, character_id, limit),
        ).fetchall()
        return tuple(self._sheet(row) for row in rows)
