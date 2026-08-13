from datetime import datetime, timezone

import pytest

from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.scene_scheduler import SceneSchedulerError, SceneTurnScheduler
from vivarium.scenes import SocialSceneService
from vivarium.traversal import TraversalEngine
from vivarium.util import to_iso


class Clock:
    def now(self): return datetime(2026, 8, 6, 23, tzinfo=timezone.utc)
    def now_iso(self): return to_iso(self.now())


def test_scheduler_rotates_bounded_opportunities_from_admitted_turns():
    conn = connect_database(":memory:"); ensure_schema(conn); clock = Clock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    for key in ("sophie", "erika"): TraversalEngine(conn, clock=clock).traverse_character(world_id, key, "porte_entree", "salon")
    SocialSceneService(conn, clock=clock).open(world_id, "chat", ["sophie", "erika"])
    scheduler = SceneTurnScheduler(conn)
    first = scheduler.next_opportunity(world_id, "chat", max_turns=2)
    assert (first.turn_number, first.speaker_key, first.turn_key) == (1, "sophie", "scene-chat-turn-1")
    conn.execute("INSERT INTO cognition_call_admission (public_id,world_id,character_id,trigger,source_key,idempotency_key,admitted_at) SELECT 'x',?,id,'scene_turn',?,'sophie:scene_turn:scene-chat-turn-1','2026-08-06T23:00:00+00:00' FROM character WHERE world_id=? AND key='sophie'", (world_id, first.turn_key, world_id))
    second = scheduler.next_opportunity(world_id, "chat", max_turns=2)
    assert (second.turn_number, second.speaker_key) == (2, "erika")
    conn.close()


@pytest.mark.parametrize("maximum", (0, 21, True))
def test_scheduler_refuses_invalid_bounds(maximum):
    conn = connect_database(":memory:"); ensure_schema(conn); world_id = IntegrationWorldService(conn).create_initial_world()["id"]
    with pytest.raises(SceneSchedulerError) as raised: SceneTurnScheduler(conn).next_opportunity(world_id, "missing", max_turns=maximum)
    assert raised.value.code == "invalid_scene_scheduler"
    conn.close()
