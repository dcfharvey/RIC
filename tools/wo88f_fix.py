"""Disposable correction: activation coverage follows the actual world population."""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "tests" / "test_physiology_activation.py"
text = path.read_text(encoding="utf-8")
old = '''  result=f.activate_world_from_initial_manifest(wid,"rodage.t0.v1",1,"rodage_operator")\n  assert result["status"]=="active" and result["anchor_at"]==T0 and result["character_count"]==4\n'''
new = '''  expected_keys=tuple(r["key"] for r in conn.execute("SELECT key FROM character WHERE world_id=? ORDER BY key",(wid,)))\n  result=f.activate_world_from_initial_manifest(wid,"rodage.t0.v1",1,"rodage_operator")\n  assert result["status"]=="active" and result["anchor_at"]==T0 and result["character_count"]==len(expected_keys)\n'''
if text.count(old) != 1:
    raise SystemExit("activation population assertion changed")
text = text.replace(old, new, 1)
old2 = '''  for table in ("sleep_regulation_state","physical_capacity_state","sleep_wake_hysteresis_state","sleep_regulation_precision_state"):\n   assert conn.execute(f"SELECT COUNT(*) FROM {table} WHERE world_id=?",(wid,)).fetchone()[0]==4\n  for key in ("chuu","erika","luna","sophie"):\n'''
new2 = '''  for table in ("sleep_regulation_state","physical_capacity_state","sleep_wake_hysteresis_state","sleep_regulation_precision_state"):\n   assert conn.execute(f"SELECT COUNT(*) FROM {table} WHERE world_id=?",(wid,)).fetchone()[0]==len(expected_keys)\n  for key in expected_keys:\n'''
if text.count(old2) != 1:
    raise SystemExit("activation dense-state assertion changed")
path.write_text(text.replace(old2, new2, 1), encoding="utf-8", newline="\n")
