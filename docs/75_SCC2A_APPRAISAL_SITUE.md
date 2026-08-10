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
