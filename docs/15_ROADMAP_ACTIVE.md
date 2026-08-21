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

Un seul chantier R&D runtime majeur à la fois. Des travaux préparatoires hors runtime peuvent avancer en parallèle s'ils ne modifient ni une baseline de qualification ni les contrats encore en cours de validation.

## Référence de cette consolidation

La base d'inspection utilisée pour cette mise à jour est `product/current` après ajout du dossier LoRA, au commit `7c70c0856db435a5de50a98939c1bef4ff59c8c8`.

Toujours refaire le préflight de `docs/GOUVERNANCE_GIT.md` avant tout WO. Cette valeur n'est pas une permission d'utiliser un ancien HEAD si `origin/product/current` a avancé.

État fonctionnel synthétique :

- Operational Cognition Grounding : **fermé**;
- P0 Memory : **ouvert**;
- rodage P0 Memory V3c : **interrompu avant audit de fermeture**, artefacts read-only;
- Conversation State : **R&D + contre-audit Grok clos — SOLIDE; audit architectural Codex restant**;
- BOL : **R&D + contre-audit Grok clos — SOLIDE; audit architectural Codex restant**;
- P3.5 Perception · Action · Sensorium : **R&D + contre-audit Grok + audit architectural Codex clos — SOLIDE AVEC RÉSERVES — READY FOR WORK ORDER**;
- PEFT/LoRA : **R&D transverse ouverte; aucune intégration runtime autorisée à ce stade**.

## Porte actuelle — P0 Memory / fermeture de V3c interrompu

Le produit possède déjà :

- admission sélective d'encodage;
- `subjective_trace` append-only;
- épisodes autobiographiques avec supports;
- retrieval contextuel borné;
- seeding social d'épisode;
- lifecycle append-only et révisions structurelles;
- exposition séparée de `memories` et `autobiographical_memories` au contexte cognitif.

V3c a été interrompu avant la fermeture formelle de P0. Cette interruption ne constitue ni un PASS ni un échec fonctionnel. Sa DB, ses journaux et son worktree sont des preuves historiques à conserver en lecture seule.

### Prochaine action P0

1. produire un rapport de qualification V3c strictement read-only à partir des données disponibles;
2. classer chaque preuve `PASS`, `FAIL`, `NOT EXERCISED UNDER VALID CONDITIONS` ou `INSUFFICIENT EVIDENCE` selon ce que les artefacts démontrent réellement;
3. vérifier la chaîne autobiographique complète;
4. trancher ce qui est requis pour fermer P0 et ce qui est volontairement différé;
5. si une preuve requise manque, ouvrir un **nouveau** rodage isolé depuis le `PRODUCT_HEAD` alors courant;
6. ne jamais modifier ou « compléter » rétroactivement V3c.

### Preuve runtime principale

```text
expérience sociale accessible
→ admission
→ subjective_trace
→ épisode autobiographique
→ retrieval contextuel ultérieur
→ CognitionContext routé
→ appel provider réel
```

Cette preuve qualifie l'exposition du souvenir au provider; elle ne prouve pas à elle seule que le souvenir a causé une décision précise du modèle.

### Scène mémoire A/B

La scène A Sophie → Erika ne peut être exercée que sous accessibilité causale réelle. La tentative V3c connue était `WAITING FOR VALID ACCESS`. Sans précondition valide, le résultat demeure `NOT EXERCISED UNDER VALID CONDITIONS`, jamais `FAILED` et jamais PASS artificiel.

Les paroles A/B restent des paroles, pas des faits canoniques concernant un carnet.

### Porte de sortie P0

L'audit doit distinguer explicitement :

- ce qui est réellement qualifié;
- ce qui manque encore au scope P0;
- ce qui appartient à une couche mémoire ultérieure.

Décisions encore à fermer notamment :

- seeding d'épisode depuis l'attention ordinaire;
- déclencheur naturel de lifecycle/révision;
- activation de candidats mémoire dans SCC;
- oubli, consolidation, familiarité, recollection et reconstruction avancée.

Une structure append-only permettant des révisions n'est pas une preuve que la reconsolidation ou l'oubli psychologique sont implémentés.

## Étape 1 après P0 — Conversation State minimal

**Maturité R&D : peer review scientifique Grok clos — SOLIDE; prêt pour audit architectural Codex.**

La science de base n'est donc pas à refaire. Lorsque P0 est fermé, la prochaine porte est :

```text
lecture du dossier Conversation State consolidé
→ audit architectural Codex contre product/current
→ résolution des divergences éventuelles
→ WO d'implantation borné
→ tests/falsifications
→ rodage de continuité conversationnelle
```

But fonctionnel : donner à une conversation une continuité interactionnelle explicite sans transformer la conversation en script ni en mémoire partagée omnisciente.

Le dossier R&D couvre déjà notamment :

- participation ≠ co-présence ≠ adressage;
- floor conversationnel;
- séquences ouvertes et pertinence de réponse sans obligation mécanique;
- repair;
- projets interactionnels / extended tellings;
- topic state et transitions;
- lapse, closing et clôture naturelle;
- compatibilité future multiparty/multi-floor.

Points à préserver lors de l'audit/WO :

- Conversation State = structure interactionnelle, pas motivation;
- état partagé de scène ≠ mémoire/croyance privée;
- une interruption peut clore sans inventer la suite;
- la répétition ne doit pas être « corrigée » par accumulation arbitraire de prompt.

## Étape 2 — Behavioral Opportunity Layer (BOL)

**Maturité R&D : peer review scientifique Grok clos — SOLIDE; prêt pour audit architectural Codex.**

Le BOL vient après Conversation State minimal. Là encore, la prochaine étape n'est pas une nouvelle recherche générale : c'est l'audit architectural contre le produit alors courant, puis un WO borné si le contrat reste compatible.

Le diagnostic V3c de Chuu reste un cas empirique utile :

```text
activité physiquement faisable
≠
opportunité comportementale pertinente
```

Besoin fonctionnel :

```text
motifs + préférences + objectifs/intention
+ contexte subjectivement accessible
+ capacités + environnement
→ petit ensemble borné d'opportunités comportementales pertinentes
→ cognition propose/sélectionne
→ moteur valide la faisabilité et les conséquences
```

Contraintes :

- pas de règle spéciale Chuu/Erika/autre personnage;
- pas de table universelle rigide `motif → activité`;
- peu d'opportunités pertinentes > énorme catalogue brut;
- absence d'opportunité pertinente ≠ impossibilité physique;
- `MotiveCandidate.possible_actions` ne doit pas être confondu avec une liste légale;
- `no_action` doit être réexaminé comme contrat sémantique, sans exiger une justification verbale décorative;
- ne pas patcher `sleep`/`rest` dans la whitelist pour contourner le problème général.

## Étape 3 — P3.5 Perception · Action · Sensorium

**Maturité : R&D + contre-audit Grok + audit architectural Codex CLOS — SOLIDE AVEC RÉSERVES — READY FOR WORK ORDER.**

P3.5 vient après BOL. Aucun nouvel audit scientifique ou architectural général n'est requis avant son futur WO, sauf si `product/current` a évolué de façon à invalider matériellement l'audit existant. Le préflight Git et une vérification fraîche de compatibilité restent obligatoires.

Principe :

```text
signal accessible
≠ détection
≠ sélection attentionnelle
≠ accès subjectif exploitable par la cognition
```

Frontière :

```text
affordance physique = relation corps ↔ environnement permettant potentiellement une action
opportunité BOL = possibilité comportementale actuellement pertinente
```

Le noyau V1 consolidé est volontairement parcimonieux :

1. accessibilité sensorielle;
2. qualité/incertitude minimale;
3. affordances relationnelles et effecteurs dépendants du corps;
4. contrats permettant la composition multi-processus, sans obligation de tout activer dans la première tranche;
5. feedback basique avec séparation correction automatique / réévaluation cognitive.

Sont explicitement reportés jusqu'à preuve d'utilité : causal inference multisensorielle sophistiquée, binding temporel fin, modèle quantitatif universel de double tâche, prédiction sensorimotrice détaillée, active sensing riche pour toutes les modalités, attention conjointe fine et segmentation subjective des événements.

La segmentation subjective des événements appartient désormais à une future R&D mémoire épisodique / construction d'épisodes, pas au noyau P3.5.

## Programme transverse dès maintenant — adaptation LLM / PEFT-LoRA

Document dédié : `docs/92_R_D_LORA_ADAPTATION_LLM.md`.

**Statut : R&D technique et fonctionnelle ouverte; prototypes hors runtime permis; intégration runtime différée.**

But : tester si un adaptateur léger améliore des comportements stables et génériques du composant LLM :

- `canon ≠ perception ≠ croyance` et `parole ≠ fait`;
- provenance et incertitude;
- abstention quand l'information manque;
- respect des contrats/schémas de sortie;
- réduction de la psychologisation ou des hidden-state claims non soutenus;
- robustesse aux données adversariales et reformulations.

Ne doivent pas devenir des poids implicites :

- faits/états canoniques;
- souvenirs individuels;
- relations, permissions, consentements;
- état conversationnel;
- opportunités BOL;
- règles physiques/affordances;
- scripts propres au casting.

### Séquence expérimentale LoRA

```text
benchmark de falsification gelé
→ baseline modèle de base
→ dataset train/validation distinct du test final
→ smoke QLoRA hors runtime
→ entraînement d'un seul adaptateur RIC initial
→ comparaison aveugle base vs base+adaptateur
→ tests OOD + régressions générales
→ décision d'intégration ou rejet
```

La R&D L0–L3 peut avancer avant P3.5 si elle ne modifie aucune baseline runtime. En revanche, **l'intégration runtime attend normalement la stabilisation de Conversation State, BOL et P3.5**.

## Étape 4 — porte d'intégration LLM adaptée

Après P3.5 :

- refaire le benchmark contre les contrats alors réellement stabilisés;
- entraîner/réentraîner l'adaptateur candidat si nécessaire;
- vérifier gains reproductibles et absence de fuite du benchmark;
- vérifier régressions conversation, SCC, décision, mémoire et sorties structurées;
- démontrer provenance `base model + adapter + version` et rollback vers le modèle de base;
- faire auditer par Codex le lifecycle réel de chargement/activation/hotswap/versioning;
- décision PRODUCT explicite : adopter, garder expérimental ou rejeter.

Un gain qualitatif subjectif ne suffit pas.

## Étape 5 — Affect au-delà du SCC

Après les fondations décisionnelles précédentes et la porte LoRA :

- dynamique affective générale;
- expression et régulation;
- interaction avec mémoire, buts, attention et relations;
- séparation stricte état subjectif / canon.

Éviter les labels émotionnels décoratifs sans mécanisme causal défendable.

## Étape 6 — cognition animale au-delà de Patoune CAT-0

Enrichir l'agence non sapiente sans projeter automatiquement le modèle humain sur l'animal et sans scripts d'espèce lorsque des mécanismes génériques suffisent.

Un éventuel LoRA RIC n'est pas présumé applicable à la cognition animale; son rôle devra être évalué séparément.

## Étape 7 — physiologie plus large

Étendre au-delà du cycle veille-sommeil/capacité physique seulement lorsque les interfaces comportementales nécessaires existent.

Chaque nouvelle variable doit avoir un propriétaire persistant, une causalité utile et une traduction comportementale justifiable. Ne pas ajouter des jauges parce qu'elles sont simplement simulables.

## Signaux V3c conservés pour les futurs chantiers

V3c est interrompu, mais ses observations restent valides dans la limite de ce qui a réellement été exercé.

### Chuu / idles techniques

Les chaînes `idle WO95 → planned_reflection → no_action → expiration` restent un cas BOL/contrat de décision, pas une justification pour raccourcir WO95 ou patcher Chuu.

### Erika / gaming

La préférence très alignée sur la whitelist a montré une signature répétitive. Conserver comme cas de calibration/monoculture; ne pas la corriger par prompt ou règle personnage avant BOL.

### `cognition_call_source_not_perceived`

Verdict observé : `HEALTHY BUT NOISY`. Le filtre protège l'accès subjectif mais intervient tard dans la génération de tentatives. Optimiser seulement en réutilisant la même autorité perceptive.

### `character_moved` / observabilité

Follow-ups séparés : payload `connector` potentiellement incomplet et `source_event_seq` absent sur le chemin d'invalidation cognitive. Les qualifier hors V3c; ne jamais corriger rétroactivement l'artefact.

### WO95 idle 600 s

Mesurer interruptions et expirations dans un rodage valide avant toute modification. Ne pas raccourcir le délai pour masquer un défaut d'opportunités.

## Backlog explicitement différé

- oubli/consolidation/recollection mémoire avancés;
- segmentation subjective d'événements / construction d'épisodes;
- hypothèses concurrentes et contradictions de croyances riches;
- réseau relationnel et réparation;
- consentement opérationnel complet;
- identité/transformation/copie/fusion avancées;
- rattrapage temporel hors ligne condensé;
- interface sociale externe complète;
- optimisation fine coût/provider après qualification fonctionnelle;
- spécialisation de plusieurs adaptateurs LLM sauf défaut distinct démontré.

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

Un résultat négatif, interrompu, `INSUFFICIENT EVIDENCE` ou `NOT EXERCISED` reste exactement cela. Ne jamais transformer l'absence de preuve en PASS.

## Gouvernance

- **ChatGPT** : science, conception fonctionnelle, cohérence conceptuelle, documentation R&D.
- **Grok** : contre-audit scientifique adversarial indépendant.
- **Codex** : architecture réelle, code, migrations, tests, invariants techniques et ordre d'implantation.
- **Propriétaire** : autorité finale produit/design.

Le code réel peut imposer une meilleure architecture que celle imaginée en R&D; Codex doit préserver le contrat fonctionnel ou signaler explicitement la divergence.
