"""Contrats du gel hors ligne et de la récupération après crash."""

from datetime import datetime, timedelta, timezone

import pytest

from vivarium.db import connect_database
from vivarium.migrations import ensure_schema
from vivarium.runtime_session import RuntimeSessionService
from vivarium.util import parse_iso, to_iso
from vivarium.world import WorldEngine


T0 = datetime(2026, 8, 8, 8, 0, tzinfo=timezone.utc)


class FakeClock:
    def __init__(self):
        self.value = T0

    def now(self):
        return self.value

    def now_iso(self):
        return to_iso(self.value)

    def advance(self, **kwargs):
        self.value += timedelta(**kwargs)


def _world(db, clock):
    conn = connect_database(db)
    ensure_schema(conn)
    world = WorldEngine(conn, clock=clock).init_world("Session test")
    return conn, world["id"]


def test_clean_stop_freezes_offline_time_and_restart_has_no_catchup(tmp_path):
    clock = FakeClock()
    conn, world_id = _world(tmp_path / "clean.sqlite", clock)
    sessions = RuntimeSessionService(conn, clock=clock)
    session = sessions.start(world_id)
    clock.advance(minutes=5)
    stopped_at = sessions.stop(session.session_id)

    clock.advance(hours=3)
    engine = WorldEngine(conn, clock=clock)
    assert engine.read_canonical_time(world_id) == stopped_at

    restarted = sessions.start(world_id)
    assert restarted.recovered_session_id is None
    assert engine.read_canonical_time(world_id) == stopped_at
    clock.advance(minutes=1)
    assert parse_iso(engine.read_canonical_time(world_id)) == parse_iso(stopped_at) + timedelta(minutes=1)
    sessions.stop(restarted.session_id)
    conn.close()


def test_unclean_session_recovers_last_heartbeat_without_offline_catchup(tmp_path):
    db = tmp_path / "crash.sqlite"
    clock = FakeClock()
    conn, world_id = _world(db, clock)
    first = RuntimeSessionService(conn, clock=clock).start(world_id)
    clock.advance(minutes=2)
    RuntimeSessionService(conn, clock=clock).heartbeat(first.session_id)
    conn.close()  # crash simulé : aucune fermeture de session

    clock.advance(hours=8)
    conn2 = connect_database(db)
    ensure_schema(conn2)
    recovered = RuntimeSessionService(conn2, clock=clock).start(world_id)
    assert recovered.recovered_session_id == first.session_id
    assert parse_iso(recovered.canonical_at) == T0 + timedelta(minutes=2)
    assert parse_iso(WorldEngine(conn2, clock=clock).read_canonical_time(world_id)) == T0 + timedelta(minutes=2)
    old = conn2.execute(
        "SELECT stop_kind FROM runtime_session WHERE id = ?", (first.session_id,)
    ).fetchone()
    assert old["stop_kind"] == "crash_recovered"
    RuntimeSessionService(conn2, clock=clock).stop(recovered.session_id)
    conn2.close()


def test_crash_recovery_never_precedes_a_committed_canonical_event(tmp_path):
    clock = FakeClock()
    conn, world_id = _world(tmp_path / "event.sqlite", clock)
    sessions = RuntimeSessionService(conn, clock=clock)
    first = sessions.start(world_id)
    target = to_iso(T0 + timedelta(minutes=7))
    WorldEngine(conn, clock=clock).set_simulated_time(world_id, target)

    recovered = sessions.start(world_id)  # simule le prochain lancement après crash
    assert recovered.recovered_session_id == first.session_id
    assert recovered.canonical_at == target
    sessions.stop(recovered.session_id)
    conn.close()


def test_runtime_lifecycle_audit_is_append_only(tmp_path):
    clock = FakeClock()
    conn, world_id = _world(tmp_path / "audit.sqlite", clock)
    sessions = RuntimeSessionService(conn, clock=clock)
    session = sessions.start(world_id)
    sessions.stop(session.session_id)
    kinds = [row["event_kind"] for row in conn.execute(
        "SELECT event_kind FROM runtime_session_event ORDER BY id"
    )]
    assert kinds == ["started", "clean_stop"]
    with pytest.raises(Exception, match="append-only"):
        conn.execute("DELETE FROM runtime_session_event")
    conn.close()
