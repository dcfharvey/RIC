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
import sqlite3
from dataclasses import dataclass
from math import prod
from typing import Any, Literal, Mapping

from .action_arbitration import ActionArbitrationFoundationService
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
from .circadian_model import RegulationInput
from .goals import GoalService
from .physical_capacity import (
    PhysicalCapacityError,
    PhysicalRequest,
    evaluate_physical_request,
)
from .repro import max_seq
from .sleep_physiology import (
    PhysicalCapacityPolicy,
    SleepPhysiologyFoundationService,
    SleepPhysiologyService,
)
from .util import Clock, parse_iso, to_iso


_LOAD_CLASSES = frozenset({"none", "light", "moderate", "vigorous"})
_SOURCE_KINDS = frozenset({"sleep_regulation", "physical_recovery", "subjective_intention"})
_SOURCE_OWNERS = {
    "sleep_regulation": "SleepPhysiologyService",
    "physical_recovery": "SleepPhysiologyService",
    "subjective_intention": "GoalService",
}
_TRANSFORMS = frozenset({"identity_milli.v1", "linear_clamped_milli.v1"})


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
class PhysicalCostRequest(PhysicalRequest):
    """Adaptateur historique du banc vers le contrat P commun."""

    def __post_init__(self) -> None:
        try:
            super().__post_init__()
        except PhysicalCapacityError as exc:
            raise SyntheticActionArbitrationError(str(exc), code=exc.code) from exc


@dataclass(frozen=True)
class PhysicalCostEvaluation:
    """Compatibilite du banc; ``cost_milli`` n'est pas utilise par le runtime."""

    feasible: bool
    required_capacity_milli: int
    cost_milli: int
    reason_code: Literal["physical_capacity_ok", "physical_capacity_insufficient"]


def evaluate_physical_cost(
    policy: PhysicalCapacityPolicy, request: PhysicalCostRequest, *, capacity_milli: Any
) -> PhysicalCostEvaluation:
    """Adapte l'ancien resultat de banc sans dupliquer les maths P."""
    try:
        result = evaluate_physical_request(policy, request, capacity_milli=capacity_milli)
    except PhysicalCapacityError as exc:
        raise SyntheticActionArbitrationError(str(exc), code=exc.code) from exc
    cost = (
        result.activity_rate_milli_per_hour
        if request.operation == "activity"
        else result.traversal_cost_milli
    )
    assert cost is not None
    return PhysicalCostEvaluation(
        result.feasible, result.required_capacity_milli, cost, result.reason_code
    )


@dataclass(frozen=True)
class SyntheticSourceMapping:
    """Mapping versionne de banc : normalisation n'est jamais calibration implicite."""

    transform_kind: Literal["identity_milli.v1", "linear_clamped_milli.v1"]
    correlation_group: str
    input_low_milli: int | None = None
    input_high_milli: int | None = None
    direction: Literal["ascending", "descending"] | None = None

    def __post_init__(self) -> None:
        if self.transform_kind not in _TRANSFORMS:
            raise SyntheticActionArbitrationError("transform invalide", code="invalid_synthetic_arbitration")
        _text(self.correlation_group, field="groupe de correlation")
        if self.transform_kind == "identity_milli.v1":
            if any(value is not None for value in (self.input_low_milli, self.input_high_milli, self.direction)):
                raise SyntheticActionArbitrationError("identity enrichie interdite", code="invalid_synthetic_arbitration")
            return
        low = _milli(self.input_low_milli, field="borne basse")
        high = _milli(self.input_high_milli, field="borne haute")
        if high <= low or self.direction not in {"ascending", "descending"}:
            raise SyntheticActionArbitrationError("mapping lineaire invalide", code="invalid_synthetic_arbitration")

    @property
    def calibrated(self) -> bool:
        return self.transform_kind != "identity_milli.v1"

    def apply(self, raw_score_milli: Any) -> int:
        raw = _milli(raw_score_milli, field="score brut")
        if self.transform_kind == "identity_milli.v1":
            return raw
        assert self.input_low_milli is not None and self.input_high_milli is not None
        assert self.direction is not None
        bounded = min(self.input_high_milli, max(self.input_low_milli, raw))
        scaled = round(
            (bounded - self.input_low_milli) * 100_000
            / (self.input_high_milli - self.input_low_milli)
        )
        return scaled if self.direction == "ascending" else 100_000 - scaled


@dataclass(frozen=True)
class SyntheticArbitrationPolicy:
    """Calibration d'ingenierie de banc, distincte du catalogue persistant."""

    policy_key: str
    version: int
    source_mappings: Mapping[str, SyntheticSourceMapping]
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
        parsed: dict[str, SyntheticSourceMapping] = {}
        for source in sorted(_SOURCE_KINDS):
            mapping = mappings[source]
            if not isinstance(mapping, Mapping):
                raise SyntheticActionArbitrationError("mapping de source invalide", code="invalid_synthetic_arbitration")
            transform = mapping.get("transform")
            group = _text(mapping.get("correlation_group"), field="groupe de correlation")
            if transform == "identity_milli.v1" and set(mapping) == {"transform", "correlation_group"}:
                parsed[source] = SyntheticSourceMapping(transform, group)
            elif transform == "linear_clamped_milli.v1" and set(mapping) == {
                "transform", "correlation_group", "input_low_milli", "input_high_milli", "direction"
            }:
                parsed[source] = SyntheticSourceMapping(
                    transform, group,
                    _milli(mapping["input_low_milli"], field="borne basse"),
                    _milli(mapping["input_high_milli"], field="borne haute"),
                    mapping["direction"],
                )
            else:
                raise SyntheticActionArbitrationError("mapping de source invalide", code="invalid_synthetic_arbitration")
        if set(inertia) != {"max_bonus_milli"} or set(equality) != {"band_milli"} \
                or set(reassessment) != {"interval_seconds"}:
            raise SyntheticActionArbitrationError("controles de politique invalides", code="invalid_synthetic_arbitration")
        return cls(
            _text(policy_key, field="politique"), _positive(version, field="version"), parsed,
            _milli(equality["band_milli"], field="bande d'egalite"),
            _milli(inertia["max_bonus_milli"], field="inertie"),
            _positive(reassessment["interval_seconds"], field="reevaluation"),
            _text(provenance, field="provenance"),
        )

    @property
    def fully_calibrated(self) -> bool:
        return all(mapping.calibrated for mapping in self.source_mappings.values())


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
            "world_id": self.world_id, "actor_key": self.actor_key,
            "canonical_at": to_iso(parse_iso(self.canonical_at)),
            "expected_event_seq": self.expected_event_seq,
            "policy": {"key": self.policy.policy_key, "version": self.policy.version},
            "current_action_key": self.current_action_key,
            "contributions": [
                {"action_key": item.specification.action_key, "kind": item.specification.action_kind,
                 "params": dict(item.specification.params), "source": item.source_kind,
                 "raw": item.raw_score_milli, "owner": item.owner, "provenance": item.provenance,
                 "feasible": item.feasible}
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
            mapping = frame.policy.source_mappings[item.source_kind]
            transformed = mapping.apply(item.raw_score_milli)
            grouped[mapping.correlation_group] = max(
                grouped.get(mapping.correlation_group, 0), transformed
            )
        score = round(100_000 * (1.0 - prod(1.0 - value / 100_000.0 for value in grouped.values())))
        if frame.current_action_key == action_key:
            score = min(100_000, score + frame.policy.current_action_inertia_milli)
        return ArbitratedAction(spec, score, feasible, tuple(sorted(item.source_kind for item in items)))

    def decide(self, frame: ActionArbitrationFrame) -> ActionArbitrationDecision:
        keys = sorted({item.specification.action_key for item in frame.contributions})
        candidates = tuple(self._candidate(frame, key) for key in keys)
        viable = tuple(item for item in candidates if item.feasible)
        if not viable:
            return ActionArbitrationDecision(
                frame.digest, "reassess_at_boundary", None, candidates,
                "no_feasible_action", frame.policy.reassessment_seconds,
            )
        top = max(item.score_milli for item in viable)
        leaders = tuple(item for item in viable if top - item.score_milli <= frame.policy.quasi_equality_milli)
        if len(leaders) != 1:
            if frame.current_action_key and any(item.specification.action_key == frame.current_action_key for item in leaders):
                winner = next(item for item in leaders if item.specification.action_key == frame.current_action_key)
                return ActionArbitrationDecision(
                    frame.digest, "continue_current_until_boundary", winner, candidates,
                    "current_action_quasi_equal", frame.policy.reassessment_seconds,
                )
            return ActionArbitrationDecision(
                frame.digest, "reassess_at_boundary", None, candidates,
                "quasi_equal_actions", frame.policy.reassessment_seconds,
            )
        winner = leaders[0]
        if winner.specification.action_key == frame.current_action_key:
            return ActionArbitrationDecision(
                frame.digest, "continue_current_until_boundary", winner, candidates,
                "current_action_leads", frame.policy.reassessment_seconds,
            )
        return ActionArbitrationDecision(
            frame.digest, "transition", winner, candidates,
            "highest_calibrated_score", frame.policy.reassessment_seconds,
        )

    @staticmethod
    def proposal_for(frame: ActionArbitrationFrame, decision: ActionArbitrationDecision) -> IntentProposal | None:
        """Meme frame -> meme identite; nouvelle frontiere -> nouveau digest."""
        if decision.frame_digest != frame.digest:
            raise SyntheticActionArbitrationError("decision hors frame", code="invalid_synthetic_arbitration")
        if decision.outcome != "transition" or decision.winner is None:
            return None
        proposal_id = f"a{decision.frame_digest[:63]}"
        spec = decision.winner.specification
        if spec.action_kind == ACTION_START_ACTIVITY:
            return IntentProposal.start_activity(
                proposal_id, frame.actor_key, spec.params["activity_type"],
                spec.params["target_location_key"], origin=ORIGIN_ACTION_ARBITRATION,
            )
        if spec.action_kind == ACTION_TRAVERSE:
            return IntentProposal.traverse(
                proposal_id, frame.actor_key, spec.params["connector_key"],
                spec.params["target_location_key"], origin=ORIGIN_ACTION_ARBITRATION,
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


class SyntheticCausalArbitrationBuilder:
    """Construit une frame depuis les owners reels, uniquement en monde de banc.

    H/phi alimentent seulement ``sleep_regulation``. P est lu comme capacite
    pour la faisabilite et comme source de ``physical_recovery`` vers ``rest``.
    Les intentions n'existent ici que via les liens explicites GoalService : le
    plan JSON opaque n'est jamais parse. Aucune valeur legacy n'est consultee.
    """

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()
        self._foundation = ActionArbitrationFoundationService(conn, clock=self._clock)
        self._physiology = SleepPhysiologyService(conn, clock=self._clock)
        self._physiology_foundation = SleepPhysiologyFoundationService(conn, clock=self._clock)
        self._goals = GoalService(conn, clock=self._clock)

    def _policy(self, world_id: int) -> SyntheticArbitrationPolicy:
        stored = self._foundation.world_policy(world_id)
        policy = SyntheticArbitrationPolicy.from_configuration(
            stored.policy_key, stored.version, stored.configuration, stored.provenance
        )
        if not policy.fully_calibrated:
            raise SyntheticActionArbitrationError(
                "identity_milli.v1 interdit sur sources causales",
                code="uncalibrated_identity_mapping",
            )
        return policy

    def _physical_evaluation(
        self,
        world_id: int,
        specification: ActionSpecification,
        policy: PhysicalCapacityPolicy,
        capacity_milli: int,
    ) -> PhysicalCostEvaluation:
        if specification.action_kind == ACTION_START_ACTIVITY:
            row = self._conn.execute(
                "SELECT physical_load_class FROM activity_definition "
                "WHERE world_id=? AND activity_type=?",
                (world_id, specification.params["activity_type"]),
            ).fetchone()
            if row is None or row["physical_load_class"] not in _LOAD_CLASSES:
                raise SyntheticActionArbitrationError(
                    "classe physique d'activite absente",
                    code="activity_physical_class_missing",
                )
            request = PhysicalCostRequest(
                "activity", physical_load_class=row["physical_load_class"]
            )
        elif specification.action_kind == ACTION_TRAVERSE:
            # Le contrat d'action v2 represente une traversee de connecteur :
            # une proposition correspond donc a une seule arete canonique.
            request = PhysicalCostRequest("traversal", edge_count=1)
        else:
            raise SyntheticActionArbitrationError(
                "action sans contrat physique", code="invalid_physical_request"
            )
        return evaluate_physical_cost(policy, request, capacity_milli=capacity_milli)

    @staticmethod
    def _require_named_activity(
        specification: Any, expected_type: str, *, field: str
    ) -> ActionSpecification:
        if not isinstance(specification, ActionSpecification) \
                or specification.action_kind != ACTION_START_ACTIVITY \
                or specification.params.get("activity_type") != expected_type:
            raise SyntheticActionArbitrationError(
                f"{field} invalide", code="invalid_causal_action"
            )
        return specification

    def build(
        self,
        world_id: int,
        actor_key: str,
        *,
        canonical_at: str,
        sleep_specification: ActionSpecification,
        rest_specification: ActionSpecification,
        wake_source: RegulationInput,
        current_action_key: str | None = None,
    ) -> ActionArbitrationFrame:
        """Lit H/phi/P + intention active et produit une frame non mutante."""
        if wake_source.state != "wake":
            raise SyntheticActionArbitrationError(
                "source de veille requise", code="invalid_causal_source"
            )
        at = to_iso(parse_iso(canonical_at))
        actor = _text(actor_key, field="acteur")
        sleep_spec = self._require_named_activity(
            sleep_specification, "sleep", field="specification sommeil"
        )
        rest_spec = self._require_named_activity(
            rest_specification, "rest", field="specification repos physique"
        )
        policy = self._policy(world_id)
        p_policy = self._physiology_foundation.validate_physical_capacity_configuration(world_id)
        state = self._physiology.read_state(world_id, actor)
        projection = self._physiology.project_synthetic(world_id, actor, wake_source)
        capacity = state.regulation.physical_capacity_milli

        specs: dict[str, ActionSpecification] = {
            sleep_spec.action_key: sleep_spec,
            rest_spec.action_key: rest_spec,
        }
        subjective: list[tuple[ActionSpecification, int, str]] = []
        intention = self._goals.active_intention(world_id, actor)
        if intention is not None:
            for link in self._goals.intention_action_links(
                world_id, actor, intention["intention_key"]
            ):
                spec = normalize_action_specification(link["action_kind"], link["params"])
                if spec.action_key != link["action_key"]:
                    raise SyntheticActionArbitrationError(
                        "action_key subjectif incoherent", code="subjective_link_corrupt"
                    )
                specs.setdefault(spec.action_key, spec)
                if specs[spec.action_key] != spec:
                    raise SyntheticActionArbitrationError(
                        "action_key subjectif ambigu", code="subjective_link_corrupt"
                    )
                # Conversion d'unite seulement : GoalService persiste 0..1000,
                # l'arbitre transporte 0..100000. La calibration vient ensuite
                # du mapping versionne et non de cette multiplication.
                subjective.append(
                    (spec, int(link["subjective_strength_milli"]) * 100, link["provenance"])
                )

        feasibility = {
            key: self._physical_evaluation(world_id, spec, p_policy, capacity).feasible
            for key, spec in specs.items()
        }
        contributions: list[ArbitrationContribution] = [
            ArbitrationContribution(
                sleep_spec, "sleep_regulation",
                round(projection.propensity.sleep_propensity * 100_000),
                "SleepPhysiologyService", "sleep_physiology_h_phi",
                feasibility[sleep_spec.action_key],
            ),
            ArbitrationContribution(
                rest_spec, "physical_recovery", capacity,
                "SleepPhysiologyService", "physical_capacity_p",
                feasibility[rest_spec.action_key],
            ),
        ]
        contributions.extend(
            ArbitrationContribution(
                spec, "subjective_intention", raw, "GoalService", provenance,
                feasibility[spec.action_key],
            )
            for spec, raw, provenance in subjective
        )
        return ActionArbitrationFrame(
            world_id, actor, at, max_seq(self._conn, world_id), policy,
            tuple(contributions), current_action_key,
        )

    def build_owner_backed(
        self,
        world_id: int,
        actor_key: str,
        *,
        canonical_at: str,
        sleep_specification: ActionSpecification,
        rest_specification: ActionSpecification,
        current_action_key: str | None = None,
    ) -> ActionArbitrationFrame:
        """Construit une frame depuis la source lumineuse owner-backed V1.

        Cette entree ne recoit volontairement aucun ``RegulationInput``. Le
        resolver derive l'etat depuis l'horloge, la position, l'activite et les
        assignments lumineux canoniques. ``build`` demeure disponible pour les
        bancs synthetiques qui fournissent des causes explicites.
        """
        source = self._physiology.resolve_light_source_owner_backed(
            world_id, actor_key, at_time=canonical_at
        )
        return self.build(
            world_id,
            actor_key,
            canonical_at=source.canonical_at,
            sleep_specification=sleep_specification,
            rest_specification=rest_specification,
            wake_source=source.source,
            current_action_key=current_action_key,
        )

    def audit_decision(
        self, frame: ActionArbitrationFrame, decision: ActionArbitrationDecision
    ) -> int:
        """Persiste uniquement la provenance operateur, jamais le canon."""
        if decision.frame_digest != frame.digest:
            raise SyntheticActionArbitrationError(
                "decision hors frame", code="invalid_synthetic_arbitration"
            )
        options = [
            {
                "action_key": item.specification.action_key,
                "score_milli": item.score_milli,
                "feasible": item.feasible,
            }
            for item in decision.candidates
        ]
        sources = [
            {
                "action_key": item.specification.action_key,
                "source_kind": item.source_kind,
                "owner": item.owner,
                "provenance": item.provenance,
                "raw_score_milli": item.raw_score_milli,
                "transformed_score_milli": frame.policy.source_mappings[item.source_kind].apply(
                    item.raw_score_milli
                ),
            }
            for item in frame.contributions
        ]
        result = {
            "outcome": decision.outcome,
            "winner_action_key": None if decision.winner is None else decision.winner.specification.action_key,
            "reason_code": decision.reason_code,
        }
        return self._foundation.record_private_audit(
            frame.world_id,
            frame_digest=frame.digest,
            options=options,
            sources=sources,
            result=result,
            canonical_at=frame.canonical_at,
            reason_code="synthetic_causal_arbitration",
        )


def synthetic_specification(action_kind: Any, params: Any) -> ActionSpecification:
    """Raccourci de banc vers le vocabulaire executable unique."""
    return normalize_action_specification(action_kind, params)
