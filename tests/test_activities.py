"""Tests du Sous-lot 3.2B — activités et effets + migration /36."""

from datetime import datetime, timedelta, timezone

import pytest

from vivarium.activities import ActivityEngine, ActivityError, upgrade_dev_activities
from vivarium.db import connect_database, transaction as _tx
from vivarium.migrations import ensure_schema, load_migrations, split_sql_statements
from vivarium.needs import NeedsEngine, derive
from vivarium.spatial import GraphEngine
from vivarium.util import new_uuid, now_utc, to_iso, parse_iso
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


def _t(**kw):
    return T0 + timedelta(**kw)


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    world = WorldEngine(conn, clock=clock).init_world(name="Acts")
    ae = ActivityEngine(conn, clock=clock)
    return conn, clock, ae, world["id"]


def _need(conn, wid, char, key):
    return conn.execute(
        "SELECT ns.value_milli, ns.rate_remainder FROM need_state ns "
        "JOIN character ch ON ch.id = ns.character_id "
        "WHERE ns.world_id = ? AND ch.key = ? AND ns.need_key = ?",
        (wid, char, key),
    ).fetchone()


def _set_need(conn, wid, char, key, value):
    with _tx(conn) as c:
        c.execute(
            "UPDATE need_state SET value_milli = ? "
            "WHERE world_id = ? AND character_id = "
            "(SELECT id FROM character WHERE world_id = ? AND key = ?) AND need_key = ?",
            (value, wid, wid, char, key),
        )


# --- Lieux autorisés ------------------------------------------------------------

def test_lieux_autorises_par_activite(setup):
    conn, _clock, ae, wid = setup
    assert ae.allowed_locations(wid, "eat") == {"cuisine"}
    assert ae.allowed_locations(wid, "clean") == {"salle_de_bain"}
    assert ae.allowed_locations(wid, "sleep") == {f"chambre_{i}" for i in range(1, 5)}
    assert ae.allowed_locations(wid, "rest") == {"salon"} | {f"chambre_{i}" for i in range(1, 5)}
    assert ae.allowed_locations(wid, "idle") == set()
    # les quatre chambres sont de type 'bedroom' (convention existante)
    kinds = {r["key"]: r["kind"] for r in conn.execute(
        "SELECT key, kind FROM location WHERE world_id = ?", (wid,)
    )}
    assert all(kinds[f"chambre_{i}"] == "bedroom" for i in range(1, 5))


def test_sleep_et_rest_acceptent_les_quatre_chambres(setup):
    _conn, _clock, ae, wid = setup
    for i in range(1, 5):
        assert ae.is_allowed(wid, "sleep", f"chambre_{i}")
        assert ae.is_allowed(wid, "rest", f"chambre_{i}")
        assert not ae.is_allowed(wid, "eat", f"chambre_{i}")


def test_refus_destination_autorisee_mais_inexistante(setup):
    _conn, _clock, ae, wid = setup
    # kind 'bedroom' autorise sleep, mais 'chambre_9' n'existe pas
    with pytest.raises(ActivityError):
        ae.start_activity(wid, "character_1", "sleep", "chambre_9")


def test_doublon_regle_par_cle_refuse(setup):
    conn, _clock, ae, wid = setup
    with _tx(conn) as c:
        with pytest.raises(Exception):
            c.execute(
                "INSERT INTO activity_allowed_location "
                "(public_id, world_id, activity_type, location_key, location_kind, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (new_uuid(), wid, "eat", "cuisine", None, now_utc()),
            )


def test_doublon_regle_par_kind_refuse(setup):
    conn, _clock, ae, wid = setup
    with _tx(conn) as c:
        with pytest.raises(Exception):
            c.execute(
                "INSERT INTO activity_allowed_location "
                "(public_id, world_id, activity_type, location_key, location_kind, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (new_uuid(), wid, "sleep", None, "bedroom", now_utc()),
            )


# --- Scénario eat ---------------------------------------------------------------

def test_eat_30min_scenario(setup):
    conn, clock, ae, wid = setup
    _set_need(conn, wid, "character_1", "satiete", 20000)
    ae.start_activity(wid, "character_1", "eat", "cuisine")
    sheet = ae.activity_sheet(wid, "character_1")
    assert sheet["type"] == "eat"
    assert parse_iso(sheet["planned_end_at"]) == T0 + timedelta(seconds=1800)
    # fait avancer le temps jusqu'à la fin de l'activité
    ae.advance_to(wid, "character_1", to_iso(_t(seconds=1800)))
    values = {k: _need(conn, wid, "character_1", k)["value_milli"] for k in ("satiete", "repos", "energie", "hygiene")}
    assert values == {"satiete": 80000, "repos": 67000, "energie": 71600, "hygiene": 78500}
    assert ae.activity_sheet(wid, "character_1") is None  # clôturée


# --- Scénario sleep -------------------------------------------------------------

def test_sleep_scenario_fin_a_8h(setup):
    conn, clock, ae, wid = setup
    _set_need(conn, wid, "character_1", "repos", 15000)
    _set_need(conn, wid, "character_1", "energie", 10000)
    ae.start_activity(wid, "character_1", "sleep", "chambre_1")
    sheet = ae.activity_sheet(wid, "character_1")
    end = parse_iso(sheet["planned_end_at"])
    # dt_repos = 37350s, dt_energie = 61200s -> max = 61200 -> borné à 8h = 28800s
    assert (end - T0).total_seconds() == 28800
    ae.advance_to(wid, "character_1", sheet["planned_end_at"])
    r = _need(conn, wid, "character_1", "repos")["value_milli"]
    e = _need(conn, wid, "character_1", "energie")["value_milli"]
    assert (r, e) == (79000, 50000)


def test_sleep_echeance_exacte_avec_reste_non_nul():
    from vivarium.activities import _seconds_to_target, SLEEP_REPOS_TARGET
    # value 97999, target 98000, rate +80/36
    assert _seconds_to_target(97999, 0, SLEEP_REPOS_TARGET, 80) == 1
    # un reste de 60 couvre déjà la dernière fraction -> dt = 0
    assert _seconds_to_target(97999, 60, SLEEP_REPOS_TARGET, 80) == 0


def test_sleep_refuse_si_inutile(setup):
    conn, _clock, ae, wid = setup
    _set_need(conn, wid, "character_1", "repos", 99000)
    _set_need(conn, wid, "character_1", "energie", 99000)
    with pytest.raises(ActivityError):
        ae.start_activity(wid, "character_1", "sleep", "chambre_1")


# --- Activité échue pendant l'arrêt --------------------------------------------

def test_activite_echue_avant_redemarrage(setup):
    conn, clock, ae, wid = setup
    events_before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type='activity_completed'",
        (wid,),
    ).fetchone()[0]
    ae.start_activity(wid, "character_1", "eat", "cuisine")
    planned_end = ae.activity_sheet(wid, "character_1")["planned_end_at"]
    clock.advance(hours=5)
    # l'application "se réveille" bien après la fin prévue
    ae.advance_to(wid, "character_1", clock.now_iso())
    # clôturée à sa fin canonique, pas à l'heure de réveil
    ev = conn.execute(
        "SELECT occurred_at FROM canonical_event WHERE world_id = ? AND event_type='activity_completed'",
        (wid,),
    ).fetchone()
    assert ev["occurred_at"] == planned_end
    events_after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type='activity_completed'",
        (wid,),
    ).fetchone()[0]
    assert events_after == events_before + 1
    assert ae.activity_sheet(wid, "character_1") is None


# --- Abandon / lectures / atomicité --------------------------------------------

def test_abort_activite(setup):
    conn, _clock, ae, wid = setup
    ae.start_activity(wid, "character_1", "rest", "salon")
    ae.abort_activity(wid, "character_1")
    row = conn.execute(
        "SELECT status FROM activity WHERE world_id = ? ORDER BY id DESC LIMIT 1", (wid,)
    ).fetchone()
    assert row["status"] == "aborted"
    assert ae.activity_sheet(wid, "character_1") is None


def test_lecture_activite_pure(setup):
    conn, _clock, ae, wid = setup
    ae.start_activity(wid, "character_1", "rest", "salon")
    events_before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    for _ in range(10):
        ae.activity_sheet(wid, "character_1")
        ae.allowed_locations(wid, "sleep")
        ae.is_allowed(wid, "eat", "cuisine")
    events_after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    assert events_after == events_before


def test_une_seule_activite_active_et_rollback_du_trajet(setup):
    conn, _clock, ae, wid = setup
    # première activité (sleep, cible = lieu courant → pas de déplacement)
    ae.start_activity(wid, "character_1", "sleep", "chambre_1")
    moved_before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type='character_moved'",
        (wid,),
    ).fetchone()[0]
    # tentative d'une seconde activité : elle déplace le personnage puis échoue
    # sur la contrainte "une seule active" → rollback complet du trajet
    with pytest.raises(Exception):
        ae.start_activity(wid, "character_1", "rest", "salon")
    moved_after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type='character_moved'",
        (wid,),
    ).fetchone()[0]
    assert moved_after == moved_before  # aucun déplacement retenu
    pos = conn.execute(
        "SELECT l.key FROM character ch JOIN location l ON l.id=ch.current_location_id "
        "WHERE ch.world_id = ? AND ch.key='character_1'",
        (wid,),
    ).fetchone()["key"]
    assert pos == "chambre_1"
    assert ae.activity_sheet(wid, "character_1") is not None  # c'est toujours le sleep


# --- Migration de conversion vers /36 ------------------------------------------

def _apply_migrations_up_to(conn, max_version):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS migrations ("
        "version INTEGER PRIMARY KEY, name TEXT NOT NULL, "
        "applied_at TEXT NOT NULL, checksum TEXT NOT NULL)"
    )
    for m in load_migrations():
        if m.version > max_version:
            continue
        done = conn.execute("SELECT 1 FROM migrations WHERE version = ?", (m.version,)).fetchone()
        if done:
            continue
        with _tx(conn) as c:
            for stmt in split_sql_statements(m.sql):
                c.execute(stmt)
            c.execute(
                "INSERT INTO migrations (version, name, applied_at, checksum) VALUES (?,?,?,?)",
                (m.version, m.name, now_utc(), m.checksum),
            )


def test_migration_0006_conversion_taux_et_restes():
    conn = connect_database(":memory:")
    _apply_migrations_up_to(conn, 5)
    now = to_iso(T0)
    target = to_iso(_t(hours=1))
    # jeu minimal avec d'anciens dénominateurs
    conn.execute(
        "INSERT INTO worlds (public_id, name, status, created_at, updated_at) VALUES (?,?,?,?,?)",
        (new_uuid(), "W", "active", now, now),
    )
    conn.execute(
        "INSERT INTO location (public_id, world_id, key, name, kind, capacity, created_at) "
        "VALUES (?,1,?,?,?,?,?)",
        (new_uuid(), "chambre_1", "Chambre 1", "bedroom", 1, now),
    )
    loc_id = conn.execute("SELECT id FROM location WHERE world_id=1 AND key='chambre_1'").fetchone()["id"]
    conn.execute(
        "INSERT INTO character (public_id, world_id, key, name, adult, current_location_id, created_at, updated_at) "
        "VALUES (?,1,?,?,1,?,?,?)",
        (new_uuid(), "character_1", "P1", loc_id, now, now),
    )
    char_id = conn.execute("SELECT id FROM character WHERE world_id=1").fetchone()["id"]
    old_defs = {"satiete": (-20, 9), "repos": (-5, 3), "energie": (-25, 18), "hygiene": (-5, 6)}
    for key, (num, den) in old_defs.items():
        conn.execute(
            "INSERT INTO need_definition (public_id, world_id, need_key, name, min_milli, max_milli, "
            "rate_num, rate_den, threshold_milli, created_at) VALUES (?,1,?,?,0,100000,?,?,?,?)",
            (new_uuid(), key, key, num, den, 35000 if key in ("satiete", "repos") else 30000, now),
        )
        conn.execute(
            "INSERT INTO need_state (public_id, world_id, character_id, need_key, value_milli, "
            "rate_remainder, anchor_at, updated_at) VALUES (?,1,?,?,70000,2,?,?)",
            (new_uuid(), char_id, key, now, now),
        )

    # valeur dérivée AVANT migration (anciens taux + reste)
    before = derive(70000, 2, now, target, *old_defs["satiete"])

    ensure_schema(conn)  # applique 0006 (conversion + tables d'activités)

    nd = conn.execute(
        "SELECT rate_num, rate_den FROM need_definition WHERE world_id=1 AND need_key='satiete'"
    ).fetchone()
    assert (nd["rate_num"], nd["rate_den"]) == (-80, 36)
    ns = conn.execute(
        "SELECT rate_remainder FROM need_state WHERE character_id=? AND need_key='satiete'",
        (char_id,),
    ).fetchone()
    assert ns["rate_remainder"] == 8  # 2 × (36/9)
    after = derive(70000, ns["rate_remainder"], now, target, -80, 36)
    assert after[0] == before[0]  # valeur dérivée identique
    assert ns["rate_remainder"] / 36 == 2 / 9  # même fraction
    conn.close()


# --- Calibration / upgrade ------------------------------------------------------

def test_upgrade_activites_idempotent(setup):
    conn, _clock, ae, wid = setup
    r1 = upgrade_dev_activities(conn, wid)
    assert r1["definitions_created"] == 0 and r1["rules_created"] == 0  # déjà seedé
