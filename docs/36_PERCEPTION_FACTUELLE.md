# Perception factuelle minimale

**Statut :** première tranche implémentée, sans mémoire ni interprétation.

## Rôle

`PerceptionService.snapshot` lit le canon sans l'écrire et produit des
`PerceptionCandidate` immuables pour un observateur précis. Il ne prétend pas
que l'observateur a fait attention, compris ou retenu ces faits : il fixe
seulement ce qui lui est objectivement accessible à cet instant.

## Règles v1

Pour une résidente située dans un lieu, la vue contient uniquement :

- sa propre localisation;
- les autres personnages effectivement co-présents;
- les objets top-level non portés à ce lieu;
- les connecteurs adjacents, leur destination, leur sens et leur état.

Un objet contenu, dans un sac ou transporté n'est pas automatiquement visible.
Un personnage, objet ou connecteur d'un autre lieu n'est jamais exporté. Les
ressources, besoins, blessures, provenance administrative et états internes
d'autrui ne font pas partie de cette vue.

## Garanties et limites

- lecture pure : ni état, ni journal, ni horloge n'est matérialisé;
- ordre déterministe et faits profondément immuables;
- une personne qui quitte le lieu cesse immédiatement d'être candidate;
- aucune détection imparfaite, champ visuel, son, obscurité, attention,
  camouflage, croyance ou mémoire n'est encore simulé.

La prochaine couche utilisera ces candidats pour sélectionner ce qui attire
l'attention, puis seulement plus tard pour créer une perception subjective et
un souvenir. Le moteur ne doit pas transformer automatiquement tout candidat
en connaissance du personnage.

## Preuves

`tests/test_perception.py` vérifie la lecture sans écriture, le filtre de lieu,
la non-visibilité des téléphones portés, l'état actuel d'une porte, le retrait
d'un personnage qui quitte la pièce et les refus sans effet.
