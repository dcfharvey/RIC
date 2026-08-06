# Vivarium social artificiel — Demande de changement proposée après le dossier maître v0.1

**Date :** 4 août 2026  
**Statut :** PROPOSÉ — ne remplace pas le dossier maître tant que le propriétaire ne l’a pas approuvé et intégré  
**Objet :** intégrer les décisions prises après la consolidation du 3 août 2026

## 1. Motif

Le dossier maître v0.1 reste la source normative initiale du dépôt. Depuis sa création, plusieurs décisions de conception ont été précisées : propriété des chambres, taxonomie des besoins, fondation psychologique, objectifs et engagements, stabilité des intentions, arbitrage décisionnel et accès du propriétaire aux scènes privées.

Cette demande ne modifie pas le code. Elle prépare une révision documentaire cohérente avant les phases cognitives.

## 2. Décisions à ajouter au registre autoritatif

### DEC-028 — Chambres personnelles

Chaque chambre est canoniquement assignée à une habitante et constitue son espace personnel. La propriété crée une norme sociale et des attentes, mais ne bloque pas magiquement l’accès physique. Une personne peut entrer sans permission si les conditions physiques le permettent, avec conséquences perceptives, émotionnelles et relationnelles.

### DEC-029 — Affichage et observation des scènes privées

Les réglages direct/résumé/masqué contrôlent la présentation spontanée d’une scène, pas son existence canonique. Le propriétaire conserve un accès explicite aux scènes privées, même lorsque leur affichage spontané est désactivé.

### DEC-030 — Taxonomie des besoins

Les besoins psychologiques ne sont pas représentés par une unique jauge sociale. Il faut distinguer présence, interaction et récupération face à la saturation. La sociabilité est une disposition de personnalité; la solitude ressentie, l’ennui, le stress momentané et le confort sont des états dérivés.

### DEC-031 — Fondation de personnalité

La personnalité initiale utilise des dimensions continues : Big Five et deux axes d’attachement. Aucun type MBTI ou « 16 personnalités » n’a d’autorité sur le comportement.

### DEC-032 — Valeurs

Les personnages possèdent des valeurs distinctes de leur personnalité et de leurs besoins. Noyau : autonomie, loyauté, bienveillance, justice, honnêteté, respect des limites, devoir, accomplissement, sécurité, exploration, tradition/appartenance et pouvoir/statut.

### DEC-033 — Objectifs et engagements

Un objectif possède une origine, une importance, une urgence, une cible et des conditions de réussite ou d’abandon. Un engagement ajoute une obligation envers soi, une personne, un groupe, une institution ou le propriétaire. Aucun engagement ne force magiquement une action.

### DEC-034 — Stabilité des intentions

Une intention adoptée persiste par défaut. Elle n’est réexaminée qu’en présence d’un changement pertinent : obstacle, urgence, blessure, nouvelle information, conflit d’engagement, changement émotionnel important, demande sociale significative ou échéance manquée.

### DEC-035 — Arbitrage explicable

Le choix d’une action ne repose ni sur le besoin le plus élevé, ni sur un score opaque, ni sur une décision libre du LLM. Le système génère quelques options, élimine les impossibilités, évalue besoins, objectifs, engagements, valeurs, coûts, risques et conséquences relationnelles, puis maintient ou révise une intention.

## 3. Révision proposée de la section 5.4

Remplacer la liste plate « faim, sommeil, hygiène, confort, énergie, santé immédiate, sociabilité, solitude, stimulation, stress et libido » par une structure compatible avec l’implémentation progressive :

### Besoins ou pressions

- alimentation;
- sommeil;
- hygiène;
- sécurité;
- autonomie;
- stimulation;
- récupération de saturation;
- présence sociale;
- interaction sociale;
- intimité, appartenance et reconnaissance comme besoins généraux à satisfaction ciblée;
- activation physique, sexualité et compétence comme pulsions fortement individualisées.

### Ressources, conditions et états dérivés

- énergie;
- blessure et douleur;
- confort;
- humeur;
- ennui;
- solitude ressentie;
- saturation sociale;
- stress momentané.

Cette révision n’oblige pas à implémenter toutes les dimensions simultanément. Elle empêche surtout de mélanger les catégories lors des phases suivantes.

## 4. Ajouts proposés à la section 5.3

Ajouter que :

- la personnalité est continue et probabiliste;
- les traits modulent des mécanismes et ne commandent pas directement des actions;
- les valeurs, préférences, objectifs, engagements et habitudes sont des structures distinctes;
- les intentions persistent jusqu’à un déclencheur de révision;
- les éléments canoniques figés restent protégés par la carte de plasticité.

## 5. Ajouts proposés au modèle de données logique

Ajouter ou préciser :

- `room_assignment` ou propriété équivalente;
- `door_state` et permissions ciblées si nécessaires;
- `action_definition` / registre d’actions;
- `event_manifestation` distinct de `canonical_event`;
- `perception` avec canal, fidélité et source;
- `belief` avec proposition, confiance et provenance;
- `belief_evidence` ou liens de soutien/contradiction;
- `episodic_memory` et références sources;
- `goal`, `commitment` et `active_intention` séparés;
- `emotion_episode` et `mood_state` simplifiés;
- `relationship` directionnelle avec historique causal;
- `affiliation` entre personnage et collectif abstrait;
- `personal_boundary` et `permission` distinctes du consentement situationnel.

Le schéma physique exact reste à proposer par l’IA programmeuse au moment du lot concerné.

## 6. Invariants à ajouter

- Une perception est produite à partir d’une manifestation accessible, jamais à partir du payload canonique complet.
- Une interprétation ne modifie jamais rétroactivement une perception.
- Une croyance conserve ses sources de soutien et de contradiction.
- Une consolidation de mémoire par LLM référence ses sources et ne peut ajouter un fait non supporté.
- Une émotion persistante possède une cause, un état introspectif ou un rappel explicite.
- Une relation est directionnelle et tout changement significatif est causal et borné.
- Une intention active ne disparaît pas sans réussite, abandon, interruption ou révision explicite.
- Un score de relation, une attirance, une libido ou un rôle ne constitue jamais un consentement.
- Le masquage d’une scène n’altère ni le canon, ni ses conséquences.

## 7. Révision proposée du plan de réalisation

Conserver les douze phases, mais préciser les sous-lots :

- Phase 4 : registre d’actions, manifestations, scènes, perceptions et snapshot subjectif.
- Phase 5 : adaptateur, faux modèle, validation structurée, budget et première intention.
- Phase 6 : croyances, provenance, mémoire, rappel, consolidation et oubli borné.
- Phase 7 : fiches finales, personnalité, valeurs, objectifs, émotions, relations, limites, conversations et initiatives.

La Phase 4 reste obligatoire avant le premier langage généré appliqué à une action.

## 8. Scénarios d’acceptation à ajouter

- intrusion physiquement possible mais socialement transgressive;
- présence sociale sans interaction;
- croyance fausse révisée par une preuve;
- promesse en conflit avec fatigue et blessure;
- relation asymétrique;
- émotion fondée sur une croyance fausse;
- affiliation extérieure abstraite;
- sortie LLM inventant un objet refusée;
- scène privée masquée mais active;
- intention persistante qui ne se recalcule pas sans déclencheur.

## 9. Éléments explicitement différés

- MBTI et archétypes comme mécanismes;
- faux souvenirs spontanés;
- embeddings obligatoires;
- acoustique détaillée;
- logique épistémique imbriquée sans limite;
- arbre de compétences complexe;
- simulation complète d’organisations externes;
- modification directe des relations ou émotions par texte libre du LLM.

## 10. Approbation attendue

Après validation du propriétaire, cette demande devrait être :

1. inscrite au changelog;
2. fusionnée dans une version ultérieure du dossier maître;
3. utilisée comme référence pour les plans des Phases 4 à 7;
4. accompagnée d’une matrice reliant les nouvelles décisions aux tests.
