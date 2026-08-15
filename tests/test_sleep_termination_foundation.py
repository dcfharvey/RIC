"""Politique de fin de sommeil : fondation pure/inactive, sans runtime."""

from datetime import datetime, timezone, timedelta

import pytest

from vivarium.db import connect_database, transaction
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema, load_migrations, split_sql_statements
from vivarium.sleep_termination import (
    SleepTerminationError,
    SleepTerminationFoundationService,
    evaluate_sleep_checkpoint,
)
from vivarium.sleep_physiology import OwnerBackedWakeViability, SleepPhysiologyService
from vivarium.util import new_uuid, to_iso


T0 = datetime(2026, 8, 11, 12, tzinfo=timezone.utc)


class FakeClock:
    def now(self): return T0
    def now_iso(self): return to_iso(T0)


def _policy():
    # Parametres de banc explicites; aucune calibration residence/production.
    return {
        "schema_version": 1,
        "checkpoint_interval_seconds": 900,
        "hard_cap_seconds": 28_800,
        "wake_admissible_enter_milli": 65_000,
        "wake_admissible_exit_milli": 55_000,
    }


def _apply_through(conn, version):
    conn.execute("CREATE TABLE migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL, checksum TEXT NOT NULL)")
    for migration in load_migrations():
        if migration.version <= version:
            with transaction(conn):
                for statement in split_sql_statements(migration.sql): conn.execute(statement)
                conn.execute("INSERT INTO migrations (version,name,applied_at,checksum) VALUES (?,?,?,?)", (migration.version,migration.name,to_iso(T0),migration.checksum))


@pytest.fixture
def setup():
    conn=connect_database(":memory:"); ensure_schema(conn); clock=FakeClock()
    world=IntegrationWorldService(conn,clock=clock).create_initial_world(); service=SleepTerminationFoundationService(conn,clock=clock)
    policy=service.register_policy("synthetic.sleep_termination.v1",1,_policy(),"synthetic_calibration_only")
    try: yield conn, world["id"], service, policy
    finally: conn.close()


def test_policy_assignment_is_immutable_and_creates_no_checkpoint_or_canonical_event(setup):
    conn,world,service,policy=setup
    before=conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id=?",(world,)).fetchone()[0]
    assert service.assign_policy(world,policy.policy_key,policy.version,"synthetic_world_setup") == policy
    assert service.world_policy(world) == policy
    assert conn.execute("SELECT COUNT(*) FROM activity_sleep_checkpoint").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM sleep_termination_audit").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id=?",(world,)).fetchone()[0] == before
    with pytest.raises(Exception,match="immutable"): conn.execute("UPDATE sleep_termination_policy SET provenance='mutated'")
    with pytest.raises(Exception,match="append-only"): conn.execute("DELETE FROM world_sleep_termination_policy_assignment WHERE world_id=?",(world,))


def test_policy_requires_explicit_strict_hysteresis_and_no_default_calibration(setup):
    _conn,_world,service,_policy_value=setup
    missing=_policy(); missing.pop("hard_cap_seconds")
    with pytest.raises(SleepTerminationError) as absent: service.register_policy("synthetic.missing.v1",1,missing,"test")
    assert absent.value.code == "invalid_configuration"
    above=_policy(); above["wake_admissible_exit_milli"]=70_000
    with pytest.raises(SleepTerminationError) as invalid_above: service.register_policy("synthetic.above.v1",1,above,"test")
    assert invalid_above.value.code == "invalid_configuration"
    equal=_policy(); equal["wake_admissible_exit_milli"]=65_000
    with pytest.raises(SleepTerminationError) as invalid_equal: service.register_policy("synthetic.equal.v1",1,equal,"test")
    assert invalid_equal.value.code == "invalid_configuration"
    assert service.register_policy("synthetic.strict.v1",1,_policy(),"test").wake_admissible_exit_milli < 65_000


def test_checkpoint_schema_binds_only_a_sleep_activity_to_its_world_policy(setup):
    conn,world,service,policy=setup
    service.assign_policy(world,policy.policy_key,policy.version,"synthetic_world_setup")
    row=conn.execute(
        "SELECT ch.id AS character_id,l.id AS location_id,p.id AS policy_id "
        "FROM character ch JOIN location l ON l.world_id=ch.world_id "
        "JOIN sleep_termination_policy p WHERE ch.world_id=? AND ch.key='sophie'",(world,)
    ).fetchone()
    now=to_iso(T0)
    conn.execute(
        "INSERT INTO activity (public_id,world_id,character_id,type,location_id,started_at,planned_end_at,status,created_at,updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",(new_uuid(),world,row["character_id"],"sleep",row["location_id"],now,now,"active",now,now)
    )
    activity_id=conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        "INSERT INTO activity_sleep_checkpoint (public_id,world_id,character_id,activity_id,policy_id,next_reassessment_at,previous_band,hard_cap_at,created_at,updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",(new_uuid(),world,row["character_id"],activity_id,row["policy_id"],now,"continue_sleep",now,now,now)
    )
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    with pytest.raises(Exception,match="cannot be deleted"):
        conn.execute("DELETE FROM activity_sleep_checkpoint WHERE activity_id=?",(activity_id,))


def test_checkpoint_identity_is_immutable_but_its_planning_state_can_advance(setup):
    conn,world,service,policy=setup
    service.assign_policy(world,policy.policy_key,policy.version,"synthetic_world_setup")
    rows=conn.execute(
        "SELECT ch.id AS character_id,l.id AS location_id,p.id AS policy_id,ch.key "
        "FROM character ch JOIN location l ON l.world_id=ch.world_id "
        "JOIN sleep_termination_policy p WHERE ch.world_id=? AND ch.key IN ('sophie','erika') ORDER BY ch.key",(world,)
    ).fetchall()
    by_key={row["key"]:row for row in rows}; now=to_iso(T0)
    activity_ids={}
    for key in ("sophie","erika"):
        row=by_key[key]
        conn.execute(
            "INSERT INTO activity (public_id,world_id,character_id,type,location_id,started_at,planned_end_at,status,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",(new_uuid(),world,row["character_id"],"sleep",row["location_id"],now,now,"active",now,now)
        )
        activity_ids[key]=conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    sophie=by_key["sophie"]
    conn.execute(
        "INSERT INTO activity_sleep_checkpoint (public_id,world_id,character_id,activity_id,policy_id,next_reassessment_at,previous_band,hard_cap_at,created_at,updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",(new_uuid(),world,sophie["character_id"],activity_ids["sophie"],sophie["policy_id"],now,"continue_sleep",now,now,now)
    )
    checkpoint_id=conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    for column,value in (("public_id",new_uuid()),("activity_id",activity_ids["erika"]),("character_id",by_key["erika"]["character_id"]),("policy_id",999_999),("hard_cap_at","2026-08-12T12:00:00.000+00:00")):
        with pytest.raises(Exception,match="identity is immutable"):
            conn.execute(f"UPDATE activity_sleep_checkpoint SET {column}=? WHERE id=?",(value,checkpoint_id))
    conn.execute(
        "UPDATE activity_sleep_checkpoint SET next_reassessment_at=?, previous_band='wake_admissible', updated_at=? WHERE id=?",("2026-08-11T12:15:00.000+00:00","2026-08-11T12:15:00.000+00:00",checkpoint_id)
    )
    current=conn.execute("SELECT next_reassessment_at,previous_band FROM activity_sleep_checkpoint WHERE id=?",(checkpoint_id,)).fetchone()
    assert tuple(current)==("2026-08-11T12:15:00.000+00:00","wake_admissible")


def test_hard_cap_audit_rejects_crossed_checkpoint_identity(setup):
    conn,world,service,policy=setup
    service.assign_policy(world,policy.policy_key,policy.version,"synthetic_world_setup")
    rows=conn.execute(
        "SELECT ch.id AS character_id,l.id AS location_id,p.id AS policy_id,ch.key "
        "FROM character ch JOIN location l ON l.world_id=ch.world_id "
        "JOIN sleep_termination_policy p WHERE ch.world_id=? AND ch.key IN ('sophie','erika') ORDER BY ch.key",(world,)
    ).fetchall()
    by_key={row["key"]:row for row in rows}; now=to_iso(T0)
    activity_ids={}
    for key in ("sophie","erika"):
        row=by_key[key]
        conn.execute(
            "INSERT INTO activity (public_id,world_id,character_id,type,location_id,started_at,planned_end_at,status,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",(new_uuid(),world,row["character_id"],"sleep",row["location_id"],now,now,"active",now,now)
        )
        activity_ids[key]=conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    sophie=by_key["sophie"]
    conn.execute(
        "INSERT INTO activity_sleep_checkpoint (public_id,world_id,character_id,activity_id,policy_id,next_reassessment_at,previous_band,hard_cap_at,created_at,updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",(new_uuid(),world,sophie["character_id"],activity_ids["sophie"],sophie["policy_id"],now,"continue_sleep",now,now,now)
    )
    checkpoint_id=conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    erika=by_key["erika"]
    with pytest.raises(Exception,match="checkpoint mismatch"):
        conn.execute(
            "INSERT INTO sleep_termination_audit (public_id,world_id,character_id,activity_id,checkpoint_id,operation,details_json,recorded_at) "
            "VALUES (?,?,?,?,?,'hard_cap_protective','{}',?)",(new_uuid(),world,erika["character_id"],activity_ids["erika"],checkpoint_id,now)
        )
    conn.execute(
        "INSERT INTO sleep_termination_audit (public_id,world_id,character_id,activity_id,checkpoint_id,operation,details_json,recorded_at) "
        "VALUES (?,?,?,?,?,'hard_cap_protective','{}',?)",(new_uuid(),world,sophie["character_id"],activity_ids["sophie"],checkpoint_id,now)
    )
    assert conn.execute("SELECT COUNT(*) FROM sleep_termination_audit WHERE checkpoint_id=?",(checkpoint_id,)).fetchone()[0] == 1


def test_pure_checkpoint_hysteresis_requires_reassessment_without_legacy_needs(setup):
    _conn,_world,_service,policy=setup
    low=evaluate_sleep_checkpoint(policy,elapsed_seconds=900,wake_viability_milli=64_999,previous_band="continue_sleep")
    assert low.reason_code == "continue_sleep" and not low.completion_eligible and low.next_reassessment_after_seconds == 900
    entered=evaluate_sleep_checkpoint(policy,elapsed_seconds=1_800,wake_viability_milli=65_000,previous_band="continue_sleep")
    assert entered.band == "wake_admissible" and entered.completion_eligible
    held=evaluate_sleep_checkpoint(policy,elapsed_seconds=2_700,wake_viability_milli=55_000,previous_band="wake_admissible")
    assert held.band == "wake_admissible" and held.completion_eligible
    exited=evaluate_sleep_checkpoint(policy,elapsed_seconds=3_600,wake_viability_milli=54_999,previous_band="wake_admissible")
    assert exited.band == "continue_sleep" and not exited.completion_eligible


def test_external_wake_requires_explicit_access_and_hard_cap_never_completes_sleep(setup):
    _conn,_world,_service,policy=setup
    inaccessible=evaluate_sleep_checkpoint(policy,elapsed_seconds=1_000,wake_viability_milli=0,previous_band="continue_sleep",external_wake_accessible=False)
    assert inaccessible.reason_code == "continue_sleep" and not inaccessible.completion_eligible
    accessible=evaluate_sleep_checkpoint(policy,elapsed_seconds=1_000,wake_viability_milli=0,previous_band="continue_sleep",external_wake_accessible=True)
    assert accessible.reason_code == "external_wake_accessible" and accessible.completion_eligible
    hard_cap=evaluate_sleep_checkpoint(policy,elapsed_seconds=28_800,wake_viability_milli=0,previous_band="continue_sleep")
    assert hard_cap.reason_code == "hard_cap_protective" and hard_cap.hard_cap_reached and not hard_cap.completion_eligible


def test_owner_backed_authorization_does_not_accept_free_viability_or_external_wake(setup):
    _conn, world, service, _policy_value = setup
    with pytest.raises(TypeError):
        service.authorize_completion_owner_backed(
            world, "sophie", at_time=to_iso(T0), wake_viability_milli=80_000
        )


def test_owner_backed_authorization_holds_writer_lock_across_projection_and_insert(tmp_path, monkeypatch):
    path = tmp_path / "atomic-owner-backed.sqlite"
    conn = connect_database(str(path))
    writer = None
    try:
        ensure_schema(conn)
        clock = FakeClock()
        world = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
        service = SleepTerminationFoundationService(conn, clock=clock)
        policy = service.register_policy(
            "synthetic.atomic.v1", 1,
            {**_policy(), "wake_admissible_enter_milli": 65_000},
            "synthetic_test",
        )
        service.assign_policy(world, policy.policy_key, policy.version, "synthetic_test")
        row = conn.execute(
            "SELECT ch.id AS character_id,l.id AS location_id,p.id AS policy_id "
            "FROM character ch JOIN location l ON l.world_id=ch.world_id "
            "JOIN sleep_termination_policy p "
            "WHERE ch.world_id=? AND ch.key='sophie'",
            (world,),
        ).fetchone()
        now = to_iso(T0)
        hard_cap = to_iso(T0 + timedelta(hours=8))
        conn.execute(
            "INSERT INTO activity (public_id,world_id,character_id,type,location_id,started_at,planned_end_at,status,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (new_uuid(), world, row["character_id"], "sleep", row["location_id"], now, hard_cap, "active", now, now),
        )
        activity_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO activity_sleep_checkpoint (public_id,world_id,character_id,activity_id,policy_id,next_reassessment_at,previous_band,hard_cap_at,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (new_uuid(), world, row["character_id"], activity_id, row["policy_id"], now, "continue_sleep", hard_cap, now, now),
        )
        projection = OwnerBackedWakeViability(
            world_id=world, character_key="sophie", canonical_at=now,
            canonical_event_seq=0, model_key="ric.sleep.additive.v1", model_version=1,
            value_milli=80_000, provenance="test", input_fingerprint="a" * 64,
            regulation_fingerprint="b" * 64,
        )
        def projected_inside_transaction(self, world_id, character_key, *, at_time=None, expected_event_seq=None):
            assert self._conn.in_transaction
            writer.execute(
                "UPDATE sleep_termination_policy SET provenance='interposed' "
                "WHERE policy_key='synthetic.atomic.v1'"
            )
            return projection

        writer = connect_database(str(path))
        writer.execute("PRAGMA busy_timeout=0")
        monkeypatch.setattr(
            SleepPhysiologyService,
            "project_wake_viability_owner_backed",
            projected_inside_transaction,
        )
        with pytest.raises(SleepTerminationError) as raised:
            service.authorize_completion_owner_backed(world, "sophie", at_time=now)
        assert raised.value.code == "invalid_wake_provenance"
        assert conn.execute(
            "SELECT COUNT(*) FROM sleep_completion_authorization"
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT provenance FROM sleep_termination_policy WHERE policy_key='synthetic.atomic.v1'"
        ).fetchone()[0] == "synthetic_test"
    finally:
        if writer is not None:
            writer.close()
        conn.close()


def test_forward_migration_from_52_creates_no_policy_checkpoint_audit_or_canonical_history():
    conn=connect_database(":memory:")
    try:
        _apply_through(conn,52); world=IntegrationWorldService(conn,clock=FakeClock()).create_initial_world()
        before=conn.execute("SELECT COUNT(*),MAX(seq) FROM canonical_event WHERE world_id=?",(world["id"],)).fetchone()
        assert ensure_schema(conn) == 58
        for table in ("sleep_termination_policy","world_sleep_termination_policy_assignment","activity_sleep_checkpoint","sleep_termination_audit"):
            assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        after=conn.execute("SELECT COUNT(*),MAX(seq) FROM canonical_event WHERE world_id=?",(world["id"],)).fetchone()
        assert tuple(after) == tuple(before)
    finally: conn.close()
