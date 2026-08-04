"""Tests du Sous-lot 3.3B2 — effets mécaniques des blessures.

Couvre la classification (light/moderate/severe), la surcharge énergétique de
déplacement (500/arête), le blocage sévère du mouvement autonome, la frontière
exacte severe→moderate, l'atomicité des refus et la reproductibilité.

Aucune colonne REAL, calculs entiers /36, lecture pure sans écriture.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest

from vivarium.activities import ActivityEngine, ActivityError, recovery_regime
from vivarium.character import CharacterEngine, CharacterError
from vivarium.db import connect_database
from vivarium.injury import (
    DEN,
    MOVEMENT_SURCHARGE_MILLI,
    InjuryEngine,
    InjuryError,
    level,
    seconds_to_level,
)
from vivarium.migrations import ensure_schema
from vivarium.policy import DeterministicPolicy, PolicyContext
from vivarium.simulation import SimulationEngine
from vivarium.util import to_iso
from vivarium.world import WorldEngine

T0 = datetime(2026, 8, 1, 8, 0, 0, tzinfo=timezone.utc)


class FakeClock:
    def __init__(self, start=T0):
        self._now = start

    def now(self):
        return self._now

    def now_iso(self):
        return to_iso(self.now())

    def advance(self, **kw):
        self._now = self._now + timedelta(**kw)


def _fresh():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    wid = WorldEngine(conn, clock=clock).init_world(name="InjFx")["id"]
    return conn, clock, wid


def _events(conn, wid):
    rows = conn.execute(
        "SELECT seq, event_type, source_kind, payload FROM canonical_event "
        "WHERE world_id = ? ORDER BY seq", (wid,)
    ).fetchall()
    return [(r["event_type"], r["source_kind"], json.loads(r["payload"])) for r in rows]


def _moved_payloads(conn, wid):
    return [p for e, _s, p in _events(conn, wid) if e == "character_moved"]


def _energy(conn, wid, char):
    row = conn.execute(
        "SELECT ns.value_milli, ns.rate_remainder, ns.anchor_at "
        "FROM need_state ns JOIN character ch ON ch.id = ns.character_id "
        "WHERE ns.world_id = ? AND ch.key = ? AND ns.need_key = 'energie'",
        (wid, char),
    ).fetchone()
    return dict(row)


def _location(conn, wid, char):
    row = conn.execute(
        "SELECT l.key FROM character ch JOIN location l ON l.id = ch.current_location_id "
        "WHERE ch.world_id = ? AND ch.key = ?", (wid, char)
    ).fetchone()
    return row["key"]


def _set_energy(conn, wid, char, value, rem=0):
    conn.execute(
        "UPDATE need_state SET value_milli = ?, rate_remainder = ?, anchor_at = ? "
        "WHERE world_id = ? AND character_id = "
        "(SELECT id FROM character WHERE world_id = ? AND key = ?) AND need_key = 'energie'",
        (value, rem, to_iso(T0), wid, wid, char),
    )


# --- Classification et fonctions pures ---------------------------------------

def test_classification_seuils_exacts():
    assert level(30000) == "light"
    assert level(30001) == "moderate"
    assert level(60000) == "moderate"
    assert level(60001) == "severe"
    assert level(100000) == "severe"


def test_seconds_to_level_et_guerison():
    # severe→moderate : 60060 → 60000 sous sleep 12/36 = 180 s
    assert seconds_to_level(60060, 0, 60000, 12, 36) == 180
    # déjà modéré
    assert seconds_to_level(60000, 0, 60000, 12, 36) == 0
    # taux nul → aucune frontière
    assert seconds_to_level(70000, 0, 60000, 0, 36) is None
    # équivalent à seconds_to_heal pour target=0
    assert seconds_to_level(3000, 0, 0, 2, 36) == 54000


def test_recovery_regime():
    assert recovery_regime("sleep") == "sleep"
    assert recovery_regime("rest") == "rest"
    assert recovery_regime("eat") == "passive"
    assert recovery_regime("idle") == "passive"


# --- Blessure légère : identique à l'absence de blessure ---------------------

def test_legere_identique_absence_blessure():
    conn, clock, wid = _fresh()
    ce = CharacterEngine(conn, clock=clock)
    ie = InjuryEngine(conn, clock=clock)
    ce.move_character(wid, "character_1", "couloir")
    ce.move_character(wid, "character_1", "salon")
    before_energy = _energy(conn, wid, "character_1")["value_milli"]
    ie.inflict_injury(wid, "character_1", 3000)  # light
    ce.move_character(wid, "character_1", "cuisine")
    assert _location(conn, wid, "character_1") == "cuisine"
    assert _energy(conn, wid, "character_1")["value_milli"] == before_energy  # aucun coût
    last = _moved_payloads(conn, wid)[-1]
    assert last["injury_energy_surcharge"] == 0
    assert last["injury_effect_level"] == "light"
    assert last["total_energy_cost"] == 0


# --- Blessure modérée : surcharge de déplacement -----------------------------

def test_modere_une_arete_surcharge_500():
    conn, clock, wid = _fresh()
    ce = CharacterEngine(conn, clock=clock)
    ie = InjuryEngine(conn, clock=clock)
    ce.move_character(wid, "character_1", "couloir")
    ce.move_character(wid, "character_1", "salon")
    ie.inflict_injury(wid, "character_1", 40000)  # moderate
    before = _energy(conn, wid, "character_1")["value_milli"]
    ce.move_character(wid, "character_1", "cuisine")
    assert _location(conn, wid, "character_1") == "cuisine"
    assert _energy(conn, wid, "character_1")["value_milli"] == before - 500
    last = _moved_payloads(conn, wid)[-1]
    assert last["injury_energy_surcharge"] == 500
    assert last["total_energy_cost"] == 500
    assert last["edge_count"] == 1
    assert last["injury_effect_level"] == "moderate"
    assert last["base_energy_cost"] == 0


def test_modere_chemin_atomique_start_activity():
    # chemin salon→couloir→salle_de_bain (2 arêtes) : surcharge totale 1000
    conn, clock, wid = _fresh()
    ce = CharacterEngine(conn, clock=clock)
    ae = ActivityEngine(conn, clock=clock)
    ie = InjuryEngine(conn, clock=clock)
    ce.move_character(wid, "character_1", "couloir")
    ce.move_character(wid, "character_1", "salon")
    ie.inflict_injury(wid, "character_1", 40000)
    _set_energy(conn, wid, "character_1", 2000)
    ae.start_activity(wid, "character_1", "clean", "salle_de_bain", sim_now=to_iso(T0))
    assert _location(conn, wid, "character_1") == "salle_de_bain"
    assert _energy(conn, wid, "character_1")["value_milli"] == 1000
    moved = _moved_payloads(conn, wid)[-2:]  # les deux arêtes du chemin atomique
    assert len(moved) == 2
    assert all(m["injury_energy_surcharge"] == 500 for m in moved)


def test_modere_energie_insuffisante_chemin_atomique_rollback():
    # énergie 800 < 1000 pour 2 arêtes : refus atomique, aucun déplacement partiel
    conn, clock, wid = _fresh()
    ce = CharacterEngine(conn, clock=clock)
    ae = ActivityEngine(conn, clock=clock)
    ie = InjuryEngine(conn, clock=clock)
    ce.move_character(wid, "character_1", "couloir")
    ce.move_character(wid, "character_1", "salon")
    ie.inflict_injury(wid, "character_1", 40000)
    _set_energy(conn, wid, "character_1", 800)
    before = len(_events(conn, wid))
    injury_before = dict(conn.execute(
        "SELECT severity_milli, rate_remainder, recovery_anchor_at, status "
        "FROM injury WHERE world_id = ?", (wid,)
    ).fetchone())
    # prévalidation du coût total avant le premier déplacement → ActivityError
    with pytest.raises(ActivityError):
        ae.start_activity(wid, "character_1", "clean", "salle_de_bain", sim_now=to_iso(T0))
    # position inchangée, énergie inchangée, blessure persistante inchangée,
    # journal canonique inchangé (rollback complet)
    assert _location(conn, wid, "character_1") == "salon"
    assert _energy(conn, wid, "character_1")["value_milli"] == 800
    injury_after = dict(conn.execute(
        "SELECT severity_milli, rate_remainder, recovery_anchor_at, status "
        "FROM injury WHERE world_id = ?", (wid,)
    ).fetchone())
    assert injury_after == injury_before
    assert len(_events(conn, wid)) == before


def test_modere_energie_exactement_egale_au_cout():
    conn, clock, wid = _fresh()
    ce = CharacterEngine(conn, clock=clock)
    ie = InjuryEngine(conn, clock=clock)
    ce.move_character(wid, "character_1", "couloir")
    ce.move_character(wid, "character_1", "salon")
    ie.inflict_injury(wid, "character_1", 40000)
    _set_energy(conn, wid, "character_1", 500)
    ce.move_character(wid, "character_1", "cuisine")
    assert _location(conn, wid, "character_1") == "cuisine"
    assert _energy(conn, wid, "character_1")["value_milli"] == 0  # borne basse autorisée


def test_modere_energie_insuffisante_refus_atomique():
    conn, clock, wid = _fresh()
    ce = CharacterEngine(conn, clock=clock)
    ie = InjuryEngine(conn, clock=clock)
    ce.move_character(wid, "character_1", "couloir")
    ce.move_character(wid, "character_1", "salon")
    ie.inflict_injury(wid, "character_1", 40000)
    _set_energy(conn, wid, "character_1", 499)
    before = len(_events(conn, wid))
    with pytest.raises(CharacterError):
        ce.move_character(wid, "character_1", "cuisine")
    assert _location(conn, wid, "character_1") == "salon"
    assert _energy(conn, wid, "character_1")["value_milli"] == 499
    assert len(_events(conn, wid)) == before  # aucun faux événement


def test_modere_refus_repeté_aucun_debit_differe():
    conn, clock, wid = _fresh()
    ce = CharacterEngine(conn, clock=clock)
    ie = InjuryEngine(conn, clock=clock)
    ce.move_character(wid, "character_1", "couloir")
    ce.move_character(wid, "character_1", "salon")
    ie.inflict_injury(wid, "character_1", 40000)
    _set_energy(conn, wid, "character_1", 499)
    before = len(_events(conn, wid))
    for _ in range(2):
        with pytest.raises(CharacterError):
            ce.move_character(wid, "character_1", "cuisine")
    assert _energy(conn, wid, "character_1")["value_milli"] == 499
    assert len(_events(conn, wid)) == before


# --- Blessure sévère : blocage du mouvement autonome -------------------------

def _severe_context(conn, clock, wid, char, severity=70000, location=None):
    ce = CharacterEngine(conn, clock=clock)
    if location is not None:
        # déplace le personnage vers le lieu voulu (sans blessure)
        cur = _location(conn, wid, char)
        if cur != location:
            from vivarium.spatial import GraphEngine
            path = GraphEngine(conn).find_path(wid, cur, location)
            for step in path[1:]:
                ce.move_character(wid, char, step)
    InjuryEngine(conn, clock=clock).inflict_injury(wid, char, severity)
    se = SimulationEngine(conn, clock=clock)
    ctx = se._context(wid, char, to_iso(T0))
    return se, ctx


def test_severe_politique_aucun_mouvement():
    conn, clock, wid = _fresh()
    se, ctx = _severe_context(conn, clock, wid, "character_1", location="salon")
    dec = se._policy.decide(ctx)
    # aucune destination distante dans le contexte
    for atype, dests in ctx.accessible.items():
        if atype == "idle":
            continue
        assert all(d == 0 for d in dests.values())
    # l'intention ne demande jamais un déplacement (distance > 0)
    if dec.intent.activity_type != "idle":
        assert ctx.accessible[dec.intent.activity_type][dec.intent.target_location_key] == 0


def test_severe_cuisine_eat_local():
    conn, clock, wid = _fresh()
    se, ctx = _severe_context(conn, clock, wid, "character_1", location="cuisine")
    # satiete déficiente pour forcer eat
    ctx = PolicyContext(
        character_key=ctx.character_key, needs=dict(ctx.needs, satiete=10000),
        need_remainders=ctx.need_remainders,
        effective_thresholds=ctx.effective_thresholds,
        current_location=ctx.current_location, profile=ctx.profile, rates=ctx.rates,
        accessible=ctx.accessible, injury_level=ctx.injury_level,
        recovery_boundary_seconds=ctx.recovery_boundary_seconds,
    )
    dec = se._policy.decide(ctx)
    assert dec.intent.activity_type == "eat"
    assert dec.intent.target_location_key == "cuisine"
    assert ctx.accessible["eat"]["cuisine"] == 0  # aucun déplacement


def test_severe_chambre_sleep_rest_local():
    conn, clock, wid = _fresh()
    se, ctx = _severe_context(conn, clock, wid, "character_1", location="chambre_1")
    ctx = PolicyContext(
        character_key=ctx.character_key, needs=dict(ctx.needs, repos=10000),
        need_remainders=ctx.need_remainders,
        effective_thresholds=ctx.effective_thresholds,
        current_location=ctx.current_location, profile=ctx.profile, rates=ctx.rates,
        accessible=ctx.accessible, injury_level=ctx.injury_level,
        recovery_boundary_seconds=ctx.recovery_boundary_seconds,
    )
    dec = se._policy.decide(ctx)
    assert dec.intent.activity_type in ("sleep", "rest")
    assert ctx.accessible[dec.intent.activity_type][dec.intent.target_location_key] == 0


def test_severe_cour_idle_dynamique():
    conn, clock, wid = _fresh()
    se, ctx = _severe_context(conn, clock, wid, "character_1", location="cour")
    dec = se._policy.decide(ctx)
    assert dec.intent.activity_type == "idle"
    assert dec.intent.duration_seconds > 1  # pas un idle d'une seconde


def test_severe_deplacement_direct_refuse():
    conn, clock, wid = _fresh()
    ce = CharacterEngine(conn, clock=clock)
    ie = InjuryEngine(conn, clock=clock)
    ce.move_character(wid, "character_1", "couloir")
    ce.move_character(wid, "character_1", "salon")
    ie.inflict_injury(wid, "character_1", 70000)
    before = len(_events(conn, wid))
    with pytest.raises(CharacterError):
        ce.move_character(wid, "character_1", "cuisine")
    assert _location(conn, wid, "character_1") == "salon"
    assert len(_events(conn, wid)) == before  # matérialisation annulée par rollback


def test_severe_activite_locale_demarrable():
    # une activité locale (eat à la cuisine, déjà sur place) reste possible
    conn, clock, wid = _fresh()
    ce = CharacterEngine(conn, clock=clock)
    ae = ActivityEngine(conn, clock=clock)
    ie = InjuryEngine(conn, clock=clock)
    ce.move_character(wid, "character_1", "couloir")
    ce.move_character(wid, "character_1", "salon")
    ce.move_character(wid, "character_1", "cuisine")
    ie.inflict_injury(wid, "character_1", 70000)
    sheet = ae.start_activity(wid, "character_1", "eat", "cuisine", sim_now=to_iso(T0))
    assert sheet["type"] == "eat"
    assert _location(conn, wid, "character_1") == "cuisine"


# --- Frontière exacte severe → moderate --------------------------------------

def test_severe_moderate_croisement_exact():
    conn, clock, wid = _fresh()
    ie = InjuryEngine(conn, clock=clock)
    # 60060, sleep 12/36 → croisement à 180 s
    ie.inflict_injury(wid, "character_1", 60060)
    clock.advance(seconds=180)
    ie.materialize_injury(wid, "character_1", clock.now_iso(), "sleep")
    sheet = ie.injury_sheet(wid, "character_1")
    assert sheet["severity_milli"] == 60000
    assert sheet["level"] == "moderate"


def test_severe_politique_reveillee_a_la_frontiere():
    # un personnage sévère sans activité utile voit son idle borné à la frontière
    conn, clock, wid = _fresh()
    ie = InjuryEngine(conn, clock=clock)
    ie.inflict_injury(wid, "character_1", 60060)
    se = SimulationEngine(conn, clock=clock)
    ctx = se._context(wid, "character_1", to_iso(T0))
    assert ctx.injury_level == "severe"
    # régime passif (aucune activité) : 60060 → 60000 sous 2/36
    assert ctx.recovery_boundary_seconds == 1080
    dec = se._policy.decide(ctx)
    assert dec.intent.activity_type == "idle"
    assert dec.intent.duration_seconds == 1080  # réveil exact au croisement


# --- Récupération / régimes / invariants -------------------------------------

def test_changement_regime_une_seule_materialisation():
    conn, clock, wid = _fresh()
    ae = ActivityEngine(conn, clock=clock)
    ce = CharacterEngine(conn, clock=clock)
    ie = InjuryEngine(conn, clock=clock)
    ce.move_character(wid, "character_1", "couloir")
    ce.move_character(wid, "character_1", "salon")
    ie.inflict_injury(wid, "character_1", 40000)
    clock.advance(seconds=3600)  # récupération passive avant le sommeil
    # démarre un sleep à la chambre (déplacement salon→couloir→chambre_1)
    ae.start_activity(wid, "character_1", "sleep", "chambre_1", sim_now=clock.now_iso())
    mats = [p for e, _s, p in _events(conn, wid) if e == "injury_materialized"]
    # une seule matérialisation à la transition (ancien régime passif), pas de
    # second événement à durée zéro
    assert len(mats) == 1
    assert mats[0]["regime"] == "passive"


def test_lecture_repetee_aucune_ecriture():
    conn, clock, wid = _fresh()
    ie = InjuryEngine(conn, clock=clock)
    ie.inflict_injury(wid, "character_1", 40000)
    before = len(_events(conn, wid))
    for _ in range(10):
        ie.injury_sheet(wid, "character_1")
        ie.list_injuries(wid, "character_1")
    assert len(_events(conn, wid)) == before


def test_pause_aucun_progres_blessure():
    conn, clock, wid = _fresh()
    world = WorldEngine(conn, clock=clock)
    ie = InjuryEngine(conn, clock=clock)
    ie.inflict_injury(wid, "character_1", 40000)
    world.pause_world(wid)
    clock.advance(hours=5)
    before = len(_events(conn, wid))
    ie.materialize_injury(wid, "character_1", to_iso(T0), "passive")  # no-op
    assert len(_events(conn, wid)) == before
    assert ie.injury_sheet(wid, "character_1")["severity_milli"] == 40000


def test_redemarrage_milieu_recuperation():
    import tempfile, os
    from vivarium.db import connect_database
    d = tempfile.mkdtemp()
    path = os.path.join(d, "w.db")
    conn = connect_database(path)
    ensure_schema(conn)
    clock = FakeClock()
    wid = WorldEngine(conn, clock=clock).init_world(name="Restart")["id"]
    ie = InjuryEngine(conn, clock=clock)
    ie.inflict_injury(wid, "character_1", 40000)
    clock.advance(seconds=3600)
    ie.materialize_injury(wid, "character_1", clock.now_iso(), "passive")
    sev1 = ie.injury_sheet(wid, "character_1")["severity_milli"]
    conn.close()

    conn2 = connect_database(path)
    ensure_schema(conn2)
    # horloge reconstruite à l'heure simulée persistée (l'ancre de la blessure)
    clock2 = FakeClock(start=T0 + timedelta(seconds=3600))
    ie2 = InjuryEngine(conn2, clock=clock2)
    assert ie2.injury_sheet(wid, "character_1")["severity_milli"] == sev1
    conn2.close()


def test_simulation_acceleree_reproductible():
    def run():
        conn, clock, wid = _fresh()
        ie = InjuryEngine(conn, clock=clock)
        for char in ("character_1", "character_2", "character_3", "character_4"):
            ie.inflict_injury(wid, char, 40000)
        rep = SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + timedelta(hours=24)))
        j = [e for e, _s, _p in _events(conn, wid)]
        conn.close()
        return j, rep.transitions

    j1, t1 = run()
    j2, t2 = run()
    assert j1 == j2
    assert t1 == t2


def test_aucune_colonne_REAL_injury():
    conn, _clock, wid = _fresh()
    types = [r["type"].upper() for r in conn.execute("PRAGMA table_info(injury)")]
    assert "REAL" not in types
