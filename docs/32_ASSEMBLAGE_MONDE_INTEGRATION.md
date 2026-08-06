# Assemblage du monde d'intégration

`IntegrationWorldService.create_initial_world` assemble dans une seule
transaction imbriquée : catalogue de résidence, modèles de personnages,
blueprint, règles standards, cinq résidentes à l'entrée extérieure, hydratation
de Chuu et contexte commun immuable. Toute erreur annule le monde entier.

Le contexte partagé ne contient que les faits autorisés : colocation volontaire,
dépenses couvertes, allocation personnelle et absence de passé commun connu.
Il est inclus dans le digest reproductible.
