"""Contrat fermé entre une cognition externe et le moteur canonique.

Une intention est une proposition non canonique. L'orchestrateur en valide la
forme puis délègue uniquement vers une action explicitement enregistrée. Une
intention refusée ne produit aucune écriture; une intention acceptée rattache
sa provenance à l'événement canonique qui a réellement modifié le monde.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from .registry import _KEY_RE
from .traversal import TraversalEngine, TraversalError
from .db import transaction
from .util import Clock


CONTRACT_SCHEMA_VERSION = 1
ACTION_TRAVERSE = "traverse"
ORIGIN_COGNITION = "cognition"
ORIGIN_DETERMINISTIC_POLICY = "deterministic_policy"
_ORIGINS = frozenset({ORIGIN_COGNITION, ORIGIN_DETERMINISTIC_POLICY})


class ActionContractError(ValueError):
    """Entrée invalide avant toute tentative de mutation canonique."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _key(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise ActionContractError(f"{label} invalide", code="invalid_action_contract")
    return value


def _world_id(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ActionContractError("monde invalide", code="invalid_world")
    return value


def _frozen_params(value: Any) -> Mapping[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"connector_key", "target_location_key"}:
        raise ActionContractError("paramètres d'intention invalides", code="invalid_action_contract")
    params = {
        "connector_key": _key(value["connector_key"], "cle de connecteur"),
        "target_location_key": _key(value["target_location_key"], "destination"),
    }
    return MappingProxyType(params)


def _deep_freeze(value: Any) -> Any:
    """Empêche un client cognitif de modifier un fait retourné par référence."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    return value


@dataclass(frozen=True)
class IntentProposal:
    """Proposition structurée, sans accès d'écriture ni texte libre.

    Le premier contrat ne contient volontairement qu'une traversée. Étendre le
    vocabulaire implique une validation et un routeur explicitement ajoutés,
    jamais une exécution dynamique d'un nom fourni par un LLM.
    """

    proposal_id: str
    actor_key: str
    action_kind: str
    params: Mapping[str, str]
    origin: str
    budget_units: int
    schema_version: int = CONTRACT_SCHEMA_VERSION

    @classmethod
    def traverse(
        cls,
        proposal_id: Any,
        actor_key: Any,
        connector_key: Any,
        target_location_key: Any,
        *,
        origin: Any = ORIGIN_COGNITION,
        budget_units: Any = 1,
    ) -> "IntentProposal":
        proposal_id = _key(proposal_id, "identifiant de proposition")
        actor_key = _key(actor_key, "acteur")
        if origin not in _ORIGINS:
            raise ActionContractError("provenance d'intention invalide", code="invalid_action_contract")
        if not isinstance(budget_units, int) or isinstance(budget_units, bool) or budget_units < 1:
            raise ActionContractError("budget d'intention invalide", code="invalid_action_contract")
        return cls(
            proposal_id=proposal_id,
            actor_key=actor_key,
            action_kind=ACTION_TRAVERSE,
            params=_frozen_params({
                "connector_key": connector_key,
                "target_location_key": target_location_key,
            }),
            origin=origin,
            budget_units=budget_units,
        )


@dataclass(frozen=True)
class WorldFact:
    """Projection minimale d'un fait canonique produit par une action acceptée."""

    world_id: int
    event_seq: int | None
    event_type: str
    occurred_at: str
    payload: Mapping[str, Any]
    schema_version: int = CONTRACT_SCHEMA_VERSION

    @classmethod
    def state(
        cls, world_id: int, fact_type: str, occurred_at: str, payload: Mapping[str, Any]
    ) -> "WorldFact":
        """Construit un fait d'état lu sans inventer d'événement canonique."""
        return cls(
            world_id=world_id,
            event_seq=None,
            event_type=fact_type,
            occurred_at=occurred_at,
            payload=_deep_freeze(payload),
        )


@dataclass(frozen=True)
class PerceptionCandidate:
    """Fait objectivement accessible, avant attention, interprétation ou mémoire."""

    observer_key: str
    access_kind: str
    fact: WorldFact
    schema_version: int = CONTRACT_SCHEMA_VERSION


@dataclass(frozen=True)
class ValidationResult:
    """Réponse fermée de l'orchestrateur, utilisable par une cognition."""

    proposal_id: str
    status: str  # accepted | refused
    reason_code: str | None
    facts: tuple[WorldFact, ...]
    schema_version: int = CONTRACT_SCHEMA_VERSION


class ActionOrchestrator:
    """Point de passage canonique des intentions externes, initialement minimal."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def _validate_proposal(proposal: Any) -> IntentProposal:
        if not isinstance(proposal, IntentProposal):
            raise ActionContractError("intention invalide", code="invalid_action_contract")
        if proposal.schema_version != CONTRACT_SCHEMA_VERSION:
            raise ActionContractError("version de contrat incompatible", code="unsupported_contract_version")
        _key(proposal.proposal_id, "identifiant de proposition")
        _key(proposal.actor_key, "acteur")
        if proposal.origin not in _ORIGINS:
            raise ActionContractError("provenance d'intention invalide", code="invalid_action_contract")
        if not isinstance(proposal.budget_units, int) or isinstance(proposal.budget_units, bool) or proposal.budget_units < 1:
            raise ActionContractError("budget d'intention invalide", code="invalid_action_contract")
        if proposal.action_kind != ACTION_TRAVERSE:
            raise ActionContractError("type d'action non supporté", code="unsupported_action")
        _frozen_params(proposal.params)
        return proposal

    @staticmethod
    def _fact_from_event(world_id: int, event: sqlite3.Row) -> WorldFact:
        return WorldFact(
            world_id=world_id,
            event_seq=event["seq"],
            event_type=event["event_type"],
            occurred_at=event["occurred_at"],
            payload=_deep_freeze(json.loads(event["payload"])),
        )

    def _existing_fact(self, world_id: int, proposal: IntentProposal) -> WorldFact | None:
        """Retrouve une acceptation antérieure et refuse le recyclage d'un identifiant."""
        event = self._conn.execute(
            "SELECT seq, event_type, occurred_at, payload FROM canonical_event "
            "WHERE world_id = ? AND event_type = 'character_moved' "
            "AND json_extract(payload, '$.action_provenance.proposal_id') = ? "
            "ORDER BY seq DESC LIMIT 1",
            (world_id, proposal.proposal_id),
        ).fetchone()
        if event is None:
            return None
        payload = json.loads(event["payload"])
        provenance = payload.get("action_provenance")
        compatible = (
            payload.get("character") == proposal.actor_key
            and payload.get("connector") == proposal.params["connector_key"]
            and payload.get("to") == proposal.params["target_location_key"]
            and provenance == {"proposal_id": proposal.proposal_id, "origin": proposal.origin}
        )
        if not compatible:
            raise ActionContractError(
                "identifiant de proposition déjà utilisé par une autre intention",
                code="proposal_id_conflict",
            )
        return self._fact_from_event(world_id, event)

    def execute(self, world_id: Any, proposal: Any) -> ValidationResult:
        """Applique une intention supportée, ou retourne un refus stable sans écriture."""
        world_id = _world_id(world_id)
        proposal = self._validate_proposal(proposal)
        # Le verrou transactionnel englobe recherche et exécution : deux retries
        # concurrents ne peuvent pas tous les deux conclure qu'ils sont premiers.
        with transaction(self._conn):
            existing = self._existing_fact(world_id, proposal)
            if existing is not None:
                return ValidationResult(proposal.proposal_id, "accepted", None, (existing,))
            try:
                TraversalEngine(self._conn, clock=self._clock).traverse_character(
                    world_id,
                    proposal.actor_key,
                    proposal.params["connector_key"],
                    proposal.params["target_location_key"],
                    action_provenance={"proposal_id": proposal.proposal_id, "origin": proposal.origin},
                )
            except TraversalError as exc:
                return ValidationResult(proposal.proposal_id, "refused", exc.code, ())

            fact = self._existing_fact(world_id, proposal)
            if fact is None:  # Defensive: accepted state without attributable event is a hard invariant breach.
                raise RuntimeError("action acceptée sans événement canonique attribuable")
            return ValidationResult(proposal.proposal_id, "accepted", None, (fact,))
