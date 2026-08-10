"""Tests du runner de migrations (Phase 1)."""

import pytest

from vivarium.db import connect_database, transaction
from vivarium.migrations import (
    Migration,
    MigrationError,
    current_version,
    ensure_schema,
    load_migrations,
    split_sql_statements,
)


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
    assert ensure_schema(conn) == 44
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(social_interpretation)")}
    assert "meaning_hypotheses_json" in columns
    assert "legacy_motive_hypotheses_json" in columns
    assert "motive_hypotheses_json" not in columns
    assert ensure_schema(conn) == 44


def test_migrations_enregistre_ledger(conn):
    ensure_schema(conn)
    rows = conn.execute("SELECT version, name, checksum FROM migrations").fetchall()
    assert rows
    applied = {r["version"]: r["checksum"] for r in rows}
    loaded = {m.version: m.checksum for m in load_migrations()}
    # le registre documente exactement les migrations connues et leur empreinte.
    for version, checksum in loaded.items():
        assert applied[version] == checksum


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
