# Vivarium Social — Audit 08

## Ontologie des entités, corps, formes et capacités

**Version :** 0.1  
**Date :** 4 août 2026  
**Verdict :** VALIDÉ AVEC RESTRUCTURATION MAJEURE

## 1. Conclusion générale

La direction initiale est solide : identité persistante, composition par composants, séparation du corps, de la forme et de la cognition, capacités déclaratives, absence de branchements rigides par espèce.

L'audit impose toutefois plusieurs corrections :

- distinguer le référent du monde, l'entité suivie et son enregistrement technique;
- séparer les objets persistants, les événements, les états, les relations et les rôles;
- faire d'« agent » une organisation fonctionnelle, non une espèce ni une identité fondamentale;
- distinguer identité, sujet cognitif, contrôleur, corps, manifestation, forme et présence;
- séparer type constitutif, phase temporaire, rôle relationnel et qualité;
- inférer les capacités depuis les composants et l'état;
- représenter les affordances comme relations situées entre acteur, action, cible et environnement;
- séparer capacité, compétence, possibilité actuelle, permission et autorisation;
- traiter les copies, transformations, séparations et fusions par des transitions d'identité explicites;
- séparer plusieurs axes de cycle de vie au lieu d'une seule liste de statuts;
- conserver les relations temporelles et les raisons de chaque dérivation.

## 2. Couches ontologiques

```text
WorldReferent
→ toute chose, propriété, événement ou relation représentable

TrackedEntity
→ référent possédant une identité canonique et un historique propres

EntityRecord
→ représentation technique persistante de cette identité

Event / Activity
→ occurrence dans le temps produisant ou utilisant des entités

State / Quality
→ manière dont une entité est à un moment donné

Relation / Role
→ lien contingent entre entités, souvent limité dans le temps
```

Une propriété banale ne devient pas automatiquement une entité suivie. Elle est promue lorsqu'elle doit être référencée, ciblée, possédée, transformée, historisée ou dotée d'un cycle de vie propre.

## 3. Identité, type, phase, rôle et qualité

```text
ConstitutiveType
→ catégorie fournissant les contraintes d'identité et la structure de base

Phase
→ état temporaire dépendant de propriétés internes

Role
→ statut temporaire dépendant d'une relation ou d'un contexte social

Quality
→ propriété mesurable ou descriptive portée par une entité
```

Exemples :

```text
Type constitutif :
slime sapiente

Phase :
déshydratée

Rôle :
colocataire

Qualité :
cohésion = 58 000
```

Un changement de phase ou de rôle ne crée pas une nouvelle identité.

## 4. Décomposition fonctionnelle de l'agent

```text
Agent
→ système persistant capable de participer à une boucle perception-décision-action

CognitiveSubject
→ propriétaire de croyances, souvenirs, émotions, objectifs et intentions

DecisionController
→ centre produisant ou arbitrant des intentions

Perceiver
→ support de canaux perceptifs

Actor / Actuator
→ support qui exécute une action dans le monde

SocialPerson
→ statut social ou juridique défini par l'univers
```

Ces catégories peuvent coïncider chez une humaine ordinaire, mais ne sont pas ontologiquement identiques.

## 5. Corps, incarnation, manifestation et forme

```text
Embodiment
→ support physique d'un agent

Manifestation
→ présence observable ou interface par laquelle une identité apparaît ou agit

FormConfiguration
→ organisation actuelle d'un corps ou d'une manifestation

AppearanceState
→ propriétés visuelles, sonores, olfactives ou tactiles présentées

ControllerAssignment
→ relation temporelle indiquant qui contrôle quoi et comment
```

Pour le MVP, chaque personnage possède normalement un seul corps actif. Le modèle peut néanmoins représenter plus tard la possession, les corps de remplacement, les projections, les avatars et les manifestations multiples sans confondre ces phénomènes avec l'identité.

## 6. Parties et composition

Les liens de composition doivent être typés :

```text
integral_part
detachable_part
material_portion
contained_entity
equipment
member_of_collective
```

Une griffe, un vêtement porté, de l'eau contenue dans le slime et une colocataire membre du foyer ne sont pas quatre instances de la même relation vague `has_part`.

## 7. Formes et transformations

Une transformation est un événement. Elle peut modifier :

- la configuration corporelle;
- les qualités;
- les canaux perceptifs;
- les capacités;
- l'apparence;
- les coûts physiologiques;
- les contraintes d'équipement.

Elle ne modifie l'identité que si une politique explicite de continuité l'établit.

Pour le slime :

```text
même identité
+ même corps continu
+ nouvelle configuration humanoïde
→ capacités de marche et de préhension potentiellement activées
```

## 8. Composants, systèmes et capacités

```text
Entity
→ identité technique stable

Component
→ données structurées attachées à l'entité

System
→ logique qui lit et transforme les composants

Capability
→ classe d'action que l'entité peut potentiellement accomplir

EnabledCapability
→ capacité actuellement disponible compte tenu de l'état

Skill / Proficiency
→ qualité d'exécution apprise ou configurée

Affordance
→ possibilité située d'effectuer une action sur une cible dans un contexte

Permission / Authorization
→ droit ou accord permettant l'action
```

Formule conceptuelle :

```text
action_tentable
=
capacité activée
+ cible et environnement compatibles
+ préconditions satisfaites
+ règles canoniques respectées
```

L'autorisation sociale ou personnelle reste une vérification distincte.

## 9. Contrat de capacité

```text
CapabilityDefinition
- action_type
- composants porteurs
- capacités préalables
- états compatibles
- paramètres
- types de cibles
- portée
- coûts
- risques
- effets possibles
- limites
- systèmes d'exécution
```

```text
CapabilityDerivation
- entité
- capacité
- sources
- état courant
- équipement
- environnement
- raison d'activation ou de désactivation
- intervalle de validité
```

La provenance de la capacité doit être inspectable.

## 10. Affordance située

```text
AffordanceCandidate
- acteur
- action
- cible
- contexte
- capacité utilisée
- disposition de la cible
- propriétés environnementales
- paramètres possibles
- confiance
- préconditions manquantes
```

Un verre n'est pas simplement « saisissable ». Il l'est relativement à une entité possédant une méthode de préhension appropriée, à une distance accessible, sans obstacle incompatible et dans un état physique suffisant.

## 11. Suppression des branchements par espèce

Les espèces et types servent à :

- instancier des configurations initiales;
- fournir des valeurs par défaut;
- valider certaines compositions;
- soutenir les descriptions et connaissances taxonomiques.

Les systèmes d'exécution interrogent plutôt :

```text
composants
capacités
état
forme
relations
contexte
```

L'odorat amélioré vient d'un composant perceptif; la digitigradie d'une morphologie; la thermotolérance d'une régulation corporelle. Aucun système général ne doit contenir `if species == wolf`.

## 12. Continuité d'identité

Un identifiant stable représente une décision canonique de suivi; il ne résout pas à lui seul toutes les questions métaphysiques.

```text
IdentityTransition
- événement
- entités sources
- entités résultantes
- type :
    transformation
    replacement
    copy
    split
    fusion
    reconstitution
- continuité déclarée
- règle d'univers appliquée
- corps conservés ou remplacés
- mémoires héritées
- contrôleurs hérités
- relations héritées
- provenance
```

Règles MVP :

- changement de forme : même identité;
- blessure ou guérison : même identité;
- copie parfaite : nouvelle identité dérivée;
- fragmentation autonome, fusion et remplacement complet : non disponibles dans le scénario initial;
- aucune transition complexe n'est implicite.

## 13. Localisation et présence

La position appartient d'abord aux corps et manifestations physiques, non à l'identité abstraite.

```text
Identity
→ peut avoir un ou plusieurs supports

Embodiment / Manifestation
→ possède une localisation

EffectivePresence
→ dérivée des supports, canaux et relations de contrôle
```

Cela permet de distinguer :

- être physiquement présent;
- percevoir à distance;
- agir à distance;
- apparaître par projection;
- posséder une autorité sans être perceptible.

## 14. Rôles et autorités

Les statuts suivants doivent être des relations temporelles :

```text
roommate
owner
guest
patient
caregiver
participant
leader
guardian
```

L'autorité est une relation possédant :

- une source;
- une cible ou un domaine;
- une portée;
- des pouvoirs précis;
- des limites;
- une durée;
- une provenance.

Le rôle de propriétaire ne confère pas magiquement toutes les capacités et ne garantit ni obéissance ni affection.

## 15. Cycles de vie séparés

L'ancienne liste mélangeait plusieurs dimensions. Le modèle révisé sépare :

```text
DefinitionLifecycle
draft
validated
deprecated

WorldExistenceState
prepared
active
inactive
destroyed

AccessibilityState
accessible
inaccessible

WorldMembership
resident
visitor
departed

PersistenceState
live
archived
restored
```

Une entité peut donc être active dans le monde, temporairement inaccessible et jamais archivée.

## 16. Relations temporelles

Les relations susceptibles de changer doivent posséder une validité :

```text
TemporalRelation
- subject
- predicate
- object
- valid_from
- valid_to
- asserted_by_event
- ended_by_event
```

Cela concerne notamment la localisation, le contrôle, l'incarnation, les rôles, la propriété, l'appartenance et la composition détachable.

## 17. Niveaux de suivi

```text
Niveau 0 — propriété de fond
aucune identité individuelle

Niveau 1 — composant
état structuré d'une entité

Niveau 2 — sous-entité suivie
identité propre, mais présentée comme partie ou support

Niveau 3 — entité autonome
cycle de vie et historique complets

Niveau 4 — collectif ou agrégat
identité du groupe distincte de ses membres
```

Promotion recommandée lorsqu'un élément devient individuellement nommé, possédé, ciblé, transformé, mémorisé, impliqué dans une relation ou doté d'un historique propre.

## 18. Structures principales

```text
canonical_entity
entity_type_assignment
entity_component
entity_quality
entity_phase
temporal_relation

embodiment
manifestation
form_configuration
appearance_state
controller_assignment
part_relation

role_assignment
authority_relation

capability_definition
capability_requirement
capability_derivation
skill_state
affordance_candidate

identity_transition
lineage_relation
world_membership
```

L'implémentation peut rester relationnelle et auditée dans SQLite. La composition est inspirée de l'ECS, sans imposer immédiatement un moteur ECS archétypal en mémoire.

## 19. Validateurs

```text
IdentityValidator
ComponentContractValidator
ComponentDependencyValidator
TemporalRelationValidator
PartWholeValidator
EmbodimentValidator
ControllerValidator
CapabilityDerivationValidator
AffordanceValidator
RoleAndAuthorityValidator
WorldCompatibilityValidator
IdentityTransitionValidator
```

Exemples de blocages :

- capacité déclarée sans composants nécessaires;
- relation temporelle impossible;
- deux contrôleurs exclusifs sur le même corps lorsque l'univers l'interdit;
- forme exigeant plus de masse que le corps n'en possède;
- action nécessitant une cognition non disponible;
- copie marquée comme la même identité sans politique explicite.

## 20. Application aux quatre profils

### Humaine

- une identité;
- un sujet cognitif;
- un corps actif;
- morphologie humaine stable;
- forme peu variable;
- capacités dérivées de la morphologie, de l'état, de l'équipement et des compétences.

### Louve anthropomorphe

- même structure générale;
- composants de fourrure, queue, oreilles mobiles, digitigradie, griffes et sens améliorés;
- langage corporel dérivé des canaux d'expression;
- aucune psychologie d'espèce imposée.

### Chat domestique

- entité et agent autonome;
- sujet cognitif non sapient;
- corps quadrupède;
- capacités, perception et décision adaptées;
- statut de personne sociale non supposé automatiquement.

### Slime sapiente

- une identité;
- un sujet cognitif;
- un corps continu;
- configuration morphologique variable;
- apparence féminine comme configuration volontaire;
- capacités dérivées de l'hydratation, de la cohésion, de la masse, de la forme et de l'effort;
- aucune duplication ou fragmentation autonome dans le MVP.

## 21. Événements

```text
entity_instantiated
entity_type_assigned
component_attached
component_detached
quality_materialized
phase_started
phase_ended
role_assigned
role_ended

embodiment_linked
embodiment_unlinked
manifestation_created
manifestation_ended
form_changed
controller_assigned
controller_released
part_relation_changed

capability_enabled
capability_disabled
affordance_detected
identity_transition_recorded
entity_archived
entity_restored
```

## 22. Rôle du LLM

Le LLM peut proposer :

- descriptions;
- configurations;
- formes plausibles;
- composants candidats;
- usages d'une capacité;
- interprétations sociales d'un rôle.

Il ne peut pas :

- créer ou fusionner une identité;
- décider qu'une copie est la même personne;
- attacher un composant;
- déclarer une capacité disponible;
- inventer un corps ou une manifestation;
- transférer le contrôle;
- contourner les validateurs;
- transformer une espèce en règle comportementale;
- exécuter une transition canonique.

## 23. Verdict final

La conception initiale est conservée sur ses principes, mais restructurée autour de distinctions plus strictes :

```text
identité
≠ enregistrement
≠ type
≠ phase
≠ rôle
≠ corps
≠ forme
≠ manifestation
≠ présence
≠ contrôleur
≠ capacité
≠ affordance
≠ permission
```

**Statut : ONTOLOGIE DES ENTITÉS, CORPS, FORMES ET CAPACITÉS — VALIDÉ AVEC RESTRUCTURATION MAJEURE.**
