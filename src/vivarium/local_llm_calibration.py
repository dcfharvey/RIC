"""Mesure locale, jetable et comparable d'un tour cognitif réel.

Le banc ne cherche pas à déclarer un modèle "bon" ou "humain". Il répète
le même contexte concret dans des bases SQLite indépendantes et rapporte ce
que la frontière sait vérifier : disponibilité, respect du contrat, décision,
validation moteur et durée du tour complet. Les poids et le monde persistant
restent hors du banc.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Callable

from .cognition import CognitionError, CognitionProvider
from .cognition_policy import CognitionCallLimits
from .cognition_router import CognitionCallRouter
from .db import connect_database
from .integration_world import IntegrationWorldService
from .migrations import ensure_schema
from .repro import max_seq
from .registry import _KEY_RE
from .traversal import TraversalEngine
from .util import Clock, to_iso


_CALIBRATION_TIME = datetime(2026, 8, 6, 21, tzinfo=timezone.utc)


class _CalibrationClock(Clock):
    """Horloge fixe : chaque entrée LLM est identique avant variation du modèle."""

    def now(self) -> datetime:
        return _CALIBRATION_TIME

    def now_iso(self) -> str:
        return to_iso(self.now())


class LocalCalibrationError(ValueError):
    """Paramètre invalide avant tout appel au fournisseur local."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _character_key(value: Any) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise LocalCalibrationError("personnage de calibration invalide", code="invalid_local_calibration")
    return value


def _model_id(value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > 200:
        raise LocalCalibrationError("identifiant de modèle invalide", code="invalid_local_calibration")
    return value.strip()


def _trial_count(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 20:
        raise LocalCalibrationError("nombre d'essais hors limites (1 à 20)", code="invalid_local_calibration")
    return value


@dataclass(frozen=True)
class LocalCalibrationTrial:
    """Une exécution indépendante du même tour perceptible."""

    number: int
    elapsed_ms: int
    outcome: str  # routed | provider_error | not_admitted
    decision: str | None
    validation_status: str | None
    validation_reason: str | None
    provider_error_code: str | None

    @property
    def healthy(self) -> bool:
        """Un refus moteur est sain; une panne ou une non-admission ne l'est pas."""
        return self.outcome == "routed" and self.decision is not None

    def as_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "elapsed_ms": self.elapsed_ms,
            "outcome": self.outcome,
            "decision": self.decision,
            "validation_status": self.validation_status,
            "validation_reason": self.validation_reason,
            "provider_error_code": self.provider_error_code,
            "healthy": self.healthy,
        }


@dataclass(frozen=True)
class LocalCalibrationReport:
    """Rapport de calibration sans comparaison abusive entre sorties libres."""

    model_id: str
    character_key: str
    trials: tuple[LocalCalibrationTrial, ...]
    schema_version: int = 1

    @property
    def healthy(self) -> bool:
        return bool(self.trials) and all(trial.healthy for trial in self.trials)

    @property
    def median_elapsed_ms(self) -> int:
        values = sorted(trial.elapsed_ms for trial in self.trials)
        if not values:
            return 0
        middle = len(values) // 2
        return values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) // 2

    @property
    def outcome_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for trial in self.trials:
            counts[trial.outcome] = counts.get(trial.outcome, 0) + 1
        return dict(sorted(counts.items()))

    @property
    def decision_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for trial in self.trials:
            if trial.decision is not None:
                counts[trial.decision] = counts.get(trial.decision, 0) + 1
        return dict(sorted(counts.items()))

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "model_id": self.model_id,
            "character_key": self.character_key,
            "healthy": self.healthy,
            "median_elapsed_ms": self.median_elapsed_ms,
            "outcome_counts": self.outcome_counts,
            "decision_counts": self.decision_counts,
            "trials": [trial.as_dict() for trial in self.trials],
        }


def run_local_cognition_calibration(
    provider: CognitionProvider,
    model_id: Any,
    *,
    trials: Any = 3,
    character_key: Any = "sophie",
    timer: Callable[[], float] = perf_counter,
) -> LocalCalibrationReport:
    """Répète un événement direct dans un monde en mémoire par essai.

    Le contexte injecté est identique à chaque passage. Les sorties d'un LLM
    peuvent varier; le rapport conserve justement cette distribution, mais ne
    confond jamais cette variabilité avec un changement de l'état du monde.
    """

    if not callable(getattr(provider, "decide", None)):
        raise LocalCalibrationError("fournisseur de calibration invalide", code="invalid_local_calibration")
    model_id, character_key, trials = _model_id(model_id), _character_key(character_key), _trial_count(trials)
    if not callable(timer):
        raise LocalCalibrationError("horloge de calibration invalide", code="invalid_local_calibration")

    results: list[LocalCalibrationTrial] = []
    for number in range(1, trials + 1):
        conn = connect_database(":memory:")
        try:
            ensure_schema(conn)
            clock = _CalibrationClock()
            world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
            TraversalEngine(conn, clock=clock).traverse_character(
                world_id, character_key, "porte_entree", "salon"
            )
            source_key = f"event_{max_seq(conn, world_id)}"
            started = timer()
            routed = CognitionCallRouter(conn, provider, clock=clock).run(
                world_id,
                character_key,
                "direct_event",
                source_key,
                f"calibration_{character_key}_{number}",
                CognitionCallLimits(0, 3_600, 1),
            )
            elapsed_ms = max(0, round((timer() - started) * 1_000))
            if routed.provider_error_code is not None:
                results.append(LocalCalibrationTrial(
                    number, elapsed_ms, "provider_error", None, None, None, routed.provider_error_code
                ))
            elif routed.turn is None:
                results.append(LocalCalibrationTrial(
                    number, elapsed_ms, "not_admitted", None, None, None,
                    routed.admission.verdict.reason_code,
                ))
            else:
                validation = routed.turn.validation
                results.append(LocalCalibrationTrial(
                    number,
                    elapsed_ms,
                    "routed",
                    routed.turn.decision.action,
                    None if validation is None else validation.status,
                    None if validation is None else validation.reason_code,
                    None,
                ))
        finally:
            conn.close()
    return LocalCalibrationReport(model_id, character_key, tuple(results))
