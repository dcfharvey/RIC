from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: refusing ambiguous transform, count={count}")
    return text.replace(old, new, 1)


path = Path("bridge_control/ric_bridge_control.py")
text = path.read_text(encoding="utf-8")
text = replace_once(
    text,
    "        self._audit_lock = threading.Lock()\n",
    "        self._audit_lock = threading.Lock()\n        self._write_lock = threading.RLock()\n",
    "writer lock",
)
old_atomic = '''    def _atomic_replace(self, target: Path, raw: bytes) -> None:\n        temporary = target.with_name(f".{target.name}.ric-write-{uuid.uuid4().hex}.tmp")\n        try:\n            with temporary.open("xb") as handle:\n                handle.write(raw)\n                handle.flush()\n                os.fsync(handle.fileno())\n            if _is_link_like(target):\n                raise ControlError("target became a reparse point", code="reparse_point_denied", status=403)\n            os.replace(temporary, target)\n        except ControlError:\n            try:\n                temporary.unlink(missing_ok=True)\n            finally:\n                raise\n        except OSError as exc:\n            try:\n                temporary.unlink(missing_ok=True)\n            finally:\n                raise ControlError("atomic write failed", code="filesystem_error", status=500) from exc\n'''
new_atomic = '''    def _atomic_replace(self, target: Path, raw: bytes, expected: str) -> None:\n        temporary = target.with_name(f".{target.name}.ric-write-{uuid.uuid4().hex}.tmp")\n        try:\n            with temporary.open("xb") as handle:\n                handle.write(raw)\n                handle.flush()\n                os.fsync(handle.fileno())\n            with self._write_lock:\n                if _is_link_like(target):\n                    raise ControlError("target became a reparse point", code="reparse_point_denied", status=403)\n                # Revalidate immediately before replacement. This serializes bridge writers and\n                # narrows the external-process race without pretending to be an OS-level CAS.\n                self._read_current(target, expected)\n                os.replace(temporary, target)\n        except ControlError:\n            try:\n                temporary.unlink(missing_ok=True)\n            finally:\n                raise\n        except OSError as exc:\n            try:\n                temporary.unlink(missing_ok=True)\n            finally:\n                raise ControlError("atomic write failed", code="filesystem_error", status=500) from exc\n'''
text = replace_once(text, old_atomic, new_atomic, "atomic CAS")
count = text.count("            self._atomic_replace(target, raw)\n")
if count != 2:
    raise SystemExit(f"atomic call sites: expected 2, got {count}")
text = text.replace("            self._atomic_replace(target, raw)\n", "            self._atomic_replace(target, raw, expected)\n")
path.write_text(text, encoding="utf-8")


test_path = Path("tests/test_dev_bridge_control.py")
test = test_path.read_text(encoding="utf-8")
if "test_atomic_replace_revalidates_expected_hash_at_commit_boundary" in test:
    raise SystemExit("CAS falsification already present")
test += '''\n\ndef test_atomic_replace_revalidates_expected_hash_at_commit_boundary(tmp_path):\n    writer, root = _writer(tmp_path)\n    target = root / "src" / "vivarium" / "race.py"\n    target.write_text("before\\n", encoding="utf-8")\n    expected = hashlib.sha256(target.read_bytes()).hexdigest()\n    target.write_text("external-change\\n", encoding="utf-8")\n\n    with pytest.raises(ControlError) as stale:\n        writer._atomic_replace(target, b"bridge-change\\n", expected)\n\n    assert stale.value.code == "stale_file"\n    assert target.read_text(encoding="utf-8") == "external-change\\n"\n    assert not list(target.parent.glob(".race.py.ric-write-*.tmp"))\n'''
test_path.write_text(test, encoding="utf-8")
