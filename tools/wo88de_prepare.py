"""Disposable self-patch for the WO88D/E generator."""
from pathlib import Path

path = Path(__file__).with_name("wo88de_apply.py")
text = path.read_text(encoding="utf-8")
old = '''    if count != 1:\n        raise SystemExit(f"{path}: expected one replacement, found {count}")\n    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\\n")\n'''
new = '''    if count != 1:\n        duplicate_abort = old == "        reason_code: str | None = None,\\n    ) -> dict[str, Any] | None:\\n" and count == 2\n        if not duplicate_abort:\n            raise SystemExit(f"{path}: expected one replacement, found {count}; pattern={old[:100]!r}")\n    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\\n")\n'''
if text.count(old) != 1:
    raise SystemExit("replace_once implementation changed")
text = text.replace(old, new, 1)
# world.py's pause implementation predates the indentation/text assumed by the
# first generator. Remove only that disposable generator section; a second
# deterministic script patches the real block with a larger, unambiguous span.
start_marker = "# World pause: active worlds materialize the correct owners, never repos/energie.\n"
end_marker = 'write(\n    "tests/test_active_runtime_cutover.py",\n'
start = text.find(start_marker)
end = text.find(end_marker)
if start < 0 or end < 0 or end <= start:
    raise SystemExit("world-pause generator section not found")
section_start = text.rfind("# ---------------------------------------------------------------------------\n", 0, start)
if section_start < 0:
    raise SystemExit("world-pause section header not found")
text = text[:section_start] + end_marker + text[end + len(end_marker):]
path.write_text(text, encoding="utf-8", newline="\n")
