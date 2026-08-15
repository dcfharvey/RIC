"""WO88D/E : scheduler actif, catch-up et falsification legacy."""
from dataclasses import asdict
from datetime import datetime,timezone,timedelta

import pytest

from vivarium.activities import ActivityEngine
from vivarium.action_arbitration import ActionArbitrationFoundationService
from vivarium.active_simulation import ActiveSimulationEngine
from vivarium.character_capabilities import sapient_character_keys
from vivarium.circadian_model import calibration_profiles
from vivarium.db import connect_database,transaction
from vivarium.decision import DecisionFrameService
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.simulation import SimulationEngine
from vivarium.sleep_physiology import ADDITIVE_MODEL_KEY,SleepPhysiologyFoundationService,SleepPhysiologyService,V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY
from vivarium.sleep_termination import SleepTerminationFoundationService
from vivarium.util import Clock,to_iso
from vivarium.world import SOURCE_ENGINE, WorldEngine, append_event

T0_DT=datetime(2026,8,12,21,0,tzinfo=timezone.utc);T0=to_iso(T0_DT)
class FakeClock(Clock):
 def __init__(self):self.current=T0_DT
 def now(self):return self.current

def profile():
 p=asdict(calibration_profiles()["human_reference_candidate.v1"]);[p.pop(k) for k in ("profile_key","version","evidence_class")];return {"model_key":ADDITIVE_MODEL_KEY,"parameters":p}

def active_world():
 clock=FakeClock();conn=connect_database(":memory:");ensure_schema(conn);wid=IntegrationWorldService(conn,clock=clock).create_initial_world()["id"];f=SleepPhysiologyFoundationService(conn,clock=clock)
 f.register_light_schedule("runtime.day.v1",1,{"schema_version":1,"segments":[{"start_second":0,"end_second":75660,"environmental_light_milli":50000},{"start_second":75660,"end_second":86400,"environmental_light_milli":0}]});f.register_location_light_profile("runtime.indoor.v1",1,25000,{"kind":"indoor"});f.register_biology_profile("runtime.human.v1",1,"human_reference",profile())
 f.register_physical_capacity_policy("runtime.p.v1",1,{"schema_version":1,"activity_cost_per_hour_milli":{"none":3600,"light":7200,"moderate":10800,"vigorous":18000},"minimum_capacity_milli":{"none":0,"light":10000,"moderate":25000,"vigorous":45000},"traversal_cost_per_edge_milli":250,"recovery_per_hour_milli":{"rest":7200,"sleep":10800}},"test")
 f.assign_light_schedule(wid,"runtime.day.v1",1,T0,"test")
 for r in conn.execute("SELECT key FROM location WHERE world_id=?",(wid,)):f.assign_location_light_profile(wid,r["key"],"runtime.indoor.v1",1,T0,"test")
 for r in conn.execute("SELECT key FROM character WHERE world_id=?",(wid,)):f.assign_biology_profile(wid,r["key"],"runtime.human.v1",1,"test")
 f.assign_physical_capacity_policy(wid,"runtime.p.v1",1,"test")
 for typ,load in V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY.items():conn.execute("UPDATE activity_definition SET physical_load_class=? WHERE world_id=? AND activity_type=?",(load,wid,typ))
 term=SleepTerminationFoundationService(conn,clock=clock);term.register_policy("runtime.sleep.v1",1,{"schema_version":1,"checkpoint_interval_seconds":30,"hard_cap_seconds":300,"wake_admissible_enter_milli":65000,"wake_admissible_exit_milli":55000},"test");term.assign_policy(wid,"runtime.sleep.v1",1,"test")
 arb=ActionArbitrationFoundationService(conn,clock=clock);ap=arb.register_policy("runtime.arb.v1",1,{"schema_version":1,"source_mappings":{"sleep_regulation":{"transform":"linear_clamped_milli.v1","correlation_group":"sleep","input_low_milli":60000,"input_high_milli":100000,"direction":"ascending"},"physical_recovery":{"transform":"linear_clamped_milli.v1","correlation_group":"recovery","input_low_milli":20000,"input_high_milli":80000,"direction":"descending"},"subjective_intention":{"transform":"linear_clamped_milli.v1","correlation_group":"subjective","input_low_milli":0,"input_high_milli":100000,"direction":"ascending"}},"correlation_groups":{"kind":"declared_by_source_mapping.v1"},"aggregation":{"kind":"max_per_group_then_saturating_sum.v1"},"current_action_inertia":{"max_bonus_milli":0},"quasi_equality":{"band_milli":100000},"reassessment":{"interval_seconds":60}},"test");arb.assign_policy(wid,ap.policy_key,ap.version,"test");f.prepare_world(wid,ADDITIVE_MODEL_KEY,1,"test")
 with transaction(conn) as tx:
  tx.execute("UPDATE world_physiology_system SET status='active',activated_at=?,activated_by=?,updated_at=? WHERE world_id=?",(T0,"test",T0,wid))
  for r in tx.execute("SELECT id FROM character WHERE world_id=?",(wid,)):
   cid=r["id"];tx.execute("INSERT INTO sleep_regulation_state (public_id,world_id,character_id,model_key,model_version,homeostatic_load_milli,circadian_phase_milli,anchor_at,updated_at) VALUES (?,?,?,?,1,50000,250000,?,?)",(f"r{cid}",wid,cid,ADDITIVE_MODEL_KEY,T0,T0));tx.execute("INSERT INTO physical_capacity_state (public_id,world_id,character_id,capacity_milli,rate_remainder,anchor_at,updated_at) VALUES (?,?,?,70000,0,?,?)",(f"p{cid}",wid,cid,T0,T0));tx.execute("INSERT INTO sleep_wake_hysteresis_state (public_id,world_id,character_id,previous_band,anchor_at,updated_at) VALUES (?,?,?,'fragile',?,?)",(f"h{cid}",wid,cid,T0,T0));tx.execute("INSERT INTO sleep_regulation_precision_state (public_id,world_id,character_id,homeostatic_load_residue,circadian_phase_residue,anchor_at,updated_at) VALUES (?,?,?,0,0,?,?)",(f"x{cid}",wid,cid,T0,T0))
 return conn,wid,clock

def legacy_snapshot(conn,wid):return tuple(tuple(r) for r in conn.execute("SELECT character_id,need_key,value_milli,rate_remainder,anchor_at FROM need_state WHERE world_id=? AND need_key IN ('repos','energie') ORDER BY character_id,need_key",(wid,)))

def test_active_decision_frame_never_calls_legacy_policy_context(monkeypatch):
 conn,wid,clock=active_world()
 try:
  monkeypatch.setattr(SimulationEngine,"policy_context",lambda *a,**k:(_ for _ in ()).throw(AssertionError("legacy")))
  frame=DecisionFrameService(conn).build_current(wid,"sophie");assert frame.character_key=="sophie";assert all(m.target_need in {"sleep_regulation","physical_capacity"} for m in frame.motives)
 finally:conn.close()

def test_catchup_crosses_activity_end_and_light_boundary_without_losing_real_time():
 conn,wid,clock=active_world()
 try:
  act=ActivityEngine(conn,clock=clock);act.start_activity(wid,"sophie","gaming","salon",sim_now=T0)
  # make the activity end before the light boundary and the wall target after both
  conn.execute("UPDATE activity SET planned_end_at=? WHERE world_id=? AND character_id=(SELECT id FROM character WHERE world_id=? AND key='sophie') AND status='active'",(to_iso(T0_DT+timedelta(seconds=30)),wid,wid))
  clock.current=T0_DT+timedelta(seconds=90);target=to_iso(clock.current);before=legacy_snapshot(conn,wid)
  report=ActiveSimulationEngine(conn,clock=clock).run_to(wid,target)
  assert report.reached_target and report.last_time==target;assert WorldEngine(conn,clock=clock).read_canonical_time(wid)==target
  last_boundary=to_iso(T0_DT+timedelta(seconds=60))
  assert all(SleepPhysiologyService(conn,clock=clock).read_state(wid,k).anchor_at==last_boundary for k in ("sophie","erika","luna","chuu"));assert legacy_snapshot(conn,wid)==before
 finally:conn.close()

def test_active_runtime_falsifies_legacy_simulation_use(monkeypatch):
 conn,wid,clock=active_world()
 try:
  monkeypatch.setattr(SimulationEngine,"run_to",lambda *a,**k:(_ for _ in ()).throw(AssertionError("legacy run")));clock.current=T0_DT+timedelta(seconds=10);before=legacy_snapshot(conn,wid);ActiveSimulationEngine(conn,clock=clock).run_to(wid,to_iso(clock.current));assert legacy_snapshot(conn,wid)==before
 finally:conn.close()


def test_active_pause_freezes_owner_physiology_without_touching_legacy_rest_energy():
 conn,wid,clock=active_world()
 try:
  before=legacy_snapshot(conn,wid);clock.current=T0_DT+timedelta(seconds=20)
  WorldEngine(conn,clock=clock).pause_world(wid)
  frozen=WorldEngine(conn,clock=clock).read_canonical_time(wid)
  assert frozen==to_iso(clock.current);assert legacy_snapshot(conn,wid)==before
  for key in ("chuu","erika","luna","sophie"):
   assert SleepPhysiologyService(conn,clock=clock).read_state(wid,key).anchor_at==frozen
 finally:conn.close()


def test_wall_pulse_before_first_causal_boundary_writes_no_physiology_or_canon():
 conn,wid,clock=active_world()
 try:
  engine=ActiveSimulationEngine(conn,clock=clock)
  target=to_iso(T0_DT+timedelta(seconds=20))
  before_states={key:SleepPhysiologyService(conn,clock=clock).read_state(wid,key) for key in ("chuu","erika","luna","sophie")}
  before_events=conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id=?",(wid,)).fetchone()[0]
  assert engine.is_due(wid,target) is False
  report=engine.run_to(wid,target)
  assert report.transitions==0 and report.last_time==target
  assert conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id=?",(wid,)).fetchone()[0] == before_events
  for key,before in before_states.items():
   assert SleepPhysiologyService(conn,clock=clock).read_state(wid,key)==before
 finally:conn.close()


def test_active_scheduler_aligns_subsecond_wall_horizon_to_causal_grid():
 conn,wid,clock=active_world()
 try:
  clock.current=T0_DT+timedelta(seconds=20, milliseconds=250)
  target=to_iso(clock.current)
  engine=ActiveSimulationEngine(conn,clock=clock)
  assert engine.is_due(wid,target) is False
  report=engine.run_to(wid,target)
  assert report.transitions==0 and report.last_time==target
 finally:conn.close()


def test_active_scheduler_allows_unrelated_newer_canonical_event_for_anchor():
 conn,wid,clock=active_world()
 try:
  ActivityEngine(conn,clock=clock).start_activity(
   wid,"chuu","gaming","salon",sim_now=T0
  )
  unrelated_at=to_iso(T0_DT+timedelta(seconds=30))
  with transaction(conn) as tx:
   append_event(
    tx,wid,SOURCE_ENGINE,"cognition_no_action",
    {"character":"luna","decision":"no_action"},
    occurred_at=unrelated_at,recorded_at=unrelated_at,
   )

  boundary=ActiveSimulationEngine(conn,clock=clock).next_boundary(
   wid,"chuu",until=to_iso(T0_DT+timedelta(seconds=61))
  )

  assert boundary is not None
  assert boundary.at==to_iso(T0_DT+timedelta(seconds=60))
  assert "arbitration_reassessment" in boundary.reasons
 finally:conn.close()


def test_arbitration_reassessment_is_a_causal_private_boundary():
 conn,wid,clock=active_world()
 try:
  before_events=conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id=?",(wid,)).fetchone()[0]
  boundary=ActiveSimulationEngine(conn,clock=clock).next_boundary(
   wid,"sophie",until=to_iso(T0_DT+timedelta(seconds=61))
  )
  assert boundary is not None and boundary.at==to_iso(T0_DT+timedelta(seconds=60))
  assert "arbitration_reassessment" in boundary.reasons
  clock.current=T0_DT+timedelta(seconds=61)
  ActiveSimulationEngine(conn,clock=clock).run_to(wid,to_iso(clock.current))
  audit_actors=tuple(sorted(
   r["actor"] for r in conn.execute(
    "SELECT json_extract(result_json,'$.actor_key') AS actor FROM action_arbitration_audit "
    "WHERE world_id=? AND reason_code='active_causal_arbitration'",(wid,)
   )
  ))
  expected=tuple(r["key"] for r in conn.execute("SELECT key FROM character WHERE world_id=? ORDER BY key",(wid,)))
  assert audit_actors==expected
  idle_events = conn.execute(
   "SELECT json_extract(payload,'$.character') AS character "
   "FROM canonical_event WHERE world_id=? AND event_type='activity_started' "
   "AND json_extract(payload,'$.activity')='idle' "
   "AND json_extract(payload,'$.action_provenance.origin')='wo95_post_boundary_idle' "
   "ORDER BY character", (wid,),
  ).fetchall()
  assert tuple(row[0] for row in idle_events) == sapient_character_keys(conn, wid)
  assert conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id=?",(wid,)).fetchone()[0] >= before_events
 finally:conn.close()


def test_active_scheduler_imports_no_synthetic_arbitration_module():
 import inspect
 import vivarium.active_simulation as module
 assert "synthetic_action_arbitration" not in inspect.getsource(module)


def test_active_runtime_exposes_no_public_synthetic_physiology_apis():
    assert not hasattr(SleepPhysiologyService, "project_synthetic")
    assert not hasattr(SleepPhysiologyService, "next_critical_boundary_synthetic")
    assert not hasattr(SleepPhysiologyService, "materialize_synthetic")
    assert not hasattr(SleepPhysiologyService, "resolve_light_source_synthetic")
