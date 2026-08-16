from datetime import datetime, timezone
import json

import pytest

from vivarium.cognition import CognitionContextService, CognitionDecision, CognitionTurnService
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.resources import ResourceEngine
from vivarium.util import to_iso


class Clock:
    def now(self):
        return datetime(2026, 8, 6, 12, tzinfo=timezone.utc)

    def now_iso(self):
        return to_iso(self.now())


class Provider:
    def __init__(self, decision):
        self.decision = decision
        self.context = None

    def decide(self, context):
        self.context = context
        return self.decision


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = Clock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    yield conn, world_id, clock
    conn.close()


def test_operational_grounding_is_owner_scoped_and_contains_static_and_dynamic_state(setup):
    conn, world_id, clock = setup

    chuu = CognitionContextService(conn, clock=clock).build(world_id, "chuu")
    grounding = chuu.self_profile["operational_grounding"]

    assert grounding["morphology"]["body_plan"] == "amorphous"
    assert grounding["capabilities"] == {
        "cognition.complex_reasoning": "available",
        "form.humanoid": "available",
    }
    assert grounding["context_signals"]["cognition.clarity"] == 80000

    sophie = CognitionContextService(conn, clock=clock).build(world_id, "sophie")
    sophie_wire = json.dumps(sophie.wire(), ensure_ascii=False)
    assert sophie.self_profile["operational_grounding"]["morphology"]["body_plan"] == "bipedal"
    assert "amorphous" not in sophie_wire
    assert "form.humanoid" not in sophie_wire
    assert "hydration" not in json.dumps(
        chuu.wire()["self_profile"]["operational_grounding"], ensure_ascii=False
    )


def test_dynamic_grounding_tracks_owner_backed_resource_band(setup):
    conn, world_id, clock = setup
    resources = ResourceEngine(conn, clock=clock)

    resources.adjust_resource(
        world_id, "chuu", "hydration", -60000, clock.now_iso(), "grounding-test"
    )
    grounding = CognitionContextService(conn, clock=clock).build(
        world_id, "chuu"
    ).self_profile["operational_grounding"]

    assert grounding["capabilities"]["form.humanoid"] == "limited"
    assert grounding["capabilities"]["cognition.complex_reasoning"] == "limited"
    assert grounding["context_signals"]["cognition.clarity"] == -40000


def test_operational_grounding_uses_generic_resource_contract_for_another_instance(setup):
    conn, world_id, clock = setup
    ResourceEngine(conn, clock=clock).register_resource_profile(
        world_id,
        "sophie",
        "focus",
        "Focus",
        90000,
        0,
        1,
        (
            {"state_key": "unfocused", "min_milli": 0, "max_milli": 49999},
            {"state_key": "focused", "min_milli": 50000, "max_milli": 100000},
        ),
        {
            "unfocused": (
                {
                    "effect_type": "capability_availability",
                    "effect_key": "action.test",
                    "availability": "unavailable",
                },
                {
                    "effect_type": "context_signal",
                    "effect_key": "focus.clarity",
                    "value_milli": -30000,
                },
            ),
            "focused": (
                {
                    "effect_type": "capability_availability",
                    "effect_key": "action.test",
                    "availability": "available",
                },
                {
                    "effect_type": "context_signal",
                    "effect_key": "focus.clarity",
                    "value_milli": 30000,
                },
            )
        },
    )

    grounding = CognitionContextService(conn, clock=clock).build(
        world_id, "sophie"
    ).self_profile["operational_grounding"]
    assert grounding["capabilities"] == {"action.test": "available"}
    assert grounding["context_signals"] == {"focus.clarity": 30000}


def test_body_plan_is_descriptive_and_does_not_script_activity_selection(setup):
    conn, world_id, clock = setup
    context = CognitionContextService(conn, clock=clock).build(world_id, "chuu")
    grounding = context.self_profile["operational_grounding"]

    assert set(grounding) == {"morphology", "capabilities", "context_signals"}
    assert "allowed_activities" not in grounding
    assert "activity" not in grounding


def test_grounding_is_observable_without_giving_the_provider_a_second_owner(setup):
    conn, world_id, clock = setup
    provider = Provider(CognitionDecision("no_action"))

    result = CognitionTurnService(conn, provider, clock=clock).run(
        world_id, "chuu", "grounding-observation"
    )

    assert result.context.self_profile["operational_grounding"] == provider.context.self_profile[
        "operational_grounding"
    ]
    assert provider.context.world_id == world_id
    assert result.validation is None
