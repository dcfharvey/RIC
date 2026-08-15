"""Occasion d'arrivée initiale, unique, bornée et ancrée dans le canon.

L'arrivée n'est ni une horloge cachée ni une volonté imposée. Le contexte
initial commun établit que les résidentes ont accepté de vivre ensemble; ce
cycle leur offre donc une seule décision de traversée avant que la politique de
besoins n'initialise leurs activités. L'appel reste soumis au ledger, au budget
et au contrat moteur--cognition.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from .activities import ActivityEngine
from .cognition import CognitionProvider
from .cognition_call_ledger import CognitionCallLedgerService
from .cognitive_flow import CognitiveFlowScheduler
from .cognition_policy import CALL_TRIGGER_INITIAL_ARRIVAL, CognitionCallLimits
from .cognition_router import CognitionCallRouter, CognitionCallRouterError, RoutedCognitionCall
from .util import Clock


class InitialArrivalCycleError(ValueError):
    """Configuration d'arrivée invalide, avant toute mutation canonique."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class InitialArrivalOutcome:
    """Une seule tentative, afin que le démarrage reste lisible et borné."""

    pending: bool
    character_key: str | None
    routed: RoutedCognitionCall | None


class InitialArrivalCycle:
    """Distribue une occasion d'arrivée à chaque résidente sapiente, une fois."""

    def __init__(
        self, conn: sqlite3.Connection, provider: CognitionProvider,
        clock: Clock | None = None,
        flow_scheduler: CognitiveFlowScheduler | None = None,
    ) -> None:
        self._conn = conn
        self._provider = provider
        self._clock = clock or Clock()
        self._flow_scheduler = flow_scheduler

    @staticmethod
    def _world_id(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise InitialArrivalCycleError("monde invalide", code="invalid_initial_arrival_cycle")
        return value

    def _arrival_seq(self, world_id: int) -> int | None:
        row = self._conn.execute(
            "SELECT seq FROM canonical_event WHERE world_id = ? "
            "AND event_type = 'world_initial_context_set' ORDER BY seq DESC LIMIT 1",
            (world_id,),
        ).fetchone()
        return None if row is None else int(row["seq"])

    def _sapient_keys(self, world_id: int) -> tuple[str, ...]:
        rows = self._conn.execute(
            "SELECT c.key, o.resolved_initial_definition_json "
            "FROM character c JOIN character_instance_origin o ON o.character_id = c.id "
            "WHERE c.world_id = ? ORDER BY c.key",
            (world_id,),
        ).fetchall()
        keys: list[str] = []
        for row in rows:
            try:
                components = json.loads(row["resolved_initial_definition_json"]).get("components", [])
                sapient = any(
                    isinstance(component, dict)
                    and component.get("key") == "cognition.profile"
                    and component.get("config", {}).get("level") == "sapient"
                    for component in components
                )
            except (TypeError, ValueError):
                sapient = False
            if sapient:
                keys.append(row["key"])
        return tuple(keys)

    def _eligible_keys(self, world_id: int, arrival_seq: int) -> tuple[str, ...]:
        source_key = f"arrival_{arrival_seq}"
        ledger = CognitionCallLedgerService(self._conn)
        eligible: list[str] = []
        for character_key in self._sapient_keys(world_id):
            history = ledger.history(world_id, character_key)
            if any(
                record.trigger == CALL_TRIGGER_INITIAL_ARRIVAL and record.source_key == source_key
                for record in history
            ):
                continue
            moved = self._conn.execute(
                "SELECT 1 FROM canonical_event WHERE world_id = ? AND seq > ? "
                "AND event_type = 'character_moved' AND json_extract(payload, '$.character') = ? LIMIT 1",
                (world_id, arrival_seq, character_key),
            ).fetchone()
            if moved is None:
                active = self._conn.execute(
                    "SELECT a.type FROM activity a JOIN character c ON c.id = a.character_id "
                    "WHERE a.world_id = ? AND c.key = ? AND a.status = 'active' "
                    "ORDER BY a.id DESC LIMIT 1",
                    (world_id, character_key),
                ).fetchone()
                # L'arrivée ne casse jamais une activité significative. Seul
                # idle est la réservation technique remplaçable au démarrage.
                if active is None or active["type"] == "idle":
                    eligible.append(character_key)
        return tuple(eligible)

    def _started(self, world_id: int, arrival_seq: int) -> bool:
        """Distingue l'onboarding neuf d'un monde déjà déplacé manuellement."""
        source_key = f"arrival_{arrival_seq}"
        admitted = self._conn.execute(
            "SELECT 1 FROM cognition_call_admission WHERE world_id = ? "
            "AND trigger = ? AND source_key = ? LIMIT 1",
            (world_id, CALL_TRIGGER_INITIAL_ARRIVAL, source_key),
        ).fetchone()
        if admitted is not None:
            return True
        moved = self._conn.execute(
            "SELECT 1 FROM canonical_event WHERE world_id = ? AND seq > ? "
            "AND event_type = 'character_moved' LIMIT 1",
            (world_id, arrival_seq),
        ).fetchone()
        return moved is None

    def tick(self, world_id: Any, limits: Any) -> InitialArrivalOutcome:
        world_id = self._world_id(world_id)
        if not isinstance(limits, CognitionCallLimits):
            raise InitialArrivalCycleError("limites cognitives invalides", code="invalid_initial_arrival_cycle")
        limits.validated()
        arrival_seq = self._arrival_seq(world_id)
        if arrival_seq is None:
            return InitialArrivalOutcome(False, None, None)
        if not self._started(world_id, arrival_seq):
            return InitialArrivalOutcome(False, None, None)
        candidates = self._eligible_keys(world_id, arrival_seq)
        if not candidates:
            return InitialArrivalOutcome(False, None, None)
        character_key = candidates[0]
        active = self._conn.execute(
            "SELECT a.type FROM activity a JOIN character c ON c.id = a.character_id "
            "WHERE a.world_id = ? AND c.key = ? AND a.status = 'active' "
            "ORDER BY a.id DESC LIMIT 1",
            (world_id, character_key),
        ).fetchone()
        if active is not None and active["type"] == "idle":
            # Ceci produit activity_aborted dans le journal canonique. Ce n'est
            # pas une annulation silencieuse : l'idle était la réservation
            # technique qui aurait précisément empêché l'occasion d'arrivée.
            ActivityEngine(self._conn, clock=self._clock).abort_activity(world_id, character_key)
        try:
            routed = CognitionCallRouter(
                self._conn, self._provider, clock=self._clock,
                flow_scheduler=self._flow_scheduler,
            ).run(
                world_id,
                character_key,
                CALL_TRIGGER_INITIAL_ARRIVAL,
                f"arrival_{arrival_seq}",
                f"arrival_{character_key}_{arrival_seq}",
                limits,
            )
        except CognitionCallRouterError as exc:
            raise InitialArrivalCycleError(str(exc), code=exc.code) from exc
        # Une admission, même dégradée, consomme l'occasion. Le prochain tick
        # pourra donc passer à la résidente suivante sans retry caché.
        return InitialArrivalOutcome(len(candidates) > 1, character_key, routed)
