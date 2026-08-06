from datetime import datetime, timezone

import pytest

from vivarium.action_contract import ActionContractError, ActionOrchestrator, IntentProposal
from vivarium.connectors import CLOSED, WorldConnectorService
from vivarium.db import connect_database
from vivarium.initial_residence import install_initial_residence_catalog
from vivarium.environment_blueprints import EnvironmentBlueprintService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, max_seq
from vivarium.util import to_iso


T0 = datetime(2026, 8, 6, 12, 0, 0, tzinfo=timezone.utc)


class FakeClock:
    def now(self):
        return T0

    def now_iso(self):
        return to_iso(self.now())


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    install_initial_residence_catalog(conn)
    world_id = EnvironmentBlueprintService(conn, clock=clock).instantiate("residence.initial", 1)["id"]
    from vivarium.character import CharacterEngine
    CharacterEngine(conn, clock=clock).create_character(world_id, "test_person", "Test", "entree_exterieure")
    yield conn, world_id, clock
    conn.close()


def test_contract_routes_a_valid_traversal_and_attributes_the_canonical_event(setup):
    conn, world_id, _clock = setup
    proposal = IntentProposal.traverse("proposal_entree", "test_person", "porte_entree", "salon")

    result = ActionOrchestrator(conn, clock=_clock).execute(world_id, proposal)

    assert result.status == "accepted"
    assert result.reason_code is None
    assert result.facts[0].event_type == "character_moved"
    assert result.facts[0].payload["action_provenance"] == {
        "proposal_id": "proposal_entree", "origin": "cognition"
    }
    with pytest.raises(TypeError):
        result.facts[0].payload["action_provenance"]["origin"] = "mutated"  # type: ignore[index]
    assert conn.execute(
        "SELECT l.key FROM character ch JOIN location l ON l.id = ch.current_location_id "
        "WHERE ch.world_id = ? AND ch.key = 'test_person'", (world_id,)
    ).fetchone()["key"] == "salon"


def test_refusal_is_a_structured_result_without_any_canonical_write(setup):
    conn, world_id, clock = setup
    WorldConnectorService(conn, clock=clock).set_state(world_id, "porte_entree", CLOSED)
    before_state = canonical_state_digest(conn, world_id)
    before_seq = max_seq(conn, world_id)

    result = ActionOrchestrator(conn, clock=clock).execute(
        world_id, IntentProposal.traverse("proposal_refusee", "test_person", "porte_entree", "salon")
    )

    assert result.status == "refused"
    assert result.reason_code == "connector_closed"
    assert result.facts == ()
    assert canonical_state_digest(conn, world_id) == before_state
    assert max_seq(conn, world_id) == before_seq


def test_retry_of_the_same_intent_is_idempotent_but_identifier_reuse_is_refused(setup):
    conn, world_id, clock = setup
    orchestrator = ActionOrchestrator(conn, clock=clock)
    proposal = IntentProposal.traverse("proposal_retry", "test_person", "porte_entree", "salon")

    first = orchestrator.execute(world_id, proposal)
    second = orchestrator.execute(world_id, proposal)

    assert first == second
    assert max_seq(conn, world_id) == first.facts[0].event_seq
    conflicting = IntentProposal.traverse("proposal_retry", "test_person", "arche_salon_cuisine", "cuisine")
    before_state = canonical_state_digest(conn, world_id)
    with pytest.raises(ActionContractError) as raised:
        orchestrator.execute(world_id, conflicting)
    assert raised.value.code == "proposal_id_conflict"
    assert canonical_state_digest(conn, world_id) == before_state


def test_contract_rejects_unknown_or_mutated_actions_before_execution(setup):
    conn, world_id, _clock = setup
    proposal = IntentProposal.traverse("proposal_valide", "test_person", "porte_entree", "salon")
    with pytest.raises(TypeError):
        proposal.params["connector_key"] = "autre"  # type: ignore[index]
    malformed = IntentProposal(
        proposal_id="proposal_inconnue", actor_key="test_person", action_kind="teleport",
        params=proposal.params, origin="cognition", budget_units=1,
    )
    before_state = canonical_state_digest(conn, world_id)
    before_seq = max_seq(conn, world_id)

    with pytest.raises(ActionContractError) as raised:
        ActionOrchestrator(conn, clock=_clock).execute(world_id, malformed)

    assert raised.value.code == "unsupported_action"
    assert canonical_state_digest(conn, world_id) == before_state
    assert max_seq(conn, world_id) == before_seq
