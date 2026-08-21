# Roadmap active — RIC

**Version :** 2.2  
**Mise à jour :** 21 août 2026  
**Statut :** trajectoire opérationnelle courante

Cette roadmap fixe l'ordre des grands chantiers. Elle ne remplace ni la passation opérationnelle (`docs/99_PASSATION_COURANTE.md`), ni le noyau normatif (`docs/00_DOSSIER_MAITRE_IA.md`), ni le registre de décisions (`docs/01_REGISTRE_DECISIONS.md`).

## Principe de conduite

RIC suit deux règles :

> **Flexible creativity. Rigorous execution.**
>
> **Verify twice. Commit once.**

Une idée peut rester ouverte tant qu'elle est exploratoire. Dès qu'elle devient spécification, architecture, code ou canon, elle doit être testable, traçable et falsifiable.

Pour tout système comportemental, cognitif, social ou physiologique : littérature scientifique/technique d'abord, traduction opérationnelle ensuite. Séparer explicitement résultats empiriques, conclusions incertaines, hypothèses de modélisation et choix d'ingénierie.

Un seul chantier R&D runtime majeur à la fois. Des travaux préparatoires purement expérimentaux peuvent avancer en parallèle s'ils ne modifient ni la baseline runtime ni les contrats encore en qualification.

## Référence produit

Baseline documentaire vérifiée avant cette mise à jour :

- version déclarée : `0.2.0a5`;
- dernière migration : `0061_autobiographical_append_only_lifecycle.sql`;
- Operational Cognition Grounding : fermé;
- P0 Memory : ouvert;
- rodage P0 Memory V3c : interrompu avant audit de fermeture; artefact à conserver en lecture seule.

Toujours revérifier `origin/product/current` avant tout WO. Ne pas traiter le SHA inscrit dans un document comme une référence plus fraîche que Git lui-même.

## Vue d'ensemble actuelle

```text
P0 Memory — fermeture
→ Conversation State minimal — R&D/Grok clos, audit Codex à faire
→ BOL — R&D/Grok clos, audit Codex à faire après Conversation State
→ P3.5 — R&D/Grok/Codex clos, READY FOR WORK ORDER quand son tour arrive
→ porte d'intégration LoRA
→ Affect
→ cognition animale
→ physiologie plus large
```

En parallèle, sans toucher au runtime : benchmark, dataset et faisabilité technique LoRA/QLoRA.

---

## Porte actuelle — P0 Memory / fermeture de V3c interrompu

Le produit possède maintenant les fondations autobiographiques suivantes :

- admission sélective d'encodage;
- `subjective_trace` append-only;
- épisodes autobiographiques avec supports;
- retrieval contextuel borné;
- seeding social d'épisode;
- lifecycle append-only et révisions structurelles;
- exposition séparée de `memories` et `autobiographical_memories` au contexte cognitif.

V3c a été interrompu avant la fermeture formelle de P0. Cette interruption ne constitue ni un PASS ni un échec fonctionnel. La base et les journaux disponibles restent des preuves historiques en lecture seule.

### Prochaine action P0

Le mandat détaillé est maintenant documenté dans `docs/P0_V3C_READONLY_QUALIFICATION_MANDATE.md`.

Ordre :

1. produire le rapport de qualification V3c strictement en lecture seule;
2. distinguer `PASS`, `FAIL`, `NOT EXERCISED UNDER VALID CONDITIONS` et `INCONCLUSIVE`;
3. vérifier si les preuves disponibles suffisent à ouvrir l'audit de fermeture P0;
4. si une preuve réellement nécessaire manque, lancer un nouveau rodage isolé depuis la référence produit alors courante;
5. ne jamais reprendre ou corriger rétroactivement V3c.

### Preuve runtime encore recherchée

```text
expérience sociale accessible
→ admission
→ trace subjective
→ épisode autobiographique
→ retrieval contextuel
→ CognitionContext routé
→ provider réel
```

La preuve qualifie l'exposition du souvenir au provider; elle ne prouve pas à elle seule que le souvenir a causé la décision du modèle.

### Si la situation de test n'a pas eu lieu

La scène A Sophie → Erika ne peut être exercée que sous accessibilité causale réelle. Si V3c n'a jamais offert cette précondition, classer le chemin `NOT EXERCISED UNDER VALID CONDITIONS`, pas `FAILED`.

### Porte de sortie P0

À la fermeture P0, distinguer :

- ce qui est réellement qualifié;
- ce qui manque encore pour P0;
- ce qui est volontairement différé à une couche mémoire ultérieure.

Les points à trancher comprennent notamment :

- seeding d'épisode à partir de l'attention ordinaire;
- déclencheur naturel de lifecycle/révision;
- activation de candidats mémoire dans SCC;
- oubli, consolidation, familiarité, recollection et reconstruction avancée.

Une structure de révision append-only n'est pas une implémentation complète de la reconsolidation ou de l'oubli psychologique.

---

## Étape 1 après P0 — Conversation State minimal

**Maturité R&D vérifiée :** peer review scientifique Grok clos — `SOLIDE`; dossier fonctionnel déjà produit. Prochaine étape quand P0 est fermé : **audit architectural Codex**, pas reprise de la recherche depuis zéro.

Dossier de référence Drive : `Vivarium_social_R&D_Conversation_State_minimal.md`.

But fonctionnel : donner à une conversation une continuité explicite suffisante pour éviter que chaque tour soit traité comme une fenêtre presque indépendante, sans transformer le dialogue en script.

Le dossier couvre déjà notamment :

- participation ≠ co-présence ≠ adressage;
- floor conversationnel;
- séquences ouvertes et expansions;
- repair;
- progressivité;
- extended tellings;
- interactional projects;
- topic state;
- clôture coordonnée;
- possibilité de silence/lapse sans fermeture automatique;
- compatibilité multiparty future.

Travail restant avant implantation :

1. audit Codex sur l'architecture réelle alors courante;
2. résoudre les divergences techniques éventuelles sans changer silencieusement le contrat fonctionnel;
3. ouvrir un WO borné seulement après audit;
4. qualifier ensuite la continuité réelle et les répétitions en runtime.

Frontière : Conversation State structure l'interaction; il ne devient ni mémoire subjective, ni BOL, ni SCC.

Ne pas corriger la répétition par accumulation de prompt ad hoc avant ce chantier.

---

## Étape 2 — Behavioral Opportunity Layer (BOL)

**Maturité R&D vérifiée :** peer review scientifique Grok clos — `SOLIDE`; prêt pour audit architectural Codex lorsque Conversation State minimal est suffisamment raccordé pour que son architecture soit inspectée sur une base fraîche.

Dossier de référence Drive : `RIC_R&D_Behavioral_Opportunity_Layer_minimal.md`.

Le diagnostic V3c de Chuu a fourni un cas empirique clair : la faisabilité moteur ne suffit pas à créer une opportunité comportementale pertinente.

État alpha observé :

```text
motifs / préférences / buts / contexte
        ↓
   [raccord générique incomplet]
        ↓
whitelist d'activités MVP techniquement faisables
        ↓
choix LLM ou no_action
```

Le BOL doit traiter le besoin fonctionnel suivant :

> À partir des motifs, préférences, objectifs, contexte, capacités et environnement réellement accessibles, produire un ensemble borné d'opportunités comportementales génériques, distinct des affordances physiques, que le moteur peut valider et que la cognition peut sélectionner.

Le dossier R&D couvre déjà :

- opportunité ≠ intention ≠ action;
- possibilité canonique ≠ opportunité subjective;
- continuer/interrompre/reprendre/report/attendre comme vraies possibilités;
- motifs concurrents sans hiérarchie fixe universelle;
- contexte, buts, besoins, habitudes, engagements, prospective memory et Conversation State comme sources;
- coût d'interruption/reprise;
- synergie/conflit entre buts;
- raisons structurées `for/against` sans score psychologique universel;
- suffisance plutôt que maximisation obligatoire;
- fonctionnement événementiel plutôt qu'un tick mental permanent.

Contraintes de conception :

- aucune règle spéciale Chuu/Erika;
- aucune table rigide `motif → activité` comme modèle universel;
- peu d'opportunités pertinentes > énorme catalogue brut;
- cognition propose, moteur valide;
- aucune omniscience canonique injectée dans le champ subjectif;
- absence d'opportunité pertinente ≠ impossibilité physique.

### Cas de référence Chuu

Le futur BOL devra expliquer génériquement pourquoi une slime avec préférence `playful_group`, aucun partenaire social accessible, un motif de récupération et un environnement donné a ou n'a pas une occasion intéressante — sans `if character == Chuu`.

### Points techniques à clarifier pendant l'audit Codex

- rôle réel de `MotiveCandidate.possible_actions`;
- sémantique de `no_action`;
- raccord entre préférences abstraites et occasions concrètes;
- raccord entre activités moteur, affordances physiques et opportunités cognitives;
- génération/bor­nage/présentation des candidates sans ranking caché.

Ne pas patcher simplement `sleep`/`rest` dans la whitelist des `planned_reflection` pour contourner le problème général.

---

## Étape 3 — P3.5 Perception · Action · Sensorium

**Maturité R&D vérifiée :** R&D scientifique + contre-audit Grok + audit architectural Codex clos. Les clarifications post-audit ont été acceptées; verdict final : **READY FOR WORK ORDER**.

Le chantier n'est pas ouvert maintenant : il attend son tour après BOL. Quand ce tour arrive, refaire un préflight frais de `origin/product/current`, puis transformer le dossier déjà audité en WO sans recommencer l'audit scientifique/architectural sauf divergence nouvelle.

Principe central :

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
4. contrats capables de supporter la composition multi-processus sans exiger la concurrence persistante dès la première tranche;
5. feedback basique avec séparation correction automatique / réévaluation cognitive.

Frontière conceptuelle :

```text
affordance physique = relation corps ↔ monde permettant une action
opportunité BOL = possibilité comportementale actuellement pertinente
```

Extensions explicitement reportées jusqu'à preuve d'utilité : fusion multisensorielle sophistiquée, binding temporel fin, quantification universelle de double tâche, attention conjointe fine, prédiction sensorimotrice détaillée et segmentation subjective des événements.

Operational Cognition Grounding prépare P3.5 mais ne le remplace pas.

---

## Programme transverse dès maintenant — adaptation LLM / PEFT-LoRA

Dossier de référence : `docs/R_D_LORA_ADAPTATION_LLM.md`.

**Statut :** faisabilité technique plausible; utilité RIC non démontrée; R&D hors runtime autorisable.

Le recours à LoRA/QLoRA est une piste d'adaptation du fournisseur, pas une nouvelle source d'autorité et pas un remplacement de l'état explicite de RIC.

### But à tester

Évaluer si une adaptation légère améliore de façon mesurable des comportements stables et génériques :

- `canon ≠ perception ≠ croyance`;
- `parole ≠ fait`;
- provenance et incertitude;
- abstention appropriée;
- respect des schémas de sortie;
- réduction du hidden-state overclaim et de la psychologisation gratuite;
- robustesse aux instructions hostiles présentes comme données du monde.

### Ce qui ne doit pas être appris dans les poids

- faits/état canonique;
- souvenirs, croyances et relations actuelles;
- permission/consentement;
- personnalité d'un personnage;
- état de conversation;
- buts/intentions en cours;
- règles physiques/affordances;
- scripts `personnage → comportement`.

Invariant :

```text
état dynamique explicite ≠ poids du modèle
```

### Méthode

```text
benchmark de falsification gelé
→ baseline modèle de base
→ dataset séparé
→ smoke-test QLoRA hors runtime
→ comparaison base vs adaptateur
→ tests hors distribution / métamorphiques / régression
→ décision d'intégration ou rejet
```

Le premier candidat reste **un seul adaptateur générique RIC**. Aucun LoRA conversation/mémoire/personnage séparé sans déficience distincte démontrée.

### Matériel

Chemin de qualification privilégié pour la RX 7800 XT : WSL2 + ROCm supporté + backend 4-bit à qualifier. Windows natif ne doit pas être présumé équivalent tant que la matrice/framework réelle ne l'a pas confirmé.

### Séquençage

La R&D benchmark/dataset/faisabilité peut avancer maintenant sans contaminer P0. En revanche, l'intégration runtime attend normalement Conversation State + BOL + P3.5, car ces chantiers stabilisent précisément ce que le LLM reçoit et produit.

---

## Étape 4 — porte d'intégration LLM adaptée

Après P3.5 :

- réévaluer le benchmark sur les contrats stabilisés;
- entraîner/réentraîner l'adaptateur candidat;
- comparer systématiquement modèle de base et variante adaptée;
- vérifier conversation, interprétation sociale, décision, mémoire, schémas de sortie et cas hors domaine;
- vérifier qu'une baisse de violations ne vient pas d'une sur-abstention;
- exiger rollback vers le modèle de base et provenance `base_model + adapter_version`;
- faire auditer par Codex le chargement/intégration réels;
- décision produit explicite d'adoption ou rejet.

Aucun gain qualitatif subjectif ne suffit.

---

## Étape 5 — Affect au-delà du SCC

Après les fondations décisionnelles précédentes et la porte d'adaptation LLM :

- dynamique affective plus générale;
- expression;
- régulation;
- interaction avec mémoire, buts, attention et relations;
- séparation stricte entre état subjectif et vérité canonique.

Toute extension devra être fondée scientifiquement et testable; éviter les labels émotionnels décoratifs sans mécanisme.

---

## Étape 6 — cognition animale au-delà de Patoune CAT-0

Développer une agence non sapiente plus riche sans projeter automatiquement le modèle cognitif humain sur l'animal.

Les mécanismes devront être génériques, comparables et fondés sur la littérature pertinente.

Un éventuel adaptateur LLM RIC ne doit pas être présumé applicable à la cognition animale : cette question devra être testée selon le rôle réel du LLM dans cette couche.

---

## Étape 7 — physiologie plus large

Étendre au-delà du cycle sommeil/capacité physique seulement lorsque les systèmes précédents offrent les interfaces nécessaires.

Éviter d'ajouter des jauges simplement parce qu'elles sont simulables : chaque variable doit avoir un propriétaire persistant, une causalité utile et une traduction comportementale justifiable.

---

## Signaux V3c à conserver pour les futurs chantiers

V3c est interrompu, mais ses observations restent des données expérimentales valides dans les limites de ce qui a réellement été exercé. Elles ne sont pas les résultats d'un rodage arrivé à son protocole de fermeture.

### Chuu / idles techniques

Les chaînes `idle WO95 → planned_reflection → no_action → expiration` restent un cas de diagnostic BOL/contrat de décision, pas une justification pour raccourcir WO95 ou patcher Chuu.

### Erika / gaming

La préférence très alignée sur la whitelist a montré une signature répétitive. Conserver cette observation comme cas de calibration/monoculture; ne pas la corriger par prompt ou règle de personnage avant BOL et les évaluations appropriées.

### `cognition_call_source_not_perceived`

Verdict observé : `HEALTHY BUT NOISY`. Le filtre protège correctement l'accès subjectif mais est utilisé tardivement. Optimisation possible après mesure, sans dupliquer l'autorité perceptive.

### `character_moved` / observabilité

Deux follow-ups techniques : payload `connector` potentiellement incomplet dans certains événements et `source_event_seq` absent sur le chemin d'invalidation cognitive. Les qualifier séparément; ne pas modifier V3c rétroactivement.

---

## Backlog explicitement différé

- oubli/consolidation/recollection mémoire avancés;
- hypothèses concurrentes et contradictions de croyances plus riches;
- réseau relationnel et réparation;
- consentement opérationnel complet;
- identité/transformation/copie/fusion avancées;
- rattrapage temporel hors ligne condensé;
- interface sociale externe complète;
- optimisation fine coûts/provider après qualification fonctionnelle;
- éventuelle spécialisation de plusieurs adaptateurs LLM, sauf défaut démontré;
- segmentation subjective des événements / construction d'épisodes au-delà de P0.

---

## Discipline de fermeture

Une étape n'est pas fermée parce que le code existe. La fermeture exige :

```text
contrat explicite
→ implémentation vérifiée
→ tests/falsifications
→ observation runtime lorsque nécessaire
→ intégration reconnue
→ product/current avancé
→ documentation synchronisée
```

Un résultat négatif, interrompu, `NOT EXERCISED` ou `INCONCLUSIVE` doit rester tel quel. Ne jamais transformer l'absence de preuve en PASS documentaire.

## Gouvernance

- ChatGPT : science, conception fonctionnelle, cohérence conceptuelle, documentation R&D.
- Grok : contre-audit scientifique adversarial indépendant.
- Codex : architecture réelle, code, migrations, tests, invariants techniques, ordre d'implantation.
- Propriétaire : autorité finale produit/design.

Le code réel peut imposer une meilleure architecture que celle imaginée en R&D; Codex doit alors préserver le contrat fonctionnel et expliquer la divergence.
