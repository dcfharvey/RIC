"""Activités et effets (Sous-lot 3.2B).

Une activité applique un **régime de taux net** (en unités /36 par seconde) à
chacun des quatre besoins pendant [started_at, planned_end_at]. Le calcul reste
en arithmétique entière (dénominateur canonique 36, reste conservé).

`ActivityEngine` exploite les API internes (qui acceptent une connexion dans une
transaction déjà ouverte) afin que chaque transition soit **atomique** sans
transaction imbriquée : déplacements pièce par pièce + matérialisation +
création/clôture + événements dans une seule transaction. L'autorité canonique
unique est préservée (écritures via `db.transaction` + `world._append_event`).
"""

from __future__ import annotations

import sqlite3
from datetime import timedelta
from typing import Any

from .character import CharacterEngine, CharacterError
from .db import transaction
from .injury import (
    MOVEMENT_SURCHARGE_MILLI,
    InjuryEngine,
    level,
)
from .needs import NeedsEngine
from .seed import SEED_ACTIVITIES, SEED_ACTIVITY_ALLOWED
from .spatial import GraphEngine
from .policy import MAX_IDLE
from .util import Clock, new_uuid, parse_iso, to_iso
from .world import SOURCE_ENGINE, SOURCE_SYSTEM, _append_event

DEN = 36  # dénominateur canonique commun


def recovery_regime(activity_type: str) -> str:
    """Régime de récupération de blessure pour une activité active.

    `sleep` et `rest` accélèrent la récupération ; toute autre activité (et
    l'absence d'activité) utilise le régime passif.
    """
    if activity_type == "sleep":
        return "sleep"
    if activity_type == "rest":
        return "rest"
    return "passive"


# Fin conditionnelle du sommeil (calibration provisoire).
SLEEP_REPOS_TARGET = 98000
SLEEP_ENERGIE_TARGET = 95000
SLEEP_MAX_SECONDS = 28800


class ActivityError(RuntimeError):
    """Erreur d'activité (lieu non autorisé, trajet impossible, activité inexistante…)."""


def _add_seconds(iso: str, seconds: int) -> str:
    return to_iso(parse_iso(iso) + timedelta(seconds=seconds))


def _seconds_to_target(value: int, remainder: int, target: int, rate: int) -> int:
    """Plus petit dt ≥ 0 (secondes) tel que value + floor((rem + rate*dt)/36) >= target."""
    if value >= target:
        return 0
    manque = target - value
    num = manque * DEN - remainder
    if num <= 0:
        return 0
    return (num + rate - 1) // rate  # ceil


class ActivityEngine:
    """Moteur des activités et de leurs effets sur les besoins."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _world(self) -> "WorldEngine":
        from .world import WorldEngine  # évite un cycle au niveau module

        return WorldEngine(self._conn, clock=self._clock)

    def _location_id(self, world_id: int, key: str) -> int:
        row = self._conn.execute(
            "SELECT id FROM location WHERE world_id = ? AND key = ?", (world_id, key)
        ).fetchone()
        if row is None:
            raise ActivityError(f"lieu inexistant : {key!r} (monde {world_id})")
        return row["id"]

    def _location_kind(self, world_id: int, key: str) -> str:
        row = self._conn.execute(
            "SELECT kind FROM location WHERE world_id = ? AND key = ?", (world_id, key)
        ).fetchone()
        if row is None:
            raise ActivityError(f"lieu inexistant : {key!r}")
        return row["kind"]

    def _def(self, world_id: int, activity_type: str):
        row = self._conn.execute(
            "SELECT * FROM activity_definition WHERE world_id = ? AND activity_type = ?",
            (world_id, activity_type),
        ).fetchone()
        if row is None:
            raise ActivityError(f"activité inconnue : {activity_type!r}")
        return row

    def _rates(self, world_id: int, activity_type: str) -> dict[str, tuple[int, int]]:
        d = self._def(world_id, activity_type)
        return {
            "satiete": (d["satiete_rate"], DEN),
            "repos": (d["repos_rate"], DEN),
            "energie": (d["energie_rate"], DEN),
            "hygiene": (d["hygiene_rate"], DEN),
        }

    # --- Lieux autorisés --------------------------------------------------------

    def allowed_locations(self, world_id: int, activity_type: str) -> set[str]:
        """Clés des lieux autorisés (résolution des types de lieu en clés)."""
        if activity_type == "idle":
            return set()  # lieu courant, géré par le moteur
        rows = self._conn.execute(
            "SELECT location_key, location_kind FROM activity_allowed_location "
            "WHERE world_id = ? AND activity_type = ?",
            (world_id, activity_type),
        ).fetchall()
        result: set[str] = set()
        for r in rows:
            if r["location_key"]:
                result.add(r["location_key"])
            if r["location_kind"]:
                for row in self._conn.execute(
                    "SELECT key FROM location WHERE world_id = ? AND kind = ?",
                    (world_id, r["location_kind"]),
                ):
                    result.add(row["key"])
        return result

    def is_allowed(self, world_id: int, activity_type: str, location_key: str) -> bool:
        if activity_type == "idle":
            return True  # uniquement vérifié pour le lieu courant
        kind = self._location_kind(world_id, location_key)
        rows = self._conn.execute(
            "SELECT location_key, location_kind FROM activity_allowed_location "
            "WHERE world_id = ? AND activity_type = ?",
            (world_id, activity_type),
        ).fetchall()
        for r in rows:
            if r["location_key"] == location_key or (
                r["location_kind"] and kind == r["location_kind"]
            ):
                return True
        return False

    # --- Lecture pure -----------------------------------------------------------

    def activity_sheet(self, world_id: int, character_key: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT a.id, a.type, a.started_at, a.planned_end_at, a.status, "
            "       l.key AS location_key "
            "FROM activity a "
            "JOIN character ch ON ch.world_id = a.world_id AND ch.id = a.character_id "
            "JOIN location l ON l.world_id = a.world_id AND l.id = a.location_id "
            "WHERE a.world_id = ? AND ch.key = ? AND a.status = 'active' "
            "ORDER BY a.id DESC LIMIT 1",
            (world_id, character_key),
        ).fetchone()
        return dict(row) if row else None

    # --- Démarrage atomique -----------------------------------------------------

    def _sleep_planned_end(
        self, c: sqlite3.Connection, world_id: int, character_key: str, start_at: str
    ) -> str:
        d = self._def(world_id, "sleep")
        rows = {
            r["need_key"]: r
            for r in c.execute(
                "SELECT ns.need_key, ns.value_milli, ns.rate_remainder "
                "FROM need_state ns JOIN character ch ON ch.id = ns.character_id "
                "WHERE ns.world_id = ? AND ch.key = ?",
                (world_id, character_key),
            )
        }
        t_repos = _seconds_to_target(
            rows["repos"]["value_milli"], rows["repos"]["rate_remainder"],
            SLEEP_REPOS_TARGET, d["repos_rate"],
        )
        t_energie = _seconds_to_target(
            rows["energie"]["value_milli"], rows["energie"]["rate_remainder"],
            SLEEP_ENERGIE_TARGET, d["energie_rate"],
        )
        necessary = max(t_repos, t_energie)
        duration = min(necessary, SLEEP_MAX_SECONDS)
        return _add_seconds(start_at, duration)

    def _path(self, world_id: int, from_key: str, to_key: str) -> list[str]:
        path = GraphEngine(self._conn).find_path(world_id, from_key, to_key)
        if path is None:
            raise ActivityError(
                f"trajet impossible de {from_key!r} vers {to_key!r}"
            )
        return path

    def start_activity(
        self,
        world_id: int,
        character_key: str,
        activity_type: str,
        target_location_key: str,
        *,
        sim_now: str | None = None,
        duration_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Démarre une activité de façon **atomique** (une seule transaction).

        Comporte : validation de la destination (explicite, autorisée et
        existante), planification du trajet, déplacements pièce par pièce,
        matérialisation des besoins à l'heure de début, calcul de
        `planned_end_at` (fixe ou formule de sommeil), création de l'activité et
        événement `activity_started`. Si une étape échoue, rollback total (le
        personnage revient à sa position initiale, aucun événement partiel).
        """
        if self._world().get_world(world_id)["status"] == "paused":
            raise ActivityError("monde en pause : aucune activité ne peut démarrer")

        ce = CharacterEngine(self._conn, clock=self._clock)
        current_row = ce._conn.execute(
            "SELECT l.key AS cur FROM character ch "
            "JOIN location l ON l.id = ch.current_location_id "
            "WHERE ch.world_id = ? AND ch.key = ?",
            (world_id, character_key),
        ).fetchone()
        if current_row is None:
            raise ActivityError(f"personnage introuvable : {character_key!r}")
        cur_key = current_row["cur"]

        if activity_type == "idle":
            if target_location_key != cur_key:
                raise ActivityError("idle exige le lieu courant")
            if duration_seconds is None:
                raise ActivityError("idle exige une durée explicite")
            if not 1 <= duration_seconds <= MAX_IDLE:
                raise ActivityError(
                    f"durée idle invalide (doit être 1..{MAX_IDLE})"
                )
        else:
            self._def(world_id, activity_type)  # activité connue
            if duration_seconds is not None:
                raise ActivityError(
                    f"durée libre refusée pour {activity_type!r} (définie ou conditionnelle)"
                )
            self._location_id(world_id, target_location_key)  # existante
            if not self.is_allowed(world_id, activity_type, target_location_key):
                raise ActivityError(
                    f"lieu {target_location_key!r} non autorisé pour {activity_type!r}"
                )

        if activity_type == "sleep":
            v = self._need(character_key, "repos", "value_milli")
            e = self._need(character_key, "energie", "value_milli")
            if v >= SLEEP_REPOS_TARGET and e >= SLEEP_ENERGIE_TARGET:
                raise ActivityError("sommeil inutile : repos et énergie déjà satisfaits")

        path = self._path(world_id, cur_key, target_location_key)

        with transaction(self._conn) as c:
            # 1) heure simulée de début (explicite ou dérivée de l'horloge)
            start_at = sim_now if sim_now is not None else self._world().read_canonical_time(world_id)
            # 1b) matérialisation de la blessure (ancien régime passif) jusqu'au début
            ie = InjuryEngine(self._conn, clock=self._clock)
            ie._materialize_injury_sim(world_id, character_key, start_at, "passive", _conn=c)
            # 1c) prévalidation du coût total de blessure avant le premier déplacement
            edge_count = len(path) - 1
            row = ie.active_injury_row(world_id, character_key)
            if row is not None and level(row["severity_milli"]) == "moderate" and edge_count > 0:
                total = MOVEMENT_SURCHARGE_MILLI * edge_count
                ne = NeedsEngine(self._conn, clock=self._clock)
                e_val, _ = ne.derive_need(world_id, character_key, "energie", start_at)
                if e_val < total:
                    raise ActivityError(
                        f"énergie insuffisante pour le trajet complet "
                        f"(blessure modérée, {character_key!r})"
                    )
            # 2) déplacements pièce par pièce, chacun tracé (même transaction)
            for step in path[1:]:
                ce._move(c, world_id, character_key, step, sim_now=start_at)
            # 3) matérialisation passive à l'heure de début
            NeedsEngine(self._conn, clock=self._clock).materialize_character_needs(
                world_id, character_key, start_at, "activity_start", _conn=c
            )
            # 4) fin planifiée
            if activity_type == "sleep":
                planned_end = self._sleep_planned_end(c, world_id, character_key, start_at)
            elif activity_type == "idle":
                planned_end = _add_seconds(start_at, duration_seconds)
            else:
                d = self._def(world_id, activity_type)
                planned_end = _add_seconds(start_at, d["min_duration_seconds"])
            # 5) création
            loc_id = self._location_id(world_id, target_location_key)
            now = self._clock.now_iso()
            c.execute(
                "INSERT INTO activity "
                "(public_id, world_id, character_id, type, location_id, started_at, "
                " planned_end_at, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)",
                (
                    new_uuid(), world_id,
                    self._character_id(world_id, character_key),
                    activity_type, loc_id, start_at, planned_end, now, now,
                ),
            )
            # 6) événement
            _append_event(
                c, world_id, SOURCE_ENGINE, "activity_started",
                {
                    "character": character_key,
                    "activity": activity_type,
                    "location": target_location_key,
                    "planned_end_at": planned_end,
                },
                occurred_at=start_at, recorded_at=now,
            )
            # 7) avancement de l'horloge canonique à l'instant de début
            self._world()._advance_clock(world_id, start_at, c)
        return self.activity_sheet(world_id, character_key)

    def _character_id(self, world_id: int, character_key: str) -> int:
        row = self._conn.execute(
            "SELECT id FROM character WHERE world_id = ? AND key = ?",
            (world_id, character_key),
        ).fetchone()
        if row is None:
            raise ActivityError(f"personnage introuvable : {character_key!r}")
        return row["id"]

    def _need(self, character_key: str, need_key: str, field: str) -> int:
        row = self._conn.execute(
            "SELECT ns.value_milli, ns.rate_remainder FROM need_state ns "
            "JOIN character ch ON ch.id = ns.character_id "
            "WHERE ch.key = ? AND ns.need_key = ?",
            (character_key, need_key),
        ).fetchone()
        if row is None:
            raise ActivityError("besoin introuvable")
        return row[field]

    # --- Progression / clôture -----------------------------------------------

    def advance_to(self, world_id: int, character_key: str, at_time: str) -> dict[str, Any] | None:
        """Fait progresser la simulation jusqu'à `at_time` (temps simulé).

        Si l'activité active a déjà atteint sa fin (`planned_end_at <= at_time`),
        elle est **clôturée à son heure canonique de fin** (régime d'activité),
        puis l'intervalle suivant est dérivé en régime passif. Retourne la fiche
        d'activité (ou None si aucune activité active).
        """
        with transaction(self._conn) as c:
            active = self._active_row(c, world_id, character_key)
            if active is None:
                return None
            ne = NeedsEngine(self._conn, clock=self._clock)
            ie = InjuryEngine(self._conn, clock=self._clock)
            now = self._clock.now_iso()
            if parse_iso(active["planned_end_at"]) <= parse_iso(at_time):
                rates = self._rates(world_id, active["type"])
                ne.materialize_with_rates(
                    world_id, character_key, active["planned_end_at"],
                    "activity_end", rates, _conn=c, activity_type=active["type"],
                )
                ie._materialize_injury_sim(
                    world_id, character_key, active["planned_end_at"],
                    recovery_regime(active["type"]), _conn=c,
                )
                c.execute(
                    "UPDATE activity SET status = 'completed', updated_at = ? WHERE id = ?",
                    (now, active["id"]),
                )
                _append_event(
                    c, world_id, SOURCE_ENGINE, "activity_completed",
                    {"character": character_key, "activity": active["type"],
                     "ended_at": active["planned_end_at"]},
                    occurred_at=active["planned_end_at"], recorded_at=now,
                )
                # intervalle suivant en régime passif jusqu'à at_time
                ne.materialize_character_needs(
                    world_id, character_key, at_time, "passive", _conn=c
                )
                ie._materialize_injury_sim(
                    world_id, character_key, at_time, "passive", _conn=c,
                )
            else:
                rates = self._rates(world_id, active["type"])
                ne.materialize_with_rates(
                    world_id, character_key, at_time, "activity_ongoing", rates,
                    _conn=c, activity_type=active["type"],
                )
                ie._materialize_injury_sim(
                    world_id, character_key, at_time,
                    recovery_regime(active["type"]), _conn=c,
                )
            # avancement de l'horloge canonique à l'instant atteint
            self._world()._advance_clock(world_id, at_time, c)
        return self.activity_sheet(world_id, character_key)

    def abort_activity(self, world_id: int, character_key: str) -> dict[str, Any] | None:
        """Abandon explicite de l'activité active (matérialisation + aborted)."""
        with transaction(self._conn) as c:
            active = self._active_row(c, world_id, character_key)
            if active is None:
                raise ActivityError("aucune activité active à abandonner")
            canonical = self._world().read_canonical_time(world_id)
            now = self._clock.now_iso()
            rates = self._rates(world_id, active["type"])
            NeedsEngine(self._conn, clock=self._clock).materialize_with_rates(
                world_id, character_key, canonical, "activity_abort", rates,
                _conn=c, activity_type=active["type"],
            )
            InjuryEngine(self._conn, clock=self._clock)._materialize_injury_sim(
                world_id, character_key, canonical,
                recovery_regime(active["type"]), _conn=c,
            )
            c.execute(
                "UPDATE activity SET status = 'aborted', updated_at = ? WHERE id = ?",
                (now, active["id"]),
            )
            _append_event(
                c, world_id, SOURCE_ENGINE, "activity_aborted",
                {"character": character_key, "activity": active["type"]},
                occurred_at=canonical, recorded_at=now,
            )
            # avancement de l'horloge canonique à l'instant d'abandon
            self._world()._advance_clock(world_id, canonical, c)
        return self.activity_sheet(world_id, character_key)

    def _active_row(self, c: sqlite3.Connection, world_id: int, character_key: str):
        return c.execute(
            "SELECT a.id, a.type, a.planned_end_at FROM activity a "
            "JOIN character ch ON ch.world_id = a.world_id AND ch.id = a.character_id "
            "WHERE a.world_id = ? AND ch.key = ? AND a.status = 'active' "
            "ORDER BY a.id DESC LIMIT 1",
            (world_id, character_key),
        ).fetchone()


def upgrade_dev_activities(
    conn: sqlite3.Connection, world_id: int, clock: Clock | None = None
) -> dict[str, int]:
    """Mise à niveau non destructive du catalogue d'activités (Sous-lot 3.2B)."""
    from .util import now_utc  # noqa: F401

    created: int = 0
    created_rules: int = 0
    with transaction(conn) as c:
        existing = {
            r["activity_type"]
            for r in c.execute(
                "SELECT activity_type FROM activity_definition WHERE world_id = ?",
                (world_id,),
            )
        }
        for typ, min_d, max_d, s, rp, e, h in SEED_ACTIVITIES:
            if typ in existing:
                continue
            c.execute(
                "INSERT INTO activity_definition "
                "(public_id, world_id, activity_type, min_duration_seconds, "
                " max_duration_seconds, satiete_rate, repos_rate, energie_rate, "
                " hygiene_rate, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (new_uuid(), world_id, typ, min_d, max_d, s, rp, e, h, now_utc()),
            )
            created += 1
        rules = c.execute(
            "SELECT activity_type, location_key, location_kind FROM activity_allowed_location "
            "WHERE world_id = ?",
            (world_id,),
        ).fetchall()
        rule_set = {(r["activity_type"], r["location_key"], r["location_kind"]) for r in rules}
        for typ, key, kind in SEED_ACTIVITY_ALLOWED:
            if (typ, key, kind) in rule_set:
                continue
            c.execute(
                "INSERT INTO activity_allowed_location "
                "(public_id, world_id, activity_type, location_key, location_kind, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (new_uuid(), world_id, typ, key, kind, now_utc()),
            )
            created_rules += 1
    return {"definitions_created": created, "rules_created": created_rules}
