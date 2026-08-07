"""Agence CAT-0 générique pour les personnages non sapients configurés.

La politique ne connaît ni espèce ni nom. Elle transforme un petit champ
d'affordances topologiques en intention courte, puis délègue toute mutation
aux moteurs canoniques existants. Les décisions et transitions subjectives
sont append-only et explicables.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from .activities import ActivityEngine
from .connectors import AVAILABLE, WorldConnectorService
from .db import transaction
from .traversal import TraversalEngine
from .util import Clock, new_uuid, parse_iso
from .world import WorldEngine


@dataclass(frozen=True)
class NonSapientOutcome:
    character_key: str | None
    source_event_seq: int | None
    selected_action: str | None
    outcome: str | None
    reason_code: str | None
    target_key: str | None


class NonSapientAgencyCycle:
    """Traite au plus une occasion animale déterministe par tick."""

    COMPONENT_KEY = "behavior.non_sapient_agency"
    ORIGIN = "non_sapient_policy"

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _profiles(self, world_id: int) -> tuple[tuple[str, dict[str, Any]], ...]:
        rows = self._conn.execute(
            "SELECT c.key, o.resolved_initial_definition_json FROM character c "
            "JOIN character_instance_origin o ON o.character_id = c.id "
            "WHERE c.world_id = ? ORDER BY c.key",
            (world_id,),
        ).fetchall()
        found: list[tuple[str, dict[str, Any]]] = []
        for row in rows:
            try:
                components = json.loads(row["resolved_initial_definition_json"])["components"]
                cognitive = next(
                    item for item in components if item.get("key") == "cognition.profile"
                )
                agency = next(
                    item for item in components if item.get("key") == self.COMPONENT_KEY
                )
                config = agency["config"]
                if cognitive["config"]["level"] != "non_sapient":
                    continue
                if config["policy"] != "reactive_associative":
                    continue
                wake = config["wake_interval_seconds"]
                retries = config["max_obstacle_retries"]
                preferred = config["preferred_location_functions"]
                if not isinstance(wake, int) or isinstance(wake, bool) or not 30 <= wake <= 3600:
                    continue
                if not isinstance(retries, int) or isinstance(retries, bool) \
                        or not 1 <= retries <= 20:
                    continue
                if not isinstance(preferred, list) or any(
                    not isinstance(item, str) or not item for item in preferred
                ):
                    continue
                found.append((row["key"], config))
            except (KeyError, StopIteration, TypeError, ValueError):
                continue
        return tuple(found)

    def _idle_source(self, world_id: int, character_key: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT a.started_at, a.planned_end_at, l.key AS location, e.seq, e.payload "
            "FROM activity a JOIN character c ON c.id = a.character_id "
            "JOIN location l ON l.id = a.location_id "
            "JOIN canonical_event e ON e.world_id = a.world_id "
            "AND e.event_type = 'activity_started' AND e.occurred_at = a.started_at "
            "AND json_extract(e.payload, '$.character') = c.key "
            "AND json_extract(e.payload, '$.activity') = 'idle' "
            "AND json_extract(e.payload, '$.planned_end_at') = a.planned_end_at "
            "WHERE a.world_id = ? AND c.key = ? AND a.status = 'active' AND a.type = 'idle' "
            "ORDER BY e.seq DESC LIMIT 1",
            (world_id, character_key),
        ).fetchone()

    def _source_event(self, world_id: int, character_key: str, idle: sqlite3.Row) -> int | None:
        payload = json.loads(idle["payload"])
        provenance = payload.get("action_provenance") or {}
        canonical_now = parse_iso(
            WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id)
        )
        # Une attente créée par cette politique est une vraie temporisation.
        # Seul un changement de passage pertinent peut la réveiller plus tôt.
        connector_event = self._conn.execute(
            "SELECT e.seq FROM canonical_event e "
            "JOIN world_connector wc ON wc.world_id=e.world_id "
            "AND wc.key=json_extract(e.payload, '$.connector') "
            "JOIN location f ON f.id=wc.from_location_id "
            "JOIN location t ON t.id=wc.to_location_id "
            "WHERE e.world_id=? AND e.seq>? AND e.event_type='connector_state_changed' "
            "AND (f.key=? OR t.key=?) ORDER BY e.seq DESC LIMIT 1",
            (world_id, idle["seq"], idle["location"], idle["location"]),
        ).fetchone()
        if connector_event is not None:
            source = int(connector_event["seq"])
        elif provenance.get("origin") == self.ORIGIN \
                and canonical_now < parse_iso(idle["planned_end_at"]):
            return None
        else:
            source = int(idle["seq"])
        used = self._conn.execute(
            "SELECT 1 FROM non_sapient_decision_event d JOIN character c ON c.id=d.character_id "
            "WHERE d.world_id=? AND c.key=? AND d.source_event_seq=?",
            (world_id, character_key, source),
        ).fetchone()
        return None if used is not None else source

    def _adjacent(self, world_id: int, character_key: str, location: str) -> list[dict[str, Any]]:
        connectors = WorldConnectorService(self._conn, clock=self._clock).list_connectors(world_id)
        visits = {
            row["target"]: row["n"]
            for row in self._conn.execute(
                "SELECT json_extract(payload, '$.to') AS target, COUNT(*) AS n "
                "FROM canonical_event WHERE world_id=? AND event_type='character_moved' "
                "AND json_extract(payload, '$.character')=? GROUP BY target",
                (world_id, character_key),
            )
        }
        result: list[dict[str, Any]] = []
        for connector in connectors:
            if connector["from"] == location:
                target = connector["to"]
            elif connector["to"] == location and connector["directions"] == "bidirectional":
                target = connector["from"]
            else:
                continue
            result.append({
                "connector": connector["key"], "target": target,
                "state": connector["state"], "visits": int(visits.get(target, 0)),
                "functions": self._location_functions(world_id, target),
            })
        return result

    def _location_functions(self, world_id: int, location_key: str) -> list[str]:
        row = self._conn.execute(
            "SELECT o.resolved_contract_json FROM world_location_origin o "
            "JOIN location l ON l.id=o.location_id WHERE o.world_id=? AND l.key=?",
            (world_id, location_key),
        ).fetchone()
        if row is None:
            return []
        try:
            values = json.loads(row["resolved_contract_json"]).get("functions", [])
            return sorted(value for value in values if isinstance(value, str))
        except (TypeError, ValueError):
            return []

    def _active_intention(self, world_id: int, character_key: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT i.* FROM non_sapient_intention i JOIN character c ON c.id=i.character_id "
            "JOIN non_sapient_intention_transition t ON t.intention_id=i.id "
            "WHERE i.world_id=? AND c.key=? AND t.id=(SELECT MAX(t2.id) FROM "
            "non_sapient_intention_transition t2 WHERE t2.intention_id=i.id) "
            "AND t.status IN ('active','suspended') ORDER BY i.id DESC LIMIT 1",
            (world_id, character_key),
        ).fetchone()

    def _choose(
        self, candidates: list[dict[str, Any]], intention: sqlite3.Row | None,
        profile: dict[str, Any], excluded_target: str | None = None,
    ) -> dict[str, Any] | None:
        candidates = [item for item in candidates if item["target"] != excluded_target]
        if intention is not None:
            for candidate in candidates:
                if candidate["target"] == intention["target_key"]:
                    return candidate
        if not candidates:
            return None
        preferred = set(profile.get("preferred_location_functions", ()))
        # Le moindre nombre de visites produit une exploration topologique.
        # L'accessibilité départage ensuite sans effacer un obstacle unique.
        return min(
            candidates,
            key=lambda item: (
                0 if preferred.intersection(item["functions"]) else 1,
                item["visits"], 0 if item["state"] == AVAILABLE else 1,
                item["connector"], item["target"],
            ),
        )

    def _blocked_attempts(self, world_id: int, character_id: int, target: str) -> int:
        return int(self._conn.execute(
            "SELECT COUNT(*) FROM non_sapient_decision_event WHERE world_id=? "
            "AND character_id=? AND target_key=? AND outcome='blocked'",
            (world_id, character_id, target),
        ).fetchone()[0])

    @staticmethod
    def _selection_reason(
        selected: dict[str, Any], intention: sqlite3.Row | None, profile: dict[str, Any]
    ) -> str:
        if intention is not None and intention["target_key"] == selected["target"]:
            return "intention_continued"
        if set(profile["preferred_location_functions"]).intersection(selected["functions"]):
            return "preferred_local_function"
        return "least_visited_accessible"

    def _character_id(self, world_id: int, character_key: str) -> int:
        return self._conn.execute(
            "SELECT id FROM character WHERE world_id=? AND key=?",
            (world_id, character_key),
        ).fetchone()["id"]

    def _new_intention(
        self, world_id: int, character_id: int, source: int, target: str,
        effective_at: str, recorded_at: str,
    ) -> int:
        cur = self._conn.execute(
            "INSERT INTO non_sapient_intention "
            "(public_id,world_id,character_id,target_kind,target_key,origin_event_seq,created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (new_uuid(), world_id, character_id, "location", target, source, recorded_at),
        )
        self._transition(cur.lastrowid, "active", "local_opportunity", effective_at, recorded_at)
        return int(cur.lastrowid)

    def _transition(self, intention_id: int, status: str, reason: str, effective_at: str, recorded_at: str) -> None:
        self._conn.execute(
            "INSERT INTO non_sapient_intention_transition "
            "(public_id,intention_id,status,reason_code,effective_at,recorded_at) VALUES (?,?,?,?,?,?)",
            (new_uuid(), intention_id, status, reason, effective_at, recorded_at),
        )

    def _record(
        self, world_id: int, character_id: int, source: int,
        candidates: list[dict[str, Any]], action: str, target: str | None,
        outcome: str, reason: str, effective_at: str, recorded_at: str,
    ) -> None:
        self._conn.execute(
            "INSERT INTO non_sapient_decision_event "
            "(public_id,world_id,character_id,source_event_seq,candidates_json,selected_action,"
            "target_key,outcome,reason_code,decided_at,recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (new_uuid(), world_id, character_id, source,
             json.dumps(candidates, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
             action, target, outcome, reason, effective_at, recorded_at),
        )

    def _bounded_wait(
        self, world_id: int, character_key: str, location: str, wake: int,
        effective_at: str, proposal_id: str,
    ) -> None:
        activity = ActivityEngine(self._conn, clock=self._clock)
        current = activity.activity_sheet(world_id, character_key)
        if current is not None and current["type"] == "idle":
            activity.abort_activity(world_id, character_key, sim_now=effective_at)
        activity.start_activity(
            world_id, character_key, "idle", location, sim_now=effective_at,
            duration_seconds=wake,
            action_provenance={"proposal_id": proposal_id, "origin": self.ORIGIN},
        )

    def tick(self, world_id: int) -> NonSapientOutcome:
        for character_key, profile in self._profiles(world_id):
            idle = self._idle_source(world_id, character_key)
            if idle is None:
                continue
            source = self._source_event(world_id, character_key, idle)
            if source is None:
                continue
            candidates = self._adjacent(world_id, character_key, idle["location"])
            intention = self._active_intention(world_id, character_key)
            effective_at = WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id)
            recorded_at = self._clock.now_iso()
            character_id = self._character_id(world_id, character_key)
            exhausted_target = None
            if intention is not None and self._blocked_attempts(
                world_id, character_id, intention["target_key"]
            ) >= profile["max_obstacle_retries"]:
                exhausted_target = intention["target_key"]
            selected = self._choose(candidates, intention, profile, exhausted_target)
            proposal_id = f"animal_{character_key}_{source}"
            with transaction(self._conn):
                if exhausted_target is not None:
                    self._transition(
                        int(intention["id"]), "abandoned", "obstacle_retry_limit",
                        effective_at, recorded_at,
                    )
                    intention = None
                if selected is None:
                    self._bounded_wait(
                        world_id, character_key, idle["location"],
                        profile["wake_interval_seconds"], effective_at, proposal_id,
                    )
                    self._record(
                        world_id, character_id, source, candidates, "wait", None,
                        "no_opportunity", "no_local_affordance", effective_at, recorded_at,
                    )
                    return NonSapientOutcome(
                        character_key, source, "wait", "no_opportunity",
                        "no_local_affordance", None,
                    )
                if intention is None or intention["target_key"] != selected["target"]:
                    intention_id = self._new_intention(
                        world_id, character_id, source, selected["target"],
                        effective_at, recorded_at,
                    )
                else:
                    intention_id = int(intention["id"])
                selection_reason = self._selection_reason(selected, intention, profile)
                if selected["state"] != AVAILABLE:
                    self._bounded_wait(
                        world_id, character_key, idle["location"],
                        profile["wake_interval_seconds"], effective_at, proposal_id,
                    )
                    self._record(
                        world_id, character_id, source, candidates, "wait", selected["target"],
                        "blocked", f"connector_{selected['state']}", effective_at, recorded_at,
                    )
                    return NonSapientOutcome(
                        character_key, source, "wait", "blocked",
                        f"connector_{selected['state']}", selected["target"],
                    )
                activity = ActivityEngine(self._conn, clock=self._clock)
                activity.abort_activity(world_id, character_key, sim_now=effective_at)
                TraversalEngine(self._conn, clock=self._clock).traverse_character(
                    world_id, character_key, selected["connector"], selected["target"],
                    action_provenance={"proposal_id": proposal_id, "origin": self.ORIGIN},
                    sim_now=effective_at,
                )
                activity.start_activity(
                    world_id, character_key, "idle", selected["target"], sim_now=effective_at,
                    duration_seconds=profile["wake_interval_seconds"],
                    action_provenance={"proposal_id": proposal_id, "origin": self.ORIGIN},
                )
                self._transition(
                    intention_id, "completed", "target_reached", effective_at, recorded_at
                )
                self._record(
                    world_id, character_id, source, candidates, "traverse", selected["target"],
                    "accepted", selection_reason, effective_at, recorded_at,
                )
                return NonSapientOutcome(
                    character_key, source, "traverse", "accepted",
                    selection_reason, selected["target"],
                )
        return NonSapientOutcome(None, None, None, None, None, None)
