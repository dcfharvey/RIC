from datetime import datetime, timezone

from vivarium.activities import ActivityEngine
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.scenes import SocialSceneService
from vivarium.telemetry import RuntimeOutcomeLog, inspect_rodage
from vivarium.util import to_iso


class Clock:
    def now(self): return datetime(2026, 8, 7, 12, tzinfo=timezone.utc)
    def now_iso(self): return to_iso(self.now())


def _world():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world_id = IntegrationWorldService(conn, clock=Clock()).create_initial_world()["id"]
    return conn, world_id


def test_rodage_snapshot_is_read_only_and_flags_repeated_dialogue():
    conn, world_id = _world()
    scenes = SocialSceneService(conn, clock=Clock())
    scenes.open(world_id, "repeat_scene", ("sophie", "erika"))
    for number in range(6):
        scenes.speak(world_id, "repeat_scene", f"turn_{number}", "sophie",
                     act_kind="greet", content="Ah, tu es là.", recipient_key="erika")
    before = conn.total_changes
    snapshot = inspect_rodage(conn, world_id)
    assert conn.total_changes == before
    assert snapshot.speech_acts == 6 and snapshot.distinct_utterances == 1
    assert "dialogue_repetition" in {warning.key for warning in snapshot.warnings}
    conn.close()


def test_rodage_snapshot_flags_activity_monoculture_only_after_evidence():
    conn, world_id = _world()
    activities = ActivityEngine(conn, clock=Clock())
    for number in range(8):
        activities.start_activity(world_id, "luna", "idle", "entree_exterieure",
                                  duration_seconds=1, sim_now=f"2026-08-07T12:00:{number:02d}.000+00:00")
        activities.abort_activity(world_id, "luna", sim_now=f"2026-08-07T12:00:{number:02d}.500+00:00")
    snapshot = inspect_rodage(conn, world_id)
    assert "activity_monoculture" in {warning.key for warning in snapshot.warnings}
    conn.close()


def test_runtime_outcome_log_is_append_only_jsonl(tmp_path):
    path = tmp_path / "runtime_outcomes.jsonl"
    log = RuntimeOutcomeLog(path)
    log.append(checked_at="2026-08-07T12:00:00.000+00:00", cycle="social",
               character="sophie", outcome="invalid",
               provider_error="invalid_scene_turn_response")
    log.append(checked_at="2026-08-07T12:01:00.000+00:00", cycle="autonomy",
               character="erika", outcome="accepted")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 and "invalid_scene_turn_response" in lines[0]
