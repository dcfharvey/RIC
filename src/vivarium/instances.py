"""Instanciation canonique de personnages depuis des gabarits publiés."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from .character import CharacterEngine
from .db import transaction
from .registry import _KEY_RE
from .templates import CharacterTemplateService
from .util import Clock, new_uuid
from .world import SOURCE_SYSTEM, WorldEngine, _append_event

_DEFAULT_PROFILE = {
    "satiete_threshold_mult_milli": 1000,
    "repos_threshold_mult_milli": 1000,
    "energie_threshold_mult_milli": 1000,
    "hygiene_threshold_mult_milli": 1000,
    "rest_preference_milli": 0,
    "idle_tolerance_milli": 0,
}


class InstanceError(ValueError):
    """Instanciation refusée sans écriture partielle."""


class CharacterInstanceService:
    """Crée une entité canonique et fige son origine de gabarit dans le monde."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def instantiate(
        self,
        world_id: Any,
        template_key: Any,
        template_version: Any,
        character_key: Any,
        location_key: Any,
    ) -> dict[str, Any]:
        if not isinstance(world_id, int) or isinstance(world_id, bool) or world_id < 1:
            raise InstanceError("monde invalide")
        if not isinstance(template_version, int) or isinstance(template_version, bool) or template_version < 1:
            raise InstanceError("version de gabarit invalide")
        if not isinstance(template_key, str) or not _KEY_RE.fullmatch(template_key):
            raise InstanceError("clé de gabarit invalide")
        if not isinstance(character_key, str) or not _KEY_RE.fullmatch(character_key):
            raise InstanceError("clé de personnage invalide")
        if not isinstance(location_key, str) or not _KEY_RE.fullmatch(location_key):
            raise InstanceError("clé de lieu invalide")

        with transaction(self._conn) as conn:
            template = conn.execute(
                "SELECT t.id AS template_id, v.status, v.definition_json, v.component_bindings_json "
                "FROM character_template t JOIN character_template_version v "
                "ON v.template_id = t.id WHERE t.key = ? AND v.version = ?",
                (template_key, template_version),
            ).fetchone()
            if template is None or template["status"] != "published":
                raise InstanceError("gabarit non publié")
            bindings = json.loads(template["component_bindings_json"])
            validation_errors = CharacterTemplateService._validation_errors(conn, bindings)
            if validation_errors:
                raise InstanceError(validation_errors[0]["code"])
            definition = json.loads(template["definition_json"])
            resolved_initial_definition = {
                "definition": definition,
                "components": bindings,
            }
            name = definition.get("name")
            if not isinstance(name, str) or not name.strip():
                raise InstanceError("le gabarit doit déclarer un nom non vide")
            if definition.get("adult") is not True:
                raise InstanceError("le gabarit doit déclarer adult à true")

            location = conn.execute(
                "SELECT id FROM location WHERE world_id = ? AND key = ?",
                (world_id, location_key),
            ).fetchone()
            if location is None:
                raise InstanceError("lieu ou monde introuvable")
            existing = conn.execute(
                "SELECT 1 FROM character WHERE world_id = ? AND key = ?",
                (world_id, character_key),
            ).fetchone()
            if existing is not None:
                raise InstanceError("clé de personnage déjà utilisée dans ce monde")

            now = self._clock.now_iso()
            canonical_now = WorldEngine(conn, clock=self._clock).read_canonical_time(world_id)
            cur = conn.execute(
                "INSERT INTO character "
                "(public_id, world_id, key, name, adult, current_location_id, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, 1, ?, ?, ?)",
                (new_uuid(), world_id, character_key, name, location["id"], now, now),
            )
            character_id = cur.lastrowid
            conn.execute(
                "INSERT INTO character_instance_origin "
                "(character_id, world_id, template_id, template_version, "
                "resolved_initial_definition_json, instantiated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    character_id,
                    world_id,
                    template["template_id"],
                    template_version,
                    json.dumps(
                        resolved_initial_definition,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    ),
                    now,
                ),
            )
            for need in conn.execute(
                "SELECT need_key, max_milli FROM need_definition WHERE world_id = ? ORDER BY need_key",
                (world_id,),
            ):
                conn.execute(
                    "INSERT INTO need_state "
                    "(public_id, world_id, character_id, need_key, value_milli, rate_remainder, anchor_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, 0, ?, ?)",
                    (
                        new_uuid(), world_id, character_id, need["need_key"], need["max_milli"],
                        canonical_now, now,
                    ),
                )
            conn.execute(
                "INSERT INTO character_profile "
                "(character_id, world_id, satiete_threshold_mult_milli, repos_threshold_mult_milli, "
                "energie_threshold_mult_milli, hygiene_threshold_mult_milli, rest_preference_milli, "
                "idle_tolerance_milli, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    character_id,
                    world_id,
                    _DEFAULT_PROFILE["satiete_threshold_mult_milli"],
                    _DEFAULT_PROFILE["repos_threshold_mult_milli"],
                    _DEFAULT_PROFILE["energie_threshold_mult_milli"],
                    _DEFAULT_PROFILE["hygiene_threshold_mult_milli"],
                    _DEFAULT_PROFILE["rest_preference_milli"],
                    _DEFAULT_PROFILE["idle_tolerance_milli"],
                    now,
                ),
            )
            _append_event(
                conn,
                world_id,
                SOURCE_SYSTEM,
                "character_instantiated",
                {
                    "character": character_key,
                    "template": template_key,
                    "template_version": template_version,
                    "location": location_key,
                },
                occurred_at=canonical_now,
                recorded_at=now,
            )
        return CharacterEngine(self._conn, clock=self._clock).character_sheet(world_id, character_key)

    def origin(self, world_id: Any, character_key: Any) -> dict[str, Any]:
        if not isinstance(world_id, int) or isinstance(world_id, bool) or world_id < 1:
            raise InstanceError("monde invalide")
        if not isinstance(character_key, str) or not _KEY_RE.fullmatch(character_key):
            raise InstanceError("clé de personnage invalide")
        row = self._conn.execute(
            "SELECT t.key AS template_key, o.template_version, o.resolved_initial_definition_json, "
            "o.instantiated_at FROM character_instance_origin o "
            "JOIN character ch ON ch.id = o.character_id "
            "JOIN character_template t ON t.id = o.template_id "
            "WHERE o.world_id = ? AND ch.key = ?",
            (world_id, character_key),
        ).fetchone()
        if row is None:
            raise InstanceError("provenance d'instance introuvable")
        return {
            "template_key": row["template_key"],
            "template_version": row["template_version"],
            "resolved_initial_definition": json.loads(row["resolved_initial_definition_json"]),
            "instantiated_at": row["instantiated_at"],
        }
