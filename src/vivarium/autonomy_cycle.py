"""Occasion de choisir une activité quand une résidente entre en idle.

Le cycle est événementiel : chaque ``activity_started: idle`` ouvre au plus
une décision. Il ne sonde pas continuellement le modèle et ne choisit jamais
à sa place. Les options proviennent du moteur et l'action retenue repasse par
le contrat canonique.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from .activities import ActivityEngine
from .character_capabilities import sapient_character_keys
from .cognition import CognitionProvider
from .cognition_call_ledger import CognitionCallLedgerService
from .cognitive_flow import CognitiveFlowScheduler
from .cognition_policy import CALL_TRIGGER_PLANNED_REFLECTION, CognitionCallLimits
from .cognition_router import CognitionCallRouter, CognitionCallRouterError, RoutedCognitionCall
from .util import Clock, parse_iso, to_iso
from .world import WorldEngine


RETRY_DELAY_SECONDS = 300
RETRY_IDLE_SECONDS = 600
RETRY_ORIGIN = "cognition_retry"


@dataclass(frozen=True)
class AutonomyOutcome:
    character_key: str | None
    source_event_seq: int | None
    routed: RoutedCognitionCall | None
    detail_code: str | None = None


class AutonomyCycle:
    """Route au plus un véritable appel de réflexion par tick de runtime."""

    def __init__(
        self, conn: sqlite3.Connection, provider: CognitionProvider,
        clock: Clock | None = None,
        flow_scheduler: CognitiveFlowScheduler | None = None,
    ) -> None:
        self._conn, self._provider, self._clock = conn, provider, clock or Clock()
        self._flow_scheduler = flow_scheduler

    def _active_idle_sources(self, world_id: int) -> tuple[tuple[str, int], ...]:
        candidates: list[tuple[str, int]] = []
        canonical_now = parse_iso(WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id))
        for character_key in sapient_character_keys(self._conn, world_id):
            active = self._conn.execute(
                "SELECT a.started_at, a.planned_end_at, l.key AS location FROM activity a "
                "JOIN character c ON c.id = a.character_id JOIN location l ON l.id = a.location_id "
                "WHERE a.world_id = ? AND c.key = ? AND a.status = 'active' AND a.type = 'idle' "
                "ORDER BY a.id DESC LIMIT 1",
                (world_id, character_key),
            ).fetchone()
            if active is None:
                continue
            events = self._conn.execute(
                "SELECT seq, occurred_at, payload FROM canonical_event WHERE world_id = ? "
                "AND event_type = 'activity_started' AND json_extract(payload, '$.character') = ? "
                "AND json_extract(payload, '$.activity') = 'idle' ORDER BY seq DESC LIMIT 8",
                (world_id, character_key),
            ).fetchall()
            for event in events:
                try:
                    payload = json.loads(event["payload"])
                except (TypeError, ValueError):
                    continue
                if event["occurred_at"] == active["started_at"] \
                        and payload.get("planned_end_at") == active["planned_end_at"] \
                        and payload.get("location") == active["location"]:
                    provenance = payload.get("action_provenance")
                    if isinstance(provenance, dict) and provenance.get("origin") == RETRY_ORIGIN:
                        retry_at = parse_iso(event["occurred_at"]) + timedelta(
                            seconds=RETRY_DELAY_SECONDS
                        )
                        if canonical_now < retry_at:
                            break
                    candidates.append((character_key, int(event["seq"])))
                    break
        return tuple(candidates)

    def _schedule_retry(
        self,
        world_id: int,
        character_key: str,
        event_seq: int,
        *,
        effective_at: str,
    ) -> None:
        """Remplace l'idle courant par une fenêtre de retry bornée et traçable."""
        activities = ActivityEngine(self._conn, clock=self._clock)
        active = activities.activity_sheet(world_id, character_key)
        if active is None or active["type"] != "idle":
            return
        activities.abort_activity(world_id, character_key, sim_now=effective_at)
        activities.start_activity(
            world_id,
            character_key,
            "idle",
            active["location_key"],
            sim_now=effective_at,
            duration_seconds=RETRY_IDLE_SECONDS,
            action_provenance={
                "proposal_id": f"retry_{character_key}_{event_seq}",
                "origin": RETRY_ORIGIN,
            },
        )

    def tick(self, world_id: Any, limits: Any) -> AutonomyOutcome:
        if not isinstance(world_id, int) or isinstance(world_id, bool) or world_id < 1:
            return AutonomyOutcome(None, None, None, "invalid_world")
        if not isinstance(limits, CognitionCallLimits):
            return AutonomyOutcome(None, None, None, "invalid_limits")
        limits.validated()
        ledger = CognitionCallLedgerService(
            self._conn, clock=self._clock, flow_scheduler=self._flow_scheduler,
        )
        router = CognitionCallRouter(
            self._conn, self._provider, clock=self._clock,
            flow_scheduler=self._flow_scheduler,
        )
        deferred: AutonomyOutcome | None = None
        for character_key, event_seq in self._active_idle_sources(world_id):
            source_key = f"idle_{event_seq}"
            if any(
                record.trigger == CALL_TRIGGER_PLANNED_REFLECTION and record.source_key == source_key
                for record in ledger.history(world_id, character_key)
            ):
                continue
            try:
                routed = router.run(
                    world_id, character_key, CALL_TRIGGER_PLANNED_REFLECTION,
                    source_key, f"autonomy_{character_key}_{event_seq}", limits,
                )
            except CognitionCallRouterError as exc:
                return AutonomyOutcome(character_key, event_seq, None, exc.code)
            outcome = AutonomyOutcome(character_key, event_seq, routed, routed.provider_error_code)
            if routed.provider_error_code is not None:
                assert routed.admission.admitted_at is not None
                self._schedule_retry(
                    world_id,
                    character_key,
                    event_seq,
                    effective_at=routed.admission.admitted_at,
                )
            if routed.attempted:
                return outcome
            # Un budget ou debounce individuel ne doit pas affamer les autres
            # résidentes. On garde le premier diagnostic, puis on continue.
            deferred = deferred or outcome
        return deferred or AutonomyOutcome(None, None, None, None)
