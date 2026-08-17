# Passation courante — RIC

**Mise à jour :** 16 août 2026  
**Projet :** RIC — Reality · Interaction · Cognition  
**Statut :** point d'entrée opérationnel courant

> Commencer ici pour reprendre le travail. Cette passation décrit l'état opérationnel et les priorités immédiates. Elle ne remplace ni le noyau normatif de `docs/00_DOSSIER_MAITRE_IA.md`, ni le registre autoritatif `docs/01_REGISTRE_DECISIONS.md`, ni `docs/GOUVERNANCE_GIT.md`.

## 1. Référence produit

La branche distante `product/current` est la seule référence autoritative du produit courant.

Photographie vérifiée au moment de cette passation :

- `PRODUCT_HEAD = 350fbf80353af55994650372b27260eb29dc4dac`
- commit : `Reject ambiguous operational grounding effects`
- distribution technique : `vivarium-social`
- import Python : `vivarium`
- version déclarée : `0.2.0a5`
- dernière migration : `0061_autobiographical_append_only_lifecycle.sql`
- dernière qualification complète connue du lot Operational Cognition Grounding : `1033 passed, 1 skipped`

Ne pas utiliser `main`, un ancien worktree, une branche de WO ou un runtime historique comme base implicite. Vérifier à nouveau `origin/product/current` avant toute écriture.

## 2. Runtime V3c actif

Le rodage P0 Memory V3c tourne sur une base isolée :

- `RUNTIME_HEAD = 350fbf80353af55994650372b27260eb29dc4dac`
- worktree : `C:\AI\Vivarium social\.rodage-p0-memory-v3c`
- DB : `data\vivarium-p0-memory-v3c.sqlite`
- world : `1`
- session : `081861ed-b259-45ae-ad3f-4f61517d2c02`
- moteur : `ActiveSimulationEngine`
- physiologie : active
- provider de qualification : Qwen3-14B, reasoning off, une instance

Le runtime est une expérience en cours. Il ne doit pas être modifié, rebasé, reset, migré ou utilisé pour développer.

Les anciennes bases et worktrees V3/V3b restent des artefacts historiques à conserver en lecture seule jusqu'à fermeture du rapport correspondant.

## 3. Architecture conceptuelle

Les noms suivants sont conceptuels et ne prescrivent pas le découpage du code :

- **Reality Engine** : ce qui est objectivement vrai, possible et causal;
- **Interaction Engine** : ce qui rend agents et réalité mutuellement accessibles et structure leurs interactions;
- **Cognitive Engine** : ce que chaque agent perçoit, interprète, mémorise, priorise et décide subjectivement.

Contrat de runtime recherché :

```text
réalité canonique
→ sous-ensemble perceptible
→ état subjectif / mémoire / préférences / besoins
→ intention / décision proposée
→ validation moteur
→ conséquence canonique
→ nouvelles perceptions
```

## 4. Invariants qui priment sur la commodité

```text
réalité/canon ≠ perception ≠ croyance
parole ≠ fait
relation ≠ permission ≠ consentement
LLM propose, moteur valide
aucun composant cognitif n'écrit directement la réalité canonique
provenance d'audit ≠ source subjectivement mémorisée
un seul propriétaire persistant par état
pas d'omniscience implicite des agents
mécanisme générique > script propre à un personnage
```

## 5. Travaux récents fermés

### File cognitive

Le défaut de saturation observé pendant V3 a été corrigé et intégré avant V3c : identité logique stable, drainage/re-offer, fairness et état `provider_dispatch_pending` ont été revus. Ne pas remettre l'ancien bug dans la liste des défauts ouverts sans nouvelle preuve.

### P0 Memory — fondations déjà intégrées

Les tranches suivantes sont présentes :

- fondation autobiographique : épisode, supports, événements d'audit, retrieval contextuel borné;
- admission d'encodage append-only;
- seeding social des épisodes;
- lifecycle autobiographique append-only avec révisions structurelles et représentation courante par feuille;
- séparation dans `CognitionContext` entre traces récentes et `autobiographical_memories`.

Ces fondations ne signifient pas que P0 est fermé ni que l'oubli/reconsolidation complet est implémenté.

### Operational Cognition Grounding — fermé

Le contexte cognitif reçoit maintenant génériquement :

- morphologie descriptive de l'agent;
- capacités owner-backed actives pertinentes;
- signaux de contexte owner-backed pertinents.

La morphologie descriptive ne devient pas une capacité causale. Les effets opérationnels ambigus portant la même clé sont refusés plutôt qu'agrégés arbitrairement.

La projection d'activités utilise en outre une prévisualisation read-only de la faisabilité physique connue avant de présenter une option au LLM; l'exécution finale continue de revalider l'état réel.

## 6. P0 Memory — état actuel

**Statut : OPEN.**

V3c a déjà observé :

```text
contenu accessible
→ décision d'admission
→ parfois subjective_trace
→ trace_only possible
```

La preuve runtime principale encore recherchée est :

```text
expérience sociale accessible
→ admission
→ subjective_trace
→ épisode autobiographique
→ retrieval contextuel ultérieur
→ CognitionContext routé
→ appel provider réel
```

Une lecture directe de `CognitionContextService` ou du service de retrieval ne suffit pas à qualifier cette dernière chaîne : il faut un vrai appel routé et son contexte observé.

### Scène mémoire A/B

Protocole de qualification :

A. Sophie dit à Erika : `J’ai laissé mon carnet rouge dans la cuisine.`  
B. plus tard : `J’ai déplacé mon carnet rouge dans le salon.`

Les deux phrases sont des paroles, jamais des faits canoniques concernant un carnet.

La première tentative V3c de scène A a donné :

`MEMORY SCENE A: WAITING FOR VALID ACCESS`

Sophie et Erika n'étaient pas co-présentes; aucune scène, téléportation, perception, parole ou mémoire n'a été fabriquée. Si V3c se termine sans précondition valide, le chemin doit être classé `NOT EXERCISED UNDER VALID CONDITIONS`, pas « failed ».

## 7. Diagnostics V3c importants

### `cognition_call_source_not_perceived`

Verdict : **B — HEALTHY BUT NOISY**.

Le routeur revalide qu'un événement canonique appartient réellement à la vue perceptive de la résidente avant admission/provider. Le volume élevé observé vient surtout de l'orchestrateur qui tente beaucoup d'événements pour chaque résidente avant ce filtre.

Aucun churn logique, backlog durable, queue full ou starvation causée par ce mécanisme n'a été démontré.

Follow-ups possibles, séparés de V3c :

- vérifier l'alignement `character_moved` ↔ champ `connector`;
- conserver `source_event_seq` même sur les invalidations;
- envisager un préfiltrage perceptif plus tôt seulement si la même autorité perceptive peut être réutilisée sans dupliquer la règle.

### Chuu — `planned_reflection → no_action`

Une séquence de 12 réflexions a donné exactement `no_action` alors que :

- grounding opérationnel présent;
- provider sain;
- aucune activité refusée;
- même catalogue de 6 types/15 couples activité-lieu;
- contexte presque figé;
- motifs dominants `sleep` / `rest`;
- préférence sociale de Chuu sans cible sociale accessible.

Audit du contrat :

- `MotiveCandidate.possible_actions` est explicatif et exposé au provider;
- il ne construit pas `activity_options`;
- `sleep` et `rest` sont de vraies activités moteur;
- la whitelist de `planned_reflection` reste celle des six loisirs alpha;
- `no_action` collapse plusieurs raisons possibles sans justification obligatoire.

Verdict : dette MVP + contrat ambigu + besoin BOL; aucun bug de raccordement pré-BOL démontré.

**Ne pas patcher Chuu ni ajouter isolément `sleep`/`rest` à la whitelist.**

Le besoin fonctionnel qui ressort est :

> Produire, à partir des motifs, préférences, objectifs, contexte, capacités et environnement accessibles, un ensemble borné d'opportunités comportementales génériques, distinctes des affordances physiques, que le moteur peut ensuite valider et que la cognition peut sélectionner.

## 8. WO95 — idle technique

Le fallback technique post-frontière reste fixé à 600 secondes et porte la provenance `wo95_post_boundary_idle`.

V3c a montré qu'un tel idle peut être interrompu rapidement lorsqu'une nouvelle activité prend le relais, mais Chuu a aussi montré des chaînes d'idles expirant normalement.

Ne pas réduire ce délai pendant V3c pour masquer un symptôme. Le mesurer et l'interpréter au rapport final.

## 9. Ce qui n'est pas à corriger pendant V3c

- Erika/gaming et autres signatures comportementales : observation, pas patch prompt/personnage;
- répétition/conversation : relève du futur Conversation State, pas d'un hack de prompt live;
- Chuu/no_action : cas de référence BOL, pas règle spéciale Chuu;
- double représentation trace + épisode : mesurer avant de corriger;
- absence d'épisode autobiographique : qualifier le chemin sous conditions valides avant toute modification;
- bruit `source_not_perceived` : diagnostic connu, pas urgence runtime.

## 10. Ordre immédiat R&D / développement

```text
V3c long run
→ scène mémoire A/B si causalement possible
→ preuve episode → retrieval → contexte routé si elle survient
→ audit de fermeture P0
→ Conversation State minimal
→ Behavioral Opportunity Layer
→ P3.5 Perception · Action · Sensorium
→ affect au-delà du SCC
→ cognition animale au-delà de Patoune
→ physiologie plus large
```

Un seul chantier R&D runtime majeur à la fois.

Conversation State ne doit pas démarrer avant l'audit de fermeture P0. BOL vient après Conversation State minimal. P3.5 ne doit pas être confondu avec BOL :

```text
affordance physique ≠ opportunité comportementale
```

## 11. Limites P0 à décider à la fermeture

Points à distinguer entre « requis pour fermer P0 » et « volontairement différé » :

- seeding d'épisode depuis l'attention ordinaire;
- déclencheur naturel de lifecycle/révision;
- activation de candidats mémoire dans SCC;
- oubli, consolidation, familiarité, recollection et reconstruction avancée.

Ne pas présenter une structure de révision append-only comme une preuve que l'oubli ou la reconsolidation psychologique sont déjà simulés.

## 12. Méthode R&D

Pour tout modèle comportemental, cognitif, social ou physiologique :

1. établir les résultats empiriques/techniques pertinents;
2. séparer les conclusions raisonnables mais incertaines;
3. expliciter les hypothèses de modélisation;
4. expliciter les choix de design/ingénierie;
5. chercher théories concurrentes, limites et falsifications;
6. ne jamais transformer un choix d'ingénierie en « loi scientifique ».

## 13. Gouvernance

- **ChatGPT** : recherche scientifique/technique, conception fonctionnelle, cohérence conceptuelle, documentation R&D.
- **Grok** : contre-audit scientifique adversarial indépendant.
- **Codex** : architecture réelle, code, migrations, propriétaires persistants, invariants techniques, tests et ordre d'implantation.
- **Propriétaire** : autorité finale produit/design.

Codex ne doit pas exécuter littéralement une architecture proposée par ChatGPT si le dépôt réel impose mieux; la divergence doit être expliquée et les contrats fonctionnels conservés.

## 14. Documents de reprise

Ordre recommandé :

1. `docs/99_PASSATION_COURANTE.md` — état opérationnel;
2. `docs/00_DOSSIER_MAITRE_IA.md` — noyau normatif stable;
3. `docs/01_REGISTRE_DECISIONS.md` — décisions autoritatives;
4. `docs/03_DECISIONS_OUVERTES.md` — décisions encore ouvertes;
5. `docs/15_ROADMAP_ACTIVE.md` — ordre de travail;
6. `docs/GOUVERNANCE_GIT.md` — référence produit et cycle Git;
7. docs de lot/R&D cités au besoin pour la provenance.

Les documents historiques et `sources/` restent utiles pour comprendre l'origine des décisions, mais ne doivent pas contredire silencieusement le produit courant ou le registre autoritatif.

**Flexible creativity. Rigorous execution.**  
**Verify twice. Commit once.**
