"""Local supervisor for the two-layer RIC development bridge.

The supervisor never persists the shared inner bearer. It receives it through
RIC_GATEWAY_TOKEN, passes it only to the two loopback child processes, and keeps
Cloudflare entirely outside its scope so an existing tunnel can remain live.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


class SupervisorError(RuntimeError):
    pass


def _child_env(token: str) -> dict[str, str]:
    env = dict(os.environ)
    env["RIC_GATEWAY_TOKEN"] = token
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    return env


def _terminate(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        try:
            process.kill()
        except OSError:
            pass


def main() -> None:
    install_dir = Path(__file__).resolve().parent
    config = install_dir / "config.json"
    if not config.is_file():
        raise SupervisorError("control config missing")
    token = os.environ.get("RIC_GATEWAY_TOKEN", "")
    if len(token) < 32:
        raise SupervisorError("RIC_GATEWAY_TOKEN must be supplied in process environment")
    workspace = Path(os.environ.get("RIC_WORKSPACE_ROOT", r"C:\AI\Vivarium social")).expanduser().resolve()
    gateway = workspace / "tools" / "ric_dev_gateway.py"
    if not gateway.is_file():
        raise SupervisorError("workspace gateway missing")

    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    inner_env = _child_env(token)
    inner_env["RIC_GATEWAY_PORT"] = "8788"
    inner = subprocess.Popen(
        [sys.executable, str(gateway)],
        cwd=str(workspace),
        env=inner_env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )

    control_env = _child_env(token)
    control_env["RIC_CONTROL_CONFIG"] = str(config)
    control = subprocess.Popen(
        [sys.executable, str(install_dir / "ric_bridge_control.py")],
        cwd=str(install_dir),
        env=control_env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )

    children = [inner, control]

    def stop(_signum=None, _frame=None):
        for process in reversed(children):
            _terminate(process)

    signal.signal(signal.SIGINT, stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, stop)

    try:
        while True:
            for name, process in (("inner", inner), ("control", control)):
                code = process.poll()
                if code is not None:
                    stop()
                    raise SupervisorError(f"{name} bridge process exited with code {code}")
            time.sleep(0.5)
    finally:
        stop()


if __name__ == "__main__":
    try:
        main()
    except SupervisorError as exc:
        raise SystemExit(f"RIC bridge supervisor failed: {exc}") from exc
