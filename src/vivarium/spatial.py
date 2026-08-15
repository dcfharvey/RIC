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
from .util import Clock, new_uuid
from .world import SOURCE_OWNER, append_event as _append_event

DEFAULT_KIND = "door"


class GraphError(RuntimeError):
    """Erreur de graphe (opération invalide, lieu inexistant, trajet impossible)."""

    def __init__(self, message: str, *, code: str = "graph_error") -> None:
        super().__init__(message)
        self.code = code


def _now_iso(clock: Clock) -> str:
    return clock.now_iso()


class GraphEngine:
    """Moteur du graphe spatial. Uniquement des lectures et des modifications admin."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    # --- Résolution -------------------------------------------------------------

    def location_id(self, world_id: int, key: str) -> int:
        row = self._conn.execute(
            "SELECT id FROM location WHERE world_id = ? AND key = ?", (world_id, key)
        ).fetchone()
        if row is None:
            raise GraphError(
                f"lieu introuvable : {key!r} (monde {world_id})",
                code="location_not_found",
            )
        return row["id"]

    _location_id = location_id

    @staticmethod
    def normalize_link_request(
        a_key: Any, b_key: Any, bidirectional: Any, kind: Any
    ) -> tuple[str, str, bool, str]:
        """Valide la forme d'un ajout de passage sans écriture."""
        if not isinstance(a_key, str) or not a_key:
            raise GraphError("origine de passage invalide", code="invalid_parameters")
        if not isinstance(b_key, str) or not b_key:
            raise GraphError("destination de passage invalide", code="invalid_parameters")
        if a_key == b_key:
            raise GraphError("boucle sur soi : passage invalide", code="invalid_link")
        if not isinstance(bidirectional, bool):
            raise GraphError("bidirectional invalide", code="invalid_parameters")
        if not isinstance(kind, str) or not kind.strip():
            raise GraphError("type de passage invalide", code="invalid_parameters")
        return a_key, b_key, bidirectional, kind.strip()

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

    def _connectivity_report(
        self,
        world_id: int,
        *,
        excluded_edges: frozenset[tuple[int, int]] = frozenset(),
    ) -> dict[str, Any]:
        """Vérifie la politique topologique déclarée du monde.

        Le graphe est orienté : être atteignable depuis le salon ne suffit pas
        si une résidente ne peut plus y revenir. Cette lecture est aussi sûre
        dans la transaction qui vient de retirer un passage.
        """
        policy = self._conn.execute(
            "SELECT policy_key, anchor_location_id FROM world_topology_policy WHERE world_id = ?",
            (world_id,),
        ).fetchone()
        if policy is None or policy["policy_key"] == "none":
            return {
                "ok": True,
                "policy": "none",
                "anchor": None,
                "root_missing": False,
                "unreachable_from_anchor": [],
                "unreachable_to_anchor": [],
            }
        id_to_key = self._id_to_key(world_id)
        root = policy["anchor_location_id"]
        if root not in id_to_key:
            return {
                "ok": False,
                "policy": policy["policy_key"],
                "anchor": None,
                "root_missing": True,
                "unreachable_from_anchor": sorted(id_to_key.values()),
                "unreachable_to_anchor": sorted(id_to_key.values()),
            }
        outgoing: dict[int, list[int]] = {location_id: [] for location_id in id_to_key}
        incoming: dict[int, list[int]] = {location_id: [] for location_id in id_to_key}
        for row in self._conn.execute(
            "SELECT from_location_id, to_location_id FROM location_link WHERE world_id = ? "
            "ORDER BY from_location_id, to_location_id",
            (world_id,),
        ):
            if (row["from_location_id"], row["to_location_id"]) in excluded_edges:
                continue
            outgoing[row["from_location_id"]].append(row["to_location_id"])
            incoming[row["to_location_id"]].append(row["from_location_id"])

        def reached(adjacency: dict[int, list[int]]) -> set[int]:
            seen = {root}
            queue: deque[int] = deque([root])
            while queue:
                current = queue.popleft()
                for neighbor in adjacency[current]:
                    if neighbor not in seen:
                        seen.add(neighbor)
                        queue.append(neighbor)
            return seen

        from_salon = reached(outgoing)
        to_salon = reached(incoming)  # graphe inversé : lieu → salon dans le vrai graphe
        unreachable_from = sorted(id_to_key[location_id] for location_id in id_to_key.keys() - from_salon)
        unreachable_to = sorted(id_to_key[location_id] for location_id in id_to_key.keys() - to_salon)
        return {
            "ok": not unreachable_from and not unreachable_to,
            "policy": policy["policy_key"],
            "anchor": id_to_key[root],
            "root_missing": False,
            "unreachable_from_anchor": unreachable_from,
            "unreachable_to_anchor": unreachable_to,
        }

    def _canonical_time(self, world_id: int) -> str:
        from .world import WorldEngine  # évite un cycle d'import

        return WorldEngine(self._conn, clock=self._clock).read_canonical_time(world_id)

    @staticmethod
    def normalize_remove_link_request(
        a_key: Any, b_key: Any, bidirectional: Any
    ) -> tuple[str, str, bool]:
        """Valide la forme d'une fermeture sans écrire."""
        a_key, b_key, bidirectional, _kind = GraphEngine.normalize_link_request(
            a_key, b_key, bidirectional, DEFAULT_KIND
        )
        return a_key, b_key, bidirectional

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

        connectivity = self._connectivity_report(world_id)

        ok = (
            self_loops == 0
            and duplicates == 0
            and not fk
            and connectivity["ok"]
        )
        return {
            "ok": ok,
            "self_loops": self_loops,
            "duplicate_edges": duplicates,
            "fk_violations": fk,
            "topology_policy": connectivity["policy"],
            "topology_anchor": connectivity["anchor"],
            "unreachable_from_anchor": connectivity["unreachable_from_anchor"],
            "unreachable_to_anchor": connectivity["unreachable_to_anchor"],
            "root_missing": connectivity["root_missing"],
        }

    def preview_remove_link(
        self, world_id: int, a_key: Any, b_key: Any, *, bidirectional: Any = True
    ) -> dict[str, Any]:
        """Calcule en lecture pure l'impact topologique d'une fermeture.

        Cette prévisualisation n'autorise pas la fermeture : l'application
        répète le même contrôle dans sa transaction pour éliminer toute fenêtre
        entre impact et mutation.
        """
        a_key, b_key, bidirectional = self.normalize_remove_link_request(
            a_key, b_key, bidirectional
        )
        a = self._location_id(world_id, a_key)
        b = self._location_id(world_id, b_key)
        requested = [(a, b)] + ([(b, a)] if bidirectional else [])
        existing = frozenset(
            (from_id, to_id)
            for from_id, to_id in requested
            if self._conn.execute(
                "SELECT 1 FROM location_link WHERE world_id = ? "
                "AND from_location_id = ? AND to_location_id = ?",
                (world_id, from_id, to_id),
            ).fetchone()
            is not None
        )
        if not existing:
            raise GraphError("passage inexistant", code="link_not_found")
        connectivity = self._connectivity_report(world_id, excluded_edges=existing)
        return {
            "from": a_key,
            "to": b_key,
            "bidirectional": bidirectional,
            "directed_links_removed": len(existing),
            "connectivity": connectivity,
        }

    # --- Modifications administratives (une transaction, un événement) ---------

    def _insert_edge(self, c: sqlite3.Connection, world_id: int, from_id: int, to_id: int, kind: str) -> None:
        if from_id == to_id:
            raise GraphError(
                "boucle sur soi : impossible de relier un lieu à lui-même",
                code="invalid_link",
            )
        created = _now_iso(self._clock)
        c.execute(
            "INSERT INTO location_link "
            "(public_id, world_id, from_location_id, to_location_id, kind, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (new_uuid(), world_id, from_id, to_id, kind, created),
        )

    def _add_link_in_transaction(
        self,
        conn: sqlite3.Connection,
        world_id: int,
        a_key: str,
        b_key: str,
        *,
        bidirectional: bool,
        kind: str,
        admin_change_id: str | None = None,
    ) -> dict[str, Any]:
        """Ajoute un passage dans une transaction déjà ouverte."""
        a = self._location_id(world_id, a_key)
        b = self._location_id(world_id, b_key)
        canonical_at = self._canonical_time(world_id)
        self._insert_edge(conn, world_id, a, b, kind)
        if bidirectional:
            self._insert_edge(conn, world_id, b, a, kind)
        payload: dict[str, Any] = {
            "from": a_key,
            "to": b_key,
            "bidirectional": bidirectional,
            "kind": kind,
        }
        if admin_change_id is not None:
            payload["admin_change_id"] = admin_change_id
        _append_event(
            conn,
            world_id,
            SOURCE_OWNER,
            "link_added",
            payload,
            occurred_at=canonical_at,
            recorded_at=_now_iso(self._clock),
        )
        return {**payload, "canonical_at": canonical_at}

    def add_link_in_transaction(
        self,
        conn: sqlite3.Connection,
        world_id: int,
        a_key: str,
        b_key: str,
        *,
        bidirectional: bool,
        kind: str,
        admin_change_id: str | None = None,
    ) -> dict[str, Any]:
        """Ajoute un passage dans une transaction déjà ouverte."""
        return self._add_link_in_transaction(
            conn,
            world_id,
            a_key,
            b_key,
            bidirectional=bidirectional,
            kind=kind,
            admin_change_id=admin_change_id,
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
        a_key, b_key, bidirectional, kind = self.normalize_link_request(
            a_key, b_key, bidirectional, kind
        )
        with transaction(self._conn) as c:
            self._add_link_in_transaction(
                c, world_id, a_key, b_key, bidirectional=bidirectional, kind=kind
            )
        return {"from": a_key, "to": b_key, "bidirectional": bidirectional, "kind": kind}

    def _remove_link_in_transaction(
        self,
        conn: sqlite3.Connection,
        world_id: int,
        a_key: str,
        b_key: str,
        *,
        bidirectional: bool,
        admin_change_id: str | None = None,
    ) -> dict[str, Any]:
        """Retire un passage et vérifie sa sûreté dans la transaction active."""
        a = self._location_id(world_id, a_key)
        b = self._location_id(world_id, b_key)
        removed = 0
        removed += conn.execute(
            "DELETE FROM location_link WHERE world_id = ? "
            "AND from_location_id = ? AND to_location_id = ?",
            (world_id, a, b),
        ).rowcount
        if bidirectional:
            removed += conn.execute(
                "DELETE FROM location_link WHERE world_id = ? "
                "AND from_location_id = ? AND to_location_id = ?",
                (world_id, b, a),
            ).rowcount
        if removed == 0:
            raise GraphError("passage inexistant", code="link_not_found")
        connectivity = self._connectivity_report(world_id)
        if not connectivity["ok"]:
            raise GraphError(
                "fermeture refusée : elle isolerait un ou plusieurs lieux "
                f"(depuis ancre={connectivity['unreachable_from_anchor']}, "
                f"vers ancre={connectivity['unreachable_to_anchor']})",
                code="would_isolate_location",
            )
        canonical_at = self._canonical_time(world_id)
        payload: dict[str, Any] = {
            "from": a_key,
            "to": b_key,
            "bidirectional": bidirectional,
            "directed_links_removed": removed,
        }
        if admin_change_id is not None:
            payload["admin_change_id"] = admin_change_id
        _append_event(
            conn, world_id, SOURCE_OWNER, "link_removed", payload,
            occurred_at=canonical_at, recorded_at=_now_iso(self._clock),
        )
        return {**payload, "canonical_at": canonical_at}

    def remove_link_in_transaction(
        self,
        conn: sqlite3.Connection,
        world_id: int,
        a_key: str,
        b_key: str,
        *,
        bidirectional: bool,
        admin_change_id: str | None = None,
    ) -> dict[str, Any]:
        """Retire un passage dans une transaction déjà ouverte."""
        return self._remove_link_in_transaction(
            conn,
            world_id,
            a_key,
            b_key,
            bidirectional=bidirectional,
            admin_change_id=admin_change_id,
        )

    def remove_link(
        self,
        world_id: int,
        a_key: str,
        b_key: str,
        *,
        bidirectional: bool = True,
    ) -> dict[str, Any]:
        """Supprime un passage sans pouvoir isoler un lieu."""
        a_key, b_key, bidirectional = self.normalize_remove_link_request(
            a_key, b_key, bidirectional
        )
        preview = self.preview_remove_link(world_id, a_key, b_key, bidirectional=bidirectional)
        if not preview["connectivity"]["ok"]:
            raise GraphError(
                "fermeture refusée : elle isolerait un ou plusieurs lieux "
                f"(depuis ancre={preview['connectivity']['unreachable_from_anchor']}, "
                f"vers ancre={preview['connectivity']['unreachable_to_anchor']})",
                code="would_isolate_location",
            )
        with transaction(self._conn) as conn:
            applied = self._remove_link_in_transaction(
                conn, world_id, a_key, b_key, bidirectional=bidirectional
            )
        return {
            field: applied[field]
            for field in ("from", "to", "bidirectional", "directed_links_removed")
        }
