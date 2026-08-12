"""Sol review falsifications for Phase A bridge hardening."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from vivarium.dev_bridge import FilesystemTools, RootLock, _tail_jsonl


def _make_directory_link(link: Path, target: Path) -> bool:
    try:
        link.symlink_to(target, target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        pass
    if os.name == "nt":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and link.exists()
    return False


def test_search_never_enumerates_directory_reparse_point_outside_root(tmp_path):
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "inside.txt").write_text("safe\n", encoding="utf-8")
    (outside / "secret.txt").write_text("outside-needle\n", encoding="utf-8")
    link = root / "outside-link"
    if not _make_directory_link(link, outside):
        pytest.skip("directory symlink/junction creation unavailable")

    result = FilesystemTools(RootLock(root)).search_text({"path": ".", "query": "outside-needle"})

    assert result["matches"] == []


def test_tail_jsonl_reads_physical_end_of_large_file_with_bounded_window(tmp_path):
    path = tmp_path / "guardian.jsonl"
    records = []
    records.extend(json.dumps({"marker": "EARLY", "index": index, "payload": "x" * 900}) for index in range(800))
    records.extend(json.dumps({"marker": "MIDDLE", "index": index, "payload": "y" * 900}) for index in range(800, 1600))
    records.append(json.dumps({"marker": "TAIL-A", "index": 1600}))
    records.append(json.dumps({"marker": "TAIL-B", "index": 1601}))
    path.write_text("\n".join(records) + "\n", encoding="utf-8")
    assert path.stat().st_size > 2 * 512 * 1024

    result = _tail_jsonl(path, 2)

    assert [record["marker"] for record in result] == ["TAIL-A", "TAIL-B"]
    assert all(record.get("marker") != "EARLY" for record in result)


def test_tail_jsonl_discards_partial_leading_record_when_window_starts_mid_line(tmp_path):
    path = tmp_path / "diagnostics.jsonl"
    path.write_bytes((b"x" * (2 * 512 * 1024 + 100)) + b"\n" + b'{"marker":"TAIL"}\n')

    result = _tail_jsonl(path, 1)

    assert result == [{"marker": "TAIL"}]
