from datetime import datetime, timezone

import pytest

from vivarium.action_options import ActionOptionService
from vivarium.connectors import CLOSED, WorldConnectorService
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.util import to_iso


class Clock:
    def now(self): return datetime(2026, 8, 6, 12, tzinfo=timezone.utc)
    def now_iso(self): return to_iso(self.now())


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world_id = IntegrationWorldService(conn, clock=Clock()).create_initial_world()["id"]
    yield conn, world_id
    conn.close()


def test_visible_option_is_kept_only_while_the_real_connector_is_traversable(setup):
    conn, world_id = setup
    visible = ({"connector": "porte_entree", "destination": "salon"},)

    options = ActionOptionService(conn).visible_traversals(world_id, "sophie", visible)
    WorldConnectorService(conn, clock=Clock()).set_state(world_id, "porte_entree", CLOSED)
    closed = ActionOptionService(conn).visible_traversals(world_id, "sophie", visible)

    assert [option.wire() for option in options] == [{
        "action_kind": "traverse", "connector_key": "porte_entree", "target_location_key": "salon",
    }]
    assert closed == ()


def test_non_visible_or_malformed_passage_never_becomes_an_option(setup):
    conn, world_id = setup

    options = ActionOptionService(conn).visible_traversals(
        world_id, "sophie", ({"connector": "porte_patio", "destination": "cour"}, {"connector": 1}),
    )

    assert options == ()
