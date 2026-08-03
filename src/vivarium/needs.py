"""Besoins dérivés et matérialisation (Sous-lot 3.2A).

Valeur entière à précision fixe : `value_milli ∈ [0, 100000]` (0 = très
déficient, 100000 = pleinement satisfait ; affichage = /1000). Taux rationnel
entier `rate_num / rate_den` en milli par seconde simulée.

`rate_remainder` conserve la fraction entre deux matérialisations afin que
l'évolution soit **exactement** indépendante du découpage : 12 h en une fois ou
12 × 1 h donnent la même valeur et le même reste.

Le calcul est entièrement en arithmétique entière (division plancher), sans
REAL, donc exactement reproductible.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from .db import transaction
from .seed import SEED_NEEDS
from .util import Clock, new_uuid, parse_iso

MAX_MILLI = 100000


class NeedsError(RuntimeError):
    """Erreur de besoin (heure antérieure, taux invalide, personnage inconnu…)."""


def derive(
    anchor_value: int,
    anchor_remainder: int,
    anchor_at: str,
    target_at: str,
    rate_num: int,
    rate_den: int,
) -> tuple[int, int]:
    """Calcule la valeur et le reste dérivés sur [anchor_at, target_at].

    total        = ancien_reste + rate_num * dt_seconds
    delta        = total // rate_den            (division plancher)
    reste_nouveau = total - delta * rate_den    (0 <= reste < rate_den)
    valeur       = ancrée + delta, puis clamp [0, 100000] ; un clamp sur une
    borne remet le reste à zéro (aucune fraction résiduelle ne ressurgit).
    """
    if rate_den <= 0:
        raise NeedsError("rate_den doit être > 0")
    dt_seconds = int((parse_iso(target_at) - parse_iso(anchor_at)).total_seconds())
    if dt_seconds < 0:
        raise NeedsError(
            "heure cible antérieure à l'heure d'ancrage : calcul refusé"
        )
    total = anchor_remainder + rate_num * dt_seconds
    delta = total // rate_den
    new_remainder = total - delta * rate_den
    if not (0 <= new_remainder < rate_den):
        raise NeedsError("reste rationnel hors bornes (ne devrait pas arriver)")
    new_value = anchor_value + delta
    if new_value <= 0 or new_value >= MAX_MILLI:
        new_value = max(0, min(MAX_MILLI, new_value))
        new_remainder = 0
    return new_value, new_remainder


def _emit_event(c, world_id: int, payload: dict[str, Any], recorded_at: str) -> None:
    from .world import SOURCE_ENGINE, _append_event  # évite un cycle d'import

    _append_event(
        c, world_id, SOURCE_ENGINE, "needs_materialized", payload, recorded_at=recorded_at
    )


class NeedsEngine:
    """Moteur des besoins. Écritures uniquement via la couche canonique."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _join_rows(self, conn: sqlite3.Connection, world_id: int, character_key: str):
        return conn.execute(
            "SELECT ns.id, ns.world_id, ns.character_id, ns.need_key, "
            "       ns.value_milli, ns.rate_remainder, ns.anchor_at, "
            "       nd.rate_num, nd.rate_den "
            "FROM need_state ns "
            "JOIN need_definition nd ON nd.world_id = ns.world_id "
            "                         AND nd.need_key = ns.need_key "
            "JOIN character ch ON ch.world_id = ns.world_id "
            "                  AND ch.id = ns.character_id "
            "WHERE ch.world_id = ? AND ch.key = ? "
            "ORDER BY ns.need_key",
            (world_id, character_key),
        ).fetchall()

    # --- Lecture pure (dérivation, aucune écriture) -----------------------------

    def derive_need(
        self, world_id: int, character_key: str, need_key: str, target_at: str
    ) -> tuple[int, int]:
        rows: list[Any] = [
            r for r in self._join_rows(self._conn, world_id, character_key)
            if r["need_key"] == need_key
        ]
        if not rows:
            raise NeedsError(f"besoin inconnu : {need_key!r} ({character_key!r})")
        r = rows[0]
        return derive(
            r["value_milli"], r["rate_remainder"], r["anchor_at"], target_at,
            r["rate_num"], r["rate_den"],
        )

    def derive_character(
        self, world_id: int, character_key: str, target_at: str
    ) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = {}
        for r in self._join_rows(self._conn, world_id, character_key):
            v, rem = derive(
                r["value_milli"], r["rate_remainder"], r["anchor_at"], target_at,
                r["rate_num"], r["rate_den"],
            )
            out[r["need_key"]] = {"value_milli": v, "rate_remainder": rem}
        return out

    # --- Matérialisation -------------------------------------------------------

    def materialize_character_needs(
        self,
        world_id: int,
        character_key: str,
        target_at: str,
        reason: str,
        *,
        _conn: sqlite3.Connection | None = None,
    ) -> dict[str, Any] | None:
        """Matérialise les quatre besoins d'un personnage.

        S'il n'y a aucun besoin à matérialiser, ne fait rien (pas d'écriture ni
        d'événement). Si `_conn` est fourni (transaction déjà ouverte par
        l'autorité canonique), opère dans cette transaction sans BEGIN/COMMIT.
        """
        if _conn is None:
            with transaction(self._conn) as c:
                return self._materialize(c, world_id, character_key, target_at, reason)
        return self._materialize(_conn, world_id, character_key, target_at, reason)

    def _materialize(
        self, c: sqlite3.Connection, world_id: int, character_key: str,
        target_at: str, reason: str,
    ) -> dict[str, Any] | None:
        rows = self._join_rows(c, world_id, character_key)
        if not rows:
            return None  # rien à matérialiser

        recorded = self._clock.now_iso()
        previous_anchor = rows[0]["anchor_at"]
        prev_vals: dict[str, int] = {}
        prev_rem: dict[str, int] = {}
        new_vals: dict[str, int] = {}
        new_rem: dict[str, int] = {}
        for r in rows:
            v, rem = derive(
                r["value_milli"], r["rate_remainder"], r["anchor_at"], target_at,
                r["rate_num"], r["rate_den"],
            )
            if not (0 <= rem < r["rate_den"]):
                raise NeedsError("reste rationnel hors bornes")
            prev_vals[r["need_key"]] = r["value_milli"]
            prev_rem[r["need_key"]] = r["rate_remainder"]
            new_vals[r["need_key"]] = v
            new_rem[r["need_key"]] = rem
            c.execute(
                "UPDATE need_state SET value_milli = ?, rate_remainder = ?, "
                "anchor_at = ?, updated_at = ? WHERE id = ?",
                (v, rem, target_at, recorded, r["id"]),
            )

        _emit_event(
            c,
            world_id,
            {
                "character": character_key,
                "reason": reason,
                "previous_anchor_at": previous_anchor,
                "new_anchor_at": target_at,
                "previous_values": prev_vals,
                "new_values": new_vals,
                "previous_remainders": prev_rem,
                "new_remainders": new_rem,
            },
            recorded_at=recorded,
        )
        return {
            "previous_anchor_at": previous_anchor,
            "new_anchor_at": target_at,
            "previous_values": prev_vals,
            "new_values": new_vals,
            "previous_remainders": prev_rem,
            "new_remainders": new_rem,
        }


def upgrade_dev_needs(
    conn: sqlite3.Connection, world_id: int, clock: Clock | None = None
) -> dict[str, int]:
    """Mise à niveau non destructive des besoins (Sous-lot 3.2A).

    Insère les `need_definition` et `need_state` manquants du monde, ancrés à
    l'heure simulée canonique courante (jamais l'heure système). Idempotente :
    une seconde exécution ne modifie ni valeur, ni ancre, ni reste, ni journal.
    """
    from .world import WorldEngine  # évite un cycle d'import

    engine = NeedsEngine(conn, clock=clock)
    world_engine = WorldEngine(conn, clock=clock)
    now = world_engine.read_canonical_time(world_id)

    with transaction(conn) as c:
        existing_defs = {
            r["need_key"]
            for r in c.execute(
                "SELECT need_key FROM need_definition WHERE world_id = ?", (world_id,)
            )
        }
        added_defs = 0
        for key, name, initial, num, den, thr in SEED_NEEDS:
            if key in existing_defs:
                continue
            c.execute(
                "INSERT INTO need_definition "
                "(public_id, world_id, need_key, name, min_milli, max_milli, "
                " rate_num, rate_den, threshold_milli, created_at) "
                "VALUES (?, ?, ?, ?, 0, 100000, ?, ?, ?, ?)",
                (new_uuid(), world_id, key, name, num, den, thr, now),
            )
            added_defs += 1
        added_states = 0
        for char_row in c.execute(
            "SELECT id, key FROM character WHERE world_id = ?", (world_id,)
        ):
            existing_keys = {
                r["need_key"]
                for r in c.execute(
                    "SELECT need_key FROM need_state WHERE character_id = ?",
                    (char_row["id"],),
                )
            }
            for key, name, initial, num, den, thr in SEED_NEEDS:
                if key in existing_keys:
                    continue
                c.execute(
                    "INSERT INTO need_state "
                    "(public_id, world_id, character_id, need_key, value_milli, "
                    " rate_remainder, anchor_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, 0, ?, ?)",
                    (
                        new_uuid(), world_id, char_row["id"], key,
                        initial, now, now,
                    ),
                )
                added_states += 1
    return {"definitions_added": added_defs, "states_added": added_states}
