"""Disposable correction for pre-activation T0 source resolution."""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "src" / "vivarium" / "rodage_v2.py"
text = path.read_text(encoding="utf-8")
old = '''            source = reader.resolve_light_source_owner_backed(\n                world_id, character, at_time=self.t0\n            ).source\n            parameters = reader.parameters_for_character(world_id, character)\n'''
new = '''            location = self._conn.execute(\n                "SELECT l.key FROM character c JOIN location l ON l.id=c.current_location_id "\n                "WHERE c.world_id=? AND c.key=?", (world_id, character)\n            ).fetchone()["key"]\n            source = reader.resolve_light_source_synthetic(\n                world_id, location, self.t0, state="wake"\n            )\n            parameters = reader.parameters_for_character(world_id, character)\n'''
if text.count(old) != 1:
    raise SystemExit("pre-activation source block changed")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
