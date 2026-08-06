"""Catalogue versionné de la résidence initiale du monde d'intégration."""

from __future__ import annotations

import sqlite3

from .environment_archetypes import EnvironmentArchetypeService
from .environment_blueprints import EnvironmentBlueprintService


def _place(name: str, functions: tuple[str, ...], slots: tuple[str, ...]) -> dict[str, object]:
    return {
        "name": name,
        "medium": "air",
        "functions": list(functions),
        "max_occupancy": None,
        "installation_slots": list(slots),
    }


INITIAL_RESIDENCE_ARCHETYPES = (
    ("place", "entry_exterior", _place("Entrée extérieure", ("arrive",), ("mailbox",))),
    ("place", "parking", _place("Stationnement extérieur", ("park",), ())),
    ("place", "salon", _place("Salon", ("socialize", "relax"), ("seating", "media"))),
    ("place", "cuisine", _place("Cuisine", ("cook", "eat"), ("appliances", "dining"))),
    ("place", "hallway", _place("Couloir", ("circulate",), ())),
    ("place", "salle_de_bain", _place("Salle de bain", ("bathe", "clean"), ("bath", "sanitary"))),
    ("place", "bedroom", _place("Chambre", ("sleep", "private"), ("bed", "storage", "desk"))),
    ("place", "laundry_room", _place("Buanderie", ("launder",), ("laundry"))),
    ("place", "backyard", _place("Cour arrière", ("outdoor", "swim"), ("pool", "shed"))),
    ("place", "pool", {
        "name": "Piscine creusée", "medium": "water", "functions": ["swim", "bathe"],
        "max_occupancy": None, "installation_slots": [],
    }),
    ("place", "shed", _place("Remise", ("store",), ("storage",))),
    ("place", "basement", _place("Sous-sol", ("maintain", "store"), ("utilities",))),
    ("connector", "door", {
        "name": "Porte", "traversal_modes": ["walk"], "directions": "bidirectional",
        "features": ["closable"],
    }),
    ("connector", "open_arch", {
        "name": "Arche ouverte", "traversal_modes": ["walk"], "directions": "bidirectional",
        "features": ["open"],
    }),
    ("connector", "patio_door", {
        "name": "Porte patio", "traversal_modes": ["walk"], "directions": "bidirectional",
        "features": ["closable", "exterior"],
    }),
    ("connector", "exterior_path", {
        "name": "Passage extérieur", "traversal_modes": ["walk"], "directions": "bidirectional",
        "features": ["open", "exterior"],
    }),
    ("connector", "pool_ladder", {
        "name": "Échelle de piscine", "traversal_modes": ["climb"], "directions": "bidirectional",
        "features": ["vertical", "water_access"],
    }),
)


def _ref(key: str) -> dict[str, object]:
    return {"key": key, "version": 1}


def _location(key: str, name: str, archetype: str) -> dict[str, object]:
    return {"key": key, "name": name, "archetype": _ref(archetype)}


def _connector(key: str, source: str, target: str, archetype: str) -> dict[str, object]:
    return {
        "key": key, "from": source, "to": target, "archetype": _ref(archetype),
        "initial_state": "available",
    }


def _object(
    key: str, name: str, kind: str, location: str, *, portable: bool = False,
    capacity: int | None = None,
) -> dict[str, object]:
    return {
        "key": key, "name": name, "kind": kind, "location": location,
        "portable": portable, "container_capacity": capacity, "state": "present",
    }


_BEDROOM_OBJECTS = tuple(
    item
    for number in range(1, 5)
    for item in (
        _object(f"lit_chambre_{number}", "Lit", "bed", f"chambre_{number}"),
        _object(f"armoire_chambre_{number}", "Armoire à linge", "wardrobe", f"chambre_{number}", capacity=30),
        _object(f"bureau_chambre_{number}", "Bureau", "desk", f"chambre_{number}"),
        _object(f"chaise_bureau_chambre_{number}", "Chaise de bureau", "chair", f"chambre_{number}"),
    )
)


INITIAL_RESIDENCE_BLUEPRINT = (
    "residence.initial",
    {
        "name": "Résidence initiale",
        "topology": {"policy": "strong_anchor", "anchor": "salon"},
        "locations": [
            _location("entree_exterieure", "Entrée extérieure", "entry_exterior"),
            _location("stationnement", "Stationnement extérieur", "parking"),
            _location("salon", "Salon", "salon"),
            _location("cuisine", "Cuisine", "cuisine"),
            _location("couloir", "Couloir", "hallway"),
            _location("salle_de_bain", "Salle de bain", "salle_de_bain"),
            *[_location(f"chambre_{number}", f"Chambre {number}", "bedroom") for number in range(1, 5)],
            _location("buanderie", "Buanderie", "laundry_room"),
            _location("cour_arriere", "Cour arrière", "backyard"),
            _location("piscine", "Piscine creusée", "pool"),
            _location("remise", "Remise", "shed"),
            _location("sous_sol", "Sous-sol", "basement"),
        ],
        "connectors": [
            _connector("porte_entree", "entree_exterieure", "salon", "door"),
            _connector("passage_stationnement", "entree_exterieure", "stationnement", "exterior_path"),
            _connector("arche_salon_cuisine", "salon", "cuisine", "open_arch"),
            _connector("arche_salon_couloir", "salon", "couloir", "open_arch"),
            *[_connector(f"porte_chambre_{number}", "couloir", f"chambre_{number}", "door") for number in range(1, 5)],
            _connector("porte_salle_de_bain", "couloir", "salle_de_bain", "door"),
            _connector("porte_buanderie", "couloir", "buanderie", "door"),
            _connector("porte_sous_sol", "couloir", "sous_sol", "door"),
            _connector("porte_patio", "cuisine", "cour_arriere", "patio_door"),
            _connector("porte_remise", "cour_arriere", "remise", "door"),
            _connector("echelle_piscine", "cour_arriere", "piscine", "pool_ladder"),
        ],
        "objects": [
            _object("boite_aux_lettres", "Boîte aux lettres", "mailbox", "entree_exterieure"),
            _object("refrigerateur", "Réfrigérateur", "refrigerator", "cuisine"),
            _object("four", "Four", "oven", "cuisine"),
            _object("four_micro_ondes", "Four micro-ondes", "microwave", "cuisine"),
            _object("lave_vaisselle", "Lave-vaisselle", "dishwasher", "cuisine"),
            _object("table_a_manger", "Table à manger", "dining_table", "cuisine"),
            *[_object(f"chaise_cuisine_{number}", "Chaise", "chair", "cuisine") for number in range(1, 5)],
            _object("bain", "Bain", "bathtub", "salle_de_bain"),
            _object("douche", "Douche", "shower", "salle_de_bain"),
            _object("toilette", "Toilette", "toilet", "salle_de_bain"),
            _object("litiere_patoune", "Litière", "litter_box", "salle_de_bain"),
            _object("vanite", "Vanité", "vanity", "salle_de_bain", capacity=6),
            _object("miroir_salle_de_bain", "Miroir", "mirror", "salle_de_bain"),
            *_BEDROOM_OBJECTS,
            _object("laveuse", "Laveuse", "washing_machine", "buanderie", capacity=12),
            _object("secheuse", "Sécheuse", "dryer", "buanderie", capacity=12),
            _object("divan", "Divan", "sofa", "salon"),
            _object("television", "Télévision", "television", "salon"),
            _object("meuble_tele", "Meuble de télévision", "tv_stand", "salon", capacity=6),
            _object("console_jeux", "Console de jeux vidéo", "game_console", "salon", portable=True),
            _object("ordinateur_commun", "Ordinateur partagé", "computer", "salon", portable=True),
            _object("cloture", "Clôture", "fence", "cour_arriere"),
            _object("chauffe_eau", "Chauffe-eau", "water_heater", "sous_sol"),
            _object("panneau_electrique", "Panneau électrique", "electrical_panel", "sous_sol"),
        ],
    },
)


def install_initial_residence_catalog(conn: sqlite3.Connection) -> dict[str, object]:
    """Installe ou vérifie les recettes v1 de la résidence, sans créer de monde."""
    archetypes = EnvironmentArchetypeService(conn).install_published_catalog(
        INITIAL_RESIDENCE_ARCHETYPES
    )
    blueprints = EnvironmentBlueprintService(conn).install_published_catalog(
        (INITIAL_RESIDENCE_BLUEPRINT,)
    )
    return {"archetypes": archetypes, "blueprint": blueprints[0]}
