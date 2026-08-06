# Vivarium social artificiel — Demande de changement normative post-audit

**Version :** 0.2  
**Date :** 4 août 2026  
**Statut :** PRÉPARÉE ET APPROUVÉE COMME DIRECTION DE CONCEPTION — non encore fusionnée dans le dossier maître du dépôt  
**Remplace :** `Vivarium_Demande_Changement_Post_v0_1.md`  
**Objet :** intégrer les conclusions des dix audits majeurs et des trois contrôles de cohérence

---

## 1. Motif

Le dossier maître v0.1 et la première demande de changement ont été rédigés avant la revue scientifique et technique rétroactive.

Cette revue a confirmé les fondations du projet, mais elle a aussi restructuré :

- attention et perception;
- croyances;
- motivation;
- personnalité;
- valeurs et limites;
- objectifs et intentions;
- arbitrage;
- ontologie;
- persistance;
- administration;
- mémoire;
- relations;
- émotions.

Le présent document prépare l’intégration normative au dépôt. Il ne modifie pas le code.

---

## 2. Documents autoritatifs de cette demande

1. `Vivarium_Exigences_Normatives_Post_Audit_v0_1.md`
2. `Vivarium_Registre_Audits_v0_8.md`
3. audits et contrôles détaillés cités dans ce registre
4. `Vivarium_Index_Maitre_Decisions_v0_3.md`
5. `Vivarium_Memoire_Assistante_v10.md`

En cas de conflit avec une ancienne formulation de conception non implémentée, les exigences post-audit prévalent après intégration officielle.

Le code et les tests continuent de décrire ce qui existe réellement.

---

## 3. Décisions du dossier maître à remplacer

### DEC-001 — Population de référence

Ancienne formulation :

> Le MVP comporte exactement quatre personnages actifs, tous explicitement adultes.

Nouvelle formulation proposée :

> Le scénario de référence du MVP comporte quatre entités actives : trois personnages sapients explicitement adultes et un chat domestique non sapient. Le moteur ne fixe pas globalement la population à quatre.

### DEC-017 et DEC-019 — Interfaces

Nouvelle formulation proposée :

> Discord est l’interface sociale principale. Une application web locale minimale est l’interface administrative et appartient au MVP. Aucune interface ne modifie directement SQLite.

### DEC-009 — Modifications profondes

Nouvelle formulation proposée :

> Toute modification canonique profonde exige une commande métier, une validation en couches, un rapport d’impact, un plan préparé immuable, un checkpoint lorsque requis, une confirmation liée à un hash et une version, une transaction atomique et un audit administratif.

### DEC-013 — Besoins

Nouvelle formulation proposée :

> Les variables physiologiques, besoins psychologiques, motifs, désirs, ressources et états dérivés sont des catégories distinctes. Les valeurs numériques restent normalement cachées et s’expriment par les comportements.

### DEC-015 — Mémoire

Nouvelle formulation proposée :

> La mémoire distingue événement canonique, perception, encodage subjectif, épisode, consolidation, représentation courante, récupération reconstructive, provenance et oubli multicausal. Le moteur conserve l’historique des révisions.

### DEC-016 — Contenu relationnel et adulte

Nouvelle formulation proposée :

> Le contenu relationnel, romantique et adulte peut émerger seulement entre entités sapientes explicitement adultes, selon leurs états, préférences, relations, permissions et consentements actuels. Aucun score relationnel, désir, rôle ou engagement ne constitue un consentement.

### DEC-023 — Intégrité corporelle

Conserver le principe actuel et préciser :

> L’univers initial interdit la mort, l’amputation et les dommages corporels involontaires permanents. Les blessures non fatales et récupérables restent permises selon des règles causales.

---

## 4. Nouvelles décisions proposées

### DEC-036 — Méthode de conception

Tout nouveau système doit être précédé d’une revue scientifique ou technique, puis transformé en système opérationnel testable.

### DEC-037 — Cognition subjective

La réalité, la perception, l’interprétation, les hypothèses, les croyances, l’encodage, les souvenirs et le récit conscient restent séparés.

### DEC-038 — Perception faillible

La perception comporte enregistrement implicite, détection, attention, conscience et intégration multisensorielle; elle permet omissions et fausses alertes.

### DEC-039 — Épistémologie structurée

Les croyances conservent hypothèses concurrentes, preuves, provenance, modèles de source, contradictions et révisions.

### DEC-040 — Motivation restructurée

Le système distingue régulation physiologique, besoins psychologiques, motifs, incitations, désirs, objectifs et apprentissage de valeur.

### DEC-041 — Personnalité mécanistique

Les traits continus modulent des mécanismes et évoluent lentement. L’attachement est contextuel, dimensionnel et propre aux relations.

### DEC-042 — Valeurs, principes et limites

Les valeurs, principes, convictions morales, limites, normes, lois et contraintes physiques sont des structures distinctes.

### DEC-043 — Objectifs et intentions

Les objectifs forment un graphe de fins et de moyens. Les intentions persistent par défaut et conservent un contexte de reprise.

### DEC-044 — Décision bornée et explicable

Le moteur génère peu d’options, distingue impossibilité et transgression, compare des profils multidimensionnels et arrête la recherche lorsqu’une option est suffisamment acceptable.

### DEC-045 — Mémoire reconstructive

La mémoire stocke ce qui a été encodé subjectivement. La récupération est guidée par des indices, faillible et distincte de la vérité canonique.

### DEC-046 — Relations multidimensionnelles

Les relations sont directionnelles, propres aux domaines, fondées sur des preuves et intégrées à un réseau social. La confiance, l’intimité, le pouvoir, l’engagement et la réparation sont décomposés.

### DEC-047 — Émotions processuelles

Les émotions sont des processus multi-composants produits par des appraisals. L’humeur, le sentiment, l’étiquette, l’expression et la régulation restent séparés.

### DEC-048 — Régulation interpersonnelle

Les agentes peuvent tenter de réguler les émotions d’autrui, mais l’effet dépend de la perception de la cible et les interventions intrusives restent soumises aux permissions.

### DEC-049 — Ontologie composable

Identité, type, phase, rôle, sujet cognitif, contrôleur, corps, manifestation, forme et apparence sont séparés.

### DEC-050 — Capacités et affordances

Les capacités sont dérivées des composants et de l’état. Les affordances sont des relations situées entre acteur, action, cible et environnement.

### DEC-051 — Transitions d’identité

Toute copie, transformation, séparation, fusion, reconstitution ou remplacement applique une politique d’identité explicite. Les cas avancés restent différés dans le MVP.

### DEC-052 — Event sourcing sélectif

Le journal conserve les changements canoniques significatifs. Les tables d’état servent les lectures courantes et les projections restent reconstruisibles.

### DEC-053 — Sauvegardes spécialisées

Snapshot de projection, checkpoint administratif, backup physique et export portable sont quatre mécanismes distincts.

### DEC-054 — Modèles et instances

Les modèles publiés sont versionnés et immuables. Chaque instanciation crée une identité indépendante et aucune modification ne se propage silencieusement.

### DEC-055 — Administration canonique

L’application web locale est un client d’une API canonique. Les changements sensibles utilisent des commandes métier.

### DEC-056 — Registres et validation

Les composants, capacités, unités, événements et validateurs possèdent des contrats versionnés. JSON Schema ne remplace pas les validateurs sémantiques.

### DEC-057 — Préparation et confirmation

Une modification profonde produit un plan préparé, un hash, une version de base et un rapport d’impact. Un changement concurrent invalide le plan.

### DEC-058 — Séparation des journaux

Le journal canonique, l’audit administratif et les diagnostics techniques sont distincts.

### DEC-059 — LLM sans autorité

Le LLM propose et formule. Il ne fixe ni vérité, ni capacité, ni mémoire, ni émotion, ni relation, ni consentement, ni résultat canonique.

### DEC-060 — Consentement indépendant

Aucune affection, confiance, intimité, autorité, attirance, promesse ou relation ne constitue un consentement actuel.

---

## 5. Exigences normatives

Intégrer le document :

`Vivarium_Exigences_Normatives_Post_Audit_v0_1.md`

Il devient le catalogue détaillé des invariants post-audit.

Le dossier maître v0.2 devra soit :

- inclure ces exigences;
- soit les référencer comme annexe normative versionnée.

---

## 6. Révision du modèle logique

La conception future doit prévoir les familles d’objets suivantes, sans imposer immédiatement toutes les tables :

```text
perceptual_opportunity
sensory_evidence
subjective_percept
attention_state

epistemic_question
hypothesis
belief_state
evidence_item
source_model
belief_conflict
epistemic_goal

physiological_regulation
regulatory_signal
psychological_need_experience
motive_candidate
incentive_value

personality_disposition
situation_response_tendency
attachment_activation_episode

value_priority
personal_principle
personal_boundary
social_norm
value_conflict

goal
goal_link
goal_commitment
intention
implementation_intention
social_commitment

decision_episode
candidate_option
option_prediction
decision_profile
execution_monitor

memory_encoding_record
memory_episode
memory_retrieval_result
memory_revision
prospective_memory_trace

relationship_view
relationship_evidence
situational_trust_assessment
responsiveness_episode
relationship_repair
social_network_context

emotion_appraisal
emotion_episode
emotion_component_state
mood_state
emotion_regulation_attempt
interpersonal_regulation_episode

canonical_entity
embodiment
manifestation
form_configuration
controller_assignment
capability_derivation
affordance_candidate

prepared_change
validation_report
impact_report
administrative_checkpoint
outbox_message
```

Le schéma physique sera conçu lot par lot. Les noms ci-dessus décrivent les séparations normatives.

---

## 7. Chemin critique corrigé

### Étape A — Terminer la Phase 3 existante

1. Phase 3.3B2 — effets mécaniques des blessures;
2. Phase 3.3C — reproductibilité et fermeture;
3. audit de fermeture du code et des tests.

### Étape B — Intégration normative

1. fusionner cette demande dans un dossier maître v0.2;
2. ajouter une matrice décision–exigence–test;
3. réconcilier les phases historiques avec l’état réel du dépôt.

### Étape C — Vertical slice administratif

1. registre minimal de contrats;
2. unités et schémas;
3. validateurs nécessaires aux quatre profils;
4. API `prepare / validate / impact / confirm`;
5. journal administratif;
6. gestionnaire d’univers et de résidence;
7. gestionnaire de modèles et d’entités;
8. interface web locale minimale;
9. création ou migration de la résidence;
10. création ou migration des quatre profils définitifs.

### Étape D — Boucle monde–action–perception

1. contrats d’actions et affordances;
2. permissions et limites;
3. manifestations d’événements;
4. scènes;
5. perception et attention;
6. snapshot subjectif.

### Étape E — Boucle cognitive et sociale

1. croyances et provenance;
2. mémoire;
3. émotions;
4. besoins et motifs;
5. objectifs, engagements et intentions;
6. arbitrage;
7. conversations;
8. relations;
9. initiatives.

### Étape F — Systèmes encore à concevoir

Toujours précédés d’une revue :

- consentement opérationnel;
- modèle de soi;
- apprentissage et évolution;
- secrets et circulation de l’information;
- orchestration et récupération de contexte LLM;
- groupes et collectifs avancés.

---

## 8. Scénarios d’acceptation post-audit

Ajouter au catalogue de tests :

- signal enregistré sans perception consciente;
- omission et fausse alerte;
- croyances concurrentes avec source commune non comptée deux fois;
- motif actif ne produisant aucun objectif;
- intention interrompue puis reprise;
- objectif subjectivement faisable mais objectivement impossible;
- décision arrêtée par suffisance;
- critère psychologique violable distinct d’un blocage canonique;
- souvenir vif mais erroné;
- effet relationnel persistant malgré souvenir inaccessible;
- confiance forte dans un domaine et faible dans un autre;
- pardon sans restauration de confiance;
- émotion latente réactivée;
- expression émotionnelle ambiguë;
- régulation réduisant l’émotion mais nuisant au but;
- tentative de soutien bienvenue puis intrusive selon le contexte;
- changement de forme sans changement d’identité;
- capacité existante mais affordance absente;
- replay sans appel au LLM;
- retry Discord sans message canonique en double;
- modification profonde invalidée par une version concurrente;
- modèle modifié sans propagation à l’instance;
- relation forte sans consentement actuel.

---

## 9. Éléments différés confirmés

- fusion et fragmentation de consciences;
- possession;
- plusieurs corps actifs;
- collectifs cognitifs avancés;
- simulation culturelle complète;
- reconsolidation biologique détaillée;
- ville complète;
- plugins arbitraires;
- milliers d’agents;
- mort, vieillissement, maladie et grossesse dans l’univers initial;
- optimisation prématurée;
- reconstruction des anciens choix par un nouveau LLM.

---

## 10. Approbation et intégration

Cette demande est approuvée comme direction de conception par le propriétaire.

Avant de la remettre à l’IA exécutante comme autorité de code :

1. fermer la Phase 3;
2. fusionner le contenu dans un dossier maître v0.2;
3. créer la matrice de traçabilité;
4. définir le premier lot administratif borné;
5. demander d’abord un plan sans code.
