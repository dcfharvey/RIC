"""Tests du Sous-lot 3.2A — besoins dérivés et matérialisation.

Entièrement déterministes : horloge injectée, arithmétique entière.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest

from vivarium.db import connect_database, transaction
from vivarium.migrations import ensure_schema
from vivarium.needs import MAX_MILLI, NeedsEngine, NeedsError, derive, upgrade_dev_needs
from vivarium.util import new_uuid, to_iso
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


def _t(hours=0, minutes=0, seconds=0):
    return T0 + timedelta(hours=hours, minutes=minutes, seconds=seconds)


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    world = WorldEngine(conn, clock=clock).init_world(name="Needs")
    return conn, clock, world["id"]


# --- Formule pure ---------------------------------------------------------------

def test_derive_valeurs_passives_24h():
    anchor = to_iso(T0)
    cases = {
        # (num, den=36, anchor_val, 1h, 6h, 12h, 24h)
        "satiete": (-80, 36, 70000, 62000, 22000, 0, 0),
        "repos": (-60, 36, 70000, 64000, 34000, 0, 0),
        "energie": (-50, 36, 70000, 65000, 40000, 10000, 0),
        "hygiene": (-30, 36, 80000, 77000, 62000, 44000, 8000),
    }
    for key, (num, den, initial, h1, h6, h12, h24) in cases.items():
        v1, _ = derive(initial, 0, anchor, to_iso(_t(hours=1)), num, den)
        v6, _ = derive(initial, 0, anchor, to_iso(_t(hours=6)), num, den)
        v12, _ = derive(initial, 0, anchor, to_iso(_t(hours=12)), num, den)
        v24, _ = derive(initial, 0, anchor, to_iso(_t(hours=24)), num, den)
        assert (v1, v6, v12, v24) == (h1, h6, h12, h24), key


def test_derive_reste_jamais_hors_borne_et_clamp():
    num, den, anchor = -80, 36, 70000
    a = to_iso(T0)
    v, r = derive(anchor, 0, a, to_iso(_t(hours=100)), num, den)
    assert v == 0 and r == 0
    v, r = derive(99000, 0, a, to_iso(_t(hours=1)), 30, 36)  # +3000 -> 102000 -> clamp
    assert v == 100000 and r == 0
    for dt in (61, 3600, 7201, 86400):
        v, r = derive(anchor, 17, a, to_iso(T0 + timedelta(seconds=dt)), num, den)
        assert 0 <= v <= MAX_MILLI
        assert 0 <= r < den


def test_derive_rejette_heure_anterieure():
    with pytest.raises(NeedsError):
        derive(70000, 0, to_iso(_t(hours=5)), to_iso(_t(hours=1)), -80, 36)


def test_derive_equivalence_independante_du_decoupage():
    partitions = {
        "1x12h": [43200],
        "12x1h": [3600] * 12,
        "720x1min": [60] * 720,
        "irregulier": [1800, 5400, 3600, 14400, 7200, 10800],
    }
    for name, num, den, initial in (("satiete", -80, 36, 70000), ("hygiene", -30, 36, 80000)):
        base_val, base_rem = None, None
        for pname, splits in partitions.items():
            assert sum(splits) == 43200, pname
            val, rem = initial, 0
            start = T0
            for dt in splits:
                val, rem = derive(val, rem, to_iso(start), to_iso(start + timedelta(seconds=dt)), num, den)
                start = start + timedelta(seconds=dt)
            if base_val is None:
                base_val, base_rem = val, rem
            else:
                assert (val, rem) == (base_val, base_rem), (pname, name)


# --- Moteur / lectures ----------------------------------------------------------

def test_lecture_pure_sans_ecriture_ni_evenement(setup):
    conn, clock, wid = setup
    ne = NeedsEngine(conn, clock=clock)
    events_before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    rows_before = conn.execute(
        "SELECT value_milli, rate_remainder, anchor_at FROM need_state WHERE world_id = ?",
        (wid,),
    ).fetchall()
    clock.advance(hours=3)
    for _ in range(20):
        ne.derive_character(wid, "character_1", clock.now_iso())
        ne.derive_need(wid, "character_1", "satiete", clock.now_iso())
    events_after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    rows_after = conn.execute(
        "SELECT value_milli, rate_remainder, anchor_at FROM need_state WHERE world_id = ?",
        (wid,),
    ).fetchall()
    assert events_after == events_before
    assert [tuple(r) for r in rows_after] == [tuple(r) for r in rows_before]


def test_materialisation_ecrit_et_produit_un_evenement(setup):
    conn, clock, wid = setup
    ne = NeedsEngine(conn, clock=clock)
    clock.advance(hours=12)
    target = clock.now_iso()  # T0 + 12h
    events_before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type='needs_materialized'",
        (wid,),
    ).fetchone()[0]
    res = ne.materialize_character_needs(wid, "character_1", target, "test")
    assert res["new_values"] == {"satiete": 0, "repos": 0, "energie": 10000, "hygiene": 44000}
    row = conn.execute(
        "SELECT ns.value_milli, ns.anchor_at FROM need_state ns "
        "JOIN character ch ON ch.id = ns.character_id "
        "WHERE ns.world_id = ? AND ch.key = 'character_1' AND ns.need_key = 'energie'",
        (wid,),
    ).fetchone()
    assert row["value_milli"] == 10000
    assert row["anchor_at"] == target
    events_after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type='needs_materialized'",
        (wid,),
    ).fetchone()[0]
    assert events_after == events_before + 1
    payload = json.loads(conn.execute(
        "SELECT payload FROM canonical_event WHERE world_id = ? AND event_type='needs_materialized'",
        (wid,),
    ).fetchone()["payload"])
    assert payload["reason"] == "test"
    assert payload["previous_values"]["satiete"] == 70000
    assert payload["new_values"] == {"satiete": 0, "repos": 0, "energie": 10000, "hygiene": 44000}
    assert "previous_remainders" in payload and "new_remainders" in payload


def test_materialisation_rollback_si_heure_anterieure(setup):
    conn, clock, wid = setup
    ne = NeedsEngine(conn, clock=clock)
    with transaction(conn) as c:
        c.execute(
            "UPDATE need_state SET anchor_at = ? WHERE world_id = ? AND need_key='satiete'",
            (to_iso(_t(hours=6)), wid),
        )
    with pytest.raises(NeedsError):
        ne.materialize_character_needs(wid, "character_1", to_iso(_t(hours=3)), "test")
    vals = {
        r["need_key"]: r["value_milli"]
        for r in conn.execute(
            "SELECT need_key, value_milli FROM need_state WHERE world_id = ?", (wid,)
        )
    }
    assert vals == {"satiete": 70000, "repos": 70000, "energie": 70000, "hygiene": 80000}


# --- Multi-monde ----------------------------------------------------------------

def test_need_state_refuse_definition_autre_monde(setup):
    conn, clock, wid = setup
    other = WorldEngine(conn, clock=clock).init_world(name="Autre")
    with transaction(conn) as c:
        c.execute(
            "INSERT INTO need_definition (public_id, world_id, need_key, name, rate_num, rate_den, threshold_milli, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (new_uuid(), other["id"], "zzz", "Z", -1, 9, 35000, to_iso(T0)),
        )
    wid_char = conn.execute(
        "SELECT id FROM character WHERE world_id = ? AND key='character_1'", (wid,)
    ).fetchone()["id"]
    with transaction(conn) as c:
        with pytest.raises(Exception):
            c.execute(
                "INSERT INTO need_state (public_id, world_id, character_id, need_key, "
                "value_milli, rate_remainder, anchor_at, updated_at) "
                "VALUES (?,1,?,?,70000,0,?,?)",
                (new_uuid(), wid_char, "zzz", to_iso(T0), to_iso(T0)),
            )


# --- Pause / reprise ------------------------------------------------------------

def test_pause_materialise_et_gel_atomique(setup):
    conn, clock, wid = setup
    we = WorldEngine(conn, clock=clock)
    ne = NeedsEngine(conn, clock=clock)
    clock.advance(hours=2)
    events_before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    we.pause_world(wid)
    assert conn.execute("SELECT status FROM worlds WHERE id = ?", (wid,)).fetchone()["status"] == "paused"
    val = conn.execute(
        "SELECT ns.value_milli FROM need_state ns JOIN character ch ON ch.id=ns.character_id "
        "WHERE ns.world_id=? AND ch.key='character_1' AND ns.need_key='satiete'", (wid,)
    ).fetchone()["value_milli"]
    assert val == 54000  # 70000 - 16000 (2h à -8/h)
    events_after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    assert events_after == events_before + 5  # 4 needs_materialized + world_paused
    we.resume_world(wid)
    assert conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type='needs_materialized'",
        (wid,),
    ).fetchone()[0] == 4  # la reprise ne crée aucune matérialisation


def test_pause_echoue_et_rollback_total(setup):
    conn, clock, wid = setup
    we = WorldEngine(conn, clock=clock)
    with transaction(conn) as c:
        c.execute(
            "UPDATE need_state SET anchor_at = ? WHERE world_id = ? AND need_key='satiete'",
            (to_iso(_t(hours=48)), wid),
        )
    events_before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    with pytest.raises(NeedsError):
        we.pause_world(wid)
    assert conn.execute("SELECT status FROM worlds WHERE id = ?", (wid,)).fetchone()["status"] == "active"
    events_after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    assert events_after == events_before


# --- Mise à niveau non destructive ---------------------------------------------

def test_mise_a_niveau_idempotente_et_ancre_canonique(tmp_path):
    db = tmp_path / "needs.db"
    conn = connect_database(db)
    ensure_schema(conn)
    clock = FakeClock()
    world = WorldEngine(conn, clock=clock).init_world(name="Needs")
    wid = world["id"]
    conn.execute("DELETE FROM need_state WHERE world_id = ?", (wid,))
    conn.execute("DELETE FROM need_definition WHERE world_id = ?", (wid,))

    r1 = upgrade_dev_needs(conn, wid, clock=clock)
    assert r1["definitions_added"] == 4
    assert r1["states_added"] == 16
    anchor = conn.execute(
        "SELECT anchor_at FROM need_state WHERE world_id = ? LIMIT 1", (wid,)
    ).fetchone()["anchor_at"]
    assert anchor == to_iso(T0)  # heure simulée canonique, pas l'heure système

    r2 = upgrade_dev_needs(conn, wid, clock=clock)
    assert r2["definitions_added"] == 0 and r2["states_added"] == 0
    conn.close()


# --- Reproductibilité -----------------------------------------------------------

def test_reproductibilite_meme_resultat():
    def run():
        conn = connect_database(":memory:")
        ensure_schema(conn)
        clock = FakeClock()
        world = WorldEngine(conn, clock=clock).init_world(name="R")
        wid = world["id"]
        engine = WorldEngine(conn, clock=clock)
        ne = NeedsEngine(conn, clock=clock)
        clock.advance(hours=1)
        ne.materialize_character_needs(wid, "character_1", clock.now_iso(), "a")
        clock.advance(hours=5)
        ne.materialize_character_needs(wid, "character_1", clock.now_iso(), "b")
        clock.advance(hours=3)
        engine.pause_world(wid)
        events = [r["event_type"] for r in conn.execute(
            "SELECT event_type FROM canonical_event WHERE world_id = ? ORDER BY seq", (wid,)
        )]
        vals = [tuple(r) for r in conn.execute(
            "SELECT ns.need_key, ns.value_milli, ns.rate_remainder FROM need_state ns "
            "JOIN character ch ON ch.id=ns.character_id WHERE ns.world_id=? AND ch.key='character_1' "
            "ORDER BY need_key", (wid,))]
        conn.close()
        return events, vals
    e1, v1 = run()
    e2, v2 = run()
    assert e1 == e2
    assert v1 == v2
