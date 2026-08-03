# Décisions ouvertes

| ID | Décision | Échéance | Règle |
| --- | --- | --- | --- |
| OD-001 | Langage, version exacte et bibliothèques | Phase 0 | L’IA architecte propose un choix par défaut après consultation de la documentation officielle actuelle. |
| OD-002 | Fournisseur et modèle principal | Avant Phase 5 | Comparer coût, qualité, confidentialité, tool calling, contexte et politique de contenu. |
| OD-003 | Budget quotidien et seuils d’alerte | Avant essais prolongés | Le système doit déjà mesurer et pouvoir limiter. |
| OD-004 | Cadence exacte des décisions cognitives | Phases 5 à 7 | Calibrer par tests, jamais un appel par personnage par minute. |
| OD-005 | Échelles et formules des besoins, traits et relations | Phases 3 à 7 | Utiliser des valeurs internes cachées et testables. |
| OD-006 | Politique chiffrée d’oubli et consolidation | Phase 6 | Définir après observation de la mémoire réelle. |
| OD-007 | Rétention des prompts, sorties et logs | Avant API réelle | Arbitrer diagnostic, confidentialité et coût disque. |
| OD-008 | Recherche sémantique et embeddings | Après mémoire de base | Commencer sans dépendance vectorielle obligatoire. |
| OD-009 | Casting final, biographies et verrous canoniques | Avant Phase 3 | Le propriétaire fournit ou approuve les fiches. |
| OD-010 | Structure exacte des salons et commandes Discord | Avant Phase 10 | Définir à partir des flux validés. |
| OD-011 | Détail stocké pour préférences et événements intimes | Phases 6 à 7 | Conserver ce qui est utile à la continuité, avec visibilité protégée. |
| OD-012 | Rétention des snapshots | Avant essais destructifs | Valeur initiale proposée puis ajustée selon espace disque. |
| OD-013 | Durée de l’essai de stabilisation | Avant Phase 12 | Recommandation initiale: au moins sept jours réels, plus essais accélérés. |

## Décisions fermées

| ID | Décision fermée | Décision retenue | Date |
| --- | --- | --- | --- |
| OD-001 | Langage, version exacte et bibliothèques | **Python 3.12** comme version de référence initiale (`requires-python >= 3.12` pour rester compatible avec les versions ultérieures). Bibliothèque standard privilégiée ; dépendance de développement : `pytest`. | 2026-08-03 |

## Évolutions futures (consignées, non implémentées)

| ID | Évolution future | Contexte |
| --- | --- | --- |
| EVO-001 | Détection d'une variation anormale de l'horloge système **vers l'avant** avant un grand rattrapage temporel. | L'horloge dérivée (Lot 2.1) suit le temps réel 1:1 ; un saut système vers l'avant produirait un énorme écart simulé. À détecter/borner avant le rattrapage, en lien avec la future phase de rattrapage. Non implémenté. |