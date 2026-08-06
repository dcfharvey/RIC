# Lot 4.2H — Effets déclaratifs des états de ressource

**Statut :** terminé et vérifié le 6 août 2026

Une bande d'état de ressource peut déclarer des effets actifs, lus sans écriture
au temps demandé :

- `capability_availability` : une capacité est `available`, `limited` ou
  `unavailable`;
- `context_signal` : un signal chiffré et non interprété est fourni aux futurs
  systèmes de cognition/motivation.

Exemples : munitions → tir indisponible; mana faible → magie limitée;
hydratation basse → signal de cognition réduite. Le signal n'impose pas une
émotion, une décision, ni une narration.

Les effets sont déclarés une seule fois par bande et deviennent immuables. Une
modification future nécessitera le pipeline administratif de changement profond.

## Exclusions

- aucun système d'action/capacité exécutable complet;
- aucune émotion, craving, humeur, personnalité ou décision forcée;
- aucun seuil ou effet chiffré propre à Chuu;
- aucun LLM ni interface.

**Validation :** 460 tests complets réussis.
