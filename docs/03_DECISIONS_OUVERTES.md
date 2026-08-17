# Décisions ouvertes — RIC

**Version :** 0.3  
**Date :** 16 août 2026  
**Statut :** actif

Ce document recense les arbitrages qui ne sont pas encore fermés. Il ne remplace pas `docs/01_REGISTRE_DECISIONS.md`, qui reste le registre autoritatif des décisions approuvées.

Une question ouverte ne doit pas être transformée silencieusement en architecture ou en règle produit par un work order.

## 1. Décisions historiques encore pertinentes

| ID | Sujet | Statut courant | Règle de conduite |
| --- | --- | --- | --- |
| OD-002 | Fournisseur/modèle principal à long terme | **ouverte** | Qwen3-14B est le provider de qualification V3c, pas une sélection universelle irrévocable. Comparer qualité, confidentialité, coût, latence et contrat de sortie lorsque le produit l'exigera. |
| OD-003 | Budget financier / alertes | **reformulée** | Ne pas réintroduire un quota cognitif fixe. La télémétrie et des limites opérateur peuvent exister pour un fournisseur payant; elles restent distinctes de la politique de pertinence/fairness des appels cognitifs. |
| OD-004 | Cadence des décisions cognitives | **reformulée** | Le runtime doit privilégier événements, pertinence, fraîcheur, fairness, backpressure et anti-runaway plutôt qu'un nombre fixe d'appels par personnage/minute. La calibration fine reste empirique. |
| OD-006 | Oubli et consolidation | **ouverte, différée** | Définir après observation suffisante de la mémoire autobiographique réelle. Ne pas inférer une politique d'oubli depuis la seule structure append-only. |
| OD-007 | Rétention prompts/sorties/télémétrie | **ouverte** | L'observabilité exacte existe; la politique de conservation/rotation à long terme reste à arbitrer selon diagnostic, confidentialité et coût disque. |
| OD-008 | Recherche sémantique / embeddings | **différée** | P0 doit rester fonctionnel sans dépendance vectorielle obligatoire. Évaluer après qualification du retrieval actuel. |
| OD-009 | Biographies approfondies et verrous d'évolution | **partiellement ouverte** | Le casting de référence est fixé. Les éléments figés/bornés/souples/libres restent à préciser lorsque l'évolution des personnages devient un chantier actif. |
| OD-010 | Interface sociale externe et commandes | **différée** | Définir à partir des flux moteur/cognition réellement stabilisés; aucune interface ne devient source de vérité. |
| OD-011 | Détail stocké pour contenu intime/relationnel | **différée** | Décider avec les contrats de consentement, mémoire et confidentialité correspondants. |
| OD-012 | Rétention snapshots/backups | **ouverte, non urgente** | Distinguer snapshot de projection, checkpoint administratif, backup physique et export portable avant fixation des durées. |
| OD-013 | Durée de stabilisation pré-bêta | **ouverte** | Le rodage V3c est une qualification ciblée, pas le test final de stabilité longue durée du produit. Fixer la durée finale à partir des défauts réellement observés. |

OD-001 (langage/runtime Python) est fermé. Les anciennes formulations de OD-003/004 qui pouvaient être lues comme une cadence/quota cognitif fixe sont supersédées par la politique actuelle de flux cognitif sans quota fixe normal.

## 2. P0 Memory — décisions de fermeture

### P0-OPEN-01 — preuve épisode → retrieval routé

**Question :** le chemin autobiographique doit-il être considéré qualifié en runtime avant fermeture P0 ?

État actuel : oui comme critère recherché, mais V3c n'a pas encore exercé la scène sociale A sous préconditions causales valides.

Preuve recherchée :

```text
parole accessible
→ admission
→ subjective_trace
→ épisode autobiographique
→ retrieval ultérieur
→ CognitionContext routé
→ provider réel
```

Si aucune co-présence valide n'arrive pendant V3c, consigner `NOT EXERCISED UNDER VALID CONDITIONS` et décider explicitement si une qualification dédiée supplémentaire est requise.

### P0-OPEN-02 — seeding depuis l'attention ordinaire

**Question :** P0 exige-t-il que des traces d'expériences ordinaires puissent naturellement devenir des épisodes, ou le seeding social suffit-il au scope P0 ?

État observé : les traces d'attention ordinaires peuvent rester `trace_only`; aucune règle universelle de clustering temporel ne doit être ajoutée sans justification.

### P0-OPEN-03 — déclencheur naturel de lifecycle/révision

**Question :** la structure append-only de révision doit-elle être exercée par un trigger naturel avant fermeture P0 ?

La structure existe; aucune politique psychologique générale de reconsolidation/oubli n'est encore démontrée.

### P0-OPEN-04 — SCC et candidats mémoire

**Question :** quelles formes de mémoire doivent être disponibles aux interprétations/appraisals SCC et à quel moment ?

Ne pas brancher toute mémoire partout : préserver pertinence, subjectivité, provenance et limites de contexte.

## 3. Conversation State — prochain chantier après P0

### CONV-OPEN-01 — état partagé minimal

Définir ce qui doit persister au niveau de la scène pour assurer continuité sans devenir mémoire omnisciente : sujet courant, actes/engagements conversationnels, questions ouvertes, état de clôture, etc.

### CONV-OPEN-02 — frontière scène partagée / mémoire privée

Déterminer quelles informations appartiennent à la structure de conversation et lesquelles doivent rester dans la cognition/mémoire propre à chaque agente.

### CONV-OPEN-03 — répétition et reprise

Définir comment détecter/limiter les répétitions et comment reprendre ou clore une conversation interrompue sans scripts de personnage ni accumulation arbitraire de prompt.

## 4. Behavioral Opportunity Layer (BOL)

### BOL-OPEN-01 — contrat fonctionnel des opportunités

Le diagnostic V3c a confirmé le besoin suivant :

```text
motifs + préférences + objectifs + contexte + capacités + environnement
→ petit ensemble d'opportunités comportementales pertinentes
```

Questions ouvertes :

- quelles entrées sont nécessaires versus optionnelles;
- comment borner le nombre d'opportunités;
- comment distinguer génération, classement, sélection et validation;
- comment conserver une explication suffisante sans fabriquer un « score psychologique universel »;
- comment préserver la généricité pour humains, Luna, Chuu et futurs agents.

L'architecture technique n'est pas décidée ici; Codex la déterminera à partir du dépôt lorsque le contrat fonctionnel sera approuvé.

### BOL-OPEN-02 — sémantique de `MotiveCandidate.possible_actions`

Le champ est actuellement explicatif et n'alimente pas `activity_options`. Son nom et sa sémantique doivent être clarifiés lors du chantier pertinent afin d'éviter qu'il soit confondu avec une liste d'actions légalement offertes au provider.

### BOL-OPEN-03 — sémantique de `no_action`

Le contrat actuel collapse au moins plusieurs situations possibles : absence de motivation, aucune option pertinente, refus volontaire, attente ou contexte insuffisant.

Décider si le BOL/contrat décisionnel doit rendre ces causes plus discriminables. Ne pas modifier le schéma uniquement pour obtenir une justification verbale du LLM.

### BOL-OPEN-04 — sleep/rest et autres actions hors whitelist

`sleep` et `rest` sont exécutables par le moteur mais absents de la whitelist des loisirs `planned_reflection`. Aucun contrat existant n'impose qu'ils soient ajoutés directement à cette whitelist.

Ne pas faire un patch `sleep/rest` isolé avant d'avoir défini le contrat générique d'opportunité.

## 5. P3.5 Perception · Action · Sensorium

### P35-OPEN-01 — contrat sensoriel

Définir les modalités, détection, attention, accès cognitif et active sensing en conservant :

```text
accessible ≠ détecté ≠ sélectionné ≠ cognitivement accessible
```

### P35-OPEN-02 — affordance physique versus opportunité BOL

La frontière conceptuelle est approuvée comme besoin de séparation, mais les contrats opérationnels restent à spécifier :

```text
affordance physique ≠ opportunité comportementale
```

Le moteur/capacité valide le possible; le BOL concerne ce qui mérite d'être considéré comportementalement.

## 6. Follow-ups techniques post-V3c

Ces points sont des candidats à des lots séparés après le rapport V3c. Aucun ne justifie un correctif live.

### TECH-OPEN-01 — `character_moved` / perception

Deux événements de déplacement de Sophie ont été rejetés parce que le payload ne contenait pas le champ `connector` attendu par le contrat perceptif. Vérifier le contrat producteur/consommateur et corriger génériquement seulement si le défaut est confirmé hors échantillon.

### TECH-OPEN-02 — `source_event_seq` sur invalidation

Le chemin `cognition_call_source_not_perceived` ne conserve pas directement `source_event_seq`; l'audit détaillé nécessite actuellement une jointure via l'événement d'orchestrateur. Décider si la traçabilité justifie une correction.

### TECH-OPEN-03 — préfiltrage perceptif

Le garde `source_not_perceived` est sain mais bruyant. Évaluer l'intérêt d'un filtrage plus précoce seulement si l'autorité perceptive existante peut être réutilisée exactement. Ne pas créer une seconde règle de perceptibilité dans l'orchestrateur.

### TECH-OPEN-04 — WO95 idle technique 600 s

Mesurer la fréquence, les interruptions et expirations sur le long run. Ne pas raccourcir le délai pour masquer les `no_action` de Chuu ou un manque d'opportunités.

## 7. Ordre de résolution

Les décisions ci-dessus ne sont pas toutes de même priorité.

Ordre immédiat :

```text
fin V3c
→ audit de fermeture P0
→ décisions P0 nécessaires
→ Conversation State minimal
→ BOL
→ P3.5
```

Les follow-ups techniques indépendants peuvent être qualifiés entre ces étapes seulement s'ils ne brouillent pas la baseline d'un chantier R&D majeur et si leur portée est réellement séparée.

## 8. Règle de décision

Avant de fermer une question :

1. vérifier l'état réel du dépôt;
2. distinguer fait observé, conclusion incertaine, hypothèse de modélisation et choix d'ingénierie;
3. chercher les conséquences sur les invariants et propriétaires persistants;
4. consigner la décision approuvée dans `docs/01_REGISTRE_DECISIONS.md` si elle devient autoritative;
5. seulement ensuite traduire en WO/code selon `docs/GOUVERNANCE_GIT.md`.
