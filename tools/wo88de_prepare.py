"""Disposable self-patch: only the public abort signature is duplicated textually."""
from pathlib import Path

path = Path(__file__).with_name("wo88de_apply.py")
text = path.read_text(encoding="utf-8")
old = '''    if count != 1:\n        raise SystemExit(f"{path}: expected one replacement, found {count}")\n    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\\n")\n'''
new = '''    if count != 1:\n        duplicate_abort = old == "        reason_code: str | None = None,\\n    ) -> dict[str, Any] | None:\\n" and count == 2\n        if not duplicate_abort:\n            raise SystemExit(f"{path}: expected one replacement, found {count}; pattern={old[:100]!r}")\n    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\\n")\n'''
if text.count(old) != 1:
    raise SystemExit("replace_once implementation changed")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
