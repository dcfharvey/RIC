import json

import pytest

from vivarium.db import connect_database
from vivarium.instances import CharacterInstanceService, InstanceError
from vivarium.migrations import ensure_schema
from vivarium.registry import RegistryService
from vivarium.templates import CharacterTemplateService
from vivarium.world import WorldEngine


def _publish_sophie_template(conn):
    registry = RegistryService(conn)
    registry.create_draft("component", "body.biological", {})
    registry.publish("component", "body.biological", 1)
    templates = CharacterTemplateService(conn)
    templates.create_draft(
        "human.sophie",
        {"name": "Sophie", "adult": True},
        [{"key": "body.biological", "version": 1, "config": {}}],
    )
    templates.publish("human.sophie", 1)


@pytest.fixture
def setup():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    world = WorldEngine(conn).init_world(name="Instances")
    _publish_sophie_template(conn)
    yield conn, world["id"], CharacterInstanceService(conn)
    conn.close()


def test_instantiation_is_canonical_and_keeps_immutable_origin(setup):
    conn, world_id, instances = setup

    sheet = instances.instantiate(world_id, "human.sophie", 1, "sophie", "chambre_1")

    assert sheet["name"] == "Sophie"
    assert sheet["location_key"] == "chambre_1"
    assert instances.origin(world_id, "sophie")["resolved_initial_definition"] == {
        "definition": {"adult": True, "name": "Sophie"},
        "components": [{"config": {}, "key": "body.biological", "version": 1}],
    }
    assert conn.execute(
        "SELECT COUNT(*) FROM need_state WHERE world_id = ? AND character_id = ?",
        (world_id, sheet["id"]),
    ).fetchone()[0] == 4
    event = conn.execute(
        "SELECT payload FROM canonical_event WHERE world_id = ? "
        "AND event_type = 'character_instantiated'",
        (world_id,),
    ).fetchone()
    assert json.loads(event["payload"])["template_version"] == 1
    with pytest.raises(Exception, match="immutable"):
        conn.execute(
            "UPDATE character_instance_origin SET template_version = 2 WHERE character_id = ?",
            (sheet["id"],),
        )


def test_instantiation_refusal_is_atomic(setup):
    conn, world_id, instances = setup
    before = conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)
    ).fetchone()[0]

    with pytest.raises(InstanceError, match="lieu"):
        instances.instantiate(world_id, "human.sophie", 1, "sophie", "unknown.room")

    assert conn.execute(
        "SELECT COUNT(*) FROM character WHERE world_id = ? AND key = 'sophie'", (world_id,)
    ).fetchone()[0] == 0
    assert conn.execute(
        "SELECT COUNT(*) FROM canonical_event WHERE world_id = ?", (world_id,)
    ).fetchone()[0] == before


def test_instantiation_requires_explicit_adult_name_and_unused_key(setup):
    conn, world_id, instances = setup
    templates = CharacterTemplateService(conn)
    templates.create_draft(
        "invalid.child", {"name": "", "adult": False},
        [{"key": "body.biological", "version": 1, "config": {}}],
    )
    templates.publish("invalid.child", 1)
    with pytest.raises(InstanceError, match="nom"):
        instances.instantiate(world_id, "invalid.child", 1, "invalid", "chambre_1")

    instances.instantiate(world_id, "human.sophie", 1, "sophie", "chambre_1")
    with pytest.raises(InstanceError, match="déjà utilisée"):
        instances.instantiate(world_id, "human.sophie", 1, "sophie", "chambre_2")


def test_instance_origin_persists_after_reopening_database(tmp_path):
    path = tmp_path / "instances.db"
    conn = connect_database(path)
    ensure_schema(conn)
    world = WorldEngine(conn).init_world(name="Persistence")
    _publish_sophie_template(conn)
    CharacterInstanceService(conn).instantiate(
        world["id"], "human.sophie", 1, "sophie", "chambre_1"
    )
    conn.close()

    conn = connect_database(path)
    try:
        ensure_schema(conn)
        origin = CharacterInstanceService(conn).origin(world["id"], "sophie")
        assert origin["template_key"] == "human.sophie"
        assert origin["template_version"] == 1
    finally:
        conn.close()


def test_failed_development_world_destruction_rolls_back_instance_data(setup):
    conn, world_id, instances = setup
    instances.instantiate(world_id, "human.sophie", 1, "sophie", "chambre_1")

    with pytest.raises(Exception, match="FOREIGN KEY"):
        WorldEngine(conn).destroy_world(world_id)

    assert instances.origin(world_id, "sophie")["template_key"] == "human.sophie"
