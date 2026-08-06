# Vivarium Social — Exigences normatives consolidées après audit

**Version :** 0.1  
**Date :** 4 août 2026  
**Statut :** NORMATIF PROPOSÉ — approuvé comme direction de conception, à intégrer au dossier maître du dépôt  
**Portée :** architecture, cognition, persistance, administration et limites du LLM  
**Documents sources :** dix audits majeurs et trois contrôles de cohérence consignés dans `Vivarium_Registre_Audits_v0_8.md`

> Ce document transforme les conclusions des audits en règles vérifiables. Il ne prétend pas que ces fonctions sont déjà implémentées.

---

## 1. Règles de gouvernance

### GOV-001 — Revue préalable

Tout nouveau système psychologique, cognitif, social ou technique doit être précédé d’une consultation de la littérature scientifique ou technique appropriée.

### GOV-002 — Statut des connaissances

Chaque conception doit distinguer :

- résultats relativement établis;
- débats ou limites de la littérature;
- décisions d’ingénierie propres au vivarium;
- éléments différés.

### GOV-003 — Passage à l’opérationnel

Une conception n’est complète que lorsqu’elle définit :

- entrées;
- état;
- transitions;
- stockage;
- événements;
- intégrations;
- limites du LLM;
- portée MVP;
- tests.

### GOV-004 — Traçabilité

Chaque exigence implémentée doit pouvoir être reliée à :

- une décision;
- un contrat;
- un lot;
- des tests;
- un commit;
- une version de schéma.

---

## 2. Autorité et séparation des représentations

### ARC-011 — Autorité canonique unique

Le moteur local est l’unique autorité sur les faits du monde. Les interfaces, scripts, imports et LLM envoient des commandes ou propositions.

### ARC-012 — Chaîne subjective complète

```text
réalité canonique
≠ signal accessible
≠ perception
≠ interprétation
≠ hypothèse
≠ croyance
≠ encodage mnésique
≠ reconstruction
≠ récit conscient
```

Aucune couche subjective ne peut réécrire rétroactivement la réalité.

### ARC-013 — Provenance

Toute modification importante doit conserver sa cause, sa source, son contexte, sa version de règle et les entités concernées.

### ARC-014 — Impossibilité contre transgression

Le moteur doit distinguer :

- impossibilité physique ou canonique;
- précondition manquante mais obtenable;
- conflit personnel;
- transgression sociale;
- absence de permission.

Une norme ou valeur ne devient pas une loi physique.

---

## 3. Perception et attention

### COG-001 — Enregistrement préconscient

Le système doit pouvoir représenter un signal enregistré sans perception consciente complète.

### COG-002 — Détection faillible

La perception doit permettre :

- détection correcte;
- omission;
- fausse alerte;
- rejet correct.

### COG-003 — Charges distinctes

Le système ne doit pas réduire toute l’attention à une seule jauge. Il distingue au minimum :

- charge perceptive;
- charge de contrôle;
- charge cognitive;
- stabilité attentionnelle;
- niveau général d’éveil.

### COG-004 — Orientation et surveillance

Une agente peut orienter ouvertement ou discrètement son attention, surveiller une cible ou explorer.

### COG-005 — Habituation et vigilance

L’habituation est spécifique au stimulus et au contexte. La vigilance prolongée peut produire omissions et fausses alertes.

### COG-006 — Intégration multisensorielle

Les preuves sensorielles ne sont combinées que lorsque leur cause commune est plausible. La fiabilité, la précision, le délai et la localisation restent traçables.

---

## 4. Interprétation et croyances

### EPI-001 — Hypothèse distincte de la croyance

Une possibilité envisagée ne devient pas automatiquement une croyance adoptée.

### EPI-002 — Questions épistémiques

Les hypothèses concurrentes sont regroupées par question et incluent une possibilité résiduelle « autre ou inconnu ».

### EPI-003 — Provenance de la preuve

Une preuve conserve :

- contenu;
- polarité;
- diagnosticité;
- fiabilité de la source;
- confiance perceptive;
- pertinence causale;
- récence;
- dépendance avec d’autres preuves.

### EPI-004 — Modèle de source

Les agentes peuvent estimer séparément l’accès, la compétence, l’honnêteté, les intérêts et la fiabilité passée d’une source.

### EPI-005 — Confiances distinctes

Le moteur sépare :

- confiance épistémique;
- acceptation pratique;
- désirabilité;
- coût de révision.

### EPI-006 — Contradictions persistantes

Des croyances contradictoires peuvent coexister, être suspendues, restreintes à un contexte ou déclencher un objectif d’enquête.

### EPI-007 — Révisions traçables

Une correction ne supprime pas silencieusement l’ancienne croyance. Elle crée une révision, une relation de remplacement et éventuellement un résidu d’influence.

---

## 5. Régulation, besoins et motivation

### MOT-001 — Pas de réservoir psychologique universel

Le moteur distingue :

```text
variable régulée
signal de déficit ou de prévision
besoin psychologique
motif
désir conscient
objectif
```

### MOT-002 — Régulation prédictive

Les pressions physiologiques peuvent dépendre de l’état présent, de sa tendance, du plan de l’agente et des conditions anticipées.

### MOT-003 — Wanting, liking et apprentissage

Le désir incitatif, le plaisir anticipé, le plaisir réel et l’apprentissage de valeur sont des dimensions distinctes.

### MOT-004 — Besoins psychologiques généraux

Autonomie, compétence et relation à autrui servent de fondation générale. Leur satisfaction et leur frustration sont représentées séparément.

### MOT-005 — Socialité décomposée

Le moteur distingue :

- qualité du contact;
- personnes désirées;
- proximité désirée;
- proximité imposée;
- saturation;
- solitude;
- appartenance.

### MOT-006 — Sexualité contextuelle

La sexualité n’est pas une jauge périodique universelle. Elle dépend notamment de la réceptivité, de l’inhibition, des incitations, de l’attraction, du contexte, de la sécurité et du consentement.

### MOT-007 — Candidats motifs

Les motifs actifs sont des objets temporaires expliquant leur source, leur direction, leur cible, leur importance, leur urgence, leurs coûts et les actions possibles.

---

## 6. Personnalité et attachement

### PER-001 — Traits comme tendances

Les Big Five et leurs facettes modulent les mécanismes; ils ne commandent jamais directement une action.

### PER-002 — Distribution d’états

Un trait décrit une distribution relativement stable comprenant niveau moyen, variabilité, inertie et signatures situationnelles.

### PER-003 — Trois représentations

Le moteur sépare :

- disposition canonique;
- conception de soi;
- réputation attribuée par autrui.

### PER-004 — Changement lent

Un changement dispositionnel exige répétition, généralisation et stabilité. Une réaction unique ne modifie pas un trait.

### ATT-001 — Attachement dimensionnel

L’anxiété et l’évitement d’attachement sont distincts des Big Five et peuvent différer entre niveau général, domaine et relation particulière.

### ATT-002 — Activation contextuelle

L’attachement devient particulièrement pertinent sous vulnérabilité, douleur, séparation, besoin de soutien, rejet ou conflit.

### ATT-003 — Stratégies distinctes

Hyperactivation et désactivation produisent des stratégies, non des actions obligatoires.

---

## 7. Valeurs, principes, normes et limites

### VAL-001 — Catégories séparées

```text
valeur
≠ principe
≠ conviction morale
≠ préférence
≠ limite personnelle
≠ norme sociale
≠ loi
≠ règle physique
```

### VAL-002 — Priorités relatives

Les valeurs forment une hiérarchie relative; elles ne sont pas toutes des curseurs indépendants maximisables simultanément.

### VAL-003 — Principes contextuels

Un principe décrit une règle de conduite contextualisée, ses exceptions, sa rigidité, ses valeurs sources et ses attentes de réparation.

### VAL-004 — Moralisation distincte

Importance, centralité identitaire, certitude, universalisation et résistance au compromis sont des dimensions distinctes.

### BND-001 — Limite comme politique d’accès

Une limite régule l’accès au corps, à l’espace, au temps, à l’attention, à l’information, aux biens, aux relations ou aux décisions.

### BND-002 — Franchissement et violation

Le système distingue :

- franchissement canonique;
- perception d’une violation;
- intention attribuée;
- connaissance de la limite;
- urgence;
- conséquences.

### BND-003 — Permission non permanente

Un accord passé ne vaut pas permission universelle et permanente.

---

## 8. Objectifs, engagements et intentions

### GOAL-001 — Distinctions fondamentales

```text
motif
≠ candidat objectif
≠ objectif adopté
≠ engagement
≠ intention
≠ plan
≠ action
```

### GOAL-002 — Objectif structuré

Un objectif possède au minimum :

- état recherché ou évité;
- propriétaire;
- sources;
- horizon;
- critères de réussite;
- faisabilité perçue;
- importance;
- urgence;
- statut.

### GOAL-003 — Graphe de buts et moyens

Plusieurs moyens peuvent servir un objectif et une même action peut servir plusieurs objectifs.

### GOAL-004 — Faisabilité objective et subjective

Un objectif peut exister même s’il est objectivement impossible, tant que l’agente le croit réalisable. Les actions impossibles restent bloquées par le moteur.

### INT-001 — Intention stable par défaut

Une intention active se poursuit sans recalcul global tant qu’aucun déclencheur pertinent ne justifie sa révision.

### INT-002 — Reprise

Une intention interrompue conserve un contexte de reprise : étape, état des objets, lieu, participantes, raison et conditions de reprise.

### INT-003 — Intentions d’implémentation

Le système peut relier un signal futur à une action préparée, sans garantir que le signal sera remarqué ni que l’action demeurera appropriée.

### COM-001 — Engagement personnel distinct du social

La détermination envers son propre but et l’obligation envers autrui sont stockées séparément.

### COM-002 — Engagements conjoints

Les objectifs partagés conservent participantes, rôles, contributions, conditions de suspension et procédure de retrait.

---

## 9. Arbitrage décisionnel

### DEC-001 — Pas d’optimisation globale

La décision ne compare pas exhaustivement toutes les actions imaginables et ne repose pas sur un score opaque unique.

### DEC-002 — Contrôleurs multiples

Les options peuvent provenir de :

- continuité de l’intention;
- habitudes;
- objectifs;
- motifs;
- émotions;
- principes;
- engagements;
- relations;
- enquête.

### DEC-003 — Ensemble borné d’options

Seules quelques options pertinentes sont générées. Une option non récupérée ne peut pas être choisie.

### DEC-004 — Prédictions subjectives

Les conséquences sont anticipées depuis les croyances et modèles de l’agente, avec incertitude.

### DEC-005 — Profil multidimensionnel

Chaque option conserve ses soutiens, coûts, risques, effets relationnels, conflits normatifs, réversibilité et information attendue.

### DEC-006 — Critères non compensatoires

Certains critères agissent comme seuils ou veto. Un seuil psychologique reste violable; une impossibilité canonique ne l’est pas.

### DEC-007 — Métadécision

Le système choisit aussi combien réfléchir selon l’enjeu, l’urgence, l’incertitude, la réversibilité et le coût cognitif.

### DEC-008 — Modes décisionnels

Modes minimaux :

- continuation;
- routine;
- décision rapide;
- délibération;
- recherche d’information;
- négociation;
- report;
- inaction délibérée.

### DEC-009 — Suffisance

La recherche s’arrête lorsqu’une option est suffisamment acceptable ou que continuer ne vaut plus son coût.

### DEC-010 — Variabilité reproductible

La variabilité est bornée, seedée, journalisée et ne peut contourner les contraintes.

### DEC-011 — Choix distinct de l’exécution

Le résultat décisionnel produit une intention ou une option. Le moteur valide ensuite l’action au moment de l’exécution.

---

## 10. Mémoire

### MEM-001 — Encodage subjectif

L’enregistrement initial représente ce que l’agente a encodé, non une copie cachée de la vérité canonique.

### MEM-002 — Frontières externes et internes

Les épisodes peuvent être segmentés par changements de lieu, participantes, activité, objectif, intention, émotion ou compréhension.

### MEM-003 — Couches distinctes

Le système distingue au minimum :

- modèle de l’événement courant;
- enregistrement d’encodage;
- représentation épisodique;
- gist;
- détails;
- connaissances sémantisées;
- schémas;
- mémoire prospective;
- reconstruction récupérée.

### MEM-004 — Consolidation transformative

La consolidation peut renforcer, abstraire, relier, sémantiser ou affaiblir certains détails. Elle ne renforce pas uniformément chaque souvenir.

### MEM-005 — Récupération faillible

La récupération peut produire un souvenir précis, un gist, une familiarité, une substitution, une intrusion, une erreur de source ou un échec.

### MEM-006 — Dimensions distinctes

Accessibilité, précision, confiance, vivacité et confiance de source ne sont jamais fusionnées.

### MEM-007 — Mise à jour prudente

Une récupération ordinaire ne réécrit pas automatiquement la mémoire. Une nouveauté ou contradiction importante peut ouvrir une mise à jour traçable.

### MEM-008 — Oubli multicausal

L’oubli peut toucher l’accès, les détails, la source, le contexte ou la compétition sans suppression physique normale de l’historique.

### MEM-009 — Influence indirecte

Un épisode inaccessible peut continuer d’influencer une habitude, une croyance, une relation ou une réaction.

---

## 11. Relations

### REL-001 — Directionnalité

A→B est distinct de B→A. Les faits dyadiques, les vues et les métaperceptions sont stockés séparément.

### REL-002 — Preuve distincte de l’état

Les changements relationnels sont causaux, contextualisés et explicables depuis des preuves.

### REL-003 — Confiance décomposée

Le système distingue :

- croyance sur la fiabilité;
- confiance situationnelle;
- comportement vulnérable.

La confiance est propre à un domaine, un risque et un contexte.

### REL-004 — Intimité processuelle

L’intimité peut évoluer par divulgation, réponse, compréhension, validation, soin et sécurité de vulnérabilité.

### REL-005 — Proximité désirée

La proximité actuelle, la proximité désirée et la plage tolérée sont distinctes par domaine.

### REL-006 — Engagement décomposé

Désir de continuité, satisfaction, investissements, alternatives, obligation et barrières de sortie ne sont pas compressés dans une seule jauge.

### REL-007 — Cadres relationnels

Plusieurs cadres peuvent coexister :

- soin communal;
- échange;
- égalité;
- autorité;
- collaboration.

### REL-008 — Pouvoir relationnel

Le pouvoir et la dépendance sont directionnels, propres à un domaine et distincts de l’affection ou de la légitimité.

### REL-009 — Pas de décroissance universelle

Le temps sans contact ne diminue pas automatiquement l’affection. Toute dégradation exige un mécanisme interprétable.

### REL-010 — Réparation décomposée

Excuse, responsabilité, restitution, pardon, reprise du contact, réconciliation et restauration de confiance sont des états distincts.

### REL-011 — Réseau social

Les tiers et groupes peuvent influencer une relation seulement par des canaux causaux explicites.

---

## 12. Émotions et régulation

### EMO-001 — Processus multi-composants

Une émotion coordonne partiellement appraisal, corps, tendance d’action, expression, sentiment et étiquette.

### EMO-002 — Appraisals multi-niveaux

Les appraisals peuvent être rapides, implicites, associatives, conscientes ou verbales.

### EMO-003 — Familles prototypiques

Les catégories émotionnelles sont des profils déclaratifs, non des signatures universelles rigides.

### EMO-004 — Affect, humeur et émotion

L’état affectif général, l’humeur, l’épisode émotionnel, le sentiment conscient et l’étiquette sont séparés.

### EMO-005 — Multiplicité

Plusieurs émotions, y compris de valences opposées, peuvent coexister.

### EMO-006 — Conscience décomposée

Accès corporel, attention interne, interprétation, différenciation, étiquetage et expression sont des capacités distinctes.

### EMO-007 — Expression ambiguë

L’expression est multimodale, contextuelle, modulée et interprétable de manière faillible.

### EMO-008 — Dynamique non universelle

Une émotion ne suit pas une décroissance unique. Faible intensité et résolution sont distinctes.

### EMO-009 — Régulation orientée vers un but

La régulation peut réduire, maintenir, augmenter, comprendre ou seulement masquer une composante.

### EMO-010 — Sélection et implémentation

Choisir une stratégie, l’exécuter et en surveiller le résultat sont des compétences distinctes.

### EMO-011 — Succès fonctionnel

Le succès dépend du but, des coûts, des effets sociaux et différés, pas seulement d’une baisse d’intensité.

### EMO-012 — Régulation interpersonnelle

Une tentative de réguler autrui forme une boucle dyadique et peut être aidante, inefficace, intrusive ou dommageable.

---

## 13. Ontologie des entités et capacités

### ONT-001 — Catégories distinctes

```text
référent
≠ entité suivie
≠ enregistrement
≠ événement
≠ qualité
≠ phase
≠ rôle
```

### ONT-002 — Agent comme organisation fonctionnelle

Le système distingue :

- identité;
- sujet cognitif;
- contrôleur;
- percepteur;
- acteur;
- corps;
- personne sociale.

### ONT-003 — Corps, manifestation, forme et apparence

Ces objets sont séparés et reliés temporellement.

### ONT-004 — Parties typées

Le moteur distingue partie intégrale, partie détachable, portion matérielle, contenu, équipement et membre d’un collectif.

### ONT-005 — Pas de branchement général par espèce

Les types fournissent des configurations et contraintes initiales. Les systèmes lisent les composants, capacités et états.

### CAP-001 — Capacité dérivée

Une capacité actuellement disponible est dérivée des composants, de la forme, de l’état, de l’équipement et de l’environnement.

### CAP-002 — Affordance située

Une affordance relie acteur, action, cible et contexte. Elle n’est pas une propriété absolue de l’objet.

### CAP-003 — Capacité, compétence et permission

Capacité, connaissance, compétence, affordance, permission et autorisation sont distinctes.

### ID-001 — Transition d’identité explicite

Transformation, remplacement, copie, séparation, fusion et reconstitution utilisent une politique d’identité explicite.

### ID-002 — Règles MVP

Dans le scénario initial :

- changement de forme : même identité;
- blessure et sommeil : même identité;
- copie : nouvelle identité dérivée;
- fusion et fragmentation autonome : indisponibles.

### ONT-006 — Cycles de vie séparés

Définition, existence dans le monde, accessibilité, appartenance et archivage possèdent des axes distincts.

---

## 14. Persistance et sauvegarde

### PST-001 — Event sourcing sélectif

Seuls les changements canoniques significatifs exigent des événements durables.

### PST-002 — Écriture atomique

État courant, événements et projections transactionnelles obligatoires sont mis à jour dans une seule transaction.

### PST-003 — État, histoire et projection

```text
état courant
≠ journal
≠ projection
```

Les projections sont reconstruisibles.

### PST-004 — Rejeu indépendant du LLM

Aucun replay ne dépend d’un nouvel appel au modèle. Les décisions externes acceptées et sources de non-déterminisme sont capturées.

### PST-005 — Contrats versionnés

Événements, réducteurs, projections et migrations possèdent des versions explicites.

### PST-006 — Snapshots spécialisés

Le système distingue :

- snapshot de projection;
- checkpoint administratif;
- sauvegarde physique;
- export portable.

### PST-007 — Histoire non effacée

Une réversion normale utilise compensation, nouvel état ou branche. Elle ne supprime pas silencieusement les événements commis.

### PST-008 — Outbox externe

Discord et autres effets externes passent par une outbox persistante et idempotente.

### PST-009 — Séparation des magasins

Canon, diagnostics LLM, actifs lourds et contenus sensibles possèdent des politiques distinctes.

### PST-010 — Sauvegardes vérifiées

Une sauvegarde n’est réputée fiable qu’après une restauration testée et des contrôles d’intégrité.

---

## 15. Modèles réutilisables et instances

### LIB-005 — Version publiée immuable

Une version publiée de modèle ne change plus. Toute évolution crée une nouvelle version.

### LIB-006 — Instance indépendante

L’instanciation crée un nouvel identifiant et fige une définition initiale résolue.

### LIB-007 — Pas de propagation silencieuse

Une modification de modèle ne transforme jamais automatiquement les instances actives.

### LIB-008 — Migration contrôlée

La mise à jour d’une instance exige diff, impact, checkpoint, confirmation, transaction et événements.

### LIB-009 — Types d’export

Le système distingue :

- modèle réutilisable;
- snapshot d’instance;
- continuation complète.

### LIB-010 — Sémantique d’identité à l’import

L’import doit annoncer s’il crée une nouvelle instance, une copie dérivée, une continuation ou une branche.

---

## 16. Administration et validation

### ADM-007 — Interface comme client

L’interface web n’est jamais une autorité. Elle utilise la même API canonique que les autres clients.

### ADM-008 — Commandes métier

Les changements sensibles utilisent des commandes explicites, pas un CRUD générique de la base.

### ADM-009 — Registres versionnés

Les définitions publiées de composants et capacités sont immuables et versionnées.

### ADM-010 — Structure contre sémantique

JSON Schema valide la structure locale. Des validateurs distincts vérifient les invariants sémantiques, temporels, ontologiques et de monde.

### ADM-011 — Données, dérivations et vues

Les données sources, états dérivés et présentations d’interface sont séparés.

### ADM-012 — Unités canoniques

Les grandeurs déclarent unité canonique, échelle de stockage, précision et unités d’affichage.

### ADM-013 — Validation en couches

Pipeline minimal :

```text
parse
→ structure
→ références
→ sémantique
→ inter-composants
→ temporalité
→ ontologie
→ capacités
→ monde
→ autorisation
→ transition
→ impact
→ concurrence
→ postconditions
```

### ADM-014 — Résultats structurés

Tout finding possède code stable, sévérité, cible, preuve, attendu, observé et suggestion de correction.

### ADM-015 — Plan préparé immuable

Une modification profonde produit un `PreparedChange` lié à un hash, à une version du monde, aux versions des cibles et à une expiration.

### ADM-016 — Confirmation exacte

La confirmation porte sur le plan précis. Tout changement concurrent oblige à préparer un nouveau plan.

### ADM-017 — Idempotence

Les commandes et confirmations mutantes possèdent des identifiants permettant de tolérer les retries sans double application.

### ADM-018 — Autorisation côté serveur

Masquer un bouton ne remplace jamais une permission. Le moindre privilège s’applique même si le même propriétaire possède initialement tous les rôles.

### ADM-019 — Journaux séparés

Le journal canonique, l’audit administratif et le diagnostic technique ne sont pas confondus.

### ADM-020 — Le MVP utilise ses outils

La résidence et les quatre profils définitifs doivent être créés ou migrés par les vrais gestionnaires, pas par une voie seed parallèle.

---

## 17. Consentement et pouvoir

### CNS-001 — Consentement distinct de toute relation

Aucun niveau d’affection, confiance, intimité, engagement, désir, rôle, autorité ou historique ne constitue un consentement actuel.

### CNS-002 — Permission actuelle et révocable

Toute action nécessitant un consentement utilise une permission spécifique, contextualisée, actuelle et révocable.

### CNS-003 — Régulation et soin

Le désir d’aider, protéger ou réguler l’émotion d’autrui ne permet pas de contourner ses limites ou permissions.

### CNS-004 — Pouvoir du propriétaire

L’autorité administrative du propriétaire demeure distincte de la perception qu’en ont les agentes, de sa présence, de sa légitimité relationnelle et de leur obéissance volontaire.

---

## 18. Limites du LLM

### LLM-001 — Proposition seulement

Le LLM peut proposer options, interprétations, formulations, résumés et structures candidates.

### LLM-002 — Aucune vérité inaccessible

Le LLM ne reçoit pas comme connaissance du personnage une information que celui-ci n’a pas perçue, apprise ou récupérée.

### LLM-003 — Aucune écriture canonique

Le LLM ne modifie ni base, événement, composant, capacité, relation, mémoire, émotion, permission ou identité.

### LLM-004 — Sortie structurée validée

Toute proposition ayant un effet mécanique passe par un contrat structuré, des validateurs et le moteur canonique.

### LLM-005 — Pas d’autorité sur les statuts

Le LLM ne peut déclarer seul qu’un objectif est réussi, qu’une relation est réparée, qu’une émotion est résolue, qu’un consentement existe ou qu’une sauvegarde est valide.

### LLM-006 — Appels ciblés

Les déplacements, besoins, routines, matérialisations temporelles et validations simples demeurent déterministes et ne nécessitent pas d’appel au modèle.

---

## 19. Portée MVP et éléments différés

### MVP obligatoire

- quatre profils de référence;
- univers et résidence configurables;
- moteur canonique déterministe;
- registre minimal de composants et capacités;
- validation et interface administrative locale;
- actions, perceptions et scènes suffisantes pour une boucle sociale;
- cognition modulaire;
- mémoire, émotions, relations et intentions dans une première portée contrôlée;
- Discord comme fenêtre sociale;
- sauvegardes testées;
- diagnostics et coûts mesurés.

### Différé

- fusion et fragmentation conscientes;
- possession;
- plusieurs corps actifs;
- conscience collective avancée;
- temporalité subjective complexe;
- ville complète;
- maladies, vieillissement, grossesse et mort dans l’univers initial;
- moteur de plugins universel;
- simulations neurologiques détaillées;
- optimisation prématurée pour des milliers d’agents.

---

## 20. Critère de conformité d’un lot

Un lot n’est conforme que si :

1. il ne contourne aucun invariant;
2. il déclare précisément ce qui est implémenté;
3. il inclut les migrations nécessaires;
4. il conserve la provenance;
5. il fournit des tests positifs, négatifs, de régression et de crash lorsque pertinent;
6. il différencie MVP et architecture future;
7. il produit un rapport de livraison vérifiable;
8. il met à jour la traçabilité documentaire.
