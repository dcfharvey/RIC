from datetime import datetime, timezone

from vivarium.db import connect_database
from vivarium.instances import CharacterInstanceService
from vivarium.migrations import ensure_schema
from vivarium.mvp_chuu import CHUU_HYDRATION_PROFILE, install_chuu_hydration
from vivarium.mvp_templates import install_mvp_character_templates
from vivarium.resources import ResourceEngine
from vivarium.util import to_iso
from vivarium.world import WorldEngine


T0 = datetime(2026, 8, 1, 8, 0, 0, tzinfo=timezone.utc)


class FakeClock:
    def now(self):
        return T0

    def now_iso(self):
        return to_iso(T0)


def test_chuu_hydration_is_installed_through_the_generic_resource_profile():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    try:
        world = WorldEngine(conn, clock=clock).init_world(name="Chuu calibration")
        install_mvp_character_templates(conn)
        CharacterInstanceService(conn, clock=clock).instantiate(
            world["id"], "resident.chuu", 1, "chuu", "salon"
        )

        active = install_chuu_hydration(ResourceEngine(conn, clock=clock), world["id"])

        assert active == {
            "resource_key": "hydration",
            "value_milli": 95000,
            "state_key": "brilliant",
            "effects": [
                {
                    "effect_type": "capability_availability",
                    "effect_key": "cognition.complex_reasoning",
                    "availability": "available",
                    "value_milli": None,
                },
                {
                    "effect_type": "capability_availability",
                    "effect_key": "form.humanoid",
                    "availability": "available",
                    "value_milli": None,
                },
                {
                    "effect_type": "context_signal",
                    "effect_key": "cognition.clarity",
                    "availability": None,
                    "value_milli": 80000,
                },
            ],
        }
        assert set(CHUU_HYDRATION_PROFILE["effects_by_state"]) == {
            "puddle_simple", "dehydrated", "hydrated", "brilliant"
        }
    finally:
        conn.close()
