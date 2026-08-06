# Lot 4.2L — Fermeture sûre de passage préparée

**Statut :** terminé et vérifié le 6 août 2026

## But

Une fermeture de passage peut couper une résidente du reste du vivarium. Cette
mutation topologique devient donc un changement préparé : impact explicite,
confirmation liée au hash et vérification atomique à l'application.

## Règle canonique ajoutée

Après toute fermeture, chaque lieu doit rester :

1. atteignable depuis `salon` ;
2. capable de rejoindre `salon`.

Le second point est indispensable car le graphe est orienté. Un lieu visible
depuis le salon mais sans chemin de retour est tout autant isolant dans la
pratique.

`GraphEngine.preview_remove_link` produit ce rapport en lecture pure. La
suppression effective le répète après les `DELETE` et avant l'événement
`link_removed`, dans la même transaction. Un échec annule les arêtes retirées
et l'événement : aucun état à moitié fermé n'est possible.

## Pipeline administratif

Nouvelle action `remove_link`, supportée par la migration `0016` et par :

```text
POST /api/admin-changes/remove-passage/prepare
```

Le plan sûr contient le nombre d'arêtes retirées et la connectivité prévue. Une
fermeture isolante est refusée dès la préparation (`would_isolate_location`),
sans plan ni audit administratif inutile. Une fermeture devenue invalide entre
préparation et confirmation reste couverte par la séquence optimiste du monde
et est de nouveau contrôlée dans la transaction d'application.

## Exclusions

- pas encore de suppression/création de lieu ;
- pas de redéfinition du point d'ancrage `salon` pour des mondes futurs ;
- pas de perception sociale de la fermeture : ce sera une couche vivante
  ultérieure, distribuée depuis le fait canonique validé.
