"""Tests du Lot 3.1 — identités et présence canonique."""

from datetime import datetime, timezone

import pytest

from vivarium.character import CharacterEngine, CharacterError, upgrade_development_world
from vivarium.db import connect_database
from vivarium.migrations import ensure_schema
from vivarium.util import to_iso
from vivarium.world import WorldEngine

T0 = datetime(2026, 8, 1, 8, 0, 0, tzinfo=timezone.utc)


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


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    world = WorldEngine(conn, clock=clock).init_world(name="Chars")
    ce = CharacterEngine(conn, clock=clock)
    return conn, ce, world["id"]


def test_quatre_personnages_adultes_persistants(setup):
    conn, ce, wid = setup
    chars = ce.list_characters(wid)
    assert [c["key"] for c in chars] == ["character_1", "character_2", "character_3", "character_4"]
    sheet = ce.character_sheet(wid, "character_1")
    assert sheet["adult"] == 1
    assert len(sheet["public_id"]) == 36
    assert sheet["location_key"] == "chambre_1"


def test_positions_distinctes_non_nulles(setup):
    _conn, ce, wid = setup
    positions = {c["key"]: c["location_key"] for c in ce.list_characters(wid)}
    assert positions == {
        "character_1": "chambre_1",
        "character_2": "chambre_2",
        "character_3": "chambre_3",
        "character_4": "chambre_4",
    }
    # current_location_id non nul
    rows = _conn.execute("SELECT current_location_id FROM character WHERE world_id = ?", (wid,)).fetchall()
    assert all(r["current_location_id"] for r in rows)


def test_aucune_colonne_is_dev(setup):
    conn, _ce, _wid = setup
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(character)")]
    assert "is_dev" not in cols
    assert "key" in cols and "name" in cols


def test_creation_emission_evenement_character_created(setup):
    conn, ce, wid = setup
    n = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type='character_created'",
        (wid,),
    ).fetchone()[0]
    assert n == 4


def test_lecture_aucune_ecriture_ni_evenement(setup):
    conn, ce, wid = setup
    events_before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    for _ in range(20):
        ce.character_sheet(wid, "character_1")
        ce.list_characters(wid)
    events_after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    assert events_after == events_before


def test_deplacement_valide_arête_dirigee(setup):
    conn, ce, wid = setup
    sheet = ce.move_character(wid, "character_1", "couloir")
    assert sheet["location_key"] == "couloir"
    row = conn.execute(
        "SELECT payload FROM canonical_event WHERE world_id = ? AND event_type='character_moved' "
        "ORDER BY id DESC LIMIT 1",
        (wid,),
    ).fetchone()
    import json
    assert json.loads(row["payload"]) == {"character": "character_1", "from": "chambre_1", "to": "couloir"}


def test_deplacement_refuse_non_adjacent(setup):
    conn, ce, wid = setup
    with pytest.raises(CharacterError):
        ce.move_character(wid, "character_1", "salle_de_bain")
    with pytest.raises(CharacterError):
        ce.move_character(wid, "character_1", "chambre_2")
    assert ce.character_sheet(wid, "character_1")["location_key"] == "chambre_1"
    n = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type='character_moved'",
        (wid,),
    ).fetchone()[0]
    assert n == 0  # aucune fausse écriture ni faux événement


def test_deplacement_vers_le_lieu_actuel_refuse(setup):
    conn, ce, wid = setup
    with pytest.raises(CharacterError):
        ce.move_character(wid, "character_1", "chambre_1")
    n = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type='character_moved'",
        (wid,),
    ).fetchone()[0]
    assert n == 0


def test_deplacement_refuse_pendant_pause(setup):
    conn, ce, wid = setup
    WorldEngine(conn).pause_world(wid)
    with pytest.raises(CharacterError):
        ce.move_character(wid, "character_1", "couloir")
    assert ce.character_sheet(wid, "character_1")["location_key"] == "chambre_1"


def test_cle_interne_immuable(setup):
    conn, ce, wid = setup
    with pytest.raises(Exception):
        conn.execute(
            "UPDATE character SET key = 'autre' WHERE world_id = ? AND key = 'character_1'",
            (wid,),
        )
        conn.execute("COMMIT")
    assert ce.character_sheet(wid, "character_1")["key"] == "character_1"


def test_deplacement_atomique_si_evenement_echoue(setup):
    conn, ce, wid = setup
    before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    # moteur neuf dont l'horloge échoue sur le 1er appel dans la transaction
    ce_bad = CharacterEngine(conn, clock=FakeClock(T0, fail_on=1))
    with pytest.raises(RuntimeError):
        ce_bad.move_character(wid, "character_1", "couloir")
    after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    assert after == before  # rollback complet
    assert ce.character_sheet(wid, "character_1")["location_key"] == "chambre_1"


def test_persistance_apres_reouverture(tmp_path):
    db = tmp_path / "chars.db"
    conn = connect_database(db)
    ensure_schema(conn)
    world = WorldEngine(conn).init_world(name="Persiste")
    wid = world["id"]
    CharacterEngine(conn).move_character(wid, "character_2", "couloir")
    conn.close()

    conn2 = connect_database(db)
    try:
        ensure_schema(conn2)
        ce = CharacterEngine(conn2)
        assert ce.character_sheet(wid, "character_2")["location_key"] == "couloir"
        assert ce.character_sheet(wid, "character_1")["location_key"] == "chambre_1"
    finally:
        conn2.close()


# --- Mise à niveau non destructive (upgrade_development_world) -----------------

def test_upgrade_idempotent_sur_monde_deja_peuple(setup):
    conn, ce, wid = setup
    events_before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    added = upgrade_development_world(conn, wid, clock=FakeClock())
    assert added == []  # aucun ajout
    # refuse de modifier un personnage existant
    assert ce.character_sheet(wid, "character_1")["name"] == "Personnage 1"
    assert ce.character_sheet(wid, "character_1")["location_key"] == "chambre_1"
    events_after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    assert events_after == events_before  # aucune écriture ni événement


def test_upgrade_ajoute_seulement_les_manquants(tmp_path):
    db = tmp_path / "upgrade.db"
    conn = connect_database(db)
    ensure_schema(conn)
    world = WorldEngine(conn).init_world(name="ÀUpgrader")
    wid = world["id"]
    # simule un monde existant sans personnages (connexion en autocommit)
    conn.execute("DELETE FROM need_state WHERE world_id = ?", (wid,))
    conn.execute("DELETE FROM character_profile WHERE world_id = ?", (wid,))
    conn.execute("DELETE FROM character WHERE world_id = ?", (wid,))

    added = upgrade_development_world(conn, wid, clock=FakeClock())
    assert added == ["character_1", "character_2", "character_3", "character_4"]

    # seconde exécution : idempotente, aucun doublon
    added2 = upgrade_development_world(conn, wid, clock=FakeClock())
    assert added2 == []
    n = conn.execute("SELECT COUNT(*) FROM character WHERE world_id = ?", (wid,)).fetchone()[0]
    assert n == 4


def test_upgrade_ne_supprime_rien_existant(tmp_path):
    db = tmp_path / "up2.db"
    conn = connect_database(db)
    ensure_schema(conn)
    world = WorldEngine(conn).init_world(name="SansChars")
    wid = world["id"]
    # conserve monde/horloge/lieux/objets/liens/événements ; retire seulement les personnages
    from vivarium.world import get_status
    before = get_status(conn, wid)
    assert before["counts"]["locations"] == 9
    conn.execute("DELETE FROM need_state WHERE world_id = ?", (wid,))
    conn.execute("DELETE FROM character_profile WHERE world_id = ?", (wid,))
    conn.execute("DELETE FROM character WHERE world_id = ?", (wid,))
    upgrade_development_world(conn, wid, clock=FakeClock())
    after = get_status(conn, wid)
    assert after["counts"]["locations"] == 9
    assert after["counts"]["characters"] == 4
    assert after["counts"]["events"] >= before["counts"]["events"]
