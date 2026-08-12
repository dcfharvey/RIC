"""GitHub Actions OIDC verification for the RIC development bridge.

The verifier deliberately has no third-party dependency. It accepts only RS256
JWTs issued by GitHub Actions, validates their signature against GitHub's JWKS,
and then applies an exact trust policy for one immutable reusable workflow.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Mapping


ISSUER = "https://token.actions.githubusercontent.com"
JWKS_URI = "https://token.actions.githubusercontent.com/.well-known/jwks"
_RSA_SHA256_DIGEST_INFO_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


class OIDCError(ValueError):
    pass


def _b64url_decode(value: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise OIDCError("invalid base64url field")
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except Exception as exc:
        raise OIDCError("invalid base64url encoding") from exc


def _json_segment(value: str) -> Mapping[str, Any]:
    try:
        decoded = json.loads(_b64url_decode(value).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OIDCError("invalid JWT JSON") from exc
    if not isinstance(decoded, Mapping):
        raise OIDCError("JWT segment must be an object")
    return decoded


def _rsa_rs256_verify(signing_input: bytes, signature: bytes, jwk: Mapping[str, Any]) -> bool:
    if jwk.get("kty") != "RSA":
        return False
    if jwk.get("alg") not in {None, "RS256"}:
        return False
    try:
        n = int.from_bytes(_b64url_decode(str(jwk["n"])), "big")
        e = int.from_bytes(_b64url_decode(str(jwk["e"])), "big")
    except (KeyError, ValueError, OIDCError):
        return False
    if n.bit_length() < 2048 or e < 3 or e % 2 == 0:
        return False
    size = (n.bit_length() + 7) // 8
    if len(signature) != size:
        return False
    signature_int = int.from_bytes(signature, "big")
    if signature_int >= n:
        return False
    encoded = pow(signature_int, e, n).to_bytes(size, "big")
    digest_info = _RSA_SHA256_DIGEST_INFO_PREFIX + hashlib.sha256(signing_input).digest()
    if len(encoded) < len(digest_info) + 11 or not encoded.startswith(b"\x00\x01"):
        return False
    separator = encoded.find(b"\x00", 2)
    if separator < 10:
        return False
    padding = encoded[2:separator]
    if any(byte != 0xFF for byte in padding):
        return False
    return hmac.compare_digest(encoded[separator + 1 :], digest_info)


@dataclass(frozen=True)
class OIDCTrustPolicy:
    repository: str
    repository_id: str
    repository_owner_id: str
    job_workflow_ref: str
    job_workflow_sha: str
    audience: str = "ric-dev-bridge"
    actor_id: str | None = None
    runner_environment: str = "github-hosted"
    max_lifetime_seconds: int = 600
    clock_skew_seconds: int = 60


class GitHubOIDCVerifier:
    def __init__(
        self,
        policy: OIDCTrustPolicy,
        *,
        urlopen: Callable[..., Any] = urllib.request.urlopen,
        clock: Callable[[], float] = time.time,
        jwks_ttl_seconds: int = 3600,
    ) -> None:
        self.policy = policy
        self._urlopen = urlopen
        self._clock = clock
        self._jwks_ttl_seconds = jwks_ttl_seconds
        self._jwks: dict[str, Mapping[str, Any]] = {}
        self._jwks_expires_at = 0.0
        self._used_jti: dict[str, float] = {}
        self._lock = threading.Lock()

    def _fetch_jwks(self, *, force: bool = False) -> dict[str, Mapping[str, Any]]:
        now = self._clock()
        with self._lock:
            if not force and self._jwks and now < self._jwks_expires_at:
                return dict(self._jwks)
        request = urllib.request.Request(JWKS_URI, headers={"Accept": "application/json"})
        try:
            with self._urlopen(request, timeout=10) as response:
                raw = response.read(256 * 1024 + 1)
        except (OSError, urllib.error.URLError) as exc:
            raise OIDCError("GitHub JWKS unavailable") from exc
        if len(raw) > 256 * 1024:
            raise OIDCError("GitHub JWKS response too large")
        try:
            doc = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OIDCError("GitHub JWKS invalid") from exc
        keys = doc.get("keys") if isinstance(doc, Mapping) else None
        if not isinstance(keys, list):
            raise OIDCError("GitHub JWKS keys missing")
        parsed: dict[str, Mapping[str, Any]] = {}
        for key in keys:
            if not isinstance(key, Mapping):
                continue
            kid = key.get("kid")
            if isinstance(kid, str) and kid and key.get("kty") == "RSA":
                parsed[kid] = key
        if not parsed:
            raise OIDCError("GitHub JWKS contains no RSA keys")
        with self._lock:
            self._jwks = parsed
            self._jwks_expires_at = now + self._jwks_ttl_seconds
        return dict(parsed)

    def _key(self, kid: str) -> Mapping[str, Any]:
        keys = self._fetch_jwks()
        key = keys.get(kid)
        if key is None:
            key = self._fetch_jwks(force=True).get(kid)
        if key is None:
            raise OIDCError("OIDC signing key unknown")
        return key

    def _validate_claims(self, claims: Mapping[str, Any]) -> None:
        policy = self.policy
        exact = {
            "iss": ISSUER,
            "aud": policy.audience,
            "repository": policy.repository,
            "repository_id": policy.repository_id,
            "repository_owner_id": policy.repository_owner_id,
            "job_workflow_ref": policy.job_workflow_ref,
            "job_workflow_sha": policy.job_workflow_sha,
            "runner_environment": policy.runner_environment,
        }
        if policy.actor_id is not None:
            exact["actor_id"] = policy.actor_id
        for key, expected in exact.items():
            actual = claims.get(key)
            if not isinstance(actual, str) or not hmac.compare_digest(actual, expected):
                raise OIDCError(f"OIDC claim rejected: {key}")

        now = int(self._clock())
        skew = policy.clock_skew_seconds
        try:
            exp = int(claims["exp"])
            iat = int(claims["iat"])
            nbf = int(claims["nbf"])
        except (KeyError, TypeError, ValueError) as exc:
            raise OIDCError("OIDC temporal claims invalid") from exc
        if exp <= iat or exp - iat > policy.max_lifetime_seconds:
            raise OIDCError("OIDC token lifetime rejected")
        if now > exp + skew or now + skew < nbf or iat > now + skew:
            raise OIDCError("OIDC token outside valid time window")
        if now - iat > policy.max_lifetime_seconds + skew:
            raise OIDCError("OIDC token too old")

        jti = claims.get("jti")
        if not isinstance(jti, str) or not jti or len(jti) > 256:
            raise OIDCError("OIDC jti invalid")
        with self._lock:
            for seen, expiry in list(self._used_jti.items()):
                if expiry + skew < now:
                    self._used_jti.pop(seen, None)
            if jti in self._used_jti:
                raise OIDCError("OIDC token replay rejected")
            self._used_jti[jti] = float(exp)

    def verify(self, token: str) -> Mapping[str, Any]:
        if not isinstance(token, str) or len(token) < 100 or len(token) > 32 * 1024:
            raise OIDCError("OIDC token malformed")
        parts = token.split(".")
        if len(parts) != 3:
            raise OIDCError("OIDC token malformed")
        header = _json_segment(parts[0])
        claims = _json_segment(parts[1])
        if header.get("alg") != "RS256" or header.get("typ") not in {None, "JWT"}:
            raise OIDCError("OIDC signing algorithm rejected")
        kid = header.get("kid")
        if not isinstance(kid, str) or not kid or len(kid) > 512:
            raise OIDCError("OIDC kid invalid")
        signature = _b64url_decode(parts[2])
        signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
        if not _rsa_rs256_verify(signing_input, signature, self._key(kid)):
            raise OIDCError("OIDC signature invalid")
        self._validate_claims(claims)
        return claims

    def verify_authorization(self, value: str | None) -> Mapping[str, Any]:
        if not isinstance(value, str) or not value.startswith("Bearer "):
            raise OIDCError("OIDC bearer missing")
        return self.verify(value[7:])
