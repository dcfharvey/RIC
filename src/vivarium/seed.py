"""Peuplement initial d'un monde de développement (Phase 1).

⚠️ Ce seed ne définit PAS l'ameublement définitif du futur vivarium. Il ne
fournit que des lieux de référence et quelques objets neutres destinés aux
tests du modèle de persistance. Aucun personnage n'est créé ici.
"""

from __future__ import annotations

# (clé interne stable, nom visible modifiable, type, capacité)
SEED_LOCATIONS: list[tuple[str, str, str, int | None]] = [
    ("salon", "Salon", "room", 6),
    ("cuisine", "Cuisine", "room", 4),
    ("salle_de_bain", "Salle de bain", "bathroom", 1),
    ("cour", "Cour", "outdoor", 8),
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
