"""Tests du Lot 2.1 — horloge canonique temps réel 1:1 et pause/reprise.

Tous les tests sont déterministes : une horloge injectée (FakeClock) remplace
l'horloge réelle, sans aucune attente réelle.
"""

from datetime import datetime, timedelta, timezone

import pytest

from vivarium.db import connect_database, transaction
from vivarium.migrations import ensure_schema
from vivarium.util import ClockError, parse_iso, to_iso
from vivarium.world import STATUS_ACTIVE, STATUS_PAUSED, WorldEngine

T0 = datetime(2026, 8, 1, 8, 0, 0, tzinfo=timezone.utc)


class FakeClock:
    """Horloge déterministe, avancée uniquement sur demande."""

    def __init__(self, start: datetime = T0, fail_on: int | None = None):
        self._now = start
        self._calls = 0
        self._fail_on = fail_on

    def now(self) -> datetime:
        self._calls += 1
        if self._fail_on is not None and self._calls == self._fail_on:
            raise ClockError("échec injecté (horloge)")
        return self._now

    def now_iso(self) -> str:
        return to_iso(self.now())

    def advance(self, **kwargs) -> None:
        self._now = self._now + timedelta(**kwargs)


def _open(tmp_path=None, clock=None):
    conn = connect_database(":memory:" if tmp_path is None else tmp_path / "w.db")
    ensure_schema(conn)
    engine = WorldEngine(conn, clock=clock or FakeClock())
    return conn, engine


def _init(engine, name="Test"):
    return engine.init_world(name=name)


def test_calcul_exact_apres_plusieurs_heures(tmp_path):
    clock = FakeClock(T0)
    conn, engine = _open(tmp_path, clock)
    world = _init(engine)
    assert parse_iso(engine.read_canonical_time(world["id"])) == T0
    clock.advance(hours=5)
    assert parse_iso(engine.read_canonical_time(world["id"])) == T0 + timedelta(hours=5)
    clock.advance(hours=3, minutes=30)
    assert parse_iso(engine.read_canonical_time(world["id"])) == T0 + timedelta(hours=8, minutes=30)
    conn.close()


def test_lecture_aucune_ecriture_ni_evenement(tmp_path):
    clock = FakeClock(T0)
    conn, engine = _open(tmp_path, clock)
    world = _init(engine)
    events_before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world["id"],)
    ).fetchone()[0]
    anchor = conn.execute(
        "SELECT simulated_now, real_updated_at FROM canonical_clock WHERE world_id = ?",
        (world["id"],),
    ).fetchone()
    status_before = conn.execute(
        "SELECT status FROM worlds WHERE id = ?", (world["id"],)
    ).fetchone()["status"]

    clock.advance(hours=6)
    for _ in range(50):
        engine.read_canonical_time(world["id"])

    events_after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world["id"],)
    ).fetchone()[0]
    anchor_after = conn.execute(
        "SELECT simulated_now, real_updated_at FROM canonical_clock WHERE world_id = ?",
        (world["id"],),
    ).fetchone()
    assert events_after == events_before
    assert anchor_after["simulated_now"] == anchor["simulated_now"]
    assert anchor_after["real_updated_at"] == anchor["real_updated_at"]
    assert conn.execute(
        "SELECT status FROM worlds WHERE id = ?", (world["id"],)
    ).fetchone()["status"] == status_before
    conn.close()


def test_gel_exact_pendant_la_pause(tmp_path):
    clock = FakeClock(T0)
    conn, engine = _open(tmp_path, clock)
    world = _init(engine)
    clock.advance(hours=2)
    engine.pause_world(world["id"])
    frozen = engine.read_canonical_time(world["id"])
    assert parse_iso(frozen) == T0 + timedelta(hours=2)
    clock.advance(hours=10)
    # toujours gelé même si 10 h réelles s'écoulent
    assert parse_iso(engine.read_canonical_time(world["id"])) == T0 + timedelta(hours=2)
    conn.close()


def test_aucun_rattrapage_du_temps_passe_en_pause(tmp_path):
    clock = FakeClock(T0)
    conn, engine = _open(tmp_path, clock)
    world = _init(engine)
    clock.advance(hours=2)
    engine.pause_world(world["id"])
    clock.advance(hours=5)  # 5 h de pause
    engine.resume_world(world["id"])
    # immédiatement après reprise : heure gelée, la pause n'est pas ajoutée
    assert parse_iso(engine.read_canonical_time(world["id"])) == T0 + timedelta(hours=2)
    clock.advance(hours=1)
    assert parse_iso(engine.read_canonical_time(world["id"])) == T0 + timedelta(hours=3)
    conn.close()


def test_reprise_et_persistance_apres_fermeture_reouverture(tmp_path):
    db = tmp_path / "persist.db"
    clock = FakeClock(T0)
    conn = connect_database(db)
    ensure_schema(conn)
    engine = WorldEngine(conn, clock=clock)
    world = _init(engine)
    clock.advance(hours=2)
    engine.pause_world(world["id"])
    frozen = engine.read_canonical_time(world["id"])
    conn.close()

    conn2 = connect_database(db)
    try:
        ensure_schema(conn2)
        engine2 = WorldEngine(conn2, clock=clock)
        assert parse_iso(engine2.read_canonical_time(world["id"])) == parse_iso(frozen)
        # monde actif : le temps continue dès la réouverture (dérivé des ancrages)
        engine2.resume_world(world["id"])
        clock.advance(hours=3)
        assert parse_iso(engine2.read_canonical_time(world["id"])) == parse_iso(frozen) + timedelta(hours=3)
    finally:
        conn2.close()


def test_pause_creer_evenement_unique_et_status(tmp_path):
    clock = FakeClock(T0)
    conn, engine = _open(tmp_path, clock)
    world = _init(engine)
    count_before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world["id"],)
    ).fetchone()[0]
    engine.pause_world(world["id"])
    engine.resume_world(world["id"])
    count_after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world["id"],)
    ).fetchone()[0]
    assert count_after == count_before + 2  # world_paused + world_resumed
    types = [r["event_type"] for r in conn.execute(
        "SELECT event_type FROM canonical_event WHERE world_id = ? AND "
        "event_type IN ('world_paused','world_resumed') ORDER BY seq", (world["id"],))]
    assert types == ["world_paused", "world_resumed"]
    conn.close()


def test_statut_reprend_active_apres_resume(tmp_path):
    clock = FakeClock(T0)
    conn, engine = _open(tmp_path, clock)
    world = _init(engine)
    engine.pause_world(world["id"])
    assert engine.get_world(world["id"])["status"] == STATUS_PAUSED
    engine.resume_world(world["id"])
    assert engine.get_world(world["id"])["status"] == STATUS_ACTIVE
    conn.close()


def test_transaction_atomique_pause_en_cas_de_panne(tmp_path):
    conn, engine = _open(tmp_path, FakeClock(T0))
    world = _init(engine)
    # capture de l'état avant l'échec de la pause
    anchor_before = conn.execute(
        "SELECT simulated_now, real_updated_at FROM canonical_clock WHERE world_id = ?",
        (world["id"],),
    ).fetchone()
    events_before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world["id"],)
    ).fetchone()[0]

    # Moteur neuf dont l'horloge échoue au 2e appel — c'est-à-dire à l'intérieur
    # de la transaction de pause (le 1er appel est dans la lecture de l'heure).
    engine2 = WorldEngine(conn, clock=FakeClock(T0, fail_on=2))
    with pytest.raises(ClockError):
        engine2.pause_world(world["id"])

    # aucune écriture partielle : statut inchangé, ancre inchangée, aucun événement
    assert engine.get_world(world["id"])["status"] == STATUS_ACTIVE
    anchor_after = conn.execute(
        "SELECT simulated_now, real_updated_at FROM canonical_clock WHERE world_id = ?",
        (world["id"],),
    ).fetchone()
    assert anchor_after["simulated_now"] == anchor_before["simulated_now"]
    assert anchor_after["real_updated_at"] == anchor_before["real_updated_at"]
    events_after = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world["id"],)
    ).fetchone()[0]
    assert events_after == events_before
    assert conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type = 'world_paused'",
        (world["id"],),
    ).fetchone()[0] == 0
    conn.close()


def test_statut_invalide_refuse_par_declencheur(tmp_path):
    conn, engine = _open(tmp_path)
    world = _init(engine)
    with pytest.raises(Exception):
        with transaction(conn) as c:
            c.execute("UPDATE worlds SET status = 'weird' WHERE id = ?", (world["id"],))
    conn.close()


def test_heure_anterieure_incoherente_refusee(tmp_path):
    clock = FakeClock(T0)
    conn, engine = _open(tmp_path, clock)
    world = _init(engine)
    clock.advance(hours=2)
    with pytest.raises(ClockError, match="incohérente"):
        engine.set_simulated_time(world["id"], to_iso(T0 + timedelta(hours=1)))
    # l'heure n'a pas changé
    assert parse_iso(engine.read_canonical_time(world["id"])) == T0 + timedelta(hours=2)
    conn.close()


def test_lecture_detecte_ancre_future(tmp_path):
    clock = FakeClock(T0)
    conn, engine = _open(tmp_path, clock)
    world = _init(engine)
    # place artificiellement l'ancre réelle dans le futur
    with transaction(conn) as c:
        c.execute(
            "UPDATE canonical_clock SET real_updated_at = ? WHERE world_id = ?",
            (to_iso(T0 + timedelta(hours=2)), world["id"]),
        )
    with pytest.raises(ClockError, match="incohérente"):
        engine.read_canonical_time(world["id"])
    conn.close()
