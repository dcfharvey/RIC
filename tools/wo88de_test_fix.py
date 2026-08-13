"""Disposable correction for WO88D/E generated tests."""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "tests" / "test_active_runtime_cutover.py"
text = path.read_text(encoding="utf-8")
for old, new in (
    ("character_1", "sophie"),
    ("character_2", "erika"),
    ("character_3", "luna"),
    ("character_4", "chuu"),
):
    text = text.replace(old, new)

append = '''\n\ndef test_active_pause_freezes_owner_physiology_without_touching_legacy_rest_energy():\n conn,wid,clock=active_world()\n try:\n  before=legacy_snapshot(conn,wid);clock.current=T0_DT+timedelta(seconds=20)\n  WorldEngine(conn,clock=clock).pause_world(wid)\n  frozen=WorldEngine(conn,clock=clock).read_canonical_time(wid)\n  assert frozen==to_iso(clock.current);assert legacy_snapshot(conn,wid)==before\n  for key in ("chuu","erika","luna","sophie"):\n   assert SleepPhysiologyService(conn,clock=clock).read_state(wid,key).anchor_at==frozen\n finally:conn.close()\n'''
if "test_active_pause_freezes_owner_physiology_without_touching_legacy_rest_energy" not in text:
    text += append
path.write_text(text, encoding="utf-8", newline="\n")
