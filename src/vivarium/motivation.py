"""Candidats de motifs dérivés d'états déjà mesurés.

Cette première tranche ne crée ni désir conscient, ni personnalité, ni objectif.
Elle transforme seulement les déficits physiologiques connus en candidats bornés
que la future décision pourra considérer. Les valeurs absentes restent ``None``
au lieu d'être inventées.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .policy import CRIT_ENERGIE, CRIT_REPOS, PolicyContext


class MotivationError(ValueError):
    """Contexte incompatible avec la projection des motifs."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


_NEED_ORDER = ("satiete", "hygiene", "repos", "energie")
_NEED_ACTIONS = {
    "satiete": ("eat",),
    "hygiene": ("clean",),
    "repos": ("sleep", "rest"),
    "energie": ("rest",),
}
_CRITICAL = {"repos": CRIT_REPOS, "energie": CRIT_ENERGIE}


@dataclass(frozen=True)
class MotiveCandidate:
    """Candidat non conscient, explicable et borné à des actions connues."""

    character_key: str
    candidate_key: str
    source_kind: str
    target_need: str
    direction: str
    pressure_milli: int
    urgency_milli: int
    importance_milli: int
    possible_actions: tuple[str, ...]
    expected_pleasure_milli: int | None = None
    estimated_cost_milli: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "character_key": self.character_key,
            "candidate_key": self.candidate_key,
            "source_kind": self.source_kind,
            "target_need": self.target_need,
            "direction": self.direction,
            "pressure_milli": self.pressure_milli,
            "urgency_milli": self.urgency_milli,
            "importance_milli": self.importance_milli,
            "possible_actions": list(self.possible_actions),
            "expected_pleasure_milli": self.expected_pleasure_milli,
            "estimated_cost_milli": self.estimated_cost_milli,
        }


class MotivationService:
    """Projection pure des motifs physiologiques accessibles à une agente."""

    @staticmethod
    def _pressure(value: Any, threshold: Any) -> int:
        if (
            isinstance(value, bool) or not isinstance(value, int)
            or isinstance(threshold, bool) or not isinstance(threshold, int)
            or threshold <= 0
        ):
            raise MotivationError("valeur ou seuil de besoin invalide", code="invalid_motivation_context")
        if value >= threshold:
            return 0
        return min(1000, (threshold - value) * 1000 // threshold)

    @staticmethod
    def _validate_context(context: Any) -> PolicyContext:
        if not isinstance(context, PolicyContext):
            raise MotivationError("contexte de motivation invalide", code="invalid_motivation_context")
        if not isinstance(context.character_key, str) or not context.character_key:
            raise MotivationError("personnage de motivation invalide", code="invalid_motivation_context")
        for key in _NEED_ORDER:
            if key not in context.needs or key not in context.effective_thresholds:
                raise MotivationError("besoin absent du contexte", code="invalid_motivation_context")
        if not isinstance(context.accessible, dict):
            raise MotivationError("actions accessibles invalides", code="invalid_motivation_context")
        return context

    def candidates(self, context: Any) -> tuple[MotiveCandidate, ...]:
        context = self._validate_context(context)
        candidates: list[MotiveCandidate] = []
        for need_key in _NEED_ORDER:
            pressure = self._pressure(context.needs[need_key], context.effective_thresholds[need_key])
            if pressure == 0:
                continue
            critical = _CRITICAL.get(need_key)
            urgency = 1000 if critical is not None and context.needs[need_key] < critical else pressure
            actions = tuple(
                action for action in _NEED_ACTIONS[need_key]
                if context.accessible.get(action)
            )
            candidates.append(MotiveCandidate(
                character_key=context.character_key,
                candidate_key=f"motive_need_{need_key}",
                source_kind="physiological_regulation",
                target_need=need_key,
                direction="restore",
                pressure_milli=pressure,
                urgency_milli=urgency,
                importance_milli=pressure,
                possible_actions=actions,
            ))
        order = {key: index for index, key in enumerate(_NEED_ORDER)}
        candidates.sort(key=lambda item: (-item.urgency_milli, -item.pressure_milli, order[item.target_need]))
        return tuple(candidates)
