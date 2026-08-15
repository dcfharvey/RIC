from __future__ import annotations

from pathlib import Path

from tools.check_architecture import private_import_violations


def test_source_has_no_private_inter_module_imports() -> None:
    root = Path(__file__).parents[1] / "src" / "vivarium"
    assert private_import_violations(root) == []


def test_guard_reports_private_imports(tmp_path: Path) -> None:
    (tmp_path / "consumer.py").write_text(
        "from .owner import _private\n", encoding="utf-8"
    )
    violations = private_import_violations(tmp_path)
    assert "private import '_private'" in violations[0]
