import pytest

from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest
from vivarium.values import ValuesError, ValuesService, normalize_value_ranking


@pytest.fixture
def setup():
    conn = connect_database(":memory:"); ensure_schema(conn)
    world = IntegrationWorldService(conn).create_initial_world()
    yield conn, world["id"]
    conn.close()


def test_values_and_preferences_are_separate_immutable_profiles(setup):
    conn, world_id = setup
    profile = ValuesService(conn).read(world_id, "erika")
    assert profile is not None and profile["ranked_value_keys"][0] == "exploration_freedom"
    assert profile["preferences"] == [{"target_kind": "activity", "target_key": "gaming", "valence_milli": 900}, {"target_kind": "social_format", "target_key": "casual_group", "valence_milli": 550}]
    assert ValuesService(conn).read(world_id, "patoune") is None
    assert canonical_state_digest(conn, world_id)["character_values_preferences"]["luna"]["ranked_value_keys"][0] == "achievement"
    with pytest.raises(Exception, match="immutable"):
        conn.execute("UPDATE character_value_profile SET ranked_value_keys_json = '[]' WHERE world_id = ?", (world_id,))


def test_incomplete_value_hierarchy_is_refused():
    with pytest.raises(ValuesError) as raised: normalize_value_ranking(["autonomy"])
    assert raised.value.code == "invalid_values_profile"
