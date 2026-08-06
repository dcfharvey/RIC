import pytest

from vivarium.db import connect_database
from vivarium.environment_archetypes import EnvironmentArchetypeError, EnvironmentArchetypeService
from vivarium.environment_blueprints import BlueprintError, EnvironmentBlueprintService
from vivarium.migrations import ensure_schema


PLACE = (
    "place",
    "room",
    {
        "name": "Pièce",
        "medium": "air",
        "functions": ["socialize"],
        "max_occupancy": 4,
        "installation_slots": ["furniture"],
    },
)
DOOR = (
    "connector",
    "door",
    {
        "name": "Porte",
        "traversal_modes": ["walk"],
        "directions": "bidirectional",
        "features": ["closable"],
    },
)
BLUEPRINT = (
    "catalog_home",
    {
        "name": "Maison catalogue",
        "topology": {"policy": "strong_anchor", "anchor": "salon"},
        "locations": [
            {"key": "salon", "name": "Salon", "archetype": {"key": "room", "version": 1}},
            {"key": "cuisine", "name": "Cuisine", "archetype": {"key": "room", "version": 1}},
        ],
        "connectors": [{
            "key": "door_salon_cuisine",
            "from": "salon",
            "to": "cuisine",
            "archetype": {"key": "door", "version": 1},
            "initial_state": "closed",
        }],
        "objects": [],
    },
)


@pytest.fixture
def conn():
    database = connect_database(":memory:")
    ensure_schema(database)
    yield database
    database.close()


def test_archetype_catalog_is_atomic_idempotent_and_conflict_aware(conn):
    archetypes = EnvironmentArchetypeService(conn)

    installed = archetypes.install_published_catalog((PLACE, DOOR))

    assert [(item["kind"], item["key"], item["version"]) for item in installed] == [
        ("place", "room", 1), ("connector", "door", 1)
    ]
    assert archetypes.install_published_catalog((PLACE, DOOR)) == installed
    incompatible = ("place", "room", {**PLACE[2], "max_occupancy": 5})
    with pytest.raises(EnvironmentArchetypeError, match="incompatible"):
        archetypes.install_published_catalog((incompatible,))
    assert conn.execute("SELECT COUNT(*) FROM environment_archetype_version").fetchone()[0] == 2


def test_blueprint_catalog_preflights_all_entries_without_partial_write(conn):
    archetypes = EnvironmentArchetypeService(conn)
    archetypes.install_published_catalog((PLACE, DOOR))
    blueprints = EnvironmentBlueprintService(conn)
    invalid = (
        "missing_archetype",
        {**BLUEPRINT[1], "locations": [{
            "key": "salon", "name": "Salon", "archetype": {"key": "missing", "version": 1}
        }], "connectors": [], "objects": [], "topology": {"policy": "none"}},
    )

    with pytest.raises(BlueprintError, match="archetype publie introuvable"):
        blueprints.install_published_catalog((BLUEPRINT, invalid))

    assert conn.execute("SELECT COUNT(*) FROM environment_blueprint").fetchone()[0] == 0
    installed = blueprints.install_published_catalog((BLUEPRINT,))
    assert installed[0]["status"] == "published"
    assert blueprints.install_published_catalog((BLUEPRINT,)) == installed
