"""Disposable patch generator for the post-cutover MVP preflight."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one match, found {text.count(old)}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


replace_once(
    "src/vivarium/mvp_preflight.py",
    "from .circadian_shadow import LEGACY_CONSUMERS\n",
    "from .active_simulation import ActiveSimulationEngine\n"
    "from .activities import ActivityEngine\n"
    "from .character import CharacterEngine\n"
    "from .decision import DecisionFrameService\n"
    "from .needs import NeedsEngine\n",
)
old = '''def _active_legacy_guard_check(conn: sqlite3.Connection, world_id: int, status: str) -> PreflightCheck:\n    \"\"\"Le gate active refuse tant que les consumers comportementaux legacy existent.\"\"\"\n    if status != \"active\":\n        return _check(\"legacy_runtime_guard\", True, \"legacy autorise hors active\")\n    forbidden = tuple(\n        entry.key for entry in LEGACY_CONSUMERS\n        if entry.role in {\"behavior\", \"physical_cost\", \"projection\"}\n    )\n    return _check(\n        \"legacy_runtime_guard\",\n        False,\n        \"consommateurs legacy actifs non commutes: \" + \",\".join(forbidden),\n    )\n'''
new = '''def _active_legacy_guard_check(conn: sqlite3.Connection, world_id: int, status: str) -> PreflightCheck:\n    \"\"\"Vérifie que le binaire déployé possède le chemin actif owner-backed.\n\n    Les modules legacy restent présents pour les mondes ``inactive/prepared`` et\n    la rétrocompatibilité. Leur présence sur disque n'est donc plus un échec :\n    ce qui compte au gate ``active`` est que les points de routage exclusifs du\n    cutover soient disponibles. Les tests WO88D/E falsifient séparément tout\n    appel à ``SimulationEngine`` depuis le chemin actif.\n    \"\"\"\n    if status != \"active\":\n        return _check(\"legacy_runtime_guard\", True, \"legacy autorise hors active\")\n    contracts = {\n        \"active_scheduler_run\": callable(getattr(ActiveSimulationEngine, \"run_to\", None)),\n        \"active_scheduler_due\": callable(getattr(ActiveSimulationEngine, \"is_due\", None)),\n        \"owner_materialization\": callable(getattr(SleepPhysiologyService, \"materialize_owner_backed\", None)),\n        \"owner_activity_p\": callable(getattr(SleepPhysiologyService, \"evaluate_activity_capacity_owner_backed\", None)),\n        \"owner_traversal_p\": callable(getattr(SleepPhysiologyService, \"apply_traversal_cost_owner_backed\", None)),\n        \"selected_legacy_needs\": callable(getattr(NeedsEngine, \"materialize_selected_needs\", None)),\n        \"activity_gate\": callable(getattr(ActivityEngine, \"_physiology_active\", None)),\n        \"movement_gate\": callable(getattr(CharacterEngine, \"_physiology_active\", None)),\n        \"decision_gate\": callable(getattr(DecisionFrameService, \"build_current\", None)),\n    }\n    missing = tuple(sorted(key for key, available in contracts.items() if not available))\n    return _check(\n        \"legacy_runtime_guard\",\n        not missing,\n        \"cutover actif disponible ; legacy isolé hors gate active\"\n        if not missing else \"contrats de cutover absents: \" + \",\".join(missing),\n    )\n'''
replace_once("src/vivarium/mvp_preflight.py", old, new)
replace_once(
    "tests/test_mvp_preflight.py",
    '''def test_active_physiology_fails_closed_on_missing_classes_and_legacy_consumers(conn):\n''',
    '''def test_active_physiology_fails_closed_on_missing_classes_but_accepts_cutover_contracts(conn):\n''',
)
replace_once(
    "tests/test_mvp_preflight.py",
    '''    assert "physical_load_classes" in failures\n    assert "legacy_runtime_guard" in failures\n    assert "owner_backed_contracts" not in failures\n''',
    '''    assert "physical_load_classes" in failures\n    assert "legacy_runtime_guard" not in failures\n    assert "owner_backed_contracts" not in failures\n    legacy_guard = next(check for check in report.checks if check.key == "legacy_runtime_guard")\n    assert legacy_guard.passed\n    assert "legacy isolé" in legacy_guard.detail\n''',
)
