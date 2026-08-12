"""Falsification tests for bounded Git writes in the isolated control plane."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from bridge_control.repo_git import RepoGit, RepoGitError


def _run(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _repo(tmp_path: Path) -> tuple[RepoGit, Path, Path]:
    root = tmp_path / "RIC"
    root.mkdir()
    _run(root, "init", "-b", "main")
    _run(root, "config", "user.name", "fixture")
    _run(root, "config", "user.email", "fixture@example.invalid")
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "src" / "base.py").write_text("BASE = True\n", encoding="utf-8")
    _run(root, "add", "src/base.py")
    _run(root, "commit", "-m", "baseline")

    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], capture_output=True, text=True, check=True)
    _run(root, "remote", "add", "origin", str(remote))

    def validate(value):
        if not isinstance(value, str):
            raise ValueError("bad path")
        candidate = (root / value).resolve()
        candidate.relative_to(root.resolve())
        if candidate.parts[-2] not in {"src", "tests"}:
            raise ValueError("outside scope")
        return candidate

    return RepoGit(root, validate), root, remote


def test_repo_git_creates_commits_and_nonforce_pushes_only_chatgpt_branch(tmp_path):
    repo, root, remote = _repo(tmp_path)

    with pytest.raises(RepoGitError) as denied:
        repo.create_branch({"branch": "main"})
    assert denied.value.code == "branch_denied"

    created = repo.create_branch({"branch": "chatgpt/bridge-fixture"})
    assert created["branch"] == "chatgpt/bridge-fixture"

    target = root / "src" / "feature.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    committed = repo.commit({"message": "feat: fixture", "paths": ["src/feature.py"]})
    assert committed["branch"] == "chatgpt/bridge-fixture"
    assert committed["paths"] == ["src/feature.py"]
    assert len(committed["commit"]) == 40

    pushed = repo.push({})
    assert pushed["pushed"] is True
    remote_head = subprocess.run(
        ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/chatgpt/bridge-fixture"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert remote_head == committed["commit"]


def test_repo_git_refuses_dirty_branch_creation_and_preexisting_stage(tmp_path):
    repo, root, _remote = _repo(tmp_path)
    (root / "src" / "base.py").write_text("BASE = False\n", encoding="utf-8")
    with pytest.raises(RepoGitError) as dirty:
        repo.create_branch({"branch": "chatgpt/dirty"})
    assert dirty.value.code == "workspace_dirty"

    _run(root, "restore", "src/base.py")
    repo.create_branch({"branch": "chatgpt/index-test"})
    staged = root / "tests" / "staged.py"
    staged.write_text("assert True\n", encoding="utf-8")
    _run(root, "add", "tests/staged.py")
    other = root / "src" / "other.py"
    other.write_text("OTHER = 1\n", encoding="utf-8")
    with pytest.raises(RepoGitError) as index:
        repo.commit({"message": "feat: no", "paths": ["src/other.py"]})
    assert index.value.code == "index_dirty"


def test_repo_git_never_accepts_other_branch_names_or_branch_mismatch(tmp_path):
    repo, root, _remote = _repo(tmp_path)
    repo.create_branch({"branch": "chatgpt/safe"})
    (root / "src" / "feature.py").write_text("VALUE = 2\n", encoding="utf-8")
    repo.commit({"message": "feat: safe", "paths": ["src/feature.py"]})

    for name in ("main", "integration/foo", "chatgpt/../main", "chatgpt/a//b", "chatgpt/x@{y"):
        with pytest.raises(RepoGitError):
            repo.push({"branch": name})

    with pytest.raises(RepoGitError) as mismatch:
        repo.push({"branch": "chatgpt/other"})
    assert mismatch.value.code == "branch_mismatch"
