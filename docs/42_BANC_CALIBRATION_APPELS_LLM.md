# Banc de calibration des appels LLM

**Statut :** première tranche implémentée et validée; aucune valeur produit n'est encore
figée.

`vivarium.cognition_call_bench` rejoue une chronologie déclarative de signaux
contre `CognitionCallPolicy`. Il produit les admissions, les reports et leurs
raisons sans appeler Gemma, sans écrire SQLite et sans modifier un monde. Le
banc est donc adapté aux comparaisons « what if » : même chronologie, limites
différentes, rapports comparables.

La calibration réelle se fera ensuite en deux mesures séparées :

1. **cadence et coût** : durée, erreurs, tokens et appels admissibles observés
   avec Gemma local;
2. **qualité** : respect du contrat, pertinence de la proposition et taux de
   refus moteur sur des scénarios ciblés.

Une seule mesure de latence ou un seul `llm-smoke` ne justifie pas un budget
quotidien. Le banc garde des limites injectées; le runtime alpha emploie
provisoirement 8 admissions par heure canonique et par personnage. Cette valeur
protège le rodage mais n'est pas une constante psychologique ni un réglage bêta.

La première mesure réelle isolée est maintenant disponible via
`python -m vivarium llm-calibrate`; elle reconstruit le même monde mémoire
pour chaque essai et rapporte contrat, décision, validation et durée. Voir
`docs/54_CALIBRATION_LOCALE_LLM.md`.
