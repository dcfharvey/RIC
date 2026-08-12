"""Bounded, read-only development bridge for Sol/Codex inspection.

The bridge is deliberately separate from the RIC runtime.  It exposes a small
JSON operation surface, keeps the workspace root locked, and uses read-only
SQLite connections for every inspector operation.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .db import connect_readonly_database
from .diagnostics import MAX_DIAGNOSTIC_STRING
from .repro import max_seq
from .sleep_physiology import SleepPhysiologyService
from .telemetry import inspect_rodage
from .world import WorldEngine


MAX_RESPONSE_BYTES = 512 * 1024
MAX_RECORD_BYTES = 16 * 1024
MAX_FILE_BYTES = 256 * 1024
MAX_SEARCH_MATCHES = 200
MAX_SEARCH_FILES = 2000
MAX_SEARCH_BYTES = 64 * 1024 * 1024
MAX_SEARCH_SECONDS = 5
MAX_TREE_ENTRIES = 500
MAX_EXEC_OUTPUT = 512 * 1024
MAX_EXEC_SECONDS = 120
MAX_JOB_SECONDS = 600
MAX_JOBS = 2
MAX_STORED_JOBS = 32
JOB_TTL_SECONDS = 3600

_SECRET_NAME = re.compile(
    r"(^|[._-])(env|secret|secrets|token|tokens|password|credential|credentials|private|key)([._-]|$)",
    re.IGNORECASE,
)
_SECRET_EXTENSIONS = {".pem", ".key", ".p12", ".pfx", ".secret"}
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
_READ_ONLY_GIT = {"status", "diff", "log", "branch", "rev-parse", "show", "ls-files"}
_ALLOWED_EXECUTABLES = {"python", "python.exe", "py", "py.exe", "pytest", "pytest.exe"}
_GIT_REF = re.compile(r"^[A-Za-z0-9._/@-]{1,256}$")
_SEARCH_SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"}


class BridgeError(ValueError):
    def __init__(self, message: str, *, code: str = "invalid_request", status: int = 400) -> None:
        super().__init__(message)
        self.code, self.status = code, status


def _bounded_limit(value: Any, default: int, maximum: int) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise BridgeError("invalid limit", code="invalid_limit") from exc
    if not 1 <= result <= maximum:
        raise BridgeError("limit outside allowed range", code="invalid_limit")
    return result


def _json_safe(value: Any, *, limit: int = MAX_RESPONSE_BYTES) -> Any:
    """Return JSON-compatible data without ever serializing secrets or huge text."""
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item, limit=limit)
            for key, item in value.items()
            if str(key).lower() not in {"authorization", "token", "secret", "password", "headers"}
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe(item, limit=limit) for item in value]
    if isinstance(value, str):
        return value[:limit]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return repr(value)[:limit]


def _json_record(value: Any) -> Any:
    safe = _json_safe(value, limit=MAX_RECORD_BYTES)
    if len(json.dumps(safe, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) > MAX_RECORD_BYTES:
        return {"truncated": True}
    return safe


class RootLock:
    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()
        if not self.root.is_dir():
            raise BridgeError("workspace root absent", code="root_missing", status=500)

    def _is_secret(self, path: Path) -> bool:
        relative = path.relative_to(self.root)
        if any(_SECRET_NAME.search(part) for part in relative.parts):
            return True
        return path.suffix.lower() in _SECRET_EXTENSIONS

    def path(self, value: Any, *, allow_root: bool = True, reject_secret: bool = True) -> Path:
        if not isinstance(value, str) or not value or "\x00" in value:
            raise BridgeError("path must be a non-empty string", code="invalid_path")
        candidate = Path(value)
        if candidate.is_absolute():
            raise BridgeError("absolute paths are forbidden", code="path_outside_root", status=403)
        resolved = (self.root / candidate).resolve(strict=False)
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise BridgeError("path escapes workspace root", code="path_outside_root", status=403) from exc
        if not allow_root and resolved == self.root:
            raise BridgeError("workspace root is not a file", code="invalid_path")
        if reject_secret and self._is_secret(resolved):
            raise BridgeError("sensitive paths are denied", code="sensitive_path_denied", status=403)
        return resolved

    def relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix() or "."


class FilesystemTools:
    def __init__(self, root: RootLock) -> None:
        self.root = root

    def list_tree(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        base = self.root.path(payload.get("path", "."))
        limit = _bounded_limit(payload.get("limit", MAX_TREE_ENTRIES), MAX_TREE_ENTRIES, MAX_TREE_ENTRIES)
        entries: list[dict[str, Any]] = []
        hidden = 0
        stack = [base]
        while stack and len(entries) < limit:
            current = stack.pop()
            try:
                children = sorted(current.iterdir(), key=lambda item: item.name.casefold(), reverse=True)
            except OSError as exc:
                raise BridgeError("directory cannot be read", code="filesystem_error", status=500) from exc
            for child in children:
                if self.root._is_secret(child):
                    hidden += 1
                    continue
                try:
                    resolved = child.resolve(strict=False)
                    resolved.relative_to(self.root.root)
                except (OSError, ValueError):
                    hidden += 1
                    continue
                entries.append({
                    "path": self.root.relative(resolved),
                    "kind": "directory" if resolved.is_dir() else "file" if resolved.is_file() else "other",
                })
                if resolved.is_dir() and not resolved.is_symlink():
                    stack.append(resolved)
                if len(entries) >= limit:
                    break
        return {"entries": entries, "truncated": bool(stack), "sensitive_hidden": hidden}

    def stat(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        path = self.root.path(payload.get("path"), allow_root=False)
        try:
            info = path.stat()
        except OSError as exc:
            raise BridgeError("path cannot be stated", code="filesystem_error", status=404) from exc
        return {"path": self.root.relative(path), "kind": "directory" if path.is_dir() else "file", "size": info.st_size}

    def read_file(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        path = self.root.path(payload.get("path"), allow_root=False)
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise BridgeError("file cannot be read", code="filesystem_error", status=404) from exc
        if len(raw) > MAX_FILE_BYTES:
            raise BridgeError("file exceeds response limit", code="response_too_large", status=413)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BridgeError("binary files are not supported", code="text_only") from exc
        return {"path": self.root.relative(path), "content": text, "truncated": False}

    def search_text(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        query = payload.get("query")
        if not isinstance(query, str) or not query or len(query) > 4096:
            raise BridgeError("query must be a bounded non-empty string")
        base = self.root.path(payload.get("path", "."))
        limit = _bounded_limit(payload.get("limit", MAX_SEARCH_MATCHES), MAX_SEARCH_MATCHES, MAX_SEARCH_MATCHES)
        matches: list[dict[str, Any]] = []
        pending = deque([base])
        inspected_files = 0
        inspected_bytes = 0
        deadline = time.monotonic() + MAX_SEARCH_SECONDS
        scan_limited = False
        while pending:
            if inspected_files >= MAX_SEARCH_FILES or inspected_bytes >= MAX_SEARCH_BYTES or time.monotonic() >= deadline:
                scan_limited = True
                break
            path = pending.popleft()
            try:
                if path.is_dir():
                    for child in path.iterdir():
                        if child.is_dir() and child.name in _SEARCH_SKIP_DIRS:
                            continue
                        pending.append(child)
                    continue
            except OSError:
                continue
            inspected_files += 1
            try:
                path = self.root.path(self.root.relative(path))
            except BridgeError:
                continue
            try:
                raw = path.read_bytes()
                if len(raw) > MAX_FILE_BYTES or inspected_bytes + len(raw) > MAX_SEARCH_BYTES:
                    scan_limited = True
                    continue
                inspected_bytes += len(raw)
                text = raw.decode("utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for line_number, line in enumerate(text.splitlines(), 1):
                if query in line:
                    matches.append({"path": self.root.relative(path), "line": line_number, "text": line[:MAX_DIAGNOSTIC_STRING]})
                    if len(matches) >= limit:
                        return {"matches": matches, "truncated": True, "scan_limited": scan_limited,
                                "files_inspected": inspected_files, "bytes_inspected": inspected_bytes}
        return {"matches": matches, "truncated": bool(pending) or scan_limited, "scan_limited": scan_limited,
                "files_inspected": inspected_files, "bytes_inspected": inspected_bytes}


def _bounded_text(raw: bytes, cap: int) -> tuple[str, bool]:
    truncated = len(raw) > cap
    return raw[:cap].decode("utf-8", errors="replace"), truncated


def _safe_process_env(root: Path | None = None) -> dict[str, str]:
    """Keep inherited execution context useful without forwarding secrets."""
    env = {
        key: value for key, value in os.environ.items()
        if not _SECRET_NAME.search(key)
        and not key.upper().startswith("GIT_CONFIG_")
        and key.upper() not in {"PYTHONPATH", "PYTHONHOME"}
    }
    if root is not None:
        env.update({
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "safe.directory",
            "GIT_CONFIG_VALUE_0": str(root),
        })
    return env


class _ProcessTree:
    """Windows Job Object wrapper with kill-on-close semantics."""

    def __init__(self, process: subprocess.Popen[bytes]) -> None:
        self.process = process
        self.handle: int | None = None

    def attach(self) -> None:
        if os.name != "nt":
            raise BridgeError("process tree isolation unavailable", code="process_isolation_unavailable", status=503)
        import ctypes
        self._ctypes = ctypes

        class _Basic(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTime", ctypes.c_longlong), ("PerJobUserTime", ctypes.c_longlong),
                ("LimitFlags", ctypes.c_uint32), ("MinimumWorkingSetSize", ctypes.c_void_p),
                ("MaximumWorkingSetSize", ctypes.c_void_p), ("ActiveProcessLimit", ctypes.c_uint32),
                ("Affinity", ctypes.c_void_p), ("PriorityClass", ctypes.c_uint32),
                ("SchedulingClass", ctypes.c_uint32),
            ]

        class _Io(ctypes.Structure):
            _fields_ = [("ReadOperationCount", ctypes.c_ulonglong), ("WriteOperationCount", ctypes.c_ulonglong),
                        ("OtherOperationCount", ctypes.c_ulonglong), ("ReadTransferCount", ctypes.c_ulonglong),
                        ("WriteTransferCount", ctypes.c_ulonglong), ("OtherTransferCount", ctypes.c_ulonglong)]

        class _Extended(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", _Basic), ("IoInfo", _Io),
                        ("ProcessMemoryLimit", ctypes.c_void_p), ("JobMemoryLimit", ctypes.c_void_p),
                        ("PeakProcessMemoryUsed", ctypes.c_void_p), ("PeakJobMemoryUsed", ctypes.c_void_p)]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        kernel.CreateJobObjectW.restype = ctypes.c_void_p
        kernel.SetInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
        kernel.SetInformationJobObject.restype = ctypes.c_int
        kernel.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        kernel.AssignProcessToJobObject.restype = ctypes.c_int
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel.CloseHandle.restype = ctypes.c_int
        handle = kernel.CreateJobObjectW(None, None)
        if not handle:
            raise BridgeError("cannot create process job", code="process_isolation_unavailable", status=503)
        info = _Extended()
        info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel.SetInformationJobObject(handle, 9, ctypes.byref(info), ctypes.sizeof(info)) \
                or not kernel.AssignProcessToJobObject(handle, ctypes.c_void_p(self.process._handle)):
            kernel.CloseHandle(handle)
            raise BridgeError("cannot isolate process tree", code="process_isolation_unavailable", status=503)
        self.handle = int(handle)
        self._kernel = kernel

    def terminate(self) -> None:
        if self.handle:
            self._kernel.TerminateJobObject(self._ctypes.c_void_p(self.handle), 1)
        else:
            self.process.terminate()

    def kill(self) -> None:
        self.terminate()

    def close(self) -> None:
        if self.handle:
            self._kernel.CloseHandle(self._ctypes.c_void_p(self.handle))
            self.handle = None


def _run_bounded_process(process: subprocess.Popen[bytes], timeout: int, cap: int, tree: _ProcessTree) -> tuple[bytes, bytes, bool]:
    """Drain both pipes concurrently while retaining only cap+1 bytes each."""
    captured: dict[str, bytearray] = {"stdout": bytearray(), "stderr": bytearray()}

    def drain(name: str, stream: Any) -> None:
        while True:
            chunk = stream.read(8192)
            if not chunk:
                return
            target = captured[name]
            if len(target) < cap + 1:
                target.extend(chunk[: cap + 1 - len(target)])

    readers = [
        threading.Thread(target=drain, args=("stdout", process.stdout), daemon=True),
        threading.Thread(target=drain, args=("stderr", process.stderr), daemon=True),
    ]
    for reader in readers:
        reader.start()
    timed_out = False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        tree.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            tree.kill()
            process.wait()
    for reader in readers:
        reader.join(timeout=5)
    return bytes(captured["stdout"]), bytes(captured["stderr"]), timed_out


class CommandRunner:
    def __init__(self, root: RootLock, *, redactions: tuple[str, ...] = ()) -> None:
        self.root = root
        self.redactions = tuple(item for item in redactions if item)

    def _redact(self, text: str) -> str:
        for item in self.redactions:
            text = text.replace(item, "[REDACTED]")
        return text

    def validate(self, payload: Mapping[str, Any]) -> tuple[list[str], Path, int, int, dict[str, str]]:
        argv = payload.get("argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(item, str) or not item for item in argv):
            raise BridgeError("argv must be a non-empty string array", code="invalid_argv")
        if len(argv) > 32 or sum(len(item) for item in argv) > 64 * 1024:
            raise BridgeError("argv exceeds limits", code="invalid_argv")
        executable = argv[0].casefold()
        if executable not in _ALLOWED_EXECUTABLES:
            raise BridgeError("executable is not allowlisted", code="executable_denied", status=403)
        argv = list(argv)
        if executable in {"python", "python.exe", "py", "py.exe"}:
            if len(argv) < 3 or argv[1:3] != ["-m", "pytest"]:
                raise BridgeError("only python -m pytest is allowed", code="unsafe_exec", status=403)
            argv = [sys.executable, *argv[1:]]
        elif executable in {"pytest", "pytest.exe"}:
            argv = [sys.executable, "-m", "pytest", *argv[1:]]
        for item in argv[1:]:
            if "\x00" in item or re.search(r"(^|[\\/])\.\.([\\/]|$)", item) or re.match(r"^[A-Za-z]:[\\/]", item):
                raise BridgeError("argv path escapes workspace root", code="path_outside_root", status=403)
        cwd = self.root.path(payload.get("cwd", "."))
        if not cwd.is_dir():
            raise BridgeError("cwd must be a directory", code="invalid_cwd")
        timeout = int(payload.get("timeout_seconds", 30))
        if not 1 <= timeout <= MAX_EXEC_SECONDS:
            raise BridgeError("timeout outside allowed range", code="invalid_timeout")
        output_limit = min(int(payload.get("output_limit", MAX_EXEC_OUTPUT)), MAX_EXEC_OUTPUT)
        if output_limit < 1024:
            raise BridgeError("output limit too small", code="invalid_output_limit")
        supplied = payload.get("env", {})
        if not isinstance(supplied, Mapping) or len(supplied) > 32:
            raise BridgeError("env must be a small mapping", code="invalid_env")
        env: dict[str, str] = {}
        for key, value in supplied.items():
            if not isinstance(key, str) or not _ENV_NAME.fullmatch(key) \
                    or key.upper() in {"PATH", "PATHEXT", "COMSPEC", "PYTHONPATH", "PYTHONHOME"} \
                    or re.search(r"TOKEN|SECRET|PASSWORD|PRIVATE|KEY", key, re.I):
                raise BridgeError("secret-like environment names are denied", code="sensitive_env_denied", status=403)
            if not isinstance(value, str) or len(value) > 4096:
                raise BridgeError("environment value is invalid", code="invalid_env")
            env[key] = value
        return argv, cwd, timeout, output_limit, env

    def run(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        argv, cwd, timeout, output_limit, supplied = self.validate(payload)
        env = _safe_process_env(self.root.root)
        env.update(supplied)
        started = time.monotonic()
        process = subprocess.Popen(
            argv, cwd=str(cwd), env=env, shell=False,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        tree = _ProcessTree(process)
        try:
            tree.attach()
        except BridgeError:
            process.terminate()
            process.wait(timeout=5)
            raise
        try:
            stdout, stderr, timed_out = _run_bounded_process(process, timeout, output_limit, tree)
        finally:
            tree.close()
        out, out_truncated = _bounded_text(stdout, output_limit)
        err, err_truncated = _bounded_text(stderr, output_limit)
        return {
            "exit_code": None if timed_out else process.returncode,
            "stdout": self._redact(out), "stderr": self._redact(err),
            "truncated": out_truncated or err_truncated, "timed_out": timed_out,
            "duration_ms": round((time.monotonic() - started) * 1000),
        }


@dataclass
class _Job:
    job_id: str
    argv: list[str]
    cwd: Path
    timeout: int
    output_limit: int
    process: subprocess.Popen[bytes]
    tree: _ProcessTree
    started: float
    stdout: str = ""
    stderr: str = ""
    truncated: bool = False
    timed_out: bool = False
    finished: bool = False


class JobManager:
    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner
        self._jobs: dict[str, _Job] = {}
        self._lock = threading.Lock()

    def _reap(self) -> None:
        cutoff = time.monotonic() - JOB_TTL_SECONDS
        with self._lock:
            for job_id, job in list(self._jobs.items()):
                if job.finished and job.started < cutoff:
                    self._jobs.pop(job_id, None)
            if len(self._jobs) > MAX_STORED_JOBS:
                for job_id, job in list(self._jobs.items()):
                    if len(self._jobs) <= MAX_STORED_JOBS:
                        break
                    if job.finished:
                        self._jobs.pop(job_id, None)

    def start(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        self._reap()
        argv, cwd, timeout, output_limit, supplied = self.runner.validate(payload)
        with self._lock:
            active = sum(not job.finished for job in self._jobs.values())
            if active >= MAX_JOBS:
                raise BridgeError("job concurrency limit reached", code="job_limit", status=429)
            env = _safe_process_env(self.runner.root.root); env.update(supplied)
            process = subprocess.Popen(
                argv, cwd=str(cwd), env=env, shell=False,
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
            tree = _ProcessTree(process)
            try:
                tree.attach()
            except BridgeError:
                process.terminate()
                process.wait(timeout=5)
                raise
            job = _Job(uuid.uuid4().hex, argv, cwd, timeout, output_limit, process, tree, time.monotonic())
            self._jobs[job.job_id] = job
        threading.Thread(target=self._watch, args=(job,), daemon=True).start()
        return {"job_id": job.job_id, "status": "running"}

    def _watch(self, job: _Job) -> None:
        try:
            stdout, stderr, job.timed_out = _run_bounded_process(job.process, job.timeout, job.output_limit, job.tree)
        finally:
            job.tree.close()
        out, out_truncated = _bounded_text(stdout, job.output_limit)
        err, err_truncated = _bounded_text(stderr, job.output_limit)
        with self._lock:
            job.stdout = self.runner._redact(out)
            job.stderr = self.runner._redact(err)
            job.truncated = out_truncated or err_truncated
            job.finished = True

    def _get(self, value: Any) -> _Job:
        if not isinstance(value, str) or not value:
            raise BridgeError("job_id is required")
        with self._lock:
            job = self._jobs.get(value)
        if job is None:
            raise BridgeError("job not found", code="job_not_found", status=404)
        return job

    def status(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        job = self._get(payload.get("job_id"))
        return {"job_id": job.job_id, "status": "finished" if job.finished else "running", "timed_out": job.timed_out}

    def output(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        job = self._get(payload.get("job_id"))
        return {"job_id": job.job_id, "status": "finished" if job.finished else "running", "exit_code": job.process.returncode if job.finished else None, "stdout": job.stdout, "stderr": job.stderr, "truncated": job.truncated, "timed_out": job.timed_out}

    def cancel(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        job = self._get(payload.get("job_id"))
        if not job.finished:
            job.tree.terminate()
        return {"job_id": job.job_id, "status": "cancellation_requested"}


class GitReadOnly:
    def __init__(self, root: RootLock, *, redactions: tuple[str, ...] = ()) -> None:
        executable = shutil.which("git")
        if not executable:
            raise BridgeError("git executable unavailable", code="git_unavailable", status=503)
        self.root = root
        self.executable = str(Path(executable).resolve())
        self.redactions = redactions

    @staticmethod
    def _ref(value: Any) -> str:
        if not isinstance(value, str) or not value or value.startswith("-") or not _GIT_REF.fullmatch(value):
            raise BridgeError("invalid git ref", code="invalid_git_ref", status=400)
        if any(token in value for token in ("..", "@{", ":", "^", "~", "\\")):
            raise BridgeError("invalid git ref", code="invalid_git_ref", status=400)
        return value

    def _run(self, args: list[str], *, timeout: int = 30) -> dict[str, Any]:
        process = subprocess.Popen(
            [self.executable, *args], cwd=str(self.root.root), env=_safe_process_env(self.root.root),
            shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        tree = _ProcessTree(process)
        try:
            try:
                tree.attach()
            except BridgeError:
                process.terminate()
                process.wait(timeout=5)
                raise
            stdout, stderr, timed_out = _run_bounded_process(process, timeout, MAX_EXEC_OUTPUT, tree)
        finally:
            tree.close()
        out, out_truncated = _bounded_text(stdout, MAX_EXEC_OUTPUT)
        err, err_truncated = _bounded_text(stderr, MAX_EXEC_OUTPUT)
        for redaction in self.redactions:
            out, err = out.replace(redaction, "[REDACTED]"), err.replace(redaction, "[REDACTED]")
        return {"exit_code": None if timed_out else process.returncode, "stdout": out, "stderr": err,
                "truncated": out_truncated or err_truncated, "timed_out": timed_out}

    def dispatch(self, operation: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        if operation == "status":
            args = ["status", "--short", "--branch", "--untracked-files=normal"]
        elif operation == "diff":
            args = ["diff", "--no-ext-diff", "--binary"]
        elif operation == "log":
            limit = min(max(int(payload.get("limit", 30)), 1), 100)
            args = ["log", "--oneline", "--decorate", f"-{limit}"]
        elif operation == "branch":
            args = ["branch", "-vv"]
        elif operation == "rev-parse":
            ref = self._ref(payload.get("ref", "HEAD"))
            args = ["rev-parse", "--verify", f"{ref}^{{commit}}"]
        elif operation == "show":
            ref = self._ref(payload.get("ref", "HEAD"))
            args = ["show", "--stat", "--oneline", ref]
        elif operation == "ls-files":
            args = ["ls-files", "--cached", "--others", "--exclude-standard"]
        else:
            raise BridgeError("git operation unavailable", code="operation_not_found", status=404)
        return self._run(args)


def _tail_jsonl(path: Path, limit: int) -> list[Any]:
    if not path.exists():
        return []
    try:
        lines: deque[bytes] = deque(maxlen=limit)
        total = 0
        with path.open("rb") as handle:
            for line in handle:
                total += len(line)
                if total > MAX_RESPONSE_BYTES * 2:
                    break
                lines.append(line.rstrip(b"\r\n"))
    except OSError as exc:
        raise BridgeError("log cannot be read", code="filesystem_error", status=404) from exc
    result = []
    for line in lines:
        try:
            result.append(_json_record(json.loads(line.decode("utf-8"))))
        except (UnicodeDecodeError, ValueError):
            result.append(_json_record({"raw": line.decode("utf-8", errors="replace")[:MAX_DIAGNOSTIC_STRING]}))
    return result


class RicInspector:
    def __init__(self, root: RootLock, db_path: str | None = None) -> None:
        self.root = root
        configured = db_path or os.environ.get("RIC_DEV_DB_PATH", "data/vivarium-rodage.sqlite")
        self.db_path = self.root.path(configured, allow_root=False)

    def _conn(self):
        if not self.db_path.is_file():
            raise BridgeError("configured database is absent", code="database_missing", status=404)
        conn = connect_readonly_database(self.db_path)
        conn.execute("PRAGMA query_only = ON")
        return conn

    def _world(self, payload: Mapping[str, Any]) -> int:
        value = payload.get("world_id", 1)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise BridgeError("world_id is invalid")
        return value

    def world_status(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        conn = self._conn()
        try:
            world = WorldEngine(conn).get_world(self._world(payload))
            canonical = WorldEngine(conn).read_canonical_time(world["id"])
            schema = conn.execute("SELECT MAX(version) FROM migrations").fetchone()[0]
            return {"world": world, "canonical_at": canonical, "schema_version": schema, "event_seq": max_seq(conn, world["id"])}
        finally:
            conn.close()

    def active_activities(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT c.key AS character_key,a.type,a.started_at,a.planned_end_at,a.status "
                "FROM activity a JOIN character c ON c.id=a.character_id "
                "WHERE a.world_id=? AND a.status='active' ORDER BY c.key,a.id LIMIT 500",
                (self._world(payload),),
            ).fetchall()
            return {"activities": [dict(row) for row in rows]}
        finally:
            conn.close()

    def physiology_snapshot(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        conn = self._conn()
        try:
            service = SleepPhysiologyService(conn)
            characters = payload.get("character_key")
            if characters is None:
                rows = conn.execute("SELECT key FROM character WHERE world_id=? ORDER BY key", (self._world(payload),)).fetchall()
                characters = [row["key"] for row in rows]
            elif isinstance(characters, str):
                characters = [characters]
            if not isinstance(characters, list) or len(characters) > 32:
                raise BridgeError("character_key must be a bounded list")
            return {"states": {key: asdict(service.read_state(self._world(payload), key)) for key in characters}}
        finally:
            conn.close()

    def arbitration_audit(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        conn = self._conn()
        try:
            limit = _bounded_limit(payload.get("limit", 50), 50, 200)
            rows = conn.execute(
                "SELECT id,world_id,frame_digest,options_json,sources_json,result_json,canonical_at,reason_code,recorded_at "
                "FROM action_arbitration_audit WHERE world_id=? ORDER BY id DESC LIMIT ?",
                (self._world(payload), limit),
            ).fetchall()
            return {"audits": [_json_record(dict(row)) for row in rows]}
        finally:
            conn.close()

    def canonical_events_since(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        conn = self._conn()
        try:
            after = int(payload.get("after_seq", 0)); limit = _bounded_limit(payload.get("limit", 100), 100, 500)
            if after < 0 or limit < 1:
                raise BridgeError("invalid event bounds")
            rows = conn.execute(
                "SELECT seq,occurred_at,source_kind,event_type,payload FROM canonical_event "
                "WHERE world_id=? AND seq>? ORDER BY seq LIMIT ?",
                (self._world(payload), after, limit),
            ).fetchall()
            return {"events": [_json_record(dict(row)) for row in rows], "truncated": len(rows) >= limit}
        finally:
            conn.close()

    def telemetry_snapshot(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        conn = self._conn()
        try:
            return asdict(inspect_rodage(conn, self._world(payload)))
        finally:
            conn.close()

    def diagnostics_tail(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        path = self.root.path(payload.get("path", "logs/llm_diagnostics.jsonl"), allow_root=False)
        return {"records": _tail_jsonl(path, _bounded_limit(payload.get("limit", 50), 50, 200))}

    def runtime_outcomes_tail(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        path = self.root.path(payload.get("path", "logs/runtime_outcomes.jsonl"), allow_root=False)
        return {"records": _tail_jsonl(path, _bounded_limit(payload.get("limit", 50), 50, 200))}

    def guardian_report(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        path = self.root.path(payload.get("path", "logs/guardian.jsonl"), allow_root=False)
        return {"records": _tail_jsonl(path, _bounded_limit(payload.get("limit", 20), 20, 100)), "read_only": True}

    def dispatch(self, operation: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        operations = {
            "world_status": self.world_status, "active_activities": self.active_activities,
            "physiology_snapshot": self.physiology_snapshot, "arbitration_audit": self.arbitration_audit,
            "canonical_events_since": self.canonical_events_since, "telemetry_snapshot": self.telemetry_snapshot,
            "diagnostics_tail": self.diagnostics_tail, "runtime_outcomes_tail": self.runtime_outcomes_tail,
            "guardian_report": self.guardian_report,
        }
        handler = operations.get(operation)
        if handler is None:
            raise BridgeError("unknown inspector operation", code="operation_not_found", status=404)
        return handler(payload)


class DevBridgeService:
    FUTURE_PERMISSIONS = {"REPO_WRITE": "DENY", "RUNTIME_CONTROL": "DENY", "REAL_WORLD_WRITE": "DENY", "DESTRUCTIVE": "DENY"}

    def __init__(self, root: Path, token: str, *, db_path: str | None = None) -> None:
        if not isinstance(token, str) or len(token) < 32:
            raise BridgeError("strong bearer token required", code="token_invalid", status=500)
        self.token = token
        lock = RootLock(root)
        self.fs = FilesystemTools(lock)
        self.runner = CommandRunner(lock, redactions=(token,))
        self.jobs = JobManager(self.runner)
        self.git = GitReadOnly(lock, redactions=(token,))
        self.inspector = RicInspector(lock, db_path)
        self.root = lock

    def authorized(self, value: str | None) -> bool:
        import secrets
        return bool(value) and secrets.compare_digest(value, f"Bearer {self.token}")

    def capabilities(self) -> dict[str, Any]:
        return {
            "permissions": {"READ": "ALLOW", "TEST_EXEC": "ALLOW", **self.FUTURE_PERMISSIONS},
            "security": {
                "loopback_only": True,
                "subprocess": "approved pytest commands only; not an OS filesystem sandbox",
                "process_tree": "Windows Job Object kill-on-close",
                "aggregate_response_bytes": MAX_RESPONSE_BYTES,
            },
            "tools": {
                "filesystem": {"permission": "READ", "operations": ["list_tree", "read_file", "stat", "search_text"]},
                "exec": {"permission": "TEST_EXEC", "operations": ["exec"], "allowlist": sorted(_ALLOWED_EXECUTABLES), "mode": "server-pinned pytest"},
                "jobs": {"permission": "TEST_EXEC", "operations": ["start_job", "job_status", "job_output", "cancel_job"], "max_concurrent": MAX_JOBS},
                "git": {"permission": "READ", "operations": sorted(_READ_ONLY_GIT), "structured_only": True},
                "ric_inspector": {"permission": "READ", "operations": ["guardian_report", "telemetry_snapshot", "world_status", "active_activities", "diagnostics_tail", "runtime_outcomes_tail", "physiology_snapshot", "arbitration_audit", "canonical_events_since"]},
            },
        }

    def _git(self, operation: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self.git.dispatch(operation, payload)

    def dispatch(self, route: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        if route == "/dev/fs":
            operation = payload.get("operation")
            result = getattr(self.fs, operation)(payload) if isinstance(operation, str) and operation in {"list_tree", "read_file", "stat", "search_text"} else None
            if result is None: raise BridgeError("filesystem operation unavailable", code="operation_not_found", status=404)
        elif route == "/dev/exec":
            if payload.get("operation", "exec") != "exec": raise BridgeError("exec operation unavailable", code="operation_not_found", status=404)
            result = self.runner.run(payload)
        elif route == "/dev/jobs":
            operation = payload.get("operation")
            handler = {"start_job": self.jobs.start, "job_status": self.jobs.status, "job_output": self.jobs.output, "cancel_job": self.jobs.cancel}.get(operation)
            if handler is None:
                raise BridgeError("job operation unavailable", code="operation_not_found", status=404)
            result = handler(payload)
        elif route == "/dev/git":
            result = self._git(str(payload.get("operation")), payload)
        elif route == "/dev/ric":
            result = self.inspector.dispatch(str(payload.get("operation")), payload)
        else:
            raise BridgeError("route unavailable", code="route_not_found", status=404)
        response = {"ok": True, "operation": payload.get("operation"), "result": _json_safe(result),
                    "duration_ms": round((time.monotonic() - started) * 1000)}
        if len(json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) > MAX_RESPONSE_BYTES:
            raise BridgeError("response exceeds aggregate limit", code="response_too_large", status=413)
        return response
