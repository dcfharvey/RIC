# Blueprints et instanciation d'environnement

**Statut :** lot A implémenté (migration `0020`).

## Rôle

Un blueprint est la composition explicite d'un monde : ses lieux, connecteurs,
objets initiaux et politique topologique. Il référence des versions publiées de
presets de lieu et de connecteur; il ne dépend donc jamais du seed technique
de la résidence de développement.

Cycle de vie : brouillon validé → publication immuable → instanciation.

## Instanciation atomique

L'instanciateur crée dans une seule transaction :

- le monde et son horloge;
- les lieux et leur provenance de preset;
- les arêtes topologiques issues des connecteurs;
- les objets initiaux top-level;
- la politique topologique;
- le snapshot de provenance du blueprint et l'événement canonique associé.

Une erreur avant la fin annule le monde entier : aucun monde vide ou demi-bâti
ne reste en base.

La provenance contient les contrats résolus et leurs versions, mais jamais les
rowids techniques : deux instanciations logiquement identiques restent
comparables par le digest reproductible.

## Limite volontaire sur les connecteurs

Pour l'instant, un connecteur de blueprint produit les arêtes dirigées qui
correspondent à son sens déclaré. Son identité est conservée dans le blueprint
figé, mais il n'est pas encore une instance mutable : pas de porte ouverte,
fermée ou verrouillée. C'est précisément le lot B suivant; ne pas feindre ce
comportement avant qu'il ait son état, son journal et ses tests propres.

## Hors périmètre

- personnages et règles de besoins du monde d'intégration;
- contenance initiale d'objets;
- connecteurs à état, permissions et coûts de traversée;
- interface ou LLM.

## Preuves

`tests/test_environment_blueprints.py` couvre publication, références de
presets, connectivité `strong_anchor`, instanciation, provenance, refus d'un
blueprint non publié et protection append-only d'un monde déjà créé.
