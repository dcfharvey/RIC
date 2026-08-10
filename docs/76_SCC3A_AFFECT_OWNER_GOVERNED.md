# SCC-3A — conséquence affective owner-governed

SCC-3A active exclusivement les candidates `affect` de SCC-2A. Une candidate
ouvre un examen chez la propriétaire affective; elle n'ordonne aucune émotion.
Le propriétaire est `AffectService`, qui reste l'unique writer des épisodes.

Le provider retourne strictement `no_change` ou `start_episode`. La seconde
sortie propose une famille autorisée, une intensité qualitative, une cible
issue de l'allowlist moteur et des supports validés. `no_change` est une sortie
normale. Les conversions low/moderate/high vers 200/500/800 milli sont une
calibration d'ingénierie, pas une mesure scientifique.

Un épisode créé est privé, sourcé par la `subjective_trace` de la propriétaire,
et utilise `action_tendency=none` et `expression_milli=0`. SCC-3A ne modifie
jamais l'humeur, les croyances, relations, buts, mémoire, actions ou canon.

Les résultats déterministes vérifient le contrat, l'ownership, les allowlists,
le retry et la provenance. La qualité psychologique générale du modèle local
n'est pas qualifiée par ce lot; aucun benchmark général ni comparaison de
modèles n'est autorisé.
