# SCC-2A — appraisal social situé

## Norme opérationnelle

SCC-2A reçoit uniquement une `social_interpretation` SCC-1B appartenant à la
propriétaire. Le moteur construit un snapshot fermé et borné, puis valide une
proposition d'appraisal qualitative. L'état persisté est privé, append-only et
owner-scoped.

L'appraisal peut être `relevant`, `not_relevant`, `ambiguous` ou `unresolved`.
Il peut proposer zéro ou plusieurs candidates indépendantes vers les domaines
`affect`, `belief`, `relationship`, `goal_or_intention` ou `memory`. Une
candidate est une invitation à un futur propriétaire; elle ne contient aucune
mutation et n'est jamais appliquée par SCC-2A.

Le provider ne reçoit que le snapshot. Les références de support sont une
allowlist construite par le moteur. Les textes du monde restent des données
non fiables, jamais des instructions. Motif caché, intention cachée, état
mental réel d'autrui, attribution imbriquée, mémoire riche et SCC-3 sont hors
contrat.

## Niveaux de conclusion

- Résultat empirique : les tests déterministes vérifient le contrat, les
  références, l'ownership, l'idempotence et l'absence de mutation descendante.
- Conclusion raisonnable mais incertaine : une appraisal qualitative peut
  servir de frontière intermédiaire avant les propriétaires SCC-3.
- Hypothèse de modélisation : les statuts et significations qualitatives
  décrivent une lecture située, non une psychologie universelle.
- Choix d'ingénierie : enums, cardinalités, snapshot, migration 0043,
  cadence et budget technique sont versionnés et falsifiables.

SCC-2A s'arrête après la persistance de l'appraisal et des candidates.

## Addendum contractuel — provider v2

Le provider `scc2a-appraisal-v2` traite la `justification` comme une
explication de routage non autoritative. Elle explique pourquoi le domaine
cible pourrait examiner les `basis_refs`; elle ne crée ni fait, ni croyance,
ni intention, ni émotion, ni support supplémentaire. Les propriétaires aval
repartent exclusivement des bases engine-owned référencées.

Une candidate `goal_or_intention` peut être fondée sur `interpretation:primary`
lorsque les `meaning_hypotheses` de l'owner y représentent déjà une proposition
de but ou d'intention. Une intention persistée explicitement engine-owned reste
également admissible. Aucune intention inventée ou cachée attribuée à autrui
n'est autorisée par le contrat.

Les contraintes structurelles communes sont validées par une fonction pure
partagée entre le parser provider et `SocialAppraisalService`; les erreurs de
sortie provider sont donc rejetées avant la persistance. L'ownership, la source,
la provenance technique et l'écriture transactionnelle restent des contrôles
distincts du service persistant. Aucun schéma SQLite n'est modifié.

SCC-3A conserve la candidate et ses bases autorisées, mais n'injecte plus la
justification dans son snapshot provider. Cette justification reste disponible
pour l'observation et l'audit technique, sans devenir une preuve causale.
