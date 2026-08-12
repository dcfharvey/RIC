"""Fondations inactives : politiques, liens subjectifs et audit prive seulement."""

from datetime import datetime, timezone

import pytest

from vivarium.action_arbitration import ActionArbitrationError, ActionArbitrationFoundationService
from vivarium.db import connect_database, transaction
from vivarium.goals import GoalError, GoalService
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema, load_migrations, split_sql_statements
from vivarium.util import to_iso


T0 = datetime(2026, 8, 11, 12, tzinfo=timezone.utc)


class FakeClock:
    def now(self): return T0
    def now_iso(self): return to_iso(T0)


def _policy():
    # Configuration de banc seulement : aucune echelle de production n'est choisie ici.
    return {"schema_version": 1, "source_mappings": {}, "correlation_groups": {}, "aggregation": {}, "current_action_inertia": {}, "quasi_equality": {}, "reassessment": {}}


def _apply_through(conn, version):
    conn.execute("CREATE TABLE migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL, checksum TEXT NOT NULL)")
    for migration in load_migrations():
        if migration.version <= version:
            with transaction(conn):
                for statement in split_sql_statements(migration.sql): conn.execute(statement)
                conn.execute("INSERT INTO migrations (version,name,applied_at,checksum) VALUES (?,?,?,?)",(migration.version,migration.name,to_iso(T0),migration.checksum))


@pytest.fixture
def setup():
    conn=connect_database(":memory:"); ensure_schema(conn); clock=FakeClock()
    world=IntegrationWorldService(conn,clock=clock).create_initial_world(); service=ActionArbitrationFoundationService(conn,clock=clock)
    policy=service.register_policy("synthetic.arbitration.v1",1,_policy(),"synthetic_calibration_only")
    try: yield conn,world["id"],service,policy
    finally: conn.close()


def test_policy_assignment_and_private_audit_are_immutable_and_noncanonical(setup):
    conn, world, service, policy = setup
    before=conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id=?",(world,)).fetchone()[0]
    assert service.assign_policy(world,policy.policy_key,policy.version,"synthetic_world_setup") == policy
    audit_id=service.record_private_audit(world,frame_digest="a"*64,options=[{"action_key":"opaque"}],sources=[{"owner":"GoalService"}],result={"status":"shadow_only"},canonical_at=to_iso(T0),reason_code="synthetic_probe")
    assert audit_id > 0
    assert conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id=?",(world,)).fetchone()[0] == before
    with pytest.raises(Exception,match="immutable"): conn.execute("UPDATE action_arbitration_policy SET provenance='mutated'")
    with pytest.raises(Exception,match="append-only"): conn.execute("DELETE FROM action_arbitration_audit WHERE id=?",(audit_id,))


def test_policy_requires_all_explicit_conceptual_sections(setup):
    _conn,_world,service,_policy_value=setup
    incomplete=_policy(); incomplete.pop("reassessment")
    with pytest.raises(ActionArbitrationError) as raised: service.register_policy("synthetic.incomplete.v1",1,incomplete,"test")
    assert raised.value.code == "invalid_configuration"


def test_explicit_intention_link_uses_closed_action_vocabulary_without_parsing_plan(setup):
    conn,world,_service,_policy_value=setup; goals=GoalService(conn,clock=FakeClock())
    before=conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id=?",(world,)).fetchone()[0]
    goals.create_goal(world,"sophie","opaque_goal",family="immediate",target={},source_kind="test",success_conditions={},perceived_feasibility_milli=1,importance_milli=2,urgency_milli=3)
    goals.adopt_intention(world,"sophie","opaque_goal","opaque_intention",plan={"not_an_action":"never_parse"},resume_context={"also":"opaque"})
    linked=goals.link_intention_action(world,"sophie","opaque_intention",action_kind="start_activity",params={"activity_type":"gaming","target_location_key":"salon"},subjective_strength_milli=700,provenance="subjective_declaration")
    assert linked["action_kind"] == "start_activity" and len(linked["action_key"]) == 64
    assert goals.intention_action_links(world,"sophie","opaque_intention")[0]["params"] == {"activity_type":"gaming","target_location_key":"salon"}
    assert conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id=?",(world,)).fetchone()[0] == before
    with pytest.raises(GoalError) as duplicate:
        goals.link_intention_action(world,"sophie","opaque_intention",action_kind="start_activity",params={"activity_type":"gaming","target_location_key":"salon"},subjective_strength_milli=700,provenance="subjective_declaration")
    assert duplicate.value.code == "duplicate_intention_action_link"


def test_intention_link_rejects_other_owner_and_malformed_action_without_writes(setup):
    conn,world,_service,_policy_value=setup; goals=GoalService(conn,clock=FakeClock())
    goals.create_goal(world,"sophie","s_goal",family="immediate",target={},source_kind="test",success_conditions={},perceived_feasibility_milli=1,importance_milli=1,urgency_milli=1)
    goals.adopt_intention(world,"sophie","s_goal","s_intention",plan={},resume_context={})
    before=conn.execute("SELECT COUNT(*) FROM subjective_intention_action_link").fetchone()[0]
    with pytest.raises(GoalError) as wrong_owner: goals.link_intention_action(world,"erika","s_intention",action_kind="traverse",params={"connector_key":"porte_entree","target_location_key":"salon"},subjective_strength_milli=1,provenance="test")
    assert wrong_owner.value.code == "intention_not_found"
    with pytest.raises(GoalError) as malformed: goals.link_intention_action(world,"sophie","s_intention",action_kind="teleport",params={},subjective_strength_milli=1,provenance="test")
    assert malformed.value.code == "unsupported_action"
    assert conn.execute("SELECT COUNT(*) FROM subjective_intention_action_link").fetchone()[0] == before


def test_forward_migration_from_50_creates_no_policy_link_audit_or_canonical_history():
    conn=connect_database(":memory:")
    try:
        _apply_through(conn,50); world=IntegrationWorldService(conn,clock=FakeClock()).create_initial_world()
        before=conn.execute("SELECT COUNT(*),MAX(seq) FROM canonical_event WHERE world_id=?",(world["id"],)).fetchone()
        assert ensure_schema(conn) == 55
        assert conn.execute("SELECT COUNT(*) FROM action_arbitration_policy").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM subjective_intention_action_link").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM action_arbitration_audit").fetchone()[0] == 0
        after=conn.execute("SELECT COUNT(*),MAX(seq) FROM canonical_event WHERE world_id=?",(world["id"],)).fetchone()
        assert tuple(after) == tuple(before)
    finally: conn.close()
