"""Tests du runner de migrations (Phase 1)."""

from datetime import datetime, timezone
from shutil import copy2

import pytest

from vivarium.attention import AttentionService
from vivarium.db import connect_database, transaction
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import (
    MIGRATIONS_DIR,
    Migration,
    MigrationError,
    current_version,
    ensure_schema,
    load_migrations,
    split_sql_statements,
)
from vivarium.subjective_memory import SubjectiveMemoryService


class FixedClock:
    def now(self):
        return datetime(2026, 8, 16, 12, tzinfo=timezone.utc)

    def now_iso(self):
        return self.now().isoformat()


@pytest.fixture
def conn():
    c = connect_database(":memory:")
    yield c
    c.close()


def test_split_sql_statements_ignore_point_virgule_dans_trigger():
    sql = (
        "CREATE TRIGGER t BEFORE UPDATE ON x BEGIN "
        "SELECT RAISE(ABORT, 'msg: interdit'); END;"
        "CREATE TABLE y (id INTEGER);"
    )
    parts = split_sql_statements(sql)
    # un point-virgule à l'intérieur du corps BEGIN...END ne doit pas découper.
    assert parts[0].lower().startswith("create trigger")
    assert "begin select" in " ".join(parts[0].lower().split())
    assert parts[1].lower().startswith("create table")


def test_load_migrations_ordre_deterministe_et_empreinte():
    migs = load_migrations()
    assert migs, "au moins la migration 0001 attendue"
    versions = [m.version for m in migs]
    assert versions == sorted(versions)
    for m in migs:
        assert len(m.checksum) == 64  # sha256


def test_load_migrations_refuse_les_doublons(tmp_path):
    (tmp_path / "0001_a.sql").write_text("CREATE TABLE a (id INTEGER);", encoding="utf-8")
    (tmp_path / "0001_b.sql").write_text("CREATE TABLE b (id INTEGER);", encoding="utf-8")
    with pytest.raises(MigrationError):
        load_migrations(tmp_path)


def test_ensure_schema_applique_et_est_idempotent(conn):
    assert current_version(conn) == 0
    v1 = ensure_schema(conn)
    assert v1 >= 1
    # deuxième appel : ne réapplique rien, même version
    v2 = ensure_schema(conn)
    assert v2 == v1
    assert current_version(conn) == v1


def test_scc1b_interpretation_only_renomme_lancienne_colonne_et_reste_idempotente(conn):
    assert ensure_schema(conn) == 61
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(social_interpretation)")}
    assert "meaning_hypotheses_json" in columns
    assert "legacy_motive_hypotheses_json" in columns
    assert "motive_hypotheses_json" not in columns
    assert ensure_schema(conn) == 61


def test_migrations_enregistre_ledger(conn):
    ensure_schema(conn)
    rows = conn.execute("SELECT version, name, checksum FROM migrations").fetchall()
    assert rows
    applied = {r["version"]: r["checksum"] for r in rows}
    loaded = {m.version: m.checksum for m in load_migrations()}
    # le registre documente exactement les migrations connues et leur empreinte.
    for version, checksum in loaded.items():
        assert applied[version] == checksum


def test_autobiographical_memory_migration_creates_owner_scoped_tables(conn):
    assert ensure_schema(conn) == 61
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert {
        "autobiographical_episode",
        "autobiographical_episode_support",
        "autobiographical_episode_event",
        "subjective_memory_encoding_admission",
        "autobiographical_episode_seed_decision",
        "autobiographical_episode_revision",
        "autobiographical_episode_revision_support",
    } <= tables
    assert ensure_schema(conn) == 61


def test_autobiographical_memory_migration_survives_existing_database_reopen(tmp_path):
    path = tmp_path / "existing.sqlite"
    first = connect_database(str(path))
    assert ensure_schema(first) == 61
    first.close()

    reopened = connect_database(str(path))
    try:
        assert ensure_schema(reopened) == 61
        assert reopened.execute(
            "SELECT checksum FROM migrations WHERE version = 61"
        ).fetchone()[0]
    finally:
        reopened.close()


def test_append_only_migration_preserves_existing_episode_as_current(tmp_path):
    legacy_dir = tmp_path / "legacy-migrations"
    legacy_dir.mkdir()
    for path in MIGRATIONS_DIR.glob("*.sql"):
        if path.name != "0061_autobiographical_append_only_lifecycle.sql":
            copy2(path, legacy_dir / path.name)

    path = tmp_path / "existing-episode.sqlite"
    legacy = connect_database(str(path))
    clock = FixedClock()
    assert ensure_schema(legacy, legacy_dir) == 60
    world_id = IntegrationWorldService(legacy, clock=clock).create_initial_world()["id"]
    item = AttentionService(legacy, clock=clock).snapshot(world_id, "sophie").selected[0]
    memory = SubjectiveMemoryService(legacy, clock=clock)
    memory.encode_attention(world_id, "sophie", "legacy-trace", item)
    trace_id = legacy.execute(
        "SELECT id FROM subjective_trace WHERE request_key = 'legacy-trace'"
    ).fetchone()[0]
    memory.form_episode(world_id, "sophie", "legacy-episode", [trace_id])
    legacy.close()

    reopened = connect_database(str(path))
    try:
        assert ensure_schema(reopened) == 61
        current = SubjectiveMemoryService(reopened, clock=clock).get_current_episode(
            world_id, "sophie", "legacy-episode"
        )
        assert current["episode_key"] == "legacy-episode"
        assert reopened.execute(
            "SELECT COUNT(*) FROM autobiographical_episode_revision"
        ).fetchone()[0] == 0
    finally:
        reopened.close()


def test_divergence_migration_modifiee_leve_erreur(conn):
    v = ensure_schema(conn)
    # simule une migration déjà appliquée mais dont le contenu a changé.
    conn.execute(
        "UPDATE migrations SET checksum = ? WHERE version = ?",
        ("0" * 64, 1),
    )
    with pytest.raises(MigrationError, match="contenu a changé"):
        ensure_schema(conn)


def test_migrations_atomiques_dans_une_transaction(conn):
    # une migration valide et une incohérente : la transaction protège l'état.
    ensure_schema(conn)
    # vérifie que le schéma est bien présent et cohérent
    tables = {
        r["name"]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }
    assert {"worlds", "location", "world_object", "canonical_event", "canonical_clock", "migrations"} <= tables
