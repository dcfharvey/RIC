from datetime import timedelta

from test_active_runtime_cutover import T0_DT, active_world

from vivarium.activities import ActivityEngine
from vivarium.active_simulation import ActiveSimulationEngine
from vivarium.autonomy_cycle import AutonomyCycle
from vivarium.cognition import CognitionDecision
from vivarium.cognition_policy import CognitionCallLimits
from vivarium.location_plans import LocationPlanService
from vivarium.util import to_iso


class NoActionProvider:
    def __init__(self):
        self.calls = []

    def decide(self, context):
        self.calls.append(context)
        return CognitionDecision("no_action")


def _end_at(clock, seconds=30):
    return to_iso(T0_DT + timedelta(seconds=seconds))


def _start_gaming(conn, world_id, clock, *, end_at):
    activities = ActivityEngine(conn, clock=clock)
    activities.start_activity(world_id, "sophie", "gaming", "salon", sim_now=to_iso(T0_DT))
    conn.execute(
        "UPDATE activity SET planned_end_at=? WHERE world_id=? AND status='active' "
        "AND character_id=(SELECT id FROM character WHERE world_id=? AND key='sophie')",
        (end_at, world_id, world_id),
    )
    return activities


def test_activity_end_creates_one_bounded_idle_at_current_location(monkeypatch):
    conn, world_id, clock = active_world()
    try:
        end_at = _end_at(clock)
        _start_gaming(conn, world_id, clock, end_at=end_at)
        engine = ActiveSimulationEngine(conn, clock=clock)
        monkeypatch.setattr(engine, "_arbitrate", lambda *args, **kwargs: None)
        clock.current = T0_DT + timedelta(seconds=31)

        report = engine.run_to(world_id, to_iso(clock.current))

        active = ActivityEngine(conn, clock=clock).activity_sheet(world_id, "sophie")
        assert report.transitions == 1
        assert active is not None
        assert active["type"] == "idle"
        assert active["location_key"] == "salon"
        assert active["planned_end_at"] == to_iso(T0_DT + timedelta(seconds=630))
        rows = conn.execute(
            "SELECT payload FROM canonical_event WHERE world_id=? "
            "AND event_type='activity_started' "
            "AND json_extract(payload,'$.activity')='idle'",
            (world_id,),
        ).fetchall()
        assert len(rows) == 1
        assert "wo95_post_boundary_idle" in rows[0]["payload"]
    finally:
        conn.close()


def test_idle_source_reaches_autonomy_and_no_action_is_distinct_from_no_source():
    conn, world_id, clock = active_world()
    try:
        provider = NoActionProvider()
        limits = CognitionCallLimits(0, 3600, 8)
        before = AutonomyCycle(conn, provider, clock=clock).tick(world_id, limits)
        assert before.character_key is None
        assert provider.calls == []

        engine = ActiveSimulationEngine(conn, clock=clock)
        engine._ensure_post_boundary_idle(world_id, "sophie", to_iso(T0_DT))
        after = AutonomyCycle(conn, provider, clock=clock).tick(world_id, limits)

        assert after.character_key == "sophie"
        assert after.routed is not None and after.routed.attempted
        assert after.routed.turn is not None
        assert after.routed.turn.decision.action == "no_action"
        assert len(provider.calls) == 1
        assert ActivityEngine(conn, clock=clock).activity_sheet(world_id, "sophie")["type"] == "idle"
    finally:
        conn.close()


def test_successor_installed_by_arbitration_prevents_extra_idle(monkeypatch):
    conn, world_id, clock = active_world()
    try:
        end_at = _end_at(clock)
        _start_gaming(conn, world_id, clock, end_at=end_at)
        engine = ActiveSimulationEngine(conn, clock=clock)

        def install_successor(world, key, at):
            ActivityEngine(conn, clock=clock).start_activity(
                world, key, "rest", "salon", sim_now=at,
            )

        monkeypatch.setattr(engine, "_arbitrate", install_successor)
        clock.current = T0_DT + timedelta(seconds=31)
        engine.run_to(world_id, to_iso(clock.current))

        active = ActivityEngine(conn, clock=clock).activity_sheet(world_id, "sophie")
        assert active is not None and active["type"] == "rest"
        assert conn.execute(
            "SELECT COUNT(*) FROM canonical_event WHERE world_id=? "
            "AND json_extract(payload,'$.action_provenance.origin')='wo95_post_boundary_idle'",
            (world_id,),
        ).fetchone()[0] == 0
    finally:
        conn.close()


def test_same_boundary_location_plan_is_resolved_before_final_idle(monkeypatch):
    conn, world_id, clock = active_world()
    try:
        end_at = _end_at(clock)
        _start_gaming(conn, world_id, clock, end_at=end_at)
        plan = LocationPlanService(conn, clock=clock).plan(
            world_id, "sophie", "entree_exterieure", end_at,
            provenance="wo95.test",
        )
        engine = ActiveSimulationEngine(conn, clock=clock)
        monkeypatch.setattr(engine, "_arbitrate", lambda *args, **kwargs: None)
        clock.current = T0_DT + timedelta(seconds=31)
        engine.run_to(world_id, to_iso(clock.current))

        resolved = LocationPlanService(conn, clock=clock).read(world_id, plan["id"])
        active = ActivityEngine(conn, clock=clock).activity_sheet(world_id, "sophie")
        assert resolved["status"] == "planned"
        assert resolved["resolution_outcome"] == "fulfilled"
        assert active is not None and active["type"] == "idle"
        assert active["location_key"] == "entree_exterieure"
    finally:
        conn.close()


def test_sleep_completion_then_abort_both_reach_post_boundary_idle(monkeypatch):
    conn, world_id, clock = active_world()
    try:
        activities = ActivityEngine(conn, clock=clock)
        activities.start_activity(
            world_id, "sophie", "sleep", "chambre_1", sim_now=to_iso(T0_DT)
        )
        character_id = conn.execute(
            "SELECT id FROM character WHERE world_id=? AND key='sophie'", (world_id,)
        ).fetchone()[0]
        conn.execute(
            "UPDATE sleep_regulation_state SET homeostatic_load_milli=0, circadian_phase_milli=0 "
            "WHERE world_id=? AND character_id=?",
            (world_id, character_id),
        )
        conn.execute(
            "UPDATE sleep_wake_hysteresis_state SET previous_band='stable' "
            "WHERE world_id=? AND character_id=?",
            (world_id, character_id),
        )
        engine = ActiveSimulationEngine(conn, clock=clock)
        monkeypatch.setattr(engine, "_arbitrate", lambda *args, **kwargs: None)
        clock.current = T0_DT + timedelta(seconds=31)
        engine.run_to(world_id, to_iso(clock.current))
        assert ActivityEngine(conn, clock=clock).activity_sheet(world_id, "sophie")["type"] == "idle"

        clock.current = T0_DT + timedelta(seconds=32)
        activities.abort_activity(
            world_id, "sophie", sim_now=to_iso(T0_DT + timedelta(seconds=32)),
            _reanchor_clock=False,
        )
        engine._ensure_post_boundary_idle(
            world_id, "sophie", to_iso(T0_DT + timedelta(seconds=32))
        )
        assert ActivityEngine(conn, clock=clock).activity_sheet(world_id, "sophie")["type"] == "idle"
    finally:
        conn.close()


def test_post_boundary_idle_is_persistently_idempotent_and_skips_non_sapient():
    conn, world_id, clock = active_world()
    try:
        engine = ActiveSimulationEngine(conn, clock=clock)
        at = to_iso(T0_DT)
        engine._ensure_post_boundary_idle(world_id, "sophie", at)
        ActivityEngine(conn, clock=clock).abort_activity(
            world_id, "sophie", sim_now=at, _reanchor_clock=False,
        )
        engine._ensure_post_boundary_idle(world_id, "sophie", at)
        assert conn.execute(
            "SELECT COUNT(*) FROM canonical_event WHERE world_id=? "
            "AND json_extract(payload,'$.action_provenance.proposal_id')=?",
            (world_id, f"wo95_idle_{world_id}_sophie_{at}"),
        ).fetchone()[0] == 1

        engine._ensure_post_boundary_idle(world_id, "patoune", at)
        assert conn.execute(
            "SELECT COUNT(*) FROM canonical_event WHERE world_id=? "
            "AND json_extract(payload,'$.character')='patoune' "
            "AND json_extract(payload,'$.action_provenance.origin')='wo95_post_boundary_idle'",
            (world_id,),
        ).fetchone()[0] == 0
    finally:
        conn.close()
