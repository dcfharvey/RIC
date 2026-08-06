"""Scènes sociales persistantes et actes de parole structurés.

Une parole est consignée comme expression sociale, jamais comme une mutation
automatique de croyance, relation, permission ou réalité canonique.
"""
from __future__ import annotations
import json, sqlite3
from typing import Any, Mapping
from .db import transaction
from .registry import _KEY_RE
from .util import Clock, new_uuid

_ACTS=frozenset({'greet','ask','answer','inform','offer','decline','apologize','acknowledge','leave'})
class SceneError(ValueError):
 def __init__(self,message:str,*,code:str)->None:super().__init__(message);self.code=code
def _key(v:Any,label:str)->str:
 if not isinstance(v,str) or not _KEY_RE.fullmatch(v):raise SceneError(f'{label} invalide',code='invalid_scene')
 return v
def _obj(v:Any,label:str)->dict[str,Any]:
 if not isinstance(v,Mapping):raise SceneError(f'{label} invalide',code='invalid_scene')
 return {str(k):item for k,item in v.items()}
def _json(v:Mapping[str,Any])->str:return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)

class SocialSceneService:
 def __init__(self,conn:sqlite3.Connection,clock:Clock|None=None):self._conn,self._clock=conn,clock or Clock()
 def _character(self,wid:int,key:str)->sqlite3.Row:
  row=self._conn.execute('SELECT id,current_location_id AS location_id FROM character WHERE world_id=? AND key=?',(wid,key)).fetchone()
  if row is None:raise SceneError('personnage introuvable',code='character_not_found')
  return row
 def _scene(self,wid:int,key:str)->sqlite3.Row:
  row=self._conn.execute('SELECT * FROM social_scene WHERE world_id=? AND scene_key=?',(wid,key)).fetchone()
  if row is None:raise SceneError('scène introuvable',code='scene_not_found')
  return row
 def open(self,wid:Any,scene_key:Any,participants:Any)->dict[str,Any]:
  if not isinstance(wid,int) or isinstance(wid,bool) or wid<1:raise SceneError('monde invalide',code='invalid_scene')
  scene_key=_key(scene_key,'scène')
  if not isinstance(participants,(tuple,list)) or not 2<=len(participants)<=5:raise SceneError('participantes invalides',code='invalid_scene')
  keys=tuple(_key(v,'participante') for v in participants)
  if len(set(keys))!=len(keys):raise SceneError('participantes dupliquées',code='invalid_scene')
  people=tuple(self._character(wid,key) for key in keys)
  if len({row['location_id'] for row in people})!=1:raise SceneError('participantes non co-localisées',code='scene_participants_not_colocated')
  now=self._clock.now_iso()
  with transaction(self._conn) as c:
   existing=c.execute('SELECT * FROM social_scene WHERE world_id=? AND scene_key=?',(wid,scene_key)).fetchone()
   if existing is not None:return self.sheet(wid,scene_key)
   cur=c.execute("INSERT INTO social_scene (public_id,world_id,scene_key,location_id,status,opened_at,closed_at,close_reason) VALUES (?,?,?,?, 'active',?,NULL,NULL)",(new_uuid(),wid,scene_key,people[0]['location_id'],now)); sid=cur.lastrowid
   for row in people:c.execute('INSERT INTO social_scene_participant (scene_id,character_id,joined_at) VALUES (?,?,?)',(sid,row['id'],now))
   c.execute("INSERT INTO social_scene_event (scene_id,event_type,payload_json,recorded_at) VALUES (?, 'scene_opened',?,?)",(sid,_json({'participants':list(keys)}),now))
  return self.sheet(wid,scene_key)
 def speak(self,wid:Any,scene_key:Any,act_key:Any,speaker_key:Any,*,act_kind:Any,content:Any,recipient_key:Any=None,payload:Any=None)->dict[str,Any]:
  if not isinstance(wid,int) or isinstance(wid,bool) or wid<1:raise SceneError('monde invalide',code='invalid_scene')
  scene_key,act_key,speaker_key=_key(scene_key,'scène'),_key(act_key,'acte'),_key(speaker_key,'locutrice')
  if act_kind not in _ACTS:raise SceneError('acte de parole inconnu',code='invalid_scene')
  if not isinstance(content,str) or not 1<=len(content)<=1200:raise SceneError('contenu de parole invalide',code='invalid_scene')
  recipient_key=None if recipient_key is None else _key(recipient_key,'destinataire'); payload={} if payload is None else _obj(payload,'payload')
  speaker=self._character(wid,speaker_key); recipient=None if recipient_key is None else self._character(wid,recipient_key); now=self._clock.now_iso()
  with transaction(self._conn) as c:
   scene=self._scene(wid,scene_key)
   if scene['status']!='active':raise SceneError('scène fermée',code='scene_not_active')
   ids={row['character_id'] for row in c.execute('SELECT character_id FROM social_scene_participant WHERE scene_id=?',(scene['id'],)).fetchall()}
   if speaker['id'] not in ids or (recipient is not None and recipient['id'] not in ids):raise SceneError('locutrice ou destinataire hors scène',code='speech_participant_not_in_scene')
   existing=c.execute('SELECT * FROM social_speech_act WHERE scene_id=? AND act_key=?',(scene['id'],act_key)).fetchone()
   if existing is not None:return self._act_sheet(existing)
   cur=c.execute('INSERT INTO social_speech_act (public_id,scene_id,speaker_character_id,recipient_character_id,act_key,act_kind,content_text,payload_json,spoken_at) VALUES (?,?,?,?,?,?,?,?,?)',(new_uuid(),scene['id'],speaker['id'],None if recipient is None else recipient['id'],act_key,act_kind,content,_json(payload),now))
   c.execute("INSERT INTO social_scene_event (scene_id,event_type,payload_json,recorded_at) VALUES (?, 'speech_recorded',?,?)",(scene['id'],_json({'act_key':act_key,'act_kind':act_kind}),now))
  return self._act_sheet(self._conn.execute('SELECT * FROM social_speech_act WHERE id=?',(cur.lastrowid,)).fetchone())
 @staticmethod
 def _act_sheet(row:sqlite3.Row)->dict[str,Any]:return {'act_key':row['act_key'],'act_kind':row['act_kind'],'content':row['content_text'],'payload':json.loads(row['payload_json'])}
 def close(self,wid:Any,scene_key:Any,*,reason:Any='completed',interrupted:bool=False)->dict[str,Any]:
  if not isinstance(wid,int) or isinstance(wid,bool) or wid<1:raise SceneError('monde invalide',code='invalid_scene')
  scene_key,reason=_key(scene_key,'scène'),_key(reason,'raison');now=self._clock.now_iso()
  with transaction(self._conn) as c:
   scene=self._scene(wid,scene_key)
   if scene['status']=='active':
    status,event=('interrupted','scene_interrupted') if interrupted else ('closed','scene_closed')
    c.execute('UPDATE social_scene SET status=?,closed_at=?,close_reason=? WHERE id=?',(status,now,reason,scene['id']))
    c.execute('INSERT INTO social_scene_event (scene_id,event_type,payload_json,recorded_at) VALUES (?,?,?,?)',(scene['id'],event,_json({'reason':reason}),now))
  return self.sheet(wid,scene_key)
 def interrupt_active(self,wid:Any,*,reason:Any='service_restart')->int:
  if not isinstance(wid,int) or isinstance(wid,bool) or wid<1:raise SceneError('monde invalide',code='invalid_scene')
  rows=self._conn.execute("SELECT scene_key FROM social_scene WHERE world_id=? AND status='active'",(wid,)).fetchall()
  for row in rows:self.close(wid,row['scene_key'],reason=reason,interrupted=True)
  return len(rows)
 def sheet(self,wid:Any,scene_key:Any)->dict[str,Any]:
  scene=self._scene(wid,_key(scene_key,'scène'))
  participants=tuple(row['key'] for row in self._conn.execute('SELECT ch.key FROM social_scene_participant p JOIN character ch ON ch.id=p.character_id WHERE p.scene_id=? ORDER BY p.id',(scene['id'],)).fetchall())
  acts=tuple(self._act_sheet(row) for row in self._conn.execute('SELECT * FROM social_speech_act WHERE scene_id=? ORDER BY id',(scene['id'],)).fetchall())
  return {'scene_key':scene['scene_key'],'status':scene['status'],'participants':participants,'acts':acts,'close_reason':scene['close_reason']}
