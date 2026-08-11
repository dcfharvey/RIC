from datetime import datetime, timedelta, timezone

import pytest

from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, scc1c_admission_audit, scc1c_admission_digest
from vivarium.scenes import SocialSceneService
from vivarium.scc1c import FixedAdmissionPolicy, SCC1CAdmissionService, SCC1CError
from vivarium.social_interpretation import SocialInterpretationService
from vivarium.subjective_memory import SubjectiveMemoryService
from vivarium.util import to_iso


class FakeClock:
    def __init__(self):
        self.current = datetime(2026, 8, 10, 12, tzinfo=timezone.utc)

    def now(self):
        return self.current

    def now_iso(self):
        return to_iso(self.current)

    def advance(self, seconds=1):
        self.current += timedelta(seconds=seconds)


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    assert ensure_schema(conn) == 46
    clock = FakeClock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    yield conn, world_id, clock
    conn.close()


def _scene(setup, *, count=1):
    conn, world_id, clock = setup
    scenes = SocialSceneService(conn, clock=clock)
    scenes.open(world_id, "scc1c_scene", ("sophie", "erika", "luna"))
    memory = SubjectiveMemoryService(conn, clock=clock)
    traces = {}
    for index in range(1, count + 1):
        key = f"speech_{index}"
        scenes.speak(world_id, "scc1c_scene", key, "sophie", act_kind="inform", content=f"parole {index}", recipient_key="erika")
        for observer in ("erika", "luna"):
            traces[(observer, index)] = memory.encode_social_speech(
                world_id, observer, f"{observer}_trace_{index}", "scc1c_scene", key
            )
    return conn, world_id, clock, traces


def test_c1_c2_roles_are_admissible_without_role_guarantee(setup):
    conn, world_id, clock, traces = _scene(setup)
    service = SCC1CAdmissionService(conn, clock=clock, policy=FixedAdmissionPolicy("selected"))
    erika = service.admit(world_id, "erika", "erika_trace_1")
    luna = service.admit(world_id, "luna", "luna_trace_1")
    assert erika.interaction_role == "addressee"
    assert luna.interaction_role == "side_participant"
    assert {erika.decision, luna.decision} == {"selected"}


def test_c3_c4_no_trace_means_no_admission_and_no_catchup(setup):
    conn, world_id, clock, traces = _scene(setup)
    service = SCC1CAdmissionService(conn, clock=clock, policy=FixedAdmissionPolicy("selected"))
    assert service.list(world_id, "erika") == ()
    with pytest.raises(SCC1CError) as raised:
        service.admit(world_id, "sophie", "sophie_trace_1")
    assert raised.value.code == "source_not_accessible"
    assert service.list(world_id, "erika") == ()


def test_c5_not_selected_is_not_unresolved_and_can_be_permanent(setup):
    conn, world_id, clock, traces = _scene(setup)
    service = SCC1CAdmissionService(conn, clock=clock, policy=FixedAdmissionPolicy("not_selected"))
    admission = service.admit(world_id, "erika", "erika_trace_1")
    assert admission.decision == "not_selected"
    assert conn.execute("SELECT COUNT(*) FROM social_interpretation").fetchone()[0] == 0
    with pytest.raises(SCC1CError) as raised:
        service.record_attempt(admission, "attempt_1", "deferred")
    assert raised.value.code == "admission_not_selected"


def test_c6_burst_is_bounded_and_idempotent(setup):
    conn, world_id, clock, traces = _scene(setup, count=8)
    service = SCC1CAdmissionService(conn, clock=clock, policy=FixedAdmissionPolicy("selected"))
    admissions = [service.admit(world_id, "erika", f"erika_trace_{i}") for i in range(1, 9)]
    assert len(admissions) == 8
    assert len(service.list(world_id, "erika")) == 8
    assert service.admit(world_id, "erika", "erika_trace_1") == admissions[0]
    assert conn.execute("SELECT COUNT(*) FROM scc1c_admission").fetchone()[0] == 8


def test_c7_c8_no_revision_heuristic_or_invented_link(setup):
    conn, world_id, clock, traces = _scene(setup)
    service = SCC1CAdmissionService(conn, clock=clock, policy=FixedAdmissionPolicy("selected"))
    admission = service.admit(world_id, "erika", "erika_trace_1")
    assert not hasattr(admission, "revision_of")
    assert conn.execute("PRAGMA table_info(scc1c_admission)").fetchall()[-1][1] == "decided_at"


def test_c9_deferred_provider_failure_retry_and_attempt_idempotence(setup):
    conn, world_id, clock, traces = _scene(setup)
    service = SCC1CAdmissionService(conn, clock=clock, policy=FixedAdmissionPolicy("selected"))
    admission = service.admit(world_id, "erika", "erika_trace_1")
    deferred = service.record_attempt(admission, "attempt_1", "deferred", "budget_exhausted")
    failed = service.record_attempt(admission, "attempt_2", "provider_unavailable", "lm_studio_down")
    assert deferred.outcome == "deferred" and failed.outcome == "provider_unavailable"
    assert service.record_attempt(admission, "attempt_2", "provider_unavailable", "lm_studio_down") == failed
    assert conn.execute("SELECT COUNT(*) FROM scc1c_attempt").fetchone()[0] == 2
    with pytest.raises(SCC1CError):
        service.record_attempt(admission, "attempt_2", "deferred")


def test_c10_private_owner_isolation(setup):
    conn, world_id, clock, traces = _scene(setup)
    service = SCC1CAdmissionService(conn, clock=clock, policy=FixedAdmissionPolicy("selected"))
    with pytest.raises(SCC1CError) as raised:
        service.admit(world_id, "luna", "erika_trace_1")
    assert raised.value.code == "source_not_accessible"


def test_c11_restart_does_not_scan_or_catch_up(tmp_path):
    path = tmp_path / "scc1c.sqlite"
    conn = connect_database(path)
    ensure_schema(conn)
    clock = FakeClock()
    world_id = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    _scene((conn, world_id, clock))
    first = SCC1CAdmissionService(conn, clock=clock, policy=FixedAdmissionPolicy("selected"))
    first.admit(world_id, "erika", "erika_trace_1")
    conn.close()
    reopened = connect_database(path)
    ensure_schema(reopened)
    assert SCC1CAdmissionService(reopened, clock=clock).list(world_id, "luna") == ()
    assert reopened.execute("SELECT COUNT(*) FROM scc1c_admission").fetchone()[0] == 1
    reopened.close()


def test_c12_selection_and_attempts_have_no_causal_effect(setup):
    conn, world_id, clock, traces = _scene(setup)
    service = SCC1CAdmissionService(conn, clock=clock, policy=FixedAdmissionPolicy("selected"))
    before = canonical_state_digest(conn, world_id)
    admission = service.admit(world_id, "erika", "erika_trace_1")
    service.record_attempt(admission, "attempt_1", "provider_unavailable")
    after = canonical_state_digest(conn, world_id)
    assert before == after
    for table in ("subjective_belief", "mood_state", "emotion_episode", "relationship_view", "situational_permission", "personal_boundary", "subjective_goal", "subjective_intention"):
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_selected_admission_can_feed_existing_scc1b_owner_and_only_then_complete(setup):
    conn, world_id, clock, traces = _scene(setup)
    admission_service = SCC1CAdmissionService(conn, clock=clock, policy=FixedAdmissionPolicy("selected"))
    admission = admission_service.admit(world_id, "erika", "erika_trace_1")
    with pytest.raises(SCC1CError) as raised:
        admission_service.record_attempt(admission, "attempt_1", "interpreted")
    assert raised.value.code == "interpretation_not_found"
    SocialInterpretationService(conn, clock=clock).create(
        world_id, "erika", "reading_1", "erika_trace_1", understanding_status="unresolved"
    )
    completed = admission_service.record_attempt(admission, "attempt_1", "interpreted")
    assert completed.outcome == "interpreted"
    assert conn.execute("SELECT COUNT(*) FROM social_interpretation").fetchone()[0] == 1


def test_audit_digest_and_partial_write_are_clean(setup):
    conn, world_id, clock, traces = _scene(setup)
    service = SCC1CAdmissionService(conn, clock=clock, policy=FixedAdmissionPolicy("selected"))
    admission = service.admit(world_id, "erika", "erika_trace_1")
    service.record_attempt(admission, "attempt_1", "provider_unavailable")
    assert scc1c_admission_audit(conn, world_id) == []
    digest = scc1c_admission_digest(conn, world_id)
    assert digest["erika"][0]["attempts"][0]["outcome"] == "provider_unavailable"
