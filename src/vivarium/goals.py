"""Objectifs subjectifs et intentions persistantes, distincts des actions."""
from __future__ import annotations
import json, sqlite3
from typing import Any, Mapping
from .db import transaction
from .registry import _KEY_RE
from .util import Clock, new_uuid

class GoalError(ValueError):
 def __init__(self,message: str,*,code: str): super().__init__(message); self.code=code
def _key(v: Any)->str:
 if not isinstance(v,str) or not _KEY_RE.fullmatch(v): raise GoalError('clé invalide',code='invalid_goal')
 return v
def _obj(v: Any,label: str)->dict[str,Any]:
 if not isinstance(v,Mapping): raise GoalError(f'{label} invalide',code='invalid_goal')
 return dict(v)
def _milli(v: Any)->int:
 if not isinstance(v,int) or isinstance(v,bool) or not 0<=v<=1000: raise GoalError('score invalide',code='invalid_goal')
 return v
def _j(v: Mapping[str,Any])->str: return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)

class GoalService:
 def __init__(self,conn: sqlite3.Connection,clock: Clock|None=None): self._conn,self._clock=conn,clock or Clock()
 def _character(self,wid: int,key: str)->int:
  r=self._conn.execute('SELECT id FROM character WHERE world_id=? AND key=?',(wid,key)).fetchone()
  if r is None: raise GoalError('personnage introuvable',code='character_not_found')
  return r['id']
 def create_goal(self,wid: int,character: str,goal_key: str,*,family: str,target: Mapping[str,Any],source_kind: str,success_conditions: Mapping[str,Any],perceived_feasibility_milli: int,importance_milli: int,urgency_milli: int,horizon_at: str|None=None)->dict[str,Any]:
  if family not in {'immediate','persistent','social','defensive','collective'}: raise GoalError('famille invalide',code='invalid_goal')
  character,goal_key,source_kind=_key(character),_key(goal_key),_key(source_kind); target=_obj(target,'cible'); success_conditions=_obj(success_conditions,'succès'); f,i,u=_milli(perceived_feasibility_milli),_milli(importance_milli),_milli(urgency_milli); cid=self._character(wid,character); now=self._clock.now_iso()
  with transaction(self._conn) as c:
   cur=c.execute('INSERT INTO subjective_goal (public_id,world_id,character_id,goal_key,family,target_json,source_kind,horizon_at,success_conditions_json,perceived_feasibility_milli,importance_milli,urgency_milli,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,\'candidate\',?)',(new_uuid(),wid,cid,goal_key,family,_j(target),source_kind,horizon_at,_j(success_conditions),f,i,u,now))
   c.execute('INSERT INTO subjective_goal_event (world_id,character_id,goal_id,event_type,payload_json,recorded_at) VALUES (?,?,?,\'goal_created\',?,?)',(wid,cid,cur.lastrowid,_j({'goal_key':goal_key,'source_kind':source_kind}),now))
  return self.goals(wid,character)[-1]
 def adopt_intention(self,wid: int,character: str,goal_key: str,intention_key: str,*,plan: Mapping[str,Any],resume_context: Mapping[str,Any])->None:
  character,goal_key,intention_key=_key(character),_key(goal_key),_key(intention_key); plan=_obj(plan,'plan'); resume_context=_obj(resume_context,'contexte'); cid=self._character(wid,character); now=self._clock.now_iso()
  with transaction(self._conn) as c:
   goal=c.execute('SELECT id FROM subjective_goal WHERE world_id=? AND character_id=? AND goal_key=? AND status IN (\'candidate\',\'adopted\')',(wid,cid,goal_key)).fetchone()
   if goal is None: raise GoalError('objectif non adoptable',code='goal_not_adoptable')
   c.execute("UPDATE subjective_intention SET status='interrupted',updated_at=? WHERE world_id=? AND character_id=? AND status='active'",(now,wid,cid))
   c.execute("UPDATE subjective_goal SET status='adopted' WHERE id=?",(goal['id'],))
   cur=c.execute("INSERT INTO subjective_intention (public_id,world_id,character_id,goal_id,intention_key,status,plan_json,resume_context_json,created_at,updated_at) VALUES (?,?,?,?,?,'active',?,?,?,?)",(new_uuid(),wid,cid,goal['id'],intention_key,_j(plan),_j(resume_context),now,now))
   c.execute("INSERT INTO subjective_goal_event (world_id,character_id,goal_id,intention_id,event_type,payload_json,recorded_at) VALUES (?,?,?,?, 'intention_adopted',?,?)",(wid,cid,goal['id'],cur.lastrowid,_j({'intention_key':intention_key}),now))
 def goals(self,wid: int,character: str)->tuple[dict[str,Any],...]:
  cid=self._character(wid,_key(character)); rows=self._conn.execute('SELECT * FROM subjective_goal WHERE world_id=? AND character_id=? ORDER BY id',(wid,cid)).fetchall(); return tuple({'goal_key':r['goal_key'],'family':r['family'],'target':json.loads(r['target_json']),'source_kind':r['source_kind'],'status':r['status'],'importance_milli':r['importance_milli'],'urgency_milli':r['urgency_milli']} for r in rows)
