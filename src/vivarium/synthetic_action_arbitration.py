"""Adaptateur de banc pour l'arbitrage causal neutre.

La logique generique vit dans ``action_arbitration_runtime``. Ce module ne
conserve que l'entree a cause explicite necessaire aux falsifications de labo.
"""
from __future__ import annotations

from typing import Any

from .action_arbitration_runtime import (
    ActionArbitrationRuntimeError,
    SourceMapping,
    ArbitrationRuntimePolicy,
    ArbitrationContribution,
    ActionArbitrationFrame,
    ArbitratedAction,
    ActionArbitrationDecision,
    ActionArbitrationService as _RuntimeActionArbitrationService,
    CausalArbitrationBuilder,
    PhysicalCostRequest,
    PhysicalCostEvaluation,
    evaluate_physical_cost,
    action_specification,
)
from .action_contract import ActionSpecification
from .circadian_model import RegulationInput

SyntheticActionArbitrationError = ActionArbitrationRuntimeError
SyntheticSourceMapping = SourceMapping
SyntheticArbitrationPolicy = ArbitrationRuntimePolicy


class ActionArbitrationService(_RuntimeActionArbitrationService):
    """Compatibilite de banc; l'implementation de decision reste unique."""

    def execute_synthetic(self, conn: Any, frame: ActionArbitrationFrame, *, clock: Any = None):
        return self.execute(conn, frame, clock=clock)


class SyntheticCausalArbitrationBuilder(CausalArbitrationBuilder):
    """Seule facade autorisee a recevoir un ``RegulationInput`` libre."""

    def build(
        self, world_id: int, actor_key: str, *, canonical_at: str,
        sleep_specification: ActionSpecification, rest_specification: ActionSpecification,
        wake_source: RegulationInput, current_action_key: str | None = None,
    ) -> ActionArbitrationFrame:
        if wake_source.state != "wake":
            raise SyntheticActionArbitrationError(
                "source de veille requise", code="invalid_causal_source"
            )
        return self._build_from_source(
            world_id, actor_key, canonical_at=canonical_at,
            sleep_specification=sleep_specification, rest_specification=rest_specification,
            wake_source=wake_source, current_action_key=current_action_key,
        )

    def audit_decision(self, frame: ActionArbitrationFrame, decision: ActionArbitrationDecision) -> int:
        return super().audit_decision(
            frame, decision, reason_code="synthetic_causal_arbitration"
        )


def synthetic_specification(action_kind: Any, params: Any) -> ActionSpecification:
    return action_specification(action_kind, params)
