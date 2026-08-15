"""Première écriture subjective contrôlée, distincte du canon du monde."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Mapping

from .action_contract import WorldFact
from .attention import AttentionItem, AttentionService
from .db import transaction
from .perception import PerceptionService
from .registry import KEY_RE as _KEY_RE
from .util import Clock, new_uuid


_FIDELITIES = frozenset({"complete", "partial", "ambiguous", "signal_only"})
MAX_RECALL_LIMIT = 50
MAX_AUTOBIOGRAPHICAL_WORKING_SET = 10
MAX_EPISODE_CUES = 32


class SubjectiveMemoryError(ValueError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _payload_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(_plain(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _json_object(value: Any, label: str) -> str:
    if not isinstance(value, Mapping):
        raise SubjectiveMemoryError(f"{label} invalide", code="invalid_episode")
    try:
        return _payload_json(value)
    except (TypeError, ValueError) as exc:
        raise SubjectiveMemoryError(f"{label} illisible", code="invalid_episode") from exc


def _json_array(value: Any, label: str) -> str:
    if not isinstance(value, (list, tuple)):
        raise SubjectiveMemoryError(f"{label} invalide", code="invalid_episode")
    try:
        return json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise SubjectiveMemoryError(f"{label} illisible", code="invalid_episode") from exc


def _milli(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 1000:
        raise SubjectiveMemoryError(f"{label} invalide", code="invalid_episode")
    return value


def _tokens(value: Any) -> frozenset[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for item in value.values():
            found.update(_tokens(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            found.update(_tokens(item))
    elif isinstance(value, str) and value.strip():
        found.add(value.strip().casefold())
    return frozenset(found)


class SubjectiveMemoryService:
    """Encode seulement une source que les couches précédentes peuvent prouver."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def _world_id(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise SubjectiveMemoryError("monde invalide", code="invalid_world")
        return value

    @staticmethod
    def _key(value: Any, label: str) -> str:
        if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
            raise SubjectiveMemoryError(f"{label} invalide", code="invalid_request")
        return value

    @staticmethod
    def _fidelity(value: Any) -> str:
        if value not in _FIDELITIES:
            raise SubjectiveMemoryError("fidélité invalide", code="invalid_fidelity")
        return value

    @staticmethod
    def _limit(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= MAX_RECALL_LIMIT:
            raise SubjectiveMemoryError("limite de rappel invalide", code="invalid_limit")
        return value

    def _character_id(self, world_id: int, character_key: str) -> int:
        row = self._conn.execute(
            "SELECT id FROM character WHERE world_id = ? AND key = ?", (world_id, character_key)
        ).fetchone()
        if row is None:
            raise SubjectiveMemoryError("personnage introuvable", code="character_not_found")
        return row["id"]

    @staticmethod
    def _same_fact(left: WorldFact, right: WorldFact) -> bool:
        return (left.world_id, left.event_seq, left.event_type, left.occurred_at, _payload_json(left.payload)) == (
            right.world_id, right.event_seq, right.event_type, right.occurred_at, _payload_json(right.payload)
        )

    def _existing(self, world_id: int, character_id: int, request_key: str):
        return self._conn.execute(
            "SELECT * FROM subjective_trace WHERE world_id = ? AND character_id = ? AND request_key = ?",
            (world_id, character_id, request_key),
        ).fetchone()

    @staticmethod
    def _sheet(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "public_id": row["public_id"], "request_key": row["request_key"],
            "source_kind": row["source_kind"], "source_event_seq": row["source_event_seq"],
            "source_social_speech_act_id": row["source_social_speech_act_id"],
            "fact_type": row["fact_type"], "fact_occurred_at": row["fact_occurred_at"],
            "access_kind": row["access_kind"], "fidelity": row["fidelity"],
            "payload": json.loads(row["payload_json"]), "encoded_at": row["encoded_at"],
        }

    def _record(self, world_id: int, character_key: str, request_key: str, source_kind: str,
                access_kind: str, fact: WorldFact, fidelity: str,
                *, source_social_speech_act_id: int | None = None) -> dict[str, Any]:
        character_id = self._character_id(world_id, character_key)
        payload = _payload_json(fact.payload)
        existing = self._existing(world_id, character_id, request_key)
        expected = (source_kind, fact.event_seq, source_social_speech_act_id, fact.event_type,
                    fact.occurred_at, access_kind, fidelity, payload)
        if existing is not None:
            actual = tuple(existing[key] for key in (
                "source_kind", "source_event_seq", "source_social_speech_act_id", "fact_type",
                "fact_occurred_at", "access_kind", "fidelity", "payload_json"
            ))
            if actual != expected:
                raise SubjectiveMemoryError("clé de demande déjà utilisée pour une autre trace", code="request_key_conflict")
            return self._sheet(existing)
        encoded_at = self._clock.now_iso()
        with transaction(self._conn) as conn:
            cur = conn.execute(
                "INSERT INTO subjective_trace (public_id, world_id, character_id, request_key, source_kind, source_event_seq, source_social_speech_act_id, fact_type, fact_occurred_at, access_kind, fidelity, payload_json, encoded_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_uuid(), world_id, character_id, request_key, source_kind, fact.event_seq,
                 source_social_speech_act_id, fact.event_type, fact.occurred_at, access_kind,
                 fidelity, payload, encoded_at),
            )
            trace_id = cur.lastrowid
            conn.execute(
                "INSERT INTO subjective_trace_event (world_id, character_id, trace_id, event_type, payload_json, recorded_at) VALUES (?, ?, ?, 'trace_encoded', ?, ?)",
                (world_id, character_id, trace_id, _payload_json({"trace_id": trace_id, "source_kind": source_kind, "fact_type": fact.event_type}), encoded_at),
            )
        return self._sheet(self._conn.execute("SELECT * FROM subjective_trace WHERE id = ?", (trace_id,)).fetchone())

    def encode_attention(self, world_id: Any, character_key: Any, request_key: Any, item: Any, *, fidelity: Any = "complete") -> dict[str, Any]:
        world_id = self._world_id(world_id); character_key = self._key(character_key, "personnage")
        request_key = self._key(request_key, "clé de demande"); fidelity = self._fidelity(fidelity)
        if not isinstance(item, AttentionItem) or item.observer_key != character_key or item.fact.event_seq is not None:
            raise SubjectiveMemoryError("source d'attention invalide", code="invalid_source")
        current = AttentionService(self._conn, clock=self._clock).snapshot(world_id, character_key).available
        if not any(candidate.source_kind == item.source_kind and self._same_fact(candidate.fact, item.fact) for candidate in current):
            raise SubjectiveMemoryError("source d'attention non admissible", code="source_not_accessible")
        return self._record(world_id, character_key, request_key, "state", item.source_kind, item.fact, fidelity)

    def encode_direct_event(self, world_id: Any, character_key: Any, request_key: Any, event_seq: Any, *, fidelity: Any = "complete") -> dict[str, Any]:
        world_id = self._world_id(world_id); character_key = self._key(character_key, "personnage")
        request_key = self._key(request_key, "clé de demande"); fidelity = self._fidelity(fidelity)
        if not isinstance(event_seq, int) or isinstance(event_seq, bool) or event_seq < 1:
            raise SubjectiveMemoryError("séquence d'événement invalide", code="invalid_source")
        feed = PerceptionService(self._conn, clock=self._clock).events_since(world_id, character_key, event_seq - 1)
        candidate = next((candidate for candidate in feed.candidates if candidate.fact.event_seq == event_seq), None)
        if candidate is None:
            raise SubjectiveMemoryError("événement non admissible", code="source_not_accessible")
        return self._record(world_id, character_key, request_key, "event", candidate.access_kind, candidate.fact, fidelity)

    def encode_social_speech(
        self, world_id: Any, observer_key: Any, request_key: Any,
        scene_key: Any, act_key: Any, *, fidelity: Any = "complete",
    ) -> dict[str, Any]:
        """Encode une parole sociale dont l'accès historique est prouvé.

        La source est relue depuis les tables de scène : aucun contenu ou
        participant fourni par l'appelant ne peut devenir la trace. La scène
        est une frontière d'accès alpha ; sa fermeture et les déplacements
        ultérieurs ne modifient pas l'accès établi au moment de la parole.
        """
        world_id = self._world_id(world_id)
        observer_key = self._key(observer_key, "observatrice")
        request_key = self._key(request_key, "clé de demande")
        scene_key = self._key(scene_key, "scène")
        act_key = self._key(act_key, "acte")
        fidelity = self._fidelity(fidelity)
        row = self._conn.execute(
            "SELECT act.id, act.act_kind, act.content_text, act.spoken_at, "
            "sp.key AS speaker_key, rp.key AS recipient_key, scene.scene_key, "
            "scene.world_id, participant.joined_at, observer.id AS observer_id "
            "FROM social_speech_act act "
            "JOIN social_scene scene ON scene.id = act.scene_id "
            "JOIN character sp ON sp.id = act.speaker_character_id "
            "LEFT JOIN character rp ON rp.id = act.recipient_character_id "
            "JOIN social_scene_participant participant ON participant.scene_id = scene.id "
            "JOIN character observer ON observer.id = participant.character_id "
            "WHERE scene.world_id = ? AND scene.scene_key = ? AND act.act_key = ? "
            "AND observer.world_id = ? AND observer.key = ?",
            (world_id, scene_key, act_key, world_id, observer_key),
        ).fetchone()
        if row is None or row["joined_at"] > row["spoken_at"]:
            raise SubjectiveMemoryError("parole sociale non accessible", code="source_not_accessible")
        payload = {
            "scene_key": row["scene_key"], "act_key": act_key,
            "act_kind": row["act_kind"], "content": row["content_text"],
            "speaker_key": row["speaker_key"], "recipient_key": row["recipient_key"],
            "spoken_at": row["spoken_at"],
            "access_rule": "social_scene_participant_at_spoken_at",
        }
        fact = WorldFact.state(world_id, "social_speech_act", row["spoken_at"], payload)
        return self._record(
            world_id, observer_key, request_key, "state", "social_scene_participant",
            fact, fidelity, source_social_speech_act_id=row["id"],
        )

    def recall_recent(self, world_id: Any, character_key: Any, *, limit: Any = 5) -> tuple[dict[str, Any], ...]:
        """Rappel minimal : propriétaire seul, ordre stable, sans reconsolidation."""
        world_id = self._world_id(world_id)
        character_key = self._key(character_key, "personnage")
        limit = self._limit(limit)
        character_id = self._character_id(world_id, character_key)
        rows = self._conn.execute(
            "SELECT * FROM subjective_trace WHERE world_id = ? AND character_id = ? "
            "ORDER BY encoded_at DESC, id DESC LIMIT ?",
            (world_id, character_id, limit),
        ).fetchall()
        return tuple(self._sheet(row) for row in rows)

    def _episode_sheet(
        self, row: sqlite3.Row, *, include_audit: bool = False
    ) -> dict[str, Any]:
        sheet = {
            "episode_key": row["episode_key"],
            "gist": json.loads(row["gist_json"]),
            "details": json.loads(row["details_json"]),
            "context": json.loads(row["context_json"]),
            "participants": tuple(json.loads(row["participants_json"])),
            "experience_started_at": row["experience_started_at"],
            "experience_ended_at": row["experience_ended_at"],
            "source_attribution": json.loads(row["source_attribution_json"]),
            "recovery_cues": tuple(json.loads(row["recovery_cues_json"])),
            "importance_milli": row["importance_milli"],
            "accessibility_milli": row["accessibility_milli"],
        }
        if include_audit:
            sheet["public_id"] = row["public_id"]
            sheet["formed_at"] = row["formed_at"]
            supports = self._conn.execute(
                "SELECT trace.id, trace.request_key, support.support_role "
                "FROM autobiographical_episode_support support "
                "JOIN subjective_trace trace ON trace.id = support.trace_id "
                "WHERE support.episode_id = ? ORDER BY support.id",
                (row["id"],),
            ).fetchall()
            sheet["support_trace_ids"] = tuple(item["id"] for item in supports)
            sheet["support_request_keys"] = tuple(item["request_key"] for item in supports)
            sheet["support_roles"] = tuple(item["support_role"] for item in supports)
        return sheet

    def _episode_row(self, world_id: int, character_id: int, episode_key: str):
        return self._conn.execute(
            "SELECT * FROM autobiographical_episode "
            "WHERE world_id = ? AND character_id = ? AND episode_key = ?",
            (world_id, character_id, episode_key),
        ).fetchone()

    def _source_rows(
        self, world_id: int, character_id: int, source_trace_ids: Any
    ) -> tuple[sqlite3.Row, ...]:
        if not isinstance(source_trace_ids, (list, tuple)) or not source_trace_ids:
            raise SubjectiveMemoryError("supports requis", code="invalid_source")
        if len(source_trace_ids) > MAX_EPISODE_CUES:
            raise SubjectiveMemoryError("trop de supports", code="invalid_source")
        if any(
            not isinstance(trace_id, int) or isinstance(trace_id, bool) or trace_id < 1
            for trace_id in source_trace_ids
        ) or len(set(source_trace_ids)) != len(source_trace_ids):
            raise SubjectiveMemoryError("supports invalides", code="invalid_source")
        placeholders = ",".join("?" for _ in source_trace_ids)
        rows = self._conn.execute(
            f"SELECT * FROM subjective_trace WHERE world_id = ? AND character_id = ? "
            f"AND id IN ({placeholders})",
            (world_id, character_id, *source_trace_ids),
        ).fetchall()
        by_id = {row["id"]: row for row in rows}
        if len(by_id) != len(source_trace_ids):
            raise SubjectiveMemoryError(
                "support subjectif inaccessible", code="source_not_accessible"
            )
        return tuple(
            sorted(
                by_id.values(),
                key=lambda row: (row["fact_occurred_at"], row["id"]),
            )
        )

    def _grounded_episode_projection(
        self, world_id: int, traces: tuple[sqlite3.Row, ...]
    ) -> tuple[str, str, str, str, str, tuple[str, ...]]:
        """Construit uniquement des champs copiés/dérivés des supports validés."""
        participants: set[str] = set()
        participant_fields = {
            "character",
            "character_key",
            "speaker_key",
            "recipient_key",
            "participant_key",
        }
        for trace in traces:
            payload = json.loads(trace["payload_json"])
            for field in participant_fields:
                value = payload.get(field) if isinstance(payload, Mapping) else None
                if isinstance(value, str) and _KEY_RE.fullmatch(value):
                    exists = self._conn.execute(
                        "SELECT 1 FROM character WHERE world_id = ? AND key = ?",
                        (world_id, value),
                    ).fetchone()
                    if exists is not None:
                        participants.add(value)
            values = payload.get("participants") if isinstance(payload, Mapping) else None
            if isinstance(values, (list, tuple)):
                for value in values:
                    if not isinstance(value, str) or _KEY_RE.fullmatch(value) is None:
                        continue
                    exists = self._conn.execute(
                        "SELECT 1 FROM character WHERE world_id = ? AND key = ?",
                        (world_id, value),
                    ).fetchone()
                    if exists is not None:
                        participants.add(value)

        fact_types = sorted({trace["fact_type"] for trace in traces})
        source_kinds = sorted({trace["source_kind"] for trace in traces})
        access_kinds = sorted({trace["access_kind"] for trace in traces})
        fidelities = sorted({trace["fidelity"] for trace in traces})
        participant_list = sorted(participants)
        support_details = [
            {
                "fact_type": trace["fact_type"],
                "occurred_at": trace["fact_occurred_at"],
                "access_kind": trace["access_kind"],
                "fidelity": trace["fidelity"],
                "payload": json.loads(trace["payload_json"]),
            }
            for trace in traces
        ]
        gist = {
            "kind": "supported_trace_projection",
            "fact_types": fact_types,
            "support_count": len(traces),
        }
        details = {"supports": support_details}
        context = {
            "fact_types": fact_types,
            "source_kinds": source_kinds,
            "access_kinds": access_kinds,
            "participants": participant_list,
        }
        source_attribution = {
            "kind": "derived_from_subjective_access",
            "source_kinds": source_kinds,
            "access_kinds": access_kinds,
            "fidelities": fidelities,
        }
        recovery_cues = tuple(
            dict.fromkeys(fact_types + access_kinds + source_kinds + participant_list)
        )
        return (
            _json_object(gist, "gist"),
            _json_object(details, "détails"),
            _json_object(context, "contexte"),
            _json_array(participant_list, "participants"),
            _json_object(source_attribution, "attribution subjective"),
            recovery_cues,
        )

    def form_episode(
        self,
        world_id: Any,
        character_key: Any,
        episode_key: Any,
        source_trace_ids: Any,
        *,
        importance_milli: Any = 0,
        accessibility_milli: Any = 1000,
    ) -> dict[str, Any]:
        """Forme explicitement un épisode depuis des traces du propriétaire.

        Le contenu est une projection structurée et déterministe des traces
        validées; la synthèse narrative reconstructive est reportée. Les
        bornes temporelles sont dérivées des traces; aucun événement
        canonique ni aucune provenance fournie par un LLM n'est accepté comme
        source directe.
        """
        world_id = self._world_id(world_id)
        character_key = self._key(character_key, "personnage")
        episode_key = self._key(episode_key, "épisode")
        importance_milli = _milli(importance_milli, "importance")
        accessibility_milli = _milli(accessibility_milli, "accessibilité")
        character_id = self._character_id(world_id, character_key)
        traces = self._source_rows(world_id, character_id, source_trace_ids)
        (
            gist_json,
            details_json,
            context_json,
            participants_json,
            source_attribution_json,
            recovery_cues,
        ) = self._grounded_episode_projection(world_id, traces)
        recovery_cues_json = _json_array(recovery_cues, "cues")
        experience_started_at = min(row["fact_occurred_at"] for row in traces)
        experience_ended_at = max(row["fact_occurred_at"] for row in traces)
        formed_at = self._clock.now_iso()

        with transaction(self._conn) as conn:
            existing = self._episode_row(world_id, character_id, episode_key)
            if existing is not None:
                expected = (
                    gist_json, details_json, context_json, participants_json,
                    experience_started_at, experience_ended_at, source_attribution_json,
                    recovery_cues_json, importance_milli, accessibility_milli,
                )
                actual = tuple(existing[key] for key in (
                    "gist_json", "details_json", "context_json", "participants_json",
                    "experience_started_at", "experience_ended_at", "source_attribution_json",
                    "recovery_cues_json", "importance_milli", "accessibility_milli",
                ))
                support_ids = tuple(item["trace_id"] for item in conn.execute(
                    "SELECT trace_id FROM autobiographical_episode_support "
                    "WHERE episode_id = ? ORDER BY id", (existing["id"],)
                ).fetchall())
                if actual != expected or support_ids != tuple(trace["id"] for trace in traces):
                    raise SubjectiveMemoryError(
                        "clé d'épisode déjà utilisée pour un autre souvenir",
                        code="episode_key_conflict",
                    )
                return self._episode_sheet(existing, include_audit=True)
            cur = conn.execute(
                "INSERT INTO autobiographical_episode ("
                "public_id, world_id, character_id, episode_key, gist_json, details_json, "
                "context_json, participants_json, experience_started_at, experience_ended_at, "
                "source_attribution_json, recovery_cues_json, importance_milli, "
                "accessibility_milli, formed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    new_uuid(), world_id, character_id, episode_key, gist_json, details_json,
                    context_json, participants_json, experience_started_at,
                    experience_ended_at, source_attribution_json, recovery_cues_json,
                    importance_milli, accessibility_milli, formed_at,
                ),
            )
            episode_id = cur.lastrowid
            for index, trace in enumerate(traces):
                conn.execute(
                    "INSERT INTO autobiographical_episode_support "
                    "(world_id, character_id, episode_id, trace_id, support_role, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        world_id, character_id, episode_id, trace["id"],
                        "primary" if index == 0 else "additional", formed_at,
                    ),
                )
            support_ids = [trace["id"] for trace in traces]
            conn.execute(
                "INSERT INTO autobiographical_episode_event "
                "(world_id, character_id, episode_id, event_type, payload_json, recorded_at) "
                "VALUES (?, ?, ?, 'episode_formed', ?, ?)",
                (
                    world_id, character_id, episode_id,
                    _payload_json({"episode_id": episode_id, "support_trace_ids": support_ids}),
                    formed_at,
                ),
            )
        return self._episode_sheet(
            self._conn.execute(
                "SELECT * FROM autobiographical_episode WHERE id = ?", (episode_id,)
            ).fetchone(),
            include_audit=True,
        )

    def get_episode(
        self, world_id: Any, character_key: Any, episode_key: Any
    ) -> dict[str, Any]:
        world_id = self._world_id(world_id)
        character_key = self._key(character_key, "personnage")
        episode_key = self._key(episode_key, "épisode")
        row = self._episode_row(world_id, self._character_id(world_id, character_key), episode_key)
        if row is None:
            raise SubjectiveMemoryError("épisode introuvable", code="episode_not_found")
        return self._episode_sheet(row, include_audit=True)

    def recall_autobiographical(
        self,
        world_id: Any,
        character_key: Any,
        *,
        context: Mapping[str, Any] | None = None,
        limit: Any = 5,
    ) -> tuple[dict[str, Any], ...]:
        """Retourne un working set borné, owner-scoped et déterministe."""
        world_id = self._world_id(world_id)
        character_key = self._key(character_key, "personnage")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_AUTOBIOGRAPHICAL_WORKING_SET:
            raise SubjectiveMemoryError("limite de working set invalide", code="invalid_limit")
        if context is None:
            context = {}
        if not isinstance(context, Mapping):
            raise SubjectiveMemoryError("contexte de rappel invalide", code="invalid_context")
        context_json = _json_object(context, "contexte de rappel")
        context_data = json.loads(context_json)
        query_cues = _tokens(context_data.get("cues", ()))
        query_tokens = _tokens(context_data)
        character_id = self._character_id(world_id, character_key)
        rows = self._conn.execute(
            "SELECT * FROM autobiographical_episode "
            "WHERE world_id = ? AND character_id = ? ORDER BY id",
            (world_id, character_id),
        ).fetchall()
        ranked: list[tuple[tuple[Any, ...], sqlite3.Row]] = []
        for row in rows:
            episode_context = json.loads(row["context_json"])
            episode_cues = _tokens(json.loads(row["recovery_cues_json"]))
            episode_tokens = episode_cues | _tokens(episode_context) | _tokens(
                json.loads(row["participants_json"])
            )
            cue_hits = len(query_cues & episode_cues)
            context_hits = len(query_tokens & episode_tokens)
            rank = (
                cue_hits, context_hits, row["importance_milli"],
                row["accessibility_milli"], row["experience_ended_at"], row["id"],
            )
            ranked.append((rank, row))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return tuple(self._episode_sheet(row) for _rank, row in ranked[:limit])
