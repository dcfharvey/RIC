# Presets de lieux et connecteurs

**Statut :** socle de contrats implémenté (migration `0019`).

## Ce que sont les presets

Un preset est une recette versionnée et publiée, pas un lieu existant. Il
permettra à un blueprint de dire « cette instance est une chambre » ou
« cette relation est une échelle » sans faire d'une résidence la loi du
moteur.

Deux familles sont volontairement distinctes :

- un preset de **lieu** déclare son nom, son milieu, ses fonctions possibles,
  une capacité d'occupation optionnelle et des emplacements d'installations;
- un preset de **connecteur** déclare son nom, ses modes de traversée
  envisageables, son sens structurel et ses propriétés.

Exemples : une piscine, un lac, un onsen ou un seau peuvent un jour partager le
milieu `water` tout en restant des lieux différents; une porte, une arche et
une échelle restent des connecteurs aux modes distincts.

## Cycle de vie rigoureux

1. Créer un brouillon validé;
2. le publier;
3. le figer définitivement;
4. créer une nouvelle version si une évolution est nécessaire.

Les presets sont globaux, donc leur création ne produit pas d'événement dans
un monde. Les futurs blueprints enregistreront explicitement quelle version
publiée ils utilisent, afin que l'histoire d'un monde ne dérive pas lorsqu'un
preset est enrichi plus tard.

## Ce que ce lot ne fait pas

Il ne crée pas encore de lieux, de passage, de porte active ou de règle
d'eau. `GraphEngine` conserve son rôle : graphe brut et intégrité. Le futur
`TraversalEngine` décidera si une entité donnée peut utiliser une instance de
connecteur. Ainsi, l'étiquette « fenêtre » ne donne pas magiquement à une
personne le droit de la traverser.

## Preuves

`tests/test_environment_archetypes.py` couvre les deux familles, la validation
des contrats, les versions, l'immuabilité au niveau SQLite et la lecture
déterministe des presets publiés.
