"""Falsifications du raccord causal arbitre, sans runtime ni residence reelle."""

from dataclasses import asdict
from datetime import datetime, timedelta, timezone

import pytest

from vivarium.action_arbitration import ActionArbitrationFoundationService
from vivarium.action_contract import ACTION_START_ACTIVITY, ActionOrchestrator, IntentProposal
from vivarium.circadian_model import calibration_profiles
from vivarium.db import connect_database, transaction
from vivarium.goals import GoalService
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import max_seq
from vivarium.sleep_physiology import (
    ADDITIVE_MODEL_KEY,
    SleepPhysiologyFoundationService,
    SleepPhysiologyError,
    SleepPhysiologyService,
)
from vivarium.synthetic_action_arbitration import (
    ActionArbitrationService,
    SyntheticActionArbitrationError,
    SyntheticCausalArbitrationBuilder,
    synthetic_specification,
)
from vivarium.util import new_uuid, to_iso


T0 = datetime(2026, 8, 11, 12, tzinfo=timezone.utc)


class FakeClock:
    def __init__(self):
        self.current = T0

    def now(self):
        return self.current

    def now_iso(self):
        return to_iso(self.current)


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


def _physical_policy():
    """Coefficients [D] de banc uniquement; aucune promotion production."""
    return {
        "schema_version": 1,
        "activity_cost_per_hour_milli": {
            "none": 0, "light": 5_000, "moderate": 15_000, "vigorous": 30_000,
        },
        "minimum_capacity_milli": {
            "none": 0, "light": 10_000, "moderate": 30_000, "vigorous": 60_000,
        },
        "traversal_cost_per_edge_milli": 5_000,
        "recovery_per_hour_milli": {"rest": 10_000, "sleep": 20_000},
    }


def _calibrated_arbitration_policy():
    """Mappings explicites de banc; valeurs arbitraires et falsifiables [D]."""
    return {
        "schema_version": 1,
        "source_mappings": {
            "sleep_regulation": {
                "transform": "linear_clamped_milli.v1",
                "correlation_group": "sleep",
                "input_low_milli": 60_000,
                "input_high_milli": 100_000,
                "direction": "ascending",
            },
            "physical_recovery": {
                "transform": "linear_clamped_milli.v1",
                "correlation_group": "recovery",
                "input_low_milli": 20_000,
                "input_high_milli": 80_000,
                "direction": "descending",
            },
            "subjective_intention": {
                "transform": "linear_clamped_milli.v1",
                "correlation_group": "subjective",
                "input_low_milli": 0,
                "input_high_milli": 100_000,
                "direction": "ascending",
            },
        },
        "correlation_groups": {"kind": "declared_by_source_mapping.v1"},
        "aggregation": {"kind": "max_per_group_then_saturating_sum.v1"},
        "current_action_inertia": {"max_bonus_milli": 0},
        "quasi_equality": {"band_milli": 1_000},
        "reassessment": {"interval_seconds": 60},
    }


def _identity_arbitration_policy():
    return {
        "schema_version": 1,
        "source_mappings": {
            source: {"transform": "identity_milli.v1", "correlation_group": source}
            for source in ("sleep_regulation", "physical_recovery", "subjective_intention")
        },
        "correlation_groups": {"kind": "declared_by_source_mapping.v1"},
        "aggregation": {"kind": "max_per_group_then_saturating_sum.v1"},
        "current_action_inertia": {"max_bonus_milli": 0},
        "quasi_equality": {"band_milli": 1_000},
        "reassessment": {"interval_seconds": 60},
    }


def _classify_activities_for_lab(conn, world_id):
    """Calibration locale explicite; 0049 reste volontairement NULL en production."""
    with transaction(conn) as tx:
        tx.execute(
            "UPDATE activity_definition SET physical_load_class = CASE "
            "WHEN activity_type IN ('sleep','rest','idle') THEN 'none' "
            "WHEN activity_type='sport' THEN 'vigorous' "
            "ELSE 'light' END WHERE world_id=?",
            (world_id,),
        )


def _activate_synthetic(conn, world_id, anchor):
    with transaction(conn) as tx:
        tx.execute(
            "UPDATE world_physiology_system SET status='active',activated_at=?,activated_by=?,updated_at=? "
            "WHERE world_id=?", (anchor, "synthetic_test", anchor, world_id),
        )
        for row in tx.execute("SELECT id FROM character WHERE world_id=?", (world_id,)):
            for statement, values in (
                (
                    "INSERT INTO sleep_regulation_state "
                    "(public_id,world_id,character_id,model_key,model_version,homeostatic_load_milli,circadian_phase_milli,anchor_at,updated_at) "
                    "VALUES (?,?,?,?,1,10000,0,?,?)",
                    (new_uuid(), world_id, row["id"], ADDITIVE_MODEL_KEY, anchor, anchor),
                ),
                (
                    "INSERT INTO physical_capacity_state "
                    "(public_id,world_id,character_id,capacity_milli,rate_remainder,anchor_at,updated_at) "
                    "VALUES (?,?,?,?,0,?,?)",
                    (new_uuid(), world_id, row["id"], 20_000, anchor, anchor),
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


def _make_world(arbitration_policy):
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    anchor = to_iso(T0)
    physiology = SleepPhysiologyFoundationService(conn, clock=clock)
    physiology.register_light_schedule("causal.day.v1", 1, _schedule())
    physiology.register_location_light_profile("causal.interior.v1", 1, 25_000, {"kind": "interior"})
    physiology.register_biology_profile("causal.human.v1", 1, "human_reference", _profile_payload())
    physiology.assign_light_schedule(world_id, "causal.day.v1", 1, anchor, "synthetic_setup")
    for row in conn.execute("SELECT key FROM location WHERE world_id=?", (world_id,)):
        physiology.assign_location_light_profile(
            world_id, row["key"], "causal.interior.v1", 1, anchor, "synthetic_setup"
        )
    for row in conn.execute("SELECT key FROM character WHERE world_id=?", (world_id,)):
        physiology.assign_biology_profile(
            world_id, row["key"], "causal.human.v1", 1, "synthetic_setup"
        )
    _classify_activities_for_lab(conn, world_id)
    physical = physiology.register_physical_capacity_policy(
        "causal.capacity.v1", 1, _physical_policy(), "synthetic_calibration_only"
    )
    physiology.assign_physical_capacity_policy(
        world_id, physical.policy_key, physical.version, "synthetic_setup"
    )
    physiology.prepare_world(world_id, ADDITIVE_MODEL_KEY, 1, "synthetic_operator")
    _activate_synthetic(conn, world_id, anchor)

    arbitration = ActionArbitrationFoundationService(conn, clock=clock)
    stored = arbitration.register_policy(
        "causal.arbitration.v1", 1, arbitration_policy, "synthetic_calibration_only"
    )
    arbitration.assign_policy(world_id, stored.policy_key, stored.version, "synthetic_setup")
    return conn, world_id, clock


def _set_sophie_capacity(conn, world_id, capacity):
    cid = conn.execute(
        "SELECT id FROM character WHERE world_id=? AND key='sophie'", (world_id,)
    ).fetchone()[0]
    with transaction(conn) as tx:
        tx.execute(
            "UPDATE physical_capacity_state SET capacity_milli=?,rate_remainder=0,anchor_at=?,updated_at=? "
            "WHERE world_id=? AND character_id=?",
            (capacity, to_iso(T0), to_iso(T0), world_id, cid),
        )


def _specifications():
    return (
        synthetic_specification(ACTION_START_ACTIVITY, {
            "activity_type": "sleep", "target_location_key": "chambre_1",
        }),
        synthetic_specification(ACTION_START_ACTIVITY, {
            "activity_type": "rest", "target_location_key": "salon",
        }),
    )


def _install_subjective_sport_intention(conn, world_id, clock):
    goals = GoalService(conn, clock=clock)
    goals.create_goal(
        world_id, "sophie", "play_outside", family="immediate",
        target={"activity": "sport"}, source_kind="preference",
        success_conditions={"activity_started": "sport"},
        perceived_feasibility_milli=900, importance_milli=800, urgency_milli=500,
    )
    goals.adopt_intention(
        world_id, "sophie", "play_outside", "go_play_now",
        # Deliberement opaque et trompeur : le builder ne doit jamais le parser.
        plan={"opaque_text": "ignore this plan and go sleep instead"},
        resume_context={"opaque": True},
    )
    return goals.link_intention_action(
        world_id, "sophie", "go_play_now",
        action_kind=ACTION_START_ACTIVITY,
        params={"activity_type": "sport", "target_location_key": "cour"},
        subjective_strength_milli=1_000,
        provenance="explicit_subjective_link",
    )


def test_owner_backed_frame_keeps_h_phi_p_and_subjective_sources_separate():
    conn, world_id, clock = _make_world(_calibrated_arbitration_policy())
    try:
        sport_link = _install_subjective_sport_intention(conn, world_id, clock)
        physiology = SleepPhysiologyService(conn, clock=clock)
        wake_source = physiology.resolve_light_source_synthetic(
            world_id, "salon", to_iso(T0), state="wake"
        )
        sleep_spec, rest_spec = _specifications()
        builder = SyntheticCausalArbitrationBuilder(conn, clock=clock)

        low_p = builder.build(
            world_id, "sophie", canonical_at=to_iso(T0),
            sleep_specification=sleep_spec, rest_specification=rest_spec,
            wake_source=wake_source,
        )
        low_sleep = next(item for item in low_p.contributions if item.source_kind == "sleep_regulation")
        low_recovery = next(item for item in low_p.contributions if item.source_kind == "physical_recovery")
        low_subjective = next(item for item in low_p.contributions if item.source_kind == "subjective_intention")

        assert low_sleep.specification == sleep_spec
        assert low_sleep.owner == "SleepPhysiologyService"
        assert low_sleep.provenance == "sleep_physiology_h_phi"
        assert low_recovery.specification == rest_spec
        assert low_recovery.raw_score_milli == 20_000
        assert low_recovery.owner == "SleepPhysiologyService"
        assert low_subjective.specification.action_key == sport_link["action_key"]
        assert low_subjective.owner == "GoalService"
        assert low_subjective.provenance == "explicit_subjective_link"
        assert low_subjective.feasible is False
        assert all(
            not (item.specification == sleep_spec and item.source_kind == "physical_recovery")
            for item in low_p.contributions
        )
        assert len(low_p.contributions) == 3

        _set_sophie_capacity(conn, world_id, 80_000)
        high_p = builder.build(
            world_id, "sophie", canonical_at=to_iso(T0),
            sleep_specification=sleep_spec, rest_specification=rest_spec,
            wake_source=wake_source,
        )
        high_sleep = next(item for item in high_p.contributions if item.source_kind == "sleep_regulation")
        high_recovery = next(item for item in high_p.contributions if item.source_kind == "physical_recovery")
        high_subjective = next(item for item in high_p.contributions if item.source_kind == "subjective_intention")

        # Modifier P seul ne peut ni recreer ni reponderer la cause H/phi.
        assert high_sleep.raw_score_milli == low_sleep.raw_score_milli
        assert high_recovery.raw_score_milli == 80_000
        assert high_subjective.feasible is True
        recovery_mapping = high_p.policy.source_mappings["physical_recovery"]
        assert recovery_mapping.apply(low_recovery.raw_score_milli) > recovery_mapping.apply(
            high_recovery.raw_score_milli
        )
        assert all(
            not (item.specification == sleep_spec and item.source_kind == "physical_recovery")
            for item in high_p.contributions
        )
    finally:
        conn.close()


def test_opaque_intention_plan_cannot_invent_an_executable_action():
    conn, world_id, clock = _make_world(_calibrated_arbitration_policy())
    try:
        link = _install_subjective_sport_intention(conn, world_id, clock)
        physiology = SleepPhysiologyService(conn, clock=clock)
        wake_source = physiology.resolve_light_source_synthetic(
            world_id, "salon", to_iso(T0), state="wake"
        )
        sleep_spec, rest_spec = _specifications()
        frame = SyntheticCausalArbitrationBuilder(conn, clock=clock).build(
            world_id, "sophie", canonical_at=to_iso(T0),
            sleep_specification=sleep_spec, rest_specification=rest_spec,
            wake_source=wake_source,
        )
        subjective = [item for item in frame.contributions if item.source_kind == "subjective_intention"]
        assert len(subjective) == 1
        assert subjective[0].specification.action_key == link["action_key"]
        assert subjective[0].specification.params["activity_type"] == "sport"
    finally:
        conn.close()


def test_identity_mapping_is_accepted_by_legacy_lab_but_refused_by_causal_builder():
    conn, world_id, clock = _make_world(_identity_arbitration_policy())
    try:
        physiology = SleepPhysiologyService(conn, clock=clock)
        wake_source = physiology.resolve_light_source_synthetic(
            world_id, "salon", to_iso(T0), state="wake"
        )
        sleep_spec, rest_spec = _specifications()
        with pytest.raises(SyntheticActionArbitrationError) as raised:
            SyntheticCausalArbitrationBuilder(conn, clock=clock).build(
                world_id, "sophie", canonical_at=to_iso(T0),
                sleep_specification=sleep_spec, rest_specification=rest_spec,
                wake_source=wake_source,
            )
        assert raised.value.code == "uncalibrated_identity_mapping"
        assert max_seq(conn, world_id) >= 0
    finally:
        conn.close()


def test_private_owner_provenance_audit_does_not_mutate_canon():
    conn, world_id, clock = _make_world(_calibrated_arbitration_policy())
    try:
        _install_subjective_sport_intention(conn, world_id, clock)
        physiology = SleepPhysiologyService(conn, clock=clock)
        wake_source = physiology.resolve_light_source_synthetic(
            world_id, "salon", to_iso(T0), state="wake"
        )
        sleep_spec, rest_spec = _specifications()
        builder = SyntheticCausalArbitrationBuilder(conn, clock=clock)
        frame = builder.build(
            world_id, "sophie", canonical_at=to_iso(T0),
            sleep_specification=sleep_spec, rest_specification=rest_spec,
            wake_source=wake_source,
        )
        decision = ActionArbitrationService().decide(frame)
        before = max_seq(conn, world_id)
        audit_id = builder.audit_decision(frame, decision)
        assert audit_id > 0
        assert max_seq(conn, world_id) == before
        sources = conn.execute(
            "SELECT sources_json FROM action_arbitration_audit WHERE id=?", (audit_id,)
        ).fetchone()[0]
        assert "SleepPhysiologyService" in sources
        assert "GoalService" in sources
        assert "sleep_physiology_h_phi" in sources
        assert "physical_capacity_p" in sources
    finally:
        conn.close()


def test_owner_backed_light_projection_rejects_free_or_stale_inputs():
    conn, world_id, clock = _make_world(_calibrated_arbitration_policy())
    try:
        physiology = SleepPhysiologyService(conn, clock=clock)
        source = physiology.resolve_light_source_owner_backed(world_id, "sophie", at_time=to_iso(T0))
        assert source.provenance == "SleepPhysiologyService.owner_backed_light_v1"
        assert source.source.occluded is False
        assert source.source.stimulation == 0.0
        assert source.assignment_metadata["schedule_assignment"]["profile_key"] == "causal.day.v1"
        assert source.assignment_metadata["location_assignment"]["profile_key"] == "causal.interior.v1"
        viability = physiology.project_wake_viability_owner_backed(
            world_id, "sophie", at_time=to_iso(T0)
        )
        assert viability.world_id == world_id
        assert viability.character_key == "sophie"
        assert viability.input_fingerprint != source.input_fingerprint

        clock.current = T0 + timedelta(seconds=5)
        current = to_iso(clock.current)
        current_source = physiology.resolve_light_source_owner_backed(
            world_id, "sophie", at_time=current
        )
        assert current_source.canonical_at == current
        with pytest.raises(SleepPhysiologyError) as stale_physiology:
            physiology.project_wake_viability_owner_backed(
                world_id, "sophie", at_time=current
            )
        assert stale_physiology.value.code == "stale_physiology_anchor"
        with pytest.raises(SleepPhysiologyError) as raised:
            physiology.resolve_light_source_owner_backed(
                world_id, "sophie", at_time=to_iso(T0)
            )
        assert raised.value.code == "stale_canonical_anchor"
        with pytest.raises(SleepPhysiologyError) as unknown_character:
            physiology.resolve_light_source_owner_backed(
                world_id, "not_a_character", at_time=current
            )
        assert unknown_character.value.code == "character_not_found"
        with pytest.raises(SleepPhysiologyError) as unknown_world:
            physiology.resolve_light_source_owner_backed(
                world_id + 999, "sophie", at_time=current
            )
        assert unknown_world.value.code == "world_not_found"
    finally:
        conn.close()


def test_owner_backed_wake_viability_fingerprint_covers_physiology_state():
    conn, world_id, clock = _make_world(_calibrated_arbitration_policy())
    try:
        physiology = SleepPhysiologyService(conn, clock=clock)
        first = physiology.project_wake_viability_owner_backed(
            world_id, "sophie", at_time=to_iso(T0)
        )
        character_id = conn.execute(
            "SELECT id FROM character WHERE world_id=? AND key='sophie'", (world_id,)
        ).fetchone()[0]
        with transaction(conn) as tx:
            tx.execute(
                "UPDATE sleep_regulation_state SET homeostatic_load_milli=? "
                "WHERE world_id=? AND character_id=?",
                (85_000, world_id, character_id),
            )
        second = physiology.project_wake_viability_owner_backed(
            world_id, "sophie", at_time=to_iso(T0)
        )
        assert first.value_milli != second.value_milli
        assert first.input_fingerprint != second.input_fingerprint
    finally:
        conn.close()


def test_owner_backed_wake_viability_stale_anchor_is_read_only():
    conn, world_id, clock = _make_world(_calibrated_arbitration_policy())
    try:
        clock.current = T0 + timedelta(seconds=5)
        before_events = max_seq(conn, world_id)
        before = tuple(conn.execute(
            "SELECT homeostatic_load_milli, circadian_phase_milli, anchor_at "
            "FROM sleep_regulation_state WHERE world_id=? ORDER BY character_id",
            (world_id,),
        ).fetchall())
        with pytest.raises(SleepPhysiologyError) as raised:
            SleepPhysiologyService(conn, clock=clock).project_wake_viability_owner_backed(
                world_id, "sophie", at_time=to_iso(clock.current)
            )
        assert raised.value.code == "stale_physiology_anchor"
        after = tuple(conn.execute(
            "SELECT homeostatic_load_milli, circadian_phase_milli, anchor_at "
            "FROM sleep_regulation_state WHERE world_id=? ORDER BY character_id",
            (world_id,),
        ).fetchall())
        assert before == after
        assert max_seq(conn, world_id) == before_events
    finally:
        conn.close()


def test_owner_backed_builder_has_no_free_wake_source_argument():
    conn, world_id, clock = _make_world(_calibrated_arbitration_policy())
    try:
        sleep_spec, rest_spec = _specifications()
        frame = SyntheticCausalArbitrationBuilder(conn, clock=clock).build_owner_backed(
            world_id, "sophie", canonical_at=to_iso(T0),
            sleep_specification=sleep_spec, rest_specification=rest_spec,
        )
        assert frame.world_id == world_id
        assert any(item.source_kind == "sleep_regulation" for item in frame.contributions)
    finally:
        conn.close()


def test_rejected_action_proposal_does_not_debit_physical_capacity():
    conn, world_id, clock = _make_world(_calibrated_arbitration_policy())
    try:
        before = tuple(conn.execute(
            "SELECT capacity_milli, rate_remainder, anchor_at FROM physical_capacity_state "
            "WHERE world_id=? ORDER BY character_id", (world_id,)
        ).fetchall())
        proposal = IntentProposal.start_activity(
            "rejected_physical_cost", "sophie", "sport", "cour"
        )
        result = ActionOrchestrator(conn, clock=clock).execute(
            world_id, proposal, effective_at=to_iso(T0), expected_event_seq=999_999
        )
        assert result.status == "refused"
        assert result.reason_code == "stale_decision_context"
        after = tuple(conn.execute(
            "SELECT capacity_milli, rate_remainder, anchor_at FROM physical_capacity_state "
            "WHERE world_id=? ORDER BY character_id", (world_id,)
        ).fetchall())
        assert before == after
    finally:
        conn.close()
