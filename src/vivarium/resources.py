"""Ressources génériques à seuils : quantité canonique, état dérivé, audit."""

from __future__ import annotations

import sqlite3
from typing import Any, Iterable

from .db import transaction
from .registry import KEY_RE as _KEY_RE
from .util import Clock, new_uuid, parse_iso

MIN_MILLI = 0
MAX_MILLI = 100000


class ResourceError(ValueError):
    """Ressource ou transition invalide, sans écriture partielle."""


def derive(
    anchor_value: int,
    anchor_remainder: int,
    anchor_at: str,
    target_at: str,
    rate_num: int,
    rate_den: int,
) -> tuple[int, int]:
    """Dérive une ressource normalisée par arithmétique entière exacte."""
    if rate_den <= 0:
        raise ResourceError("dénominateur de taux invalide")
    elapsed = int((parse_iso(target_at) - parse_iso(anchor_at)).total_seconds())
    if elapsed < 0:
        raise ResourceError("heure cible antérieure à l'ancre")
    total = anchor_remainder + rate_num * elapsed
    delta = total // rate_den
    remainder = total - delta * rate_den
    value = anchor_value + delta
    if value <= MIN_MILLI or value >= MAX_MILLI:
        return max(MIN_MILLI, min(MAX_MILLI, value)), 0
    return value, remainder


class ResourceEngine:
    """Gère les quantités; les conséquences de chaque état restent externes."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    @staticmethod
    def _key(value: Any, label: str) -> str:
        if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
            raise ResourceError(f"{label} invalide")
        return value

    @staticmethod
    def _integer(value: Any, label: str, minimum: int | None = None) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or (
            minimum is not None and value < minimum
        ):
            raise ResourceError(f"{label} invalide")
        return value

    @classmethod
    def _bands(cls, values: Iterable[Any]) -> tuple[tuple[str, int, int], ...]:
        if isinstance(values, (str, bytes)):
            raise ResourceError("bandes invalides")
        try:
            raw = tuple(values)
        except TypeError as exc:
            raise ResourceError("bandes invalides") from exc
        if not raw:
            raise ResourceError("bandes invalides")
        parsed: list[tuple[str, int, int]] = []
        seen: set[str] = set()
        for item in raw:
            if not isinstance(item, dict) or set(item) != {"state_key", "min_milli", "max_milli"}:
                raise ResourceError("bande invalide")
            key = cls._key(item["state_key"], "state_key")
            lower = cls._integer(item["min_milli"], "min_milli", MIN_MILLI)
            upper = cls._integer(item["max_milli"], "max_milli", MIN_MILLI)
            if key in seen or lower > upper or upper > MAX_MILLI:
                raise ResourceError("bande invalide")
            seen.add(key)
            parsed.append((key, lower, upper))
        parsed.sort(key=lambda item: item[1])
        expected = MIN_MILLI
        for _key, lower, upper in parsed:
            if lower != expected:
                raise ResourceError("bandes non exhaustives ou chevauchantes")
            expected = upper + 1
        if expected != MAX_MILLI + 1:
            raise ResourceError("bandes non exhaustives ou chevauchantes")
        return tuple(parsed)

    def register_resource(
        self,
        world_id: Any,
        character_key: Any,
        resource_key: Any,
        name: Any,
        initial_value_milli: Any,
        rate_num: Any,
        rate_den: Any,
        bands: Iterable[Any],
    ) -> dict[str, Any]:
        """Crée une ressource et ses bandes immuables, avec un seul événement."""
        world_id = self._integer(world_id, "monde", 1)
        character_key = self._key(character_key, "clé de personnage")
        resource_key = self._key(resource_key, "clé de ressource")
        if not isinstance(name, str) or not name.strip():
            raise ResourceError("nom de ressource invalide")
        initial_value_milli = self._integer(initial_value_milli, "valeur initiale", MIN_MILLI)
        rate_num = self._integer(rate_num, "numérateur de taux")
        rate_den = self._integer(rate_den, "dénominateur de taux", 1)
        if initial_value_milli > MAX_MILLI:
            raise ResourceError("valeur initiale invalide")
        bands = self._bands(bands)

        with transaction(self._conn) as conn:
            canonical_now = self._register_resource_in_transaction(
                conn,
                world_id,
                character_key,
                resource_key,
                name,
                initial_value_milli,
                rate_num,
                rate_den,
                bands,
            )
        return self.read_resource(world_id, character_key, resource_key, canonical_now)

    def register_resource_profile(
        self,
        world_id: Any,
        character_key: Any,
        resource_key: Any,
        name: Any,
        initial_value_milli: Any,
        rate_num: Any,
        rate_den: Any,
        bands: Iterable[Any],
        effects_by_state: Any,
    ) -> dict[str, Any]:
        """Installe une ressource, ses bandes et leurs effets en un seul commit.

        C'est le chemin approprié quand une physiologie ou un équipement est
        défini d'avance. Une erreur de contrat ne peut donc jamais laisser une
        ressource à moitié configurée dans le monde.
        """
        world_id = self._integer(world_id, "monde", 1)
        character_key = self._key(character_key, "clé de personnage")
        resource_key = self._key(resource_key, "clé de ressource")
        if not isinstance(name, str) or not name.strip():
            raise ResourceError("nom de ressource invalide")
        initial_value_milli = self._integer(initial_value_milli, "valeur initiale", MIN_MILLI)
        rate_num = self._integer(rate_num, "numérateur de taux")
        rate_den = self._integer(rate_den, "dénominateur de taux", 1)
        if initial_value_milli > MAX_MILLI:
            raise ResourceError("valeur initiale invalide")
        bands = self._bands(bands)
        if not isinstance(effects_by_state, dict):
            raise ResourceError("effets de profil invalides")
        expected_states = {state_key for state_key, _lower, _upper in bands}
        if set(effects_by_state) != expected_states:
            raise ResourceError("effets de profil incomplets")
        effects = {
            state_key: self._effects(effects_by_state[state_key])
            for state_key in expected_states
        }
        with transaction(self._conn) as conn:
            canonical_now = self._register_resource_in_transaction(
                conn,
                world_id,
                character_key,
                resource_key,
                name,
                initial_value_milli,
                rate_num,
                rate_den,
                bands,
            )
            for state_key, _lower, _upper in bands:
                self._declare_band_effects_in_transaction(
                    conn,
                    world_id,
                    character_key,
                    resource_key,
                    state_key,
                    effects[state_key],
                    canonical_now,
                )
        return self.active_effects(world_id, character_key, resource_key, canonical_now)

    def _register_resource_in_transaction(
        self,
        conn: sqlite3.Connection,
        world_id: int,
        character_key: str,
        resource_key: str,
        name: str,
        initial_value_milli: int,
        rate_num: int,
        rate_den: int,
        bands: tuple[tuple[str, int, int], ...],
    ) -> str:
        character = conn.execute(
            "SELECT id FROM character WHERE world_id = ? AND key = ?",
            (world_id, character_key),
        ).fetchone()
        if character is None:
            raise ResourceError("personnage ou monde introuvable")
        existing = conn.execute(
            "SELECT 1 FROM resource_state WHERE character_id = ? AND resource_key = ?",
            (character["id"], resource_key),
        ).fetchone()
        if existing is not None:
            raise ResourceError("ressource déjà enregistrée pour ce personnage")
        definition = conn.execute(
            "SELECT name FROM resource_definition WHERE world_id = ? AND resource_key = ?",
            (world_id, resource_key),
        ).fetchone()
        now = self._clock.now_iso()
        from .world import WorldEngine, SOURCE_SYSTEM, append_event as _append_event

        canonical_now = WorldEngine(conn, clock=self._clock).read_canonical_time(world_id)
        if definition is None:
            conn.execute(
                "INSERT INTO resource_definition "
                "(public_id, world_id, resource_key, name, created_at) VALUES (?, ?, ?, ?, ?)",
                (new_uuid(), world_id, resource_key, name, now),
            )
        elif definition["name"] != name:
            raise ResourceError("définition de ressource incompatible dans ce monde")
        cur = conn.execute(
            "INSERT INTO resource_state "
            "(public_id, world_id, character_id, resource_key, value_milli, rate_num, "
            "rate_den, rate_remainder, anchor_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)",
            (
                new_uuid(), world_id, character["id"], resource_key,
                initial_value_milli, rate_num, rate_den, canonical_now, now,
            ),
        )
        resource_id = cur.lastrowid
        for state_key, lower, upper in bands:
            conn.execute(
                "INSERT INTO resource_state_band "
                "(resource_state_id, state_key, min_milli, max_milli) VALUES (?, ?, ?, ?)",
                (resource_id, state_key, lower, upper),
            )
        state_key = self._state_key(conn, resource_id, initial_value_milli)
        _append_event(
            conn,
            world_id,
            SOURCE_SYSTEM,
            "resource_registered",
            {
                "character": character_key,
                "resource": resource_key,
                "initial_value_milli": initial_value_milli,
                "rate_num": rate_num,
                "rate_den": rate_den,
                "state": state_key,
            },
            occurred_at=canonical_now,
            recorded_at=now,
        )
        return canonical_now

    @staticmethod
    def _state_key(conn: sqlite3.Connection, resource_id: int, value_milli: int) -> str:
        return ResourceEngine._band(conn, resource_id, value_milli)["state_key"]

    @staticmethod
    def _band(
        conn: sqlite3.Connection, resource_id: int, value_milli: int
    ) -> sqlite3.Row:
        row = conn.execute(
            "SELECT id, state_key FROM resource_state_band WHERE resource_state_id = ? "
            "AND min_milli <= ? AND max_milli >= ?",
            (resource_id, value_milli, value_milli),
        ).fetchone()
        if row is None:
            raise ResourceError("aucune bande ne couvre la valeur de ressource")
        return row

    @classmethod
    def _effects(cls, values: Iterable[Any]) -> tuple[dict[str, Any], ...]:
        if isinstance(values, (str, bytes)):
            raise ResourceError("effets invalides")
        try:
            raw = tuple(values)
        except TypeError as exc:
            raise ResourceError("effets invalides") from exc
        if not raw:
            raise ResourceError("effets invalides")
        effects: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for item in raw:
            if not isinstance(item, dict) or not isinstance(item.get("effect_type"), str):
                raise ResourceError("effet invalide")
            effect_type = item["effect_type"]
            effect_key = cls._key(item.get("effect_key"), "clé d'effet")
            identity = (effect_type, effect_key)
            if identity in seen:
                raise ResourceError("effet dupliqué")
            seen.add(identity)
            if effect_type == "capability_availability":
                if set(item) != {"effect_type", "effect_key", "availability"} or item["availability"] not in {
                    "available", "limited", "unavailable"
                }:
                    raise ResourceError("effet de capacité invalide")
                effects.append(
                    {
                        "effect_type": effect_type,
                        "effect_key": effect_key,
                        "availability": item["availability"],
                        "value_milli": None,
                    }
                )
            elif effect_type == "context_signal":
                value = item.get("value_milli")
                if (
                    set(item) != {"effect_type", "effect_key", "value_milli"}
                    or not isinstance(value, int)
                    or isinstance(value, bool)
                    or not -100000 <= value <= 100000
                ):
                    raise ResourceError("signal de contexte invalide")
                effects.append(
                    {
                        "effect_type": effect_type,
                        "effect_key": effect_key,
                        "availability": None,
                        "value_milli": value,
                    }
                )
            else:
                raise ResourceError("type d'effet invalide")
        return tuple(effects)

    def _row(self, world_id: int, character_key: str, resource_key: str) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT rs.id, rs.value_milli, rs.rate_num, rs.rate_den, rs.rate_remainder, rs.anchor_at "
            "FROM resource_state rs JOIN character ch ON ch.id = rs.character_id "
            "WHERE rs.world_id = ? AND ch.key = ? AND rs.resource_key = ?",
            (world_id, character_key, resource_key),
        ).fetchone()
        if row is None:
            raise ResourceError("ressource introuvable")
        return row

    def read_resource(
        self, world_id: Any, character_key: Any, resource_key: Any, target_at: str
    ) -> dict[str, Any]:
        """Lit valeur et état dérivés sans écriture ni événement."""
        world_id = self._integer(world_id, "monde", 1)
        character_key = self._key(character_key, "clé de personnage")
        resource_key = self._key(resource_key, "clé de ressource")
        if not isinstance(target_at, str):
            raise ResourceError("heure cible invalide")
        row = self._row(world_id, character_key, resource_key)
        value, remainder = derive(
            row["value_milli"], row["rate_remainder"], row["anchor_at"], target_at,
            row["rate_num"], row["rate_den"],
        )
        return {
            "resource_key": resource_key,
            "value_milli": value,
            "rate_remainder": remainder,
            "state_key": self._state_key(self._conn, row["id"], value),
            "anchor_at": row["anchor_at"],
        }

    def materialize_resource(
        self, world_id: Any, character_key: Any, resource_key: Any, target_at: str, reason: str
    ) -> dict[str, Any]:
        """Matérialise une ressource et son changement d'état dans une transaction."""
        world_id = self._integer(world_id, "monde", 1)
        character_key = self._key(character_key, "clé de personnage")
        resource_key = self._key(resource_key, "clé de ressource")
        if not isinstance(target_at, str) or not isinstance(reason, str) or not reason:
            raise ResourceError("matérialisation invalide")
        with transaction(self._conn) as conn:
            row = self._row(world_id, character_key, resource_key)
            value, remainder = derive(
                row["value_milli"], row["rate_remainder"], row["anchor_at"], target_at,
                row["rate_num"], row["rate_den"],
            )
            old_state = self._state_key(conn, row["id"], row["value_milli"])
            new_state = self._state_key(conn, row["id"], value)
            now = self._clock.now_iso()
            conn.execute(
                "UPDATE resource_state SET value_milli = ?, rate_remainder = ?, anchor_at = ?, "
                "updated_at = ? WHERE id = ?",
                (value, remainder, target_at, now, row["id"]),
            )
            from .world import SOURCE_ENGINE, append_event as _append_event

            _append_event(
                conn,
                world_id,
                SOURCE_ENGINE,
                "resource_materialized",
                {
                    "character": character_key,
                    "resource": resource_key,
                    "reason": reason,
                    "previous_value_milli": row["value_milli"],
                    "new_value_milli": value,
                    "previous_state": old_state,
                    "new_state": new_state,
                    "rate_num": row["rate_num"],
                    "rate_den": row["rate_den"],
                },
                occurred_at=target_at,
                recorded_at=now,
            )
        return self.read_resource(world_id, character_key, resource_key, target_at)

    def adjust_resource(
        self,
        world_id: Any,
        character_key: Any,
        resource_key: Any,
        delta_milli: Any,
        target_at: str,
        reason: str,
    ) -> dict[str, Any]:
        """Applique un gain ou une perte bornée d'une ressource à un instant donné.

        La valeur est d'abord dérivée depuis son ancre, puis le delta est
        appliqué exactement. Un dépassement est refusé entièrement : le moteur
        ne transforme jamais silencieusement une quantité demandée en une
        quantité tronquée.
        """
        world_id = self._integer(world_id, "monde", 1)
        character_key = self._key(character_key, "clé de personnage")
        resource_key = self._key(resource_key, "clé de ressource")
        if not isinstance(delta_milli, int) or isinstance(delta_milli, bool) or delta_milli == 0:
            raise ResourceError("ajustement de ressource invalide")
        if not isinstance(target_at, str) or not isinstance(reason, str) or not reason:
            raise ResourceError("ajustement de ressource invalide")
        with transaction(self._conn) as conn:
            row = self._row(world_id, character_key, resource_key)
            previous_value, previous_remainder = derive(
                row["value_milli"], row["rate_remainder"], row["anchor_at"], target_at,
                row["rate_num"], row["rate_den"],
            )
            new_value = previous_value + delta_milli
            if not MIN_MILLI <= new_value <= MAX_MILLI:
                raise ResourceError("ajustement de ressource hors limites")
            previous_state = self._state_key(conn, row["id"], previous_value)
            new_state = self._state_key(conn, row["id"], new_value)
            now = self._clock.now_iso()
            conn.execute(
                "UPDATE resource_state SET value_milli = ?, rate_remainder = ?, anchor_at = ?, "
                "updated_at = ? WHERE id = ?",
                (new_value, previous_remainder, target_at, now, row["id"]),
            )
            from .world import SOURCE_ENGINE, append_event as _append_event

            _append_event(
                conn,
                world_id,
                SOURCE_ENGINE,
                "resource_adjusted",
                {
                    "character": character_key,
                    "resource": resource_key,
                    "reason": reason,
                    "delta_milli": delta_milli,
                    "previous_value_milli": previous_value,
                    "new_value_milli": new_value,
                    "previous_state": previous_state,
                    "new_state": new_state,
                    "rate_num": row["rate_num"],
                    "rate_den": row["rate_den"],
                },
                occurred_at=target_at,
                recorded_at=now,
            )
        return self.read_resource(world_id, character_key, resource_key, target_at)

    def declare_band_effects(
        self,
        world_id: Any,
        character_key: Any,
        resource_key: Any,
        state_key: Any,
        effects: Iterable[Any],
    ) -> list[dict[str, Any]]:
        """Fige les effets d'une bande, avec une trace canonique unique."""
        world_id = self._integer(world_id, "monde", 1)
        character_key = self._key(character_key, "clé de personnage")
        resource_key = self._key(resource_key, "clé de ressource")
        state_key = self._key(state_key, "state_key")
        effects = self._effects(effects)
        with transaction(self._conn) as conn:
            from .world import WorldEngine

            canonical_now = WorldEngine(conn, clock=self._clock).read_canonical_time(world_id)
            self._declare_band_effects_in_transaction(
                conn,
                world_id,
                character_key,
                resource_key,
                state_key,
                effects,
                canonical_now,
            )
        return self.active_effects(world_id, character_key, resource_key, canonical_now)["effects"]

    def _declare_band_effects_in_transaction(
        self,
        conn: sqlite3.Connection,
        world_id: int,
        character_key: str,
        resource_key: str,
        state_key: str,
        effects: tuple[dict[str, Any], ...],
        canonical_now: str,
    ) -> None:
        row = self._row(world_id, character_key, resource_key)
        band = conn.execute(
            "SELECT id FROM resource_state_band WHERE resource_state_id = ? AND state_key = ?",
            (row["id"], state_key),
        ).fetchone()
        if band is None:
            raise ResourceError("bande de ressource introuvable")
        if conn.execute(
            "SELECT 1 FROM resource_state_effect WHERE resource_state_band_id = ?",
            (band["id"],),
        ).fetchone() is not None:
            raise ResourceError("les effets de cette bande sont déjà déclarés")
        for effect in effects:
            conn.execute(
                "INSERT INTO resource_state_effect "
                "(resource_state_band_id, effect_type, effect_key, availability, value_milli) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    band["id"],
                    effect["effect_type"],
                    effect["effect_key"],
                    effect["availability"],
                    effect["value_milli"],
                ),
            )
        from .world import SOURCE_SYSTEM, append_event as _append_event

        _append_event(
            conn,
            world_id,
            SOURCE_SYSTEM,
            "resource_effects_declared",
            {
                "character": character_key,
                "resource": resource_key,
                "state": state_key,
                "effects": effects,
            },
            occurred_at=canonical_now,
            recorded_at=self._clock.now_iso(),
        )

    def active_effects(
        self, world_id: Any, character_key: Any, resource_key: Any, target_at: str
    ) -> dict[str, Any]:
        """Retourne les effets actifs de la bande dérivée, sans écriture."""
        world_id = self._integer(world_id, "monde", 1)
        character_key = self._key(character_key, "clé de personnage")
        resource_key = self._key(resource_key, "clé de ressource")
        if not isinstance(target_at, str):
            raise ResourceError("heure cible invalide")
        row = self._row(world_id, character_key, resource_key)
        value, _remainder = derive(
            row["value_milli"], row["rate_remainder"], row["anchor_at"], target_at,
            row["rate_num"], row["rate_den"],
        )
        band = self._band(self._conn, row["id"], value)
        rows = self._conn.execute(
            "SELECT effect_type, effect_key, availability, value_milli "
            "FROM resource_state_effect WHERE resource_state_band_id = ? "
            "ORDER BY effect_type, effect_key",
            (band["id"],),
        ).fetchall()
        return {
            "resource_key": resource_key,
            "value_milli": value,
            "state_key": band["state_key"],
            "effects": [dict(item) for item in rows],
        }
