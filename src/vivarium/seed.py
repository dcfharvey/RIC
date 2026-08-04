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

# Besoins de base (Sous-lot 3.2A) — calibration provisoire.
# (need_key, name, valeur initiale milli, rate_num, rate_den=36, seuil milli)
# Dénominateur canonique commun 36 : tous les taux en unités /36 par seconde.
# 70000 = 70,000 ; 0 = déficient ; 100000 = satisfait.
SEED_NEEDS: list[tuple[str, str, int, int, int, int]] = [
    ("satiete", "Satiété", 70000, -80, 36, 35000),
    ("repos", "Repos", 70000, -60, 36, 35000),
    ("energie", "Énergie", 70000, -50, 36, 30000),
    ("hygiene", "Hygiène", 80000, -30, 36, 40000),
]

# Activités de base (Sous-lot 3.2B) — calibration provisoire.
# (activity_type, min_duration_seconds, max_duration_seconds,
#  satiete_rate, repos_rate, energie_rate, hygiene_rate)  -- tous /36 par seconde
SEED_ACTIVITIES: list[tuple[str, int, int, int, int, int, int]] = [
    # idle : durée dynamique (portée par Intent, 1..MAX_IDLE) ; ici plage de sécurité
    ("idle", 1, 28800, -80, -60, -50, -30),
    ("eat", 1800, 1800, 1200, -60, 32, -30),
    ("rest", 3600, 3600, -80, 30, 27, -30),
    ("clean", 900, 900, -80, -60, -50, 2400),
    ("sleep", 0, 28800, -32, 80, 50, -18),
]

# Lieux autorisés par activité (key OU kind, jamais les deux).
# (activity_type, location_key|None, location_kind|None)
SEED_ACTIVITY_ALLOWED: list[tuple[str, str | None, str | None]] = [
    ("eat", "cuisine", None),
    ("clean", "salle_de_bain", None),
    ("rest", "salon", None),
    ("rest", None, "bedroom"),
    ("sleep", None, "bedroom"),
    # idle : lieu courant (aucune règle)
]

# Profils seedés — valeurs NEUTRES identiques pour les 4 habitantes (3.2C).
# Aucune différence canonique dérivée de la calibration ; les variations ne
# doivent exister que dans des tests ciblés. Tout paramètre en milli.
SEED_PROFILES: list[dict[str, int]] = [
    {
        "satiete_threshold_mult_milli": 1000,
        "repos_threshold_mult_milli": 1000,
        "energie_threshold_mult_milli": 1000,
        "hygiene_threshold_mult_milli": 1000,
        "rest_preference_milli": 0,
        "idle_tolerance_milli": 0,
    }
    for _ in range(4)
]
