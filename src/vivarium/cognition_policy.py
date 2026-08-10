"""Politique pure qui décide si un appel cognitif est admissible.

Cette couche ne connaît ni SQLite, ni le fournisseur LLM, ni la décision du
personnage. Elle rend seulement un verdict stable à partir d'un motif fermé et
d'un historique explicitement fourni. Sa persistance append-only viendra dans
un lot séparé.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

from .registry import _KEY_RE
from .util import parse_iso


CALL_TRIGGER_INITIAL_ARRIVAL = "initial_arrival"
CALL_TRIGGER_DIRECT_EVENT = "direct_event"
CALL_TRIGGER_ACTION_REFUSED = "action_refused"
CALL_TRIGGER_INTENTION_BLOCKED = "intention_blocked"
CALL_TRIGGER_INTENTION_COMPLETED = "intention_completed"
CALL_TRIGGER_SCENE_TURN = "scene_turn"
CALL_TRIGGER_PLANNED_REFLECTION = "planned_reflection"
CALL_TRIGGER_OWNER_INTERVENTION = "owner_intervention"
CALL_TRIGGER_SOCIAL_INTERPRETATION = "social_interpretation"
CALL_TRIGGER_SOCIAL_APPRAISAL = "social_appraisal"

CALL_TRIGGERS = frozenset({
    CALL_TRIGGER_INITIAL_ARRIVAL,
    CALL_TRIGGER_DIRECT_EVENT,
    CALL_TRIGGER_ACTION_REFUSED,
    CALL_TRIGGER_INTENTION_BLOCKED,
    CALL_TRIGGER_INTENTION_COMPLETED,
    CALL_TRIGGER_SCENE_TURN,
    CALL_TRIGGER_PLANNED_REFLECTION,
    CALL_TRIGGER_OWNER_INTERVENTION,
    CALL_TRIGGER_SOCIAL_INTERPRETATION,
    CALL_TRIGGER_SOCIAL_APPRAISAL,
})


class CognitionCallPolicyError(ValueError):
    """Entrée invalide de la politique, avant tout appel local."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _key(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise CognitionCallPolicyError(f"{label} invalide", code="invalid_cognition_call_request")
    return value


def _instant(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise CognitionCallPolicyError(f"{label} invalide", code="invalid_cognition_call_request")
    try:
        return parse_iso(value)
    except (TypeError, ValueError) as exc:
        raise CognitionCallPolicyError(f"{label} invalide", code="invalid_cognition_call_request") from exc


@dataclass(frozen=True)
class CognitionCallRequest:
    """Un signal canonique à l'origine connue, jamais du texte fourni par le LLM."""

    character_key: str
    trigger: str
    source_key: str
    requested_at: str

    def validated(self) -> "CognitionCallRequest":
        _key(self.character_key, "personnage")
        if self.trigger not in CALL_TRIGGERS:
            raise CognitionCallPolicyError("motif d'appel inconnu", code="unknown_cognition_call_trigger")
        _key(self.source_key, "source")
        _instant(self.requested_at, "instant")
        return self

    @property
    def idempotency_key(self) -> str:
        self.validated()
        return f"{self.character_key}:{self.trigger}:{self.source_key}"


@dataclass(frozen=True)
class CognitionCallRecord:
    """Admission déjà enregistrée par le futur journal technique append-only."""

    character_key: str
    trigger: str
    source_key: str
    admitted_at: str

    def validated(self) -> "CognitionCallRecord":
        CognitionCallRequest(self.character_key, self.trigger, self.source_key, self.admitted_at).validated()
        _instant(self.admitted_at, "trace d'appel")
        return self

    @property
    def idempotency_key(self) -> str:
        return CognitionCallRequest(
            self.character_key, self.trigger, self.source_key, self.admitted_at
        ).idempotency_key


@dataclass(frozen=True)
class CognitionCallLimits:
    """Limites explicites, fournies par la configuration versionnée du banc."""

    debounce_seconds: int
    budget_window_seconds: int
    max_calls_per_window: int

    def validated(self) -> "CognitionCallLimits":
        for value, label, lower, upper in (
            (self.debounce_seconds, "debounce", 0, 86_400),
            (self.budget_window_seconds, "fenêtre de budget", 1, 7 * 86_400),
            (self.max_calls_per_window, "budget d'appel", 1, 10_000),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or not lower <= value <= upper:
                raise CognitionCallPolicyError(f"{label} invalide", code="invalid_cognition_call_limits")
        return self


@dataclass(frozen=True)
class CognitionCallVerdict:
    """Résultat sérialisable : l'appelant choisit ensuite de journaliser ou non."""

    status: str  # eligible | deferred
    reason_code: str
    idempotency_key: str

    @property
    def eligible(self) -> bool:
        return self.status == "eligible"


class CognitionCallPolicy:
    """Applique dans un ordre fixe : doublon, debounce, puis budget.

    ``history`` représente les admissions de ce personnage seulement. Il est
    délibérément injecté afin que cette classe soit déterministe et sans effet
    de bord; le prochain lot lui donnera un journal SQLite append-only.
    """

    @staticmethod
    def evaluate(request: Any, history: Iterable[Any], limits: Any) -> CognitionCallVerdict:
        if not isinstance(request, CognitionCallRequest):
            raise CognitionCallPolicyError("demande d'appel invalide", code="invalid_cognition_call_request")
        if not isinstance(limits, CognitionCallLimits):
            raise CognitionCallPolicyError("limites d'appel invalides", code="invalid_cognition_call_limits")
        request, limits = request.validated(), limits.validated()
        try:
            records = tuple(history)
        except TypeError as exc:
            raise CognitionCallPolicyError("historique d'appel invalide", code="invalid_cognition_call_history") from exc
        if not all(isinstance(record, CognitionCallRecord) for record in records):
            raise CognitionCallPolicyError("historique d'appel invalide", code="invalid_cognition_call_history")
        records = tuple(record.validated() for record in records)
        if any(record.character_key != request.character_key for record in records):
            raise CognitionCallPolicyError("historique d'appel hors personnage", code="invalid_cognition_call_history")
        now = _instant(request.requested_at, "instant")
        dated_records = tuple((record, _instant(record.admitted_at, "trace d'appel")) for record in records)
        if any(admitted_at > now for _, admitted_at in dated_records):
            raise CognitionCallPolicyError("historique d'appel dans le futur", code="invalid_cognition_call_history")

        key = request.idempotency_key
        if any(record.idempotency_key == key for record, _ in dated_records):
            return CognitionCallVerdict("deferred", "duplicate_call", key)

        if limits.debounce_seconds:
            latest = max((admitted_at for _, admitted_at in dated_records), default=None)
            if latest is not None and (now - latest).total_seconds() < limits.debounce_seconds:
                return CognitionCallVerdict("deferred", "debounced", key)

        calls_in_window = sum(
            1 for _, admitted_at in dated_records
            if (now - admitted_at).total_seconds() < limits.budget_window_seconds
        )
        if calls_in_window >= limits.max_calls_per_window:
            return CognitionCallVerdict("deferred", "budget_exhausted", key)
        return CognitionCallVerdict("eligible", "eligible", key)
