"""Small deterministic architectural guard for the Vivarium package.

The first gate is intentionally narrow: a package module must not import a
private symbol from another package module. Private names remain available for
implementation details inside their owning module, but consumers need a
public contract before depending on them.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path


def private_import_violations(root: Path) -> list[str]:
    """Return stable diagnostics for private inter-module imports below root."""
    violations: list[str] = []
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            violations.append(f"{path}:{exc.lineno}: syntax error: {exc.msg}")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            for alias in node.names:
                if alias.name.startswith("_") and alias.name not in {
                    "__future__",
                    "__version__",
                }:
                    imported = alias.name
                    module = "." * node.level + (node.module or "")
                    violations.append(
                        f"{path}:{node.lineno}: private import {imported!r} from {module!r}"
                    )
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "src" / "vivarium",
        help="Python package tree to inspect (default: src/vivarium)",
    )
    args = parser.parse_args()
    violations = private_import_violations(args.root)
    if violations:
        print("Architectural guard failed:")
        print("\n".join(violations))
        return 1
    print(f"Architectural guard passed: {args.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
