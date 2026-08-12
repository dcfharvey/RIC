"""Fondations persistantes, inactives et privees du futur arbitrage d'actions.

Ce module ne compare aucun score, ne cree aucune ``IntentProposal`` et ne
mutile jamais le canon. Les donnees qu'il conserve preparent seulement les
politiques, liens subjectifs et traces operateur des futurs bancs synthetiques.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from typing import Any, Mapping

from .db import transaction
from .registry import _KEY_RE
from .util import Clock, new_uuid, parse_iso, to_iso


_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_POLICY_FIELDS = frozenset({
    "schema_version", "source_mappings", "correlation_groups", "aggregation",
    "current_action_inertia", "quasi_equality", "reassessment",
})


class ActionArbitrationError(ValueError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ActionArbitrationPolicy:
    policy_key: str
    version: int
    configuration: Mapping[str, Any]
    provenance: str
    created_at: str


def _key(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise ActionArbitrationError(f"{field} invalide", code="invalid_configuration")
    return value


def _version(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ActionArbitrationError("version invalide", code="invalid_configuration")
    return value


def _json(value: Any, *, field: str) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise ActionArbitrationError(f"{field} invalide", code="invalid_configuration") from exc


def _policy_payload(value: Any) -> dict[str, Any]:
    """Valide une politique explicite sans imposer de calibration de production."""
    if not isinstance(value, Mapping) or set(value) != _POLICY_FIELDS or value.get("schema_version") != 1:
        raise ActionArbitrationError("politique d'arbitrage invalide", code="invalid_configuration")
    payload = {key: value[key] for key in _POLICY_FIELDS}
    if any(not isinstance(payload[key], Mapping) for key in _POLICY_FIELDS - {"schema_version"}):
        raise ActionArbitrationError("politique d'arbitrage incomplete", code="invalid_configuration")
    return payload


class ActionArbitrationFoundationService:
    """Unique owner du catalogue, assignment et audit prives de cette fondation."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _world_id(self, value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ActionArbitrationError("monde invalide", code="invalid_world")
        if self._conn.execute("SELECT 1 FROM worlds WHERE id = ?", (value,)).fetchone() is None:
            raise ActionArbitrationError("monde introuvable", code="world_not_found")
        return value

    def register_policy(self, policy_key: Any, version: Any, configuration: Any, provenance: Any) -> ActionArbitrationPolicy:
        key, ver = _key(policy_key, field="politique"), _version(version)
        payload, origin, now = _policy_payload(configuration), _key(provenance, field="provenance"), self._clock.now_iso()
        try:
            with transaction(self._conn) as conn:
                conn.execute("INSERT INTO action_arbitration_policy (public_id,policy_key,version,policy_json,provenance,created_at) VALUES (?,?,?,?,?,?)", (new_uuid(),key,ver,_json(payload,field="politique"),origin,now))
        except sqlite3.IntegrityError as exc:
            raise ActionArbitrationError("politique d'arbitrage deja enregistree", code="duplicate_policy") from exc
        return self.policy(key, ver)

    def policy(self, policy_key: Any, version: Any) -> ActionArbitrationPolicy:
        key, ver = _key(policy_key, field="politique"), _version(version)
        row = self._conn.execute("SELECT policy_key,version,policy_json,provenance,created_at FROM action_arbitration_policy WHERE policy_key=? AND version=?", (key,ver)).fetchone()
        if row is None:
            raise ActionArbitrationError("politique d'arbitrage introuvable", code="policy_not_found")
        return ActionArbitrationPolicy(row["policy_key"],int(row["version"]),_policy_payload(json.loads(row["policy_json"])),row["provenance"],row["created_at"])

    def assign_policy(self, world_id: Any, policy_key: Any, version: Any, provenance: Any) -> ActionArbitrationPolicy:
        world, policy = self._world_id(world_id), self.policy(policy_key,version)
        origin, now = _key(provenance, field="provenance"), self._clock.now_iso()
        policy_id = self._conn.execute("SELECT id FROM action_arbitration_policy WHERE policy_key=? AND version=?",(policy.policy_key,policy.version)).fetchone()["id"]
        try:
            with transaction(self._conn) as conn:
                conn.execute("INSERT INTO world_action_arbitration_policy_assignment (public_id,world_id,policy_id,assigned_at,provenance,created_at) VALUES (?,?,?,?,?,?)",(new_uuid(),world,policy_id,now,origin,now))
        except sqlite3.IntegrityError as exc:
            raise ActionArbitrationError("monde deja assigne", code="duplicate_assignment") from exc
        return policy

    def world_policy(self, world_id: Any) -> ActionArbitrationPolicy:
        world = self._world_id(world_id)
        row = self._conn.execute("SELECT p.policy_key,p.version FROM world_action_arbitration_policy_assignment a JOIN action_arbitration_policy p ON p.id=a.policy_id WHERE a.world_id=?",(world,)).fetchone()
        if row is None:
            raise ActionArbitrationError("politique d'arbitrage non assignee", code="policy_not_assigned")
        return self.policy(row["policy_key"],int(row["version"]))

    def record_private_audit(self, world_id: Any, *, frame_digest: Any, options: Any, sources: Any, result: Any, canonical_at: Any, reason_code: Any) -> int:
        """Conserve un diagnostic operateur; aucun fait canonique n'est emis."""
        world, policy = self._world_id(world_id), self.world_policy(world_id)
        if not isinstance(frame_digest,str) or not _DIGEST.fullmatch(frame_digest):
            raise ActionArbitrationError("digest de frame invalide", code="invalid_audit")
        if not isinstance(options,list) or not isinstance(sources,list) or not isinstance(result,Mapping):
            raise ActionArbitrationError("audit d'arbitrage invalide", code="invalid_audit")
        try: canonical = to_iso(parse_iso(canonical_at))
        except (TypeError, ValueError) as exc: raise ActionArbitrationError("instant canonique invalide", code="invalid_audit") from exc
        reason, now = _key(reason_code, field="raison"), self._clock.now_iso()
        policy_id = self._conn.execute("SELECT id FROM action_arbitration_policy WHERE policy_key=? AND version=?",(policy.policy_key,policy.version)).fetchone()["id"]
        with transaction(self._conn) as conn:
            cur=conn.execute("INSERT INTO action_arbitration_audit (public_id,world_id,policy_id,frame_digest,options_json,sources_json,result_json,canonical_at,reason_code,recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?)",(new_uuid(),world,policy_id,frame_digest,_json(options,field="options"),_json(sources,field="sources"),_json(dict(result),field="resultat"),canonical,reason,now))
        return int(cur.lastrowid)
