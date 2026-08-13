"""Hugin/Munin V0: lecture humaine privilegiee, bornee et sans ecriture.

Ce module est un read-model moteur. Il ne planifie pas de requete LLM et ne
persiste aucun rapport. Hugin expose uniquement des lignes canoniques etablies;
Munin expose uniquement les etats subjectifs effectivement persistes, repartis
par proprietaire. Le texte narratif est une projection deterministe du rapport
structure.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from typing import Any, Literal

from .sleep_physiology import SleepPhysiologyService
from .util import parse_iso
from .world import WorldEngine

Mode = Literal["hugin", "munin", "both"]
Focus = Literal["events", "conversation", "subjective_state", "causal_chain", "comparison", "current_state"]
_KEY = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_MODES = {"hugin", "munin", "both"}
_FOCUSES = {"events", "conversation", "subjective_state", "causal_chain", "comparison", "current_state"}


class ObservationError(ValueError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ObservationQuery:
    mode: Mode = "both"
    subject_keys: tuple[str, ...] = ()
    focus: Focus = "events"
    start_at: str | None = None
    end_at: str | None = None
    location_key: str | None = None
    max_events: int = 50
    max_items_per_owner: int = 50

    def __post_init__(self) -> None:
        if self.mode not in _MODES or self.focus not in _FOCUSES:
            raise ObservationError("mode ou focus d'observation invalide", code="invalid_observation_query")
        if self.mode in {"munin", "both"} and not self.subject_keys:
            raise ObservationError("Munin exige des proprietaires explicites", code="subject_scope_required")
        if len(self.subject_keys) > 8 or len(set(self.subject_keys)) != len(self.subject_keys):
            raise ObservationError("portee de proprietaires invalide", code="invalid_observation_query")
        if any(not isinstance(k, str) or not _KEY.fullmatch(k) for k in self.subject_keys):
            raise ObservationError("cle de proprietaire invalide", code="invalid_observation_query")
        if self.start_at is not None:
            parse_iso(self.start_at)
        if self.end_at is not None:
            parse_iso(self.end_at)
        if self.start_at and self.end_at and parse_iso(self.start_at) > parse_iso(self.end_at):
            raise ObservationError("fenetre temporelle inverse", code="invalid_observation_query")
        if not isinstance(self.max_events, int) or not 1 <= self.max_events <= 100:
            raise ObservationError("borne d'evenements invalide", code="invalid_observation_query")
        if not isinstance(self.max_items_per_owner, int) or not 1 <= self.max_items_per_owner <= 100:
            raise ObservationError("borne subjective invalide", code="invalid_observation_query")


def _json(value: Any) -> Any:
    try:
        return json.loads(value) if isinstance(value, str) else value
    except (TypeError, ValueError):
        return {"invalid_json": True}


def _fingerprint(value: Any) -> str:
    wire = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(wire.encode("utf-8")).hexdigest()


class HuginMuninObservationService:
    """Construit des rapports bornes depuis des SELECT valides uniquement."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def _world(self, world_id: int) -> sqlite3.Row:
        row = self.conn.execute("SELECT id, public_id, name, status FROM worlds WHERE id=?", (world_id,)).fetchone()
        if row is None:
            raise ObservationError("monde introuvable", code="world_not_found")
        return row

    def _owners(self, world_id: int, keys: tuple[str, ...]) -> dict[str, int]:
        if not keys:
            return {}
        marks = ",".join("?" for _ in keys)
        rows = self.conn.execute(
            f"SELECT key,id FROM character WHERE world_id=? AND key IN ({marks})", (world_id, *keys)
        ).fetchall()
        result = {row["key"]: row["id"] for row in rows}
        if len(result) != len(keys):
            raise ObservationError("proprietaire introuvable dans le monde", code="character_not_found")
        return result

    @staticmethod
    def _evidence(ref: str, kind: str, layer: str, owner: str | None, data: dict[str, Any]) -> dict[str, Any]:
        return {"ref": ref, "kind": kind, "layer": layer, "owner": owner, "data": data}

    @staticmethod
    def _claim(key: str, layer: str, owner: str | None, text: str, uncertainty: str, refs: list[str]) -> dict[str, Any]:
        return {"claim_key": key, "layer": layer, "owner": owner, "text": text,
                "uncertainty": uncertainty, "evidence_refs": refs}

    def _window(self, column: str, query: ObservationQuery) -> tuple[str, list[Any]]:
        clauses = [f"{column} >= ?"] if query.start_at else []
        args: list[Any] = [query.start_at] if query.start_at else []
        if query.end_at:
            clauses.append(f"{column} <= ?")
            args.append(query.end_at)
        return (" AND ".join(clauses) if clauses else "1=1"), args

    def _hugin(self, world_id: int, query: ObservationQuery) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
        evidence: list[dict[str, Any]] = []
        claims: list[dict[str, Any]] = []
        where, args = self._window("e.occurred_at", query)
        events = self.conn.execute(
            f"SELECT e.public_id,e.seq,e.occurred_at,e.source_kind,e.event_type,e.payload "
            f"FROM canonical_event e WHERE e.world_id=? AND {where} ORDER BY e.seq LIMIT ?",
            (world_id, *args, query.max_events),
        ).fetchall()
        speech_where, speech_args = self._window("a.spoken_at", query)
        speeches = self.conn.execute(
            f"SELECT a.public_id,a.act_kind,a.content_text,a.spoken_at,s.key AS speaker,r.key AS recipient "
            f"FROM social_speech_act a JOIN character s ON s.id=a.speaker_character_id "
            f"LEFT JOIN character r ON r.id=a.recipient_character_id "
            f"JOIN social_scene sc ON sc.id=a.scene_id WHERE sc.world_id=? AND {speech_where} "
            "ORDER BY a.spoken_at,a.id LIMIT ?", (world_id, *speech_args, query.max_events),
        ).fetchall()
        if query.focus in {"events", "comparison"}:
            for row in events:
                ref = f"canonical_event:{row['public_id']}"
                data = {"seq": row["seq"], "occurred_at": row["occurred_at"], "source_kind": row["source_kind"],
                        "event_type": row["event_type"], "payload": _json(row["payload"])}
                evidence.append(self._evidence(ref, "canonical_event", "canon", None, data))
                claims.append(self._claim(f"canon:{row['seq']}", "canon", None,
                    f"Evenement canonique {row['event_type']} (seq {row['seq']}).", "established", [ref]))
        if query.focus in {"events", "conversation", "comparison"}:
            for row in speeches:
                ref = f"social_speech_act:{row['public_id']}"
                data = {"spoken_at": row["spoken_at"], "speaker": row["speaker"], "recipient": row["recipient"],
                        "act_kind": row["act_kind"], "content_text": row["content_text"]}
                evidence.append(self._evidence(ref, "social_speech_act", "canon", None, data))
                addressee = f" a {row['recipient']}" if row["recipient"] else ""
                claims.append(self._claim(f"speech:{row['public_id']}", "canon", None,
                    f"{row['speaker']} a parle{addressee}: {row['content_text']}", "established", [ref]))
        truncated = len(events) >= query.max_events or len(speeches) >= query.max_events
        return claims, evidence, truncated

    def _current_state(self, world_id: int, query: ObservationQuery) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
        claims: list[dict[str, Any]] = []
        evidence: list[dict[str, Any]] = []
        params: list[Any] = [world_id]
        clauses = ["ch.world_id=?"]
        if query.subject_keys:
            marks = ",".join("?" for _ in query.subject_keys)
            clauses.append(f"ch.key IN ({marks})")
            params.extend(query.subject_keys)
        if query.location_key is not None:
            clauses.append("l.key=?")
            params.append(query.location_key)
        rows = self.conn.execute(
            "SELECT ch.key,ch.name,l.key AS location_key,l.name AS location_name, "
            "(SELECT a.type FROM activity a WHERE a.world_id=ch.world_id AND a.character_id=ch.id AND a.status='active' ORDER BY a.id DESC LIMIT 1) AS activity_type, "
            "(SELECT a.started_at FROM activity a WHERE a.world_id=ch.world_id AND a.character_id=ch.id AND a.status='active' ORDER BY a.id DESC LIMIT 1) AS activity_started_at "
            "FROM character ch JOIN location l ON l.id=ch.current_location_id WHERE " + " AND ".join(clauses) + " ORDER BY ch.key",
            tuple(params),
        ).fetchall()
        now = WorldEngine(self.conn).read_canonical_time(world_id)
        system_row = self.conn.execute(
            "SELECT status FROM world_physiology_system WHERE world_id=?", (world_id,)
        ).fetchone()
        physiology_status = "inactive" if system_row is None else system_row["status"]
        physiology_service = SleepPhysiologyService(self.conn) if physiology_status == "active" else None
        for row in rows:
            ref = f"current_character:{row['key']}"
            last_move = self.conn.execute(
                "SELECT e.public_id,e.occurred_at FROM canonical_event e WHERE e.world_id=? AND e.event_type='character_moved' "
                "AND json_extract(e.payload,'$.character')=? AND json_extract(e.payload,'$.to')=? ORDER BY e.seq DESC LIMIT 1",
                (world_id, row["key"], row["location_key"]),
            ).fetchone()
            duration_seconds = None
            if last_move is not None:
                duration_seconds = max(0, int((parse_iso(now) - parse_iso(last_move["occurred_at"])).total_seconds()))
            physiology = {
                "status": physiology_status,
                "canonical_now": now,
                "wake_sleep_state": "sleep" if row["activity_type"] == "sleep" else "wake",
                "persisted": None,
                "projection": None,
                "projection_evaluated_at": None,
                "projection_policy": "not_extrapolated_by_read_model",
            }
            if physiology_service is not None:
                state = physiology_service.read_state(world_id, row["key"])
                physiology["persisted"] = {
                    "model_key": state.model_key,
                    "model_version": state.model_version,
                    "anchor_at": state.anchor_at,
                    "homeostatic_load_milli": state.regulation.homeostatic_load_milli,
                    "circadian_phase_milli": state.regulation.circadian_phase_milli,
                    "physical_capacity_milli": state.regulation.physical_capacity_milli,
                    "previous_stability_band": state.hysteresis.previous_band,
                }
            data = {"character_key": row["key"], "name": row["name"], "location_key": row["location_key"],
                    "location_name": row["location_name"], "activity_type": row["activity_type"],
                    "activity_started_at": row["activity_started_at"], "canonical_now": now,
                    "duration_seconds": duration_seconds, "physiology": physiology,
                    "last_transition": None if last_move is None else {"public_id": last_move["public_id"], "occurred_at": last_move["occurred_at"]}}
            evidence.append(self._evidence(ref, "current_canonical_state", "canon", None, data))
            activity = f"; activite courante: {row['activity_type']}" if row["activity_type"] else ""
            duration = (f"; present depuis {duration_seconds} secondes au minimum" if duration_seconds is not None
                        else "; duree de presence non etablissable")
            claims.append(self._claim(f"current:{row['key']}", "canon", None,
                f"{row['name']} ({row['key']}) est actuellement a {row['location_name']} ({row['location_key']}){activity}{duration}.",
                "established", [ref]))
        if query.location_key is not None and not rows:
            claims.append(self._claim("current:empty", "canon", None,
                f"Aucun personnage canonique n'est actuellement observe a {query.location_key}.", "not_observed", []))
        return claims, evidence, False

    def _munin(self, world_id: int, query: ObservationQuery, owners: dict[str, int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
        claims: list[dict[str, Any]] = []
        evidence: list[dict[str, Any]] = []
        truncated = False
        for owner, character_id in owners.items():
            limit = query.max_items_per_owner
            if query.focus in {"subjective_state", "comparison"}:
                mood = self.conn.execute(
                    "SELECT valence_milli,activation_milli,updated_at FROM mood_state WHERE world_id=? AND character_id=?",
                    (world_id, character_id),
                ).fetchone()
                if mood is not None:
                    ref = f"mood:{owner}"
                    evidence.append(self._evidence(ref, "mood_state", "subjective", owner,
                        {"valence_milli": mood["valence_milli"], "activation_milli": mood["activation_milli"], "updated_at": mood["updated_at"]}))
                    claims.append(self._claim(f"mood:{owner}", "mood", owner,
                        f"L'humeur persistante de {owner} est disponible comme etat prive.", "subjective", [ref]))
                beliefs = self.conn.execute(
                    "SELECT public_id,belief_key,proposition_json,polarity,confidence_milli,status FROM subjective_belief "
                    "WHERE world_id=? AND character_id=? ORDER BY id LIMIT ?", (world_id, character_id, limit),
                ).fetchall()
                for belief in beliefs:
                    ref = f"belief:{belief['public_id']}"
                    evidence.append(self._evidence(ref, "subjective_belief", "subjective", owner,
                        {"belief_key": belief["belief_key"], "proposition": _json(belief["proposition_json"]), "polarity": belief["polarity"], "confidence_milli": belief["confidence_milli"], "status": belief["status"]}))
                    claims.append(self._claim(f"belief:{belief['public_id']}", "belief", owner,
                        f"{owner} croit subjectivement la proposition {belief['belief_key']} ({belief['polarity']}).", "subjective", [ref]))
                goals = self.conn.execute(
                    "SELECT goal_key,family,target_json,status,importance_milli,urgency_milli FROM subjective_goal "
                    "WHERE world_id=? AND character_id=? ORDER BY id LIMIT ?", (world_id, character_id, limit),
                ).fetchall()
                for goal in goals:
                    ref = f"goal:{owner}:{goal['goal_key']}"
                    evidence.append(self._evidence(ref, "subjective_goal", "subjective", owner,
                        {"goal_key": goal["goal_key"], "family": goal["family"], "target": _json(goal["target_json"]), "status": goal["status"], "importance_milli": goal["importance_milli"], "urgency_milli": goal["urgency_milli"]}))
                    claims.append(self._claim(f"goal:{owner}:{goal['goal_key']}", "goal", owner,
                        f"{owner} a un objectif subjectif {goal['goal_key']} ({goal['status']}).", "subjective", [ref]))
            where, args = self._window("t.encoded_at", query)
            traces = self.conn.execute(
                f"SELECT t.public_id,t.request_key,t.encoded_at,t.fidelity,t.access_kind,a.public_id AS act_public,a.content_text,a.act_kind,s.key AS speaker,r.key AS recipient "
                f"FROM subjective_trace t JOIN social_speech_act a ON a.id=t.source_social_speech_act_id "
                f"JOIN character s ON s.id=a.speaker_character_id LEFT JOIN character r ON r.id=a.recipient_character_id "
                f"WHERE t.world_id=? AND t.character_id=? AND {where} ORDER BY t.encoded_at,t.id LIMIT ?",
                (world_id, character_id, *args, limit),
            ).fetchall()
            if len(traces) >= limit:
                truncated = True
            if not traces:
                claims.append(self._claim(f"munin:{owner}:empty", "subjective", owner,
                    f"Aucune donnee subjective persistee disponible pour {owner} dans ce scope.", "not_observed", []))
            for t in traces:
                tref = f"subjective_trace:{t['public_id']}"
                aref = f"social_speech_act:{t['act_public']}"
                evidence.extend([
                    self._evidence(tref, "subjective_trace", "subjective", owner,
                        {"request_key": t["request_key"], "encoded_at": t["encoded_at"], "fidelity": t["fidelity"], "access_kind": t["access_kind"]}),
                    self._evidence(aref, "social_speech_act", "canon", None,
                        {"speaker": t["speaker"], "recipient": t["recipient"], "act_kind": t["act_kind"], "content_text": t["content_text"]}),
                ])
                claims.append(self._claim(f"trace:{t['public_id']}", "trace", owner,
                    f"{owner} possede une trace subjective de la parole de {t['speaker']}.", "subjective", [tref, aref]))
                if query.focus not in {"subjective_state", "causal_chain", "comparison"}:
                    continue
                interpretations = self.conn.execute(
                    "SELECT i.public_id,i.interpretation_key,i.understanding_status,i.meaning_hypotheses_json "
                    "FROM social_interpretation i WHERE i.world_id=? AND i.character_id=? AND i.source_trace_id=? ORDER BY i.id",
                    (world_id, character_id, self.conn.execute("SELECT id FROM subjective_trace WHERE public_id=?", (t["public_id"],)).fetchone()["id"]),
                ).fetchall()
                if not interpretations:
                    claims.append(self._claim(f"interpretation:{t['public_id']}:empty", "subjective", owner,
                        f"Aucune interpretation persistante n'est disponible pour cette trace de {owner}.", "not_observed", [tref]))
                for i in interpretations:
                    iref = f"social_interpretation:{i['public_id']}"
                    evidence.append(self._evidence(iref, "social_interpretation", "subjective", owner,
                        {"status": i["understanding_status"], "meaning_hypotheses": _json(i["meaning_hypotheses_json"])}))
                    claims.append(self._claim(f"interpretation:{i['public_id']}", "interpretation", owner,
                        f"{owner} a une interpretation {i['understanding_status']} de cette parole.", "subjective", [iref, tref]))
                    appraisals = self.conn.execute(
                        "SELECT a.public_id,a.appraisal_key,a.appraisal_status,a.qualitative_meaning,a.importance "
                        "FROM social_appraisal a WHERE a.world_id=? AND a.character_id=? AND a.source_interpretation_id=? ORDER BY a.id",
                        (world_id, character_id, self.conn.execute("SELECT id FROM social_interpretation WHERE public_id=?", (i["public_id"],)).fetchone()["id"]),
                    ).fetchall()
                    for a in appraisals:
                        aref2 = f"social_appraisal:{a['public_id']}"
                        evidence.append(self._evidence(aref2, "social_appraisal", "subjective", owner,
                            {"status": a["appraisal_status"], "meaning": a["qualitative_meaning"], "importance": a["importance"]}))
                        claims.append(self._claim(f"appraisal:{a['public_id']}", "appraisal", owner,
                            f"{owner} appraise cette interpretation comme {a['appraisal_status']} ({a['qualitative_meaning']}, importance {a['importance']}).", "subjective", [aref2, iref]))
                        candidates = self.conn.execute(
                            "SELECT public_id,candidate_key,domain,justification FROM social_appraisal_candidate WHERE appraisal_id=(SELECT id FROM social_appraisal WHERE public_id=?) ORDER BY id",
                            (a["public_id"],),
                        ).fetchall()
                        for c in candidates:
                            cref = f"candidate:{c['public_id']}"
                            evidence.append(self._evidence(cref, "candidate", "technical", owner,
                                {"candidate_key": c["candidate_key"], "domain": c["domain"], "justification": c["justification"]}))
                            claims.append(self._claim(f"candidate:{c['public_id']}", "candidate", owner,
                                f"Une candidate {c['domain']} existe pour {owner}; elle n'est pas une mutation.", "proposed", [cref, aref2]))
                            if c["domain"] == "affect":
                                decisions = self.conn.execute(
                                    "SELECT public_id,decision,episode_key,detail_code FROM scc3a_decision WHERE candidate_id=(SELECT id FROM social_appraisal_candidate WHERE public_id=?) ORDER BY id",
                                    (c["public_id"],),
                                ).fetchall()
                                for d in decisions:
                                    dref = f"scc3a_decision:{d['public_id']}"
                                    evidence.append(self._evidence(dref, "scc3a_decision", "technical", owner,
                                        {"decision": d["decision"], "episode_key": d["episode_key"], "detail_code": d["detail_code"]}))
                                    claims.append(self._claim(f"decision:{d['public_id']}", "scc3a", owner,
                                        f"Le proprietaire affectif a rendu la decision {d['decision']}.", "subjective", [dref, cref]))
                                    if d["decision"] == "start_episode" and d["episode_key"]:
                                        episodes = self.conn.execute(
                                            "SELECT e.public_id,e.family,e.intensity_milli,e.status,t.key AS target_key FROM emotion_episode e LEFT JOIN character t ON t.id=e.target_character_id WHERE e.world_id=? AND e.character_id=? AND e.episode_key=?",
                                            (world_id, character_id, d["episode_key"]),
                                        ).fetchall()
                                        for e in episodes:
                                            eref = f"emotion_episode:{e['public_id']}"
                                            evidence.append(self._evidence(eref, "emotion_episode", "subjective", owner,
                                                {"family": e["family"], "intensity_milli": e["intensity_milli"], "status": e["status"], "target": e["target_key"]}))
                                            claims.append(self._claim(f"episode:{e['public_id']}", "emotion", owner,
                                                f"{owner} possede un episode affectif {e['family']} ({e['status']}).", "subjective", [eref, dref, tref]))
        return claims, evidence, truncated

    def report(self, world_id: int, query: ObservationQuery) -> dict[str, Any]:
        world = self._world(world_id)
        owners = self._owners(world_id, query.subject_keys)
        claims: list[dict[str, Any]] = []
        evidence: list[dict[str, Any]] = []
        truncated = False
        sections: dict[str, Any] = {}
        if query.mode in {"hugin", "both"}:
            if query.focus == "current_state":
                c, e, t = self._current_state(world_id, query)
            else:
                c, e, t = self._hugin(world_id, query)
            claims.extend(c); evidence.extend(e); truncated |= t
            sections["hugin"] = {"claims": c, "evidence_refs": [x["ref"] for x in e]}
        if query.mode in {"munin", "both"}:
            c, e, t = self._munin(world_id, query, owners); claims.extend(c); evidence.extend(e); truncated |= t
            sections["munin"] = {"claims": c, "evidence_refs": [x["ref"] for x in e]}
        structured = {"schema_version": 1, "mode": query.mode, "focus": query.focus, "world": dict(world),
                     "subjects": list(query.subject_keys), "claims": claims, "evidence": evidence,
                     "sections": sections, "bounds": {"max_events": query.max_events, "max_items_per_owner": query.max_items_per_owner,
                     "truncated": truncated}}
        structured["snapshot_fingerprint"] = _fingerprint(structured)
        structured["narrative"] = self._narrative(query, claims, truncated)
        return structured

    @staticmethod
    def _narrative(query: ObservationQuery, claims: list[dict[str, Any]], truncated: bool) -> str:
        canon = sum(c["layer"] == "canon" for c in claims)
        subjective = sum(c["layer"] in {"trace", "interpretation", "appraisal", "emotion"} for c in claims)
        suffix = " (scope tronque)" if truncated else ""
        if query.mode == "hugin":
            return f"Hugin: {canon} constat(s) canoniques etablis dans le scope{suffix}."
        if query.mode == "munin":
            return f"Munin: {subjective} constat(s) subjectifs persistes, repartis par proprietaire{suffix}."
        return f"Hugin/Munin: {canon} constat(s) canoniques et {subjective} constat(s) subjectifs{suffix}."


def observation_audit(report: dict[str, Any]) -> dict[str, Any]:
    """Audit deterministe non persiste du rapport deja produit."""
    refs = {e["ref"] for e in report.get("evidence", ())}
    missing = sorted({ref for c in report.get("claims", ()) for ref in c.get("evidence_refs", ()) if ref not in refs})
    return {"schema_version": 1, "snapshot_fingerprint": report.get("snapshot_fingerprint"),
            "claim_count": len(report.get("claims", ())), "evidence_count": len(refs),
            "missing_evidence_refs": missing, "read_only": True, "healthy": not missing}
