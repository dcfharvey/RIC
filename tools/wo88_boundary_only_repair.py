"""One-shot WO88D repair: wall time must not materialize active physiology."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


replace_once(
    "src/vivarium/active_simulation.py",
    '''    def is_due(self,world_id:int,target_time:str)->bool:\n        self._require_active(world_id);target=to_iso(parse_iso(target_time));characters=self._characters(world_id)\n        # Even without an activity/light/checkpoint boundary, H/phi/P are continuous\n        # owner state and must reach the captured runtime target before cognition reads them.\n        if any(parse_iso(self._physiology.read_state(world_id,key).anchor_at)<parse_iso(target) for key in characters):\n            return True\n        return any(self.next_boundary(world_id,key,until=target) is not None for key in characters)\n''',
    '''    def is_due(self,world_id:int,target_time:str)->bool:\n        self._require_active(world_id);target=to_iso(parse_iso(target_time));characters=self._characters(world_id)\n        # Wall time is not a causal boundary. Owner-backed H/phi/P stay persisted\n        # at their last processed cause boundary until one is actually due.\n        return any(self.next_boundary(world_id,key,until=target) is not None for key in characters)\n''',
)

replace_once(
    "src/vivarium/active_simulation.py",
    '''        # Final materialization at the captured real-time target. No historical\n        # decision is invented while catching up.\n        for key in chars:\n            active=self._activities.activity_sheet(world_id,key)\n            if active is None:self._passive_to(world_id,key,captured)\n            else:self._activities.advance_to(world_id,key,captured,_reanchor_clock=False)\n        with transaction(self._conn) as c:WorldEngine(self._conn,clock=self._clock)._advance_clock(world_id,captured,c)\n''',
    '''        # The world clock may reanchor to the captured real-time target, but the\n        # physiology is never materialized merely because wall time passed.\n        # Persisted H/phi/P therefore remain at the last processed causal boundary.\n        with transaction(self._conn) as c:WorldEngine(self._conn,clock=self._clock)._advance_clock(world_id,captured,c)\n''',
)

replace_once(
    "tests/test_active_runtime_cutover.py",
    '''  assert report.reached_target and report.last_time==target;assert WorldEngine(conn,clock=clock).read_canonical_time(wid)==target\n  assert all(SleepPhysiologyService(conn,clock=clock).read_state(wid,k).anchor_at==target for k in ("sophie","erika","luna","chuu"));assert legacy_snapshot(conn,wid)==before\n''',
    '''  assert report.reached_target and report.last_time==target;assert WorldEngine(conn,clock=clock).read_canonical_time(wid)==target\n  last_boundary=to_iso(T0_DT+timedelta(seconds=60))\n  assert all(SleepPhysiologyService(conn,clock=clock).read_state(wid,k).anchor_at==last_boundary for k in ("sophie","erika","luna","chuu"));assert legacy_snapshot(conn,wid)==before\n''',
)

replace_once(
    "tests/test_active_runtime_cutover.py",
    '''  assert frozen==to_iso(clock.current);assert legacy_snapshot(conn,wid)==before\n  for key in ("chuu","erika","luna","sophie"):\n   assert SleepPhysiologyService(conn,clock=clock).read_state(wid,key).anchor_at==frozen\n''',
    '''  assert frozen==to_iso(clock.current);assert legacy_snapshot(conn,wid)==before\n  for key in ("chuu","erika","luna","sophie"):\n   assert SleepPhysiologyService(conn,clock=clock).read_state(wid,key).anchor_at==T0\n''',
)

with (ROOT / "tests/test_active_runtime_cutover.py").open("a", encoding="utf-8", newline="\n") as handle:
    handle.write('''\n\ndef test_wall_pulse_before_first_causal_boundary_writes_no_physiology_or_canon():\n conn,wid,clock=active_world()\n try:\n  engine=ActiveSimulationEngine(conn,clock=clock)\n  target=to_iso(T0_DT+timedelta(seconds=20))\n  before_states={key:SleepPhysiologyService(conn,clock=clock).read_state(wid,key) for key in ("chuu","erika","luna","sophie")}\n  before_events=conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id=?",(wid,)).fetchone()[0]\n  assert engine.is_due(wid,target) is False\n  report=engine.run_to(wid,target)\n  assert report.transitions==0 and report.last_time==target\n  assert conn.execute("SELECT COUNT(*) FROM canonical_event WHERE world_id=?",(wid,)).fetchone()[0]==before_events\n  for key,before in before_states.items():\n   assert SleepPhysiologyService(conn,clock=clock).read_state(wid,key)==before\n finally:conn.close()\n''')
