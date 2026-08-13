"""Rodage V2 : monde neuf, asymétrique et reproductible."""
from datetime import datetime, timezone

from vivarium.db import connect_database
from vivarium.migrations import ensure_schema
from vivarium.mvp_preflight import inspect_mvp_preflight
from vivarium.objects import ObjectService
from vivarium.resources import ResourceEngine
from vivarium.rodage_v2 import RodageV2Service
from vivarium.sleep_physiology import SleepPhysiologyService, V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY
from vivarium.util import Clock, to_iso


T0_DT = datetime(2026, 8, 13, 2, 15, tzinfo=timezone.utc)
T0 = to_iso(T0_DT)


class FixedClock(Clock):
    def now(self):
        return T0_DT


def _world():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    result = RodageV2Service(conn, clock=FixedClock()).create_world()
    return conn, result["world_id"], result


def _locations(conn, world_id):
    return {
        row["key"]: row["location"]
        for row in conn.execute(
            "SELECT c.key,l.key AS location FROM character c "
            "JOIN location l ON l.id=c.current_location_id WHERE c.world_id=? ORDER BY c.key",
            (world_id,),
        )
    }


def test_rodage_v2_bootstrap_is_clean_and_asymmetric():
    conn, world_id, result = _world()
    try:
        assert result["t0"] == T0
        assert result["preflight"] == "pass"
        assert _locations(conn, world_id) == {
            "chuu": "salle_de_bain",
            "erika": "salon",
            "luna": "entree_exterieure",
            "patoune": "salon",
            "sophie": "lieu_travail",
        }
        assert result["initial_activities"] == {
            "chuu": "bathe",
            "erika": "gaming",
            "luna": None,
            "patoune": "sleep",
            "sophie": "work",
        }

        bag = ObjectService(conn, clock=FixedClock()).object_sheet(world_id, "sac_voyage_luna")
        assert bag["carrier"] == "luna"
        assert bag["location"] == "entree_exterieure"

        hydration = ResourceEngine(conn, clock=FixedClock()).read_resource(
            world_id, "chuu", "hydration", T0
        )
        assert hydration["value_milli"] == 100_000
        assert hydration["state_key"] == "brilliant"

        sophie_work = conn.execute(
            "SELECT started_at,planned_end_at FROM activity a JOIN character c ON c.id=a.character_id "
            "WHERE a.world_id=? AND c.key='sophie' AND a.status='active' AND a.type='work'",
            (world_id,),
        ).fetchone()
        assert sophie_work is not None
        assert sophie_work["started_at"] == T0
        assert sophie_work["planned_end_at"] > T0
    finally:
        conn.close()


def test_rodage_v2_biology_and_t0_state_do_not_recreate_character_symmetry():
    conn, world_id, _result = _world()
    try:
        evidence = {
            row["key"]: row["evidence_class"]
            for row in conn.execute(
                "SELECT c.key,p.evidence_class FROM character c "
                "JOIN character_sleep_biology_assignment a ON a.character_id=c.id AND a.world_id=c.world_id "
                "JOIN sleep_biology_profile p ON p.id=a.profile_id "
                "WHERE c.world_id=? ORDER BY c.key",
                (world_id,),
            )
        }
        assert evidence == {
            "chuu": "fictional_canon",
            "erika": "human_reference",
            "luna": "fictional_canon",
            "patoune": "generic_feline",
            "sophie": "human_reference",
        }

        physiology = SleepPhysiologyService(conn, clock=FixedClock())
        states = {
            key: physiology.read_state(world_id, key).regulation
            for key in ("chuu", "erika", "luna", "patoune", "sophie")
        }
        triples = {
            (state.homeostatic_load_milli, state.circadian_phase_milli, state.physical_capacity_milli)
            for state in states.values()
        }
        assert len(triples) == 5
        assert all(physiology.read_state(world_id, key).anchor_at == T0 for key in states)
    finally:
        conn.close()


def test_rodage_v2_activity_vocabulary_is_generic_and_physically_complete():
    conn, world_id, _result = _world()
    try:
        definitions = {
            row["activity_type"]: row["physical_load_class"]
            for row in conn.execute(
                "SELECT activity_type,physical_load_class FROM activity_definition "
                "WHERE world_id=? ORDER BY activity_type",
                (world_id,),
            )
        }
        assert definitions == V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY
        assert definitions["bathe"] == "none"
        assert definitions["work"] == "light"
        sleep_locations = {
            row[0]
            for row in conn.execute(
                "SELECT location_key FROM activity_allowed_location "
                "WHERE world_id=? AND activity_type='sleep' AND location_key IS NOT NULL",
                (world_id,),
            )
        }
        assert "salon" in sleep_locations
        assert conn.execute(
            "SELECT 1 FROM activity_allowed_location WHERE world_id=? AND activity_type='work' "
            "AND location_key='lieu_travail'",
            (world_id,),
        ).fetchone() is not None
    finally:
        conn.close()


def test_rodage_v2_preflight_passes_after_active_initial_scene():
    conn, world_id, _result = _world()
    try:
        report = inspect_mvp_preflight(conn, world_id=world_id)
        failures = {check.key: check.detail for check in report.checks if not check.passed}
        assert failures == {}
        assert conn.execute(
            "SELECT COUNT(*) FROM initial_physiology_manifest_entry e "
            "JOIN initial_physiology_manifest m ON m.id=e.manifest_id WHERE m.world_id=?",
            (world_id,),
        ).fetchone()[0] == 5
        assert conn.execute(
            "SELECT status FROM world_physiology_system WHERE world_id=?",
            (world_id,),
        ).fetchone()[0] == "active"
        assert conn.execute(
            "SELECT COUNT(*) FROM runtime_session WHERE world_id=? AND stopped_at IS NULL",
            (world_id,),
        ).fetchone()[0] == 0
    finally:
        conn.close()
