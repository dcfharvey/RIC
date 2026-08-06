# Vivarium Social — Audit 10

## Interface administrative, registre de composants et capacités, validation et changements contrôlés

**Version :** 0.1  
**Date :** 4 août 2026  
**Verdict :** VALIDÉ AVEC RESTRUCTURATION IMPORTANTE

## 1. Conclusion générale

La fondation initiale est validée :

- Discord demeure la fenêtre sociale;
- une interface web locale constitue l’atelier administratif;
- l’interface ne modifie jamais directement SQLite;
- une API canonique prépare, valide et applique les changements;
- les composants et capacités sont décrits par des contrats;
- les modifications profondes exigent un rapport d’impact, une confirmation, une transaction et un audit;
- les formulaires peuvent être partiellement générés depuis les schémas.

L’audit impose cependant une séparation stricte entre plusieurs notions :

```text
interface
≠ autorité canonique

schéma structurel
≠ invariant sémantique
≠ compatibilité avec un univers
≠ autorisation

validation
≠ rapport d’impact
≠ confirmation
≠ exécution

définition de composant
≠ instance de composant
≠ état dérivé
≠ présentation dans l’interface

avertissement
≠ erreur bloquante
≠ décision du propriétaire
```

La correction centrale est la suivante :

> L’interface administrative doit être un client inspectable d’un service canonique de changement. Elle ne doit contenir ni raccourci caché vers la base, ni logique d’autorité différente de celle utilisée par les commandes, scripts, imports ou futurs outils.

## 2. Architecture administrative révisée

```text
Interface web locale
→ API administrative documentée
→ Service de commandes
→ Préparateur de changement
→ Registre de contrats
→ Validateurs
→ Analyse d’impact
→ Confirmation liée à un plan précis
→ Moteur canonique
→ Transaction SQLite
→ Événements + état courant + outbox
```

Aucune couche située avant le moteur canonique ne peut déclarer un changement accompli.

L’interface peut :

- créer des brouillons;
- afficher les contrats;
- envoyer des commandes;
- présenter les rapports;
- demander une confirmation;
- afficher les résultats.

Elle ne peut pas :

- écrire une table;
- forcer un statut;
- ignorer un validateur;
- fabriquer un événement;
- changer une capacité dérivée;
- déclarer qu’une migration a réussi.

## 3. API canonique plutôt que CRUD direct

Un CRUD générique est acceptable pour certains brouillons sans conséquence, mais les changements canoniques sensibles doivent employer des commandes métier.

```text
Mauvais :
PATCH /characters/123
{ "identity": ..., "body": ..., "memories": ... }

Bon :
POST /changes/prepare
{
  "command_type": "revise_character_definition",
  "target": "entity_123",
  "requested_changes": ...
}
```

Les commandes expriment l’intention administrative :

```text
create_universe
create_entity_draft
activate_entity
revise_character_definition
assign_role
change_world_rule
archive_entity
restore_entity
instantiate_template
migrate_instance_from_template
import_package
```

Cette approche évite de traiter comme équivalentes des modifications dont les conséquences sont radicalement différentes.

## 4. Contrat de l’API

L’API doit être décrite par une spécification OpenAPI 3.1 ou ultérieure compatible avec le dialecte JSON Schema retenu.

```text
AdminAPIContract
- api_version
- endpoints
- command_schemas
- response_schemas
- authentication
- authorization_scopes
- concurrency_contract
- error_contract
- deprecation_policy
```

Principes :

- schémas d’entrée et de sortie explicites;
- types d’erreurs stables;
- version de contrat déclarée;
- documentation générable;
- tests de conformité entre l’implémentation et le contrat;
- aucune réponse importante uniquement sous forme de texte libre.

## 5. Registre de composants

Un registre n’est pas seulement une liste de noms. Chaque définition publiée devient un contrat versionné et immuable.

```text
ComponentDefinition
- component_type
- version
- lifecycle_status
- title
- description
- structural_schema
- semantic_contracts
- dependencies
- incompatibilities
- owned_fields
- derived_fields
- canonical_units
- defaults
- initialization_policy
- mutation_policy
- migration_contracts
- event_contracts
- validator_bindings
- ui_hints
- documentation
```

États :

```text
draft
validated
published
deprecated
retired
```

Une définition publiée n’est pas modifiée en place. Une évolution crée une nouvelle version.

## 6. Définition, instance et état dérivé

```text
ComponentDefinition
→ ce que signifie ce type de composant

ComponentInstance
→ données propres à une entité

DerivedComponentState
→ résultat calculé depuis plusieurs sources

ComponentView
→ présentation adaptée à l’interface
```

Exemple :

```text
Définition :
HydrationRegulation v1

Instance :
hydratation actuelle, réserve, reste rationnel

État dérivé :
cohésion estimée

Vue :
« Hydratation : 72 % »
```

L’interface ne doit pas permettre d’éditer directement un champ dérivé comme s’il constituait une donnée source.

## 7. Registre de capacités

```text
CapabilityDefinition
- capability_type
- version
- action_type
- required_components
- required_capabilities
- compatible_states
- target_contract
- parameter_schema
- canonical_costs
- risks
- effect_contract
- limit_contract
- execution_system
- validator_bindings
- event_contracts
- documentation
```

La définition décrit une capacité potentielle. Son activation actuelle reste une dérivation produite par le moteur.

```text
CapabilityDefinition
+ composants
+ forme
+ état
+ équipement
+ environnement
→ CapabilityDerivation
```

Le registre ne stocke pas manuellement `can_run = true` lorsque cette vérité peut être calculée.

## 8. JSON Schema : rôle et limite

JSON Schema convient pour :

- types;
- propriétés requises;
- structures conditionnelles;
- bornes numériques;
- formats;
- unions;
- métadonnées;
- références entre schémas;
- génération partielle de formulaires.

Il ne suffit pas à exprimer tout seul :

- cohérence entre plusieurs entités;
- contraintes temporelles;
- graphes de lieux;
- continuité d’identité;
- dépendances entre événements;
- autorisations;
- impact sur les relations et souvenirs;
- compatibilité complète avec les règles d’un univers.

Décision :

```text
JSON Schema
→ validation structurelle locale

Validateurs sémantiques
→ invariants du domaine

Validateurs de graphe
→ relations et dépendances

Validateurs temporels
→ intervalles et ordre

Validateurs de transition
→ légalité du changement d’état

Validateurs de monde
→ compatibilité avec le profil d’univers
```

Nous empruntons à SHACL l’idée de contraintes nommées appliquées à un graphe de données et de rapports de validation structurés, sans imposer RDF ou SHACL comme stockage du MVP.

## 9. Schémas de formulaire et schémas de données séparés

Le schéma canonique ne doit pas être contaminé par toutes les décisions visuelles.

```text
data_schema
→ sens et validité des données

ui_schema
→ ordre, groupes, widgets, aide, visibilité, présentation
```

Exemple :

```text
data_schema :
integer 0..100000, unité canonique

ui_schema :
curseur 0..100, afficher « % », groupe « Physiologie »
```

Les champs simples peuvent être générés automatiquement.

Les éditeurs complexes doivent recevoir des vues spécialisées :

- graphe des lieux;
- chronologie;
- relations;
- morphologie;
- dépendances de composants;
- capacités;
- comparaison de versions;
- rapport d’impact.

Un formulaire généré n’est pas une excuse pour exposer directement la structure interne de la base.

## 10. Unités, précision et présentation

Chaque grandeur mesurable doit déclarer :

```text
MeasureContract
- quantity_kind
- canonical_unit
- storage_scale
- allowed_display_units
- rounding_policy
- min
- max
- precision
```

Les unités utilisent des codes UCUM lorsque le domaine possède une unité physique standard.

```text
longueur
→ m

masse
→ kg

température
→ K en canon ou Cel selon contrat explicite

durée
→ s
```

Les échelles purement internes déclarent une unité arbitraire versionnée :

```text
vivarium:need-pressure/1
vivarium:relationship-confidence/1
```

Règles :

- la base conserve l’unité canonique;
- l’interface choisit l’unité d’affichage;
- toute conversion est centralisée;
- aucune valeur nue lorsque son unité est ambiguë;
- précision fixe et reste rationnel lorsque nécessaire;
- le changement d’unité visuelle ne modifie pas la valeur canonique.

## 11. Validation en couches

La validation devient un pipeline explicite.

```text
1. Parse
2. Validation structurelle
3. Validation référentielle
4. Validation sémantique locale
5. Validation inter-composants
6. Validation temporelle
7. Validation ontologique
8. Validation de capacité
9. Compatibilité avec l’univers
10. Autorisation administrative
11. Validation de transition
12. Analyse d’impact
13. Contrôle de concurrence
14. Validation des postconditions
```

### Parse

Le document est lisible et respecte l’encodage attendu.

### Structurelle

Les champs, types, bornes et variantes respectent JSON Schema.

### Référentielle

Les identifiants existent, les références ont le bon type et ne pointent pas vers une entité inaccessible lorsque cela est interdit.

### Sémantique locale

Le composant est cohérent avec lui-même.

### Inter-composants

Les composants requis existent; les incompatibilités et dépendances sont respectées.

### Temporelle

Les intervalles, transitions et ordres sont cohérents.

### Ontologique

L’identité, les corps, manifestations, rôles et parties respectent les règles validées à l’audit 08.

### Capacité

Les capacités déclarées ou demandées sont réellement dérivables.

### Monde

La configuration respecte les lois du profil d’univers.

### Autorisation

L’acteur administratif possède le droit d’effectuer cette opération et de modifier ces champs.

### Transition

Le changement est légal depuis l’état actuel.

### Impact

Les conséquences directes et dérivées sont calculées.

### Concurrence

Le plan est toujours fondé sur la même version canonique.

### Postconditions

Les invariants demeurent vrais après la simulation ou le commit.

## 12. Contrat d’un résultat de validation

```text
ValidationFinding
- code stable
- severity
- validator_id
- validator_version
- message_key
- human_message
- json_pointer éventuel
- target_entities
- related_contracts
- evidence
- expected
- observed
- remediation_hints
- suppressibility
```

Sévérités :

```text
BLOCKER
→ commit interdit

WARNING
→ commit possible seulement selon la politique de confirmation

INFO
→ information utile

DEFERRED_CHECK
→ vérification dépendant de l’exécution ou d’un système externe
```

Un avertissement n’est jamais une erreur que l’interface a arbitrairement décidé d’ignorer. Sa possibilité de suppression appartient au contrat du validateur et à la politique administrative.

## 13. Rapport machine et rapport humain

Le même résultat doit servir :

- à l’interface;
- aux tests;
- aux scripts;
- aux diagnostics;
- au propriétaire.

```text
ValidationReport
- conforms
- findings
- blocked_operations
- acknowledged_warnings
- validator_set_version
- evaluated_at
- based_on_world_version
```

L’API utilise un format d’erreur compatible avec `application/problem+json` et peut inclure des pointeurs précis vers les champs invalides.

L’interface traduit ensuite les codes en explications lisibles, sans modifier leur sens.

## 14. Préparer avant de confirmer

Une modification sensible suit :

```text
DraftCommand
→ normalize
→ validate
→ derive change set
→ simulate
→ compute dependency closure
→ impact report
→ checkpoint requirement
→ PreparedChange
```

```text
PreparedChange
- plan_id
- command_id
- normalized_command
- based_on_world_version
- target_versions
- change_set
- change_hash
- validation_report
- impact_report
- required_confirmations
- required_checkpoint
- expires_at
- status
```

Le plan préparé est immuable.

Modifier la commande crée un nouveau plan.

## 15. Changement explicite et diff

Le changement préparé doit être exprimé sous forme structurée.

Pour les documents JSON, JSON Patch peut être utilisé lorsque ses opérations représentent correctement la modification :

```text
add
remove
replace
move
copy
test
```

Pour les opérations métier, le moteur conserve aussi une représentation sémantique :

```text
SemanticChange
- operation_type
- subject
- property_or_relation
- before
- after
- justification
- consequences
```

Le propriétaire ne doit pas confirmer seulement une liste technique de chemins JSON. Il doit voir les effets métier.

## 16. Rapport d’impact

```text
ImpactReport
- direct_changes
- derived_changes
- affected_entities
- affected_components
- affected_capabilities
- affected_relations
- affected_roles
- affected_goals_or_commitments
- historical_consistency_effects
- identity_sensitive_effects
- asset_effects
- migrations
- irreversible_effects
- rollback_or_compensation_plan
- estimated_cost
- risk_level
- unknowns
```

Catégories de risque :

```text
LOW
→ cosmétique ou facilement réversible

MODERATE
→ effet mécanique local

HIGH
→ plusieurs systèmes, relations ou historiques affectés

CRITICAL
→ identité, continuité, suppression, import profond,
  changement de lois fondamentales
```

Un impact inconnu n’est pas traité comme nul.

## 17. Confirmation liée au contenu exact

La confirmation doit porter sur :

```text
plan_id
change_hash
based_on_world_version
warnings acknowledged
checkpoint_id éventuel
```

Pas sur un simple bouton « Oui » détaché du plan.

```text
ConfirmPreparedChange
- plan_id
- expected_change_hash
- expected_world_version
- acknowledged_findings
- confirmation_method
```

Le commit échoue si :

- le plan a expiré;
- le monde a changé;
- une cible a changé;
- le hash ne correspond plus;
- un nouveau bloqueur apparaît;
- le checkpoint requis n’existe pas.

## 18. Concurrence optimiste

Chaque ressource ou agrégat modifiable possède une version.

```text
world_version
entity_version
template_version
registry_version
```

Les lectures peuvent exposer un `ETag`. Les requêtes mutantes fournissent `If-Match` ou un champ équivalent.

```text
lecture :
ETag = "entity-123-v18"

préparation :
based_on = v18

entre-temps :
entité passe à v19

commit :
refus PRECONDITION_FAILED
→ nouvelle préparation obligatoire
```

Cela empêche qu’une ancienne page écrase silencieusement un changement plus récent.

## 19. Idempotence et reprise

Chaque commande mutante reçoit un `command_id` unique.

```text
CommandRecord
- command_id
- actor
- command_type
- payload_hash
- first_received_at
- status
- resulting_plan_id
- resulting_transaction_id
```

Si la même commande est reçue deux fois :

- même identifiant et même payload : retourner le résultat existant;
- même identifiant et payload différent : refuser;
- nouvel identifiant : nouvelle opération.

La confirmation et le commit possèdent également des identifiants uniques afin de tolérer un retry réseau sans appliquer deux fois la modification.

## 20. Autorisation et moindre privilège

Même avec un seul propriétaire au début, le service ne doit pas considérer que toute requête provenant de l’interface a automatiquement tous les droits.

Rôles minimaux possibles :

```text
viewer
editor
owner
diagnostic_operator
```

Les permissions portent sur :

```text
action
type de ressource
instance ciblée
propriété sensible
univers
niveau de risque
```

Exemples :

```text
viewer
→ lire l’état non secret

editor
→ créer et modifier des brouillons

owner
→ confirmer les changements canoniques profonds

diagnostic_operator
→ lire les traces techniques,
  sans modifier les personnages
```

Le MVP peut attribuer tous les rôles au même compte, tout en conservant les séparations dans le service.

## 21. Interface locale et sécurité

Configuration par défaut :

```text
écoute sur loopback seulement
aucune exposition réseau implicite
session administrative locale
origine unique
```

Une exposition au réseau exige explicitement :

- authentification;
- autorisation;
- TLS ou tunnel sécurisé;
- politique CORS restrictive;
- protection CSRF si des cookies authentifiés sont utilisés;
- limitation de débit;
- journal de sécurité;
- rotation ou révocation des sessions.

Les contrôles sont appliqués par l’API, pas uniquement par l’affichage des boutons.

## 22. Séparer trois journaux

```text
CanonicalEventLog
→ ce qui s’est produit dans l’univers

AdministrativeAuditLog
→ qui a demandé, préparé, confirmé ou refusé un changement

DiagnosticLog
→ détails techniques, erreurs, traces LLM et performance
```

Exemple :

```text
Canonical :
entity_form_changed

Administrative :
owner confirmed plan P-42,
hash H, based on world v311

Diagnostic :
validator capability-derivation v3 took 18 ms
```

L’audit administratif ne doit pas être visible comme un souvenir pour les personnages, sauf si une action correspondante est perceptible dans leur monde.

## 23. Interface administrative minimale

### Tableau de bord

- état du monde;
- horloge;
- activité;
- erreurs;
- changements en attente;
- sauvegarde récente;
- santé des projections et de l’outbox.

### Univers

- règles;
- temps;
- mortalité;
- population;
- lois physiques et sociales;
- compatibilité;
- versions.

### Lieux et environnement

- lieux;
- graphe;
- accès;
- objets;
- ressources;
- propriétés;
- validation de chemin.

### Entités

- identité;
- type;
- corps;
- composants;
- formes;
- capacités dérivées;
- état courant;
- validation;
- historique;
- archive.

### Modèles

- brouillons;
- versions;
- variantes;
- dépendances;
- instanciation;
- comparaison et migration.

### Registres

- composants;
- capacités;
- schémas;
- unités;
- versions;
- dépréciations;
- validateurs.

### Changements

- brouillons;
- plans préparés;
- diffs;
- rapports d’impact;
- confirmations;
- transactions;
- compensations.

### Diagnostic

- événements;
- projections;
- outbox;
- LLM;
- backups;
- imports;
- vérifications d’intégrité.

## 24. Création d’une entité par les vrais outils du MVP

```text
1. Créer un brouillon
2. Choisir un type ou modèle
3. Attacher les composants requis
4. Compléter les propriétés
5. Résoudre les capacités
6. Valider la structure
7. Valider la cohérence interne
8. Valider contre l’univers
9. Prévisualiser l’identité, le corps et les capacités
10. Préparer l’activation
11. Examiner le rapport d’impact
12. Confirmer
13. Créer l’identité, l’état et les événements
14. Afficher la fiche canonique
```

Les quatre personnages définitifs doivent être créés par ce processus ou migrés explicitement depuis les personnages techniques existants.

## 25. Création de l’univers et de la résidence

L’univers initial et la résidence doivent eux aussi être créés ou importés via le gestionnaire réel :

```text
WorldProfileDraft
EnvironmentDraft
LocationGraphDraft
ObjectAndResourceDrafts
RuleSetDraft
```

Puis :

```text
validation
→ préparation
→ rapport d’impact
→ activation
```

Les données seedées peuvent servir de fixture de développement, mais ne doivent pas devenir une voie administrative parallèle.

## 26. Modifications profondes d’un personnage

Une modification est dite profonde lorsqu’elle affecte notamment :

- identité;
- continuité;
- cognition;
- valeurs fondamentales;
- personnalité dispositionnelle;
- corps;
- capacités;
- mémoire;
- relations;
- règles physiologiques.

Flux obligatoire :

```text
sélectionner la cible
→ décrire la modification
→ calculer le diff
→ identifier les systèmes dépendants
→ simuler la migration
→ rapport d’impact
→ checkpoint
→ confirmation explicite
→ transaction
→ événements
→ validation post-commit
```

Le rapport doit expliquer :

- ce qui change;
- ce qui demeure;
- ce qui est recalculé;
- ce qui est converti;
- ce qui risque d’être perdu;
- ce que le personnage pourrait percevoir;
- les effets historiques et relationnels.

## 27. Archives et suppressions

Une entité référencée par l’histoire n’est normalement pas supprimée physiquement.

```text
archive
→ retire de l’usage actif tout en préservant les références

restore
→ réactive selon un plan validé

purge
→ opération exceptionnelle de données,
  distincte d’un événement du monde
```

L’interface doit employer le verbe exact. Un bouton « supprimer » ambigu est interdit pour les identités canoniques.

## 28. Dépréciation d’un contrat

Lorsqu’un composant ou une capacité est remplacé :

```text
published
→ deprecated
→ migration_available
→ retired_for_new_instances
```

Les instances existantes peuvent continuer d’utiliser l’ancienne version pendant une période déclarée.

Le registre doit indiquer :

- remplacement recommandé;
- compatibilité;
- migration disponible;
- date ou version de retrait;
- entités encore dépendantes;
- conséquences d’un maintien.

Une définition dépréciée ne disparaît pas tant que des événements ou instances historiques en dépendent.

## 29. Extension par modules

Un module futur doit déclarer :

```text
ModuleManifest
- module_id
- version
- engine_compatibility
- schemas
- components
- capabilities
- validators
- migrations
- events
- permissions
- ui_extensions
- dependencies
- conflicts
```

Installation :

```text
staging
→ signature ou provenance
→ validation
→ analyse de compatibilité
→ rapport d’impact
→ backup
→ confirmation
→ migration
→ tests post-installation
```

Le chargement arbitraire de code non validé n’est pas une fonction MVP.

## 30. Accessibilité et prévention des erreurs

L’interface vise au minimum les principes de WCAG 2.2 niveau AA lorsque raisonnablement applicable.

Exigences pratiques :

- navigation clavier;
- ordre de focus cohérent;
- labels explicites;
- erreurs liées aux champs;
- contrastes suffisants;
- information non transmise uniquement par couleur;
- cibles interactives utilisables;
- confirmation qui identifie clairement l’objet et les conséquences;
- conservation des entrées après une erreur;
- possibilité de revoir un diff avant commit.

Les opérations risquées ne doivent jamais dépendre d’un petit bouton adjacent à une action banale.

## 31. Tests obligatoires

### Contrats

- chaque schéma est lui-même valide;
- les exemples satisfont leur schéma;
- OpenAPI correspond au serveur;
- anciennes versions restent lisibles.

### Validateurs

- déterminisme;
- codes stables;
- chemins précis;
- validateurs en panne traités selon une politique `fail closed`;
- aucun warning ne devient blocker par hasard;
- aucun blocker ne peut être supprimé par l’interface.

### Préparation et confirmation

- plan expiré;
- hash incorrect;
- monde modifié;
- cible modifiée;
- warning non reconnu;
- checkpoint manquant;
- double confirmation;
- retry réseau.

### Autorisation

- accès à une autre entité;
- fonction interdite;
- champ sensible;
- élévation de rôle;
- endpoint non affiché mais appelé directement.

### Interface

- clavier;
- lecteurs d’écran essentiels;
- champs dynamiques;
- gros rapports;
- erreur réseau;
- reprise après redémarrage;
- langue et unités d’affichage.

### Intégrité

- transaction échouée;
- postcondition fausse;
- projection obsolète;
- événement créé sans changement d’état;
- changement d’état sans événement.

## 32. Rôle du LLM

Le LLM peut :

- proposer une définition de composant;
- proposer une configuration d’entité;
- expliquer un rapport;
- résumer un diff;
- suggérer des corrections;
- générer une description ou aide contextuelle;
- classer préliminairement un impact.

Il ne peut pas :

```text
publier un contrat
attribuer une version
définir seul une unité
attacher un composant
déclarer une capacité
modifier la sévérité d’un validateur
faire disparaître un blocker
confirmer un plan
autoriser une opération
produire un checkpoint
commettre une transaction
déclarer les postconditions satisfaites
```

Toute suggestion du LLM est marquée comme telle et renvoyée vers les mêmes contrats que les entrées humaines.

## 33. Application immédiate au MVP

Ordre technique recommandé :

```text
1. Registre minimal des contrats
2. Validateur structurel
3. Validateurs sémantiques requis par les quatre profils
4. API de brouillon et lecture
5. API prepare / validate / impact
6. PreparedChange + hash + version
7. Confirmation + transaction
8. Journal administratif
9. Interface univers et résidence
10. Interface entités
11. Interface capacités dérivées
12. Interface logs et diagnostics
```

Portée étroite :

- seuls les composants nécessaires aux quatre entités;
- seuls les profils d’univers nécessaires à la résidence initiale;
- aucun constructeur ontologique universel complet;
- aucun marché de plugins;
- aucun éditeur visuel complexe non nécessaire;
- mais aucun raccourci qui contourne le pipeline canonique.

## 34. Structures principales

```text
component_definition
component_definition_version
capability_definition
capability_definition_version
schema_registry
unit_definition
validator_registry
validator_binding

admin_command
prepared_change
prepared_change_target
semantic_change
validation_report
validation_finding
impact_report
impact_item
confirmation_record

authorization_role
authorization_permission
admin_actor
admin_session

administrative_audit_event
api_contract_version
module_manifest
```

## 35. Verdict final

Notre architecture administrative était correctement orientée. Les corrections principales sont :

```text
faire de l’interface un client, jamais une autorité
utiliser des commandes métier
versionner les contrats publiés
séparer schéma structurel et invariants sémantiques
séparer données, état dérivé et présentation
normaliser les unités
valider en couches
produire des findings structurés et stables
préparer un plan immuable avant confirmation
lier la confirmation à un hash et une version
refuser les plans devenus obsolètes
calculer l’impact au-delà du diff technique
séparer journal canonique, audit administratif et diagnostic
appliquer l’autorisation côté serveur
prévoir accessibilité, reprise et tests de concurrence
faire créer l’univers et les personnages par les vrais outils du MVP
```

**Statut : INTERFACE ADMINISTRATIVE, REGISTRE DE COMPOSANTS ET VALIDATION — VALIDÉ AVEC RESTRUCTURATION IMPORTANTE.**

## 36. Références principales consultées

- JSON Schema Draft 2020-12, Core et Validation.
- OpenAPI Specification 3.1.
- W3C Shapes Constraint Language (SHACL).
- RFC 9110, HTTP Semantics.
- RFC 9457, Problem Details for HTTP APIs.
- RFC 6902, JSON Patch.
- Unified Code for Units of Measure (UCUM), version 2.2.
- NIST Role-Based Access Control Model.
- NIST SP 800-53, Least Privilege.
- OWASP API Security Top 10 et CSRF Prevention Cheat Sheet.
- W3C Web Content Accessibility Guidelines 2.2.
