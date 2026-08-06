import pytest

from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.cognition import CognitionContextService
from vivarium.repro import subjective_social_audit
from vivarium.social import SocialError, SocialService
from vivarium.subjective_memory import SubjectiveMemoryService
from vivarium.traversal import TraversalEngine


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world_id = IntegrationWorldService(conn).create_initial_world()["id"]
    yield conn, world_id, SocialService(conn)
    conn.close()


def _sophie_trace(conn, world_id):
    seq = conn.execute("SELECT MAX(seq) FROM canonical_event WHERE world_id = ?", (world_id,)).fetchone()[0] + 1
    TraversalEngine(conn).traverse_character(world_id, "sophie", "porte_entree", "salon")
    SubjectiveMemoryService(conn).encode_direct_event(world_id, "sophie", "saw_move", seq)


def test_relationship_is_directional_sourced_bounded_and_immutable(setup):
    conn, world_id, social = setup
    _sophie_trace(conn, world_id)
    view = social.adjust_relationship(world_id, "sophie", "erika", "saw_erika", trace_request_key="saw_move", impact={"familiarity_milli": 100, "trust_milli": 20})
    assert view["dimensions"]["familiarity_milli"] == 100
    assert social.relationship(world_id, "erika", "sophie") is None
    assert social.adjust_relationship(world_id, "sophie", "erika", "same_trace", trace_request_key="saw_move", impact={"trust_milli": 20}) == view
    row = conn.execute("SELECT id FROM relationship_view WHERE world_id = ?", (world_id,)).fetchone()
    with pytest.raises(Exception):
        conn.execute("UPDATE relationship_view SET dimensions_json = '{}' WHERE id = ?", (row["id"],))
    with pytest.raises(SocialError) as raised:
        social.adjust_relationship(world_id, "erika", "sophie", "steal", trace_request_key="saw_move", impact={"trust_milli": 20})
    assert raised.value.code == "relationship_source_not_accessible"


def test_boundaries_and_permissions_are_explicit_reversible_and_not_relationship_scores(setup):
    conn, world_id, social = setup
    boundary = social.declare_boundary(world_id, "sophie", "no_uninvited_room", domain="space", scope={"location": "chambre_sophie"})
    assert boundary["status"] == "active"
    assert social.revoke_boundary(world_id, "sophie", "no_uninvited_room", reason="changed_mind")["status"] == "revoked"
    permission = social.grant_permission(world_id, "sophie", "erika", "erika_room_visit", action_key="enter_room", scope={"location": "chambre_sophie"})
    assert permission["status"] == "granted"
    assert social.has_active_permission(world_id, "sophie", "erika", action_key="enter_room", scope={"location": "chambre_sophie"})
    assert not social.has_active_permission(world_id, "sophie", "erika", action_key="enter_room", scope={"location": "salon"})
    assert social.revoke_permission(world_id, "sophie", "erika", "erika_room_visit", reason="visit_over")["status"] == "revoked"
    assert not social.has_active_permission(world_id, "sophie", "erika", action_key="enter_room", scope={"location": "chambre_sophie"})
    row = conn.execute("SELECT id FROM situational_permission WHERE world_id = ?", (world_id,)).fetchone()
    with pytest.raises(Exception):
        conn.execute("UPDATE situational_permission SET status = 'granted' WHERE id = ?", (row["id"],))


def test_personal_boundary_does_not_create_a_canonical_physical_block(setup):
    _, world_id, social = setup
    social.declare_boundary(world_id, "sophie", "no_uninvited_room", domain="space", scope={"location": "chambre_sophie"})
    assert social.relationship(world_id, "sophie", "erika") is None
    assert not social.has_active_permission(world_id, "sophie", "erika", action_key="enter_room", scope={"location": "chambre_sophie"})


def test_cognition_context_receives_only_its_own_relationships_and_boundaries(setup):
    conn, world_id, social = setup
    _sophie_trace(conn, world_id)
    social.adjust_relationship(world_id, "sophie", "erika", "saw_erika", trace_request_key="saw_move", impact={"familiarity_milli": 100})
    social.declare_boundary(world_id, "sophie", "no_uninvited_room", domain="space", scope={"location": "chambre_sophie"})
    sophie = CognitionContextService(conn).build(world_id, "sophie")
    erika = CognitionContextService(conn).build(world_id, "erika")
    assert sophie.relationships[0]["target_character_key"] == "erika"
    assert sophie.boundaries[0]["boundary_key"] == "no_uninvited_room"
    assert erika.relationships == () and erika.boundaries == ()


def test_social_audit_accepts_sourced_directional_state(setup):
    conn, world_id, social = setup
    _sophie_trace(conn, world_id)
    social.adjust_relationship(world_id, "sophie", "erika", "saw_erika", trace_request_key="saw_move", impact={"familiarity_milli": 100})
    social.declare_boundary(world_id, "sophie", "no_uninvited_room", domain="space", scope={"location": "chambre_sophie"})
    social.grant_permission(world_id, "sophie", "erika", "erika_room_visit", action_key="enter_room", scope={"location": "chambre_sophie"})
    assert subjective_social_audit(conn, world_id) == []
