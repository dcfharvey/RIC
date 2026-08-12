from datetime import datetime, timezone

import pytest

from vivarium.db import connect_database, transaction
from vivarium.migrations import ensure_schema
from vivarium.seed import SEED_ACTIVITIES, SEED_ACTIVITY_ALLOWED, SEED_NEEDS
from vivarium.util import new_uuid, to_iso
from vivarium.world import WorldEngine
from vivarium.world_rules import WorldRuleError, WorldRuleService


T0 = datetime(2026, 8, 6, 18, 0, tzinfo=timezone.utc)


class FakeClock:
    def now(self):
        return T0

    def now_iso(self):
        return to_iso(self.now())


def _empty_residence(conn, clock):
    world_id = WorldEngine(conn, clock=clock).init_world(name="Règles", seed=False)["id"]
    with transaction(conn) as c:
        for key, kind in (
            ("salon", "room"), ("cuisine", "room"),
            ("salle_de_bain", "bathroom"), ("chambre", "bedroom"),
            ("cour_arriere", "backyard"), ("entree_exterieure", "entry_exterior"),
        ):
            c.execute(
                "INSERT INTO location (public_id, world_id, key, name, kind, capacity, created_at) VALUES (?, ?, ?, ?, ?, NULL, ?)",
                (new_uuid(), world_id, key, key.title(), kind, clock.now_iso()),
            )
    return world_id


def test_installs_standard_rules_without_seed_and_then_is_idempotent():
    conn = connect_database(":memory:")
    try:
        ensure_schema(conn)
        clock = FakeClock()
        world_id = _empty_residence(conn, clock)
        rules = WorldRuleService(conn, clock=clock)

        first = rules.install_standard_residence_rules(world_id)
        second = rules.install_standard_residence_rules(world_id)

        assert first == {
            "rule_set": "standard_residence.v1", "changed": True,
            "needs_added": len(SEED_NEEDS), "activities_added": len(SEED_ACTIVITIES),
            "activity_locations_added": len(SEED_ACTIVITY_ALLOWED),
        }
        assert second["changed"] is False
        assert conn.execute("SELECT COUNT(*) FROM need_definition WHERE world_id = ?", (world_id,)).fetchone()[0] == len(SEED_NEEDS)
        assert conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type = 'world_rules_installed'", (world_id,)).fetchone()[0] == 1
    finally:
        conn.close()


def test_missing_required_location_refuses_without_adding_rules():
    conn = connect_database(":memory:")
    try:
        ensure_schema(conn)
        world_id = WorldEngine(conn, clock=FakeClock()).init_world(name="Vide", seed=False)["id"]

        with pytest.raises(WorldRuleError) as raised:
            WorldRuleService(conn, clock=FakeClock()).install_standard_residence_rules(world_id)

        assert raised.value.code == "required_location_missing"
        assert conn.execute("SELECT COUNT(*) FROM need_definition WHERE world_id = ?", (world_id,)).fetchone()[0] == 0
    finally:
        conn.close()


def test_conflicting_existing_rule_is_never_silently_overwritten():
    conn = connect_database(":memory:")
    try:
        ensure_schema(conn)
        clock = FakeClock()
        world_id = _empty_residence(conn, clock)
        rules = WorldRuleService(conn, clock=clock)
        rules.install_standard_residence_rules(world_id)
        conn.execute("UPDATE need_definition SET rate_num = 999 WHERE world_id = ? AND need_key = 'satiete'", (world_id,))

        with pytest.raises(WorldRuleError) as raised:
            rules.install_standard_residence_rules(world_id)

        assert raised.value.code == "need_definition_conflict"
        assert conn.execute("SELECT rate_num FROM need_definition WHERE world_id = ? AND need_key = 'satiete'", (world_id,)).fetchone()[0] == 999
    finally:
        conn.close()


def test_standard_rules_install_explicit_wakefulness_and_defer_physical_classification():
    conn = connect_database(":memory:")
    try:
        ensure_schema(conn)
        clock = FakeClock()
        world_id = _empty_residence(conn, clock)
        WorldRuleService(conn, clock=clock).install_standard_residence_rules(world_id)

        actual = {
            row["activity_type"]: (
                row["requires_sustained_wakefulness"], row["physical_load_class"],
            )
            for row in conn.execute(
                "SELECT activity_type, requires_sustained_wakefulness, physical_load_class "
                "FROM activity_definition WHERE world_id = ?", (world_id,)
            )
        }
        expected = {activity[0]: (int(activity[-1]), None) for activity in SEED_ACTIVITIES}
        assert actual == expected
    finally:
        conn.close()
