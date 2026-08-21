# Codex task — état courant RIC

**Mise à jour :** 21 août 2026  
**Statut :** P0 Memory ouvert; V3c interrompu; prochaine mission = qualification read-only et audit de fermeture

## 1. Référence produit

La seule référence produit autoritative est `product/current`.

Avant toute opération technique :

1. fetch du remote;
2. résolution exacte de `origin/product/current`;
3. annonce du `PRODUCT_HEAD`;
4. vérification de l'état local/worktrees;
5. aucune utilisation implicite de `main`, d'un ancien WO ou d'un runtime historique comme base de développement.

Suivre `docs/GOUVERNANCE_GIT.md`.

## 2. Artefact V3c — READ ONLY absolu

Le rodage P0 Memory V3c a été interrompu avant audit de fermeture.

Références historiques connues :

- `RUNTIME_HEAD = 350fbf80353af55994650372b27260eb29dc4dac`
- worktree : `C:\AI\Vivarium social\.rodage-p0-memory-v3c`
- DB : `data\vivarium-p0-memory-v3c.sqlite`
- world : `1`
- session : `081861ed-b259-45ae-ad3f-4f61517d2c02`
- moteur : `ActiveSimulationEngine`
- provider de qualification : `qwen3-14b`

Ces chemins sont des **indices historiques à vérifier**, pas une permission d'écriture.

Interdiction : rebase, reset, checkout modifiant le worktree, migration, VACUUM/repair, écriture SQLite, injection de données, reprise du runtime, téléportation, scène fabriquée, réexécution destructive ou utilisation comme worktree de développement.

Si la DB/worktree/journaux ne sont plus présents, le rapport doit le dire et travailler seulement avec les preuves réellement disponibles.

## 3. Mission immédiate — rapport de qualification P0 Memory V3c

**Autorité primaire d'extraction : TECH.**  
**Interprétation des critères : MIXED.**  
**Décision finale de scope/fermeture P0 : PRODUCT + R&D, après preuve technique.**

Cette mission est un **audit**, pas un work order d'implémentation. Aucun correctif ne doit être développé dans le même mandat.

### 3.1 Préflight de preuve

Rapporter :

- `PRODUCT_HEAD` courant;
- existence/absence du worktree V3c;
- HEAD exact du worktree s'il existe;
- existence/absence de la DB et journaux;
- taille, timestamps utiles et mode d'ouverture;
- preuve que toute ouverture SQLite est read-only (`mode=ro` ou équivalent robuste);
- session/world réellement trouvés;
- tout écart avec les références historiques ci-dessus.

Ne pas « réparer » un écart.

### 3.2 Chaîne principale à qualifier

Chercher causalement, dans l'ordre :

```text
expérience sociale accessible
→ admission cognitive
→ subjective_trace
→ épisode autobiographique
→ retrieval contextuel ultérieur
→ CognitionContext réellement routé
→ appel provider réel contenant ce contexte
```

Une lecture directe d'un service de retrieval ou la construction manuelle d'un `CognitionContext` ne qualifie pas la dernière partie de la chaîne. Il faut une preuve d'un vrai appel routé observé dans les artefacts du runtime.

Pour chaque maillon : citer les identifiants/seq/timestamps/rows/log records suffisants pour permettre un contre-audit, sans modifier la DB.

### 3.3 Classification obligatoire

Pour chaque critère :

- `PASS` — preuve positive suffisante;
- `FAIL` — précondition valide exercée et comportement attendu réfuté;
- `NOT EXERCISED UNDER VALID CONDITIONS` — aucune occasion causale valide;
- `INSUFFICIENT EVIDENCE` — artefacts incomplets/ambigus malgré une situation potentiellement pertinente.

Ne jamais convertir absence de preuve en PASS ou FAIL.

### 3.4 Scène mémoire A/B

Protocole historique :

A. Sophie → Erika : `J’ai laissé mon carnet rouge dans la cuisine.`  
B. plus tard : `J’ai déplacé mon carnet rouge dans le salon.`

Les phrases sont des **actes de parole**, jamais des faits canoniques sur un carnet.

La tentative connue A était `WAITING FOR VALID ACCESS` parce que Sophie et Erika n'étaient pas co-présentes. Vérifier si une scène valide a finalement eu lieu avant interruption. Si non : `NOT EXERCISED UNDER VALID CONDITIONS`.

Aucune scène, perception, mémoire ou co-présence ne doit être reconstruite/fabriquée pour produire un résultat.

## 4. Décisions P0 à informer, sans les prendre silencieusement

Le rapport doit fournir les preuves nécessaires pour que R&D/produit tranche :

### P0-OPEN-01 — chaîne épisode → retrieval → provider

Dire si elle est PASS/FAIL/NOT EXERCISED/INSUFFICIENT et si un nouveau rodage est techniquement nécessaire pour obtenir la preuve manquante.

### P0-OPEN-02 — seeding depuis l'attention ordinaire

Mesurer ce qui s'est réellement produit : traces `trace_only`, épisodes, sources d'admission, éventuels patterns. Ne pas inventer une règle de clustering ou déclarer qu'un comportement non observé est requis scientifiquement.

### P0-OPEN-03 — lifecycle/révision naturel

Chercher si une révision/lifecycle a été déclenché naturellement dans la boucle normale. Distinguer « structure disponible » de « mécanisme vivant exercé ».

### P0-OPEN-04 — mémoire disponible dans SCC

Observer seulement les raccordements réellement exercés. Ne pas brancher ou simuler manuellement de nouvelles formes de mémoire dans SCC.

## 5. Diagnostics secondaires à mesurer dans le même audit

Ces diagnostics peuvent être extraits parce qu'ils partagent les mêmes artefacts, mais ils ne doivent pas devenir des correctifs dans ce mandat.

### `cognition_call_source_not_perceived`

Verdict historique : `B — HEALTHY BUT NOISY`.

Mesurer si possible : volume, répartition par source/type/personnage, backlog/fairness, traces de starvation ou absence de celles-ci. Ne pas déclarer bug uniquement sur le volume.

Follow-ups déjà identifiés :

- `character_moved` ↔ champ `connector`;
- conservation de `source_event_seq` sur invalidation;
- préfiltrage perceptif plus tôt seulement s'il réutilise exactement la même autorité.

### Chuu — `planned_reflection → no_action`

Conserver comme référence BOL. Mesurer les séquences observées, contexte/opportunités/motifs accessibles et suites d'idle.

Ne pas :

- patcher Chuu;
- ajouter `sleep`/`rest` à la whitelist;
- modifier `no_action` dans ce mandat.

### WO95 idle technique 600 s

Mesurer fréquence, durée réelle, interruptions et expirations observables. Ne pas modifier le délai.

### Trace + épisode

Mesurer la double représentation éventuelle et son usage réel. Ne pas la « dédupliquer » avant d'avoir montré qu'elle constitue un défaut fonctionnel.

## 6. Forme du rapport attendu

Produire un rapport autonome avec :

1. préflight et sources de preuve;
2. tableau des critères P0 avec classification;
3. chaîne causale principale avec identifiants/timestamps;
4. scène A/B;
5. attention seeding;
6. lifecycle/révision;
7. SCC/mémoire;
8. diagnostics secondaires;
9. limites de l'audit;
10. décisions qui exigent `TECH`, `SCI`, `PRODUCT` ou `MIXED`;
11. verdict parmi :
   - `P0 CLOSURE EVIDENCE SUFFICIENT`;
   - `P0 CLOSURE BLOCKED — NEW QUALIFICATION RUN REQUIRED`;
   - `P0 CLOSURE BLOCKED — TECHNICAL DEFECT DEMONSTRATED`;
   - `P0 CLOSURE BLOCKED — PRODUCT/R&D SCOPE DECISION REQUIRED`;
   - combinaison explicite si plusieurs blocages distincts existent.

Si un nouveau rodage est requis, proposer seulement son **contrat de qualification minimal** et ses préconditions; ne pas le lancer dans ce mandat sauf nouvelle autorisation explicite.

## 7. Chantiers suivants — maturité vérifiée

### Conversation State

- R&D scientifique : faite;
- contre-audit Grok : clos — `SOLIDE`;
- prochaine porte après P0 : **audit architectural Codex**, puis WO borné.

### Behavioral Opportunity Layer

- R&D scientifique : faite;
- contre-audit Grok : clos — `SOLIDE`;
- prochaine porte après Conversation State : **audit architectural Codex**, puis WO borné.

### P3.5 Perception · Action · Sensorium

- R&D : consolidée;
- contre-audit Grok : clos;
- audit architectural Codex : clos;
- verdict : **SOLIDE AVEC RÉSERVES — READY FOR WORK ORDER**;
- attend son tour après BOL et un préflight frais de `product/current`.

## 8. Piste R&D PEFT/LoRA

Dossier : `docs/92_R_D_LORA_ADAPTATION_LLM.md`.

Travaux hors runtime autorisables en parallèle :

- benchmark gelé avant dataset;
- baseline modèle vanilla;
- dataset train/validation distinct du test final;
- smoke QLoRA hors DB RIC persistante;
- mesures matériel/VRAM/RAM/stabilité;
- comparaison base vs adaptateur;
- tests OOD/régression.

Un seul adaptateur RIC général au premier essai. Ne pas encoder dans les poids : faits du monde, mémoire individuelle, relations/consentements actuels, Conversation State, opportunités BOL, règles physiques ou scripts de personnages.

Aucune intégration runtime avant sa porte après P3.5 sans nouvelle décision produit explicite.

**Autorité pipeline/hotswap/versioning : TECH.**  
**Frontière de ce qui est apprenable : MIXED.**  
**Adoption finale : PRODUCT.**

## 9. Ordre de travail

```text
rapport V3c read-only
→ audit de fermeture P0
→ nouveau rodage P0 isolé seulement si nécessaire
→ audit architectural + WO Conversation State
→ audit architectural + WO BOL
→ WO P3.5
→ porte d'intégration LoRA
→ affect
→ cognition animale
→ physiologie plus large
```

La R&D LoRA hors runtime peut progresser en parallèle; un seul chantier R&D **runtime majeur** à la fois.

## 10. Interdictions immédiates

Ne pas :

- modifier les DB/runtime V3/V3b/V3c;
- modifier WO95 pour masquer les idles;
- patcher Chuu spécifiquement;
- ajouter `sleep/rest` comme correctif isolé;
- réintroduire un quota cognitif fixe;
- ouvrir un WO runtime Conversation State/BOL avant fermeture P0;
- intégrer un LoRA dans le runtime courant;
- encoder dans les poids LLM un état qui doit rester explicite/auditable;
- présenter une décision d'ingénierie comme une loi scientifique.

## 11. Gouvernance

- **ChatGPT** : science, conception fonctionnelle, cohérence conceptuelle et documentation R&D.
- **Grok** : contre-audit scientifique adversarial.
- **Codex** : architecture réelle, code, migrations, owners techniques, tests et ordre d'implantation.
- **Propriétaire** : décision finale produit/design.

**Verify twice. Commit once.**
