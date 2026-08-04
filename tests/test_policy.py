"""Tests de la politique de décision déterministe (3.2C + extensions 3.3A).

3.3A :
- `Intent.duration_seconds` est obligatoire pour `idle` et strictement positif ;
- l'attente `idle` a une **durée dynamique** : première seconde où la décision
  changerait (franchissement d'un seuil / palier d'urgence / critique), sinon
  plafond de sécurité `MAX_IDLE` ;
- règle de sommeil naturelle : repos déficient ⇒ sleep ; seule énergie modérée
  ⇒ rest ; critique ⇒ sleep. `rest_preference` ne peut jamais annuler un
  sommeil exigé.
"""

from datetime import datetime, timedelta, timezone

import pytest

from vivarium.policy import (
    CRIT_ENERGIE,
    CRIT_REPOS,
    MAX_IDLE,
    DecisionResult,
    DeterministicPolicy,
    Intent,
    PolicyContext,
    _first_true,
    _derive_seconds,
)

# seuils effectifs neutres (profil 1000)
SEUILS = {"satiete": 35000, "repos": 35000, "energie": 30000, "hygiene": 40000}
# taux passifs neutres /36 par seconde (SEED_NEEDS)
RATES = {"satiete": -80, "repos": -60, "energie": -50, "hygiene": -30}
NEUTRAL = {
    "satiete_threshold_mult_milli": 1000,
    "repos_threshold_mult_milli": 1000,
    "energie_threshold_mult_milli": 1000,
    "hygiene_threshold_mult_milli": 1000,
    "rest_preference_milli": 0,
    "idle_tolerance_milli": 0,
}
ACCESSIBLE = {
    "idle": {"couloir": 0},
    "eat": {"cuisine": 1},
    "clean": {"salle_de_bain": 2},
    "sleep": {"chambre_1": 0, "chambre_2": 3, "chambre_3": 2},
    "rest": {"salon": 1, "chambre_1": 0},
}


def _ctx(needs, profile=None, current="couloir", accessible=None,
         remainders=None, rates=None):
    return PolicyContext(
        character_key="character_1",
        needs=needs,
        need_remainders=remainders or {k: 0 for k in needs},
        effective_thresholds=SEUILS,
        current_location=current,
        profile=profile or NEUTRAL,
        rates=rates or RATES,
        accessible=accessible or ACCESSIBLE,
    )


def test_intent_et_decisionresult_separes():
    # Intent minimal (activité + destination, durée None par défaut) ;
    # DecisionResult porte l'explication séparée.
    d = DecisionResult(Intent("sleep", "chambre_1"), trigger_need="repos", reason_code="critical")
    assert d.intent.activity_type == "sleep"
    assert d.intent.target_location_key == "chambre_1"
    assert d.intent.duration_seconds is None
    assert d.trigger_need == "repos" and d.reason_code == "critical"


# --- Critiques ---------------------------------------------------------------

@pytest.mark.parametrize(
    "needsp,trigger",
    [
        ({"satiete": 90000, "repos": 18000, "energie": 90000, "hygiene": 90000}, "repos"),
        ({"satiete": 90000, "repos": 90000, "energie": 12000, "hygiene": 90000}, "energie"),
    ],
)
def test_critique_impose_sleep(needsp, trigger):
    d = DeterministicPolicy().decide(_ctx(needsp))
    assert d.intent.activity_type == "sleep"
    assert d.reason_code == "critical"
    assert d.trigger_need == trigger


def test_critique_impose_sleep_meme_avec_rest_pref_max():
    # rest_pref +1000 ne peut pas annuler une urgence critique
    prof = dict(NEUTRAL, rest_preference_milli=1000)
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 18000, "energie": 90000, "hygiene": 90000}, profile=prof
    ))
    assert d.intent.activity_type == "sleep"


def test_aucune_attente_quand_critique():
    # repos critique ⇒ sleep immédiat, jamais un idle
    ctx = _ctx({"satiete": 90000, "repos": 18000, "energie": 90000, "hygiene": 90000})
    d = DeterministicPolicy().decide(ctx)
    assert d.intent.activity_type == "sleep"
    # énergie critique ⇒ sleep immédiat
    d2 = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 90000, "energie": 12000, "hygiene": 90000}
    ))
    assert d2.intent.activity_type == "sleep"


# --- Règle de sommeil naturelle (3.3A) ---------------------------------------

def test_repos_deficient_seul_impose_sleep():
    # repos isolé modérément déficient (30000 < 35000), énergie ok → sleep
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 30000, "energie": 70000, "hygiene": 90000}
    ))
    assert d.intent.activity_type == "sleep"


def test_energie_seule_moderee_impose_rest():
    # énergie seule modérément déficiente (25000 < 30000), repos OK → rest
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 70000, "energie": 25000, "hygiene": 90000}
    ))
    assert d.intent.activity_type == "rest"


def test_deux_deficients_sommeil():
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 30000, "energie": 25000, "hygiene": 90000}
    ))
    assert d.intent.activity_type == "sleep"


def test_rest_pref_ne_peut_pas_annuler_repos():
    # repos déficient → sleep même avec rest_pref maximale positive
    prof = dict(NEUTRAL, rest_preference_milli=1000)
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 30000, "energie": 70000, "hygiene": 90000}, profile=prof
    ))
    assert d.intent.activity_type == "sleep"


def test_eat_quand_satiete_la_plus_urgente():
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 20000, "repos": 30000, "energie": 25000, "hygiene": 90000}
    ))
    assert d.intent.activity_type == "eat"


# --- Attente dynamique (3.3A) ------------------------------------------------

def test_aucun_besoin_deficient_choisit_idle_avec_duree():
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 90000, "energie": 90000, "hygiene": 90000}
    ))
    assert d.intent.activity_type == "idle"
    assert d.intent.target_location_key == "couloir"
    assert d.intent.duration_seconds is not None
    assert 0 < d.intent.duration_seconds <= MAX_IDLE


def test_idle_une_seule_longue_attente_pas_de_microcycles():
    # pas de déficits : une seule attente jusqu'au premier franchissement de seuil
    ctx = _ctx({"satiete": 90000, "repos": 90000, "energie": 90000, "hygiene": 90000})
    # le franchissement le plus proche est la satiété (taux -80)
    d = DeterministicPolicy().decide(ctx)
    assert d.intent.activity_type == "idle"
    assert d.intent.duration_seconds > 60  # substantiellement plus que 15 min

def test_idle_tolerance_faible_urgence():
    # besoin sous seuil mais urgence faible + tolérance élevée → idle
    prof = dict(NEUTRAL, idle_tolerance_milli=1000)  # idle_floor = 500
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 34000, "repos": 90000, "energie": 90000, "hygiene": 90000}, profile=prof
    ))
    # déficit satiete = 1000 ; urgency = 1000*1000//35000 = 28 <= 500 → idle
    assert d.intent.activity_type == "idle"
    assert d.intent.duration_seconds is not None and d.intent.duration_seconds > 0


def test_destination_courante_prioritaire():
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 30000, "energie": 25000, "hygiene": 90000},
        current="chambre_1",
    ))
    assert d.intent.activity_type == "sleep"
    assert d.intent.target_location_key == "chambre_1"


def test_destination_plus_courte_puis_cle_stable():
    ctx = _ctx(
        {"satiete": 90000, "repos": 30000, "energie": 25000, "hygiene": 90000},
        current="couloir",
        accessible={
            "idle": {"couloir": 0},
            "sleep": {"chambre_1": 1, "chambre_2": 1, "chambre_4": 2},
        },
    )
    d = DeterministicPolicy().decide(ctx)
    assert d.intent.activity_type == "sleep"
    assert d.intent.target_location_key == "chambre_1"  # + courte, égalité par clé


def test_no_accessible_destination_repli_idle():
    ctx = _ctx(
        {"satiete": 20000, "repos": 90000, "energie": 90000, "hygiene": 90000},
        accessible={"idle": {"couloir": 0}},  # aucune destination eat accessible
    )
    d = DeterministicPolicy().decide(ctx)
    assert d.intent.activity_type == "idle"
    assert d.reason_code == "no_accessible_destination"
    assert d.intent.duration_seconds == 1


# --- Exactitude à la seconde (3.3A) -------------------------------------------

def test_first_true_borne_avance_seconde():
    # f vrai seulement à partir de dt=3 (borne franchie à la 3e seconde)
    f = lambda dt: dt >= 3
    assert _first_true(0, 10, f) == 3


def test_first_true_vrai_des_le_debut():
    assert _first_true(0, 10, lambda dt: dt >= 0) == 0


def test_first_true_jamais_vrai():
    assert _first_true(0, 10, lambda dt: False) is None


def test_derive_seconds_est_identique_a_needs_derive():
    from vivarium.needs import derive
    from vivarium.util import parse_iso, to_iso
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    dt = 12345
    v, r = _derive_seconds(70000, 0, dt, -80, 36)
    nv, nr = derive(70000, 0, to_iso(t0), to_iso(t0 + timedelta(seconds=dt)), -80, 36)
    assert (v, r) == (nv, nr)


def test_exactitude_seconde_borne_egale_puis_seconde_suivante():
    # hygiène v=40001, taux -30, reste 0 : à dt=1 la valeur atteint EXACTEMENT le
    # seuil (40000) sans le franchir (comparaison stricte v < seuil) ; le
    # franchissement n'arrive qu'à la seconde suivante (dt=2 → 39999).
    ctx = _ctx({"satiete": 90000, "repos": 90000, "energie": 90000, "hygiene": 40001})
    wait, _ = DeterministicPolicy()._idle_wait(ctx, 100, has_deficient=False)
    assert wait == 2


def test_exactitude_seconde_reste_non_nul():
    # un reste rationnel non nul retarde le franchissement du seuil.
    # hygiène v=40001, taux -30, reste 35 :
    #   dt=1 → total=35-30=5, delta=0  → 40001
    #   dt=2 → total=35-60=-25, delta=-1 → 40000 (== seuil, non franchi)
    #   dt=3 → total=35-90=-55, delta=-2 → 39999 (< seuil) ⇒ franchi à dt=3
    ctx = _ctx(
        {"satiete": 90000, "repos": 90000, "energie": 90000, "hygiene": 40001},
        remainders={"satiete": 0, "repos": 0, "energie": 0, "hygiene": 35},
    )
    wait, _ = DeterministicPolicy()._idle_wait(ctx, 100, has_deficient=False)
    assert wait == 3


def test_derive_seconds_clamp_remet_reste_a_zero():
    # un clamp sur une borne remet le reste à zéro (aucune fraction ne ressurgit)
    v, r = _derive_seconds(0, 35, 1, -80, 36)  # total=35-80=-45 → delta=-2 → -2 < 0
    assert (v, r) == (0, 0)  # clamp bas + reste remis à 0
    v2, r2 = _derive_seconds(100000, 0, 1, 50, 36)  # total=50, delta=1 → 100001
    assert (v2, r2) == (100000, 0)  # clamp haut + reste remis à 0


def test_context_detache_de_la_base():
    # la politique n'a aucun connexion ni capacité de requête : rien ne peut écrire
    ctx = _ctx({"satiete": 20000, "repos": 90000, "energie": 90000, "hygiene": 90000})
    d = DeterministicPolicy().decide(ctx)
    assert isinstance(d, DecisionResult)
    assert isinstance(d.intent, Intent)
