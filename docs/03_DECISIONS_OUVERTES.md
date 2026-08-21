# Décisions ouvertes — RIC

**Version :** 0.4  
**Date :** 21 août 2026  
**Statut :** actif

Ce document recense les arbitrages qui ne sont pas encore fermés. Il ne remplace pas `docs/01_REGISTRE_DECISIONS.md`, qui reste le registre autoritatif des décisions approuvées.

Une question ouverte ne doit pas être transformée silencieusement en architecture ou en règle produit par un work order.

## 1. Décisions historiques encore pertinentes

| ID | Sujet | Statut courant | Règle de conduite |
| --- | --- | --- | --- |
| OD-002 | Fournisseur/modèle principal à long terme | **ouverte** | Qwen3-14B est un provider de qualification observé, pas une sélection universelle irrévocable. Comparer qualité, confidentialité, coût, latence, contrat de sortie et compatibilité d'adaptation lorsque le produit l'exigera. |
| OD-003 | Budget financier / alertes | **reformulée** | Ne pas réintroduire un quota cognitif fixe. La télémétrie et des limites opérateur peuvent exister pour un fournisseur payant; elles restent distinctes de la politique de pertinence/fairness des appels cognitifs. |
| OD-004 | Cadence des décisions cognitives | **reformulée** | Privilégier événements, pertinence, fraîcheur, fairness, backpressure et anti-runaway plutôt qu'un nombre fixe d'appels/personnage/minute. Calibration fine empirique. |
| OD-006 | Oubli et consolidation | **ouverte, différée** | Définir après observation suffisante de la mémoire autobiographique réelle. Ne pas inférer une politique d'oubli depuis la seule structure append-only. |
| OD-007 | Rétention prompts/sorties/télémétrie | **ouverte** | L'observabilité existe; la politique de conservation/rotation à long terme reste à arbitrer selon diagnostic, confidentialité et coût disque. |
| OD-008 | Recherche sémantique / embeddings | **différée** | P0 doit rester fonctionnel sans dépendance vectorielle obligatoire. Évaluer après qualification du retrieval actuel. |
| OD-009 | Biographies approfondies et verrous d'évolution | **partiellement ouverte** | Le casting de référence est fixé. Les éléments figés/bornés/souples/libres restent à préciser lorsque l'évolution devient un chantier actif. |
| OD-010 | Interface sociale externe et commandes | **différée** | Définir à partir des flux moteur/cognition stabilisés; aucune interface ne devient source de vérité. |
| OD-011 | Détail stocké pour contenu intime/relationnel | **différée** | Décider avec les contrats de consentement, mémoire et confidentialité correspondants. |
| OD-012 | Rétention snapshots/backups | **ouverte, non urgente** | Distinguer snapshot de projection, checkpoint administratif, backup physique et export portable avant fixation des durées. |
| OD-013 | Durée de stabilisation pré-bêta | **ouverte** | V3c a été interrompu et n'est pas le test final de stabilité longue durée. Fixer la durée finale à partir des défauts réellement observés. |

OD-001 est fermé. Les anciennes formulations de OD-003/004 pouvant être lues comme un quota cognitif fixe sont supersédées.

---

## 2. P0 Memory — décisions de fermeture

### P0-OPEN-01 — preuve épisode → retrieval routé

**Autorité : MIXED (TECH + PRODUCT).**

Question : le chemin autobiographique doit-il être qualifié en runtime avant fermeture P0?

Preuve recherchée :

```text
parole/expérience accessible
→ admission
→ subjective_trace
→ épisode autobiographique
→ retrieval ultérieur
→ CognitionContext routé
→ provider réel
```

V3c ayant été interrompu, appliquer le mandat `docs/P0_V3C_READONLY_QUALIFICATION_MANDATE.md`. Si le chemin n'a pas été exercé sous préconditions valides : `NOT EXERCISED UNDER VALID CONDITIONS`, puis décision explicite sur la nécessité d'un nouveau rodage.

### P0-OPEN-02 — seeding depuis l'attention ordinaire

**Autorité : MIXED (SCI + PRODUCT + TECH).**

Question : P0 exige-t-il que des traces ordinaires puissent naturellement devenir des épisodes, ou le seeding social suffit-il au scope minimal?

État observé : les traces ordinaires peuvent rester `trace_only`; aucune règle universelle de clustering temporel ne doit être ajoutée sans justification.

### P0-OPEN-03 — déclencheur naturel de lifecycle/révision

**Autorité : MIXED.**

Question : la structure append-only de révision doit-elle être exercée par un trigger naturel avant fermeture P0?

La structure existe; cela ne démontre pas une politique psychologique de reconsolidation/oubli.

### P0-OPEN-04 — SCC et candidats mémoire

**Autorité : MIXED.**

Question : quelles formes de mémoire doivent être disponibles aux interprétations/appraisals SCC et à quel moment?

Ne pas brancher toute mémoire partout : préserver pertinence, subjectivité, provenance et limites de contexte.

---

## 3. Conversation State — prochain chantier après P0

**Maturité vérifiée :** R&D scientifique + contre-audit Grok clos (`SOLIDE`). Le dossier existe déjà; la prochaine porte est l'audit architectural Codex, pas une nouvelle recherche générale.

### CONV-OPEN-01 — traduction architecturale de l'état interactionnel minimal

**Autorité : TECH, sous contraintes fonctionnelles MIXED.**

Le dossier fonctionnel couvre déjà floors, participation/adressage, séquences ouvertes, repair, topic state, projets interactionnels, lapse et clôture. Codex doit déterminer comment ces contrats se raccordent à l'architecture réelle sans créer un deuxième propriétaire de mémoire ou de perception.

### CONV-OPEN-02 — frontière structure partagée / subjectivité privée

**Autorité : MIXED.**

Conserver la frontière : ce qui est publiquement/interactionnellement ouvert peut appartenir à la structure de conversation; compréhension, souvenir, croyance et interprétation restent propres aux agentes.

L'audit doit vérifier les cas où deux participantes n'ont pas la même perception/compréhension d'une même interaction.

### CONV-OPEN-03 — reprise, lapse, interruption et fermeture runtime

**Autorité : MIXED.**

La R&D décrit déjà ces phénomènes; restent à décider dans le produit réel les critères suffisamment minimaux pour une première tranche et les falsifications runtime associées.

Ne pas résoudre la répétition par un prompt cumulatif parallèle au Conversation State.

---

## 4. Behavioral Opportunity Layer (BOL)

**Maturité vérifiée :** R&D scientifique + contre-audit Grok clos (`SOLIDE`). L'audit architectural Codex reste à faire lorsque Conversation State minimal est suffisamment raccordé pour que la dépendance soit réelle et fraîche.

### BOL-OPEN-01 — raccord architectural du contrat d'opportunité

**Autorité : TECH sous contraintes MIXED.**

Le besoin fonctionnel est déjà consolidé :

```text
motifs + préférences + objectifs + contexte + capacités + environnement
→ petit ensemble d'opportunités comportementales pertinentes
```

Le dossier interdit un score psychologique universel, une hiérarchie fixe et l'omniscience canonique. Codex doit déterminer comment générer/borner/exposer ces candidates dans le dépôt réel.

### BOL-OPEN-02 — sémantique de `MotiveCandidate.possible_actions`

**Autorité : MIXED.**

Le champ est actuellement explicatif et n'alimente pas `activity_options`. Clarifier sa responsabilité et son nom si nécessaire afin qu'il ne soit pas confondu avec une liste d'actions légalement disponibles.

### BOL-OPEN-03 — sémantique de `no_action`

**Autorité : MIXED.**

Le contrat actuel collapse plusieurs situations : aucune opportunité pertinente, attente, maintien implicite, refus, information insuffisante, etc.

Décider quelles distinctions ont une utilité causale/diagnostique réelle. Ne pas ajouter un schéma uniquement pour demander au LLM une justification verbale.

### BOL-OPEN-04 — `sleep/rest` et autres activités hors whitelist

**Autorité : MIXED.**

`sleep` et `rest` sont exécutables mais absents de la whitelist de loisirs `planned_reflection`. Aucun contrat n'impose de les ajouter directement. Le BOL doit résoudre le problème génériquement avant tout patch isolé.

---

## 5. P3.5 Perception · Action · Sensorium

**Statut R&D :** plus de divergence fonctionnelle bloquante. R&D + contre-audit Grok + audit architectural Codex clos; clarifications acceptées; verdict `READY FOR WORK ORDER`.

Les anciens `P35-OPEN-01/02` ne sont donc plus des décisions R&D ouvertes : la séparation `signal accessible ≠ détection ≠ attention ≠ accès cognitif` et `affordance physique ≠ opportunité BOL` est consolidée.

Reste seulement, lorsque son tour arrive :

- préflight frais de `origin/product/current`;
- ouverture d'un WO borné à partir du dossier audité;
- décisions TECH locales si l'architecture a évolué depuis l'audit;
- aucune réouverture scientifique sans divergence nouvelle.

---

## 6. Adaptation LLM / PEFT-LoRA

Dossier : `docs/R_D_LORA_ADAPTATION_LLM.md`.

**Statut :** expérimentation hors runtime permise; utilité produit non démontrée; intégration runtime placée après P3.5.

### LORA-OPEN-01 — critère d'adoption

**Autorité : PRODUCT + MIXED.**

Question : quel gain contractuel justifie la dette d'entraînement/versionnement/intégration d'un adaptateur?

Aucun seuil arbitraire n'est encore fixé. Le gain doit être reproductible sur benchmark réservé, ne pas provenir d'une sur-abstention et ne pas créer de régression majeure.

### LORA-OPEN-02 — gouvernance du dataset et du benchmark

**Autorité : MIXED.**

Décider/versionner :

- provenance de chaque exemple;
- séparation train/validation/test par familles de scénario;
- règles anti-fuite;
- usage ou non de données historiques de runtime;
- politique de conservation de datasets sensibles;
- benchmark métamorphique et hors domaine.

Principe déjà retenu : **benchmark gelé avant le dataset d'entraînement**.

### LORA-OPEN-03 — backend d'entraînement AMD

**Autorité : TECH.**

La RX 7800 XT est supportée par ROCm en WSL2 dans la matrice actuelle; bitsandbytes expose `gfx1101` pour ROCm/4-bit. Il faut néanmoins qualifier la stack réelle avant de la choisir.

Premier verdict à produire : `FEASIBLE / FEASIBLE WITH LIMITS / NOT YET FEASIBLE`.

Aucun besoin de modifier RIC pour ce smoke-test.

### LORA-OPEN-04 — identité, activation et rollback runtime

**Autorité : TECH.**

Avant intégration : provenance observable `base_model + adapter_id/version`, activation/désactivation testable, rollback vers le modèle de base, comportement en cas d'adaptateur manquant/incompatible et choix merge/non-merge.

Préférence R&D initiale : conserver l'adaptateur séparé pendant les cycles de qualification; décision d'architecture finale à Codex.

### LORA-OPEN-05 — réduction éventuelle du prompt après adaptation

**Autorité : MIXED.**

Ne pas retirer automatiquement les invariants du prompt dès qu'un LoRA semble les avoir appris. Toute réduction doit être A/B testée afin de préserver falsifiabilité, provider interchangeability et robustesse.

### Invariant

```text
état dynamique explicite ≠ poids du modèle
```

Le LoRA général ne doit pas stocker casting, souvenirs, relations, consentements, état conversationnel ou règles physiques.

---

## 7. Follow-ups techniques post-V3c

Ces points sont des candidats à des lots séparés après le rapport V3c. Aucun ne justifie un correctif live ou une modification de l'artefact historique.

### TECH-OPEN-01 — `character_moved` / perception

Deux événements de déplacement de Sophie ont été rejetés parce que le payload ne contenait pas le champ `connector` attendu. Vérifier producteur/consommateur et corriger génériquement seulement si le défaut est confirmé hors échantillon.

### TECH-OPEN-02 — `source_event_seq` sur invalidation

Le chemin `cognition_call_source_not_perceived` ne conserve pas directement `source_event_seq`; l'audit nécessite une jointure via l'événement d'orchestrateur. Décider si la traçabilité justifie une correction.

### TECH-OPEN-03 — préfiltrage perceptif

Le garde `source_not_perceived` est sain mais bruyant. Évaluer un filtrage plus précoce seulement si l'autorité perceptive existante peut être réutilisée exactement. Ne pas créer une deuxième règle de perceptibilité.

### TECH-OPEN-04 — WO95 idle technique 600 s

Mesurer fréquence, interruptions et expirations dans le rapport V3c. Ne pas raccourcir le délai pour masquer les `no_action` de Chuu ou un manque d'opportunités.

---

## 8. Ordre de résolution

```text
rapport V3c read-only
→ audit/fermeture P0
→ nouveau rodage P0 isolé seulement si preuve nécessaire
→ audit architectural Conversation State
→ WO Conversation State + qualification
→ audit architectural BOL sur base fraîche
→ WO BOL + qualification
→ WO P3.5 (audit déjà clos, préflight frais)
→ porte d'intégration LoRA
→ Affect
→ cognition animale
→ physiologie plus large
```

En parallèle autorisé : benchmark/dataset/smoke-test LoRA hors runtime.

Les follow-ups TECH post-V3c peuvent être qualifiés entre ces étapes seulement s'ils ne brouillent pas la baseline d'un chantier majeur.

---

## 9. Règle de décision

Avant de fermer une question :

1. vérifier l'état réel du dépôt;
2. distinguer fait observé, conclusion incertaine, hypothèse de modélisation et choix d'ingénierie;
3. chercher les conséquences sur les invariants et propriétaires persistants;
4. indiquer l'autorité dominante `TECH / SCI / PRODUCT / MIXED`;
5. consigner la décision approuvée dans `docs/01_REGISTRE_DECISIONS.md` si elle devient autoritative;
6. seulement ensuite traduire en WO/code selon `docs/GOUVERNANCE_GIT.md`.
