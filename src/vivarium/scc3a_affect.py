"""SCC-3A : examen owner-governed d'une candidate affect uniquement."""
from __future__ import annotations
import json, re, sqlite3
from typing import Any, Mapping
from .affect import AffectError, AffectService
from .db import transaction
from .registry import _KEY_RE
from .util import Clock, new_uuid

FAMILIES=frozenset({'joy','relief','sadness','anger','fear','shame','guilt','affection'})
INTENSITIES=frozenset({'low','moderate','high'})
DECISIONS=frozenset({'no_change','start_episode'})
INTENSITY_MILLI={'low':200,'moderate':500,'high':800}
_FP=re.compile(r'^[0-9a-f]{64}$')
_FORBIDDEN=re.compile(r'(voulait|veut|intention|motif|jalou|manipul|mentir|personnalit|sinc[eè]re|coupable|blesser|confronter|fuir|agir|action)',re.I)

class SCC3AAffectError(ValueError):
    def __init__(self,message:str,*,code:str): super().__init__(message); self.code=code
def _j(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def _key(v,label):
    if not isinstance(v,str) or not _KEY_RE.fullmatch(v): raise SCC3AAffectError(f'{label} invalide',code='invalid_scc3a')
    return v

class SCC3AAffectService:
    """Proprietaire de la decision SCC-3A; AffectService reste owner des episodes."""
    def __init__(self,conn:sqlite3.Connection,clock:Clock|None=None): self.conn,self.clock=conn,clock or Clock()
    def _candidate(self,wid:int,owner:str,candidate_key:str):
        if isinstance(candidate_key,int):
            return self.conn.execute("SELECT c.*,a.appraisal_status,a.qualitative_meaning,a.importance,a.bases_json,a.snapshot_fingerprint,a.source_interpretation_id,i.interpretation_key,t.request_key,sp.key AS speaker_key,rp.key AS recipient_key FROM social_appraisal_candidate c JOIN social_appraisal a ON a.id=c.appraisal_id JOIN social_interpretation i ON i.id=a.source_interpretation_id JOIN subjective_trace t ON t.id=i.source_trace_id JOIN social_speech_act act ON act.id=t.source_social_speech_act_id JOIN character sp ON sp.id=act.speaker_character_id JOIN character rp ON rp.id=act.recipient_character_id JOIN character owner ON owner.id=c.character_id WHERE c.world_id=? AND owner.key=? AND c.id=? AND c.domain='affect'",(wid,owner,candidate_key)).fetchone()
        return self.conn.execute("SELECT c.*,a.appraisal_status,a.qualitative_meaning,a.importance,a.bases_json,a.snapshot_fingerprint,a.source_interpretation_id,i.interpretation_key,t.request_key,sp.key AS speaker_key,rp.key AS recipient_key FROM social_appraisal_candidate c JOIN social_appraisal a ON a.id=c.appraisal_id JOIN social_interpretation i ON i.id=a.source_interpretation_id JOIN subjective_trace t ON t.id=i.source_trace_id JOIN social_speech_act act ON act.id=t.source_social_speech_act_id JOIN character sp ON sp.id=act.speaker_character_id JOIN character rp ON rp.id=act.recipient_character_id JOIN character owner ON owner.id=c.character_id WHERE c.world_id=? AND owner.key=? AND c.candidate_key=? AND c.domain='affect'",(wid,owner,candidate_key)).fetchone()
    def _validate_provenance(self,p:Mapping[str,Any]):
        if set(p)!={'model_id','provider_version','snapshot_fingerprint','provider_turn_id'} or not all(isinstance(p[k],str) and p[k].strip() for k in ('model_id','provider_version')) or not isinstance(p['snapshot_fingerprint'],str) or not _FP.fullmatch(p['snapshot_fingerprint']): raise SCC3AAffectError('provenance SCC-3A invalide',code='invalid_scc3a')
    def decide(self,wid:int,owner:str,candidate_key:str,*,decision:str,family:str|None=None,qualitative_intensity:str|None=None,target_ref:str|None=None,support_refs:Any=(),provenance:Mapping[str,Any],decision_key:str|None=None)->dict[str,Any]:
        owner=_key(owner,'proprietaire'); candidate_id=candidate_key if isinstance(candidate_key,int) else None; candidate_key=_key(candidate_key,'candidate') if candidate_id is None else candidate_key; row=self._candidate(wid,owner,candidate_id if candidate_id is not None else candidate_key)
        if row is None: raise SCC3AAffectError('candidate affect inaccessible',code='candidate_not_found')
        candidate_bases=json.loads(row['basis_refs_json']); appraisal_bases=json.loads(row['bases_json'])
        if not candidate_bases or len(set(candidate_bases)) != len(candidate_bases) or not set(candidate_bases) <= set(appraisal_bases):
            raise SCC3AAffectError('bases candidate invalides',code='invalid_scc3a')
        if decision not in DECISIONS: raise SCC3AAffectError('decision affective invalide',code='invalid_scc3a')
        if decision=='no_change':
            if any(x is not None for x in (family,qualitative_intensity,target_ref)) or support_refs: raise SCC3AAffectError('no_change doit rester vide',code='invalid_scc3a')
        else:
            if family not in FAMILIES or qualitative_intensity not in INTENSITIES or not isinstance(support_refs,(list,tuple)) or not support_refs or any(not isinstance(x,str) for x in support_refs): raise SCC3AAffectError('proposition affective incomplete',code='invalid_scc3a')
            if _FORBIDDEN.search(' '.join(str(x) for x in support_refs)): raise SCC3AAffectError('psychologisation interdite',code='invalid_scc3a')
            if target_ref is not None and target_ref not in {row['speaker_key'],row['recipient_key']}: raise SCC3AAffectError('cible hors allowlist',code='invalid_scc3a')
            allowed={'candidate:primary','appraisal:primary','interpretation:primary','trace:primary'}
            if any(x not in allowed for x in support_refs): raise SCC3AAffectError('support hors snapshot',code='invalid_scc3a')
        self._validate_provenance(provenance); decision_key=_key(decision_key or f'scc3a_{row["id"]}','decision')
        existing=self.conn.execute('SELECT * FROM scc3a_decision WHERE world_id=? AND character_id=? AND candidate_id=?',(wid,row['character_id'],row['id'])).fetchone()
        if existing is not None: return self.get_decision(existing['id'])
        candidate_key=row['candidate_key']; episode_key=None
        if decision=='start_episode':
            episode_key=f'scc3a_episode_{row["id"]}'
            appraisal={'scc3a_decision':decision,'candidate_key':candidate_key,'appraisal_status':row['appraisal_status'],'qualitative_meaning':row['qualitative_meaning'],'importance':row['importance'],'support_refs':list(support_refs)}
            try:
                AffectService(self.conn,clock=self.clock).start_episode(wid,owner,episode_key,family=family,appraisal=appraisal,cause_trace_key=row['request_key'],intensity_milli=INTENSITY_MILLI[qualitative_intensity],action_tendency='none',expression_milli=0,target_character_key=target_ref)
            except AffectError as exc: raise SCC3AAffectError(str(exc),code=getattr(exc,'code','affect_failed')) from exc
        now=self.clock.now_iso()
        with transaction(self.conn) as conn:
            cur=conn.execute('INSERT INTO scc3a_decision (public_id,world_id,character_id,candidate_id,decision_key,decision,episode_key,detail_code,provider_model_id,provider_version,snapshot_fingerprint,provider_turn_id,recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',(new_uuid(),wid,row['character_id'],row['id'],decision_key,decision,episode_key,None,provenance['model_id'],provenance['provider_version'],provenance['snapshot_fingerprint'],provenance['provider_turn_id'],now))
            decision_id=cur.lastrowid
        return self.get_decision(decision_id)
    def get_decision(self,decision_id:int)->dict[str,Any]:
        row=self.conn.execute('SELECT d.*,c.candidate_key FROM scc3a_decision d JOIN social_appraisal_candidate c ON c.id=d.candidate_id WHERE d.id=?',(decision_id,)).fetchone(); assert row is not None
        return {k:row[k] for k in ('public_id','decision_key','decision','episode_key','detail_code','provider_model_id','provider_version','snapshot_fingerprint','provider_turn_id','recorded_at','candidate_key')}
