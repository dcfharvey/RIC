"""Disposable correction for active scheduler tick freshness."""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "src" / "vivarium" / "active_simulation.py"
text = path.read_text(encoding="utf-8")
old = '''    def is_due(self,world_id:int,target_time:str)->bool:\n        self._require_active(world_id);target=to_iso(parse_iso(target_time))\n        return any(self.next_boundary(world_id,key,until=target) is not None for key in self._characters(world_id))\n'''
new = '''    def is_due(self,world_id:int,target_time:str)->bool:\n        self._require_active(world_id);target=to_iso(parse_iso(target_time));characters=self._characters(world_id)\n        # Even without an activity/light/checkpoint boundary, H/phi/P are continuous\n        # owner state and must reach the captured runtime target before cognition reads them.\n        if any(parse_iso(self._physiology.read_state(world_id,key).anchor_at)<parse_iso(target) for key in characters):\n            return True\n        return any(self.next_boundary(world_id,key,until=target) is not None for key in characters)\n'''
if text.count(old) != 1:
    raise SystemExit(f"active is_due block expected once, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
