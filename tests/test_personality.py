from datetime import datetime, timezone

import pytest

from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.personality import PersonalityError, PersonalityService, normalize_profile
from vivarium.repro import canonical_state_digest


class Clock:
    def now(self): return datetime(2026, 8, 6, 12, tzinfo=timezone.utc)
    def now_iso(self): return "2026-08-06T12:00:00Z"


@pytest.fixture
def setup():
    conn = connect_database(":memory:"); ensure_schema(conn); clock = Clock()
    world = IntegrationWorldService(conn, clock=clock).create_initial_world()
    yield conn, world["id"], clock
    conn.close()


def test_sapient_mvp_profiles_are_instantiated_from_immutable_template_v2(setup):
    conn, world_id, _ = setup
    personalities = PersonalityService(conn)
    sophie = personalities.read(world_id, "sophie")
    assert sophie is not None
    assert sophie["traits"]["conscientiousness"]["mean_milli"] == 730
    assert sophie["attachment"]["general"]["avoidance_milli"] == 620
    assert canonical_state_digest(conn, world_id)["character_personality_disposition"]["sophie"]["traits"]["openness"]["mean_milli"] == 700
    assert personalities.read(world_id, "patoune") is None
    version = conn.execute(
        "SELECT template_version FROM character_instance_origin o JOIN character c ON c.id = o.character_id "
        "WHERE o.world_id = ? AND c.key = 'sophie'", (world_id,)
    ).fetchone()["template_version"]
    assert version == 2
    with pytest.raises(Exception, match="immutable"):
        conn.execute("UPDATE character_personality_disposition SET traits_json = '{}' WHERE world_id = ?", (world_id,))


def test_personality_is_a_declarative_modulator_not_a_behavior_command(setup):
    conn, world_id, _ = setup
    personalities = PersonalityService(conn)
    modulation = personalities.situation_modulation(world_id, "erika", "social_context")
    assert set(modulation) == {"extraversion", "agreeableness", "conscientiousness", "openness", "stress_reactivity"}
    assert modulation["extraversion"] == 120
    assert personalities.situation_modulation(world_id, "erika", "unknown_context")["openness"] == 0


def test_invalid_profile_is_refused_before_any_instance_write():
    with pytest.raises(PersonalityError) as raised:
        normalize_profile({"traits": {}, "attachment": {}})
    assert raised.value.code == "invalid_personality_profile"
