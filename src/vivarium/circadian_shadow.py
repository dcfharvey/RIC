"""Contrats de compatibilité/shadow pour le cycle veille-sommeil V1.

Ce module est volontairement hors du chemin runtime. Il fournit seulement :

* un manifeste vérifiable des consommateurs legacy de ``repos``/``energie`` ;
* une projection de motif de sommeil et un arbitrage pur sur des copies de
  banc ;
* une conséquence de stabilité appliquée par un double de moteur, jamais par
  la physiologie.

Les entrées sont des valeurs de banc explicites. Aucune API ne lit SQLite,
ne convertit ``repos`` en H, ne convertit ``energie`` en P, ni ne fabrique un
fait canonique. Les paramètres restent des choix d'ingénierie de calibration,
pas des affirmations biologiques.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

from .circadian_model import (
    CircadianParameters,
    Propensity,
    RegulationState,
    WakeStability,
    sleep_propensity,
)


class CircadianShadowError(ValueError):
    """Entrée de banc ou contrat de compatibilité invalide."""


@dataclass(frozen=True)
class LegacyConsumer:
    """Un usage legacy recensé, avec son propriétaire et son rôle de cutover."""

    key: str
    owner: str
    path: str
    symbols: tuple[str, ...]
    role: Literal["behavior", "physical_cost", "projection", "bootstrap", "audit", "guard"]
    cutover_group: str


@dataclass(frozen=True)
class CutoverSwitchGroup:
    """Commutateur qui doit rester atomique au futur cutover."""

    key: str
    switches: tuple[str, ...]
    rationale: str


LEGACY_CONSUMERS: tuple[LegacyConsumer, ...] = (
    LegacyConsumer(
        "decision_policy", "DecisionPolicy", "src/vivarium/policy.py",
        ("repos", "energie", "CRIT_REPOS", "CRIT_ENERGIE"), "behavior", "behavioral_cutover",
    ),
    LegacyConsumer(
        "simulation_context", "SimulationEngine", "src/vivarium/simulation.py",
        ("NEED_KEYS", "repos", "energie"), "behavior", "behavioral_cutover",
    ),
    LegacyConsumer(
        "activity_engine", "ActivityEngine", "src/vivarium/activities.py",
        ("repos_rate", "energie_rate", "SLEEP_REPOS_TARGET", "SLEEP_ENERGIE_TARGET"),
        "behavior", "behavioral_cutover",
    ),
    LegacyConsumer(
        "motivation_projection", "MotivationService", "src/vivarium/motivation.py",
        ("_NEED_ORDER", "repos", "energie", "_NEED_ACTIONS"), "behavior", "behavioral_cutover",
    ),
    LegacyConsumer(
        "attention_projection", "AttentionService", "src/vivarium/attention.py",
        ("repos_threshold_mult_milli", "energie_threshold_mult_milli"), "projection", "behavioral_cutover",
    ),
    LegacyConsumer(
        "decision_frame", "DecisionFrameService", "src/vivarium/decision.py",
        ("MotivationService", "SimulationEngine"), "behavior", "behavioral_cutover",
    ),
    LegacyConsumer(
        "injury_movement_cost", "CharacterEngine", "src/vivarium/character.py",
        ("MOVEMENT_SURCHARGE_MILLI", "energie"), "physical_cost", "physical_capacity_cutover",
    ),
    LegacyConsumer(
        "admin_read_model", "AdminReadService", "src/vivarium/admin.py",
        ("energie", "energy"), "projection", "observability_cutover",
    ),
    LegacyConsumer(
        "world_defaults", "WorldEngine", "src/vivarium/world.py",
        ("repos_threshold_mult_milli", "energie_threshold_mult_milli", "repos_rate", "energie_rate"),
        "bootstrap", "legacy_preservation",
    ),
    LegacyConsumer(
        "world_rules", "WorldRulesService", "src/vivarium/world_rules.py",
        ("repos_rate", "energie_rate"), "bootstrap", "legacy_preservation",
    ),
    LegacyConsumer(
        "instance_defaults", "InstanceService", "src/vivarium/instances.py",
        ("repos_threshold_mult_milli", "energie_threshold_mult_milli"), "bootstrap", "legacy_preservation",
    ),
    LegacyConsumer(
        "seed_data", "Seed", "src/vivarium/seed.py",
        ("repos", "energie", "repos_rate", "energie_rate"), "bootstrap", "legacy_preservation",
    ),
    LegacyConsumer(
        "reproducibility_audit", "Reproducibility", "src/vivarium/repro.py",
        ("repos_rate", "energie_rate", "repos_threshold_mult_milli", "energie_threshold_mult_milli"),
        "audit", "legacy_preservation",
    ),
    LegacyConsumer(
        "circadian_boundary_guard", "circadian_model", "src/vivarium/circadian_model.py",
        ("repos", "energie"), "guard", "legacy_preservation",
    ),
    LegacyConsumer(
        "shadow_boundary_guard", "circadian_shadow", "src/vivarium/circadian_shadow.py",
        ("LEGACY_CONSUMERS", "repos", "energie"), "guard", "legacy_preservation",
    ),
)


CUTOVER_SWITCH_GROUPS: tuple[CutoverSwitchGroup, ...] = (
    CutoverSwitchGroup(
        "behavioral_cutover",
        (
            "DecisionPolicy", "SimulationEngine", "ActivityEngine",
            "MotivationService", "AttentionService", "DecisionFrameService",
        ),
        "motif sommeil, arbitrage, terminaison de sommeil et réévaluation doivent changer ensemble",
    ),
    CutoverSwitchGroup(
        "physical_capacity_cutover",
        ("CharacterEngine", "ActivityEngine"),
        "les coûts physiques passent ensemble à P ; aucune conversion depuis energie",
    ),
    CutoverSwitchGroup(
        "observability_cutover",
        ("AdminReadService",),
        "les vues peuvent exposer P, mais conservent les valeurs legacy comme historique",
    ),
    CutoverSwitchGroup(
        "legacy_preservation",
        ("WorldEngine", "WorldRulesService", "InstanceService", "Seed", "Reproducibility"),
        "bootstrap et audits gardent la compatibilité et la provenance sans piloter la physiologie",
    ),
)


@dataclass(frozen=True)
class LegacyAuditReport:
    consumers: tuple[LegacyConsumer, ...]
    cutover_groups: tuple[CutoverSwitchGroup, ...]
    missing_paths: tuple[str, ...]
    missing_symbols: tuple[str, ...]
    unlisted_hits: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return not (self.missing_paths or self.missing_symbols or self.unlisted_hits)


def audit_legacy_consumers(root: str | Path | None = None) -> LegacyAuditReport:
    """Vérifie que le manifeste couvre tous les fichiers Python touchant les deux besoins.

    Les commentaires de garde sont recensés eux aussi : ils constituent une
    frontière négative importante du raccord. Les tests et la documentation
    sont exclus car ils ne sont pas des consommateurs runtime.
    """

    repo = Path(root) if root is not None else Path(__file__).resolve().parents[2]
    manifest_paths = {entry.path for entry in LEGACY_CONSUMERS}
    missing_paths: list[str] = []
    missing_symbols: list[str] = []
    for entry in LEGACY_CONSUMERS:
        path = repo / entry.path
        if not path.is_file():
            missing_paths.append(entry.path)
            continue
        text = path.read_text(encoding="utf-8")
        for symbol in entry.symbols:
            if symbol not in text:
                missing_symbols.append(f"{entry.path}:{symbol}")

    unlisted_hits: list[str] = []
    source_root = repo / "src" / "vivarium"
    if source_root.is_dir():
        for path in sorted(source_root.rglob("*.py")):
            relative = path.relative_to(repo).as_posix()
            text = path.read_text(encoding="utf-8")
            if re.search(r"\b(?:repos|energie)\b", text) and relative not in manifest_paths:
                unlisted_hits.append(relative)
    return LegacyAuditReport(
        LEGACY_CONSUMERS, CUTOVER_SWITCH_GROUPS,
        tuple(sorted(set(missing_paths))), tuple(sorted(set(missing_symbols))),
        tuple(sorted(set(unlisted_hits))),
    )


def _score(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
        raise CircadianShadowError(f"{field} doit être entre 0 et 1")
    return float(value)


@dataclass(frozen=True)
class SleepMotiveProjection:
    """Offre volontaire et explicable ; ce n'est ni un ordre ni une jauge."""

    candidate_key: str
    action: str
    score: float
    reason: str

    def __post_init__(self) -> None:
        if not self.candidate_key or not self.action or not self.reason:
            raise CircadianShadowError("motif de sommeil incomplet")
        _score(self.score, field="score")

    @classmethod
    def from_propensity(
        cls, propensity: Propensity, *, offer_threshold: float = 0.5,
    ) -> "SleepMotiveProjection | None":
        """Construit le candidat depuis la propension additive, jamais depuis P."""
        threshold = _score(offer_threshold, field="offer_threshold")
        if propensity.family != "additive":
            raise CircadianShadowError("le shadow exige la propension additive V1")
        if propensity.sleep_propensity < threshold:
            return None
        return cls(
            candidate_key="sleep_regulation",
            action="sleep",
            score=propensity.sleep_propensity,
            reason="sleep_propensity_additive",
        )

    def as_option(self) -> "ArbitrationOption":
        return ArbitrationOption(self.candidate_key, "sleep_motive", self.action, self.score)


def sleep_motive_projection(
    state: RegulationState,
    parameters: CircadianParameters,
    *,
    offer_threshold: float = 0.5,
) -> SleepMotiveProjection | None:
    """Projection pratique H/φ → motif ; la capacité P n'est jamais consultée."""

    return SleepMotiveProjection.from_propensity(
        sleep_propensity(state, parameters, family="additive"),
        offer_threshold=offer_threshold,
    )


@dataclass(frozen=True)
class ArbitrationOption:
    option_key: str
    source_kind: Literal["intention", "sleep_motive", "alternative"]
    action: str
    score: float

    def __post_init__(self) -> None:
        if not self.option_key or not self.action:
            raise CircadianShadowError("option d'arbitrage incomplète")
        _score(self.score, field="score")


@dataclass(frozen=True)
class VoluntaryArbitrationFrame:
    active_intention: ArbitrationOption | None = None
    sleep_motive: SleepMotiveProjection | None = None
    alternatives: tuple[ArbitrationOption, ...] = ()

    def __post_init__(self) -> None:
        if self.active_intention is not None and self.active_intention.source_kind != "intention":
            raise CircadianShadowError("active_intention doit être une option d'intention")
        if any(option.source_kind != "alternative" for option in self.alternatives):
            raise CircadianShadowError("alternatives d'arbitrage invalides")


@dataclass(frozen=True)
class ArbitrationResult:
    winner_kind: Literal["intention", "sleep_motive", "alternative", "none"]
    winner_key: str | None
    action: str | None
    reason: str
    considered: tuple[str, ...]


def arbitrate_voluntary(frame: VoluntaryArbitrationFrame) -> ArbitrationResult:
    """Compare des options explicites sans priorité implicite de catégorie.

    Une égalité reste une situation à réévaluer ; elle n'est pas départagée par
    l'ordre legacy ``active_intention > motives[0]``.
    """

    options = [option for option in (frame.active_intention,) if option is not None]
    if frame.sleep_motive is not None:
        options.append(frame.sleep_motive.as_option())
    options.extend(frame.alternatives)
    if not options:
        return ArbitrationResult("none", None, None, "no_viable_option", ())
    if len({option.option_key for option in options}) != len(options):
        raise CircadianShadowError("les clés d'options doivent être uniques")
    top_score = max(option.score for option in options)
    leaders = [option for option in options if option.score == top_score]
    considered = tuple(sorted(option.option_key for option in options))
    if len(leaders) != 1:
        return ArbitrationResult("none", None, None, "tie_requires_reassessment", considered)
    winner = leaders[0]
    return ArbitrationResult(winner.source_kind, winner.option_key, winner.action, "highest_explicit_score", considered)


@dataclass(frozen=True)
class WakeStabilityEligibility:
    """Cause/eligibility produite par la physiologie, sans mutation moteur."""

    eligible: bool
    activity_id: str | None
    cause: str | None
    band: Literal["stable", "fragile", "critical"]


def wake_stability_eligibility(
    stability: WakeStability,
    *, activity_id: str | None,
    requires_sustained_wakefulness: bool,
) -> WakeStabilityEligibility:
    """Expose une conséquence potentielle ; le moteur reste le validateur."""

    valid_id = isinstance(activity_id, str) and bool(activity_id)
    eligible = stability.band == "critical" and requires_sustained_wakefulness and valid_id
    return WakeStabilityEligibility(
        eligible, activity_id if valid_id else None,
        "wake_stability_critical" if eligible else None, stability.band,
    )


@dataclass(frozen=True)
class MotorConsequence:
    applied: bool
    duplicate: bool
    activity_id: str | None
    status: Literal["active", "aborted", "missing"]
    cause: str | None


class SyntheticActivityEngine:
    """Double de propriétaire moteur pour vérifier bornage et idempotence."""

    def __init__(self, activities: Mapping[str, str] | None = None) -> None:
        self._statuses = dict(activities or {})
        if any(status not in {"active", "aborted"} for status in self._statuses.values()):
            raise CircadianShadowError("statut d'activité synthétique invalide")
        self._events: list[tuple[str, str, str]] = []

    def register_active(self, activity_id: str) -> None:
        if not isinstance(activity_id, str) or not activity_id:
            raise CircadianShadowError("activité synthétique invalide")
        self._statuses.setdefault(activity_id, "active")

    def apply_stability_eligibility(self, eligibility: WakeStabilityEligibility) -> MotorConsequence:
        activity_id = eligibility.activity_id
        if not eligibility.eligible or activity_id is None:
            return MotorConsequence(False, False, activity_id, "missing", eligibility.cause)
        status = self._statuses.get(activity_id)
        if status is None:
            return MotorConsequence(False, False, activity_id, "missing", eligibility.cause)
        if status == "aborted":
            return MotorConsequence(False, True, activity_id, "aborted", eligibility.cause)
        self._statuses[activity_id] = "aborted"
        self._events.append((activity_id, "aborted", eligibility.cause or "unknown"))
        return MotorConsequence(True, False, activity_id, "aborted", eligibility.cause)

    @property
    def events(self) -> tuple[tuple[str, str, str], ...]:
        return tuple(self._events)

    def snapshot(self) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(self._statuses.items()))

    @classmethod
    def from_snapshot(cls, snapshot: tuple[tuple[str, str], ...]) -> "SyntheticActivityEngine":
        return cls(dict(snapshot))
