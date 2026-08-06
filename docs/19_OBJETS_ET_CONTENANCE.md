# Objets et contenance canonique

**Statut :** lot initial implémenté (migration `0018`), complété par la
possession physique de personnage (`0023`; voir `docs/33_POSSESSION_PERSONNAGE.md`).

## But

Le Vivarium distingue maintenant une **installation** (fixe) d'un **objet
portable**. Un objet peut aussi être un conteneur d'autres objets. Cette
contenance est une hiérarchie physique; elle ne remplace ni le graphe de
déplacement entre lieux ni la possession par un personnage, désormais fournie
par `docs/33_POSSESSION_PERSONNAGE.md`.

## Contrat actuel

- `ObjectService` crée, lit, liste et déplace les objets top-level.
- Une installation (`portable=false`) ne peut pas être déplacée ni rangée.
- Un conteneur est un objet avec `container_capacity` explicite. La capacité
  compte ses enfants directs; `0` signifie qu'il n'accepte aucun contenu.
- `ContainmentService` place un objet portable dans un conteneur ou le retire
  vers un lieu explicite.
- Chaque objet conserve un `location_id` effectif matérialisé. Ainsi, une
  bille dans une boîte elle-même dans la cuisine est lisible directement
  comme étant dans la cuisine, sans calcul caché de la chaîne.
- Déplacer un conteneur déplace atomiquement le lieu effectif de tout son
  sous-arbre. Une seule opération produit un seul événement canonique.
- Tout refus laisse l'état et le journal inchangés.

## Protections

La migration ajoute des contraintes et triggers SQLite qui refusent :

- un objet dont le lieu ou le parent appartient à un autre monde;
- un enfant dont le lieu effectif ne correspond pas au lieu de son parent;
- un auto-parentage ou un cycle de contenance.

Les services ajoutent les règles métier : portabilité, capacité, objet cible
conteneur, déplacement d'un objet contenu et validation des entrées. Chaque
mutation et son événement append-only sont dans la même transaction.

## Hors portée assumée

Ce lot ne modélise pas encore :

- un objet tenu ou inventorié par un personnage;
- une personne, Patoune ou Chuu « dans » un objet;
- liquides, volume, masse, dimensions, verrouillage ou accessibilité;
- connecteurs et permission de traversée.

Ces cas auront besoin de contrats supplémentaires. Par exemple, le seau de
Chuu devra croiser ses formes, son hydratation et les règles de traversée :
le faire passer dès maintenant pour un simple objet casserait la distinction
entre fait physique et possibilité de l'entité.

## Preuves

`tests/test_objects_and_containment.py` couvre création, objet fixe, capacité,
cycle, déplacement de sous-arbre, retrait et protection inter-mondes. Le
digest reproductible inclut les objets, leur parent et leur lieu effectif.
