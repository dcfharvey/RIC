"""Tests du moteur canonique et de la persistance (Phase 1)."""

import json

import pytest

from vivarium.db import connect_database, transaction
from vivarium.migrations import ensure_schema
from vivarium.seed import SEED_LOCATIONS, SEED_OBJECTS
from vivarium.world import SOURCE_ENGINE, SOURCE_OWNER, WorldEngine, get_status


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
    assert types == ["world_created", "world_seeded"]


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


def test_append_event_incremente_seq_et_source_extensible(setup):
    conn, engine, world = setup
    b1 = engine.append_event(world["id"], SOURCE_ENGINE, "test_event", {"n": 1})
    b2 = engine.append_event(world["id"], SOURCE_OWNER, "owner_test", {"n": 2})
    assert b2 > b1
    rows = conn.execute(
        "SELECT seq, source_kind, event_type, payload FROM canonical_event "
        "WHERE world_id = ? AND event_type IN ('test_event','owner_test') ORDER BY seq",
        (world["id"],),
    ).fetchall()
    assert [r["source_kind"] for r in rows] == [SOURCE_ENGINE, SOURCE_OWNER]
    assert json.loads(rows[1]["payload"]) == {"n": 2}


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
