"""Point d'entrée local one-shot du premier Rodage V2.

Le module prépare une base neuve, valide le T0 et n'ouvre la session runtime
qu'après les contrôles déterministes, le préflight, Hugin et la disponibilité
du provider attendu. Il ne connaît pas l'ancien SQLite de rodage.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
import sqlite3
from typing import Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .action_arbitration import ActionArbitrationFoundationService
from .circadian_model import calibration_profiles
from .cognition import LMStudioProvider, LocalLLMSettings
from .db import connect_database
from .integration_world import IntegrationWorldService
from .location_plans import LocationPlanService
from .migrations import ensure_schema
from .mvp_preflight import inspect_mvp_preflight
from .observation import HuginMuninObservationService, ObservationQuery
from .rodage_v2_bootstrap import (
    ActivityStartSpec, CarriedObjectSpec, ExternalPlaceSpec, RodageV2BootstrapService,
)
from .runtime_session import RuntimeSessionService
from .sleep_physiology import (
    ADDITIVE_MODEL_KEY, SleepPhysiologyFoundationService, V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY,
)
from .sleep_termination import SleepTerminationFoundationService
from .util import Clock, to_iso
from .world import WorldEngine


class OfficialBootstrapError(RuntimeError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class OfficialBootstrapReport:
    database: str
    world_id: int
    t0: str
    preflight_healthy: bool
    hugin_ok: bool
    provider_model: str
    session_id: int | None


def _profile_payload(profile_key: str) -> dict[str, object]:
    payload = asdict(calibration_profiles()[profile_key])
    for key in ("profile_key", "version", "evidence_class"):
        payload.pop(key)
    return {"model_key": ADDITIVE_MODEL_KEY, "parameters": payload}


def _eastern_timezone():
    try:
        return ZoneInfo("America/Toronto")
    except ZoneInfoNotFoundError:
        # Windows Python sans tzdata: WO91 est exécuté pendant la journée EDT
        # actuelle; ne pas faire dépendre le contrat d'un offset permanent.
        return timezone(timedelta(hours=-4), name="EDT")


def _configure_physiology(conn: sqlite3.Connection, world_id: int, anchor: str) -> SleepPhysiologyFoundationService:
    service = SleepPhysiologyFoundationService(conn)
    service.register_light_schedule("rodage_v2.day.v1", 1, {
        "schema_version": 1,
        "segments": [{"start_second": 0, "end_second": 86400, "environmental_light_milli": 50_000}],
    })
    service.register_location_light_profile("rodage_v2.exposure.v1", 1, 25_000, {"kind": "effective_exposure"})
    service.register_biology_profile(
        "rodage_v2.human.v1", 1, "human_reference", _profile_payload("human_reference_candidate.v1")
    )
    service.register_biology_profile(
        "rodage_v2.feline.v1", 1, "generic_feline", _profile_payload("generic_feline_hypothesis.v1")
    )
    fictional = _profile_payload("human_reference_candidate.v1")
    service.register_biology_profile("rodage_v2.fictional_sapient.v1", 1, "fictional_canon", fictional)
    service.register_initial_physiology_policy("rodage_v2.t0_regions.v1", 1, {
        "schema_version": 1, "model_key": ADDITIVE_MODEL_KEY, "model_version": 1,
        "homeostatic_load_region": {"min_milli": 45_000, "max_milli": 55_000},
        "physical_capacity_region": {"min_milli": 70_000, "max_milli": 90_000},
        "bootstrap_rule": "wake_stability.stable_seed.v1", "residue_rule": "zero_at_t0.v1",
    }, "wo91.t0.policy_center.v1")
    service.register_t0_phase_rule("rodage_v2.t0_phase.v1", 1, {
        "schema_version": 1, "rule_kind": "schedule_light_phase_windows.v1",
        "light_phase_windows": [[0, 999_999]], "dark_phase_windows": [[0, 999_999]],
    }, "wo91.t0.phase_rule.v1")
    service.register_physical_capacity_policy("rodage_v2.capacity.v1", 1, {
        "schema_version": 1,
        "activity_cost_per_hour_milli": {"none": 3_600, "light": 7_200, "moderate": 10_800, "vigorous": 18_000},
        "minimum_capacity_milli": {"none": 0, "light": 10_000, "moderate": 25_000, "vigorous": 45_000},
        "traversal_cost_per_edge_milli": 250,
        "recovery_per_hour_milli": {"rest": 7_200, "sleep": 10_800},
    }, "wo91.t0.capacity_policy.v1")
    service.assign_light_schedule(world_id, "rodage_v2.day.v1", 1, anchor, "wo91.t0.assignment.v1")
    for row in conn.execute("SELECT key FROM location WHERE world_id=?", (world_id,)):
        service.assign_location_light_profile(world_id, row["key"], "rodage_v2.exposure.v1", 1, anchor, "wo91.t0.assignment.v1")
    biology = {"sophie": "rodage_v2.human.v1", "erika": "rodage_v2.human.v1", "patoune": "rodage_v2.feline.v1", "luna": "rodage_v2.fictional_sapient.v1", "chuu": "rodage_v2.fictional_sapient.v1"}
    for key, profile in biology.items():
        service.assign_biology_profile(world_id, key, profile, 1, "wo91.t0.casting.v1")
    service.assign_physical_capacity_policy(world_id, "rodage_v2.capacity.v1", 1, "wo91.t0.assignment.v1")
    for activity_type, load in V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY.items():
        conn.execute("UPDATE activity_definition SET physical_load_class=? WHERE world_id=? AND activity_type=?", (load, world_id, activity_type))
    term = SleepTerminationFoundationService(conn)
    term.register_policy("rodage_v2.sleep.v1", 1, {
        "schema_version": 1, "checkpoint_interval_seconds": 60, "hard_cap_seconds": 28_800,
        "wake_admissible_enter_milli": 65_000, "wake_admissible_exit_milli": 55_000,
    }, "wo91.t0.sleep_policy.v1")
    term.assign_policy(world_id, "rodage_v2.sleep.v1", 1, "wo91.t0.assignment.v1")
    arb = ActionArbitrationFoundationService(conn)
    policy = arb.register_policy("rodage_v2.arbitration.v1", 1, {
        "schema_version": 1, "source_mappings": {
            "sleep_regulation": {"transform": "linear_clamped_milli.v1", "correlation_group": "sleep", "input_low_milli": 60_000, "input_high_milli": 100_000, "direction": "ascending"},
            "physical_recovery": {"transform": "linear_clamped_milli.v1", "correlation_group": "recovery", "input_low_milli": 20_000, "input_high_milli": 80_000, "direction": "descending"},
            "subjective_intention": {"transform": "linear_clamped_milli.v1", "correlation_group": "subjective", "input_low_milli": 0, "input_high_milli": 100_000, "direction": "ascending"},
        }, "correlation_groups": {"kind": "declared_by_source_mapping.v1"},
        "aggregation": {"kind": "max_per_group_then_saturating_sum.v1"}, "current_action_inertia": {"max_bonus_milli": 0},
        "quasi_equality": {"band_milli": 100_000}, "reassessment": {"interval_seconds": 60},
    }, "wo91.t0.arbitration_policy.v1")
    arb.assign_policy(world_id, policy.policy_key, policy.version, "wo91.t0.assignment.v1")
    service.prepare_world(world_id, ADDITIVE_MODEL_KEY, 1, "wo91.operator")
    return service


def bootstrap_official(
    db_path: Path, *, clock: Clock | None = None, launch_runtime: bool = True,
    provider_checker: Callable[[], str] | None = None,
) -> OfficialBootstrapReport:
    """Prépare et, par défaut, ouvre le premier monde officiel.

    La fonction est utilisée par la commande opérateur; les tests passent une
    base jetable et ``launch_runtime=False``. Toute erreur après création de la
    cible supprime uniquement cette cible neuve et ses sidecars.
    """
    db_path = Path(db_path)
    if db_path.exists() or any(Path(str(db_path) + suffix).exists() for suffix in ("-wal", "-shm")):
        raise OfficialBootstrapError("la cible officielle existe déjà", code="target_exists")
    clock = clock or Clock()
    now = clock.now()
    local = now.astimezone(_eastern_timezone())
    if local.hour >= 16:
        raise OfficialBootstrapError("T0 >= 16:00 EDT : scénario Sophie obsolète", code="t0_after_return_deadline")
    t0 = to_iso(now)
    conn: sqlite3.Connection | None = None
    created = False
    try:
        conn = connect_database(db_path); created = True; ensure_schema(conn)
        world = IntegrationWorldService(conn, clock=clock).create_initial_world(name="Rodage V2")
        world_id = world["id"]
        # La fondation du manifeste exige une ancre canonique gelée. Cette
        # ouverture/fermeture technique ne lance pas l'autonomie : elle fixe
        # uniquement le T0 capturé, avant toute activation physiologique.
        technical = RuntimeSessionService(conn, clock=clock).start(world_id)
        RuntimeSessionService(conn, clock=clock).stop(technical.session_id)
        bootstrap = RodageV2BootstrapService(conn, clock=clock)
        bootstrap.add_external_places(world_id, (
            ExternalPlaceSpec("espace_exterieur", "Espace extérieur", "entree_exterieure"),
            ExternalPlaceSpec("lieu_travail", "Lieu de travail", "espace_exterieur"),
        ))
        physiology = _configure_physiology(conn, world_id, t0)
        manifest = physiology.create_initial_physiology_manifest(
            world_id, "rodage_v2.t0.v1", 1, "rodage_v2.t0_regions.v1", 1,
            "rodage_v2.t0_phase.v1", 1, t0, "wo91.t0.manifest.v1", "T0 réel sans passé reconstruit",
        )
        for row in conn.execute("SELECT key FROM character WHERE world_id=? ORDER BY key", (world_id,)):
            physiology.append_initial_physiology_manifest_entry(
                world_id, manifest["manifest_key"], 1,
                physiology.derive_initial_manifest_entry(world_id, manifest["manifest_key"], 1, row["key"]),
            )
        physiology.seal_initial_physiology_manifest(world_id, manifest["manifest_key"], 1)
        physiology.activate_world_from_initial_manifest(world_id, manifest["manifest_key"], 1, "wo91.operator")
        bootstrap.start_activities(world_id, (
            ActivityStartSpec("sophie", "work", "lieu_travail"),
            ActivityStartSpec("erika", "gaming", "salon"),
            ActivityStartSpec("patoune", "sleep", "salon"),
            ActivityStartSpec("chuu", "clean", "salle_de_bain"),
        ))
        bootstrap.give_carried_objects(world_id, (CarriedObjectSpec("luna", "sac_luna", "Sac d'effets personnels"),))
        return_local = datetime.combine(local.date(), time(16, 0), tzinfo=local.tzinfo)
        return_at = to_iso(return_local.astimezone(now.tzinfo))
        LocationPlanService(conn, clock=clock).plan(world_id, "sophie", "entree_exterieure", return_at, provenance="wo91.return_schedule.v1")
        report = inspect_mvp_preflight(conn, world_id=world_id)
        if not report.healthy:
            raise OfficialBootstrapError("préflight en échec", code="preflight_failed")
        hugin = HuginMuninObservationService(conn, clock=clock).report(
            world_id, ObservationQuery(mode="hugin", subject_keys=("sophie", "erika", "luna", "chuu", "patoune"), focus="current_state")
        )
        hugin_ok = len(hugin.get("evidence", ())) >= 5
        if not hugin_ok:
            raise OfficialBootstrapError("observation Hugin incomplète", code="hugin_failed")
        expected_model = provider_checker() if provider_checker is not None else _check_provider()
        session_id = None
        if launch_runtime:
            session_id = RuntimeSessionService(conn, clock=clock).start(world_id).session_id
        return OfficialBootstrapReport(str(db_path), world_id, t0, True, hugin_ok, expected_model, session_id)
    except Exception:
        if conn is not None:
            conn.close(); conn = None
        if created:
            for path in (db_path, Path(str(db_path) + "-wal"), Path(str(db_path) + "-shm")):
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
        raise
    finally:
        if conn is not None:
            conn.close()


def _check_provider() -> str:
    settings = LocalLLMSettings.from_environment(require_model=True)
    records = LMStudioProvider(settings).list_model_records()
    if not any(record.get("key") == settings.model_id for record in records):
        raise OfficialBootstrapError("modèle LLM attendu indisponible", code="llm_model_unavailable")
    if "qwen3-14b" not in settings.model_id.casefold():
        raise OfficialBootstrapError("modèle configuré différent de Qwen3-14B", code="unexpected_llm_model")
    return settings.model_id


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="rodage-v2-start")
    parser.add_argument("--db", type=Path, default=Path("data/vivarium-rodage-v2.sqlite"))
    parser.add_argument("--dry-run", action="store_true", help="effectue les contrôles sans ouvrir la session runtime")
    args = parser.parse_args(argv)
    try:
        report = bootstrap_official(args.db, launch_runtime=not args.dry_run)
    except (OfficialBootstrapError, sqlite3.Error, ValueError) as exc:
        print(f"Rodage V2 refusé : {exc}")
        return 1
    print(f"Rodage V2 prêt : base={report.database} world_id={report.world_id} T0={report.t0} modèle={report.provider_model}")
    if report.session_id is not None:
        print(f"Session runtime ouverte : {report.session_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
