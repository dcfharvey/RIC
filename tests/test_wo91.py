from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from vivarium.active_simulation import ActiveSimulationEngine
from vivarium.location_plans import LocationPlanService
from vivarium.rodage_v2_official import OfficialBootstrapError, bootstrap_official
from vivarium.runtime_session import RuntimeSessionService
from vivarium.util import Clock, to_iso


class FakeClock(Clock):
    def __init__(self, value: datetime):
        self.current = value

    def now(self):
        return self.current


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 8, 13, hour, minute, tzinfo=timezone.utc)


def test_wo91_sophie_due_boundary_is_causal_and_idempotent(tmp_path: Path):
    db = tmp_path / "rodage-v2.sqlite"
    clock = FakeClock(_at(15))
    report = bootstrap_official(db, clock=clock, launch_runtime=False, provider_checker=lambda: "qwen3-14b")
    import sqlite3
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    try:
        RuntimeSessionService(conn, clock=clock).start(report.world_id)
        before = conn.execute(
            "SELECT l.key FROM character c JOIN location l ON l.id=c.current_location_id "
            "WHERE c.world_id=? AND c.key='sophie'", (report.world_id,)
        ).fetchone()[0]
        assert before == "lieu_travail"
        clock.current = _at(15, 30)
        ActiveSimulationEngine(conn, clock=clock).run_to(report.world_id, to_iso(clock.current))
        assert conn.execute(
            "SELECT l.key FROM character c JOIN location l ON l.id=c.current_location_id "
            "WHERE c.world_id=? AND c.key='sophie'", (report.world_id,)
        ).fetchone()[0] == "lieu_travail"
        assert conn.execute("SELECT COUNT(*) FROM character_location_plan_resolution").fetchone()[0] == 0
        clock.current = _at(20)
        first = ActiveSimulationEngine(conn, clock=clock).run_to(report.world_id, to_iso(clock.current), max_transitions=10_000)
        assert first.transitions >= 1
        assert conn.execute(
            "SELECT l.key FROM character c JOIN location l ON l.id=c.current_location_id "
            "WHERE c.world_id=? AND c.key='sophie'", (report.world_id,)
        ).fetchone()[0] == "entree_exterieure"
        resolution_count = conn.execute("SELECT COUNT(*) FROM character_location_plan_resolution").fetchone()[0]
        assert resolution_count == 1
        second = ActiveSimulationEngine(conn, clock=clock).run_to(report.world_id, to_iso(clock.current))
        assert second.transitions == 0
        assert conn.execute("SELECT COUNT(*) FROM character_location_plan_resolution").fetchone()[0] == resolution_count
    finally:
        conn.close()


def test_wo91_work_is_generic_and_profiles_are_provenanced(tmp_path: Path):
    db = tmp_path / "rodage-v2.sqlite"
    report = bootstrap_official(db, clock=FakeClock(_at(15)), launch_runtime=False, provider_checker=lambda: "qwen3-14b")
    import sqlite3
    conn = sqlite3.connect(str(db)); conn.row_factory = sqlite3.Row
    try:
        activity = conn.execute(
            "SELECT a.type FROM activity a JOIN character c ON c.id=a.character_id "
            "WHERE c.world_id=? AND c.key='sophie' AND a.status='active'", (report.world_id,)
        ).fetchone()[0]
        assert activity == "work"
        assert conn.execute("SELECT 1 FROM activity WHERE type='photography' AND status='active'").fetchone() is None
        rows = conn.execute(
            "SELECT c.key,p.evidence_class FROM character_sleep_biology_assignment a "
            "JOIN character c ON c.id=a.character_id JOIN sleep_biology_profile p ON p.id=a.profile_id "
            "WHERE c.world_id=? ORDER BY c.key", (report.world_id,)
        ).fetchall()
        assert {row["key"]: row["evidence_class"] for row in rows} == {
            "sophie": "human_reference", "erika": "human_reference", "patoune": "generic_feline",
            "luna": "fictional_canon", "chuu": "fictional_canon",
        }
    finally:
        conn.close()


def test_wo91_official_entry_refuses_existing_target_and_late_t0(tmp_path: Path):
    existing = tmp_path / "rodage-v2.sqlite"
    existing.write_bytes(b"sentinel")
    with pytest.raises(OfficialBootstrapError) as exc:
        bootstrap_official(existing, clock=FakeClock(_at(15)), launch_runtime=False, provider_checker=lambda: "qwen3-14b")
    assert exc.value.code == "target_exists"
    late = tmp_path / "late.sqlite"
    with pytest.raises(OfficialBootstrapError) as exc:
        bootstrap_official(late, clock=FakeClock(_at(20)), launch_runtime=False, provider_checker=lambda: "qwen3-14b")
    assert exc.value.code == "t0_after_return_deadline"
    assert not late.exists()
