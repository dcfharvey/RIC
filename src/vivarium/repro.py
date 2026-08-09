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
from .needs import derive as needs_derive
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

    w = conn.execute("SELECT name, status FROM worlds WHERE id = ?", (world_id,)).fetchone()
    d["worlds"] = {"name": w["name"], "status": w["status"]}

    has_initial_context = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'world_initial_context'"
    ).fetchone() is not None
    if has_initial_context:
        context = conn.execute(
            "SELECT facts_json FROM world_initial_context WHERE world_id = ?", (world_id,)
        ).fetchone()
        d["world_initial_context"] = None if context is None else json.loads(context["facts_json"])

    has_environment_origin = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'world_environment_origin'"
    ).fetchone() is not None
    if has_environment_origin:
        origin = conn.execute(
            "SELECT b.key, o.blueprint_version, o.resolved_definition_json "
            "FROM world_environment_origin o JOIN environment_blueprint b ON b.id = o.blueprint_id "
            "WHERE o.world_id = ?",
            (world_id,),
        ).fetchone()
        d["world_environment_origin"] = (
            None if origin is None else {
                "blueprint_key": origin["key"],
                "blueprint_version": origin["blueprint_version"],
                "resolved_definition": json.loads(origin["resolved_definition_json"]),
            }
        )

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

    objects: dict[str, dict[str, Any]] = {}
    for r in conn.execute(
        "SELECT o.key, o.name, o.kind, o.state, o.portable, o.container_capacity, "
        "l.key AS location_key, p.key AS parent_key "
        "FROM world_object o JOIN location l ON l.id = o.location_id "
        "LEFT JOIN world_object p ON p.id = o.parent_object_id "
        "WHERE o.world_id = ?",
        (world_id,),
    ).fetchall():
        carrier_row = None
        if conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'character_carried_object'"
        ).fetchone() is not None:
            carrier_row = conn.execute(
                "WITH RECURSIVE ancestors(id, parent_object_id, depth, path) AS ("
                " SELECT id, parent_object_id, 0, ',' || id || ',' FROM world_object WHERE id = "
                "(SELECT id FROM world_object WHERE world_id = ? AND key = ?) "
                " UNION ALL "
                " SELECT o.id, o.parent_object_id, a.depth + 1, a.path || o.id || ',' "
                " FROM world_object o JOIN ancestors a ON a.parent_object_id = o.id "
                " WHERE o.world_id = ? AND instr(a.path, ',' || o.id || ',') = 0"
                ") SELECT ch.key FROM ancestors a JOIN character_carried_object co ON co.object_id = a.id "
                "JOIN character ch ON ch.id = co.character_id WHERE co.world_id = ? "
                "ORDER BY a.depth DESC LIMIT 1",
                (world_id, r["key"], world_id, world_id),
            ).fetchone()
        objects[r["key"]] = {
            "name": r["name"],
            "kind": r["kind"],
            "state": r["state"],
            "portable": bool(r["portable"]),
            "container_capacity": r["container_capacity"],
            "location": r["location_key"],
            "parent": r["parent_key"],
            "carrier": None if carrier_row is None else carrier_row["key"],
        }
    d["world_object"] = dict(sorted(objects.items()))

    has_connectors = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'world_connector'"
    ).fetchone() is not None
    if has_connectors:
        connectors: dict[str, dict[str, Any]] = {}
        for r in conn.execute(
            "SELECT c.key, c.archetype_version, c.directions, c.state, a.key AS archetype, "
            "f.key AS from_key, t.key AS to_key FROM world_connector c "
            "JOIN environment_archetype a ON a.id = c.archetype_id "
            "JOIN location f ON f.id = c.from_location_id JOIN location t ON t.id = c.to_location_id "
            "WHERE c.world_id = ?",
            (world_id,),
        ).fetchall():
            connectors[r["key"]] = {
                "archetype": r["archetype"], "archetype_version": r["archetype_version"],
                "from": r["from_key"], "to": r["to_key"], "directions": r["directions"],
                "state": r["state"],
            }
        d["world_connector"] = dict(sorted(connectors.items()))

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

    has_personality = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'character_personality_disposition'"
    ).fetchone() is not None
    if has_personality:
        dispositions: dict[str, dict[str, Any]] = {}
        for r in conn.execute(
            "SELECT ch.key, p.schema_version, p.traits_json, p.attachment_json "
            "FROM character_personality_disposition p JOIN character ch ON ch.id = p.character_id "
            "WHERE p.world_id = ? ORDER BY ch.key",
            (world_id,),
        ).fetchall():
            dispositions[r["key"]] = {
                "schema_version": r["schema_version"], "traits": json.loads(r["traits_json"]),
                "attachment": json.loads(r["attachment_json"]),
            }
        d["character_personality_disposition"] = dispositions

    has_values = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'character_value_profile'").fetchone() is not None
    if has_values:
        values: dict[str, dict[str, Any]] = {}
        for r in conn.execute("SELECT ch.key, v.ranked_value_keys_json, p.items_json FROM character_value_profile v JOIN character_preference_profile p ON p.world_id = v.world_id AND p.character_id = v.character_id JOIN character ch ON ch.id = v.character_id WHERE v.world_id = ? ORDER BY ch.key", (world_id,)).fetchall():
            values[r["key"]] = {"ranked_value_keys": json.loads(r["ranked_value_keys_json"]), "preferences": json.loads(r["items_json"])}
        d["character_values_preferences"] = values

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

    resources: dict[str, dict[str, dict[str, Any]]] = {}
    for r in conn.execute(
        "SELECT ch.key, rs.resource_key, rs.value_milli, rs.rate_num, rs.rate_den, "
        "rs.rate_remainder, rs.anchor_at FROM resource_state rs "
        "JOIN character ch ON ch.id = rs.character_id WHERE rs.world_id = ?",
        (world_id,),
    ).fetchall():
        resources.setdefault(r["key"], {})[r["resource_key"]] = {
            field: r[field]
            for field in (
                "value_milli", "rate_num", "rate_den", "rate_remainder", "anchor_at"
            )
        }
    d["resource_state"] = {
        key: dict(sorted(value.items())) for key, value in sorted(resources.items())
    }

    resource_rules: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for r in conn.execute(
        "SELECT ch.key AS character_key, rs.resource_key, b.state_key, b.min_milli, b.max_milli, "
        "e.effect_type, e.effect_key, e.availability, e.value_milli "
        "FROM resource_state rs JOIN character ch ON ch.id = rs.character_id "
        "JOIN resource_state_band b ON b.resource_state_id = rs.id "
        "LEFT JOIN resource_state_effect e ON e.resource_state_band_id = b.id "
        "WHERE rs.world_id = ? ORDER BY ch.key, rs.resource_key, b.min_milli, "
        "e.effect_type, e.effect_key",
        (world_id,),
    ).fetchall():
        item = {
            "state_key": r["state_key"],
            "min_milli": r["min_milli"],
            "max_milli": r["max_milli"],
            "effects": [],
        }
        bands = resource_rules.setdefault(r["character_key"], {}).setdefault(
            r["resource_key"], []
        )
        if not bands or bands[-1]["state_key"] != item["state_key"]:
            bands.append(item)
        if r["effect_type"] is not None:
            bands[-1]["effects"].append(
                {
                    "effect_type": r["effect_type"],
                    "effect_key": r["effect_key"],
                    "availability": r["availability"],
                    "value_milli": r["value_milli"],
                }
            )
    d["resource_rules"] = {
        character: dict(sorted(resources.items()))
        for character, resources in sorted(resource_rules.items())
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


def _canonical_rate(
    need: str,
    rate_source: str,
    activity_type: str | None,
    need_defs: dict[str, dict[str, Any]],
    activity_defs: dict[str, dict[str, tuple[int, int]]],
) -> tuple[int, int] | None:
    """Taux canonique autorisé par les règles pour `need` à cet instant.

    `rate_source == "need_definition"` → taux passif de `need_definition` ;
    `rate_source == "activity"` → taux de `activity_definition` pour
    `activity_type`. Retourne None si la source/activité est inconnue.
    """
    if rate_source == "need_definition":
        d = need_defs.get(need)
        return (d["rate_num"], d["rate_den"]) if d else None
    if rate_source == "activity":
        ad = activity_defs.get(activity_type or "")
        if ad and need in ad:
            return ad[need]
        return None
    return None


def _audit_needs_chain(
    events: list[tuple[int, dict[str, Any]]],
    need_defs: dict[str, dict[str, Any]],
    activity_defs: dict[str, dict[str, tuple[int, int]]],
) -> list[tuple[int, str]]:
    """Audit complet d'une chaîne de matérialisation de besoins.

    Vérifie, pour chaque événement : ancres monotones, continuité (previous ==
    new précédent), bornes [0,100000] et restes [0,den), taux déclaré conforme au
    taux canonique des règles (`need_definition`/`activity_definition`), et
    recalcul exact de la valeur et du reste via la fonction canonique `derive`.
    Détecte les erreurs compensées de valeur et de reste.
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
        rate_source = p.get("rate_source", "need_definition")
        activity_type = p.get("activity_type")
        for need in p["new_values"]:
            nv = p["new_values"][need]
            nr = p["new_remainders"][need]
            pv = p["previous_values"][need]
            pr = p["previous_remainders"][need]
            num = p["rate_nums"][need]
            den = p["rate_dens"][need]
            canonical = _canonical_rate(need, rate_source, activity_type, need_defs, activity_defs)
            if canonical is None:
                errors.append((seq, f"needs: unknown canonical rate {need}"))
            elif (num, den) != canonical:
                errors.append((seq, f"needs: declared rate {num}/{den} != canonical {canonical[0]}/{canonical[1]} {need}"))
            if not (0 <= nv <= 100000):
                errors.append((seq, f"needs: value out of bounds {need}"))
            if not (0 <= nr < den):
                errors.append((seq, f"needs: remainder out of bounds {need}"))
            exp_v, exp_r = needs_derive(
                pv, pr, p["previous_anchor_at"], p["new_anchor_at"], num, den
            )
            if exp_v != nv:
                errors.append((seq, f"needs: value {nv} != expected {exp_v} {need}"))
            if exp_r != nr:
                errors.append((seq, f"needs: remainder {nr} != expected {exp_r} {need}"))
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
    # Définitions (configuration créée au seed, non modifiée par la simulation) :
    # elles représentent les règles en vigueur pour tous les événements du run.
    need_defs: dict[str, dict[str, Any]] = {}
    for r in conn.execute(
        "SELECT need_key, rate_num, rate_den FROM need_definition WHERE world_id = ?",
        (world_id,),
    ).fetchall():
        need_defs[r["need_key"]] = {"rate_num": r["rate_num"], "rate_den": r["rate_den"]}
    activity_defs: dict[str, dict[str, tuple[int, int]]] = {}
    for r in conn.execute(
        "SELECT activity_type, satiete_rate, repos_rate, energie_rate, hygiene_rate "
        "FROM activity_definition WHERE world_id = ?",
        (world_id,),
    ).fetchall():
        activity_defs[r["activity_type"]] = {
            "satiete": (r["satiete_rate"], 36),
            "repos": (r["repos_rate"], 36),
            "energie": (r["energie_rate"], 36),
            "hygiene": (r["hygiene_rate"], 36),
        }
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
        for seq, msg in _audit_needs_chain(events, need_defs, activity_defs):
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


def subjective_trace_digest(conn: sqlite3.Connection, world_id: int) -> dict[str, list[dict[str, Any]]]:
    """Projection vérifiable de la mémoire subjective, hors digest canonique."""
    rows = conn.execute(
        "SELECT ch.key AS character, st.request_key, st.source_kind, st.source_event_seq, "
        "st.source_social_speech_act_id, "
        "st.fact_type, st.fact_occurred_at, st.access_kind, st.fidelity, st.payload_json "
        "FROM subjective_trace st JOIN character ch ON ch.id = st.character_id "
        "WHERE st.world_id = ? ORDER BY ch.key, st.encoded_at, st.id",
        (world_id,),
    ).fetchall()
    out: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        out.setdefault(row["character"], []).append({
            "request_key": row["request_key"], "source_kind": row["source_kind"],
            "source_event_seq": row["source_event_seq"],
            "source_social_speech_act_id": row["source_social_speech_act_id"],
            "fact_type": row["fact_type"],
            "fact_occurred_at": row["fact_occurred_at"], "access_kind": row["access_kind"],
            "fidelity": row["fidelity"], "payload": json.loads(row["payload_json"]),
        })
    return out


def subjective_trace_audit(conn: sqlite3.Connection, world_id: int) -> list[str]:
    """Vérifie l'append-only subjectif sans lui attribuer le statut canonique."""
    findings: list[str] = []
    rows = conn.execute(
        "SELECT st.id, st.character_id, st.source_kind, st.source_event_seq, "
        "st.source_social_speech_act_id, st.fact_type, "
        "ste.character_id AS event_character_id, ste.event_type, ste.payload_json "
        "FROM subjective_trace st LEFT JOIN subjective_trace_event ste ON ste.trace_id = st.id "
        "WHERE st.world_id = ? ORDER BY st.id, ste.id",
        (world_id,),
    ).fetchall()
    seen: set[int] = set()
    for row in rows:
        if row["id"] in seen:
            findings.append(f"trace {row['id']}: multiple audit events")
            continue
        seen.add(row["id"])
        if row["event_type"] != "trace_encoded" or row["event_character_id"] != row["character_id"]:
            findings.append(f"trace {row['id']}: missing or mismatched audit event")
            continue
        payload = json.loads(row["payload_json"])
        if payload.get("trace_id") != row["id"] or payload.get("source_kind") != row["source_kind"] or payload.get("fact_type") != row["fact_type"]:
            findings.append(f"trace {row['id']}: audit payload mismatch")
        if (row["source_kind"] == "event") != (row["source_event_seq"] is not None):
            findings.append(f"trace {row['id']}: source kind mismatch")
        if row["source_social_speech_act_id"] is not None and row["source_kind"] != "state":
            findings.append(f"trace {row['id']}: social speech source kind mismatch")
    return findings


def subjective_belief_digest(conn: sqlite3.Connection, world_id: int) -> dict[str, list[dict[str, Any]]]:
    """Projection vérifiable des croyances privées, hors du digest canonique."""
    rows = conn.execute(
        "SELECT ch.key AS character, b.id, b.belief_key, b.question_key, b.proposition_json, "
        "b.polarity, b.confidence_milli, b.status, b.visibility, prior.belief_key AS revision_of, "
        "e.polarity AS evidence_polarity, e.diagnosticity_milli, e.source_reliability_milli, "
        "st.request_key AS source_trace "
        "FROM subjective_belief b JOIN character ch ON ch.id = b.character_id "
        "LEFT JOIN subjective_belief prior ON prior.id = b.revision_of_id "
        "LEFT JOIN subjective_belief_evidence e ON e.belief_id = b.id "
        "LEFT JOIN subjective_trace st ON st.id = e.trace_id "
        "WHERE b.world_id = ? ORDER BY ch.key, b.created_at, b.id, e.id",
        (world_id,),
    ).fetchall()
    out: dict[str, list[dict[str, Any]]] = {}
    by_belief: dict[int, dict[str, Any]] = {}
    for row in rows:
        entry = by_belief.get(row["id"])
        if entry is None:
            entry = {
                "belief_key": row["belief_key"], "question_key": row["question_key"],
                "proposition": json.loads(row["proposition_json"]), "polarity": row["polarity"],
                "confidence_milli": row["confidence_milli"], "status": row["status"],
                "visibility": row["visibility"], "revision_of": row["revision_of"], "evidence": [],
            }
            by_belief[row["id"]] = entry
            out.setdefault(row["character"], []).append(entry)
        if row["source_trace"] is not None:
            entry["evidence"].append({
                "source_trace": row["source_trace"], "polarity": row["evidence_polarity"],
                "diagnosticity_milli": row["diagnosticity_milli"],
                "source_reliability_milli": row["source_reliability_milli"],
            })
    return out


def subjective_belief_audit(conn: sqlite3.Connection, world_id: int) -> list[str]:
    """Détecte les écarts entre croyances, preuves et journal subjectif."""
    findings: list[str] = []
    beliefs = conn.execute(
        "SELECT b.id, b.character_id, b.belief_key, b.status, b.revision_of_id, "
        "parent.world_id AS parent_world_id, parent.character_id AS parent_character_id "
        "FROM subjective_belief b LEFT JOIN subjective_belief parent ON parent.id = b.revision_of_id "
        "WHERE b.world_id = ? ORDER BY b.id",
        (world_id,),
    ).fetchall()
    for belief in beliefs:
        evidence_count = conn.execute(
            "SELECT COUNT(*) FROM subjective_belief_evidence WHERE belief_id = ?", (belief["id"],)
        ).fetchone()[0]
        if evidence_count == 0:
            findings.append(f"belief {belief['id']}: missing evidence")
        event_rows = conn.execute(
            "SELECT event_type, character_id FROM subjective_belief_event "
            "WHERE belief_id = ? AND world_id = ? ORDER BY id",
            (belief["id"], world_id),
        ).fetchall()
        expected = "belief_revised" if belief["revision_of_id"] is not None else "belief_adopted"
        if len(event_rows) != 1 or event_rows[0]["event_type"] != expected or event_rows[0]["character_id"] != belief["character_id"]:
            findings.append(f"belief {belief['id']}: missing or mismatched audit event")
        if belief["revision_of_id"] is not None and (
            belief["parent_world_id"] != world_id or belief["parent_character_id"] != belief["character_id"]
        ):
            findings.append(f"belief {belief['id']}: invalid revision owner")
        if belief["status"] == "contested":
            successor = conn.execute(
                "SELECT 1 FROM subjective_belief child JOIN subjective_belief_event event ON event.belief_id = child.id "
                "WHERE child.revision_of_id = ? AND event.event_type = 'belief_revised' LIMIT 1",
                (belief["id"],),
            ).fetchone()
            if successor is None:
                findings.append(f"belief {belief['id']}: contested without audited successor")
    return findings


def subjective_affect_digest(conn: sqlite3.Connection, world_id: int) -> dict[str, Any]:
    """Projection des humeurs et émotions privées, séparée du digest canonique."""
    moods = conn.execute(
        "SELECT ch.key AS character, mood.valence_milli, mood.activation_milli "
        "FROM mood_state mood JOIN character ch ON ch.id = mood.character_id "
        "WHERE mood.world_id = ? ORDER BY ch.key",
        (world_id,),
    ).fetchall()
    episodes = conn.execute(
        "SELECT ch.key AS character, episode.episode_key, episode.family, target.key AS target, "
        "episode.appraisal_json, episode.intensity_milli, episode.action_tendency, episode.expression_milli, episode.status "
        "FROM emotion_episode episode JOIN character ch ON ch.id = episode.character_id "
        "LEFT JOIN character target ON target.id = episode.target_character_id "
        "WHERE episode.world_id = ? ORDER BY ch.key, episode.created_at, episode.id",
        (world_id,),
    ).fetchall()
    return {
        "moods": {row["character"]: {"valence_milli": row["valence_milli"], "activation_milli": row["activation_milli"]} for row in moods},
        "episodes": [
            {"character": row["character"], "episode_key": row["episode_key"], "family": row["family"],
             "target": row["target"], "appraisal": json.loads(row["appraisal_json"]),
             "intensity_milli": row["intensity_milli"], "action_tendency": row["action_tendency"],
             "expression_milli": row["expression_milli"], "status": row["status"]}
            for row in episodes
        ],
    }


def subjective_affect_audit(conn: sqlite3.Connection, world_id: int) -> list[str]:
    """Contrôle la provenance des états affectifs et leurs journaux privés."""
    findings: list[str] = []
    moods = conn.execute(
        "SELECT mood.id, mood.character_id, mood.last_event_id, event.event_type, event.character_id AS event_character_id "
        "FROM mood_state mood LEFT JOIN mood_event event ON event.id = mood.last_event_id WHERE mood.world_id = ?",
        (world_id,),
    ).fetchall()
    for mood in moods:
        if mood["event_type"] not in {"mood_initialized", "mood_changed"} or mood["event_character_id"] != mood["character_id"]:
            findings.append(f"mood {mood['id']}: missing or mismatched latest event")
    episodes = conn.execute(
        "SELECT episode.id, episode.character_id, episode.status, episode.last_event_id, trace.character_id AS trace_character_id, "
        "event.event_type, event.character_id AS event_character_id "
        "FROM emotion_episode episode JOIN subjective_trace trace ON trace.id = episode.cause_trace_id "
        "LEFT JOIN emotion_event event ON event.id = episode.last_event_id WHERE episode.world_id = ?",
        (world_id,),
    ).fetchall()
    for episode in episodes:
        expected = "emotion_started" if episode["status"] == "active" else "emotion_resolved"
        if episode["trace_character_id"] != episode["character_id"]:
            findings.append(f"emotion {episode['id']}: inaccessible cause")
        if episode["event_type"] != expected or episode["event_character_id"] != episode["character_id"]:
            findings.append(f"emotion {episode['id']}: missing or mismatched latest event")
    return findings


def subjective_social_audit(conn: sqlite3.Connection, world_id: int) -> list[str]:
    """Vérifie la causalité minimale des vues sociales et des permissions."""
    findings: list[str] = []
    relationships = conn.execute(
        "SELECT view.id, view.owner_character_id, view.target_character_id, view.last_event_id, "
        "event.owner_character_id AS event_owner, event.target_character_id AS event_target, trace.character_id AS trace_owner "
        "FROM relationship_view view LEFT JOIN relationship_event event ON event.id=view.last_event_id "
        "LEFT JOIN relationship_evidence evidence ON evidence.view_id=view.id "
        "LEFT JOIN subjective_trace trace ON trace.id=evidence.trace_id WHERE view.world_id=? GROUP BY view.id",
        (world_id,),
    ).fetchall()
    for view in relationships:
        if view["event_owner"] != view["owner_character_id"] or view["event_target"] != view["target_character_id"]:
            findings.append(f"relationship {view['id']}: missing or mismatched latest event")
        if view["trace_owner"] != view["owner_character_id"]:
            findings.append(f"relationship {view['id']}: inaccessible evidence")
    for table, event_table, label in (("personal_boundary", "personal_boundary_event", "boundary"), ("situational_permission", "situational_permission_event", "permission")):
        rows = conn.execute(
            f"SELECT state.id, state.last_event_id, event.id AS event_id FROM {table} state LEFT JOIN {event_table} event ON event.id=state.last_event_id WHERE state.world_id=?",
            (world_id,),
        ).fetchall()
        for row in rows:
            if row["event_id"] is None:
                findings.append(f"{label} {row['id']}: missing latest event")
    return findings


def social_interpretation_digest(conn: sqlite3.Connection, world_id: int) -> dict[str, list[dict[str, Any]]]:
    """Projection vérifiable des interprétations, séparée du canon."""
    rows = conn.execute(
        "SELECT interpretation.id AS interpretation_id, ch.key AS character, interpretation.interpretation_key, "
        "interpretation.source_trace_id, source.request_key AS source_trace_request_key, "
        "interpretation.interaction_role, interpretation.understanding_status, "
        "interpretation.meaning_hypotheses_json, interpretation.motive_hypotheses_json, "
        "prior.interpretation_key AS revision_of_key, interpretation.created_at "
        "FROM social_interpretation interpretation "
        "JOIN character ch ON ch.id = interpretation.character_id "
        "JOIN subjective_trace source ON source.id = interpretation.source_trace_id "
        "LEFT JOIN social_interpretation prior ON prior.id = interpretation.revision_of_id "
        "WHERE interpretation.world_id = ? ORDER BY ch.key, interpretation.created_at, interpretation.id",
        (world_id,),
    ).fetchall()
    out: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        support = conn.execute(
            "SELECT trace.request_key FROM social_interpretation_support support "
            "JOIN subjective_trace trace ON trace.id = support.trace_id "
            "JOIN social_interpretation interpretation ON interpretation.id = support.interpretation_id "
            "WHERE support.interpretation_id = ? ORDER BY support.id", (row["interpretation_id"],)
        ).fetchall()
        out.setdefault(row["character"], []).append({
            "interpretation_key": row["interpretation_key"], "source_trace_id": row["source_trace_id"],
            "source_trace_request_key": row["source_trace_request_key"],
            "interaction_role": row["interaction_role"], "understanding_status": row["understanding_status"],
            "meaning_hypotheses": json.loads(row["meaning_hypotheses_json"]),
            "motive_hypotheses": json.loads(row["motive_hypotheses_json"]),
            "revision_of_key": row["revision_of_key"],
            "supporting_trace_request_keys": tuple(item["request_key"] for item in support),
            "created_at": row["created_at"],
        })
    return out


def social_interpretation_audit(conn: sqlite3.Connection, world_id: int) -> list[str]:
    """Vérifie la provenance, l'ownership et l'audit append-only SCC-1A."""
    findings: list[str] = []
    rows = conn.execute(
        "SELECT interpretation.id, interpretation.world_id, interpretation.character_id, "
        "interpretation.source_trace_id, interpretation.revision_of_id, interpretation.origin_kind, "
        "interpretation.model_id, interpretation.provider_version, interpretation.snapshot_fingerprint, "
        "interpretation.provider_turn_id, event.event_type, "
        "event.character_id AS event_character_id, event.payload_json "
        "FROM social_interpretation interpretation "
        "LEFT JOIN social_interpretation_event event ON event.interpretation_id = interpretation.id "
        "WHERE interpretation.world_id = ? ORDER BY interpretation.id, event.id", (world_id,)
    ).fetchall()
    seen: set[int] = set()
    for row in rows:
        if row["id"] in seen:
            findings.append(f"interpretation {row['id']}: multiple audit events")
            continue
        seen.add(row["id"])
        expected_event = "interpretation_revised" if row["revision_of_id"] is not None else "interpretation_created"
        if row["event_type"] != expected_event or row["event_character_id"] != row["character_id"]:
            findings.append(f"interpretation {row['id']}: missing or mismatched audit event")
            continue
        if row["origin_kind"] == "llm":
            import re
            if (not isinstance(row["model_id"], str) or not row["model_id"].strip()
                    or not isinstance(row["provider_version"], str) or not row["provider_version"].strip()
                    or not isinstance(row["snapshot_fingerprint"], str)
                    or re.fullmatch(r"[0-9a-f]{64}", row["snapshot_fingerprint"]) is None):
                findings.append(f"interpretation {row['id']}: incoherent LLM provenance")
        elif row["origin_kind"] == "direct_controlled":
            if any(row[key] is not None for key in ("model_id", "provider_version", "snapshot_fingerprint", "provider_turn_id")):
                findings.append(f"interpretation {row['id']}: direct provenance masks LLM fields")
        else:
            findings.append(f"interpretation {row['id']}: unknown provenance origin")
        payload = json.loads(row["payload_json"])
        if payload.get("interpretation_id") != row["id"] or payload.get("source_trace_id") != row["source_trace_id"]:
            findings.append(f"interpretation {row['id']}: audit payload mismatch")
        if payload.get("revision_of_id") != row["revision_of_id"]:
            findings.append(f"interpretation {row['id']}: revision audit mismatch")
        support_ids = [item["trace_id"] for item in conn.execute(
            "SELECT trace_id FROM social_interpretation_support WHERE interpretation_id = ? ORDER BY id",
            (row["id"],),
        ).fetchall()]
        if payload.get("support_trace_ids") != support_ids:
            findings.append(f"interpretation {row['id']}: support audit mismatch")
    support = conn.execute(
        "SELECT support.id, interpretation.world_id, interpretation.character_id, interpretation.source_trace_id, "
        "trace.id AS trace_id, trace.world_id AS trace_world_id, "
        "trace.character_id AS trace_character_id, trace.fact_type, trace.source_social_speech_act_id "
        "FROM social_interpretation_support support "
        "JOIN social_interpretation interpretation ON interpretation.id = support.interpretation_id "
        "JOIN subjective_trace trace ON trace.id = support.trace_id "
        "WHERE interpretation.world_id = ?", (world_id,)
    ).fetchall()
    for row in support:
        if (row["world_id"], row["character_id"]) != (row["trace_world_id"], row["trace_character_id"]):
            findings.append(f"support {row['id']}: inaccessible or wrong owner")
        elif row["trace_id"] == row["source_trace_id"]:
            findings.append(f"support {row['id']}: duplicates primary source")
    return findings


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
