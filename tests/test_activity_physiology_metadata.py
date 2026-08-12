"""Fondation inactive des métadonnées d'activité du cutover circadien."""

from datetime import datetime, timezone

from vivarium.db import connect_database, transaction
from vivarium.migrations import ensure_schema, load_migrations, split_sql_statements
from vivarium.util import new_uuid, to_iso
from vivarium.world import WorldEngine


T0 = datetime(2026, 8, 11, 12, tzinfo=timezone.utc)


class FakeClock:
    def now(self):
        return T0

    def now_iso(self):
        return to_iso(self.now())


def _apply_through(conn, version):
    conn.execute(
        "CREATE TABLE migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, "
        "applied_at TEXT NOT NULL, checksum TEXT NOT NULL)"
    )
    for migration in load_migrations():
        if migration.version > version:
            continue
        with transaction(conn):
            for statement in split_sql_statements(migration.sql):
                conn.execute(statement)
            conn.execute(
                "INSERT INTO migrations (version, name, applied_at, checksum) VALUES (?, ?, ?, ?)",
                (migration.version, migration.name, to_iso(T0), migration.checksum),
            )


def test_forward_migration_classifies_known_activity_wakefulness_without_canonical_history():
    conn = connect_database(":memory:")
    try:
        _apply_through(conn, 48)
        world_id = WorldEngine(conn, clock=FakeClock()).init_world(name="Legacy", seed=False)["id"]
        now = to_iso(T0)
        for activity_type in ("sleep", "eat", "legacy_custom"):
            conn.execute(
                "INSERT INTO activity_definition "
                "(public_id, world_id, activity_type, min_duration_seconds, max_duration_seconds, "
                "satiete_rate, repos_rate, energie_rate, hygiene_rate, created_at) "
                "VALUES (?, ?, ?, 1, 1, 0, 0, 0, 0, ?)",
                (new_uuid(), world_id, activity_type, now),
            )
        before = conn.execute(
            "SELECT COUNT(*), MAX(seq) FROM canonical_event WHERE world_id = ?", (world_id,)
        ).fetchone()

        assert ensure_schema(conn) == 52

        rows = {
            row["activity_type"]: (
                row["requires_sustained_wakefulness"], row["physical_load_class"],
            )
            for row in conn.execute(
                "SELECT activity_type, requires_sustained_wakefulness, physical_load_class "
                "FROM activity_definition WHERE world_id = ?", (world_id,)
            )
        }
        assert rows == {
            "sleep": (0, None),
            "eat": (1, None),
            "legacy_custom": (None, None),
        }
        after = conn.execute(
            "SELECT COUNT(*), MAX(seq) FROM canonical_event WHERE world_id = ?", (world_id,)
        ).fetchone()
        assert tuple(after) == tuple(before)
    finally:
        conn.close()


def test_metadata_constraints_reject_unknown_physical_load_values_but_allow_null():
    conn = connect_database(":memory:")
    try:
        ensure_schema(conn)
        world_id = WorldEngine(conn, clock=FakeClock()).init_world(name="Metadata", seed=False)["id"]
        now = to_iso(T0)
        conn.execute(
            "INSERT INTO activity_definition "
            "(public_id, world_id, activity_type, min_duration_seconds, max_duration_seconds, "
            "satiete_rate, repos_rate, energie_rate, hygiene_rate, "
            "requires_sustained_wakefulness, physical_load_class, created_at) "
            "VALUES (?, ?, 'legacy_ok', 1, 1, 0, 0, 0, 0, NULL, NULL, ?)",
            (new_uuid(), world_id, now),
        )
        try:
            conn.execute(
                "INSERT INTO activity_definition "
                "(public_id, world_id, activity_type, min_duration_seconds, max_duration_seconds, "
                "satiete_rate, repos_rate, energie_rate, hygiene_rate, "
                "requires_sustained_wakefulness, physical_load_class, created_at) "
                "VALUES (?, ?, 'invalid_load', 1, 1, 0, 0, 0, 0, 1, 'unclassified', ?)",
                (new_uuid(), world_id, now),
            )
        except Exception as error:
            assert "CHECK constraint failed" in str(error)
        else:
            raise AssertionError("une valeur physique inconnue aurait dû être refusée")
    finally:
        conn.close()
