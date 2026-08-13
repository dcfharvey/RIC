"""Disposable deterministic patch generator for WO88F activation."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")


marker = "    def register_physical_capacity_policy(\n"
method = '''    def activate_world_from_initial_manifest(
        self, world_id: Any, manifest_key: Any, version: Any, activated_by: Any
    ) -> dict[str, Any]:
        """Active H/phi/P atomiquement depuis un manifeste T0 scellé.

        Cette opération de cutover ne reconstruit aucune histoire, n'émet aucun
        événement canonique et ne touche jamais ``need_state``. Elle exige un
        runtime proprement arrêté au T0, un système ``prepared`` sur le modèle
        sélectionné, une couverture dense du manifeste, une politique P valide
        et une politique de terminaison du sommeil assignée.
        """
        world = self._world_id(world_id)
        self._require_world(world)
        key = _key(manifest_key, field="manifeste")
        ver = _version(version)
        actor = _key(activated_by, field="acteur d'activation")
        now = self._now()

        with transaction(self._conn) as conn:
            system = conn.execute(
                "SELECT status,prepared_model_key,prepared_model_version FROM world_physiology_system "
                "WHERE world_id=?", (world,),
            ).fetchone()
            if system is None or system["status"] != "prepared":
                raise SleepPhysiologyError(
                    "système physiologique non préparé", code="physiology_not_prepared"
                )
            if system["prepared_model_key"] != ADDITIVE_MODEL_KEY \
                    or int(system["prepared_model_version"] or 0) != 1:
                raise SleepPhysiologyError("modèle préparé incompatible", code="invalid_model")
            if conn.execute(
                "SELECT 1 FROM runtime_session WHERE world_id=? AND stopped_at IS NULL",
                (world,),
            ).fetchone() is not None:
                raise SleepPhysiologyError("session runtime ouverte", code="runtime_session_open")

            manifest = self.initial_physiology_manifest(world, key, ver)
            if manifest["sealed_at"] is None:
                raise SleepPhysiologyError(
                    "manifeste initial non scellé", code="manifest_not_sealed"
                )
            if manifest["model_key"] != ADDITIVE_MODEL_KEY or int(manifest["model_version"]) != 1:
                raise SleepPhysiologyError("modèle du manifeste incompatible", code="invalid_model")
            frozen = self._frozen_manifest_t0(world)
            if _at(manifest["anchor_at"]) != frozen:
                raise SleepPhysiologyError(
                    "manifeste hors T0 canonique gelé", code="canonical_t0_mismatch"
                )

            # Revalider sous la même transaction ferme le TOCTOU entre preuve et cutover.
            characters = self.validate_initial_physiology_manifest(world, key, ver)
            self.validate_physical_capacity_configuration(world)
            if conn.execute(
                "SELECT 1 FROM world_sleep_termination_policy_assignment WHERE world_id=?",
                (world,),
            ).fetchone() is None:
                raise SleepPhysiologyError(
                    "politique de terminaison du sommeil absente",
                    code="sleep_termination_policy_missing",
                )

            for table in (
                "sleep_regulation_state", "physical_capacity_state",
                "sleep_wake_hysteresis_state", "sleep_regulation_precision_state",
            ):
                if conn.execute(
                    f"SELECT 1 FROM {table} WHERE world_id=? LIMIT 1", (world,)
                ).fetchone() is not None:
                    raise SleepPhysiologyError(
                        "état physiologique préexistant", code="activation_state_exists"
                    )

            entries = conn.execute(
                "SELECT e.character_id,e.homeostatic_load_milli,e.circadian_phase_milli,"
                "e.physical_capacity_milli,e.previous_band,e.homeostatic_load_residue,"
                "e.circadian_phase_residue,e.physical_capacity_remainder "
                "FROM initial_physiology_manifest_entry e WHERE e.manifest_id=? "
                "ORDER BY e.character_id", (manifest["manifest_id"],),
            ).fetchall()
            if len(entries) != len(characters):
                raise SleepPhysiologyError(
                    "couverture de manifeste incomplète", code="incomplete_initial_manifest"
                )

            for entry in entries:
                character_id = int(entry["character_id"])
                conn.execute(
                    "INSERT INTO sleep_regulation_state "
                    "(public_id,world_id,character_id,model_key,model_version,"
                    "homeostatic_load_milli,circadian_phase_milli,anchor_at,updated_at) "
                    "VALUES (?,?,?,?,1,?,?,?,?)",
                    (new_uuid(), world, character_id, ADDITIVE_MODEL_KEY,
                     int(entry["homeostatic_load_milli"]), int(entry["circadian_phase_milli"]),
                     frozen, now),
                )
                conn.execute(
                    "INSERT INTO physical_capacity_state "
                    "(public_id,world_id,character_id,capacity_milli,rate_remainder,anchor_at,updated_at) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (new_uuid(), world, character_id, int(entry["physical_capacity_milli"]),
                     int(entry["physical_capacity_remainder"]), frozen, now),
                )
                conn.execute(
                    "INSERT INTO sleep_wake_hysteresis_state "
                    "(public_id,world_id,character_id,previous_band,anchor_at,updated_at) "
                    "VALUES (?,?,?,?,?,?)",
                    (new_uuid(), world, character_id, entry["previous_band"], frozen, now),
                )
                conn.execute(
                    "INSERT INTO sleep_regulation_precision_state "
                    "(public_id,world_id,character_id,homeostatic_load_residue,"
                    "circadian_phase_residue,anchor_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                    (new_uuid(), world, character_id, float(entry["homeostatic_load_residue"]),
                     float(entry["circadian_phase_residue"]), frozen, now),
                )

            changed = conn.execute(
                "UPDATE world_physiology_system SET status='active',activated_at=?,"
                "activated_by=?,updated_at=? WHERE world_id=? AND status='prepared'",
                (now, actor, now, world),
            )
            if changed.rowcount != 1:
                raise SleepPhysiologyError(
                    "gate physiologique modifié pendant activation", code="activation_race"
                )

        return {
            "world_id": world, "status": "active", "model_key": ADDITIVE_MODEL_KEY,
            "model_version": 1, "anchor_at": frozen, "manifest_key": key,
            "manifest_version": ver, "character_count": len(characters),
            "activated_at": now, "activated_by": actor,
        }

'''
replace_once("src/vivarium/sleep_physiology.py", marker, method + marker)

write(
    "tests/test_physiology_activation.py",
    '''"""WO88F : cutover atomique depuis le manifeste T0 scellé."""
from dataclasses import asdict
from datetime import datetime, timezone

import pytest

from vivarium.circadian_model import calibration_profiles
from vivarium.db import connect_database
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.runtime_session import RuntimeSessionService
from vivarium.sleep_physiology import (
    ADDITIVE_MODEL_KEY,
    InitialPhysiologyManifestEntry,
    SleepPhysiologyError,
    SleepPhysiologyFoundationService,
    SleepPhysiologyService,
    V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY,
)
from vivarium.sleep_termination import SleepTerminationFoundationService
from vivarium.util import to_iso

T0_DT = datetime(2026, 8, 12, 21, 0, tzinfo=timezone.utc)
T0 = to_iso(T0_DT)


class FixedClock:
    def now(self):
        return T0_DT

    def now_iso(self):
        return T0


def profile():
    p = asdict(calibration_profiles()["human_reference_candidate.v1"])
    for key in ("profile_key", "version", "evidence_class"):
        p.pop(key)
    return {"model_key": ADDITIVE_MODEL_KEY, "parameters": p}


def configured_world(*, seal=True, prepare=True):
    conn = connect_database(":memory:")
    ensure_schema(conn)
    clock = FixedClock()
    wid = IntegrationWorldService(conn, clock=clock).create_initial_world()["id"]
    sessions = RuntimeSessionService(conn, clock=clock)
    sessions.stop(sessions.start(wid).session_id)
    f = SleepPhysiologyFoundationService(conn, clock=clock)
    f.register_light_schedule(
        "activation.day.v1", 1,
        {"schema_version": 1, "segments": [{"start_second": 0, "end_second": 86400, "environmental_light_milli": 90000}]},
    )
    f.register_location_light_profile("activation.indoor.v1", 1, 25000, {"kind": "indoor"})
    f.register_biology_profile("activation.human.v1", 1, "human_reference", profile())
    f.register_initial_physiology_policy(
        "activation.t0.v1", 1,
        {
            "schema_version": 1,
            "model_key": ADDITIVE_MODEL_KEY,
            "model_version": 1,
            "homeostatic_load_region": {"min_milli": 40000, "max_milli": 60000},
            "physical_capacity_region": {"min_milli": 70000, "max_milli": 90000},
            "bootstrap_rule": "wake_stability.stable_seed.v1",
            "residue_rule": "zero_at_t0.v1",
        },
        "test",
    )
    f.register_t0_phase_rule(
        "activation.phase.v1", 1,
        {
            "schema_version": 1,
            "rule_kind": "schedule_light_phase_windows.v1",
            "light_phase_windows": [[200000, 300000]],
            "dark_phase_windows": [[700000, 800000]],
        },
        "test",
    )
    f.register_physical_capacity_policy(
        "activation.p.v1", 1,
        {
            "schema_version": 1,
            "activity_cost_per_hour_milli": {"none": 3600, "light": 7200, "moderate": 10800, "vigorous": 18000},
            "minimum_capacity_milli": {"none": 0, "light": 10000, "moderate": 25000, "vigorous": 45000},
            "traversal_cost_per_edge_milli": 250,
            "recovery_per_hour_milli": {"rest": 7200, "sleep": 10800},
        },
        "test",
    )
    f.assign_light_schedule(wid, "activation.day.v1", 1, T0, "test")
    for row in conn.execute("SELECT key FROM location WHERE world_id=?", (wid,)):
        f.assign_location_light_profile(wid, row["key"], "activation.indoor.v1", 1, T0, "test")
    for row in conn.execute("SELECT key FROM character WHERE world_id=?", (wid,)):
        f.assign_biology_profile(wid, row["key"], "activation.human.v1", 1, "test")
    f.assign_physical_capacity_policy(wid, "activation.p.v1", 1, "test")
    for typ, load in V1_PHYSICAL_LOAD_CLASS_BY_ACTIVITY.items():
        conn.execute(
            "UPDATE activity_definition SET physical_load_class=? WHERE world_id=? AND activity_type=?",
            (load, wid, typ),
        )
    term = SleepTerminationFoundationService(conn, clock=clock)
    term.register_policy(
        "activation.sleep.v1", 1,
        {
            "schema_version": 1,
            "checkpoint_interval_seconds": 900,
            "hard_cap_seconds": 28800,
            "wake_admissible_enter_milli": 65000,
            "wake_admissible_exit_milli": 55000,
        },
        "test",
    )
    term.assign_policy(wid, "activation.sleep.v1", 1, "test")
    f.create_initial_physiology_manifest(
        wid, "rodage.t0.v1", 1, "activation.t0.v1", 1,
        "activation.phase.v1", 1, T0, "test", "T0 explicite",
    )
    for row in conn.execute("SELECT key FROM character WHERE world_id=? ORDER BY key", (wid,)):
        f.append_initial_physiology_manifest_entry(
            wid, "rodage.t0.v1", 1,
            InitialPhysiologyManifestEntry(
                row["key"], "activation.human.v1", 1, 50000, 250000,
                75000, "fragile", "test", "T0 explicite",
            ),
        )
    if seal:
        f.seal_initial_physiology_manifest(wid, "rodage.t0.v1", 1)
    if prepare:
        f.prepare_world(wid, ADDITIVE_MODEL_KEY, 1, "test")
    return conn, wid, clock, f


def legacy(conn, wid):
    return tuple(
        tuple(r)
        for r in conn.execute(
            "SELECT character_id,need_key,value_milli,rate_remainder,anchor_at "
            "FROM need_state WHERE world_id=? ORDER BY character_id,need_key",
            (wid,),
        )
    )


def test_activation_materializes_dense_owner_state_atomically_without_canonical_history():
    conn, wid, clock, f = configured_world()
    try:
        character_keys = tuple(
            row["key"]
            for row in conn.execute("SELECT key FROM character WHERE world_id=? ORDER BY key", (wid,))
        )
        expected_count = len(character_keys)
        before_legacy = legacy(conn, wid)
        before_events = conn.execute(
            "SELECT COUNT(*) FROM canonical_event WHERE world_id=?", (wid,)
        ).fetchone()[0]
        result = f.activate_world_from_initial_manifest(wid, "rodage.t0.v1", 1, "rodage_operator")
        assert result["status"] == "active"
        assert result["anchor_at"] == T0
        assert result["character_count"] == expected_count
        assert f.system_status(wid) == "active"
        assert legacy(conn, wid) == before_legacy
        assert conn.execute(
            "SELECT COUNT(*) FROM canonical_event WHERE world_id=?", (wid,)
        ).fetchone()[0] == before_events
        for table in (
            "sleep_regulation_state",
            "physical_capacity_state",
            "sleep_wake_hysteresis_state",
            "sleep_regulation_precision_state",
        ):
            assert conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE world_id=?", (wid,)
            ).fetchone()[0] == expected_count
        for key in character_keys:
            state = SleepPhysiologyService(conn, clock=clock).read_state(wid, key)
            assert state.anchor_at == T0
            assert state.regulation.homeostatic_load_milli == 50000
            assert state.regulation.physical_capacity_milli == 75000
    finally:
        conn.close()


def test_activation_refuses_unsealed_manifest_without_partial_state():
    conn, wid, clock, f = configured_world(seal=False)
    try:
        with pytest.raises(SleepPhysiologyError) as caught:
            f.activate_world_from_initial_manifest(wid, "rodage.t0.v1", 1, "test")
        assert caught.value.code == "manifest_not_sealed"
        assert f.system_status(wid) == "prepared"
        assert conn.execute(
            "SELECT COUNT(*) FROM sleep_regulation_state WHERE world_id=?", (wid,)
        ).fetchone()[0] == 0
    finally:
        conn.close()


def test_activation_refuses_open_runtime_and_rolls_back_preexisting_state():
    conn, wid, clock, f = configured_world()
    try:
        session = RuntimeSessionService(conn, clock=clock).start(wid)
        try:
            with pytest.raises(SleepPhysiologyError) as caught:
                f.activate_world_from_initial_manifest(wid, "rodage.t0.v1", 1, "test")
            assert caught.value.code == "runtime_session_open"
            assert f.system_status(wid) == "prepared"
        finally:
            RuntimeSessionService(conn, clock=clock).stop(session.session_id)
        cid = conn.execute(
            "SELECT id FROM character WHERE world_id=? ORDER BY id LIMIT 1", (wid,)
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO physical_capacity_state "
            "(public_id,world_id,character_id,capacity_milli,rate_remainder,anchor_at,updated_at) "
            "VALUES ('preexisting',?,?,75000,0,?,?)",
            (wid, cid, T0, T0),
        )
        with pytest.raises(SleepPhysiologyError) as caught:
            f.activate_world_from_initial_manifest(wid, "rodage.t0.v1", 1, "test")
        assert caught.value.code == "activation_state_exists"
        assert f.system_status(wid) == "prepared"
        assert conn.execute(
            "SELECT COUNT(*) FROM sleep_regulation_state WHERE world_id=?", (wid,)
        ).fetchone()[0] == 0
    finally:
        conn.close()


def test_activation_is_single_use_and_requires_prepared_gate():
    conn, wid, clock, f = configured_world()
    try:
        f.activate_world_from_initial_manifest(wid, "rodage.t0.v1", 1, "test")
        with pytest.raises(SleepPhysiologyError) as caught:
            f.activate_world_from_initial_manifest(wid, "rodage.t0.v1", 1, "test")
        assert caught.value.code == "physiology_not_prepared"
    finally:
        conn.close()
''',
)
