from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: refusing ambiguous transform, count={count}")
    return text.replace(old, new, 1)


# --- OIDC verifier: strict base64url/JWK usage + exact caller scope. ---
auth_path = Path("src/vivarium/dev_bridge_auth.py")
auth = auth_path.read_text(encoding="utf-8")
auth = replace_once(auth, "import json\nimport threading\n", "import json\nimport re\nimport threading\n", "auth import")
auth = replace_once(
    auth,
    'JWKS_URI = "https://token.actions.githubusercontent.com/.well-known/jwks"\n_RSA_SHA256_DIGEST_INFO_PREFIX',
    'JWKS_URI = "https://token.actions.githubusercontent.com/.well-known/jwks"\n_B64URL = re.compile(r"^[A-Za-z0-9_-]+$")\n_RSA_SHA256_DIGEST_INFO_PREFIX',
    "auth b64 regex",
)
auth = replace_once(
    auth,
    '    if not isinstance(value, str) or not value:\n        raise OIDCError("invalid base64url field")\n    try:\n        return base64.urlsafe_b64decode',
    '    if not isinstance(value, str) or not value or not _B64URL.fullmatch(value):\n        raise OIDCError("invalid base64url field")\n    try:\n        return base64.urlsafe_b64decode',
    "auth strict b64",
)
auth = replace_once(
    auth,
    '    if jwk.get("alg") not in {None, "RS256"}:\n        return False\n',
    '    if jwk.get("alg") not in {None, "RS256"} or jwk.get("use") not in {None, "sig"}:\n        return False\n',
    "auth jwk use",
)
auth = replace_once(
    auth,
    '    job_workflow_ref: str\n    job_workflow_sha: str\n    actor_id: str | None = None\n',
    '    job_workflow_ref: str\n    job_workflow_sha: str\n    caller_ref: str\n    caller_workflow_ref: str\n    event_name: str\n    repository_visibility: str = "private"\n    actor_id: str | None = None\n',
    "auth caller policy",
)
auth = replace_once(
    auth,
    '            "job_workflow_sha": policy.job_workflow_sha,\n            "runner_environment": policy.runner_environment,\n',
    '            "job_workflow_sha": policy.job_workflow_sha,\n            "ref": policy.caller_ref,\n            "workflow_ref": policy.caller_workflow_ref,\n            "event_name": policy.event_name,\n            "repository_visibility": policy.repository_visibility,\n            "runner_environment": policy.runner_environment,\n',
    "auth exact caller claims",
)
auth_path.write_text(auth, encoding="utf-8")


# --- Control plane: normalized protected paths + exact caller config + bounded Git writes. ---
control_path = Path("bridge_control/ric_bridge_control.py")
control = control_path.read_text(encoding="utf-8")
control = replace_once(
    control,
    'except ImportError:  # Repository test/import path.\n    from vivarium.dev_bridge_auth import GitHubOIDCVerifier, OIDCError, OIDCTrustPolicy\n',
    'except ImportError:  # Repository test/import path.\n    from vivarium.dev_bridge_auth import GitHubOIDCVerifier, OIDCError, OIDCTrustPolicy\n\ntry:  # Installed pinned copy.\n    from repo_git import RepoGit, RepoGitError\nexcept ImportError:  # Repository test/import path.\n    from bridge_control.repo_git import RepoGit, RepoGitError\n',
    "control repo git import",
)
control = replace_once(
    'WRITE_ROUTE = "/dev/write"\n',
    'WRITE_ROUTE = "/dev/write"\nREPO_ROUTE = "/dev/repo"\n',
    "control repo route",
)
control = replace_once(
    '    trusted_workflow_ref: str\n    trusted_workflow_sha: str\n    write_roots: tuple[str, ...]\n',
    '    trusted_workflow_ref: str\n    trusted_workflow_sha: str\n    caller_ref: str\n    caller_workflow_ref: str\n    event_name: str\n    write_roots: tuple[str, ...]\n',
    "control config caller fields",
)
control = replace_once(
    '            trusted_workflow_ref=workflow_ref,\n            trusted_workflow_sha=workflow_sha,\n            write_roots=string_list',
    '            trusted_workflow_ref=workflow_ref,\n            trusted_workflow_sha=workflow_sha,\n            caller_ref=required_string("caller_ref"),\n            caller_workflow_ref=required_string("caller_workflow_ref"),\n            event_name=required_string("event_name"),\n            write_roots=string_list',
    "control config load caller",
)
control = replace_once(
    '        self._write_roots = set(config.write_roots)\n        self._write_files = {Path(item).as_posix() for item in config.write_files}\n        self._protected = {Path(item).as_posix() for item in config.protected_paths}\n',
    '        self._write_roots = {item.casefold() for item in config.write_roots}\n        self._write_files = {Path(item).as_posix().casefold() for item in config.write_files}\n        self._protected = {Path(item).as_posix().casefold() for item in config.protected_paths}\n        self._protected_existing = [self.root / item for item in config.protected_paths]\n',
    "control normalized sets",
)
control = replace_once(
    '        relative = lexical.as_posix()\n        if relative in self._protected:\n',
    '        relative = lexical.as_posix()\n        relative_key = relative.casefold()\n        if relative_key in self._protected:\n',
    "control protected casefold",
)
control = replace_once(
    '        if lexical.parts[0] not in self._write_roots and relative not in self._write_files:\n',
    '        if lexical.parts[0].casefold() not in self._write_roots and relative_key not in self._write_files:\n',
    "control scope casefold",
)
control = replace_once(
    '        if target.exists() and not target.is_file():\n            raise ControlError("target is not a regular file", code="invalid_path")\n        return target\n',
    '        if target.exists() and not target.is_file():\n            raise ControlError("target is not a regular file", code="invalid_path")\n        try:\n            canonical_key = target.relative_to(self.root).as_posix().casefold()\n        except ValueError as exc:\n            raise ControlError("path escapes workspace", code="path_outside_root", status=403) from exc\n        if canonical_key in self._protected:\n            raise ControlError("bridge security boundary is immutable", code="protected_path", status=403)\n        if target.exists():\n            for protected in self._protected_existing:\n                try:\n                    if protected.exists() and os.path.samefile(target, protected):\n                        raise ControlError("bridge security boundary is immutable", code="protected_path", status=403)\n                except OSError:\n                    continue\n        return target\n',
    "control canonical protected",
)
control = replace_once(
    '        self.writer = RepoWriter(config, install_dir / "control_audit.jsonl")\n        policy = OIDCTrustPolicy(\n',
    '        self.writer = RepoWriter(config, install_dir / "control_audit.jsonl")\n        self.repo_git = RepoGit(config.workspace_root, lambda value: self.writer._path(value, must_exist=True))\n        policy = OIDCTrustPolicy(\n',
    "control repo git init",
)
control = replace_once(
    '            job_workflow_ref=config.trusted_workflow_ref,\n            job_workflow_sha=config.trusted_workflow_sha,\n        )\n',
    '            job_workflow_ref=config.trusted_workflow_ref,\n            job_workflow_sha=config.trusted_workflow_sha,\n            caller_ref=config.caller_ref,\n            caller_workflow_ref=config.caller_workflow_ref,\n            event_name=config.event_name,\n        )\n',
    "control policy caller",
)
control = replace_once(
    '        permissions["REPO_WRITE"] = "ALLOW_OIDC_CAS"\n',
    '        permissions["REPO_WRITE"] = "ALLOW_OIDC_CAS_GIT"\n',
    "control capability permission",
)
control = replace_once(
    '        tools["repo_write"] = {\n            "permission": "REPO_WRITE",\n            "operations": ["write_file", "replace_text", "create_file"],\n',
    '        tools["repo_write"] = {\n            "permission": "REPO_WRITE",\n            "operations": ["write_file", "replace_text", "create_file"],\n',
    "control repo write anchor",
)
control = replace_once(
    '        result["tools"] = tools\n        return result\n',
    '        tools["repo_git"] = {\n            "permission": "REPO_WRITE",\n            "operations": ["create_branch", "commit", "push"],\n            "branch_namespace": "chatgpt/",\n            "force_push": False,\n            "merge_reset_clean_delete": False,\n        }\n        result["tools"] = tools\n        return result\n',
    "control repo git capability",
)
control = replace_once(
    '        if route not in READ_POST_ROUTES and route != WRITE_ROUTE:\n',
    '        if route not in READ_POST_ROUTES and route not in {WRITE_ROUTE, REPO_ROUTE}:\n',
    "control route acceptance",
)
control = replace_once(
    '            if route == WRITE_ROUTE:\n                try:\n',
    '            if route == WRITE_ROUTE:\n                try:\n',
    "control write anchor",
)
control = replace_once(
    '                result = self.server.writer.dispatch(payload, request_id=request_id)\n                self._json(200, {"ok": True, "operation": payload.get("operation"), "result": result,\n                                 "duration_ms": round((time.monotonic() - started) * 1000)})\n            else:\n                status, raw, content_type = self.server.proxy_inner("POST", route, body)\n',
    '                result = self.server.writer.dispatch(payload, request_id=request_id)\n                self._json(200, {"ok": True, "operation": payload.get("operation"), "result": result,\n                                 "duration_ms": round((time.monotonic() - started) * 1000)})\n            elif route == REPO_ROUTE:\n                try:\n                    payload = json.loads(body.decode("utf-8")) if body else {}\n                except (UnicodeDecodeError, json.JSONDecodeError) as exc:\n                    raise ControlError("invalid JSON", code="invalid_json") from exc\n                if not isinstance(payload, Mapping):\n                    raise ControlError("JSON object required", code="invalid_json")\n                started = time.monotonic()\n                result = self.server.repo_git.dispatch(str(payload.get("operation")), payload)\n                self._json(200, {"ok": True, "operation": payload.get("operation"), "result": result,\n                                 "duration_ms": round((time.monotonic() - started) * 1000)})\n            else:\n                status, raw, content_type = self.server.proxy_inner("POST", route, body)\n',
    "control repo route dispatch",
)
control = replace_once(
    '        except ControlError as exc:\n            self._json(exc.status, {"ok": False, "error": {"code": exc.code, "message": str(exc)}})\n        except Exception:\n',
    '        except (ControlError, RepoGitError) as exc:\n            self._json(exc.status, {"ok": False, "error": {"code": exc.code, "message": str(exc)}})\n        except Exception:\n',
    "control post exception",
)
control_path.write_text(control, encoding="utf-8")


# --- Tests: exact caller policy/config and Windows case-insensitive protection. ---
test_path = Path("tests/test_dev_bridge_control.py")
test = test_path.read_text(encoding="utf-8")
test = replace_once(
    test,
    '        job_workflow_ref=TRUSTED_REF,\n        job_workflow_sha=TRUSTED_SHA,\n    )\n',
    '        job_workflow_ref=TRUSTED_REF,\n        job_workflow_sha=TRUSTED_SHA,\n        caller_ref="refs/heads/bridge/sol-rpc-v2",\n        caller_workflow_ref="dcfharvey/RIC/.github/workflows/sol-rpc-oidc.yml@refs/heads/bridge/sol-rpc-v2",\n        event_name="push",\n    )\n',
    "test policy caller",
)
test = replace_once(
    '        "runner_environment": "github-hosted",\n',
    '        "ref": "refs/heads/bridge/sol-rpc-v2",\n        "workflow_ref": "dcfharvey/RIC/.github/workflows/sol-rpc-oidc.yml@refs/heads/bridge/sol-rpc-v2",\n        "event_name": "push",\n        "repository_visibility": "private",\n        "runner_environment": "github-hosted",\n',
    "test caller claims",
)
test = replace_once(
    '        trusted_workflow_ref=TRUSTED_REF,\n        trusted_workflow_sha=TRUSTED_SHA,\n        write_roots=',
    '        trusted_workflow_ref=TRUSTED_REF,\n        trusted_workflow_sha=TRUSTED_SHA,\n        caller_ref="refs/heads/bridge/sol-rpc-v2",\n        caller_workflow_ref="dcfharvey/RIC/.github/workflows/sol-rpc-oidc.yml@refs/heads/bridge/sol-rpc-v2",\n        event_name="push",\n        write_roots=',
    "test config object caller",
)
test = replace_once(
    '        "trusted_workflow_sha": "a" * 40,\n        "write_roots": ["src"],\n',
    '        "trusted_workflow_sha": "a" * 40,\n        "caller_ref": "refs/heads/bridge/sol-rpc-v2",\n        "caller_workflow_ref": "dcfharvey/RIC/.github/workflows/sol-rpc-oidc.yml@refs/heads/bridge/sol-rpc-v2",\n        "event_name": "push",\n        "write_roots": ["src"],\n',
    "test config json caller",
)
append = '''\n\ndef test_repo_writer_protected_paths_are_case_insensitive(tmp_path):\n    writer, root = _writer(tmp_path)\n    protected = root / "src" / "vivarium" / "dev_bridge.py"\n    protected.write_text("LOCK = True\\n", encoding="utf-8")\n    before = protected.read_bytes()\n    with pytest.raises(ControlError) as denied:\n        writer.dispatch({"operation": "write_file", "path": "SRC/VIVARIUM/DEV_BRIDGE.PY",\n                         "expected_sha256": hashlib.sha256(before).hexdigest(), "content": "LOCK = False\\n"},\n                        request_id=str(uuid.uuid4()))\n    assert denied.value.code in {"protected_path", "file_missing"}\n    assert protected.read_bytes() == before\n\n\ndef test_oidc_rejects_wrong_caller_branch_even_with_valid_trusted_workflow():\n    request_id = str(uuid.uuid4())\n    audience = request_audience(request_id, "GET", "/health", b"")\n    claims = _claims(audience)\n    claims["ref"] = "refs/heads/attacker"\n    verifier = GitHubOIDCVerifier(_policy(), urlopen=_urlopen, clock=lambda: NOW)\n    with pytest.raises(OIDCError, match="ref"):\n        verifier.verify(_sign(claims), expected_audience=audience)\n'''
if "test_repo_writer_protected_paths_are_case_insensitive" in test:
    raise SystemExit("hardening tests already appended")
test += append
test_path.write_text(test, encoding="utf-8")
