"""Tests d'accès à SQLite (Phase 0, niveau infrastructure).

Ces tests vérifient que Python peut ouvrir SQLite avec les réglages qui
serviront de prérequis à la persistance canonique (Phase 1). Aucun schéma
métier n'est défini ici.
"""

import sqlite3
from pathlib import Path


def test_sqlite_version_disponible():
    conn = sqlite3.connect(":memory:")
    try:
        version = conn.execute("SELECT sqlite_version()").fetchone()[0]
    finally:
        conn.close()
    parts = [int(p) for p in version.split(".")]
    # SQLite moderne, au minimum 3.x récent.
    assert parts[0] >= 3 and parts[1] >= 20


def test_contraintes_cles_etrangeres_actives():
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conn.close()


def test_contrainte_fk_reelle(tmp_path):
    db = Path(tmp_path) / "test.db"
    conn = sqlite3.connect(db)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY)")
        conn.execute(
            "CREATE TABLE child ("
            " id INTEGER PRIMARY KEY, parent_id INTEGER NOT NULL,"
            " FOREIGN KEY (parent_id) REFERENCES parent(id))"
        )
        conn.commit()
        try:
            conn.execute("INSERT INTO child (parent_id) VALUES (999)")
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # attendu : la clé étrangère est bien appliquée
        else:
            raise AssertionError("La clé étrangère doit rejeter une ligne orpheline")
    finally:
        conn.close()


def test_journal_mode_wal(tmp_path):
    db = Path(tmp_path) / "wal.db"
    conn = sqlite3.connect(db)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"
    finally:
        conn.close()
