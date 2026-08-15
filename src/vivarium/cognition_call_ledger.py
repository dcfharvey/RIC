"""Journal technique append-only des admissions d'appels cognitifs.

Ce journal n'est ni un fait canonique, ni une mémoire subjective. Il fournit
seulement à la politique pure l'historique stable qui protège les appels LLM
des retries, des rafales et du dépassement de budget.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from .cognition_policy import (
    CALL_TRIGGER_PLANNED_REFLECTION,
    CognitionCallLimits,
    CognitionCallPolicy,
    CognitionCallPolicyError,
    CognitionCallRecord,
    CognitionCallRequest,
    CognitionCallVerdict,
)
from .cognitive_flow import CognitiveFlowRequest, CognitiveFlowScheduler, CognitiveFlowTelemetry
from .db import transaction
from .registry import KEY_RE as _KEY_RE
from .util import Clock, new_uuid, parse_iso, to_iso
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

    def __init__(
        self, conn: sqlite3.Connection, clock: Clock | None = None,
        flow_scheduler: CognitiveFlowScheduler | None = None,
    ) -> None:
        self._conn = conn
        self._clock = clock or Clock()
        self._flow_scheduler = flow_scheduler
        self._flow_telemetry = CognitiveFlowTelemetry(conn, clock=self._clock)

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

    @staticmethod
    def _autonomy_reservation(
        conn: sqlite3.Connection, world_id: int, character_id: int,
    ) -> int:
        """Réserve une place pour l'idle technique encore sans réflexion.

        La source reste le journal canonique ``activity_started`` et l'état
        actif courant; aucune mémoire de scheduler n'est introduite. Les
        retries d'autonomie restent protégés par la même règle car ils sont
        eux aussi des attentes techniques, non des choix comportementaux.
        """
        row = conn.execute(
            "SELECT e.seq FROM activity a "
            "JOIN character c ON c.id = a.character_id "
            "JOIN location l ON l.id = a.location_id "
            "JOIN canonical_event e ON e.world_id = a.world_id "
            "WHERE a.world_id = ? AND a.character_id = ? AND a.status = 'active' "
            "AND a.type = 'idle' AND e.event_type = 'activity_started' "
            "AND e.occurred_at = a.started_at "
            "AND json_extract(e.payload, '$.character') = c.key "
            "AND json_extract(e.payload, '$.activity') = 'idle' "
            "AND json_extract(e.payload, '$.location') = l.key "
            "AND json_extract(e.payload, '$.planned_end_at') = a.planned_end_at "
            "AND json_extract(e.payload, '$.action_provenance.origin') "
            "IN ('wo95_post_boundary_idle', 'cognition_retry') "
            "ORDER BY e.seq DESC LIMIT 1",
            (world_id, character_id),
        ).fetchone()
        if row is None:
            return 0
        source_key = f"idle_{int(row['seq'])}"
        already_admitted = conn.execute(
            "SELECT 1 FROM cognition_call_admission "
            "WHERE world_id = ? AND character_id = ? AND trigger = ? AND source_key = ? LIMIT 1",
            (world_id, character_id, CALL_TRIGGER_PLANNED_REFLECTION, source_key),
        ).fetchone()
        return 0 if already_admitted is not None else 1

    def verdict(
        self,
        world_id: Any,
        character_key: Any,
        trigger: Any,
        source_key: Any,
        limits: Any,
    ) -> CognitionCallVerdict:
        """Évalue une admission sans créer de journal technique.

        Ce contrôle sert aux schedulers qui doivent ignorer silencieusement une
        occasion encore techniquement fermée. L'admission persistée reste la
        seule autorité juste avant l'appel provider.
        """
        world_id, character_key = _world_id(world_id), _key(character_key, "personnage")
        trigger, source_key = _key(trigger, "motif"), _key(source_key, "source")
        if not isinstance(limits, CognitionCallLimits):
            raise CognitionCallLedgerError("limites d'appel invalides", code="invalid_cognition_call_limits")
        try:
            limits.validated()
            character_id = self._character_id(self._conn, world_id, character_key)
            now = WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id)
            request = CognitionCallRequest(character_key, trigger, source_key, now).validated()
            return CognitionCallPolicy.evaluate(
                request, self._history(self._conn, world_id, character_id), limits,
                reserved_calls=self._autonomy_reservation(self._conn, world_id, character_id),
            )
        except CognitionCallPolicyError as exc:
            raise CognitionCallLedgerError(str(exc), code=exc.code) from exc

    def retry_not_before(
        self,
        world_id: Any,
        character_key: Any,
        limits: Any,
        *,
        attempted_at: Any,
        reason_code: Any,
        retry_delay_seconds: Any,
    ) -> str:
        """Retourne la prochaine date techniquement admissible pour un retry.

        Les refus de budget et de debounce doivent attendre l'echeance calculee
        depuis le ledger persistant; les autres echecs techniques recoivent un
        petit delai explicite. Cette lecture ne cree ni admission ni tentative.
        """
        world_id, character_key = _world_id(world_id), _key(character_key, "personnage")
        if not isinstance(limits, CognitionCallLimits):
            raise CognitionCallLedgerError("limites d'appel invalides", code="invalid_cognition_call_limits")
        try:
            limits.validated()
        except CognitionCallPolicyError as exc:
            raise CognitionCallLedgerError(str(exc), code=exc.code) from exc
        if not isinstance(reason_code, str):
            raise CognitionCallLedgerError("raison de retry invalide", code="invalid_cognition_call_request")
        if not isinstance(retry_delay_seconds, int) or isinstance(retry_delay_seconds, bool) \
                or not 0 <= retry_delay_seconds <= 86_400:
            raise CognitionCallLedgerError("delai de retry invalide", code="invalid_cognition_call_request")
        try:
            attempt = parse_iso(attempted_at)
        except (TypeError, ValueError) as exc:
            raise CognitionCallLedgerError("date de tentative invalide", code="invalid_cognition_call_request") from exc
        if reason_code not in {"budget_exhausted", "debounced"}:
            return to_iso(attempt + timedelta(seconds=retry_delay_seconds))
        character_id = self._character_id(self._conn, world_id, character_key)
        if limits.max_calls_per_window is None and reason_code == "budget_exhausted":
            return to_iso(parse_iso(WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id)))
        now = parse_iso(WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id))
        history = self._history(self._conn, world_id, character_id)
        instants = tuple(parse_iso(record.admitted_at) for record in history)
        if reason_code == "budget_exhausted":
            inside = tuple(
                instant for instant in instants
                if (now - instant).total_seconds() < limits.budget_window_seconds
            )
            if len(inside) >= limits.max_calls_per_window:
                return to_iso(min(inside) + timedelta(seconds=limits.budget_window_seconds))
            return to_iso(now)
        if reason_code == "debounced":
            latest = max(instants, default=None)
            if latest is not None:
                return to_iso(latest + timedelta(seconds=limits.debounce_seconds))
            return to_iso(now)
        raise AssertionError("raison de retry non gérée")

    def retry_due(
        self,
        world_id: Any,
        character_key: Any,
        limits: Any,
        *,
        attempted_at: Any,
        reason_code: Any,
        retry_delay_seconds: Any,
    ) -> bool:
        """Indique si un retry peut etre tente sans creer de nouvelle ecriture."""
        world_id, character_key = _world_id(world_id), _key(character_key, "personnage")
        release_at = self.retry_not_before(
            world_id, character_key, limits,
            attempted_at=attempted_at,
            reason_code=reason_code,
            retry_delay_seconds=retry_delay_seconds,
        )
        if reason_code in {"budget_exhausted", "debounced"}:
            now = WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id)
        else:
            now = self._clock.now_iso()
        return parse_iso(now) >= parse_iso(release_at)

    def admit(
        self,
        world_id: Any,
        character_key: Any,
        trigger: Any,
        source_key: Any,
        limits: Any,
        *,
        source_event_seq: int | None = None,
        parent_event_seq: int | None = None,
    ) -> CognitionCallAdmission:
        world_id, character_key = _world_id(world_id), _key(character_key, "personnage")
        trigger, source_key = _key(trigger, "motif"), _key(source_key, "source")
        if not isinstance(limits, CognitionCallLimits):
            raise CognitionCallLedgerError("limites d'appel invalides", code="invalid_cognition_call_limits")
        try:
            limits.validated()
        except CognitionCallPolicyError as exc:
            raise CognitionCallLedgerError(str(exc), code=exc.code) from exc

        flow_request: CognitiveFlowRequest | None = None
        if self._flow_scheduler is not None:
            requested_at = WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id)
            flow_request = CognitiveFlowRequest(
                world_id, character_key, trigger, source_key, requested_at,
                source_event_seq=source_event_seq, parent_event_seq=parent_event_seq,
            )
            self._flow_telemetry.record(flow_request, "opportunity")
            offer = self._flow_scheduler.offer(flow_request)
            if offer.state != "ready":
                self._flow_telemetry.record(
                    flow_request, offer.state, reason_code=offer.reason_code,
                    wait_started_at=requested_at,
                )
                return CognitionCallAdmission(
                    CognitionCallVerdict("deferred", offer.reason_code, flow_request.idempotency_key),
                    None, None,
                )

        with transaction(self._conn) as conn:
            character_id = self._character_id(conn, world_id, character_key)
            try:
                now = WorldEngine(conn, clock=self._clock).read_canonical_time(world_id)
                request = CognitionCallRequest(character_key, trigger, source_key, now).validated()
                verdict = CognitionCallPolicy.evaluate(
                    request, self._history(conn, world_id, character_id), limits,
                    reserved_calls=self._autonomy_reservation(conn, world_id, character_id),
                )
            except CognitionCallPolicyError as exc:
                if flow_request is not None:
                    self._flow_scheduler.cancel(flow_request.idempotency_key)
                raise CognitionCallLedgerError(str(exc), code=exc.code) from exc
            if not verdict.eligible:
                if flow_request is not None:
                    self._flow_scheduler.cancel(flow_request.idempotency_key)
                state = "duplicate" if verdict.reason_code == "duplicate_call" else "refused"
                if flow_request is not None:
                    self._flow_telemetry.record(
                        flow_request, state, reason_code=verdict.reason_code, canonical_at=now,
                    )
                return CognitionCallAdmission(verdict, None, None)
            admission_id = new_uuid()
            conn.execute(
                "INSERT INTO cognition_call_admission "
                "(public_id, world_id, character_id, trigger, source_key, idempotency_key, admitted_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (admission_id, world_id, character_id, request.trigger, request.source_key,
                 verdict.idempotency_key, now),
            )
            if flow_request is not None:
                self._flow_telemetry.record(flow_request, "admitted", canonical_at=now)
                self._flow_scheduler.complete(flow_request.idempotency_key)
            return CognitionCallAdmission(verdict, admission_id, now)
