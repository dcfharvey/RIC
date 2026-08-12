"""Banc d'integration sommeil/activite, hors residence et hors runtime."""

import sqlite3
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

import pytest

from vivarium.activities import ActivityEngine
from vivarium.circadian_model import RegulationInput, calibration_profiles
from vivarium.db import connect_database, transaction
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import max_seq
from vivarium.sleep_physiology import (
    ADDITIVE_MODEL_KEY,
    SleepPhysiologyFoundationService,
)
from vivarium.sleep_termination import SleepTerminationError, SleepTerminationFoundationService
from vivarium.synthetic_sleep_integration import (
    SyntheticSleepActivityCoordinator,
    SyntheticSleepIntegrationError,
)
from vivarium.util import new_uuid, to_iso


T0 = datetime(2026, 8, 11, 12, tzinfo=timezone.utc)


class FakeClock:
    def now(self):
        return T0

    def now_iso(self):
        return to_iso(T0)


def _profile_payload():
    candidate = asdict(calibration_profiles()["human_reference_candidate.v1"])
    for key in ("profile_key", "version", "evidence_class"):
        candidate.pop(key)
    return {"model_key": ADDITIVE_MODEL_KEY, "parameters": candidate}


def _schedule():
    return {"schema_version": 1, "segments": [
        {"start_second": 0, "end_second": 21600, "environmental_light_milli": 0},
        {"start_second": 21600, "end_second": 72000, "environmental_light_milli": 90000},
        {"start_second": 72000, "end_second": 86400, "environmental_light_milli": 0},
    ]}


def _termination_policy():
    return {
        "schema_version": 1, "checkpoint_interval_seconds": 600, "hard_cap_seconds": 1800,
        "wake_admissible_enter_milli": 65000, "wake_admissible_exit_milli": 55000,
    }


def _activate_synthetic(conn, world_id, anchor):
    """Fixture test-only : jamais exposee par le produit ni par le runtime."""
    with transaction(conn) as tx:
        tx.execute(
            "UPDATE world_physiology_system SET status='active',activated_at=?,activated_by=?,updated_at=? WHERE world_id=?",
            (anchor, "synthetic_test", anchor, world_id),
        )
        for row in tx.execute("SELECT id FROM character WHERE world_id=?", (world_id,)):
            for statement, values in (
                (
                    "INSERT INTO sleep_regulation_state "
                    "(public_id,world_id,character_id,model_key,model_version,homeostatic_load_milli,circadian_phase_milli,anchor_at,updated_at) "
                    "VALUES (?,?,?,?,1,50000,250000,?,?)",
                    (new_uuid(), world_id, row["id"], ADDITIVE_MODEL_KEY, anchor, anchor),
                ),
                (
                    "INSERT INTO physical_capacity_state "
                    "(public_id,world_id,character_id,capacity_milli,rate_remainder,anchor_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                    (new_uuid(), world_id, row["id"], 70000, 0, anchor, anchor),
                ),
                (
                    "INSERT INTO sleep_wake_hysteresis_state "
                    "(public_id,world_id,character_id,previous_band,anchor_at,updated_at) VALUES (?,?,?,?,?,?)",
                    (new_uuid(), world_id, row["id"], "stable", anchor, anchor),
                ),
                (
                    "INSERT INTO sleep_regulation_precision_state "
                    "(public_id,world_id,character_id,homeostatic_load_residue,circadian_phase_residue,anchor_at,updated_at) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (new_uuid(), world_id, row["id"], 0.0, 0.0, anchor, anchor),
                ),
            ):
                tx.execute(statement, values)


def _set_state(conn, world_id, *, anchor, h, phase):
    character_id = conn.execute(
        "SELECT id FROM character WHERE world_id=? AND key='sophie'", (world_id,)
    ).fetchone()[0]
    with transaction(conn) as tx:
        tx.execute(
            "UPDATE sleep_regulation_state SET homeostatic_load_milli=?,circadian_phase_milli=?,anchor_at=? "
            "WHERE world_id=? AND character_id=?", (h, phase, anchor, world_id, character_id),
        )
        tx.execute(
            "UPDATE physical_capacity_state SET anchor_at=? WHERE world_id=? AND character_id=?",
            (anchor, world_id, character_id),
        )
        tx.execute(
            "UPDATE sleep_wake_hysteresis_state SET previous_band='stable',anchor_at=? WHERE world_id=? AND character_id=?",
            (anchor, world_id, character_id),
        )
        tx.execute(
            "UPDATE sleep_regulation_precision_state SET homeostatic_load_residue=0.0,circadian_phase_residue=0.0,anchor_at=? "
            "WHERE world_id=? AND character_id=?", (anchor, world_id, character_id),
        )


@pytest.fixture
def synthetic_world():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    foundation = SleepPhysiologyFoundationService(conn, clock=clock)
    anchor = to_iso(T0)
    foundation.register_light_schedule("synthetic.day.v1", 1, _schedule())
    foundation.register_location_light_profile("synthetic.interior.v1", 1, 25000, {"kind": "interior"})
    foundation.register_biology_profile("synthetic.human.v1", 1, "human_reference", _profile_payload())
    foundation.assign_light_schedule(world_id, "synthetic.day.v1", 1, anchor, "synthetic_setup")
    for row in conn.execute("SELECT key FROM location WHERE world_id=?", (world_id,)):
        foundation.assign_location_light_profile(
            world_id, row["key"], "synthetic.interior.v1", 1, anchor, "synthetic_setup"
        )
    for row in conn.execute("SELECT key FROM character WHERE world_id=?", (world_id,)):
        foundation.assign_biology_profile(
            world_id, row["key"], "synthetic.human.v1", 1, "synthetic_setup"
        )
    foundation.prepare_world(world_id, ADDITIVE_MODEL_KEY, 1, "synthetic_operator")
    _activate_synthetic(conn, world_id, anchor)
    termination = SleepTerminationFoundationService(conn, clock=clock)
    policy = termination.register_policy("synthetic.sleep.v1", 1, _termination_policy(), "synthetic_calibration_only")
    termination.assign_policy(world_id, policy.policy_key, policy.version, "synthetic_setup")
    try:
        yield conn, world_id, clock
    finally:
        conn.close()


def _sources():
    return (
        RegulationInput("sleep", 0, 25000, occluded=True),
        RegulationInput("wake", 0, 25000),
    )


def _start_sleep(conn, world_id, clock):
    """Precondition de copie controlee, sans passer par le start legacy.

    Le raccord causal qui choisira effectivement le sommeil n'est pas encore
    implemente. Ce banc commence donc avec un episode canonique deja actif et
    ne teste que son checkpoint/sa terminaison sous ownership ActivityEngine.
    """
    character_id = conn.execute(
        "SELECT id FROM character WHERE world_id=? AND key='sophie'", (world_id,)
    ).fetchone()[0]
    location_id = conn.execute(
        "SELECT id FROM location WHERE world_id=? AND key='chambre_1'", (world_id,)
    ).fetchone()[0]
    start = to_iso(T0)
    with transaction(conn):
        conn.execute(
            "INSERT INTO activity "
            "(public_id,world_id,character_id,type,location_id,started_at,planned_end_at,status,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (new_uuid(), world_id, character_id, "sleep", location_id, start,
             to_iso(T0 + timedelta(hours=12)), "active", start, start),
        )


def test_checkpoint_completes_sleep_once_and_exposes_rearbitration_boundary(synthetic_world):
    conn, world_id, clock = synthetic_world
    _set_state(conn, world_id, anchor=to_iso(T0), h=10_000, phase=0)
    _start_sleep(conn, world_id, clock)
    coordinator = SyntheticSleepActivityCoordinator(conn, clock=clock)
    first = to_iso(T0 + timedelta(seconds=600))
    coordinator.attach_checkpoint(
        world_id, "sophie", first_reassessment_at=first,
        hard_cap_at=to_iso(T0 + timedelta(seconds=1800)),
    )
    sleep_source, wake_source = _sources()
    scheduled = coordinator.next_boundary(world_id, "sophie", wake_source=wake_source, until=first)
    assert scheduled is not None and scheduled.at == first and scheduled.reasons == ("sleep_checkpoint",)

    result = coordinator.process_sleep_checkpoint(
        world_id, "sophie", at_time=first, sleep_source=sleep_source, wake_source=wake_source
    )
    assert result.activity_completed and result.re_arbitration_required
    assert ActivityEngine(conn, clock=clock).activity_sheet(world_id, "sophie") is None
    event = conn.execute(
        "SELECT id,event_type,payload FROM canonical_event WHERE world_id=? ORDER BY seq DESC LIMIT 1",
        (world_id,),
    ).fetchone()
    assert event["event_type"] == "activity_completed" and "sleep_checkpoint" in event["payload"]
    authorization = conn.execute(
        "SELECT boundary_at,consumed_event_id FROM sleep_completion_authorization"
    ).fetchone()
    assert authorization is not None
    assert authorization["boundary_at"] == first
    assert authorization["consumed_event_id"] == event["id"]


def test_direct_sleep_completion_without_authorization_rolls_back_canonical_mutation(synthetic_world):
    """Falsification du bypass : checkpoint present ne veut pas dire reveil autorise."""
    conn, world_id, clock = synthetic_world
    _set_state(conn, world_id, anchor=to_iso(T0), h=10_000, phase=0)
    _start_sleep(conn, world_id, clock)
    coordinator = SyntheticSleepActivityCoordinator(conn, clock=clock)
    due = to_iso(T0 + timedelta(seconds=600))
    coordinator.attach_checkpoint(
        world_id, "sophie", first_reassessment_at=due,
        hard_cap_at=to_iso(T0 + timedelta(seconds=1800)),
    )
    engine = ActivityEngine(conn, clock=clock)
    before_seq = max_seq(conn, world_id)

    with pytest.raises(sqlite3.IntegrityError):
        engine.complete_sleep_from_checkpoint(world_id, "sophie", at_time=due)

    active = engine.activity_sheet(world_id, "sophie")
    assert active is not None and active["type"] == "sleep"
    assert max_seq(conn, world_id) == before_seq
    assert conn.execute("SELECT COUNT(*) FROM sleep_completion_authorization").fetchone()[0] == 0


def test_completion_authorization_cannot_be_minted_before_due_boundary(synthetic_world):
    conn, world_id, clock = synthetic_world
    _start_sleep(conn, world_id, clock)
    coordinator = SyntheticSleepActivityCoordinator(conn, clock=clock)
    due = to_iso(T0 + timedelta(seconds=600))
    coordinator.attach_checkpoint(
        world_id, "sophie", first_reassessment_at=due,
        hard_cap_at=to_iso(T0 + timedelta(seconds=1800)),
    )
    service = SleepTerminationFoundationService(conn, clock=clock)
    with pytest.raises(SleepTerminationError) as raised:
        service.authorize_completion(
            world_id, "sophie", at_time=to_iso(T0 + timedelta(seconds=599)),
            wake_viability_milli=100_000,
        )
    assert raised.value.code == "checkpoint_not_due"
    assert conn.execute("SELECT COUNT(*) FROM sleep_completion_authorization").fetchone()[0] == 0


def test_hard_cap_is_private_idempotent_and_never_completes_sleep(synthetic_world):
    conn, world_id, clock = synthetic_world
    _set_state(conn, world_id, anchor=to_iso(T0), h=95000, phase=500000)
    _start_sleep(conn, world_id, clock)
    coordinator = SyntheticSleepActivityCoordinator(conn, clock=clock)
    cap = to_iso(T0 + timedelta(seconds=1800))
    coordinator.attach_checkpoint(world_id, "sophie", first_reassessment_at=to_iso(T0 + timedelta(seconds=600)), hard_cap_at=cap)
    sleep_source, wake_source = _sources()

    first = coordinator.process_sleep_checkpoint(
        world_id, "sophie", at_time=cap, sleep_source=sleep_source, wake_source=wake_source
    )
    second = coordinator.process_sleep_checkpoint(
        world_id, "sophie", at_time=cap, sleep_source=sleep_source, wake_source=wake_source
    )
    assert first.evaluation.hard_cap_reached and first.hard_cap_reported and not first.activity_completed
    assert second.evaluation.hard_cap_reached and not second.hard_cap_reported and not second.activity_completed
    assert ActivityEngine(conn, clock=clock).activity_sheet(world_id, "sophie")["type"] == "sleep"
    assert conn.execute("SELECT COUNT(*) FROM sleep_termination_audit").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM sleep_completion_authorization").fetchone()[0] == 0


def test_critical_stability_interrupts_once_then_requires_a_new_arbitration_frame(synthetic_world):
    conn, world_id, clock = synthetic_world
    ActivityEngine(conn, clock=clock).start_activity(
        world_id, "sophie", "gaming", "salon", sim_now=to_iso(T0)
    )
    _set_state(conn, world_id, anchor=to_iso(T0), h=100000, phase=500000)
    coordinator = SyntheticSleepActivityCoordinator(conn, clock=clock)
    wake_source = _sources()[1]
    boundary = to_iso(T0 + timedelta(seconds=1))
    scheduled = coordinator.next_boundary(world_id, "sophie", wake_source=wake_source, until=boundary)
    assert scheduled is not None and "wake_stability_critical" in scheduled.reasons

    before = max_seq(conn, world_id)
    first = coordinator.interrupt_critical_wake_stability(
        world_id, "sophie", at_time=boundary, wake_source=wake_source
    )
    after = max_seq(conn, world_id)
    second = coordinator.interrupt_critical_wake_stability(
        world_id, "sophie", at_time=boundary, wake_source=wake_source
    )
    assert first.interrupted and first.reason_code == "wake_stability_critical" and first.re_arbitration_required
    assert not second.interrupted and not second.re_arbitration_required
    assert max_seq(conn, world_id) == after > before
    aborted = conn.execute(
        "SELECT payload FROM canonical_event WHERE world_id=? AND event_type='activity_aborted'",
        (world_id,),
    ).fetchall()
    assert len(aborted) == 1 and "wake_stability_critical" in aborted[0]["payload"]


def test_checkpoint_refuses_early_processing_without_materializing_physiology(synthetic_world):
    conn, world_id, clock = synthetic_world
    _start_sleep(conn, world_id, clock)
    coordinator = SyntheticSleepActivityCoordinator(conn, clock=clock)
    due = to_iso(T0 + timedelta(seconds=600))
    coordinator.attach_checkpoint(world_id, "sophie", first_reassessment_at=due, hard_cap_at=to_iso(T0 + timedelta(seconds=1800)))
    sleep_source, wake_source = _sources()
    before = conn.execute(
        "SELECT anchor_at FROM sleep_regulation_state r JOIN character ch ON ch.id=r.character_id "
        "WHERE r.world_id=? AND ch.key='sophie'", (world_id,)
    ).fetchone()[0]
    with pytest.raises(SyntheticSleepIntegrationError) as raised:
        coordinator.process_sleep_checkpoint(
            world_id, "sophie", at_time=to_iso(T0 + timedelta(seconds=599)),
            sleep_source=sleep_source, wake_source=wake_source,
        )
    assert raised.value.code == "checkpoint_not_due"
    assert conn.execute(
        "SELECT anchor_at FROM sleep_regulation_state r JOIN character ch ON ch.id=r.character_id "
        "WHERE r.world_id=? AND ch.key='sophie'", (world_id,)
    ).fetchone()[0] == before
    assert conn.execute("SELECT COUNT(*) FROM sleep_completion_authorization").fetchone()[0] == 0
