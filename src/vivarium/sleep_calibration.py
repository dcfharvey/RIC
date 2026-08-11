"""Banc déterministe, jetable et sans runtime pour le modèle circadien V1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Callable, Literal

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


# Contrats numériques du banc, pas paramètres biologiques. Le phase-lock doit
# persister plusieurs cycles ; la borne maximale évite un test sans fin.
PHASE_LOCK_TOLERANCE_TURNS = 1e-6
PHASE_LOCK_CONSECUTIVE_CYCLES = 3
PHASE_LOCK_MAX_CYCLES = 512
PARTITION_PHASE_TOLERANCE_TURNS = 1e-8


@dataclass(frozen=True)
class CalibrationObservation:
    name: str
    value: float | int | bool


@dataclass(frozen=True)
class CalibrationTrajectory:
    """Série de projections du banc, jamais un état canonique persistant."""

    name: str
    unit: str
    values: tuple[int, ...]


@dataclass(frozen=True)
class CalibrationReport:
    profile_key: str
    profile_version: int
    observations: tuple[CalibrationObservation, ...]
    trajectories: tuple[CalibrationTrajectory, ...]

    @property
    def passed(self) -> bool:
        return all(bool(item.value) for item in self.observations if isinstance(item.value, bool))

    def as_dict(self) -> dict:
        return {
            "profile_key": self.profile_key,
            "profile_version": self.profile_version,
            "passed": self.passed,
            "observations": [asdict(item) for item in self.observations],
            "trajectories": [asdict(item) for item in self.trajectories],
        }


@dataclass(frozen=True)
class FamilyScenario:
    """Comparaison de projections, sans créer de seuil de décision runtime."""

    name: str
    additive_milli: int
    sensitivity_modulated_milli: int


@dataclass(frozen=True)
class ParameterSweep:
    """Résultat d'un voisinage borné de calibration, jamais un profil actif."""

    parameter_key: str
    candidate_values: tuple[str, ...]
    passing_values: tuple[str, ...]
    failing_values: tuple[str, ...]
    failure_reasons: tuple[str, ...]


@dataclass(frozen=True)
class CoupledSweep:
    """Exploration conjointe de deux paramètres connus comme corrélés."""

    row_key: str
    column_key: str
    row_values: tuple[str, ...]
    column_values: tuple[str, ...]
    passed_cells: tuple[str, ...]
    failed_cells: tuple[str, ...]


@dataclass(frozen=True)
class FelineSandbox:
    """Capacité générique, non une prédiction sur un personnage ou une espèce."""

    candidate_label: str
    opportunity_episode_count: int


@dataclass(frozen=True)
class CalibrationSelectionReport:
    """Rapport reproductible de choix V1, séparé du profil de production futur."""

    profile_key: str
    recommended_family: Literal["additive", "sensitivity_modulated"]
    family_scenarios: tuple[FamilyScenario, ...]
    shared_physiology_passed: bool
    parameter_sweeps: tuple[ParameterSweep, ...]
    period_forcing_sweep: CoupledSweep
    feline_sandbox: tuple[FelineSandbox, ...]

    @property
    def passed(self) -> bool:
        """Le candidat central est sain ; les échecs de frontière sont attendus."""
        return self.shared_physiology_passed

    def as_dict(self) -> dict:
        return {
            "profile_key": self.profile_key,
            "recommended_family": self.recommended_family,
            "passed": self.passed,
            "family_scenarios": [asdict(item) for item in self.family_scenarios],
            "shared_physiology_passed": self.shared_physiology_passed,
            "parameter_sweeps": [asdict(item) for item in self.parameter_sweeps],
            "period_forcing_sweep": asdict(self.period_forcing_sweep),
            "feline_sandbox": [asdict(item) for item in self.feline_sandbox],
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


def _shifted_light_cycle(state: RegulationState, parameters: CircadianParameters) -> RegulationState:
    """Même cycle de sommeil, zeitgeber objectif déplacé de huit heures."""
    state = advance_regulation(state, _source("wake", 0), 8 * 3_600, parameters)
    state = advance_regulation(state, _source("wake", 100_000), 8 * 3_600, parameters)
    state = advance_regulation(state, _source("sleep", 100_000, occluded=True), 4 * 3_600, parameters)
    return advance_regulation(state, _source("sleep", 0, occluded=True), 4 * 3_600, parameters)


def _phase_lock(
    initial: RegulationState,
    parameters: CircadianParameters,
    cycle: Callable[[RegulationState, CircadianParameters], RegulationState],
) -> tuple[RegulationState, tuple[float, ...], int | None]:
    """Cherche un phase-lock par convergence de l'écart cycle à cycle."""
    state = initial
    phases = [state.circadian_phase]
    stable_cycles = 0
    for index in range(1, PHASE_LOCK_MAX_CYCLES + 1):
        previous = state.circadian_phase
        state = cycle(state, parameters)
        phases.append(state.circadian_phase)
        if abs(_phase_delta(state.circadian_phase, previous)) <= PHASE_LOCK_TOLERANCE_TURNS:
            stable_cycles += 1
            if stable_cycles >= PHASE_LOCK_CONSECUTIVE_CYCLES:
                return state, tuple(phases), index
        else:
            stable_cycles = 0
    return state, tuple(phases), None


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


def run_reference_calibration(
    profile_key: str = "human_reference_candidate.v1",
    *,
    parameters: CircadianParameters | None = None,
    propensity_family: Literal["additive", "sensitivity_modulated"] = "additive",
) -> CalibrationReport:
    """Exécute les falsifications minimales sans monde ni base persistante.

    Ce banc ne prétend pas simuler les choix sociaux. Il mesure les propriétés
    de la couche physiologique avant son raccord futur à l'arbitre moteur.
    """
    profiles = calibration_profiles()
    if parameters is None:
        parameters = profiles[profile_key]
    elif parameters.profile_key != profile_key:
        raise ValueError("profil de calibration et paramètres incohérents")
    initial = RegulationState(0.35, 0.15, 0.60)
    dark_wake = _source("wake", 0)
    light_wake = _source("wake", 100_000)

    # Contrat B : H et P sont invariants ici ; la phase est vérifiée selon une
    # tolérance de convergence, y compris avec des frontières non alignées sur
    # le quantum numérique de soixante secondes.
    partition_source = light_wake
    one_piece = advance_regulation(initial, partition_source, 24 * 3_600, parameters)
    parts = (61, 377, 1_234, 4_567, 987, 10_000)
    irregular = initial
    for duration in (*parts, 24 * 3_600 - sum(parts)):
        irregular = advance_regulation(irregular, partition_source, duration, parameters)
    partition_phase_error = abs(_phase_delta(one_piece.circadian_phase, irregular.circadian_phase))
    partition_converges = (
        abs(one_piece.homeostatic_load - irregular.homeostatic_load) < 1e-12
        and abs(one_piece.physical_capacity - irregular.physical_capacity) < 1e-12
        and partition_phase_error <= PARTITION_PHASE_TOLERANCE_TURNS
    )

    # Free-running observable, sans forcer un cycle lumière externe.
    free_state = initial
    free_phases = [free_state.circadian_phase]
    for _ in range(5):
        free_state = advance_regulation(free_state, dark_wake, 86_400, parameters)
        free_phases.append(free_state.circadian_phase)
    nominal_phase = (initial.circadian_phase + 5) % 1.0
    free_running = abs(_phase_delta(free_state.circadian_phase, nominal_phase)) > 0.001

    # Même lumière, deux phases : le forcing net de lumière, comparé au même
    # free-run, doit changer de signe.
    early_start = RegulationState(0.4, 0.125, 0.7)
    late_start = RegulationState(0.4, 0.625, 0.7)
    early = advance_regulation(early_start, light_wake, 2 * 3_600, parameters)
    late = advance_regulation(late_start, light_wake, 2 * 3_600, parameters)
    early_dark = advance_regulation(early_start, dark_wake, 2 * 3_600, parameters)
    late_dark = advance_regulation(late_start, dark_wake, 2 * 3_600, parameters)
    phase_dependent_light = (
        _phase_delta(early.circadian_phase, early_dark.circadian_phase)
        * _phase_delta(late.circadian_phase, late_dark.circadian_phase)
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

    # L'équation accepte du sommeil de jour ; séparément, la propension haute
    # rend ce sommeil accessible au futur arbitre sans lui imposer l'état.
    day_nap_start = RegulationState(0.68, 0.0, 0.60)
    day_nap = advance_regulation(day_nap_start, _source("sleep", 100_000, occluded=True), 90 * 60, parameters)
    post_deprivation_day = RegulationState(0.84, 0.0, 0.60)
    daytime_sleep_equation_dissipates_h = day_nap.homeostatic_load < day_nap_start.homeostatic_load
    daytime_sleep_propensity_accessible = (
        sleep_propensity(post_deprivation_day, parameters, family=propensity_family).sleep_propensity >= 0.50
    )

    postponed_start = RegulationState(0.72, 0.50, 0.85)
    postponed = advance_regulation(postponed_start, _source("wake", 0, stimulation=1.0), 4 * 3_600, parameters)
    postponed_stability = wake_stability(postponed, _source("wake", 0, stimulation=1.0), parameters)
    voluntary_postponement_degrades = (
        postponed.homeostatic_load > postponed_start.homeostatic_load
        and postponed_stability.instability > 0.0
    )

    # Le phase-lock est la propriété exigée : des écarts quotidiens convergent
    # dans une bande numérique, sans choisir un nombre de jours biologique.
    locked_state, stable_phases, stable_lock_cycle = _phase_lock(
        RegulationState(0.40, 0.18, 0.70), parameters, _daily_light_cycle
    )
    phase_locked = stable_lock_cycle is not None
    shifted_state, shifted_phases, shifted_lock_cycle = _phase_lock(
        locked_state, parameters, _shifted_light_cycle
    )
    reentrained = (
        shifted_lock_cycle is not None
        and abs(_phase_delta(shifted_phases[1], shifted_phases[-1])) > PHASE_LOCK_TOLERANCE_TURNS
        and abs(_phase_delta(shifted_phases[-1], stable_phases[-1])) > PHASE_LOCK_TOLERANCE_TURNS
    )

    # Deux familles réellement distinctes. La seconde module la pente de la
    # réponse à H ; une recherche exhaustive de k simple montre qu'aucune
    # famille additive H+kC ne la reproduit sur cette grille non saturée.
    comparison_states = (
        RegulationState(0.46, 0.00, 0.80), RegulationState(0.46, 0.25, 0.80),
        RegulationState(0.58, 0.00, 0.80), RegulationState(0.58, 0.25, 0.80),
        RegulationState(0.68, 0.00, 0.80), RegulationState(0.68, 0.25, 0.80),
    )
    sensitivity_values = tuple(
        sleep_propensity(state, parameters, family="sensitivity_modulated").sleep_propensity
        for state in comparison_states
    )
    best_additive_error = min(
        max(
            abs(
                sleep_propensity(state, replace(parameters, circadian_propensity_weight=weight / 1_000), family="additive").sleep_propensity
                - target
            )
            for state, target in zip(comparison_states, sensitivity_values, strict=True)
        )
        for weight in range(0, 601)
    )
    families_not_trivially_equivalent = best_additive_error > 0.001

    # À physiologie extrême, la stimulation diminue la manifestation continue
    # mais laisse la bande critical et sa conséquence moteur atteignables à
    # chaque nouvelle activité : pas de protection indéfinie.
    extreme = RegulationState(1.0, 0.5, 0.8)
    no_stimulation = wake_stability(extreme, _source("wake", 0, stimulation=0.0), parameters)
    full_stimulation = wake_stability(extreme, _source("wake", 0, stimulation=1.0), parameters)
    critical_bands = []
    critical_state = extreme
    previous_band: Literal["stable", "fragile", "critical"] = "stable"
    for _ in range(24):
        stability = wake_stability(critical_state, _source("wake", 0, stimulation=1.0), parameters, previous_band=previous_band)
        critical_bands.append(stability.band == "critical")
        previous_band = stability.band
        critical_state = advance_regulation(critical_state, _source("wake", 0, stimulation=1.0), 3_600, parameters)
    first = stability_consequence(full_stimulation, activity_id="activity-1", requires_sustained_wakefulness=True, gate_state=StabilityGateState())
    repeat = stability_consequence(full_stimulation, activity_id="activity-1", requires_sustained_wakefulness=True, gate_state=first.next_gate_state)
    bounded_stability = (
        first.should_interrupt and not repeat.should_interrupt
        and 0.0 < full_stimulation.instability < no_stimulation.instability
        and all(critical_bands)
    )

    # Restriction et récupération : pas de dette cachée après convergence, mais
    # les trajectoires divergent bel et bien pendant le protocole.
    regular_states = [RegulationState(0.35, 0.15, 0.70)]
    restricted_states = [RegulationState(0.35, 0.15, 0.70)]
    for _ in range(4):
        regular_states.append(_restriction_protocol(regular_states[-1], parameters, sleep_hours=8, days=1))
        restricted_states.append(_restriction_protocol(restricted_states[-1], parameters, sleep_hours=5, days=1))
    recovery_states = [restricted_states[-1]]
    for _ in range(3):
        recovery_states.append(_restriction_protocol(recovery_states[-1], parameters, sleep_hours=8, days=1))
    restriction_accumulates = restricted_states[-1].homeostatic_load > regular_states[-1].homeostatic_load
    convergence_is_markovian = (
        advance_regulation(regular_states[-1], dark_wake, 3_600, parameters)
        == advance_regulation(RegulationState(regular_states[-1].homeostatic_load, regular_states[-1].circadian_phase, regular_states[-1].physical_capacity), dark_wake, 3_600, parameters)
    )
    feline_episodes = _opportunity_episodes(profiles["generic_feline_hypothesis.v1"])

    return CalibrationReport(
        parameters.profile_key,
        parameters.version,
        (
            CalibrationObservation("partition_numerically_converges", partition_converges),
            CalibrationObservation("partition_phase_error_nano_turns", round(partition_phase_error * 1_000_000_000)),
            CalibrationObservation("offline_freeze_at_zero_duration", advance_regulation(initial, dark_wake, 0, parameters) == initial),
            CalibrationObservation("free_running_observable", free_running),
            CalibrationObservation("phase_dependent_light", phase_dependent_light),
            CalibrationObservation("stable_zeitgeber_phase_locks", phase_locked),
            CalibrationObservation("shifted_zeitgeber_reentrains_to_different_lock", reentrained),
            CalibrationObservation("sleep_occlusion_attenuates_light", sleep_occlusion),
            CalibrationObservation("normal_night_is_plausible", normal_night_plausible),
            CalibrationObservation("daytime_sleep_equation_dissipates_h", daytime_sleep_equation_dissipates_h),
            CalibrationObservation("post_deprivation_daytime_sleep_propensity_accessible", daytime_sleep_propensity_accessible),
            CalibrationObservation("voluntary_postponement_degrades_physiology", voluntary_postponement_degrades),
            CalibrationObservation("rest_and_sleep_separate_h_and_p", capacity_separation),
            CalibrationObservation("low_physical_capacity_does_not_change_sleep_propensity", sleep_propensity(RegulationState(0.70, 0.30, 0.10), parameters, family=propensity_family).sleep_propensity == sleep_propensity(RegulationState(0.70, 0.30, 0.90), parameters, family=propensity_family).sleep_propensity),
            CalibrationObservation("propensity_families_not_trivially_equivalent", families_not_trivially_equivalent),
            CalibrationObservation("best_additive_fit_max_error_milli", round(best_additive_error * 100_000)),
            CalibrationObservation("critical_stability_is_bounded", bounded_stability),
            CalibrationObservation("repeated_restriction_accumulates_during_protocol", restriction_accumulates),
            CalibrationObservation("complete_state_convergence_is_markovian", convergence_is_markovian),
            CalibrationObservation("generic_feline_opportunities_allow_multiple_episodes", feline_episodes >= 2),
            CalibrationObservation("generic_feline_episode_count", feline_episodes),
        ),
        (
            CalibrationTrajectory("free_running_daily_phase", "phase_milli_turn", tuple(round(value * 1_000_000) for value in free_phases)),
            CalibrationTrajectory("stable_zeitgeber_daily_phase", "phase_milli_turn", tuple(round(value * 1_000_000) for value in stable_phases)),
            CalibrationTrajectory("shifted_zeitgeber_daily_phase", "phase_milli_turn", tuple(round(value * 1_000_000) for value in shifted_phases)),
            CalibrationTrajectory("regular_sleep_h", "load_milli", tuple(round(value.homeostatic_load * 100_000) for value in regular_states)),
            CalibrationTrajectory("restriction_h", "load_milli", tuple(round(value.homeostatic_load * 100_000) for value in restricted_states)),
            CalibrationTrajectory("recovery_h", "load_milli", tuple(round(value.homeostatic_load * 100_000) for value in recovery_states)),
            CalibrationTrajectory("stability_no_stimulation_vs_maximal", "instability_milli", (round(no_stimulation.instability * 100_000), round(full_stimulation.instability * 100_000))),
            CalibrationTrajectory("additive_vs_sensitivity_modulated", "propensity_milli_pairs", tuple(round(value * 100_000) for pair in zip((sleep_propensity(state, parameters, family="additive").sleep_propensity for state in comparison_states), sensitivity_values, strict=True) for value in pair)),
        ),
    )


def _failed_falsifications(report: CalibrationReport) -> tuple[str, ...]:
    return tuple(item.name for item in report.observations if isinstance(item.value, bool) and not item.value)


def _parameter_sweep(
    parameters: CircadianParameters,
    *,
    parameter_key: str,
    candidates: tuple[tuple[str, int | float], ...],
) -> ParameterSweep:
    """Balaye un axe local sans prétendre identifier un optimum biologique."""
    passing: list[str] = []
    failing: list[str] = []
    reasons: list[str] = []
    for label, value in candidates:
        candidate = replace(parameters, **{parameter_key: value})
        failures = _failed_falsifications(
            run_reference_calibration(
                candidate.profile_key, parameters=candidate, propensity_family="additive"
            )
        )
        if failures:
            failing.append(label)
            reasons.append(f"{label}: {', '.join(failures)}")
        else:
            passing.append(label)
    return ParameterSweep(parameter_key, tuple(label for label, _ in candidates), tuple(passing), tuple(failing), tuple(reasons))


def _mapping_sweep(
    parameters: CircadianParameters,
    *,
    parameter_key: str,
    candidates: tuple[tuple[str, dict[str, float]], ...],
) -> ParameterSweep:
    """Balaye un petit groupe structurel, ici les bandes d'hystérésis."""
    passing: list[str] = []
    failing: list[str] = []
    reasons: list[str] = []
    for label, changes in candidates:
        candidate = replace(parameters, **changes)
        failures = _failed_falsifications(
            run_reference_calibration(
                candidate.profile_key, parameters=candidate, propensity_family="additive"
            )
        )
        if failures:
            failing.append(label)
            reasons.append(f"{label}: {', '.join(failures)}")
        else:
            passing.append(label)
    return ParameterSweep(parameter_key, tuple(label for label, _ in candidates), tuple(passing), tuple(failing), tuple(reasons))


def _period_forcing_sweep(parameters: CircadianParameters) -> CoupledSweep:
    """Explore la corrélation période intrinsèque/forcing lumineux connue du V1."""
    periods = (
        ("23h30", 23 * 3_600 + 30 * 60),
        ("23h45", 23 * 3_600 + 45 * 60),
        ("24h00", 24 * 3_600),
        ("24h10", 24 * 3_600 + 10 * 60),
        ("24h20", 24 * 3_600 + 20 * 60),
        ("24h30", 24 * 3_600 + 30 * 60),
        ("24h40", 24 * 3_600 + 40 * 60),
    )
    forcings = (("3000", 3_000), ("3500", 3_500), ("4000", 4_000), ("4500", 4_500), ("5000", 5_000), ("5500", 5_500), ("6000", 6_000))
    passed: list[str] = []
    failed: list[str] = []
    for period_label, period in periods:
        for forcing_label, forcing in forcings:
            candidate = replace(
                parameters,
                intrinsic_period_seconds=period,
                light_phase_shift_milli_per_hour=forcing,
            )
            failures = _failed_falsifications(
                run_reference_calibration(
                    candidate.profile_key, parameters=candidate, propensity_family="additive"
                )
            )
            cell = f"{period_label}/{forcing_label}"
            (failed if failures else passed).append(cell)
    return CoupledSweep(
        "intrinsic_period", "light_phase_shift_milli_per_hour",
        tuple(label for label, _ in periods), tuple(label for label, _ in forcings),
        tuple(passed), tuple(failed),
    )


def run_calibration_selection(
    profile_key: str = "human_reference_candidate.v1",
) -> CalibrationSelectionReport:
    """Compare les familles puis sonde une région locale, sans sélectionner un runtime.

    Toutes les bornes sont des points d'exploration [C/D]. Ce rapport ne rend
    aucun chiffre biologiquement vrai et ne change pas ``calibration_profiles``.
    """
    parameters = calibration_profiles()[profile_key]
    if parameters.evidence_class != "human_reference":
        raise ValueError("la sélection de région V1 vise le candidat humain")

    # Les deux familles reçoivent les mêmes situations. Les cycles H/phase et
    # la lumière leur sont communs ; seules les projections dérivées divergent.
    scenario_states = (
        ("normal_sleep_cycle", RegulationState(0.72, 0.50, 0.70)),
        ("high_h_wake_favorable", RegulationState(0.68, 0.00, 0.70)),
        ("moderate_h_sleep_favorable", RegulationState(0.58, 0.50, 0.70)),
        ("daytime_nap", RegulationState(0.68, 0.00, 0.70)),
        ("prolonged_deprivation", RegulationState(0.90, 0.00, 0.70)),
        ("post_deprivation_daytime_sleep", RegulationState(0.84, 0.00, 0.70)),
    )
    family_scenarios = tuple(
        FamilyScenario(
            name,
            round(sleep_propensity(state, parameters, family="additive").sleep_propensity * 100_000),
            round(
                sleep_propensity(state, parameters, family="sensitivity_modulated").sleep_propensity
                * 100_000
            ),
        )
        for name, state in scenario_states
    )
    additive_reference = run_reference_calibration(profile_key, propensity_family="additive")
    sensitivity_reference = run_reference_calibration(profile_key, propensity_family="sensitivity_modulated")
    shared_physiology_passed = additive_reference.passed and sensitivity_reference.passed

    sweeps = (
        _parameter_sweep(parameters, parameter_key="tau_wake_seconds", candidates=(("14h", 14 * 3_600), ("18h", 18 * 3_600), ("22h", 22 * 3_600))),
        _parameter_sweep(parameters, parameter_key="tau_sleep_seconds", candidates=(("2h", 2 * 3_600), ("3h", 3 * 3_600), ("4h", 4 * 3_600))),
        _parameter_sweep(parameters, parameter_key="intrinsic_period_seconds", candidates=(("23h40", 23 * 3_600 + 40 * 60), ("24h10", 24 * 3_600 + 10 * 60), ("24h40", 24 * 3_600 + 40 * 60))),
        _parameter_sweep(parameters, parameter_key="light_phase_shift_milli_per_hour", candidates=(("3000", 3_000), ("5000", 5_000), ("6000", 6_000))),
        _parameter_sweep(parameters, parameter_key="light_half_saturation_milli", candidates=(("20000", 20_000), ("30000", 30_000), ("45000", 45_000))),
        _parameter_sweep(parameters, parameter_key="sleep_occlusion_milli", candidates=(("2000", 2_000), ("5000", 5_000), ("10000", 10_000))),
        _parameter_sweep(parameters, parameter_key="circadian_propensity_weight", candidates=(("0.16", 0.16), ("0.24", 0.24), ("0.32", 0.32))),
        _parameter_sweep(parameters, parameter_key="homeostatic_stability_weight", candidates=(("0.65", 0.65), ("0.78", 0.78), ("0.90", 0.90))),
        _parameter_sweep(parameters, parameter_key="circadian_stability_weight", candidates=(("0.20", 0.20), ("0.34", 0.34), ("0.48", 0.48))),
        _parameter_sweep(parameters, parameter_key="max_stimulation_relief", candidates=(("0.40", 0.40), ("0.55", 0.55), ("0.70", 0.70))),
        _mapping_sweep(parameters, parameter_key="stability_bands", candidates=(
            ("low", {"fragile_enter": 0.42, "fragile_exit": 0.34, "critical_enter": 0.72, "critical_exit": 0.60}),
            ("reference", {"fragile_enter": 0.48, "fragile_exit": 0.40, "critical_enter": 0.78, "critical_exit": 0.66}),
            ("high", {"fragile_enter": 0.54, "fragile_exit": 0.46, "critical_enter": 0.84, "critical_exit": 0.72}),
        )),
        _parameter_sweep(parameters, parameter_key="active_capacity_cost_per_hour", candidates=(("0.015", 0.015), ("0.025", 0.025), ("0.035", 0.035))),
        _parameter_sweep(parameters, parameter_key="rest_capacity_recovery_per_hour", candidates=(("0.030", 0.030), ("0.045", 0.045), ("0.060", 0.060))),
        _parameter_sweep(parameters, parameter_key="sleep_capacity_recovery_per_hour", candidates=(("0.050", 0.050), ("0.070", 0.070), ("0.090", 0.090))),
    )
    feline = calibration_profiles()["generic_feline_hypothesis.v1"]
    feline_sandbox = tuple(
        FelineSandbox(label, _opportunity_episodes(replace(feline, tau_wake_seconds=wake_hours * 3_600,
                                                             tau_sleep_seconds=sleep_hours * 3_600)))
        for label, wake_hours, sleep_hours in (
            ("slower_hypothesis", 12, 3),
            ("reference_hypothesis", 10, 2),
            ("faster_hypothesis", 8, 1),
        )
    )

    # Les deux familles remplissent les falsifications, mais l'additive ne
    # demande qu'un poids lisible H + kC. L'alternative n'apporte ici aucune
    # propriété nécessaire inaccessible à cette forme parcimonieuse.
    return CalibrationSelectionReport(
        parameters.profile_key,
        "additive",
        family_scenarios,
        shared_physiology_passed,
        sweeps,
        _period_forcing_sweep(parameters),
        feline_sandbox,
    )
