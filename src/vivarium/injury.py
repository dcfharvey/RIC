"""Blessures de mobilité — état, causalité et récupération (Sous-lot 3.3B1).

Modèle minimal, entièrement déterministe et récupérable : une blessure générique
`mobility`, entière /36 (aucune REAL), ancrée temporellement avec un reste
rationnel persistant, indépendante du découpage et du changement de régime.

Règles canoniques de 3.3B1 (effets de mobilité reportés à 3.3B2) :
- une cause canonique (`scripted_accident`) ne peut produire qu'une blessure ;
- `started_at = cause.occurred_at` ; `recovery_anchor_at = cause.occurred_at` ;
  `injury_occurred.occurred_at = cause.occurred_at`, avec `cause.seq < seq(accident)` ;
- `injure_character` restreint aux causes dont `occurred_at` est **égal** à
  l'heure canonique courante (une cause ancienne est refusée clairement) ;
- une blessure guérie est **terminale** (immuable) ; une nouvelle blessure est
  toujours une nouvelle ligne ;
- la récupération se matérialise par un régime **typé** (`passive`/`rest`/`sleep`),
  traduit en taux constants ; toute matérialisation réelle écrit l'état + un
  événement d'audit `injury_materialized` ; la guérison émet `injury_healed`.

`InjuryEngine` encapsule la logique mais n'est pas une seconde autorité canonique :
toutes les écritures passent par `db.transaction` + `world._append_event`.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import timedelta
from typing import Any

from .db import transaction
from .util import Clock, new_uuid, parse_iso, to_iso
from .world import SOURCE_ENGINE, SOURCE_OWNER, _append_event

SEVERITY_MAX = 100000
DEN = 36  # dénominateur canonique commun (même que besoins/activités)

# Régimes de récupération typés → numérateur de taux (milli / secondes, /36).
# Rapport sleep > rest > passive.
RECOVERY_RATES: dict[str, int] = {"passive": 2, "rest": 6, "sleep": 12}

# Niveaux de sévérité (observables ; effets de mobilité reportés à 3.3B2).
SEV_LIGHT_MAX = 30000
SEV_MODERATE_MAX = 60000


class InjuryError(RuntimeError):
    """Erreur de blessure (cause invalide, régime inconnu, heure illégale…)."""


def level(severity_milli: int) -> str:
    """Niveau d'une sévérité (usage observationnel en 3.3B1)."""
    if severity_milli <= 0:
        return "none"
    if severity_milli <= SEV_LIGHT_MAX:
        return "light"
    if severity_milli <= SEV_MODERATE_MAX:
        return "moderate"
    return "severe"


def derive(
    anchor_severity: int,
    anchor_remainder: int,
    anchor_at: str,
    target_at: str,
    rate_num: int,
    rate_den: int,
) -> tuple[int, int]:
    """Sévérité et reste dérivés sur [anchor_at, target_at] (récupération).

    total        = ancien_reste + rate_num * dt
    delta        = total // rate_den           (division plancher)
    reste_nouveau= total - delta * rate_den    (0 <= reste < rate_den)
    sévérité     = ancrée - delta, puis clamp [0, 100000] ; un clamp sur une
    borne remet le reste à zéro (aucune fraction résiduelle ne ressurgit).
    """
    if rate_den <= 0:
        raise InjuryError("rate_den doit être > 0")
    dt = int((parse_iso(target_at) - parse_iso(anchor_at)).total_seconds())
    if dt < 0:
        raise InjuryError("heure cible antérieure à l'heure d'ancrage : refusé")
    total = anchor_remainder + rate_num * dt
    delta = total // rate_den
    new_remainder = total - delta * rate_den
    if not (0 <= new_remainder < rate_den):
        raise InjuryError("reste rationnel hors bornes (ne devrait pas arriver)")
    new_severity = anchor_severity - delta
    if new_severity <= 0 or new_severity >= SEVERITY_MAX:
        new_severity = max(0, min(SEVERITY_MAX, new_severity))
        new_remainder = 0
    return new_severity, new_remainder


def seconds_to_heal(severity: int, remainder: int, rate_num: int, rate_den: int) -> int:
    """Plus petit dt >= 0 tel que la sévérité atteigne 0 sous `rate_num/rate_den`."""
    if severity <= 0:
        return 0
    manque = severity - 0
    numer = manque * rate_den - remainder
    if numer <= 0:
        return 0
    return (numer + rate_num - 1) // rate_num  # ceil


def _add_seconds(iso: str, seconds: int) -> str:
    return to_iso(parse_iso(iso) + timedelta(seconds=seconds))


class InjuryEngine:
    """Moteur des blessures. Écritures uniquement via la couche canonique."""

    def __init__(self, conn: sqlite3.Connection, clock: Clock | None = None) -> None:
        self._conn = conn
        self._clock = clock or Clock()

    def _now(self) -> str:
        return self._clock.now_iso()

    def _world(self) -> Any:
        from .world import WorldEngine  # évite un cycle d'import

        return WorldEngine(self._conn, clock=self._clock)

    def _canonical_time(self, world_id: int) -> str:
        return self._world().read_canonical_time(world_id)

    def _next_seq(self, c: sqlite3.Connection, world_id: int) -> int:
        return c.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 FROM canonical_event WHERE world_id = ?",
            (world_id,),
        ).fetchone()[0]

    def _character_id(self, world_id: int, character_key: str) -> int:
        row = self._conn.execute(
            "SELECT id FROM character WHERE world_id = ? AND key = ?",
            (world_id, character_key),
        ).fetchone()
        if row is None:
            raise InjuryError(f"personnage introuvable : {character_key!r}")
        return row["id"]

    def _current_location_key(self, world_id: int, character_key: str) -> str:
        row = self._conn.execute(
            "SELECT l.key FROM character ch "
            "JOIN location l ON l.id = ch.current_location_id "
            "WHERE ch.world_id = ? AND ch.key = ?",
            (world_id, character_key),
        ).fetchone()
        if row is None:
            raise InjuryError(f"personnage introuvable : {character_key!r}")
        return row["key"]

    # --- Lecture pure -----------------------------------------------------------

    def active_injury_row(
        self, world_id: int, character_key: str
    ) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT i.* FROM injury i "
            "JOIN character ch ON ch.world_id = i.world_id AND ch.id = i.character_id "
            "WHERE i.world_id = ? AND ch.key = ? AND i.status = 'active'",
            (world_id, character_key),
        ).fetchone()

    def injury_sheet(
        self, world_id: int, character_key: str, target_at: str | None = None
    ) -> dict[str, Any] | None:
        """Fiche de la blessure active (lecture dérivée pure, aucune écriture)."""
        row = self.active_injury_row(world_id, character_key)
        if row is None:
            return None
        now = self._canonical_time(world_id)
        at = target_at if target_at is not None else now
        at = min(at, now, key=lambda x: parse_iso(x))
        sev, rem = derive(
            row["severity_milli"], row["rate_remainder"],
            row["recovery_anchor_at"], at,
            RECOVERY_RATES["passive"], DEN,
        )
        return {
            "public_id": row["public_id"],
            "kind": row["kind"],
            "status": row["status"],
            "severity_milli": sev,
            "rate_remainder": rem,
            "level": level(sev),
            "recovery_anchor_at": row["recovery_anchor_at"],
            "recovered_at": row["recovered_at"],
            "cause_event_seq": row["cause_event_seq"],
        }

    def list_injuries(self, world_id: int, character_key: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT i.public_id, i.kind, i.status, i.severity_milli, i.recovered_at "
            "FROM injury i JOIN character ch ON ch.world_id = i.world_id AND ch.id = i.character_id "
            "WHERE i.world_id = ? AND ch.key = ? ORDER BY i.id",
            (world_id, character_key),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Création de la cause ---------------------------------------------------

    def script_accident(
        self,
        world_id: int,
        character_key: str,
        severity_milli: int,
        injury_kind: str = "mobility",
        location_key: str | None = None,
        description: str = "",
        sim_now: str | None = None,
        source: str = SOURCE_OWNER,
    ) -> int:
        """Crée l'événement causal `scripted_accident` (source `owner` par défaut).

        `sim_now` est une injection réservée aux tests internes ; elle ne doit
        jamais être future par rapport à l'heure canonique courante. Retourne le
        `seq` canonique de l'événement.
        """
        cur = self._canonical_time(world_id)
        occurred = sim_now if sim_now is not None else cur
        if parse_iso(occurred) > parse_iso(cur):
            raise InjuryError("heure de cause future refusée")
        if not (0 < severity_milli <= SEVERITY_MAX):
            raise InjuryError("sévérité invalide (doit être 0 < s <= 100000)")

        with transaction(self._conn) as c:
            if location_key is None:
                location_key = self._current_location_key(world_id, character_key)
            if location_key != self._current_location_key(world_id, character_key):
                raise InjuryError("lieu de l'accident différent du lieu courant")
            seq = self._next_seq(c, world_id)
            payload = {
                "character": character_key,
                "injury_kind": injury_kind,
                "severity_milli": severity_milli,
                "location": location_key,
                "description": description,
            }
            _append_event(
                c, world_id, source, "scripted_accident", payload,
                occurred_at=occurred, recorded_at=self._now(),
            )
        return seq

    # --- Blessure à partir d'une cause -----------------------------------------

    def injure_character(self, world_id: int, character_key: str, cause_seq: int) -> dict[str, Any]:
        """Crée la blessure à partir d'un événement causal **préexistant**."""
        with transaction(self._conn) as c:
            return self._injure(c, world_id, character_key, cause_seq)

    def _injure(
        self, c: sqlite3.Connection, world_id: int, character_key: str, cause_seq: int
    ) -> dict[str, Any]:
        cause = c.execute(
            "SELECT * FROM canonical_event WHERE world_id = ? AND seq = ?",
            (world_id, cause_seq),
        ).fetchone()
        if cause is None:
            raise InjuryError(f"cause introuvable : seq {cause_seq}")
        if cause["event_type"] != "scripted_accident":
            raise InjuryError(
                f"type de cause non autorisé : {cause['event_type']!r}"
            )
        payload = json.loads(cause["payload"])
        if payload.get("character") != character_key:
            raise InjuryError("la cause concerne un autre personnage")
        cur = self._canonical_time(world_id)
        if parse_iso(cause["occurred_at"]) != parse_iso(cur):
            raise InjuryError(
                "cause non contiguë : son occurred_at doit être égal à l'heure "
                "canonique courante"
            )
        severity = payload.get("severity_milli")
        if not (0 < severity <= SEVERITY_MAX):
            raise InjuryError("sévérité invalide dans la cause")
        loc = payload.get("location")
        if loc != self._current_location_key(world_id, character_key):
            raise InjuryError("lieu de la cause incohérent avec le lieu courant")
        if c.execute(
            "SELECT 1 FROM injury WHERE world_id = ? AND cause_event_seq = ?",
            (world_id, cause_seq),
        ).fetchone():
            raise InjuryError("cause déjà consommée : elle a déjà produit une blessure")
        if c.execute(
            "SELECT 1 FROM injury WHERE world_id = ? AND character_id = ? AND status = 'active'",
            (world_id, self._character_id(world_id, character_key)),
        ).fetchone():
            raise InjuryError("une blessure active existe déjà pour ce personnage")

        now = self._now()
        started_at = cause["occurred_at"]
        injury_id = new_uuid()
        char_id = self._character_id(world_id, character_key)
        c.execute(
            "INSERT INTO injury "
            "(public_id, world_id, character_id, kind, status, severity_milli, "
            " rate_remainder, recovery_anchor_at, started_at, recovered_at, "
            " cause_event_seq, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 'active', ?, 0, ?, ?, NULL, ?, ?, ?)",
            (
                injury_id, world_id, char_id, payload.get("injury_kind"),
                severity, started_at, started_at, cause_seq, now, now,
            ),
        )
        _append_event(
            c, world_id, SOURCE_ENGINE, "injury_occurred",
            {
                "character": character_key,
                "kind": payload.get("injury_kind"),
                "severity": severity,
                "location": loc,
                "cause_event_type": cause["event_type"],
                "cause_event_seq": cause_seq,
            },
            occurred_at=started_at, recorded_at=now,
        )
        return self.injury_sheet(world_id, character_key)

    # --- Opération combinée -----------------------------------------------------

    def inflict_injury(
        self,
        world_id: int,
        character_key: str,
        severity_milli: int,
        injury_kind: str = "mobility",
        description: str = "",
        sim_now: str | None = None,
        cause_source: str = SOURCE_OWNER,
    ) -> dict[str, Any]:
        """Commodité (tests/administration) : cause + blessure en **une transaction**.

        Si la création de la blessure échoue, l'accident scripté est également
        annulé (aucun faux accident présenté comme ayant causé une blessure).
        """
        cur = self._canonical_time(world_id)
        occurred = sim_now if sim_now is not None else cur
        if parse_iso(occurred) > parse_iso(cur):
            raise InjuryError("heure de cause future refusée")
        if not (0 < severity_milli <= SEVERITY_MAX):
            raise InjuryError("sévérité invalide (doit être 0 < s <= 100000)")

        with transaction(self._conn) as c:
            loc = self._current_location_key(world_id, character_key)
            seq = self._next_seq(c, world_id)
            _append_event(
                c, world_id, cause_source, "scripted_accident",
                {
                    "character": character_key,
                    "injury_kind": injury_kind,
                    "severity_milli": severity_milli,
                    "location": loc,
                    "description": description,
                },
                occurred_at=occurred, recorded_at=self._now(),
            )
            # si _injure échoue, le rollback annule aussi l'accident ci-dessus
            return self._injure(c, world_id, character_key, seq)

    # --- Matérialisation / récupération ----------------------------------------

    def materialize_injury(
        self, world_id: int, character_key: str, target_at: str, regime: str
    ) -> dict[str, Any] | None:
        """Matérialise la récupération de la blessure active à `target_at`.

        `regime` est typé (`passive`/`rest`/`sleep`) ; le moteur le traduit en
        taux constant. Cible doit être >= ancre et <= heure canonique courante.
        Chaque modification réelle émet `injury_materialized` ; la guérison émet
        `injury_healed` à l'heure exacte (la même transaction).
        """
        if regime not in RECOVERY_RATES:
            raise InjuryError(f"régime inconnu : {regime!r}")
        rate = RECOVERY_RATES[regime]
        active = self.active_injury_row(world_id, character_key)
        if active is None:
            return None
        if parse_iso(target_at) < parse_iso(active["recovery_anchor_at"]):
            raise InjuryError("heure cible antérieure à l'heure d'ancrage")
        cur = self._canonical_time(world_id)
        if parse_iso(target_at) > parse_iso(cur):
            raise InjuryError("cible au-delà de l'heure canonique courante")

        with transaction(self._conn) as c:
            row = c.execute(
                "SELECT * FROM injury WHERE id = ?", (active["id"],)
            ).fetchone()
            if row is None:
                return None
            sev, rem = derive(
                row["severity_milli"], row["rate_remainder"],
                row["recovery_anchor_at"], target_at, rate, DEN,
            )
            prev = {
                "severity": row["severity_milli"],
                "anchor": row["recovery_anchor_at"],
                "remainder": row["rate_remainder"],
            }
            now = self._now()
            if sev <= 0:
                heal_sec = seconds_to_heal(
                    row["severity_milli"], row["rate_remainder"], rate, DEN
                )
                heal_time = _add_seconds(row["recovery_anchor_at"], heal_sec)
                new = {"severity": 0, "anchor": heal_time, "remainder": 0}
                _append_event(
                    c, world_id, SOURCE_ENGINE, "injury_materialized",
                    {"character": character_key,
                     "cause_event_seq": row["cause_event_seq"],
                     "regime": regime, "reason": "recovery",
                     "previous": prev, "new": new},
                    occurred_at=heal_time, recorded_at=now,
                )
                _append_event(
                    c, world_id, SOURCE_ENGINE, "injury_healed",
                    {"character": character_key,
                     "cause_event_seq": row["cause_event_seq"],
                     "kind": row["kind"], "healed_at": heal_time},
                    occurred_at=heal_time, recorded_at=now,
                )
                c.execute(
                    "UPDATE injury SET severity_milli = 0, rate_remainder = 0, "
                    "recovery_anchor_at = ?, recovered_at = ?, status = 'healed', "
                    "updated_at = ? WHERE id = ?",
                    (heal_time, heal_time, now, row["id"]),
                )
            elif (parse_iso(target_at) != parse_iso(row["recovery_anchor_at"])) or (sev != row["severity_milli"]) or (rem != row["rate_remainder"]):
                new = {"severity": sev, "anchor": target_at, "remainder": rem}
                _append_event(
                    c, world_id, SOURCE_ENGINE, "injury_materialized",
                    {"character": character_key,
                     "cause_event_seq": row["cause_event_seq"],
                     "regime": regime, "reason": "recovery",
                     "previous": prev, "new": new},
                    occurred_at=target_at, recorded_at=now,
                )
                c.execute(
                    "UPDATE injury SET severity_milli = ?, rate_remainder = ?, "
                    "recovery_anchor_at = ?, updated_at = ? WHERE id = ?",
                    (sev, rem, target_at, now, row["id"]),
                )
            # sinon : aucune modification réelle → aucun événement, aucune écriture
        return self.injury_sheet(world_id, character_key)
