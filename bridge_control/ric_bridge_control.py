"""Isolated OIDC-authenticated control plane for the RIC development bridge.

This service is intended to run from a pinned copy OUTSIDE the mutable RIC
workspace. It imports no RIC runtime module. GitHub Actions authenticates with a
short-lived OIDC token emitted from one immutable reusable workflow. Every token
is additionally bound to the exact HTTP request through its audience claim.

The control plane directly owns only bounded repository text writes. Existing
READ/TEST_EXEC/LM operations are proxied over loopback to the lower-trust Phase A
gateway using a bearer token that never leaves the local machine.
"""

from __future__ import annotations

import hashlib
import hmac
import http.client
import json
import os
import re
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

try:  # Installed pinned copy.
    from dev_bridge_auth import GitHubOIDCVerifier, OIDCError, OIDCTrustPolicy
except ImportError:  # Repository test/import path.
    from vivarium.dev_bridge_auth import GitHubOIDCVerifier, OIDCError, OIDCTrustPolicy


LISTEN_HOST = "127.0.0.1"
DEFAULT_LISTEN_PORT = 8788
INNER_HOST = "127.0.0.1"
DEFAULT_INNER_PORT = 8787
MAX_BODY_BYTES = 192 * 1024
MAX_RESPONSE_BYTES = 300 * 1024
MAX_WRITE_BYTES = 128 * 1024

READ_GET_ROUTES = {"/health", "/capabilities", "/v1/models"}
READ_POST_ROUTES = {
    "/dev/fs",
    "/dev/exec",
    "/dev/jobs",
    "/dev/git",
    "/dev/ric",
    "/v1/chat/completions",
    "/v1/responses",
}
WRITE_ROUTE = "/dev/write"

_SECRET_NAME = re.compile(
    r"(^|[._-])(env|secret|secrets|token|tokens|password|credential|credentials|private|key)([._-]|$)",
    re.IGNORECASE,
)
_SECRET_EXTENSIONS = {".pem", ".key", ".p12", ".pfx", ".secret"}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")

DEFAULT_WRITE_ROOTS = ("src", "tests", "tools", "docs")
DEFAULT_WRITE_FILES = ("README.md", "CHANGELOG.md", "pyproject.toml")
DEFAULT_PROTECTED_PATHS = (
    "src/vivarium/dev_bridge.py",
    "src/vivarium/dev_bridge_auth.py",
    "src/vivarium/dev_bridge_write.py",
    "tools/ric_dev_gateway.py",
    "tools/install_ric_bridge_control.py",
)


class ControlError(ValueError):
    def __init__(self, message: str, *, code: str = "invalid_request", status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def request_audience(request_id: str, method: str, route: str, body: bytes) -> str:
    try:
        parsed = uuid.UUID(request_id)
    except (ValueError, AttributeError) as exc:
        raise ControlError("request id must be UUID4", code="invalid_request_id") from exc
    if parsed.version != 4:
        raise ControlError("request id must be UUID4", code="invalid_request_id")
    method = method.upper()
    if method not in {"GET", "POST"} or not route.startswith("/") or "?" in route or "#" in route:
        raise ControlError("request binding input invalid", code="invalid_request_binding")
    digest = hashlib.sha256(method.encode("ascii") + b"\n" + route.encode("utf-8") + b"\n" + body).hexdigest()
    return f"ric-dev-bridge:v1:{request_id}:{digest}"


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _is_link_like(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        return bool(is_junction and is_junction())
    except OSError:
        return True


@dataclass(frozen=True)
class ControlConfig:
    workspace_root: Path
    repository: str
    repository_id: str
    repository_owner_id: str
    actor_id: str
    trusted_workflow_ref: str
    trusted_workflow_sha: str
    write_roots: tuple[str, ...]
    write_files: tuple[str, ...]
    protected_paths: tuple[str, ...]
    inner_port: int = DEFAULT_INNER_PORT
    listen_port: int = DEFAULT_LISTEN_PORT

    @classmethod
    def load(cls, path: Path) -> "ControlConfig":
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ControlError("control config cannot be read", code="config_invalid", status=500) from exc
        if not isinstance(doc, Mapping):
            raise ControlError("control config must be object", code="config_invalid", status=500)

        def required_string(name: str) -> str:
            value = doc.get(name)
            if not isinstance(value, str) or not value:
                raise ControlError(f"config field missing: {name}", code="config_invalid", status=500)
            return value

        root = Path(required_string("workspace_root")).expanduser().resolve()
        if not root.is_dir():
            raise ControlError("workspace root absent", code="config_invalid", status=500)
        workflow_sha = required_string("trusted_workflow_sha").lower()
        if not _GIT_COMMIT_SHA.fullmatch(workflow_sha):
            raise ControlError("trusted workflow SHA invalid", code="config_invalid", status=500)
        workflow_ref = required_string("trusted_workflow_ref")
        if not workflow_ref.endswith("@" + workflow_sha):
            raise ControlError("trusted workflow ref must be pinned to trusted SHA", code="config_invalid", status=500)

        def string_list(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
            value = doc.get(name, list(default))
            if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
                raise ControlError(f"config list invalid: {name}", code="config_invalid", status=500)
            return tuple(value)

        try:
            inner_port = int(doc.get("inner_port", DEFAULT_INNER_PORT))
            listen_port = int(doc.get("listen_port", DEFAULT_LISTEN_PORT))
        except (TypeError, ValueError) as exc:
            raise ControlError("control ports invalid", code="config_invalid", status=500) from exc
        if not (1024 <= inner_port <= 65535 and 1024 <= listen_port <= 65535 and inner_port != listen_port):
            raise ControlError("control ports invalid", code="config_invalid", status=500)

        return cls(
            workspace_root=root,
            repository=required_string("repository"),
            repository_id=required_string("repository_id"),
            repository_owner_id=required_string("repository_owner_id"),
            actor_id=required_string("actor_id"),
            trusted_workflow_ref=workflow_ref,
            trusted_workflow_sha=workflow_sha,
            write_roots=string_list("write_roots", DEFAULT_WRITE_ROOTS),
            write_files=string_list("write_files", DEFAULT_WRITE_FILES),
            protected_paths=string_list("protected_paths", DEFAULT_PROTECTED_PATHS),
            inner_port=inner_port,
            listen_port=listen_port,
        )


class RepoWriter:
    """CAS-style text writer limited to explicitly approved repository roots."""

    def __init__(self, config: ControlConfig, audit_path: Path) -> None:
        self.config = config
        self.root = config.workspace_root
        self.audit_path = audit_path
        self._audit_lock = threading.Lock()
        self._write_roots = set(config.write_roots)
        self._write_files = {Path(item).as_posix() for item in config.write_files}
        self._protected = {Path(item).as_posix() for item in config.protected_paths}

    def _path(self, value: Any, *, must_exist: bool | None = None) -> Path:
        if not isinstance(value, str) or not value or "\x00" in value:
            raise ControlError("path must be a non-empty string", code="invalid_path")
        lexical = Path(value)
        if lexical.is_absolute() or any(part in {"", ".", ".."} for part in lexical.parts):
            raise ControlError("absolute/traversal paths forbidden", code="path_outside_root", status=403)
        relative = lexical.as_posix()
        if relative in self._protected:
            raise ControlError("bridge security boundary is immutable", code="protected_path", status=403)
        if any(_SECRET_NAME.search(part) for part in lexical.parts) or lexical.suffix.lower() in _SECRET_EXTENSIONS:
            raise ControlError("sensitive paths are denied", code="sensitive_path_denied", status=403)
        if lexical.parts[0] not in self._write_roots and relative not in self._write_files:
            raise ControlError("path outside repository write scope", code="write_scope_denied", status=403)

        current = self.root
        for part in lexical.parts:
            current = current / part
            if (current.exists() or current.is_symlink()) and _is_link_like(current):
                raise ControlError("symlink/junction path denied", code="reparse_point_denied", status=403)
        try:
            parent = current.parent.resolve(strict=True)
            parent.relative_to(self.root)
        except (OSError, ValueError) as exc:
            raise ControlError("path parent escapes workspace", code="path_outside_root", status=403) from exc
        if not parent.is_dir():
            raise ControlError("path parent is not directory", code="invalid_path")
        target = parent / current.name
        try:
            target.resolve(strict=False).relative_to(self.root)
        except ValueError as exc:
            raise ControlError("path escapes workspace", code="path_outside_root", status=403) from exc
        if must_exist is True and not target.is_file():
            raise ControlError("target file missing", code="file_missing", status=404)
        if must_exist is False and target.exists():
            raise ControlError("target already exists", code="file_exists", status=409)
        if target.exists() and not target.is_file():
            raise ControlError("target is not a regular file", code="invalid_path")
        return target

    def _content(self, value: Any) -> bytes:
        if not isinstance(value, str) or "\x00" in value:
            raise ControlError("content must be UTF-8 text", code="invalid_content")
        raw = value.encode("utf-8")
        if len(raw) > MAX_WRITE_BYTES:
            raise ControlError("write exceeds byte limit", code="write_too_large", status=413)
        return raw

    def _expected(self, value: Any) -> str:
        if not isinstance(value, str) or not _SHA256.fullmatch(value.lower()):
            raise ControlError("expected_sha256 required", code="expected_hash_required")
        return value.lower()

    def _read_current(self, target: Path, expected: str) -> bytes:
        try:
            raw = target.read_bytes()
        except OSError as exc:
            raise ControlError("target cannot be read", code="filesystem_error", status=500) from exc
        if len(raw) > MAX_WRITE_BYTES:
            raise ControlError("target exceeds write byte limit", code="write_too_large", status=413)
        actual = _sha256(raw)
        if actual != expected:
            raise ControlError("stale file hash", code="stale_file", status=409)
        return raw

    def _atomic_replace(self, target: Path, raw: bytes) -> None:
        temporary = target.with_name(f".{target.name}.ric-write-{uuid.uuid4().hex}.tmp")
        try:
            with temporary.open("xb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            if _is_link_like(target):
                raise ControlError("target became a reparse point", code="reparse_point_denied", status=403)
            os.replace(temporary, target)
        except ControlError:
            try:
                temporary.unlink(missing_ok=True)
            finally:
                raise
        except OSError as exc:
            try:
                temporary.unlink(missing_ok=True)
            finally:
                raise ControlError("atomic write failed", code="filesystem_error", status=500) from exc

    def _create_exclusive(self, target: Path, raw: bytes) -> None:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(target, flags, 0o644)
        except FileExistsError as exc:
            raise ControlError("target already exists", code="file_exists", status=409) from exc
        except OSError as exc:
            raise ControlError("file creation failed", code="filesystem_error", status=500) from exc
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            try:
                target.unlink(missing_ok=True)
            finally:
                raise

    def _audit(self, request_id: str, operation: str, path: Path, before: str | None, after: str) -> None:
        record = {
            "at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "request_id": request_id,
            "operation": operation,
            "path": path.relative_to(self.root).as_posix(),
            "before_sha256": before,
            "after_sha256": after,
        }
        try:
            with self._audit_lock:
                with self.audit_path.open("a", encoding="utf-8", newline="\n") as handle:
                    handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        except OSError:
            # The write already happened; never lie by converting success into an apparent rollback.
            pass

    def dispatch(self, payload: Mapping[str, Any], *, request_id: str) -> dict[str, Any]:
        operation = payload.get("operation")
        if operation == "write_file":
            target = self._path(payload.get("path"), must_exist=True)
            expected = self._expected(payload.get("expected_sha256"))
            self._read_current(target, expected)
            raw = self._content(payload.get("content"))
            self._atomic_replace(target, raw)
            after = _sha256(raw)
            self._audit(request_id, operation, target, expected, after)
            return {"path": target.relative_to(self.root).as_posix(), "before_sha256": expected,
                    "after_sha256": after, "bytes": len(raw)}

        if operation == "replace_text":
            target = self._path(payload.get("path"), must_exist=True)
            expected = self._expected(payload.get("expected_sha256"))
            current = self._read_current(target, expected)
            try:
                text = current.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ControlError("target is not UTF-8 text", code="text_only") from exc
            old = payload.get("old")
            new = payload.get("new")
            if not isinstance(old, str) or not old or not isinstance(new, str) or "\x00" in old or "\x00" in new:
                raise ControlError("replace_text requires bounded text", code="invalid_content")
            if len(old.encode("utf-8")) > MAX_WRITE_BYTES or len(new.encode("utf-8")) > MAX_WRITE_BYTES:
                raise ControlError("replacement exceeds byte limit", code="write_too_large", status=413)
            count = text.count(old)
            if count != 1:
                raise ControlError("replacement source must occur exactly once", code="replace_not_unique", status=409)
            raw = text.replace(old, new, 1).encode("utf-8")
            if len(raw) > MAX_WRITE_BYTES:
                raise ControlError("result exceeds byte limit", code="write_too_large", status=413)
            self._atomic_replace(target, raw)
            after = _sha256(raw)
            self._audit(request_id, operation, target, expected, after)
            return {"path": target.relative_to(self.root).as_posix(), "before_sha256": expected,
                    "after_sha256": after, "bytes": len(raw)}

        if operation == "create_file":
            target = self._path(payload.get("path"), must_exist=False)
            raw = self._content(payload.get("content"))
            self._create_exclusive(target, raw)
            after = _sha256(raw)
            self._audit(request_id, operation, target, None, after)
            return {"path": target.relative_to(self.root).as_posix(), "before_sha256": None,
                    "after_sha256": after, "bytes": len(raw)}

        raise ControlError("write operation unavailable", code="operation_not_found", status=404)


class ControlServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, config: ControlConfig, inner_token: str, install_dir: Path) -> None:
        super().__init__((LISTEN_HOST, config.listen_port), ControlHandler)
        if not isinstance(inner_token, str) or len(inner_token) < 32:
            raise ControlError("inner gateway token missing", code="config_invalid", status=500)
        self.config = config
        self.inner_token = inner_token
        self.writer = RepoWriter(config, install_dir / "control_audit.jsonl")
        policy = OIDCTrustPolicy(
            repository=config.repository,
            repository_id=config.repository_id,
            repository_owner_id=config.repository_owner_id,
            actor_id=config.actor_id,
            job_workflow_ref=config.trusted_workflow_ref,
            job_workflow_sha=config.trusted_workflow_sha,
        )
        self.verifier = GitHubOIDCVerifier(policy)

    def proxy_inner(self, method: str, route: str, body: bytes) -> tuple[int, bytes, str]:
        connection = http.client.HTTPConnection(INNER_HOST, self.config.inner_port, timeout=120)
        headers = {"Accept": "application/json", "Authorization": f"Bearer {self.inner_token}"}
        if body:
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(body))
        try:
            connection.request(method, route, body=body or None, headers=headers)
            response = connection.getresponse()
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            status = response.status
            content_type = response.getheader("Content-Type") or "application/json"
        except (OSError, http.client.HTTPException) as exc:
            raise ControlError("inner gateway unavailable", code="inner_unavailable", status=502) from exc
        finally:
            connection.close()
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ControlError("inner response exceeds control limit", code="response_too_large", status=502)
        return status, raw, content_type


class ControlHandler(BaseHTTPRequestHandler):
    server_version = "RICBridgeControl/1"

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.command} {urlsplit(self.path).path} -> {args[1]}", flush=True)

    def _route(self) -> str | None:
        parsed = urlsplit(self.path)
        if parsed.query or parsed.fragment:
            self._json(404, {"ok": False, "error": {"code": "query_forbidden", "message": "query strings are forbidden"}})
            return None
        return parsed.path

    def _read_body(self) -> bytes | None:
        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length or "0")
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY_BYTES:
            self._json(413, {"ok": False, "error": {"code": "request_too_large", "message": "request too large"}})
            return None
        return self.rfile.read(length)

    def _legacy_lm_authorized(self, route: str) -> bool:
        if route not in {"/v1/models", "/v1/chat/completions", "/v1/responses"}:
            return False
        value = self.headers.get("Authorization")
        expected = f"Bearer {self.server.inner_token}"
        return isinstance(value, str) and hmac.compare_digest(value, expected)

    def _authenticate(self, route: str, body: bytes) -> str | None:
        request_id = self.headers.get("X-RIC-Request-ID")
        if not request_id:
            self._json(401, {"ok": False, "error": {"code": "request_id_required", "message": "request id required"}})
            return None
        try:
            audience = request_audience(request_id, self.command, route, body)
            self.server.verifier.verify_authorization(self.headers.get("Authorization"), expected_audience=audience)
        except (ControlError, OIDCError):
            self._json(401, {"ok": False, "error": {"code": "unauthorized", "message": "unauthorized"}})
            return None
        return request_id

    def _json(self, status: int, payload: Mapping[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if len(raw) > MAX_RESPONSE_BYTES:
            status = 500
            raw = b'{"ok":false,"error":{"code":"response_too_large","message":"response too large"}}'
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _raw(self, status: int, raw: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _capabilities(self) -> Mapping[str, Any]:
        status, raw, _ = self.server.proxy_inner("GET", "/capabilities", b"")
        if status != 200:
            raise ControlError("inner capabilities unavailable", code="inner_unavailable", status=502)
        try:
            doc = json.loads(raw.decode("utf-8"))
            result = dict(doc["result"])
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ControlError("inner capabilities invalid", code="inner_unavailable", status=502) from exc
        permissions = dict(result.get("permissions", {}))
        permissions["REPO_WRITE"] = "ALLOW_OIDC_CAS"
        result["permissions"] = permissions
        security = dict(result.get("security", {}))
        security.update({
            "public_auth": "GitHub Actions OIDC; immutable reusable workflow; request-bound audience",
            "repo_write_scope": "bounded UTF-8 CAS writes; bridge control files protected",
            "control_plane": "pinned copy outside mutable RIC workspace",
        })
        result["security"] = security
        tools = dict(result.get("tools", {}))
        tools["repo_write"] = {
            "permission": "REPO_WRITE",
            "operations": ["write_file", "replace_text", "create_file"],
            "max_bytes": MAX_WRITE_BYTES,
            "write_roots": list(self.server.config.write_roots),
            "protected_paths": list(self.server.config.protected_paths),
        }
        result["tools"] = tools
        return result

    def do_GET(self) -> None:
        route = self._route()
        if route is None:
            return
        if route not in READ_GET_ROUTES:
            self._json(404, {"ok": False, "error": {"code": "route_not_found", "message": "route not found"}})
            return
        if route == "/v1/models" and self._legacy_lm_authorized(route):
            request_id = None
        else:
            request_id = self._authenticate(route, b"")
            if request_id is None:
                return
        try:
            if route == "/health":
                result = {
                    "service": "ric-bridge-control",
                    "repo_write": True,
                    "auth": "github-oidc-request-bound",
                    "request_id": request_id,
                }
                self._json(200, {"ok": True, "operation": "health", "result": result, "duration_ms": 0})
            elif route == "/capabilities":
                self._json(200, {"ok": True, "operation": "capabilities", "result": self._capabilities(), "duration_ms": 0})
            else:
                status, raw, content_type = self.server.proxy_inner("GET", route, b"")
                self._raw(status, raw, content_type)
        except ControlError as exc:
            self._json(exc.status, {"ok": False, "error": {"code": exc.code, "message": str(exc)}})

    def do_POST(self) -> None:
        route = self._route()
        if route is None:
            return
        if route not in READ_POST_ROUTES and route != WRITE_ROUTE:
            self._json(404, {"ok": False, "error": {"code": "route_not_found", "message": "route not found"}})
            return
        body = self._read_body()
        if body is None:
            return
        if route in {"/v1/chat/completions", "/v1/responses"} and self._legacy_lm_authorized(route):
            request_id = None
        else:
            request_id = self._authenticate(route, body)
            if request_id is None:
                return
        try:
            if route == WRITE_ROUTE:
                try:
                    payload = json.loads(body.decode("utf-8")) if body else {}
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ControlError("invalid JSON", code="invalid_json") from exc
                if not isinstance(payload, Mapping):
                    raise ControlError("JSON object required", code="invalid_json")
                started = time.monotonic()
                result = self.server.writer.dispatch(payload, request_id=request_id)
                self._json(200, {"ok": True, "operation": payload.get("operation"), "result": result,
                                 "duration_ms": round((time.monotonic() - started) * 1000)})
            else:
                status, raw, content_type = self.server.proxy_inner("POST", route, body)
                self._raw(status, raw, content_type)
        except ControlError as exc:
            self._json(exc.status, {"ok": False, "error": {"code": exc.code, "message": str(exc)}})
        except Exception:
            self._json(500, {"ok": False, "error": {"code": "control_error", "message": "control operation failed"}})


def load_server(config_path: Path | None = None) -> ControlServer:
    install_dir = Path(__file__).resolve().parent
    path = config_path or Path(os.environ.get("RIC_CONTROL_CONFIG", str(install_dir / "config.json")))
    config = ControlConfig.load(path)
    inner_token = os.environ.get("RIC_GATEWAY_TOKEN", "")
    return ControlServer(config, inner_token, install_dir)


def main() -> None:
    server = load_server()
    print(
        f"RIC bridge control listening on {LISTEN_HOST}:{server.config.listen_port}; "
        f"inner gateway {INNER_HOST}:{server.config.inner_port}; OIDC repo-write enabled",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    try:
        main()
    except (ControlError, OIDCError) as exc:
        raise SystemExit(f"bridge control startup failed: {exc}") from exc
