# Roadmap active — RIC

**Version :** 2.2  
**Mise à jour :** 21 août 2026  
**Statut :** trajectoire opérationnelle courante

Cette roadmap fixe l'ordre des grands chantiers. Elle ne remplace ni la passation opérationnelle (`docs/99_PASSATION_COURANTE.md`), ni le noyau normatif (`docs/00_DOSSIER_MAITRE_IA.md`), ni le registre de décisions (`docs/01_REGISTRE_DECISIONS.md`).

## Principe de conduite

> **Flexible creativity. Rigorous execution.**  
> **Verify twice. Commit once.**

Une idée peut rester ouverte tant qu'elle est exploratoire. Dès qu'elle devient spécification, architecture, code ou canon, elle doit être testable, traçable et falsifiable.

Pour tout système comportemental, cognitif, social ou physiologique : littérature scientifique/technique d'abord, traduction opérationnelle ensuite. Séparer explicitement résultats empiriques, conclusions incertaines, hypothèses de modélisation et choix d'ingénierie.

Un seul chantier R&D runtime majeur à la fois. Des travaux préparatoires expérimentaux peuvent avancer en parallèle s'ils ne modifient ni la baseline runtime ni les contrats encore en qualification.

## Référence produit

- version déclarée : `0.2.0a5`;
- dernière migration : `0061_autobiographical_append_only_lifecycle.sql`;
- Operational Cognition Grounding : fermé;
- P0 Memory : ouvert;
- V3c : interrompu avant audit de fermeture; artefact historique read-only.

Toujours revérifier `origin/product/current` avant tout WO. Git prime sur tout SHA documentaire historique.

## Vue d'ensemble

```text
P0 Memory — fermeture
→ Conversation State — R&D/Grok clos; audit Codex à faire
→ BOL — R&D/Grok clos; audit Codex à faire sur base fraîche
→ P3.5 — R&D/Grok/Codex clos; READY FOR WORK ORDER quand son tour arrive
→ porte d'intégration LoRA
→ Affect
→ cognition animale
→ physiologie plus large
```

En parallèle sans toucher au runtime : benchmark, dataset et faisabilité technique LoRA/QLoRA.

---

## Porte actuelle — P0 Memory / V3c interrompu

Fondations intégrées :

- admission sélective d'encodage;
- `subjective_trace` append-only;
- épisodes autobiographiques avec supports;
- retrieval contextuel borné;
- seeding social d'épisode;
- lifecycle append-only et révisions structurelles;
- exposition séparée des traces récentes et `autobiographical_memories` au contexte cognitif.

V3c a été interrompu avant fermeture formelle. Cette interruption n'est ni PASS ni FAIL.

### Prochaine action

Le contrat détaillé de qualification est dans `docs/P0_V3C_READONLY_QUALIFICATION_MANDATE.md`.

1. rapport V3c strictement read-only;
2. classification `PASS / FAIL / NOT EXERCISED UNDER VALID CONDITIONS / INCONCLUSIVE`;
3. audit de fermeture P0 si les preuves suffisent;
4. nouveau rodage isolé seulement si une preuve réellement nécessaire manque;
5. jamais de reprise/correction rétroactive de V3c.

### Preuve runtime recherchée

```text
expérience sociale accessible
→ admission
→ subjective_trace
→ épisode autobiographique
→ retrieval contextuel
→ CognitionContext routé
→ provider réel
```

Cette preuve qualifie l'exposition du souvenir au provider, pas son influence causale sur la réponse.

### Porte de sortie P0

Distinguer explicitement ce qui est qualifié, ce qui manque réellement pour P0 et ce qui est volontairement différé.

Décisions principales :

- seeding depuis l'attention ordinaire;
- trigger naturel de lifecycle/révision;
- candidats mémoire dans SCC;
- oubli/consolidation/familiarité/recollection/reconstruction avancés.

Une structure append-only n'est pas une preuve d'oubli ou de reconsolidation psychologique.

---

## Étape 1 — Conversation State minimal

**Maturité vérifiée : peer review scientifique Grok clos — `SOLIDE`; dossier fonctionnel existant.**

La prochaine porte après P0 est donc l'**audit architectural Codex**, pas une nouvelle R&D générale.

Dossier Drive : `Vivarium_social_R&D_Conversation_State_minimal.md`.

Le dossier couvre déjà notamment :

- co-présence ≠ participation ≠ adressage;
- floor conversationnel;
- séquences ouvertes, expansions et side sequences;
- repair;
- progressivité;
- extended tellings / principal contributor;
- interactional projects;
- topic state;
- lapse/silence sans fermeture automatique;
- clôture coordonnée;
- compatibilité multiparty future.

Travail restant : audit Codex sur l'architecture alors courante → WO borné → qualification runtime de continuité/répétition/reprise/clôture.

Frontière : Conversation State structure l'interaction; il ne devient ni mémoire subjective, ni BOL, ni SCC.

Ne pas corriger les répétitions par accumulation de prompt ad hoc avant ce chantier.

---

## Étape 2 — Behavioral Opportunity Layer (BOL)

**Maturité vérifiée : peer review scientifique Grok clos — `SOLIDE`; dossier prêt pour audit architectural Codex.**

L'audit doit toutefois être fait sur une base fraîche après raccordement suffisant de Conversation State, dont BOL dépend fonctionnellement.

Dossier Drive : `RIC_R&D_Behavioral_Opportunity_Layer_minimal.md`.

Le diagnostic Chuu soutient le besoin : faisabilité moteur ≠ opportunité comportementale pertinente.

```text
motifs / préférences / buts / contexte
        ↓
   [raccord générique alpha incomplet]
        ↓
whitelist d'activités faisables
        ↓
choix LLM ou no_action
```

Contrat cible :

> À partir des motifs, préférences, objectifs, contexte, capacités et environnement accessibles, produire un petit ensemble d'opportunités comportementales génériques et pertinentes, distinctes des affordances physiques, que la cognition peut considérer et que le moteur valide finalement.

R&D déjà consolidée :

- opportunité ≠ intention ≠ action;
- possibilité canonique ≠ opportunité subjective;
- continuer/interrompre/reprendre/report/attendre comme possibilités explicites;
- sources multiples : besoins, buts, habitudes, engagements, mémoire prospective, Conversation State, environnement;
- coût d'interruption/reprise;
- raisons structurées `for/against` sans score psychologique universel;
- suffisance plutôt que maximisation obligatoire;
- réévaluation événementielle plutôt qu'un tick mental permanent.

Contraintes : aucune règle Chuu/Erika, aucune table universelle `motif → activité`, aucune omniscience canonique, cognition propose/moteur valide.

Points TECH à auditer : rôle de `MotiveCandidate.possible_actions`, sémantique de `no_action`, relation préférences↔opportunités, activité moteur↔opportunité cognitive, bornage/présentation sans ranking caché.

Ne pas patcher `sleep/rest` isolément dans la whitelist.

---

## Étape 3 — P3.5 Perception · Action · Sensorium

**Maturité vérifiée : R&D scientifique + contre-audit Grok + audit architectural Codex clos; clarifications acceptées; verdict final `READY FOR WORK ORDER`.**

P3.5 attend son tour après BOL. À ce moment : préflight frais de `origin/product/current`, puis WO à partir du dossier déjà audité. Ne pas refaire l'audit sans divergence nouvelle.

Principe :

```text
signal accessible
≠ détection
≠ sélection attentionnelle
≠ accès subjectif exploitable par la cognition
```

Noyau V1 consolidé :

1. accessibilité sensorielle;
2. qualité/incertitude minimale;
3. affordances relationnelles corps × environnement et effecteurs;
4. contrats compatibles avec composition multi-processus, sans imposer la concurrence persistante dès la première tranche;
5. feedback basique avec correction automatique ≠ réévaluation cognitive.

Frontière :

```text
affordance physique = relation corps ↔ monde permettant une action
opportunité BOL = possibilité comportementale actuellement pertinente
```

Reportés jusqu'à preuve d'utilité : fusion multisensorielle sophistiquée, binding temporel fin, quantification universelle de double tâche, attention conjointe fine, prédiction sensorimotrice détaillée et segmentation subjective des événements.

---

## Programme transverse — adaptation LLM / PEFT-LoRA

Dossier autoritatif courant : `docs/92_R_D_LORA_ADAPTATION_LLM.md`.

**Statut : R&D technique/fonctionnelle ouverte; prototype hors runtime autorisable; utilité produit non démontrée.**

But : tester si un seul adaptateur général RIC améliore des comportements stables :

- canon/perception/croyance;
- parole/fait;
- provenance/incertitude;
- abstention appropriée;
- schémas de sortie;
- hidden-state overclaim;
- instruction hostile présente comme donnée du monde.

Ce qui reste hors des poids : faits du monde, souvenirs/beliefs/relations actuels, consentements, personnalité du casting, Conversation State courant, opportunités BOL courantes, règles physiques/affordances et scripts propres à un personnage.

Invariant :

```text
état dynamique explicite ≠ poids du modèle
```

### Méthode

```text
benchmark de falsification gelé avant le dataset
→ baseline vanilla
→ dataset séparé
→ smoke-test QLoRA hors runtime
→ base vs base+LoRA
→ tests hors distribution / métamorphiques / régression
→ décision d'intégration ou rejet
```

Le premier essai reste **un seul adaptateur général**. Aucun LoRA conversation/mémoire/personnage séparé sans déficience distincte démontrée.

### Matériel

La RX 7800 XT (`gfx1101`) est une cible plausible. Le chemin prioritaire à qualifier est WSL2 + ROCm, où AMD liste explicitement la carte; le backend 4-bit/bitsandbytes doit être testé sur le poste réel avant toute dépendance. Ne pas présumer Windows natif équivalent.

### Séquençage

Benchmark/dataset/smoke-test peuvent avancer maintenant sans contaminer P0. L'intégration runtime attend normalement Conversation State + BOL + P3.5.

---

## Étape 4 — porte d'intégration LoRA

Après P3.5 :

- réévaluer le benchmark sur les contrats stabilisés;
- entraîner/réentraîner l'adaptateur candidat;
- comparer modèle de base vs adapté;
- vérifier conversation, social, décision, mémoire, schémas de sortie et hors domaine;
- vérifier qu'une baisse de violations ne vient pas d'une sur-abstention;
- exiger provenance `base_model + adapter_version` et rollback vers le modèle de base;
- audit Codex du chargement/lifecycle/observabilité réels;
- décision produit explicite d'adoption ou rejet.

Aucun gain qualitatif subjectif ne suffit.

---

## Étape 5 — Affect au-delà du SCC

- dynamique affective générale;
- expression;
- régulation;
- interaction avec mémoire, buts, attention et relations;
- état subjectif ≠ vérité canonique.

Fondement scientifique et falsification obligatoires; pas de labels émotionnels décoratifs sans mécanisme.

## Étape 6 — cognition animale au-delà de Patoune CAT-0

Développer une agence non sapiente plus riche sans projeter automatiquement le modèle humain. Mécanismes génériques et fondés sur la littérature pertinente.

Ne pas présumer qu'un LoRA RIC humain/sapient est applicable à la cognition animale.

## Étape 7 — physiologie plus large

Étendre au-delà de veille-sommeil/capacité physique seulement lorsque les interfaces précédentes existent. Chaque variable doit avoir propriétaire persistant, causalité utile et traduction comportementale justifiable.

---

## Signaux V3c à conserver

### Chuu / idles

`idle WO95 → planned_reflection → no_action → expiration` = cas BOL/contrat de décision, pas justification pour raccourcir WO95 ou patcher Chuu.

### Erika / gaming

Signature répétitive utile pour calibration/monoculture; pas de règle de personnage avant BOL.

### `cognition_call_source_not_perceived`

Verdict observé : `HEALTHY BUT NOISY`. Filtre sain, généré tardivement; optimiser seulement après mesure, sans dupliquer l'autorité perceptive.

### `character_moved` / observabilité

Follow-ups : payload `connector` potentiellement incomplet; `source_event_seq` absent sur invalidation. Qualifier séparément; jamais corriger V3c rétroactivement.

---

## Backlog différé

- oubli/consolidation/recollection mémoire avancés;
- contradictions/hypothèses de croyance plus riches;
- réseau relationnel et réparation;
- consentement opérationnel complet;
- identité/transformation/copie/fusion avancées;
- rattrapage temporel hors ligne condensé;
- interface sociale externe complète;
- optimisation fine coûts/provider;
- plusieurs adaptateurs LLM sans défaut démontré;
- segmentation subjective des événements / construction d'épisodes au-delà de P0.

## Discipline de fermeture

```text
contrat explicite
→ implémentation vérifiée
→ tests/falsifications
→ observation runtime lorsque nécessaire
→ intégration reconnue
→ product/current avancé
→ documentation synchronisée
```

Un résultat négatif, interrompu, `NOT EXERCISED` ou `INCONCLUSIVE` doit rester tel quel.

## Gouvernance

- ChatGPT : science, conception fonctionnelle, cohérence conceptuelle, documentation R&D.
- Grok : contre-audit scientifique adversarial indépendant.
- Codex : architecture réelle, code, migrations, tests, invariants techniques, ordre d'implantation.
- Propriétaire : autorité finale produit/design.

Le code réel peut imposer une meilleure architecture que celle imaginée en R&D; Codex doit préserver le contrat fonctionnel et expliquer la divergence.
