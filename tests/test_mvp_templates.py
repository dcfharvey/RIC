import pytest

from vivarium.db import connect_database
from vivarium.migrations import ensure_schema
from vivarium.mvp_templates import MVP_CHARACTER_TEMPLATES, install_mvp_character_templates
from vivarium.templates import CharacterTemplateService


@pytest.fixture
def conn():
    database = connect_database(":memory:")
    ensure_schema(database)
    yield database
    database.close()


def test_mvp_templates_are_published_and_idempotent(conn):
    installed = install_mvp_character_templates(conn)

    assert [item["key"] for item in installed] == [entry[0] for entry in MVP_CHARACTER_TEMPLATES]
    assert all(item["status"] == "published" for item in installed)
    assert install_mvp_character_templates(conn) == installed
    chuu = CharacterTemplateService(conn).get_version("resident.chuu", 1)
    assert any(component["key"] == "physiology.resource_dependent_state" for component in chuu["components"])


def test_mvp_templates_do_not_overwrite_existing_versions(conn):
    install_mvp_character_templates(conn)
    templates = CharacterTemplateService(conn)
    templates.create_draft(
        "resident.sophie",
        {"name": "Sophie différente", "adult": True},
        [{"key": "body.morphology", "version": 1, "config": {"body_plan": "bipedal"}}],
    )
    # Une nouvelle version personnelle est permise; le catalogue v1 reste intact.
    install_mvp_character_templates(conn)
    assert templates.get_version("resident.sophie", 1)["definition"]["name"] == "Sophie"
