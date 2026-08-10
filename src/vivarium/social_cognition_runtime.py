"""Raccordement vivant borné : SCC-0 -> SCC-1C -> SCC-1B."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from .cognition_call_ledger import CognitionCallLedgerService
from .cognition import CognitionError
from .cognition_policy import CALL_TRIGGER_SOCIAL_INTERPRETATION, CognitionCallLimits
from .social_appraisal_runtime import LiveSocialAppraisalService
from .scc3a_affect_runtime import LiveSCC3AAffectService
from .scenes import SceneError, SocialSceneService
from .scc1c import SCC1CAdmission, SCC1CAdmissionService, SCC1CError
from .social_interpretation import SocialInterpretationError
from .social_interpretation_provider import (
    SocialInterpretationLLMService,
    SocialInterpretationProviderError,
)
from .subjective_memory import SubjectiveMemoryError, SubjectiveMemoryService
from .util import Clock, parse_iso
from .world import WorldEngine


RETRY_DELAY_SECONDS = 30


@dataclass(frozen=True)
class LiveSocialCognitionOutcome:
    character_key: str
    trace_request_key: str | None
    admission: str
    technical_status: str | None
    detail_code: str | None
    interpretation_key: str | None
    appraisal_status: str | None = None
    appraisal_candidate_count: int = 0
    appraisal_technical_status: str | None = None
    affect_statuses: tuple[str, ...] = ()


class LiveSocialCognitionError(ValueError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class LiveSocialCognitionService:
    """Ne possède ni le canon, ni SCC-1B; il ne fait que chaîner les owners."""

    def __init__(self, conn: sqlite3.Connection, provider: Any, clock: Clock | None = None, admission_policy: Any = None, appraisal_provider: Any = None, affect_provider: Any = None) -> None:
        self._conn = conn
        self._provider = provider
        self._clock = clock or Clock()
        self._memory = SubjectiveMemoryService(conn, clock=self._clock)
        self._admissions = SCC1CAdmissionService(conn, clock=self._clock, policy=admission_policy)
        self._ledger = CognitionCallLedgerService(conn, clock=self._clock)
        self._interpretations = SocialInterpretationLLMService(conn, provider, clock=self._clock)
        self._appraisal_provider = appraisal_provider
        self._appraisals = None if appraisal_provider is None else LiveSocialAppraisalService(conn, appraisal_provider, clock=self._clock)
        self._affect = None if affect_provider is None else LiveSCC3AAffectService(conn, affect_provider, clock=self._clock)

    def _scene_participants(self, world_id: int, scene_key: str, act_key: str) -> tuple[str, ...]:
        try:
            scene = SocialSceneService(self._conn, clock=self._clock).sheet(world_id, scene_key)
        except SceneError as exc:
            raise LiveSocialCognitionError(str(exc), code=exc.code) from exc
        if not any(act["act_key"] == act_key for act in scene["acts"]):
            raise LiveSocialCognitionError("acte social introuvable", code="speech_not_found")
        return tuple(scene["participants"])

    def _existing_attempt(self, admission: SCC1CAdmission):
        return self._conn.execute(
            "SELECT outcome, detail_code FROM scc1c_attempt WHERE admission_id = ? ORDER BY id DESC LIMIT 1",
            (self._conn.execute("SELECT id FROM scc1c_admission WHERE public_id = ?", (admission.public_id,)).fetchone()["id"],),
        ).fetchone()

    def _attempt_number(self, admission: SCC1CAdmission) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM scc1c_attempt WHERE admission_id = (SELECT id FROM scc1c_admission WHERE public_id = ?)",
            (admission.public_id,),
        ).fetchone()
        return int(row[0]) + 1

    def _interpret(self, world_id: int, character_key: str, trace_request_key: str,
                   admission: SCC1CAdmission, limits: CognitionCallLimits,
                   *, retry: bool = False) -> LiveSocialCognitionOutcome:
        existing = self._existing_attempt(admission)
        if existing is not None and not retry:
            return LiveSocialCognitionOutcome(
                character_key, trace_request_key, admission.decision,
                existing["outcome"], existing["detail_code"],
                f"live_scc1b_{admission.trace_id}",
            )
        attempt_number = self._attempt_number(admission)
        attempt_key = f"live_scc1c_attempt_{admission.trace_id}_{attempt_number}"
        source_key = f"social_trace_{admission.trace_id}_attempt_{attempt_number}"
        try:
            technical = self._ledger.admit(
                world_id, character_key, CALL_TRIGGER_SOCIAL_INTERPRETATION,
                source_key, limits,
            )
        except ValueError as exc:
            raise LiveSocialCognitionError(str(exc), code=getattr(exc, "code", "technical_admission_failed")) from exc
        if not technical.verdict.eligible:
            attempt = self._admissions.record_attempt(
                admission, attempt_key, "deferred", technical.verdict.reason_code,
            )
            return LiveSocialCognitionOutcome(
                character_key, trace_request_key, admission.decision,
                attempt.outcome, attempt.detail_code, None,
            )
        interpretation_key = f"live_scc1b_{admission.trace_id}"
        try:
            self._interpretations.run(
                world_id, character_key, interpretation_key, trace_request_key,
                provider_turn_id=f"scc1c_{admission.trace_id}_{attempt_number}",
            )
        except (CognitionError, SocialInterpretationProviderError, SocialInterpretationError) as exc:
            attempt = self._admissions.record_attempt(
                admission, attempt_key, "provider_unavailable", getattr(exc, "code", "provider_failed"),
            )
            return LiveSocialCognitionOutcome(
                character_key, trace_request_key, admission.decision,
                attempt.outcome, attempt.detail_code, None,
            )
        attempt = self._admissions.record_attempt(admission, attempt_key, "interpreted")
        appraisal = None
        if self._appraisals is not None:
            appraisal = self._appraisals.process(world_id, character_key, interpretation_key, limits)
        affect = ()
        if self._affect is not None and appraisal is not None and appraisal.technical_status == "appraised":
            affect = self._affect.process_interpretation(world_id, character_key, interpretation_key, limits)
        return LiveSocialCognitionOutcome(
            character_key, trace_request_key, admission.decision,
            attempt.outcome, attempt.detail_code, interpretation_key,
            None if appraisal is None else appraisal.appraisal_status,
            0 if appraisal is None else appraisal.candidate_count,
            None if appraisal is None else appraisal.technical_status,
            tuple(item.technical_status for item in affect),
        )

    def process_speech(self, world_id: int, scene_key: str, act_key: str,
                       limits: CognitionCallLimits) -> tuple[LiveSocialCognitionOutcome, ...]:
        """Traite exactement l'acte nouvellement accepté, jamais l'historique."""
        outcomes: list[LiveSocialCognitionOutcome] = []
        for character_key in self._scene_participants(world_id, scene_key, act_key):
            trace_request_key = f"live_trace_{act_key}_{character_key}"
            try:
                self._memory.encode_social_speech(
                    world_id, character_key, trace_request_key, scene_key, act_key,
                )
                admission = self._admissions.admit(world_id, character_key, trace_request_key)
            except (SubjectiveMemoryError, SCC1CError) as exc:
                if getattr(exc, "code", None) == "source_not_accessible":
                    continue
                raise LiveSocialCognitionError(str(exc), code=getattr(exc, "code", "social_cognition_failed")) from exc
            if admission.decision == "not_selected":
                outcomes.append(LiveSocialCognitionOutcome(character_key, trace_request_key, admission.decision, None, None, None))
            else:
                outcomes.append(self._interpret(world_id, character_key, trace_request_key, admission, limits))
        return tuple(outcomes)

    def retry(self, world_id: int, character_key: str, trace_request_key: str,
              limits: CognitionCallLimits) -> LiveSocialCognitionOutcome:
        """Retry explicite d'une seule occasion technique déjà sélectionnée."""
        admission_row = self._conn.execute(
            "SELECT admission.public_id FROM scc1c_admission admission JOIN character ch ON ch.id = admission.character_id "
            "JOIN subjective_trace trace ON trace.id = admission.trace_id "
            "WHERE admission.world_id = ? AND ch.key = ? AND trace.request_key = ?",
            (world_id, character_key, trace_request_key),
        ).fetchone()
        if admission_row is None:
            raise LiveSocialCognitionError("admission introuvable", code="admission_not_found")
        admission_row = self._conn.execute(
            "SELECT admission.*, ch.key AS character_key, trace.request_key FROM scc1c_admission admission "
            "JOIN character ch ON ch.id = admission.character_id JOIN subjective_trace trace ON trace.id = admission.trace_id "
            "WHERE admission.public_id = ?", (admission_row["public_id"],)
        ).fetchone()
        admission = SCC1CAdmission(
            admission_row["public_id"], admission_row["world_id"], admission_row["character_key"],
            admission_row["request_key"], admission_row["trace_id"], admission_row["interaction_role"],
            admission_row["decision"], admission_row["policy_version"], admission_row["decided_at"],
        )
        if admission.decision != "selected":
            return LiveSocialCognitionOutcome(character_key, trace_request_key, admission.decision, None, None, None)
        latest = self._existing_attempt(admission)
        if latest is None or latest["outcome"] == "interpreted":
            return self._interpret(world_id, character_key, trace_request_key, admission, limits)
        now = parse_iso(WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id))
        last_time = self._conn.execute(
            "SELECT recorded_at FROM scc1c_attempt WHERE admission_id = (SELECT id FROM scc1c_admission WHERE public_id = ?) ORDER BY id DESC LIMIT 1",
            (admission.public_id,),
        ).fetchone()["recorded_at"]
        if (now - parse_iso(last_time)).total_seconds() < RETRY_DELAY_SECONDS:
            return LiveSocialCognitionOutcome(character_key, trace_request_key, admission.decision, latest["outcome"], "retry_backoff", None)
        return self._interpret(world_id, character_key, trace_request_key, admission, limits, retry=True)

    def retry_one_pending(self, world_id: int, limits: CognitionCallLimits) -> LiveSocialCognitionOutcome | None:
        """Reprend au plus une tentative explicitement persistée et échouée."""
        if self._appraisals is not None:
            pending_appraisal = self._appraisals.retry_one_pending(world_id, limits)
            if pending_appraisal is not None:
                return LiveSocialCognitionOutcome(
                    pending_appraisal.character_key, None, "already_interpreted",
                    pending_appraisal.technical_status, pending_appraisal.detail_code,
                    pending_appraisal.interpretation_key, pending_appraisal.appraisal_status,
                    pending_appraisal.candidate_count, pending_appraisal.technical_status,
                )
        if self._affect is not None:
            pending_affect = self._affect.retry_one_pending(world_id, limits)
            if pending_affect is not None:
                return LiveSocialCognitionOutcome(pending_affect.character_key, None, "already_appraised", pending_affect.technical_status, pending_affect.detail_code, None, None, 0, None, (pending_affect.technical_status,))
        row = self._conn.execute(
            "SELECT ch.key AS character_key, trace.request_key "
            "FROM scc1c_attempt attempt JOIN scc1c_admission admission ON admission.id = attempt.admission_id "
            "JOIN character ch ON ch.id = admission.character_id JOIN subjective_trace trace ON trace.id = admission.trace_id "
            "WHERE attempt.outcome IN ('deferred','provider_unavailable') "
            "AND NOT EXISTS (SELECT 1 FROM scc1c_attempt newer WHERE newer.admission_id = attempt.admission_id AND newer.id > attempt.id) "
            "ORDER BY attempt.recorded_at, attempt.id LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return self.retry(world_id, row["character_key"], row["request_key"], limits)
