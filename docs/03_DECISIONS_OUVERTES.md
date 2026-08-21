# Décisions ouvertes — RIC

**Version :** 0.4  
**Date :** 21 août 2026  
**Statut :** actif

Ce document recense les arbitrages qui ne sont pas encore fermés. Il ne remplace pas `docs/01_REGISTRE_DECISIONS.md`, qui reste le registre autoritatif des décisions approuvées.

Une question ouverte ne doit pas être transformée silencieusement en architecture ou en règle produit par un work order.

## 1. Décisions historiques encore pertinentes

| ID | Sujet | Statut courant | Règle de conduite |
| --- | --- | --- | --- |
| OD-002 | Fournisseur/modèle principal à long terme | **ouverte** | Qwen3-14B est un provider de qualification observé, pas une sélection universelle irrévocable. Comparer qualité, confidentialité, coût, latence, contrat de sortie et compatibilité d'adaptation lorsque nécessaire. |
| OD-003 | Budget financier / alertes | **reformulée** | Ne pas réintroduire un quota cognitif fixe. Télémétrie et limites opérateur pour un fournisseur payant restent distinctes de pertinence/fairness. |
| OD-004 | Cadence des décisions cognitives | **reformulée** | Privilégier événements, pertinence, fraîcheur, fairness, backpressure et anti-runaway plutôt qu'un quota fixe. Calibration empirique. |
| OD-006 | Oubli et consolidation | **ouverte, différée** | Définir après observation suffisante de la mémoire autobiographique réelle. Ne pas inférer une politique d'oubli depuis la structure append-only. |
| OD-007 | Rétention prompts/sorties/télémétrie | **ouverte** | Politique long terme à arbitrer selon diagnostic, confidentialité et coût disque. |
| OD-008 | Recherche sémantique / embeddings | **différée** | P0 doit fonctionner sans dépendance vectorielle obligatoire. |
| OD-009 | Biographies approfondies et verrous d'évolution | **partiellement ouverte** | Les limites d'évolution restent à préciser lorsqu'elles deviennent actives. |
| OD-010 | Interface sociale externe et commandes | **différée** | Définir après stabilisation des flux; aucune interface ne devient source de vérité. |
| OD-011 | Détail stocké pour contenu intime/relationnel | **différée** | Décider avec consentement, mémoire et confidentialité. |
| OD-012 | Rétention snapshots/backups | **ouverte, non urgente** | Distinguer snapshot, checkpoint, backup physique et export portable. |
| OD-013 | Durée de stabilisation pré-bêta | **ouverte** | V3c a été interrompu; il ne qualifie pas la stabilité longue durée finale. |

OD-001 est fermé. Les anciennes formulations de OD-003/004 pouvant être lues comme un quota cognitif fixe sont supersédées.

## 2. P0 Memory — décisions de fermeture

### P0-OPEN-01 — preuve épisode → retrieval routé

**Autorité : MIXED (TECH + PRODUCT).**

Preuve recherchée :

```text
expérience accessible
→ admission
→ subjective_trace
→ épisode autobiographique
→ retrieval ultérieur
→ CognitionContext routé
→ provider réel
```

V3c étant interrompu, utiliser `docs/P0_V3C_READONLY_QUALIFICATION_MANDATE.md`. Si le chemin n'a jamais été exercé sous préconditions valides, conserver `NOT EXERCISED UNDER VALID CONDITIONS` et décider ensuite si un nouveau rodage est requis.

### P0-OPEN-02 — seeding depuis l'attention ordinaire

**Autorité : MIXED (SCI + PRODUCT + TECH).**

P0 exige-t-il qu'une expérience ordinaire puisse naturellement devenir un épisode, ou le seeding social suffit-il au scope minimal? Les traces ordinaires peuvent actuellement rester `trace_only`; aucune règle universelle de clustering temporel n'est justifiée par défaut.

### P0-OPEN-03 — déclencheur naturel de lifecycle/révision

**Autorité : MIXED.**

La structure append-only existe. Décider si un trigger naturel doit être exercé avant fermeture P0. Ne pas confondre cette structure avec une reconsolidation/oubli psychologique démontré.

### P0-OPEN-04 — SCC et candidats mémoire

**Autorité : MIXED.**

Quelles formes de mémoire doivent être disponibles aux interprétations/appraisals SCC et quand? Ne pas brancher toute mémoire partout : préserver pertinence, subjectivité, provenance et limites de contexte.

## 3. Conversation State — prochain chantier après P0

**Maturité : R&D scientifique + contre-audit Grok clos (`SOLIDE`).** La prochaine porte est l'audit architectural Codex.

### CONV-OPEN-01 — traduction architecturale de l'état interactionnel minimal

**Autorité : TECH sous contraintes MIXED.**

Le dossier fonctionnel couvre déjà floors, participation/adressage, séquences ouvertes, repair, topic state, projets interactionnels, lapse et clôture. Codex doit déterminer comment les raccorder sans créer un deuxième propriétaire de mémoire/perception.

### CONV-OPEN-02 — structure partagée / subjectivité privée

**Autorité : MIXED.**

Conserver la frontière : l'état publiquement interactionnel peut être partagé; compréhension, souvenir, croyance et interprétation restent propres à chaque agente.

### CONV-OPEN-03 — reprise, lapse, interruption et fermeture runtime

**Autorité : MIXED.**

Décider le plus petit sous-ensemble implantable et ses falsifications. Ne pas résoudre répétition/reprise avec un prompt cumulatif parallèle.

## 4. Behavioral Opportunity Layer (BOL)

**Maturité : R&D scientifique + contre-audit Grok clos (`SOLIDE`).** Audit architectural Codex à faire sur une base fraîche après raccordement suffisant de Conversation State.

### BOL-OPEN-01 — raccord architectural du contrat d'opportunité

**Autorité : TECH sous contraintes MIXED.**

```text
motifs + préférences + objectifs + contexte + capacités + environnement
→ petit ensemble d'opportunités comportementales pertinentes
```

Le dossier interdit score psychologique universel, hiérarchie fixe et omniscience canonique. Codex doit déterminer génération/bornage/exposition des candidates dans le dépôt réel.

### BOL-OPEN-02 — `MotiveCandidate.possible_actions`

**Autorité : MIXED.**

Le champ est explicatif et n'alimente pas `activity_options`. Clarifier sa responsabilité afin qu'il ne soit pas interprété comme une liste légale d'actions.

### BOL-OPEN-03 — `no_action`

**Autorité : MIXED.**

Le contrat collapse plusieurs situations : aucune opportunité pertinente, attente, maintien implicite, refus, information insuffisante, etc. Ne distinguer que les causes ayant une utilité causale/diagnostique réelle.

### BOL-OPEN-04 — `sleep/rest` hors whitelist

**Autorité : MIXED.**

`sleep` et `rest` sont exécutables mais absents de la whitelist de loisirs `planned_reflection`. Aucun patch isolé avant contrat BOL générique.

## 5. P3.5 Perception · Action · Sensorium

**Statut : R&D + contre-audit Grok + audit architectural Codex clos; clarifications acceptées; `READY FOR WORK ORDER`.**

Les anciens points ouverts sur le contrat sensoriel et la frontière affordance/BOL sont consolidés :

```text
signal accessible ≠ détection ≠ attention ≠ accès cognitif
affordance physique ≠ opportunité comportementale
```

Quand son tour arrive : préflight frais de `origin/product/current`, puis WO borné. Ne rouvrir science/architecture qu'en cas de divergence nouvelle.

## 6. Adaptation LLM / PEFT-LoRA

Dossier : `docs/92_R_D_LORA_ADAPTATION_LLM.md`.

**Statut : expérimentation hors runtime permise; utilité produit non démontrée; intégration après P3.5.**

### LORA-OPEN-01 — critère d'adoption

**Autorité : PRODUCT + MIXED.**

Quel gain contractuel justifie dette d'entraînement, versionnement et intégration? Le gain doit être reproductible sur benchmark réservé, ne pas provenir d'une sur-abstention et ne pas créer de régression majeure.

### LORA-OPEN-02 — gouvernance dataset / benchmark

**Autorité : MIXED.**

Décider/versionner provenance des exemples, séparation train/validation/test par familles de scénarios, règles anti-fuite, usage éventuel de données runtime et politique de conservation. Principe déjà retenu : **benchmark gelé avant dataset d'entraînement**.

### LORA-OPEN-03 — backend AMD

**Autorité : TECH.**

La RX 7800 XT est explicitement supportée dans la matrice WSL2 ROCm actuelle et `gfx1101` est couvert par bitsandbytes ROCm. Qualifier la stack réelle avant choix définitif : `FEASIBLE / FEASIBLE WITH LIMITS / NOT YET FEASIBLE`.

### LORA-OPEN-04 — identité, activation et rollback runtime

**Autorité : TECH.**

Avant intégration : provenance `base_model + adapter_id/version`, activation/désactivation testable, rollback vers base, gestion adaptateur manquant/incompatible et choix merge/non-merge. Préférence R&D initiale : adaptateur séparé pendant qualification; architecture finale à Codex.

### LORA-OPEN-05 — réduction éventuelle du prompt

**Autorité : MIXED.**

Ne pas retirer automatiquement les invariants du prompt parce qu'un LoRA semble les avoir appris. Toute réduction doit être A/B testée pour préserver falsifiabilité et interchangeabilité du provider.

Invariant :

```text
état dynamique explicite ≠ poids du modèle
```

## 7. Follow-ups techniques post-V3c

Aucun ne justifie un correctif live ni une modification de l'artefact historique.

### TECH-OPEN-01 — `character_moved` / perception

Vérifier le contrat producteur/consommateur autour du champ `connector`; corriger génériquement seulement si le défaut est confirmé hors échantillon.

### TECH-OPEN-02 — `source_event_seq` sur invalidation

Décider si la traçabilité justifie de conserver directement `source_event_seq` sur `cognition_call_source_not_perceived`.

### TECH-OPEN-03 — préfiltrage perceptif

Évaluer un filtrage plus précoce seulement si l'autorité perceptive existante peut être réutilisée exactement; ne pas créer une deuxième règle.

### TECH-OPEN-04 — WO95 idle 600 s

Mesurer fréquence, interruptions et expirations dans le rapport V3c. Ne pas raccourcir le délai pour masquer les `no_action`.

## 8. Ordre de résolution

```text
rapport V3c read-only
→ audit/fermeture P0
→ nouveau rodage P0 seulement si preuve nécessaire
→ audit architectural Conversation State
→ WO Conversation State + qualification
→ audit architectural BOL sur base fraîche
→ WO BOL + qualification
→ WO P3.5 (audit déjà clos)
→ porte d'intégration LoRA
→ Affect
→ cognition animale
→ physiologie plus large
```

En parallèle autorisé : benchmark/dataset/smoke-test LoRA hors runtime.

## 9. Règle de décision

Avant de fermer une question :

1. vérifier l'état réel du dépôt;
2. distinguer fait observé, conclusion incertaine, hypothèse de modélisation et choix d'ingénierie;
3. chercher les conséquences sur invariants et propriétaires persistants;
4. indiquer l'autorité dominante `TECH / SCI / PRODUCT / MIXED`;
5. consigner la décision approuvée dans `docs/01_REGISTRE_DECISIONS.md` si elle devient autoritative;
6. seulement ensuite traduire en WO/code selon `docs/GOUVERNANCE_GIT.md`.
