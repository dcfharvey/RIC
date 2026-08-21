# Roadmap active — RIC

**Version :** 2.1  
**Mise à jour :** 20 août 2026  
**Statut :** trajectoire opérationnelle courante

Cette roadmap fixe l'ordre des grands chantiers. Elle ne remplace ni la passation opérationnelle (`docs/99_PASSATION_COURANTE.md`), ni le noyau normatif (`docs/00_DOSSIER_MAITRE_IA.md`), ni le registre de décisions (`docs/01_REGISTRE_DECISIONS.md`).

## Principe de conduite

RIC suit deux règles :

> **Flexible creativity. Rigorous execution.**
>
> **Verify twice. Commit once.**

Une idée peut rester ouverte tant qu'elle est exploratoire. Dès qu'elle devient spécification, architecture, code ou canon, elle doit être testable, traçable et falsifiable.

Pour tout système comportemental, cognitif, social ou physiologique : littérature scientifique/technique d'abord, traduction opérationnelle ensuite. Séparer explicitement résultats empiriques, conclusions incertaines, hypothèses de modélisation et choix d'ingénierie.

Un seul chantier R&D runtime majeur à la fois. Des travaux préparatoires purement expérimentaux peuvent avancer en parallèle s'ils ne modifient ni la baseline runtime ni les contrats encore en qualification.

## Référence produit

Au moment de cette mise à jour :

- `PRODUCT_HEAD = ceb560e980066972ba844256bd195cc0f7e740a7`
- version déclarée : `0.2.0a5`
- dernière migration : `0061_autobiographical_append_only_lifecycle.sql`
- Operational Cognition Grounding : fermé
- P0 Memory : ouvert
- rodage P0 Memory V3c : interrompu avant audit de fermeture; artefact à conserver en lecture seule

Toujours revérifier `origin/product/current` avant tout WO.

## Porte actuelle — P0 Memory / fermeture de V3c interrompu

Le produit possède maintenant les fondations autobiographiques suivantes :

- admission sélective d'encodage;
- `subjective_trace` append-only;
- épisodes autobiographiques avec supports;
- retrieval contextuel borné;
- seeding social d'épisode;
- lifecycle append-only et révisions structurelles;
- exposition séparée de `memories` et `autobiographical_memories` au contexte cognitif.

V3c a été interrompu avant la fermeture formelle de P0. Cette interruption ne constitue ni un PASS ni un échec fonctionnel. La base et les journaux disponibles restent des preuves historiques en lecture seule.

### Prochaine action P0

1. produire un rapport de qualification V3c strictement en lecture seule à partir des données disponibles;
2. distinguer ce qui a réellement été exercé, ce qui a échoué et ce qui n'a simplement pas été exercé sous préconditions causales valides;
3. vérifier si les preuves disponibles suffisent à fermer P0;
4. si une preuve nécessaire manque, lancer un nouveau rodage isolé depuis la référence produit alors courante plutôt que modifier ou reprendre rétroactivement V3c;
5. seulement après l'audit de fermeture P0, ouvrir le chantier runtime majeur suivant.

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

### Si la situation de test n'a pas eu lieu

La scène A Sophie → Erika ne peut être exercée que sous accessibilité causale réelle. Si V3c n'a jamais offert cette précondition, classer le chemin `NOT EXERCISED UNDER VALID CONDITIONS`, pas `FAILED`.

### Porte de sortie P0

À la fermeture P0, distinguer :

- ce qui est réellement qualifié;
- ce qui manque encore pour P0;
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

## Programme transverse dès maintenant — adaptation LLM / PEFT-LoRA

Le recours à un adaptateur entraîné de type LoRA/QLoRA est désormais une piste R&D explicite. Il ne constitue pas encore une décision d'architecture ni un remplacement du provider courant.

### But à tester

Évaluer si une adaptation légère du modèle peut améliorer de façon mesurable des comportements **stables et génériques** du composant LLM, notamment :

- respect de `canon ≠ perception ≠ croyance` et `parole ≠ fait`;
- discipline de provenance et d'incertitude;
- abstention lorsque l'information est insuffisante;
- respect des contrats et schémas de sortie;
- réduction de la psychologisation gratuite et des affirmations de hidden state non soutenues;
- robustesse aux formulations adversariales ou ambiguës.

### Ce qui ne doit pas être appris dans les poids

Un adaptateur RIC ne doit pas devenir un stockage caché pour :

- faits du monde ou état canonique;
- souvenirs individuels;
- relations, permissions ou consentements;
- personnalité propre à un personnage;
- scripts `personnage → comportement`;
- règles physiques ou affordances qui appartiennent au moteur;
- état conversationnel ou opportunités comportementales qui doivent rester explicites et auditables.

Le modèle de base doit rester conceptuellement remplaçable conformément à DEC-026. Qwen3-14B reste un provider de qualification observé, pas une dépendance produit irrévocable.

### Méthode avant intégration

L'ordre expérimental recommandé est :

```text
benchmark de falsification gelé
→ dataset d'entraînement séparé
→ prototype LoRA/QLoRA hors runtime
→ comparaison modèle de base vs modèle + adaptateur
→ tests hors distribution et régressions générales
→ décision explicite d'intégration ou rejet
```

Le benchmark doit précéder le dataset afin d'éviter d'entraîner directement sur les cas servant ensuite de preuve de réussite.

Les premiers essais doivent privilégier un seul adaptateur générique de discipline RIC. Des adaptateurs spécialisés supplémentaires ne sont justifiés que par une déficience distincte, reproductible et mieux corrigée séparément.

### Séquençage

La recherche, le benchmark, la constitution du dataset et les prototypes hors runtime peuvent commencer avant la fermeture des étapes 1–3, tant qu'ils ne modifient aucune baseline de qualification.

En revanche, **l'intégration runtime d'un LoRA ne doit normalement pas précéder la stabilisation de Conversation State, BOL et P3.5**, car ces chantiers modifient précisément ce que le LLM reçoit, ce qu'il doit interpréter et les contrats de sortie qu'il doit respecter.

La porte d'intégration est donc placée immédiatement après P3.5 et avant les extensions cognitives suivantes. L'architecture réelle de chargement, activation, hotswap, fusion ou coexistence d'adaptateurs reste à déterminer par Codex à partir du runtime réel.

## Étape 4 — porte d'intégration LLM adaptée

Après P3.5 :

- réévaluer le benchmark avec les contrats cognitifs alors stabilisés;
- entraîner ou réentraîner l'adaptateur candidat sur ces contrats;
- comparer systématiquement le modèle de base et la variante adaptée;
- vérifier les régressions sur conversation, interprétation sociale, décision, mémoire et sorties structurées;
- décider explicitement si l'adaptateur devient une option runtime, une baseline de qualification ou est rejeté.

Aucun gain qualitatif subjectif ne suffit : l'intégration exige des falsifications reproductibles et la possibilité de revenir au modèle de base.

## Étape 5 — Affect au-delà du SCC

Après les fondations décisionnelles précédentes et la porte d'adaptation LLM :

- dynamique affective plus générale;
- expression;
- régulation;
- interaction avec mémoire, buts, attention et relations;
- séparation stricte entre état subjectif et vérité canonique.

Toute extension devra être fondée scientifiquement et testable; éviter les labels émotionnels décoratifs sans mécanisme.

## Étape 6 — cognition animale au-delà de Patoune CAT-0

Développer une agence non sapiente plus riche sans projeter automatiquement le modèle cognitif humain sur l'animal.

Les mécanismes devront être génériques, comparables et fondés sur la littérature pertinente.

Un éventuel adaptateur LLM RIC ne doit pas être présumé applicable à la cognition animale : cette question devra être testée séparément selon le rôle réel du LLM dans cette couche.

## Étape 7 — physiologie plus large

Étendre au-delà du cycle sommeil/capacité physique seulement lorsque les systèmes précédents offrent les interfaces nécessaires.

Éviter d'ajouter des jauges physiologiques simplement parce qu'elles sont simulables : chaque variable doit avoir un propriétaire persistant, une causalité utile et une traduction comportementale justifiable.

## Signaux V3c à conserver pour les futurs chantiers

V3c est interrompu, mais ses observations restent des données expérimentales valides dans les limites de ce qui a réellement été exercé. Elles ne doivent pas être présentées comme les résultats d'un rodage arrivé à son protocole de fermeture.

### Chuu / idles techniques

Les chaînes `idle WO95 → planned_reflection → no_action → expiration` restent un cas de diagnostic BOL/contrat de décision, pas une justification pour raccourcir WO95 ou patcher Chuu.

### Erika / gaming

La préférence très alignée sur la whitelist a montré une signature comportementale répétitive. Conserver cette observation comme cas de calibration/monoculture; ne pas la corriger par prompt ou règle de personnage avant BOL et les évaluations appropriées.

### `cognition_call_source_not_perceived`

Verdict observé : `HEALTHY BUT NOISY`. Le filtre protège correctement l'accès subjectif mais est utilisé tardivement par rapport à la génération des tentatives. Optimisation possible après mesure, sans dupliquer l'autorité perceptive.

### `character_moved` / observabilité

Deux follow-ups techniques ont été repérés : payload `connector` potentiellement incomplet dans certains événements et `source_event_seq` absent sur le chemin d'invalidation cognitive. Les qualifier séparément; ne pas modifier l'artefact V3c pour les corriger rétroactivement.

## Backlog explicitement différé

Les éléments suivants sont importants mais ne doivent pas interrompre la trajectoire actuelle :

- oubli/consolidation/recollection mémoire avancés;
- hypothèses concurrentes et contradictions de croyances plus riches;
- réseau relationnel et réparation;
- consentement opérationnel complet;
- identité/transformation/copie/fusion avancées;
- rattrapage temporel hors ligne condensé;
- interface sociale externe complète;
- optimisation fine des coûts/provider après qualification fonctionnelle;
- éventuelle spécialisation de plusieurs adaptateurs LLM, sauf défaut démontré qui la justifie.

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

Un résultat négatif, interrompu ou `NOT EXERCISED` doit être conservé tel quel. Ne jamais transformer l'absence de preuve en PASS documentaire.

## Gouvernance

- ChatGPT : science, conception fonctionnelle, cohérence conceptuelle, documentation R&D.
- Grok : contre-audit scientifique adversarial indépendant.
- Codex : architecture réelle, code, migrations, tests, invariants techniques, ordre d'implantation.
- Propriétaire : autorité finale produit/design.

Le code réel peut imposer une meilleure architecture que celle imaginée en R&D; Codex doit alors préserver le contrat fonctionnel et expliquer la divergence.
