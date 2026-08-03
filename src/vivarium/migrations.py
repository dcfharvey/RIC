"""Runner de migrations versionnées minimal (bibliothèque standard).

Le registre `migrations` est l'unique source d'autorité sur la version du
schéma. Aucune version de schéma n'est dupliquée ailleurs (en particulier
pas dans `worlds`).

Garanties :
- ordre d'application déterministe (préfixe numérique du fichier) ;
- refus des doublons de version ;
- application atomique : chaque migration est exécutée dans une transaction ;
- enregistrement de la version, du nom, de la date et d'une empreinte SHA-256 ;
- détection d'une migration déjà appliquée dont le contenu a changé : échec
  explicite, jamais de réparation silencieuse.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from .db import transaction
from .util import now_utc

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
MIGRATION_FILENAME_RE = re.compile(r"^(\d+)_([A-Za-z0-9_]+)\.sql$")


class MigrationError(RuntimeError):
    """Erreur du runner de migrations (doublon, divergence ou contenu invalide)."""


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    checksum: str
    sql: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def split_sql_statements(sql: str) -> list[str]:
    """Découpe un script SQL en instructions, en gérant BEGIN...END (triggers).

    Ignore les commentaires `--` et les littéraux entre guillemets. Un point
    virgule n'est un terminateur que hors d'un bloc BEGIN...END.
    """
    statements: list[str] = []
    buf: list[str] = []
    depth = 0
    quote: str | None = None
    i = 0
    n = len(sql)
    while i < n:
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""
        if quote:
            buf.append(ch)
            if ch == quote:
                if nxt == quote:  # guillemet doublé ('' ou "")
                    buf.append(nxt)
                    i += 2
                    continue
                quote = None
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if ch == "-" and nxt == "-":
            while i < n and sql[i] != "\n":
                i += 1
            continue
        if ch.isalpha() or ch == "_":
            word = re.match(r"[A-Za-z_]+", sql[i:]).group(0)
            w = word.upper()
            if w == "BEGIN":
                depth += 1
            elif w == "END":
                depth = max(0, depth - 1)
            buf.append(word)
            i += len(word)
            continue
        if ch == ";" and depth == 0:
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def load_migrations(directory: Path = MIGRATIONS_DIR) -> list[Migration]:
    """Charge les migrations d'un répertoire, triées et uniques par version."""
    if not directory.is_dir():
        raise MigrationError(f"répertoire de migrations introuvable : {directory}")
    found: list[Migration] = []
    for path in sorted(directory.iterdir()):
        m = MIGRATION_FILENAME_RE.match(path.name)
        if not m:
            continue
        version = int(m.group(1))
        name = m.group(2)
        content = path.read_text(encoding="utf-8")
        found.append(
            Migration(
                version=version,
                name=name,
                checksum=_sha256(content.encode("utf-8")),
                sql=content,
            )
        )
    seen: set[int] = set()
    for mig in found:
        if mig.version in seen:
            raise MigrationError(f"version de migration dupliquée : {mig.version}")
        seen.add(mig.version)
    found.sort(key=lambda m: m.version)
    return found


def _create_ledger(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            checksum TEXT NOT NULL
        )
        """
    )


def current_version(conn) -> int:
    """Version courante du schéma, lue depuis le registre (autorité unique)."""
    _create_ledger(conn)
    row = conn.execute("SELECT MAX(version) AS v FROM migrations").fetchone()
    return row["v"] if row and row["v"] is not None else 0


def ensure_schema(conn, directory: Path = MIGRATIONS_DIR) -> int:
    """Applique les migrations manquantes et retourne la version courante.

    Lève `MigrationError` en cas de divergence (migration déjà appliquée
    dont le contenu a changé) ou de doublon. N'applique jamais une migration
    deux fois. Chaque migration s'exécute dans une transaction atomique.
    """
    _create_ledger(conn)
    applied = {
        row["version"]: row["checksum"]
        for row in conn.execute("SELECT version, checksum FROM migrations")
    }
    pending = load_migrations(directory)
    for mig in pending:
        if mig.version in applied:
            if applied[mig.version] != mig.checksum:
                raise MigrationError(
                    f"migration {mig.version} ({mig.name}) déjà appliquée mais son "
                    f"contenu a changé (empreinte différente) ; refus de réparer "
                    f"silencieusement une divergence"
                )
            continue  # déjà appliquée et inchangée
        with transaction(conn) as c:
            for stmt in split_sql_statements(mig.sql):
                c.execute(stmt)
            c.execute(
                "INSERT INTO migrations (version, name, applied_at, checksum) "
                "VALUES (?, ?, ?, ?)",
                (mig.version, mig.name, now_utc(), mig.checksum),
            )
    return current_version(conn)
