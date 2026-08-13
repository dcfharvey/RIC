"""Gardien local en lecture seule du runtime MVP.

Il détecte et classe les anomalies, mais ne répare jamais l'état canonique.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import json
from pathlib import Path
import sqlite3
from typing import Any, Callable, Protocol

from .mvp_preflight import _active_assignment_issues, inspect_mvp_preflight
from .telemetry import inspect_rodage
from .util import Clock, parse_iso, to_iso
from .world import WorldEngine


GUARDIAN_INTERVAL_SECONDS = 3600
OVERDUE_GRACE_SECONDS = 120


class ModelLister(Protocol):
    def list_models(self) -> tuple[str, ...]: ...


@dataclass(frozen=True)
class GuardianCheck:
    key: str
    level: str
    detail: str


@dataclass(frozen=True)
class GuardianReport:
    checked_at: str
    world_id: int
    status: str
    checks: tuple[GuardianCheck, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "checked_at": self.checked_at,
            "world_id": self.world_id,
            "status": self.status,
            "checks": [check.__dict__ for check in self.checks],
        }


class LocalGuardian:
    """Audit périodique léger, persistant et sans appel génératif."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        world_id: int,
        *,
        log_path: Path,
        model_lister: ModelLister | None = None,
        service_probe: Callable[[], bool] | None = None,
        interval_seconds: int = GUARDIAN_INTERVAL_SECONDS,
        clock: Clock | None = None,
        runtime_session_id: int | None = None,
    ) -> None:
        if not isinstance(interval_seconds, int) or isinstance(interval_seconds, bool) \
                or not 60 <= interval_seconds <= 86400:
            raise ValueError("intervalle du gardien invalide (60..86400 secondes)")
        self._conn = conn
        self._world_id = world_id
        self._log_path = Path(log_path)
        self._model_lister = model_lister
        self._service_probe = service_probe
        self._interval_seconds = interval_seconds
        self._clock = clock or Clock()
        self._runtime_session_id = runtime_session_id
        self._next_check_at = None
        self._last_event_seq: int | None = None

    def _event_seq(self) -> int:
        row = self._conn.execute(
            "SELECT COALESCE(MAX(seq), 0) FROM canonical_event WHERE world_id = ?",
            (self._world_id,),
        ).fetchone()
        return int(row[0])

    def due(self) -> bool:
        return (
            self._next_check_at is None
            or self._clock.now() >= self._next_check_at
            or self._event_seq() != self._last_event_seq
        )

    def inspect(self) -> GuardianReport:
        checked_at = self._clock.now_iso()
        checks: list[GuardianCheck] = []
        preflight = inspect_mvp_preflight(self._conn, world_id=self._world_id)
        own_open_session = False
        if self._runtime_session_id is not None:
            issues = _active_assignment_issues(self._conn, self._world_id, "active")
            rows = self._conn.execute(
                "SELECT id FROM runtime_session WHERE world_id=? AND stopped_at IS NULL",
                (self._world_id,),
            ).fetchall()
            own_open_session = issues == ("open_runtime_session",) \
                and len(rows) == 1 and int(rows[0]["id"]) == self._runtime_session_id
        if preflight.healthy or own_open_session:
            checks.append(GuardianCheck("canonical_integrity", "ok", "prévol structurel sain"))
        else:
            detail = "; ".join(f"{item.key}: {item.detail}" for item in preflight.failures)
            checks.append(GuardianCheck("canonical_integrity", "critical", detail))

        canonical_now = parse_iso(
            WorldEngine(self._conn, clock=self._clock).read_canonical_time(self._world_id)
        )
        overdue_before = canonical_now - timedelta(seconds=OVERDUE_GRACE_SECONDS)
        overdue = self._conn.execute(
            "SELECT c.key, a.type, a.planned_end_at FROM activity a "
            "JOIN character c ON c.id = a.character_id "
            "WHERE a.world_id = ? AND a.status = 'active' AND a.planned_end_at < ? "
            "ORDER BY a.planned_end_at, c.key",
            (self._world_id, to_iso(overdue_before)),
        ).fetchall()
        if overdue:
            detail = ", ".join(
                f"{row['key']}:{row['type']}@{row['planned_end_at']}" for row in overdue
            )
            checks.append(GuardianCheck("runtime_deadlines", "critical", detail))
        else:
            checks.append(GuardianCheck("runtime_deadlines", "ok", "aucune échéance en retard"))

        if self._model_lister is None:
            checks.append(GuardianCheck("local_llm", "info", "LLM local désactivé"))
        else:
            try:
                models = self._model_lister.list_models()
            except Exception as exc:
                checks.append(GuardianCheck("local_llm", "attention", type(exc).__name__))
            else:
                level = "ok" if models else "attention"
                detail = ",".join(models) if models else "aucun modèle chargé"
                checks.append(GuardianCheck("local_llm", level, detail))

        if self._service_probe is not None:
            try:
                service_alive = self._service_probe()
            except Exception as exc:
                checks.append(GuardianCheck("control_server", "critical", type(exc).__name__))
            else:
                checks.append(
                    GuardianCheck(
                        "control_server",
                        "ok" if service_alive else "critical",
                        "actif" if service_alive else "thread arrêté",
                    )
                )

        telemetry = inspect_rodage(self._conn, self._world_id)
        if telemetry.warnings:
            checks.append(GuardianCheck(
                "rodage_patterns",
                "attention",
                "; ".join(f"{item.key}: {item.detail}" for item in telemetry.warnings),
            ))
        else:
            checks.append(GuardianCheck(
                "rodage_patterns",
                "ok",
                f"fenêtre: {telemetry.speech_acts} paroles, {telemetry.activity_starts} activités",
            ))

        levels = {check.level for check in checks}
        status = "CRITIQUE" if "critical" in levels else "ATTENTION" if "attention" in levels else "SAIN"
        report = GuardianReport(checked_at, self._world_id, status, tuple(checks))
        self._append(report)
        self._last_event_seq = self._event_seq()
        self._next_check_at = self._clock.now() + timedelta(seconds=self._interval_seconds)
        return report

    def run_if_due(self) -> GuardianReport | None:
        return self.inspect() if self.due() else None

    def _append(self, report: GuardianReport) -> None:
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        with self._log_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(report.as_dict(), ensure_ascii=False, sort_keys=True) + "\n")
