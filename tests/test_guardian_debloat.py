from datetime import datetime, timedelta, timezone

from vivarium.db import connect_database
from vivarium.guardian import LocalGuardian
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.util import to_iso
from vivarium.world import WorldEngine


class Clock:
    def __init__(self):
        self.current = datetime(2026, 8, 7, 4, tzinfo=timezone.utc)

    def now(self):
        return self.current

    def now_iso(self):
        return to_iso(self.current)

    def advance(self, seconds):
        self.current += timedelta(seconds=seconds)


def test_canonical_event_does_not_force_guardian_recheck(tmp_path):
    clock = Clock()
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    guardian = LocalGuardian(conn, world_id, log_path=tmp_path / "guardian.jsonl", clock=clock)

    assert guardian.run_if_due() is not None
    WorldEngine(conn, clock=clock).rename_world(world_id, "changed")
    assert guardian.run_if_due() is None
    clock.advance(3600)
    assert guardian.run_if_due() is not None
    conn.close()
