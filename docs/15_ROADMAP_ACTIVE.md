# Roadmap active — RIC

**Version :** 2.0  
**Mise à jour :** 16 août 2026  
**Statut :** trajectoire opérationnelle courante

Cette roadmap fixe l'ordre des grands chantiers. Elle ne remplace ni la passation opérationnelle (`docs/99_PASSATION_COURANTE.md`), ni le noyau normatif (`docs/00_DOSSIER_MAITRE_IA.md`), ni le registre de décisions (`docs/01_REGISTRE_DECISIONS.md`).

## Principe de conduite

RIC suit deux règles :

> **Flexible creativity. Rigorous execution.**
>
> **Verify twice. Commit once.**

Une idée peut rester ouverte tant qu'elle est exploratoire. Dès qu'elle devient spécification, architecture, code ou canon, elle doit être testable, traçable et falsifiable.

Pour tout système comportemental, cognitif, social ou physiologique : littérature scientifique/technique d'abord, traduction opérationnelle ensuite. Séparer explicitement résultats empiriques, conclusions incertaines, hypothèses de modélisation et choix d'ingénierie.

Un seul chantier R&D runtime majeur à la fois.

## Référence produit

Au moment de cette mise à jour :

- `PRODUCT_HEAD = 350fbf80353af55994650372b27260eb29dc4dac`
- version déclarée : `0.2.0a5`
- dernière migration : `0061_autobiographical_append_only_lifecycle.sql`
- Operational Cognition Grounding : fermé
- P0 Memory : ouvert, en rodage V3c

Toujours revérifier `origin/product/current` avant tout WO.

## Porte actuelle — P0 Memory / V3c

Le produit possède maintenant les fondations autobiographiques suivantes :

- admission sélective d'encodage;
- `subjective_trace` append-only;
- épisodes autobiographiques avec supports;
- retrieval contextuel borné;
- seeding social d'épisode;
- lifecycle append-only et révisions structurelles;
- exposition séparée de `memories` et `autobiographical_memories` au contexte cognitif.

Le rodage doit déterminer ce que ces mécanismes font réellement dans la boucle normale.

### Preuve runtime encore recherchée

```text
expérience sociale accessible
→ admission
→ trace subjective
→ épisode autobiographique
→ retrieval contextuel
→ CognitionContext routé
→ provider réel
```

La preuve qualifie l'exposition du souvenir au provider; elle ne prouve pas à elle seule que le souvenir a causé la décision du modèle.

### Si la situation de test n'arrive pas

La scène A Sophie → Erika ne peut être exercée que sous accessibilité causale réelle. Sans co-présence valide avant la fin de V3c, classer le chemin `NOT EXERCISED UNDER VALID CONDITIONS`, pas `FAILED`.

### Porte de sortie P0

À la fin de V3c, faire un audit explicite de fermeture. Distinguer :

- ce qui est réellement qualifié;
- ce qui manque pour P0;
- ce qui est volontairement différé à une couche mémoire ultérieure.

Les points à trancher comprennent notamment :

- seeding d'épisode à partir de l'attention ordinaire;
- déclencheur naturel de lifecycle/révision;
- activation de candidats mémoire dans SCC;
- oubli, consolidation, familiarité, recollection et reconstruction avancée.

Une structure de révision append-only n'est pas une implémentation complète de la reconsolidation ou de l'oubli psychologique.

## Étape 1 après P0 — Conversation State minimal

Conversation State vient immédiatement après l'audit de fermeture P0.

But fonctionnel : donner à une conversation une continuité explicite suffisante pour éviter que chaque tour soit traité comme une fenêtre presque indépendante, sans transformer le dialogue en script.

Questions à spécifier avant code :

- quel état de conversation doit persister;
- comment distinguer sujet courant, engagements conversationnels, questions ouvertes et clôture;
- comment réduire répétition et perte de continuité;
- ce qui appartient à l'état partagé de scène versus à la mémoire subjective de chaque participante;
- comment une scène interrompue se ferme sans inventer la suite.

Le mécanisme actuel de scènes bornées reste une contrainte de sécurité, pas la définition finale d'une conversation naturelle.

Ne pas corriger la répétition par accumulation de prompt ad hoc avant ce chantier.

## Étape 2 — Behavioral Opportunity Layer (BOL)

Le diagnostic V3c de Chuu a fourni un cas empirique clair : la faisabilité moteur ne suffit pas à créer une opportunité comportementale pertinente.

État actuel observé :

```text
motifs / préférences / buts / contexte
        ↓
   [raccord générique incomplet]
        ↓
whitelist d'activités MVP techniquement faisables
        ↓
choix LLM ou no_action
```

Le BOL doit traiter le besoin fonctionnel suivant :

> À partir des motifs, préférences, objectifs, contexte, capacités et environnement réellement accessibles, produire un ensemble borné d'opportunités comportementales génériques, distinct des affordances physiques, que le moteur peut valider et que la cognition peut sélectionner.

Contraintes de conception :

- ne pas coder des comportements propres à Chuu, Erika ou un autre personnage;
- ne pas réduire le système à une table rigide `motif → activité`;
- peu d'opportunités pertinentes valent mieux qu'un énorme catalogue brut;
- la cognition peut proposer, jamais rendre une action physiquement possible;
- le moteur conserve l'autorité finale de faisabilité et de conséquence;
- une absence d'opportunité pertinente doit rester distinguable d'une impossibilité physique.

### Cas de référence Chuu

Le futur BOL devra pouvoir expliquer génériquement pourquoi une slime avec préférence `playful_group`, aucun partenaire social accessible, un motif de récupération et un environnement donné a ou n'a pas une occasion intéressante — sans règle spéciale `if character == Chuu`.

### Contrats à clarifier avec le BOL

- `MotiveCandidate.possible_actions` : projection explicative, pas liste légale d'options;
- `no_action` : aujourd'hui plusieurs causes sémantiques sont collapsées dans la même réponse minimale;
- relation entre préférences abstraites et occasions concrètes;
- relation entre activité moteur et opportunité cognitive.

Ne pas patcher simplement `sleep`/`rest` dans la whitelist des `planned_reflection` pour contourner le problème général.

## Étape 3 — P3.5 Perception · Action · Sensorium

P3.5 vient après BOL.

Principe central :

```text
accessible signal
≠ détecté
≠ sélectionné par l'attention
≠ accessible cognitivement
```

P3.5 doit généraliser les contrats de perception/action/sensorium : modalités, détection, attention, active sensing, relation corps-environnement et affordances physiques.

Frontière conceptuelle :

```text
affordance physique = relation corps ↔ monde permettant une action
opportunité BOL = possibilité comportementale considérée comme pertinente
```

Operational Cognition Grounding prépare cette étape en exposant déjà une partie du soi opérationnel et des capacités owner-backed, mais ne remplace pas P3.5.

## Étape 4 — Affect au-delà du SCC

Après les fondations décisionnelles précédentes :

- dynamique affective plus générale;
- expression;
- régulation;
- interaction avec mémoire, buts, attention et relations;
- séparation stricte entre état subjectif et vérité canonique.

Toute extension devra être fondée scientifiquement et testable; éviter les labels émotionnels décoratifs sans mécanisme.

## Étape 5 — cognition animale au-delà de Patoune CAT-0

Développer une agence non sapiente plus riche sans projeter automatiquement le modèle cognitif humain sur l'animal.

Les mécanismes devront être génériques, comparables et fondés sur la littérature pertinente.

## Étape 6 — physiologie plus large

Étendre au-delà du cycle sommeil/capacité physique seulement lorsque les systèmes précédents offrent les interfaces nécessaires.

Éviter d'ajouter des jauges physiologiques simplement parce qu'elles sont simulables : chaque variable doit avoir un propriétaire persistant, une causalité utile et une traduction comportementale justifiable.

## Signaux V3c à conserver pour les futurs chantiers

### Chuu / idles techniques

Les chaînes `idle WO95 → planned_reflection → no_action → expiration` sont actuellement un cas de diagnostic BOL/contrat de décision, pas une justification pour raccourcir WO95 ou patcher Chuu.

### Erika / gaming

La préférence très alignée sur la whitelist peut produire une signature répétitive. Observer la monoculture pendant V3c; ne pas la corriger avant BOL/calibration appropriée.

### `cognition_call_source_not_perceived`

Verdict actuel : `HEALTHY BUT NOISY`. Le filtre protège correctement l'accès subjectif mais est utilisé tardivement par rapport à la génération des tentatives. Optimisation possible après mesure, sans dupliquer l'autorité perceptive.

### `character_moved` / observabilité

Deux follow-ups techniques ont été repérés : payload `connector` potentiellement incomplet dans certains événements et `source_event_seq` absent sur le chemin d'invalidation cognitive. Aucun des deux ne justifie une modification live de V3c.

## Backlog explicitement différé

Les éléments suivants sont importants mais ne doivent pas interrompre la trajectoire actuelle :

- oubli/consolidation/recollection mémoire avancés;
- hypothèses concurrentes et contradictions de croyances plus riches;
- réseau relationnel et réparation;
- consentement opérationnel complet;
- identité/transformation/copie/fusion avancées;
- rattrapage temporel hors ligne condensé;
- interface sociale externe complète;
- optimisation fine des coûts/provider après qualification fonctionnelle.

## Discipline de fermeture

Une étape n'est pas fermée parce que le code existe. La fermeture exige :

```text
contrat explicite
→ implémentation vérifiée
→ tests/falsifications
→ observation runtime lorsque nécessaire
→ intégration reconnue
→ product/current avancé
→ documentation synchronisée
```

Un résultat négatif ou `NOT EXERCISED` doit être conservé tel quel. Ne jamais transformer l'absence de preuve en PASS documentaire.

## Gouvernance

- ChatGPT : science, conception fonctionnelle, cohérence conceptuelle, documentation R&D.
- Grok : contre-audit scientifique adversarial indépendant.
- Codex : architecture réelle, code, migrations, tests, invariants techniques, ordre d'implantation.
- Propriétaire : autorité finale produit/design.

Le code réel peut imposer une meilleure architecture que celle imaginée en R&D; Codex doit alors préserver le contrat fonctionnel et expliquer la divergence.
