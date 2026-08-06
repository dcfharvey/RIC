# Lot 4.2C — Validation structurelle des gabarits

**Statut :** terminé et vérifié le 5 août 2026
**But :** vérifier de façon déterministe qu'un gabarit référence des versions
publiées précises de composants et que chaque configuration respecte le contrat
déclaré de son composant, sans créer encore une entité de monde.

## Contrat minimal retenu

Une liaison de composant est figée par `{key, version, config}`. Une publication
ne consulte jamais « la dernière version » d'un composant : elle exige la
version explicitement référencée. Ainsi un gabarit ne dérive pas à cause d'une
évolution ultérieure du registre.

Un composant peut déclarer dans son contrat un `config_schema` borné :

- `required` : liste de clés;
- `properties` : types scalaires ou structurés, énumérations et bornes
  numériques;
- `additional_properties` : booléen explicite.

Ce n'est pas une implémentation générale de JSON Schema et ne remplace aucun
validateur sémantique. C'est une garde structurelle locale et inspectable.

## Exclusions

- aucune instance, incarnation, relation ou mémoire;
- aucune déduction de capacité, affordance ou permission;
- aucun héritage, overlay, actif ou import/export;
- aucune écriture lors d'une simple validation;
- aucun LLM ni interface.

## Critères d'acceptation

- le rapport est déterministe, court et sans raisonnement interne;
- une version de composant absente ou non publiée bloque la publication;
- les champs requis, inconnus ou de type/borne invalide bloquent la publication;
- la publication reste atomique si la validation échoue;
- les 446 tests complets et la revue de diff restent verts.
