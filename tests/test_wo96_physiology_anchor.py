"""WO96 : la cognition lit l'ancre physiologique persistée sans reconstruire le passé."""

from datetime import timedelta

import pytest

from vivarium.db import transaction
from vivarium.decision import DecisionFrameService
from vivarium.activities import ActivityEngine
from vivarium.sleep_physiology import SleepPhysiologyError, SleepPhysiologyService
from vivarium.util import to_iso
from vivarium.world import SOURCE_ENGINE, _append_event

from test_active_runtime_cutover import T0_DT, active_world


def _physiology_snapshot(conn, world_id: int, character_key: str):
    character_id = conn.execute(
        "SELECT id FROM character WHERE world_id=? AND key=?",
        (world_id, character_key),
    ).fetchone()[0]
    return tuple(
        tuple(row)
        for row in conn.execute(
            "SELECT 'regulation',homeostatic_load_milli,circadian_phase_milli,anchor_at "
            "FROM sleep_regulation_state WHERE world_id=? AND character_id=? "
            "UNION ALL "
            "SELECT 'capacity',capacity_milli,rate_remainder,anchor_at "
            "FROM physical_capacity_state WHERE world_id=? AND character_id=? "
            "UNION ALL "
            "SELECT 'hysteresis',previous_band,NULL,anchor_at "
            "FROM sleep_wake_hysteresis_state WHERE world_id=? AND character_id=? "
            "UNION ALL "
            "SELECT 'precision',homeostatic_load_residue,circadian_phase_residue,anchor_at "
            "FROM sleep_regulation_precision_state WHERE world_id=? AND character_id=? "
            "ORDER BY 1",
            (world_id, character_id, world_id, character_id, world_id, character_id, world_id, character_id),
        )
    )


@pytest.mark.parametrize(
    ("event_type", "payload"),
    (
        ("cognition_no_action", {"character": "sophie", "decision": "no_action"}),
        ("speech_recorded", {"character": "sophie", "act_kind": "inform"}),
    ),
)
def test_decision_frame_reads_persisted_physiology_after_non_physiology_event(
    event_type, payload
):
    conn, world_id, clock = active_world()
    try:
        before_state = _physiology_snapshot(conn, world_id, "sophie")
        before_clock = tuple(
            conn.execute(
                "SELECT simulated_now,real_updated_at,runtime_state FROM canonical_clock "
                "WHERE world_id=?",
                (world_id,),
            ).fetchone()
        )
        at = to_iso(T0_DT + timedelta(seconds=30))
        with transaction(conn) as tx:
            _append_event(
                tx,
                world_id,
                SOURCE_ENGINE,
                event_type,
                payload,
                occurred_at=at,
                recorded_at=at,
            )

        frame = DecisionFrameService(conn).build_current(world_id, "sophie")

        assert frame.character_key == "sophie"
        assert frame.motives
        assert _physiology_snapshot(conn, world_id, "sophie") == before_state
        assert tuple(
            conn.execute(
                "SELECT simulated_now,real_updated_at,runtime_state FROM canonical_clock "
                "WHERE world_id=?",
                (world_id,),
            ).fetchone()
        ) == before_clock
    finally:
        conn.close()


def test_decision_frame_after_activity_start_uses_new_persisted_frontier():
    conn, world_id, clock = active_world()
    try:
        at = to_iso(T0_DT + timedelta(seconds=30))
        clock.current = T0_DT + timedelta(seconds=30)
        ActivityEngine(conn, clock=clock).start_activity(
            world_id, "sophie", "gaming", "salon", sim_now=at
        )
        state = SleepPhysiologyService(conn, clock=clock).read_state(world_id, "sophie")
        assert state.anchor_at == at
        frame = DecisionFrameService(conn).build_current(world_id, "sophie")
        assert frame.character_key == "sophie"
        assert frame.motives
    finally:
        conn.close()


def test_historical_owner_projection_still_rejects_newer_canonical_causes():
    conn, world_id, clock = active_world()
    try:
        physiology = SleepPhysiologyService(conn, clock=clock)
        historical = to_iso(T0_DT)
        at = to_iso(T0_DT + timedelta(seconds=30))
        before_state = _physiology_snapshot(conn, world_id, "sophie")
        with transaction(conn) as tx:
            _append_event(
                tx,
                world_id,
                SOURCE_ENGINE,
                "cognition_no_action",
                {"character": "sophie", "decision": "no_action"},
                occurred_at=at,
                recorded_at=at,
            )

        with pytest.raises(SleepPhysiologyError) as raised:
            physiology.resolve_light_source_owner_backed(
                world_id, "sophie", at_time=historical
            )
        assert raised.value.code == "stale_canonical_anchor"
        assert _physiology_snapshot(conn, world_id, "sophie") == before_state
    finally:
        conn.close()
