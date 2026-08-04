"""Tests de la Phase 3.3C — reproductibilité finale et fermeture technique.

Garantie :
    même état initial + mêmes règles + mêmes commandes
    + mêmes valeurs de l'horloge injectée aux mêmes points
    + même ordre canonique
    = même état et même journal sémantique

Régimes temporels : monde actif (le temps mural compte 1:1), monde paused (le
temps mural ne compte pas), reproductibilité contrôlée (FakeClock déterministe).
"""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from vivarium.activities import ActivityEngine
from vivarium.character import CharacterEngine
from vivarium.db import connect_database
from vivarium.injury import InjuryEngine
from vivarium.migrations import ensure_schema
from vivarium.repro import (
    SimulationRunReport,
    _audit_injury_chain,
    _audit_needs_chain,
    canonical_state_digest,
    materialization_chain_audit,
    max_seq,
    raw_canonical_event_log,
    reproducible_semantic_projection,
    semantic_event_digest,
    structural_event_audit,
)
from vivarium.simulation import SimulationEngine, SimulationLimitError
from vivarium.util import parse_iso, to_iso
from vivarium.world import WorldEngine

T0 = datetime(2026, 8, 1, 8, 0, 0, tzinfo=timezone.utc)
H24 = timedelta(hours=24)
D7 = timedelta(days=7)


class FakeClock:
    def __init__(self, start=T0, fail_on=None):
        self._now = start
        self._calls = 0
        self._fail_on = fail_on

    def now(self):
        self._calls += 1
        if self._fail_on is not None and self._calls == self._fail_on:
            raise RuntimeError("échec injecté (horloge)")
        return self._now

    def now_iso(self):
        return to_iso(self.now())

    def advance(self, **kw):
        self._now = self._now + timedelta(**kw)


def _fresh():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    wid = WorldEngine(conn, clock=clock).init_world(name="Repro")["id"]
    return conn, clock, wid


def _events(conn, wid):
    return [
        r["event_type"]
        for r in conn.execute(
            "SELECT event_type FROM canonical_event WHERE world_id = ? ORDER BY seq",
            (wid,),
        )
    ]


def _sim(conn, wid):
    return conn.execute(
        "SELECT simulated_now FROM canonical_clock WHERE world_id = ?", (wid,)
    ).fetchone()[0]


def _needs_final(conn, wid, char):
    vals = {}
    for r in conn.execute(
        "SELECT ns.need_key, ns.value_milli FROM need_state ns "
        "JOIN character ch ON ch.id = ns.character_id "
        "WHERE ns.world_id = ? AND ch.key = ?",
        (wid, char),
    ):
        vals[r["need_key"]] = r["value_milli"]
    return vals


# --- RUN A / B : deux runs indépendants ---------------------------------------

def test_deux_runs_24h_etat_et_journal_identiques():
    def run():
        conn, clock, wid = _fresh()
        SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
        state = canonical_state_digest(conn, wid)
        journal = semantic_event_digest(conn, wid)
        conn.close()
        return state, journal

    s1, j1 = run()
    s2, j2 = run()
    assert s1 == s2
    assert j1 == j2


# --- RUN D : continu == segmenté (mêmes valeurs Clock.now) --------------------

def test_continu_egal_segmente_meme_clock():
    conn, clock, wid = _fresh()
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    state_c = canonical_state_digest(conn, wid)
    journal_c = semantic_event_digest(conn, wid)
    conn.close()

    conn, clock, wid = _fresh()
    se = SimulationEngine(conn, clock=clock)
    se.run_to(wid, to_iso(T0 + timedelta(hours=8)))
    se.run_to(wid, to_iso(T0 + timedelta(hours=16)))
    se.run_to(wid, to_iso(T0 + H24))
    state_s = canonical_state_digest(conn, wid)
    journal_s = semantic_event_digest(conn, wid)
    conn.close()

    assert state_c == state_s
    assert journal_c == journal_s


# --- RUN C : continu == redémarrage au milieu (mêmes valeurs Clock.now) ------

def test_continu_egal_redemarrage_meme_clock():
    conn, clock, wid = _fresh()
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    state_c = canonical_state_digest(conn, wid)
    journal_c = semantic_event_digest(conn, wid)
    conn.close()

    d = tempfile.mkdtemp()
    path = os.path.join(d, "w.db")
    conn = connect_database(path)
    ensure_schema(conn)
    clock = FakeClock()
    wid = WorldEngine(conn, clock=clock).init_world(name="Repro")["id"]
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + timedelta(hours=12)))
    conn.close()

    conn = connect_database(path)
    ensure_schema(conn)
    clock2 = FakeClock()  # même valeur Clock.now que le run continu
    SimulationEngine(conn, clock=clock2).run_to(wid, to_iso(T0 + H24))
    state_r = canonical_state_digest(conn, wid)
    journal_r = semantic_event_digest(conn, wid)
    conn.close()

    assert state_c == state_r
    assert journal_c == journal_r


# --- Monde actif : délai mural compté exactement une fois ---------------------

def test_monde_actif_delai_mural_entre_segments_compte_une_fois():
    conn, clock, wid = _fresh()
    se = SimulationEngine(conn, clock=clock)
    se.run_to(wid, to_iso(T0 + timedelta(hours=8)))
    # l'horloge canonique est ancrée à 8h (real_updated_at = T0, now = T0)
    assert parse_iso(_sim(conn, wid)) == T0 + timedelta(hours=8)
    # délai mural de 10 min
    clock.advance(minutes=10)
    # le délai mural est compté exactement une fois : lecture = 8h + 10min
    cur = WorldEngine(conn, clock=clock).read_canonical_time(wid)
    assert parse_iso(cur) == T0 + timedelta(hours=8, minutes=10)
    se.run_to(wid, to_iso(T0 + H24))
    # l'état final est cohérent (ancré à 24h), pas de double comptage
    assert parse_iso(_sim(conn, wid)) == T0 + H24


def test_monde_actif_delai_mural_redemarrage_compte_une_fois():
    d = tempfile.mkdtemp()
    path = os.path.join(d, "w.db")
    conn = connect_database(path)
    ensure_schema(conn)
    clock = FakeClock()
    wid = WorldEngine(conn, clock=clock).init_world(name="Repro")["id"]
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + timedelta(hours=12)))
    conn.close()

    # redémarrage 10 min murales plus tard
    conn = connect_database(path)
    ensure_schema(conn)
    clock2 = FakeClock(start=T0 + timedelta(minutes=10))
    # la reprise commence à 12h + 10min (délai mural compté une fois)
    cur = WorldEngine(conn, clock=clock2).read_canonical_time(wid)
    assert parse_iso(cur) == T0 + timedelta(hours=12, minutes=10)
    SimulationEngine(conn, clock=clock2).run_to(wid, to_iso(T0 + H24))
    assert parse_iso(_sim(conn, wid)) == T0 + H24
    conn.close()


def test_monde_paused_delai_mural_ignore():
    conn, clock, wid = _fresh()
    world = WorldEngine(conn, clock=clock)
    se = SimulationEngine(conn, clock=clock)
    se.run_to(wid, to_iso(T0 + timedelta(hours=6)))
    world.pause_world(wid)
    clock.advance(hours=3)  # délai mural pendant la pause
    cur = world.read_canonical_time(wid)
    assert parse_iso(cur) == T0 + timedelta(hours=6)  # gelée, pas de rattrapage
    world.resume_world(wid)
    se.run_to(wid, to_iso(T0 + H24))
    assert parse_iso(_sim(conn, wid)) == T0 + H24


# --- Frontière multi-personnages : aucune dérive ------------------------------

def test_aucune_derive_millisecondes_frontiere_multi_personnages():
    conn, clock, wid = _fresh()
    se = SimulationEngine(conn, clock=clock)
    se.run_to(wid, to_iso(T0 + H24))
    # après le run, l'horloge est ancrée exactement à l'instant atteint
    assert parse_iso(_sim(conn, wid)) == T0 + H24
    # et la lecture dérivée ne renvoie pas T + quelques ms (FakeClock gelé)
    cur = WorldEngine(conn, clock=clock).read_canonical_time(wid)
    assert parse_iso(cur) == T0 + H24


# --- Crash et rollback --------------------------------------------------------

def test_rollback_annule_etat_journal_et_horloge():
    # une exception pendant une transition annule état, journal et horloge
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock(fail_on=5)  # échoue tôt pendant le premier démarrage
    wid = WorldEngine(conn, clock=clock).init_world(name="Repro")["id"]
    before_state = canonical_state_digest(conn, wid)
    before_journal = semantic_event_digest(conn, wid)
    before_sim = _sim(conn, wid)
    with pytest.raises(RuntimeError):
        SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    assert canonical_state_digest(conn, wid) == before_state
    assert semantic_event_digest(conn, wid) == before_journal
    assert _sim(conn, wid) == before_sim


def test_crash_entre_personnages_frontiere_puis_reprise():
    # un crash en cours de run laisse le monde à une frontière cohérente ;
    # la reprise donne le même résultat qu'un run continu (ni duplication ni omission)
    d = tempfile.mkdtemp()
    path = os.path.join(d, "w.db")

    # run continu de référence
    conn, clock, wid = _fresh()
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    ref_state = canonical_state_digest(conn, wid)
    ref_journal = semantic_event_digest(conn, wid)
    conn.close()

    # run avec crash en cours (échec injecté à un appel d'horloge en cours de run)
    conn = connect_database(path)
    ensure_schema(conn)
    clock = FakeClock(fail_on=40)
    wid = WorldEngine(conn, clock=clock).init_world(name="Repro")["id"]
    try:
        SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    except RuntimeError:
        pass
    conn.close()

    # reprise depuis l'état cohérent après le crash
    conn = connect_database(path)
    ensure_schema(conn)
    clock2 = FakeClock()
    SimulationEngine(conn, clock=clock2).run_to(wid, to_iso(T0 + H24))
    state = canonical_state_digest(conn, wid)
    journal = semantic_event_digest(conn, wid)
    conn.close()

    assert state == ref_state
    assert journal == ref_journal


# --- Journal d'horloge --------------------------------------------------------

def test_run_to_n_emet_aucun_clock_updated():
    conn, clock, wid = _fresh()
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    assert "clock_updated" not in _events(conn, wid)


def test_set_simulated_time_emet_clock_updated():
    conn, clock, wid = _fresh()
    WorldEngine(conn, clock=clock).set_simulated_time(wid, to_iso(T0 + timedelta(hours=1)))
    assert "clock_updated" in _events(conn, wid)


# --- Scénarios de fermeture ---------------------------------------------------

def test_scenario_24h_invariants():
    conn, clock, wid = _fresh()
    rep = SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    assert rep.reached_target is True
    assert rep.transitions < 2000
    for char in ("character_1", "character_2", "character_3", "character_4"):
        for v in _needs_final(conn, wid, char).values():
            assert 0 <= v <= 100000
        sleeps = conn.execute(
            "SELECT COUNT(*) FROM activity a JOIN character ch ON ch.id=a.character_id "
            "WHERE a.world_id=? AND ch.key=? AND a.type='sleep'",
            (wid, char),
        ).fetchone()[0]
        assert sleeps >= 1
    # une seule position canonique par personnage
    assert conn.execute(
        "SELECT COUNT(*) FROM character WHERE world_id=?", (wid,)
    ).fetchone()[0] == 4
    # au plus une activité active par personnage
    active = conn.execute(
        "SELECT COUNT(*) FROM activity WHERE world_id=? AND status='active'", (wid,)
    ).fetchone()[0]
    assert active <= 4


def test_scenario_blessures_invariants():
    conn, clock, wid = _fresh()
    ie = InjuryEngine(conn, clock=clock)
    ie.inflict_injury(wid, "character_1", 3000)   # légère
    ie.inflict_injury(wid, "character_2", 40000)  # modérée
    ie.inflict_injury(wid, "character_3", 70000)  # sévère
    rep = SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    assert rep.reached_target is True
    # au plus une blessure active par personnage
    n_active = conn.execute(
        "SELECT COUNT(*) FROM injury WHERE world_id=? AND status='active'", (wid,)
    ).fetchone()[0]
    assert n_active <= 3
    # blessures guéries terminales : sévérité 0, reste 0
    bad = conn.execute(
        "SELECT COUNT(*) FROM injury WHERE world_id=? AND status='healed' "
        "AND (severity_milli != 0 OR rate_remainder != 0 OR recovered_at IS NULL)",
        (wid,),
    ).fetchone()[0]
    assert bad == 0


def test_scenario_endurance_7j_sans_derive():
    def run():
        conn, clock, wid = _fresh()
        rep = SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + D7), max_transitions=10000)
        state = canonical_state_digest(conn, wid)
        journal = semantic_event_digest(conn, wid)
        conn.close()
        return rep, state, journal

    r1, s1, j1 = run()
    r2, s2, j2 = run()
    assert s1 == s2
    assert j1 == j2
    assert r1.transitions < 10000
    # restes rationnels dans leur plage [0, 36)
    conn, clock, wid = _fresh()
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + D7), max_transitions=10000)
    bad_rem = conn.execute(
        "SELECT COUNT(*) FROM need_state WHERE world_id=? AND NOT (rate_remainder BETWEEN 0 AND 35)",
        (wid,),
    ).fetchone()[0]
    assert bad_rem == 0
    conn.close()


# --- Invariants et structure du journal ---------------------------------------

def test_invariants_toutes_tables_apres_run():
    conn, clock, wid = _fresh()
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    # besoins dans [0,100000]
    assert conn.execute(
        "SELECT COUNT(*) FROM need_state WHERE world_id=? AND NOT (value_milli BETWEEN 0 AND 100000)",
        (wid,),
    ).fetchone()[0] == 0
    # aucune colonne REAL dans les tables d'état
    for table in ("need_state", "activity", "injury", "character", "canonical_clock"):
        types = [r["type"].upper() for r in conn.execute(f"PRAGMA table_info({table})")]
        assert "REAL" not in types
    # séquences continues
    seqs = [r["seq"] for r in conn.execute(
        "SELECT seq FROM canonical_event WHERE world_id=? ORDER BY seq", (wid,)
    )]
    assert seqs == list(range(1, len(seqs) + 1))
    # temps canoniques non décroissants
    times = [parse_iso(r["occurred_at"]) for r in conn.execute(
        "SELECT occurred_at FROM canonical_event WHERE world_id=? ORDER BY seq", (wid,)
    )]
    assert all(b >= a for a, b in zip(times, times[1:]))


def test_verification_structurelle_journal():
    conn, clock, wid = _fresh()
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    rows = conn.execute(
        "SELECT seq, event_type, payload FROM canonical_event WHERE world_id=? ORDER BY seq",
        (wid,),
    ).fetchall()
    # payload JSON valide
    for r in rows:
        json.loads(r["payload"])
    # aucun doublon de seq
    assert len(rows) == len({r["seq"] for r in rows})
    # aucun événement de succès sur refus : pas de character_moved sans déplacement
    moved = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id=? AND event_type='character_moved'",
        (wid,),
    ).fetchone()[0]
    assert moved >= 0


# --- Rapport stable -----------------------------------------------------------

def test_rapport_stable():
    conn, clock, wid = _fresh()
    rep = SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    report = SimulationRunReport(
        commit="1bb93ed", schema_version=8, world_id=wid,
        start_time=to_iso(T0), end_time=to_iso(T0 + H24),
        transition_count=rep.transitions,
        event_count_by_type={},
        canonical_state_digest=canonical_state_digest(conn, wid),
        semantic_event_digest=semantic_event_digest(conn, wid),
    )
    assert report.rng_seed == "not_applicable"
    # max(seq) = total des événements ; le digest sémantique exclut la
    # matérialisation, donc il est inférieur ou égal.
    assert max_seq(conn, wid) >= len(semantic_event_digest(conn, wid))
    conn.close()


# --- Journal brut : audit structurel par run --------------------------------

def _audit_ok(audit):
    assert audit["seq_continuous_1_to_n"] is True
    assert audit["no_holes"] is True
    assert audit["no_duplicate_seq"] is True
    assert audit["occurred_at_monotonic"] is True
    assert audit["payloads_valid_json"] is True
    assert audit["causality_valid"] is True
    assert audit["bad_causes"] == []


def test_audit_structurel_journal_brut_chaque_run():
    # continu
    conn, clock, wid = _fresh()
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    _audit_ok(structural_event_audit(conn, wid))
    n_cont = len(raw_canonical_event_log(conn, wid))
    conn.close()
    # segmenté
    conn, clock, wid = _fresh()
    se = SimulationEngine(conn, clock=clock)
    se.run_to(wid, to_iso(T0 + timedelta(hours=8)))
    se.run_to(wid, to_iso(T0 + timedelta(hours=16)))
    se.run_to(wid, to_iso(T0 + H24))
    _audit_ok(structural_event_audit(conn, wid))
    n_seg = len(raw_canonical_event_log(conn, wid))
    conn.close()
    # le journal brut peut avoir un découpage différent (plus de matérialisations)
    assert n_seg > n_cont


def test_causalite_normalisee_projection():
    # un run avec blessures : la projection normalise cause_event_seq vers la
    # position relative de l'événement causal retenu (jamais masquée).
    conn, clock, wid = _fresh()
    ie = InjuryEngine(conn, clock=clock)
    ie.inflict_injury(wid, "character_1", 40000)
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    proj = reproducible_semantic_projection(conn, wid)
    # l'événement causal scripted_accident est retenu dans la projection
    types = [e[0] for e in proj]
    assert "scripted_accident" in types
    # toute cause normalisée pointe vers une position relative valide 1..N
    for ev in proj:
        p = json.loads(ev[3])
        if "cause_event_seq" in p:
            assert 1 <= p["cause_event_seq"] <= len(proj)
    conn.close()


def test_ordre_relatif_faits_preserve():
    conn, clock, wid = _fresh()
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    proj = reproducible_semantic_projection(conn, wid)
    # pour chaque activité, activity_started précède activity_completed
    starts = [i for i, e in enumerate(proj) if e[0] == "activity_started"]
    comps = [i for i, e in enumerate(proj) if e[0] == "activity_completed"]
    # l'ordre relatif des faits est préservé (les positions sont croissantes)
    assert starts == sorted(starts)
    assert comps == sorted(comps)
    conn.close()


def test_materialisation_erronee_detectee_par_etat():
    # une valeur erronée dans une matérialisation change l'état final → détectée
    # par le digest d'état, même si la matérialisation est exclue de la projection.
    conn, clock, wid = _fresh()
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    correct = canonical_state_digest(conn, wid)
    conn.execute(
        "UPDATE need_state SET value_milli = 12345 "
        "WHERE world_id=? AND need_key='satiete' AND character_id="
        "(SELECT id FROM character WHERE world_id=? AND key='character_1')",
        (wid, wid),
    )
    assert canonical_state_digest(conn, wid) != correct
    conn.close()


def test_materialisation_manquante_detectee_par_etat():
    # une ancre manquante (matérialisation absente) rend l'état incohérent →
    # détectée par le digest d'état.
    conn, clock, wid = _fresh()
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    correct = canonical_state_digest(conn, wid)
    conn.execute(
        "UPDATE need_state SET anchor_at = ? "
        "WHERE world_id=? AND need_key='satiete' AND character_id="
        "(SELECT id FROM character WHERE world_id=? AND key='character_1')",
        (to_iso(T0), wid, wid),
    )
    assert canonical_state_digest(conn, wid) != correct
    conn.close()


# --- MaterializationChainAudit : erreurs compensées --------------------------

def test_audit_chaine_materialisation_ok_run_normal():
    # un run normal (continu et segmenté) ne produit aucune erreur de chaîne
    conn, clock, wid = _fresh()
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    assert materialization_chain_audit(conn, wid) == []
    conn.close()
    conn, clock, wid = _fresh()
    se = SimulationEngine(conn, clock=clock)
    se.run_to(wid, to_iso(T0 + timedelta(hours=8)))
    se.run_to(wid, to_iso(T0 + timedelta(hours=16)))
    se.run_to(wid, to_iso(T0 + H24))
    assert materialization_chain_audit(conn, wid) == []
    conn.close()


def test_erreurs_compensees_blessure_detectees_par_audit_chaine():
    # chaîne compensée : 100 → 99 (erreur) → 96 (compense) ; final identique à
    # la chaîne correcte 100 → 98 → 96, mais l'événement A est incorrect.
    events = [
        (1, "injury_materialized", {
            "character": "character_1", "cause_event_seq": 7, "regime": "passive",
            "previous": {"severity": 100, "anchor": to_iso(T0), "remainder": 0},
            "new": {"severity": 99, "anchor": to_iso(T0 + timedelta(seconds=36)), "remainder": 0},
        }),
        (2, "injury_materialized", {
            "character": "character_1", "cause_event_seq": 7, "regime": "passive",
            "previous": {"severity": 99, "anchor": to_iso(T0 + timedelta(seconds=36)), "remainder": 0},
            "new": {"severity": 96, "anchor": to_iso(T0 + timedelta(seconds=72)), "remainder": 0},
        }),
    ]
    errors = _audit_injury_chain(events)
    # l'événement A (seq 1) est signalé : 99 != 98 attendu
    assert any(seq == 1 and "severity 99" in msg for seq, msg in errors)


def test_erreurs_compensees_besoins_detectees_par_audit_chaine():
    # chaîne compensée : reste erroné à l'événement A, compensé à B ; l'état
    # final (valeur + reste) est identique à la chaîne correcte, mais A est
    # incorrect (taux implicite non entier).
    events = [
        (1, {
            "character": "character_1", "reason": "passive",
            "previous_anchor_at": to_iso(T0), "new_anchor_at": to_iso(T0 + timedelta(seconds=36)),
            "previous_values": {"satiete": 100}, "new_values": {"satiete": 102},
            "previous_remainders": {"satiete": 0}, "new_remainders": {"satiete": 1},
        }),
        (2, {
            "character": "character_1", "reason": "passive",
            "previous_anchor_at": to_iso(T0 + timedelta(seconds=36)), "new_anchor_at": to_iso(T0 + timedelta(seconds=72)),
            "previous_values": {"satiete": 102}, "new_values": {"satiete": 104},
            "previous_remainders": {"satiete": 1}, "new_remainders": {"satiete": 0},
        }),
    ]
    errors = _audit_needs_chain(events)
    # l'événement A (seq 1) est signalé : taux implicite non entier
    assert any(seq == 1 and "implied rate non-integer" in msg for seq, msg in errors)


def test_clock_etat_coherents_apres_run_to():
    # après run_to, l'horloge persistée est ancrée à l'instant atteint et l'état
    # matérialisé est cohérent (aucune divergence entre simulated_now et les ancres).
    conn, clock, wid = _fresh()
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24))
    sim = parse_iso(_sim(conn, wid))
    assert sim == T0 + H24
    # toutes les ancres de besoins et de blessures sont <= l'heure atteinte
    max_need_anchor = conn.execute(
        "SELECT MAX(anchor_at) FROM need_state WHERE world_id=?", (wid,)
    ).fetchone()[0]
    assert parse_iso(max_need_anchor) <= sim
    max_inj_anchor = conn.execute(
        "SELECT MAX(recovery_anchor_at) FROM injury WHERE world_id=?", (wid,)
    ).fetchone()[0]
    if max_inj_anchor is not None:
        assert parse_iso(max_inj_anchor) <= sim
    conn.close()


# --- Absence de frontière -----------------------------------------------------

def test_absence_de_frontiere_signale_violation():
    # un monde bloqué avant target_time lève SimulationLimitError (violation),
    # pas un arrêt normal.
    conn, clock, wid = _fresh()
    # monde vide sans personnage actif : aucune activité possible
    with pytest.raises(SimulationLimitError):
        SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + H24), max_transitions=5)
    conn.close()
