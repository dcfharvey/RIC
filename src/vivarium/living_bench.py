"""Banc jetable de la première boucle vivante, avec fournisseur injectable."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
from .cognition import CognitionProvider
from .cognition_policy import CognitionCallLimits
from .db import connect_database
from .integration_world import IntegrationWorldService
from .migrations import ensure_schema
from .orchestrator import VivariumOrchestrator, OrchestratorTick
from .repro import canonical_state_digest, structural_event_audit
from .traversal import TraversalEngine

@dataclass(frozen=True)
class LivingBenchReport:
 ticks:tuple[OrchestratorTick,...];canonical_digest:dict[str,Any];audit_findings:dict[str,Any]
 @property
 def provider_outcomes(self):return tuple(item for tick in self.ticks for item in tick.outcomes if item.outcome in {'routed','provider_degraded'})

def run_living_bench(provider:CognitionProvider,limits:CognitionCallLimits,*,max_ticks:int=8,on_tick:Callable[[OrchestratorTick],None]|None=None)->LivingBenchReport:
 """Construit puis ferme une base en mémoire; ne touche aucun monde utilisateur."""
 if not isinstance(max_ticks,int) or isinstance(max_ticks,bool) or not 1<=max_ticks<=32:raise ValueError('max_ticks invalide')
 conn=connect_database(':memory:')
 try:
  ensure_schema(conn);wid=IntegrationWorldService(conn).create_initial_world()['id']
  # Signal concret : Sophie traverse une porte que les observatrices peuvent percevoir.
  TraversalEngine(conn).traverse_character(wid,'sophie','porte_entree','salon')
  orch=VivariumOrchestrator(conn,provider);ticks=[]
  for _ in range(max_ticks):
   tick=orch.tick(wid,limits,max_events_per_character=20);ticks.append(tick)
   if on_tick is not None:on_tick(tick)
   if not tick.outcomes:break
  return LivingBenchReport(tuple(ticks),canonical_state_digest(conn,wid),structural_event_audit(conn,wid))
 finally:conn.close()
