"""Raccord sommeil/activite limite aux mondes synthetiques controles.

Le coordinateur ne fait jamais partie de la boucle runtime. Il assemble des
causes de banc explicites : la physiologie materialise H/phi/P, la politique
de terminaison evalue une frontiere, puis ActivityEngine reste le seul owner
des transitions `completed` et `aborted`. Les valeurs legacy restent isolees
dans le moteur d'activite existant; elles ne sont ni lues ni converties vers
H ou P par ce module.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Literal

from .activities import ActivityEngine, ActivityError
from .circadian_model import RegulationInput
from .db import transaction
from .sleep_physiology import SleepPhysiologyService
from .sleep_termination import (
    SleepCheckpointEvaluation,
    SleepTerminationError,
    SleepTerminationFoundationService,
    evaluate_sleep_checkpoint,
)
from .util import Clock, parse_iso, to_iso


class SyntheticSleepIntegrationError(ValueError):
    """Frontiere ou cause de banc invalide avant toute mutation."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SyntheticBoundary:
    at: str
    reasons: tuple[Literal["sleep_checkpoint", "sleep_hard_cap", "wake_stability_critical"], ...]


@dataclass(frozen=True)
class SleepCheckpointResult:
    evaluation: SleepCheckpointEvaluation
    checkpoint_advanced: bool
    hard_cap_reported: bool
    activity_completed: bool
    re_arbitration_required: bool


@dataclass(frozen=True)
class StabilityInterruptionResult:
    interrupted: bool
    reason_code: str | None
    re_arbitration_required: bool
    stability_band: str


def _at(value: Any, *, field: str) -> str:
    try:
        return to_iso(parse_iso(value))
    except (TypeError, ValueError) as exc:
        raise SyntheticSleepIntegrationError(f"{field} invalide", code="invalid_synthetic_boundary") from exc


class SyntheticSleepActivityCoordinator:
    """Coordonne des frontieres, sans devenir owner de l'activite ni de H/P."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()
        self._activities = ActivityEngine(conn, clock=self._clock)
        self._physiology = SleepPhysiologyService(conn, clock=self._clock)
        self._termination = SleepTerminationFoundationService(conn, clock=self._clock)

    def _policy_id(self, world_id: int) -> int:
        row = self._conn.execute(
            "SELECT a.policy_id FROM world_sleep_termination_policy_assignment a "
            "WHERE a.world_id=?", (world_id,)
        ).fetchone()
        if row is None:
            raise SyntheticSleepIntegrationError(
                "politique de terminaison absente", code="policy_not_assigned"
            )
        return int(row["policy_id"])

    def attach_checkpoint(
        self, world_id: int, character_key: str, *, first_reassessment_at: str,
        hard_cap_at: str, previous_band: str = "continue_sleep",
    ) -> dict[str, Any]:
        """Delegue la creation du plan au proprietaire ActivityEngine."""
        return self._activities.attach_sleep_checkpoint(
            world_id, character_key, policy_id=self._policy_id(world_id),
            next_reassessment_at=_at(first_reassessment_at, field="reevaluation"),
            hard_cap_at=_at(hard_cap_at, field="hard_cap"), previous_band=previous_band,
        )

    def next_boundary(
        self, world_id: int, character_key: str, *, wake_source: RegulationInput,
        until: str,
    ) -> SyntheticBoundary | None:
        """Lit la prochaine frontiere explicite, sans materialiser quoi que ce soit."""
        if wake_source.state != "wake":
            raise SyntheticSleepIntegrationError("source de veille requise", code="invalid_synthetic_source")
        limit = _at(until, field="limite")
        candidates: list[tuple[
            str, Literal["sleep_checkpoint", "sleep_hard_cap", "wake_stability_critical"]
        ]] = []
        checkpoint = self._activities.sleep_checkpoint(world_id, character_key)
        if checkpoint is not None and checkpoint["status"] == "active":
            for value, reason in (
                (checkpoint["next_reassessment_at"], "sleep_checkpoint"),
                (checkpoint["hard_cap_at"], "sleep_hard_cap"),
            ):
                if parse_iso(value) <= parse_iso(limit):
                    candidates.append((value, reason))

        active = self._activities.activity_sheet(world_id, character_key)
        if active is not None:
            row = self._conn.execute(
                "SELECT requires_sustained_wakefulness FROM activity_definition "
                "WHERE world_id=? AND activity_type=?", (world_id, active["type"]),
            ).fetchone()
            if row is not None and bool(row["requires_sustained_wakefulness"]):
                critical = self._physiology.next_critical_boundary_synthetic(
                    world_id, character_key, wake_source, limit
                )
                if critical is not None:
                    candidates.append((critical, "wake_stability_critical"))
        if not candidates:
            return None
        first = min(parse_iso(value) for value, _reason in candidates)
        at = to_iso(first)
        return SyntheticBoundary(at, tuple(sorted(reason for value, reason in candidates if parse_iso(value) == first)))

    def process_sleep_checkpoint(
        self, world_id: int, character_key: str, *, at_time: str,
        sleep_source: RegulationInput, wake_source: RegulationInput,
    ) -> SleepCheckpointResult:
        """Materialise puis applique une seule decision de checkpoint atomiquement."""
        if sleep_source.state != "sleep" or wake_source.state != "wake":
            raise SyntheticSleepIntegrationError("sources sommeil/veille requises", code="invalid_synthetic_source")
        at = _at(at_time, field="checkpoint")
        with transaction(self._conn):
            checkpoint = self._activities.sleep_checkpoint(world_id, character_key)
            if checkpoint is None or checkpoint["status"] != "active":
                raise SyntheticSleepIntegrationError("checkpoint actif absent", code="checkpoint_missing")
            if parse_iso(at) < parse_iso(checkpoint["next_reassessment_at"]):
                raise SyntheticSleepIntegrationError("checkpoint pas encore du", code="checkpoint_not_due")
            if parse_iso(at) > parse_iso(checkpoint["hard_cap_at"]):
                raise SyntheticSleepIntegrationError("checkpoint apres hard cap", code="checkpoint_after_hard_cap")

            # Cette ecriture est celle du proprietaire physiologique. Le
            # coordinateur ne calcule aucune valeur H/phi/P lui-meme.
            self._physiology.materialize_synthetic(world_id, character_key, at, sleep_source)
            projection = self._physiology.project_synthetic(world_id, character_key, wake_source)
            viability = round((1.0 - projection.stability.instability) * 100_000)
            elapsed = int((parse_iso(at) - parse_iso(checkpoint["started_at"])).total_seconds())
            policy = self._termination.world_policy(world_id)
            evaluation = evaluate_sleep_checkpoint(
                policy, elapsed_seconds=elapsed, wake_viability_milli=viability,
                previous_band=checkpoint["previous_band"], external_wake_accessible=False,
            )
            if evaluation.completion_eligible:
                # Re-evaluation volontaire par l'owner de la politique : le
                # bool de l'evaluateur local n'est pas un jeton forgeable. La
                # preuve persiste le checkpoint/episode/frontiere exacts et le
                # trigger 0055 la consomme avec l'evenement canonique.
                self._termination.authorize_completion(
                    world_id, character_key, at_time=at,
                    wake_viability_milli=viability, external_wake_accessible=False,
                )
                self._activities.complete_sleep_from_checkpoint(world_id, character_key, at_time=at)
                return SleepCheckpointResult(evaluation, False, False, True, True)
            if evaluation.hard_cap_reached:
                reported = self._activities.report_sleep_hard_cap(world_id, character_key, at_time=at)
                return SleepCheckpointResult(evaluation, False, reported, False, False)
            assert evaluation.next_reassessment_after_seconds is not None
            next_at = to_iso(parse_iso(at) + timedelta(seconds=evaluation.next_reassessment_after_seconds))
            self._activities.advance_sleep_checkpoint(
                world_id, character_key, at_time=at, next_reassessment_at=next_at,
                previous_band=evaluation.band,
            )
            return SleepCheckpointResult(evaluation, True, False, False, False)

    def interrupt_critical_wake_stability(
        self, world_id: int, character_key: str, *, at_time: str,
        wake_source: RegulationInput,
    ) -> StabilityInterruptionResult:
        """Applique au plus une interruption moteur apres une projection critique."""
        if wake_source.state != "wake":
            raise SyntheticSleepIntegrationError("source de veille requise", code="invalid_synthetic_source")
        at = _at(at_time, field="interruption")
        with transaction(self._conn):
            materialized = self._physiology.materialize_synthetic(world_id, character_key, at, wake_source)
            active = self._activities.activity_sheet(world_id, character_key)
            if active is None:
                return StabilityInterruptionResult(False, None, False, materialized.projection.stability.band)
            definition = self._conn.execute(
                "SELECT requires_sustained_wakefulness FROM activity_definition "
                "WHERE world_id=? AND activity_type=?", (world_id, active["type"]),
            ).fetchone()
            eligible = definition is not None and bool(definition["requires_sustained_wakefulness"])
            if materialized.projection.stability.band != "critical" or not eligible:
                return StabilityInterruptionResult(False, None, False, materialized.projection.stability.band)
            self._activities.abort_activity(
                world_id, character_key, sim_now=at, reason_code="wake_stability_critical"
            )
            return StabilityInterruptionResult(True, "wake_stability_critical", True, "critical")
