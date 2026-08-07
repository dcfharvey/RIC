from datetime import datetime, timezone

import pytest

from vivarium.cognition_policy import CognitionCallLimits
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.scene_turn import SceneTurnDecision, SceneTurnError, SceneTurnService
from vivarium.scenes import SocialSceneService
from vivarium.traversal import TraversalEngine
from vivarium.util import to_iso


class Clock:
    def now(self):
        return datetime(2026, 8, 6, 22, tzinfo=timezone.utc)

    def now_iso(self):
        return to_iso(self.now())


class Provider:
    def __init__(self, decision):
        self.decision, self.calls, self.context = decision, 0, None

    def decide(self, context):
        self.calls += 1
        self.context = context
        return self.decision


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = Clock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    for character_key in ("sophie", "erika"):
        TraversalEngine(conn, clock=clock).traverse_character(world_id, character_key, "porte_entree", "salon")
    scenes = SocialSceneService(conn, clock=clock)
    scenes.open(world_id, "arrival_chat", ["sophie", "erika"])
    scenes.speak(world_id, "arrival_chat", "greet_1", "erika", act_kind="greet", content="Salut, Sophie.", recipient_key="sophie")
    yield conn, world_id, clock, scenes
    conn.close()


def test_scene_turn_admits_one_llm_turn_with_private_context_and_replay(setup):
    conn, world_id, clock, scenes = setup
    provider = Provider(SceneTurnDecision("speak", "answer", "Salut, Erika.", "erika"))
    service = SceneTurnService(conn, provider, clock=clock)
    limits = CognitionCallLimits(0, 3_600, 2)

    result = service.run(world_id, "arrival_chat", "sophie", "sophie_reply_1", limits)

    assert result.attempted and result.speech is not None and result.speech["content"] == "Salut, Erika."
    assert result.provider_error_code is None and result.validation_error_code is None
    assert provider.calls == 1
    assert {item["key"] for item in provider.context.participants} == {"sophie", "erika"}
    assert provider.context.recent_acts[-1]["content"] == "Salut, Sophie."
    assert conn.execute("SELECT COUNT(*) FROM cognition_call_admission").fetchone()[0] == 1

    replay = service.run(world_id, "arrival_chat", "sophie", "sophie_reply_1", limits)
    assert replay.replayed and replay.speech == result.speech and provider.calls == 1
    assert len(scenes.sheet(world_id, "arrival_chat")["acts"]) == 2


def test_scene_turn_rejects_a_recipient_outside_the_active_scene_without_speech(setup):
    conn, world_id, clock, scenes = setup
    provider = Provider(SceneTurnDecision("speak", "ask", "Luna est-elle là ?", "luna"))

    result = SceneTurnService(conn, provider, clock=clock).run(
        world_id, "arrival_chat", "sophie", "invalid_recipient", CognitionCallLimits(0, 3_600, 2)
    )

    assert result.attempted and result.speech is None
    assert result.validation_error_code == "scene_recipient_not_in_scene"
    assert len(scenes.sheet(world_id, "arrival_chat")["acts"]) == 1


def test_scene_turn_marks_a_bad_provider_response_without_expression(setup):
    conn, world_id, clock, scenes = setup
    provider = Provider(object())

    result = SceneTurnService(conn, provider, clock=clock).run(
        world_id, "arrival_chat", "sophie", "bad_response", CognitionCallLimits(0, 3_600, 2)
    )

    assert result.attempted and result.provider_error_code == "invalid_scene_turn_response"
    assert len(scenes.sheet(world_id, "arrival_chat")["acts"]) == 1


def test_scene_turn_duplicate_no_action_is_deferred_before_a_second_provider_call(setup):
    conn, world_id, clock, _ = setup
    provider = Provider(SceneTurnDecision("no_action"))
    service = SceneTurnService(conn, provider, clock=clock)
    limits = CognitionCallLimits(0, 3_600, 2)

    assert service.run(world_id, "arrival_chat", "sophie", "wait_1", limits).decision.action == "no_action"
    duplicate = service.run(world_id, "arrival_chat", "sophie", "wait_1", limits)

    assert provider.calls == 1 and duplicate.decision is None
    assert duplicate.deferred_reason_code == "duplicate_call"


def test_scene_turn_requires_an_active_colocated_scene_before_admission(setup):
    conn, world_id, clock, _ = setup
    TraversalEngine(conn, clock=clock).traverse_character(world_id, "erika", "porte_entree", "entree_exterieure")
    provider = Provider(SceneTurnDecision("no_action"))

    with pytest.raises(SceneTurnError) as raised:
        SceneTurnService(conn, provider, clock=clock).run(
            world_id, "arrival_chat", "sophie", "separated", CognitionCallLimits(0, 3_600, 2)
        )

    assert raised.value.code == "scene_participants_not_colocated"
    assert provider.calls == 0
    assert conn.execute("SELECT COUNT(*) FROM cognition_call_admission").fetchone()[0] == 0
