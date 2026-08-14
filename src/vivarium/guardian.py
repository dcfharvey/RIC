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

    def due(self) -> bool:
        """Le gardien est périodique; les événements canoniques ne déclenchent pas un audit."""
        return self._next_check_at is None or self._clock.now() >= self._next_check_at

    def _runtime_consistency(self) -> GuardianCheck:
        """Vérifie seulement les invariants opérationnels nécessaires au runtime vivant."""
        world = self._conn.execute(
            "SELECT status FROM worlds WHERE id = ?", (self._world_id,)
        ).fetchone()
        if world is None:
            return GuardianCheck("runtime_consistency", "critical", "monde introuvable")
        if world["status"] not in {"active", "paused"}:
            return GuardianCheck(
                "runtime_consistency", "critical", f"statut monde invalide: {world['status']!r}"
            )

        clock = self._conn.execute(
            "SELECT runtime_state FROM canonical_clock WHERE world_id = ?", (self._world_id,)
        ).fetchone()
        if clock is None:
            return GuardianCheck("runtime_consistency", "critical", "horloge canonique absente")

        if self._runtime_session_id is not None:
            open_session = self._conn.execute(
                "SELECT id FROM runtime_session WHERE world_id=? AND stopped_at IS NULL",
                (self._world_id,),
            ).fetchone()
            if open_session is None or int(open_session["id"]) != self._runtime_session_id:
                return GuardianCheck(
                    "runtime_consistency", "critical", "session runtime propriétaire absente ou remplacée"
                )
            if clock["runtime_state"] != "running":
                return GuardianCheck(
                    "runtime_consistency", "critical",
                    f"horloge runtime incohérente: {clock['runtime_state']!r}",
                )

        return GuardianCheck(
            "runtime_consistency", "ok", "monde, horloge et session runtime cohérents"
        )

    def inspect(self) -> GuardianReport:
        checked_at = self._clock.now_iso()
        checks: list[GuardianCheck] = [self._runtime_consistency()]

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
                f"fenêtre: {telemetry.speech_acts} paroles, "
                f"{sum(sum(counts.values()) for counts in telemetry.activity_mix.values())} activités "
                f"comportementales, {telemetry.technical_idle_starts} idle techniques",
            ))

        levels = {check.level for check in checks}
        status = "CRITIQUE" if "critical" in levels else "ATTENTION" if "attention" in levels else "SAIN"
        report = GuardianReport(checked_at, self._world_id, status, tuple(checks))
        self._append(report)
        self._next_check_at = self._clock.now() + timedelta(seconds=self._interval_seconds)
        return report

    def run_if_due(self) -> GuardianReport | None:
        return self.inspect() if self.due() else None

    def _append(self, report: GuardianReport) -> None:
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        with self._log_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(report.as_dict(), ensure_ascii=False, sort_keys=True) + "\n")
