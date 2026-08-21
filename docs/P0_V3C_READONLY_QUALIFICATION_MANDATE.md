# Mandat — Qualification read-only du rodage P0 Memory V3c

**Date :** 21 août 2026  
**Statut :** prêt à exécuter dès que les artefacts locaux V3c sont accessibles  
**Nature :** audit/qualification uniquement; aucun correctif, migration ou reprise runtime dans ce mandat.

## 0. Autorité

- **TECH** : identité des artefacts, extraction SQL/logs, chronologie, preuves provider, métriques.
- **MIXED** : interprétation des chaînes causales et classification PASS/FAIL/NOT EXERCISED/INCONCLUSIVE.
- **SCI** : seulement si l'audit prétend tirer une conclusion sur mémoire/cognition au-delà du contrat logiciel.
- **PRODUCT** : décision finale sur ce qui est exigé pour fermer P0 versus volontairement différé.

Codex conserve l'autorité sur la méthode d'inspection du dépôt et des artefacts réels. Ce document fixe le contrat de preuve, pas une architecture.

## 1. Artefact historique de référence

Snapshot documenté :

- `RUNTIME_HEAD = 350fbf80353af55994650372b27260eb29dc4dac`
- worktree : `C:\AI\Vivarium social\.rodage-p0-memory-v3c`
- DB : `data\vivarium-p0-memory-v3c.sqlite`
- world : `1`
- session : `081861ed-b259-45ae-ad3f-4f61517d2c02`
- moteur : `ActiveSimulationEngine`
- provider : `qwen3-14b`, reasoning off, une instance.

Ces valeurs doivent être **revérifiées** sur les artefacts; elles ne doivent pas être réécrites ou forcées pour correspondre à la documentation.

V3c a été interrompu avant audit de fermeture. Son état global est :

```text
ABORTED / INTERRUPTED
≠ FAILED
≠ PASSED
```

## 2. Interdictions absolues

Ne pas :

- démarrer/reprendre le runtime V3c;
- migrer la DB;
- corriger une ligne de données;
- téléporter ou repositionner un personnage;
- injecter une parole, perception, mémoire ou épisode;
- appeler un service de retrieval directement pour fabriquer une preuve runtime;
- rebaser/reset le worktree;
- utiliser V3c comme base de développement;
- lancer un correctif dans le même mandat;
- convertir une absence de preuve en PASS.

Ouvrir SQLite en `mode=ro` ou avec un mécanisme techniquement équivalent garantissant l'absence d'écriture. Si une copie d'analyse est nécessaire, conserver l'original intact et consigner hash/source de la copie.

## 3. Classification de chaque preuve

Chaque exigence reçoit exactement un statut principal :

- `PASS` : preuve positive causalement suffisante observée;
- `FAIL` : comportement exercé sous préconditions valides mais contrat violé;
- `NOT EXERCISED UNDER VALID CONDITIONS` : préconditions nécessaires jamais réunies avant interruption;
- `INCONCLUSIVE` : données insuffisantes/ambiguës pour distinguer les catégories précédentes.

Ne pas utiliser « probablement PASS » comme substitut.

## 4. Préflight d'intégrité

Avant analyse fonctionnelle :

1. relever le chemin réel de la DB et du worktree;
2. vérifier que les artefacts existent;
3. relever taille, timestamps et hash de la DB si raisonnablement possible;
4. confirmer le `RUNTIME_HEAD` du worktree sans checkout/reset;
5. identifier les journaux/audits associés;
6. vérifier l'identité `world/session` dans les données;
7. consigner toute divergence avec la passation;
8. prouver que l'inspection est read-only.

Si l'identité de session ne peut pas être établie, classer les blocs concernés `INCONCLUSIVE` plutôt que mélanger plusieurs runtimes.

## 5. Chaîne P0 principale à qualifier

```text
expérience sociale réellement accessible
→ admission cognitive/encodage
→ subjective_trace
→ épisode autobiographique
→ retrieval contextuel ultérieur
→ inclusion dans CognitionContext routé
→ appel provider réel
```

Important :

- l'exposition du souvenir au provider qualifie l'exposition;
- elle ne prouve pas que le souvenir a causé la sortie du modèle;
- lire directement `CognitionContextService` ou le retrieval hors d'un vrai appel routé ne satisfait pas la dernière étape.

Pour chaque maillon, documenter : identifiant/séquence, timestamp canonique, personnage, provenance, source de preuve, lien causal avec le maillon précédent et statut.

## 6. Scène mémoire A/B

A. Sophie dit à Erika : `J’ai laissé mon carnet rouge dans la cuisine.`  
B. plus tard : `J’ai déplacé mon carnet rouge dans le salon.`

Ces énoncés sont des **paroles**, jamais des faits canoniques sur un carnet.

Questions :

1. Sophie et Erika ont-elles été dans une configuration d'accès perceptif valide pour A?
2. A a-t-elle réellement été prononcée sous ces conditions?
3. Erika l'a-t-elle réellement perçue/admis selon le runtime?
4. Une trace puis un épisode ont-ils été produits?
5. B a-t-elle ultérieurement eu lieu sous conditions valides?
6. Un retrieval ultérieur a-t-il exposé l'épisode A ou une révision pertinente au provider?
7. À aucun moment le moteur n'a-t-il transformé le contenu du discours en vérité canonique sur le carnet?

Observation documentée : première tentative A = `WAITING FOR VALID ACCESS` parce que Sophie et Erika n'étaient pas co-présentes.

Si aucune occasion valide n'est survenue avant interruption :

```text
MEMORY SCENE A/B = NOT EXERCISED UNDER VALID CONDITIONS
```

## 7. Seeding autobiographique hors scène contrôlée

Chercher aussi les épisodes réellement produits naturellement pendant V3c.

Pour chaque épisode : événements support, origine sociale/ordinaire, propriétaire, relation avec `subjective_trace`, admission précédente, révisions/lifecycle, retrieval ultérieur et exposition provider éventuelle.

Une chaîne naturellement équivalente peut qualifier P0 même si la scène A/B n'a pas été exercée, mais seulement si tous les maillons requis sont causalement observables.

## 8. Double représentation trace + épisode

Mesurer sans corriger :

- fréquence `trace_only`;
- fréquence trace + épisode;
- cas où les deux apparaissent simultanément dans le contexte;
- duplication textuelle/tokens éventuelle;
- effet observable sur retrieval/context building.

Verdict attendu : observation de coût/duplication, pas décision d'architecture.

## 9. Lifecycle / révision

Vérifier si V3c a réellement exercé : création de révision, changement de feuille/current representation, déclencheur naturel observable et conservation de la provenance.

Ne pas appeler cela « reconsolidation psychologique » ou « oubli » sans mécanisme correspondant.

## 10. SCC ↔ mémoire

Qualifier seulement ce qui est réellement branché : quelles formes de mémoire ont été candidates au SCC, lesquelles ont été récupérées/exposées, et s'il existe des événements où une mémoire aurait été pertinente mais absente.

Distinguer absence de feature prévue, absence d'occasion et défaut d'exécution.

## 11. `cognition_call_source_not_perceived`

Verdict historique à vérifier : `HEALTHY BUT NOISY`.

Mesurer : total d'invalidations, répartition personnage/type, évolution temporelle, backlog/queue depth disponible, preuve/absence de starvation, présence de `source_event_seq`, et échantillon `character_moved`/`connector`.

Tout correctif éventuel = follow-up séparé.

## 12. WO95 post-boundary idle

Mesurer : nombre de `wo95_post_boundary_idle`, durée avant interruption/expiration, taux interrompu vs expiré, distribution par personnage, séquences `idle → planned_reflection → action/no_action`, cas répétés chez Chuu et relation avec les frontières d'activité.

Ne pas modifier les 600 secondes.

## 13. Chuu `planned_reflection → no_action`

Reconstituer à partir des traces historiques : nombre de réflexions, `activity_options`, motifs/préférences/contexte, sorties provider, refus moteur éventuels, disponibilité de cibles sociales et stabilité du contexte.

Question : le diagnostic « dette MVP / besoin BOL, pas panne de grounding démontrée » reste-t-il soutenu?

Aucune règle spéciale Chuu ni ajout isolé de `sleep/rest`.

## 14. Rapport de sortie

Le rapport final contient :

### A. Identité

HEAD, DB, session, hashes/paths, mode read-only, sources inspectées.

### B. Résumé exécutif

Un verdict parmi :

- `P0 EVIDENCE SUFFICIENT FOR CLOSURE AUDIT`;
- `P0 ADDITIONAL RUNTIME PROOF REQUIRED`;
- `P0 BLOCKED BY INCONCLUSIVE ARTIFACTS`.

Ce verdict n'est pas lui-même la décision produit de fermeture.

### C. Matrice de preuve

Chaque critère avec `PASS / FAIL / NOT EXERCISED / INCONCLUSIVE`.

### D. Chronologie causale

Événements et séquences déterminants, sans cherry-picking.

### E. Diagnostics secondaires

source_not_perceived, idles, Chuu, duplication trace/episode, lifecycle, SCC.

### F. Décisions P0 à soumettre

Pour chaque point : autorité dominante `TECH / SCI / PRODUCT / MIXED` et recommandation séparée des faits.

### G. Nouveau rodage éventuel

Seulement si une preuve réellement requise manque : décrire **ce qui doit être exercé**, pas comment modifier le runtime pour forcer le résultat.

## 15. Règle de fermeture

```text
preuves V3c
→ audit de fermeture P0
→ décision des exigences réellement nécessaires
→ si nécessaire, nouveau rodage isolé depuis product/current frais
```

Ne jamais :

```text
V3c incomplet
→ patch V3c
→ fabriquer la scène manquante
→ PASS rétroactif
```

**Verify twice. Commit once.**
