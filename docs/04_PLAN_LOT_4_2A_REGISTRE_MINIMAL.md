# Lot 4.2A — Registre minimal de contrats

**Statut :** terminé et vérifié le 5 août 2026
**But :** créer la première source canonique des composants, capacités et unités
nécessaires au futur créateur de personnages, sans créer encore de personnage
définitif ni d'interface d'édition.

## Portée

Le lot introduit des définitions versionnées et immuables après publication :

- composants ;
- capacités ;
- unités ;
- dépendances et incompatibilités déclaratives ;
- schémas JSON bornés pour les paramètres de composant.

Le registre est générique et ne contient pas encore de contrats préremplis. Il
doit pouvoir décrire les cinq entités MVP (deux humaines, une louve anthro, une
slime et un chat) sans plafonner le nombre, l'espèce ou le profil cognitif.
L'absence d'un composant reste valide lorsque ses dépendances ne l'exigent pas.

## Exclusions

- aucun brouillon ou modèle de personnage ;
- aucune instanciation d'entité ;
- aucun formulaire ou écran nouveau ;
- aucune capacité calculée à partir d'une entité ;
- aucun LLM, Discord, import/export, snapshot administratif ou modification des
  personnages techniques ;
- aucun mécanisme générique de plugin.

## Contrats techniques à décider dans le code

1. La migration ajoute les tables du registre sans modifier les tables du monde
   ni les personnages existants.
2. Une définition publiée est append-only ; une correction produit une nouvelle
   version, jamais un `UPDATE` silencieux.
3. Les corps JSON ont une structure minimale imposée par SQLite (objet pour un
   contrat; listes pour les références) et sont validés par la couche métier
   pour les identifiants, versions et relations déclaratives.
4. Les identifiants de registre sont stables, minuscules et séparés par des
   points (`body.biological`, `perception.auditory`).
5. Le registre ne produit pas encore d'événement canonique de monde : il définit
   des contrats globaux, pas un fait survenu dans un univers. Son audit
   administratif détaillé arrive avec `prepare / validate / impact / confirm`.

## Critères d'acceptation

- migration idempotente et testée ;
- création puis lecture déterministe d'une définition brouillon ;
- publication atomique d'une version ;
- publication doublon ou identifiant/version invalide refusés sans écriture
  partielle ;
- version publiée non modifiable et non supprimable ;
- dépendance et incompatibilité référencent seulement des définitions publiées ;
- le registre reste neutre envers toute espèce, cardinalité ou personnalité ;
- les 446 tests de la suite restent verts ;
- le diff est revu contre les invariants d'autorité, d'atomicité et de
  séparation canonique/administrative.

## Suite prévue

`4.2B` a posé les brouillons et versions publiées de modèles de personnage.
Le validateur structurel de configuration, les variantes, les instances et le
pipeline de changement profond restent hors de ce lot.
