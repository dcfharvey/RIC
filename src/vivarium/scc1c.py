"""Admission SCC-1C bornée, sans sélection sémantique ni raccordement runtime."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from typing import Any

from .db import transaction
from .registry import _KEY_RE
from .util import Clock, new_uuid


POLICY_VERSION = "scc1c-structural-v1"
_ROLES = frozenset(("speaker", "addressee", "side_participant"))
_DECISIONS = frozenset(("selected", "not_selected"))
_OUTCOMES = frozenset(("deferred", "provider_unavailable", "interpreted"))


class SCC1CError(ValueError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class StructuralAdmissionPolicy:
    """Throttle stable fondé sur l'identité de trace, jamais sur son contenu.

    Le rôle est conservé comme donnée dérivée et comme entrée structurelle,
    mais aucun rôle ne garantit ou interdit une sélection.
    """

    version = POLICY_VERSION

    def decide(self, trace_public_id: str, interaction_role: str) -> str:
        bucket = hashlib.sha256(f"{self.version}:{interaction_role}:{trace_public_id}".encode()).digest()[0]
        return "selected" if bucket % 2 == 0 else "not_selected"


class FixedAdmissionPolicy:
    """Politique déterministe de test; elle n'est pas la politique de production."""

    def __init__(self, decision: str, version: str = "test-fixed-v1") -> None:
        if decision not in _DECISIONS:
            raise ValueError("invalid fixed decision")
        self.version, self.decision = version, decision

    def decide(self, trace_public_id: str, interaction_role: str) -> str:
        return self.decision


@dataclass(frozen=True)
class SCC1CAdmission:
    public_id: str
    world_id: int
    character_key: str
    trace_request_key: str
    trace_id: int
    interaction_role: str
    decision: str
    policy_version: str
    decided_at: str


@dataclass(frozen=True)
class SCC1CAttempt:
    public_id: str
    attempt_key: str
    outcome: str
    detail_code: str | None
    recorded_at: str


def _key(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise SCC1CError(f"{label} invalide", code="invalid_request")
    return value


class SCC1CAdmissionService:
    """Propriétaire de l'admission seulement; SCC-1B reste son propre owner."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None, policy: Any = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()
        self._policy = policy or StructuralAdmissionPolicy()

    def _character(self, world_id: int, character_key: str) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT id, key FROM character WHERE world_id = ? AND key = ?", (world_id, character_key)
        ).fetchone()
        if row is None:
            raise SCC1CError("personnage introuvable", code="character_not_found")
        return row

    def _source(self, world_id: int, character_id: int, request_key: str) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT trace.id AS trace_id, trace.public_id AS trace_public_id, trace.request_key, "
            "act.speaker_character_id, act.recipient_character_id "
            "FROM subjective_trace trace JOIN social_speech_act act "
            "ON act.id = trace.source_social_speech_act_id "
            "JOIN social_scene scene ON scene.id = act.scene_id "
            "WHERE trace.world_id = ? AND trace.character_id = ? AND trace.request_key = ? "
            "AND trace.fact_type = 'social_speech_act' AND scene.world_id = ?",
            (world_id, character_id, request_key, world_id),
        ).fetchone()
        if row is None:
            raise SCC1CError("source SCC-0 non admissible", code="source_not_accessible")
        if row["speaker_character_id"] == character_id:
            role = "speaker"
        elif row["recipient_character_id"] == character_id:
            role = "addressee"
        else:
            role = "side_participant"
        return row, role

    @staticmethod
    def _sheet(row: sqlite3.Row) -> SCC1CAdmission:
        return SCC1CAdmission(
            row["public_id"], row["world_id"], row["character_key"], row["request_key"],
            row["trace_id"], row["interaction_role"], row["decision"], row["policy_version"], row["decided_at"],
        )

    def _row(self, admission_id: int) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT admission.*, ch.key AS character_key, trace.request_key "
            "FROM scc1c_admission admission JOIN character ch ON ch.id = admission.character_id "
            "JOIN subjective_trace trace ON trace.id = admission.trace_id WHERE admission.id = ?",
            (admission_id,),
        ).fetchone()
        assert row is not None
        return row

    def admit(self, world_id: Any, character_key: Any, trace_request_key: Any) -> SCC1CAdmission:
        if not isinstance(world_id, int) or isinstance(world_id, bool) or world_id < 1:
            raise SCC1CError("monde invalide", code="invalid_world")
        character_key = _key(character_key, "propriétaire")
        trace_request_key = _key(trace_request_key, "trace")
        character = self._character(world_id, character_key)
        source, role = self._source(world_id, character["id"], trace_request_key)
        decision = self._policy.decide(source["trace_public_id"], role)
        version = getattr(self._policy, "version", None)
        if decision not in _DECISIONS or not isinstance(version, str) or not version:
            raise SCC1CError("politique SCC-1C invalide", code="invalid_policy")
        existing = self._conn.execute(
            "SELECT id, trace_id, interaction_role, decision, policy_version FROM scc1c_admission "
            "WHERE world_id = ? AND character_id = ? AND trace_id = ?",
            (world_id, character["id"], source["trace_id"]),
        ).fetchone()
        expected = (source["trace_id"], role, decision, version)
        if existing is not None:
            if tuple(existing[key] for key in ("trace_id", "interaction_role", "decision", "policy_version")) != expected:
                raise SCC1CError("clé d'admission déjà utilisée", code="admission_key_conflict")
            return self._sheet(self._row(existing["id"]))
        now = self._clock.now_iso()
        with transaction(self._conn) as conn:
            cur = conn.execute(
                "INSERT INTO scc1c_admission (public_id, world_id, character_id, trace_id, interaction_role, decision, policy_version, decided_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (new_uuid(), world_id, character["id"], source["trace_id"], role, decision, version, now),
            )
            admission_id = cur.lastrowid
        return self._sheet(self._row(admission_id))

    def record_attempt(self, admission: SCC1CAdmission, attempt_key: Any, outcome: Any, detail_code: Any = None) -> SCC1CAttempt:
        if not isinstance(admission, SCC1CAdmission) or admission.decision != "selected":
            raise SCC1CError("une tentative exige une admission sélectionnée", code="admission_not_selected")
        attempt_key = _key(attempt_key, "tentative")
        if outcome not in _OUTCOMES:
            raise SCC1CError("résultat technique invalide", code="invalid_attempt")
        if detail_code is not None:
            detail_code = _key(detail_code, "détail")
        character_id = self._character(admission.world_id, admission.character_key)["id"]
        admission_row = self._conn.execute(
            "SELECT id FROM scc1c_admission WHERE public_id = ? AND world_id = ? AND character_id = ? AND decision = 'selected'",
            (admission.public_id, admission.world_id, character_id),
        ).fetchone()
        if admission_row is None:
            raise SCC1CError("admission inconnue", code="admission_not_found")
        if outcome == "interpreted":
            interpretation = self._conn.execute(
                "SELECT 1 FROM social_interpretation WHERE world_id = ? AND character_id = ? AND source_trace_id = ? LIMIT 1",
                (admission.world_id, character_id, admission.trace_id),
            ).fetchone()
            if interpretation is None:
                raise SCC1CError("interprétation SCC-1B absente", code="interpretation_not_found")
        row = self._conn.execute(
            "SELECT * FROM scc1c_attempt WHERE world_id = ? AND character_id = ? AND attempt_key = ?",
            (admission.world_id, character_id, attempt_key),
        ).fetchone()
        expected = (outcome, detail_code)
        if row is not None:
            if (row["outcome"], row["detail_code"]) != expected:
                raise SCC1CError("clé de tentative déjà utilisée", code="attempt_key_conflict")
            return SCC1CAttempt(row["public_id"], row["attempt_key"], row["outcome"], row["detail_code"], row["recorded_at"])
        now = self._clock.now_iso()
        with transaction(self._conn) as conn:
            conn.execute(
                "INSERT INTO scc1c_attempt (public_id, world_id, character_id, admission_id, attempt_key, outcome, detail_code, recorded_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (new_uuid(), admission.world_id, character_id, admission_row["id"], attempt_key, outcome, detail_code, now),
            )
        row = self._conn.execute(
            "SELECT * FROM scc1c_attempt WHERE world_id = ? AND character_id = ? AND attempt_key = ?",
            (admission.world_id, character_id, attempt_key),
        ).fetchone()
        return SCC1CAttempt(row["public_id"], row["attempt_key"], row["outcome"], row["detail_code"], row["recorded_at"])

    def list(self, world_id: Any, character_key: Any) -> tuple[SCC1CAdmission, ...]:
        if not isinstance(world_id, int) or isinstance(world_id, bool) or world_id < 1:
            raise SCC1CError("monde invalide", code="invalid_world")
        character_key = _key(character_key, "propriétaire")
        character = self._character(world_id, character_key)
        rows = self._conn.execute(
            "SELECT admission.*, ch.key AS character_key, trace.request_key FROM scc1c_admission admission "
            "JOIN character ch ON ch.id = admission.character_id JOIN subjective_trace trace ON trace.id = admission.trace_id "
            "WHERE admission.world_id = ? AND admission.character_id = ? ORDER BY admission.decided_at, admission.id",
            (world_id, character["id"]),
        ).fetchall()
        return tuple(self._sheet(row) for row in rows)
