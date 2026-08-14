from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.observation import HuginMuninObservationService, ObservationQuery
from vivarium.sleep_physiology import SleepPhysiologyService
from test_active_runtime_cutover import T0, active_world


def _current_data(report, character_key):
    ref = f"current_character:{character_key}"
    return next(item["data"] for item in report["evidence"] if item["ref"] == ref)


def test_active_current_state_exposes_persisted_owner_physiology_read_only():
    conn, wid, clock = active_world()
    try:
        service = SleepPhysiologyService(conn, clock=clock)
        before_state = service.read_state(wid, "sophie")
        before_events = conn.execute(
            "SELECT COUNT(*) FROM canonical_event WHERE world_id=?", (wid,)
        ).fetchone()[0]

        query = ObservationQuery(mode="hugin", subject_keys=("sophie",), focus="current_state")
        first = HuginMuninObservationService(conn, clock=clock).report(wid, query)
        second = HuginMuninObservationService(conn, clock=clock).report(wid, query)
        physiology = _current_data(first, "sophie")["physiology"]

        assert physiology["status"] == "active"
        assert physiology["canonical_now"] == T0
        assert physiology["wake_sleep_state"] == "wake"
        assert physiology["persisted"] == {
            "model_key": before_state.model_key,
            "model_version": before_state.model_version,
            "anchor_at": T0,
            "homeostatic_load_milli": 50000,
            "circadian_phase_milli": 250000,
            "physical_capacity_milli": 70000,
            "previous_stability_band": "fragile",
        }
        assert physiology["projection"] is None
        assert physiology["projection_evaluated_at"] is None
        assert physiology["projection_policy"] == "not_extrapolated_by_read_model"
        assert second == first
        assert service.read_state(wid, "sophie") == before_state
        assert conn.execute(
            "SELECT COUNT(*) FROM canonical_event WHERE world_id=?", (wid,)
        ).fetchone()[0] == before_events
    finally:
        conn.close()


def test_inactive_current_state_does_not_invent_active_physiology():
    conn = connect_database(":memory:")
    try:
        ensure_schema(conn)
        wid = IntegrationWorldService(conn).create_initial_world()["id"]
        report = HuginMuninObservationService(conn).report(
            wid,
            ObservationQuery(mode="hugin", subject_keys=("sophie",), focus="current_state"),
        )
        physiology = _current_data(report, "sophie")["physiology"]
        assert physiology["status"] == "inactive"
        assert physiology["persisted"] is None
        assert physiology["projection"] is None
        assert physiology["projection_evaluated_at"] is None
    finally:
        conn.close()
