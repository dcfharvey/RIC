# Décisions ouvertes — RIC

**Version :** 0.4  
**Date :** 21 août 2026  
**Statut :** actif

Ce document recense les arbitrages qui ne sont pas encore fermés. Il ne remplace pas `docs/01_REGISTRE_DECISIONS.md`, registre autoritatif des décisions approuvées.

Une question ouverte ne doit pas être transformée silencieusement en architecture ou règle produit par un work order.

## 1. Décisions historiques encore pertinentes

| ID | Sujet | Statut courant | Règle de conduite |
| --- | --- | --- | --- |
| OD-002 | Fournisseur/modèle principal à long terme | **ouverte** | Qwen3-14B a servi de provider de qualification; ce n'est pas une sélection universelle irrévocable. Comparer qualité, confidentialité, coût, latence, contrat de sortie et adaptation éventuelle lorsque le produit l'exige. |
| OD-003 | Budget financier / alertes | **reformulée** | Ne pas réintroduire un quota cognitif fixe. Télémétrie et limites opérateur peuvent exister pour un fournisseur payant mais restent distinctes de pertinence/fairness. |
| OD-004 | Cadence des décisions cognitives | **reformulée** | Privilégier événements, pertinence, fraîcheur, fairness, backpressure et anti-runaway plutôt qu'un nombre fixe d'appels par personnage/minute. Calibration fine empirique. |
| OD-006 | Oubli et consolidation | **ouverte, différée** | Définir après observation suffisante de la mémoire autobiographique réelle. Ne pas inférer une politique d'oubli depuis la seule structure append-only. |
| OD-007 | Rétention prompts/sorties/télémétrie | **ouverte** | La politique de conservation/rotation à long terme reste à arbitrer selon diagnostic, confidentialité et coût disque. |
| OD-008 | Recherche sémantique / embeddings | **différée** | P0 doit rester fonctionnel sans dépendance vectorielle obligatoire. Évaluer après qualification du retrieval actuel. |
| OD-009 | Biographies approfondies et verrous d'évolution | **partiellement ouverte** | Le casting de référence est fixé; les éléments figés/bornés/souples/libres restent à préciser lorsque l'évolution devient active. |
| OD-010 | Interface sociale externe et commandes | **différée** | Définir à partir des flux moteur/cognition stabilisés; aucune interface ne devient source de vérité. |
| OD-011 | Détail stocké pour contenu intime/relationnel | **différée** | Décider avec les contrats consentement, mémoire et confidentialité correspondants. |
| OD-012 | Rétention snapshots/backups | **ouverte, non urgente** | Distinguer snapshot de projection, checkpoint administratif, backup physique et export portable avant fixation des durées. |
| OD-013 | Durée de stabilisation pré-bêta | **ouverte** | V3c a été interrompu et n'est pas le test final de stabilité longue durée. Fixer la durée finale à partir des défauts réellement observés. |

OD-001 est fermé. Les anciennes formulations de OD-003/004 suggérant une cadence/quota fixe sont supersédées par la politique actuelle de flux cognitif sans quota fixe normal.

## 2. P0 Memory — décisions de fermeture

V3c est **interrompu**. Il ne doit plus être décrit comme un rodage en cours. Ses artefacts restent des preuves read-only et l'audit doit distinguer `PASS`, `FAIL`, `NOT EXERCISED UNDER VALID CONDITIONS` et `INSUFFICIENT EVIDENCE`.

### P0-OPEN-01 — preuve épisode → retrieval routé

**Question :** le chemin autobiographique doit-il être observé de bout en bout en runtime avant fermeture P0 ?

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

La tentative de scène A connue n'avait pas de précondition causale valide. Le rapport V3c doit d'abord établir ce qui s'est réellement produit. Si la preuve requise manque, décider explicitement si un nouveau rodage isolé est nécessaire; ne pas reprendre/modifier V3c.

**Autorité de fermeture : MIXED** — preuve technique par Codex/outillage; portée fonctionnelle P0 par ChatGPT + propriétaire.

### P0-OPEN-02 — seeding depuis l'attention ordinaire

**Question :** P0 exige-t-il que des traces d'expériences ordinaires puissent naturellement devenir des épisodes, ou le seeding social suffit-il au scope P0 ?

État observé : des traces d'attention ordinaires peuvent rester `trace_only`; aucune règle universelle de clustering temporel ne doit être ajoutée sans justification.

**Autorité : SCI/PRODUCT**, avec audit TECH de l'impact réel avant implémentation.

### P0-OPEN-03 — déclencheur naturel de lifecycle/révision

**Question :** la structure append-only de révision doit-elle être exercée par un trigger naturel avant fermeture P0 ?

La structure existe; aucune politique psychologique générale de reconsolidation/oubli n'est démontrée.

**Autorité : MIXED.**

### P0-OPEN-04 — SCC et candidats mémoire

**Question :** quelles formes de mémoire doivent être disponibles aux interprétations/appraisals SCC et à quel moment ?

Ne pas brancher toute mémoire partout : préserver pertinence, subjectivité, provenance et limites de contexte.

**Autorité : SCI/MIXED.**

## 3. Conversation State — prochain chantier après P0

**Maturité R&D : peer review scientifique Grok clos — SOLIDE; prêt pour audit architectural Codex.**

La science générale du dossier n'est pas à refaire avant le chantier. La prochaine porte, après fermeture P0, est l'audit architectural contre `product/current`, puis un WO borné si aucune divergence bloquante n'apparaît.

### CONV-OPEN-01 — état partagé minimal

Déterminer l'ensemble minimal qui doit persister au niveau interactionnel : floors/participation, séquences ouvertes, topic/project state, repair, lapse/closing, etc., en utilisant le dossier R&D consolidé comme autorité fonctionnelle plutôt qu'en redéfinissant la théorie depuis zéro.

### CONV-OPEN-02 — frontière scène partagée / mémoire privée

Déterminer ce qui appartient à la structure de conversation et ce qui reste dans la cognition/mémoire propre à chaque agente.

### CONV-OPEN-03 — répétition, lapse et reprise

Définir comment le modèle structurel réduit les répétitions, traite les silences/lapses et permet reprise ou clôture après interruption sans scripts de personnage ni accumulation arbitraire de prompt.

**Autorité du chantier : MIXED** — science/fonctionnel déjà consolidés; architecture/owners/tests à Codex; choix produit au propriétaire.

## 4. Behavioral Opportunity Layer (BOL)

**Maturité R&D : peer review scientifique Grok clos — SOLIDE; prêt pour audit architectural Codex.**

Le prochain travail BOL, après Conversation State, est donc l'audit architectural contre le produit alors courant, pas une nouvelle recherche générale.

### BOL-OPEN-01 — contrat fonctionnel des opportunités

Besoin :

```text
motifs + préférences + objectifs/intention
+ contexte subjectivement accessible
+ capacités + environnement
→ petit ensemble d'opportunités comportementales pertinentes
```

Points à confirmer dans l'audit/WO : entrées réellement nécessaires, bornage, séparation génération/classement/sélection/validation, explicabilité utile sans score psychologique universel, et généricité inter-agents.

L'architecture technique n'est pas décidée ici.

### BOL-OPEN-02 — sémantique de `MotiveCandidate.possible_actions`

Le champ est actuellement explicatif et n'alimente pas `activity_options`. Son nom/sens doivent être clarifiés pour éviter toute confusion avec une liste d'actions légalement offertes au provider.

### BOL-OPEN-03 — sémantique de `no_action`

Le contrat actuel collapse plusieurs situations : absence de motivation, aucune opportunité pertinente, refus/attente, contexte insuffisant, etc.

Décider si ces causes doivent être discriminables structurellement. Ne pas modifier le schéma uniquement pour obtenir une justification verbale décorative du LLM.

### BOL-OPEN-04 — sleep/rest et actions hors whitelist

`sleep` et `rest` sont exécutables par le moteur mais absents de la whitelist des loisirs `planned_reflection`. Aucun contrat existant n'impose de les y ajouter directement.

Ne pas faire un patch isolé avant le contrat générique d'opportunité.

**Autorité du chantier : MIXED.**

## 5. P3.5 Perception · Action · Sensorium

**Maturité : R&D + contre-audit Grok + audit architectural Codex CLOS — SOLIDE AVEC RÉSERVES — READY FOR WORK ORDER.**

Les anciennes questions P35-OPEN-01/02 ont été suffisamment clarifiées pour lever le blocage architectural général. Elles restent des dimensions à préserver dans les WOs/tests, pas des raisons de recommencer l'audit complet.

### P35-CONTRACT-01 — chaîne sensorielle à préserver

```text
signal accessible
≠ détection
≠ sélection attentionnelle
≠ accès subjectif exploitable par la cognition
```

### P35-CONTRACT-02 — affordance physique versus opportunité BOL

```text
affordance physique ≠ opportunité comportementale
```

Le moteur/capacité garde l'autorité sur le possible; BOL concerne ce qui devient comportementalement pertinent.

### P35-GATE-01 — ouverture future du WO

Quand son tour arrive après BOL : refaire le préflight `product/current`, vérifier que l'évolution du produit n'invalide pas l'audit existant, puis ouvrir un WO borné. Aucun nouvel audit scientifique/architectural général n'est requis par défaut.

**Autorité du WO : TECH avec invariants MIXED déjà approuvés.**

## 6. Adaptation LLM / PEFT-LoRA

Dossier actif : `docs/92_R_D_LORA_ADAPTATION_LLM.md`.

La R&D hors runtime peut avancer en parallèle; l'intégration runtime attend normalement Conversation State + BOL + P3.5.

### LORA-OPEN-01 — utilité comportementale

**Question :** un unique adaptateur RIC améliore-t-il de façon reproductible les frontières/invariants, la provenance, l'abstention et les contrats de sortie par rapport au modèle de base ?

Le benchmark doit être figé avant le dataset. Un gain sur le train ou une préférence qualitative ne suffit pas.

**Autorité : SCI/TECH.**

### LORA-OPEN-02 — frontière des connaissances apprenables

**Question :** quelles propriétés stables du comportement LLM peuvent être adaptées sans encoder d'état dynamique ou déplacer une autorité hors moteur ?

Interdit comme cible persistante : faits du monde, souvenirs individuels, relations/permissions/consentements actuels, Conversation State, opportunités BOL, règles physiques/affordances et scripts personnage→comportement.

**Autorité : MIXED.**

### LORA-OPEN-03 — pipeline/runtime d'adaptateur

**Question future :** quel pipeline QLoRA et quel lifecycle de chargement/activation/hotswap/versioning/rollback conviennent au runtime réel et au matériel cible ?

Ne pas prescrire cette architecture avant audit Codex et smoke-test sur la machine réelle.

**Autorité : TECH.**

### LORA-OPEN-04 — adoption produit

**Question :** si l'adaptateur surpasse la baseline sans régression inacceptable, devient-il option runtime, baseline de qualification, ou reste-t-il expérimental ?

**Autorité : PRODUCT**, après preuve TECH/SCI.

## 7. Follow-ups techniques post-V3c

Ces points sont candidats à des lots séparés après le rapport V3c. Aucun ne justifie une modification de l'artefact historique.

### TECH-OPEN-01 — `character_moved` / perception

Certains déplacements de Sophie ont été rejetés parce que le payload ne contenait pas le champ `connector` attendu. Vérifier producteur/consommateur et corriger génériquement seulement si le défaut est confirmé hors échantillon.

### TECH-OPEN-02 — `source_event_seq` sur invalidation

Le chemin `cognition_call_source_not_perceived` ne conserve pas directement `source_event_seq`; l'audit détaillé nécessite une jointure. Décider si la traçabilité justifie une correction.

### TECH-OPEN-03 — préfiltrage perceptif

Le garde `source_not_perceived` est sain mais bruyant. Évaluer un filtrage plus précoce seulement si l'autorité perceptive existante peut être réutilisée exactement; ne pas créer une deuxième règle de perceptibilité.

### TECH-OPEN-04 — WO95 idle technique 600 s

Mesurer fréquence, interruptions et expirations sur un rodage valide. Ne pas raccourcir le délai pour masquer les `no_action` ou un manque d'opportunités.

## 8. Ordre de résolution

```text
rapport V3c read-only
→ audit de fermeture P0
→ nouveau rodage P0 isolé seulement si nécessaire
→ audit architectural + WO Conversation State
→ audit architectural + WO BOL
→ WO P3.5 déjà prêt R&D/architecture
→ porte d'intégration LoRA
→ chantiers cognitifs/physiologiques suivants
```

La R&D LoRA hors runtime peut avancer en parallèle. Les follow-ups techniques indépendants peuvent être qualifiés entre les grandes étapes seulement s'ils ne brouillent pas une baseline et si leur portée est réellement séparée.

## 9. Règle de décision

Avant de fermer une question :

1. vérifier l'état réel du dépôt;
2. distinguer fait observé, conclusion incertaine, hypothèse de modélisation et choix d'ingénierie;
3. chercher les conséquences sur invariants et propriétaires persistants;
4. identifier l'autorité requise (`TECH`, `SCI`, `PRODUCT`, `MIXED`);
5. consigner toute décision approuvée devenue autoritative dans `docs/01_REGISTRE_DECISIONS.md`;
6. seulement ensuite traduire en WO/code selon `docs/GOUVERNANCE_GIT.md`.
