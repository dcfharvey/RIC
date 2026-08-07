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
from typing import Any

from .character_capabilities import sapient_character_keys
from .cognition import CognitionProvider
from .cognition_call_ledger import CognitionCallLedgerService
from .cognition_policy import CALL_TRIGGER_PLANNED_REFLECTION, CognitionCallLimits
from .cognition_router import CognitionCallRouter, CognitionCallRouterError, RoutedCognitionCall
from .util import Clock


@dataclass(frozen=True)
class AutonomyOutcome:
    character_key: str | None
    source_event_seq: int | None
    routed: RoutedCognitionCall | None
    detail_code: str | None = None


class AutonomyCycle:
    """Route au plus un véritable appel de réflexion par tick de runtime."""

    def __init__(self, conn: sqlite3.Connection, provider: CognitionProvider, clock: Clock | None = None) -> None:
        self._conn, self._provider, self._clock = conn, provider, clock or Clock()

    def _active_idle_sources(self, world_id: int) -> tuple[tuple[str, int], ...]:
        candidates: list[tuple[str, int]] = []
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
                    candidates.append((character_key, int(event["seq"])))
                    break
        return tuple(candidates)

    def tick(self, world_id: Any, limits: Any) -> AutonomyOutcome:
        if not isinstance(world_id, int) or isinstance(world_id, bool) or world_id < 1:
            return AutonomyOutcome(None, None, None, "invalid_world")
        if not isinstance(limits, CognitionCallLimits):
            return AutonomyOutcome(None, None, None, "invalid_limits")
        limits.validated()
        ledger = CognitionCallLedgerService(self._conn, clock=self._clock)
        router = CognitionCallRouter(self._conn, self._provider, clock=self._clock)
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
            if routed.attempted:
                return outcome
            # Un budget ou debounce individuel ne doit pas affamer les autres
            # résidentes. On garde le premier diagnostic, puis on continue.
            deferred = deferred or outcome
        return deferred or AutonomyOutcome(None, None, None, None)
