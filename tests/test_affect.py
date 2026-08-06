import pytest

from vivarium.affect import AffectError, AffectService
from vivarium.cognition import CognitionContextService
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import subjective_affect_audit, subjective_affect_digest
from vivarium.subjective_memory import SubjectiveMemoryService
from vivarium.traversal import TraversalEngine


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world_id = IntegrationWorldService(conn).create_initial_world()["id"]
    yield conn, world_id, AffectService(conn)
    conn.close()


def _sophie_trace(conn, world_id):
    seq = conn.execute("SELECT MAX(seq) FROM canonical_event WHERE world_id = ?", (world_id,)).fetchone()[0] + 1
    TraversalEngine(conn).traverse_character(world_id, "sophie", "porte_entree", "salon")
    SubjectiveMemoryService(conn).encode_direct_event(world_id, "sophie", "saw_move", seq)


def test_mood_is_private_eventful_and_bounded(setup):
    conn, world_id, affect = setup
    assert affect.mood(world_id, "sophie") is None
    assert affect.set_mood(world_id, "sophie", valence_milli=-200, activation_milli=350, reason="arrival") == {
        "valence_milli": -200, "activation_milli": 350,
    }
    assert affect.set_mood(world_id, "sophie", valence_milli=100, activation_milli=100, reason="settled") == {
        "valence_milli": 100, "activation_milli": 100,
    }
    row = conn.execute("SELECT id FROM mood_state WHERE world_id = ?", (world_id,)).fetchone()
    with pytest.raises(Exception):
        conn.execute("UPDATE mood_state SET valence_milli = 999 WHERE id = ?", (row["id"],))
    assert conn.execute("SELECT COUNT(*) FROM mood_event WHERE world_id = ?", (world_id,)).fetchone()[0] == 2


def test_emotion_requires_private_cause_and_keeps_audited_resolution(setup):
    conn, world_id, affect = setup
    with pytest.raises(AffectError) as raised:
        affect.start_episode(world_id, "sophie", "arrival_fear", family="fear", appraisal={}, cause_trace_key="missing", intensity_milli=600, action_tendency="withdraw", expression_milli=100)
    assert raised.value.code == "affect_source_not_accessible"
    _sophie_trace(conn, world_id)
    episode = affect.start_episode(
        world_id, "sophie", "arrival_fear", family="fear", appraisal={"novelty": 800},
        cause_trace_key="saw_move", intensity_milli=600, action_tendency="withdraw", expression_milli=100,
        target_character_key="erika",
    )
    assert episode["status"] == "active" and episode["target_character_key"] == "erika"
    assert affect.resolve_episode(world_id, "sophie", "arrival_fear", reason="safe_now")["status"] == "resolved"
    assert affect.active_episodes(world_id, "sophie") == ()
    row = conn.execute("SELECT id FROM emotion_episode WHERE world_id = ?", (world_id,)).fetchone()
    with pytest.raises(Exception):
        conn.execute("UPDATE emotion_episode SET intensity_milli = 1 WHERE id = ?", (row["id"],))
    assert conn.execute("SELECT COUNT(*) FROM emotion_event WHERE world_id = ?", (world_id,)).fetchone()[0] == 2


def test_emotion_cannot_use_another_residents_trace(setup):
    conn, world_id, affect = setup
    _sophie_trace(conn, world_id)
    with pytest.raises(AffectError) as raised:
        affect.start_episode(world_id, "erika", "stolen_cause", family="anger", appraisal={}, cause_trace_key="saw_move", intensity_milli=300, action_tendency="confront", expression_milli=300)
    assert raised.value.code == "affect_source_not_accessible"


def test_cognition_context_has_only_own_affective_state(setup):
    conn, world_id, affect = setup
    affect.set_mood(world_id, "sophie", valence_milli=-200, activation_milli=350, reason="arrival")
    _sophie_trace(conn, world_id)
    affect.start_episode(world_id, "sophie", "arrival_fear", family="fear", appraisal={}, cause_trace_key="saw_move", intensity_milli=600, action_tendency="withdraw", expression_milli=100)
    sophie = CognitionContextService(conn).build(world_id, "sophie")
    erika = CognitionContextService(conn).build(world_id, "erika")
    assert sophie.mood == {"valence_milli": -200, "activation_milli": 350}
    assert sophie.emotions[0]["episode_key"] == "arrival_fear"
    assert erika.mood is None and erika.emotions == ()


def test_affect_digest_and_audit_are_subjective(setup):
    conn, world_id, affect = setup
    affect.set_mood(world_id, "sophie", valence_milli=-200, activation_milli=350, reason="arrival")
    _sophie_trace(conn, world_id)
    affect.start_episode(world_id, "sophie", "arrival_fear", family="fear", appraisal={}, cause_trace_key="saw_move", intensity_milli=600, action_tendency="withdraw", expression_milli=100)
    digest = subjective_affect_digest(conn, world_id)
    assert digest["moods"]["sophie"]["valence_milli"] == -200
    assert digest["episodes"][0]["episode_key"] == "arrival_fear"
    assert subjective_affect_audit(conn, world_id) == []
