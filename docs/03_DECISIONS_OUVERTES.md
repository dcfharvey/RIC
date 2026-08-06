# Décisions ouvertes

**Version :** 0.2
**Date :** 4 août 2026
**Statut :** actif — révisé après fermeture technique de la Phase 3

| ID | Décision | Échéance | Règle |
| --- | --- | --- | --- |
| OD-001 | Langage, version exacte et bibliothèques | **fermée** | Python 3.12 de référence (`requires-python >= 3.12`), bibliothèque standard, `pytest` en dev. |
| OD-002 | Fournisseur et modèle principal | Avant Phase 5 | Comparer coût, qualité, confidentialité, tool calling, contexte et politique de contenu. |
| OD-003 | Budget quotidien et seuils d’alerte | Avant essais prolongés | Le système doit déjà mesurer et pouvoir limiter. |
| OD-004 | Cadence exacte des décisions cognitives | Phases 5 à 7 | Calibrer par tests, jamais un appel par personnage par minute. |
| OD-005 | Échelles et formules des besoins, traits et relations | Phases 3 à 7 | Utiliser des valeurs internes cachées et testables. (besoins implémentés ; traits/relations futurs) |
| OD-006 | Politique chiffrée d’oubli et consolidation | Phase 6 | Définir après observation de la mémoire réelle. |
| OD-007 | Rétention des prompts, sorties et logs | Avant API réelle | Arbitrer diagnostic, confidentialité et coût disque. |
| OD-008 | Recherche sémantique et embeddings | Après mémoire de base | Commencer sans dépendance vectorielle obligatoire. |
| OD-009 | Casting final, biographies et verrous canoniques | **partiellement fermée** — le casting MVP est fixé à Sophie et Erika (humaines sapientes adultes), une louve anthro sapiente adulte, une slime sapiente adulte à apparence féminine et un chat domestique non sapient. Les fiches détaillées restent à définir avant instanciation. | Toute entité doit être créée par le pipeline générique de modèles et d’instances. |
| OD-010 | Structure exacte des salons et commandes Discord | Avant Phase 10 | Définir à partir des flux validés. |
| OD-011 | Détail stocké pour préférences et événements intimes | Phases 6 à 7 | Conserver ce qui est utile à la continuité, avec visibilité protégée. |
| OD-012 | Rétention des snapshots | Avant essais destructifs | Valeur initiale proposée puis ajustée selon espace disque. |
| OD-013 | Durée de l’essai de stabilisation | Avant Phase 12 | Recommandation initiale : au moins sept jours réels, plus essais accélérés. |

## Décisions fermées

| ID | Décision fermée | Décision retenue | Date |
| --- | --- | --- | --- |
| OD-001 | Langage, version exacte et bibliothèques | Python 3.12 de référence ; bibliothèque standard ; `pytest` en dev. | 2026-08-03 |
| OD-009 (partiel) | Casting de référence | Cinq entités : Sophie et Erika, humaines sapientes adultes ; une louve anthro sapiente adulte ; une slime sapiente adulte à apparence féminine ; un chat domestique non sapient. | 2026-08-05 |

## Évolutions futures (consignées, non implémentées)

| ID | Évolution future | Contexte |
| --- | --- | --- |
| EVO-001 | Détection d’une variation anormale de l’horloge système vers l’avant avant un grand rattrapage temporel. | L’horloge dérivée (Lot 2.1) suit le temps réel 1:1 ; un saut système vers l’avant produirait un énorme écart simulé. À détecter/borner avant le rattrapage. Non implémenté. |
