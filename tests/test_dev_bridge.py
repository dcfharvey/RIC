"""Falsifications for the bounded Phase A development bridge."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from vivarium.db import connect_database, connect_readonly_database
from vivarium.dev_bridge import (
    BridgeError,
    CommandRunner,
    DevBridgeService,
    FilesystemTools,
    JobManager,
    RootLock,
)
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.repro import canonical_state_digest, max_seq


def _script(root: Path, name: str, body: str) -> str:
    path = root / name
    path.write_text(body, encoding="utf-8")
    return name


def test_filesystem_root_lock_and_sensitive_defaults(tmp_path):
    normal = tmp_path / "normal.txt"
    normal.write_text("alpha\nbeta\n", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=hidden", encoding="utf-8")
    tools = FilesystemTools(RootLock(tmp_path))

    assert tools.read_file({"path": "normal.txt"})["content"].splitlines() == ["alpha", "beta"]
    assert tools.search_text({"path": ".", "query": "beta"})["matches"][0]["line"] == 2
    with pytest.raises(BridgeError) as traversal:
        tools.read_file({"path": "../outside.txt"})
    assert traversal.value.code == "path_outside_root"
    with pytest.raises(BridgeError):
        tools.read_file({"path": str(tmp_path.parent / "outside.txt")})
    with pytest.raises(BridgeError) as secret:
        tools.read_file({"path": ".env"})
    assert secret.value.code == "sensitive_path_denied"
    listing = tools.list_tree({"path": "."})
    assert all(item["path"] != ".env" for item in listing["entries"])
    assert listing["sensitive_hidden"] >= 1


def test_filesystem_symlink_outside_is_rejected_when_supported(tmp_path):
    outside = tmp_path.parent / "bridge-outside-secret.txt"
    outside.write_text("outside", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    with pytest.raises(BridgeError) as raised:
        FilesystemTools(RootLock(tmp_path)).read_file({"path": "link.txt"})
    assert raised.value.code == "path_outside_root"


def test_search_scan_is_progressively_bounded(tmp_path):
    for index in range(2100):
        (tmp_path / f"file-{index}.txt").write_text("no match\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "ignored.txt").write_text("needle\n", encoding="utf-8")
    result = FilesystemTools(RootLock(tmp_path)).search_text({"path": ".", "query": "needle"})
    assert result["matches"] == []
    assert result["scan_limited"] is True
    assert result["files_inspected"] <= 2000


def test_exec_allowlist_shell_injection_timeout_output_cap_and_scoped_env(tmp_path):
    runner = CommandRunner(RootLock(tmp_path))
    script = _script(tmp_path, "test_probe.py", "def test_probe():\n import os\n print(os.getenv('RIC_BRIDGE_SCOPED','missing'))\n print(os.getenv('RIC_GATEWAY_TOKEN','missing'))\n print('x'*20000)\n")
    result = runner.run({
        "argv": ["python", "-m", "pytest", script, "-s", "-q"], "cwd": ".", "output_limit": 1024,
        "env": {"RIC_BRIDGE_SCOPED": "only-this-process"},
    })
    assert result["exit_code"] == 0
    assert "only-this-process" in result["stdout"]
    assert "missing" in result["stdout"]
    assert result["truncated"] is True
    assert os.environ.get("RIC_BRIDGE_SCOPED") is None

    injection = runner.run({"argv": ["python", "-m", "pytest", "test_probe.py; echo injected"], "cwd": "."})
    assert injection["exit_code"] != 0
    assert "injected" not in injection["stdout"]
    with pytest.raises(BridgeError) as denied:
        runner.run({"argv": ["powershell", "-c", "Write-Output bad"], "cwd": "."})
    assert denied.value.code == "executable_denied"
    with pytest.raises(BridgeError) as path_env:
        runner.run({"argv": ["python", "-m", "pytest", script], "cwd": ".", "env": {"PYTHONPATH": "outside"}})
    assert path_env.value.code == "sensitive_env_denied"

    sleeper = _script(tmp_path, "test_sleep.py", "def test_sleep():\n import time\n time.sleep(3)\n")
    timed = runner.run({"argv": ["python", "-m", "pytest", sleeper, "-q"], "cwd": ".", "timeout_seconds": 1})
    assert timed["timed_out"] is True


def test_jobs_start_poll_cancel_and_concurrency_limit(tmp_path):
    runner = CommandRunner(RootLock(tmp_path))
    sleeper = _script(tmp_path, "test_job_sleep.py", "def test_sleep():\n import time\n print('started', flush=True)\n time.sleep(3)\n")
    jobs = JobManager(runner)
    first = jobs.start({"argv": ["python", "-m", "pytest", sleeper, "-q"], "cwd": ".", "timeout_seconds": 10})
    second = jobs.start({"argv": ["python", "-m", "pytest", sleeper, "-q"], "cwd": ".", "timeout_seconds": 10})
    with pytest.raises(BridgeError) as limited:
        jobs.start({"argv": ["python", "-m", "pytest", sleeper, "-q"], "cwd": ".", "timeout_seconds": 10})
    assert limited.value.code == "job_limit"
    assert jobs.status(first)["status"] in {"running", "finished"}
    assert jobs.cancel(first)["status"] == "cancellation_requested"
    assert jobs.cancel(second)["status"] == "cancellation_requested"
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and (jobs.status(first)["status"] != "finished" or jobs.status(second)["status"] != "finished"):
        time.sleep(0.05)
    assert jobs.output(first)["status"] == "finished"
    assert jobs.output(second)["status"] == "finished"
    noisy = _script(tmp_path, "test_job_noisy.py", "def test_noisy():\n print('x' * 20000)\n")
    bounded = jobs.start({"argv": ["python", "-m", "pytest", noisy, "-s", "-q"], "cwd": ".", "timeout_seconds": 10, "output_limit": 1024})
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and jobs.status(bounded)["status"] != "finished":
        time.sleep(0.05)
    bounded_output = jobs.output(bounded)
    assert bounded_output["truncated"] is True
    assert len(bounded_output["stdout"]) <= 1024


def test_process_tree_cancel_and_timeout_kill_descendants(tmp_path):
    sentinel_cancel = tmp_path / "cancel-sentinel.txt"
    ready_cancel = tmp_path / "cancel-ready.txt"
    release_cancel = tmp_path / "cancel-release.txt"
    cancel_child = _script(tmp_path, "cancel_child.py", f"""import pathlib, time
release = pathlib.Path(r'{release_cancel}')
while not release.exists():
    time.sleep(0.05)
pathlib.Path(r'{sentinel_cancel}').write_text('survived')
""")
    parent = _script(tmp_path, "test_parent.py", f"""def test_parent():
 import pathlib, subprocess, sys, time
 subprocess.Popen([sys.executable, r'{tmp_path / cancel_child}'])
 pathlib.Path(r'{ready_cancel}').write_text('ready')
 time.sleep(30)
""")
    runner = CommandRunner(RootLock(tmp_path))
    jobs = JobManager(runner)
    job = jobs.start({"argv": ["python", "-m", "pytest", parent, "-q"], "cwd": ".", "timeout_seconds": 30})
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and not ready_cancel.exists() and jobs.status(job)["status"] != "finished":
        time.sleep(0.05)
    assert ready_cancel.exists(), jobs.output(job)
    jobs.cancel(job)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and jobs.status(job)["status"] != "finished":
        time.sleep(0.05)
    assert jobs.output(job)["status"] == "finished"
    release_cancel.write_text("release", encoding="utf-8")
    time.sleep(0.5)
    assert not sentinel_cancel.exists()

    sentinel_timeout = tmp_path / "timeout-sentinel.txt"
    ready_timeout = tmp_path / "timeout-ready.txt"
    release_timeout = tmp_path / "timeout-release.txt"
    timeout_child = _script(tmp_path, "timeout_child.py", f"""import pathlib, time
release = pathlib.Path(r'{release_timeout}')
while not release.exists():
    time.sleep(0.05)
pathlib.Path(r'{sentinel_timeout}').write_text('survived')
""")
    parent_timeout = _script(tmp_path, "test_parent_timeout.py", f"""def test_parent_timeout():
 import pathlib, subprocess, sys, time
 subprocess.Popen([sys.executable, r'{tmp_path / timeout_child}'])
 pathlib.Path(r'{ready_timeout}').write_text('ready')
 time.sleep(30)
""")
    timeout_job = jobs.start({"argv": ["python", "-m", "pytest", parent_timeout, "-q"], "cwd": ".", "timeout_seconds": 6})
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and not ready_timeout.exists() and jobs.status(timeout_job)["status"] != "finished":
        time.sleep(0.05)
    assert ready_timeout.exists(), jobs.output(timeout_job)
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline and jobs.status(timeout_job)["status"] != "finished":
        time.sleep(0.05)
    result = jobs.output(timeout_job)
    assert result["status"] == "finished"
    assert result["timed_out"] is True, result
    release_timeout.write_text("release", encoding="utf-8")
    time.sleep(0.5)
    assert not sentinel_timeout.exists()

def test_service_auth_capabilities_and_read_only_inspector(tmp_path):
    db_path = tmp_path / "inspect.sqlite"
    conn = connect_database(str(db_path))
    try:
        ensure_schema(conn)
        world_id = IntegrationWorldService(conn).create_initial_world()["id"]
    finally:
        conn.close()
    token = "t" * 48
    service = DevBridgeService(tmp_path, token, db_path="inspect.sqlite")
    assert service.authorized(None) is False
    assert service.authorized("Bearer wrong") is False
    assert service.authorized(f"Bearer {token}") is True
    capabilities = service.capabilities()
    assert capabilities["permissions"]["REPO_WRITE"] == "DENY"
    assert "exec" in capabilities["tools"]
    assert "git" not in capabilities["tools"]["exec"]["allowlist"]
    before_conn = connect_readonly_database(db_path)
    before = (canonical_state_digest(before_conn, world_id), max_seq(before_conn, world_id))
    before_conn.close()
    status = service.dispatch("/dev/ric", {"operation": "world_status", "world_id": world_id})
    telemetry = service.dispatch("/dev/ric", {"operation": "telemetry_snapshot", "world_id": world_id})
    assert status["ok"] is True
    assert telemetry["ok"] is True
    after_conn = connect_readonly_database(db_path)
    after = (canonical_state_digest(after_conn, world_id), max_seq(after_conn, world_id))
    after_conn.close()
    assert after == before

    huge = tmp_path / "records.jsonl"
    huge.write_text(("{\"payload\":\"" + ("x" * 10000) + "\"}\n") * 100, encoding="utf-8")
    with pytest.raises(BridgeError) as too_large:
        service.dispatch("/dev/ric", {"operation": "diagnostics_tail", "path": "records.jsonl", "limit": 100})
    assert too_large.value.code == "response_too_large"


def test_git_surface_is_read_only_and_sees_untracked_workspace():
    root = Path(__file__).resolve().parents[1]
    service = DevBridgeService(root, "g" * 48)
    before_head = (root / ".git" / "HEAD").read_bytes()
    before_index = (root / ".git" / "index").read_bytes()
    result = service.dispatch("/dev/git", {"operation": "status"})
    assert result["ok"] is True
    assert result["result"]["exit_code"] == 0
    assert result["result"]["stdout"].startswith("## ")
    with pytest.raises(BridgeError) as denied:
        service._git("commit", {})
    assert denied.value.code == "operation_not_found"
    with pytest.raises(BridgeError):
        service.runner.run({"argv": ["git", "branch", "evil"], "cwd": "."})
    with pytest.raises(BridgeError) as injected:
        service._git("show", {"ref": "--output=leak"})
    assert injected.value.code == "invalid_git_ref"
    with pytest.raises(BridgeError):
        service._git("show", {"ref": "HEAD:.env"})
    assert (root / ".git" / "HEAD").read_bytes() == before_head
    assert (root / ".git" / "index").read_bytes() == before_index
