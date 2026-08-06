"""Presets versionnes de lieux et de connecteurs.

Ils decrivent ce qu'un blueprint pourra instancier; ils ne modifient ni un
monde existant, ni le graphe, ni les permissions de traversee. Les regles
physiques restent donc explicites et futures au lieu d'etre inventees par une
etiquette comme ``pool`` ou ``door``.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Iterable

from .db import transaction
from .registry import _KEY_RE
from .util import new_uuid, now_utc


PLACE = "place"
CONNECTOR = "connector"
_KINDS = frozenset({PLACE, CONNECTOR})
_DIRECTIONS = frozenset({"one_way", "bidirectional"})
_NAME_MAX = 120


class EnvironmentArchetypeError(ValueError):
    """Contrat, version ou publication d'un preset invalide."""


class EnvironmentArchetypeService:
    """Gere des brouillons publies et immuables de presets environnementaux."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @staticmethod
    def _kind(value: Any) -> str:
        if value not in _KINDS:
            raise EnvironmentArchetypeError("type d'archetype invalide")
        return value

    @staticmethod
    def _key(value: Any, label: str = "cle") -> str:
        if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
            raise EnvironmentArchetypeError(f"{label} invalide")
        return value

    @staticmethod
    def _version(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise EnvironmentArchetypeError("version invalide")
        return value

    @staticmethod
    def _name(value: Any) -> str:
        if not isinstance(value, str) or not (name := value.strip()) or len(name) > _NAME_MAX:
            raise EnvironmentArchetypeError("nom invalide")
        return name

    @classmethod
    def _keys(cls, value: Any, label: str) -> list[str]:
        if isinstance(value, (str, bytes)):
            raise EnvironmentArchetypeError(f"{label} invalide")
        try:
            raw = list(value)
        except TypeError as exc:
            raise EnvironmentArchetypeError(f"{label} invalide") from exc
        parsed = [cls._key(item, label) for item in raw]
        if len(set(parsed)) != len(parsed):
            raise EnvironmentArchetypeError(f"{label} contient un doublon")
        return parsed

    @classmethod
    def _contract(cls, archetype_kind: str, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise EnvironmentArchetypeError("contrat doit etre un objet")
        if archetype_kind == PLACE:
            required = {"name", "medium", "functions", "max_occupancy", "installation_slots"}
            if set(value) != required:
                raise EnvironmentArchetypeError("contrat de lieu invalide")
            capacity = value["max_occupancy"]
            if capacity is not None and (
                not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1
            ):
                raise EnvironmentArchetypeError("capacite d'occupation invalide")
            return {
                "name": cls._name(value["name"]),
                "medium": cls._key(value["medium"], "milieu"),
                "functions": cls._keys(value["functions"], "fonctions"),
                "max_occupancy": capacity,
                "installation_slots": cls._keys(value["installation_slots"], "emplacements"),
            }
        required = {"name", "traversal_modes", "directions", "features"}
        if set(value) != required:
            raise EnvironmentArchetypeError("contrat de connecteur invalide")
        directions = value["directions"]
        if directions not in _DIRECTIONS:
            raise EnvironmentArchetypeError("directions de connecteur invalides")
        modes = cls._keys(value["traversal_modes"], "modes de traversee")
        if not modes:
            raise EnvironmentArchetypeError("modes de traversee invalides")
        return {
            "name": cls._name(value["name"]),
            "traversal_modes": modes,
            "directions": directions,
            "features": cls._keys(value["features"], "proprietes"),
        }

    @staticmethod
    def _json(value: dict[str, Any]) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

    def create_draft(self, archetype_kind: Any, key: Any, contract: Any) -> dict[str, Any]:
        """Cree une nouvelle version brouillon sans ecraser une version publiee."""
        archetype_kind = self._kind(archetype_kind)
        key = self._key(key)
        contract = self._contract(archetype_kind, contract)
        contract_json = self._json(contract)
        with transaction(self._conn) as conn:
            archetype = conn.execute(
                "SELECT id FROM environment_archetype WHERE archetype_kind = ? AND key = ?",
                (archetype_kind, key),
            ).fetchone()
            if archetype is None:
                cur = conn.execute(
                    "INSERT INTO environment_archetype (public_id, archetype_kind, key, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (new_uuid(), archetype_kind, key, now_utc()),
                )
                archetype_id, version = cur.lastrowid, 1
            else:
                archetype_id = archetype["id"]
                if conn.execute(
                    "SELECT 1 FROM environment_archetype_version WHERE archetype_id = ? AND status = 'draft'",
                    (archetype_id,),
                ).fetchone() is not None:
                    raise EnvironmentArchetypeError("un brouillon existe deja pour cet archetype")
                version = conn.execute(
                    "SELECT COALESCE(MAX(version), 0) + 1 FROM environment_archetype_version "
                    "WHERE archetype_id = ?",
                    (archetype_id,),
                ).fetchone()[0]
            conn.execute(
                "INSERT INTO environment_archetype_version "
                "(archetype_id, version, status, contract_json, created_at) VALUES (?, ?, 'draft', ?, ?)",
                (archetype_id, version, contract_json, now_utc()),
            )
        return self.get_version(archetype_kind, key, version)

    def get_version(self, archetype_kind: Any, key: Any, version: Any) -> dict[str, Any]:
        archetype_kind = self._kind(archetype_kind)
        key = self._key(key)
        version = self._version(version)
        row = self._conn.execute(
            "SELECT a.archetype_kind, a.key, v.version, v.status, v.contract_json, v.created_at, v.published_at "
            "FROM environment_archetype a JOIN environment_archetype_version v ON v.archetype_id = a.id "
            "WHERE a.archetype_kind = ? AND a.key = ? AND v.version = ?",
            (archetype_kind, key, version),
        ).fetchone()
        if row is None:
            raise EnvironmentArchetypeError("archetype introuvable")
        return {
            "kind": row["archetype_kind"], "key": row["key"], "version": row["version"],
            "status": row["status"], "contract": json.loads(row["contract_json"]),
            "created_at": row["created_at"], "published_at": row["published_at"],
        }

    def publish(self, archetype_kind: Any, key: Any, version: Any) -> dict[str, Any]:
        """Publie un contrat fige; ses instances futures pourront le referencer."""
        archetype_kind = self._kind(archetype_kind)
        key = self._key(key)
        version = self._version(version)
        with transaction(self._conn) as conn:
            row = conn.execute(
                "SELECT v.id, v.status FROM environment_archetype a "
                "JOIN environment_archetype_version v ON v.archetype_id = a.id "
                "WHERE a.archetype_kind = ? AND a.key = ? AND v.version = ?",
                (archetype_kind, key, version),
            ).fetchone()
            if row is None:
                raise EnvironmentArchetypeError("archetype introuvable")
            if row["status"] != "draft":
                raise EnvironmentArchetypeError("seul un brouillon peut etre publie")
            conn.execute(
                "UPDATE environment_archetype_version SET status = 'published', published_at = ? WHERE id = ?",
                (now_utc(), row["id"]),
            )
        return self.get_version(archetype_kind, key, version)

    def list_published(self, archetype_kind: Any) -> list[dict[str, Any]]:
        """Liste deterministe des contrats publiables par un futur blueprint."""
        archetype_kind = self._kind(archetype_kind)
        rows = self._conn.execute(
            "SELECT a.key, v.version FROM environment_archetype a "
            "JOIN environment_archetype_version v ON v.archetype_id = a.id "
            "WHERE a.archetype_kind = ? AND v.status = 'published' "
            "ORDER BY a.key, v.version",
            (archetype_kind,),
        ).fetchall()
        return [self.get_version(archetype_kind, row["key"], row["version"]) for row in rows]

    def create_place_draft(self, key: Any, contract: Any) -> dict[str, Any]:
        return self.create_draft(PLACE, key, contract)

    def create_connector_draft(self, key: Any, contract: Any) -> dict[str, Any]:
        return self.create_draft(CONNECTOR, key, contract)
