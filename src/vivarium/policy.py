"""Politique de décision déterministe (Sous-lot 3.2C).

`DecisionPolicy.decide(context)` produit uniquement une intention structurée ;
elle ne modifie jamais la base, les besoins, la position ni les activités, et ne
reçoit aucune connexion ni capacité d'interrogation. `PolicyContext` est un
instantané immuable de données.

Arithmétique entière uniquement (aucun flottant) :
- urgency_milli(need) = deficit × 1000 // seuil_effectif   (0..1000)
- comparaisons par produits croisés pour éviter les pertes d'arrondi.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Seuils critiques absolus (milli)
CRIT_REPOS = 20000
CRIT_ENERGIE = 15000

# Règle graduée de rest_preference (bande modérée uniquement)
PAIR_REST_MIN_MILLI = 100          # préférence repos minimale pour préférer rest (cas double-déficit)
PAIR_REST_MODERATE_URGENCY = 600   # bande modérée : pair_urgency <= ce seuil
PAIR_SLEEP_MIN_NEG_MILLI = -100    # préférence négative minimale pour préférer sleep (cas isolé)

# Ordre de départage stable en cas d'égalité exacte
CAND_ORDER: tuple[str, ...] = ("satiete", "hygiene", "repos", "energie")


@dataclass(frozen=True)
class Intent:
    """Contrat minimal d'exécution pour le moteur."""

    activity_type: str
    target_location_key: str


@dataclass(frozen=True)
class DecisionResult:
    """Justification observable, séparée du contrat d'exécution (non canonique seule)."""

    intent: Intent
    trigger_need: str | None = None
    reason_code: str | None = None


@dataclass(frozen=True)
class PolicyContext:
    """Instantané de données (aucune capacité d'accès/exécution)."""

    character_key: str
    needs: dict[str, int]                  # valeur dérivée (value_milli)
    effective_thresholds: dict[str, int]   # seuils effectifs (profil appliqué)
    current_location: str
    profile: dict[str, int]                # les 6 paramètres du profil (milli)
    # activity_type -> {dest_key: distance}; seules les destinations accessibles,
    # déjà triées et filtrées par l'appelant (aucune lecture ici).
    accessible: dict[str, dict[str, int]] = field(default_factory=dict)


def _max_by_products(items: list[tuple[str, int, int]]) -> tuple[str, int, int]:
    """Max de deficit/seuil par produits croisés ; garde la première en cas d'égalité."""
    best: tuple[str, int, int] | None = None
    for label, d, s in items:
        if best is None or d * best[2] > best[1] * s:
            best = (label, d, s)
    assert best is not None
    return best


def _urgency(deficit: int, seuil: int) -> int:
    if deficit <= 0:
        return 0
    return deficit * 1000 // seuil


class DeterministicPolicy:
    """Politique déterministe ; même algorithme pour tous les personnages."""

    PROFILE_KEYS = (
        "satiete_threshold_mult_milli", "repos_threshold_mult_milli",
        "energie_threshold_mult_milli", "hygiene_threshold_mult_milli",
        "rest_preference_milli", "idle_tolerance_milli",
    )

    def decide(self, context: PolicyContext) -> DecisionResult:
        needs = context.needs
        se = context.effective_thresholds
        prof = context.profile
        idle_floor = 100 + 400 * prof["idle_tolerance_milli"] // 1000

        # 1) toute urgence critique → agir immédiatement (sleep ; idle_tolerance ignorée)
        repos_crit = needs["repos"] < CRIT_REPOS
        energie_crit = needs["energie"] < CRIT_ENERGIE
        if repos_crit or energie_crit:
            trigger = "repos" if repos_crit else "energie"
            return self._result(context, "sleep", trigger, "critical")

        # 2) déficits (champ sous son seuil effectif)
        defs: dict[str, int | None] = {}
        for k in CAND_ORDER:
            v, s = needs[k], se[k]
            defs[k] = (s - v) if v < s else None

        # 3) groupes candidats (satiete → eat, hygiene → clean, repos/energie → sleep|rest)
        candidates: list[tuple[str, int, int, str]] = []  # (label, deficit, seuil, activité)
        if defs["satiete"] is not None:
            candidates.append(("satiete", defs["satiete"], se["satiete"], "eat"))
        if defs["hygiene"] is not None:
            candidates.append(("hygiene", defs["hygiene"], se["hygiene"], "clean"))
        rest_rep = self._rest_rep(defs, se)
        if rest_rep is not None:
            candidates.append(("rest_sleep", rest_rep[0], rest_rep[1], "sleep|rest"))

        if not candidates:
            return self._result(context, "idle", None, "no_need")

        winner = _max_by_products([(lbl, d, s) for lbl, d, s, _ in candidates])
        lbl = winner[0]

        # 4) action
        if lbl == "satiete":
            return self._act_single(context, "eat", "satiete", idle_floor)
        if lbl == "hygiene":
            return self._act_single(context, "clean", "hygiene", idle_floor)
        # repos/energie conjoints
        return self._act_pair(context, defs, se, idle_floor)

    def _rest_rep(self, defs, se):
        dr, de = defs["repos"], defs["energie"]
        if dr is None and de is None:
            return None
        if dr is None:
            return (de, se["energie"])
        if de is None:
            return (dr, se["repos"])
        # le plus urgent ; égalité → repos d'abord
        lbl, d, s = _max_by_products(
            [("repos", dr, se["repos"]), ("energie", de, se["energie"])]
        )
        return (d, s)

    def _act_single(self, ctx, activity, need_key, idle_floor) -> DecisionResult:
        v, s = ctx.needs[need_key], ctx.effective_thresholds[need_key]
        u = _urgency(s - v, s)
        if u <= idle_floor:
            return self._result(ctx, "idle", need_key, "idle_floor")
        return self._result(ctx, activity, need_key, None)

    def _act_pair(self, ctx, defs, se, idle_floor) -> DecisionResult:
        u_repos = _urgency(defs["repos"] or 0, se["repos"])
        u_energie = _urgency(defs["energie"] or 0, se["energie"])
        pair_urgency = max(u_repos, u_energie)
        trigger = "energie" if u_energie >= u_repos else "repos"

        if pair_urgency <= idle_floor:
            return self._result(ctx, "idle", trigger, "idle_floor")

        rest_pref = ctx.profile["rest_preference_milli"]
        both = defs["repos"] is not None and defs["energie"] is not None
        if both:
            prefer_rest = (
                rest_pref >= PAIR_REST_MIN_MILLI
                and pair_urgency <= PAIR_REST_MODERATE_URGENCY
            )
            activity = "rest" if prefer_rest else "sleep"
        else:
            # cas isolé (un seul besoin modérément déficient) : défaut rest,
            # préférence négative suffisamment forte -> sleep (graduée par magnitude)
            prefer_sleep = rest_pref <= PAIR_SLEEP_MIN_NEG_MILLI
            activity = "sleep" if prefer_sleep else "rest"
        return self._result(ctx, activity, trigger, None)

    def _result(self, ctx, activity, trigger, reason_code) -> DecisionResult:
        if activity == "idle":
            intent = Intent("idle", ctx.current_location)
            return DecisionResult(intent, trigger, reason_code)
        dests = ctx.accessible.get(activity)
        if not dests:
            # aucune destination accessible
            intent = Intent("idle", ctx.current_location)
            return DecisionResult(intent, trigger, "no_accessible_destination")
        # destination déterministe : distance minimale, départage par clé stable
        min_dist = min(dests.values())
        dest = min((k for k, d in dests.items() if d == min_dist), key=lambda k: k)
        return DecisionResult(Intent(activity, dest), trigger, reason_code)
