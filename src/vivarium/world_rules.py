"""Installation explicite et vérifiable de règles de monde de référence."""

from __future__ import annotations

import sqlite3
from typing import Any

from .db import transaction
from .seed import SEED_ACTIVITIES, SEED_ACTIVITY_ALLOWED, SEED_NEEDS
from .util import Clock, new_uuid
from .world import SOURCE_SYSTEM, WorldEngine, _append_event

STANDARD_RULESET_KEY = "standard_residence.v1"


class WorldRuleError(ValueError):
    """Règles incompatibles ou monde incapable de les recevoir."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class WorldRuleService:
    """Installe les règles standard sans dépendre du seed de développement."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def _world_id(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise WorldRuleError("monde invalide", code="invalid_world")
        return value

    def install_standard_residence_rules(self, world_id: Any) -> dict[str, Any]:
        """Installe ou vérifie le jeu de règles standard de résidence.

        L'appel est idempotent. Une définition existante différente est un
        conflit explicite : le service ne la corrige jamais silencieusement.
        """
        world_id = self._world_id(world_id)
        with transaction(self._conn) as conn:
            if conn.execute("SELECT 1 FROM worlds WHERE id = ?", (world_id,)).fetchone() is None:
                raise WorldRuleError("monde introuvable", code="world_not_found")
            self._assert_required_places(conn, world_id)
            inserted_needs = self._install_needs(conn, world_id)
            inserted_activities = self._install_activities(conn, world_id)
            inserted_allowed = self._install_allowed_locations(conn, world_id)
            inserted = inserted_needs + inserted_activities + inserted_allowed
            if inserted:
                now = self._clock.now_iso()
                canonical_now = WorldEngine(conn, clock=self._clock).read_canonical_time(world_id)
                _append_event(
                    conn, world_id, SOURCE_SYSTEM, "world_rules_installed",
                    {
                        "rule_set": STANDARD_RULESET_KEY,
                        "needs_added": inserted_needs,
                        "activities_added": inserted_activities,
                        "activity_locations_added": inserted_allowed,
                    },
                    occurred_at=canonical_now, recorded_at=now,
                )
        return {
            "rule_set": STANDARD_RULESET_KEY,
            "changed": bool(inserted),
            "needs_added": inserted_needs,
            "activities_added": inserted_activities,
            "activity_locations_added": inserted_allowed,
        }

    @staticmethod
    def _assert_required_places(conn: sqlite3.Connection, world_id: int) -> None:
        required_keys = {key for _activity, key, kind in SEED_ACTIVITY_ALLOWED if key is not None}
        present = {
            row["key"] for row in conn.execute(
                "SELECT key FROM location WHERE world_id = ?", (world_id,)
            )
        }
        missing = sorted(required_keys - present)
        if missing:
            raise WorldRuleError(
                f"lieux requis absents pour les règles standard : {missing}",
                code="required_location_missing",
            )
        required_kinds = {kind for _activity, key, kind in SEED_ACTIVITY_ALLOWED if kind is not None}
        present_kinds = {
            row["kind"] for row in conn.execute(
                "SELECT DISTINCT kind FROM location WHERE world_id = ?", (world_id,)
            )
        }
        missing_kinds = sorted(required_kinds - present_kinds)
        if missing_kinds:
            raise WorldRuleError(
                f"types de lieux requis absents pour les règles standard : {missing_kinds}",
                code="required_location_kind_missing",
            )

    def _install_needs(self, conn: sqlite3.Connection, world_id: int) -> int:
        now = self._clock.now_iso()
        added = 0
        for key, name, _initial, rate_num, rate_den, threshold in SEED_NEEDS:
            row = conn.execute(
                "SELECT name, min_milli, max_milli, rate_num, rate_den, threshold_milli "
                "FROM need_definition WHERE world_id = ? AND need_key = ?", (world_id, key)
            ).fetchone()
            expected = (name, 0, 100000, rate_num, rate_den, threshold)
            if row is None:
                conn.execute(
                    "INSERT INTO need_definition (public_id, world_id, need_key, name, min_milli, max_milli, rate_num, rate_den, threshold_milli, created_at) VALUES (?, ?, ?, ?, 0, 100000, ?, ?, ?, ?)",
                    (new_uuid(), world_id, key, name, rate_num, rate_den, threshold, now),
                )
                added += 1
            elif tuple(row) != expected:
                raise WorldRuleError(f"définition de besoin incompatible : {key}", code="need_definition_conflict")
        return added

    def _install_activities(self, conn: sqlite3.Connection, world_id: int) -> int:
        now = self._clock.now_iso()
        added = 0
        for activity_type, minimum, maximum, satiete, repos, energie, hygiene in SEED_ACTIVITIES:
            row = conn.execute(
                "SELECT min_duration_seconds, max_duration_seconds, satiete_rate, repos_rate, energie_rate, hygiene_rate "
                "FROM activity_definition WHERE world_id = ? AND activity_type = ?", (world_id, activity_type)
            ).fetchone()
            expected = (minimum, maximum, satiete, repos, energie, hygiene)
            if row is None:
                conn.execute(
                    "INSERT INTO activity_definition (public_id, world_id, activity_type, min_duration_seconds, max_duration_seconds, satiete_rate, repos_rate, energie_rate, hygiene_rate, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (new_uuid(), world_id, activity_type, *expected, now),
                )
                added += 1
            elif tuple(row) != expected:
                raise WorldRuleError(f"définition d'activité incompatible : {activity_type}", code="activity_definition_conflict")
        return added

    def _install_allowed_locations(self, conn: sqlite3.Connection, world_id: int) -> int:
        now = self._clock.now_iso()
        added = 0
        for activity_type, location_key, location_kind in SEED_ACTIVITY_ALLOWED:
            if location_key is not None:
                row = conn.execute(
                    "SELECT 1 FROM activity_allowed_location WHERE world_id = ? AND activity_type = ? AND location_key = ?",
                    (world_id, activity_type, location_key),
                ).fetchone()
                if row is None:
                    conn.execute(
                        "INSERT INTO activity_allowed_location (public_id, world_id, activity_type, location_key, location_kind, created_at) VALUES (?, ?, ?, ?, NULL, ?)",
                        (new_uuid(), world_id, activity_type, location_key, now),
                    )
                    added += 1
            else:
                row = conn.execute(
                    "SELECT 1 FROM activity_allowed_location WHERE world_id = ? AND activity_type = ? AND location_kind = ?",
                    (world_id, activity_type, location_kind),
                ).fetchone()
                if row is None:
                    conn.execute(
                        "INSERT INTO activity_allowed_location (public_id, world_id, activity_type, location_key, location_kind, created_at) VALUES (?, ?, ?, NULL, ?, ?)",
                        (new_uuid(), world_id, activity_type, location_kind, now),
                    )
                    added += 1
        return added
