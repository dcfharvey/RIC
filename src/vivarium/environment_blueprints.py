"""Blueprints environnementaux et instanciation canonique d'un monde neuf."""

from __future__ import annotations

import json
import sqlite3
from collections import deque
from typing import Any

from .db import transaction
from .environment_archetypes import CONNECTOR, PLACE
from .registry import KEY_RE as _KEY_RE
from .util import Clock, new_uuid, now_utc
from .world import SOURCE_SYSTEM, WORLD_NAME_MAX_LEN, WorldEngine, append_event as _append_event

_POLICIES = frozenset({"none", "strong_anchor"})
_CONNECTOR_STATES = frozenset({"available", "closed", "blocked"})


class BlueprintError(ValueError):
    """Blueprint invalide, non publiable ou instanciation refusee."""


class EnvironmentBlueprintService:
    """Gere les blueprints figes puis les instancie atomiquement."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def _key(value: Any, label: str = "cle") -> str:
        if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
            raise BlueprintError(f"{label} invalide")
        return value

    @staticmethod
    def _version(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise BlueprintError("version invalide")
        return value

    @staticmethod
    def _name(value: Any, label: str = "nom") -> str:
        if not isinstance(value, str) or not (clean := value.strip()) or len(clean) > WORLD_NAME_MAX_LEN:
            raise BlueprintError(f"{label} invalide")
        return clean

    @classmethod
    def _reference(cls, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict) or set(value) != {"key", "version"}:
            raise BlueprintError("reference d'archetype invalide")
        return {"key": cls._key(value["key"], "cle d'archetype"), "version": cls._version(value["version"])}

    @classmethod
    def _topology(cls, value: Any, location_keys: set[str]) -> dict[str, Any]:
        if not isinstance(value, dict) or "policy" not in value:
            raise BlueprintError("politique topologique invalide")
        policy = value["policy"]
        if policy not in _POLICIES:
            raise BlueprintError("politique topologique invalide")
        if policy == "none":
            if set(value) != {"policy"}:
                raise BlueprintError("politique topologique invalide")
            return {"policy": "none"}
        if set(value) != {"policy", "anchor"}:
            raise BlueprintError("politique topologique invalide")
        anchor = cls._key(value["anchor"], "ancre")
        if anchor not in location_keys:
            raise BlueprintError("ancre topologique inconnue")
        return {"policy": "strong_anchor", "anchor": anchor}

    @classmethod
    def _definition(cls, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict) or set(value) != {"name", "locations", "connectors", "objects", "topology"}:
            raise BlueprintError("definition de blueprint invalide")
        if not isinstance(value["locations"], list) or not value["locations"]:
            raise BlueprintError("lieux invalides")
        locations: list[dict[str, Any]] = []
        location_keys: set[str] = set()
        for item in value["locations"]:
            if not isinstance(item, dict) or set(item) != {"key", "name", "archetype"}:
                raise BlueprintError("lieu de blueprint invalide")
            key = cls._key(item["key"], "cle de lieu")
            if key in location_keys:
                raise BlueprintError("cle de lieu dupliquee")
            location_keys.add(key)
            locations.append({"key": key, "name": cls._name(item["name"], "nom de lieu"), "archetype": cls._reference(item["archetype"])})

        if not isinstance(value["connectors"], list):
            raise BlueprintError("connecteurs invalides")
        connectors: list[dict[str, Any]] = []
        connector_keys: set[str] = set()
        for item in value["connectors"]:
            if not isinstance(item, dict) or set(item) not in (
                {"key", "from", "to", "archetype"},
                {"key", "from", "to", "archetype", "initial_state"},
            ):
                raise BlueprintError("connecteur de blueprint invalide")
            key = cls._key(item["key"], "cle de connecteur")
            source, target = cls._key(item["from"], "origine"), cls._key(item["to"], "destination")
            if key in connector_keys or source not in location_keys or target not in location_keys or source == target:
                raise BlueprintError("connecteur de blueprint invalide")
            connector_keys.add(key)
            initial_state = item.get("initial_state", "available")
            if initial_state not in _CONNECTOR_STATES:
                raise BlueprintError("etat initial de connecteur invalide")
            connectors.append({
                "key": key, "from": source, "to": target,
                "archetype": cls._reference(item["archetype"]),
                "initial_state": initial_state,
            })

        if not isinstance(value["objects"], list):
            raise BlueprintError("objets initiaux invalides")
        objects: list[dict[str, Any]] = []
        object_keys: set[str] = set()
        required_object = {"key", "name", "kind", "location", "portable", "container_capacity", "state"}
        for item in value["objects"]:
            if not isinstance(item, dict) or set(item) != required_object:
                raise BlueprintError("objet initial invalide")
            key, location = cls._key(item["key"], "cle d'objet"), cls._key(item["location"], "lieu d'objet")
            capacity = item["container_capacity"]
            if key in object_keys or location not in location_keys or not isinstance(item["portable"], bool):
                raise BlueprintError("objet initial invalide")
            if capacity is not None and (not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 0):
                raise BlueprintError("objet initial invalide")
            object_keys.add(key)
            objects.append({
                "key": key, "name": cls._name(item["name"], "nom d'objet"),
                "kind": cls._key(item["kind"], "type d'objet"), "location": location,
                "portable": item["portable"], "container_capacity": capacity,
                "state": cls._key(item["state"], "etat d'objet"),
            })
        return {
            "name": cls._name(value["name"]), "locations": locations, "connectors": connectors,
            "objects": objects, "topology": cls._topology(value["topology"], location_keys),
        }

    @staticmethod
    def _json(value: dict[str, Any]) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

    @staticmethod
    def _published_archetype(
        conn: sqlite3.Connection, archetype_kind: str, reference: dict[str, Any]
    ) -> sqlite3.Row:
        row = conn.execute(
            "SELECT a.id, a.key, v.version, v.contract_json FROM environment_archetype a "
            "JOIN environment_archetype_version v ON v.archetype_id = a.id "
            "WHERE a.archetype_kind = ? AND a.key = ? AND v.version = ? AND v.status = 'published'",
            (archetype_kind, reference["key"], reference["version"]),
        ).fetchone()
        if row is None:
            raise BlueprintError("archetype publie introuvable")
        return row

    @classmethod
    def _resolve(cls, conn: sqlite3.Connection, definition: dict[str, Any]) -> dict[str, Any]:
        locations: list[dict[str, Any]] = []
        location_map: dict[str, dict[str, Any]] = {}
        for item in definition["locations"]:
            archetype = cls._published_archetype(conn, PLACE, item["archetype"])
            resolved = {**item, "archetype_contract": json.loads(archetype["contract_json"]), "archetype_id": archetype["id"]}
            locations.append(resolved)
            location_map[item["key"]] = resolved
        connectors: list[dict[str, Any]] = []
        directed: set[tuple[str, str]] = set()
        for item in definition["connectors"]:
            archetype = cls._published_archetype(conn, CONNECTOR, item["archetype"])
            contract = json.loads(archetype["contract_json"])
            initial_state = item.get("initial_state", "available")
            if initial_state not in _CONNECTOR_STATES:
                raise BlueprintError("etat initial de connecteur invalide")
            if initial_state == "closed" and "closable" not in contract["features"]:
                raise BlueprintError("connecteur ferme non fermable")
            edges = [(item["from"], item["to"])]
            if contract["directions"] == "bidirectional":
                edges.append((item["to"], item["from"]))
            if any(edge in directed for edge in edges):
                raise BlueprintError("connecteurs produisent une arete dupliquee")
            directed.update(edges)
            connectors.append({
                **item,
                "initial_state": initial_state,
                "archetype_contract": contract,
                "archetype_id": archetype["id"],
                "directed_edges": edges,
            })
        if definition["topology"]["policy"] == "strong_anchor":
            anchor = definition["topology"]["anchor"]
            outgoing: dict[str, set[str]] = {key: set() for key in location_map}
            incoming: dict[str, set[str]] = {key: set() for key in location_map}
            for source, target in directed:
                outgoing[source].add(target)
                incoming[target].add(source)
            def reached(graph: dict[str, set[str]]) -> set[str]:
                seen, queue = {anchor}, deque([anchor])
                while queue:
                    for target in graph[queue.popleft()]:
                        if target not in seen:
                            seen.add(target); queue.append(target)
                return seen
            if reached(outgoing) != set(location_map) or reached(incoming) != set(location_map):
                raise BlueprintError("topologie strong_anchor non connexe")
        return {**definition, "locations": locations, "connectors": connectors}

    @staticmethod
    def _provenance_definition(resolved: dict[str, Any]) -> dict[str, Any]:
        """Snapshot logique : aucun rowid interne ne devient une preuve de monde."""
        return {
            **resolved,
            "locations": [
                {key: value for key, value in item.items() if key != "archetype_id"}
                for item in resolved["locations"]
            ],
            "connectors": [
                {key: value for key, value in item.items() if key != "archetype_id"}
                for item in resolved["connectors"]
            ],
        }

    def create_draft(self, key: Any, definition: Any) -> dict[str, Any]:
        key, definition = self._key(key), self._definition(definition)
        with transaction(self._conn) as conn:
            blueprint = conn.execute("SELECT id FROM environment_blueprint WHERE key = ?", (key,)).fetchone()
            if blueprint is None:
                cur = conn.execute("INSERT INTO environment_blueprint (public_id, key, created_at) VALUES (?, ?, ?)", (new_uuid(), key, now_utc()))
                blueprint_id, version = cur.lastrowid, 1
            else:
                blueprint_id = blueprint["id"]
                if conn.execute("SELECT 1 FROM environment_blueprint_version WHERE blueprint_id = ? AND status = 'draft'", (blueprint_id,)).fetchone():
                    raise BlueprintError("un brouillon existe deja pour ce blueprint")
                version = conn.execute("SELECT COALESCE(MAX(version), 0) + 1 FROM environment_blueprint_version WHERE blueprint_id = ?", (blueprint_id,)).fetchone()[0]
            conn.execute("INSERT INTO environment_blueprint_version (blueprint_id, version, status, definition_json, created_at) VALUES (?, ?, 'draft', ?, ?)", (blueprint_id, version, self._json(definition), now_utc()))
        return self.get_version(key, version)

    def install_published_catalog(
        self, entries: Any
    ) -> list[dict[str, Any]]:
        """Installe des blueprints v1 validés, atomiquement et sans dérive."""
        try:
            raw = tuple(entries)
        except TypeError as exc:
            raise BlueprintError("catalogue de blueprints invalide") from exc
        normalized: list[tuple[str, dict[str, Any], str]] = []
        seen: set[str] = set()
        for entry in raw:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise BlueprintError("catalogue de blueprints invalide")
            key = self._key(entry[0])
            definition = self._definition(entry[1])
            if key in seen:
                raise BlueprintError("catalogue de blueprints contient un doublon")
            seen.add(key)
            normalized.append((key, definition, self._json(definition)))
        with transaction(self._conn) as conn:
            for _key, definition, _definition_json in normalized:
                self._resolve(conn, definition)
            for key, _definition, definition_json in normalized:
                blueprint = conn.execute(
                    "SELECT id FROM environment_blueprint WHERE key = ?", (key,)
                ).fetchone()
                if blueprint is None:
                    cur = conn.execute(
                        "INSERT INTO environment_blueprint (public_id, key, created_at) VALUES (?, ?, ?)",
                        (new_uuid(), key, now_utc()),
                    )
                    conn.execute(
                        "INSERT INTO environment_blueprint_version "
                        "(blueprint_id, version, status, definition_json, created_at, published_at) "
                        "VALUES (?, 1, 'published', ?, ?, ?)",
                        (cur.lastrowid, definition_json, now_utc(), now_utc()),
                    )
                    continue
                version = conn.execute(
                    "SELECT status, definition_json FROM environment_blueprint_version "
                    "WHERE blueprint_id = ? AND version = 1",
                    (blueprint["id"],),
                ).fetchone()
                if (
                    version is None
                    or version["status"] != "published"
                    or version["definition_json"] != definition_json
                ):
                    raise BlueprintError("catalogue de blueprints incompatible avec l'existant")
        return [self.get_version(key, 1) for key, _definition, _json in normalized]

    def get_version(self, key: Any, version: Any) -> dict[str, Any]:
        key, version = self._key(key), self._version(version)
        row = self._conn.execute(
            "SELECT b.key, v.version, v.status, v.definition_json, v.created_at, v.published_at "
            "FROM environment_blueprint b JOIN environment_blueprint_version v ON v.blueprint_id = b.id "
            "WHERE b.key = ? AND v.version = ?", (key, version)
        ).fetchone()
        if row is None:
            raise BlueprintError("blueprint introuvable")
        return {"key": row["key"], "version": row["version"], "status": row["status"], "definition": json.loads(row["definition_json"]), "created_at": row["created_at"], "published_at": row["published_at"]}

    def publish(self, key: Any, version: Any) -> dict[str, Any]:
        key, version = self._key(key), self._version(version)
        with transaction(self._conn) as conn:
            row = conn.execute(
                "SELECT v.id, v.status, v.definition_json FROM environment_blueprint b "
                "JOIN environment_blueprint_version v ON v.blueprint_id = b.id WHERE b.key = ? AND v.version = ?",
                (key, version),
            ).fetchone()
            if row is None:
                raise BlueprintError("blueprint introuvable")
            if row["status"] != "draft":
                raise BlueprintError("seul un brouillon peut etre publie")
            self._resolve(conn, json.loads(row["definition_json"]))
            conn.execute("UPDATE environment_blueprint_version SET status = 'published', published_at = ? WHERE id = ?", (now_utc(), row["id"]))
        return self.get_version(key, version)

    def instantiate(self, key: Any, version: Any, *, world_name: Any | None = None) -> dict[str, Any]:
        """Instancie un monde entier ou rien, depuis un blueprint publie."""
        key, version = self._key(key), self._version(version)
        if world_name is not None:
            world_name = self._name(world_name, "nom de monde")
        with transaction(self._conn) as conn:
            row = conn.execute(
                "SELECT b.id AS blueprint_id, v.definition_json FROM environment_blueprint b "
                "JOIN environment_blueprint_version v ON v.blueprint_id = b.id "
                "WHERE b.key = ? AND v.version = ? AND v.status = 'published'", (key, version)
            ).fetchone()
            if row is None:
                raise BlueprintError("blueprint publie introuvable")
            resolved = self._resolve(conn, json.loads(row["definition_json"]))
            engine = WorldEngine(conn, clock=self._clock)
            world_id, now = engine.create_empty_world_in_transaction(
                conn, world_name or resolved["name"], seeded=False
            )
            location_ids: dict[str, int] = {}
            for item in resolved["locations"]:
                cur = conn.execute(
                    "INSERT INTO location (public_id, world_id, key, name, kind, capacity, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (new_uuid(), world_id, item["key"], item["name"], item["archetype"]["key"], item["archetype_contract"]["max_occupancy"], now),
                )
                location_ids[item["key"]] = cur.lastrowid
                conn.execute(
                    "INSERT INTO world_location_origin (location_id, world_id, archetype_id, archetype_version, resolved_contract_json, instantiated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (cur.lastrowid, world_id, item["archetype_id"], item["archetype"]["version"], self._json(item["archetype_contract"]), now),
                )
            topology = resolved["topology"]
            if topology["policy"] == "strong_anchor":
                conn.execute("UPDATE world_topology_policy SET policy_key = 'strong_anchor', anchor_location_id = ?, configured_at = ? WHERE world_id = ?", (location_ids[topology["anchor"]], now, world_id))
            for item in resolved["connectors"]:
                cur = conn.execute(
                    "INSERT INTO world_connector (public_id, world_id, key, archetype_id, archetype_version, from_location_id, to_location_id, directions, state, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (new_uuid(), world_id, item["key"], item["archetype_id"], item["archetype"]["version"], location_ids[item["from"]], location_ids[item["to"]], item["archetype_contract"]["directions"], item["initial_state"], now),
                )
                for source, target in item["directed_edges"]:
                    conn.execute(
                        "INSERT INTO location_link (public_id, world_id, from_location_id, to_location_id, kind, created_at, connector_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (new_uuid(), world_id, location_ids[source], location_ids[target], item["archetype"]["key"], now, cur.lastrowid),
                    )
            for item in resolved["objects"]:
                conn.execute(
                    "INSERT INTO world_object (public_id, world_id, location_id, key, name, kind, state, created_at, portable, container_capacity, parent_object_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                    (new_uuid(), world_id, location_ids[item["location"]], item["key"], item["name"], item["kind"], item["state"], now, int(item["portable"]), item["container_capacity"]),
                )
            conn.execute(
                "INSERT INTO world_environment_origin (world_id, blueprint_id, blueprint_version, resolved_definition_json, instantiated_at) VALUES (?, ?, ?, ?, ?)",
                (world_id, row["blueprint_id"], version, self._json(self._provenance_definition(resolved)), now),
            )
            _append_event(
                conn, world_id, SOURCE_SYSTEM, "environment_blueprint_instantiated",
                {"blueprint": key, "blueprint_version": version, "locations": len(resolved["locations"]), "connectors": len(resolved["connectors"]), "objects": len(resolved["objects"]), "topology_policy": topology["policy"]},
                occurred_at=now, recorded_at=now,
            )
        return WorldEngine(self._conn, clock=self._clock).get_world(world_id)

    def origin(self, world_id: Any) -> dict[str, Any]:
        if not isinstance(world_id, int) or isinstance(world_id, bool) or world_id < 1:
            raise BlueprintError("monde invalide")
        row = self._conn.execute(
            "SELECT b.key, o.blueprint_version, o.resolved_definition_json, o.instantiated_at "
            "FROM world_environment_origin o JOIN environment_blueprint b ON b.id = o.blueprint_id WHERE o.world_id = ?", (world_id,)
        ).fetchone()
        if row is None:
            raise BlueprintError("provenance d'environnement introuvable")
        return {"blueprint_key": row["key"], "blueprint_version": row["blueprint_version"], "resolved_definition": json.loads(row["resolved_definition_json"]), "instantiated_at": row["instantiated_at"]}
