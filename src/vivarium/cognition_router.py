"""Route un appel LLM explicitement admissible, sans boucle autonome.

Le routeur raccorde seulement les déclencheurs dont la source peut être
prouvée aujourd'hui. Il journalise d'abord l'admission technique, puis délègue
un unique tour à la frontière LLM existante.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import Any

from .cognition import CognitionError, CognitionProvider, CognitionTurnResult, CognitionTurnService
from .cognition_call_ledger import CognitionCallAdmission, CognitionCallLedgerService
from .cognition_policy import CALL_TRIGGER_DIRECT_EVENT, CognitionCallLimits
from .perception import PerceptionError, PerceptionService
from .registry import _KEY_RE
from .util import Clock


_DIRECT_EVENT_SOURCE_RE = re.compile(r"^event_([1-9][0-9]*)$")


class CognitionCallRouterError(ValueError):
    """Déclencheur non raccordé ou source non perceptible, sans appel LLM."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _key(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise CognitionCallRouterError(f"{label} invalide", code="invalid_cognition_call_request")
    return value


@dataclass(frozen=True)
class RoutedCognitionCall:
    """Résultat du routeur, y compris le mode dégradé sans mutation canonique."""

    admission: CognitionCallAdmission
    turn: CognitionTurnResult | None
    provider_error_code: str | None

    @property
    def attempted(self) -> bool:
        return self.admission.verdict.eligible


class CognitionCallRouter:
    """Point d'entrée contrôlé pour un unique appel cognitif explicite."""

    def __init__(self, conn: sqlite3.Connection, provider: CognitionProvider, clock: Clock | None = None) -> None:
        self._conn = conn
        self._provider = provider
        self._clock = clock or Clock()
        self._ledger = CognitionCallLedgerService(conn, clock=self._clock)

    def _validate_direct_event_source(self, world_id: int, character_key: str, source_key: str) -> int:
        match = _DIRECT_EVENT_SOURCE_RE.fullmatch(source_key)
        if match is None:
            raise CognitionCallRouterError("source d'événement direct invalide", code="invalid_cognition_call_source")
        event_seq = int(match.group(1))
        try:
            feed = PerceptionService(self._conn, clock=self._clock).events_since(world_id, character_key, event_seq - 1)
        except PerceptionError as exc:
            raise CognitionCallRouterError(str(exc), code="invalid_cognition_call_source") from exc
        if not any(candidate.fact.event_seq == event_seq for candidate in feed.candidates):
            raise CognitionCallRouterError("événement non perceptible", code="cognition_call_source_not_perceived")
        return event_seq

    def run(
        self,
        world_id: Any,
        character_key: Any,
        trigger: Any,
        source_key: Any,
        proposal_id: Any,
        limits: Any,
    ) -> RoutedCognitionCall:
        if not isinstance(world_id, int) or isinstance(world_id, bool) or world_id < 1:
            raise CognitionCallRouterError("monde invalide", code="invalid_cognition_call_request")
        character_key, trigger = _key(character_key, "personnage"), _key(trigger, "motif")
        source_key, proposal_id = _key(source_key, "source"), _key(proposal_id, "proposition")
        if trigger != CALL_TRIGGER_DIRECT_EVENT:
            raise CognitionCallRouterError("motif d'appel non raccordé", code="unroutable_cognition_call_trigger")
        after_event_seq = self._validate_direct_event_source(world_id, character_key, source_key) - 1
        admission = self._ledger.admit(world_id, character_key, trigger, source_key, limits)
        if not admission.verdict.eligible:
            return RoutedCognitionCall(admission, None, None)
        try:
            turn = CognitionTurnService(self._conn, self._provider, clock=self._clock).run(
                world_id, character_key, proposal_id, after_event_seq=after_event_seq
            )
        except CognitionError as exc:
            return RoutedCognitionCall(admission, None, exc.code)
        return RoutedCognitionCall(admission, turn, None)
