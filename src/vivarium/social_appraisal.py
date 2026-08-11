"""Owner persistant SCC-2A : appraisal prive et candidates sans mutation."""
from __future__ import annotations
import json, re, sqlite3
from typing import Any, Mapping
from .db import transaction
from .registry import _KEY_RE
from .util import Clock, new_uuid

STATUSES = frozenset({'relevant','not_relevant','ambiguous','unresolved'})
MEANINGS = frozenset({'favorable','defavorable','mixed','neutral','uncertain'})
IMPORTANCE = frozenset({'low','moderate','high','uncertain'})
DOMAINS = frozenset({'affect','belief','relationship','goal_or_intention','memory'})
_FP = re.compile(r'^[0-9a-f]{64}$')
_FORBIDDEN = re.compile(
    r'(?:\b(?:delta|trust)\s*=|\bset_[a-z][a-z0-9_]*\b|'
    r'\b(?:elle|il|[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ-]*)\s+'
    r'(?:voulait|veut|ment|manipuler|est\s+(?:jalouse?|coupable))\b|'
    r'\b(?:son|sa)\s+intention\s+cach[ée]e\b|\bmotif\s+(?:cach[ée]|invente)\b)',
    re.I,
)

def validate_appraisal_structure(proposal: Mapping[str, Any], allowed_refs: set[str], *, error_code: str) -> dict[str, Any]:
    if (not isinstance(proposal, dict) or set(proposal) != {'schema_version','appraisal_status','qualitative_meaning','importance','bases','candidates'} or proposal['schema_version'] != 1 or proposal['appraisal_status'] not in STATUSES or proposal['qualitative_meaning'] not in MEANINGS or proposal['importance'] not in IMPORTANCE or not isinstance(proposal['bases'], list) or not isinstance(proposal['candidates'], list)):
        raise SocialAppraisalError('sortie appraisal hors contrat', code=error_code)
    bases=proposal['bases']
    if len(bases)>16 or any(not isinstance(item,str) or not 1<=len(item)<=120 or item not in allowed_refs for item in bases) or len(set(bases))!=len(bases):
        raise SocialAppraisalError('bases invalides', code=error_code)
    status=proposal['appraisal_status']
    if status=='unresolved' and (proposal['qualitative_meaning']!='uncertain' or proposal['importance']!='uncertain' or bases):
        raise SocialAppraisalError('unresolved doit rester sans lecture precise', code=error_code)
    candidates=proposal['candidates']
    if (status=='not_relevant' and candidates) or (status=='relevant' and not bases) or len(candidates)>8:
        raise SocialAppraisalError('coherence appraisal invalide', code=error_code)
    seen=set(); allowed_bases=set(bases)
    for candidate in candidates:
        if not isinstance(candidate,dict) or set(candidate)!={'candidate_key','domain','basis_refs','justification'}:
            raise SocialAppraisalError('candidate hors contrat', code=error_code)
        candidate_key=candidate['candidate_key']
        if not isinstance(candidate_key,str) or not _KEY_RE.fullmatch(candidate_key) or candidate_key in seen or candidate['domain'] not in DOMAINS:
            raise SocialAppraisalError('candidate invalide', code=error_code)
        refs=candidate['basis_refs']
        if not isinstance(refs,list) or not refs or any(not isinstance(ref,str) or ref not in allowed_bases for ref in refs) or len(set(refs))!=len(refs):
            raise SocialAppraisalError('support candidate invalide', code=error_code)
        text=candidate['justification']
        if not isinstance(text,str) or not 1<=len(text.strip())<=280 or _FORBIDDEN.search(text):
            raise SocialAppraisalError('justification hors frontiere SCC-2A', code=error_code)
        seen.add(candidate_key)
    return proposal

class SocialAppraisalError(ValueError):
    def __init__(self, message: str, *, code: str): super().__init__(message); self.code = code
def _j(v: Any) -> str: return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
def _key(v: Any, label: str) -> str:
    if not isinstance(v, str) or not _KEY_RE.fullmatch(v): raise SocialAppraisalError(f'{label} invalide', code='invalid_appraisal')
    return v

class SocialAppraisalService:
    """Seul proprietaire des appraisals et candidates SCC-2A."""
    def __init__(self, conn: sqlite3.Connection, clock: Clock|None=None): self._conn,self._clock=conn,clock or Clock()
    def _owner(self,wid:int,key:str)->int:
        row=self._conn.execute('SELECT id FROM character WHERE world_id=? AND key=?',(wid,key)).fetchone()
        if row is None: raise SocialAppraisalError('proprietaire introuvable',code='character_not_found')
        return row['id']
    def create(self, wid:int, owner:str, appraisal_key:str, source_interpretation_key:str, *, appraisal_status:str, qualitative_meaning:str, importance:str, bases:Any, candidates:Any=(), technical_provenance:Mapping[str,Any]|None=None)->dict[str,Any]:
        if not isinstance(wid,int) or isinstance(wid,bool) or wid<1: raise SocialAppraisalError('monde invalide',code='invalid_appraisal')
        owner,appraisal_key,source_interpretation_key=(_key(owner,'proprietaire'),_key(appraisal_key,'appraisal'),_key(source_interpretation_key,'interpretation'))
        proposal=validate_appraisal_structure({'schema_version':1,'appraisal_status':appraisal_status,'qualitative_meaning':qualitative_meaning,'importance':importance,'bases':list(bases) if isinstance(bases,(list,tuple)) else bases,'candidates':list(candidates) if isinstance(candidates,(list,tuple)) else candidates},{item for item in bases if isinstance(item,str)} if isinstance(bases,(list,tuple)) else set(),error_code='invalid_appraisal')
        bases=tuple(proposal['bases'])
        clean=[{'candidate_key':c['candidate_key'],'domain':c['domain'],'basis_refs':tuple(c['basis_refs']),'justification':c['justification'].strip()} for c in proposal['candidates']]
        p=dict(technical_provenance or {}); expected={'origin_kind','model_id','provider_version','snapshot_fingerprint','provider_turn_id'}
        if set(p)!=expected or p['origin_kind'] not in {'llm','direct_controlled'} or not all(isinstance(p[k],str) and p[k].strip() for k in ('model_id','provider_version')) or not isinstance(p['snapshot_fingerprint'],str) or not _FP.fullmatch(p['snapshot_fingerprint']): raise SocialAppraisalError('provenance invalide',code='invalid_appraisal')
        if p['provider_turn_id'] is not None and (not isinstance(p['provider_turn_id'],str) or not p['provider_turn_id']): raise SocialAppraisalError('tour provider invalide',code='invalid_appraisal')
        cid=self._owner(wid,owner)
        source=self._conn.execute('SELECT id FROM social_interpretation WHERE world_id=? AND character_id=? AND interpretation_key=?',(wid,cid,source_interpretation_key)).fetchone()
        if source is None: raise SocialAppraisalError('interpretation source inaccessible',code='source_not_accessible')
        existing=self._conn.execute('SELECT id FROM social_appraisal WHERE world_id=? AND character_id=? AND appraisal_key=?',(wid,cid,appraisal_key)).fetchone()
        if existing is not None:
            row=self.get(wid,owner,appraisal_key)
            if row['source_interpretation_key']!=source_interpretation_key or row['snapshot_fingerprint']!=p['snapshot_fingerprint']: raise SocialAppraisalError('cle appraisal deja utilisee',code='appraisal_key_conflict')
            return row
        now=self._clock.now_iso()
        with transaction(self._conn) as c:
            cur=c.execute('INSERT INTO social_appraisal (public_id,world_id,character_id,source_interpretation_id,appraisal_key,appraisal_status,qualitative_meaning,importance,bases_json,origin_kind,model_id,provider_version,snapshot_fingerprint,provider_turn_id,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(new_uuid(),wid,cid,source['id'],appraisal_key,appraisal_status,qualitative_meaning,importance,_j(bases),p['origin_kind'],p['model_id'],p['provider_version'],p['snapshot_fingerprint'],p['provider_turn_id'],now))
            aid=cur.lastrowid
            for item in clean: c.execute('INSERT INTO social_appraisal_candidate (public_id,world_id,character_id,appraisal_id,candidate_key,domain,basis_refs_json,justification,created_at) VALUES (?,?,?,?,?,?,?,?,?)',(new_uuid(),wid,cid,aid,item['candidate_key'],item['domain'],_j(item['basis_refs']),item['justification'],now))
            c.execute('INSERT INTO social_appraisal_event (public_id,world_id,character_id,appraisal_id,event_type,payload_json,recorded_at) VALUES (?,?,?,?,?,?,?)',(new_uuid(),wid,cid,aid,'appraisal_created',_j({'appraisal_key':appraisal_key,'source_interpretation_key':source_interpretation_key,'candidate_count':len(clean)}),now))
        return self.get(wid,owner,appraisal_key)
    def get(self,wid:int,owner:str,appraisal_key:str)->dict[str,Any]:
        cid=self._owner(wid,_key(owner,'proprietaire')); row=self._conn.execute('SELECT a.*,i.interpretation_key AS source_interpretation_key FROM social_appraisal a JOIN social_interpretation i ON i.id=a.source_interpretation_id WHERE a.world_id=? AND a.character_id=? AND a.appraisal_key=?',(wid,cid,appraisal_key)).fetchone()
        if row is None: raise SocialAppraisalError('appraisal introuvable',code='appraisal_not_found')
        cs=self._conn.execute('SELECT candidate_key,domain,basis_refs_json,justification FROM social_appraisal_candidate WHERE appraisal_id=? ORDER BY id',(row['id'],)).fetchall()
        return {'public_id':row['public_id'],'appraisal_key':row['appraisal_key'],'world_id':wid,'character_key':owner,'source_interpretation_key':row['source_interpretation_key'],'appraisal_status':row['appraisal_status'],'qualitative_meaning':row['qualitative_meaning'],'importance':row['importance'],'bases':tuple(json.loads(row['bases_json'])),'candidates':tuple({'candidate_key':c['candidate_key'],'domain':c['domain'],'basis_refs':tuple(json.loads(c['basis_refs_json'])),'justification':c['justification']} for c in cs),'origin_kind':row['origin_kind'],'model_id':row['model_id'],'provider_version':row['provider_version'],'snapshot_fingerprint':row['snapshot_fingerprint'],'provider_turn_id':row['provider_turn_id'],'created_at':row['created_at']}
