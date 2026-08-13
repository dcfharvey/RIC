"""Disposable fixture corrections after wo88bc_apply.py."""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "tests" / "test_active_activity_traversal.py"
text = path.read_text(encoding="utf-8")
text = text.replace(
    'T30 = to_iso(datetime(2026, 8, 12, 21, 0, 30, tzinfo=timezone.utc))',
    'T30_DT = datetime(2026, 8, 12, 21, 0, 30, tzinfo=timezone.utc)\nT30 = to_iso(T30_DT)',
)
text = text.replace(
    '''        ActivityEngine(conn, clock=clock).advance_to(world_id, "erika", T30)\n''',
    '''        clock.current = T30_DT\n        ActivityEngine(conn, clock=clock).advance_to(world_id, "erika", T30)\n''',
)
text = text.replace(
    '''class FakeClock(Clock):\n    def now(self):\n        return T0_DT\n''',
    '''class FakeClock(Clock):\n    def __init__(self):\n        self.current = T0_DT\n\n    def now(self):\n        return self.current\n''',
)
text = text.replace(
    '''        activity = ActivityEngine(conn, clock=clock).start_activity(\n            world_id, "luna", "sleep", "chambre_luna", sim_now=T0\n        )\n''',
    '''        activities = ActivityEngine(conn, clock=clock)\n        sleep_location = sorted(activities.allowed_locations(world_id, "sleep"))[0]\n        activity = activities.start_activity(\n            world_id, "luna", "sleep", sleep_location, sim_now=T0\n        )\n''',
)
path.write_text(text, encoding="utf-8", newline="\n")
