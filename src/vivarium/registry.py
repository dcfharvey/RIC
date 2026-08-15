"""Registre minimal et versionné des contrats du Vivarium (Phase 4.2A)."""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Any, Iterable

from .db import transaction
from .util import new_uuid, now_utc

_KINDS = frozenset({"component", "capability", "unit"})
# Public contract used by services that validate registry-compatible keys.
KEY_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
# Compatibility alias for this owner module's private implementation calls.
_KEY_RE = KEY_RE


class RegistryError(ValueError):
    """Contrat de registre invalide ou transition de publication impossible."""


class RegistryService:
    """Écrit les contrats globaux sans contourner leurs invariants de version."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @staticmethod
    def _validate_kind_key(kind: Any, key: Any) -> tuple[str, str]:
        if kind not in _KINDS:
            raise RegistryError("kind invalide")
        if not isinstance(key, str) or not _KEY_RE.fullmatch(key):
            raise RegistryError("key invalide")
        return kind, key

    @staticmethod
    def _validate_contract(contract: Any) -> str:
        if not isinstance(contract, dict):
            raise RegistryError("contract doit être un objet")
        return json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _validate_refs(values: Iterable[Any], field: str) -> tuple[str, ...]:
        if isinstance(values, (str, bytes)):
            raise RegistryError(f"{field} invalide")
        try:
            refs = tuple(values)
        except TypeError as exc:
            raise RegistryError(f"{field} invalide") from exc
        if len(set(refs)) != len(refs):
            raise RegistryError(f"{field} contient un doublon")
        for ref in refs:
            if not isinstance(ref, str) or not _KEY_RE.fullmatch(ref):
                raise RegistryError(f"{field} contient une référence invalide")
        return refs

    def create_draft(
        self,
        kind: Any,
        key: Any,
        contract: Any,
        *,
        dependencies: Iterable[Any] = (),
        incompatibilities: Iterable[Any] = (),
    ) -> dict[str, Any]:
        """Crée une nouvelle version brouillon, atomiquement et sans écraser l'ancienne."""
        kind, key = self._validate_kind_key(kind, key)
        contract_json = self._validate_contract(contract)
        dependencies = self._validate_refs(dependencies, "dependencies")
        incompatibilities = self._validate_refs(incompatibilities, "incompatibilities")
        if set(dependencies) & set(incompatibilities):
            raise RegistryError("une référence ne peut être dépendance et incompatibilité")

        with transaction(self._conn) as conn:
            definition = conn.execute(
                "SELECT id FROM registry_definition WHERE kind = ? AND key = ?",
                (kind, key),
            ).fetchone()
            if definition is None:
                cur = conn.execute(
                    "INSERT INTO registry_definition (public_id, kind, key, created_at) VALUES (?, ?, ?, ?)",
                    (new_uuid(), kind, key, now_utc()),
                )
                definition_id = cur.lastrowid
                version = 1
            else:
                definition_id = definition["id"]
                pending = conn.execute(
                    "SELECT 1 FROM registry_definition_version WHERE definition_id = ? AND status = 'draft'",
                    (definition_id,),
                ).fetchone()
                if pending is not None:
                    raise RegistryError("un brouillon existe déjà pour cette définition")
                version = conn.execute(
                    "SELECT COALESCE(MAX(version), 0) + 1 AS next_version FROM registry_definition_version WHERE definition_id = ?",
                    (definition_id,),
                ).fetchone()["next_version"]
            cur = conn.execute(
                "INSERT INTO registry_definition_version "
                "(definition_id, version, status, contract_json, dependencies_json, incompatibilities_json, created_at) "
                "VALUES (?, ?, 'draft', ?, ?, ?, ?)",
                (definition_id, version, contract_json, json.dumps(dependencies), json.dumps(incompatibilities), now_utc()),
            )
        return self.get_version(kind, key, version, version_id=cur.lastrowid)

    def get_version(
        self, kind: Any, key: Any, version: Any, *, version_id: int | None = None
    ) -> dict[str, Any]:
        kind, key = self._validate_kind_key(kind, key)
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise RegistryError("version invalide")
        row = self._conn.execute(
            "SELECT d.kind, d.key, v.id, v.version, v.status, v.contract_json, v.dependencies_json, "
            "v.incompatibilities_json, v.created_at, v.published_at "
            "FROM registry_definition d JOIN registry_definition_version v ON v.definition_id = d.id "
            "WHERE d.kind = ? AND d.key = ? AND v.version = ?",
            (kind, key, version),
        ).fetchone()
        if row is None or (version_id is not None and row["id"] != version_id):
            raise RegistryError("définition introuvable")
        return {
            "kind": row["kind"], "key": row["key"], "version": row["version"],
            "status": row["status"], "contract": json.loads(row["contract_json"]),
            "dependencies": json.loads(row["dependencies_json"]),
            "incompatibilities": json.loads(row["incompatibilities_json"]),
            "created_at": row["created_at"], "published_at": row["published_at"],
        }

    def publish(self, kind: Any, key: Any, version: Any) -> dict[str, Any]:
        """Publie un brouillon après avoir vérifié que ses références sont publiées."""
        kind, key = self._validate_kind_key(kind, key)
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise RegistryError("version invalide")
        with transaction(self._conn) as conn:
            row = conn.execute(
                "SELECT d.id AS definition_id, v.id, v.status, v.dependencies_json, v.incompatibilities_json "
                "FROM registry_definition d JOIN registry_definition_version v ON v.definition_id = d.id "
                "WHERE d.kind = ? AND d.key = ? AND v.version = ?",
                (kind, key, version),
            ).fetchone()
            if row is None:
                raise RegistryError("définition introuvable")
            if row["status"] != "draft":
                raise RegistryError("seul un brouillon peut être publié")
            for ref in json.loads(row["dependencies_json"]) + json.loads(row["incompatibilities_json"]):
                found = conn.execute(
                    "SELECT 1 FROM registry_definition d JOIN registry_definition_version v ON v.definition_id = d.id "
                    "WHERE d.key = ? AND v.status = 'published' LIMIT 1", (ref,)
                ).fetchone()
                if found is None:
                    raise RegistryError(f"référence non publiée : {ref}")
            conn.execute(
                "UPDATE registry_definition_version SET status = 'published', published_at = ? WHERE id = ?",
                (now_utc(), row["id"]),
            )
        return self.get_version(kind, key, version)

    def install_published_catalog(
        self, definitions: Iterable[tuple[Any, Any, Any]]
    ) -> list[dict[str, Any]]:
        """Installe un petit catalogue logiciel de contrats, atomiquement.

        Une entrée déjà publiée en version 1 doit être identique au contrat
        attendu. Le catalogue ne corrige jamais silencieusement une définition
        existante et ne crée aucune version supplémentaire lors d'un second
        appel.
        """
        try:
            entries = tuple(definitions)
        except TypeError as exc:
            raise RegistryError("catalogue invalide") from exc
        normalized: list[tuple[str, str, str]] = []
        seen: set[tuple[str, str]] = set()
        for entry in entries:
            if not isinstance(entry, tuple) or len(entry) != 3:
                raise RegistryError("catalogue invalide")
            kind, key = self._validate_kind_key(entry[0], entry[1])
            contract_json = self._validate_contract(entry[2])
            if (kind, key) in seen:
                raise RegistryError("catalogue contient un doublon")
            seen.add((kind, key))
            normalized.append((kind, key, contract_json))

        with transaction(self._conn) as conn:
            for kind, key, contract_json in normalized:
                definition = conn.execute(
                    "SELECT id, kind FROM registry_definition WHERE key = ?", (key,)
                ).fetchone()
                if definition is None:
                    cur = conn.execute(
                        "INSERT INTO registry_definition (public_id, kind, key, created_at) "
                        "VALUES (?, ?, ?, ?)",
                        (new_uuid(), kind, key, now_utc()),
                    )
                    conn.execute(
                        "INSERT INTO registry_definition_version "
                        "(definition_id, version, status, contract_json, dependencies_json, "
                        "incompatibilities_json, created_at, published_at) "
                        "VALUES (?, 1, 'published', ?, '[]', '[]', ?, ?)",
                        (cur.lastrowid, contract_json, now_utc(), now_utc()),
                    )
                    continue
                if definition["kind"] != kind:
                    raise RegistryError("clé de catalogue déjà utilisée par un autre type")
                version = conn.execute(
                    "SELECT status, contract_json, dependencies_json, incompatibilities_json "
                    "FROM registry_definition_version WHERE definition_id = ? AND version = 1",
                    (definition["id"],),
                ).fetchone()
                if (
                    version is None
                    or version["status"] != "published"
                    or version["contract_json"] != contract_json
                    or version["dependencies_json"] != "[]"
                    or version["incompatibilities_json"] != "[]"
                ):
                    raise RegistryError("catalogue incompatible avec le registre existant")
        return [self.get_version(kind, key, 1) for kind, key, _ in normalized]
