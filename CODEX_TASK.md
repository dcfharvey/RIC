# Codex task — état courant RIC

**Mise à jour :** 16 août 2026  
**Statut :** aucun nouveau WO runtime majeur autorisé pendant le rodage V3c

## Référence produit

La seule référence produit autoritative est `product/current`.

Au moment de cette mise à jour :

- `PRODUCT_HEAD = 350fbf80353af55994650372b27260eb29dc4dac`
- version Python déclarée : `0.2.0a5`
- schéma courant : migration `0061_autobiographical_append_only_lifecycle.sql`

Toujours refaire le préflight Git décrit dans `docs/GOUVERNANCE_GIT.md` avant tout nouveau travail. Ne jamais utiliser `main`, un ancien worktree ou un runtime historique comme base implicite.

## Runtime de qualification actif

Rodage P0 Memory V3c :

- `RUNTIME_HEAD = 350fbf80353af55994650372b27260eb29dc4dac`
- worktree : `C:\AI\Vivarium social\.rodage-p0-memory-v3c`
- DB : `data\vivarium-p0-memory-v3c.sqlite`
- session : `081861ed-b259-45ae-ad3f-4f61517d2c02`
- moteur : `ActiveSimulationEngine`
- physiologie : active
- provider de qualification : `qwen3-14b`

Ce runtime est une expérience en cours. Ne pas le rebaser, reset, migrer, renommer, corriger ou utiliser comme worktree de développement.

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

P0 n'est pas fermé. La preuve runtime encore recherchée est :

```text
expérience sociale accessible
→ admission
→ subjective_trace
→ épisode autobiographique
→ retrieval contextuel ultérieur
→ CognitionContext routé
→ appel provider réel
```

Une tentative de scène contrôlée Sophie → Erika est actuellement `WAITING FOR VALID ACCESS` : aucune co-présence causale valide n'était disponible. Ne pas téléporter, fabriquer une perception, injecter une mémoire ou appeler directement le retrieval pour produire artificiellement un PASS.

Si la fenêtre V3c se termine sans situation valide, conclure `NOT EXERCISED UNDER VALID CONDITIONS`, pas « mémoire en échec ».

## Diagnostics V3c à conserver comme données, pas comme correctifs live

### `cognition_call_source_not_perceived`

Verdict : `B — HEALTHY BUT NOISY`.

Le volume élevé vient principalement du fait que l'orchestrateur teste des événements canoniques contre la vue perceptive de chaque résidente. Aucun churn logique, backlog durable ou starvation n'a été démontré.

Follow-ups séparés après V3c seulement :

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

## Ordre de travail autorisé

Tant que V3c/P0 n'est pas audité à fermeture :

1. laisser V3c continuer;
2. diagnostics read-only et consolidation documentaire permis;
3. exécuter le scénario mémoire A/B seulement quand les préconditions causales réelles existent;
4. à la fin : audit de fermeture P0;
5. ensuite seulement : Conversation State minimal;
6. puis Behavioral Opportunity Layer;
7. puis P3.5 Perception · Action · Sensorium.

Un seul chantier R&D runtime majeur à la fois.

## Interdictions immédiates

Ne pas :

- modifier WO95 pour masquer les idles de 600 s;
- patcher Chuu spécifiquement;
- réintroduire un quota fixe N appels LLM / fenêtre dans la cognition normale;
- ouvrir Conversation State ou BOL en parallèle de la fermeture P0;
- modifier les DB/runtime V3, V3b ou V3c utilisés comme preuves historiques;
- présenter une décision d'ingénierie comme une loi scientifique.

## Gouvernance

- ChatGPT : recherche, conception fonctionnelle, cohérence conceptuelle, documentation R&D.
- Grok : contre-audit scientifique adversarial indépendant.
- Codex : autorité sur l'architecture réelle, le code, les migrations, les invariants techniques, les tests et l'ordre d'implantation.
- Propriétaire : autorité finale produit/design.

**Verify twice. Commit once.**
