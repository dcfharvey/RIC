from datetime import datetime, timezone

import pytest

from vivarium.arrival_cycle import InitialArrivalCycle
from vivarium.cognition import CognitionDecision
from vivarium.cognition_policy import CognitionCallLimits
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.simulation import SimulationEngine
from vivarium.util import to_iso
from vivarium.world import WorldEngine


class Clock:
    def now(self): return datetime(2026, 8, 6, 12, tzinfo=timezone.utc)
    def now_iso(self): return to_iso(self.now())


class Provider:
    def __init__(self): self.calls = []
    def decide(self, context):
        self.calls.append(context.character_key)
        return CognitionDecision("no_action")


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    wid = IntegrationWorldService(conn, clock=Clock()).create_initial_world()["id"]
    yield conn, wid
    conn.close()


def test_initial_arrival_visits_each_sapient_once_and_never_patoune(setup):
    conn, wid = setup
    provider = Provider()
    cycle = InitialArrivalCycle(conn, provider)
    limits = CognitionCallLimits(0, 3_600, 8)

    outcomes = [cycle.tick(wid, limits) for _ in range(4)]

    assert [outcome.character_key for outcome in outcomes] == ["chuu", "erika", "luna", "sophie"]
    assert [outcome.pending for outcome in outcomes] == [True, True, True, False]
    assert provider.calls == ["chuu", "erika", "luna", "sophie"]
    assert cycle.tick(wid, limits).character_key is None
    assert conn.execute(
        "SELECT COUNT(*) FROM cognition_call_admission WHERE world_id = ? AND trigger = 'initial_arrival'", (wid,)
    ).fetchone()[0] == 4


def test_arrival_releases_only_initial_idle_before_validated_traversal(setup):
    conn, wid = setup
    clock = Clock()
    now = WorldEngine(conn, clock=clock).read_canonical_time(wid)
    SimulationEngine(conn, clock=clock).run_to(wid, now)

    class EnterProvider:
        def decide(self, context):
            return CognitionDecision("traverse", "porte_entree", "salon")

    outcome = InitialArrivalCycle(conn, EnterProvider(), clock=clock).tick(
        wid, CognitionCallLimits(0, 3_600, 8)
    )

    assert outcome.character_key == "chuu"
    assert outcome.routed and outcome.routed.turn and outcome.routed.turn.validation
    assert outcome.routed.turn.validation.status == "accepted"
    assert conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ? AND event_type = 'activity_aborted'", (wid,)
    ).fetchone()[0] == 1
