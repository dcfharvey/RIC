import pytest

from vivarium.db import connect_database
from vivarium.migrations import ensure_schema
from vivarium.registry import RegistryService
from vivarium.templates import CharacterTemplateService, TemplateError


BIOLOGICAL_BODY = [{"key": "body.biological", "version": 1, "config": {}}]


@pytest.fixture
def services():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    registry = RegistryService(conn)
    registry.create_draft("component", "body.biological", {})
    registry.publish("component", "body.biological", 1)
    yield CharacterTemplateService(conn)
    conn.close()


def test_template_requires_published_components_and_versions_are_immutable(services):
    draft = services.create_draft(
        "human.sophie", {"name": "Sophie"}, BIOLOGICAL_BODY
    )
    assert draft["status"] == "draft"
    assert services.publish("human.sophie", 1)["status"] == "published"
    with pytest.raises(Exception, match="immutable"):
        services._conn.execute(
            "UPDATE character_template_version SET definition_json = '{}' WHERE version = 1"
        )

    v2 = services.create_draft(
        "human.sophie", {"name": "Sophie V2"}, BIOLOGICAL_BODY
    )
    assert v2["version"] == 2
    assert services.get_version("human.sophie", 1)["definition"] == {"name": "Sophie"}


def test_template_refuses_missing_component(services):
    services.create_draft(
        "human.erika", {}, [{"key": "body.missing", "version": 1, "config": {}}]
    )
    with pytest.raises(TemplateError, match="component_not_published"):
        services.publish("human.erika", 1)
    assert services.get_version("human.erika", 1)["status"] == "draft"


def test_template_refuses_ambiguous_or_invalid_component_bindings(services):
    with pytest.raises(TemplateError, match="liaison"):
        services.create_draft("human.invalid", {}, ["body.biological"])
    with pytest.raises(TemplateError, match="liaison"):
        services.create_draft(
            "human.invalid", {}, [{"key": "body.biological", "version": True, "config": {}}]
        )


def test_template_validates_component_configuration(services):
    registry = RegistryService(services._conn)
    registry.create_draft(
        "component",
        "body.typed",
        {
            "config_schema": {
                "required": ["mass_kg"],
                "properties": {
                    "mass_kg": {"type": "number", "minimum": 1, "maximum": 500}
                },
                "additional_properties": False,
            }
        },
    )
    registry.publish("component", "body.typed", 1)
    services.create_draft(
        "human.schema", {}, [{"key": "body.typed", "version": 1, "config": {"mass_kg": 0}}]
    )
    report = services.validate("human.schema", 1)
    assert report["valid"] is False
    assert report["errors"] == [
        {"code": "config_below_minimum", "component": "body.typed", "field": "mass_kg"}
    ]
    with pytest.raises(TemplateError, match="config_below_minimum"):
        services.publish("human.schema", 1)


def test_template_binds_a_component_version_without_drifting_to_later_versions(services):
    registry = RegistryService(services._conn)
    registry.create_draft("component", "body.biological", {"title": "Body v2"})
    registry.publish("component", "body.biological", 2)

    services.create_draft("human.pinned", {}, BIOLOGICAL_BODY)
    published = services.publish("human.pinned", 1)

    assert published["components"] == BIOLOGICAL_BODY
