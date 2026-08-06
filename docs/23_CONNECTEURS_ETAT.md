# Connecteurs à état simple

**Statut :** lot B implémenté (migration `0021`).

## Distinction essentielle

Le graphe `location_link` répond à « quels lieux sont reliés ? ». Une instance
`world_connector` répond désormais à « quel passage physique est-ce, et dans
quel état est-il ? ».

Un connector créé par blueprint possède : une clé stable, son preset et sa
version, ses deux extrémités, son sens et son état. Ses arêtes de graphe le
référencent; SQLite interdit qu'une arête soit reliée au mauvais connecteur.

## États actuels

- `available` : le connecteur est structurellement utilisable;
- `closed` : seulement pour un preset portant la propriété `closable`;
- `blocked` : obstruction générale, sans encore inventer de serrure, clé,
  force ou cause physique.

Tout changement est atomique et journalisé. Une requête pure au connecteur
répond alors correctement qu'il est inutilisable lorsqu'il est fermé ou bloqué.

## Limite volontaire

`GraphEngine` reste le graphe brut : il indique encore qu'une arête existe,
même si sa porte est fermée. Aucun personnage n'est encore déplacé par le
connecteur lui-même. Le prochain lot (`TraversalEngine`) sera la seule action
canonique qui combinera origine, sens, état et position d'une entité.

Les anciennes arêtes techniques sans instance de connecteur restent lisibles
et ne sont pas modifiées rétroactivement. Les nouveaux mondes issus de
blueprints produisent des connecteurs identifiés.

## Preuves

`tests/test_connectors.py` couvre l'identité produite par blueprint, le passage
de `available` à `closed`, le journal, le digest et le refus atomique d'une
arche non fermable.
