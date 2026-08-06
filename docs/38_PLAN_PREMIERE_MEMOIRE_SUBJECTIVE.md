# Plan — première mémoire subjective

**Statut :** conception prête à implémenter; aucun schéma ni état de mémoire
n'est encore créé par ce document.

## Problème exact

Le journal canonique sait qu'un fait a eu lieu. `PerceptionService` sait quels
faits étaient accessibles, et `AttentionService` les classe comme entrées
possibles. Aucun de ces niveaux ne prouve qu'une résidente a remarqué,
compris ou retenu le fait. Écrire directement un souvenir depuis un événement
canonique violerait cette séparation.

```text
fait canonique ≠ accessible ≠ remarqué ≠ encodé ≠ croyance
```

## Première tranche proposée

La tranche initiale ne fera pas de récit libre, d'oubli, de consolidation par
LLM ni de croyance. Elle introduira seulement une **trace de perception
subjective encodée** et une lecture bornée de cette trace.

Une trace contiendra :

- son propriétaire et un identifiant de demande idempotent ;
- la source exacte : fait d'état ou événement canonique, type, séquence si elle
  existe, instant et payload réduit ;
- la règle d'accès qui autorisait la source ;
- l'instant d'encodage et une fidélité fermée (`complete`, `partial`,
  `ambiguous`, `signal_only`) ;
- éventuellement des participants/objets déjà reconnus dans la source, jamais
  une interprétation ajoutée ;
- une confidentialité privée par défaut.

Cette trace est immuable. Une couche ultérieure pourra créer un souvenir
épisodique qui la référence, ou une croyance qui la soutient/contredit, mais
ne modifiera pas son encodage d'origine.

## Validation non négociable

La future `SubjectiveMemoryService` ne fera pas confiance à un texte ni à un
`WorldFact` fabriqué par un appelant :

- pour un candidat d'état, elle recalculera l'attention et exigera une égalité
  exacte avec une entrée encore disponible pour la résidente ;
- pour un événement, elle relira le flux `events_since` et exigera la séquence,
  le type et le payload public exacts ;
- une source d'autrui hors des règles de perception sera refusée ;
- la même demande idempotente retournera la trace initiale, tandis que la
  réutiliser pour une autre source sera refusé ;
- aucun rappel ni simple affichage n'écrira une nouvelle trace.

Le moteur canonique reste l'autorité des faits. La mémoire subjective est un
état séparé, écrit uniquement par son service contrôlé; son audit indiquera
qu'un encodage a été enregistré, jamais que son contenu est devenu vrai pour
le monde.

## Stockage et audit proposés

Une migration dédiée créera une table structurée de traces subjectives, liée
au monde et au personnage, plus un journal append-only de ses opérations. Les
payloads réduits, identifiants de source, fidélite et clés de demande seront
interrogeables; un court résumé libre n'arrivera qu'avec la tâche LLM de
consolidation, sous validation de sources.

Le digest canonique ne mélangera pas ces traces avec la réalité du monde. Un
digest ou audit subjectif distinct les rendra néanmoins vérifiables à la
reprise et au banc d'essai.

## Lecture initiale

La première lecture sera déterministe : propriétaire seul, ordre par récence et
limite obligatoire. Elle ne fera
ni embedding, ni rappel créatif, ni reconsolidation. L'oubli initial réduira
plus tard l'accessibilité; il ne supprimera jamais la source.

## Hors de ce lot

- attention imparfaite, distraction, sommeil et occlusion détaillée ;
- résumés narratifs ou toute écriture LLM ;
- consolidation, condensation, oubli et faux souvenirs ;
- croyances, déductions, rumeurs, relations, émotions et objectifs ;
- reconstruction a posteriori d'événements d'autrui.

## Critères de sortie

1. une source réellement admissible peut être encodée une fois;
2. une source inventée, cachée ou d'autrui est refusée sans écriture;
3. retry identique idempotent, conflit de clé refusé;
4. trace, audit et lecture sont reproductibles et séparés du digest canonique;
5. tests ciblés, test de redémarrage et suite complète verts.
