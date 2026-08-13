"""Disposable corrections for active scheduler freshness and light catch-up."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]

# Every active tick must advance continuous owner state, even without a special boundary.
path = root / "src" / "vivarium" / "active_simulation.py"
text = path.read_text(encoding="utf-8")
old = '''    def is_due(self,world_id:int,target_time:str)->bool:\n        self._require_active(world_id);target=to_iso(parse_iso(target_time))\n        return any(self.next_boundary(world_id,key,until=target) is not None for key in self._characters(world_id))\n'''
new = '''    def is_due(self,world_id:int,target_time:str)->bool:\n        self._require_active(world_id);target=to_iso(parse_iso(target_time));characters=self._characters(world_id)\n        # Even without an activity/light/checkpoint boundary, H/phi/P are continuous\n        # owner state and must reach the captured runtime target before cognition reads them.\n        if any(parse_iso(self._physiology.read_state(world_id,key).anchor_at)<parse_iso(target) for key in characters):\n            return True\n        return any(self.next_boundary(world_id,key,until=target) is not None for key in characters)\n'''
if text.count(old) != 1:
    raise SystemExit(f"active is_due block expected once, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")

# A catch-up light boundary is historical by design. The generic owner-backed frame
# reader rejects any historical frame after *any* later world event; that is correct
# for cognition but too broad for this scheduler helper. Here we instead prove that
# this character has not crossed an unmaterialized movement/activity boundary.
path = root / "src" / "vivarium" / "sleep_physiology.py"
text = path.read_text(encoding="utf-8")
old = '''        source = self.resolve_light_source_owner_backed(\n            world, character, at_time=anchor\n        )\n        schedule = source.assignment_metadata["schedule_assignment"]["schedule"]\n        segments = schedule.get("segments") if isinstance(schedule, Mapping) else None\n'''
new = '''        self._assert_no_unmaterialized_character_boundary(\n            world, character, anchor, limit\n        )\n        regime, _load, _sustained, _activity_type = self._owner_backed_regime(\n            world, character\n        )\n        location_key_row = self._conn.execute(\n            "SELECT l.key FROM character c JOIN location l ON l.id=c.current_location_id "\n            "WHERE c.world_id=? AND c.key=?", (world, character)\n        ).fetchone()\n        if location_key_row is None:\n            raise SleepPhysiologyError(\n                "position canonique absente", code="canonical_position_missing"\n            )\n        _source, metadata = self._resolve_light_source_values(\n            world, location_key_row["key"], anchor, state=regime\n        )\n        schedule = metadata["schedule_assignment"]["schedule"]\n        segments = schedule.get("segments") if isinstance(schedule, Mapping) else None\n'''
if text.count(old) != 1:
    raise SystemExit(f"light boundary source block expected once, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
