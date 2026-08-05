"""Tests de la Phase 4.1A — couche de lecture administrative (AdminReadService).

Vérifie : liste des mondes, état général, instant canonique observé, personnages,
besoins dérivés, activité, blessure, journal paginé, monde/personnage inexistant,
pagination bornée, payload masqué/inclus, résumé déterministe, lecture sans effet
de bord et snapshot cohérent de vue composée.
"""

from datetime import datetime, timedelta, timezone

import pytest

from vivarium.admin import AdminReadError, AdminReadService, MAX_JOURNAL_LIMIT
from vivarium.activities import ActivityEngine
from vivarium.character import CharacterEngine
from vivarium.db import connect_database
from vivarium.injury import InjuryEngine
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, max_seq
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
    wid = WorldEngine(conn, clock=clock).init_world(name="Admin")["id"]
    return conn, clock, wid


def _service(conn, clock):
    return AdminReadService(conn, clock=clock)


# --- Liste des mondes --------------------------------------------------------

def test_list_worlds(setup):
    conn, clock, wid = setup
    svc = _service(conn, clock)
    worlds = svc.list_worlds()
    assert [w["id"] for w in worlds] == [wid]
    assert worlds[0]["name"] == "Admin"


# --- Dashboard ---------------------------------------------------------------

def test_dashboard_monde_actif(setup):
    conn, clock, wid = setup
    svc = _service(conn, clock)
    clock.advance(hours=2)
    d = svc.dashboard(wid)
    assert d["world"]["id"] == wid
    assert d["world"]["status"] == "active"
    assert d["observed_canonical_at"] == to_iso(T0 + timedelta(hours=2))
    assert d["last_seq"] == max_seq(conn, wid)
    assert d["last_seq"] > 0


def test_dashboard_monde_paused(setup):
    conn, clock, wid = setup
    WorldEngine(conn, clock=clock).pause_world(wid)
    clock.advance(hours=5)  # délai mural ignoré en pause
    d = _service(conn, clock).dashboard(wid)
    assert d["world"]["status"] == "paused"
    # heure canonique gelée (pause matérialisée à l'instant de la pause)
    assert d["observed_canonical_at"] == to_iso(T0)


def test_dashboard_monde_inexistant(setup):
    conn, clock, _wid = setup
    with pytest.raises(AdminReadError):
        _service(conn, clock).dashboard(9999)


# --- Personnages -------------------------------------------------------------

def test_list_character_views(setup):
    conn, clock, wid = setup
    svc = _service(conn, clock)
    views = svc.list_character_views(wid)
    assert [v["character"]["key"] for v in views] == [
        "character_1", "character_2", "character_3", "character_4",
    ]
    for v in views:
        assert v["character"]["name"]
        assert v["character"]["location"]
        assert "energie" in v["needs"]
        assert v["observed_canonical_at"]


def test_character_view_besoins_et_energie(setup):
    conn, clock, wid = setup
    clock.advance(hours=1)
    v = _service(conn, clock).character_view(wid, "character_1")
    assert v["character"]["key"] == "character_1"
    assert v["character"]["location"] == "chambre_1"
    # besoins dérivés au même instant observé
    assert v["observed_canonical_at"] == to_iso(T0 + timedelta(hours=1))
    assert v["energy"] == v["needs"]["energie"]["value_milli"]
    assert 0 <= v["energy"] <= 100000


def test_character_view_activite_active(setup):
    conn, clock, wid = setup
    ce = CharacterEngine(conn, clock=clock)
    ae = ActivityEngine(conn, clock=clock)
    ce.move_character(wid, "character_1", "couloir")
    ce.move_character(wid, "character_1", "salon")
    ce.move_character(wid, "character_1", "cuisine")
    ae.start_activity(wid, "character_1", "eat", "cuisine", sim_now=to_iso(T0))
    v = _service(conn, clock).character_view(wid, "character_1")
    assert v["activity"] is not None
    assert v["activity"]["type"] == "eat"
    assert v["activity"]["status"] == "active"


def test_character_view_blessure_et_niveau(setup):
    conn, clock, wid = setup
    InjuryEngine(conn, clock=clock).inflict_injury(wid, "character_1", 40000)
    v = _service(conn, clock).character_view(wid, "character_1")
    assert v["injury"] is not None
    assert v["injury"]["level"] == "moderate"
    assert v["injury"]["severity_milli"] == 40000


def test_character_view_personnage_inexistant(setup):
    conn, clock, wid = setup
    with pytest.raises(AdminReadError):
        _service(conn, clock).character_view(wid, "ghost")


# --- Journal -----------------------------------------------------------------

def test_journal_initial(setup):
    conn, clock, wid = setup
    rows = _service(conn, clock).journal_view(wid, limit=100)
    types = [r["event_type"] for r in rows]
    assert "world_created" in types
    assert "world_seeded" in types
    assert types.count("character_created") == 4
    # ordre par seq
    seqs = [r["seq"] for r in rows]
    assert seqs == sorted(seqs)


def test_journal_enrichi_apres_commandes(setup):
    conn, clock, wid = setup
    ce = CharacterEngine(conn, clock=clock)
    ce.move_character(wid, "character_1", "couloir")
    rows = _service(conn, clock).journal_view(wid, limit=100)
    assert any(r["event_type"] == "character_moved" for r in rows)
    moved = [r for r in rows if r["event_type"] == "character_moved"]
    assert moved[0]["actor"] == "character_1"


def test_journal_page_au_dela_derniere_sequence(setup):
    conn, clock, wid = setup
    n = max_seq(conn, wid)
    rows = _service(conn, clock).journal_view(wid, limit=10, offset=n)
    assert rows == []


def test_journal_monde_inexistant(setup):
    conn, clock, _wid = setup
    with pytest.raises(AdminReadError):
        _service(conn, clock).journal_view(9999, limit=10)


def test_journal_limit_invalide(setup):
    conn, clock, wid = setup
    svc = _service(conn, clock)
    for bad in (0, -1, MAX_JOURNAL_LIMIT + 1):
        with pytest.raises(ValueError):
            svc.journal_view(wid, limit=bad)


def test_journal_offset_invalide(setup):
    conn, clock, wid = setup
    with pytest.raises(ValueError):
        _service(conn, clock).journal_view(wid, limit=10, offset=-1)


def test_journal_payload_masque_par_defaut(setup):
    conn, clock, wid = setup
    rows = _service(conn, clock).journal_view(wid, limit=10)
    assert all("payload" not in r for r in rows)


def test_journal_payload_inclus_sur_demande(setup):
    conn, clock, wid = setup
    rows = _service(conn, clock).journal_view(wid, limit=10, include_payload=True)
    assert all("payload" in r for r in rows)
    assert "name" in rows[0]["payload"]  # world_created payload


def test_journal_resume_generique_type_inconnu():
    # fonction statique : type inconnu → résumé générique sûr
    assert AdminReadService._event_summary("totally_unknown", {}) == "Événement totally_unknown"


# --- Lecture sans effet de bord ----------------------------------------------

def test_lecture_sans_effet_de_bord(setup):
    conn, clock, wid = setup
    svc = _service(conn, clock)
    before_state = canonical_state_digest(conn, wid)
    before_seq = max_seq(conn, wid)
    before_events = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    before_need_anchor = conn.execute(
        "SELECT anchor_at FROM need_state WHERE world_id = ? LIMIT 1", (wid,)
    ).fetchone()[0]

    # lectures répétées
    for _ in range(5):
        svc.dashboard(wid)
        svc.list_character_views(wid)
        svc.character_view(wid, "character_1")
        svc.journal_view(wid, limit=50)

    assert canonical_state_digest(conn, wid) == before_state
    assert max_seq(conn, wid) == before_seq
    assert conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0] == before_events
    assert conn.execute(
        "SELECT anchor_at FROM need_state WHERE world_id = ? LIMIT 1", (wid,)
    ).fetchone()[0] == before_need_anchor


def test_lecture_ne_materialise_pas_blessure(setup):
    conn, clock, wid = setup
    InjuryEngine(conn, clock=clock).inflict_injury(wid, "character_1", 40000)
    clock.advance(hours=2)
    before = dict(conn.execute(
        "SELECT severity_milli, rate_remainder, recovery_anchor_at, status "
        "FROM injury WHERE world_id = ?", (wid,)
    ).fetchone())
    _service(conn, clock).character_view(wid, "character_1")
    after = dict(conn.execute(
        "SELECT severity_milli, rate_remainder, recovery_anchor_at, status "
        "FROM injury WHERE world_id = ?", (wid,)
    ).fetchone())
    assert after == before  # aucune matérialisation de blessure


# --- Snapshot cohérent de vue composée --------------------------------------

def test_snapshot_coherent_vue_composee(setup):
    conn, clock, wid = setup
    clock.advance(hours=3)
    v = _service(conn, clock).character_view(wid, "character_1")
    # tous les besoins dérivés au même instant observé
    assert v["observed_canonical_at"] == to_iso(T0 + timedelta(hours=3))
    for need in ("satiete", "repos", "energie", "hygiene"):
        assert v["needs"][need]["value_milli"] >= 0
    # dashboard et vue personnage partagent le même instant observé
    d = _service(conn, clock).dashboard(wid)
    assert d["observed_canonical_at"] == v["observed_canonical_at"]
