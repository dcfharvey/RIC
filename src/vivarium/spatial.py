"""Connectivité spatiale de la résidence (Lot 2.2).

Le graphe est **orienté** : une ligne de `location_link` signifie toujours qu'on
peut passer de `from_location_id` vers `to_location_id`. Un passage physique
bidirectionnel est représenté par deux lignes réciproques.

Distinction conceptuelle de l'API :
- `can_traverse(A, B)` : une arête dirigée A→B existe ;
- `has_physical_connection(A, B)` : au moins une arête existe dans un sens ou
  l'autre ;
- `adjacent_from(A)` : lieux directement atteignables depuis A ;
- `find_path(A, B)` : trajet dirigé valide (BFS, toutes traversées à coût égal).

Les recherches (adjacence, trajet, intégrité) sont des **lectures pures** :
aucune écriture ni événement. Les modifications administratives du graphe
(`add_link`/`remove_link`) sont effectuées par le moteur, dans une seule
transaction, et produisent un unique événement canonique par opération.
"""

from __future__ import annotations

import sqlite3
from collections import deque
from typing import Any

from .db import transaction
from .seed import SEED_LINKS
from .util import Clock, new_uuid
from .world import SOURCE_OWNER, _append_event

DEFAULT_KIND = "door"


class GraphError(RuntimeError):
    """Erreur de graphe (opération invalide, lieu inexistant, trajet impossible)."""


def _now_iso(clock: Clock) -> str:
    return clock.now_iso()


class GraphEngine:
    """Moteur du graphe spatial. Uniquement des lectures et des modifications admin."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    # --- Résolution -------------------------------------------------------------

    def _location_id(self, world_id: int, key: str) -> int:
        row = self._conn.execute(
            "SELECT id FROM location WHERE world_id = ? AND key = ?", (world_id, key)
        ).fetchone()
        if row is None:
            raise GraphError(f"lieu introuvable : {key!r} (monde {world_id})")
        return row["id"]

    def _directed_ids(self, world_id: int, from_id: int) -> list[int]:
        rows = self._conn.execute(
            "SELECT to_location_id FROM location_link "
            "WHERE world_id = ? AND from_location_id = ?",
            (world_id, from_id),
        ).fetchall()
        return [r["to_location_id"] for r in rows]

    def _id_to_key(self, world_id: int) -> dict[int, str]:
        return {
            r["id"]: r["key"]
            for r in self._conn.execute(
                "SELECT id, key FROM location WHERE world_id = ?", (world_id,)
            )
        }

    def _canonical_time(self, world_id: int) -> str:
        from .world import WorldEngine  # évite un cycle d'import

        return WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id)

    # --- Lectures pures (aucune écriture) ---------------------------------------

    def can_traverse(self, world_id: int, a_key: str, b_key: str) -> bool:
        """Vrai si une arête dirigée A→B existe."""
        a, b = self._location_id(world_id, a_key), self._location_id(world_id, b_key)
        row = self._conn.execute(
            "SELECT 1 FROM location_link WHERE world_id = ? "
            "AND from_location_id = ? AND to_location_id = ?",
            (world_id, a, b),
        ).fetchone()
        return row is not None

    def has_physical_connection(self, world_id: int, a_key: str, b_key: str) -> bool:
        """Vrai si au moins une arête existe entre A et B (dans un sens ou l'autre)."""
        a, b = self._location_id(world_id, a_key), self._location_id(world_id, b_key)
        row = self._conn.execute(
            "SELECT 1 FROM location_link WHERE world_id = ? "
            "AND ((from_location_id = ? AND to_location_id = ?) "
            "     OR (from_location_id = ? AND to_location_id = ?)) "
            "LIMIT 1",
            (world_id, a, b, b, a),
        ).fetchone()
        return row is not None

    def adjacent_from(self, world_id: int, a_key: str) -> list[str]:
        """Clés des lieux directement atteignables depuis A (arêtes A→X)."""
        a = self._location_id(world_id, a_key)
        rows = self._conn.execute(
            "SELECT l.key FROM location_link ll "
            "JOIN location l ON l.id = ll.to_location_id "
            "WHERE ll.world_id = ? AND ll.from_location_id = ? "
            "ORDER BY l.key",
            (world_id, a),
        ).fetchall()
        return [r["key"] for r in rows]

    def find_path(self, world_id: int, a_key: str, b_key: str) -> list[str] | None:
        """Trajet dirigé valide de A vers B (BFS), ou None si impossible."""
        start, goal = self._location_id(world_id, a_key), self._location_id(world_id, b_key)
        id_key = self._id_to_key(world_id)
        if start == goal:
            return [a_key]
        parent: dict[int, int | None] = {start: None}
        queue: deque[int] = deque([start])
        while queue:
            cur = queue.popleft()
            if cur == goal:
                break
            for nxt in self._directed_ids(world_id, cur):
                if nxt not in parent:
                    parent[nxt] = cur
                    queue.append(nxt)
        if goal not in parent:
            return None
        path: list[int] = [goal]
        while parent[path[-1]] is not None:
            path.append(parent[path[-1]])
        path.reverse()
        return [id_key[i] for i in path]

    def check_graph_integrity(self, world_id: int) -> dict[str, Any]:
        """Rapport d'intégrité du graphe (lecture pure).

        R1 pas de boucle A→A ; R2 même monde (FK) ; R3 pas d'arête dupliquée ;
        R4 destinations existantes ; R5 tous les lieux du seed accessibles depuis
        `salon` ; R6 chaque passage bidirectionnel du seed a ses deux arêtes.
        """
        self_loops = self._conn.execute(
            "SELECT COUNT(*) FROM location_link "
            "WHERE world_id = ? AND from_location_id = to_location_id",
            (world_id,),
        ).fetchone()[0]

        total = self._conn.execute(
            "SELECT COUNT(*) FROM location_link WHERE world_id = ?", (world_id,)
        ).fetchone()[0]
        distinct = self._conn.execute(
            "SELECT COUNT(*) FROM (SELECT 1 FROM location_link WHERE world_id = ? "
            "GROUP BY world_id, from_location_id, to_location_id)",
            (world_id,),
        ).fetchone()[0]
        duplicates = total - distinct

        fk = [
            dict(r)
            for r in self._conn.execute("SELECT * FROM pragma_foreign_key_check")
            if r["table"] == "location_link"
        ]

        location_keys = [
            r["key"]
            for r in self._conn.execute(
                "SELECT key FROM location WHERE world_id = ? ORDER BY key", (world_id,)
            )
        ]
        unreachable: list[str] = []
        for key in location_keys:
            if key != "salon" and self.find_path(world_id, "salon", key) is None:
                unreachable.append(key)

        missing_reciprocal: list[tuple[str, str]] = []
        for a, b in SEED_LINKS:
            if not (self.can_traverse(world_id, a, b) and self.can_traverse(world_id, b, a)):
                missing_reciprocal.append((a, b))

        ok = (
            self_loops == 0
            and duplicates == 0
            and not fk
            and not unreachable
            and not missing_reciprocal
        )
        return {
            "ok": ok,
            "self_loops": self_loops,
            "duplicate_edges": duplicates,
            "fk_violations": fk,
            "unreachable_from_salon": unreachable,
            "missing_reciprocal": missing_reciprocal,
        }

    # --- Modifications administratives (une transaction, un événement) ---------

    def _insert_edge(self, c: sqlite3.Connection, world_id: int, from_id: int, to_id: int, kind: str) -> None:
        if from_id == to_id:
            raise GraphError("boucle sur soi : impossible de relier un lieu à lui-même")
        created = _now_iso(self._clock)
        c.execute(
            "INSERT INTO location_link "
            "(public_id, world_id, from_location_id, to_location_id, kind, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (new_uuid(), world_id, from_id, to_id, kind, created),
        )

    def add_link(
        self,
        world_id: int,
        a_key: str,
        b_key: str,
        *,
        bidirectional: bool = True,
        kind: str = DEFAULT_KIND,
    ) -> dict[str, Any]:
        """Ajoute un passage physique. `bidirectional=True` crée les deux arêtes
        réciproques dans la même transaction ; sinon une seule (A→B).

        Produit un **unique** événement canonique et échoue entièrement (rollback)
        si une partie de l'opération échoue.
        """
        a = self._location_id(world_id, a_key)
        b = self._location_id(world_id, b_key)
        with transaction(self._conn) as c:
            self._insert_edge(c, world_id, a, b, kind)
            if bidirectional:
                self._insert_edge(c, world_id, b, a, kind)
            _append_event(
                c, world_id, SOURCE_OWNER, "link_added",
                {"from": a_key, "to": b_key, "bidirectional": bidirectional, "kind": kind},
                occurred_at=self._canonical_time(world_id),
                recorded_at=_now_iso(self._clock),
            )
        return {"from": a_key, "to": b_key, "bidirectional": bidirectional, "kind": kind}

    def remove_link(
        self,
        world_id: int,
        a_key: str,
        b_key: str,
        *,
        bidirectional: bool = True,
    ) -> dict[str, Any]:
        """Supprime un passage physique. `bidirectional=True` retire les deux
        arêtes réciproques ; sinon une seule (A→B). Une transaction, un événement.
        """
        a = self._location_id(world_id, a_key)
        b = self._location_id(world_id, b_key)
        with transaction(self._conn) as c:
            removed = 0
            removed += c.execute(
                "DELETE FROM location_link WHERE world_id = ? "
                "AND from_location_id = ? AND to_location_id = ?",
                (world_id, a, b),
            ).rowcount
            if bidirectional:
                removed += c.execute(
                    "DELETE FROM location_link WHERE world_id = ? "
                    "AND from_location_id = ? AND to_location_id = ?",
                    (world_id, b, a),
                ).rowcount
            if removed == 0:
                raise GraphError(
                    f"passage inexistant entre {a_key!r} et {b_key!r}"
                )
            _append_event(
                c, world_id, SOURCE_OWNER, "link_removed",
                {"from": a_key, "to": b_key, "bidirectional": bidirectional},
                occurred_at=self._canonical_time(world_id),
                recorded_at=_now_iso(self._clock),
            )
        return {"from": a_key, "to": b_key, "bidirectional": bidirectional}
