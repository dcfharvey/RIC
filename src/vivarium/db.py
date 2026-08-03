"""Connexion SQLite contrôlée et gestion des transactions atomiques (Phase 1).

Le moteur canonique est la seule autorité d'écriture : la couche de code
métier écrit l'état et produit sa trace canonique dans la même transaction.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path


def connect_database(path: Path) -> sqlite3.Connection:
    """Ouvre (ou crée) une base SQLite avec les réglages de persistance.

    - WAL pour permettre reprise et migrations de manière sûre ;
    - contraintes de clés étrangères activées (INV-016) ;
    - timeout d'attente sur verrou ;
    - gestion des transactions explicite (autocommit).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.isolation_level = None  # autocommit ; transactions gérées explicitement
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection):
    """Ouvre une transaction atomique ; rollback total en cas d'erreur.

    Toute écriture d'état et son événement canonique associé doivent être
    émis à l'intérieur d'un seul `transaction(...)` pour ne jamais laisser
    d'état partiellement appliqué (INV-016).
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")
