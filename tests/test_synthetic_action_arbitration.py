"""Integration synthetique du futur arbitre, sans branchement runtime."""

from datetime import datetime, timezone

import pytest

from vivarium.action_arbitration import ActionArbitrationFoundationService
from vivarium.action_contract import ACTION_START_ACTIVITY, ACTION_TRAVERSE
from vivarium.db import connect_database
from vivarium.environment_blueprints import EnvironmentBlueprintService
from vivarium.initial_residence import install_initial_residence_catalog
from vivarium.migrations import ensure_schema
from vivarium.repro import max_seq
from vivarium.sleep_physiology import PhysicalCapacityPolicy
from vivarium.synthetic_action_arbitration import (
    ActionArbitrationFrame,
    ActionArbitrationService,
    ArbitrationContribution,
    PhysicalCostRequest,
    SyntheticActionArbitrationError,
    SyntheticArbitrationPolicy,
    evaluate_physical_cost,
    synthetic_specification,
)
from vivarium.util import to_iso


T0 = datetime(2026, 8, 11, 12, tzinfo=timezone.utc)


class FakeClock:
    def now(self):
        return T0

    def now_iso(self):
        return to_iso(T0)


def _physical_policy() -> PhysicalCapacityPolicy:
    """Coefficients de banc, jamais une calibration de residence."""
    return PhysicalCapacityPolicy(
        "synthetic.capacity.v1", 1,
        {"none": 0, "light": 100, "moderate": 300, "vigorous": 600},
        {"none": 0, "light": 100, "moderate": 300, "vigorous": 600},
        25, {"rest": 100, "sleep": 200}, "synthetic_calibration_only", to_iso(T0),
    )


def _configuration():
    return {
        "schema_version": 1,
        "source_mappings": {
            "sleep_regulation": {"transform": "identity_milli.v1", "correlation_group": "sleep"},
            "physical_recovery": {"transform": "identity_milli.v1", "correlation_group": "recovery"},
            "subjective_intention": {"transform": "identity_milli.v1", "correlation_group": "subjective"},
        },
        "correlation_groups": {"kind": "declared_by_source_mapping.v1"},
        "aggregation": {"kind": "max_per_group_then_saturating_sum.v1"},
        "current_action_inertia": {"max_bonus_milli": 0},
        "quasi_equality": {"band_milli": 1_000},
        "reassessment": {"interval_seconds": 60},
    }


def _policy() -> SyntheticArbitrationPolicy:
    return SyntheticArbitrationPolicy.from_configuration(
        "synthetic.arbitration.v1", 1, _configuration(), "synthetic_calibration_only"
    )


def _contribution(spec, source, score, *, feasible=True):
    owners = {
        "sleep_regulation": "SleepPhysiologyService",
        "physical_recovery": "SleepPhysiologyService",
        "subjective_intention": "GoalService",
    }
    return ArbitrationContribution(spec, source, score, owners[source], "synthetic_lab", feasible)


@pytest.fixture
def synthetic_world():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    install_initial_residence_catalog(conn)
    world_id = EnvironmentBlueprintService(conn, clock=clock).instantiate("residence.initial", 1)["id"]
    from vivarium.character import CharacterEngine
    CharacterEngine(conn, clock=clock).create_character(
        world_id, "test_person", "Test", "entree_exterieure"
    )
    try:
        yield conn, world_id, clock
    finally:
        conn.close()


def _frame(world_id, seq, contributions, *, current=None):
    return ActionArbitrationFrame(
        world_id, "test_person", to_iso(T0), seq, _policy(), tuple(contributions), current
    )


def test_physical_request_is_pure_and_p_can_limit_effort_while_supporting_rest():
    policy = _physical_policy()
    moderate = PhysicalCostRequest("activity", physical_load_class="moderate")
    low = evaluate_physical_cost(policy, moderate, capacity_milli=250)
    high = evaluate_physical_cost(policy, moderate, capacity_milli=800)

    assert not low.feasible and low.reason_code == "physical_capacity_insufficient"
    assert high.feasible and high.reason_code == "physical_capacity_ok"
    assert low.cost_milli == high.cost_milli == 300
    assert evaluate_physical_cost(
        policy, PhysicalCostRequest("traversal", edge_count=3), capacity_milli=74
    ).feasible is False
    with pytest.raises(SyntheticActionArbitrationError):
        PhysicalCostRequest("activity", physical_load_class=None)

    sleep = synthetic_specification(ACTION_START_ACTIVITY, {
        "activity_type": "sleep", "target_location_key": "bedroom",
    })
    rest = synthetic_specification(ACTION_START_ACTIVITY, {
        "activity_type": "rest", "target_location_key": "salon",
    })
    sport = synthetic_specification(ACTION_START_ACTIVITY, {
        "activity_type": "sport", "target_location_key": "salon",
    })
    # H/phi et donc `sleep_regulation` restent fixes. Seule la contribution
    # `physical_recovery` varie avec P dans la couche amont du banc.
    high_p = _frame(1, 0, [_contribution(sleep, "sleep_regulation", 60_000)])
    low_p = _frame(1, 0, [
        _contribution(sleep, "sleep_regulation", 60_000),
        _contribution(rest, "physical_recovery", 80_000),
        # La meme frame peut rendre l'effort non faisable tout en laissant
        # `rest` disponible : P ne contourne jamais l'arbitre.
        _contribution(sport, "subjective_intention", 95_000, feasible=low.feasible),
    ])
    service = ActionArbitrationService()
    assert service.decide(high_p).winner.specification.action_key == sleep.action_key
    assert service.decide(low_p).winner.specification.action_key == rest.action_key
    assert high_p.contributions[0].raw_score_milli == low_p.contributions[0].raw_score_milli
    assert next(
        item for item in service.decide(low_p).candidates if item.specification == sport
    ).feasible is False


def test_arbitration_has_no_category_priority_and_correlated_support_is_not_double_counted():
    sleep = synthetic_specification(ACTION_START_ACTIVITY, {
        "activity_type": "sleep", "target_location_key": "bedroom",
    })
    traverse = synthetic_specification(ACTION_TRAVERSE, {
        "connector_key": "porte_entree", "target_location_key": "salon",
    })
    service = ActionArbitrationService()

    decision = service.decide(_frame(1, 0, [
        _contribution(sleep, "sleep_regulation", 80_000),
        _contribution(traverse, "subjective_intention", 90_000),
    ]))
    assert decision.winner.specification.action_key == traverse.action_key

    # Deux soutiens de la meme source/groupe ne s'additionnent pas en cachette.
    repeated = service.decide(_frame(1, 0, [
        _contribution(sleep, "sleep_regulation", 60_000),
        _contribution(sleep, "sleep_regulation", 60_000),
        _contribution(traverse, "subjective_intention", 70_000),
    ]))
    sleep_candidate = next(item for item in repeated.candidates if item.specification == sleep)
    assert sleep_candidate.score_milli == 60_000
    assert repeated.winner.specification.action_key == traverse.action_key


def test_same_frame_keeps_proposal_identity_and_orchestrator_applies_one_mutation(synthetic_world):
    conn, world_id, clock = synthetic_world
    traverse = synthetic_specification(ACTION_TRAVERSE, {
        "connector_key": "porte_entree", "target_location_key": "salon",
    })
    frame = _frame(world_id, max_seq(conn, world_id), [
        _contribution(traverse, "subjective_intention", 90_000),
    ])
    service = ActionArbitrationService()
    first_decision = service.decide(frame)
    proposal = service.proposal_for(frame, first_decision)
    assert proposal is not None and proposal.origin == "action_arbitration"
    assert proposal.proposal_id == service.proposal_for(frame, first_decision).proposal_id

    first_decision, first = service.execute_synthetic(conn, frame, clock=clock)
    second_decision, second = service.execute_synthetic(conn, frame, clock=clock)
    assert first_decision == second_decision
    assert first.status == second.status == "accepted"
    assert first.facts == second.facts
    assert first.facts[0].payload["action_provenance"] == {
        "proposal_id": proposal.proposal_id, "origin": "action_arbitration",
    }
    assert max_seq(conn, world_id) == first.facts[0].event_seq

    # Une nouvelle frontiere canonique modifie la frame et donc son identite;
    # elle ne peut pas etre confondue avec le retry precedent.
    new_frame = _frame(world_id, max_seq(conn, world_id), [
        _contribution(traverse, "subjective_intention", 90_000),
    ])
    assert service.proposal_for(new_frame, service.decide(new_frame)).proposal_id != proposal.proposal_id


def test_registered_lab_policy_and_private_audit_stay_noncanonical(synthetic_world):
    conn, world_id, clock = synthetic_world
    foundation = ActionArbitrationFoundationService(conn, clock=clock)
    stored = foundation.register_policy(
        "synthetic.arbitration.v1", 1, _configuration(), "synthetic_calibration_only"
    )
    foundation.assign_policy(world_id, stored.policy_key, stored.version, "synthetic_world_setup")
    policy = SyntheticArbitrationPolicy.from_configuration(
        stored.policy_key, stored.version, stored.configuration, stored.provenance
    )
    sleep = synthetic_specification(ACTION_START_ACTIVITY, {
        "activity_type": "sleep", "target_location_key": "bedroom",
    })
    frame = ActionArbitrationFrame(
        world_id, "test_person", to_iso(T0), max_seq(conn, world_id), policy,
        (_contribution(sleep, "sleep_regulation", 70_000),),
    )
    before = max_seq(conn, world_id)
    decision = ActionArbitrationService().decide(frame)
    audit_id = foundation.record_private_audit(
        world_id, frame_digest=decision.frame_digest,
        options=[{"action_key": sleep.action_key}], sources=[{"owner": "SleepPhysiologyService"}],
        result={"outcome": decision.outcome}, canonical_at=to_iso(T0), reason_code="synthetic_probe",
    )
    assert audit_id > 0
    assert max_seq(conn, world_id) == before


def test_synthetic_policy_requires_explicit_groups_and_owner_provenance():
    incomplete = _configuration()
    incomplete.pop("correlation_groups")
    with pytest.raises(SyntheticActionArbitrationError):
        SyntheticArbitrationPolicy.from_configuration("synthetic.policy.v1", 1, incomplete, "test")

    sleep = synthetic_specification(ACTION_START_ACTIVITY, {
        "activity_type": "sleep", "target_location_key": "bedroom",
    })
    with pytest.raises(SyntheticActionArbitrationError):
        ArbitrationContribution(sleep, "sleep_regulation", 1, "GoalService", "forged")


def test_frame_digest_and_proposal_are_invariant_to_contribution_enumeration_order():
    sleep = synthetic_specification(ACTION_START_ACTIVITY, {
        "activity_type": "sleep", "target_location_key": "bedroom",
    })
    traverse = synthetic_specification(ACTION_TRAVERSE, {
        "connector_key": "porte_entree", "target_location_key": "salon",
    })
    contributions = (
        _contribution(sleep, "sleep_regulation", 30_000),
        # Ces deux elements ont la meme cle de tri historique, mais pas la
        # meme semantique. Leur permutation ne doit changer ni digest ni ID.
        _contribution(sleep, "sleep_regulation", 70_000, feasible=False),
        _contribution(traverse, "subjective_intention", 90_000),
    )
    first = _frame(1, 7, contributions)
    second = _frame(1, 7, tuple(reversed(contributions)))
    service = ActionArbitrationService()

    first_decision = service.decide(first)
    second_decision = service.decide(second)
    assert first.digest == second.digest
    assert first_decision == second_decision
    assert first_decision.outcome == "transition"
    assert service.proposal_for(first, first_decision).proposal_id == service.proposal_for(
        second, second_decision
    ).proposal_id
