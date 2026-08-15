"""Relations directionnelles, limites personnelles et permissions explicites."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Mapping

from .db import transaction
from .registry import KEY_RE as _KEY_RE
from .util import Clock, new_uuid


_RELATION_DIMENSIONS = frozenset({
    "familiarity_milli", "trust_milli", "affection_milli", "respect_milli",
    "safety_milli", "intimacy_milli", "attraction_milli", "irritation_milli",
})
_BOUNDARY_DOMAINS = frozenset({"body", "space", "time", "attention", "information", "property", "relationship", "decision"})
_BOUNDARY_ORIGINS = frozenset({"declared", "implicit"})


class SocialError(ValueError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _world_id(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise SocialError("monde invalide", code="invalid_social")
    return value


def _key(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise SocialError(f"{label} invalide", code="invalid_social")
    return value


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise SocialError(f"{label} invalide", code="invalid_social")
    return {str(key): item for key, item in value.items()}


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _dimensions(value: Any) -> dict[str, int]:
    value = _object(value, "impact relationnel")
    if not value or set(value) - _RELATION_DIMENSIONS:
        raise SocialError("impact relationnel invalide", code="invalid_social")
    out: dict[str, int] = {}
    for key, amount in value.items():
        if not isinstance(amount, int) or isinstance(amount, bool) or not -200 <= amount <= 200:
            raise SocialError("impact relationnel hors limite", code="invalid_social")
        if key == "familiarity_milli" and amount < 0:
            raise SocialError("familiarité ne peut pas décroître sans protocole", code="invalid_social")
        out[key] = amount
    return out


def _baseline() -> dict[str, int]:
    return {dimension: 0 for dimension in _RELATION_DIMENSIONS}


class SocialService:
    """Ecrit des états sociaux seulement depuis une source privée traçable."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _character_id(self, world_id: int, character_key: str) -> int:
        row = self._conn.execute(
            "SELECT id FROM character WHERE world_id = ? AND key = ?", (world_id, character_key)
        ).fetchone()
        if row is None:
            raise SocialError("personnage introuvable", code="character_not_found")
        return row["id"]

    @staticmethod
    def _relationship_sheet(row: sqlite3.Row) -> dict[str, Any]:
        return {"target_character_key": row["target_key"], "dimensions": json.loads(row["dimensions_json"])}

    def adjust_relationship(
        self,
        world_id: Any,
        owner_key: Any,
        target_key: Any,
        evidence_key: Any,
        *,
        trace_request_key: Any,
        impact: Any,
        context: Any = None,
    ) -> dict[str, Any]:
        """Applique un petit impact causal, jamais un score LLM direct."""
        world_id = _world_id(world_id)
        owner_key = _key(owner_key, "propriétaire")
        target_key = _key(target_key, "cible")
        evidence_key = _key(evidence_key, "preuve")
        trace_request_key = _key(trace_request_key, "source")
        impact = _dimensions(impact)
        context = {} if context is None else _object(context, "contexte")
        owner_id = self._character_id(world_id, owner_key)
        target_id = self._character_id(world_id, target_key)
        if owner_id == target_id:
            raise SocialError("relation à soi interdite", code="invalid_social")
        now = self._clock.now_iso()
        with transaction(self._conn) as conn:
            trace = conn.execute(
                "SELECT id FROM subjective_trace WHERE world_id = ? AND character_id = ? AND request_key = ?",
                (world_id, owner_id, trace_request_key),
            ).fetchone()
            if trace is None:
                raise SocialError("preuve relationnelle non accessible", code="relationship_source_not_accessible")
            view = conn.execute(
                "SELECT * FROM relationship_view WHERE world_id = ? AND owner_character_id = ? AND target_character_id = ?",
                (world_id, owner_id, target_id),
            ).fetchone()
            initialized = view is None
            if view is None:
                cur = conn.execute(
                    "INSERT INTO relationship_view (public_id, world_id, owner_character_id, target_character_id, dimensions_json, last_event_id, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, NULL, ?, ?)",
                    (new_uuid(), world_id, owner_id, target_id, _json(_baseline()), now, now),
                )
                view_id, current = cur.lastrowid, _baseline()
            else:
                view_id, current = view["id"], json.loads(view["dimensions_json"])
            existing = conn.execute(
                "SELECT id FROM relationship_evidence WHERE view_id = ? AND trace_id = ?", (view_id, trace["id"])
            ).fetchone()
            if existing is not None:
                row = conn.execute(
                    "SELECT view.dimensions_json, target.key AS target_key FROM relationship_view view "
                    "JOIN character target ON target.id=view.target_character_id WHERE view.id = ?", (view_id,)
                ).fetchone()
                assert row is not None
                return self._relationship_sheet(row)
            updated = dict(current)
            for dimension, delta in impact.items():
                upper = 1000
                lower = 0 if dimension == "familiarity_milli" else -1000
                updated[dimension] = max(lower, min(upper, updated[dimension] + delta))
            conn.execute(
                "INSERT INTO relationship_evidence (view_id, trace_id, impact_json, context_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (view_id, trace["id"], _json(impact), _json(context), now),
            )
            event = conn.execute(
                "INSERT INTO relationship_event (world_id, owner_character_id, target_character_id, view_id, event_type, payload_json, recorded_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (world_id, owner_id, target_id, view_id, "relationship_initialized" if initialized else "relationship_changed", _json({"evidence_key": evidence_key, "impact": impact}), now),
            )
            conn.execute(
                "UPDATE relationship_view SET dimensions_json = ?, last_event_id = ?, updated_at = ? WHERE id = ?",
                (_json(updated), event.lastrowid, now, view_id),
            )
        row = self._conn.execute(
            "SELECT view.dimensions_json, target.key AS target_key FROM relationship_view view "
            "JOIN character target ON target.id=view.target_character_id WHERE view.id = ?", (view_id,)
        ).fetchone()
        assert row is not None
        return self._relationship_sheet(row)

    def relationship(self, world_id: Any, owner_key: Any, target_key: Any) -> dict[str, Any] | None:
        world_id = _world_id(world_id)
        owner_id = self._character_id(world_id, _key(owner_key, "propriétaire"))
        target_id = self._character_id(world_id, _key(target_key, "cible"))
        row = self._conn.execute(
            "SELECT view.dimensions_json, target.key AS target_key FROM relationship_view view "
            "JOIN character target ON target.id=view.target_character_id "
            "WHERE view.world_id = ? AND view.owner_character_id = ? AND view.target_character_id = ?",
            (world_id, owner_id, target_id),
        ).fetchone()
        return None if row is None else self._relationship_sheet(row)

    def relationships(self, world_id: Any, owner_key: Any, *, limit: int = 12) -> tuple[dict[str, Any], ...]:
        world_id = _world_id(world_id)
        owner_id = self._character_id(world_id, _key(owner_key, "propriétaire"))
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
            raise SocialError("limite de relations invalide", code="invalid_social")
        rows = self._conn.execute(
            "SELECT view.dimensions_json, target.key AS target_key FROM relationship_view view "
            "JOIN character target ON target.id=view.target_character_id "
            "WHERE view.world_id = ? AND view.owner_character_id = ? ORDER BY view.updated_at DESC, view.id DESC LIMIT ?",
            (world_id, owner_id, limit),
        ).fetchall()
        return tuple(self._relationship_sheet(row) for row in rows)

    def active_boundaries(self, world_id: Any, character_key: Any, *, limit: int = 12) -> tuple[dict[str, Any], ...]:
        world_id = _world_id(world_id)
        character_id = self._character_id(world_id, _key(character_key, "personnage"))
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
            raise SocialError("limite de limites invalide", code="invalid_social")
        rows = self._conn.execute(
            "SELECT boundary_key, domain, scope_json, origin FROM personal_boundary "
            "WHERE world_id = ? AND character_id = ? AND status = 'active' ORDER BY created_at DESC, id DESC LIMIT ?",
            (world_id, character_id, limit),
        ).fetchall()
        return tuple({"boundary_key": row["boundary_key"], "domain": row["domain"], "scope": json.loads(row["scope_json"]), "origin": row["origin"]} for row in rows)

    def declare_boundary(
        self, world_id: Any, character_key: Any, boundary_key: Any, *, domain: Any, scope: Any, origin: Any = "declared",
    ) -> dict[str, Any]:
        world_id = _world_id(world_id)
        character_key = _key(character_key, "personnage")
        boundary_key = _key(boundary_key, "limite")
        if domain not in _BOUNDARY_DOMAINS or origin not in _BOUNDARY_ORIGINS:
            raise SocialError("limite invalide", code="invalid_social")
        scope = _object(scope, "portée")
        character_id = self._character_id(world_id, character_key)
        now = self._clock.now_iso()
        with transaction(self._conn) as conn:
            existing = conn.execute(
                "SELECT * FROM personal_boundary WHERE world_id = ? AND character_id = ? AND boundary_key = ?",
                (world_id, character_id, boundary_key),
            ).fetchone()
            if existing is not None:
                return {"boundary_key": existing["boundary_key"], "domain": existing["domain"], "scope": json.loads(existing["scope_json"]), "status": existing["status"], "origin": existing["origin"]}
            cur = conn.execute(
                "INSERT INTO personal_boundary (public_id, world_id, character_id, boundary_key, domain, scope_json, origin, status, last_event_id, created_at, revoked_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 'active', NULL, ?, NULL)",
                (new_uuid(), world_id, character_id, boundary_key, domain, _json(scope), origin, now),
            )
            boundary_id = cur.lastrowid
            event = conn.execute(
                "INSERT INTO personal_boundary_event (world_id, character_id, boundary_id, event_type, payload_json, recorded_at) "
                "VALUES (?, ?, ?, 'boundary_declared', ?, ?)",
                (world_id, character_id, boundary_id, _json({"boundary_key": boundary_key}), now),
            )
            conn.execute("UPDATE personal_boundary SET last_event_id = ? WHERE id = ?", (event.lastrowid, boundary_id))
        return {"boundary_key": boundary_key, "domain": domain, "scope": scope, "status": "active", "origin": origin}

    def revoke_boundary(self, world_id: Any, character_key: Any, boundary_key: Any, *, reason: Any) -> dict[str, Any]:
        world_id = _world_id(world_id)
        character_key = _key(character_key, "personnage")
        boundary_key = _key(boundary_key, "limite")
        reason = _key(reason, "raison")
        character_id = self._character_id(world_id, character_key)
        now = self._clock.now_iso()
        with transaction(self._conn) as conn:
            row = conn.execute(
                "SELECT * FROM personal_boundary WHERE world_id = ? AND character_id = ? AND boundary_key = ?",
                (world_id, character_id, boundary_key),
            ).fetchone()
            if row is None:
                raise SocialError("limite introuvable", code="boundary_not_found")
            if row["status"] == "revoked":
                return {"boundary_key": row["boundary_key"], "domain": row["domain"], "scope": json.loads(row["scope_json"]), "status": "revoked", "origin": row["origin"]}
            event = conn.execute(
                "INSERT INTO personal_boundary_event (world_id, character_id, boundary_id, event_type, payload_json, recorded_at) VALUES (?, ?, ?, 'boundary_revoked', ?, ?)",
                (world_id, character_id, row["id"], _json({"reason": reason}), now),
            )
            conn.execute("UPDATE personal_boundary SET status = 'revoked', last_event_id = ?, revoked_at = ? WHERE id = ?", (event.lastrowid, now, row["id"]))
        return {"boundary_key": row["boundary_key"], "domain": row["domain"], "scope": json.loads(row["scope_json"]), "status": "revoked", "origin": row["origin"]}

    def grant_permission(
        self, world_id: Any, issuer_key: Any, recipient_key: Any, permission_key: Any, *, action_key: Any, scope: Any, expires_at: Any = None,
    ) -> dict[str, Any]:
        """Déclare une permission ciblée; elle ne prouve ni capacité ni consentement général."""
        world_id = _world_id(world_id)
        issuer_key = _key(issuer_key, "émettrice")
        recipient_key = _key(recipient_key, "bénéficiaire")
        permission_key = _key(permission_key, "permission")
        action_key = _key(action_key, "action")
        scope = _object(scope, "portée")
        if expires_at is not None and (not isinstance(expires_at, str) or not expires_at):
            raise SocialError("expiration invalide", code="invalid_social")
        issuer_id = self._character_id(world_id, issuer_key)
        recipient_id = self._character_id(world_id, recipient_key)
        if issuer_id == recipient_id:
            raise SocialError("permission à soi interdite", code="invalid_social")
        now = self._clock.now_iso()
        with transaction(self._conn) as conn:
            existing = conn.execute(
                "SELECT * FROM situational_permission WHERE world_id = ? AND issuer_character_id = ? AND recipient_character_id = ? AND permission_key = ?",
                (world_id, issuer_id, recipient_id, permission_key),
            ).fetchone()
            if existing is not None:
                return self._permission_sheet(existing)
            cur = conn.execute(
                "INSERT INTO situational_permission (public_id, world_id, issuer_character_id, recipient_character_id, permission_key, action_key, scope_json, status, last_event_id, created_at, expires_at, revoked_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 'granted', NULL, ?, ?, NULL)",
                (new_uuid(), world_id, issuer_id, recipient_id, permission_key, action_key, _json(scope), now, expires_at),
            )
            permission_id = cur.lastrowid
            event = conn.execute(
                "INSERT INTO situational_permission_event (world_id, issuer_character_id, recipient_character_id, permission_id, event_type, payload_json, recorded_at) "
                "VALUES (?, ?, ?, ?, 'permission_granted', ?, ?)",
                (world_id, issuer_id, recipient_id, permission_id, _json({"permission_key": permission_key}), now),
            )
            conn.execute("UPDATE situational_permission SET last_event_id = ? WHERE id = ?", (event.lastrowid, permission_id))
        row = self._conn.execute("SELECT * FROM situational_permission WHERE id = ?", (permission_id,)).fetchone()
        assert row is not None
        return self._permission_sheet(row)

    @staticmethod
    def _permission_sheet(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "permission_key": row["permission_key"], "action_key": row["action_key"],
            "scope": json.loads(row["scope_json"]), "status": row["status"], "expires_at": row["expires_at"],
        }

    def revoke_permission(self, world_id: Any, issuer_key: Any, recipient_key: Any, permission_key: Any, *, reason: Any) -> dict[str, Any]:
        world_id = _world_id(world_id)
        issuer_key = _key(issuer_key, "émettrice")
        recipient_key = _key(recipient_key, "bénéficiaire")
        permission_key = _key(permission_key, "permission")
        reason = _key(reason, "raison")
        issuer_id = self._character_id(world_id, issuer_key)
        recipient_id = self._character_id(world_id, recipient_key)
        now = self._clock.now_iso()
        with transaction(self._conn) as conn:
            row = conn.execute(
                "SELECT * FROM situational_permission WHERE world_id = ? AND issuer_character_id = ? AND recipient_character_id = ? AND permission_key = ?",
                (world_id, issuer_id, recipient_id, permission_key),
            ).fetchone()
            if row is None:
                raise SocialError("permission introuvable", code="permission_not_found")
            if row["status"] == "revoked":
                return self._permission_sheet(row)
            event = conn.execute(
                "INSERT INTO situational_permission_event (world_id, issuer_character_id, recipient_character_id, permission_id, event_type, payload_json, recorded_at) "
                "VALUES (?, ?, ?, ?, 'permission_revoked', ?, ?)",
                (world_id, issuer_id, recipient_id, row["id"], _json({"reason": reason}), now),
            )
            conn.execute("UPDATE situational_permission SET status = 'revoked', last_event_id = ?, revoked_at = ? WHERE id = ?", (event.lastrowid, now, row["id"]))
        row = self._conn.execute("SELECT * FROM situational_permission WHERE id = ?", (row["id"],)).fetchone()
        assert row is not None
        return self._permission_sheet(row)

    def has_active_permission(self, world_id: Any, issuer_key: Any, recipient_key: Any, *, action_key: Any, scope: Any, at: Any = None) -> bool:
        """Lecture stricte : permission explicite, actuelle et de portée identique seulement."""
        world_id = _world_id(world_id)
        issuer_id = self._character_id(world_id, _key(issuer_key, "émettrice"))
        recipient_id = self._character_id(world_id, _key(recipient_key, "bénéficiaire"))
        action_key = _key(action_key, "action")
        scope_json = _json(_object(scope, "portée"))
        at = self._clock.now_iso() if at is None else at
        if not isinstance(at, str) or not at:
            raise SocialError("instant invalide", code="invalid_social")
        row = self._conn.execute(
            "SELECT 1 FROM situational_permission WHERE world_id = ? AND issuer_character_id = ? AND recipient_character_id = ? "
            "AND action_key = ? AND scope_json = ? AND status = 'granted' AND (expires_at IS NULL OR expires_at > ?) LIMIT 1",
            (world_id, issuer_id, recipient_id, action_key, scope_json, at),
        ).fetchone()
        return row is not None
