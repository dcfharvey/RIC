"""Install the isolated RIC bridge control plane outside the mutable workspace.

No bearer/token is written to disk. The installer copies only audited control
files, writes a non-secret trust/config manifest, and refuses installation inside
the RIC workspace.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


TRUSTED_WORKFLOW_SHA = "bcf38918c0ed746bf3d9440b91b2e325b3860530"
TRUSTED_WORKFLOW_REF = (
    "dcfharvey/RIC/.github/workflows/ric-dev-trusted.yml@" + TRUSTED_WORKFLOW_SHA
)
CALLER_REF = "refs/heads/bridge/sol-rpc-v2"
CALLER_WORKFLOW_REF = (
    "dcfharvey/RIC/.github/workflows/sol-rpc-oidc.yml@refs/heads/bridge/sol-rpc-v2"
)
REPOSITORY = "dcfharvey/RIC"
REPOSITORY_ID = "1328282903"
REPOSITORY_OWNER_ID = "314814044"
ACTOR_ID = "314814044"

COPY_MAP = {
    "bridge_control/ric_bridge_control.py": "ric_bridge_control.py",
    "bridge_control/repo_git.py": "repo_git.py",
    "bridge_control/supervisor.py": "supervisor.py",
    "src/vivarium/dev_bridge_auth.py": "dev_bridge_auth.py",
}

PROTECTED_PATHS = [
    "src/vivarium/dev_bridge.py",
    "src/vivarium/dev_bridge_auth.py",
    "src/vivarium/dev_bridge_write.py",
    "tools/ric_dev_gateway.py",
    "tools/install_ric_bridge_control.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    head = result.stdout.strip().lower()
    if result.returncode != 0 or len(head) != 40 or any(ch not in "0123456789abcdef" for ch in head):
        raise SystemExit("installer requires a valid Git checkout")
    return head


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=r"C:\AI\Vivarium social")
    parser.add_argument("--install-dir", default=r"C:\AI\RIC Bridge Control")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    install_dir = Path(args.install_dir).expanduser().resolve()
    if not workspace.is_dir() or not (workspace / ".git").exists():
        raise SystemExit("workspace is not the RIC Git checkout")
    if install_dir == workspace or is_within(install_dir, workspace) or is_within(workspace, install_dir):
        raise SystemExit("install directory must be isolated from the RIC workspace")

    for source in COPY_MAP:
        path = workspace / source
        if not path.is_file():
            raise SystemExit(f"required source missing: {source}")

    if install_dir.exists() and any(install_dir.iterdir()) and not args.force:
        raise SystemExit("install directory is non-empty; use --force only after inspection")
    install_dir.mkdir(parents=True, exist_ok=True)

    if args.force:
        allowed_existing = {
            "ric_bridge_control.py", "repo_git.py", "supervisor.py", "dev_bridge_auth.py",
            "config.json", "manifest.json", "control_audit.jsonl",
        }
        unexpected = [item.name for item in install_dir.iterdir() if item.name not in allowed_existing]
        if unexpected:
            raise SystemExit(f"refusing to overwrite directory with unexpected files: {unexpected}")

    source_head = git_head(workspace)
    copied = {}
    for source, destination in COPY_MAP.items():
        source_path = workspace / source
        destination_path = install_dir / destination
        temporary = destination_path.with_suffix(destination_path.suffix + ".tmp")
        shutil.copyfile(source_path, temporary)
        os.replace(temporary, destination_path)
        copied[destination] = {
            "source": source,
            "sha256": sha256(destination_path),
            "bytes": destination_path.stat().st_size,
        }

    config = {
        "workspace_root": str(workspace),
        "repository": REPOSITORY,
        "repository_id": REPOSITORY_ID,
        "repository_owner_id": REPOSITORY_OWNER_ID,
        "actor_id": ACTOR_ID,
        "trusted_workflow_ref": TRUSTED_WORKFLOW_REF,
        "trusted_workflow_sha": TRUSTED_WORKFLOW_SHA,
        "caller_ref": CALLER_REF,
        "caller_workflow_ref": CALLER_WORKFLOW_REF,
        "event_name": "push",
        "write_roots": ["src", "tests", "tools", "docs"],
        "write_files": ["README.md", "CHANGELOG.md", "pyproject.toml"],
        "protected_paths": PROTECTED_PATHS,
        "listen_port": 8787,
        "inner_port": 8788,
    }
    config_raw = json.dumps(config, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    config_path = install_dir / "config.json"
    config_path.write_text(config_raw, encoding="utf-8")

    manifest = {
        "schema_version": 1,
        "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "workspace_root": str(workspace),
        "source_head": source_head,
        "trusted_workflow_sha": TRUSTED_WORKFLOW_SHA,
        "caller_ref": CALLER_REF,
        "files": copied,
        "config_sha256": sha256(config_path),
        "secrets_persisted": False,
    }
    (install_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"RIC bridge control installed to {install_dir}")
    print(f"source HEAD: {source_head}")
    print("No bearer/token persisted. Start supervisor with RIC_GATEWAY_TOKEN in process environment.")


if __name__ == "__main__":
    main()
