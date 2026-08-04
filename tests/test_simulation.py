"""Tests du simulateur déterministe (Sous-lot 3.2C)."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from vivarium.activities import ActivityEngine
from vivarium.db import connect_database
from vivarium.migrations import ensure_schema
from vivarium.needs import NeedsEngine
from vivarium.simulation import SimulationEngine, SimulationLimitError
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


def _world(tmp_path=None):
    conn = connect_database(":memory:" if tmp_path is None else tmp_path / "w.db")
    ensure_schema(conn)
    clock = FakeClock()
    world = WorldEngine(conn, clock=clock).init_world(name="Sim")
    return conn, clock, world["id"]


def _journal(conn, wid):
    rows = conn.execute(
        "SELECT event_type FROM canonical_event WHERE world_id = ? ORDER BY seq", (wid,)
    ).fetchall()
    return [r["event_type"] for r in rows]


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


def test_simulation_24h():
    conn, clock, wid = _world()
    se = SimulationEngine(conn, clock=clock)
    target = to_iso(T0 + timedelta(hours=24))
    rep = se.run_to(wid, target)
    assert rep.reached_target is True
    assert rep.transitions < 2000  # garde par défaut (marge raisonnable)
    assert rep.transitions > 4  # au moins les 4 démarrages initiaux + déroulé
    for char in ("character_1", "character_2", "character_3", "character_4"):
        for v in _needs_final(conn, wid, char).values():
            assert 0 <= v <= 100000
        # plusieurs activités réalisées
        n = conn.execute(
            "SELECT COUNT(*) FROM activity WHERE world_id = ? AND character_id = "
            "(SELECT id FROM character WHERE key = ?)",
            (wid, char),
        ).fetchone()[0]
        assert n >= 3
    # aucune activité simultanée en double : index partiel garantit 1 active max
    active = conn.execute(
        "SELECT COUNT(*) FROM activity WHERE world_id = ? AND status='active'", (wid,)
    ).fetchone()[0]
    assert active <= 4
    conn.close()


def test_reproductibilite_24h():
    def run():
        conn, clock, wid = _world()
        rep = SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + timedelta(hours=24)))
        j = _journal(conn, wid)
        needs = {c: _needs_final(conn, wid, c) for c in ("character_1", "character_2", "character_3", "character_4")}
        conn.close()
        return j, needs, rep.transitions

    j1, n1, t1 = run()
    j2, n2, t2 = run()
    assert j1 == j2
    assert n1 == n2
    assert t1 == t2


def test_garde_limite_transitions():
    conn, clock, wid = _world()
    se = SimulationEngine(conn, clock=clock)
    with pytest.raises(SimulationLimitError) as exc:
        se.run_to(wid, to_iso(T0 + timedelta(hours=24)), max_transitions=1)
    e = exc.value
    assert e.transitions >= 1
    assert e.last_time
    assert isinstance(e.character, str)
    assert not hasattr(e, "reached_target")  # ne prétend jamais avoir atteint


def test_garde_doit_etre_positive():
    conn, clock, wid = _world()
    with pytest.raises(ValueError):
        SimulationEngine(conn, clock=clock).run_to(wid, to_iso(T0 + timedelta(hours=1)), max_transitions=0)


def test_heure_cible_au_milieu_dune_activite():
    conn, clock, wid = _world()
    ae = ActivityEngine(conn, clock=clock)
    # démarre eat pour les 4 habitantes au même temps simulé
    for i in range(1, 5):
        ae.start_activity(wid, f"character_{i}", "eat", "cuisine", sim_now=to_iso(T0))
    completed_before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type='activity_completed'",
        (wid,),
    ).fetchone()[0]
    se = SimulationEngine(conn, clock=clock)
    mid = to_iso(T0 + timedelta(seconds=900))  # au milieu d'un eat de 1800s
    rep = se.run_to(wid, mid)
    assert rep.reached_target is True
    # activité toujours active, aucun activity_completed, aucune nouvelle décision
    assert rep.active_activities
    completed_after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type='activity_completed'",
        (wid,),
    ).fetchone()[0]
    assert completed_after == completed_before


def test_bornes_simultanees_ordre_journal():
    conn, clock, wid = _world()
    ae = ActivityEngine(conn, clock=clock)
    for i in range(1, 5):
        ae.start_activity(wid, f"character_{i}", "rest", f"chambre_{i}", sim_now=to_iso(T0))
    se = SimulationEngine(conn, clock=clock)
    se.run_to(wid, to_iso(T0 + timedelta(seconds=3600)))  # fin des 4 rest simultanée
    rows = conn.execute(
        "SELECT seq, payload FROM canonical_event WHERE world_id = ? "
        "AND event_type='activity_completed' ORDER BY seq",
        (wid,),
    ).fetchall()
    chars = [json.loads(r["payload"])["character"] for r in rows]
    assert chars == ["character_1", "character_2", "character_3", "character_4"]
    conn.close()


def test_profils_seedes_neutres():
    conn, clock, wid = _world()
    rows = conn.execute(
        "SELECT satiete_threshold_mult_milli, repos_threshold_mult_milli, "
        "energie_threshold_mult_milli, hygiene_threshold_mult_milli, "
        "rest_preference_milli, idle_tolerance_milli FROM character_profile "
        "WHERE world_id = ?",
        (wid,),
    ).fetchall()
    assert all(
        tuple(r) == (1000, 1000, 1000, 1000, 0, 0) for r in rows
    )
    # aucune colonne REAL (arithmétique entière garantie)
    types = [r["type"].upper() for r in conn.execute("PRAGMA table_info(character_profile)")]
    assert "REAL" not in types
    assert "INTEGER" in types
    conn.close()
