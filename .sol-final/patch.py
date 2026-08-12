from pathlib import Path

path = Path("bridge_control/ric_bridge_control.py")
text = path.read_text(encoding="utf-8")

replacements = [
    (
        "import hashlib\nimport http.client\n",
        "import hashlib\nimport hmac\nimport http.client\n",
    ),
    (
        '_SHA256 = re.compile(r"^[0-9a-f]{64}$")\n',
        '_SHA256 = re.compile(r"^[0-9a-f]{64}$")\n_GIT_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")\n',
    ),
    (
        '        if not _SHA256.fullmatch(workflow_sha):\n            raise ControlError("trusted workflow SHA invalid", code="config_invalid", status=500)\n',
        '        if not _GIT_COMMIT_SHA.fullmatch(workflow_sha):\n            raise ControlError("trusted workflow SHA invalid", code="config_invalid", status=500)\n',
    ),
    (
        '    def _authenticate(self, route: str, body: bytes) -> str | None:\n',
        '    def _legacy_lm_authorized(self, route: str) -> bool:\n'
        '        if route not in {"/v1/models", "/v1/chat/completions", "/v1/responses"}:\n'
        '            return False\n'
        '        value = self.headers.get("Authorization")\n'
        '        expected = f"Bearer {self.server.inner_token}"\n'
        '        return isinstance(value, str) and hmac.compare_digest(value, expected)\n\n'
        '    def _authenticate(self, route: str, body: bytes) -> str | None:\n',
    ),
    (
        '        request_id = self._authenticate(route, b"")\n        if request_id is None:\n            return\n        try:\n            if route == "/health":\n',
        '        if route == "/v1/models" and self._legacy_lm_authorized(route):\n'
        '            request_id = None\n'
        '        else:\n'
        '            request_id = self._authenticate(route, b"")\n'
        '            if request_id is None:\n'
        '                return\n'
        '        try:\n'
        '            if route == "/health":\n',
    ),
    (
        '        request_id = self._authenticate(route, body)\n        if request_id is None:\n            return\n        try:\n            if route == WRITE_ROUTE:\n',
        '        if route in {"/v1/chat/completions", "/v1/responses"} and self._legacy_lm_authorized(route):\n'
        '            request_id = None\n'
        '        else:\n'
        '            request_id = self._authenticate(route, body)\n'
        '            if request_id is None:\n'
        '                return\n'
        '        try:\n'
        '            if route == WRITE_ROUTE:\n',
    ),
]

for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"refusing ambiguous transform: expected 1 occurrence, got {count}: {old[:80]!r}")
    text = text.replace(old, new)

path.write_text(text, encoding="utf-8")
