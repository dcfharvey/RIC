"""Disposable corrections applied after wo88_apply.py on the build branch."""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "tests" / "test_active_physical_capacity.py"
text = path.read_text(encoding="utf-8")
old = '''            tx.execute(\n                "INSERT INTO sleep_wake_hysteresis_state (public_id,world_id,character_id,previous_band,anchor_at,updated_at) VALUES (?,?,?,'fragile',?,?,?)",\n                (f"hys-{cid}", world_id, cid, ANCHOR, ANCHOR, ANCHOR),\n            )\n'''
new = '''            tx.execute(\n                "INSERT INTO sleep_wake_hysteresis_state (public_id,world_id,character_id,previous_band,anchor_at,updated_at) VALUES (?,?,?,'fragile',?,?)",\n                (f"hys-{cid}", world_id, cid, ANCHOR, ANCHOR),\n            )\n'''
if text.count(old) != 1:
    raise SystemExit("expected hysteresis fixture block exactly once")
text = text.replace(old, new, 1)
for old_stamp, new_stamp in (
    ('ANCHOR = "2026-08-11T12:00:00+00:00"', 'ANCHOR = "2026-08-11T12:00:00.000000Z"'),
    ('T30 = "2026-08-11T12:00:30+00:00"', 'T30 = "2026-08-11T12:00:30.000000Z"'),
    ('T60 = "2026-08-11T12:01:00+00:00"', 'T60 = "2026-08-11T12:01:00.000000Z"'),
):
    if text.count(old_stamp) != 1:
        raise SystemExit(f"expected timestamp once: {old_stamp}")
    text = text.replace(old_stamp, new_stamp, 1)
path.write_text(text, encoding="utf-8", newline="\n")
