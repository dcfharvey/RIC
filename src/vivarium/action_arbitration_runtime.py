"""Arbitrage causal neutre partage par le runtime actif et les bancs.

Le module ne possede aucun etat canonique. Il lit les owners etablis, produit
une frame deterministe, puis toute transition passe par ``ActionOrchestrator``.
Les API runtime publiques ne recoivent jamais de ``RegulationInput`` libre.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from math import prod
from typing import Any, Literal, Mapping

from .action_arbitration import ActionArbitrationFoundationService
from .activities import ActivityEngine
from .spatial import GraphEngine
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


class ActionArbitrationRuntimeError(ValueError):
    """Configuration ou frame de banc invalide, avant toute mutation."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _milli(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100_000:
        raise ActionArbitrationRuntimeError(f"{field} invalide", code="invalid_synthetic_arbitration")
    return value


def _positive(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ActionArbitrationRuntimeError(f"{field} invalide", code="invalid_synthetic_arbitration")
    return value


def _text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 120:
        raise ActionArbitrationRuntimeError(f"{field} invalide", code="invalid_synthetic_arbitration")
    return value


def _digest(value: Mapping[str, Any]) -> str:
    try:
        wire = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise ActionArbitrationRuntimeError("frame non serialisable", code="invalid_synthetic_arbitration") from exc
    return hashlib.sha256(wire.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PhysicalCostRequest(PhysicalRequest):
    """Adaptateur historique du banc vers le contrat P commun."""

    def __post_init__(self) -> None:
        try:
            super().__post_init__()
        except PhysicalCapacityError as exc:
            raise ActionArbitrationRuntimeError(str(exc), code=exc.code) from exc


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
        raise ActionArbitrationRuntimeError(str(exc), code=exc.code) from exc
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
class SourceMapping:
    """Mapping versionne de banc : normalisation n'est jamais calibration implicite."""

    transform_kind: Literal["identity_milli.v1", "linear_clamped_milli.v1"]
    correlation_group: str
    input_low_milli: int | None = None
    input_high_milli: int | None = None
    direction: Literal["ascending", "descending"] | None = None

    def __post_init__(self) -> None:
        if self.transform_kind not in _TRANSFORMS:
            raise ActionArbitrationRuntimeError("transform invalide", code="invalid_synthetic_arbitration")
        _text(self.correlation_group, field="groupe de correlation")
        if self.transform_kind == "identity_milli.v1":
            if any(value is not None for value in (self.input_low_milli, self.input_high_milli, self.direction)):
                raise ActionArbitrationRuntimeError("identity enrichie interdite", code="invalid_synthetic_arbitration")
            return
        low = _milli(self.input_low_milli, field="borne basse")
        high = _milli(self.input_high_milli, field="borne haute")
        if high <= low or self.direction not in {"ascending", "descending"}:
            raise ActionArbitrationRuntimeError("mapping lineaire invalide", code="invalid_synthetic_arbitration")

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
class ArbitrationRuntimePolicy:
    """Calibration d'ingenierie de banc, distincte du catalogue persistant."""

    policy_key: str
    version: int
    source_mappings: Mapping[str, SourceMapping]
    quasi_equality_milli: int
    current_action_inertia_milli: int
    reassessment_seconds: int
    provenance: str

    @classmethod
    def from_configuration(
        cls, policy_key: Any, version: Any, configuration: Any, provenance: Any
    ) -> "ArbitrationRuntimePolicy":
        if not isinstance(configuration, Mapping) or configuration.get("schema_version") != 1:
            raise ActionArbitrationRuntimeError("politique de banc invalide", code="invalid_synthetic_arbitration")
        mappings = configuration.get("source_mappings")
        correlation_groups = configuration.get("correlation_groups")
        aggregation = configuration.get("aggregation")
        inertia = configuration.get("current_action_inertia")
        equality = configuration.get("quasi_equality")
        reassessment = configuration.get("reassessment")
        if not all(isinstance(value, Mapping) for value in (
            mappings, correlation_groups, aggregation, inertia, equality, reassessment,
        )):
            raise ActionArbitrationRuntimeError("politique de banc incomplete", code="invalid_synthetic_arbitration")
        if set(mappings) != _SOURCE_KINDS \
                or correlation_groups != {"kind": "declared_by_source_mapping.v1"} \
                or aggregation != {"kind": "max_per_group_then_saturating_sum.v1"}:
            raise ActionArbitrationRuntimeError("politique de banc incompatible", code="invalid_synthetic_arbitration")
        parsed: dict[str, SourceMapping] = {}
        for source in sorted(_SOURCE_KINDS):
            mapping = mappings[source]
            if not isinstance(mapping, Mapping):
                raise ActionArbitrationRuntimeError("mapping de source invalide", code="invalid_synthetic_arbitration")
            transform = mapping.get("transform")
            group = _text(mapping.get("correlation_group"), field="groupe de correlation")
            if transform == "identity_milli.v1" and set(mapping) == {"transform", "correlation_group"}:
                parsed[source] = SourceMapping(transform, group)
            elif transform == "linear_clamped_milli.v1" and set(mapping) == {
                "transform", "correlation_group", "input_low_milli", "input_high_milli", "direction"
            }:
                parsed[source] = SourceMapping(
                    transform, group,
                    _milli(mapping["input_low_milli"], field="borne basse"),
                    _milli(mapping["input_high_milli"], field="borne haute"),
                    mapping["direction"],
                )
            else:
                raise ActionArbitrationRuntimeError("mapping de source invalide", code="invalid_synthetic_arbitration")
        if set(inertia) != {"max_bonus_milli"} or set(equality) != {"band_milli"} \
                or set(reassessment) != {"interval_seconds"}:
            raise ActionArbitrationRuntimeError("controles de politique invalides", code="invalid_synthetic_arbitration")
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
            raise ActionArbitrationRuntimeError("contribution invalide", code="invalid_synthetic_arbitration")
        if self.owner != _SOURCE_OWNERS[self.source_kind]:
            raise ActionArbitrationRuntimeError(
                "owner de contribution invalide", code="invalid_synthetic_arbitration"
            )
        _text(self.provenance, field="provenance")


@dataclass(frozen=True)
class ActionArbitrationFrame:
    world_id: int
    actor_key: str
    canonical_at: str
    expected_event_seq: int
    policy: ArbitrationRuntimePolicy
    contributions: tuple[ArbitrationContribution, ...]
    current_action_key: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.world_id, bool) or not isinstance(self.world_id, int) or self.world_id < 1:
            raise ActionArbitrationRuntimeError("monde invalide", code="invalid_synthetic_arbitration")
        _text(self.actor_key, field="acteur")
        try:
            to_iso(parse_iso(self.canonical_at))
        except (TypeError, ValueError) as exc:
            raise ActionArbitrationRuntimeError("instant canonique invalide", code="invalid_synthetic_arbitration") from exc
        if isinstance(self.expected_event_seq, bool) or not isinstance(self.expected_event_seq, int) or self.expected_event_seq < 0:
            raise ActionArbitrationRuntimeError("sequence canonique invalide", code="invalid_synthetic_arbitration")
        if not isinstance(self.policy, ArbitrationRuntimePolicy) or not self.contributions:
            raise ActionArbitrationRuntimeError("frame incomplete", code="invalid_synthetic_arbitration")
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
    """Arbitre deterministe partage; toute transition repasse par le moteur."""

    @staticmethod
    def _candidate(frame: ActionArbitrationFrame, action_key: str) -> ArbitratedAction:
        items = tuple(item for item in frame.contributions if item.specification.action_key == action_key)
        if not items:
            raise AssertionError("candidat absent")
        spec = items[0].specification
        if any(item.specification != spec for item in items):
            raise ActionArbitrationRuntimeError("action_key ambigu", code="invalid_synthetic_arbitration")
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
            raise ActionArbitrationRuntimeError("decision hors frame", code="invalid_synthetic_arbitration")
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
        raise ActionArbitrationRuntimeError("action gagnante inconnue", code="invalid_synthetic_arbitration")

    def execute(
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


class CausalArbitrationBuilder:
    """Construit des frames causales depuis les owners etablis.

    H/phi alimentent ``sleep_regulation``; P reste une capacite physique et la
    source de ``physical_recovery``. Les intentions executables viennent
    uniquement des liens structures de GoalService. Le plan opaque n'est jamais
    parse et aucune valeur legacy repos/energie n'est consultee.
    """

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()
        self._foundation = ActionArbitrationFoundationService(conn, clock=self._clock)
        self._physiology = SleepPhysiologyService(conn, clock=self._clock)
        self._physiology_foundation = SleepPhysiologyFoundationService(conn, clock=self._clock)
        self._goals = GoalService(conn, clock=self._clock)

    def _policy(self, world_id: int) -> ArbitrationRuntimePolicy:
        stored = self._foundation.world_policy(world_id)
        policy = ArbitrationRuntimePolicy.from_configuration(
            stored.policy_key, stored.version, stored.configuration, stored.provenance
        )
        if not policy.fully_calibrated:
            raise ActionArbitrationRuntimeError(
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
                raise ActionArbitrationRuntimeError(
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
            raise ActionArbitrationRuntimeError(
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
            raise ActionArbitrationRuntimeError(
                f"{field} invalide", code="invalid_causal_action"
            )
        return specification

    def _build_from_source(
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
        """Noyau partage; la source explicite reste privee aux adaptateurs de banc."""
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
                    raise ActionArbitrationRuntimeError(
                        "action_key subjectif incoherent", code="subjective_link_corrupt"
                    )
                specs.setdefault(spec.action_key, spec)
                if specs[spec.action_key] != spec:
                    raise ActionArbitrationRuntimeError(
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

    def _nearest_activity_specification(
        self, world_id: int, actor_key: str, activity_type: str
    ) -> ActionSpecification:
        activities = ActivityEngine(self._conn, clock=self._clock)
        row = self._conn.execute(
            "SELECT l.key FROM character ch JOIN location l ON l.id=ch.current_location_id "
            "WHERE ch.world_id=? AND ch.key=?", (world_id, actor_key),
        ).fetchone()
        if row is None:
            raise ActionArbitrationRuntimeError(
                "position canonique absente", code="canonical_position_missing"
            )
        current = row["key"]
        allowed = {current} if activity_type == "idle" else activities.allowed_locations(
            world_id, activity_type
        )
        reachable: list[tuple[int, str]] = []
        graph = GraphEngine(self._conn)
        for location in sorted(allowed):
            path = graph.find_path(world_id, current, location)
            if path is not None:
                reachable.append((len(path) - 1, location))
        if not reachable:
            raise ActionArbitrationRuntimeError(
                f"aucun lieu atteignable pour {activity_type}", code="no_reachable_activity_location"
            )
        _edges, target = min(reachable)
        return normalize_action_specification(
            ACTION_START_ACTIVITY,
            {"activity_type": activity_type, "target_location_key": target},
        )

    def current_action_key(self, world_id: int, actor_key: str) -> str | None:
        active = ActivityEngine(self._conn, clock=self._clock).activity_sheet(world_id, actor_key)
        if active is None:
            return None
        return normalize_action_specification(
            ACTION_START_ACTIVITY,
            {"activity_type": active["type"], "target_location_key": active["location_key"]},
        ).action_key

    def build_owner_backed(
        self,
        world_id: int,
        actor_key: str,
        *,
        canonical_at: str,
        sleep_specification: ActionSpecification | None = None,
        rest_specification: ActionSpecification | None = None,
        current_action_key: str | None = None,
    ) -> ActionArbitrationFrame:
        """Construit une frame runtime sans accepter de cause physiologique libre."""
        at = to_iso(parse_iso(canonical_at))
        sleep_specification = sleep_specification or self._nearest_activity_specification(
            world_id, actor_key, "sleep"
        )
        rest_specification = rest_specification or self._nearest_activity_specification(
            world_id, actor_key, "rest"
        )
        source = self._physiology.resolve_light_source_owner_backed(
            world_id, actor_key, at_time=at
        )
        return self._build_from_source(
            world_id,
            actor_key,
            canonical_at=source.canonical_at,
            sleep_specification=sleep_specification,
            rest_specification=rest_specification,
            wake_source=source.source,
            current_action_key=current_action_key,
        )

    def next_reassessment_at(self, world_id: int, actor_key: str) -> str:
        """Prochaine frontiere periodique depuis le dernier arbitrage causal effectif."""
        actor = _text(actor_key, field="acteur")
        state = self._physiology.read_state(world_id, actor)
        row = self._conn.execute(
            "SELECT canonical_at FROM action_arbitration_audit "
            "WHERE world_id=? AND reason_code='active_causal_arbitration' "
            "AND json_extract(result_json,'$.actor_key')=? "
            "ORDER BY canonical_at DESC,id DESC LIMIT 1",
            (world_id, actor),
        ).fetchone()
        base = parse_iso(state.anchor_at)
        if row is not None:
            base = max(base, parse_iso(row["canonical_at"]))
        return to_iso(base + __import__("datetime").timedelta(seconds=self._policy(world_id).reassessment_seconds))

    def audit_decision(
        self, frame: ActionArbitrationFrame, decision: ActionArbitrationDecision, *,
        validation: ValidationResult | None = None,
        reason_code: str = "active_causal_arbitration",
    ) -> int:
        """Persiste une trace operateur privee; elle ne devient jamais un fait canonique."""
        if decision.frame_digest != frame.digest:
            raise ActionArbitrationRuntimeError(
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
            "actor_key": frame.actor_key,
            "outcome": decision.outcome,
            "winner_action_key": None if decision.winner is None else decision.winner.specification.action_key,
            "reason_code": decision.reason_code,
            "validation_status": None if validation is None else validation.status,
            "validation_reason_code": None if validation is None else validation.reason_code,
        }
        return self._foundation.record_private_audit(
            frame.world_id, frame_digest=frame.digest, options=options, sources=sources,
            result=result, canonical_at=frame.canonical_at, reason_code=reason_code,
        )


def action_specification(action_kind: Any, params: Any) -> ActionSpecification:
    """Raccourci de banc vers le vocabulaire executable unique."""
    return normalize_action_specification(action_kind, params)
