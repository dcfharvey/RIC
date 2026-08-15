"""Activités et effets (Sous-lot 3.2B).

Une activité applique un **régime de taux net** (en unités /36 par seconde) à
chacun des quatre besoins pendant [started_at, planned_end_at]. Le calcul reste
en arithmétique entière (dénominateur canonique 36, reste conservé).

`ActivityEngine` exploite les API internes (qui acceptent une connexion dans une
transaction déjà ouverte) afin que chaque transition soit **atomique** sans
transaction imbriquée : déplacements pièce par pièce + matérialisation +
création/clôture + événements dans une seule transaction. L'autorité canonique
unique est préservée (écritures via `db.transaction` + `world.append_event`).
"""

from __future__ import annotations

import json
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
from .registry import KEY_RE as _KEY_RE
from .util import Clock, new_uuid, parse_iso, to_iso
from .world import SOURCE_ENGINE, SOURCE_SYSTEM, append_event as _append_event

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
        if activity_type == "sleep":
            # Le sommeil ne dépend d'aucun mobilier ni type de pièce. La
            # validation de l'accessibilité canonique reste assurée par le
            # trajet atomique de ``start_activity``.
            self._location_id(world_id, location_key)
            return True
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

    def resolve_path(self, world_id: int, from_key: str, to_key: str) -> list[str]:
        """Retourne un trajet d'activité valide ou lève une erreur métier."""
        path = GraphEngine(self._conn).find_path(world_id, from_key, to_key)
        if path is None:
            raise ActivityError(
                f"trajet impossible de {from_key!r} vers {to_key!r}"
            )
        return path

    _path = resolve_path

    _ACTIVE_NEED_KEYS = frozenset({"satiete", "hygiene"})

    def _physiology_active(self, world_id: int) -> bool:
        from .sleep_physiology import SleepPhysiologyFoundationService

        return SleepPhysiologyFoundationService(
            self._conn, clock=self._clock
        ).system_status(world_id) == "active"

    def _materialize_active_needs(
        self, c: sqlite3.Connection, world_id: int, character_key: str, target_at: str,
        reason: str, *, activity_type: str | None = None,
    ) -> None:
        rates = None if activity_type is None else self._rates(world_id, activity_type)
        NeedsEngine(self._conn, clock=self._clock).materialize_selected_needs(
            world_id, character_key, target_at, reason, self._ACTIVE_NEED_KEYS,
            rates=rates, _conn=c, activity_type=activity_type,
        )

    def _active_sleep_plan(self, world_id: int, start_at: str) -> tuple[int, str, str]:
        from .sleep_termination import SleepTerminationFoundationService

        service = SleepTerminationFoundationService(self._conn, clock=self._clock)
        policy = service.world_policy(world_id)
        assignment = self._conn.execute(
            "SELECT policy_id FROM world_sleep_termination_policy_assignment WHERE world_id=?",
            (world_id,),
        ).fetchone()
        if assignment is None:
            raise ActivityError("politique de terminaison du sommeil absente")
        next_at = _add_seconds(start_at, policy.checkpoint_interval_seconds)
        hard_cap = _add_seconds(start_at, policy.hard_cap_seconds)
        return int(assignment["policy_id"]), next_at, hard_cap

    def _start_activity_active(
        self, world_id: int, character_key: str, activity_type: str,
        target_location_key: str, *, sim_now: str | None = None,
        duration_seconds: int | None = None,
        action_provenance: dict[str, str] | None = None,
        _reanchor_clock: bool = True,
    ) -> dict[str, Any]:
        """WO88B : démarrage atomique sans lecture/écriture repos-énergie."""
        if self._world().get_world(world_id)["status"] == "paused":
            raise ActivityError("monde en pause : aucune activité ne peut démarrer")
        ce = CharacterEngine(self._conn, clock=self._clock)
        current_row = self._conn.execute(
            "SELECT l.key AS cur FROM character ch JOIN location l ON l.id=ch.current_location_id "
            "WHERE ch.world_id=? AND ch.key=?", (world_id, character_key),
        ).fetchone()
        if current_row is None:
            raise ActivityError(f"personnage introuvable : {character_key!r}")
        cur_key = current_row["cur"]
        if activity_type == "idle":
            if target_location_key != cur_key:
                raise ActivityError("idle exige le lieu courant")
            if duration_seconds is None or not 1 <= duration_seconds <= MAX_IDLE:
                raise ActivityError(f"durée idle invalide (doit être 1..{MAX_IDLE})")
        else:
            self._def(world_id, activity_type)
            if duration_seconds is not None:
                raise ActivityError(
                    f"durée libre refusée pour {activity_type!r} (définie ou conditionnelle)"
                )
            self._location_id(world_id, target_location_key)
            if not self.is_allowed(world_id, activity_type, target_location_key):
                raise ActivityError(
                    f"lieu {target_location_key!r} non autorisé pour {activity_type!r}"
                )
        path = self._path(world_id, cur_key, target_location_key)
        with transaction(self._conn) as c:
            start_at = sim_now if sim_now is not None else self._world().read_canonical_time(world_id)
            from .sleep_physiology import SleepPhysiologyError, SleepPhysiologyService
            physiology = SleepPhysiologyService(self._conn, clock=self._clock)
            try:
                physiology.materialize_owner_backed(world_id, character_key, start_at)
                state = physiology.read_state(world_id, character_key)
                edge_count = len(path) - 1
                traversal = physiology.evaluate_traversal_capacity_owner_backed(
                    world_id, character_key, edge_count=max(1, edge_count)
                ) if edge_count else None
                if traversal is not None and not traversal.feasible:
                    raise ActivityError("capacité physique insuffisante pour le trajet complet")
                after_path = state.regulation.physical_capacity_milli - (
                    0 if traversal is None or traversal.traversal_cost_milli is None
                    else traversal.traversal_cost_milli
                )
                activity_eval = physiology.evaluate_activity_capacity_owner_backed(
                    world_id, character_key, activity_type, capacity_milli=after_path
                )
                if not activity_eval.feasible:
                    raise ActivityError("capacité physique insuffisante pour l'activité")
            except SleepPhysiologyError as exc:
                raise ActivityError(str(exc)) from exc
            InjuryEngine(self._conn, clock=self._clock).materialize_injury_sim(
                world_id, character_key, start_at, "passive", _conn=c
            )
            for step in path[1:]:
                ce.move_in_transaction(c, world_id, character_key, step, sim_now=start_at)
            self._materialize_active_needs(
                c, world_id, character_key, start_at, "activity_start"
            )
            sleep_plan = None
            if activity_type == "sleep":
                sleep_plan = self._active_sleep_plan(world_id, start_at)
                planned_end = sleep_plan[2]
            elif activity_type == "idle":
                planned_end = _add_seconds(start_at, duration_seconds)
            else:
                planned_end = _add_seconds(start_at, self._def(world_id, activity_type)["min_duration_seconds"])
            loc_id = self._location_id(world_id, target_location_key)
            now = self._clock.now_iso()
            c.execute(
                "INSERT INTO activity (public_id,world_id,character_id,type,location_id,started_at,"
                "planned_end_at,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,'active',?,?)",
                (new_uuid(), world_id, self._character_id(world_id, character_key), activity_type,
                 loc_id, start_at, planned_end, now, now),
            )
            payload = {
                "character": character_key, "activity": activity_type,
                "location": target_location_key, "planned_end_at": planned_end,
            }
            if action_provenance is not None:
                if set(action_provenance) != {"proposal_id", "origin"} or not all(
                    isinstance(value, str) for value in action_provenance.values()
                ):
                    raise ActivityError("provenance d'action invalide")
                payload["action_provenance"] = dict(action_provenance)
            _append_event(
                c, world_id, SOURCE_ENGINE, "activity_started", payload,
                occurred_at=start_at, recorded_at=now,
            )
            if sleep_plan is not None:
                self.attach_sleep_checkpoint(
                    world_id, character_key, policy_id=sleep_plan[0],
                    next_reassessment_at=sleep_plan[1], hard_cap_at=sleep_plan[2],
                )
            if _reanchor_clock:
                self._world().advance_clock_in_transaction(world_id, start_at, c)
        return self.activity_sheet(world_id, character_key) or {}

    def start_activity(
        self,
        world_id: int,
        character_key: str,
        activity_type: str,
        target_location_key: str,
        *,
        sim_now: str | None = None,
        duration_seconds: int | None = None,
        action_provenance: dict[str, str] | None = None,
        _reanchor_clock: bool = True,
    ) -> dict[str, Any]:
        """Démarre une activité de façon **atomique** (une seule transaction).

        Comporte : validation de la destination (explicite, autorisée et
        existante), planification du trajet, déplacements pièce par pièce,
        matérialisation des besoins à l'heure de début, calcul de
        `planned_end_at` (fixe ou formule de sommeil), création de l'activité et
        événement `activity_started`. Si une étape échoue, rollback total (le
        personnage revient à sa position initiale, aucun événement partiel).
        """
        if self._physiology_active(world_id):
            return self._start_activity_active(
                world_id, character_key, activity_type, target_location_key,
                sim_now=sim_now, duration_seconds=duration_seconds,
                action_provenance=action_provenance, _reanchor_clock=_reanchor_clock,
            )
        if self._world().get_world(world_id)["status"] == "paused":
            raise ActivityError("monde en pause : aucune activité ne peut démarrer")

        ce = CharacterEngine(self._conn, clock=self._clock)
        current_row = self._conn.execute(
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
            ie.materialize_injury_sim(world_id, character_key, start_at, "passive", _conn=c)
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
                ce.move_in_transaction(c, world_id, character_key, step, sim_now=start_at)
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
            payload = {
                "character": character_key,
                "activity": activity_type,
                "location": target_location_key,
                "planned_end_at": planned_end,
            }
            if action_provenance is not None:
                if set(action_provenance) != {"proposal_id", "origin"} or not all(
                    isinstance(value, str) for value in action_provenance.values()
                ):
                    raise ActivityError("provenance d'action invalide")
                payload["action_provenance"] = dict(action_provenance)
            _append_event(
                c, world_id, SOURCE_ENGINE, "activity_started",
                payload,
                occurred_at=start_at, recorded_at=now,
            )
            # 7) avancement de l'horloge canonique à l'instant de début
            if _reanchor_clock:
                self._world().advance_clock_in_transaction(world_id, start_at, c)
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

    def advance_to(
        self, world_id: int, character_key: str, at_time: str, *,
        _reanchor_clock: bool = True,
    ) -> dict[str, Any] | None:
        """Fait progresser la simulation jusqu'à `at_time` (temps simulé).

        Si l'activité active a déjà atteint sa fin (`planned_end_at <= at_time`),
        elle est **clôturée à son heure canonique de fin** (régime d'activité),
        puis l'intervalle suivant est dérivé en régime passif. Retourne la fiche
        d'activité (ou None si aucune activité active).
        """
        if self._physiology_active(world_id):
            return self._advance_to_active(
                world_id, character_key, at_time, _reanchor_clock=_reanchor_clock
            )
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
                ie.materialize_injury_sim(
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
                ie.materialize_injury_sim(
                    world_id, character_key, at_time, "passive", _conn=c,
                )
            else:
                rates = self._rates(world_id, active["type"])
                ne.materialize_with_rates(
                    world_id, character_key, at_time, "activity_ongoing", rates,
                    _conn=c, activity_type=active["type"],
                )
                ie.materialize_injury_sim(
                    world_id, character_key, at_time,
                    recovery_regime(active["type"]), _conn=c,
                )
            # avancement de l'horloge canonique à l'instant atteint
            if _reanchor_clock:
                self._world().advance_clock_in_transaction(world_id, at_time, c)
        return self.activity_sheet(world_id, character_key)

    def _advance_to_active(
        self, world_id: int, character_key: str, at_time: str, *,
        _reanchor_clock: bool = True,
    ) -> dict[str, Any] | None:
        from .sleep_physiology import SleepPhysiologyService

        with transaction(self._conn) as c:
            active = self._active_row(c, world_id, character_key)
            if active is None:
                return None
            physiology = SleepPhysiologyService(self._conn, clock=self._clock)
            ie = InjuryEngine(self._conn, clock=self._clock)
            now = self._clock.now_iso()
            if active["type"] == "sleep":
                # ``planned_end_at`` est un hard cap protecteur, jamais une
                # autorisation implicite de réveil. Le scheduler WO88D gère les checkpoints.
                target = min(parse_iso(at_time), parse_iso(active["planned_end_at"]))
                target_iso = to_iso(target)
                physiology.materialize_owner_backed(world_id, character_key, target_iso)
                self._materialize_active_needs(
                    c, world_id, character_key, target_iso, "activity_ongoing",
                    activity_type="sleep",
                )
                ie.materialize_injury_sim(
                    world_id, character_key, target_iso, "sleep", _conn=c
                )
                if _reanchor_clock:
                    self._world().advance_clock_in_transaction(world_id, target_iso, c)
                return self.activity_sheet(world_id, character_key)
            if parse_iso(active["planned_end_at"]) <= parse_iso(at_time):
                boundary = active["planned_end_at"]
                physiology.materialize_owner_backed(world_id, character_key, boundary)
                self._materialize_active_needs(
                    c, world_id, character_key, boundary, "activity_end",
                    activity_type=active["type"],
                )
                ie.materialize_injury_sim(
                    world_id, character_key, boundary, recovery_regime(active["type"]), _conn=c
                )
                c.execute("UPDATE activity SET status='completed',updated_at=? WHERE id=?", (now, active["id"]))
                _append_event(
                    c, world_id, SOURCE_ENGINE, "activity_completed",
                    {"character": character_key, "activity": active["type"], "ended_at": boundary},
                    occurred_at=boundary, recorded_at=now,
                )
                if _reanchor_clock:
                    self._world().advance_clock_in_transaction(world_id, boundary, c)
                if parse_iso(at_time) > parse_iso(boundary):
                    physiology.materialize_owner_backed(world_id, character_key, at_time)
                    self._materialize_active_needs(
                        c, world_id, character_key, at_time, "passive"
                    )
                    ie.materialize_injury_sim(
                        world_id, character_key, at_time, "passive", _conn=c
                    )
                    if _reanchor_clock:
                        self._world().advance_clock_in_transaction(world_id, at_time, c)
            else:
                physiology.materialize_owner_backed(world_id, character_key, at_time)
                self._materialize_active_needs(
                    c, world_id, character_key, at_time, "activity_ongoing",
                    activity_type=active["type"],
                )
                ie.materialize_injury_sim(
                    world_id, character_key, at_time, recovery_regime(active["type"]), _conn=c
                )
                if _reanchor_clock:
                    self._world().advance_clock_in_transaction(world_id, at_time, c)
        return self.activity_sheet(world_id, character_key)

    def abort_activity(
        self, world_id: int, character_key: str, *, sim_now: str | None = None,
        reason_code: str | None = None,
        _reanchor_clock: bool = True,
    ) -> dict[str, Any] | None:
        """Abandon explicite de l'activité active (matérialisation + aborted)."""
        if reason_code is not None and (not isinstance(reason_code, str) or not _KEY_RE.fullmatch(reason_code)):
            raise ActivityError("raison d'abandon invalide")
        if self._physiology_active(world_id):
            return self._abort_activity_active(
                world_id, character_key, sim_now=sim_now, reason_code=reason_code,
                _reanchor_clock=_reanchor_clock,
            )
        with transaction(self._conn) as c:
            active = self._active_row(c, world_id, character_key)
            if active is None:
                raise ActivityError("aucune activité active à abandonner")
            canonical = sim_now or self._world().read_canonical_time(world_id)
            now = self._clock.now_iso()
            rates = self._rates(world_id, active["type"])
            NeedsEngine(self._conn, clock=self._clock).materialize_with_rates(
                world_id, character_key, canonical, "activity_abort", rates,
                _conn=c, activity_type=active["type"],
            )
            InjuryEngine(self._conn, clock=self._clock).materialize_injury_sim(
                world_id, character_key, canonical,
                recovery_regime(active["type"]), _conn=c,
            )
            c.execute(
                "UPDATE activity SET status = 'aborted', updated_at = ? WHERE id = ?",
                (now, active["id"]),
            )
            payload = {"character": character_key, "activity": active["type"]}
            if reason_code is not None:
                payload["reason_code"] = reason_code
            _append_event(
                c, world_id, SOURCE_ENGINE, "activity_aborted",
                payload,
                occurred_at=canonical, recorded_at=now,
            )
            # avancement de l'horloge canonique à l'instant d'abandon
            if _reanchor_clock:
                self._world().advance_clock_in_transaction(world_id, canonical, c)
        return self.activity_sheet(world_id, character_key)

    def _abort_activity_active(
        self, world_id: int, character_key: str, *, sim_now: str | None = None,
        reason_code: str | None = None,
        _reanchor_clock: bool = True,
    ) -> dict[str, Any] | None:
        from .sleep_physiology import SleepPhysiologyService

        with transaction(self._conn) as c:
            active = self._active_row(c, world_id, character_key)
            if active is None:
                raise ActivityError("aucune activité active à abandonner")
            canonical = sim_now or self._world().read_canonical_time(world_id)
            SleepPhysiologyService(self._conn, clock=self._clock).materialize_owner_backed(
                world_id, character_key, canonical
            )
            self._materialize_active_needs(
                c, world_id, character_key, canonical, "activity_abort",
                activity_type=active["type"],
            )
            InjuryEngine(self._conn, clock=self._clock).materialize_injury_sim(
                world_id, character_key, canonical, recovery_regime(active["type"]), _conn=c
            )
            now = self._clock.now_iso()
            c.execute("UPDATE activity SET status='aborted',updated_at=? WHERE id=?", (now, active["id"]))
            payload = {"character": character_key, "activity": active["type"]}
            if reason_code is not None:
                payload["reason_code"] = reason_code
            _append_event(
                c, world_id, SOURCE_ENGINE, "activity_aborted", payload,
                occurred_at=canonical, recorded_at=now,
            )
            if _reanchor_clock:
                self._world().advance_clock_in_transaction(world_id, canonical, c)
        return self.activity_sheet(world_id, character_key)

    # --- Frontieres de sommeil synthetiques -----------------------------------

    def attach_sleep_checkpoint(
        self, world_id: int, character_key: str, *, policy_id: int,
        next_reassessment_at: str, hard_cap_at: str,
        previous_band: str = "continue_sleep",
    ) -> dict[str, Any]:
        """Attache un plan de terminaison a un sommeil actif de banc.

        Ce plan appartient au cycle canonique de l'activite. Il ne planifie
        aucun runtime et n'emet aucun evenement : cette API ne sert qu'au
        raccord synthetique avant cutover.
        """
        if isinstance(policy_id, bool) or not isinstance(policy_id, int) or policy_id < 1:
            raise ActivityError("politique de checkpoint invalide")
        if previous_band not in {"continue_sleep", "wake_admissible"}:
            raise ActivityError("bande de checkpoint invalide")
        try:
            next_at = to_iso(parse_iso(next_reassessment_at))
            hard_at = to_iso(parse_iso(hard_cap_at))
        except (TypeError, ValueError) as exc:
            raise ActivityError("frontiere de checkpoint invalide") from exc
        if parse_iso(next_at) > parse_iso(hard_at):
            raise ActivityError("checkpoint apres hard cap")
        with transaction(self._conn) as c:
            active = self._active_row(c, world_id, character_key)
            if active is None or active["type"] != "sleep":
                raise ActivityError("checkpoint exige un sommeil actif")
            if parse_iso(next_at) < parse_iso(active["started_at"]):
                raise ActivityError("checkpoint avant le sommeil")
            now = self._clock.now_iso()
            try:
                c.execute(
                    "INSERT INTO activity_sleep_checkpoint "
                    "(public_id,world_id,character_id,activity_id,policy_id,next_reassessment_at,previous_band,hard_cap_at,created_at,updated_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (new_uuid(), world_id, self._character_id(world_id, character_key), active["id"],
                     policy_id, next_at, previous_band, hard_at, now, now),
                )
            except sqlite3.IntegrityError as exc:
                raise ActivityError("checkpoint de sommeil deja attache") from exc
        return self.sleep_checkpoint(world_id, character_key) or {}

    def sleep_checkpoint(self, world_id: int, character_key: str) -> dict[str, Any] | None:
        """Lit le checkpoint de sommeil sans faire progresser le temps."""
        row = self._conn.execute(
            "SELECT cp.id,cp.activity_id,cp.policy_id,cp.next_reassessment_at,cp.previous_band,"
            "cp.hard_cap_at,cp.hard_cap_reported_at,a.started_at,a.status "
            "FROM activity_sleep_checkpoint cp JOIN activity a ON a.id=cp.activity_id "
            "JOIN character ch ON ch.id=cp.character_id "
            "WHERE cp.world_id=? AND ch.key=? ORDER BY cp.id DESC LIMIT 1",
            (world_id, character_key),
        ).fetchone()
        return None if row is None else dict(row)

    def advance_sleep_checkpoint(
        self, world_id: int, character_key: str, *, at_time: str,
        next_reassessment_at: str, previous_band: str,
    ) -> dict[str, Any]:
        """Avance uniquement le plan mutable d'un sommeil toujours actif."""
        if previous_band not in {"continue_sleep", "wake_admissible"}:
            raise ActivityError("bande de checkpoint invalide")
        try:
            at = to_iso(parse_iso(at_time))
            next_at = to_iso(parse_iso(next_reassessment_at))
        except (TypeError, ValueError) as exc:
            raise ActivityError("frontiere de checkpoint invalide") from exc
        if parse_iso(next_at) <= parse_iso(at):
            raise ActivityError("prochaine reevaluation non progressive")
        with transaction(self._conn) as c:
            checkpoint = self.sleep_checkpoint(world_id, character_key)
            if checkpoint is None or checkpoint["status"] != "active":
                raise ActivityError("checkpoint de sommeil actif absent")
            if parse_iso(checkpoint["next_reassessment_at"]) > parse_iso(at):
                raise ActivityError("checkpoint pas encore echu")
            if parse_iso(next_at) > parse_iso(checkpoint["hard_cap_at"]):
                raise ActivityError("reevaluation apres hard cap")
            c.execute(
                "UPDATE activity_sleep_checkpoint SET next_reassessment_at=?,previous_band=?,updated_at=? WHERE id=?",
                (next_at, previous_band, self._clock.now_iso(), checkpoint["id"]),
            )
        return self.sleep_checkpoint(world_id, character_key) or {}

    def report_sleep_hard_cap(self, world_id: int, character_key: str, *, at_time: str) -> bool:
        """Enregistre une alerte technique unique; elle ne reveille jamais."""
        try:
            at = to_iso(parse_iso(at_time))
        except (TypeError, ValueError) as exc:
            raise ActivityError("instant de hard cap invalide") from exc
        with transaction(self._conn) as c:
            checkpoint = self.sleep_checkpoint(world_id, character_key)
            if checkpoint is None or checkpoint["status"] != "active":
                raise ActivityError("checkpoint de sommeil actif absent")
            if parse_iso(at) < parse_iso(checkpoint["hard_cap_at"]):
                raise ActivityError("hard cap non atteint")
            if checkpoint["hard_cap_reported_at"] is not None:
                return False
            now = self._clock.now_iso()
            c.execute(
                "UPDATE activity_sleep_checkpoint SET hard_cap_reported_at=?,updated_at=? WHERE id=?",
                (at, now, checkpoint["id"]),
            )
            c.execute(
                "INSERT INTO sleep_termination_audit "
                "(public_id,world_id,character_id,activity_id,checkpoint_id,operation,details_json,recorded_at) "
                "VALUES (?,?,?,?,?,'hard_cap_protective',?,?)",
                (new_uuid(), world_id, self._character_id(world_id, character_key),
                 checkpoint["activity_id"], checkpoint["id"],
                 json.dumps({"at_time": at}, sort_keys=True, separators=(",", ":")), now),
            )
        return True

    def complete_sleep_from_checkpoint(
        self, world_id: int, character_key: str, *, at_time: str,
        _reanchor_clock: bool = True,
    ) -> dict[str, Any] | None:
        """Termine un sommeil a une frontiere deja validee par son checkpoint."""
        try:
            at = to_iso(parse_iso(at_time))
        except (TypeError, ValueError) as exc:
            raise ActivityError("instant de terminaison invalide") from exc
        with transaction(self._conn) as c:
            checkpoint = self.sleep_checkpoint(world_id, character_key)
            active = self._active_row(c, world_id, character_key)
            if checkpoint is None or checkpoint["status"] != "active" or active is None \
                    or active["id"] != checkpoint["activity_id"] or active["type"] != "sleep":
                raise ActivityError("sommeil de checkpoint absent")
            if parse_iso(at) < parse_iso(active["started_at"]):
                raise ActivityError("terminaison avant sommeil")
            now = self._clock.now_iso()
            rates = self._rates(world_id, "sleep")
            if self._physiology_active(world_id):
                from .sleep_physiology import SleepPhysiologyService
                SleepPhysiologyService(self._conn, clock=self._clock).materialize_owner_backed(
                    world_id, character_key, at
                )
                self._materialize_active_needs(
                    c, world_id, character_key, at, "sleep_checkpoint_complete",
                    activity_type="sleep",
                )
            else:
                NeedsEngine(self._conn, clock=self._clock).materialize_with_rates(
                    world_id, character_key, at, "sleep_checkpoint_complete", rates,
                    _conn=c, activity_type="sleep",
                )
            InjuryEngine(self._conn, clock=self._clock).materialize_injury_sim(
                world_id, character_key, at, "sleep", _conn=c,
            )
            c.execute("UPDATE activity SET status='completed',updated_at=? WHERE id=?", (now, active["id"]))
            _append_event(
                c, world_id, SOURCE_ENGINE, "activity_completed",
                {"character": character_key, "activity": "sleep", "ended_at": at,
                 "reason_code": "sleep_checkpoint"},
                occurred_at=at, recorded_at=now,
            )
            if _reanchor_clock:
                self._world().advance_clock_in_transaction(world_id, at, c)
        return self.activity_sheet(world_id, character_key)

    def _active_row(self, c: sqlite3.Connection, world_id: int, character_key: str):
        return c.execute(
            "SELECT a.id, a.type, a.started_at, a.planned_end_at FROM activity a "
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
        has_metadata = any(
            row["name"] == "requires_sustained_wakefulness"
            for row in c.execute("PRAGMA table_info(activity_definition)")
        )
        for typ, min_d, max_d, s, rp, e, h, sustained_wakefulness in SEED_ACTIVITIES:
            if typ in existing:
                continue
            if has_metadata:
                c.execute(
                    "INSERT INTO activity_definition "
                    "(public_id, world_id, activity_type, min_duration_seconds, "
                    " max_duration_seconds, satiete_rate, repos_rate, energie_rate, "
                    " hygiene_rate, requires_sustained_wakefulness, physical_load_class, "
                    " created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        new_uuid(), world_id, typ, min_d, max_d, s, rp, e, h,
                        int(sustained_wakefulness), None, now_utc(),
                    ),
                )
            else:
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
