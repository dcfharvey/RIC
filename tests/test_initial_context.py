import pytest

from vivarium.db import connect_database, transaction
from vivarium.initial_context import InitialContextError, InitialContextService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest
from vivarium.world import WorldEngine


def test_nested_transactions_rollback_only_inner_savepoint():
    conn = connect_database(":memory:")
    try:
        conn.execute("CREATE TABLE test_nested (value INTEGER NOT NULL)")
        with transaction(conn):
            conn.execute("INSERT INTO test_nested VALUES (1)")
            with pytest.raises(RuntimeError):
                with transaction(conn):
                    conn.execute("INSERT INTO test_nested VALUES (2)")
                    raise RuntimeError("rollback inner")
            conn.execute("INSERT INTO test_nested VALUES (3)")
        assert [row[0] for row in conn.execute("SELECT value FROM test_nested ORDER BY value")] == [1, 3]
    finally:
        conn.close()


def test_initial_shared_context_is_immutable_journaled_and_in_digest():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    try:
        world = WorldEngine(conn).init_world(name="Contexte")
        facts = {
            "residency": {"voluntary": True, "expenses_covered": True, "personal_allowance": True},
            "knowledge_boundary": {"only_declared_facts": True},
        }

        stored = InitialContextService(conn).set_shared_facts(world["id"], facts)

        assert stored == facts
        with pytest.raises(InitialContextError, match="déjà fixé"):
            InitialContextService(conn).set_shared_facts(world["id"], facts)
        with pytest.raises(Exception, match="immutable"):
            conn.execute("UPDATE world_initial_context SET facts_json = '{}' WHERE world_id = ?", (world["id"],))
        assert canonical_state_digest(conn, world["id"])["world_initial_context"] == facts
    finally:
        conn.close()
