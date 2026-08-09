"""Contrats du banc d'essai reproductible."""

from datetime import datetime, timedelta, timezone

import pytest

from vivarium.bench import (
    BenchAction,
    BenchScenario,
    BenchScenarioError,
    compare_bench_runs,
    run_bench,
)
from vivarium.db import connect_database
from vivarium.migrations import ensure_schema
from vivarium.util import to_iso
from vivarium.world import WorldEngine

T0 = datetime(2026, 8, 1, 8, tzinfo=timezone.utc)


def _at(hours: int = 0, minutes: int = 0) -> str:
    return to_iso(T0 + timedelta(hours=hours, minutes=minutes))


def _base(actions=(), *, target_hours=2):
    return BenchScenario(
        name="scenario de reference",
        start_at=_at(),
        target_at=_at(hours=target_hours),
        actions=tuple(actions),
    )


def test_bench_isole_produit_rapport_auditable_et_json():
    report = run_bench(_base())

    assert report.is_healthy
    assert report.final_time == _at(hours=2)
    assert report.schema_version == 37
    assert report.canonical_state["worlds"]["status"] == "active"
    assert report.raw_events
    assert report.semantic_events
    output = report.to_json()
    assert '"healthy": true' in output
    assert '"refusals": []' in output


def test_bench_exercise_the_closed_intent_contract_in_integration_world():
    scenario = BenchScenario(
        name="intention de traversée",
        start_at=_at(), target_at=_at(), initial_world="integration",
        actions=(BenchAction(
            at=_at(), kind="intent_traverse",
            params={
                "proposal_id": "bench_entree", "actor_key": "sophie",
                "connector_key": "porte_entree", "target_location_key": "salon",
            },
        ),),
    )

    report = run_bench(scenario)

    assert report.is_healthy
    assert report.canonical_state["character"]["sophie"]["location"] == "salon"
    assert any(event[0] == "character_moved" and '"proposal_id":"bench_entree"' in event[3]
               for event in report.semantic_events)


def test_bench_reproduit_strictement_le_meme_scenario():
    scenario = _base(
        (
            BenchAction(at=_at(minutes=30), kind="rename_world", params={"name": "Experience A"}),
            BenchAction(at=_at(hours=1), kind="inflict_injury", params={"character_key": "character_1", "severity_milli": 30000}),
        ),
        target_hours=4,
    )
    left = run_bench(scenario)
    right = run_bench(scenario)

    comparison = compare_bench_runs(left, right)
    assert comparison.identical
    assert left.canonical_state == right.canonical_state
    assert left.semantic_events == right.semantic_events
    assert all(event[1] != "world_renamed" or "Experience A" in event[4] for event in left.raw_events)


def test_bench_conserve_un_refus_attendu_sans_contaminer_le_run():
    report = run_bench(_base((
        BenchAction(
            at=_at(minutes=15),
            kind="move_character",
            params={"character_key": "character_1", "target_location_key": "cuisine"},
            expected="refused",
        ),
    )))

    assert report.is_healthy
    assert len(report.refusals) == 1
    refusal = report.refusals[0]
    assert refusal.error_type == "CharacterError"
    assert refusal.error_code == "activity_active"


def test_bench_refuse_un_resultat_contraire_au_contrat():
    with pytest.raises(BenchScenarioError, match="appliquee alors qu'un refus"):
        run_bench(_base((
            BenchAction(at=_at(), kind="rename_world", params={"name": "Valide"}, expected="refused"),
        )))


def test_bench_refuse_les_actions_non_ordonnees_ou_hors_intervalle():
    with pytest.raises(BenchScenarioError, match="ordre temporel"):
        run_bench(_base((
            BenchAction(at=_at(hours=1), kind="pause_world"),
            BenchAction(at=_at(minutes=30), kind="resume_world"),
        )))
    with pytest.raises(BenchScenarioError, match="intervalle"):
        run_bench(_base((BenchAction(at=_at(hours=3), kind="pause_world"),)))


def test_bench_gere_pause_et_reprise_a_heure_canonique_gelee():
    report = run_bench(_base((
        BenchAction(at=_at(minutes=30), kind="pause_world"),
        BenchAction(at=_at(minutes=30), kind="resume_world"),
    )))

    assert report.is_healthy
    assert [result.kind for result in report.action_results] == ["pause_world", "resume_world"]
    assert report.final_time == _at(hours=2)


def test_bench_refuse_de_faire_passer_le_temps_canonique_pendant_une_pause():
    with pytest.raises(BenchScenarioError, match="pendant une pause"):
        run_bench(_base((
            BenchAction(at=_at(minutes=30), kind="pause_world"),
            BenchAction(at=_at(hours=1), kind="resume_world"),
        )))


def test_bench_ne_touche_jamais_une_base_existante(tmp_path):
    path = tmp_path / "monde-a-preserver.sqlite"
    conn = connect_database(path)
    try:
        ensure_schema(conn)
        original = WorldEngine(conn).init_world(name="Monde a preserver")
        before = list(conn.execute("SELECT name FROM worlds"))
        run_bench(_base())
        after = list(conn.execute("SELECT name FROM worlds"))
        assert original["name"] == "Monde a preserver"
        assert before == after
    finally:
        conn.close()


def test_bench_compare_voit_une_variante_reelle():
    left = run_bench(_base((BenchAction(at=_at(minutes=10), kind="rename_world", params={"name": "A"}),)))
    right = run_bench(_base((BenchAction(at=_at(minutes=10), kind="rename_world", params={"name": "B"}),)))

    comparison = compare_bench_runs(left, right)
    assert not comparison.identical
    assert not comparison.same_canonical_state
    assert not comparison.same_semantic_events


def test_bench_exerce_une_fermeture_spatiale_sure():
    report = run_bench(_base((
        BenchAction(
            at=_at(minutes=30), kind="add_link",
            params={"from_location_key": "cour", "to_location_key": "cuisine"},
        ),
        BenchAction(
            at=_at(minutes=30), kind="remove_link",
            params={"from_location_key": "salon", "to_location_key": "cuisine"},
        ),
    )))

    assert report.is_healthy
    assert [result.outcome for result in report.action_results] == ["applied", "applied"]
    assert report.canonical_state["worlds"]["name"] == "Banc d'essai temporaire"


def test_bench_expose_un_refus_de_fermeture_isolante():
    report = run_bench(_base((
        BenchAction(
            at=_at(minutes=30), kind="remove_link",
            params={"from_location_key": "couloir", "to_location_key": "chambre_1"},
            expected="refused",
        ),
    )))

    assert report.is_healthy
    assert report.refusals[0].error_type == "GraphError"
    assert report.refusals[0].error_code == "would_isolate_location"


def test_bench_can_audit_the_real_integration_world_without_persistence():
    scenario = BenchScenario(
        name="arrivée de référence",
        start_at=_at(),
        target_at=_at(),
        initial_world="integration",
    )

    report = run_bench(scenario)

    assert report.is_healthy
    assert sorted(report.canonical_state["character"]) == ["chuu", "erika", "luna", "patoune", "sophie"]
    assert all(
        item["location"] == "entree_exterieure"
        for item in report.canonical_state["character"].values()
    )
    assert report.canonical_state["world_initial_context"]["residency"]["voluntary"] is True
