"""Projection explicable entre motifs, buts et intention active.

Cette couche reste pure : elle organise les raisons disponibles à un instant
donné; elle ne crée pas une action et ne remplace pas la validation canonique.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .goals import GoalService
from .motivation import MotivationService, MotiveCandidate
from .policy import PolicyContext
from .simulation import SimulationEngine
from .sleep_physiology import SleepPhysiologyFoundationService, SleepPhysiologyService

class DecisionError(ValueError):
 def __init__(self,message: str,*,code: str)->None: super().__init__(message); self.code=code

@dataclass(frozen=True)
class DecisionFrame:
 character_key:str
 active_intention:dict[str,Any]|None
 goals:tuple[dict[str,Any],...]
 motives:tuple[MotiveCandidate,...]
 dominant_reason_kind:str|None
 dominant_reason_key:str|None
 def wire(self)->dict[str,Any]:
  return {'character_key':self.character_key,'active_intention':self.active_intention,'goals':list(self.goals),'motives':[item.as_dict() for item in self.motives],'dominant_reason_kind':self.dominant_reason_kind,'dominant_reason_key':self.dominant_reason_key}

class DecisionFrameService:
 def __init__(self,conn)->None:self._conn=conn
 def build(self,world_id:Any,character_key:Any,context:Any)->DecisionFrame:
  if not isinstance(context,PolicyContext):raise DecisionError('contexte de décision invalide',code='invalid_decision_context')
  if context.character_key!=character_key:raise DecisionError('contexte attribué à un autre personnage',code='decision_context_mismatch')
  goals=GoalService(self._conn).goals(world_id,character_key); active=GoalService(self._conn).active_intention(world_id,character_key); motives=MotivationService().candidates(context)
  if active is not None:return DecisionFrame(character_key,active,goals,motives,'active_intention',active['intention_key'])
  if motives:return DecisionFrame(character_key,None,goals,motives,'motive',motives[0].candidate_key)
  candidates=[goal for goal in goals if goal['status'] in {'candidate','adopted'}]
  if candidates:
   best=max(candidates,key=lambda goal:(goal['urgency_milli'],goal['importance_milli'],goal['goal_key']))
   return DecisionFrame(character_key,None,goals,motives,'goal',best['goal_key'])
  return DecisionFrame(character_key,None,goals,motives,None,None)
 def build_current(self,world_id:Any,character_key:Any)->DecisionFrame:
  if SleepPhysiologyFoundationService(self._conn).system_status(world_id)=="active":
   goals=GoalService(self._conn).goals(world_id,character_key);active=GoalService(self._conn).active_intention(world_id,character_key)
   physiology=SleepPhysiologyService(self._conn);state=physiology.read_state(world_id,character_key)
   source=physiology.resolve_light_source_owner_backed(world_id,character_key,at_time=state.anchor_at)
   projection=physiology.project_synthetic(world_id,character_key,source.source)
   sleep_pressure=max(0,min(1000,round(projection.propensity.sleep_propensity*1000)))
   recovery=max(0,min(1000,round((1.0-state.regulation.physical_capacity)*1000)))
   motives=[]
   if sleep_pressure:
    motives.append(MotiveCandidate(character_key,"motive_sleep_regulation","physiology_owner_backed","sleep_regulation","regulate",sleep_pressure,sleep_pressure,sleep_pressure,("sleep",)))
   if recovery:
    motives.append(MotiveCandidate(character_key,"motive_physical_capacity","physiology_owner_backed","physical_capacity","restore",recovery,recovery,recovery,("rest",)))
   motives.sort(key=lambda item:(-item.urgency_milli,-item.pressure_milli,item.candidate_key));motives=tuple(motives)
   if active is not None:return DecisionFrame(character_key,active,goals,motives,"active_intention",active["intention_key"])
   if motives:return DecisionFrame(character_key,None,goals,motives,"physiology",motives[0].candidate_key)
   candidates=[goal for goal in goals if goal["status"] in {"candidate","adopted"}]
   if candidates:
    best=max(candidates,key=lambda goal:(goal["urgency_milli"],goal["importance_milli"],goal["goal_key"]));return DecisionFrame(character_key,None,goals,motives,"goal",best["goal_key"])
   return DecisionFrame(character_key,None,goals,motives,None,None)
  return self.build(world_id,character_key,SimulationEngine(self._conn).policy_context(world_id,character_key))
