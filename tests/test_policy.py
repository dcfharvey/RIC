"""Tests de la politique de décision déterministe (Sous-lot 3.2C)."""

import pytest

from vivarium.policy import (
    CRIT_ENERGIE,
    CRIT_REPOS,
    DecisionResult,
    DeterministicPolicy,
    Intent,
    PolicyContext,
)

# seuils effectifs neutres (profil 1000)
SEUILS = {"satiete": 35000, "repos": 35000, "energie": 30000, "hygiene": 40000}
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


def _ctx(needs, profile=None, current="couloir", accessible=None):
    return PolicyContext(
        character_key="character_1",
        needs=needs,
        effective_thresholds=SEUILS,
        current_location=current,
        profile=profile or NEUTRAL,
        accessible=accessible or ACCESSIBLE,
    )


def test_intent_et_decisionresult_separes():
    # Intent minimal (activité + destination) ; DecisionResult porte l'explication.
    d = DecisionResult(Intent("sleep", "chambre_1"), trigger_need="repos", reason_code="critical")
    assert d.intent.activity_type == "sleep"
    assert d.intent.target_location_key == "chambre_1"
    assert d.trigger_need == "repos" and d.reason_code == "critical"


@pytest.mark.parametrize(
    "needsp,expected",
    [
        ({"satiete": 90000, "repos": 18000, "energie": 90000, "hygiene": 90000}, "sleep"),  # repos critique
        ({"satiete": 90000, "repos": 90000, "energie": 12000, "hygiene": 90000}, "sleep"),  # energie critique
    ],
)
def test_critique_impose_sleep(needsp, expected):
    d = DeterministicPolicy().decide(_ctx(needsp))
    assert d.intent.activity_type == expected
    assert d.reason_code == "critical"


def test_critique_impose_sleep_meme_avec_rest_pref_max():
    # rest_pref +1000 ne peut pas annuler une urgence critique
    prof = dict(NEUTRAL, rest_preference_milli=1000)
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 18000, "energie": 90000, "hygiene": 90000}, profile=prof
    ))
    assert d.intent.activity_type == "sleep"


def test_deficit_modere_isoole_rest():
    # repos seul modérément déficient (30000 < 35000), énergie ok → rest
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 30000, "energie": 70000, "hygiene": 90000}
    ))
    assert d.intent.activity_type == "rest"
    # énergie seule modérément déficiente (25000 < 30000), repos ok → rest
    d2 = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 70000, "energie": 25000, "hygiene": 90000}
    ))
    assert d2.intent.activity_type == "rest"


def test_deux_deficients_sommeil_par_defaut():
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 30000, "energie": 25000, "hygiene": 90000}
    ))
    assert d.intent.activity_type == "sleep"


def test_rest_pref_positive_graduee_deux_deficients_moderes():
    # amplitude faible : pas assez pour basculer vers rest
    lo = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 30000, "energie": 25000, "hygiene": 90000},
        profile=dict(NEUTRAL, rest_preference_milli=50),
    ))
    assert lo.intent.activity_type == "sleep"
    # amplitude suffisante (+1000) et urgence modérée → rest
    hi = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 30000, "energie": 25000, "hygiene": 90000},
        profile=dict(NEUTRAL, rest_preference_milli=1000),
    ))
    assert hi.intent.activity_type == "rest"


def test_rest_pref_negative_graduee_isoole_modere():
    # isolé modéré → rest par défaut ; préférence négative forte → sleep
    base = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 30000, "energie": 70000, "hygiene": 90000}
    ))
    assert base.intent.activity_type == "rest"
    neg = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 30000, "energie": 70000, "hygiene": 90000},
        profile=dict(NEUTRAL, rest_preference_milli=-1000),
    ))
    assert neg.intent.activity_type == "sleep"


def test_eat_quand_satiete_la_plus_urgente():
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 20000, "repos": 30000, "energie": 25000, "hygiene": 90000}
    ))
    assert d.intent.activity_type == "eat"


def test_aucun_besoin_deficient_choisit_idle():
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 90000, "energie": 90000, "hygiene": 90000}
    ))
    assert d.intent.activity_type == "idle"
    assert d.intent.target_location_key == "couloir"


def test_destination_courante_prioritaire():
    # character dans chambre_1, sleep autorisé à chambre_1 (0 arête) vs chambre_3 (2)
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 90000, "repos": 30000, "energie": 25000, "hygiene": 90000},
        current="chambre_1",
    ))
    assert d.intent.activity_type == "sleep"
    assert d.intent.target_location_key == "chambre_1"


def test_destination_plus_courte_puis_cle_stable():
    # pas dans une chambre → choisir le trajet le plus court, départage par clé
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


def test_idle_tolerance_faible_urgence():
    # besoin sous seuil mais urgence faible + tolérance élevée → idle
    prof = dict(NEUTRAL, idle_tolerance_milli=1000)  # idle_floor = 500
    d = DeterministicPolicy().decide(_ctx(
        {"satiete": 34000, "repos": 90000, "energie": 90000, "hygiene": 90000}, profile=prof
    ))
    # déficit satiete = 1000 ; urgency = 1000*1000//35000 = 28 <= 500 → idle
    assert d.intent.activity_type == "idle"


def test_no_accessible_destination_repli_idle():
    ctx = _ctx(
        {"satiete": 20000, "repos": 90000, "energie": 90000, "hygiene": 90000},
        accessible={"idle": {"couloir": 0}},  # aucune destination eat accessible
    )
    d = DeterministicPolicy().decide(ctx)
    assert d.intent.activity_type == "idle"
    assert d.reason_code == "no_accessible_destination"


def test_context_detache_de_la_base():
    # la politique n'a aucun connexion ni capacité de requête : rien ne peut écrire
    ctx = _ctx({"satiete": 20000, "repos": 90000, "energie": 90000, "hygiene": 90000})
    d = DeterministicPolicy().decide(ctx)
    assert isinstance(d, DecisionResult)
    assert isinstance(d.intent, Intent)
