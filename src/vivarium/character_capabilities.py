"""Lecture commune des capacités déclarées dans l'origine d'un personnage."""

from __future__ import annotations

import json
import sqlite3


def sapient_character_keys(conn: sqlite3.Connection, world_id: int) -> tuple[str, ...]:
    """Retourne uniquement les personnages dont le profil canonique est sapient."""
    rows = conn.execute(
        "SELECT c.key, o.resolved_initial_definition_json FROM character c "
        "JOIN character_instance_origin o ON o.character_id = c.id "
        "WHERE c.world_id = ? ORDER BY c.key",
        (world_id,),
    ).fetchall()
    result: list[str] = []
    for row in rows:
        try:
            components = json.loads(row["resolved_initial_definition_json"]).get("components", [])
            if any(
                isinstance(component, dict)
                and component.get("key") == "cognition.profile"
                and component.get("config", {}).get("level") == "sapient"
                for component in components
            ):
                result.append(row["key"])
        except (TypeError, ValueError):
            continue
    return tuple(result)


def is_sapient(conn: sqlite3.Connection, world_id: int, character_key: str) -> bool:
    return character_key in sapient_character_keys(conn, world_id)
