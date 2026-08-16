"""Première écriture subjective contrôlée, distincte du canon du monde."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any, Mapping

from .action_contract import WorldFact
from .attention import AttentionItem, AttentionService
from .db import transaction
from .needs import NeedsError
from .perception import PerceptionService
from .registry import KEY_RE as _KEY_RE
from .util import Clock, new_uuid


_FIDELITIES = frozenset({"complete", "partial", "ambiguous", "signal_only"})
MAX_RECALL_LIMIT = 50
MAX_AUTOBIOGRAPHICAL_WORKING_SET = 10
MAX_EPISODE_CUES = 32
ATTENTION_ADMISSION_LIMIT = 5


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


def _candidate_fingerprint(
    candidate_kind: str, fact_type: str, payload: Any, source_kind: str | None = None,
) -> str:
    """Identité stable d'un candidat, sans confondre le temps d'observation et le contenu."""
    value = _payload_json({
        "candidate_kind": candidate_kind,
        "fact_type": fact_type,
        "payload": payload,
        "source_kind": source_kind,
    })
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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

    @staticmethod
    def _cognitive_payload(trace: sqlite3.Row) -> dict[str, Any]:
        """Projection de contenu, sans identifiants ni règle d'accès technique."""
        payload = json.loads(trace["payload_json"])
        if trace["fact_type"] == "social_speech_act" and isinstance(payload, Mapping):
            return {
                key: payload[key]
                for key in ("act_kind", "content", "speaker_key", "recipient_key", "spoken_at")
                if key in payload
            }
        return payload

    @classmethod
    def _cognitive_sheet(cls, row: sqlite3.Row) -> dict[str, Any]:
        """Feuille subjective destinée à la cognition, distincte de l'audit."""
        return {
            "fact_type": row["fact_type"],
            "fact_occurred_at": row["fact_occurred_at"],
            "payload": cls._cognitive_payload(row),
        }

    def _existing_admission(self, world_id: int, character_id: int, request_key: str):
        return self._conn.execute(
            "SELECT * FROM subjective_memory_encoding_admission "
            "WHERE world_id = ? AND character_id = ? AND request_key = ?",
            (world_id, character_id, request_key),
        ).fetchone()

    def _admission_sheet(self, row: sqlite3.Row) -> dict[str, Any]:
        trace = None
        if row["trace_id"] is not None:
            trace_row = self._conn.execute(
                "SELECT * FROM subjective_trace WHERE id = ?", (row["trace_id"],)
            ).fetchone()
            if trace_row is not None:
                trace = self._sheet(trace_row)
        return {
            "public_id": row["public_id"],
            "request_key": row["request_key"],
            "candidate_kind": row["candidate_kind"],
            "candidate_fingerprint": row["candidate_fingerprint"],
            "outcome": row["outcome"],
            "reason_code": row["reason_code"],
            "trace": trace,
            "decided_at": row["decided_at"],
        }

    def _record_admission(
        self,
        world_id: int,
        character_id: int,
        request_key: str,
        candidate_kind: str,
        candidate_fingerprint: str,
        outcome: str,
        reason_code: str,
        trace_id: int | None,
    ) -> dict[str, Any]:
        existing = self._existing_admission(world_id, character_id, request_key)
        expected = (candidate_kind, candidate_fingerprint, outcome, reason_code, trace_id)
        if existing is not None:
            actual = tuple(existing[key] for key in (
                "candidate_kind", "candidate_fingerprint", "outcome", "reason_code", "trace_id"
            ))
            if actual != expected:
                raise SubjectiveMemoryError(
                    "clé d'admission déjà utilisée pour un autre candidat",
                    code="request_key_conflict",
                )
            return self._admission_sheet(existing)
        decided_at = self._clock.now_iso()
        with transaction(self._conn) as conn:
            cur = conn.execute(
                "INSERT INTO subjective_memory_encoding_admission "
                "(public_id, world_id, character_id, request_key, candidate_kind, "
                "candidate_fingerprint, outcome, reason_code, trace_id, decided_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    new_uuid(), world_id, character_id, request_key, candidate_kind,
                    candidate_fingerprint, outcome, reason_code, trace_id, decided_at,
                ),
            )
            admission_id = cur.lastrowid
        return self._admission_sheet(self._conn.execute(
            "SELECT * FROM subjective_memory_encoding_admission WHERE id = ?",
            (admission_id,),
        ).fetchone())

    def _existing_seed_decision(self, world_id: int, character_id: int, trace_id: int):
        return self._conn.execute(
            "SELECT * FROM autobiographical_episode_seed_decision "
            "WHERE world_id = ? AND character_id = ? AND trace_id = ?",
            (world_id, character_id, trace_id),
        ).fetchone()

    @staticmethod
    def _seed_sheet(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "public_id": row["public_id"],
            "trace_id": row["trace_id"],
            "outcome": row["outcome"],
            "reason_code": row["reason_code"],
            "episode_id": row["episode_id"],
            "decided_at": row["decided_at"],
        }

    def _record_seed_decision(
        self,
        world_id: int,
        character_id: int,
        trace_id: int,
        outcome: str,
        reason_code: str,
        episode_id: int | None,
    ) -> dict[str, Any]:
        existing = self._existing_seed_decision(world_id, character_id, trace_id)
        expected = (outcome, reason_code, episode_id)
        if existing is not None:
            actual = tuple(existing[key] for key in ("outcome", "reason_code", "episode_id"))
            if actual != expected:
                raise SubjectiveMemoryError(
                    "une trace a déjà reçu une décision de seeding différente",
                    code="seed_decision_conflict",
                )
            return self._seed_sheet(existing)
        decided_at = self._clock.now_iso()
        with transaction(self._conn) as conn:
            cur = conn.execute(
                "INSERT INTO autobiographical_episode_seed_decision "
                "(public_id, world_id, character_id, trace_id, outcome, reason_code, "
                "episode_id, decided_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    new_uuid(), world_id, character_id, trace_id, outcome, reason_code,
                    episode_id, decided_at,
                ),
            )
            decision_id = cur.lastrowid
        return self._seed_sheet(self._conn.execute(
            "SELECT * FROM autobiographical_episode_seed_decision WHERE id = ?",
            (decision_id,),
        ).fetchone())

    def _trace_row(self, world_id: int, character_id: int, request_key: str):
        return self._conn.execute(
            "SELECT * FROM subjective_trace WHERE world_id = ? AND character_id = ? "
            "AND request_key = ?", (world_id, character_id, request_key),
        ).fetchone()

    def _record_phase_a(
        self,
        world_id: int,
        character_key: str,
        request_key: str,
        candidate_kind: str,
        fact_type: str,
        payload: Any,
        outcome: str,
        reason_code: str,
        trace: dict[str, Any] | None,
        source_kind: str | None = None,
    ) -> dict[str, Any]:
        character_id = self._character_id(world_id, character_key)
        trace_id = None if trace is None else self._trace_row(
            world_id, character_id, request_key
        )["id"]
        return self._record_admission(
            world_id, character_id, request_key, candidate_kind,
            _candidate_fingerprint(candidate_kind, fact_type, payload, source_kind),
            outcome, reason_code, trace_id,
        )

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

    def admit_attention(
        self, world_id: Any, character_key: Any, request_key: Any, item: Any,
        *, fidelity: Any = "complete",
    ) -> dict[str, Any]:
        """Décide explicitement si un candidat accessible est encodé.

        La politique MVP examine toute la vue disponible, mais n'accorde une
        admission automatique qu'au premier candidat sélectionné. Les autres
        décisions restent persistées comme ``not_encoded``. Ce choix borne la
        politique sans transformer la sélection d'attention en équivalent
        universel de la mémoire.
        """
        world_id = self._world_id(world_id)
        character_key = self._key(character_key, "personnage")
        request_key = self._key(request_key, "clé de demande")
        fidelity = self._fidelity(fidelity)
        if not isinstance(item, AttentionItem) or item.observer_key != character_key or item.fact.event_seq is not None:
            raise SubjectiveMemoryError("source d'attention invalide", code="invalid_source")
        character_id = self._character_id(world_id, character_key)
        existing = self._existing_admission(world_id, character_id, request_key)
        if existing is not None:
            admission = self._admission_sheet(existing)
            trace = admission["trace"]
            seed = None
            if trace is not None:
                trace_row = self._trace_row(world_id, character_id, request_key)
                seed_row = self._existing_seed_decision(world_id, character_id, trace_row["id"])
                if seed_row is not None:
                    seed = self._seed_sheet(seed_row)
            return {"decision": admission, "trace": trace, "seed": seed}
        snapshot = AttentionService(self._conn, clock=self._clock).snapshot(
            world_id, character_key, limit=ATTENTION_ADMISSION_LIMIT
        )
        available = tuple(
            candidate for candidate in snapshot.available
            if candidate.source_kind == item.source_kind
            and self._same_fact(candidate.fact, item.fact)
        )
        if not available:
            raise SubjectiveMemoryError("source d'attention non admissible", code="source_not_accessible")
        selected_index = next(
            (
                index for index, candidate in enumerate(snapshot.selected)
                if candidate.source_kind == item.source_kind
                and self._same_fact(candidate.fact, item.fact)
            ),
            None,
        )
        if selected_index is None:
            admission = self._record_phase_a(
                world_id, character_key, request_key, "attention", item.fact.event_type,
                item.fact.payload, "not_encoded", "attention_not_selected", None,
                item.source_kind,
            )
            return {"decision": admission, "trace": None, "seed": None}
        if selected_index != 0:
            admission = self._record_phase_a(
                world_id, character_key, request_key, "attention", item.fact.event_type,
                item.fact.payload, "not_encoded", "attention_not_primary_candidate", None,
                item.source_kind,
            )
            return {"decision": admission, "trace": None, "seed": None}
        with transaction(self._conn):
            trace = self._record(
                world_id, character_key, request_key, "state", item.source_kind,
                item.fact, fidelity,
            )
            admission = self._record_phase_a(
                world_id, character_key, request_key, "attention", item.fact.event_type,
                item.fact.payload, "encoded", "attention_primary_candidate", trace,
                item.source_kind,
            )
            trace_id = self._trace_row(world_id, character_id, request_key)["id"]
            seed = self._record_seed_decision(
                world_id, character_id, trace_id, "trace_only",
                "attention_state_not_episode_unit", None,
            )
        return {"decision": admission, "trace": trace, "seed": seed}

    def encode_attention(
        self, world_id: Any, character_key: Any, request_key: Any, item: Any,
        *, fidelity: Any = "complete",
    ) -> dict[str, Any]:
        """Compatibilité : l'appel d'encodage passe désormais par l'admission."""
        result = self.admit_attention(
            world_id, character_key, request_key, item, fidelity=fidelity,
        )
        if result["trace"] is None:
            raise SubjectiveMemoryError(
                "candidat d'attention non encodé", code="not_encoded",
            )
        return result["trace"]

    def _sapient_character_keys(self, world_id: int) -> tuple[str, ...]:
        rows = self._conn.execute(
            "SELECT c.key, o.resolved_initial_definition_json "
            "FROM character c JOIN character_instance_origin o ON o.character_id = c.id "
            "WHERE c.world_id = ? ORDER BY c.key", (world_id,)
        ).fetchall()
        keys: list[str] = []
        for row in rows:
            try:
                components = json.loads(row["resolved_initial_definition_json"])["components"]
                profile = next(item for item in components if item.get("key") == "cognition.profile")
                if profile["config"]["level"] != "non_sapient":
                    keys.append(row["key"])
            except (KeyError, StopIteration, TypeError, ValueError):
                continue
        return tuple(keys)

    def admit_current_attention(self, world_id: Any) -> tuple[dict[str, Any], ...]:
        """Évalue les candidats accessibles dans le cycle mémoire runtime."""
        world_id = self._world_id(world_id)
        decisions: list[dict[str, Any]] = []
        for character_key in self._sapient_character_keys(world_id):
            snapshot = AttentionService(self._conn, clock=self._clock).snapshot(
                world_id, character_key, limit=ATTENTION_ADMISSION_LIMIT,
            )
            for item in snapshot.available:
                fingerprint = _candidate_fingerprint(
                    "attention", item.fact.event_type, item.fact.payload, item.source_kind,
                )
                request_key = f"memory-attention-{fingerprint[:32]}"
                try:
                    decisions.append(self.admit_attention(
                        world_id, character_key, request_key, item,
                    ))
                except SubjectiveMemoryError as exc:
                    if exc.code != "source_not_accessible":
                        raise
        return tuple(decisions)

    def encode_direct_event(self, world_id: Any, character_key: Any, request_key: Any, event_seq: Any, *, fidelity: Any = "complete") -> dict[str, Any]:
        world_id = self._world_id(world_id); character_key = self._key(character_key, "personnage")
        request_key = self._key(request_key, "clé de demande"); fidelity = self._fidelity(fidelity)
        if not isinstance(event_seq, int) or isinstance(event_seq, bool) or event_seq < 1:
            raise SubjectiveMemoryError("séquence d'événement invalide", code="invalid_source")
        feed = PerceptionService(self._conn, clock=self._clock).events_since(world_id, character_key, event_seq - 1)
        candidate = next((candidate for candidate in feed.candidates if candidate.fact.event_seq == event_seq), None)
        if candidate is None:
            raise SubjectiveMemoryError("événement non admissible", code="source_not_accessible")
        character_id = self._character_id(world_id, character_key)
        with transaction(self._conn):
            trace = self._record(
                world_id, character_key, request_key, "event", candidate.access_kind,
                candidate.fact, fidelity,
            )
            self._record_phase_a(
                world_id, character_key, request_key, "direct_event",
                candidate.fact.event_type, candidate.fact.payload, "encoded",
                "explicit_direct_event", trace,
            )
            trace_id = self._trace_row(world_id, character_id, request_key)["id"]
            self._record_seed_decision(
                world_id, character_id, trace_id, "trace_only",
                "episode_seeding_not_requested", None,
            )
        return trace

    def _social_speech_source(
        self, world_id: int, observer_key: str, scene_key: str, act_key: str,
    ) -> tuple[WorldFact, int, str]:
        world_id = self._world_id(world_id)
        observer_key = self._key(observer_key, "observatrice")
        scene_key = self._key(scene_key, "scène")
        act_key = self._key(act_key, "acte")
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
        return fact, row["id"], row["speaker_key"]

    def encode_social_speech(
        self, world_id: Any, observer_key: Any, request_key: Any,
        scene_key: Any, act_key: Any, *, fidelity: Any = "complete",
    ) -> dict[str, Any]:
        """Encode une parole après une décision explicite de l'appelant.

        La source et son contenu sont toujours relus depuis la scène. Le
        chemin runtime passe par :meth:`admit_social_speech`, qui ajoute la
        décision d'encodage avant d'appeler cette opération de matérialisation.
        """
        world_id = self._world_id(world_id)
        observer_key = self._key(observer_key, "observatrice")
        request_key = self._key(request_key, "clé de demande")
        fidelity = self._fidelity(fidelity)
        fact, source_act_id, _speaker_key = self._social_speech_source(
            world_id, observer_key, scene_key, act_key,
        )
        with transaction(self._conn):
            trace = self._record(
                world_id, observer_key, request_key, "state",
                "social_scene_participant", fact, fidelity,
                source_social_speech_act_id=source_act_id,
            )
            self._record_phase_a(
                world_id, observer_key, request_key, "social_speech",
                fact.event_type, fact.payload, "encoded", "explicit_social_input",
                trace,
            )
        return trace

    def admit_social_speech(
        self, world_id: Any, observer_key: Any, request_key: Any,
        scene_key: Any, act_key: Any, *, fidelity: Any = "complete",
    ) -> dict[str, Any]:
        """Admission sociale explicite, suivie d'un seeding discret optionnel."""
        world_id = self._world_id(world_id)
        observer_key = self._key(observer_key, "observatrice")
        request_key = self._key(request_key, "clé de demande")
        character_id = self._character_id(world_id, observer_key)
        existing = self._existing_admission(world_id, character_id, request_key)
        if existing is not None:
            admission = self._admission_sheet(existing)
            trace = admission["trace"]
        else:
            fact, _source_act_id, speaker_key = self._social_speech_source(
                world_id, observer_key, scene_key, act_key,
            )
            allowed = observer_key == speaker_key
            denial_reason = "social_source_not_attention_admitted"
            if not allowed:
                try:
                    snapshot = AttentionService(self._conn, clock=self._clock).snapshot(
                        world_id, observer_key, limit=ATTENTION_ADMISSION_LIMIT,
                    )
                except NeedsError:
                    # Une incapacité technique à évaluer l'admission ne vaut
                    # jamais décision positive d'encodage.
                    allowed = False
                    denial_reason = "social_admission_unavailable"
                else:
                    denial_reason = "social_source_not_attention_admitted"
                    allowed = any(
                        item.source_kind == "perception:co_presence"
                        and item.fact.payload.get("character") == speaker_key
                        for item in snapshot.selected
                    )
            if not allowed:
                admission = self._record_phase_a(
                    world_id, observer_key, request_key, "social_speech",
                    fact.event_type, fact.payload, "not_encoded",
                    denial_reason, None,
                    "social_scene_participant",
                )
                return {"decision": admission, "trace": None, "seed": None}
            trace = self.encode_social_speech(
                world_id, observer_key, request_key, scene_key, act_key,
                fidelity=fidelity,
            )
            admission = self._admission_sheet(
                self._existing_admission(world_id, character_id, request_key)
            )
        if trace is None:
            raise SubjectiveMemoryError("parole sociale non encodée", code="not_encoded")
        trace_id = self._trace_row(world_id, character_id, request_key)["id"]
        seed = self.seed_episode_for_trace(
            world_id, observer_key, trace_id, reason_code="social_speech_discrete_unit",
        )
        return {"decision": admission, "trace": trace, "seed": seed}

    def seed_episode_for_trace(
        self, world_id: Any, character_key: Any, trace_id: Any, *,
        reason_code: str | None = None,
    ) -> dict[str, Any]:
        """Phase B séparée : un support discret peut amorcer un épisode unique."""
        world_id = self._world_id(world_id)
        character_key = self._key(character_key, "personnage")
        if not isinstance(trace_id, int) or isinstance(trace_id, bool) or trace_id < 1:
            raise SubjectiveMemoryError("trace invalide", code="invalid_source")
        character_id = self._character_id(world_id, character_key)
        trace = self._conn.execute(
            "SELECT * FROM subjective_trace WHERE id = ? AND world_id = ? AND character_id = ?",
            (trace_id, world_id, character_id),
        ).fetchone()
        if trace is None:
            raise SubjectiveMemoryError("support subjectif inaccessible", code="source_not_accessible")
        existing = self._existing_seed_decision(world_id, character_id, trace_id)
        if existing is not None:
            return self._seed_sheet(existing)
        discrete = trace["source_kind"] == "event" or trace["fact_type"] == "social_speech_act"
        if not discrete:
            return self._record_seed_decision(
                world_id, character_id, trace_id, "trace_only",
                reason_code or "trace_not_a_discrete_episode_unit", None,
            )
        episode_key = f"episode-seed-{trace['request_key']}"
        self.form_episode(
            world_id, character_key, episode_key, [trace_id],
        )
        episode_row = self._episode_row(world_id, character_id, episode_key)
        return self._record_seed_decision(
            world_id, character_id, trace_id, "episode_seeded",
            reason_code or "discrete_trace_episode_seeded", episode_row["id"],
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

    def recall_recent_cognitive(
        self, world_id: Any, character_key: Any, *, limit: Any = 5,
        exclude_source_social_speech_act_ids: tuple[int, ...] = (),
    ) -> tuple[dict[str, Any], ...]:
        """Rappel récent projeté pour la cognition, sans métadonnées d'audit."""
        world_id = self._world_id(world_id)
        character_key = self._key(character_key, "personnage")
        limit = self._limit(limit)
        character_id = self._character_id(world_id, character_key)
        excluded = tuple(
            value for value in exclude_source_social_speech_act_ids
            if isinstance(value, int) and not isinstance(value, bool) and value > 0
        )
        if excluded:
            placeholders = ",".join("?" for _ in excluded)
            rows = self._conn.execute(
                "SELECT * FROM subjective_trace WHERE world_id = ? AND character_id = ? "
                f"AND (source_social_speech_act_id IS NULL OR source_social_speech_act_id NOT IN ({placeholders})) "
                "ORDER BY encoded_at DESC, id DESC LIMIT ?",
                (world_id, character_id, *excluded, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM subjective_trace WHERE world_id = ? AND character_id = ? "
                "ORDER BY encoded_at DESC, id DESC LIMIT ?",
                (world_id, character_id, limit),
            ).fetchall()
        return tuple(self._cognitive_sheet(row) for row in rows)

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
        participant_list = sorted(participants)
        support_details = [
            {
                "fact_type": trace["fact_type"],
                "occurred_at": trace["fact_occurred_at"],
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
            "participants": participant_list,
        }
        source_attribution = {"kind": "unresolved"}
        recovery_cues = tuple(dict.fromkeys(fact_types + participant_list))
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
