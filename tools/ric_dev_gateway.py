"""Loopback-only RIC development gateway.

Preserves the temporary OpenAI-compatible LM Studio proxy and adds the bounded
Phase A JSON bridge.  The bearer token is read only from the process
environment; it is never logged or returned.
"""

from __future__ import annotations

import http.client
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vivarium.dev_bridge import BridgeError, DevBridgeService  # noqa: E402


LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = int(os.environ.get("RIC_GATEWAY_PORT", "8787"))
UPSTREAM_HOST = "127.0.0.1"
UPSTREAM_PORT = 1234
MAX_BODY_BYTES = 1_048_576
MAX_RESPONSE_BYTES = 16 * 1_048_576
TOKEN = os.environ.get("RIC_GATEWAY_TOKEN", "")
LM_ROUTES = {
    ("GET", "/v1/models"),
    ("POST", "/v1/chat/completions"),
    ("POST", "/v1/responses"),
}
DEV_ROUTES = {"/dev/fs", "/dev/exec", "/dev/jobs", "/dev/git", "/dev/ric"}


def _authorized(value: str | None) -> bool:
    import secrets
    return bool(value) and secrets.compare_digest(value, f"Bearer {TOKEN}")


def _write_json(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_RESPONSE_BYTES:
        status, raw = 500, b'{"error":{"code":"response_too_large","message":"response too large"}}'
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


class GatewayHandler(BaseHTTPRequestHandler):
    server_version = "RICDevGateway/1"

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.command} {urlsplit(self.path).path} -> {args[1]}", flush=True)

    def _auth_route(self) -> str | None:
        parsed = urlsplit(self.path)
        if parsed.query or parsed.fragment:
            _write_json(self, 404, {"ok": False, "error": {"code": "query_forbidden", "message": "query strings are forbidden"}})
            return None
        if not _authorized(self.headers.get("Authorization")):
            _write_json(self, 401, {"ok": False, "error": {"code": "unauthorized", "message": "unauthorized"}})
            return None
        return parsed.path

    def _read_body(self) -> bytes | None:
        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length or "-1")
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY_BYTES:
            _write_json(self, 413, {"ok": False, "error": {"code": "request_too_large", "message": "request too large"}})
            return None
        return self.rfile.read(length)

    def _dev_json(self, route: str, raw: bytes) -> None:
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
            if not isinstance(payload, dict):
                raise BridgeError("JSON object required", code="invalid_json")
            result = self.server.service.dispatch(route, payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            _write_json(self, 400, {"ok": False, "error": {"code": "invalid_json", "message": str(exc)}})
            return
        except BridgeError as exc:
            _write_json(self, exc.status, {"ok": False, "error": {"code": exc.code, "message": str(exc)}})
            return
        except Exception:
            _write_json(self, 500, {"ok": False, "error": {"code": "bridge_error", "message": "bridge operation failed"}})
            return
        _write_json(self, 200, result)

    def _proxy_lm(self, route: str, body: bytes = b"") -> None:
        connection = http.client.HTTPConnection(UPSTREAM_HOST, UPSTREAM_PORT, timeout=90)
        headers = {"Accept": "application/json"}
        if body:
            headers.update({"Content-Type": "application/json", "Content-Length": str(len(body))})
        try:
            connection.request(self.command, route, body=body or None, headers=headers)
            response = connection.getresponse()
            payload = response.read(MAX_RESPONSE_BYTES + 1)
        except (OSError, http.client.HTTPException):
            _write_json(self, 502, {"ok": False, "error": {"code": "upstream_unavailable", "message": "upstream unavailable"}})
            return
        finally:
            connection.close()
        if len(payload) > MAX_RESPONSE_BYTES:
            _write_json(self, 502, {"ok": False, "error": {"code": "response_too_large", "message": "upstream response too large"}})
            return
        self.send_response(response.status)
        self.send_header("Content-Type", response.getheader("Content-Type") or "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        route = self._auth_route()
        if route is None:
            return
        if route == "/health":
            _write_json(self, 200, {"ok": True, "operation": "health", "result": {"service": "ric-dev-bridge", "read_only": True}, "duration_ms": 0})
        elif route == "/capabilities":
            _write_json(self, 200, {"ok": True, "operation": "capabilities", "result": self.server.service.capabilities(), "duration_ms": 0})
        elif (self.command, route) in LM_ROUTES:
            self._proxy_lm(route)
        else:
            _write_json(self, 404, {"ok": False, "error": {"code": "route_not_found", "message": "route not found"}})

    def do_POST(self) -> None:
        route = self._auth_route()
        if route is None:
            return
        raw = self._read_body()
        if raw is None:
            return
        if route in DEV_ROUTES:
            self._dev_json(route, raw)
        elif (self.command, route) in LM_ROUTES:
            self._proxy_lm(route, raw)
        else:
            _write_json(self, 404, {"ok": False, "error": {"code": "route_not_found", "message": "route not found"}})


class GatewayServer(ThreadingHTTPServer):
    def __init__(self, address, token: str):
        super().__init__(address, GatewayHandler)
        root = Path(os.environ.get("RIC_DEV_ROOT", str(ROOT))).resolve()
        db_path = os.environ.get("RIC_DEV_DB_PATH")
        self.service = DevBridgeService(root, token, db_path=db_path)


if __name__ == "__main__":
    if not TOKEN or len(TOKEN) < 32:
        raise SystemExit("RIC_GATEWAY_TOKEN must be a strong temporary token")
    server = GatewayServer((LISTEN_HOST, LISTEN_PORT), TOKEN)
    print(f"gateway listening on {LISTEN_HOST}:{LISTEN_PORT}; upstream {UPSTREAM_HOST}:{UPSTREAM_PORT}; dev bridge enabled", flush=True)
    server.serve_forever()
