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
from .cognition_policy import (
    CALL_TRIGGER_DIRECT_EVENT,
    CALL_TRIGGER_INITIAL_ARRIVAL,
    CALL_TRIGGER_PLANNED_REFLECTION,
    CognitionCallLimits,
)
from .perception import PerceptionError, PerceptionService
from .registry import _KEY_RE
from .util import Clock


_DIRECT_EVENT_SOURCE_RE = re.compile(r"^event_([1-9][0-9]*)$")
_INITIAL_ARRIVAL_SOURCE_RE = re.compile(r"^arrival_([1-9][0-9]*)$")
_IDLE_SOURCE_RE = re.compile(r"^idle_([1-9][0-9]*)$")


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

    def _validate_initial_arrival_source(self, world_id: int, character_key: str, source_key: str) -> int:
        """Ancre l'occasion unique d'arrivée dans le contexte commun immuable.

        Elle ne peut plus être proposée à une résidente qui a déjà réellement
        quitté son point d'arrivée. Ce contrôle évite de transformer un ancien
        contexte en impulsion périodique après redémarrage.
        """
        match = _INITIAL_ARRIVAL_SOURCE_RE.fullmatch(source_key)
        if match is None:
            raise CognitionCallRouterError("source d'arrivée initiale invalide", code="invalid_cognition_call_source")
        event_seq = int(match.group(1))
        event = self._conn.execute(
            "SELECT seq FROM canonical_event WHERE world_id = ? AND seq = ? "
            "AND event_type = 'world_initial_context_set'",
            (world_id, event_seq),
        ).fetchone()
        if event is None:
            raise CognitionCallRouterError("contexte initial introuvable", code="cognition_call_source_not_available")
        moved = self._conn.execute(
            "SELECT 1 FROM canonical_event WHERE world_id = ? AND seq > ? "
            "AND event_type = 'character_moved' AND json_extract(payload, '$.character') = ? LIMIT 1",
            (world_id, event_seq, character_key),
        ).fetchone()
        if moved is not None:
            raise CognitionCallRouterError("arrivée initiale déjà dépassée", code="cognition_call_source_not_available")
        return event_seq

    def _validate_idle_source(self, world_id: int, character_key: str, source_key: str) -> int:
        """Prouve que la réflexion correspond à l'idle encore actif."""
        match = _IDLE_SOURCE_RE.fullmatch(source_key)
        if match is None:
            raise CognitionCallRouterError("source d'idle invalide", code="invalid_cognition_call_source")
        event_seq = int(match.group(1))
        event = self._conn.execute(
            "SELECT occurred_at, payload FROM canonical_event WHERE world_id = ? AND seq = ? "
            "AND event_type = 'activity_started'",
            (world_id, event_seq),
        ).fetchone()
        if event is None:
            raise CognitionCallRouterError("idle source introuvable", code="cognition_call_source_not_available")
        import json
        try:
            payload = json.loads(event["payload"])
        except (TypeError, ValueError) as exc:
            raise CognitionCallRouterError("idle source illisible", code="invalid_cognition_call_source") from exc
        if payload.get("character") != character_key or payload.get("activity") != "idle":
            raise CognitionCallRouterError("idle source hors personnage", code="cognition_call_source_not_available")
        active = self._conn.execute(
            "SELECT a.started_at, a.planned_end_at, l.key AS location FROM activity a "
            "JOIN character c ON c.id = a.character_id "
            "JOIN location l ON l.id = a.location_id "
            "WHERE a.world_id = ? AND c.key = ? AND a.status = 'active' AND a.type = 'idle' "
            "ORDER BY a.id DESC LIMIT 1",
            (world_id, character_key),
        ).fetchone()
        if active is None or active["started_at"] != event["occurred_at"] \
                or active["planned_end_at"] != payload.get("planned_end_at") \
                or active["location"] != payload.get("location"):
            raise CognitionCallRouterError("idle source déjà dépassé", code="cognition_call_source_not_available")
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
        # Une arrivée qui a déjà produit un déplacement ne satisfait plus la
        # source fraîche. Son retry est néanmoins inoffensif et doit conserver
        # le verdict append-only de déduplication, sans rappeler le modèle.
        if trigger == CALL_TRIGGER_INITIAL_ARRIVAL and any(
            record.trigger == trigger and record.source_key == source_key
            for record in self._ledger.history(world_id, character_key)
        ):
            admission = self._ledger.admit(world_id, character_key, trigger, source_key, limits)
            return RoutedCognitionCall(admission, None, None)
        if trigger == CALL_TRIGGER_DIRECT_EVENT:
            after_event_seq = self._validate_direct_event_source(world_id, character_key, source_key) - 1
        elif trigger == CALL_TRIGGER_INITIAL_ARRIVAL:
            after_event_seq = self._validate_initial_arrival_source(world_id, character_key, source_key) - 1
        elif trigger == CALL_TRIGGER_PLANNED_REFLECTION:
            after_event_seq = self._validate_idle_source(world_id, character_key, source_key) - 1
        else:
            raise CognitionCallRouterError("motif d'appel non raccordé", code="unroutable_cognition_call_trigger")
        admission = self._ledger.admit(world_id, character_key, trigger, source_key, limits)
        if not admission.verdict.eligible:
            return RoutedCognitionCall(admission, None, None)
        try:
            turn = CognitionTurnService(self._conn, self._provider, clock=self._clock).run(
                world_id, character_key, proposal_id, after_event_seq=after_event_seq,
                decision_cue=self._decision_cue(world_id, trigger, source_key),
            )
        except CognitionError as exc:
            return RoutedCognitionCall(admission, None, exc.code)
        return RoutedCognitionCall(admission, turn, None)

    def _decision_cue(self, world_id: int, trigger: str, source_key: str) -> dict[str, object]:
        """Expose seulement l'origine établie de l'occasion, jamais une consigne."""
        cue: dict[str, object] = {"trigger": trigger}
        if trigger == CALL_TRIGGER_PLANNED_REFLECTION:
            cue["source"] = source_key
            cue["reason"] = "idle_activity_started"
        if trigger == CALL_TRIGGER_INITIAL_ARRIVAL:
            row = self._conn.execute(
                "SELECT facts_json FROM world_initial_context WHERE world_id = ?", (world_id,)
            ).fetchone()
            if row is not None:
                import json
                cue["initial_shared_facts"] = json.loads(row["facts_json"])
        return cue
