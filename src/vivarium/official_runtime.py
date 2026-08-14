"""Contrat de démarrage du rodage officiel du moteur actif."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Any

from .mvp_runtime import MVPRuntime
from .runtime_provenance import RuntimeProvenance, verify_runtime_provenance
from .sleep_physiology import ADDITIVE_MODEL_KEY, SleepPhysiologyFoundationService


class OfficialRuntimeError(RuntimeError):
    """Le monde ne démontre pas le contrat de rodage officiel."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class OfficialRuntimeValidation:
    world_id: int
    database_path: str
    physiology_status: str
    initial_manifest: str
    biological_assignments: int
    simulation_engine: str
    character_count: int
    provenance: RuntimeProvenance | None = None
    runtime_session_id: int | None = None

    def as_dict(self) -> dict[str, Any]:
        values = {
            "WORLD_ID": self.world_id,
            "DATABASE_PATH": self.database_path,
            "PHYSIOLOGY_STATUS": self.physiology_status,
            "INITIAL_MANIFEST": self.initial_manifest,
            "BIOLOGICAL_ASSIGNMENTS": self.biological_assignments,
            "SIMULATION_ENGINE": self.simulation_engine,
            "RUNTIME_SESSION_ID": self.runtime_session_id,
        }
        if self.provenance is not None:
            values.update(self.provenance.as_dict())
        return values


def validate_official_world(
    conn: sqlite3.Connection,
    world_id: int,
    *,
    database_path: Path | str,
    provenance: RuntimeProvenance | None = None,
    runtime_session_id: int | None = None,
) -> OfficialRuntimeValidation:
    """Effectue une validation lecture seule avant d'ouvrir un rodage officiel."""
    if not isinstance(world_id, int) or isinstance(world_id, bool) or world_id < 1:
        raise OfficialRuntimeError("monde officiel invalide", code="invalid_world")
    physiology = SleepPhysiologyFoundationService(conn)
    status = physiology.system_status(world_id)
    if status != "active":
        raise OfficialRuntimeError(
            f"physiologie officielle inactive: {status}", code="physiology_inactive"
        )
    system = conn.execute(
        "SELECT prepared_model_key, prepared_model_version FROM world_physiology_system WHERE world_id=?",
        (world_id,),
    ).fetchone()
    if system is None or system["prepared_model_key"] != ADDITIVE_MODEL_KEY or int(system["prepared_model_version"] or 0) != 1:
        raise OfficialRuntimeError("modèle physiologique actif absent ou incompatible", code="physiology_model_invalid")

    character_count = int(conn.execute("SELECT COUNT(*) FROM character WHERE world_id=?", (world_id,)).fetchone()[0])
    if character_count < 1:
        raise OfficialRuntimeError("monde officiel sans personnage", code="characters_missing")
    assignment_count = int(conn.execute(
        "SELECT COUNT(DISTINCT character_id) FROM character_sleep_biology_assignment WHERE world_id=?",
        (world_id,),
    ).fetchone()[0])
    if assignment_count != character_count:
        raise OfficialRuntimeError(
            f"assignations biologiques incomplètes: {assignment_count}/{character_count}",
            code="biological_assignments_incomplete",
        )

    manifest = conn.execute(
        "SELECT m.id,m.manifest_key,m.version,m.model_key,m.model_version,m.anchor_at,c.sealed_at,c.entry_count "
        "FROM initial_physiology_manifest m "
        "LEFT JOIN initial_physiology_manifest_completion c ON c.manifest_id=m.id "
        "WHERE m.world_id=? ORDER BY m.id DESC LIMIT 1",
        (world_id,),
    ).fetchone()
    if manifest is None or manifest["sealed_at"] is None:
        raise OfficialRuntimeError("manifeste physiologique initial non scellé", code="initial_manifest_incomplete")
    if manifest["model_key"] != ADDITIVE_MODEL_KEY or int(manifest["model_version"] or 0) != 1:
        raise OfficialRuntimeError("modèle du manifeste initial incompatible", code="initial_manifest_invalid")
    entry_count = int(conn.execute(
        "SELECT COUNT(*) FROM initial_physiology_manifest_entry WHERE manifest_id=?", (manifest["id"],)
    ).fetchone()[0])
    if int(manifest["entry_count"] or 0) != character_count or entry_count != character_count:
        raise OfficialRuntimeError(
            f"couverture du manifeste initial incomplète: {entry_count}/{character_count}",
            code="initial_manifest_incomplete",
        )

    for table in (
        "sleep_regulation_state", "physical_capacity_state",
        "sleep_wake_hysteresis_state", "sleep_regulation_precision_state",
    ):
        count = int(conn.execute(f"SELECT COUNT(DISTINCT character_id) FROM {table} WHERE world_id=?", (world_id,)).fetchone()[0])
        if count != character_count:
            raise OfficialRuntimeError(
                f"état physiologique incomplet dans {table}: {count}/{character_count}",
                code="physiology_state_incomplete",
            )

    runtime = MVPRuntime(conn, world_id, simulation_contract="active")
    try:
        engine = runtime.simulation_engine_name()
    except Exception as exc:
        raise OfficialRuntimeError(str(exc), code="active_engine_unavailable") from exc
    if engine != "ActiveSimulationEngine":
        raise OfficialRuntimeError(
            f"moteur sélectionné inattendu: {engine}", code="active_engine_unavailable"
        )
    return OfficialRuntimeValidation(
        world_id=world_id,
        database_path=str(Path(database_path).resolve()),
        physiology_status=status,
        initial_manifest=f"{manifest['manifest_key']}@{manifest['version']}",
        biological_assignments=assignment_count,
        simulation_engine=engine,
        character_count=character_count,
        provenance=provenance,
        runtime_session_id=runtime_session_id,
    )


def verify_official_provenance(
    *, expected_checkout_root: Path, expected_runtime_head: str, expected_product_head: str | None = None
) -> RuntimeProvenance:
    return verify_runtime_provenance(
        expected_checkout_root=expected_checkout_root,
        expected_runtime_head=expected_runtime_head,
        expected_product_head=expected_product_head,
    )
