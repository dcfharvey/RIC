"""Peuplement initial d'un monde de développement (Phase 1 + Lot 2.2).

⚠️ Ce seed ne définit PAS l'ameublement définitif du futur vivarium. Il ne
fournit que des lieux de référence et quelques objets neutres destinés aux
tests du modèle de persistance. Aucun personnage n'est créé ici.

Depuis le Lot 2.2, un neuvième lieu (`couloir`, type `circulation`) et un
graphe de passages physiques bidirectionnels sont ajoutés.
"""

from __future__ import annotations

# (clé interne stable, nom visible modifiable, type, capacité)
SEED_LOCATIONS: list[tuple[str, str, str, int | None]] = [
    ("salon", "Salon", "room", 6),
    ("cuisine", "Cuisine", "room", 4),
    ("salle_de_bain", "Salle de bain", "bathroom", 1),
    ("cour", "Cour", "outdoor", 8),
    ("couloir", "Couloir", "circulation", 8),
    ("chambre_1", "Chambre 1", "bedroom", 1),
    ("chambre_2", "Chambre 2", "bedroom", 1),
    ("chambre_3", "Chambre 3", "bedroom", 1),
    ("chambre_4", "Chambre 4", "bedroom", 1),
]

# (clé interne stable, nom visible, type, clé de lieu cible)
SEED_OBJECTS: list[tuple[str, str, str, str]] = [
    ("table", "Table", "furniture", "cuisine"),
    ("chaise", "Chaise", "furniture", "salon"),
    ("lit", "Lit", "furniture", "chambre_1"),
]

# Passages physiques **bidirectionnels** (chaque paire produit deux arêtes
# dirigées réciproques dans `location_link`).
SEED_LINKS: list[tuple[str, str]] = [
    ("salon", "cuisine"),
    ("salon", "couloir"),
    ("salon", "cour"),
    ("couloir", "salle_de_bain"),
    ("couloir", "chambre_1"),
    ("couloir", "chambre_2"),
    ("couloir", "chambre_3"),
    ("couloir", "chambre_4"),
]

# Quatre habitantes **provisoires** de développement (Lot 3.1).
# (clé interne immuable, nom visible provisoire, lieu de départ)
# Aucune personnalité ni biographie inventée. `key` reste l'identifiant
# technique définitif ; seuls `name` et de futurs profils seront modifiés.
SEED_CHARACTERS: list[tuple[str, str, str]] = [
    ("character_1", "Personnage 1", "chambre_1"),
    ("character_2", "Personnage 2", "chambre_2"),
    ("character_3", "Personnage 3", "chambre_3"),
    ("character_4", "Personnage 4", "chambre_4"),
]
