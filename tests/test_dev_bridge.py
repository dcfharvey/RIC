"""Falsifications for the bounded Phase A development bridge."""

from __future__ import annotations

import os
import sys
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


def test_exec_allowlist_shell_injection_timeout_output_cap_and_scoped_env(tmp_path):
    runner = CommandRunner(RootLock(tmp_path))
    script = _script(tmp_path, "probe.py", "import os,sys,time\nprint(os.getenv('RIC_BRIDGE_SCOPED','missing'))\nprint(os.getenv('RIC_GATEWAY_TOKEN','missing'))\nprint('x'*20000)\n")
    result = runner.run({
        "argv": [sys.executable, script], "cwd": ".", "output_limit": 1024,
        "env": {"RIC_BRIDGE_SCOPED": "only-this-process"},
    })
    assert result["exit_code"] == 0
    assert "only-this-process" in result["stdout"]
    assert "missing" in result["stdout"]
    assert result["truncated"] is True
    assert os.environ.get("RIC_BRIDGE_SCOPED") is None

    injection = runner.run({"argv": [sys.executable, "probe.py; echo injected"], "cwd": "."})
    assert injection["exit_code"] != 0
    assert "injected" not in injection["stdout"]
    with pytest.raises(BridgeError) as denied:
        runner.run({"argv": ["powershell", "-c", "Write-Output bad"], "cwd": "."})
    assert denied.value.code == "executable_denied"
    with pytest.raises(BridgeError) as path_env:
        runner.run({"argv": [sys.executable, script], "cwd": ".", "env": {"PYTHONPATH": "outside"}})
    assert path_env.value.code == "sensitive_env_denied"

    sleeper = _script(tmp_path, "sleep.py", "import time\ntime.sleep(3)\n")
    timed = runner.run({"argv": [sys.executable, sleeper], "cwd": ".", "timeout_seconds": 1})
    assert timed["timed_out"] is True


def test_jobs_start_poll_cancel_and_concurrency_limit(tmp_path):
    runner = CommandRunner(RootLock(tmp_path))
    sleeper = _script(tmp_path, "job_sleep.py", "import time\nprint('started', flush=True)\ntime.sleep(3)\n")
    jobs = JobManager(runner)
    first = jobs.start({"argv": [sys.executable, sleeper], "cwd": ".", "timeout_seconds": 10})
    second = jobs.start({"argv": [sys.executable, sleeper], "cwd": ".", "timeout_seconds": 10})
    with pytest.raises(BridgeError) as limited:
        jobs.start({"argv": [sys.executable, sleeper], "cwd": ".", "timeout_seconds": 10})
    assert limited.value.code == "job_limit"
    assert jobs.status(first)["status"] in {"running", "finished"}
    assert jobs.cancel(first)["status"] == "cancellation_requested"
    assert jobs.cancel(second)["status"] == "cancellation_requested"
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and (jobs.status(first)["status"] != "finished" or jobs.status(second)["status"] != "finished"):
        time.sleep(0.05)
    assert jobs.output(first)["status"] == "finished"
    assert jobs.output(second)["status"] == "finished"
    noisy = _script(tmp_path, "job_noisy.py", "print('x' * 20000)")
    bounded = jobs.start({"argv": [sys.executable, noisy], "cwd": ".", "timeout_seconds": 10, "output_limit": 1024})
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and jobs.status(bounded)["status"] != "finished":
        time.sleep(0.05)
    bounded_output = jobs.output(bounded)
    assert bounded_output["truncated"] is True
    assert len(bounded_output["stdout"]) <= 1024


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


def test_git_surface_is_read_only_and_sees_untracked_workspace():
    root = Path(__file__).resolve().parents[1]
    service = DevBridgeService(root, "g" * 48)
    result = service.dispatch("/dev/git", {"operation": "status"})
    assert result["ok"] is True
    assert result["result"]["exit_code"] == 0
    assert result["result"]["stdout"].startswith("## ")
    with pytest.raises(BridgeError) as denied:
        service._git("commit", {})
    assert denied.value.code == "operation_not_found"
