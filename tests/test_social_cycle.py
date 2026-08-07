from datetime import datetime, timezone

import pytest

from vivarium.character import CharacterEngine
from vivarium.cognition_policy import CognitionCallLimits
from vivarium.connectors import WorldConnectorService
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.scene_turn import SceneTurnDecision
from vivarium.social_cycle import SocialSceneCycle
from vivarium.traversal import TraversalEngine
from vivarium.util import to_iso


class Clock:
    def now(self):
        return datetime(2026, 8, 6, 12, tzinfo=timezone.utc)

    def now_iso(self):
        return to_iso(self.now())


class Provider:
    def __init__(self, decision):
        self.decision = decision
        self.calls = 0

    def decide(self, context):
        self.calls += 1
        return self.decision


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = Clock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    yield conn, world_id, clock
    conn.close()


def _move_erika_to_salon(conn, world_id, clock):
    TraversalEngine(conn, clock=clock).traverse_character(
        world_id, "erika", "porte_entree", "salon"
    )


def test_movement_opens_a_sourced_two_person_scene_and_offers_one_turn(setup):
    conn, world_id, clock = setup
    _move_erika_to_salon(conn, world_id, clock)
    CharacterEngine(conn, clock=clock).move_character(world_id, "sophie", "salon")
    provider = Provider(SceneTurnDecision("speak", "greet", "Salut Erika.", "erika"))

    outcome = SocialSceneCycle(conn, provider).tick(
        world_id, CognitionCallLimits(0, 3600, 8)
    )

    assert outcome.opened_scene_keys == ("encounter_" + str(
        conn.execute("SELECT MAX(seq) FROM canonical_event WHERE world_id = ?", (world_id,)).fetchone()[0]
    ) + "_sophie_erika",)
    assert outcome.turn is not None and outcome.turn.speech["content"] == "Salut Erika."
    assert provider.calls == 1


def test_new_world_opens_one_initial_encounter_from_canonical_context(setup):
    conn, world_id, _clock = setup
    provider = Provider(SceneTurnDecision("no_action"))

    outcome = SocialSceneCycle(conn, provider).tick(
        world_id, CognitionCallLimits(0, 3600, 8)
    )

    source_seq = conn.execute(
        "SELECT seq FROM canonical_event "
        "WHERE world_id = ? AND event_type = 'world_initial_context_set'",
        (world_id,),
    ).fetchone()[0]
    assert outcome.opened_scene_keys == (f"encounter_{source_seq}_chuu_erika",)
    assert outcome.turn is not None
    assert provider.calls == 1

    later = SocialSceneCycle(conn, provider).tick(world_id, CognitionCallLimits(0, 3600, 8))
    assert later.opened_scene_keys == ()


def test_cycle_never_opens_a_scene_with_patoune(setup):
    conn, world_id, clock = setup
    _move_erika_to_salon(conn, world_id, clock)
    CharacterEngine(conn, clock=clock).move_character(world_id, "patoune", "salon")

    outcome = SocialSceneCycle(conn, Provider(SceneTurnDecision("no_action"))).tick(
        world_id, CognitionCallLimits(0, 3600, 8)
    )

    assert outcome.opened_scene_keys == ()
    assert outcome.turn is None


def test_cycle_closes_after_its_fixed_turn_budget_without_extra_call(setup):
    conn, world_id, clock = setup
    _move_erika_to_salon(conn, world_id, clock)
    CharacterEngine(conn, clock=clock).move_character(world_id, "sophie", "salon")
    provider = Provider(SceneTurnDecision("no_action"))
    cycle = SocialSceneCycle(conn, provider)
    limits = CognitionCallLimits(0, 3600, 8)

    for _ in range(4):
        cycle.tick(world_id, limits)
    outcome = cycle.tick(world_id, limits)

    assert provider.calls == 4
    assert outcome.closed_scene_keys
    assert conn.execute(
        "SELECT status FROM social_scene WHERE world_id = ?", (world_id,)
    ).fetchone()[0] == "closed"


def test_cycle_interrupts_when_a_participant_has_left_before_the_next_turn(setup):
    conn, world_id, clock = setup
    _move_erika_to_salon(conn, world_id, clock)
    CharacterEngine(conn, clock=clock).move_character(world_id, "sophie", "salon")
    cycle = SocialSceneCycle(conn, Provider(SceneTurnDecision("no_action")))
    limits = CognitionCallLimits(0, 3600, 8)
    cycle.tick(world_id, limits)
    TraversalEngine(conn, clock=clock).traverse_character(world_id, "sophie", "porte_entree", "entree_exterieure")

    outcome = cycle.tick(world_id, limits)

    assert outcome.interrupted_scene_keys
    assert conn.execute(
        "SELECT status, close_reason FROM social_scene WHERE world_id = ?", (world_id,)
    ).fetchone()["status"] == "interrupted"
