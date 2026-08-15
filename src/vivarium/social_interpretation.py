"""Lectures sociales privées, sans croyance ni conséquence automatique."""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Any, Iterable

from .db import transaction
from .registry import KEY_RE as _KEY_RE
from .util import Clock, new_uuid


_STATUSES = frozenset({"clear", "ambiguous", "unresolved"})
_MAX_HYPOTHESES = 3
_MAX_HYPOTHESIS_LENGTH = 280
_TECHNICAL_PROVENANCE_KEYS = frozenset(("origin_kind", "model_id", "provider_version", "snapshot_fingerprint", "provider_turn_id"))
_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")


class SocialInterpretationError(ValueError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class SocialInterpretationService:
    """Propriétaire unique des interprétations sociales SCC-1A."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def _world_id(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise SocialInterpretationError("monde invalide", code="invalid_world")
        return value

    validate_world_id = _world_id

    @staticmethod
    def _key(value: Any, label: str) -> str:
        if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
            raise SocialInterpretationError(f"{label} invalide", code="invalid_request")
        return value

    validate_key = _key

    @staticmethod
    def _hypotheses(value: Any, label: str) -> tuple[str, ...]:
        if value is None:
            return ()
        if not isinstance(value, (list, tuple)) or len(value) > _MAX_HYPOTHESES:
            raise SocialInterpretationError(f"{label} invalides", code="invalid_interpretation")
        result: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise SocialInterpretationError(f"{label} invalides", code="invalid_interpretation")
            normalized = item.strip()
            if not 1 <= len(normalized) <= _MAX_HYPOTHESIS_LENGTH:
                raise SocialInterpretationError(f"{label} invalides", code="invalid_interpretation")
            if normalized not in result:
                result.append(normalized)
        return tuple(result)

    def _character_id(self, world_id: int, character_key: str) -> int:
        row = self._conn.execute(
            "SELECT id FROM character WHERE world_id = ? AND key = ?", (world_id, character_key)
        ).fetchone()
        if row is None:
            raise SocialInterpretationError("personnage introuvable", code="character_not_found")
        return row["id"]

    def _source(self, world_id: int, character_id: int, request_key: str) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT trace.id AS trace_id, trace.source_social_speech_act_id, "
            "act.speaker_character_id, act.recipient_character_id, "
            "scene.world_id AS scene_world_id "
            "FROM subjective_trace trace "
            "JOIN social_speech_act act ON act.id = trace.source_social_speech_act_id "
            "JOIN social_scene scene ON scene.id = act.scene_id "
            "WHERE trace.world_id = ? AND trace.character_id = ? "
            "AND trace.request_key = ? AND trace.fact_type = 'social_speech_act'",
            (world_id, character_id, request_key),
        ).fetchone()
        if row is None or row["scene_world_id"] != world_id:
            raise SocialInterpretationError("source SCC-0 non admissible", code="source_not_accessible")
        if row["speaker_character_id"] == character_id:
            role = "speaker"
        elif row["recipient_character_id"] == character_id:
            role = "addressee"
        else:
            role = "side_participant"
        return row, role

    def _support_ids(self, world_id: int, character_id: int, keys: Iterable[str], source_id: int) -> tuple[int, ...]:
        ids: list[int] = []
        for request_key in keys:
            row = self._conn.execute(
                "SELECT trace.id FROM subjective_trace trace "
                "WHERE trace.world_id = ? AND trace.character_id = ? AND trace.request_key = ?",
                (world_id, character_id, request_key),
            ).fetchone()
            if row is None:
                raise SocialInterpretationError("preuve secondaire non admissible", code="support_not_accessible")
            if row["id"] == source_id or row["id"] in ids:
                raise SocialInterpretationError("preuve secondaire dupliquée", code="duplicate_support")
            ids.append(row["id"])
        return tuple(ids)

    @staticmethod
    def _provenance(value: Any) -> dict[str, Any]:
        if value is None:
            value = {"origin_kind": "direct_controlled", "model_id": None,
                     "provider_version": None, "snapshot_fingerprint": None,
                     "provider_turn_id": None}
        if not isinstance(value, dict) or set(value) != _TECHNICAL_PROVENANCE_KEYS:
            raise SocialInterpretationError("provenance technique invalide", code="invalid_interpretation")
        origin = value["origin_kind"]
        if origin not in {"llm", "direct_controlled"}:
            raise SocialInterpretationError("provenance technique invalide", code="invalid_interpretation")
        if origin == "direct_controlled":
            if any(value[key] is not None for key in _TECHNICAL_PROVENANCE_KEYS - {"origin_kind"}):
                raise SocialInterpretationError("provenance directe incohérente", code="invalid_interpretation")
            return dict(value)
        for key in ("model_id", "provider_version", "snapshot_fingerprint"):
            if not isinstance(value[key], str) or not value[key].strip() or len(value[key]) > 256:
                raise SocialInterpretationError("provenance LLM incomplète", code="invalid_interpretation")
        if not _FINGERPRINT_RE.fullmatch(value["snapshot_fingerprint"]):
            raise SocialInterpretationError("fingerprint de provenance invalide", code="invalid_interpretation")
        if value["provider_turn_id"] is not None and (not isinstance(value["provider_turn_id"], str) or not 1 <= len(value["provider_turn_id"]) <= 120):
            raise SocialInterpretationError("identifiant de tour invalide", code="invalid_interpretation")
        return dict(value)

    def _row(self, interpretation_id: int) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT interpretation.*, source.request_key AS source_trace_request_key, "
            "prior.interpretation_key AS revision_of_key "
            "FROM social_interpretation interpretation "
            "JOIN subjective_trace source ON source.id = interpretation.source_trace_id "
            "LEFT JOIN social_interpretation prior ON prior.id = interpretation.revision_of_id "
            "WHERE interpretation.id = ?", (interpretation_id,),
        ).fetchone()
        assert row is not None
        return row

    def _sheet(self, interpretation_id: int) -> dict[str, Any]:
        row = self._row(interpretation_id)
        support = self._conn.execute(
            "SELECT trace.request_key FROM social_interpretation_support support "
            "JOIN subjective_trace trace ON trace.id = support.trace_id "
            "WHERE support.interpretation_id = ? ORDER BY support.id", (interpretation_id,)
        ).fetchall()
        return {
            "public_id": row["public_id"], "interpretation_key": row["interpretation_key"],
            "world_id": row["world_id"], "character_id": row["character_id"],
            "source_trace_id": row["source_trace_id"],
            "source_trace_request_key": row["source_trace_request_key"],
            "interaction_role": row["interaction_role"],
            "understanding_status": row["understanding_status"],
            "meaning_hypotheses": json.loads(row["meaning_hypotheses_json"]),

            "revision_of_key": row["revision_of_key"],
            "supporting_trace_request_keys": tuple(item["request_key"] for item in support),
            "origin_kind": row["origin_kind"], "model_id": row["model_id"],
            "provider_version": row["provider_version"], "snapshot_fingerprint": row["snapshot_fingerprint"],
            "provider_turn_id": row["provider_turn_id"],
            "created_at": row["created_at"],
        }

    def create(
        self, world_id: Any, character_key: Any, interpretation_key: Any,
        source_trace_request_key: Any, *, understanding_status: Any,
        meaning_hypotheses: Any = (),
        revision_of_key: Any = None, supporting_trace_request_keys: Any = (),
        technical_provenance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        world_id = self._world_id(world_id)
        character_key = self._key(character_key, "propriétaire")
        interpretation_key = self._key(interpretation_key, "interprétation")
        source_trace_request_key = self._key(source_trace_request_key, "source")
        if understanding_status not in _STATUSES:
            raise SocialInterpretationError("statut de compréhension invalide", code="invalid_interpretation")
        meaning = self._hypotheses(meaning_hypotheses, "hypothèses de sens")
        if understanding_status == "unresolved" and meaning:
            raise SocialInterpretationError("unresolved ne peut contenir d'hypothèse", code="invalid_interpretation")
        if understanding_status == "clear" and not meaning:
            raise SocialInterpretationError("clear exige une hypothèse de sens", code="invalid_interpretation")
        if understanding_status == "ambiguous" and len(meaning) < 2:
            raise SocialInterpretationError("ambiguous exige plusieurs hypothèses de sens", code="invalid_interpretation")
        if revision_of_key is not None:
            revision_of_key = self._key(revision_of_key, "révision")
        if not isinstance(supporting_trace_request_keys, (list, tuple)):
            raise SocialInterpretationError("preuves secondaires invalides", code="invalid_interpretation")
        support_keys = tuple(self._key(key, "preuve secondaire") for key in supporting_trace_request_keys)
        character_id = self._character_id(world_id, character_key)
        source, role = self._source(world_id, character_id, source_trace_request_key)
        prior_id = None
        if revision_of_key is not None:
            prior = self._conn.execute(
                "SELECT id, source_trace_id FROM social_interpretation "
                "WHERE world_id = ? AND character_id = ? AND interpretation_key = ?",
                (world_id, character_id, revision_of_key),
            ).fetchone()
            if prior is None:
                raise SocialInterpretationError("interprétation à réviser introuvable", code="revision_not_found")
            if prior["source_trace_id"] != source["trace_id"]:
                raise SocialInterpretationError("révision sur une source différente", code="revision_source_conflict")
            if not support_keys:
                raise SocialInterpretationError("une révision exige une preuve secondaire", code="revision_support_required")
            prior_id = prior["id"]
        support_ids = self._support_ids(world_id, character_id, support_keys, source["trace_id"])
        provenance = self._provenance(technical_provenance)
        existing = self._conn.execute(
            "SELECT id, source_trace_id, interaction_role, understanding_status, "
            "meaning_hypotheses_json, revision_of_id, origin_kind, model_id, "
            "provider_version, snapshot_fingerprint, provider_turn_id "
            "FROM social_interpretation WHERE world_id = ? AND character_id = ? AND interpretation_key = ?",
            (world_id, character_id, interpretation_key),
        ).fetchone()
        expected = (source["trace_id"], role, understanding_status, _json(list(meaning)),
                    prior_id, provenance.get("origin_kind"), provenance.get("model_id"),
                    provenance.get("provider_version"), provenance.get("snapshot_fingerprint"),
                    provenance.get("provider_turn_id"))
        if existing is not None:
            actual = (existing["source_trace_id"], existing["interaction_role"], existing["understanding_status"],
                      existing["meaning_hypotheses_json"], existing["revision_of_id"],
                      existing["origin_kind"], existing["model_id"], existing["provider_version"],
                      existing["snapshot_fingerprint"], existing["provider_turn_id"])
            current_support = tuple(row["trace_id"] for row in self._conn.execute(
                "SELECT trace_id FROM social_interpretation_support WHERE interpretation_id = ? ORDER BY id",
                (existing["id"],)
            ).fetchall())
            if actual != expected or current_support != support_ids:
                raise SocialInterpretationError("clé d'interprétation déjà utilisée", code="interpretation_key_conflict")
            return self._sheet(existing["id"])
        now = self._clock.now_iso()
        with transaction(self._conn) as conn:
            cur = conn.execute(
                "INSERT INTO social_interpretation "
                "(public_id, world_id, character_id, interpretation_key, source_trace_id, interaction_role, "
                "understanding_status, meaning_hypotheses_json, legacy_motive_hypotheses_json, revision_of_id, created_at, "
                "origin_kind, model_id, provider_version, snapshot_fingerprint, provider_turn_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_uuid(), world_id, character_id, interpretation_key, source["trace_id"], role,
                 understanding_status, _json(list(meaning)), _json([]), prior_id, now,
                 provenance.get("origin_kind"), provenance.get("model_id"), provenance.get("provider_version"),
                 provenance.get("snapshot_fingerprint"), provenance.get("provider_turn_id")),
            )
            interpretation_id = cur.lastrowid
            for trace_id in support_ids:
                conn.execute(
                    "INSERT INTO social_interpretation_support (interpretation_id, trace_id, created_at) VALUES (?, ?, ?)",
                    (interpretation_id, trace_id, now),
                )
            event_type = "interpretation_revised" if prior_id is not None else "interpretation_created"
            conn.execute(
                "INSERT INTO social_interpretation_event "
                "(world_id, character_id, interpretation_id, event_type, payload_json, recorded_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (world_id, character_id, interpretation_id, event_type,
                 _json({"interpretation_id": interpretation_id, "source_trace_id": source["trace_id"],
                        "revision_of_id": prior_id, "support_trace_ids": list(support_ids)}), now),
            )
        return self._sheet(interpretation_id)

    def get(self, world_id: Any, character_key: Any, interpretation_key: Any) -> dict[str, Any]:
        world_id = self._world_id(world_id)
        character_key = self._key(character_key, "propriétaire")
        interpretation_key = self._key(interpretation_key, "interprétation")
        character_id = self._character_id(world_id, character_key)
        row = self._conn.execute(
            "SELECT id FROM social_interpretation WHERE world_id = ? AND character_id = ? AND interpretation_key = ?",
            (world_id, character_id, interpretation_key),
        ).fetchone()
        if row is None:
            raise SocialInterpretationError("interprétation introuvable", code="interpretation_not_found")
        return self._sheet(row["id"])

    def list(self, world_id: Any, character_key: Any, *, limit: Any = 50) -> tuple[dict[str, Any], ...]:
        world_id = self._world_id(world_id)
        character_key = self._key(character_key, "propriétaire")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
            raise SocialInterpretationError("limite invalide", code="invalid_limit")
        character_id = self._character_id(world_id, character_key)
        rows = self._conn.execute(
            "SELECT id FROM social_interpretation WHERE world_id = ? AND character_id = ? "
            "ORDER BY created_at DESC, id DESC LIMIT ?", (world_id, character_id, limit)
        ).fetchall()
        return tuple(self._sheet(row["id"]) for row in rows)

    def create_interpretation(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.create(*args, **kwargs)
