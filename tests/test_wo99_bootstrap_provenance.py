from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import subprocess

import pytest

from vivarium.db import connect_database
from vivarium.cli import _run_mvp_runtime
from vivarium.integration_world import IntegrationWorldService
from vivarium.migrations import ensure_schema
from vivarium.mvp_runtime import MVPRuntime, MVPRuntimeError
from vivarium.official_runtime import OfficialRuntimeError, validate_official_world
from vivarium.rodage_v2_official import OfficialBootstrapError, bootstrap_official
from vivarium.runtime_provenance import RuntimeProvenanceError, verify_runtime_provenance
from vivarium.util import Clock


class FakeClock(Clock):
    def now(self):
        return datetime(2026, 8, 13, 15, tzinfo=timezone.utc)


def _git_head(ref: str) -> str:
    return subprocess.run(
        ["git", "rev-parse", ref], check=True, capture_output=True, text=True
    ).stdout.strip()


def test_official_bootstrap_reports_active_engine_and_provenance(tmp_path: Path):
    checkout = Path(__file__).resolve().parents[1]
    runtime_head = _git_head("HEAD")
    product_head = _git_head("origin/product/current")
    db = tmp_path / "official.sqlite"
    report = bootstrap_official(
        db,
        clock=FakeClock(),
        launch_runtime=False,
        provider_checker=lambda: "qwen3-14b",
        expected_checkout_root=checkout,
        expected_runtime_head=runtime_head,
        expected_product_head=product_head,
    )

    assert report.product_head == product_head
    assert report.runtime_head == runtime_head
    assert report.python_package_root == str(checkout / "src" / "vivarium")
    assert report.physiology_status == "active"
    assert report.initial_manifest
    assert report.biological_assignments == 5
    assert report.simulation_engine == "ActiveSimulationEngine"
    assert report.session_id is None


def test_official_runtime_rejects_inactive_physiology(tmp_path: Path):
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world_id = IntegrationWorldService(conn, clock=FakeClock()).create_initial_world()["id"]
    runtime = MVPRuntime(conn, world_id, simulation_contract="active")

    with pytest.raises(MVPRuntimeError) as exc:
        runtime.run_once()
    assert exc.value.code == "official_physiology_inactive"
    conn.close()


def test_official_validation_rejects_incomplete_physiology_state(tmp_path: Path):
    db = tmp_path / "incomplete.sqlite"
    report = bootstrap_official(
        db, clock=FakeClock(), launch_runtime=False, provider_checker=lambda: "qwen3-14b"
    )
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("DELETE FROM sleep_regulation_precision_state WHERE world_id=?", (report.world_id,))
        conn.commit()
        with pytest.raises(OfficialRuntimeError) as exc:
            validate_official_world(conn, report.world_id, database_path=db)
        assert exc.value.code == "physiology_state_incomplete"
    finally:
        conn.close()


def test_official_bootstrap_requires_provenance_when_opening_runtime(tmp_path: Path):
    with pytest.raises(OfficialBootstrapError) as exc:
        bootstrap_official(
            tmp_path / "missing-proof.sqlite",
            clock=FakeClock(),
            launch_runtime=True,
            provider_checker=lambda: "qwen3-14b",
        )
    assert exc.value.code == "runtime_provenance_required"


def test_runtime_provenance_rejects_other_checkout_and_wrong_head():
    checkout = Path(__file__).resolve().parents[1]
    runtime_head = _git_head("HEAD")
    product_head = _git_head("origin/product/current")
    with pytest.raises(RuntimeProvenanceError) as exc:
        verify_runtime_provenance(
            expected_checkout_root=checkout.parent,
            expected_runtime_head=runtime_head,
            expected_product_head=product_head,
        )
    assert exc.value.code == "python_package_root_mismatch"

    with pytest.raises(RuntimeProvenanceError) as exc:
        verify_runtime_provenance(
            expected_checkout_root=checkout,
            expected_runtime_head="0" * 40,
            expected_product_head=product_head,
        )
    assert exc.value.code == "runtime_head_mismatch"


def test_official_cli_refuses_wrong_checkout_before_opening_database(tmp_path: Path):
    checkout = Path(__file__).resolve().parents[1]
    runtime_head = _git_head("HEAD")
    product_head = _git_head("origin/product/current")
    result = _run_mvp_runtime(
        tmp_path / "does-not-exist.sqlite",
        None,
        enable_local_llm=False,
        port=0,
        tick_seconds=1.0,
        max_ticks=1,
        guardian_interval=60,
        official_checkout_root=checkout.parent,
        official_runtime_head=runtime_head,
        official_product_head=product_head,
    )
    assert result == 2


def test_generic_runtime_keeps_explicit_legacy_contract():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world_id = IntegrationWorldService(conn, clock=FakeClock()).create_initial_world()["id"]
    runtime = MVPRuntime(conn, world_id)

    assert runtime.simulation_engine_name() == "SimulationEngine"
    assert runtime.run_once().simulation is not None
    conn.close()
