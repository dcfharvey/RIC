import pytest

from vivarium.db import connect_database
from vivarium.goals import GoalError, GoalService
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema


@pytest.fixture
def setup():
    conn = connect_database(":memory:"); ensure_schema(conn)
    world_id = IntegrationWorldService(conn).create_initial_world()["id"]
    yield conn, world_id, GoalService(conn)
    conn.close()


def test_goal_is_subjective_and_active_intention_is_stable_until_replaced(setup):
    conn, world_id, goals = setup
    created = goals.create_goal(world_id, "sophie", "restore_repos", family="immediate", target={"need": "repos"}, source_kind="physiological_regulation", success_conditions={"need_at_least_milli": 70000}, perceived_feasibility_milli=900, importance_milli=800, urgency_milli=700)
    assert created["status"] == "candidate"
    goals.adopt_intention(world_id, "sophie", "restore_repos", "rest_in_room", plan={"kind": "rest"}, resume_context={"step": "start", "location": "salon"})
    goals.create_goal(world_id, "sophie", "check_phone", family="immediate", target={"object": "telephone_sophie"}, source_kind="preference", success_conditions={"checked": True}, perceived_feasibility_milli=1000, importance_milli=300, urgency_milli=100)
    goals.adopt_intention(world_id, "sophie", "check_phone", "check_phone_now", plan={"kind": "inspect"}, resume_context={"step": "start"})
    rows = conn.execute("SELECT intention_key, status FROM subjective_intention WHERE world_id = ? ORDER BY id", (world_id,)).fetchall()
    assert [(row["intention_key"], row["status"]) for row in rows] == [("rest_in_room", "interrupted"), ("check_phone_now", "active")]
    assert goals.active_intention(world_id, "sophie")["intention_key"] == "check_phone_now"
    assert conn.execute("SELECT COUNT(*) FROM subjective_goal_event WHERE world_id = ?", (world_id,)).fetchone()[0] == 4


def test_goal_refusal_leaves_no_partial_subjective_state(setup):
    conn, world_id, goals = setup
    with pytest.raises(GoalError) as raised:
        goals.create_goal(world_id, "sophie", "broken", family="unknown", target={}, source_kind="invalid", success_conditions={}, perceived_feasibility_milli=1, importance_milli=1, urgency_milli=1)
    assert raised.value.code == "invalid_goal"
    assert conn.execute("SELECT COUNT(*) FROM subjective_goal WHERE world_id = ?", (world_id,)).fetchone()[0] == 0
