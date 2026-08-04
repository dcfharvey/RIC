"""Outils de reproductibilité et de comparaison (Phase 3.3C).

Digests et rapport **non persistés**, destinés aux tests et au diagnostic. Ils
ne constituent ni une vérité canonique supplémentaire ni une écriture.

Garantie de reproductibilité :
    même état initial
    + mêmes règles
    + mêmes commandes
    + mêmes valeurs de l'horloge injectée aux mêmes points
    + même ordre canonique
    = même état et même journal sémantique

Distinction des régimes temporels :
- monde actif : `read_canonical_time = simulated_now + (now - real_updated_at)`
  (le temps mural écoulé compte légitimement) ;
- monde paused : `read_canonical_time = simulated_now` (le temps mural ne compte pas).

Les références sont normalisées par clés logiques (`character.key`,
`location.key`, `need_key`, type d'activité + personnage, `cause_event_seq`).
Les rowids, UUID, timestamps muraux et clés étrangères numériques sont exclus.
`canonical_event` n'est pas dans `CanonicalStateDigest` : il possède son propre
`SemanticEventDigest` ; le `max(seq)` courant est comparé comme invariant séparé.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any


def _norm_payload(payload: str) -> str:
    """JSON déterministe (clés triées, séparateurs compacts)."""
    return json.dumps(json.loads(payload), sort_keys=True, separators=(",", ":"))


def canonical_state_digest(conn: sqlite3.Connection, world_id: int) -> dict[str, Any]:
    """Digest déterministe de l'état canonique, références par clés logiques."""
    d: dict[str, Any] = {}

    w = conn.execute("SELECT status FROM worlds WHERE id = ?", (world_id,)).fetchone()
    d["worlds"] = {"status": w["status"]}

    c = conn.execute(
        "SELECT simulated_now FROM canonical_clock WHERE world_id = ?", (world_id,)
    ).fetchone()
    d["canonical_clock"] = {"simulated_now": c["simulated_now"]}

    chars: dict[str, dict[str, Any]] = {}
    for r in conn.execute(
        "SELECT ch.key, ch.name, l.key AS loc FROM character ch "
        "JOIN location l ON l.id = ch.current_location_id WHERE ch.world_id = ?",
        (world_id,),
    ).fetchall():
        chars[r["key"]] = {"name": r["name"], "location": r["loc"]}
    d["character"] = dict(sorted(chars.items()))

    prof: dict[str, dict[str, int]] = {}
    for r in conn.execute(
        "SELECT ch.key, cp.satiete_threshold_mult_milli, cp.repos_threshold_mult_milli, "
        "cp.energie_threshold_mult_milli, cp.hygiene_threshold_mult_milli, "
        "cp.rest_preference_milli, cp.idle_tolerance_milli "
        "FROM character_profile cp JOIN character ch ON ch.id = cp.character_id "
        "WHERE cp.world_id = ?",
        (world_id,),
    ).fetchall():
        prof[r["key"]] = {
            k: r[k]
            for k in r.keys()
            if k != "key"
        }
    d["character_profile"] = dict(sorted(prof.items()))

    needs: dict[str, dict[str, dict[str, Any]]] = {}
    for r in conn.execute(
        "SELECT ch.key, ns.need_key, ns.value_milli, ns.rate_remainder, ns.anchor_at "
        "FROM need_state ns JOIN character ch ON ch.id = ns.character_id "
        "WHERE ns.world_id = ?",
        (world_id,),
    ).fetchall():
        needs.setdefault(r["key"], {})[r["need_key"]] = {
            "value_milli": r["value_milli"],
            "rate_remainder": r["rate_remainder"],
            "anchor_at": r["anchor_at"],
        }
    d["need_state"] = {
        k: dict(sorted(v.items())) for k, v in sorted(needs.items())
    }

    acts: dict[str, list[dict[str, Any]]] = {}
    for r in conn.execute(
        "SELECT ch.key, a.type, a.status, a.started_at, a.planned_end_at, l.key AS loc "
        "FROM activity a JOIN character ch ON ch.id = a.character_id "
        "JOIN location l ON l.id = a.location_id WHERE a.world_id = ?",
        (world_id,),
    ).fetchall():
        acts.setdefault(r["key"], []).append({
            "type": r["type"], "status": r["status"],
            "started_at": r["started_at"], "planned_end_at": r["planned_end_at"],
            "location": r["loc"],
        })
    d["activity"] = {
        k: sorted(v, key=lambda x: (x["started_at"], x["type"], x["status"]))
        for k, v in sorted(acts.items())
    }

    inj: dict[str, list[dict[str, Any]]] = {}
    for r in conn.execute(
        "SELECT ch.key, i.kind, i.status, i.severity_milli, i.rate_remainder, "
        "i.recovery_anchor_at, i.started_at, i.recovered_at, i.cause_event_seq "
        "FROM injury i JOIN character ch ON ch.id = i.character_id "
        "WHERE i.world_id = ?",
        (world_id,),
    ).fetchall():
        inj.setdefault(r["key"], []).append({
            k: r[k] for k in r.keys() if k != "key"
        })
    d["injury"] = {
        k: sorted(v, key=lambda x: x["started_at"]) for k, v in sorted(inj.items())
    }
    return d


def max_seq(conn: sqlite3.Connection, world_id: int) -> int:
    """Séquence canonique courante (invariant séparé du digest d'état)."""
    return conn.execute(
        "SELECT COALESCE(MAX(seq), 0) FROM canonical_event WHERE world_id = ?",
        (world_id,),
    ).fetchone()[0]


# Événements de matérialisation (bookkeeping) : leur découpage exact diffère
# légitimement entre un run continu et un run segmenté/redémarré (les ancres
# sont avancées à des bornes différentes). Ils ne représentent pas un fait du
# monde ; ils sont exclus de la comparaison sémantique. Les faits significatifs
# (activités, déplacements, blessures, horloge admin) restent comparés.
_MATERIALIZATION_EVENTS = frozenset({"needs_materialized", "injury_materialized"})


def semantic_event_digest(conn: sqlite3.Connection, world_id: int) -> list[tuple]:
    """Digest sémantique du journal (faits significatifs, ordre préservé).

    Exclut les événements de matérialisation (`needs_materialized`,
    `injury_materialized`) dont le découpage diffère légitimement entre un run
    continu et un run segmenté/redémarré. Le `seq` absolu n'est pas comparé :
    la matérialisation intercalée change le numéro absolu tout en préservant
    l'ordre des faits ; la continuité de `seq` est vérifiée comme invariant
    structurel séparé.
    """
    rows = conn.execute(
        "SELECT event_type, occurred_at, source_kind, payload "
        "FROM canonical_event WHERE world_id = ? ORDER BY seq",
        (world_id,),
    ).fetchall()
    return [
        (r["event_type"], r["occurred_at"], r["source_kind"],
         _norm_payload(r["payload"]))
        for r in rows
        if r["event_type"] not in _MATERIALIZATION_EVENTS
    ]


@dataclass
class SimulationRunReport:
    """Rapport stable de simulation (outil de test/diagnostic, non canonique)."""

    commit: str
    schema_version: int
    world_id: int
    start_time: str
    end_time: str
    rng_seed: str | None = "not_applicable"  # aucun RNG : pas applicable
    restart_points: list[str] = field(default_factory=list)
    pause_intervals: list[tuple[str, str]] = field(default_factory=list)
    transition_count: int = 0
    event_count_by_type: dict[str, int] = field(default_factory=dict)
    final_character_states: dict[str, Any] = field(default_factory=dict)
    final_need_states: dict[str, Any] = field(default_factory=dict)
    final_injuries: dict[str, Any] = field(default_factory=dict)
    canonical_state_digest: dict[str, Any] = field(default_factory=dict)
    semantic_event_digest: list[tuple] = field(default_factory=list)
    invariant_findings: list[str] = field(default_factory=list)
