"""Brouillons et versions publiées des modèles de personnages (Phase 4.2B)."""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Iterable

from .db import transaction
from .registry import _KEY_RE
from .util import new_uuid, now_utc


class TemplateError(ValueError):
    pass


class CharacterTemplateService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @staticmethod
    def _key(key: Any) -> str:
        if not isinstance(key, str) or not _KEY_RE.fullmatch(key):
            raise TemplateError("key invalide")
        return key

    @staticmethod
    def _definition(value: Any) -> str:
        if not isinstance(value, dict):
            raise TemplateError("definition doit être un objet")
        try:
            return json.dumps(
                value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
            )
        except (TypeError, ValueError) as exc:
            raise TemplateError("definition doit être sérialisable en JSON") from exc

    def _components(self, values: Iterable[Any]) -> tuple[dict[str, Any], ...]:
        if isinstance(values, (str, bytes)):
            raise TemplateError("components invalide")
        try:
            bindings = tuple(values)
        except TypeError as exc:
            raise TemplateError("components invalide") from exc
        if not bindings:
            raise TemplateError("components invalide")
        parsed: list[dict[str, Any]] = []
        keys: set[str] = set()
        for binding in bindings:
            if not isinstance(binding, dict) or set(binding) != {"key", "version", "config"}:
                raise TemplateError("liaison de composant invalide")
            component_key = binding["key"]
            component_version = binding["version"]
            config = binding["config"]
            if (
                not isinstance(component_key, str)
                or not _KEY_RE.fullmatch(component_key)
                or component_key in keys
                or not isinstance(component_version, int)
                or isinstance(component_version, bool)
                or component_version < 1
                or not isinstance(config, dict)
            ):
                raise TemplateError("liaison de composant invalide")
            keys.add(component_key)
            try:
                json.dumps(
                    config, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
                )
            except (TypeError, ValueError) as exc:
                raise TemplateError("liaison de composant invalide") from exc
            parsed.append(
                {"key": component_key, "version": component_version, "config": config}
            )
        return tuple(parsed)

    def create_draft(
        self, key: Any, definition: Any, components: Iterable[Any]
    ) -> dict[str, Any]:
        key = self._key(key)
        definition_json = self._definition(definition)
        components = self._components(components)
        with transaction(self._conn) as conn:
            row = conn.execute(
                "SELECT id FROM character_template WHERE key = ?", (key,)
            ).fetchone()
            if row is None:
                cur = conn.execute(
                    "INSERT INTO character_template (public_id, key, created_at) VALUES (?, ?, ?)",
                    (new_uuid(), key, now_utc()),
                )
                template_id = cur.lastrowid
                version = 1
            else:
                template_id = row["id"]
                pending = conn.execute(
                    "SELECT 1 FROM character_template_version "
                    "WHERE template_id = ? AND status = 'draft'",
                    (template_id,),
                ).fetchone()
                if pending is not None:
                    raise TemplateError("un brouillon existe déjà")
                version = conn.execute(
                    "SELECT COALESCE(MAX(version), 0) + 1 AS next_version "
                    "FROM character_template_version WHERE template_id = ?",
                    (template_id,),
                ).fetchone()["next_version"]
            conn.execute(
                "INSERT INTO character_template_version "
                "(template_id, version, status, definition_json, component_bindings_json, created_at) "
                "VALUES (?, ?, 'draft', ?, ?, ?)",
                (
                    template_id,
                    version,
                    definition_json,
                    json.dumps(
                        components,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    ),
                    now_utc(),
                ),
            )
        return self.get_version(key, version)

    def get_version(self, key: Any, version: Any) -> dict[str, Any]:
        key = self._key(key)
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise TemplateError("version invalide")
        row = self._conn.execute(
            "SELECT t.key, v.version, v.status, v.definition_json, v.component_bindings_json, "
            "v.created_at, v.published_at FROM character_template t "
            "JOIN character_template_version v ON v.template_id = t.id "
            "WHERE t.key = ? AND v.version = ?",
            (key, version),
        ).fetchone()
        if row is None:
            raise TemplateError("modèle introuvable")
        return {
            "key": row["key"],
            "version": row["version"],
            "status": row["status"],
            "definition": json.loads(row["definition_json"]),
            "components": json.loads(row["component_bindings_json"]),
            "created_at": row["created_at"],
            "published_at": row["published_at"],
        }

    def publish(self, key: Any, version: Any) -> dict[str, Any]:
        key = self._key(key)
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise TemplateError("version invalide")
        with transaction(self._conn) as conn:
            row = conn.execute(
                "SELECT v.id, v.status, v.component_bindings_json FROM character_template t "
                "JOIN character_template_version v ON v.template_id=t.id WHERE t.key=? AND v.version=?",
                (key, version),
            ).fetchone()
            if row is None:
                raise TemplateError("modèle introuvable")
            if row["status"] != "draft":
                raise TemplateError("seul un brouillon peut être publié")
            errors = self._validation_errors(
                conn, json.loads(row["component_bindings_json"])
            )
            if errors:
                raise TemplateError(errors[0]["code"])
            conn.execute(
                "UPDATE character_template_version SET status='published', published_at=? WHERE id=?",
                (now_utc(), row["id"]),
            )
        return self.get_version(key, version)

    def validate(self, key: Any, version: Any) -> dict[str, Any]:
        """Retourne un diagnostic déterministe; ne modifie jamais le gabarit."""
        template = self.get_version(key, version)
        errors = self._validation_errors(self._conn, template["components"])
        return {
            "key": template["key"],
            "version": template["version"],
            "valid": not errors,
            "errors": errors,
        }

    @staticmethod
    def _validation_errors(
        conn: sqlite3.Connection, bindings: Iterable[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        for binding in bindings:
            key = binding["key"]
            version = binding["version"]
            row = conn.execute(
                "SELECT v.contract_json FROM registry_definition d "
                "JOIN registry_definition_version v ON v.definition_id = d.id "
                "WHERE d.kind = 'component' AND d.key = ? AND v.version = ? "
                "AND v.status = 'published'",
                (key, version),
            ).fetchone()
            if row is None:
                errors.append(
                    {"code": "component_not_published", "key": key, "version": version}
                )
                continue
            errors.extend(
                CharacterTemplateService._config_errors(
                    key, version, binding["config"], json.loads(row["contract_json"])
                )
            )
        return errors

    @staticmethod
    def _config_errors(
        component_key: str,
        component_version: int,
        config: dict[str, Any],
        contract: dict[str, Any],
    ) -> list[dict[str, Any]]:
        schema = contract.get("config_schema", {})
        if not isinstance(schema, dict):
            return [
                {
                    "code": "invalid_component_schema",
                    "key": component_key,
                    "version": component_version,
                }
            ]
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        additional = schema.get("additional_properties", False)
        if (
            set(schema) - {"required", "properties", "additional_properties"}
            or not isinstance(required, list)
            or len(set(required)) != len(required)
            or any(not isinstance(field, str) for field in required)
            or not isinstance(properties, dict)
            or any(field not in properties for field in required)
            or not isinstance(additional, bool)
        ):
            return [
                {
                    "code": "invalid_component_schema",
                    "key": component_key,
                    "version": component_version,
                }
            ]
        errors: list[dict[str, Any]] = []
        for field in required:
            if field not in config:
                errors.append({"code": "missing_config_field", "component": component_key, "field": field})
        for field, value in config.items():
            spec = properties.get(field)
            if spec is None:
                if not additional:
                    errors.append({"code": "unknown_config_field", "component": component_key, "field": field})
                continue
            if not isinstance(spec, dict) or set(spec) - {"type", "enum", "minimum", "maximum"}:
                errors.append({"code": "invalid_component_schema", "key": component_key, "version": component_version})
                continue
            expected = spec.get("type")
            if expected not in {"string", "number", "integer", "boolean", "object", "array"}:
                errors.append({"code": "invalid_component_schema", "key": component_key, "version": component_version})
                continue
            if not CharacterTemplateService._matches_type(value, expected):
                errors.append({"code": "invalid_config_type", "component": component_key, "field": field})
                continue
            if "enum" in spec and (not isinstance(spec["enum"], list) or value not in spec["enum"]):
                errors.append({"code": "invalid_config_enum", "component": component_key, "field": field})
            for bound in ("minimum", "maximum"):
                if bound in spec and (
                    not isinstance(spec[bound], (int, float))
                    or isinstance(spec[bound], bool)
                    or not isinstance(value, (int, float))
                    or isinstance(value, bool)
                ):
                    errors.append({"code": "invalid_component_schema", "key": component_key, "version": component_version})
                    break
            else:
                if "minimum" in spec and value < spec["minimum"]:
                    errors.append({"code": "config_below_minimum", "component": component_key, "field": field})
                if "maximum" in spec and value > spec["maximum"]:
                    errors.append({"code": "config_above_maximum", "component": component_key, "field": field})
        return errors

    @staticmethod
    def _matches_type(value: Any, expected: str) -> bool:
        return {
            "string": isinstance(value, str),
            "number": isinstance(value, (int, float)) and not isinstance(value, bool),
            "integer": isinstance(value, int) and not isinstance(value, bool),
            "boolean": isinstance(value, bool),
            "object": isinstance(value, dict),
            "array": isinstance(value, list),
        }[expected]
