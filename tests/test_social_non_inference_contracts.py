"""Contrats nucléaires : une expression sociale n'est jamais sa conséquence."""

from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.scenes import SocialSceneService
from vivarium.social import SocialService
from vivarium.subjective_memory import SubjectiveMemoryService
from vivarium.traversal import TraversalEngine


def test_speech_kinds_never_infer_belief_relation_permission_or_affect():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world_id = IntegrationWorldService(conn).create_initial_world()["id"]
    scenes = SocialSceneService(conn)
    scenes.open(world_id, "contract_scene", ("sophie", "erika"))
    protected = (
        "subjective_belief", "relationship_view", "situational_permission",
        "mood_state", "emotion_episode",
    )
    before = {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in protected}
    for number, (kind, content) in enumerate((
        ("inform", "Tu es brillante aujourd'hui."),
        ("decline", "Non merci."),
        ("apologize", "Je suis désolée."),
    )):
        scenes.speak(world_id, "contract_scene", f"contract_{number}", "sophie",
                     act_kind=kind, content=content, recipient_key="erika")
    after = {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in protected}
    assert after == before
    conn.close()


def test_positive_relationship_never_implies_permission_or_consent_state():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world_id = IntegrationWorldService(conn).create_initial_world()["id"]
    memory = SubjectiveMemoryService(conn)
    event_seq = conn.execute(
        "SELECT MAX(seq) FROM canonical_event WHERE world_id = ?", (world_id,)
    ).fetchone()[0] + 1
    TraversalEngine(conn).traverse_character(
        world_id, "sophie", "porte_entree", "salon"
    )
    memory.encode_direct_event(world_id, "sophie", "positive_history", event_seq)
    social = SocialService(conn)
    social.adjust_relationship(
        world_id, "sophie", "erika", "positive_history_evidence",
        trace_request_key="positive_history", impact={"trust_milli": 200, "affection_milli": 200},
    )
    assert not social.has_active_permission(
        world_id, "sophie", "erika", action_key="enter_room",
        scope={"location": "chambre_sophie"},
    )
    assert conn.execute("SELECT COUNT(*) FROM situational_permission").fetchone()[0] == 0
    conn.close()
