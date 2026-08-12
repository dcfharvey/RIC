from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: refusing ambiguous transform, count={count}")
    return text.replace(old, new, 1)


repo_path = Path("bridge_control/repo_git.py")
text = repo_path.read_text(encoding="utf-8")
text = replace_once(
    text,
    '                "commit", "--no-verify", "-m", message.strip(),\n            ])\n',
    '                "commit", "--no-verify", "-m", message.strip(), "--only", "--", *sorted(staged),\n            ])\n',
    "git commit exact paths",
)
repo_path.write_text(text, encoding="utf-8")


test_path = Path("tests/test_bridge_repo_git.py")
test = test_path.read_text(encoding="utf-8")
if "test_repo_git_commit_does_not_capture_concurrently_staged_outsider" in test:
    raise SystemExit("concurrent staging falsification already present")
test += '''\n\ndef test_repo_git_commit_does_not_capture_concurrently_staged_outsider(tmp_path):\n    repo, root, _remote = _repo(tmp_path)\n    repo.create_branch({"branch": "chatgpt/concurrent-stage"})\n    requested = root / "src" / "requested.py"\n    requested.write_text("REQUESTED = True\\n", encoding="utf-8")\n    outsider = root / "tests" / "outsider.py"\n    outsider.write_text("OUTSIDER = True\\n", encoding="utf-8")\n\n    original_run = repo._run\n    injected = False\n\n    def wrapped(args, *, timeout=90, ok=(0,)):\n        nonlocal injected\n        if "commit" in args and not injected:\n            injected = True\n            _run(root, "add", "tests/outsider.py")\n        return original_run(args, timeout=timeout, ok=ok)\n\n    repo._run = wrapped\n    result = repo.commit({"message": "feat: requested only", "paths": ["src/requested.py"]})\n    assert result["paths"] == ["src/requested.py"]\n    names = _run(root, "show", "--pretty=format:", "--name-only", "HEAD").splitlines()\n    assert "src/requested.py" in names\n    assert "tests/outsider.py" not in names\n    assert _run(root, "diff", "--cached", "--name-only") == "tests/outsider.py"\n'''
test_path.write_text(test, encoding="utf-8")
