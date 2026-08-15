"""Pipeline administratif préparé pour les mutations sensibles.

Les actions prises en charge sont ``rename_world``, ``add_link`` et
``remove_link``.
Le contrat reste identique : plan immuable, hash exact, impact sémantique,
contrôle optimiste de la version du monde, expiration et application
idempotente. Les plans/audits administratifs restent distincts des faits
canoniques ; l'action appliquée continue d'écrire son propre événement.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import timedelta
from typing import Any

from .db import transaction
from .spatial import GraphEngine, GraphError
from .util import Clock, new_uuid, parse_iso, to_iso
from .world import WorldEngine, WorldError

DEFAULT_PLAN_TTL_SECONDS = 300
MAX_PLAN_TTL_SECONDS = 3600


class AdminChangeError(RuntimeError):
    """Refus stable d'un plan administratif."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class AdminChangeService:
    """Frontière d'écriture admin : prepare → validate → impact → confirm.

    ``world_event_seq`` est la version optimiste d'un monde : toute écriture
    canonique concurrente crée une séquence nouvelle et force un nouveau plan.
    """

    ACTIONS = frozenset({"rename_world", "add_link", "remove_link"})

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _world(self) -> WorldEngine:
        return WorldEngine(self._conn, clock=self._clock)

    @staticmethod
    def _world_id(value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise AdminChangeError("world_id invalide", code="invalid_parameters")
        return value

    @staticmethod
    def _ttl(value: Any) -> int:
        if value is None:
            return DEFAULT_PLAN_TTL_SECONDS
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 1 <= value <= MAX_PLAN_TTL_SECONDS
        ):
            raise AdminChangeError("durée du plan invalide", code="invalid_parameters")
        return value

    @staticmethod
    def _hash(
        action_key: str,
        world_id: int,
        world_event_seq: int,
        payload: dict[str, Any],
        impact: dict[str, Any],
        expires_at: str,
    ) -> str:
        body = _canonical_json(
            {
                "action_key": action_key,
                "world_id": world_id,
                "world_event_seq": world_event_seq,
                "payload": payload,
                "impact": impact,
                "expires_at": expires_at,
            }
        )
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    @staticmethod
    def _audit(
        conn: sqlite3.Connection,
        plan_id: int,
        event_type: str,
        occurred_at: str,
        recorded_at: str,
        payload: dict[str, Any],
    ) -> None:
        seq = conn.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 FROM admin_audit_event "
            "WHERE change_plan_id = ?",
            (plan_id,),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO admin_audit_event "
            "(public_id, change_plan_id, seq, event_type, occurred_at, recorded_at, payload_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (new_uuid(), plan_id, seq, event_type, occurred_at, recorded_at, _canonical_json(payload)),
        )

    @staticmethod
    def _row_to_plan(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["public_id"],
            "action": row["action_key"],
            "status": row["status"],
            "world_id": row["world_id"],
            "world_event_seq": row["world_event_seq"],
            "payload": json.loads(row["payload_json"]),
            "impact": json.loads(row["impact_json"]),
            "hash": row["plan_hash"],
            "expires_at": row["expires_at"],
            "prepared_at": row["prepared_at"],
            "applied_at": row["applied_at"],
            "result": (
                json.loads(row["applied_result_json"])
                if row["applied_result_json"] is not None
                else None
            ),
        }

    def _plan_row(self, plan_id: Any) -> sqlite3.Row:
        if not isinstance(plan_id, str) or not plan_id:
            raise AdminChangeError("identifiant de plan invalide", code="invalid_parameters")
        row = self._conn.execute(
            "SELECT * FROM admin_change_plan WHERE public_id = ?", (plan_id,)
        ).fetchone()
        if row is None:
            raise AdminChangeError("plan introuvable", code="plan_not_found")
        return row

    def _store_prepared_plan(
        self,
        conn: sqlite3.Connection,
        *,
        world_id: int,
        action: str,
        payload: dict[str, Any],
        impact: dict[str, Any],
        ttl_seconds: int,
    ) -> dict[str, Any]:
        """Fige un plan et son audit dans la transaction de préparation."""
        if action not in self.ACTIONS:  # garde interne contre un SQL administratif libre
            raise RuntimeError(f"action administrative non supportée : {action}")
        now = self._clock.now_iso()
        expires_at = to_iso(self._clock.now() + timedelta(seconds=ttl_seconds))
        canonical_at = self._world().read_canonical_time(world_id)
        world_event_seq = conn.execute(
            "SELECT COALESCE(MAX(seq), 0) FROM canonical_event WHERE world_id = ?",
            (world_id,),
        ).fetchone()[0]
        plan_hash = self._hash(
            action, world_id, world_event_seq, payload, impact, expires_at
        )
        cur = conn.execute(
            "INSERT INTO admin_change_plan "
            "(public_id, world_id, action_key, status, payload_json, impact_json, "
            "world_event_seq, plan_hash, expires_at, prepared_at) "
            "VALUES (?, ?, ?, 'prepared', ?, ?, ?, ?, ?, ?)",
            (
                new_uuid(), world_id, action, _canonical_json(payload),
                _canonical_json(impact), world_event_seq, plan_hash, expires_at, now,
            ),
        )
        plan_id = cur.lastrowid
        self._audit(
            conn,
            plan_id,
            "change_prepared",
            canonical_at,
            now,
            {"action": action, "world_event_seq": world_event_seq, "hash": plan_hash},
        )
        row = conn.execute(
            "SELECT * FROM admin_change_plan WHERE id = ?", (plan_id,)
        ).fetchone()
        return self._row_to_plan(row)

    def prepare_rename_world(
        self, world_id: Any, name: Any, *, ttl_seconds: Any = None
    ) -> dict[str, Any]:
        """Fige un renommage non sensible sans modifier le monde.

        Le plan conserve le nom normalisé, l'ancien nom et la dernière séquence
        canonique. Il devient donc invalide si le monde a changé entre la
        préparation et la confirmation.
        """
        world_id = self._world_id(world_id)
        ttl_seconds = self._ttl(ttl_seconds)
        try:
            normalized = WorldEngine.normalize_world_name(name)
        except WorldError as exc:
            raise AdminChangeError(str(exc), code=exc.code) from None

        with transaction(self._conn) as conn:
            world = conn.execute(
                "SELECT name FROM worlds WHERE id = ?", (world_id,)
            ).fetchone()
            if world is None:
                raise AdminChangeError("monde introuvable", code="world_not_found")
            if world["name"] == normalized:
                raise AdminChangeError("ce nom est déjà appliqué", code="no_effect")
            payload = {"from": world["name"], "to": normalized}
            impact = {
                "classification": "non_sensitive",
                "summary": "Renomme le monde sans modifier de personnage, lieu ou règle.",
                "affected": {"world": 1, "characters": 0, "locations": 0},
                "requires_snapshot": False,
                "requires_confirmation": True,
            }
            return self._store_prepared_plan(
                conn,
                world_id=world_id,
                action="rename_world",
                payload=payload,
                impact=impact,
                ttl_seconds=ttl_seconds,
            )

    def prepare_add_link(
        self,
        world_id: Any,
        from_location: Any,
        to_location: Any,
        *,
        bidirectional: Any = True,
        kind: Any = "door",
        ttl_seconds: Any = None,
    ) -> dict[str, Any]:
        """Fige l'ajout d'un passage entre deux lieux déjà existants."""
        world_id = self._world_id(world_id)
        ttl_seconds = self._ttl(ttl_seconds)
        try:
            from_location, to_location, bidirectional, kind = GraphEngine.normalize_link_request(
                from_location, to_location, bidirectional, kind
            )
        except GraphError as exc:
            raise AdminChangeError(str(exc), code=exc.code) from None
        with transaction(self._conn) as conn:
            if conn.execute("SELECT 1 FROM worlds WHERE id = ?", (world_id,)).fetchone() is None:
                raise AdminChangeError("monde introuvable", code="world_not_found")
            graph = GraphEngine(conn, clock=self._clock)
            try:
                graph.location_id(world_id, from_location)
                graph.location_id(world_id, to_location)
            except GraphError as exc:
                raise AdminChangeError(str(exc), code=exc.code) from None
            directions = [(from_location, to_location)]
            if bidirectional:
                directions.append((to_location, from_location))
            if any(graph.can_traverse(world_id, origin, destination) for origin, destination in directions):
                raise AdminChangeError("au moins une arête du passage existe déjà", code="no_effect")
            payload = {
                "from": from_location,
                "to": to_location,
                "bidirectional": bidirectional,
                "kind": kind,
            }
            impact = {
                "classification": "world_topology",
                "summary": "Ajoute un passage et modifie les trajets possibles entre deux lieux.",
                "affected": {
                    "world": 1,
                    "locations": 2,
                    "directed_links_created": len(directions),
                    "characters": 0,
                },
                "requires_snapshot": False,
                "requires_confirmation": True,
            }
            return self._store_prepared_plan(
                conn,
                world_id=world_id,
                action="add_link",
                payload=payload,
                impact=impact,
                ttl_seconds=ttl_seconds,
            )

    def prepare_remove_link(
        self,
        world_id: Any,
        from_location: Any,
        to_location: Any,
        *,
        bidirectional: Any = True,
        ttl_seconds: Any = None,
    ) -> dict[str, Any]:
        """Fige une fermeture sûre; toute isolation est refusée avant plan."""
        world_id = self._world_id(world_id)
        ttl_seconds = self._ttl(ttl_seconds)
        try:
            from_location, to_location, bidirectional = GraphEngine.normalize_remove_link_request(
                from_location, to_location, bidirectional
            )
        except GraphError as exc:
            raise AdminChangeError(str(exc), code=exc.code) from None
        with transaction(self._conn) as conn:
            if conn.execute("SELECT 1 FROM worlds WHERE id = ?", (world_id,)).fetchone() is None:
                raise AdminChangeError("monde introuvable", code="world_not_found")
            try:
                preview = GraphEngine(conn, clock=self._clock).preview_remove_link(
                    world_id, from_location, to_location, bidirectional=bidirectional
                )
            except GraphError as exc:
                raise AdminChangeError(str(exc), code=exc.code) from None
            connectivity = preview["connectivity"]
            if not connectivity["ok"]:
                raise AdminChangeError(
                    "fermeture refusée : elle isolerait un ou plusieurs lieux "
                    f"(depuis ancre={connectivity['unreachable_from_anchor']}, "
                    f"vers ancre={connectivity['unreachable_to_anchor']})",
                    code="would_isolate_location",
                )
            payload = {
                "from": from_location,
                "to": to_location,
                "bidirectional": bidirectional,
            }
            impact = {
                "classification": "world_topology",
                "summary": "Retire un passage sans isoler aucun lieu du salon.",
                "affected": {
                    "world": 1,
                    "locations": 2,
                    "directed_links_removed": preview["directed_links_removed"],
                    "characters": 0,
                },
                "connectivity_after": connectivity,
                "requires_snapshot": False,
                "requires_confirmation": True,
            }
            return self._store_prepared_plan(
                conn,
                world_id=world_id,
                action="remove_link",
                payload=payload,
                impact=impact,
                ttl_seconds=ttl_seconds,
            )

    def validate(self, plan_id: Any) -> dict[str, Any]:
        """Réévalue les préconditions sans écriture ni événement."""
        row = self._plan_row(plan_id)
        plan = self._row_to_plan(row)
        current_seq = self._conn.execute(
            "SELECT COALESCE(MAX(seq), 0) FROM canonical_event WHERE world_id = ?",
            (plan["world_id"],),
        ).fetchone()[0]
        findings: list[dict[str, Any]] = []
        if plan["status"] != "prepared":
            findings.append(self._finding(
                "plan_not_prepared", "error", plan, "prepared", plan["status"],
                "Prépare un nouveau changement pour toute nouvelle application.",
            ))
        if parse_iso(self._clock.now_iso()) > parse_iso(plan["expires_at"]):
            findings.append(self._finding(
                "plan_expired", "error", plan, "confirmation avant expiration", plan["expires_at"],
                "Prépare un nouveau changement.",
            ))
        if current_seq != plan["world_event_seq"]:
            findings.append(self._finding(
                "world_changed", "error", plan, plan["world_event_seq"], current_seq,
                "Le monde a changé : prépare un nouveau plan.",
            ))
        return {"plan_id": plan["id"], "valid": not findings, "findings": findings}

    @staticmethod
    def _finding(
        code: str,
        severity: str,
        plan: dict[str, Any],
        expected: Any,
        observed: Any,
        suggestion: str,
    ) -> dict[str, Any]:
        return {
            "code": code,
            "severity": severity,
            "target": {"kind": "world", "id": plan["world_id"]},
            "evidence": {"plan_id": plan["id"], "action": plan["action"]},
            "expected": expected,
            "observed": observed,
            "suggestion": suggestion,
        }

    def impact(self, plan_id: Any) -> dict[str, Any]:
        """Retourne le rapport d'impact figé, accompagné de sa validité actuelle."""
        plan = self._row_to_plan(self._plan_row(plan_id))
        validation = self.validate(plan_id)
        return {"plan_id": plan["id"], "impact": plan["impact"], "validation": validation}

    def confirm(self, plan_id: Any, plan_hash: Any) -> dict[str, Any]:
        """Confirme le plan exact et applique son action une seule fois."""
        if not isinstance(plan_hash, str) or len(plan_hash) != 64:
            raise AdminChangeError("hash de plan invalide", code="invalid_parameters")
        if not isinstance(plan_id, str) or not plan_id:
            raise AdminChangeError("identifiant de plan invalide", code="invalid_parameters")

        with transaction(self._conn) as conn:
            row = conn.execute(
                "SELECT * FROM admin_change_plan WHERE public_id = ?", (plan_id,)
            ).fetchone()
            if row is None:
                raise AdminChangeError("plan introuvable", code="plan_not_found")
            plan = self._row_to_plan(row)
            if plan_hash != plan["hash"]:
                raise AdminChangeError("le hash ne correspond pas au plan", code="hash_mismatch")
            if plan["status"] == "applied":
                return {
                    "plan_id": plan["id"],
                    "status": "already_applied",
                    "result": plan["result"],
                }
            if parse_iso(self._clock.now_iso()) > parse_iso(plan["expires_at"]):
                raise AdminChangeError("le plan a expiré", code="plan_expired")
            current_seq = conn.execute(
                "SELECT COALESCE(MAX(seq), 0) FROM canonical_event WHERE world_id = ?",
                (plan["world_id"],),
            ).fetchone()[0]
            if current_seq != plan["world_event_seq"]:
                raise AdminChangeError("le monde a changé depuis la préparation", code="world_changed")

            if plan["action"] == "rename_world":
                applied = self._world().rename_world_in_transaction(
                    conn,
                    plan["world_id"],
                    plan["payload"]["to"],
                    admin_change_id=plan["id"],
                )
                result = {"world_id": applied["id"], "name": applied["name"]}
            elif plan["action"] == "add_link":
                applied = GraphEngine(conn, clock=self._clock).add_link_in_transaction(
                    conn,
                    plan["world_id"],
                    plan["payload"]["from"],
                    plan["payload"]["to"],
                    bidirectional=plan["payload"]["bidirectional"],
                    kind=plan["payload"]["kind"],
                    admin_change_id=plan["id"],
                )
                result = {
                    field: applied[field]
                    for field in ("from", "to", "bidirectional", "kind")
                }
            elif plan["action"] == "remove_link":
                try:
                    applied = GraphEngine(conn, clock=self._clock).remove_link_in_transaction(
                        conn,
                        plan["world_id"],
                        plan["payload"]["from"],
                        plan["payload"]["to"],
                        bidirectional=plan["payload"]["bidirectional"],
                        admin_change_id=plan["id"],
                    )
                except GraphError as exc:
                    raise AdminChangeError(str(exc), code=exc.code) from None
                result = {
                    field: applied[field]
                    for field in ("from", "to", "bidirectional", "directed_links_removed")
                }
            else:  # plan impossible hors corruption manuelle de la base
                raise RuntimeError(f"action de plan inconnue : {plan['action']}")
            applied_at = self._clock.now_iso()
            conn.execute(
                "UPDATE admin_change_plan SET status = 'applied', applied_at = ?, "
                "applied_result_json = ? WHERE id = ?",
                (applied_at, _canonical_json(result), row["id"]),
            )
            self._audit(
                conn,
                row["id"],
                "change_applied",
                applied["canonical_at"],
                applied_at,
                {"action": plan["action"], "result": result},
            )
        return {"plan_id": plan["id"], "status": "applied", "result": result}
