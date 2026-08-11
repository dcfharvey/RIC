"""Banc déterministe, jetable et sans runtime pour le modèle circadien V1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from .circadian_model import (
    CircadianParameters,
    RegulationInput,
    RegulationState,
    StabilityGateState,
    advance_regulation,
    calibration_profiles,
    effective_light_drive,
    sleep_propensity,
    stability_consequence,
    wake_stability,
)


@dataclass(frozen=True)
class CalibrationObservation:
    name: str
    value: float | int | bool


@dataclass(frozen=True)
class CalibrationReport:
    profile_key: str
    profile_version: int
    observations: tuple[CalibrationObservation, ...]

    @property
    def passed(self) -> bool:
        return all(bool(item.value) for item in self.observations if isinstance(item.value, bool))

    def as_dict(self) -> dict:
        return {
            "profile_key": self.profile_key,
            "profile_version": self.profile_version,
            "passed": self.passed,
            "observations": [asdict(item) for item in self.observations],
        }


def _source(state: Literal["wake", "rest", "sleep"], light: int, *, occluded: bool = False,
            stimulation: float = 0.0) -> RegulationInput:
    return RegulationInput(state, light, 100_000, occluded, stimulation)


def _phase_delta(left: float, right: float) -> float:
    """Écart circulaire signé en tours, utile aux scénarios sans heure civile."""
    return ((left - right + 0.5) % 1.0) - 0.5


def _daily_light_cycle(state: RegulationState, parameters: CircadianParameters) -> RegulationState:
    """Une journée synthétique : 12 h exposées, 4 h éveillées sombres, 8 h sommeil."""
    state = advance_regulation(state, _source("wake", 100_000), 12 * 3_600, parameters)
    state = advance_regulation(state, _source("wake", 0), 4 * 3_600, parameters)
    return advance_regulation(state, _source("sleep", 0, occluded=True), 8 * 3_600, parameters)


def _restriction_protocol(
    state: RegulationState, parameters: CircadianParameters, *, sleep_hours: int, days: int
) -> RegulationState:
    for _ in range(days):
        state = advance_regulation(state, _source("wake", 100_000), (24 - sleep_hours) * 3_600, parameters)
        state = advance_regulation(state, _source("sleep", 0, occluded=True), sleep_hours * 3_600, parameters)
    return state


def _opportunity_episodes(parameters: CircadianParameters) -> int:
    """Sandbox d'occasions neutres ; ce n'est pas le futur arbitre production.

    À chaque frontière horaire, une opportunité de sommeil existe. Le compteur
    vérifie seulement qu'un profil générique peut produire plus d'un épisode
    sans branche identitaire ni oscillateur ultradien.
    """
    state = RegulationState(0.54, 0.50, 0.80)
    episodes = 0
    for _ in range(24):
        if sleep_propensity(state, parameters).sleep_propensity >= 0.65:
            state = advance_regulation(state, _source("sleep", 0, occluded=True), 90 * 60, parameters)
            episodes += 1
        else:
            state = advance_regulation(state, _source("wake", 0), 60 * 60, parameters)
    return episodes


def run_reference_calibration(profile_key: str = "human_reference_candidate.v1") -> CalibrationReport:
    """Exécute les falsifications minimales sans monde ni base persistante.

    Ce banc ne prétend pas simuler les choix sociaux. Il mesure les propriétés
    de la couche physiologique avant son raccord futur à l'arbitre moteur.
    """
    parameters = calibration_profiles()[profile_key]
    initial = RegulationState(0.35, 0.15, 0.60)
    dark_wake = _source("wake", 0)
    light_wake = _source("wake", 100_000)

    # Invariance de découpage : mêmes causes, même horizon, sans dépendance
    # à la cadence du runtime.
    one_piece = advance_regulation(initial, dark_wake, 6 * 3_600, parameters)
    split = advance_regulation(
        advance_regulation(initial, dark_wake, 2 * 3_600, parameters), dark_wake, 4 * 3_600, parameters
    )
    partition_invariant = (
        abs(one_piece.homeostatic_load - split.homeostatic_load) < 1e-12
        and abs(one_piece.circadian_phase - split.circadian_phase) < 1e-12
        and abs(one_piece.physical_capacity - split.physical_capacity) < 1e-12
    )

    # Sans zeitgeber, le profil non exactement 24 h dérive progressivement.
    free_run = advance_regulation(initial, dark_wake, 5 * 86_400, parameters)
    nominal_phase = (initial.circadian_phase + 5 * 86_400 / 86_400) % 1.0
    free_running = abs(free_run.circadian_phase - nominal_phase) > 0.001

    # Même lumière, deux phases : forcing de signe différent.
    early_start = RegulationState(0.4, 0.125, 0.7)
    late_start = RegulationState(0.4, 0.625, 0.7)
    early = advance_regulation(early_start, light_wake, 2 * 3_600, parameters)
    late = advance_regulation(late_start, light_wake, 2 * 3_600, parameters)
    early_dark = advance_regulation(early_start, dark_wake, 2 * 3_600, parameters)
    late_dark = advance_regulation(late_start, dark_wake, 2 * 3_600, parameters)
    # Le free-run avance toujours : ce qui doit changer de signe est le delta
    # apporté par la lumière relativement à ce même free-run.
    phase_dependent_light = (
        (early.circadian_phase - early_dark.circadian_phase)
        * (late.circadian_phase - late_dark.circadian_phase)
        < 0
    )

    awake_drive = effective_light_drive(light_wake, parameters)
    sleep_drive = effective_light_drive(_source("sleep", 100_000, occluded=True), parameters)
    sleep_occlusion = sleep_drive < awake_drive

    sleep_state = advance_regulation(RegulationState(0.70, 0.3, 0.30), _source("sleep", 0), 3 * 3_600, parameters)
    rest_state = advance_regulation(RegulationState(0.70, 0.3, 0.30), _source("rest", 0), 3 * 3_600, parameters)
    capacity_separation = (
        sleep_state.homeostatic_load < 0.70
        and rest_state.homeostatic_load > 0.70
        and sleep_state.physical_capacity > 0.30
        and rest_state.physical_capacity > 0.30
    )

    normal_night = advance_regulation(RegulationState(0.78, 0.55, 0.40), _source("sleep", 0), 8 * 3_600, parameters)
    normal_night_plausible = normal_night.homeostatic_load < 0.20 and normal_night.physical_capacity > 0.40

    day_nap_start = RegulationState(0.68, 0.0, 0.60)
    day_nap = advance_regulation(day_nap_start, _source("sleep", 100_000, occluded=True), 90 * 60, parameters)
    nap_is_possible = day_nap.homeostatic_load < day_nap_start.homeostatic_load

    postponed_start = RegulationState(0.72, 0.50, 0.85)
    postponed = advance_regulation(postponed_start, _source("wake", 0, stimulation=1.0), 4 * 3_600, parameters)
    postponed_stability = wake_stability(postponed, _source("wake", 0, stimulation=1.0), parameters)
    # Le score peut déjà être saturé avant le report ; la falsification porte
    # donc sur les causes continues (H et stabilité), pas sur un score affiché
    # qui ne peut dépasser 1.
    voluntary_postponement_degrades = (
        postponed.homeostatic_load > postponed_start.homeostatic_load
        and postponed_stability.instability > 0.0
    )

    # Entrainment et ré-entrainment : on constate un effet cumulatif, limité,
    # plutôt qu'un prétendu alignement instantané à une heure civile.
    dark_reference = RegulationState(0.40, 0.18, 0.70)
    lit_reference = dark_reference
    dark_after_one = advance_regulation(dark_reference, dark_wake, 24 * 3_600, parameters)
    dark_after_many = advance_regulation(dark_reference, dark_wake, 5 * 24 * 3_600, parameters)
    lit_after_one = _daily_light_cycle(lit_reference, parameters)
    lit_after_many = lit_reference
    for _ in range(5):
        lit_after_many = _daily_light_cycle(lit_after_many, parameters)
    one_day_effect = abs(_phase_delta(lit_after_one.circadian_phase, dark_after_one.circadian_phase))
    many_day_effect = abs(_phase_delta(lit_after_many.circadian_phase, dark_after_many.circadian_phase))
    entrainment_progressive = one_day_effect > 0.0 and many_day_effect > one_day_effect and one_day_effect < 0.25

    shifted_once = advance_regulation(lit_after_many, _source("wake", 100_000), 8 * 3_600, parameters)
    shifted_many = shifted_once
    for _ in range(3):
        shifted_many = _daily_light_cycle(shifted_many, parameters)
    first_reentrainment_delta = abs(_phase_delta(shifted_once.circadian_phase, lit_after_many.circadian_phase))
    later_reentrainment_delta = abs(_phase_delta(shifted_many.circadian_phase, lit_after_many.circadian_phase))
    reentrainment_progressive = (
        first_reentrainment_delta < 0.40
        and later_reentrainment_delta < 0.50
        and later_reentrainment_delta > 0.0001
    )

    # Comparaison des deux familles exigée par le contrat : elles sont toutes
    # deux évaluées, mais aucune coexistence production n'est créée.
    # Point volontairement dans la bande non saturée : comparer deux fonctions
    # au plafond 1 ne constituerait pas une comparaison falsifiable.
    comparison_state = RegulationState(0.50, 0.25, 0.80)
    additive = sleep_propensity(comparison_state, parameters, family="additive")
    modulated = sleep_propensity(comparison_state, parameters, family="threshold_modulated")
    families_distinct = abs(additive.sleep_propensity - modulated.sleep_propensity) > 1e-6

    critical_state = RegulationState(0.98, 0.5, 0.8)
    low_stimulation = _source("wake", 0, stimulation=0.0)
    high_stimulation = _source("wake", 0, stimulation=1.0)
    unstable = wake_stability(critical_state, low_stimulation, parameters)
    stimulated = wake_stability(critical_state, high_stimulation, parameters)
    first = stability_consequence(
        unstable, activity_id="activity-1", requires_sustained_wakefulness=True, gate_state=StabilityGateState()
    )
    repeat = stability_consequence(
        unstable, activity_id="activity-1", requires_sustained_wakefulness=True, gate_state=first.next_gate_state
    )
    bounded_stability = (
        first.should_interrupt and not repeat.should_interrupt
        and 0.0 < stimulated.instability < unstable.instability
    )

    regular = _restriction_protocol(RegulationState(0.35, 0.15, 0.70), parameters, sleep_hours=8, days=4)
    restricted = _restriction_protocol(RegulationState(0.35, 0.15, 0.70), parameters, sleep_hours=5, days=4)
    restriction_accumulates = restricted.homeostatic_load > regular.homeostatic_load
    # Contrat markovien V1 : à état complet identique, aucune histoire cachée
    # n'est inventée pour conserver une dette chronique résiduelle.
    convergence_is_markovian = (
        advance_regulation(regular, dark_wake, 3_600, parameters)
        == advance_regulation(RegulationState(regular.homeostatic_load, regular.circadian_phase, regular.physical_capacity), dark_wake, 3_600, parameters)
    )
    feline_episodes = _opportunity_episodes(calibration_profiles()["generic_feline_hypothesis.v1"])

    return CalibrationReport(
        parameters.profile_key,
        parameters.version,
        (
            CalibrationObservation("partition_invariant", partition_invariant),
            CalibrationObservation("offline_freeze_at_zero_duration", advance_regulation(initial, dark_wake, 0, parameters) == initial),
            CalibrationObservation("free_running_observable", free_running),
            CalibrationObservation("phase_dependent_light", phase_dependent_light),
            CalibrationObservation("sleep_occlusion_attenuates_light", sleep_occlusion),
            CalibrationObservation("normal_night_is_plausible", normal_night_plausible),
            CalibrationObservation("daytime_nap_and_post_deprivation_sleep_are_possible", nap_is_possible),
            CalibrationObservation("voluntary_postponement_degrades_physiology", voluntary_postponement_degrades),
            CalibrationObservation("entrainment_is_progressive", entrainment_progressive),
            CalibrationObservation("reentrainment_is_progressive", reentrainment_progressive),
            CalibrationObservation("rest_and_sleep_separate_h_and_p", capacity_separation),
            CalibrationObservation("low_physical_capacity_does_not_change_sleep_propensity", sleep_propensity(RegulationState(0.70, 0.30, 0.10), parameters).sleep_propensity == sleep_propensity(RegulationState(0.70, 0.30, 0.90), parameters).sleep_propensity),
            CalibrationObservation("propensity_families_are_comparable", families_distinct),
            CalibrationObservation("critical_stability_is_bounded", bounded_stability),
            CalibrationObservation("repeated_restriction_accumulates_during_protocol", restriction_accumulates),
            CalibrationObservation("complete_state_convergence_is_markovian", convergence_is_markovian),
            CalibrationObservation("generic_feline_opportunities_allow_multiple_episodes", feline_episodes >= 2),
            CalibrationObservation("additive_propensity_milli", round(additive.sleep_propensity * 100_000)),
            CalibrationObservation("modulated_propensity_milli", round(modulated.sleep_propensity * 100_000)),
            CalibrationObservation("awake_light_drive_milli", round(awake_drive * 100_000)),
            CalibrationObservation("sleep_light_drive_milli", round(sleep_drive * 100_000)),
            CalibrationObservation("generic_feline_episode_count", feline_episodes),
        ),
    )
