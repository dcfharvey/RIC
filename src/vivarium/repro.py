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

from .injury import RECOVERY_RATES
from .util import parse_iso


def _norm_payload(payload: str) -> str:
    """JSON déterministe (clés triées, séparateurs compacts)."""
    return json.dumps(json.loads(payload), sort_keys=True, separators=(",", ":"))


def _is_valid_json(payload: str) -> bool:
    try:
        json.loads(payload)
        return True
    except (ValueError, TypeError):
        return False


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
# monde ; ils sont exclus de la projection sémantique. Les faits significatifs
# (activités, déplacements, blessures, horloge admin) restent comparés.
_MATERIALIZATION_EVENTS = frozenset({"needs_materialized", "injury_materialized"})


def raw_canonical_event_log(conn: sqlite3.Connection, world_id: int) -> list[tuple]:
    """Journal canonique brut complet : toutes les séquences, tous les événements,
    aucune exclusion (y compris `recorded_at` mural, non canonique)."""
    rows = conn.execute(
        "SELECT seq, event_type, occurred_at, source_kind, payload, recorded_at "
        "FROM canonical_event WHERE world_id = ? ORDER BY seq",
        (world_id,),
    ).fetchall()
    return [
        (r["seq"], r["event_type"], r["occurred_at"], r["source_kind"],
         r["payload"], r["recorded_at"])
        for r in rows
    ]


def structural_event_audit(conn: sqlite3.Connection, world_id: int) -> dict[str, Any]:
    """Audit structurel du journal brut (invariants par run).

    Vérifie : séquences continues 1..N, aucun trou, aucun doublon, `occurred_at`
    monotones, payloads JSON valides, causalités pointant vers des événements
    existants. Ne dépend pas de l'ordre implicite de SQLite (tri explicite).
    """
    rows = conn.execute(
        "SELECT seq, event_type, occurred_at, payload "
        "FROM canonical_event WHERE world_id = ? ORDER BY seq",
        (world_id,),
    ).fetchall()
    seqs = [r["seq"] for r in rows]
    times = [parse_iso(r["occurred_at"]) for r in rows]
    existing = set(seqs)
    bad_causes: list[tuple[int, int]] = []
    for r in rows:
        p = json.loads(r["payload"])
        if "cause_event_seq" in p and p["cause_event_seq"] not in existing:
            bad_causes.append((r["seq"], p["cause_event_seq"]))
    return {
        "seq_continuous_1_to_n": seqs == list(range(1, len(seqs) + 1)),
        "no_holes": len(seqs) == 0 or (seqs[0] == 1 and seqs[-1] == len(seqs)),
        "no_duplicate_seq": len(seqs) == len(set(seqs)),
        "occurred_at_monotonic": all(b >= a for a, b in zip(times, times[1:])),
        "payloads_valid_json": all(_is_valid_json(r["payload"]) for r in rows),
        "causality_valid": not bad_causes,
        "bad_causes": bad_causes,
    }


def reproducible_semantic_projection(conn: sqlite3.Connection, world_id: int) -> list[tuple]:
    """Projection sémantique reproductible (faits significatifs, ordre préservé).

    Destinée à comparer un run continu, segmenté et redémarré. Exclut les
    événements de matérialisation dont le découpage diffère légitimement, et
    renumérote les faits retenus 1..N (position relative) pour la comparaison.
    La causalité (`cause_event_seq`) est normalisée vers la position relative de
    l'événement causal retenu (jamais masquée ni supprimée).
    """
    rows = conn.execute(
        "SELECT seq, event_type, occurred_at, source_kind, payload "
        "FROM canonical_event WHERE world_id = ? ORDER BY seq",
        (world_id,),
    ).fetchall()
    retained = [r for r in rows if r["event_type"] not in _MATERIALIZATION_EVENTS]
    seq_to_rel = {r["seq"]: i + 1 for i, r in enumerate(retained)}
    out: list[tuple] = []
    for r in retained:
        p = json.loads(r["payload"])
        if "cause_event_seq" in p:
            cause = p["cause_event_seq"]
            if cause in seq_to_rel:
                p["cause_event_seq"] = seq_to_rel[cause]
        out.append((r["event_type"], r["occurred_at"], r["source_kind"],
                    json.dumps(p, sort_keys=True, separators=(",", ":"))))
    return out


def semantic_event_digest(conn: sqlite3.Connection, world_id: int) -> list[tuple]:
    """Alias de `reproducible_semantic_projection` (objet C)."""
    return reproducible_semantic_projection(conn, world_id)


def _audit_needs_chain(events: list[tuple[int, dict[str, Any]]]) -> list[tuple[int, str]]:
    """Audit d'une chaîne de matérialisation de besoins (liste de (seq, payload)).

    Vérifie : ancres monotones, bornes [0,100000], restes [0,36), continuité
    (previous == new précédent), et taux implicite entier (détecte les erreurs
    de reste compensées). Le taux attendu n'étant pas porté par l'événement, une
    erreur de valeur compensée dont le taux implicite reste entier n'est pas
    détectable ici — champ manquant : `rate_num`/`rate_den` (et type d'activité
    pour les raisons liées à une activité).
    """
    errors: list[tuple[int, str]] = []
    prev: dict[str, Any] | None = None
    for seq, p in events:
        pa = parse_iso(p["previous_anchor_at"])
        na = parse_iso(p["new_anchor_at"])
        if na < pa:
            errors.append((seq, "needs: new_anchor < previous_anchor"))
        if prev is not None:
            for need in p["previous_values"]:
                if p["previous_values"][need] != prev["new_values"][need]:
                    errors.append((seq, f"needs: value discontinuity {need}"))
                if p["previous_remainders"][need] != prev["new_remainders"][need]:
                    errors.append((seq, f"needs: remainder discontinuity {need}"))
        dt = int((na - pa).total_seconds())
        for need in p["new_values"]:
            nv = p["new_values"][need]
            nr = p["new_remainders"][need]
            pv = p["previous_values"][need]
            pr = p["previous_remainders"][need]
            if not (0 <= nv <= 100000):
                errors.append((seq, f"needs: value out of bounds {need}"))
            if not (0 <= nr < 36):
                errors.append((seq, f"needs: remainder out of bounds {need}"))
            delta = nv - pv
            total = delta * 36 + nr
            numer = total - pr
            if dt > 0 and numer % dt != 0:
                errors.append((seq, f"needs: implied rate non-integer {need}"))
            elif dt == 0 and delta != 0:
                errors.append((seq, f"needs: change at zero duration {need}"))
        prev = p
    return errors


def _audit_injury_chain(
    events: list[tuple[int, str, dict[str, Any]]]
) -> list[tuple[int, str]]:
    """Audit d'une chaîne de matérialisation de blessure (liste de
    (seq, event_type, payload)). Recompte sévérité et reste depuis le régime
    (taux connu), détectant les erreurs compensées. Vérifie la guérison exacte
    et l'absence de matérialisation après guérison.
    """
    errors: list[tuple[int, str]] = []
    healed = False
    for seq, etype, p in events:
        if etype == "injury_healed":
            healed = True
            continue
        if healed:
            errors.append((seq, "injury: materialization after healed"))
            continue
        rate = RECOVERY_RATES.get(p.get("regime"))
        if rate is None:
            errors.append((seq, "injury: unknown regime"))
            continue
        prev_sev = p["previous"]["severity"]
        prev_rem = p["previous"]["remainder"]
        prev_anchor = parse_iso(p["previous"]["anchor"])
        new_anchor = parse_iso(p["new"]["anchor"])
        new_sev = p["new"]["severity"]
        new_rem = p["new"]["remainder"]
        dt = int((new_anchor - prev_anchor).total_seconds())
        total = prev_rem + rate * dt
        delta = total // 36
        exp_rem = total - delta * 36
        exp_sev = prev_sev - delta
        if exp_sev != new_sev:
            errors.append((seq, f"injury: severity {new_sev} != expected {exp_sev}"))
        if exp_rem != new_rem:
            errors.append((seq, f"injury: remainder {new_rem} != expected {exp_rem}"))
        if new_sev < 0:
            errors.append((seq, "injury: negative severity"))
    return errors


def materialization_chain_audit(
    conn: sqlite3.Connection, world_id: int
) -> list[tuple[int, str, str]]:
    """Audit de cohérence mathématique des chaînes de matérialisation (objet D).

    Vérifie, dans chaque journal brut pris séparément, la validité de chaque
    trajectoire technique (besoins et blessures), sans exiger que le run continu
    et le run segmenté aient le même découpage. Retourne une liste de
    (seq, personnage, message) pour chaque événement incorrect.
    """
    errors: list[tuple[int, str, str]] = []
    rows = conn.execute(
        "SELECT seq, payload FROM canonical_event "
        "WHERE world_id = ? AND event_type = 'needs_materialized' ORDER BY seq",
        (world_id,),
    ).fetchall()
    by_char: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for r in rows:
        p = json.loads(r["payload"])
        by_char.setdefault(p["character"], []).append((r["seq"], p))
    for char, events in by_char.items():
        for seq, msg in _audit_needs_chain(events):
            errors.append((seq, char, msg))
    rows = conn.execute(
        "SELECT seq, event_type, payload FROM canonical_event "
        "WHERE world_id = ? AND event_type IN "
        "('injury_materialized','injury_healed') ORDER BY seq",
        (world_id,),
    ).fetchall()
    by_inj: dict[tuple, list[tuple[int, str, dict[str, Any]]]] = {}
    for r in rows:
        p = json.loads(r["payload"])
        key = (p.get("character"), p.get("cause_event_seq"))
        by_inj.setdefault(key, []).append((r["seq"], r["event_type"], p))
    for key, events in by_inj.items():
        for seq, msg in _audit_injury_chain(events):
            errors.append((seq, key[0], msg))
    return errors


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
