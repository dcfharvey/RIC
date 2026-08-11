"""Runtime persistant et borné du premier MVP alpha.

Cette couche assemble des services déjà canoniques; elle n'introduit pas une
deuxième logique de monde. Elle peut fonctionner sans fournisseur local : les
routines déterministes continuent, tandis que les appels cognitifs et sociaux
restent simplement absents. Avec un fournisseur, chaque sous-système conserve
ses propres admissions, limites et modes dégradés.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from .cognition import CognitionProvider
from .diagnostics import DiagnosticRecorder
from .cognition_policy import CognitionCallLimits
from .autonomy_cycle import AutonomyCycle, AutonomyOutcome
from .arrival_cycle import InitialArrivalCycle, InitialArrivalOutcome
from .orchestrator import OrchestratorTick, VivariumOrchestrator
from .scenes import SocialSceneService
from .scene_turn import SceneTurnProvider
from .social_interpretation_provider import SocialInterpretationProvider
from .social_appraisal_provider import SocialAppraisalProvider
from .scc3a_affect_provider import SCC3AAffectProvider
from .simulation import SimulationReport, SimulationEngine
from .social_cycle import SocialCycleOutcome, SocialSceneCycle
from .world import WorldEngine
from .non_sapient import NonSapientAgencyCycle, NonSapientOutcome
from .util import Clock


class MVPRuntimeError(ValueError):
    """Configuration de runtime invalide avant une exécution."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class MVPRunReport:
    world_id: int
    status: str
    simulation: SimulationReport | None
    arrival: InitialArrivalOutcome | None
    cognition: OrchestratorTick | None
    autonomy: AutonomyOutcome | None
    social: SocialCycleOutcome | None
    non_sapient: NonSapientOutcome | None = None


class MVPRuntime:
    """Un tick d'application : déterminisme, puis cognition et social bornés."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        world_id: Any,
        *,
        cognition_provider: CognitionProvider | None = None,
        scene_provider: SceneTurnProvider | None = None,
        interpretation_provider: SocialInterpretationProvider | None = None,
        appraisal_provider: SocialAppraisalProvider | None = None,
        affect_provider: SCC3AAffectProvider | None = None,
        admission_policy: Any = None,
        limits: CognitionCallLimits | None = None,
        max_transitions: int = 120,
        clock: Clock | None = None,
        diagnostics: DiagnosticRecorder | None = None,
    ) -> None:
        if not isinstance(world_id, int) or isinstance(world_id, bool) or world_id < 1:
            raise MVPRuntimeError("monde invalide", code="invalid_mvp_runtime")
        if (cognition_provider is None) != (scene_provider is None):
            raise MVPRuntimeError(
                "les fournisseurs cognitif et social doivent être activés ensemble",
                code="invalid_mvp_runtime",
            )
        if scene_provider is None and interpretation_provider is not None:
            raise MVPRuntimeError(
                "le provider d'interprétation exige le provider de scène",
                code="invalid_mvp_runtime",
            )
        if appraisal_provider is not None and interpretation_provider is None:
            raise MVPRuntimeError("le provider d appraisal exige le provider d interpretation", code="invalid_mvp_runtime")
        if affect_provider is not None and appraisal_provider is None:
            raise MVPRuntimeError("le provider affect exige le provider d appraisal", code="invalid_mvp_runtime")
        if not isinstance(max_transitions, int) or isinstance(max_transitions, bool) or not 1 <= max_transitions <= 1000:
            raise MVPRuntimeError("borne de transitions invalide", code="invalid_mvp_runtime")
        self._conn = conn
        self.world_id = world_id
        self._cognition_provider = cognition_provider
        self._scene_provider = scene_provider
        self._interpretation_provider = interpretation_provider
        self._admission_policy = admission_policy
        self._limits = limits or CognitionCallLimits(0, 3600, 8)
        self._limits.validated()
        self._max_transitions = max_transitions
        self._clock = clock or Clock()
        self._social_cycle = None if scene_provider is None else SocialSceneCycle(
            conn, scene_provider, clock=self._clock,
            interpretation_provider=interpretation_provider,
            appraisal_provider=appraisal_provider,
            affect_provider=affect_provider,
            admission_policy=admission_policy,
            diagnostics=diagnostics,
        )

    def run_once(self) -> MVPRunReport:
        """Fait progresser un monde actif, sans jamais traiter une pause."""
        world = WorldEngine(self._conn, clock=self._clock).get_world(self.world_id)
        if world["status"] == "paused":
            return MVPRunReport(self.world_id, "paused", None, None, None, None, None)
        arrival = None
        if self._cognition_provider is not None and self._scene_provider is not None:
            arrival = InitialArrivalCycle(self._conn, self._cognition_provider, clock=self._clock).tick(
                self.world_id, self._limits
            )
            # L'activité déterministe verrouille un déplacement en cours. La
            # phase d'arrivée doit donc se terminer avant son initialisation;
            # une résidente reçoit au plus une occasion par tick.
            if arrival.pending:
                return MVPRunReport(self.world_id, "active", None, arrival, None, None, None)
        target = WorldEngine(self._conn, clock=self._clock).read_canonical_time(self.world_id)
        # `run_to` matérialise les besoins des activités actives. L'appeler à
        # chaque pulsation murale alors qu'aucune activité n'arrive à son terme
        # ne crée aucune décision et gonfle inutilement le journal canonique.
        # La prochaine échéance planifiée est le jalon objectif : avant elle,
        # l'état dérivé reste lisible sans écriture; à elle, le simulateur
        # reprend seul la main.
        simulation = None
        if self._simulation_due(target):
            simulation = SimulationEngine(self._conn, clock=self._clock).run_to(
                self.world_id, target, max_transitions=self._max_transitions
            )
        cognition = None
        autonomy = None
        social = None
        non_sapient = NonSapientAgencyCycle(self._conn, clock=self._clock).tick(self.world_id)
        if self._cognition_provider is not None and self._scene_provider is not None:
            # Une nouvelle attente commune est une occasion sociale factuelle.
            # Elle doit être observée avant que l'autonomie puisse remplacer
            # l'`idle` qui la source; sinon une décision d'activité valide
            # efface systématiquement l'occasion avant sa découverte.
            assert self._social_cycle is not None
            social = self._social_cycle.tick(
                self.world_id, self._limits
            )
            # L'attente d'une replique peut faire franchir une echeance du
            # monde. On rend alors immediatement la main au determinisme au
            # lieu de construire un contexte cognitif deja en retard.
            if self._simulation_due(
                WorldEngine(self._conn, clock=self._clock).read_canonical_time(self.world_id)
            ):
                return MVPRunReport(
                    self.world_id, "active", simulation, arrival, None, None, social,
                    non_sapient,
                )
            autonomy = AutonomyCycle(self._conn, self._cognition_provider, clock=self._clock).tick(
                self.world_id, self._limits
            )
            if self._simulation_due(
                WorldEngine(self._conn, clock=self._clock).read_canonical_time(self.world_id)
            ):
                return MVPRunReport(
                    self.world_id, "active", simulation, arrival, None, autonomy, social,
                    non_sapient,
                )
            cognition = VivariumOrchestrator(
                self._conn, self._cognition_provider, clock=self._clock
            ).tick(self.world_id, self._limits, max_events_per_character=1)
        return MVPRunReport(
            self.world_id, "active", simulation, arrival, cognition, autonomy, social,
            non_sapient,
        )

    def _simulation_due(self, target_time: str) -> bool:
        """Retourne si une transition déterministe est exigible à `target_time`.

        Le cas sans activité reste dû : `SimulationEngine` doit alors choisir
        l'activité déterministe initiale. Sinon, seule la première fin planifiée
        peut faire évoluer le monde; une lecture intermédiaire ne doit pas se
        transformer en écriture périodique.
        """
        row = self._conn.execute(
            "SELECT MIN(planned_end_at) AS next_end FROM activity "
            "WHERE world_id = ? AND status = 'active'",
            (self.world_id,),
        ).fetchone()
        return row is None or row["next_end"] is None or row["next_end"] <= target_time

    def shutdown(self) -> int:
        """Clôture les scènes actives sans produire de parole fictive."""
        return SocialSceneService(self._conn).interrupt_active(
            self.world_id, reason="runtime_shutdown"
        )
