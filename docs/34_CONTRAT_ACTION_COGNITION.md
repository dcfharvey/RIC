# Contrat fermé d'action moteur–cognition

**Statut :** première tranche implémentée, sans LLM.

## Problème résolu

Une cognition ne doit jamais recevoir un accès d'écriture à SQLite ni appeler
un service canonique arbitraire. Elle formule une intention structurée; le
moteur la vérifie, l'applique seulement si elle est possible, puis renvoie un
résultat stable. Un refus n'écrit aucun fait.

## Contrat v1

`IntentProposal` est immuable et porte :

- une version de contrat;
- un identifiant de proposition valide;
- l'acteur;
- une provenance fermée (`cognition` ou `deterministic_policy`);
- un budget entier explicite;
- une action du vocabulaire autorisé et ses paramètres exactement attendus.

Le seul verbe livré est `traverse` : `connector_key` et
`target_location_key`. `ActionOrchestrator` route alors vers
`TraversalEngine`, qui conserve toutes les validations existantes (présence,
sens, connecteur, état, topologie, blessure, activité, transaction).

Le résultat est un `ValidationResult` :

- `accepted` avec un ou plusieurs `WorldFact` issus de l'événement canonique;
- `refused` avec un `reason_code` stable et aucun fait nouveau.

La proposition acceptée est ajoutée comme provenance dans `character_moved`.
Les faits retournés sont profondément immuables : une couche cognitive ne peut
pas altérer par référence la représentation qui lui a été donnée.
Une même proposition acceptée est idempotente : un retry retourne le fait
initial au lieu de déplacer deux fois le personnage; réutiliser son identifiant
pour une autre intention est refusé.

## Limites volontaires

- aucune décision subjective, perception ou mémoire n'est encore créée;
- aucun LLM ni texte libre n'entre dans le contrat;
- `take`, `put_down`, activités, équipements et interactions d'installation
  n'ont pas encore de verbe cognitif. Ils seront ajoutés un par un, avec leur
  validation et leurs scénarios de banc respectifs;
- un refus est une réponse non canonique : il est visible pour la cognition et
  le banc, mais ne pollue pas l'histoire du monde.

## Preuves

`tests/test_action_contract.py` couvre : traversée acceptée et attribuée,
refus sans écriture, action inconnue refusée avant exécution et immutabilité
profonde du fait retourné, idempotence et conflit d'identifiant. Le banc possède aussi `intent_traverse` pour exercer
la frontière dans le monde d'intégration.
