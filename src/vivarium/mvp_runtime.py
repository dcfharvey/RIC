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
from .cognition_policy import CognitionCallLimits
from .orchestrator import OrchestratorTick, VivariumOrchestrator
from .scenes import SocialSceneService
from .scene_turn import SceneTurnProvider
from .simulation import SimulationReport, SimulationEngine
from .social_cycle import SocialCycleOutcome, SocialSceneCycle
from .world import WorldEngine


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
    cognition: OrchestratorTick | None
    social: SocialCycleOutcome | None


class MVPRuntime:
    """Un tick d'application : déterminisme, puis cognition et social bornés."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        world_id: Any,
        *,
        cognition_provider: CognitionProvider | None = None,
        scene_provider: SceneTurnProvider | None = None,
        limits: CognitionCallLimits | None = None,
        max_transitions: int = 120,
    ) -> None:
        if not isinstance(world_id, int) or isinstance(world_id, bool) or world_id < 1:
            raise MVPRuntimeError("monde invalide", code="invalid_mvp_runtime")
        if (cognition_provider is None) != (scene_provider is None):
            raise MVPRuntimeError(
                "les fournisseurs cognitif et social doivent être activés ensemble",
                code="invalid_mvp_runtime",
            )
        if not isinstance(max_transitions, int) or isinstance(max_transitions, bool) or not 1 <= max_transitions <= 1000:
            raise MVPRuntimeError("borne de transitions invalide", code="invalid_mvp_runtime")
        self._conn = conn
        self.world_id = world_id
        self._cognition_provider = cognition_provider
        self._scene_provider = scene_provider
        self._limits = limits or CognitionCallLimits(0, 3600, 8)
        self._limits.validated()
        self._max_transitions = max_transitions

    def run_once(self) -> MVPRunReport:
        """Fait progresser un monde actif, sans jamais traiter une pause."""
        world = WorldEngine(self._conn).get_world(self.world_id)
        if world["status"] == "paused":
            return MVPRunReport(self.world_id, "paused", None, None, None)
        target = WorldEngine(self._conn).read_canonical_time(self.world_id)
        simulation = SimulationEngine(self._conn).run_to(
            self.world_id, target, max_transitions=self._max_transitions
        )
        cognition = None
        social = None
        if self._cognition_provider is not None and self._scene_provider is not None:
            cognition = VivariumOrchestrator(
                self._conn, self._cognition_provider
            ).tick(self.world_id, self._limits, max_events_per_character=1)
            social = SocialSceneCycle(self._conn, self._scene_provider).tick(
                self.world_id, self._limits
            )
        return MVPRunReport(self.world_id, "active", simulation, cognition, social)

    def shutdown(self) -> int:
        """Clôture les scènes actives sans produire de parole fictive."""
        return SocialSceneService(self._conn).interrupt_active(
            self.world_id, reason="runtime_shutdown"
        )
