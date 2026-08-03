"""Interface en ligne de commande du vivarium (Phase 1).

Commandes :
- `init`   : initialise un nouveau monde de développement ;
- `status` : inspecte l'état général du monde.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .db import connect_database
from .migrations import ensure_schema
from .settings import Settings
from .world import WORLD_DEFAULT_NAME, WorldEngine, get_status


def _resolve_db_path(args_db: str | None) -> Path:
    if args_db:
        return Path(args_db).resolve()
    return Settings().db_path


def _run_init(conn, args) -> int:
    engine = WorldEngine(conn)
    worlds = engine.list_worlds()
    if worlds:
        if not getattr(args, "force", False):
            print(
                "Un monde existe déjà. Utilisez --force pour réinitialiser le monde "
                "de développement (écrase la base locale de développement).",
                file=__import__("sys").stderr,
            )
            return 2
        db_path = _resolve_db_path(getattr(args, "db", None))
        conn.close()
        _delete_dev_db(db_path)
        conn = connect_database(db_path)
        ensure_schema(conn)
        engine = WorldEngine(conn)
    world = engine.init_world(name=args.name)
    print(f"Monde initialisé : id={world['id']} name={world['name']!r}")
    print(f"  statut       : {world['status']}")
    print("  lieux        : 9 (salon, cuisine, salle de bain, cour, couloir, 4 chambres)")
    print("  objets       : table, chaise, lit (seed de test, non définitif)")
    return 0


def _delete_dev_db(db_path: Path) -> None:
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(db_path) + suffix)
        if p.exists():
            p.unlink()


def _run_status(conn) -> int:
    status = get_status(conn)
    if not status["present"]:
        print(status["message"])
        return 1
    w = status["world"]
    print(f"Monde : id={w['id']} name={w['name']!r} statut={w['status']}")
    print(f"Version de schéma (registre migrations) : {status['schema_version']}")
    clock = status["clock"]
    print(f"Horloge canonique : {clock['simulated_now'] if clock else 'n/d'}")
    integrity = status["integrity_check"]
    print(
        "Integrity check : "
        + ("ok" if integrity == ["ok"] else f"anomalies {integrity}")
    )
    fk = status["foreign_key_check"]
    print(f"Foreign key check : {'aucune violation' if not fk else f'{len(fk)} violation(s)'}")
    counts = status["counts"]
    print(
        f"Compteurs : lieux={counts['locations']} objets={counts['objects']} "
        f"événements={counts['events']}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vivarium", description="Vivarium social artificiel")
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Initialise un nouveau monde de développement.")
    p_init.add_argument("--name", default=WORLD_DEFAULT_NAME)
    p_init.add_argument("--db", default=None, help="Chemin de la base (défaut : data/world.dev.sqlite).")
    p_init.add_argument("--force", action="store_true",
                        help="Réinitialise la base locale de développement.")

    p_status = sub.add_parser("status", help="Inspecte l'état général du monde.")
    p_status.add_argument("--db", default=None, help="Chemin de la base.")

    args = parser.parse_args(argv)

    from .logging_setup import configure_logging

    configure_logging(Settings())

    if not args.command:
        print(f"vivarium-social {__version__}")
        return 0

    db_path = _resolve_db_path(getattr(args, "db", None))
    conn = connect_database(db_path)
    try:
        ensure_schema(conn)
        if args.command == "init":
            return _run_init(conn, args)
        if args.command == "status":
            return _run_status(conn)
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return 0
