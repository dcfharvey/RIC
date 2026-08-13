"""Noyau quantitatif *inactif* du domaine veille-sommeil.

Ce module est volontairement pur : il ne connait ni SQLite, ni le runtime, ni
les besoins alpha. Il sert aux bancs de calibration et aux tests de
falsification qui précèdent un futur cutover. L'appeler ne peut donc ni créer
un événement canonique, ni modifier ``repos``/``energie``.

Les paramètres fournis ici sont des candidats de calibration versionnés. Ils
ne sont pas des constantes biologiques ni des profils activés dans une
résidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, exp, pi, sin
from typing import Literal


SECONDS_PER_HOUR = 3_600
MILLI = 100_000
PHASE_TURNS = 1_000_000
# Résolution numérique, non biologique. Elle rend l'intégration indépendante
# de la cadence des pulses runtime quand les causes restent constantes.
MAX_CIRCADIAN_QUANTUM_SECONDS = 60


class CircadianModelError(ValueError):
    """Paramètre ou état de calibration invalide."""


def _unit(value: float, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
        raise CircadianModelError(f"{field} doit être entre 0 et 1")
    return float(value)


def _milli(value: int, *, field: str, upper: int = MILLI) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= upper:
        raise CircadianModelError(f"{field} invalide")
    return value


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _smoothstep(low: float, high: float, value: float) -> float:
    if high <= low:
        raise CircadianModelError("bande de propension invalide")
    x = _clamp((value - low) / (high - low))
    return x * x * (3.0 - 2.0 * x)


@dataclass(frozen=True)
class CircadianParameters:
    """Paramètres d'un candidat de calibration, jamais d'un profil actif."""

    profile_key: str
    version: int
    evidence_class: Literal["human_reference", "generic_feline", "fictional_canon"]
    tau_wake_seconds: int
    tau_sleep_seconds: int
    intrinsic_period_seconds: int
    light_half_saturation_milli: int
    light_phase_shift_milli_per_hour: int
    light_sensitivity_milli: int
    sleep_occlusion_milli: int
    circadian_propensity_weight: float
    propensity_offer_low: float
    propensity_offer_high: float
    circadian_sensitivity_modulation: float
    homeostatic_stability_weight: float
    circadian_stability_weight: float
    max_stimulation_relief: float
    fragile_enter: float
    fragile_exit: float
    critical_enter: float
    critical_exit: float
    active_capacity_cost_per_hour: float
    rest_capacity_recovery_per_hour: float
    sleep_capacity_recovery_per_hour: float

    def __post_init__(self) -> None:
        if not self.profile_key or not isinstance(self.version, int) or self.version < 1:
            raise CircadianModelError("identité de profil invalide")
        if self.evidence_class not in {"human_reference", "generic_feline", "fictional_canon"}:
            raise CircadianModelError("classe de preuve invalide")
        for value, field in (
            (self.tau_wake_seconds, "tau_wake_seconds"),
            (self.tau_sleep_seconds, "tau_sleep_seconds"),
            (self.intrinsic_period_seconds, "intrinsic_period_seconds"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise CircadianModelError(f"{field} invalide")
        _milli(self.light_half_saturation_milli, field="light_half_saturation_milli")
        if self.light_half_saturation_milli == 0:
            raise CircadianModelError("light_half_saturation_milli doit être positif")
        _milli(self.light_phase_shift_milli_per_hour, field="light_phase_shift_milli_per_hour")
        _milli(self.light_sensitivity_milli, field="light_sensitivity_milli")
        _milli(self.sleep_occlusion_milli, field="sleep_occlusion_milli")
        for value, field in (
            (self.circadian_propensity_weight, "circadian_propensity_weight"),
            (self.propensity_offer_low, "propensity_offer_low"),
            (self.propensity_offer_high, "propensity_offer_high"),
            (self.circadian_sensitivity_modulation, "circadian_sensitivity_modulation"),
            (self.homeostatic_stability_weight, "homeostatic_stability_weight"),
            (self.circadian_stability_weight, "circadian_stability_weight"),
            (self.max_stimulation_relief, "max_stimulation_relief"),
            (self.fragile_enter, "fragile_enter"),
            (self.fragile_exit, "fragile_exit"),
            (self.critical_enter, "critical_enter"),
            (self.critical_exit, "critical_exit"),
            (self.active_capacity_cost_per_hour, "active_capacity_cost_per_hour"),
            (self.rest_capacity_recovery_per_hour, "rest_capacity_recovery_per_hour"),
            (self.sleep_capacity_recovery_per_hour, "sleep_capacity_recovery_per_hour"),
        ):
            _unit(value, field=field)
        if not self.propensity_offer_low < self.propensity_offer_high:
            raise CircadianModelError("bande de propension inversée")
        if not self.fragile_exit <= self.fragile_enter < self.critical_enter:
            raise CircadianModelError("bandes de stabilité fragiles invalides")
        if not self.fragile_exit < self.critical_exit <= self.critical_enter:
            raise CircadianModelError("bandes de stabilité critiques invalides")
        # Une stimulation ne doit jamais pouvoir annuler toute instabilité.
        if self.max_stimulation_relief >= 1.0:
            raise CircadianModelError("le soulagement de stimulation doit rester borné")


@dataclass(frozen=True)
class RegulationState:
    """État interne normalisé du banc ; sa persistance future reste inactive."""

    homeostatic_load: float
    circadian_phase: float
    physical_capacity: float

    def __post_init__(self) -> None:
        _unit(self.homeostatic_load, field="homeostatic_load")
        _unit(self.physical_capacity, field="physical_capacity")
        if isinstance(self.circadian_phase, bool) or not isinstance(self.circadian_phase, (int, float)):
            raise CircadianModelError("circadian_phase invalide")

    @property
    def homeostatic_load_milli(self) -> int:
        return round(self.homeostatic_load * MILLI)

    @property
    def circadian_phase_milli(self) -> int:
        return round((self.circadian_phase % 1.0) * (PHASE_TURNS - 1))

    @property
    def physical_capacity_milli(self) -> int:
        return round(self.physical_capacity * MILLI)


@dataclass(frozen=True)
class RegulationInput:
    """Causes objectives du segment : ni cognition ni décision."""

    state: Literal["wake", "rest", "sleep"]
    environmental_light_milli: int
    location_exposure_milli: int
    occluded: bool = False
    stimulation: float = 0.0

    def __post_init__(self) -> None:
        if self.state not in {"wake", "rest", "sleep"}:
            raise CircadianModelError("état veille-sommeil invalide")
        _milli(self.environmental_light_milli, field="environmental_light_milli")
        _milli(self.location_exposure_milli, field="location_exposure_milli")
        if not isinstance(self.occluded, bool):
            raise CircadianModelError("occluded doit être booléen")
        _unit(self.stimulation, field="stimulation")


@dataclass(frozen=True)
class Propensity:
    """Projection dérivée ; elle n'est jamais persistée comme une jauge."""

    homeostatic_component: float
    circadian_wake_support: float
    sleep_propensity: float
    family: Literal["additive", "sensitivity_modulated"]


@dataclass(frozen=True)
class WakeStability:
    """Projection physiologique/contextuelle, distincte de la décision."""

    base_instability: float
    instability: float
    band: Literal["stable", "fragile", "critical"]


@dataclass(frozen=True)
class StabilityGateState:
    """Double de banc pour l'idempotence de conséquence moteur.

    Il n'est pas un état physiologique de production : l'activité canonique et
    sa transition vers ``aborted`` appartiendront au moteur. L'hystérésis
    physiologique éventuelle est représentée séparément par ``previous_band``.
    """

    interrupted_activity_id: str | None = None


@dataclass(frozen=True)
class StabilityConsequence:
    should_interrupt: bool
    reason: str | None
    next_gate_state: StabilityGateState


def circadian_wake_support(phase: float) -> float:
    """Oscillation lisse V1 ; ce n'est pas une PRC humaine littérale."""
    return (cos(2.0 * pi * (phase % 1.0)) + 1.0) / 2.0


def effective_light_drive(source: RegulationInput, parameters: CircadianParameters) -> float:
    """Drive RIC effectif, sans prétendre représenter directement des lux."""
    exposure = (source.environmental_light_milli / MILLI) * (source.location_exposure_milli / MILLI)
    if source.occluded or source.state == "sleep":
        exposure *= parameters.sleep_occlusion_milli / MILLI
    exposure *= parameters.light_sensitivity_milli / MILLI
    return _clamp(exposure)


def _light_saturation(drive: float, parameters: CircadianParameters) -> float:
    half = parameters.light_half_saturation_milli / MILLI
    return drive / (drive + half) if drive else 0.0


def advance_regulation(
    state: RegulationState,
    source: RegulationInput,
    duration_seconds: int | float,
    parameters: CircadianParameters,
) -> RegulationState:
    """Intègre un segment objectif sans effet de bord.

    L'homéostasie utilise sa solution exponentielle fermée. La phase utilise
    des quanta fixes d'ingénierie, afin que sa progression ne suive jamais la
    cadence du runtime.
    """
    if isinstance(duration_seconds, bool) or not isinstance(duration_seconds, (int, float)) or duration_seconds < 0:
        raise CircadianModelError("duration_seconds invalide")
    if duration_seconds == 0:
        return state
    duration_hours = duration_seconds / SECONDS_PER_HOUR
    if source.state == "sleep":
        homeostatic = state.homeostatic_load * exp(-duration_seconds / parameters.tau_sleep_seconds)
        capacity = state.physical_capacity + parameters.sleep_capacity_recovery_per_hour * duration_hours
    else:
        homeostatic = 1.0 - (1.0 - state.homeostatic_load) * exp(-duration_seconds / parameters.tau_wake_seconds)
        if source.state == "rest":
            capacity = state.physical_capacity + parameters.rest_capacity_recovery_per_hour * duration_hours
        else:
            capacity = state.physical_capacity - parameters.active_capacity_cost_per_hour * duration_hours

    drive = effective_light_drive(source, parameters)
    saturated = _light_saturation(drive, parameters)
    phase = state.circadian_phase % 1.0
    remaining = duration_seconds
    while remaining > 0:
        quantum = min(remaining, MAX_CIRCADIAN_QUANTUM_SECONDS)
        hours = quantum / SECONDS_PER_HOUR
        midpoint = (phase + quantum / parameters.intrinsic_period_seconds / 2.0) % 1.0
        # Sinusoïde signée : la direction du forcing dépend de la phase et
        # l'amplitude est bornée par le profil de calibration.
        forcing = (
            parameters.light_phase_shift_milli_per_hour / PHASE_TURNS
            * saturated
            * sin(2.0 * pi * midpoint)
        )
        phase = (phase + quantum / parameters.intrinsic_period_seconds + forcing * hours) % 1.0
        remaining -= quantum
    return RegulationState(_clamp(homeostatic), phase, _clamp(capacity))


def sleep_propensity(
    state: RegulationState,
    parameters: CircadianParameters,
    *,
    family: Literal["additive", "sensitivity_modulated"] = "additive",
) -> Propensity:
    """Calcule deux familles concurrentes ; aucune ne pilote le runtime."""
    support = circadian_wake_support(state.circadian_phase)
    circadian_sleep_influence = 1.0 - support
    if family == "additive":
        combined = _clamp(
            state.homeostatic_load + parameters.circadian_propensity_weight * circadian_sleep_influence
        )
        score = _smoothstep(parameters.propensity_offer_low, parameters.propensity_offer_high, combined)
    elif family == "sensitivity_modulated":
        # Alternative réellement différente : C modifie la sensibilité de la
        # réponse à H, et non les deux bornes de la même smoothstep. À H=0 ou
        # H=1, C n'invente ni n'annule de charge ; entre les deux, il change la
        # pente. Cette forme comporte un terme H×C non réductible à H + kC.
        homeostatic_score = _smoothstep(
            parameters.propensity_offer_low,
            parameters.propensity_offer_high,
            state.homeostatic_load,
        )
        exponent = 1.0 + parameters.circadian_sensitivity_modulation * (support - 0.5)
        score = homeostatic_score ** exponent
    else:
        raise CircadianModelError("famille de propension inconnue")
    return Propensity(state.homeostatic_load, support, score, family)


def wake_stability(
    state: RegulationState,
    source: RegulationInput,
    parameters: CircadianParameters,
    *,
    previous_band: Literal["stable", "fragile", "critical"] = "stable",
) -> WakeStability:
    """Dérive une stabilité à bandes avec hystérésis, sans forcer le sommeil."""
    if previous_band not in {"stable", "fragile", "critical"}:
        raise CircadianModelError("bande précédente invalide")
    base = _clamp(
        parameters.homeostatic_stability_weight * state.homeostatic_load
        + parameters.circadian_stability_weight * (1.0 - circadian_wake_support(state.circadian_phase))
    )
    # La stimulation ne peut enlever qu'une fraction plafonnée de la
    # manifestation actuelle : même maximale, elle ne garantit jamais 0.
    reduced = base * (1.0 - parameters.max_stimulation_relief * source.stimulation)
    # Le seuil de conséquence est défini par la physiologie brute : au-delà de
    # cette bande, la stimulation peut réduire la manifestation continue, mais
    # ne peut plus faire sortir de ``critical``. Elle ne peut donc pas garantir
    # une veille viable indéfinie sous H/C extrêmes.
    instability = max(reduced, parameters.critical_enter if base >= parameters.critical_enter else 0.0)
    if previous_band == "critical":
        band: Literal["stable", "fragile", "critical"] = (
            "critical" if instability >= parameters.critical_exit
            else "fragile" if instability >= parameters.fragile_exit else "stable"
        )
    elif previous_band == "fragile":
        band = "critical" if instability >= parameters.critical_enter else (
            "fragile" if instability >= parameters.fragile_exit else "stable"
        )
    else:
        band = "critical" if instability >= parameters.critical_enter else (
            "fragile" if instability >= parameters.fragile_enter else "stable"
        )
    return WakeStability(base, instability, band)


def stability_consequence(
    stability: WakeStability,
    *,
    activity_id: str | None,
    requires_sustained_wakefulness: bool,
    gate_state: StabilityGateState,
) -> StabilityConsequence:
    """Exerce un contrat de banc ; le moteur futur restera validateur."""
    eligible = (
        stability.band == "critical"
        and requires_sustained_wakefulness
        and isinstance(activity_id, str)
        and bool(activity_id)
        and gate_state.interrupted_activity_id != activity_id
    )
    if eligible:
        return StabilityConsequence(True, "wake_stability_critical", StabilityGateState(activity_id))
    return StabilityConsequence(False, None, gate_state)


def calibration_profiles() -> dict[str, CircadianParameters]:
    """Candidats explicitement exploratoires pour les bancs, non activables."""
    common = dict(
        version=1,
        light_half_saturation_milli=30_000,
        # Ancre de calibration RIC : 1 200 ne produisait pas de phase-locking
        # pour le zeitgeber V1 décalé. Cette amplitude est retenue parce que
        # les deux protocoles de lock convergent, pas comme valeur biologique.
        light_phase_shift_milli_per_hour=5_000,
        light_sensitivity_milli=100_000,
        sleep_occlusion_milli=5_000,
        circadian_propensity_weight=0.24,
        propensity_offer_low=0.42,
        propensity_offer_high=0.74,
        circadian_sensitivity_modulation=0.20,
        homeostatic_stability_weight=0.78,
        circadian_stability_weight=0.34,
        max_stimulation_relief=0.55,
        fragile_enter=0.48,
        fragile_exit=0.40,
        critical_enter=0.78,
        critical_exit=0.66,
        active_capacity_cost_per_hour=0.025,
        rest_capacity_recovery_per_hour=0.045,
        sleep_capacity_recovery_per_hour=0.070,
    )
    return {
        "human_reference_candidate.v1": CircadianParameters(
            profile_key="human_reference_candidate.v1",
            evidence_class="human_reference",
            # Candidats RIC : ni la littérature ni ce code ne les présentent
            # comme des constantes humaines mesurées.
            tau_wake_seconds=18 * SECONDS_PER_HOUR,
            tau_sleep_seconds=3 * SECONDS_PER_HOUR,
            intrinsic_period_seconds=24 * SECONDS_PER_HOUR + 10 * 60,
            **common,
        ),
        "generic_feline_hypothesis.v1": CircadianParameters(
            profile_key="generic_feline_hypothesis.v1",
            evidence_class="generic_feline",
            # Hypothèse de calibration C, non une physiologie féline établie.
            tau_wake_seconds=10 * SECONDS_PER_HOUR,
            tau_sleep_seconds=2 * SECONDS_PER_HOUR,
            intrinsic_period_seconds=24 * SECONDS_PER_HOUR + 10 * 60,
            **common,
        ),
    }
