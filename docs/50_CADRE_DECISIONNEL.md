# Cadre décisionnel initial

**Statut :** intégration partielle au 6 août 2026.

`DecisionFrameService` est une projection pure : elle rassemble, pour une
résidente et un instant déterministe, l'intention active, les objectifs et les
candidats de motifs physiologiques. Son ordre de priorité explicite est :

1. intention active persistante ;
2. motif physiologique le plus urgent ;
3. objectif candidat le plus urgent puis important ;
4. aucune raison dominante.

Le cadre ne choisit ni n'exécute une action. Il ne modifie pas le monde, ne
donne pas au LLM un score à écrire et ne contourne pas `ActionOrchestrator`.
Son rôle est de fournir une explication bornée à la future sélection d'options.

Il est maintenant construit depuis l'heure canonique et le contexte de
simulation en lecture seule, puis joint au `CognitionContext` v5. Le LLM peut
donc voir la raison dominante sans pouvoir modifier l'intention, le motif ou
l'objectif qui la justifie.

Restent à livrer : génération d'options, conflits de valeurs/limites,
prédictions, suffisance, monitoring d'exécution et articulation complète au
cycle de simulation.
