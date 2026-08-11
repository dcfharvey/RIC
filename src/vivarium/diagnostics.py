"""Capture diagnostique locale, optionnelle et bornee des appels LLM.

Ce journal est volontairement hors SQLite : il n'est ni canonique, ni
subjectif, ni relu par les providers. Les erreurs d'instrumentation sont
absorbees afin que ON/OFF ne change pas le monde.
"""
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_DIAGNOSTIC_RECORDS = 500
MAX_DIAGNOSTIC_BYTES = 8 * 1024 * 1024
MAX_DIAGNOSTIC_STRING = 64 * 1024


def _safe(value: Any, *, path: str = "", truncated: list[str] | None = None) -> Any:
    if isinstance(value, dict):
        return {str(k): _safe(v, path=f"{path}.{k}" if path else str(k), truncated=truncated) for k, v in value.items()
                if str(k).lower() not in {"api_token", "authorization", "headers", "secret", "password"}}
    if isinstance(value, (list, tuple)):
        return [_safe(v, path=f"{path}[{i}]", truncated=truncated) for i, v in enumerate(value)]
    if isinstance(value, str):
        if len(value) > MAX_DIAGNOSTIC_STRING:
            if truncated is not None:
                truncated.append(path)
            return value[:MAX_DIAGNOSTIC_STRING]
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return repr(value)[:MAX_DIAGNOSTIC_STRING]


class DiagnosticRecorder:
    """Journal JSONL borné; aucune ouverture de fichier si disabled."""

    def __init__(self, path: Path | None = None, *, enabled: bool = False,
                 max_records: int = MAX_DIAGNOSTIC_RECORDS,
                 max_bytes: int = MAX_DIAGNOSTIC_BYTES) -> None:
        if not isinstance(max_records, int) or not 1 <= max_records <= MAX_DIAGNOSTIC_RECORDS:
            raise ValueError("borne de diagnostics invalide")
        if not isinstance(max_bytes, int) or not 1024 <= max_bytes <= MAX_DIAGNOSTIC_BYTES:
            raise ValueError("taille de diagnostics invalide")
        self.path = None if path is None else Path(path)
        self.enabled = bool(enabled) and self.path is not None
        self.max_records, self.max_bytes = max_records, max_bytes
        self._lock = threading.Lock()

    @classmethod
    def from_environment(cls) -> "DiagnosticRecorder":
        enabled = os.environ.get("VIVARIUM_DIAGNOSTICS", "").lower() in {"1", "true", "yes", "on"}
        path = os.environ.get("VIVARIUM_DIAGNOSTICS_PATH", "logs/llm_diagnostics.jsonl")
        return cls(Path(path), enabled=enabled)

    def record(self, kind: str, payload: dict[str, Any]) -> str | None:
        if not self.enabled:
            return None
        diagnostic_id = str(uuid.uuid4())
        truncated: list[str] = []
        event = {
            "schema_version": 1,
            "diagnostic_id": diagnostic_id,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "kind": kind,
            "payload": _safe(payload, truncated=truncated),
        }
        if truncated:
            event["truncated_fields"] = truncated
        try:
            line = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            encoded = line.encode("utf-8")
            if len(encoded) > self.max_bytes:
                return diagnostic_id
            with self._lock:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("ab") as stream:
                    stream.write(encoded)
                self._trim_locked()
        except (OSError, ValueError, TypeError):
            # Diagnostics must never alter provider, validation or runtime flow.
            return diagnostic_id
        return diagnostic_id

    def _trim_locked(self) -> None:
        assert self.path is not None
        if self.path.stat().st_size <= self.max_bytes:
            with self.path.open("rb") as stream:
                if sum(1 for _ in stream) <= self.max_records:
                    return
        lines = self.path.read_bytes().splitlines()
        lines = lines[-self.max_records:]
        while len(lines) > 1 and sum(len(item) + 1 for item in lines) > self.max_bytes:
            lines.pop(0)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_bytes(b"\n".join(lines) + (b"\n" if lines else b""))
        os.replace(tmp, self.path)
