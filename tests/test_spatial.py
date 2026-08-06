"""Tests du Lot 2.2 — connectivité spatiale (graphe orienté)."""

from datetime import datetime, timezone

import pytest

from vivarium.db import connect_database, transaction
from vivarium.migrations import ensure_schema
from vivarium.seed import SEED_LINKS
from vivarium.spatial import GraphEngine, GraphError
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


@pytest.fixture
def graph():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    world = WorldEngine(conn, clock=clock).init_world(name="Spatial")
    g = GraphEngine(conn, clock=clock)
    return conn, g, world["id"]


def test_neuf_lieux_et_couloir(graph):
    conn, _g, wid = graph
    keys = {r["key"] for r in conn.execute("SELECT key FROM location WHERE world_id = ?", (wid,))}
    assert "couloir" in keys
    assert len(keys) == 9


def test_seed_genere_deux_aretes_par_lien(graph):
    conn, _g, wid = graph
    n = conn.execute(
        "SELECT COUNT(*) FROM location_link WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    assert n == len(SEED_LINKS) * 2  # 16 arêtes dirigées


def test_adjacence_directe(graph):
    _conn, g, wid = graph
    assert g.can_traverse(wid, "salon", "cuisine")
    assert g.can_traverse(wid, "couloir", "chambre_1")
    assert not g.can_traverse(wid, "chambre_1", "salle_de_bain")  # via couloir, pas direct


def test_has_physical_connection(graph):
    _conn, g, wid = graph
    assert g.has_physical_connection(wid, "salon", "cuisine")
    assert g.has_physical_connection(wid, "chambre_1", "couloir")


def test_trajet_valide_de_salon_a_chambre_4(graph):
    _conn, g, wid = graph
    path = g.find_path(wid, "salon", "chambre_4")
    assert path is not None
    assert path[0] == "salon"
    assert path[-1] == "chambre_4"
    assert "couloir" in path


def test_integrite_du_seed(graph):
    _conn, g, wid = graph
    rep = g.check_graph_integrity(wid)
    assert rep["ok"] is True
    assert rep["self_loops"] == 0
    assert rep["duplicate_edges"] == 0
    assert rep["fk_violations"] == []
    assert rep["topology_policy"] == "strong_anchor"
    assert rep["topology_anchor"] == "salon"
    assert rep["unreachable_from_anchor"] == []
    assert rep["unreachable_to_anchor"] == []
    assert rep["root_missing"] is False


# --- Sens uniques et direction -------------------------------------------------

def test_can_traverse_vs_has_physical_connection_a_sens_unique(graph):
    conn, g, wid = graph
    with transaction(conn) as c:
        c.execute(
            "INSERT INTO location (public_id, world_id, key, name, kind, capacity, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            ("a" * 36, wid, "studio_a", "Studio A", "room", 1, "2026-01-01T00:00:00+00:00"),
        )
        c.execute(
            "INSERT INTO location (public_id, world_id, key, name, kind, capacity, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            ("b" * 36, wid, "studio_b", "Studio B", "room", 1, "2026-01-01T00:00:00+00:00"),
        )
    g.add_link(wid, "studio_a", "studio_b", bidirectional=False)
    assert g.can_traverse(wid, "studio_a", "studio_b") is True
    assert g.can_traverse(wid, "studio_b", "studio_a") is False
    assert g.has_physical_connection(wid, "studio_a", "studio_b") is True
    assert g.has_physical_connection(wid, "studio_b", "studio_a") is True  # au moins un sens


def test_find_path_respecte_les_directions(graph):
    _conn, g, wid = graph
    # Une voie de remplacement orientée maintient la connectivité forte après
    # le retrait de salon→cuisine; la fermeture ne peut plus isoler un lieu.
    g.add_link(wid, "cour", "cuisine", bidirectional=False)
    g.remove_link(wid, "salon", "cuisine", bidirectional=False)  # retire salon→cuisine
    assert g.can_traverse(wid, "salon", "cuisine") is False
    assert g.can_traverse(wid, "cuisine", "salon") is True
    assert g.find_path(wid, "salon", "cuisine") == ["salon", "cour", "cuisine"]
    assert isinstance(g.find_path(wid, "cuisine", "salon"), list)


# --- Création / suppression bidirectionnelle et atomicité -----------------------

def test_creation_bidirectionnelle_produit_deux_aretes_et_un_evenement(graph):
    conn, g, wid = graph
    events_before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type = 'link_added'",
        (wid,),
    ).fetchone()[0]
    g.add_link(wid, "cour", "cuisine", bidirectional=True)
    assert g.can_traverse(wid, "cour", "cuisine")
    assert g.can_traverse(wid, "cuisine", "cour")
    events_after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type = 'link_added'",
        (wid,),
    ).fetchone()[0]
    assert events_after == events_before + 1  # un seul événement pour l'opération complète


def test_creation_sens_unique_une_seule_arete(graph):
    _conn, g, wid = graph
    g.add_link(wid, "cour", "cuisine", bidirectional=False)
    assert g.can_traverse(wid, "cour", "cuisine")
    assert not g.can_traverse(wid, "cuisine", "cour")


def test_echec_seconde_insertion_annule_la_premiere(graph):
    conn, g, wid = graph
    # Une alternative préserve le graphe lors de la fermeture de seed.
    g.add_link(wid, "cour", "cuisine", bidirectional=True)
    # retire le passage bidirectionnel salon↔cuisine
    g.remove_link(wid, "salon", "cuisine")
    assert not g.can_traverse(wid, "salon", "cuisine")
    assert not g.can_traverse(wid, "cuisine", "salon")

    # crée une seule arête cuisine→salon (sens unique)
    g.add_link(wid, "cuisine", "salon", bidirectional=False)
    assert not g.can_traverse(wid, "salon", "cuisine")

    # tentative bidirectionnelle : add_link(salon, cuisine) insère salon→cuisine (ok),
    # puis cuisine→salon (existe déjà → UNIQUE) → rollback : salon→cuisine annulé.
    with pytest.raises(Exception):
        g.add_link(wid, "salon", "cuisine", bidirectional=True)
    assert not g.can_traverse(wid, "salon", "cuisine")
    assert g.can_traverse(wid, "cuisine", "salon")  # l'existant est intact


def test_suppression_bidirectionnelle_atomique(graph):
    _conn, g, wid = graph
    g.add_link(wid, "cour", "salle_de_bain", bidirectional=True)
    assert g.can_traverse(wid, "cour", "salle_de_bain")
    assert g.can_traverse(wid, "salle_de_bain", "cour")
    g.remove_link(wid, "cour", "salle_de_bain")  # bidirectionnel par défaut
    assert not g.can_traverse(wid, "cour", "salle_de_bain")
    assert not g.can_traverse(wid, "salle_de_bain", "cour")


def test_suppression_inexistante_echoue(graph):
    _conn, g, wid = graph
    with pytest.raises(GraphError):
        g.remove_link(wid, "chambre_1", "chambre_2")  # aucun passage direct
    assert g.can_traverse(wid, "couloir", "chambre_1")  # graphe seed intact


def test_suppression_qui_isole_refusee_et_rollback_complet(graph):
    conn, g, wid = graph
    before_edges = conn.execute(
        "SELECT COUNT(*) FROM location_link WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    before_events = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]

    with pytest.raises(GraphError) as exc:
        g.remove_link(wid, "couloir", "chambre_1")

    assert exc.value.code == "would_isolate_location"
    assert g.can_traverse(wid, "couloir", "chambre_1")
    assert g.can_traverse(wid, "chambre_1", "couloir")
    assert conn.execute(
        "SELECT COUNT(*) FROM location_link WHERE world_id = ?", (wid,)
    ).fetchone()[0] == before_edges
    assert conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0] == before_events


def test_politique_none_autorise_un_monde_a_zones_separees(graph):
    conn, g, wid = graph
    conn.execute(
        "UPDATE world_topology_policy SET policy_key = 'none', anchor_location_id = NULL "
        "WHERE world_id = ?", (wid,)
    )

    g.remove_link(wid, "couloir", "chambre_1")

    report = g.check_graph_integrity(wid)
    assert report["ok"] is True
    assert report["topology_policy"] == "none"
    assert g.can_traverse(wid, "couloir", "chambre_1") is False


# --- Intégrité / lectures pures -------------------------------------------------

def test_lectures_spatiales_aucune_ecriture_ni_evenement(graph):
    conn, g, wid = graph
    events_before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    edges_before = conn.execute(
        "SELECT COUNT(*) FROM location_link WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    for _ in range(20):
        g.find_path(wid, "salon", "chambre_4")
        g.can_traverse(wid, "salon", "cuisine")
        g.has_physical_connection(wid, "chambre_1", "couloir")
        g.adjacent_from(wid, "couloir")
        g.check_graph_integrity(wid)
    events_after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    edges_after = conn.execute(
        "SELECT COUNT(*) FROM location_link WHERE world_id = ?", (wid,)
    ).fetchone()[0]
    assert events_after == events_before
    assert edges_after == edges_before


def test_aucun_trajet_si_lieu_isole(graph):
    conn, g, wid = graph
    with transaction(conn) as c:
        c.execute(
            "INSERT INTO location (public_id, world_id, key, name, kind, capacity, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            ("c" * 36, wid, "cave", "Cave", "room", 1, "2026-01-01T00:00:00+00:00"),
        )
    assert g.find_path(wid, "salon", "cave") is None
    rep = g.check_graph_integrity(wid)
    assert "cave" in rep["unreachable_from_anchor"]
    assert "cave" in rep["unreachable_to_anchor"]


def test_boucle_sur_soi_refusee(graph):
    _conn, g, wid = graph
    with pytest.raises(GraphError):
        g.add_link(wid, "salon", "salon", bidirectional=False)


def test_persistance_liens_apres_reouverture(tmp_path):
    db = tmp_path / "spatial.db"
    conn = connect_database(db)
    ensure_schema(conn)
    world = WorldEngine(conn).init_world(name="Persist")
    wid = world["id"]
    conn.close()

    conn2 = connect_database(db)
    try:
        ensure_schema(conn2)
        g2 = GraphEngine(conn2)
        assert g2.can_traverse(wid, "couloir", "chambre_1") is True
        assert g2.find_path(wid, "salon", "chambre_4") is not None
    finally:
        conn2.close()
