"""Falsification tests for the isolated RIC bridge control plane."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import uuid
from pathlib import Path

import pytest

from bridge_control.ric_bridge_control import (
    ControlConfig,
    ControlError,
    RepoWriter,
    request_audience,
)
from vivarium.dev_bridge_auth import GitHubOIDCVerifier, OIDCError, OIDCTrustPolicy


N_B64 = "qmQfV21aih-Ls5wpS17NfG_FQpA-TAB9ah8bV3HyQF4OdpgOKVSq4AAwPZ2VS5Rb0Tkf92f-bBHR22yZSqGxgcX515D5tM2W2MKFTcv5QEM5JmHU_dW1Snmt93obuVcGNy8cWWcUgy1aAWsa2ZQZJ1bM575SmglvzwaaQrgyy6PXWtUTp0YbhfsaI4fofvab4mNicmfI_5jbLN7AqlNs7d-UEELKnLOokkF-A7i02pqULJzmW2ELLPDkb22WGoIMBOBOK2KGlzpdX8HgLu0H2B_wQPUkTKYkagmX-5najhUZZpStcRGS7JUPl4W9HXWL7ScbUWkK-PJlpoDqa4Chvw"
E_B64 = "AQAB"
D = int("1798ce0e5982946651fe89bdde463ec6e0e3bc9825487938e51d71b7e67bda162c8298043e0d0facfdd9b06ec662352592100b314421a3edc3d6536fd73a154f178fc61eb9b62452a3aa2cb3dd6fa34aabfb78c8fa6e42311230d978fba5eb3b5d211517fc8286b81d22dd2656c37fc846e9119ef5e9872d08caad4a582010bb61895ef3eda8181bd2fa20393a7000eaf1d6c7be77ad4ad37d822a3e47c93a1b54c4ef04119153a8c766b29beb7c2b0e2faad83a13e0a2c4c016b9af6ef5ecb6fab8ae614b719e7eaa5b6586e155920756aef1a7ebe17a4d6917bbd3d7f257c11acebac5ca92e61070c120d36a1e5952f8db7f3e0847316dd18f28a13227a4c1", 16)
N = int.from_bytes(base64.urlsafe_b64decode(N_B64 + "=" * (-len(N_B64) % 4)), "big")
DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")
TRUSTED_SHA = "a" * 40
TRUSTED_REF = f"dcfharvey/RIC/.github/workflows/ric-dev-trusted.yml@{TRUSTED_SHA}"
NOW = 2_000_000_000


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _sign(claims: dict, *, kid: str = "test-key") -> str:
    header = {"alg": "RS256", "kid": kid, "typ": "JWT"}
    first = _b64(json.dumps(header, sort_keys=True, separators=(",", ":")).encode())
    second = _b64(json.dumps(claims, sort_keys=True, separators=(",", ":")).encode())
    signing_input = f"{first}.{second}".encode("ascii")
    digest_info = DIGEST_INFO + hashlib.sha256(signing_input).digest()
    size = (N.bit_length() + 7) // 8
    encoded = b"\x00\x01" + b"\xff" * (size - len(digest_info) - 3) + b"\x00" + digest_info
    signature = pow(int.from_bytes(encoded, "big"), D, N).to_bytes(size, "big")
    return f"{first}.{second}.{_b64(signature)}"


class _Response:
    def __init__(self, doc: dict):
        self.raw = json.dumps(doc).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, amount=-1):
        return self.raw if amount < 0 else self.raw[:amount]


def _urlopen(_request, timeout=10):
    assert timeout == 10
    return _Response({"keys": [{"kty": "RSA", "alg": "RS256", "kid": "test-key", "n": N_B64, "e": E_B64}]})


def _policy() -> OIDCTrustPolicy:
    return OIDCTrustPolicy(
        repository="dcfharvey/RIC",
        repository_id="1328282903",
        repository_owner_id="314814044",
        actor_id="314814044",
        job_workflow_ref=TRUSTED_REF,
        job_workflow_sha=TRUSTED_SHA,
        caller_ref="refs/heads/bridge/sol-rpc-v2",
        caller_workflow_ref="dcfharvey/RIC/.github/workflows/sol-rpc-oidc.yml@refs/heads/bridge/sol-rpc-v2",
        event_name="push",
    )


def _claims(audience: str, *, jti: str | None = None, workflow_sha: str = TRUSTED_SHA) -> dict:
    return {
        "iss": "https://token.actions.githubusercontent.com",
        "aud": audience,
        "repository": "dcfharvey/RIC",
        "repository_id": "1328282903",
        "repository_owner_id": "314814044",
        "actor_id": "314814044",
        "job_workflow_ref": f"dcfharvey/RIC/.github/workflows/ric-dev-trusted.yml@{workflow_sha}",
        "job_workflow_sha": workflow_sha,
        "ref": "refs/heads/bridge/sol-rpc-v2",
        "workflow_ref": "dcfharvey/RIC/.github/workflows/sol-rpc-oidc.yml@refs/heads/bridge/sol-rpc-v2",
        "event_name": "push",
        "repository_visibility": "private",
        "runner_environment": "github-hosted",
        "iat": NOW,
        "nbf": NOW - 30,
        "exp": NOW + 300,
        "jti": jti or uuid.uuid4().hex,
    }


def test_oidc_accepts_only_signed_pinned_request_bound_token():
    request_id = str(uuid.uuid4())
    body = b'{"operation":"status"}'
    audience = request_audience(request_id, "POST", "/dev/git", body)
    verifier = GitHubOIDCVerifier(_policy(), urlopen=_urlopen, clock=lambda: NOW)
    token = _sign(_claims(audience))

    claims = verifier.verify(token, expected_audience=audience)
    assert claims["job_workflow_sha"] == TRUSTED_SHA

    other = request_audience(request_id, "POST", "/dev/git", b'{"operation":"show"}')
    verifier2 = GitHubOIDCVerifier(_policy(), urlopen=_urlopen, clock=lambda: NOW)
    with pytest.raises(OIDCError, match="aud"):
        verifier2.verify(token, expected_audience=other)

    wrong_workflow = _sign(_claims(audience, workflow_sha="b" * 40))
    verifier3 = GitHubOIDCVerifier(_policy(), urlopen=_urlopen, clock=lambda: NOW)
    with pytest.raises(OIDCError, match="job_workflow_ref|job_workflow_sha"):
        verifier3.verify(wrong_workflow, expected_audience=audience)


def test_oidc_replay_tamper_and_time_windows_are_rejected():
    request_id = str(uuid.uuid4())
    audience = request_audience(request_id, "GET", "/health", b"")
    verifier = GitHubOIDCVerifier(_policy(), urlopen=_urlopen, clock=lambda: NOW)
    jti = uuid.uuid4().hex
    token = _sign(_claims(audience, jti=jti))
    verifier.verify(token, expected_audience=audience)
    with pytest.raises(OIDCError, match="replay"):
        verifier.verify(token, expected_audience=audience)

    broken = token[:-2] + ("AA" if token[-2:] != "AA" else "BB")
    verifier2 = GitHubOIDCVerifier(_policy(), urlopen=_urlopen, clock=lambda: NOW)
    with pytest.raises(OIDCError, match="signature"):
        verifier2.verify(broken, expected_audience=audience)

    expired = _claims(audience)
    expired.update({"iat": NOW - 900, "nbf": NOW - 900, "exp": NOW - 600})
    verifier3 = GitHubOIDCVerifier(_policy(), urlopen=_urlopen, clock=lambda: NOW)
    with pytest.raises(OIDCError):
        verifier3.verify(_sign(expired), expected_audience=audience)


def _config(root: Path) -> ControlConfig:
    return ControlConfig(
        workspace_root=root.resolve(),
        repository="dcfharvey/RIC",
        repository_id="1328282903",
        repository_owner_id="314814044",
        actor_id="314814044",
        trusted_workflow_ref=TRUSTED_REF,
        trusted_workflow_sha=TRUSTED_SHA,
        caller_ref="refs/heads/bridge/sol-rpc-v2",
        caller_workflow_ref="dcfharvey/RIC/.github/workflows/sol-rpc-oidc.yml@refs/heads/bridge/sol-rpc-v2",
        event_name="push",
        write_roots=("src", "tests", "tools", "docs"),
        write_files=("README.md", "pyproject.toml"),
        protected_paths=("src/vivarium/dev_bridge.py", "tools/ric_dev_gateway.py"),
        inner_port=8788,
        listen_port=8787,
    )


def _writer(tmp_path: Path) -> tuple[RepoWriter, Path]:
    root = tmp_path / "RIC"
    for folder in ("src/vivarium", "tests", "tools", "docs", "data"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    audit = tmp_path / "control_audit.jsonl"
    return RepoWriter(_config(root), audit), root


def test_repo_writer_is_cas_scoped_and_bridge_files_are_immutable(tmp_path):
    writer, root = _writer(tmp_path)
    target = root / "src" / "vivarium" / "feature.py"
    target.write_text("value = 1\n", encoding="utf-8")
    before = hashlib.sha256(target.read_bytes()).hexdigest()
    request_id = str(uuid.uuid4())

    result = writer.dispatch({"operation": "write_file", "path": "src/vivarium/feature.py",
                              "expected_sha256": before, "content": "value = 2\n"}, request_id=request_id)
    assert target.read_text(encoding="utf-8") == "value = 2\n"
    assert result["before_sha256"] == before
    assert result["after_sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()

    with pytest.raises(ControlError) as stale:
        writer.dispatch({"operation": "write_file", "path": "src/vivarium/feature.py",
                         "expected_sha256": before, "content": "value = 3\n"}, request_id=str(uuid.uuid4()))
    assert stale.value.code == "stale_file"

    for denied in ("data/world.sqlite", "src/vivarium/dev_bridge.py", "tools/ric_dev_gateway.py", "../escape.py"):
        with pytest.raises(ControlError):
            writer.dispatch({"operation": "create_file", "path": denied, "content": "x"}, request_id=str(uuid.uuid4()))

    records = [json.loads(line) for line in writer.audit_path.read_text(encoding="utf-8").splitlines()]
    assert records[-1]["request_id"] == request_id
    assert "content" not in records[-1]


def test_repo_writer_replace_is_unique_and_create_is_exclusive(tmp_path):
    writer, root = _writer(tmp_path)
    target = root / "docs" / "note.md"
    target.write_text("alpha beta gamma\n", encoding="utf-8")
    expected = hashlib.sha256(target.read_bytes()).hexdigest()
    writer.dispatch({"operation": "replace_text", "path": "docs/note.md", "expected_sha256": expected,
                     "old": "beta", "new": "delta"}, request_id=str(uuid.uuid4()))
    assert target.read_text(encoding="utf-8") == "alpha delta gamma\n"

    created = writer.dispatch({"operation": "create_file", "path": "tests/new_test.py", "content": "assert True\n"},
                              request_id=str(uuid.uuid4()))
    assert created["before_sha256"] is None
    with pytest.raises(ControlError) as duplicate:
        writer.dispatch({"operation": "create_file", "path": "tests/new_test.py", "content": "x"},
                        request_id=str(uuid.uuid4()))
    assert duplicate.value.code == "file_exists"

    repeated = root / "docs" / "repeat.md"
    repeated.write_text("x x\n", encoding="utf-8")
    repeated_hash = hashlib.sha256(repeated.read_bytes()).hexdigest()
    with pytest.raises(ControlError) as non_unique:
        writer.dispatch({"operation": "replace_text", "path": "docs/repeat.md", "expected_sha256": repeated_hash,
                         "old": "x", "new": "y"}, request_id=str(uuid.uuid4()))
    assert non_unique.value.code == "replace_not_unique"


def _make_directory_link(link: Path, target: Path) -> bool:
    try:
        link.symlink_to(target, target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        pass
    if os.name == "nt":
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                                capture_output=True, text=True, check=False)
        return result.returncode == 0 and link.exists()
    return False


def test_repo_writer_refuses_outbound_symlink_or_junction(tmp_path):
    writer, root = _writer(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "victim.py").write_text("untouched\n", encoding="utf-8")
    link = root / "src" / "linked"
    if not _make_directory_link(link, outside):
        pytest.skip("directory symlink/junction creation unavailable")
    with pytest.raises(ControlError) as denied:
        writer.dispatch({"operation": "write_file", "path": "src/linked/victim.py",
                         "expected_sha256": hashlib.sha256((outside / "victim.py").read_bytes()).hexdigest(),
                         "content": "changed\n"}, request_id=str(uuid.uuid4()))
    assert denied.value.code == "reparse_point_denied"
    assert (outside / "victim.py").read_text(encoding="utf-8") == "untouched\n"


def test_control_config_requires_immutable_workflow_ref(tmp_path):
    root = tmp_path / "RIC"
    root.mkdir()
    config = {
        "workspace_root": str(root),
        "repository": "dcfharvey/RIC",
        "repository_id": "1328282903",
        "repository_owner_id": "314814044",
        "actor_id": "314814044",
        "trusted_workflow_ref": "dcfharvey/RIC/.github/workflows/ric-dev-trusted.yml@refs/heads/main",
        "trusted_workflow_sha": "a" * 40,
        "caller_ref": "refs/heads/bridge/sol-rpc-v2",
        "caller_workflow_ref": "dcfharvey/RIC/.github/workflows/sol-rpc-oidc.yml@refs/heads/bridge/sol-rpc-v2",
        "event_name": "push",
        "write_roots": ["src"],
        "write_files": ["README.md"],
        "protected_paths": ["src/vivarium/dev_bridge.py"],
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ControlError, match="pinned"):
        ControlConfig.load(path)


def test_repo_writer_protected_paths_are_case_insensitive(tmp_path):
    writer, root = _writer(tmp_path)
    protected = root / "src" / "vivarium" / "dev_bridge.py"
    protected.write_text("LOCK = True\n", encoding="utf-8")
    before = protected.read_bytes()
    with pytest.raises(ControlError) as denied:
        writer.dispatch({"operation": "write_file", "path": "SRC/VIVARIUM/DEV_BRIDGE.PY",
                         "expected_sha256": hashlib.sha256(before).hexdigest(), "content": "LOCK = False\n"},
                        request_id=str(uuid.uuid4()))
    assert denied.value.code in {"protected_path", "file_missing", "path_outside_root"}
    assert protected.read_bytes() == before


def test_oidc_rejects_wrong_caller_branch_even_with_valid_trusted_workflow():
    request_id = str(uuid.uuid4())
    audience = request_audience(request_id, "GET", "/health", b"")
    claims = _claims(audience)
    claims["ref"] = "refs/heads/attacker"
    verifier = GitHubOIDCVerifier(_policy(), urlopen=_urlopen, clock=lambda: NOW)
    with pytest.raises(OIDCError, match="ref"):
        verifier.verify(_sign(claims), expected_audience=audience)
