# Correctif alpha 0.1.0a4 — sortie LLM non plafonnée

**Statut :** livré sur décision explicite du propriétaire, le 6 août 2026.

Le Vivarium ne transmet plus le champ `max_output_tokens` à LM Studio et ne
lit plus `VIVARIUM_LLM_MAX_TOKENS`. Gemma utilise donc la limite configurée
dans LM Studio, sans plafond ajouté par le projet.

Cette décision retire un plafond de génération, pas les frontières d'autorité :
les schémas JSON, la validation du moteur, les limites de tours de scènes, les
délais réseau et les admissions d'appels restent en place. Une réponse longue
reste une proposition; elle ne devient jamais un fait canonique sans validation.
