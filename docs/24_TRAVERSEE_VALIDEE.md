# Traversée validée

**Statut :** lot C initial implémenté (aucune migration nouvelle).

## De la carte au franchissement réel

`GraphEngine` trouve un chemin dans la carte. `TraversalEngine` traite une
tentative concrète : « ce personnage franchit ce connecteur vers ce lieu ».

Il vérifie en lecture puis dans la même transaction :

1. l'existence du personnage et sa position actuelle;
2. sa présence à une extrémité du connecteur;
3. le bon sens et la bonne destination;
4. l'état du connecteur;
5. la cohérence entre ce connecteur et l'arête topologique;
6. les garde-fous existants du déplacement (pause, activité active, blessure,
   énergie), avant de modifier la position.

Un refus ne modifie ni position, ni blessure, ni énergie, ni journal.

## Interaction avec pathfinding

Le pathfinding peut produire `chambre → couloir → salon → porte → cour`. Il ne
franchit rien. La traversée applique une étape à la fois et peut échouer sur
une porte fermée. La cognition future reçoit alors un refus stable comme
`connector_closed`, à partir duquel elle peut proposer une nouvelle action :
frapper, attendre, appeler, chercher une autre entrée ou utiliser un accès réel
quand ces systèmes existeront.

## Compatibilité et limite

Les mondes techniques historiques ont des arêtes sans instance de connecteur;
leurs déplacements restent compatibles. Dans un monde créé par blueprint, même
`CharacterEngine.move_character` respecte désormais l'état du connecteur et
enregistre sa clé dans `character_moved`. Ainsi, un ancien appel interne ne
peut pas contourner une porte fermée.

Les capacités (nager, grimper, se faufiler), les ressources et permissions
seront ajoutées comme validateurs explicites quand une règle concrète les
nécessitera. Elles ne sont pas inventées dans ce lot.

## Preuves

`tests/test_traversal.py` couvre prévisualisation, événement causal, porte
fermée, rollback complet et compatibilité de l'ancien déplacement avec un
connecteur instancié.
