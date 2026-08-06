# Vivarium Social — Contrôle de cohérence 02

## Relations

**Version :** 0.1  
**Date :** 4 août 2026  
**Verdict :** VALIDÉ AVEC CORRECTIONS CIBLÉES ET UNE EXTENSION DE RÉSEAU SOCIAL

## 1. Conclusion générale

Le système relationnel conçu précédemment est bien fondé et demeure compatible avec les audits réalisés depuis :

- attachement;
- personnalité;
- croyances et métaperceptions;
- valeurs et limites;
- objectifs et engagements;
- décision;
- mémoire;
- ontologie;
- persistance.

Il ne doit pas être reconstruit. Ses piliers sont maintenus :

```text
relation directionnelle
relation multidimensionnelle
faits dyadiques distincts des perceptions
métaperceptions faillibles
preuves relationnelles
rôles composables
pouvoir et dépendance séparés de l’affection
réparation progressive
```

Les corrections principales sont :

```text
confiance
≠ confiance accordée dans une situation
≠ perception de fiabilité

intimité
≠ simple proximité
≠ quantité de divulgation

engagement
≠ satisfaction
≠ obligation
≠ santé de la relation

réparation
≠ excuse
≠ pardon
≠ réconciliation
≠ restauration de confiance

relation dyadique
≠ relation isolée du réseau social
```

## 2. Trois niveaux demeurent obligatoires

```text
DyadicCanonicalFact
→ rôle, accord, interaction et dépendance objectivement établis

RelationshipView A→B
→ manière dont A évalue et vit sa relation avec B

RelationshipMetaView A about B→A
→ ce que A croit que B pense, ressent ou attend envers A
```

Exemple :

```text
Fait canonique :
A et B partagent une chambre selon un accord actif.

Vue A→B :
A considère B comme très fiable et proche.

Vue B→A :
B apprécie A, mais souhaite davantage de distance.

Métaperception A :
A croit que B souhaite encore plus de proximité.
```

Aucun de ces niveaux ne doit être automatiquement déduit des deux autres.

## 3. Directionnalité et interdépendance

```text
A→B
≠
B→A
```

Mais les deux vues ne sont pas indépendantes au sens causal :

```text
comportement de A
→ perception de B
→ état B→A
→ comportement futur de B
→ perception de A
→ état A→B
```

Le système doit donc permettre :

- effets d’acteur;
- effets de partenaire;
- boucles réciproques;
- divergences persistantes;
- états dyadiques émergents.

La relation n’est pas stockée comme une seule fiche symétrique.

## 4. État relationnel et preuves restent séparés

```text
RelationshipEvidence
→ observation interprétée portant sur un domaine relationnel

RelationshipState
→ estimation actuelle résultant d’un ensemble de preuves
```

Une preuve contient :

```text
RelationshipEvidence
- evaluator
- target
- source_event
- perceived_action
- attributed_intention
- domain
- direction
- diagnosticity
- stakes
- surprise
- confidence
- context
- repetition_cluster
- source_memory
```

L’état courant ne remplace pas les preuves. Les preuves permettent d’expliquer :

```text
pourquoi la confiance a changé
quels événements ont pesé
dans quel domaine
avec quelle certitude
```

## 5. La confiance doit être divisée

Nous conservons les domaines proposés :

```text
benevolence
honesty_integrity
reliability
competence
discretion
boundary_respect
predictability
```

Mais il faut désormais distinguer trois objets :

```text
TrustworthinessBelief
→ A croit que B possède une certaine qualité

SituationalTrust
→ A accepte une vulnérabilité précise envers B

TrustBehavior
→ A agit effectivement de manière vulnérable
```

Exemple :

```text
A croit B honnête.
A doute de sa compétence médicale.
A lui confie un secret.
A refuse néanmoins qu’elle traite sa blessure.
```

La confiance est donc :

- directionnelle;
- ciblée;
- propre à un domaine;
- liée à un risque;
- dépendante de l’enjeu et des alternatives;
- distincte de l’affection.

## 6. Contrat de confiance située

```text
SituationalTrustAssessment
- trustor
- trustee
- vulnerable_action
- domain
- potential_loss
- reversibility
- trustee_access
- trustworthiness_beliefs
- relationship_history
- alternatives
- safeguards
- confidence
- willingness
```

Une confiance générale peut servir de prior, mais ne remplace pas l’évaluation de la situation.

```text
« Je lui fais confiance »
```

doit être traduisible en :

```text
« Je lui fais confiance pour quoi,
dans quelles conditions,
et avec quel risque? »
```

## 7. Intimité comme processus

L’intimité ne sera pas une jauge uniquement produite par la proximité ou la quantité de conversations.

Cycle :

```text
divulgation ou expression
→ réponse du partenaire
→ perception de compréhension
→ perception de validation
→ perception de soin
→ sécurité de vulnérabilité
→ intimité éventuellement accrue
```

```text
ResponsivenessEpisode
- discloser
- responder
- content_domain
- vulnerability
- response
- perceived_understanding
- perceived_validation
- perceived_care
- insensitivity
- confidence
- relational_effect
```

Une divulgation profonde suivie d’une réponse froide peut diminuer l’intimité. Une réponse attentive à une petite préoccupation peut l’augmenter.

## 8. Proximité actuelle, proximité désirée et écart

Chaque vue relationnelle peut conserver :

```text
ClosenessPreference
- relationship
- domain
- current_closeness
- desired_closeness
- tolerated_range
- discrepancy
- urgency
- context
```

Domaines possibles :

```text
émotionnel
physique
social
informationnel
quotidien
sexuel
décisionnel
```

Une relation peut être objectivement proche tout en étant vécue comme :

```text
pas assez proche
juste assez proche
trop proche
```

La proximité ne sera jamais automatiquement assimilée au bien-être.

## 9. Engagement relationnel décomposé

Le système antérieur séparait déjà plusieurs dimensions. Nous précisons :

```text
RelationshipCommitmentState
- continuity_desire
- maintenance_intention
- psychological_attachment
- satisfaction
- investments
- perceived_alternatives
- forecast_future_quality
- moral_or_role_obligation
- barriers_to_exit
- identity_integration
- confidence
```

Ces dimensions ne doivent pas être compressées dans un seul score.

Exemples :

```text
fort désir de continuité
+ satisfaction faible
+ investissements élevés

faible désir de continuité
+ forte obligation morale
+ alternatives faibles

satisfaction élevée
+ peu d’investissements
+ engagement encore fragile
```

Un engagement élevé ne prouve ni l’absence de coercition ni la santé de la relation.

## 10. Cadres relationnels composables

Les cadres suivants restent validés :

```text
communal_care
→ répondre aux besoins sans comptabilité immédiate

exchange_reciprocity
→ équilibrer contributions et retours

authority_ranking
→ organiser droits, responsabilités et déférence

equality_matching
→ rechercher une symétrie ou alternance

collaboration
→ coordonner des contributions vers un résultat partagé
```

Une relation peut combiner plusieurs cadres selon le domaine.

```text
soins
→ communal

dépenses
→ échange explicite

sécurité
→ autorité temporaire

tâches domestiques
→ égalité ou alternance
```

Les conflits peuvent venir d’un désaccord sur le cadre applicable, pas seulement d’un manque d’affection.

```text
A croit offrir librement.
B croit contracter une dette.
```

## 11. Pouvoir et dépendance

Le pouvoir n’est pas une propriété globale possédée par une personne.

```text
PowerRelation
- actor
- partner
- domain
- resource_control
- dependency
- alternatives
- exit_ability
- authority
- information_control
- sanction_capacity
- vulnerability
- perceived_power
- actual_power
```

Le système distingue :

```text
pouvoir de A
pouvoir de B
symétrie
asymétrie
pouvoir structurel
pouvoir perçu
```

Une personne puissante dans le domaine matériel peut être dépendante dans le domaine émotionnel.

Le propriétaire du vivarium possède une puissance structurelle considérable, sans que cela crée automatiquement :

- affection;
- confiance;
- légitimité;
- obéissance volontaire;
- consentement;
- intimité.

## 12. Effet relationnel d’une interaction

La chaîne reste :

```text
interaction canonique
→ perception
→ interprétation
→ attribution d’intention
→ signification personnelle
→ émotion
→ preuve relationnelle
→ mise à jour
```

Le même comportement peut donc produire des effets différents.

```text
La louve entre sans frapper.

Interprétation A :
urgence légitime
→ faible dommage

Interprétation B :
négligence
→ baisse de confiance aux limites

Interprétation C :
contrôle intentionnel
→ peur, colère et forte révision
```

Le moteur n’applique jamais directement :

```text
entered_without_knocking
→ affection -10
```

## 13. Diagnosticité, répétition et généralisation

L’impact dépend notamment de :

```text
enjeu
intention attribuée
certitude
surprise
violation d’attente
répétition
historique
vulnérabilité
valeurs concernées
coût produit
possibilité de réparation
```

Règles :

- plusieurs petites preuves cohérentes peuvent construire une attente;
- une violation hautement diagnostique peut modifier rapidement un domaine;
- une violation dans un domaine ne remet pas automatiquement tous les autres à zéro;
- la généralisation exige une justification;
- une preuve ambiguë conserve un poids faible ou conditionnel.

```text
Erreur de compétence
→ ne prouve pas automatiquement la malveillance.

Mensonge intentionnel
→ ne prouve pas automatiquement l’incompétence.
```

## 14. Habituation relationnelle et attentes

Les événements répétés ne doivent pas produire le même changement indéfiniment.

```text
première aide importante
→ preuve forte de bienveillance

centième aide routinière
→ confirmation plus faible,
  sauf coût ou enjeu particulier
```

Mais l’absence d’un comportement devenu attendu peut devenir elle-même diagnostique.

```text
elle répond toujours aux appels urgents
→ une absence inexpliquée devient saillante
```

Le système doit conserver :

```text
RelationshipExpectation
- owner
- target
- expected_behavior
- context
- confidence
- importance
- source
- violation_tolerance
```

## 15. Métaperceptions

```text
RelationshipMetaView
- subject
- target
- inferred_dimension
- inferred_value
- confidence
- evidence
- projection_influence
- last_revision
```

Le personnage peut être :

- correctement informé;
- biaisé vers le rejet;
- excessivement optimiste;
- précis globalement mais faux sur ce partenaire;
- conscient de son incertitude.

La métaperception ne doit pas recopier automatiquement l’état réel B→A.

Elle est mise à jour par :

- paroles;
- comportements;
- expressions;
- réactions;
- témoignages;
- attentes;
- projections depuis le modèle de soi;
- souvenirs.

## 16. Entretien et dégradation

Le moteur ne doit pas appliquer une décroissance universelle :

```text
affection -= time_without_contact
```

L’absence de contact peut signifier :

- distance normale;
- rupture d’une attente;
- indisponibilité connue;
- oubli;
- évitement;
- fin progressive de la relation;
- rien de particulier.

La dégradation vient plutôt de mécanismes identifiables :

```text
attentes non satisfaites
occasions manquées
désengagement
diminution d’investissement
expériences négatives
perte de connaissance mutuelle
changements de buts ou de rôles
nouveaux liens concurrents
```

Les relations familiales, amicales, professionnelles et romantiques ne possèdent pas la même dynamique de maintien.

## 17. Réparation relationnelle décomposée

Une réparation peut contenir :

```text
RepairProcess
- transgression
- reconnaissance du fait
- reconnaissance du dommage
- responsabilité
- explication
- regret
- excuse
- restitution
- changement promis
- changement observé
- sécurité restaurée
- confiance réévaluée
- contact repris
- statut
```

Il faut distinguer :

```text
apology_received
forgiveness
anger_reduced
avoidance_reduced
contact_resumed
reconciliation
trust_restored
role_restored
```

Une excuse peut être sincère et insuffisante. Le pardon peut exister sans reprise de relation. Le contact peut reprendre sans confiance. La confiance peut être partiellement restaurée dans un domaine et demeurer faible dans un autre.

## 18. Réparation par preuve future

Les paroles modifient :

- l’attribution d’intention;
- la responsabilité perçue;
- la valeur relationnelle;
- la confiance dans la compréhension du dommage.

Mais certains domaines nécessitent des comportements ultérieurs.

```text
promesse de respecter une limite
→ intention déclarée

limite respectée à plusieurs reprises
→ preuve comportementale

limite de nouveau franchie
→ échec de réparation
```

Le système ne ferme pas automatiquement un processus de réparation après une excuse.

## 19. Résidus relationnels

La liste antérieure est maintenue :

```text
grief
felt_debt
broken_promise
shared_secret
betrayal
targeted_gratitude
perceived_injustice
unanswered_issue
suspended_conflict
repair_need
```

Nous ajoutons :

```text
ambiguous_commitment
unacknowledged_harm
closeness_discrepancy
power_grievance
role_confusion
network_pressure
```

Un résidu peut rester actif même après le retour d’un état relationnel globalement positif.

## 20. Couche de réseau social

Une dyade n’existe pas isolément.

```text
SocialNetworkContext
- focal_relationship
- third_parties
- shared_groups
- approval_or_disapproval
- information_routes
- coalitions
- conflicting_loyalties
- reputation_effects
- structural_support
- structural_pressure
```

Le réseau peut affecter :

- les informations accessibles;
- la réputation;
- les alternatives;
- les coûts de rupture;
- les occasions d’interaction;
- la légitimité perçue;
- la confiance transférée;
- les alliances.

Mais aucun tiers ne modifie directement A→B sans un canal causal :

```text
témoignage
observation
pression
sanction
opportunité
rumeur
accord collectif
```

## 21. Relations collectives

Certaines propriétés appartiennent à un groupe, pas à une somme de dyades :

```text
GroupRelationshipState
- group_entity
- members
- shared_identity
- cohesion
- norms
- roles
- common_goals
- factions
- collective_history
- membership_security
```

Le foyer peut éventuellement devenir une entité collective.

Cependant :

```text
forte cohésion du groupe
≠ chaque dyade est proche

conflit A↔B
≠ groupe entièrement dissous
```

Cette couche sera légère dans le MVP, mais l’ontologie doit la permettre.

## 22. Dissolution et changement de rôle

La fin d’une relation n’efface pas son historique.

```text
RelationshipLifecycle
- emerging
- active
- strained
- distancing
- suspended
- transformed
- dissolved
- historical
```

Ces statuts sont descriptifs et peuvent différer selon les participantes.

Une relation romantique peut devenir une amitié; une colocataire peut partir tout en restant proche; un rôle peut cesser alors que l’affection persiste.

La dissolution canonique d’un accord ne met pas automatiquement toutes les dimensions psychologiques à zéro.

## 23. Relations et consentement

Règle absolue de conception :

```text
affection
confiance
engagement
intimité
désir
rôle
autorité
historique positif
```

ne constituent jamais un consentement actuel.

Le futur système de consentement pourra lire les états relationnels comme contexte, mais il devra obtenir et suivre une permission spécifique, actuelle et révocable.

Une forte relation peut augmenter la probabilité qu’une demande soit bienvenue. Elle ne permet pas au moteur de sauter l’étape.

## 24. Relations et secrets

Le futur système de secrets doit se connecter à :

```text
discretion_trust
shared_secret
confidentiality_agreement
boundary
commitment
network_route
metaperception
```

Un secret partagé peut :

- augmenter l’intimité;
- créer une dette;
- accroître une dépendance;
- produire une vulnérabilité;
- devenir un engagement;
- détériorer une autre relation.

Le système relationnel ne stocke pas lui-même tout le contenu secret. Il conserve ses effets et références.

## 25. Chat

Le chat utilise un sous-ensemble :

```text
familiarity
recognition
safety
attachment
proximity_preference
handling_tolerance
care_expectation
practical_trust
resource_association
play
fear
avoidance
```

Il peut aussi posséder :

```text
desired_distance
routine_expectation
specific_person_preference
repair through repeated safe behavior
```

Il n’emploie pas automatiquement :

- engagement moral abstrait;
- conception explicite d’une dyade;
- dette symbolique;
- réputation narrative;
- pardon verbal;
- cadre romantique.

## 26. Stockage révisé

```text
relationship_dyad
relationship_role
relationship_agreement

relationship_view
relationship_dimension
relationship_meta_view
relationship_expectation
closeness_preference

relationship_evidence
relationship_evidence_cluster
relationship_residue

trustworthiness_belief
situational_trust_assessment
trust_behavior

responsiveness_episode
relationship_commitment_state
power_relation
relational_frame

relationship_repair
relationship_repair_step
relationship_dissolution

social_network_context
relationship_third_party_link
group_relationship_state
```

## 27. Événements

```text
relationship_view_initialized
relationship_evidence_registered
relationship_dimension_updated
relationship_expectation_formed
relationship_expectation_violated

trustworthiness_updated
situational_trust_assessed
trust_behavior_observed

responsiveness_episode_recorded
intimacy_updated
closeness_discrepancy_detected

relationship_commitment_updated
power_relation_updated
relational_frame_inferred
relational_frame_conflict_detected

relationship_residue_created
relationship_repair_started
relationship_repair_step_completed
relationship_trust_partially_restored
relationship_repair_stalled
relationship_repair_resolved

relationship_role_changed
relationship_dissolution_started
relationship_transformed
relationship_dissolved

network_influence_registered
group_relationship_updated
```

## 28. Rôle du LLM

Le LLM peut :

- résumer une relation;
- proposer une attribution consciente;
- formuler un conflit relationnel;
- générer une demande de réparation;
- proposer une manière de communiquer une limite;
- produire un dossier relationnel compact;
- identifier une divergence probable de cadres.

Il ne peut pas :

```text
définir l’état réel de B→A depuis A
transformer une interaction en variation arbitraire
déclarer une confiance globale
déduire un consentement
fermer une réparation
accorder un pardon
supprimer un résidu
déclarer une relation dissoute
inventer un accord
transférer automatiquement une réputation
```

Le moteur fournit au LLM des raisons structurées, pas une trentaine de nombres sans contexte.

## 29. Tests obligatoires

```text
affection asymétrique
confiance forte dans un domaine et faible dans un autre
confiance déclarée sans comportement vulnérable
comportement vulnérable malgré faible confiance
divulgation suivie d’insensibilité
proximité trop élevée pour une participante
engagement élevé dans une relation insatisfaisante
cadres communal et échange en conflit
pouvoir matériel et dépendance émotionnelle inversés
violation de compétence sans généralisation à l’intégrité
excuse sans restauration de confiance
pardon sans réconciliation
contact repris sans sécurité restaurée
métaperception fausse
rumeur tierce avec source incertaine
groupe cohésif malgré conflit dyadique
dissolution de rôle avec affection persistante
forte relation sans consentement actuel
chat utilisant uniquement le sous-ensemble compatible
```

## 30. Verdict final

Le système antérieur est conservé.

Corrections ciblées :

```text
séparer trustworthiness, situational trust et trust behavior
faire de l’intimité un processus de divulgation et responsiveness
ajouter l’écart entre proximité actuelle et désirée
décomposer l’engagement
conserver plusieurs cadres relationnels simultanés
rendre le pouvoir directionnel, structurel et propre à un domaine
éviter toute décroissance relationnelle universelle
décomposer complètement la réparation
exiger des preuves futures pour certaines restaurations
ajouter la couche de réseau et de groupe
connecter consentement et secrets sans les absorber
```

**Statut : RELATIONS — VALIDÉ AVEC CORRECTIONS CIBLÉES ET EXTENSION DE RÉSEAU SOCIAL.**

## 31. Références principales consultées

- Reis et Shaver, modèle processuel de l’intimité.
- Laurenceau, Barrett et Pietromonaco, *Intimacy as an interpersonal process*.
- Canevello et Crocker, *Creating good relationships: responsiveness, relationship quality, and interpersonal goals*.
- Rusbult et Van Lange, *Interdependence, interaction, and relationships*.
- Le et al., *Communal motivation and well-being in interpersonal relationships: An integrative review and meta-analysis*.
- Rusbult, Investment Model; Rodrigues et Lopes, engagement moral.
- Colquitt, Scott et LePine, méta-analyse trust, trustworthiness et prise de risque.
- Overall et Hammond, *Power and Ideology in Close Relationships*.
- Kim et al., réparation des violations de compétence et d’intégrité.
- Ma et al., excuses, confiance perçue et émotions négatives.
- Hannon et al., confiance post-transgression et pardon.
- Carlson et al., métaprécision dyadique.
- Frost et al., écarts de proximité.
- Felmlee, réseaux sociaux et qualité relationnelle.
