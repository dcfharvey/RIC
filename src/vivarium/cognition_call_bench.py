"""Banc reproductible de la politique d'admission LLM.

Le banc rejoue uniquement des signaux déjà décrits. Il ne contacte pas un
modèle et ne crée pas de monde : son rôle est de comparer une cadence et un
budget candidats avant de les rendre opérationnels.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

from .cognition_policy import (
    CognitionCallLimits,
    CognitionCallPolicy,
    CognitionCallPolicyError,
    CognitionCallRecord,
    CognitionCallRequest,
    CognitionCallVerdict,
)
from .registry import _KEY_RE


class CognitionCallBenchError(ValueError):
    """Chronologie ou configuration de banc invalide."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class CognitionCallSignal:
    """Signal externe fermé, placé à une heure canonique donnée."""

    character_key: str
    trigger: str
    source_key: str
    requested_at: str

    def request(self) -> CognitionCallRequest:
        request = CognitionCallRequest(
            self.character_key, self.trigger, self.source_key, self.requested_at
        )
        try:
            return request.validated()
        except CognitionCallPolicyError as exc:
            raise CognitionCallBenchError(str(exc), code=exc.code) from exc


@dataclass(frozen=True)
class CognitionCallBenchReport:
    """Résultat stable d'une expérience de cadence, sans effet de bord."""

    limits: CognitionCallLimits
    verdicts: tuple[CognitionCallVerdict, ...]

    @property
    def admitted_count(self) -> int:
        return sum(verdict.eligible for verdict in self.verdicts)

    @property
    def deferred_count(self) -> int:
        return len(self.verdicts) - self.admitted_count

    @property
    def reason_counts(self) -> dict[str, int]:
        return dict(sorted(Counter(verdict.reason_code for verdict in self.verdicts).items()))

    def as_dict(self) -> dict[str, Any]:
        return {
            "limits": {
                "debounce_seconds": self.limits.debounce_seconds,
                "budget_window_seconds": self.limits.budget_window_seconds,
                "max_calls_per_window": self.limits.max_calls_per_window,
            },
            "admitted_count": self.admitted_count,
            "deferred_count": self.deferred_count,
            "reason_counts": self.reason_counts,
            "verdicts": [
                {
                    "status": verdict.status,
                    "reason_code": verdict.reason_code,
                    "idempotency_key": verdict.idempotency_key,
                }
                for verdict in self.verdicts
            ],
        }


def run_call_policy_bench(
    signals: Iterable[Any], limits: Any
) -> CognitionCallBenchReport:
    """Rejoue les signaux dans leur ordre, avec un historique par résidente."""

    if not isinstance(limits, CognitionCallLimits):
        raise CognitionCallBenchError("limites de banc invalides", code="invalid_cognition_call_limits")
    try:
        limits.validated()
        entries = tuple(signals)
    except (CognitionCallPolicyError, TypeError) as exc:
        code = getattr(exc, "code", "invalid_cognition_call_bench")
        raise CognitionCallBenchError(str(exc), code=code) from exc

    histories: defaultdict[str, list[CognitionCallRecord]] = defaultdict(list)
    latest_at: dict[str, str] = {}
    verdicts: list[CognitionCallVerdict] = []
    for signal in entries:
        if not isinstance(signal, CognitionCallSignal):
            raise CognitionCallBenchError("signal de banc invalide", code="invalid_cognition_call_bench")
        request = signal.request()
        previous_at = latest_at.get(request.character_key)
        if previous_at is not None and request.requested_at < previous_at:
            raise CognitionCallBenchError(
                "les signaux d'une résidente doivent être chronologiques",
                code="non_chronological_cognition_call_bench",
            )
        latest_at[request.character_key] = request.requested_at
        try:
            verdict = CognitionCallPolicy.evaluate(request, histories[request.character_key], limits)
        except CognitionCallPolicyError as exc:
            raise CognitionCallBenchError(str(exc), code=exc.code) from exc
        verdicts.append(verdict)
        if verdict.eligible:
            histories[request.character_key].append(
                CognitionCallRecord(
                    request.character_key, request.trigger, request.source_key, request.requested_at
                )
            )
    return CognitionCallBenchReport(limits, tuple(verdicts))
