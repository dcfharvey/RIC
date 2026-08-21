# Codex task — état courant RIC

**Mise à jour :** 21 août 2026  
**Statut :** P0 Memory ouvert; V3c interrompu; prochain travail runtime = qualification read-only, aucun correctif dans le même mandat

## Référence produit

La seule référence produit autoritative est `product/current`.

Version/schéma documentaire courant :

- version Python déclarée : `0.2.0a5`;
- migration : `0061_autobiographical_append_only_lifecycle.sql`.

Toujours refaire le préflight Git de `docs/GOUVERNANCE_GIT.md`. Ne jamais utiliser `main`, un ancien worktree ou un runtime historique comme base implicite. Git frais prime sur tout SHA recopié dans une passation.

## Prochaine tâche — qualification V3c read-only

Mandat autoritatif de travail :

`docs/P0_V3C_READONLY_QUALIFICATION_MANDATE.md`

But : produire le rapport de qualification de V3c à partir des artefacts existants, sans aucune écriture ni reprise runtime.

Statuts de preuve obligatoires :

```text
PASS
FAIL
NOT EXERCISED UNDER VALID CONDITIONS
INCONCLUSIVE
```

Verdict de rapport attendu parmi :

```text
P0 EVIDENCE SUFFICIENT FOR CLOSURE AUDIT
P0 ADDITIONAL RUNTIME PROOF REQUIRED
P0 BLOCKED BY INCONCLUSIVE ARTIFACTS
```

Ce verdict technique n'est pas lui-même la décision produit de fermeture P0.

## Runtime V3c — artefact historique interrompu

Snapshot à revérifier, jamais à forcer :

- `RUNTIME_HEAD = 350fbf80353af55994650372b27260eb29dc4dac`
- worktree : `C:\AI\Vivarium social\.rodage-p0-memory-v3c`
- DB : `data\vivarium-p0-memory-v3c.sqlite`
- session : `081861ed-b259-45ae-ad3f-4f61517d2c02`
- moteur : `ActiveSimulationEngine`
- provider : `qwen3-14b`, reasoning off, une instance.

V3c n'est plus une expérience active à poursuivre. DB, journaux et worktree = preuves historiques read-only.

Ne pas rebase/reset/migrate/rename/corriger V3c et ne pas l'utiliser comme base de développement.

## P0 — preuve centrale

```text
expérience sociale accessible
→ admission
→ subjective_trace
→ épisode autobiographique
→ retrieval contextuel ultérieur
→ CognitionContext routé
→ appel provider réel
```

Une lecture directe du service de retrieval/context ne remplace pas la preuve d'un vrai appel provider routé.

La scène Sophie → Erika avec le carnet rouge est un protocole de qualification, pas une permission de fabriquer co-présence, perception, parole ou mémoire. Première tentative documentée : `WAITING FOR VALID ACCESS`.

Si la précondition n'a jamais existé avant interruption : `NOT EXERCISED UNDER VALID CONDITIONS`.

Chercher aussi toute chaîne autobiographique naturelle équivalente réellement produite pendant V3c; elle peut constituer une preuve valable si tous les maillons sont causalement observables.

## État des chantiers suivants

### Conversation State

R&D scientifique + contre-audit Grok clos (`SOLIDE`). Après fermeture P0 : audit architectural Codex sur la base réelle, puis WO borné. Ne pas recommencer la R&D générale.

### Behavioral Opportunity Layer

R&D scientifique + contre-audit Grok clos (`SOLIDE`). Audit architectural Codex après raccordement suffisant de Conversation State et sur un `product/current` frais.

Le cas Chuu reste référence fonctionnelle :

```text
activité physiquement faisable
≠ opportunité comportementale pertinente
```

Ne pas patcher Chuu ni ajouter `sleep/rest` isolément à une whitelist pour contourner BOL.

### P3.5 Perception · Action · Sensorium

R&D + contre-audit Grok + audit architectural Codex clos; clarifications acceptées; verdict `READY FOR WORK ORDER`.

Quand son tour arrive après BOL : préflight frais puis WO; ne pas refaire l'audit sans divergence nouvelle.

## Adaptation LLM / LoRA — travail parallèle hors runtime

Dossier : `docs/92_R_D_LORA_ADAPTATION_LLM.md`.

Pré-enregistrement de benchmark en préparation :

`data/bench/lora_ric_discipline_preregistration_draft.json`

Travaux autorisables tant qu'ils ne modifient pas la baseline P0 :

- finaliser le benchmark avant tout dataset dérivé des erreurs;
- qualifier la stack AMD/WSL2/ROCm/bitsandbytes sur micro-dataset artificiel;
- préparer un dataset séparé du benchmark;
- comparer base vs un seul adaptateur général RIC;
- mesurer violations, sur-abstention, tests métamorphiques et régressions générales.

Aucune intégration runtime avant Conversation State + BOL + P3.5 sauf nouvelle décision produit explicite fondée sur preuve.

Invariant :

```text
état dynamique explicite ≠ poids du modèle
```

Ne pas entraîner comme vérité persistante : faits du monde, souvenirs, relations, consentements, personnalité du casting, état Conversation State, opportunités BOL ou règles physiques.

## Diagnostics V3c à conserver

### `cognition_call_source_not_perceived`

Verdict historique : `HEALTHY BUT NOISY`. Mesurer dans le rapport; aucun churn/backlog/starvation n'est démontré à ce jour.

Follow-ups séparés seulement :

- `character_moved` / champ `connector`;
- `source_event_seq` sur invalidation;
- éventuel préfiltrage plus tôt si la même autorité perceptive est réutilisée sans duplication.

### Chuu `planned_reflection → no_action`

Le grounding est présent; aucun refus moteur systématique n'a été démontré. Les 12 `no_action` observés soutiennent une dette MVP/contrat BOL, pas un correctif personnage.

### WO95 idle

Fallback technique 600 s, provenance `wo95_post_boundary_idle`. Mesurer interruptions/expirations; ne pas changer pour masquer BOL/no_action.

## Ordre de travail

```text
rapport V3c read-only
→ audit/fermeture P0
→ nouveau rodage P0 isolé seulement si preuve nécessaire
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

En parallèle : R&D LoRA hors runtime uniquement.

## Interdictions immédiates

Ne pas :

- modifier V3/V3b/V3c utilisés comme preuves;
- modifier WO95 pour masquer les idles;
- patcher Chuu spécifiquement;
- réintroduire un quota fixe d'appels LLM;
- ouvrir un WO runtime Conversation State/BOL avant fermeture P0;
- réouvrir P3.5 scientifique/architectural sans divergence nouvelle;
- intégrer un LoRA dans le runtime courant;
- encoder dans les poids un état qui doit rester explicite, persistant et auditable;
- présenter un choix d'ingénierie comme une loi scientifique.

## Gouvernance

- ChatGPT : recherche, conception fonctionnelle, cohérence conceptuelle, documentation R&D.
- Grok : contre-audit scientifique adversarial indépendant.
- Codex : architecture réelle, code, migrations, owners persistants, invariants techniques, tests et ordre d'implantation.
- Propriétaire : autorité finale produit/design.

**Verify twice. Commit once.**
