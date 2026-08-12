"""Bounded Git write operations for the isolated RIC bridge control plane."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping


_BRANCH = re.compile(r"^chatgpt/[A-Za-z0-9][A-Za-z0-9._/-]{0,119}$")
_SECRET_ENV = re.compile(r"TOKEN|SECRET|PASSWORD|PRIVATE|CREDENTIAL|KEY", re.IGNORECASE)
MAX_GIT_OUTPUT = 256 * 1024
MAX_GIT_SECONDS = 90


class RepoGitError(ValueError):
    def __init__(self, message: str, *, code: str = "git_request_invalid", status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def _branch(value: Any) -> str:
    if not isinstance(value, str) or not _BRANCH.fullmatch(value):
        raise RepoGitError("branch must use the chatgpt/ namespace", code="branch_denied", status=403)
    if any(token in value for token in ("..", "//", "@{", "\\")) or value.endswith(("/", ".")):
        raise RepoGitError("branch name rejected", code="branch_denied", status=403)
    return value


class RepoGit:
    """Create, commit, and non-force-push only Sol-owned development branches."""

    def __init__(self, root: Path, validate_path: Callable[[Any], Path]) -> None:
        executable = shutil.which("git")
        if not executable:
            raise RepoGitError("git executable unavailable", code="git_unavailable", status=503)
        self.root = root.resolve()
        self.git = str(Path(executable).resolve())
        self.validate_path = validate_path

    def _env(self) -> dict[str, str]:
        return {
            key: value for key, value in os.environ.items()
            if not _SECRET_ENV.search(key)
            and not key.upper().startswith("GIT_CONFIG_")
            and key.upper() not in {"PYTHONPATH", "PYTHONHOME"}
        }

    def _run(self, args: list[str], *, timeout: int = MAX_GIT_SECONDS, ok: tuple[int, ...] = (0,)) -> dict[str, Any]:
        command = [
            self.git,
            "-c", f"core.hooksPath={os.devnull}",
            "-c", "commit.gpgsign=false",
            *args,
        ]
        try:
            process = subprocess.Popen(
                command,
                cwd=str(self.root),
                env=self._env(),
                shell=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            process.kill()
            stdout, stderr = process.communicate()
            raise RepoGitError("git command timed out", code="git_timeout", status=504) from exc
        except OSError as exc:
            raise RepoGitError("git command failed to start", code="git_unavailable", status=503) from exc
        out_truncated = len(stdout) > MAX_GIT_OUTPUT
        err_truncated = len(stderr) > MAX_GIT_OUTPUT
        out = stdout[:MAX_GIT_OUTPUT].decode("utf-8", errors="replace")
        err = stderr[:MAX_GIT_OUTPUT].decode("utf-8", errors="replace")
        result = {
            "exit_code": process.returncode,
            "stdout": out,
            "stderr": err,
            "truncated": out_truncated or err_truncated,
        }
        if process.returncode not in ok:
            raise RepoGitError("git command rejected or failed", code="git_failed", status=409)
        return result

    def _current_branch(self) -> str:
        result = self._run(["branch", "--show-current"])
        branch = result["stdout"].strip()
        return _branch(branch)

    def _tracked_dirty(self) -> bool:
        result = self._run(["status", "--porcelain=v1", "--untracked-files=no"])
        return bool(result["stdout"].strip())

    def _staged(self) -> list[str]:
        result = self._run(["diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"])
        return [item for item in result["stdout"].split("\x00") if item]

    def create_branch(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        name = _branch(payload.get("branch"))
        if self._tracked_dirty():
            raise RepoGitError("tracked workspace must be clean before branch creation", code="workspace_dirty", status=409)
        if self._staged():
            raise RepoGitError("index must be clean before branch creation", code="index_dirty", status=409)
        self._run(["switch", "-c", name, "--no-track"])
        return {"branch": name, "created": True}

    def commit(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        branch = self._current_branch()
        message = payload.get("message")
        if not isinstance(message, str) or not message.strip() or len(message) > 160 or "\n" in message or "\r" in message:
            raise RepoGitError("commit message invalid", code="commit_message_invalid")
        paths = payload.get("paths")
        if not isinstance(paths, list) or not paths or len(paths) > 64 or any(not isinstance(item, str) for item in paths):
            raise RepoGitError("commit paths invalid", code="commit_paths_invalid")
        if self._staged():
            raise RepoGitError("pre-existing staged changes denied", code="index_dirty", status=409)

        relative: list[str] = []
        for item in paths:
            path = self.validate_path(item)
            if not path.is_file():
                raise RepoGitError("commit path must be an existing file", code="commit_paths_invalid")
            rel = path.relative_to(self.root).as_posix()
            if rel not in relative:
                relative.append(rel)
        requested = set(relative)

        self._run(["add", "--", *relative])
        try:
            staged = set(self._staged())
            if not staged:
                raise RepoGitError("nothing changed in requested paths", code="nothing_to_commit", status=409)
            if not staged.issubset(requested):
                raise RepoGitError("staging escaped requested paths", code="staging_scope_violation", status=500)
            result = self._run([
                "-c", "user.name=RIC Sol Bridge",
                "-c", "user.email=ric-sol-bridge@localhost",
                "commit", "--no-verify", "-m", message.strip(), "--", *sorted(staged),
            ])
        except Exception:
            self._run(["restore", "--staged", "--", *relative], ok=(0, 1))
            raise
        head = self._run(["rev-parse", "HEAD"])["stdout"].strip()
        return {"branch": branch, "commit": head, "paths": sorted(staged), "stdout": result["stdout"]}

    def push(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        branch = self._current_branch()
        requested = payload.get("branch", branch)
        requested = _branch(requested)
        if requested != branch:
            raise RepoGitError("push branch must be current branch", code="branch_mismatch", status=409)
        result = self._run(["push", "--porcelain", "--set-upstream", "origin", f"HEAD:refs/heads/{branch}"], timeout=120)
        return {"branch": branch, "pushed": True, "stdout": result["stdout"], "stderr": result["stderr"]}

    def dispatch(self, operation: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        if operation == "create_branch":
            return self.create_branch(payload)
        if operation == "commit":
            return self.commit(payload)
        if operation == "push":
            return self.push(payload)
        raise RepoGitError("repository write operation unavailable", code="operation_not_found", status=404)
