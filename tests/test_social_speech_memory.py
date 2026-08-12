import pytest

from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import subjective_trace_audit, subjective_trace_digest
from vivarium.scenes import SocialSceneService
from vivarium.subjective_memory import SubjectiveMemoryError, SubjectiveMemoryService
from vivarium.traversal import TraversalEngine


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    assert ensure_schema(conn) == 54
    world_id = IntegrationWorldService(conn).create_initial_world()["id"]
    yield conn, world_id
    conn.close()


def _at_salon(conn, world_id, *keys):
    traversal = TraversalEngine(conn)
    for key in keys:
        traversal.traverse_character(world_id, key, "porte_entree", "salon")


def test_direct_recipient_and_non_target_participant_can_encode_exact_expression(setup):
    conn, world_id = setup
    _at_salon(conn, world_id, "sophie", "erika", "luna")
    scenes = SocialSceneService(conn)
    scenes.open(world_id, "three_way", ("sophie", "erika", "luna"))
    scenes.speak(
        world_id, "three_way", "act_1", "sophie", act_kind="inform",
        content="Sophie exprime une assertion.", recipient_key="erika",
    )
    memory = SubjectiveMemoryService(conn)

    erika = memory.encode_social_speech(world_id, "erika", "hear_1", "three_way", "act_1")
    luna = memory.encode_social_speech(world_id, "luna", "hear_2", "three_way", "act_1")

    for trace in (erika, luna):
        assert trace["fact_type"] == "social_speech_act"
        assert trace["payload"]["content"] == "Sophie exprime une assertion."
        assert trace["payload"]["speaker_key"] == "sophie"
        assert trace["payload"]["recipient_key"] == "erika"
        assert trace["access_kind"] == "social_scene_participant"
        assert trace["source_social_speech_act_id"] is not None


def test_speaker_can_encode_own_speech_and_co_present_non_participant_cannot(setup):
    conn, world_id = setup
    _at_salon(conn, world_id, "sophie", "erika", "luna")
    scenes = SocialSceneService(conn)
    scenes.open(world_id, "closed_pair", ("sophie", "erika"))
    scenes.speak(world_id, "closed_pair", "act_1", "sophie", act_kind="greet", content="Bonjour.")
    memory = SubjectiveMemoryService(conn)

    own = memory.encode_social_speech(world_id, "sophie", "own_1", "closed_pair", "act_1")
    assert own["payload"]["speaker_key"] == "sophie"
    with pytest.raises(SubjectiveMemoryError) as raised:
        memory.encode_social_speech(world_id, "luna", "outside_1", "closed_pair", "act_1")
    assert raised.value.code == "source_not_accessible"


def test_closed_scene_and_later_movement_do_not_erase_historical_access(setup):
    conn, world_id = setup
    _at_salon(conn, world_id, "sophie", "erika")
    scenes = SocialSceneService(conn)
    scenes.open(world_id, "historical", ("sophie", "erika"))
    scenes.speak(world_id, "historical", "act_1", "erika", act_kind="ask", content="Toujours là?")
    scenes.close(world_id, "historical", reason="completed")
    TraversalEngine(conn).traverse_character(world_id, "erika", "porte_entree", "entree_exterieure")
    TraversalEngine(conn).traverse_character(world_id, "sophie", "porte_entree", "entree_exterieure")

    trace = SubjectiveMemoryService(conn).encode_social_speech(
        world_id, "sophie", "historical_1", "historical", "act_1"
    )
    assert trace["payload"]["content"] == "Toujours là?"


def test_social_speech_source_is_reread_and_request_is_idempotent_with_conflict(setup):
    conn, world_id = setup
    _at_salon(conn, world_id, "sophie", "erika")
    scenes = SocialSceneService(conn)
    scenes.open(world_id, "integrity", ("sophie", "erika"))
    scenes.speak(world_id, "integrity", "act_1", "sophie", act_kind="inform", content="Source réelle.")
    scenes.speak(world_id, "integrity", "act_2", "sophie", act_kind="inform", content="Autre source.")
    memory = SubjectiveMemoryService(conn)

    trace = memory.encode_social_speech(world_id, "erika", "same_key", "integrity", "act_1")
    assert memory.encode_social_speech(world_id, "erika", "same_key", "integrity", "act_1") == trace
    with pytest.raises(SubjectiveMemoryError) as raised:
        memory.encode_social_speech(world_id, "erika", "same_key", "integrity", "act_2")
    assert raised.value.code == "request_key_conflict"
    with pytest.raises(SubjectiveMemoryError) as raised:
        memory.encode_social_speech(world_id, "erika", "fake", "integrity", "missing")
    assert raised.value.code == "source_not_accessible"


def test_social_speech_encoding_is_not_a_causal_inference_and_is_auditable(setup):
    conn, world_id = setup
    _at_salon(conn, world_id, "sophie", "erika")
    scenes = SocialSceneService(conn)
    scenes.open(world_id, "anti_inference", ("sophie", "erika"))
    scenes.speak(world_id, "anti_inference", "act_1", "sophie", act_kind="apologize", content="Pardon.")
    protected = (
        "subjective_belief", "relationship_view", "situational_permission",
        "mood_state", "emotion_episode",
    )
    before = {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in protected}
    trace = SubjectiveMemoryService(conn).encode_social_speech(
        world_id, "erika", "anti_1", "anti_inference", "act_1"
    )
    after = {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in protected}
    assert after == before
    assert subjective_trace_audit(conn, world_id) == []
    digest = subjective_trace_digest(conn, world_id)
    assert digest["erika"][0]["source_social_speech_act_id"] == trace["source_social_speech_act_id"]
