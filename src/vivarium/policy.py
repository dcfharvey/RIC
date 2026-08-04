"""Politique de décision déterministe (Sous-lot 3.2C, étendu 3.3A).

`DecisionPolicy.decide(context)` produit uniquement une intention structurée ;
elle ne modifie rien et ne reçoit aucune connexion ni capacité d'interrogation.

3.3A :
- `Intent` transporte `duration_seconds` (obligatoire uniquement pour `idle`) ;
- l'attente `idle` a une **durée dynamique** = première seconde où la décision
  changerait (franchissement d'un seuil/critique/palier d'urgence) ;
- règle de sommeil naturelle : repos déficient ⇒ sleep ; energy seule modérée ⇒
  rest ; critique ⇒ sleep (rest_preference ne bloque jamais un sommeil exigé).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

# Seuils critiques absolus (milli)
CRIT_REPOS = 20000
CRIT_ENERGIE = 15000

# Plafond de sécurité de l'attente (3.3A)
MAX_IDLE = 28800  # 8 h en secondes

# Ordre de départage stable en cas d'égalité exacte
CAND_ORDER: tuple[str, ...] = ("satiete", "hygiene", "repos", "energie")

DEN = 36


@dataclass(frozen=True)
class Intent:
    """Contrat minimal d'exécution pour le moteur.

    `duration_seconds` n'est utilisé que pour `idle` (attente dynamique) ;
    il est refusé pour les activités dont la durée vient de la définition ou
    d'une condition de fin.
    """

    activity_type: str
    target_location_key: str
    duration_seconds: int | None = None


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
    need_remainders: dict[str, int]        # restes dérivés au même instant
    effective_thresholds: dict[str, int]   # seuils effectifs (profil appliqué)
    current_location: str
    profile: dict[str, int]                # les 6 paramètres du profil (milli)
    rates: dict[str, int]                  # taux passifs /36 par besoin
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


def _derive_seconds(
    anchor_value: int, anchor_remainder: int, dt: int, num: int, den: int
) -> tuple[int, int]:
    """Même arithmétique que `needs.derive`, mais sur `dt` secondes entières."""
    total = anchor_remainder + num * dt
    delta = total // den
    new_remainder = total - delta * den
    new_value = anchor_value + delta
    if new_value <= 0 or new_value >= 100000:
        new_value = max(0, min(100000, new_value))
        new_remainder = 0
    return new_value, new_remainder


def _first_true(lo: int, hi: int, f: Callable[[int], bool]) -> int | None:
    """Plus petit dt ∈ [lo, hi] où f(dt) est vrai (f monotone croissante)."""
    if f(lo):
        return lo
    if not f(hi):
        return None
    # invariant : f(lo) faux, f(hi) vrai
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if f(mid):
            hi = mid
        else:
            lo = mid
    return hi


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

        # 1) toute urgence critique → agir immédiatement (sleep, jamais d'attente)
        repos_crit = needs["repos"] < CRIT_REPOS
        energie_crit = needs["energie"] < CRIT_ENERGIE
        if repos_crit or energie_crit:
            trigger = "repos" if repos_crit else "energie"
            return self._result(context, "sleep", trigger, "critical")

        # déficits (champ sous son seuil effectif)
        defs: dict[str, int | None] = {}
        for k in CAND_ORDER:
            v, s = needs[k], se[k]
            defs[k] = (s - v) if v < s else None

        # groupes candidats (satiete → eat, hygiene → clean, repos/energie → sleep|rest)
        candidates: list[tuple[str, int, int, str]] = []
        if defs["satiete"] is not None:
            candidates.append(("satiete", defs["satiete"], se["satiete"], "eat"))
        if defs["hygiene"] is not None:
            candidates.append(("hygiene", defs["hygiene"], se["hygiene"], "clean"))
        rest_rep = self._rest_rep(defs, se)
        if rest_rep is not None:
            candidates.append(("rest_sleep", rest_rep[0], rest_rep[1], "sleep|rest"))

        has_deficient = any(defs[k] is not None for k in CAND_ORDER)

        if not candidates:
            # rien ne nécessite d'agir : attente jusqu'à la prochaine borne
            wait, reason = self._idle_wait(context, idle_floor, has_deficient=False)
            if wait <= 0:
                wait = 1
            return DecisionResult(
                Intent("idle", context.current_location, duration_seconds=wait),
                None, reason,
            )

        winner = _max_by_products([(lbl, d, s) for lbl, d, s, _ in candidates])
        lbl = winner[0]

        if lbl == "satiete":
            return self._act_single(context, "eat", "satiete", idle_floor, has_deficient)
        if lbl == "hygiene":
            return self._act_single(context, "clean", "hygiene", idle_floor, has_deficient)
        return self._act_pair(context, defs, se, idle_floor, has_deficient)

    def _idle_wait(self, ctx, idle_floor, has_deficient) -> tuple[int, str]:
        """Première seconde (>0, ≤ MAX_IDLE) où la décision changerait.

        - aucun besoin déficient : premier franchissement d'un seuil d'intervention ;
        - besoin déficient toléré : premier dépassement du palier d'urgence ;
        - repos/énergie : franchissement critique pris en compte.
        - sinon : plafond de sécurité (idle_safety_boundary).
        """
        def _first(k, pred) -> int | None:
            num = ctx.rates[k]
            v0 = ctx.needs[k]
            r0 = ctx.need_remainders[k]
            s = ctx.effective_thresholds[k]
            f = lambda dt: pred(_derive_seconds(v0, r0, dt, num, DEN)[0], s)
            return _first_true(0, MAX_IDLE, f)

        his: list[int] = []
        if has_deficient:
            for k in CAND_ORDER:
                if ctx.needs[k] < ctx.effective_thresholds[k]:
                    d = _first(k, lambda v, s: (s - v) * 1000 // s > idle_floor)
                    if d is not None:
                        his.append(d)
        else:
            for k in CAND_ORDER:
                d = _first(k, lambda v, s: v < s)
                if d is not None:
                    his.append(d)
        # franchissement critique (hard wake)
        for k, crit in (("repos", CRIT_REPOS), ("energie", CRIT_ENERGIE)):
            d = _first(k, lambda v, s, c=crit: v < c)
            if d is not None:
                his.append(d)

        if his:
            wait = min(his)
            if 0 < wait < MAX_IDLE:
                return wait, ("no_need" if not has_deficient else "idle_floor")
        return MAX_IDLE, "idle_safety_boundary"

    def _act_single(self, ctx, activity, need_key, idle_floor, has_deficient) -> DecisionResult:
        v, s = ctx.needs[need_key], ctx.effective_thresholds[need_key]
        u = _urgency(s - v, s)
        if u <= idle_floor:
            wait, reason = self._idle_wait(ctx, idle_floor, has_deficient)
            if wait > 0:
                return DecisionResult(
                    Intent("idle", ctx.current_location, duration_seconds=wait),
                    need_key, reason,
                )
            # aucune attente : agir immédiatement
        return self._result(ctx, activity, need_key, None)

    def _act_pair(self, ctx, defs, se, idle_floor, has_deficient) -> DecisionResult:
        u_repos = _urgency(defs["repos"] or 0, se["repos"])
        u_energie = _urgency(defs["energie"] or 0, se["energie"])
        pair_urgency = max(u_repos, u_energie)
        trigger = "energie" if u_energie >= u_repos else "repos"

        if pair_urgency <= idle_floor:
            wait, reason = self._idle_wait(ctx, idle_floor, has_deficient)
            if wait > 0:
                return DecisionResult(
                    Intent("idle", ctx.current_location, duration_seconds=wait),
                    trigger, reason,
                )

        # Règle naturelle : repos déficient ⇒ sleep ; énergie seule modérée ⇒ rest.
        if defs["repos"] is not None:
            return self._result(ctx, "sleep", "repos", None)
        # seule energy déficiente (repos acceptable) → rest
        return self._result(ctx, "rest", "energie", None)

    def _rest_rep(self, defs, se):
        dr, de = defs["repos"], defs["energie"]
        if dr is None and de is None:
            return None
        if dr is None:
            return (de, se["energie"])
        if de is None:
            return (dr, se["repos"])
        lbl, d, s = _max_by_products(
            [("repos", dr, se["repos"]), ("energie", de, se["energie"])]
        )
        return (d, s)

    def _result(self, ctx, activity, trigger, reason_code) -> DecisionResult:
        if activity == "idle":
            raise RuntimeError("idle passes par _idle_wait, pas par _result")
        dests = ctx.accessible.get(activity)
        if not dests:
            intent = Intent("idle", ctx.current_location, duration_seconds=1)
            return DecisionResult(intent, trigger, "no_accessible_destination")
        min_dist = min(dests.values())
        dest = min((k for k, d in dests.items() if d == min_dist), key=lambda k: k)
        return DecisionResult(Intent(activity, dest), trigger, reason_code)
