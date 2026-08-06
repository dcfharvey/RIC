# Vivarium Social — Audit 09

## Persistance, journal d’événements, snapshots, sauvegardes et personnages réutilisables

**Version :** 0.1  
**Date :** 4 août 2026  
**Verdict :** VALIDÉ AVEC RESTRUCTURATION IMPORTANTE

## 1. Conclusion générale

La fondation initiale est bonne :

- SQLite comme stockage canonique local;
- moteur canonique seul autorisé à modifier le monde;
- journal append-only;
- état courant matérialisé;
- snapshots;
- séparation entre modèle réutilisable et instance;
- actifs lourds hors SQLite;
- prompts et réponses LLM séparés de la vérité canonique.

L’audit impose cependant une clarification stricte entre plusieurs mécanismes souvent appelés « sauvegarde » :

```text
journal canonique
≠ état courant
≠ projection dérivée
≠ snapshot de projection
≠ point de contrôle administratif
≠ copie de sécurité de la base
≠ export portable
≠ modèle réutilisable
≠ continuation complète d’un personnage
```

Le projet doit employer un modèle hybride et sélectif : journaliser les changements canoniquement significatifs, conserver des tables d’état courant efficaces, rendre les projections reconstructibles et ne pas tenter de transformer chaque microvariation calculable en événement durable.

## 2. Limite de l’event sourcing

L’event sourcing apporte un historique complet et la reconstruction d’état, mais il augmente fortement les coûts de conception, de migration, de requête, de test et d’évolution de schéma. Il ne doit donc pas être appliqué à tous les sous-systèmes par principe.

Décision :

```text
Domaines canoniques persistants
→ événements sémantiques + état courant transactionnel

Projections et index
→ reconstruisibles

États dérivables à faible coût
→ recalculés, non journalisés à chaque microvariation

Diagnostics LLM et techniques
→ stockage séparé avec rétention propre

Actifs lourds
→ fichiers externes référencés par identifiant et empreinte
```

Le journal conserve les faits utiles pour expliquer l’évolution du monde, pas chaque étape interne d’un calcul déterministe.

## 3. Événement, commande et proposition

```text
Command
→ demande de tenter une modification

LLMProposal
→ suggestion structurée non canonique

DomainEvent
→ fait canonique ayant effectivement eu lieu

ExternalSideEffect
→ envoi ou action hors de la transaction SQLite
```

Exemple :

```text
Commande :
déplacer character_1 vers la cuisine

Validation :
trajet disponible, mobilité suffisante

Événements :
movement_started
character_moved
movement_completed
```

Une commande refusée ne produit pas `character_moved`. Elle peut produire un événement de diagnostic ou de refus si ce refus est lui-même important.

Le LLM ne doit jamais être rejoué pour reconstruire l’état. Le moteur conserve la proposition structurée effectivement acceptée ou les effets canoniques qui en ont résulté.

## 4. Contrat d’un événement canonique

```text
CanonicalEvent
- world_id
- sequence
- event_id
- event_type
- event_schema_version
- canonical_occurred_at
- committed_at
- actor_entity_id éventuel
- source
- transaction_id
- correlation_id éventuel
- causation_event_id éventuel
- command_id éventuel
- payload structuré
- visibility_class
- reducer_contract_version
- integrity_metadata
```

Règles :

- `sequence` est strictement croissant dans un monde;
- `event_id` est globalement unique;
- l’événement est formulé au passé;
- le payload décrit un fait, pas une intention vague;
- la version du schéma est explicite;
- la causalité est traçable;
- les événements d’une même transition atomique partagent un `transaction_id`;
- aucun événement commis n’est modifié silencieusement.

## 5. Temps canonique et temps d’enregistrement

```text
canonical_occurred_at
→ moment où le fait est réputé avoir eu lieu dans l’univers

committed_at
→ moment où le moteur l’a durablement enregistré

sequence
→ ordre canonique de traitement dans le journal
```

Pour le MVP, les corrections rétroactives ne sont pas insérées au milieu du journal. Elles sont ajoutées comme nouveaux événements référençant ce qu’elles corrigent.

```text
canonical_fact_corrected
- target_event_id
- correction
- reason
- effective_policy
```

Une réécriture véritable du passé exige plus tard une branche ou une opération administrative spécialisée.

## 6. Atomicité de l’écriture

Une transition canonique doit écrire dans une seule transaction SQLite :

```text
vérification de version attendue
→ validation
→ mise à jour de l’état courant
→ insertion des événements
→ mise à jour des projections transactionnelles obligatoires
→ COMMIT
```

Soit tout est commis, soit rien ne l’est.

Les effets externes, comme un message Discord, ne peuvent pas faire partie du commit SQLite. Ils doivent passer par une file de sortie persistante :

```text
outbox_message
- message_id
- source_event_id
- destination
- payload
- status
- attempts
- next_attempt_at
- delivered_at
```

L’envoi est idempotent ou possède un registre de livraison afin d’éviter les doublons après un redémarrage.

## 7. État courant, journal et projections

```text
État courant
→ réponse efficace à « qu’est-ce qui est vrai maintenant? »

Journal canonique
→ réponse à « comment cet état a-t-il été produit? »

Projection
→ vue spécialisée calculée depuis les faits canoniques
```

Le moteur ne doit pas obliger les lectures normales à rejouer toute l’histoire.

Décision hybride :

- les événements sont l’autorité historique;
- les tables d’état courant sont l’autorité opérationnelle du présent;
- toute transition significative met les deux à jour atomiquement;
- des tests de reconstruction vérifient que les réducteurs reproduisent un état équivalent;
- une divergence est une erreur d’intégrité, pas un conflit à résoudre arbitrairement.

## 8. Ce qui mérite un événement

Journaliser lorsque le changement :

- modifie une vérité canonique persistante;
- explique une décision ou une conséquence future;
- crée, modifie ou termine une relation;
- affecte une ressource, un droit, une position ou une capacité;
- doit être mémorisable ou perceptible;
- est requis pour reconstruire l’état;
- est nécessaire à l’audit administratif.

Ne pas journaliser systématiquement :

- chaque lecture;
- chaque score intermédiaire;
- chaque candidat rejeté de faible importance;
- chaque microvariation dérivable;
- chaque token ou étape interne du LLM;
- les caches;
- les données temporaires sans conséquence.

Un événement peut résumer un intervalle déterministe :

```text
needs_materialized
- from_time
- to_time
- resulting_values
- rational_remainders
- rule_version
```

plutôt que produire un événement par seconde.

## 9. Déterminisme et sources de non-déterminisme

La reconstruction ne doit jamais dépendre d’un résultat externe disparu.

Sources à capturer :

```text
tirage pseudo-aléatoire
heure externe utilisée
entrée du propriétaire
message Discord reçu
réponse structurée acceptée du LLM
résultat d’un outil externe
ordre d’événements concurrents
version de règle lorsque nécessaire
```

Pour les tirages :

```text
random_decision
- generator_algorithm
- seed_scope
- draw_index
- sampled_value
- distribution_contract
```

Le journal peut conserver le résultat tiré plutôt que dépendre éternellement de l’implémentation exacte du générateur.

Pour le LLM :

```text
llm_interaction_record
- diagnostic_id
- model/provider
- prompt_contract_version
- input_context_digest
- structured_proposal
- validation_result
- accepted_portion
```

Seule la partie acceptée et ses effets deviennent canoniques. Le texte brut peut être conservé temporairement dans le magasin diagnostic.

## 10. Rejouabilité réaliste

Il faut distinguer trois niveaux :

```text
StateRecovery
→ reconstruire un état exploitable

SemanticReplay
→ reconstruire les mêmes faits et relations canoniques

BitwiseReplay
→ reproduire exactement chaque octet interne
```

Objectif du vivarium :

- `StateRecovery` obligatoire;
- `SemanticReplay` obligatoire pour les domaines canoniques;
- `BitwiseReplay` non requis entre versions arbitraires du logiciel.

Les anciennes décisions sociales ou sorties LLM ne doivent pas être recalculées avec un modèle plus récent. Leur résultat canonique est déjà inscrit.

## 11. Évolution du schéma des événements

Chaque type d’événement possède un contrat versionné.

Stratégie normale :

```text
ancien événement immuable
→ lecteur détecte sa version
→ upcaster produit une représentation courante en mémoire
→ réducteur courant l’applique
```

Tactiques admises :

- événement versionné;
- upcasting;
- migration copy-and-transform vers un nouveau journal;
- transformation exceptionnelle hors ligne avec traçabilité complète.

Tactiques interdites par défaut :

- modifier les anciens payloads en place sans trace;
- réutiliser le même numéro de version avec une autre signification;
- laisser le code deviner la forme d’un événement;
- supprimer un champ historique nécessaire à l’interprétation.

Les migrations lourdes créent une nouvelle génération de journal et un lien de provenance vers l’ancienne.

## 12. Versionnement des réducteurs et projections

```text
ProjectionDefinition
- projection_name
- schema_version
- reducer_version
- source_event_contracts
- rebuild_strategy
```

Une projection incompatible est :

- migrée;
- reconstruite;
- ou abandonnée puis régénérée.

Elle n’est jamais considérée comme historique irremplaçable.

Les tests doivent inclure :

- replay depuis zéro;
- replay depuis snapshot;
- anciens événements upcastés;
- doublons;
- événements inconnus;
- projections interrompues puis reprises;
- comparaison état courant / état rejoué.

## 13. Quatre objets distincts appelés « snapshot »

### Snapshot de projection

Cache de performance :

```text
ProjectionSnapshot
- world_id
- projection
- through_sequence
- projection_schema_version
- reducer_version
- state_blob
- checksum
- created_at
```

Il est supprimable et reconstruisible.

### Point de contrôle administratif

État nommé avant une opération risquée :

```text
AdministrativeCheckpoint
- checkpoint_id
- world_id
- through_sequence
- reason
- affected_entities
- state_package
- asset_manifest
- created_by
- created_at
```

Il sert à inspecter, comparer, créer une branche ou préparer une restauration explicite.

### Sauvegarde physique

Copie cohérente de la base et des actifs pour panne, corruption ou perte matérielle.

### Export portable

Paquet destiné au transfert, à l’archivage ou à l’import dans une autre installation.

Ces quatre objets ne sont pas interchangeables.

## 14. Une restauration n’efface pas l’histoire

Avant le commit d’une modification profonde :

```text
prepare
→ impact report
→ checkpoint
→ confirmation
→ transaction
```

Si la transaction échoue avant `COMMIT`, SQLite annule tout.

Après un commit réussi, « revenir en arrière » signifie l’une des opérations suivantes :

```text
compensation
→ appliquer de nouveaux événements qui restaurent certains états

reversion administrative
→ produire un nouvel état à partir d’un checkpoint avec événement explicite

branching
→ créer un nouveau monde depuis le checkpoint sans modifier l’original

disaster restore
→ remplacer physiquement une installation endommagée par une sauvegarde
```

Aucune restauration normale ne supprime silencieusement les événements déjà survenus.

## 15. Branches et univers dérivés

Une branche n’est pas nécessaire au MVP immédiat, mais l’architecture doit la permettre.

```text
WorldBranch
- child_world_id
- parent_world_id
- fork_sequence
- creation_reason
- checkpoint_id
- created_at
```

La branche reçoit :

- de nouvelles identités d’instance pour les objets créés après la bifurcation;
- des références de provenance vers les entités sources;
- son propre ordre d’événements;
- aucune fusion automatique vers le parent.

## 16. Sauvegardes SQLite

La sauvegarde d’une base active ne doit pas être une copie naïve du seul fichier `.db`, particulièrement en mode WAL.

Méthodes prévues :

- API de sauvegarde en ligne SQLite;
- `VACUUM INTO` pour une copie compacte;
- arrêt propre et copie de l’ensemble cohérent lorsque la procédure l’exige.

Une sauvegarde doit inclure :

```text
database.sqlite
external_assets/
manifest
schema_metadata
application_version
checksums
backup_created_at
```

Vérifications :

```text
PRAGMA integrity_check
PRAGMA foreign_key_check
validation des manifestes d’actifs
test périodique de restauration
```

Une sauvegarde non restaurée en test demeure une hypothèse de récupération, pas une preuve.

## 17. Version de la base et migrations

SQLite offre des champs applicatifs permettant d’identifier le fichier et de suivre une version gérée par l’application.

Le vivarium doit employer :

```text
PRAGMA application_id
PRAGMA user_version
```

Et une table plus détaillée :

```text
schema_migration
- migration_id
- from_version
- to_version
- checksum
- applied_at
- application_build
- status
```

Règles :

- migration dans une transaction lorsque possible;
- sauvegarde avant migration destructive;
- aucune diminution silencieuse de version;
- script idempotent ou état d’application explicite;
- validation post-migration;
- procédure de reprise documentée;
- compatibilité minimale déclarée dans les exports.

## 18. Intégrité et détection de corruption logique

La base doit vérifier :

- clés étrangères activées sur chaque connexion;
- contraintes `CHECK`;
- unicité des séquences;
- immutabilité des événements commis;
- cohérence entre tables d’état et événements;
- références d’actifs valides;
- sommes de contrôle pour exports, snapshots et sauvegardes;
- absence d’événements orphelins;
- continuité des versions d’agrégat.

Outils internes :

```text
verify_event_stream
rebuild_projection
compare_rebuilt_state
verify_assets
verify_export_package
verify_backup_restore
```

## 19. Confidentialité et rétention

Un journal append-only peut accumuler des informations privées et rendre la suppression difficile. Le système doit donc éviter d’y placer inutilement des textes bruts, prompts complets, secrets en clair ou informations diagnostiques volumineuses.

Séparation :

```text
CanonicalStore
→ faits minimaux nécessaires au monde

DiagnosticStore
→ prompts, réponses brutes, traces techniques

AssetStore
→ médias et fichiers

SecretPayloadStore
→ contenu sensible chiffré ou à visibilité restreinte, si requis
```

Le magasin diagnostic possède une politique configurable :

- rétention courte;
- compression;
- archivage;
- purge;
- conservation manuelle d’un cas;
- redaction d’informations sensibles.

La suppression d’un contenu canonique sensible doit utiliser une politique explicite : chiffrement avec destruction de clé, payload externalisé remplaçable, ou migration auditée. « Append-only » ne doit pas être interprété comme obligation de conserver éternellement tous les octets.

## 20. Modèle de personnage et instance

```text
CharacterTemplate
→ définition initiale réutilisable

CharacterTemplateVersion
→ version immuable publiée de cette définition

CharacterInstance
→ identité canonique créée dans un univers

Incarnation
→ présence particulière de cette identité dans cet univers
```

Une instance reçoit toujours un nouvel `entity_id`.

Le modèle contient :

- identité de référence et noms par défaut;
- apparence initiale;
- type et morphologie;
- composants;
- besoins et régulations;
- perception;
- capacités;
- cognition;
- personnalité et valeurs initiales;
- style de communication;
- préférences initiales;
- actifs nécessaires;
- variantes configurables;
- éventuels rôles ou objets initiaux demandés.

Il ne contient pas automatiquement :

- souvenirs acquis;
- relations développées;
- blessures actuelles;
- humeur;
- position;
- croyances apprises;
- engagements en cours;
- historique de l’ancienne instance;
- secrets d’un autre univers.

## 21. Publication et version des modèles

Un modèle éditable possède un état `draft`.

Une version publiée devient immuable :

```text
CharacterTemplateVersion
- template_id
- version
- schema_version
- parent_version éventuelle
- resolved_definition
- asset_manifest
- validation_report
- created_at
- published_at
```

Modifier un modèle publié crée une nouvelle version.

Une instance conserve :

```text
source_template_id
source_template_version
resolved_initial_definition
instantiated_at
```

La définition résolue est conservée afin qu’une modification future du modèle ne transforme pas silencieusement les personnages existants.

## 22. Variantes et héritage

Les variantes peuvent utiliser :

```text
base_template
+ overlays déclaratifs
+ paramètres
→ resolved_definition
```

Exemple :

```text
base : louve anthropomorphe
overlay : palette grise
overlay : perception olfactive avancée
paramètre : taille 178 cm
```

À l’instanciation, le moteur :

1. résout les dépendances;
2. applique les overlays dans un ordre explicite;
3. détecte les conflits;
4. valide contre l’univers;
5. produit une définition concrète figée;
6. conserve la provenance de chaque propriété.

L’instance ne dépend pas dynamiquement d’une chaîne de modèles mutable.

## 23. Mise à jour d’une instance depuis un modèle

Aucune propagation automatique.

Une mise à jour ultérieure suit :

```text
sélectionner nouvelle version
→ calculer diff
→ classer les changements
→ produire rapport d’impact
→ choisir les changements applicables
→ checkpoint
→ confirmation
→ transaction
→ événements de migration
```

Catégories :

```text
cosmétique
descriptif
mécanique compatible
mécanique avec conversion
identitaire sensible
incompatible avec l’univers
```

Une nouvelle couleur par défaut peut être proposée; une nouvelle anatomie, cognition ou règle de continuité exige une migration beaucoup plus stricte.

## 24. Trois formats d’export de personnage

### Modèle réutilisable

```text
template_export
```

Définition initiale, variantes et actifs. Aucun vécu.

### État instantané d’instance

```text
instance_snapshot_export
```

Identité, état courant et références nécessaires à une reprise contrôlée, sans nécessairement inclure l’histoire complète.

### Continuation complète

```text
instance_continuation_export
```

État, histoire sélectionnée ou complète, souvenirs, croyances, relations, engagements, provenance et actifs.

L’import doit annoncer clairement s’il crée :

- une nouvelle instance inspirée du modèle;
- une copie dérivée;
- une continuation déclarée;
- une branche du même monde.

L’ontologie d’identité validée à l’audit 08 décide la relation, pas le fichier lui-même.

## 25. Paquet d’export portable

Structure suggérée :

```text
manifest.json
schema/
data/
events/
snapshots/
assets/
provenance/
checksums/
```

Le manifeste contient :

```text
package_type
package_version
minimum_engine_version
schema_versions
source_world
source_sequence
template_or_entity_ids
included_history_scope
identity_semantics
asset_index
checksums
created_at
provenance
```

Les sommes de contrôle détectent les fichiers absents ou modifiés.

Un import s’effectue d’abord en zone de préparation :

```text
unpack
→ verify checksums
→ validate schemas
→ inspect identity semantics
→ resolve conflicts
→ impact report
→ confirm
→ transactional import
```

## 26. Actifs externes

Les images, audio et médias lourds restent hors SQLite.

```text
AssetRecord
- asset_id
- content_hash
- media_type
- byte_size
- relative_path
- created_at
- source
- license_or_usage_notes
- visibility
- status
```

Les références canoniques utilisent `asset_id`, jamais un chemin absolu fragile.

Deux fichiers identiques peuvent partager un même contenu sans partager nécessairement la même signification logique.

La suppression physique d’un actif exige qu’aucune référence vivante, sauvegarde requise ou politique de conservation ne le retienne.

## 27. Raw LLM et diagnostics

Les prompts et réponses brutes ne sont pas la mémoire du personnage ni le journal canonique.

Ils servent à :

- diagnostiquer une décision;
- comparer des modèles;
- reproduire un incident;
- évaluer les coûts;
- améliorer les contrats.

```text
LLMDiagnosticRecord
- interaction_id
- world_id
- related_event_ids
- model
- provider
- parameters
- prompt_contract_version
- context_digest
- raw_input_ref
- raw_output_ref
- structured_output
- validation_errors
- accepted_fields
- token_usage
- retention_class
```

Ils peuvent être purgés sans supprimer les événements canoniques qui en ont résulté.

## 28. Structures principales

```text
canonical_event
event_type_registry
event_upcaster_registry
event_transaction
aggregate_version

projection_definition
projection_checkpoint
projection_rebuild

administrative_checkpoint
world_branch

backup_record
backup_manifest
schema_migration

character_template
character_template_version
template_overlay
template_dependency
character_instance_origin
instance_template_migration

asset
asset_reference
export_package
import_session

llm_diagnostic_record
outbox_message
delivery_record
```

## 29. Validateurs et tests

```text
EventContractValidator
EventSequenceValidator
ReplayValidator
ProjectionConsistencyValidator
SnapshotCompatibilityValidator
MigrationValidator
BackupValidator
RestoreValidator
TemplateResolutionValidator
InstanceIsolationValidator
ExportPackageValidator
AssetIntegrityValidator
DiagnosticRetentionValidator
```

Tests obligatoires :

- crash avant commit;
- crash après commit avant envoi Discord;
- redémarrage avec messages outbox;
- replay complet;
- replay depuis snapshot;
- snapshot obsolète;
- ancien événement upcasté;
- migration interrompue;
- import corrompu;
- actif manquant;
- duplication d’un message;
- mise à jour de modèle sans propagation silencieuse;
- restauration d’une sauvegarde sur environnement vierge.

## 30. Rôle du LLM

Le LLM peut proposer :

- le contenu initial d’un modèle;
- une variante;
- une description;
- une migration narrative;
- une classification préliminaire des différences;
- un résumé d’historique;
- une sélection de souvenirs pour un export.

Il ne peut pas :

- écrire directement dans la base;
- inventer un événement déjà survenu;
- modifier un événement commis;
- choisir la sémantique d’identité d’un import;
- appliquer une migration;
- déclarer une sauvegarde valide;
- décider qu’un snapshot remplace le journal;
- inclure implicitement le vécu d’une instance dans un modèle;
- propager une modification vers des instances existantes;
- supprimer les diagnostics ou actifs sans politique.

## 31. Verdict final

La conception initiale est maintenue sur ses fondations, mais réorganisée autour de séparations strictes :

```text
événement
≠ commande
≠ proposition LLM

histoire
≠ état courant
≠ projection

snapshot
≠ checkpoint
≠ backup
≠ export

template
≠ version publiée
≠ instance
≠ continuation

canonique
≠ diagnostic
≠ actif externe
```

**Statut : PERSISTANCE, SNAPSHOTS ET PERSONNAGES RÉUTILISABLES — VALIDÉ AVEC RESTRUCTURATION IMPORTANTE.**

## 32. Références principales consultées

- Microsoft Azure Architecture Center, *Event Sourcing pattern*.
- Overeem et al., *An Empirical Characterization of Event Sourced Systems and Their Schema Evolution — Lessons from Industry*.
- W3C, *PROV-O: The PROV Ontology*.
- SQLite, *Online Backup API*, *Write-Ahead Logging*, *PRAGMA* et documentation des clés étrangères.
- RFC 8493, *The BagIt File Packaging Format (V1.0)*.
- Fowler, Galpin et Cheney, *Language-Integrated Query for Temporal Data*.
