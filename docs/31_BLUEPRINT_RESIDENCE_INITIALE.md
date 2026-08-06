# Blueprint de la résidence initiale

**Statut :** catalogue v1 publié et testé; aucune instance persistante du monde
d'intégration n'est encore créée.

## Ce qui est livré

`vivarium.initial_residence.install_initial_residence_catalog` installe,
atomiquement et sans écraser une version existante :

- les presets de lieux et connecteurs nécessaires;
- le blueprint publié `residence.initial`;
- les 15 lieux, 14 connecteurs et installations fixes de la résidence.

Le catalogue peut être installé dans n'importe quelle base vide ou existante;
il ne crée pas de monde. Une incompatibilité avec une version 1 déjà publiée
échoue sans correction silencieuse.

## Plan retenu

- entrée extérieure ↔ salon : porte;
- entrée extérieure ↔ stationnement : passage extérieur;
- salon ↔ cuisine et salon ↔ couloir : arches ouvertes;
- couloir ↔ chambres, salle de bain, buanderie et sous-sol : portes;
- cuisine ↔ cour arrière : porte patio;
- cour arrière ↔ remise : porte;
- cour arrière ↔ piscine : échelle.

L'entrée extérieure contient la boîte aux lettres, point d'arrivée commun. La
cuisine contient la table; aucune salle à manger séparée n'est créée.

Les connecteurs du blueprint commencent `available`. « Une porte existe » n'a
pas été interprété comme « elle est fermée au premier instant » : un état fermé
devra être un fait explicitement choisi pour un scénario. Le blueprint sait
désormais toutefois déclarer un état initial `available`, `closed` ou `blocked`
et refuse `closed` pour un connecteur non fermable.

## Limites assumées

- le grenier n'est pas encore instancié : son escalier escamotable exige un
  type de connecteur rétractable, absent du moteur actuel;
- les quatre téléphones et le port des objets par personnage attendent le lot
  d'équipement, donc aucun téléphone n'est posé artificiellement au sol;
- les machines, piscine, télévision et autres objets existent comme faits
  fixes, mais leurs fonctions détaillées ne sont pas encore simulées;
- les chambres sont neutres : elles ne sont attribuées à personne avant une
  décision ou un mécanisme explicite.

## Preuves

Les catalogues globaux et leur prévalidation atomique sont couverts par
`tests/test_environment_catalogs.py`. La recette de résidence est couverte par
`tests/test_initial_residence.py`; elle vérifie l'idempotence, l'instanciation,
le trajet entrée→piscine, la boîte aux lettres et le comptage des objets.
