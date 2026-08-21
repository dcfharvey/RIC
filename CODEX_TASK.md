# Codex task — état courant RIC

**Mise à jour :** 20 août 2026  
**Statut :** P0 Memory ouvert; V3c interrompu; aucun nouveau WO runtime majeur avant audit de fermeture P0

## Référence produit

La seule référence produit autoritative est `product/current`.

Au moment de cette mise à jour :

- `PRODUCT_HEAD = ceb560e980066972ba844256bd195cc0f7e740a7`
- version Python déclarée : `0.2.0a5`
- schéma courant : migration `0061_autobiographical_append_only_lifecycle.sql`

Toujours refaire le préflight Git décrit dans `docs/GOUVERNANCE_GIT.md` avant tout nouveau travail. Ne jamais utiliser `main`, un ancien worktree ou un runtime historique comme base implicite.

## Runtime V3c — artefact historique interrompu

Le rodage P0 Memory V3c a été interrompu avant audit de fermeture :

- `RUNTIME_HEAD = 350fbf80353af55994650372b27260eb29dc4dac`
- worktree : `C:\AI\Vivarium social\.rodage-p0-memory-v3c`
- DB : `data\vivarium-p0-memory-v3c.sqlite`
- session : `081861ed-b259-45ae-ad3f-4f61517d2c02`
- moteur : `ActiveSimulationEngine`
- physiologie : active
- provider de qualification : `qwen3-14b`

Ce runtime n'est plus une expérience active à poursuivre. Le worktree, la DB et les journaux sont des preuves historiques à conserver strictement en lecture seule. Ne pas les rebaser, reset, migrer, renommer, corriger ou utiliser comme worktree de développement.

## État des chantiers

### Fermé / intégré

- correctif de drainage/fairness de la file cognitive;
- fondation autobiographique P0 : épisode + supports + retrieval contextuel borné;
- admission d'encodage et seeding social;
- lifecycle autobiographique append-only avec révisions structurelles;
- Operational Cognition Grounding : morphologie descriptive + capacités/signaux owner-backed dans le contexte cognitif;
- alignement générique de la projection d'activités avec la faisabilité physique connue.

La qualification complète du dernier lot de grounding rapportée avant intégration est `1033 passed, 1 skipped`.

### Ouvert — P0 Memory

P0 n'est pas fermé. La preuve runtime qui restait recherchée est :

```text
expérience sociale accessible
→ admission
→ subjective_trace
→ épisode autobiographique
→ retrieval contextuel ultérieur
→ CognitionContext routé
→ appel provider réel
```

Une tentative de scène contrôlée Sophie → Erika a donné `WAITING FOR VALID ACCESS` : aucune co-présence causale valide n'était disponible. Ne pas téléporter, fabriquer une perception, injecter une mémoire ou appeler directement le retrieval pour produire artificiellement un PASS.

La prochaine tâche est de produire le rapport de qualification V3c en lecture seule à partir des données disponibles. Toute condition jamais exercée sous préconditions valides doit rester `NOT EXERCISED UNDER VALID CONDITIONS`, pas « failed ».

Après le rapport :

- si les preuves suffisent, procéder à l'audit de fermeture P0;
- si une preuve nécessaire manque, préparer un nouveau rodage isolé depuis le `PRODUCT_HEAD` alors courant;
- ne jamais reprendre ou modifier rétroactivement V3c pour compléter la preuve.

## Diagnostics V3c à conserver comme données

### `cognition_call_source_not_perceived`

Verdict : `B — HEALTHY BUT NOISY`.

Le volume élevé vient principalement du fait que l'orchestrateur teste des événements canoniques contre la vue perceptive de chaque résidente. Aucun churn logique, backlog durable ou starvation n'a été démontré.

Follow-ups séparés seulement :

- alignement du payload `character_moved` avec le contrat perceptif (`connector`);
- conservation de `source_event_seq` sur les invalidations;
- éventuel préfiltrage perceptif plus tôt uniquement si la même autorité perceptive peut être réutilisée sans dupliquer les règles.

### Chuu — répétition `planned_reflection → no_action`

Le grounding est présent et stable. Le diagnostic n'a pas démontré de panne corporelle ni de refus moteur.

Le constat fonctionnel est :

```text
activité faisable
≠
opportunité comportementale pertinente
```

`MotiveCandidate.possible_actions` est une projection explicative; il ne construit pas `activity_options`. `sleep` et `rest` sont de vraies activités moteur, mais ne font pas partie de la whitelist MVP des six loisirs autonomes présentés aux `planned_reflection`.

Ne pas ajouter `sleep`/`rest` à cette whitelist comme patch Chuu. Le diagnostic soutient un besoin générique futur de Behavioral Opportunity Layer (BOL), sans en prescrire l'architecture.

## Piste R&D LLM / LoRA

La roadmap autorise désormais une piste expérimentale PEFT/LoRA hors runtime.

Travaux permis avant P3.5, sans modifier la baseline de qualification :

- benchmark de falsification modèle de base vs modèle adapté;
- définition de ce qu'un adaptateur RIC peut et ne peut pas apprendre;
- préparation d'un dataset séparé du benchmark;
- prototypes LoRA/QLoRA hors runtime;
- mesures de régression et de généralisation.

Un éventuel adaptateur doit viser une discipline générique : invariants, provenance, incertitude, abstention et contrats de sortie. Il ne doit pas servir de stockage caché pour faits du monde, souvenirs, relations, consentements, personnalité ou scripts propres aux personnages.

Aucune intégration runtime d'un LoRA n'est autorisée avant la stabilisation de Conversation State, BOL et P3.5, sauf nouvelle décision produit explicite fondée sur une preuve contraire. L'architecture de chargement, hotswap, fusion ou coexistence d'adaptateurs reste à Codex au moment du chantier correspondant.

## Ordre de travail autorisé

```text
rapport V3c read-only
→ audit de fermeture P0
→ nouveau rodage P0 isolé seulement si nécessaire
→ Conversation State minimal
→ Behavioral Opportunity Layer
→ P3.5 Perception · Action · Sensorium
→ porte d'intégration LLM adaptée / LoRA
→ affect au-delà du SCC
→ cognition animale
→ physiologie plus large
```

Un seul chantier R&D runtime majeur à la fois.

La R&D LoRA hors runtime peut avancer en parallèle parce qu'elle ne modifie ni le produit ni la qualification P0.

## Interdictions immédiates

Ne pas :

- modifier WO95 pour masquer les idles de 600 s;
- patcher Chuu spécifiquement;
- réintroduire un quota fixe N appels LLM / fenêtre dans la cognition normale;
- ouvrir Conversation State ou BOL avant la fermeture P0;
- modifier les DB/runtime V3, V3b ou V3c utilisés comme preuves historiques;
- intégrer un adaptateur LoRA dans le runtime courant avant sa porte de qualification;
- encoder dans des poids LLM de l'état qui doit rester explicite, persistant et auditable;
- présenter une décision d'ingénierie comme une loi scientifique.

## Gouvernance

- ChatGPT : recherche, conception fonctionnelle, cohérence conceptuelle, documentation R&D.
- Grok : contre-audit scientifique adversarial indépendant.
- Codex : autorité sur l'architecture réelle, le code, les migrations, les invariants techniques, les tests et l'ordre d'implantation.
- Propriétaire : autorité finale produit/design.

**Verify twice. Commit once.**
