"""Prévol déterministe et non destructif d'un monde candidat au MVP.

Ce module ne lance aucune simulation, ne contacte aucun LLM et n'applique
aucune migration. Il répond à une question volontairement plus étroite que
« le Vivarium est-il terminé ? » : *la base choisie est-elle structurellement
saine et contient-elle le socle du monde MVP attendu ?*

Le prévol est destiné à être exécuté juste avant d'ouvrir les outils de
contrôle opérateur. Les essais vivants restent des bancs séparés, bornés et
jetables : leur résultat ne peut jamais rendre une base saine par magie.
"""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Any

from .integration_world import INITIAL_RESIDENTS, INITIAL_SHARED_FACTS
from .migrations import load_migrations
from .repro import (
    materialization_chain_audit,
    structural_event_audit,
    subjective_affect_audit,
    subjective_belief_audit,
    subjective_social_audit,
    subjective_trace_audit,
    social_interpretation_audit,
    social_appraisal_audit,
    scc3a_affect_audit,
    scc1c_admission_audit,
)


EXPECTED_CHARACTER_KEYS = tuple(character_key for _, character_key in INITIAL_RESIDENTS)


class MVPPreflightError(ValueError):
    """Entrée de prévol invalide ou base impossible à inspecter."""


@dataclass(frozen=True)
class PreflightCheck:
    """Un contrôle lisible, stable et sans donnée narrative sensible."""

    key: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class MVPPreflightReport:
    """Résultat compact, sérialisable par l'interface ou la CLI."""

    world_id: int | None
    world_name: str | None
    checks: tuple[PreflightCheck, ...]

    @property
    def healthy(self) -> bool:
        return bool(self.world_id is not None) and all(check.passed for check in self.checks)

    @property
    def failures(self) -> tuple[PreflightCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)

    def as_dict(self) -> dict[str, Any]:
        return {
            "world_id": self.world_id,
            "world_name": self.world_name,
            "healthy": self.healthy,
            "checks": [
                {"key": check.key, "passed": check.passed, "detail": check.detail}
                for check in self.checks
            ],
        }


def _check(key: str, passed: bool, detail: str) -> PreflightCheck:
    return PreflightCheck(key=key, passed=passed, detail=detail)


def _world_row(conn: sqlite3.Connection, world_id: int | None) -> sqlite3.Row | None:
    if world_id is not None:
        if isinstance(world_id, bool) or not isinstance(world_id, int) or world_id < 1:
            raise MVPPreflightError("world_id doit être un entier strictement positif")
        row = conn.execute(
            "SELECT id, name, status FROM worlds WHERE id = ?", (world_id,)
        ).fetchone()
        if row is None:
            raise MVPPreflightError(f"monde introuvable : {world_id}")
        return row

    rows = conn.execute("SELECT id, name, status FROM worlds ORDER BY id").fetchall()
    if len(rows) == 1:
        return rows[0]
    return None


def _physiology_system_check(conn: sqlite3.Connection, world_id: int) -> PreflightCheck:
    """Contrôle le gate physiologique par SQL direct, sans lire l'horloge.

    Le raccord est volontairement inactif : ce contrôle informe l'opérateur de
    la configuration sans matérialiser H/phase/P et sans faire progresser le
    temps canonique.
    """
    row = conn.execute(
        "SELECT status, prepared_model_key, prepared_model_version "
        "FROM world_physiology_system WHERE world_id = ?",
        (world_id,),
    ).fetchone()
    status = "inactive" if row is None else row["status"]
    character_count = conn.execute(
        "SELECT COUNT(*) FROM character WHERE world_id = ?", (world_id,)
    ).fetchone()[0]
    regulation_count = conn.execute(
        "SELECT COUNT(*) FROM sleep_regulation_state WHERE world_id = ?", (world_id,)
    ).fetchone()[0]
    capacity_count = conn.execute(
        "SELECT COUNT(*) FROM physical_capacity_state WHERE world_id = ?", (world_id,)
    ).fetchone()[0]
    hysteresis_count = conn.execute(
        "SELECT COUNT(*) FROM sleep_wake_hysteresis_state WHERE world_id = ?", (world_id,)
    ).fetchone()[0]
    if status == "inactive":
        passed = regulation_count == 0 and capacity_count == 0 and hysteresis_count == 0
        return _check(
            "sleep_physiology",
            passed,
            "inactive ; aucun état matérialisé" if passed else "inactive avec états physiologiques inattendus",
        )
    if status == "prepared":
        schedules = conn.execute(
            "SELECT COUNT(*) FROM world_light_schedule_assignment WHERE world_id = ?", (world_id,)
        ).fetchone()[0]
        locations = conn.execute("SELECT COUNT(*) FROM location WHERE world_id = ?", (world_id,)).fetchone()[0]
        exposed = conn.execute(
            "SELECT COUNT(DISTINCT location_id) FROM world_location_light_assignment WHERE world_id = ?",
            (world_id,),
        ).fetchone()[0]
        biologic = conn.execute(
            "SELECT COUNT(DISTINCT character_id) FROM character_sleep_biology_assignment WHERE world_id = ?",
            (world_id,),
        ).fetchone()[0]
        model_ok = row["prepared_model_key"] == "ric.sleep.additive.v1" and row["prepared_model_version"] == 1
        passed = (
            model_ok and schedules > 0 and exposed == locations and biologic == character_count
            and regulation_count == 0 and capacity_count == 0 and hysteresis_count == 0
        )
        return _check(
            "sleep_physiology",
            passed,
            "prepared complet et toujours inactif" if passed else "prepared incomplet ou contient des états prématurés",
        )
    if status == "active":
        model_ok = row["prepared_model_key"] == "ric.sleep.additive.v1" and row["prepared_model_version"] == 1
        desynchronized = conn.execute(
            "SELECT COUNT(*) FROM sleep_regulation_state r "
            "JOIN physical_capacity_state p ON p.world_id = r.world_id AND p.character_id = r.character_id "
            "JOIN sleep_wake_hysteresis_state h ON h.world_id = r.world_id AND h.character_id = r.character_id "
            "WHERE r.world_id = ? "
            "AND (r.anchor_at != p.anchor_at OR r.anchor_at != h.anchor_at)",
            (world_id,),
        ).fetchone()[0]
        passed = (
            model_ok and regulation_count == character_count and capacity_count == character_count
            and hysteresis_count == character_count and desynchronized == 0
        )
        return _check(
            "sleep_physiology",
            passed,
            "active avec états complets" if passed else "active avec états physiologiques incomplets",
        )
    return _check("sleep_physiology", False, f"statut physiologique inconnu : {status!r}")


def inspect_mvp_preflight(
    conn: sqlite3.Connection, *, world_id: int | None = None
) -> MVPPreflightReport:
    """Inspecte une base existante sans créer, modifier ou réparer quoi que ce soit.

    L'appelant doit déjà avoir ouvert la base. Cela permet à la CLI de l'ouvrir
    en lecture seule et aux tests de fournir une base en mémoire. Les audits
    sont les mêmes projections de lecture que celles du banc : aucun résultat
    de prévol n'est une écriture dans l'histoire du monde.
    """
    try:
        row = _world_row(conn, world_id)
    except sqlite3.DatabaseError as exc:
        raise MVPPreflightError(f"base illisible : {exc}") from exc

    if row is None:
        count = conn.execute("SELECT COUNT(*) FROM worlds").fetchone()[0]
        return MVPPreflightReport(
            None,
            None,
            (
                _check(
                    "single_world_selected",
                    False,
                    "aucun monde unique sélectionnable ; indique --world-id si la base en contient plusieurs"
                    if count
                    else "aucun monde dans la base",
                ),
            ),
        )

    selected_world_id = int(row["id"])
    checks: list[PreflightCheck] = []

    expected_schema = max(migration.version for migration in load_migrations())
    schema_row = conn.execute("SELECT MAX(version) FROM migrations").fetchone()
    actual_schema = schema_row[0] if schema_row and schema_row[0] is not None else 0
    checks.append(
        _check(
            "schema_version",
            actual_schema == expected_schema,
            f"attendu={expected_schema}; trouvé={actual_schema}",
        )
    )

    integrity = [item[0] for item in conn.execute("PRAGMA integrity_check").fetchall()]
    checks.append(_check("sqlite_integrity", integrity == ["ok"], "ok" if integrity == ["ok"] else repr(integrity)))

    foreign_keys = [tuple(item) for item in conn.execute("PRAGMA foreign_key_check").fetchall()]
    checks.append(_check("foreign_keys", not foreign_keys, "aucune violation" if not foreign_keys else repr(foreign_keys)))

    checks.append(
        _check(
            "world_status",
            row["status"] in {"active", "paused"},
            f"statut={row['status']!r}",
        )
    )

    characters = conn.execute(
        "SELECT key, current_location_id FROM character WHERE world_id = ? ORDER BY key",
        (selected_world_id,),
    ).fetchall()
    actual_keys = tuple(item["key"] for item in characters)
    checks.append(
        _check(
            "mvp_cast",
            actual_keys == tuple(sorted(EXPECTED_CHARACTER_KEYS)),
            f"attendu={','.join(sorted(EXPECTED_CHARACTER_KEYS))}; trouvé={','.join(actual_keys) or 'aucun'}",
        )
    )
    missing_positions = tuple(item["key"] for item in characters if item["current_location_id"] is None)
    checks.append(
        _check(
            "character_positions",
            not missing_positions,
            "toutes les positions sont canoniques" if not missing_positions else f"sans position : {','.join(missing_positions)}",
        )
    )
    checks.append(_physiology_system_check(conn, selected_world_id))

    origins = conn.execute(
        "SELECT c.key AS character_key, t.key AS template_key, o.template_version "
        "FROM character_instance_origin o "
        "JOIN character c ON c.id = o.character_id "
        "JOIN character_template t ON t.id = o.template_id "
        "WHERE o.world_id = ? ORDER BY c.key",
        (selected_world_id,),
    ).fetchall()
    actual_origins = tuple(
        (item["character_key"], item["template_key"], item["template_version"])
        for item in origins
    )
    expected_origins = tuple(
        sorted((character_key, template_key, 4) for template_key, character_key in INITIAL_RESIDENTS)
    )
    checks.append(
        _check(
            "character_origins",
            actual_origins == expected_origins,
            "gabarits MVP v4 et provenance immuable vérifiés"
            if actual_origins == expected_origins
            else f"provenances incompatibles : {actual_origins!r}",
        )
    )

    context = conn.execute(
        "SELECT facts_json FROM world_initial_context WHERE world_id = ?", (selected_world_id,)
    ).fetchone()
    context_ok = context is not None
    if context_ok:
        import json

        try:
            facts = json.loads(context["facts_json"])
            context_ok = all(facts.get(key) == value for key, value in INITIAL_SHARED_FACTS.items())
        except (TypeError, ValueError):
            context_ok = False
    checks.append(
        _check(
            "initial_shared_context",
            context_ok,
            "contexte commun MVP vérifié" if context_ok else "contexte commun MVP absent ou incompatible",
        )
    )

    structural = structural_event_audit(conn, selected_world_id)
    structural_ok = all(value for key, value in structural.items() if key != "bad_causes") and not structural["bad_causes"]
    checks.append(_check("canonical_journal", structural_ok, "journal structurel sain" if structural_ok else repr(structural)))

    materialization = materialization_chain_audit(conn, selected_world_id)
    checks.append(_check("materialization_chains", not materialization, "aucune anomalie" if not materialization else repr(materialization)))

    subjective_findings = (
        *subjective_trace_audit(conn, selected_world_id),
        *social_interpretation_audit(conn, selected_world_id),
        *social_appraisal_audit(conn, selected_world_id),
        *scc3a_affect_audit(conn, selected_world_id),
        *scc1c_admission_audit(conn, selected_world_id),
        *subjective_belief_audit(conn, selected_world_id),
        *subjective_affect_audit(conn, selected_world_id),
        *subjective_social_audit(conn, selected_world_id),
    )
    checks.append(
        _check(
            "subjective_ledgers",
            not subjective_findings,
            "aucune anomalie" if not subjective_findings else repr(subjective_findings),
        )
    )

    return MVPPreflightReport(selected_world_id, row["name"], tuple(checks))
