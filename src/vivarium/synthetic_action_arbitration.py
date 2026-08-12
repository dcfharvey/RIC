"""Raccord d'arbitrage executable limite aux mondes synthetiques.

Le module rassemble les contrats deja fondes sans les brancher au runtime :
P est evalue exclusivement comme capacite physique, les contributions sont
ramenees par une politique de banc explicite, puis une action gagnante peut
devenir une ``IntentProposal`` idempotente executee par l'orchestrateur
canonique existant. Aucun appel ici ne lit ``repos`` ou ``energie`` et aucune
API ne derive l'heure depuis le wall-clock.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import prod
from typing import Any, Literal, Mapping

from .action_contract import (
    ACTION_START_ACTIVITY,
    ACTION_TRAVERSE,
    ORIGIN_ACTION_ARBITRATION,
    ActionOrchestrator,
    ActionSpecification,
    IntentProposal,
    ValidationResult,
    normalize_action_specification,
)
from .sleep_physiology import PhysicalCapacityPolicy
from .util import parse_iso, to_iso


_LOAD_CLASSES = frozenset({"none", "light", "moderate", "vigorous"})
_SOURCE_KINDS = frozenset({"sleep_regulation", "physical_recovery", "subjective_intention"})
_SOURCE_OWNERS = {
    "sleep_regulation": "SleepPhysiologyService",
    "physical_recovery": "SleepPhysiologyService",
    "subjective_intention": "GoalService",
}


class SyntheticActionArbitrationError(ValueError):
    """Configuration ou frame de banc invalide, avant toute mutation."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _milli(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100_000:
        raise SyntheticActionArbitrationError(f"{field} invalide", code="invalid_synthetic_arbitration")
    return value


def _positive(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SyntheticActionArbitrationError(f"{field} invalide", code="invalid_synthetic_arbitration")
    return value


def _text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 120:
        raise SyntheticActionArbitrationError(f"{field} invalide", code="invalid_synthetic_arbitration")
    return value


def _digest(value: Mapping[str, Any]) -> str:
    try:
        wire = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise SyntheticActionArbitrationError("frame non serialisable", code="invalid_synthetic_arbitration") from exc
    return hashlib.sha256(wire.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PhysicalCostRequest:
    """Demande explicite au futur owner P, sans ecriture de P dans ce lot."""

    operation: Literal["activity", "traversal"]
    physical_load_class: Literal["none", "light", "moderate", "vigorous"] | None = None
    edge_count: int | None = None

    def __post_init__(self) -> None:
        if self.operation == "activity":
            if self.physical_load_class not in _LOAD_CLASSES or self.edge_count is not None:
                raise SyntheticActionArbitrationError("demande d'activite physique invalide", code="invalid_physical_request")
        elif self.operation == "traversal":
            if self.physical_load_class is not None or isinstance(self.edge_count, bool) \
                    or not isinstance(self.edge_count, int) or self.edge_count < 1:
                raise SyntheticActionArbitrationError("demande de traversee physique invalide", code="invalid_physical_request")
        else:
            raise SyntheticActionArbitrationError("operation physique invalide", code="invalid_physical_request")


@dataclass(frozen=True)
class PhysicalCostEvaluation:
    feasible: bool
    required_capacity_milli: int
    cost_milli: int
    reason_code: Literal["physical_capacity_ok", "physical_capacity_insufficient"]


def evaluate_physical_cost(
    policy: PhysicalCapacityPolicy, request: PhysicalCostRequest, *, capacity_milli: Any
) -> PhysicalCostEvaluation:
    """Evalue une requete P sans muter d'etat ni consulter le legacy."""
    capacity = _milli(capacity_milli, field="capacite physique")
    if request.operation == "activity":
        assert request.physical_load_class is not None
        load = request.physical_load_class
        required = int(policy.minimum_capacity_milli[load])
        cost = int(policy.activity_cost_per_hour_milli[load])
    else:
        assert request.edge_count is not None
        required = int(policy.traversal_cost_per_edge_milli) * request.edge_count
        cost = required
    feasible = capacity >= required
    return PhysicalCostEvaluation(
        feasible, required, cost,
        "physical_capacity_ok" if feasible else "physical_capacity_insufficient",
    )


@dataclass(frozen=True)
class SyntheticArbitrationPolicy:
    """Calibration d'ingenierie de banc, distincte du catalogue persistant."""

    policy_key: str
    version: int
    source_mappings: Mapping[str, str]
    quasi_equality_milli: int
    current_action_inertia_milli: int
    reassessment_seconds: int
    provenance: str

    @classmethod
    def from_configuration(
        cls, policy_key: Any, version: Any, configuration: Any, provenance: Any
    ) -> "SyntheticArbitrationPolicy":
        if not isinstance(configuration, Mapping) or configuration.get("schema_version") != 1:
            raise SyntheticActionArbitrationError("politique de banc invalide", code="invalid_synthetic_arbitration")
        mappings = configuration.get("source_mappings")
        correlation_groups = configuration.get("correlation_groups")
        aggregation = configuration.get("aggregation")
        inertia = configuration.get("current_action_inertia")
        equality = configuration.get("quasi_equality")
        reassessment = configuration.get("reassessment")
        if not all(isinstance(value, Mapping) for value in (
            mappings, correlation_groups, aggregation, inertia, equality, reassessment,
        )):
            raise SyntheticActionArbitrationError("politique de banc incomplete", code="invalid_synthetic_arbitration")
        if set(mappings) != _SOURCE_KINDS \
                or correlation_groups != {"kind": "declared_by_source_mapping.v1"} \
                or aggregation != {"kind": "max_per_group_then_saturating_sum.v1"}:
            raise SyntheticActionArbitrationError("politique de banc incompatible", code="invalid_synthetic_arbitration")
        groups: dict[str, str] = {}
        for source in sorted(_SOURCE_KINDS):
            mapping = mappings[source]
            if not isinstance(mapping, Mapping) or set(mapping) != {"transform", "correlation_group"} \
                    or mapping["transform"] != "identity_milli.v1":
                raise SyntheticActionArbitrationError("mapping de source invalide", code="invalid_synthetic_arbitration")
            groups[source] = _text(mapping["correlation_group"], field="groupe de correlation")
        if set(inertia) != {"max_bonus_milli"} or set(equality) != {"band_milli"} \
                or set(reassessment) != {"interval_seconds"}:
            raise SyntheticActionArbitrationError("controles de politique invalides", code="invalid_synthetic_arbitration")
        return cls(
            _text(policy_key, field="politique"), _positive(version, field="version"), groups,
            _milli(equality["band_milli"], field="bande d'egalite"),
            _milli(inertia["max_bonus_milli"], field="inertie"),
            _positive(reassessment["interval_seconds"], field="reevaluation"),
            _text(provenance, field="provenance"),
        )


@dataclass(frozen=True)
class ArbitrationContribution:
    """Une raison explicable de soutenir une action, jamais une mutation."""

    specification: ActionSpecification
    source_kind: Literal["sleep_regulation", "physical_recovery", "subjective_intention"]
    raw_score_milli: int
    owner: str
    provenance: str
    feasible: bool = True

    def __post_init__(self) -> None:
        _milli(self.raw_score_milli, field="score brut")
        if self.source_kind not in _SOURCE_KINDS or not isinstance(self.feasible, bool):
            raise SyntheticActionArbitrationError("contribution invalide", code="invalid_synthetic_arbitration")
        if self.owner != _SOURCE_OWNERS[self.source_kind]:
            raise SyntheticActionArbitrationError(
                "owner de contribution invalide", code="invalid_synthetic_arbitration"
            )
        _text(self.provenance, field="provenance")


@dataclass(frozen=True)
class ActionArbitrationFrame:
    world_id: int
    actor_key: str
    canonical_at: str
    expected_event_seq: int
    policy: SyntheticArbitrationPolicy
    contributions: tuple[ArbitrationContribution, ...]
    current_action_key: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.world_id, bool) or not isinstance(self.world_id, int) or self.world_id < 1:
            raise SyntheticActionArbitrationError("monde invalide", code="invalid_synthetic_arbitration")
        _text(self.actor_key, field="acteur")
        try:
            to_iso(parse_iso(self.canonical_at))
        except (TypeError, ValueError) as exc:
            raise SyntheticActionArbitrationError("instant canonique invalide", code="invalid_synthetic_arbitration") from exc
        if isinstance(self.expected_event_seq, bool) or not isinstance(self.expected_event_seq, int) or self.expected_event_seq < 0:
            raise SyntheticActionArbitrationError("sequence canonique invalide", code="invalid_synthetic_arbitration")
        if not isinstance(self.policy, SyntheticArbitrationPolicy) or not self.contributions:
            raise SyntheticActionArbitrationError("frame incomplete", code="invalid_synthetic_arbitration")
        if self.current_action_key is not None:
            _text(self.current_action_key, field="action courante")

    @property
    def digest(self) -> str:
        return _digest({
            "world_id": self.world_id, "actor_key": self.actor_key, "canonical_at": to_iso(parse_iso(self.canonical_at)),
            "expected_event_seq": self.expected_event_seq,
            "policy": {"key": self.policy.policy_key, "version": self.policy.version},
            "current_action_key": self.current_action_key,
            "contributions": [
                {"action_key": item.specification.action_key, "kind": item.specification.action_kind,
                 "params": dict(item.specification.params), "source": item.source_kind,
                 "raw": item.raw_score_milli, "owner": item.owner, "provenance": item.provenance,
                 "feasible": item.feasible}
                # Les contributions forment un multiensemble : leur ordre
                # d'enumeration ne constitue jamais une nouvelle frontiere.
                # Tous les champs semantiques qui peuvent differer font donc
                # partie de l'ordre canonique.
                for item in sorted(
                    self.contributions,
                    key=lambda value: (
                        value.specification.action_key,
                        value.source_kind,
                        value.owner,
                        value.provenance,
                        value.raw_score_milli,
                        value.feasible,
                    ),
                )
            ],
        })


@dataclass(frozen=True)
class ArbitratedAction:
    specification: ActionSpecification
    score_milli: int
    feasible: bool
    contribution_sources: tuple[str, ...]


@dataclass(frozen=True)
class ActionArbitrationDecision:
    frame_digest: str
    outcome: Literal["transition", "continue_current_until_boundary", "reassess_at_boundary"]
    winner: ArbitratedAction | None
    candidates: tuple[ArbitratedAction, ...]
    reason_code: str
    reassessment_seconds: int


class ActionArbitrationService:
    """Arbitre executable de banc; aucun branchement SimulationEngine ici."""

    @staticmethod
    def _candidate(frame: ActionArbitrationFrame, action_key: str) -> ArbitratedAction:
        items = tuple(item for item in frame.contributions if item.specification.action_key == action_key)
        if not items:
            raise AssertionError("candidat absent")
        spec = items[0].specification
        if any(item.specification != spec for item in items):
            raise SyntheticActionArbitrationError("action_key ambigu", code="invalid_synthetic_arbitration")
        feasible = all(item.feasible for item in items)
        grouped: dict[str, int] = {}
        for item in items:
            group = frame.policy.source_mappings[item.source_kind]
            grouped[group] = max(grouped.get(group, 0), item.raw_score_milli)
        score = round(100_000 * (1.0 - prod(1.0 - value / 100_000.0 for value in grouped.values())))
        if frame.current_action_key == action_key:
            score = min(100_000, score + frame.policy.current_action_inertia_milli)
        return ArbitratedAction(spec, score, feasible, tuple(sorted(item.source_kind for item in items)))

    def decide(self, frame: ActionArbitrationFrame) -> ActionArbitrationDecision:
        keys = sorted({item.specification.action_key for item in frame.contributions})
        candidates = tuple(self._candidate(frame, key) for key in keys)
        viable = tuple(item for item in candidates if item.feasible)
        if not viable:
            return ActionArbitrationDecision(frame.digest, "reassess_at_boundary", None, candidates, "no_feasible_action", frame.policy.reassessment_seconds)
        top = max(item.score_milli for item in viable)
        leaders = tuple(item for item in viable if top - item.score_milli <= frame.policy.quasi_equality_milli)
        if len(leaders) != 1:
            if frame.current_action_key and any(item.specification.action_key == frame.current_action_key for item in leaders):
                winner = next(item for item in leaders if item.specification.action_key == frame.current_action_key)
                return ActionArbitrationDecision(frame.digest, "continue_current_until_boundary", winner, candidates, "current_action_quasi_equal", frame.policy.reassessment_seconds)
            return ActionArbitrationDecision(frame.digest, "reassess_at_boundary", None, candidates, "quasi_equal_actions", frame.policy.reassessment_seconds)
        winner = leaders[0]
        if winner.specification.action_key == frame.current_action_key:
            return ActionArbitrationDecision(frame.digest, "continue_current_until_boundary", winner, candidates, "current_action_leads", frame.policy.reassessment_seconds)
        return ActionArbitrationDecision(frame.digest, "transition", winner, candidates, "highest_calibrated_score", frame.policy.reassessment_seconds)

    @staticmethod
    def proposal_for(frame: ActionArbitrationFrame, decision: ActionArbitrationDecision) -> IntentProposal | None:
        """Meme frame -> meme identite; nouvelle frontiere -> nouveau digest."""
        if decision.frame_digest != frame.digest:
            raise SyntheticActionArbitrationError("decision hors frame", code="invalid_synthetic_arbitration")
        if decision.outcome != "transition" or decision.winner is None:
            return None
        # Le registre d'actions impose une cle commencant par une lettre. La
        # troncature conserve 63 hexadecimaux (252 bits) : elle est technique,
        # deterministe et ne devient pas une identite comportementale.
        proposal_id = f"a{decision.frame_digest[:63]}"
        spec = decision.winner.specification
        if spec.action_kind == ACTION_START_ACTIVITY:
            return IntentProposal.start_activity(
                proposal_id, frame.actor_key, spec.params["activity_type"], spec.params["target_location_key"],
                origin=ORIGIN_ACTION_ARBITRATION,
            )
        if spec.action_kind == ACTION_TRAVERSE:
            return IntentProposal.traverse(
                proposal_id, frame.actor_key, spec.params["connector_key"], spec.params["target_location_key"],
                origin=ORIGIN_ACTION_ARBITRATION,
            )
        raise SyntheticActionArbitrationError("action gagnante inconnue", code="invalid_synthetic_arbitration")

    def execute_synthetic(
        self, conn: Any, frame: ActionArbitrationFrame, *, clock: Any = None
    ) -> tuple[ActionArbitrationDecision, ValidationResult | None]:
        """Seul pont de banc vers le moteur : l'orchestrateur revalide toujours."""
        decision = self.decide(frame)
        proposal = self.proposal_for(frame, decision)
        if proposal is None:
            return decision, None
        result = ActionOrchestrator(conn, clock=clock).execute(
            frame.world_id, proposal, effective_at=to_iso(parse_iso(frame.canonical_at)),
            expected_event_seq=frame.expected_event_seq,
        )
        return decision, result


def synthetic_specification(action_kind: Any, params: Any) -> ActionSpecification:
    """Raccourci de banc vers le vocabulaire executable unique."""
    return normalize_action_specification(action_kind, params)
