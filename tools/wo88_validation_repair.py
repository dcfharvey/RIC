"""One-shot WO88 validation repair: make legacy tests self-contained under active physiology."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


# CLI smoke tests must not depend on the developer machine having a model env var.
for name in (
    "test_cli_llm_smoke_reports_a_healthy_ephemeral_run",
    "test_cli_llm_calibrate_reports_a_healthy_ephemeral_series",
    "test_cli_scene_smoke_reports_a_healthy_ephemeral_turn",
    "test_cli_scene_bench_reports_a_healthy_ephemeral_conversation",
):
    old = f"def {name}(monkeypatch, capsys):\n"
    new = old + "    monkeypatch.setenv(\"VIVARIUM_LLM_MODEL\", \"gemma-local\")\n"
    replace_once("tests/test_cli.py", old, new)

replace_once(
    "tests/test_synthetic_sleep_integration.py",
    '''class FakeClock:\n    def now(self):\n        return T0\n\n    def now_iso(self):\n        return to_iso(T0)\n''',
    '''class FakeClock:\n    def __init__(self):\n        self.current = T0\n\n    def now(self):\n        return self.current\n\n    def now_iso(self):\n        return to_iso(self.current)\n''',
)

replace_once(
    "tests/test_synthetic_sleep_integration.py",
    '''def _termination_policy():\n    return {\n        "schema_version": 1, "checkpoint_interval_seconds": 600, "hard_cap_seconds": 1800,\n        "wake_admissible_enter_milli": 65000, "wake_admissible_exit_milli": 55000,\n    }\n\n\ndef _activate_synthetic''',
    '''def _termination_policy():\n    return {\n        "schema_version": 1, "checkpoint_interval_seconds": 600, "hard_cap_seconds": 1800,\n        "wake_admissible_enter_milli": 65000, "wake_admissible_exit_milli": 55000,\n    }\n\n\ndef _physical_policy():\n    return {\n        "schema_version": 1,\n        "activity_cost_per_hour_milli": {\n            "none": 0, "light": 5000, "moderate": 15000, "vigorous": 30000,\n        },\n        "minimum_capacity_milli": {\n            "none": 0, "light": 10000, "moderate": 30000, "vigorous": 60000,\n        },\n        "traversal_cost_per_edge_milli": 5000,\n        "recovery_per_hour_milli": {"rest": 10000, "sleep": 20000},\n    }\n\n\ndef _classify_activities(conn, world_id):\n    with transaction(conn) as tx:\n        tx.execute(\n            "UPDATE activity_definition SET physical_load_class = CASE "\n            "WHEN activity_type IN ('sleep','rest','idle') THEN 'none' "\n            "WHEN activity_type='sport' THEN 'vigorous' ELSE 'light' END "\n            "WHERE world_id=?",\n            (world_id,),\n        )\n\n\ndef _activate_synthetic''',
)

replace_once(
    "tests/test_synthetic_sleep_integration.py",
    '''    for row in conn.execute("SELECT key FROM character WHERE world_id=?", (world_id,)):\n        foundation.assign_biology_profile(\n            world_id, row["key"], "synthetic.human.v1", 1, "synthetic_setup"\n        )\n    foundation.prepare_world(world_id, ADDITIVE_MODEL_KEY, 1, "synthetic_operator")\n''',
    '''    for row in conn.execute("SELECT key FROM character WHERE world_id=?", (world_id,)):\n        foundation.assign_biology_profile(\n            world_id, row["key"], "synthetic.human.v1", 1, "synthetic_setup"\n        )\n    physical = foundation.register_physical_capacity_policy(\n        "synthetic.capacity.v1", 1, _physical_policy(), "synthetic_calibration_only"\n    )\n    foundation.assign_physical_capacity_policy(\n        world_id, physical.policy_key, physical.version, "synthetic_setup"\n    )\n    _classify_activities(conn, world_id)\n    foundation.prepare_world(world_id, ADDITIVE_MODEL_KEY, 1, "synthetic_operator")\n''',
)

replace_once(
    "tests/test_synthetic_sleep_integration.py",
    '''    assert scheduled is not None and scheduled.at == first and scheduled.reasons == ("sleep_checkpoint",)\n\n    result = coordinator.process_sleep_checkpoint(''',
    '''    assert scheduled is not None and scheduled.at == first and scheduled.reasons == ("sleep_checkpoint",)\n\n    clock.current = T0 + timedelta(seconds=600)\n    result = coordinator.process_sleep_checkpoint(''',
)

replace_once(
    "tests/test_synthetic_sleep_integration.py",
    '''    engine = ActivityEngine(conn, clock=clock)\n    before_seq = max_seq(conn, world_id)\n\n    with pytest.raises(sqlite3.IntegrityError):''',
    '''    engine = ActivityEngine(conn, clock=clock)\n    before_seq = max_seq(conn, world_id)\n    clock.current = T0 + timedelta(seconds=600)\n\n    with pytest.raises(sqlite3.IntegrityError):''',
)

replace_once(
    "tests/test_synthetic_sleep_integration.py",
    '''    before = max_seq(conn, world_id)\n    first = coordinator.interrupt_critical_wake_stability(''',
    '''    before = max_seq(conn, world_id)\n    clock.current = T0 + timedelta(seconds=1)\n    first = coordinator.interrupt_critical_wake_stability(''',
)
