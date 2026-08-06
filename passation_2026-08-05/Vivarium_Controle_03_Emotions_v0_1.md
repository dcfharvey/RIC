# Vivarium Social — Contrôle de cohérence 03

## Émotions

**Version :** 0.1  
**Date :** 4 août 2026  
**Verdict :** VALIDÉ AVEC CORRECTIONS CIBLÉES ET EXTENSION DE LA RÉGULATION INTERPERSONNELLE

## 1. Conclusion générale

Le système émotionnel conçu précédemment est scientifiquement bien fondé et demeure compatible avec les audits réalisés depuis :

- perception et attention;
- croyances;
- besoins et motivation;
- personnalité et attachement;
- valeurs;
- objectifs et intentions;
- décision;
- mémoire;
- relations;
- ontologie.

Il ne doit pas être reconstruit. Ses piliers sont maintenus :

```text
événement subjectivement interprété
→ appraisal
→ épisode émotionnel
→ tendances d’action
→ expression
→ régulation
→ évolution temporelle
→ conséquences cognitives et sociales
```

Les corrections nécessaires sont ciblées :

```text
famille émotionnelle
≠ programme fixe

appraisal
≠ raisonnement verbal conscient

émotion
≠ sentiment conscient
≠ étiquette verbale
≠ humeur
≠ affect général

expression
≠ lecture directe de l’état interne

diminution d’intensité
≠ régulation réussie

régulation
≠ seulement intrapersonnelle
```

## 2. L’émotion comme processus multi-composants

Un épisode émotionnel doit coordonner plusieurs composants sans exiger qu’ils soient parfaitement synchronisés :

```text
appraisal
physiologie et état corporel
tendance d’action
expression
sentiment conscient
étiquette émotionnelle
attention
motivation
```

```text
EmotionComponentState
- episode_id
- component_type
- current_state
- onset
- latency
- intensity
- confidence
- source
- last_update
```

La cohérence entre composants est une propriété émergente et variable, non une condition binaire.

Un agent peut :

- ressentir une activation corporelle avant de comprendre sa cause;
- afficher peu d’expression malgré une émotion intense;
- avoir une tendance d’action qu’il inhibe;
- éprouver quelque chose sans pouvoir le nommer;
- verbaliser une émotion différente de son état dominant.

## 3. Appraisal multi-niveaux

L’appraisal reste le mécanisme principal reliant une situation subjective à l’émotion, mais il ne doit pas être limité à une réflexion consciente ou verbale.

```text
AppraisalProcess
- triggering_representation
- processing_level
- checks
- outputs
- confidence
- accessibility
- update_history
```

Niveaux possibles :

```text
rapide et implicite
associatif
conscient mais non verbal
délibéré et verbal
```

Les dimensions retenues restent :

```text
relevance
goal_congruence
novelty
certainty
urgency
agency_self
agency_other
agency_circumstance
control
coping_capacity
avoidability
reversibility
norm_compatibility
boundary_impact
relational_meaning
loss_character
threat_character
```

Toutes ne sont pas calculées avec la même précision à chaque épisode.

## 4. Les familles émotionnelles sont des profils, pas des signatures rigides

Les profils comme colère, peur, tristesse, culpabilité, honte, gratitude, soulagement et joie demeurent utiles.

Ils deviennent des prototypes déclaratifs :

```text
EmotionFamilyProfile
- family
- typical_appraisal_patterns
- common_action_tendencies
- common_bodily_patterns
- common_expression_impulses
- common_regulation_targets
- compatible_mixed_states
- cultural_or_personal_variants
```

Une famille ne correspond pas à :

```text
un seul visage
une seule posture
une seule physiologie
une seule action
```

Une candidate émotionnelle est générée lorsqu’un ensemble d’appraisals ressemble suffisamment à un profil, mais le moteur conserve les facteurs réels plutôt que de remplacer le processus par l’étiquette.

## 5. Affect général, humeur et épisode émotionnel

```text
CoreAffectiveState
→ valence et activation générales momentanées

MoodState
→ état affectif plus diffus, durable et faiblement lié à une cause unique

EmotionEpisode
→ processus relativement organisé autour d’un enjeu ou d’une cause perçue
```

```text
CoreAffectiveState
- valence
- arousal
- tension
- energy
- last_materialized
```

```text
MoodState
- valence_bias
- activation_bias
- irritability
- anxiety_tone
- approach_tone
- duration
- attributed_causes
- confidence
- inertia_profile
```

Le mood influence les appraisals futurs sans commander les émotions.

Une émotion peut contribuer au mood, mais ne devient pas automatiquement une humeur durable.

## 6. Émotions simultanées et ambivalence

Le système maintient plusieurs épisodes actifs.

```text
joie envers un résultat
+
tristesse envers ce qui a été perdu
```

Les émotions de même valence peuvent également coexister :

```text
colère
+
peur
+
culpabilité
```

Les épisodes ne sont fusionnés que lorsqu’ils partagent réellement :

- le même enjeu;
- la même cible;
- une appraisal compatible;
- une proximité temporelle;
- une dynamique commune.

Sinon, ils demeurent séparés.

```text
MixedEmotionConfiguration
- active_episodes
- shared_trigger
- compatible_components
- conflicts
- conscious_integration
- ambivalence
```

## 7. Conscience, différenciation et étiquette

Le moteur sépare :

```text
état émotionnel produit
accès interoceptif
conscience qu’une émotion existe
différenciation
étiquette supposée
confiance dans l’étiquette
capacité à l’exprimer
```

```text
EmotionAwarenessProfile
- bodily_signal_access
- attention_to_internal_state
- interpretation_accuracy
- differentiation
- labeling_skill
- source_awareness
- acceptance
- expression_skill
```

L’interoception ne doit pas être une seule jauge. Détecter un signal corporel, y porter attention, l’interpréter correctement et le relier à une émotion sont des opérations distinctes.

```text
EmotionLabelHypothesis
- episode
- label
- confidence
- consciously_accessible
- evidence
- source
```

Le personnage peut dire :

```text
« Je suis fâchée »
```

alors que le moteur représente :

```text
peur de rejet
+ humiliation
+ colère secondaire
+ faible différenciation consciente
```

Cette divergence est un fait psychologique, pas une erreur du moteur.

## 8. Dynamique temporelle

Le modèle précédent de matérialisation paresseuse est maintenu.

Une émotion ne suit pas une décroissance universelle.

```text
EmotionDynamicsProfile
- onset_pattern
- baseline_decay
- minimum_duration
- reactivation_sensitivity
- rumination_sensitivity
- unresolved_issue_sensitivity
- regulation_sensitivity
- habituation
- context_dependence
```

```text
intensity_change
=
natural_dissipation
+ ongoing_cause
+ new_evidence
+ rumination
+ memory_reactivation
+ bodily_state
+ social_feedback
- effective_regulation
- concrete_resolution
```

Cette expression décrit les contributions; elle n’impose pas une somme naïve unique.

L’inertie doit rester distincte de la stabilité. Une émotion persistante peut être adaptée si la cause demeure active; une émotion très variable peut être inadaptée si elle répond de manière excessive à des fluctuations minimes.

## 9. Résolution et état latent

Une baisse d’intensité ne signifie pas que l’enjeu est résolu.

```text
EmotionResolutionState
- trigger_ended
- appraisal_revised
- goal_state_changed
- threat_removed
- loss_integrated
- repair_completed
- uncertainty_reduced
- residue
- reactivation_conditions
```

Statuts :

```text
emerging
active
peaking
declining
latent
reactivated
resolved
superseded
```

Une colère latente peut réapparaître lors d’une nouvelle violation comparable. Une peur peut diminuer tout en maintenant une surveillance accrue.

## 10. Tendances d’action

Les tendances d’action demeurent distinctes des décisions :

```text
approach
avoid
confront
protect
repair
seek_support
seek_information
monitor
hide
submit
assert_boundary
comfort
withdraw
freeze
explore
celebrate
```

```text
ActionTendency
- episode
- type
- target
- direction
- strength
- urgency
- conscious_access
- bodily_preparation
- inhibition
```

Le système décisionnel reçoit les tendances, mais les arbitre avec :

- objectifs;
- valeurs;
- engagements;
- capacités;
- risques;
- relations;
- règles;
- consentement.

## 11. Expression émotionnelle

L’expression reste multimodale :

```text
visage
voix
posture
mouvement
orientation
distance
contact
rythme
morphologie
```

Mais l’expression n’est pas une traduction univoque de l’émotion.

```text
produced_expression
=
spontaneous_impulse
+ communicative_intention
+ cultural_or_personal_display_rules
- suppression
+ bodily_leakage
+ physical_constraints
```

```text
ExpressionEpisode
- source_emotions
- spontaneous_impulses
- communicative_goal
- display_rules
- regulation
- body_adapter
- produced_channels
- leakage
```

Les autres personnages n’accèdent qu’à l’expression produite, puis l’interprètent selon leur propre perception et leurs croyances.

## 12. Adaptateurs corporels

Le principe des adaptateurs est maintenu.

```text
GenericExpressionImpulse
→ BodyExpressionAdapter
→ mouvements et signaux physiquement réalisables
```

### Humaine

- visage;
- regard;
- voix;
- posture;
- gestes;
- distance.

### Louve anthropomorphe

- canaux humains;
- oreilles;
- queue;
- orientation olfactive;
- tension de la fourrure si pertinente;
- posture digitigrade.

### Chat

- oreilles;
- queue;
- pupilles;
- posture;
- orientation;
- vocalisations;
- distance;
- immobilisation ou fuite.

### Slime

- forme;
- cohésion visible;
- fluidité;
- tension de surface;
- opacité ou couleur si le profil le permet;
- amplitude des mouvements;
- maintien ou perte de la silhouette.

Aucun adaptateur ne crée un « détecteur d’émotion » infaillible pour les observateurs.

## 13. Règles d’affichage et culture

```text
DisplayRule
- agent_or_culture
- context
- audience
- emotion_or_component
- encouraged_expression
- discouraged_expression
- substitution
- intensity_modulation
- confidence
```

Les règles d’affichage peuvent venir :

- de la personnalité;
- de l’apprentissage;
- du rôle;
- du contexte social;
- de la culture;
- du rapport de pouvoir;
- d’une stratégie délibérée.

Le MVP peut commencer avec des règles individuelles et sociales simples, sans construire immédiatement une simulation culturelle complète.

## 14. Régulation : trois décisions distinctes

```text
1. Faut-il réguler?
2. Quel aspect faut-il modifier?
3. Quelle stratégie faut-il choisir et appliquer?
```

```text
EmotionRegulationGoal
- target
- desired_direction
- desired_intensity
- desired_duration
- desired_expression
- desired_action_tendency
- social_goal
- instrumental_goal
- reason
```

Une personne peut vouloir :

- diminuer une émotion;
- l’augmenter;
- la maintenir;
- en comprendre la cause;
- changer seulement son expression;
- préserver une colère utile;
- réduire sa peur assez pour agir;
- paraître calme sans cesser d’être vigilante.

## 15. Sélection et implémentation de stratégie

```text
RegulationStrategySelection
- goal
- candidate_strategies
- emotion_intensity
- controllability
- time_available
- cognitive_load
- social_context
- costs
- expected_effects
- skill
- preference
- selected_strategy
```

```text
RegulationImplementation
- strategy
- start
- fidelity
- effort
- interruption
- immediate_effects
- side_effects
- actual_outcome
```

Savoir choisir une stratégie et savoir l’exécuter sont deux compétences distinctes.

## 16. Stratégies

```text
situation_selection
situation_modification
attention_deployment
reappraisal
acceptance
problem_solving
expression
expression_suppression
physiological_regulation
savoring
distraction
rumination
social_support_seeking
interpersonal_regulation
```

Aucune stratégie n’est universellement bonne ou mauvaise.

Exemples :

```text
suppression
→ peut protéger une interaction immédiate,
  mais coûte de l’effort et masque l’état à autrui

distraction
→ utile face à une intensité élevée et temporaire,
  mais insuffisante si le problème exige une action

reappraisal
→ utile si la situation peut être interprétée autrement,
  mais moins pertinente pendant une urgence immédiate

acceptance
→ peut réduire la lutte contre l’état,
  sans résoudre la cause externe
```

## 17. Succès de régulation

```text
RegulationOutcome
- goal_attainment
- emotion_change
- expression_change
- action_tendency_change
- physiological_cost
- cognitive_cost
- social_cost
- delayed_effect
- recurrence
- learning
```

Une stratégie n’est pas réussie uniquement parce que l’intensité baisse.

```text
colère diminuée
+
limite importante abandonnée
→ succès émotionnel partiel,
  échec instrumental possible
```

```text
peur encore présente
+
action sécuritaire accomplie
→ régulation fonctionnelle possible
```

## 18. Flexibilité

La compétence émotionnelle inclut :

```text
sensibilité au contexte
répertoire de stratégies
choix de stratégie
implémentation
surveillance du résultat
changement ou arrêt de stratégie
```

```text
RegulationFlexibilityProfile
- context_sensitivity
- strategy_repertoire
- switching_cost
- monitoring_quality
- persistence_bias
- abandonment_bias
- feedback_use
```

Le moteur ne doit pas récompenser la variété pour elle-même. Employer plusieurs stratégies inutiles n’est pas plus flexible que conserver une stratégie qui fonctionne.

## 19. Régulation interpersonnelle

La régulation peut viser :

```text
ses propres émotions avec l’aide d’autrui
les émotions d’autrui
un état affectif dyadique ou collectif
```

```text
InterpersonalRegulationEpisode
- regulator
- target
- perceived_target_state
- regulator_goal
- target_goal_estimate
- strategy
- consent_or_welcome
- relationship_context
- power_context
- target_interpretation
- immediate_effect
- relational_effect
- feedback_cycle
```

Cycle :

```text
A perçoit l’état de B
→ A décide d’intervenir
→ B perçoit et interprète l’intervention
→ l’émotion de B change ou non
→ B répond
→ A ajuste ou cesse
```

Une tentative de réconfort peut :

- soulager;
- irriter;
- sembler intrusive;
- invalider;
- créer de la proximité;
- accroître une dépendance;
- échouer sans mauvaise intention.

La relation et le pouvoir influencent la régulation, mais ne permettent pas de présumer qu’elle est bienvenue.

## 20. Régulation sociale et consentement

Les actions ordinaires de soutien peuvent être proposées selon le contexte.

Les interventions intrusives exigent une permission ou une justification :

```text
contact physique
restriction de mouvement
exposition forcée
retrait d’un objet
divulgation d’informations
pression émotionnelle
```

La régulation ne doit jamais devenir un prétexte permettant au moteur de contourner le futur système de consentement.

## 21. Mémoire, croyance et émotion

Le système conserve les séparations validées :

```text
émotion lors de l’événement
émotion encodée comme contexte
émotion produite par le rappel
réinterprétation actuelle
```

Une émotion reçoit des croyances et hypothèses comme entrées, mais ne les transforme pas automatiquement en vérités.

```text
croyance incertaine de trahison
→ colère et peur possibles

nouvelle preuve disculpante
→ appraisal révisée
→ émotion modifiée
```

La mémoire enregistre le contexte émotionnel sans convertir l’émotion en preuve objective de ce qui s’est passé.

## 22. Relations et émotions

Une émotion envers une personne ne constitue pas directement une dimension relationnelle.

```text
colère actuelle
≠ faible affection permanente

gratitude actuelle
≠ confiance globale

désir actuel
≠ engagement
```

L’émotion produit :

- des tendances;
- une signification;
- des comportements;
- éventuellement une preuve relationnelle.

La relation est mise à jour à travers l’interprétation des événements et de leurs conséquences, pas par copie directe de l’intensité émotionnelle.

## 23. Mood et décision

Le mood peut :

- biaiser la saillance;
- modifier les attentes;
- rendre certaines interprétations plus accessibles;
- modifier l’effort;
- influencer la sélection de stratégies.

Mais il ne doit jamais imposer :

```text
mood négatif
→ toute décision devient négative
```

Le contexte décisionnel reçoit les biais pertinents et leur intensité, avec une possibilité de correction consciente.

## 24. Chat et agents non sapients

Le chat utilise :

- appraisal rapide;
- peur;
- intérêt;
- frustration;
- plaisir;
- sécurité;
- tendances d’approche et d’évitement;
- expression corporelle;
- régulation par retrait, proximité, familiarité et environnement.

Il n’utilise pas automatiquement :

- étiquettes verbales;
- honte narrative complexe;
- culpabilité morale abstraite;
- reappraisal verbal;
- réflexion métacognitive élaborée.

Le moteur conserve toutefois des épisodes émotionnels et dynamiques compatibles avec sa cognition.

## 25. Stockage révisé

```text
core_affective_state
mood_state
mood_contributor

emotion_appraisal
emotion_appraisal_factor
emotion_episode
emotion_episode_trigger
emotion_component_state
emotion_mixed_configuration

emotion_action_tendency
emotion_expression
emotion_display_rule
emotion_label_hypothesis
emotion_awareness_profile

emotion_regulation_goal
emotion_regulation_selection
emotion_regulation_attempt
emotion_regulation_outcome
emotion_regulation_flexibility

interpersonal_regulation_episode
interpersonal_regulation_step
emotion_resolution
```

## 26. Événements

```text
emotion_appraisal_created
emotion_episode_started
emotion_episode_reinforced
emotion_component_updated
emotion_mixed_configuration_detected
emotion_episode_declining
emotion_episode_became_latent
emotion_episode_reactivated
emotion_episode_resolved

emotion_tendency_updated
emotion_expression_produced
emotion_label_hypothesis_formed
emotion_awareness_updated

emotion_regulation_goal_formed
emotion_regulation_strategy_selected
emotion_regulation_started
emotion_regulation_adjusted
emotion_regulation_completed
emotion_regulation_failed

interpersonal_regulation_started
interpersonal_regulation_received
interpersonal_regulation_rejected
interpersonal_regulation_effect_observed

mood_updated
```

## 27. Rôle du LLM

Le LLM peut :

- proposer une interprétation consciente;
- formuler une étiquette incertaine;
- générer une expression verbale;
- proposer une stratégie de régulation;
- résumer un conflit émotionnel;
- produire une tentative de soutien;
- expliquer les raisons accessibles au personnage.

Il ne peut pas :

```text
créer une émotion sans appraisal
fixer directement l’intensité
déclarer une expression universelle
lire l’émotion d’autrui avec certitude
révéler un état inconscient
résoudre un épisode arbitrairement
choisir ou imposer une régulation
déclarer une stratégie réussie
confondre humeur et émotion
transformer une tendance en action
déduire le consentement à une intervention
```

## 28. Tests obligatoires

```text
appraisal implicite avant étiquette
composants émotionnels partiellement désynchronisés
forte émotion avec faible expression
expression stratégique sans émotion correspondante
étiquette consciente erronée
faible différenciation émotionnelle
émotions positives et négatives simultanées
deux colères envers des enjeux différents
mood négatif sans épisode dominant unique
émotion latente réactivée
intensité faible avec problème non résolu
suppression réussie de l’expression sans baisse de l’expérience
régulation diminuant l’émotion mais nuisant au but
stratégie efficace dans un contexte et inefficace dans un autre
tentative de réconfort bienvenue
tentative de réconfort intrusive
relation forte sans permission d’intervention corporelle
chat régulant par retrait ou proximité
slime exprimant via morphologie et cohésion
```

## 29. Verdict final

Le système antérieur est conservé.

Corrections ciblées :

```text
faire des familles émotionnelles des profils déclaratifs
séparer appraisals implicites et raisonnement conscient
ajouter l’état affectif général et le mood
représenter la cohérence partielle des composants
séparer expérience, conscience, différenciation et étiquette
rendre les expressions multimodales, contextuelles et non diagnostiques
éviter une décroissance universelle
séparer sélection et implémentation de la régulation
évaluer le succès selon le but, les coûts et les effets différés
ajouter la flexibilité de régulation
ajouter un véritable cycle de régulation interpersonnelle
```

**Statut : ÉMOTIONS — VALIDÉ AVEC CORRECTIONS CIBLÉES ET EXTENSION DE LA RÉGULATION INTERPERSONNELLE.**

## 30. Références principales consultées

- Scherer et Moors, *The Emotion Process: Event Appraisal and Component Differentiation*.
- Scherer, *Studying appraisal-driven emotion processes*.
- Kuppens et Verduyn, *Emotion dynamics*.
- Russell, *Core affect, prototypical emotional episodes, and other things called emotion*.
- Oh et Tong, *Specificity in the Study of Mixed Emotions*.
- Barrett et al., *Emotional Expressions Reconsidered*.
- Scherer et Ellgring, *Multimodal expression of emotion*.
- Matthews et al., méta-analyse des déterminants du choix de régulation.
- Sheppes et al., *Emotion regulation choice*.
- Reeck, Ames et Ochsner, *The Social Regulation of Emotion*.
- Zaki et Williams, *Interpersonal emotion regulation*.
- Arican-Dinc et Gable, *Dyadic Emotion Regulation*.
- Van Bael et al., interoception subjective et alexithymie.
- Erbas et al., différenciation émotionnelle.
- Koval et al., recherches sur l’inertie affective.
