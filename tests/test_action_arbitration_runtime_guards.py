"""Gardes de falsification locales pour le raccord causal d'arbitrage."""

import sqlite3

import pytest

from vivarium.action_contract import ACTION_START_ACTIVITY
from vivarium.sleep_physiology import PhysicalCapacityPolicy
from vivarium.action_arbitration_runtime import (
    ActionArbitrationRuntimeError,
    CausalArbitrationBuilder,
)
from vivarium.action_contract import normalize_action_specification


def _policy() -> PhysicalCapacityPolicy:
    return PhysicalCapacityPolicy(
        "synthetic.guard.v1",
        1,
        {"none": 0, "light": 1, "moderate": 2, "vigorous": 3},
        {"none": 0, "light": 10, "moderate": 20, "vigorous": 30},
        1,
        {"rest": 1, "sleep": 2},
        "synthetic_test_only",
        "2026-08-12T12:00:00.000+00:00",
    )


def test_physical_evaluation_refuses_missing_activity_class_without_default():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE activity_definition ("
        "world_id INTEGER NOT NULL, activity_type TEXT NOT NULL, physical_load_class TEXT)"
    )
    conn.execute(
        "INSERT INTO activity_definition (world_id,activity_type,physical_load_class) "
        "VALUES (1,'sport',NULL)"
    )
    specification = normalize_action_specification(
        ACTION_START_ACTIVITY,
        {"activity_type": "sport", "target_location_key": "cour"},
    )
    try:
        with pytest.raises(ActionArbitrationRuntimeError) as raised:
            CausalArbitrationBuilder(conn)._physical_evaluation(
                1, specification, _policy(), 100_000
            )
        assert raised.value.code == "activity_physical_class_missing"
    finally:
        conn.close()
