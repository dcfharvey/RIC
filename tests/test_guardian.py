from datetime import datetime, timedelta, timezone
import json
import sqlite3

import pytest

from vivarium.activities import ActivityEngine
from vivarium.db import connect_database
from vivarium.guardian import LocalGuardian
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.runtime_session import RuntimeSessionService
from vivarium.util import to_iso
from vivarium.world import WorldEngine


class Clock:
    def __init__(self): self.current = datetime(2026, 8, 7, 4, tzinfo=timezone.utc)
    def now(self): return self.current
    def now_iso(self): return to_iso(self.current)
    def advance(self, seconds): self.current += timedelta(seconds=seconds)


class Models:
    def __init__(self, values=("google/gemma-4-12b-qat",), error=None):
        self.values, self.error, self.calls = values, error, 0
    def list_models(self):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.values


def _world(clock):
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    return conn, world_id


def test_guardian_is_hourly_logged_and_non_generative(tmp_path):
    clock = Clock()
    conn, world_id = _world(clock)
    models = Models()
    log = tmp_path / "guardian.jsonl"
    guardian = LocalGuardian(
        conn, world_id, log_path=log, model_lister=models, clock=clock
    )

    first = guardian.run_if_due()
    assert first is not None and first.status == "SAIN"
    assert guardian.run_if_due() is None
    clock.advance(3599)
    assert guardian.run_if_due() is None
    clock.advance(1)
    second = guardian.run_if_due()
    assert second is not None and second.status == "SAIN"
    assert models.calls == 2
    lines = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [line["status"] for line in lines] == ["SAIN", "SAIN"]
    conn.close()


def test_guardian_does_not_recheck_between_intervals_after_a_canonical_event(tmp_path):
    clock = Clock()
    conn, world_id = _world(clock)
    guardian = LocalGuardian(conn, world_id, log_path=tmp_path / "guardian.jsonl", clock=clock)
    assert guardian.run_if_due() is not None
    assert guardian.run_if_due() is None
    WorldEngine(conn, clock=clock).rename_world(world_id, "Événement surveillé")
    assert guardian.run_if_due() is None
    clock.advance(3600)
    assert guardian.run_if_due() is not None
    conn.close()


def test_guardian_classifies_local_llm_failure_as_attention(tmp_path):
    clock = Clock()
    conn, world_id = _world(clock)
    report = LocalGuardian(
        conn,
        world_id,
        log_path=tmp_path / "guardian.jsonl",
        model_lister=Models(error=TimeoutError()),
        clock=clock,
    ).inspect()
    assert report.status == "ATTENTION"
    assert next(check for check in report.checks if check.key == "local_llm").detail == "TimeoutError"
    conn.close()


def test_guardian_marks_a_genuinely_overdue_activity_critical(tmp_path):
    clock = Clock()
    conn, world_id = _world(clock)
    ActivityEngine(conn, clock=clock).start_activity(
        world_id, "luna", "idle", "entree_exterieure", duration_seconds=1
    )
    clock.advance(122)
    report = LocalGuardian(
        conn, world_id, log_path=tmp_path / "guardian.jsonl", clock=clock
    ).inspect()
    assert report.status == "CRITIQUE"
    deadline = next(check for check in report.checks if check.key == "runtime_deadlines")
    assert deadline.level == "critical" and "luna:idle" in deadline.detail
    conn.close()


def test_guardian_marks_a_dead_control_server_critical(tmp_path):
    clock = Clock()
    conn, world_id = _world(clock)
    report = LocalGuardian(
        conn,
        world_id,
        log_path=tmp_path / "guardian.jsonl",
        service_probe=lambda: False,
        clock=clock,
    ).inspect()
    assert report.status == "CRITIQUE"
    assert next(check for check in report.checks if check.key == "control_server").level == "critical"
    conn.close()


def test_guardian_accepts_the_runtime_session_it_owns(tmp_path):
    clock = Clock()
    conn, world_id = _world(clock)
    session = RuntimeSessionService(conn, clock=clock).start(world_id)
    report = LocalGuardian(
        conn, world_id, log_path=tmp_path / "guardian.jsonl", clock=clock,
        runtime_session_id=session.session_id,
    ).inspect()
    assert report.status == "SAIN"
    consistency = next(check for check in report.checks if check.key == "runtime_consistency")
    assert consistency.level == "ok"
    conn.close()


def test_guardian_rejects_a_replaced_runtime_session(tmp_path):
    clock = Clock()
    conn, world_id = _world(clock)
    session = RuntimeSessionService(conn, clock=clock).start(world_id)
    report = LocalGuardian(
        conn, world_id, log_path=tmp_path / "guardian.jsonl", clock=clock,
        runtime_session_id=session.session_id + 1,
    ).inspect()
    assert report.status == "CRITIQUE"
    consistency = next(check for check in report.checks if check.key == "runtime_consistency")
    assert consistency.level == "critical"
    conn.close()


def test_runtime_schema_rejects_multiple_open_sessions(tmp_path):
    clock = Clock()
    conn, world_id = _world(clock)
    RuntimeSessionService(conn, clock=clock).start(world_id)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO runtime_session "
            "(public_id, world_id, started_at, last_heartbeat_at, last_canonical_at) "
            "VALUES ('guardian-second-session', ?, ?, ?, ?)",
            (world_id, clock.now_iso(), clock.now_iso(), clock.now_iso()),
        )
    conn.close()
