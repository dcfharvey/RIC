from vivarium.connectors import WorldConnectorService
from vivarium.db import connect_database
from vivarium.environment_blueprints import EnvironmentBlueprintService
from vivarium.initial_residence import install_initial_residence_catalog
from vivarium.migrations import ensure_schema
from vivarium.spatial import GraphEngine


def test_initial_residence_catalog_is_generic_idempotent_and_instantiable():
    conn = connect_database(":memory:")
    ensure_schema(conn)
    try:
        installed = install_initial_residence_catalog(conn)
        assert installed == install_initial_residence_catalog(conn)
        blueprint = installed["blueprint"]
        assert blueprint["key"] == "residence.initial"
        assert blueprint["status"] == "published"
        assert "grenier" not in {item["key"] for item in blueprint["definition"]["locations"]}

        world = EnvironmentBlueprintService(conn).instantiate("residence.initial", 1)

        assert GraphEngine(conn).find_path(world["id"], "entree_exterieure", "piscine") == [
            "entree_exterieure", "salon", "cuisine", "cour_arriere", "piscine"
        ]
        assert WorldConnectorService(conn).connector_sheet(world["id"], "porte_patio")["state"] == "available"
        assert conn.execute(
            "SELECT COUNT(*) FROM world_object WHERE world_id = ?", (world["id"],)
        ).fetchone()[0] == len(blueprint["definition"]["objects"])
        assert conn.execute(
            "SELECT COUNT(*) FROM world_object WHERE world_id = ? AND key = 'boite_aux_lettres' "
            "AND location_id = (SELECT id FROM location WHERE world_id = ? AND key = 'entree_exterieure')",
            (world["id"], world["id"]),
        ).fetchone()[0] == 1
    finally:
        conn.close()
