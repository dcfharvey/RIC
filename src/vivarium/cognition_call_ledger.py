"""Journal technique append-only des admissions d'appels cognitifs.

Ce journal n'est ni un fait canonique, ni une mémoire subjective. Il fournit
seulement à la politique pure l'historique stable qui protège les appels LLM
des retries, des rafales et du dépassement de budget.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from .cognition_policy import (
    CognitionCallLimits,
    CognitionCallPolicy,
    CognitionCallPolicyError,
    CognitionCallRecord,
    CognitionCallRequest,
    CognitionCallVerdict,
)
from .db import transaction
from .registry import _KEY_RE
from .util import Clock, new_uuid
from .world import WorldEngine


class CognitionCallLedgerError(ValueError):
    """Refus explicite de la frontière technique des appels cognitifs."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _world_id(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise CognitionCallLedgerError("monde invalide", code="invalid_cognition_call_request")
    return value


def _key(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise CognitionCallLedgerError(f"{label} invalide", code="invalid_cognition_call_request")
    return value


@dataclass(frozen=True)
class CognitionCallAdmission:
    """Verdict de politique et, seulement si admis, trace persistée associée."""

    verdict: CognitionCallVerdict
    admission_id: str | None
    admitted_at: str | None


class CognitionCallLedgerService:
    """Insère une admission une fois, ou retourne un refus sans mutation.

    L'heure est obtenue de l'horloge canonique du monde : un adaptateur LLM ne
    peut ni fournir sa propre cadence ni modifier le journal directement.
    """

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def _character_id(conn: sqlite3.Connection, world_id: int, character_key: str) -> int:
        row = conn.execute(
            "SELECT id FROM character WHERE world_id = ? AND key = ?", (world_id, character_key)
        ).fetchone()
        if row is None:
            raise CognitionCallLedgerError("personnage introuvable", code="character_not_found")
        return row["id"]

    @staticmethod
    def _history(conn: sqlite3.Connection, world_id: int, character_id: int) -> tuple[CognitionCallRecord, ...]:
        rows = conn.execute(
            "SELECT ch.key AS character_key, a.trigger, a.source_key, a.admitted_at "
            "FROM cognition_call_admission a JOIN character ch ON ch.id = a.character_id "
            "WHERE a.world_id = ? AND a.character_id = ? ORDER BY a.admitted_at, a.id",
            (world_id, character_id),
        ).fetchall()
        return tuple(CognitionCallRecord(row["character_key"], row["trigger"], row["source_key"], row["admitted_at"]) for row in rows)

    def history(self, world_id: Any, character_key: Any) -> tuple[CognitionCallRecord, ...]:
        world_id, character_key = _world_id(world_id), _key(character_key, "personnage")
        character_id = self._character_id(self._conn, world_id, character_key)
        return self._history(self._conn, world_id, character_id)

    def admit(
        self,
        world_id: Any,
        character_key: Any,
        trigger: Any,
        source_key: Any,
        limits: Any,
    ) -> CognitionCallAdmission:
        world_id, character_key = _world_id(world_id), _key(character_key, "personnage")
        trigger, source_key = _key(trigger, "motif"), _key(source_key, "source")
        if not isinstance(limits, CognitionCallLimits):
            raise CognitionCallLedgerError("limites d'appel invalides", code="invalid_cognition_call_limits")
        try:
            limits.validated()
        except CognitionCallPolicyError as exc:
            raise CognitionCallLedgerError(str(exc), code=exc.code) from exc

        with transaction(self._conn) as conn:
            character_id = self._character_id(conn, world_id, character_key)
            try:
                now = WorldEngine(conn, clock=self._clock).read_canonical_time(world_id)
                request = CognitionCallRequest(character_key, trigger, source_key, now).validated()
                verdict = CognitionCallPolicy.evaluate(request, self._history(conn, world_id, character_id), limits)
            except CognitionCallPolicyError as exc:
                raise CognitionCallLedgerError(str(exc), code=exc.code) from exc
            if not verdict.eligible:
                return CognitionCallAdmission(verdict, None, None)
            admission_id = new_uuid()
            conn.execute(
                "INSERT INTO cognition_call_admission "
                "(public_id, world_id, character_id, trigger, source_key, idempotency_key, admitted_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (admission_id, world_id, character_id, request.trigger, request.source_key,
                 verdict.idempotency_key, now),
            )
            return CognitionCallAdmission(verdict, admission_id, now)
