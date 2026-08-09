"""Tests du pipeline admin immuable : prepare -> validate -> impact -> confirm."""

import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from vivarium.admin_changes import AdminChangeError, AdminChangeService
from vivarium.db import connect_database
from vivarium.migrations import ensure_schema
from vivarium.migrations import MIGRATIONS_DIR, current_version
from vivarium.repro import max_seq
from vivarium.spatial import GraphEngine
from vivarium.util import to_iso
from vivarium.world import WorldEngine

T0 = datetime(2026, 8, 6, 12, 0, 0, tzinfo=timezone.utc)


class FakeClock:
    def __init__(self, start=T0):
        self._now = start

    def now(self):
        return self._now

    def now_iso(self):
        return to_iso(self._now)

    def advance(self, **kwargs):
        self._now += timedelta(**kwargs)


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FakeClock()
    wid = WorldEngine(conn, clock=clock).init_world(name="Avant")['id']
    return conn, clock, wid


def _service(conn, clock):
    return AdminChangeService(conn, clock=clock)


def _audit_count(conn):
    return conn.execute("SELECT COUNT(*) FROM admin_audit_event").fetchone()[0]


def test_prepare_fige_plan_sans_modifier_le_monde_ni_le_journal_canonique(setup):
    conn, clock, wid = setup
    before = max_seq(conn, wid)
    plan = _service(conn, clock).prepare_rename_world(wid, "  Après  ")
    assert plan["action"] == "rename_world"
    assert plan["status"] == "prepared"
    assert plan["payload"] == {"from": "Avant", "to": "Après"}
    assert len(plan["hash"]) == 64
    assert WorldEngine(conn, clock=clock).get_world(wid)["name"] == "Avant"
    assert max_seq(conn, wid) == before
    assert _audit_count(conn) == 1


def test_validate_et_impact_sont_des_lectures_pures(setup):
    conn, clock, wid = setup
    service = _service(conn, clock)
    plan = service.prepare_rename_world(wid, "Après")
    before = (max_seq(conn, wid), _audit_count(conn))
    assert service.validate(plan["id"]) == {"plan_id": plan["id"], "valid": True, "findings": []}
    report = service.impact(plan["id"])
    assert report["impact"]["classification"] == "non_sensitive"
    assert report["impact"]["affected"] == {"world": 1, "characters": 0, "locations": 0}
    assert (max_seq(conn, wid), _audit_count(conn)) == before


def test_confirm_applique_atomiquement_et_lie_le_fait_au_plan(setup):
    conn, clock, wid = setup
    service = _service(conn, clock)
    plan = service.prepare_rename_world(wid, "Après")
    result = service.confirm(plan["id"], plan["hash"])
    assert result == {"plan_id": plan["id"], "status": "applied", "result": {"world_id": wid, "name": "Après"}}
    assert WorldEngine(conn, clock=clock).get_world(wid)["name"] == "Après"
    event = conn.execute(
        "SELECT payload FROM canonical_event WHERE world_id = ? AND event_type = 'world_renamed'",
        (wid,),
    ).fetchone()
    assert json.loads(event["payload"])["admin_change_id"] == plan["id"]
    assert _audit_count(conn) == 2
    assert service._row_to_plan(service._plan_row(plan["id"]))["status"] == "applied"


def test_confirm_retry_is_idempotent(setup):
    conn, clock, wid = setup
    service = _service(conn, clock)
    plan = service.prepare_rename_world(wid, "Après")
    service.confirm(plan["id"], plan["hash"])
    before = (max_seq(conn, wid), _audit_count(conn))
    retry = service.confirm(plan["id"], plan["hash"])
    assert retry["status"] == "already_applied"
    assert retry["result"] == {"world_id": wid, "name": "Après"}
    assert (max_seq(conn, wid), _audit_count(conn)) == before


def test_bad_hash_refused_without_mutation(setup):
    conn, clock, wid = setup
    service = _service(conn, clock)
    plan = service.prepare_rename_world(wid, "Après")
    before = (max_seq(conn, wid), _audit_count(conn))
    with pytest.raises(AdminChangeError, match="hash") as exc:
        service.confirm(plan["id"], "0" * 64)
    assert exc.value.code == "hash_mismatch"
    assert WorldEngine(conn, clock=clock).get_world(wid)["name"] == "Avant"
    assert (max_seq(conn, wid), _audit_count(conn)) == before


def test_plan_expire_sans_mutation(setup):
    conn, clock, wid = setup
    service = _service(conn, clock)
    plan = service.prepare_rename_world(wid, "Après", ttl_seconds=3)
    clock.advance(seconds=4)
    validation = service.validate(plan["id"])
    assert validation["valid"] is False
    assert validation["findings"][0]["code"] == "plan_expired"
    before = (max_seq(conn, wid), _audit_count(conn))
    with pytest.raises(AdminChangeError) as exc:
        service.confirm(plan["id"], plan["hash"])
    assert exc.value.code == "plan_expired"
    assert (max_seq(conn, wid), _audit_count(conn)) == before


def test_changement_concurrent_force_un_nouveau_plan(setup):
    conn, clock, wid = setup
    service = _service(conn, clock)
    plan = service.prepare_rename_world(wid, "Après")
    WorldEngine(conn, clock=clock).rename_world(wid, "Concurrent")
    validation = service.validate(plan["id"])
    assert validation["valid"] is False
    assert validation["findings"][0]["code"] == "world_changed"
    before = (max_seq(conn, wid), _audit_count(conn))
    with pytest.raises(AdminChangeError) as exc:
        service.confirm(plan["id"], plan["hash"])
    assert exc.value.code == "world_changed"
    assert WorldEngine(conn, clock=clock).get_world(wid)["name"] == "Concurrent"
    assert (max_seq(conn, wid), _audit_count(conn)) == before


def test_echec_durant_application_rollback_tout_le_plan(setup, monkeypatch):
    conn, clock, wid = setup
    service = _service(conn, clock)
    plan = service.prepare_rename_world(wid, "Après")
    before = (max_seq(conn, wid), _audit_count(conn))

    def boom(self, conn, world_id, normalized_name, **kwargs):
        raise RuntimeError("artificial failure")

    monkeypatch.setattr(WorldEngine, "_rename_world_in_transaction", boom)
    with pytest.raises(RuntimeError, match="artificial"):
        service.confirm(plan["id"], plan["hash"])
    assert WorldEngine(conn, clock=clock).get_world(wid)["name"] == "Avant"
    assert (max_seq(conn, wid), _audit_count(conn)) == before
    assert service._row_to_plan(service._plan_row(plan["id"]))["status"] == "prepared"


def test_plan_et_audit_sont_immutables(setup):
    conn, clock, wid = setup
    plan = _service(conn, clock).prepare_rename_world(wid, "Après")
    with pytest.raises(Exception, match="(immutable|transition is invalid)"):
        conn.execute(
            "UPDATE admin_change_plan SET payload_json = '{}' WHERE public_id = ?",
            (plan["id"],),
        )
    with pytest.raises(Exception, match="append-only"):
        conn.execute("DELETE FROM admin_audit_event")


def test_prepare_ajout_de_passage_fige_l_impact_sans_muter_le_graphe(setup):
    conn, clock, wid = setup
    service = _service(conn, clock)
    before = (max_seq(conn, wid), _audit_count(conn))
    plan = service.prepare_add_link(wid, "cour", "cuisine", kind="arch")
    assert plan["action"] == "add_link"
    assert plan["payload"] == {
        "from": "cour", "to": "cuisine", "bidirectional": True, "kind": "arch"
    }
    assert plan["impact"]["classification"] == "world_topology"
    assert plan["impact"]["affected"]["directed_links_created"] == 2
    from vivarium.spatial import GraphEngine
    assert GraphEngine(conn, clock=clock).can_traverse(wid, "cour", "cuisine") is False
    assert (max_seq(conn, wid), _audit_count(conn)) == (before[0], before[1] + 1)


def test_confirmer_passage_lie_le_plan_au_fait_canonique(setup):
    conn, clock, wid = setup
    service = _service(conn, clock)
    plan = service.prepare_add_link(wid, "cour", "cuisine", kind="arch")
    result = service.confirm(plan["id"], plan["hash"])
    assert result == {
        "plan_id": plan["id"], "status": "applied",
        "result": {"from": "cour", "to": "cuisine", "bidirectional": True, "kind": "arch"},
    }
    from vivarium.spatial import GraphEngine
    graph = GraphEngine(conn, clock=clock)
    assert graph.can_traverse(wid, "cour", "cuisine") is True
    assert graph.can_traverse(wid, "cuisine", "cour") is True
    event = conn.execute(
        "SELECT payload FROM canonical_event WHERE world_id = ? AND event_type = 'link_added' "
        "ORDER BY seq DESC LIMIT 1",
        (wid,),
    ).fetchone()
    assert json.loads(event["payload"])["admin_change_id"] == plan["id"]


def test_confirmer_passage_sens_unique_ne_cree_pas_le_retour(setup):
    conn, clock, wid = setup
    service = _service(conn, clock)
    plan = service.prepare_add_link(
        wid, "cour", "cuisine", bidirectional=False, kind="service"
    )
    service.confirm(plan["id"], plan["hash"])
    from vivarium.spatial import GraphEngine
    graph = GraphEngine(conn, clock=clock)
    assert graph.can_traverse(wid, "cour", "cuisine") is True
    assert graph.can_traverse(wid, "cuisine", "cour") is False


def test_prepare_et_confirmer_fermeture_sure_lie_le_plan_au_fait(setup):
    conn, clock, wid = setup
    service = _service(conn, clock)
    # Le seed est un arbre : on crée une voie de remplacement avant fermeture.
    GraphEngine(conn, clock=clock).add_link(wid, "cour", "cuisine", bidirectional=True)
    before = max_seq(conn, wid)

    plan = service.prepare_remove_link(wid, "salon", "cuisine")

    assert plan["action"] == "remove_link"
    assert plan["impact"]["affected"]["directed_links_removed"] == 2
    assert plan["impact"]["connectivity_after"]["ok"] is True
    assert max_seq(conn, wid) == before  # préparation sans fait canonique
    result = service.confirm(plan["id"], plan["hash"])
    assert result["result"] == {
        "from": "salon", "to": "cuisine", "bidirectional": True,
        "directed_links_removed": 2,
    }
    graph = GraphEngine(conn, clock=clock)
    assert graph.can_traverse(wid, "salon", "cuisine") is False
    assert graph.find_path(wid, "salon", "cuisine") == ["salon", "cour", "cuisine"]
    event = conn.execute(
        "SELECT payload FROM canonical_event WHERE world_id = ? AND event_type = 'link_removed' "
        "ORDER BY seq DESC LIMIT 1", (wid,),
    ).fetchone()
    assert json.loads(event["payload"])["admin_change_id"] == plan["id"]


def test_preparation_fermeture_isolante_refusee_sans_plan_ni_audit(setup):
    conn, clock, wid = setup
    before = (max_seq(conn, wid), _audit_count(conn))

    with pytest.raises(AdminChangeError) as exc:
        _service(conn, clock).prepare_remove_link(wid, "couloir", "chambre_1")

    assert exc.value.code == "would_isolate_location"
    assert (max_seq(conn, wid), _audit_count(conn)) == before


@pytest.mark.parametrize(
    "from_location,to_location,bidirectional,kind,code",
    [
        ("cour", "cour", True, "door", "invalid_link"),
        ("ghost", "cour", True, "door", "location_not_found"),
        ("salon", "cuisine", True, "door", "no_effect"),
    ],
)
def test_preparation_passage_invalide_refusee_sans_plan(
    setup, from_location, to_location, bidirectional, kind, code
):
    conn, clock, wid = setup
    before = (max_seq(conn, wid), _audit_count(conn))
    with pytest.raises(AdminChangeError) as exc:
        _service(conn, clock).prepare_add_link(
            wid, from_location, to_location, bidirectional=bidirectional, kind=kind
        )
    assert exc.value.code == code
    assert (max_seq(conn, wid), _audit_count(conn)) == before


def test_migration_0016_preserve_les_plans_et_audits_0015(tmp_path):
    partial = tmp_path / "migrations_0015"
    partial.mkdir()
    for source in MIGRATIONS_DIR.glob("*.sql"):
        if source.name <= "0015_admin_change_actions.sql":
            shutil.copy2(source, partial / source.name)
    conn = connect_database(":memory:")
    try:
        assert ensure_schema(conn, directory=partial) == 15
        clock = FakeClock()
        wid = WorldEngine(conn, clock=clock).init_world(name="Avant")["id"]
        plan = _service(conn, clock).prepare_rename_world(wid, "Après")
        assert _audit_count(conn) == 1
        assert ensure_schema(conn) == 37
        restored = _service(conn, clock)._row_to_plan(_service(conn, clock)._plan_row(plan["id"]))
        assert restored["payload"] == {"from": "Avant", "to": "Après"}
        assert _audit_count(conn) == 1
        assert current_version(conn) == 37
    finally:
        conn.close()
