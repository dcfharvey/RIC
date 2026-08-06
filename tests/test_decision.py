import pytest

from vivarium.db import connect_database
from vivarium.decision import DecisionError, DecisionFrameService
from vivarium.goals import GoalService
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.policy import PolicyContext


def _context(character_key="sophie", repos=100000):
    return PolicyContext(character_key=character_key, needs={"satiete": 100000, "hygiene": 100000, "repos": repos, "energie": 100000}, need_remainders={"satiete": 0, "hygiene": 0, "repos": 0, "energie": 0}, effective_thresholds={"satiete": 60000, "hygiene": 60000, "repos": 60000, "energie": 60000}, current_location="salon", profile={}, rates={}, accessible={"sleep": {"chambre_sophie": 1}, "rest": {"salon": 0}, "eat": {}, "clean": {}})


@pytest.fixture
def setup():
    conn=connect_database(":memory:"); ensure_schema(conn); world_id=IntegrationWorldService(conn).create_initial_world()["id"]
    yield conn,world_id
    conn.close()


def test_frame_keeps_active_intention_ahead_of_new_motive(setup):
    conn,world_id=setup; goals=GoalService(conn)
    goals.create_goal(world_id,"sophie","rest_goal",family="immediate",target={},source_kind="physiological_regulation",success_conditions={},perceived_feasibility_milli=900,importance_milli=900,urgency_milli=900)
    goals.adopt_intention(world_id,"sophie","rest_goal","rest_now",plan={"kind":"rest"},resume_context={})
    frame=DecisionFrameService(conn).build(world_id,"sophie",_context(repos=1000))
    assert frame.dominant_reason_kind=="active_intention" and frame.dominant_reason_key=="rest_now"


def test_frame_uses_bounded_motive_without_writing_world(setup):
    conn,world_id=setup
    frame=DecisionFrameService(conn).build(world_id,"sophie",_context(repos=1000))
    assert frame.dominant_reason_kind=="motive" and frame.motives[0].target_need=="repos"
    with pytest.raises(DecisionError): DecisionFrameService(conn).build(world_id,"erika",_context("sophie"))
