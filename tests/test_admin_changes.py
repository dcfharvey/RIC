"""Tests du pipeline admin immuable : prepare -> validate -> impact -> confirm."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from vivarium.admin_changes import AdminChangeError, AdminChangeService
from vivarium.db import connect_database
from vivarium.migrations import ensure_schema
from vivarium.repro import max_seq
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
