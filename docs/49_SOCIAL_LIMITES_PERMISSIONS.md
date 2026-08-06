# Relations, limites et permissions — lot initial

**Statut :** implémenté partiellement au 6 août 2026.

## Relations directionnelles

Une `relationship_view` appartient à une résidente vers une cible précise.
`A → B` n'implique donc jamais `B → A`. Les dimensions ne sont pas compressées
dans un unique score : familiarité, confiance, affection, respect, sécurité,
intimité, attraction et irritation restent séparées.

Chaque changement exige une trace privée de la propriétaire et une petite
variation bornée. Les valeurs ne sont pas libres d'être écrites par le LLM;
celui-ci pourra éventuellement proposer une interprétation qualitative, que le
moteur convertira ou refusera. Une même source ne peut être appliquée deux fois
à la même vue.

## Limites et permissions

Une limite personnelle a une propriétaire, un domaine (corps, espace, temps,
attention, information, biens, relation ou décision), une portée structurée et
un état révocable. Elle n'est pas une interdiction physique : sans règle
canonique spécifique, elle crée une question sociale et non un mur magique.

Une permission est distincte : elle est émise par une résidente à une autre,
pour une action et une portée identiques, et peut être révoquée ou expirer.
La lecture ne retourne vrai que pour une permission explicite et actuelle.
Aucune relation, attirance, valeur, besoin ou ancienne permission ne devient un
consentement automatique.

## Intégrité et exposition

Les trois familles ont un état courant et un événement append-only requis pour
chaque changement. SQLite interdit les modifications et suppressions
silencieuses. `subjective_social_audit` vérifie l'événement actuel et la source
privée des relations.

Le contexte cognitif v4 expose seulement les relations et limites actives de
la résidente concernée; les permissions d'autrui ne sont pas divulguées.

## Limites assumées

Restent futurs : confiance située, réparation décomposée, appartenances,
réseau social, consentement opérationnel complet, détection/perception d'une
transgression et intégration aux futurs actes sociaux. Les actions actuelles de
traversée ne sont volontairement pas bloquées par une limite personnelle.

## Preuve de sortie

- directionnalité et source privée testées ;
- impact relationnel borné et dédoublonné ;
- limites et permissions explicites, réversibles et auditables ;
- aucune permission inférée depuis une relation ;
- contexte LLM v4 privé et borné ;
- suite complète : 634 tests réussis.
