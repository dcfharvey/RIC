import pytest

from vivarium.db import connect_database
from vivarium.initial_context import InitialContextError, InitialContextService
from vivarium.integration_world import INITIAL_SHARED_FACTS, IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.resources import ResourceEngine


def test_initial_integration_world_is_assembled_atomically_from_real_services():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    try:
        world = IntegrationWorldService(conn).create_initial_world()

        assert [row["key"] for row in conn.execute(
            "SELECT key FROM character WHERE world_id = ? ORDER BY key", (world["id"],)
        )] == ["chuu", "erika", "luna", "patoune", "sophie"]
        assert conn.execute(
            "SELECT COUNT(*) FROM character WHERE world_id = ? AND current_location_id = "
            "(SELECT id FROM location WHERE world_id = ? AND key = 'entree_exterieure')",
            (world["id"], world["id"]),
        ).fetchone()[0] == 5
        assert ResourceEngine(conn).read_resource(
            world["id"], "chuu", "hydration", conn.execute(
                "SELECT simulated_now FROM canonical_clock WHERE world_id = ?", (world["id"],)
            ).fetchone()[0],
        )["state_key"] == "brilliant"
        assert InitialContextService(conn).shared_facts(world["id"]) == INITIAL_SHARED_FACTS
    finally:
        conn.close()


def test_invalid_context_rolls_back_the_entire_initial_world_assembly():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    try:
        with pytest.raises(InitialContextError, match="faits initiaux invalides"):
            IntegrationWorldService(conn).create_initial_world(shared_facts=None)

        assert conn.execute("SELECT COUNT(*) FROM worlds").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM character").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM world_initial_context").fetchone()[0] == 0
    finally:
        conn.close()
