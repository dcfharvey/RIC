"""Tests du Sous-lot 3.3B1 — blessures : état, causalité et récupération.

Les effets de mobilité (déplacements, activités, politique, simulateur) sont
explicitement reportés à 3.3B2 : ce fichier ne teste que l'apparition avec une
cause valide, l'évolution sous régimes typés et la guérison exacte.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest

from vivarium.db import connect_database
from vivarium.injury import (
    DEN,
    InjuryEngine,
    InjuryError,
    derive,
    level,
    seconds_to_heal,
)
from vivarium.migrations import ensure_schema
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


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    wid = WorldEngine(conn, clock=clock).init_world(name="Inj")["id"]
    ie = InjuryEngine(conn, clock=clock)
    return conn, clock, ie, wid


INJURY_EVENTS = ("scripted_accident", "injury_occurred",
                "injury_materialized", "injury_healed")


def _events(conn, wid):
    rows = conn.execute(
        "SELECT seq, event_type, source_kind, payload FROM canonical_event "
        "WHERE world_id = ? ORDER BY seq", (wid,)
    ).fetchall()
    return [(r["event_type"], r["source_kind"], json.loads(r["payload"])) for r in rows]


def _injury_events(conn, wid):
    return [e for e in _events(conn, wid) if e[0] in INJURY_EVENTS]


def _injury_state(conn, wid, char):
    row = conn.execute(
        "SELECT i.status, i.severity_milli, i.rate_remainder, i.recovery_anchor_at, "
        "       i.started_at, i.recovered_at, i.cause_event_seq "
        "FROM injury i JOIN character ch ON ch.id = i.character_id "
        "WHERE i.world_id = ? AND ch.key = ?", (wid, char)
    ).fetchone()
    return dict(row) if row else None


def _fresh():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    wid = WorldEngine(conn, clock=clock).init_world(name="Inj")["id"]
    return conn, clock, InjuryEngine(conn, clock=clock), wid


# --- Apparition et causalité ---------------------------------------------------

def test_inflict_injury_cree_cause_et_blessure_atomiques(setup):
    conn, _clock, ie, wid = setup
    sheet = ie.inflict_injury(wid, "character_1", 3000)
    assert sheet["status"] == "active"
    assert sheet["severity_milli"] == 3000
    assert sheet["level"] == "light"
    ev = _injury_events(conn, wid)
    assert [e[0] for e in ev] == ["scripted_accident", "injury_occurred"]
    assert ev[0][1] == "owner" and ev[1][1] == "engine"
    cause_ev = conn.execute(
        "SELECT seq FROM canonical_event WHERE world_id=? AND event_type='scripted_accident'", (wid,)
    ).fetchone()
    occ_ev = conn.execute(
        "SELECT seq FROM canonical_event WHERE world_id=? AND event_type='injury_occurred'", (wid,)
    ).fetchone()
    assert cause_ev["seq"] < occ_ev["seq"]
    st = _injury_state(conn, wid, "character_1")
    assert st["recovery_anchor_at"] == to_iso(T0)
    assert st["started_at"] == to_iso(T0)
    assert st["status"] == "active"


def test_script_accident_puis_injure_par_cause(setup):
    conn, _clock, ie, wid = setup
    cause = ie.script_accident(wid, "character_1", 3000)
    sheet = ie.injure_character(wid, "character_1", cause)
    assert sheet["severity_milli"] == 3000
    assert [e[0] for e in _injury_events(conn, wid)] == ["scripted_accident", "injury_occurred"]


def test_cause_depassee_refusee(setup):
    _conn, clock, ie, wid = setup
    cause = ie.script_accident(wid, "character_1", 3000)
    clock.advance(hours=2)
    with pytest.raises(InjuryError):
        ie.injure_character(wid, "character_1", cause)


def test_cause_future_refusee(setup):
    _conn, _clock, ie, wid = setup
    with pytest.raises(InjuryError):
        ie.script_accident(wid, "character_1", 3000, sim_now=to_iso(T0 + timedelta(hours=1)))


def test_severite_nulle_refusee_sans_accident_set(setup):
    conn, _clock, ie, wid = setup
    with pytest.raises(InjuryError):
        ie.inflict_injury(wid, "character_1", 0)
    n = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id=? AND event_type='scripted_accident'", (wid,)
    ).fetchone()[0]
    assert n == 0


def test_rollback_combine_si_blessure_echoue(setup):
    conn, _clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 3000)
    with pytest.raises(InjuryError):
        ie.inflict_injury(wid, "character_1", 5000)  # échoue : blessure active
    n = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id=? AND event_type='scripted_accident'", (wid,)
    ).fetchone()[0]
    assert n == 1


def test_une_seule_active_et_reutilisation_cause_refusee(setup):
    conn, _clock, ie, wid = setup
    cause = ie.script_accident(wid, "character_1", 3000)
    ie.injure_character(wid, "character_1", cause)
    with pytest.raises(InjuryError):
        ie.injure_character(wid, "character_1", cause)
    char_id = conn.execute("SELECT id FROM character WHERE key='character_1'", ()).fetchone()["id"]
    with pytest.raises(Exception):
        conn.execute(
            "INSERT INTO injury (public_id, world_id, character_id, kind, status, "
            "severity_milli, rate_remainder, recovery_anchor_at, started_at, recovered_at, "
            "cause_event_seq, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("u2", wid, char_id, "mobility", "active", 1000, 0, to_iso(T0), to_iso(T0), None,
             cause, to_iso(T0), to_iso(T0)),
        )


def test_reutilisation_cause_apres_guerison_refusee(setup):
    _conn, clock, ie, wid = setup
    cause = ie.script_accident(wid, "character_1", 3000)
    ie.injure_character(wid, "character_1", cause)
    clock.advance(hours=20)
    ie.materialize_injury(wid, "character_1", clock.now_iso(), "passive")
    with pytest.raises(InjuryError):
        ie.injure_character(wid, "character_1", cause)


# --- Récupération, guérison et invariants --------------------------------------

def test_guerison_exacte_ancre_egale_heure_exacte(setup):
    conn, clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 3000)
    heal_time = to_iso(T0 + timedelta(seconds=54000))  # 15h passif
    clock.advance(seconds=90000)
    ie.materialize_injury(wid, "character_1", clock.now_iso(), "passive")
    st = _injury_state(conn, wid, "character_1")
    assert st["status"] == "healed"
    assert st["severity_milli"] == 0 and st["rate_remainder"] == 0
    assert st["recovered_at"] == heal_time
    assert st["recovery_anchor_at"] == heal_time
    ev = _injury_events(conn, wid)
    assert ev[-1][0] == "injury_healed"
    mats = [e for e in ev if e[0] == "injury_materialized"]
    assert len(mats) == 1


def test_independance_etat_final_du_decoupage():
    def run(decoupage):
        conn, clock, ie, wid = _fresh()
        ie.inflict_injury(wid, "character_1", 3000)
        if decoupage == "once":
            clock.advance(seconds=54000)
            ie.materialize_injury(wid, "character_1", clock.now_iso(), "passive")
        else:
            step = 54000 // decoupage
            for _ in range(decoupage):
                clock.advance(seconds=step)
                ie.materialize_injury(wid, "character_1", clock.now_iso(), "passive")
        state = _injury_state(conn, wid, "character_1")
        ev = _events(conn, wid)
        conn.close()
        return state, len([e for e in ev if e[0] == "injury_materialized"])

    s1, m1 = run("once")
    s540, m540 = run(540)
    assert s1 == s540          # état final identique
    assert m1 == 1 and m540 == 540  # mais journaux volontairement différents


def test_reproductibilite_journal_sequence_identique():
    def run():
        conn, clock, ie, wid = _fresh()
        ie.inflict_injury(wid, "character_1", 3000)
        clock.advance(seconds=10000)
        ie.materialize_injury(wid, "character_1", clock.now_iso(), "passive")
        clock.advance(seconds=10000)
        ie.materialize_injury(wid, "character_1", clock.now_iso(), "passive")
        clock.advance(seconds=3600)
        ie.materialize_injury(wid, "character_1", clock.now_iso(), "sleep")
        ev = _injury_events(conn, wid)
        state = _injury_state(conn, wid, "character_1")
        conn.close()
        return ev, state
    e1, s1 = run()
    e2, s2 = run()
    assert e1 == e2 and s1 == s2


def test_regime_inconnu_refuse(setup):
    _conn, _clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 3000)
    with pytest.raises(InjuryError):
        ie.materialize_injury(wid, "character_1", to_iso(T0), "hyper")


def test_effet_regime_sleep_gt_rest_gt_passive():
    def sev_after(regime):
        conn, clock, ie, wid = _fresh()
        ie.inflict_injury(wid, "character_1", 80000)
        clock.advance(seconds=3600)
        ie.materialize_injury(wid, "character_1", clock.now_iso(), regime)
        s = ie.injury_sheet(wid, "character_1")["severity_milli"]
        conn.close()
        return s
    p, r, s = sev_after("passive"), sev_after("rest"), sev_after("sleep")
    assert p == 79800 and r == 79400 and s == 78800
    assert s < r < p


def test_derive_et_seconds_to_heal_entiers():
    assert seconds_to_heal(3000, 0, 2, 36) == 54000
    assert derive(3000, 0, to_iso(T0), to_iso(T0 + timedelta(seconds=54000)), 2, 36) == (0, 0)
    assert seconds_to_heal(2800, 2, 6, 36) == (2800 * 36 - 2 + 6 - 1) // 6
    assert level(0) == "none" and level(3000) == "light"
    assert level(40000) == "moderate" and level(70000) == "severe"


def test_cible_future_au_dela_heure_canonique_refusee(setup):
    conn, _clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 3000)
    with pytest.raises(InjuryError):
        ie.materialize_injury(wid, "character_1", to_iso(T0 + timedelta(hours=3)), "passive")


def test_cible_future_refusee_pendant_pause(setup):
    conn, clock, ie, wid = setup
    world = WorldEngine(conn, clock=clock)
    ie.inflict_injury(wid, "character_1", 3000)
    world.pause_world(wid)
    clock.advance(hours=2)
    with pytest.raises(InjuryError):
        ie.materialize_injury(wid, "character_1", clock.now_iso(), "passive")
    before = len(_injury_events(conn, wid))
    ie.materialize_injury(wid, "character_1", to_iso(T0), "passive")  # no-op
    assert len(_injury_events(conn, wid)) == before


def test_cible_anterieure_a_ancre_refusee(setup):
    _conn, _clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 3000)
    with pytest.raises(InjuryError):
        ie.materialize_injury(wid, "character_1", to_iso(T0 - timedelta(seconds=100)), "passive")


def test_healed_terminal_trigger(setup):
    conn, clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 3000)
    clock.advance(hours=20)
    ie.materialize_injury(wid, "character_1", clock.now_iso(), "passive")
    row = conn.execute("SELECT id FROM injury WHERE world_id=?", (wid,)).fetchone()
    with pytest.raises(Exception):
        conn.execute(
            "UPDATE injury SET status='active', severity_milli=1000, recovered_at=NULL WHERE id=?",
            (row["id"],),
        )
    with pytest.raises(Exception):
        conn.execute("UPDATE injury SET severity_milli=500 WHERE id=?", (row["id"],))


def test_nouvelle_blessure_apres_guerison_nouvelle_ligne(setup):
    conn, clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 3000)
    clock.advance(hours=20)
    ie.materialize_injury(wid, "character_1", clock.now_iso(), "passive")
    ie.inflict_injury(wid, "character_1", 5000)
    hist = ie.list_injuries(wid, "character_1")
    assert len(hist) == 2
    assert hist[0]["status"] == "healed" and hist[1]["status"] == "active"
    assert hist[0]["public_id"] != hist[1]["public_id"]


def test_lecture_pure_aucune_ecriture(setup):
    conn, _clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 3000)
    before = len(_events(conn, wid))
    for _ in range(10):
        ie.injury_sheet(wid, "character_1")
        ie.list_injuries(wid, "character_1")
        ie.active_injury_row(wid, "character_1")
    assert len(_events(conn, wid)) == before


def test_pas_de_colonne_REAL(setup):
    conn, _clock, _ie, wid = setup
    types = [r["type"].upper() for r in conn.execute("PRAGMA table_info(injury)")]
    assert "REAL" not in types


# --- injury_sheet_at : dérivation pure sous régime explicite (4.1A) ----------

def _injury_at(ie, wid, char, at, regime):
    return ie.injury_sheet_at(wid, char, to_iso(at), regime)


def test_injury_sheet_at_passive(setup):
    conn, clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 3000)
    clock.advance(seconds=3600)
    sheet = _injury_at(ie, wid, "character_1", clock.now(), "passive")
    # 3000 sous 2/36 pendant 3600 s = 200 ; reste 3000-200=2800
    assert sheet["severity_milli"] == 2800
    assert sheet["level"] == "light"


def test_injury_sheet_at_rest(setup):
    conn, clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 60000)
    clock.advance(seconds=3600)
    sheet = _injury_at(ie, wid, "character_1", clock.now(), "rest")
    # 60000 sous 6/36 pendant 3600 s = 600 ; reste 59400
    assert sheet["severity_milli"] == 59400


def test_injury_sheet_at_sleep(setup):
    conn, clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 60000)
    clock.advance(seconds=3600)
    sheet = _injury_at(ie, wid, "character_1", clock.now(), "sleep")
    # 60000 sous 12/36 pendant 3600 s = 1200 ; reste 58800
    assert sheet["severity_milli"] == 58800


def test_injury_sheet_at_severe_moderate_frontiere(setup):
    conn, clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 60060)
    # sous sleep 12/36 : croisement severe→moderate à 180 s
    before = _injury_at(ie, wid, "character_1", T0 + timedelta(seconds=179), "sleep")
    at = _injury_at(ie, wid, "character_1", T0 + timedelta(seconds=180), "sleep")
    after = _injury_at(ie, wid, "character_1", T0 + timedelta(seconds=181), "sleep")
    assert before["level"] == "severe"
    assert at["severity_milli"] == 60000 and at["level"] == "moderate"
    assert after["level"] == "moderate"


def test_injury_sheet_at_moderate_light_frontiere(setup):
    conn, clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 30060)
    # sous sleep 12/36 : croisement moderate→light à 180 s
    at = _injury_at(ie, wid, "character_1", T0 + timedelta(seconds=180), "sleep")
    assert at["severity_milli"] == 30000 and at["level"] == "light"


def test_injury_sheet_at_guerison_exacte(setup):
    conn, clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 3000)
    # sous sleep 12/36 : guérison à 3000*36/12 = 9000 s
    at = _injury_at(ie, wid, "character_1", T0 + timedelta(seconds=9000), "sleep")
    assert at["severity_milli"] == 0
    assert at["level"] == "none"


def test_injury_sheet_at_avant_apres_frontiere(setup):
    conn, clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 60060)
    before = _injury_at(ie, wid, "character_1", T0 + timedelta(seconds=179), "sleep")
    at = _injury_at(ie, wid, "character_1", T0 + timedelta(seconds=180), "sleep")
    after = _injury_at(ie, wid, "character_1", T0 + timedelta(seconds=183), "sleep")
    assert before["severity_milli"] > at["severity_milli"]
    assert at["severity_milli"] == 60000
    assert after["severity_milli"] < at["severity_milli"]


def test_injury_sheet_at_aucune_ecriture(setup):
    conn, clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 40000)
    clock.advance(hours=2)
    before = dict(conn.execute(
        "SELECT severity_milli, rate_remainder, recovery_anchor_at, status "
        "FROM injury WHERE world_id = ?", (wid,)
    ).fetchone())
    before_events = len(_events(conn, wid))
    for regime in ("passive", "rest", "sleep"):
        _injury_at(ie, wid, "character_1", clock.now(), regime)
    after = dict(conn.execute(
        "SELECT severity_milli, rate_remainder, recovery_anchor_at, status "
        "FROM injury WHERE world_id = ?", (wid,)
    ).fetchone())
    assert after == before
    assert len(_events(conn, wid)) == before_events


def test_injury_sheet_at_regime_inconnu(setup):
    _conn, _clock, ie, wid = setup
    ie.inflict_injury(wid, "character_1", 3000)
    with pytest.raises(InjuryError):
        _injury_at(ie, wid, "character_1", T0, "bogus")
