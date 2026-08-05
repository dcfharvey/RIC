"""Tests du moteur canonique et de la persistance (Phase 1)."""

import json

import pytest

from vivarium.db import connect_database, transaction
from vivarium.migrations import ensure_schema
from vivarium.seed import SEED_LOCATIONS, SEED_OBJECTS
from vivarium.world import (
    WORLD_NAME_MAX_LEN,
    WorldEngine,
    WorldError,
    get_status,
)


@pytest.fixture
def setup():
    """Ouvre une base mémoire, migre et retourne un moteur + un monde."""
    conn = connect_database(":memory:")
    ensure_schema(conn)
    engine = WorldEngine(conn)
    world = engine.init_world(name="Monde test")
    return conn, engine, world


def test_init_cree_world_clock_lieux_objets_et_evenements(setup):
    conn, engine, world = setup
    assert world["status"] == "active"
    assert world["name"] == "Monde test"

    locs = conn.execute(
        "SELECT key, name FROM location WHERE world_id = ? ORDER BY key", (world["id"],)
    ).fetchall()
    assert len(locs) == 9
    expected = {k: n for k, n, _kind, _cap in SEED_LOCATIONS}
    assert {r["key"]: r["name"] for r in locs} == expected

    objs = conn.execute(
        "SELECT key FROM world_object WHERE world_id = ? ORDER BY key", (world["id"],)
    ).fetchall()
    assert [r["key"] for r in objs] == sorted(o[0] for o in SEED_OBJECTS)

    clock = conn.execute(
        "SELECT simulated_now FROM canonical_clock WHERE world_id = ?", (world["id"],)
    ).fetchone()
    assert clock["simulated_now"]

    events = conn.execute(
        "SELECT event_type FROM canonical_event WHERE world_id = ? ORDER BY seq",
        (world["id"],),
    ).fetchall()
    types = [r["event_type"] for r in events]
    assert types == ["world_created"] + ["character_created"] * 4 + ["world_seeded"]


def test_reouverture_retrouve_le_monde(tmp_path):
    db = tmp_path / "world.db"
    conn = connect_database(db)
    ensure_schema(conn)
    engine = WorldEngine(conn)
    world = engine.init_world(name="Persistant")
    last = conn.execute(
        "SELECT seq FROM canonical_event WHERE world_id = ? ORDER BY seq DESC LIMIT 1",
        (world["id"],),
    ).fetchone()[0]
    conn.close()

    # réouverture : mêmes données, dernière transaction retrouvée
    conn2 = connect_database(db)
    try:
        ensure_schema(conn2)
        engine2 = WorldEngine(conn2)
        loaded = engine2.get_world(world["id"])
        assert loaded["name"] == "Persistant"
        last2 = conn2.execute(
            "SELECT seq FROM canonical_event WHERE world_id = ? ORDER BY seq DESC LIMIT 1",
            (world["id"],),
        ).fetchone()[0]
        assert last2 == last
        assert len(engine2.list_worlds()) == 1
    finally:
        conn2.close()


def test_lieux_nom_modifiable_mais_cle_stable(setup):
    conn, _engine, world = setup
    cur = conn.execute(
        "UPDATE location SET name = ? WHERE world_id = ? AND key = ?",
        ("Chambre bleue", world["id"], "chambre_1"),
    )
    conn.execute("COMMIT") if conn.in_transaction else None
    row = conn.execute(
        "SELECT key, name FROM location WHERE world_id = ? AND key = ?",
        (world["id"], "chambre_1"),
    ).fetchone()
    assert row["key"] == "chambre_1"  # identité interne inchangée
    assert row["name"] == "Chambre bleue"


def test_identifiants_publics_uuid_distincts(setup):
    conn, _engine, world = setup
    ids = conn.execute(
        "SELECT public_id FROM location WHERE world_id = ?", (world["id"],)
    ).fetchall()
    values = [r["public_id"] for r in ids]
    assert len(values) == len(set(values)) == 9
    assert all(len(v) == 36 for v in values)


def test_aucune_api_publique_append_event(setup):
    # C-3 : l'écriture brute d'événements est strictement interne ; aucune API
    # publique générique ne permet d'injecter un event_type/payload/occurred_at
    # arbitraire sans mutation métier correspondante.
    _conn, engine, world = setup
    assert not hasattr(engine, "append_event")
    # les événements métier continuent d'incrémenter seq correctement
    engine.rename_world(world["id"], "Nouveau nom")
    seqs = [
        r["seq"] for r in _conn.execute(
            "SELECT seq FROM canonical_event WHERE world_id = ? ORDER BY seq",
            (world["id"],),
        )
    ]
    assert seqs == list(range(1, len(seqs) + 1))


# --- C-2 : événements administratifs situés dans le temps canonique ----------

class _FakeClock:
    def __init__(self, start):
        self._now = start

    def now(self):
        return self._now

    def now_iso(self):
        from vivarium.util import to_iso
        return to_iso(self.now())

    def advance(self, **kw):
        from datetime import timedelta
        self._now = self._now + timedelta(**kw)


def _admin_clock():
    from datetime import datetime, timezone
    return _FakeClock(datetime(2026, 8, 4, 0, 0, 0, tzinfo=timezone.utc))


def test_rename_world_apres_fast_forward_occurred_at_canonique():
    from datetime import timedelta
    from vivarium.simulation import SimulationEngine
    from vivarium.repro import structural_event_audit
    from vivarium.util import parse_iso, to_iso

    clock = _admin_clock()
    conn = connect_database(":memory:")
    ensure_schema(conn)
    engine = WorldEngine(conn, clock=clock)
    wid = engine.init_world(name="A")["id"]
    T1 = clock.now() + timedelta(days=7)
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T1))
    engine.rename_world(wid, "Nouveau nom")
    row = conn.execute(
        "SELECT occurred_at, recorded_at FROM canonical_event "
        "WHERE world_id = ? AND event_type = 'world_renamed'", (wid,)
    ).fetchone()
    # occurred_at = heure canonique du monde (T1), pas l'heure murale (R0)
    assert parse_iso(row["occurred_at"]) == T1
    # recorded_at reste mural (distinct)
    assert parse_iso(row["recorded_at"]) == clock.now()
    # le journal demeure monotone
    assert structural_event_audit(conn, wid)["occurred_at_monotonic"] is True


def test_link_added_removed_apres_fast_forward_occurred_at_canonique():
    from datetime import timedelta
    from vivarium.simulation import SimulationEngine
    from vivarium.spatial import GraphEngine
    from vivarium.repro import structural_event_audit
    from vivarium.util import parse_iso, to_iso

    clock = _admin_clock()
    conn = connect_database(":memory:")
    ensure_schema(conn)
    engine = WorldEngine(conn, clock=clock)
    wid = engine.init_world(name="A")["id"]
    T1 = clock.now() + timedelta(days=7)
    SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T1))
    g = GraphEngine(conn, clock=clock)
    # paire non présente dans le seed (cuisine → salle_de_bain)
    g.add_link(wid, "cuisine", "salle_de_bain", bidirectional=False)
    g.remove_link(wid, "cuisine", "salle_de_bain", bidirectional=False)
    for etype in ("link_added", "link_removed"):
        row = conn.execute(
            "SELECT occurred_at FROM canonical_event "
            "WHERE world_id = ? AND event_type = ?", (wid, etype)
        ).fetchone()
        assert parse_iso(row["occurred_at"]) == T1
    assert structural_event_audit(conn, wid)["occurred_at_monotonic"] is True


def test_rename_world_paused_occurred_at_gel():
    from vivarium.util import parse_iso

    clock = _admin_clock()
    conn = connect_database(":memory:")
    ensure_schema(conn)
    engine = WorldEngine(conn, clock=clock)
    wid = engine.init_world(name="A")["id"]
    clock.advance(hours=2)
    engine.pause_world(wid)
    frozen = engine.read_canonical_time(wid)
    clock.advance(hours=10)  # délai mural pendant la pause
    engine.rename_world(wid, "Renommé")
    row = conn.execute(
        "SELECT occurred_at FROM canonical_event "
        "WHERE world_id = ? AND event_type = 'world_renamed'", (wid,)
    ).fetchone()
    assert parse_iso(row["occurred_at"]) == parse_iso(frozen)


def test_rename_world_actif_occurred_at_derive():
    from vivarium.util import parse_iso

    clock = _admin_clock()
    conn = connect_database(":memory:")
    ensure_schema(conn)
    engine = WorldEngine(conn, clock=clock)
    wid = engine.init_world(name="A")["id"]
    clock.advance(hours=3)  # monde actif : heure canonique dérivée = R0 + 3 h
    engine.rename_world(wid, "Renommé")
    row = conn.execute(
        "SELECT occurred_at FROM canonical_event "
        "WHERE world_id = ? AND event_type = 'world_renamed'", (wid,)
    ).fetchone()
    assert parse_iso(row["occurred_at"]) == clock.now()


def test_json_invalide_rejete(setup):
    _conn, engine, world = setup
    with pytest.raises(Exception):
        with transaction(_conn) as c:
            c.execute(
                "INSERT INTO canonical_event (public_id, world_id, seq, occurred_at, "
                "recorded_at, source_kind, event_type, payload) VALUES (?,?,?,?,?,?,?,?)",
                ("x" * 36, world["id"], 9999, "2026-01-01T00:00:00+00:00",
                 "2026-01-01T00:00:00+00:00", "engine", "bad", "pas du json"),
            )


def test_etat_et_evenement_meme_transaction_atomique(setup):
    conn, engine, world = setup
    # renommage = état + événement dans la même transaction : les deux sont validés ensemble
    engine.rename_world(world["id"], "Nouveau nom")
    row = conn.execute(
        "SELECT name FROM worlds WHERE id = ?", (world["id"],)
    ).fetchone()
    event = conn.execute(
        "SELECT payload FROM canonical_event WHERE world_id = ? AND event_type='world_renamed'",
        (world["id"],),
    ).fetchone()
    assert row["name"] == "Nouveau nom"
    assert json.loads(event["payload"])["to"] == "Nouveau nom"


def test_transaction_echoue_sans_etat_partiel(tmp_path):
    db = tmp_path / "atomic.db"
    conn = connect_database(db)
    ensure_schema(conn)
    engine = WorldEngine(conn)
    world = engine.init_world(name="Atomic")
    before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world["id"],)
    ).fetchone()[0]
    # tentative : modifie l'état puis échoue sur l'événement (payload invalide) → rollback total
    with pytest.raises(Exception):
        with transaction(conn) as c:
            c.execute("UPDATE worlds SET name = 'BROKEN' WHERE id = ?", (world["id"],))
            c.execute(
                "INSERT INTO canonical_event (public_id, world_id, seq, occurred_at, "
                "recorded_at, source_kind, event_type, payload) VALUES (?,?,?,?,?,?,?,?)",
                ("y" * 36, world["id"], 99999, "2026-01-01T00:00:00+00:00",
                 "2026-01-01T00:00:00+00:00", "engine", "bad", "pas du json"),
            )
    # rollback : ni le nom ni l'événement ne subsistent
    name = conn.execute(
        "SELECT name FROM worlds WHERE id = ?", (world["id"],)
    ).fetchone()["name"]
    after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world["id"],)
    ).fetchone()[0]
    assert name == "Atomic"
    assert after == before


def test_clone_et_reouverture_wal(tmp_path):
    from vivarium.world import WorldEngine as WE
    db = tmp_path / "wal.db"
    conn = connect_database(db)
    ensure_schema(conn)
    WE(conn).init_world(name="WAL")
    conn.close()
    # le fichier -wal peut exister ; l'état doit être stable après checkpoint via réouverture
    conn2 = connect_database(db)
    try:
        ensure_schema(conn2)
        assert len(WE(conn2).list_worlds()) == 1
    finally:
        conn2.close()


def test_integrite_et_cles_etrangeres_ok(setup):
    conn, _engine, world = setup
    status = get_status(conn, world["id"])
    assert status["integrity_check"] == ["ok"]
    assert status["foreign_key_check"] == []
    assert status["schema_version"] >= 1
    assert status["clock"] is not None
    assert status["counts"]["locations"] == 9
    assert status["counts"]["objects"] == 3
    assert status["counts"]["characters"] == 4
    assert status["counts"]["events"] >= 2


def test_cle_etrangere_refuse_objet_orphelin(setup):
    conn, _engine, world = setup
    with pytest.raises(Exception):
        with transaction(conn) as c:
            c.execute(
                "INSERT INTO world_object (public_id, world_id, location_id, key, name, kind, state, created_at) "
                "VALUES (?,?,?,?,?,?,?,?)",
                ("z" * 36, world["id"], 999999, "orphelin", "Objet", "furniture", "present", "2026-01-01T00:00:00+00:00"),
            )


# --- Durcissement 4.1B : rename_world et pause/resume répétées ---------------

def _events(conn, wid, etype):
    return conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type = ?",
        (wid, etype),
    ).fetchone()[0]


def test_rename_world_valide_normalise(setup):
    conn, engine, world = setup
    engine.rename_world(world["id"], "  Nouveau nom  ")
    assert engine.get_world(world["id"])["name"] == "Nouveau nom"
    row = conn.execute(
        "SELECT payload FROM canonical_event WHERE world_id = ? AND event_type='world_renamed'",
        (world["id"],),
    ).fetchone()
    assert json.loads(row["payload"])["to"] == "Nouveau nom"


def test_rename_world_refus_vide(setup):
    conn, engine, world = setup
    before = engine.get_world(world["id"])["name"]
    before_events = _events(conn, world["id"], "world_renamed")
    with pytest.raises(WorldError) as ei:
        engine.rename_world(world["id"], "")
    assert ei.value.code == "invalid_name"
    assert engine.get_world(world["id"])["name"] == before
    assert _events(conn, world["id"], "world_renamed") == before_events


def test_rename_world_refus_espaces_seulement(setup):
    conn, engine, world = setup
    before_events = _events(conn, world["id"], "world_renamed")
    with pytest.raises(WorldError) as ei:
        engine.rename_world(world["id"], "   ")
    assert ei.value.code == "invalid_name"
    assert _events(conn, world["id"], "world_renamed") == before_events


def test_rename_world_refus_mauvais_type(setup):
    conn, engine, world = setup
    before_events = _events(conn, world["id"], "world_renamed")
    with pytest.raises(WorldError) as ei:
        engine.rename_world(world["id"], 123)
    assert ei.value.code == "invalid_name"
    assert _events(conn, world["id"], "world_renamed") == before_events


def test_rename_world_longueur_exacte_120(setup):
    conn, engine, world = setup
    name = "a" * WORLD_NAME_MAX_LEN
    engine.rename_world(world["id"], name)
    assert engine.get_world(world["id"])["name"] == name


def test_rename_world_longueur_121_refuse(setup):
    conn, engine, world = setup
    before_events = _events(conn, world["id"], "world_renamed")
    with pytest.raises(WorldError) as ei:
        engine.rename_world(world["id"], "a" * (WORLD_NAME_MAX_LEN + 1))
    assert ei.value.code == "invalid_name"
    assert _events(conn, world["id"], "world_renamed") == before_events


def test_pause_repetee_refusee(setup):
    conn, engine, world = setup
    engine.pause_world(world["id"])
    before_events = _events(conn, world["id"], "world_paused")
    with pytest.raises(WorldError) as ei:
        engine.pause_world(world["id"])
    assert ei.value.code == "already_paused"
    assert _events(conn, world["id"], "world_paused") == before_events
    assert engine.get_world(world["id"])["status"] == "paused"


def test_resume_repetee_refusee(setup):
    conn, engine, world = setup
    engine.pause_world(world["id"])
    engine.resume_world(world["id"])
    before_events = _events(conn, world["id"], "world_resumed")
    with pytest.raises(WorldError) as ei:
        engine.resume_world(world["id"])
    assert ei.value.code == "already_active"
    assert _events(conn, world["id"], "world_resumed") == before_events
    assert engine.get_world(world["id"])["status"] == "active"


def test_pause_repetee_aucune_modification_horloge(setup):
    conn, engine, world = setup
    engine.pause_world(world["id"])
    clock_before = conn.execute(
        "SELECT simulated_now, real_updated_at FROM canonical_clock WHERE world_id = ?",
        (world["id"],),
    ).fetchone()
    with pytest.raises(WorldError):
        engine.pause_world(world["id"])
    clock_after = conn.execute(
        "SELECT simulated_now, real_updated_at FROM canonical_clock WHERE world_id = ?",
        (world["id"],),
    ).fetchone()
    assert tuple(clock_before) == tuple(clock_after)
