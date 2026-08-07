from datetime import datetime, timedelta, timezone
import sqlite3

import pytest

from vivarium.activities import ActivityEngine
from vivarium.connectors import AVAILABLE, CLOSED, WorldConnectorService
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.instances import CharacterInstanceService
from vivarium.migrations import ensure_schema
from vivarium.non_sapient import NonSapientAgencyCycle
from vivarium.simulation import SimulationEngine
from vivarium.util import to_iso


T0 = datetime(2026, 8, 7, 12, tzinfo=timezone.utc)


class Clock:
    def __init__(self):
        self.current = T0

    def now(self):
        return self.current

    def now_iso(self):
        return to_iso(self.current)

    def advance(self, seconds):
        self.current += timedelta(seconds=seconds)


def _setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = Clock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    SimulationEngine(conn, clock=clock).run_to(world_id, clock.now_iso())
    return conn, world_id, clock


def _location(conn, world_id, key):
    return conn.execute(
        "SELECT l.key FROM character c JOIN location l ON l.id=c.current_location_id "
        "WHERE c.world_id=? AND c.key=?", (world_id, key),
    ).fetchone()["key"]


def test_cat0_enters_through_an_available_local_affordance_without_llm():
    conn, world_id, clock = _setup()
    try:
        result = NonSapientAgencyCycle(conn, clock=clock).tick(world_id)

        assert result.character_key == "patoune"
        assert result.selected_action == "traverse" and result.outcome == "accepted"
        assert _location(conn, world_id, "patoune") == "salon"
        idle = ActivityEngine(conn).activity_sheet(world_id, "patoune")
        assert idle["type"] == "idle"
        assert idle["planned_end_at"] == to_iso(T0 + timedelta(seconds=300))
        assert conn.execute("SELECT COUNT(*) FROM cognition_call_admission").fetchone()[0] == 0
    finally:
        conn.close()


def test_cat0_closed_door_keeps_intention_and_opening_reactivates_it():
    conn, world_id, clock = _setup()
    try:
        connectors = WorldConnectorService(conn, clock=clock)
        connectors.set_state(world_id, "porte_entree", CLOSED)

        blocked = NonSapientAgencyCycle(conn, clock=clock).tick(world_id)
        assert blocked.outcome == "blocked" and blocked.target_key == "salon"
        assert _location(conn, world_id, "patoune") == "entree_exterieure"
        status = conn.execute(
            "SELECT t.status FROM non_sapient_intention_transition t ORDER BY t.id DESC LIMIT 1"
        ).fetchone()["status"]
        assert status == "active"

        connectors.set_state(world_id, "porte_entree", AVAILABLE)
        resumed = NonSapientAgencyCycle(conn, clock=clock).tick(world_id)
        assert resumed.selected_action == "traverse" and resumed.outcome == "accepted"
        assert _location(conn, world_id, "patoune") == "salon"
        statuses = [row[0] for row in conn.execute(
            "SELECT status FROM non_sapient_intention_transition ORDER BY id"
        )]
        assert statuses == ["active", "completed"]
    finally:
        conn.close()


def test_cat0_policy_is_bound_to_component_not_character_name():
    conn, world_id, clock = _setup()
    try:
        # Patoune est occupée; une deuxième instance du même profil générique
        # doit donc recevoir l'occasion sans aucun branchement sur son nom.
        ActivityEngine(conn, clock=clock).abort_activity(world_id, "patoune", sim_now=clock.now_iso())
        CharacterInstanceService(conn, clock=clock).instantiate(
            world_id, "resident.patoune", 4, "animal_test", "entree_exterieure"
        )
        ActivityEngine(conn, clock=clock).start_activity(
            world_id, "animal_test", "idle", "entree_exterieure", duration_seconds=28800,
            sim_now=clock.now_iso(),
        )

        result = NonSapientAgencyCycle(conn, clock=clock).tick(world_id)

        assert result.character_key == "animal_test"
        assert _location(conn, world_id, "animal_test") == "salon"
    finally:
        conn.close()


def test_cat0_policy_created_wait_is_not_polled_before_its_boundary():
    conn, world_id, clock = _setup()
    try:
        first = NonSapientAgencyCycle(conn, clock=clock).tick(world_id)
        second = NonSapientAgencyCycle(conn, clock=clock).tick(world_id)

        assert first.character_key == "patoune"
        assert second.character_key is None
        assert conn.execute("SELECT COUNT(*) FROM non_sapient_decision_event").fetchone()[0] == 1
    finally:
        conn.close()


def test_cat0_ignores_connector_changes_outside_the_local_opportunity_field():
    conn, world_id, clock = _setup()
    try:
        first = NonSapientAgencyCycle(conn, clock=clock).tick(world_id)
        assert first.target_key == "salon"
        WorldConnectorService(conn, clock=clock).set_state(world_id, "porte_patio", CLOSED)

        second = NonSapientAgencyCycle(conn, clock=clock).tick(world_id)

        assert second.character_key is None
        assert conn.execute("SELECT COUNT(*) FROM non_sapient_decision_event").fetchone()[0] == 1
    finally:
        conn.close()


def test_cat0_abandons_a_persistently_blocked_target_and_uses_an_alternative():
    conn, world_id, clock = _setup()
    try:
        connectors = WorldConnectorService(conn, clock=clock)
        connectors.set_state(world_id, "porte_entree", CLOSED)
        cycle = NonSapientAgencyCycle(conn, clock=clock)
        for _ in range(3):
            result = cycle.tick(world_id)
            assert result.outcome == "blocked"
            clock.advance(300)
            SimulationEngine(conn, clock=clock).run_to(world_id, clock.now_iso())

        result = cycle.tick(world_id)

        assert result.outcome == "accepted"
        assert result.target_key == "stationnement"
        assert _location(conn, world_id, "patoune") == "stationnement"
        statuses = [row[0] for row in conn.execute(
            "SELECT status FROM non_sapient_intention_transition ORDER BY id"
        )]
        assert statuses == ["active", "abandoned", "active", "completed"]
    finally:
        conn.close()


def test_cat0_subjective_ledgers_are_append_only():
    conn, world_id, clock = _setup()
    try:
        NonSapientAgencyCycle(conn, clock=clock).tick(world_id)

        for statement in (
            "UPDATE non_sapient_intention SET target_key='ailleurs'",
            "DELETE FROM non_sapient_intention_transition",
            "UPDATE non_sapient_decision_event SET reason_code='rewritten'",
        ):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                conn.execute(statement)
    finally:
        conn.close()
