# Prompt prêt à envoyer à DeepSeek — Audit technique de fermeture de la Phase 3

**Projet :** Vivarium social artificiel  
**Type de réponse demandé :** audit technique complet, sans implémentation  
**Point de départ officiel :** commit `a63964976d37397d502dbee101dbb231537ec3f3`  
**État confirmé :** Phase 3 fonctionnellement terminée  
**Tests confirmés :** 220 réussis  
**Scénarios confirmés :** 24 h et 7 jours validés  
**Étape demandée :** audit technique de fermeture de la Phase 3 uniquement

## 0. Règle d’autorité et point d’arrêt obligatoire

Avant toute conclusion, inspecte réellement le dépôt, les migrations, le schéma, les tests, les transactions et la documentation technique.

Ordre d’autorité :

1. code et migrations du dépôt;
2. tests exécutables;
3. contrats événementiels et invariants implémentés;
4. documentation technique;
5. présente instruction;
6. documents post-audit présents à la racine.

Documents post-audit non suivis :

- `Vivarium_Demande_Changement_Post_Audit_v0_2.md`;
- `Vivarium_Exigences_Normatives_Post_Audit_v0_1.md`;
- `Vivarium_Feuille_Route_Post_Audit_v0_1.md`.

Ces documents servent de contexte normatif, mais cet audit n’est pas leur intégration documentaire.

Si une exigence approuvée est impossible, contradictoire, ambiguë, incomplète ou exige une redéfinition du contrat :

```text
arrête l’analyse concernée
→ décris précisément le conflit
→ propose les options et leurs conséquences
→ attends une décision explicite
```

Aucune adaptation silencieuse du contrat n’est autorisée.

## 1. But de l’audit

L’objectif n’est pas d’ajouter une fonctionnalité.

L’objectif est de répondre à cette question :

> Le moteur canonique déterministe construit pendant la Phase 3 est-il techniquement cohérent, fermé, traçable, reproductible, reprenable et suffisamment stable pour servir de fondation à la Phase 4?

L’audit doit vérifier transversalement :

```text
schéma
+ état canonique
+ horloge
+ transactions
+ besoins
+ activités
+ déplacements
+ blessures
+ politique déterministe
+ journal
+ reprise après crash
+ reproductibilité
+ tests
+ documentation
= moteur fermé et cohérent
```

## 2. Travail demandé maintenant

Tu dois :

- inspecter l’état réel du dépôt au commit officiel;
- exécuter la régression complète;
- établir la carte technique réelle de la Phase 3;
- identifier les invariants transversaux;
- vérifier leur implémentation et leurs tests;
- détecter les contournements, duplications, contradictions et dettes;
- classer chaque constat;
- produire un verdict de fermeture;
- proposer, si nécessaire, une liste bornée de correctifs;
- distinguer les correctifs obligatoires des améliorations reportables.

Tu ne dois pas :

- modifier de fichier;
- écrire de code;
- créer de migration;
- créer de commit;
- intégrer les documents post-audit;
- commencer la Phase 4;
- proposer une refonte générale;
- inventer de nouveaux systèmes.

Arrête-toi après le rapport d’audit et attends l’approbation.

## 3. Inspection initiale obligatoire

Confirme :

### Dépôt
- HEAD exact;
- branche;
- état de l’arbre;
- fichiers non suivis;
- version Python;
- version SQLite si accessible;
- résultat exact des 220 tests;
- avertissements éventuels;
- tests lents ou instables.

### Schéma
- dernière migration appliquée;
- nombre de migrations;
- tables Phase 3;
- contraintes;
- triggers;
- index;
- clés étrangères;
- règles d’immutabilité;
- colonnes temporelles;
- présence de types REAL là où ils sont interdits.

### Modules
Dresse la carte réelle de :
- `world.py`;
- `simulation.py`;
- `character.py`;
- `activities.py`;
- `needs.py`;
- `injury.py`;
- `policy.py`;
- `repro.py`;
- persistance / base;
- CLI ou points d’entrée.

Pour chacun :
- responsabilité;
- API publique;
- helpers internes;
- tables lues;
- tables écrites;
- événements émis;
- transactions ouvertes;
- dépendances.

## 4. Carte d’autorité

Établis :

```text
qui peut lire
qui peut proposer
qui peut valider
qui peut modifier
qui peut journaliser
qui peut avancer le temps
qui peut ouvrir une transaction
```

Vérifie qu’aucune interface ou commande ne modifie directement les tables métier sans passer par le moteur canonique, qu’aucune méthode publique ne contourne les validations et que les variantes simulateur internes sont séparées des API publiques.

Signale tout chemin pouvant :

- déplacer sans validation;
- modifier l’énergie sans transaction;
- matérialiser une blessure au mauvais instant;
- créer une activité sans vérifier graphe ou énergie;
- avancer l’horloge sans cohérence;
- écrire un événement sans mutation correspondante;
- muter l’état sans événement obligatoire.

## 5. Audit du schéma et des migrations

Pour chaque table et migration, vérifie :

- types;
- bornes;
- `NOT NULL`;
- unicité;
- clés étrangères;
- index;
- cohérence monde/personnage;
- contraintes partielles;
- protection des états terminaux;
- append-only du journal;
- champs orphelins;
- redondances contradictoires;
- compatibilité depuis une base vide;
- reproductibilité de `ensure_schema`;
- divergence éventuelle entre schéma neuf et migré;
- absence de valeurs métier critiques en `REAL`;
- valeurs milli et restes entiers;
- références d’événements valides;
- unicité de l’activité active;
- unicité de la blessure active;
- séquences du journal par monde.

Si possible, compare :
```text
base neuve → toutes migrations → schéma final
base historique de test → migrations successives → schéma final
```

## 6. Audit des transactions et de l’atomicité

Construis une matrice pour :

- initialisation du monde;
- déplacement direct;
- démarrage d’activité;
- fin d’activité;
- abandon d’activité;
- matérialisation des besoins;
- matérialisation des blessures;
- accident scripté;
- pause;
- reprise;
- mise à l’heure administrative;
- progression du simulateur.

Pour chaque opération :
- fonction d’entrée;
- transaction propriétaire;
- sous-appels partageant `_conn`;
- état modifié;
- événements émis;
- horloge modifiée;
- comportement en exception;
- test de rollback;
- lacune éventuelle.

Vérifie :

```text
aucune écriture partielle
aucun événement sans état
aucun état sans événement obligatoire
aucune horloge avancée sans état cohérent
aucune matérialisation survivant à un refus
```

## 7. Audit du temps

Vérifie :

```text
temps mural
temps canonique persisté
temps canonique dérivé
temps cible du simulateur
occurred_at
recorded_at
ancres
planned_end_at
```

Confirme :

- formule exacte de l’horloge active;
- pause;
- reprise;
- absence de rattrapage indésirable;
- redémarrage;
- mise à jour atomique de `simulated_now` et `real_updated_at`;
- ordre à une frontière;
- absence d’heure murale dans les décisions;
- aucune décision à T + microsecondes dans une frontière T;
- aucun événement métier avec `occurred_at` mural;
- monotonie;
- aucune ancre future;
- aucune double progression.

Inspecte aussi les chemins hors simulateur : commandes directes, pause, reprise, accidents, mouvements, matérialisations manuelles et commandes administratives.

## 8. Audit du graphe spatial et des déplacements

Vérifie :

- lieux et liens;
- directionnalité;
- recherche de chemin;
- ordre stable;
- absence de téléportation;
- validation d’adjacence;
- coût par arête;
- prévalidation multi-arêtes;
- atomicité du trajet;
- énergie exacte;
- énergie insuffisante;
- blessures light/moderate/severe;
- payload stable de `character_moved`.

Confirme :
- `edge_count=1` par événement d’arête;
- somme des événements cohérente avec le chemin;
- aucune double surcharge;
- refus sans événement, débit ni matérialisation persistante;
- mouvement direct pendant activité conforme;
- aucun contournement de `_move`.

## 9. Audit des besoins

Vérifie :

- définitions;
- valeurs;
- bornes;
- taux;
- restes;
- ancres;
- dérivation pure;
- matérialisation;
- influence des activités;
- ordre des régimes;
- absence de `REAL`;
- exactitude aux bornes;
- lecture sans écriture.

Inspecte `needs_materialized` :
- forme stable;
- `rate_source`;
- `activity_type`;
- `rate_nums`;
- `rate_dens`;
- valeurs et restes avant/après;
- ancres avant/après.

Vérifie que les taux déclarés correspondent aux définitions canoniques et que l’hypothèse d’immutabilité des définitions est vraie dans le code actuel.

## 10. Audit des activités

Vérifie :

- définitions;
- lieux autorisés;
- durée;
- effets;
- activité active unique;
- début;
- fin;
- abandon;
- sommeil;
- repos;
- idle;
- frontières simultanées;
- redémarrage.

Confirme :
- ancien régime jusqu’à T;
- transition à T;
- nouveau régime après T;
- aucune double matérialisation;
- aucune double fin;
- aucune durée négative ou boucle nulle;
- aucune décision sur état périmé;
- aucune activité impossible lancée;
- aucune activité incohérente après crash.

## 11. Audit des blessures

Vérifie :

- seuils;
- niveaux dérivés;
- taux passif/rest/sleep;
- arithmétique entière;
- restes;
- ancres;
- guérison;
- terminalité;
- unicité;
- cause;
- causalité;
- frontière exacte;
- effets sur mouvement et énergie;
- politique severe;
- activité locale;
- idle dynamique.

Inspecte :
- `injury_occurred`;
- `injury_materialized`;
- `injury_healed`;
- `scripted_accident`.

Confirme :
- aucune rematérialisation après guérison;
- aucune guérison avant zéro;
- aucune valeur négative;
- aucun changement rétroactif de régime;
- aucun mouvement severe;
- surcharge moderate exacte;
- aucune divergence entre état persisté et niveau dérivé.

## 12. Audit de la politique déterministe

Vérifie que `DeterministicPolicy` est :
- pure;
- sans RNG;
- sans SQLite direct;
- sans heure murale;
- sans mutation;
- stable sur l’ordre des candidats;
- bornée;
- explicable;
- compatible avec contraintes d’activité, blessure, énergie et lieu.

Cherche toute dépendance implicite à :
- dictionnaire;
- set;
- SQL sans `ORDER BY`;
- rowid;
- UUID;
- microsecondes murales.

## 13. Audit du simulateur

Vérifie `SimulationEngine.run_to` de bout en bout :
- entrée;
- validation;
- heure de départ;
- cible;
- prochaine frontière;
- ordre des personnages;
- clôtures;
- décisions;
- démarrages;
- mouvements;
- progression d’horloge;
- limites;
- fallback;
- arrêt normal;
- erreurs.

Confirme :

```text
aucune transition après target_time
aucune frontière retraitée
aucun personnage sauté
aucun traitement double
aucune décision avant matérialisation
aucune boucle sans progrès
```

Teste ou inspecte :
- actif;
- paused;
- cible égale;
- cible antérieure;
- aucune frontière;
- plusieurs personnages;
- crash entre personnages;
- redémarrage;
- segmenté;
- longue durée.

## 14. Audit du journal et de la reproductibilité

Distingue clairement :

### A. RawCanonicalEventLog
Journal complet, aucune exclusion.

### B. StructuralEventAudit
Séquences, trous, doublons, ordre, monotonie, JSON, causalités, orphelins, succès après rollback.

### C. ReproducibleSemanticProjection
Faits retenus, exclusions, renumérotation, causalité normalisée, ordre relatif, comparaison continu/segmenté/redémarré.

### D. MaterializationChainAudit
Exactitude mathématique, continuité, taux, ancres, restes, valeurs, sévérités, guérison, erreurs compensées.

Vérifie les faux négatifs possibles :
- événement exclu masquant une erreur;
- causalité supprimée;
- ordre perdu;
- configuration historique non versionnée;
- comparaison seulement finale;
- audit réutilisant la même fonction fautive sans test indépendant.

Vérifie aussi :

```text
même état initial
+ mêmes règles
+ mêmes commandes
+ mêmes valeurs de l’horloge injectée aux mêmes points
+ même ordre canonique
= même état et même projection sémantique
```

## 15. Audit des erreurs et des lectures pures

Dresse les exceptions métier et techniques :
- monde absent;
- personnage absent;
- mouvement invalide;
- énergie insuffisante;
- blessure sévère;
- activité impossible;
- absence de frontière;
- limite de transitions;
- erreur de transaction;
- erreur d’audit.

Pour chacune :
- type;
- message;
- données structurées;
- appelant;
- effet transactionnel;
- événement ou absence;
- test;
- cohérence inter-module.

Vérifie que les lectures :
- ne matérialisent pas;
- ne modifient pas d’ancre;
- n’émettent pas d’événement;
- ne changent pas l’horloge;
- ne créent pas d’objet;
- ne dépendent pas d’un ordre accidentel.

## 16. Audit des tests

Classe les 220 tests par domaine :
- monde;
- schéma;
- horloge;
- espace;
- personnages;
- besoins;
- activités;
- blessures;
- simulation;
- reproductibilité;
- journal;
- rollbacks.

Pour chaque domaine :
- nombre;
- invariants couverts;
- invariants non couverts;
- redondances;
- fragilité;
- dépendance à l’implémentation;
- dépendance à l’ordre;
- dépendance au temps;
- dépendance au système de fichiers;
- dépendance à SQLite.

Vérifie que :
- les fixtures ne sont pas trop permissives;
- les monkeypatchs ne masquent pas le contrat réel;
- les scénarios 24 h et 7 jours sont reproductibles;
- les tests de redémarrage ferment réellement la connexion;
- les tests de crash représentent une vraie transaction interrompue;
- les tests de corruption ne modifient pas l’audit lui-même.

## 17. Audit qualité du code

Inspecte :
- cycles d’import;
- dépendances croisées;
- duplication;
- fonctions trop longues;
- helpers privés utilisés hors module;
- paramètres `_conn`;
- paramètres de contournement;
- noms incohérents;
- code mort;
- constantes dupliquées;
- SQL dupliqué;
- ordre SQL implicite;
- commentaires périmés;
- docstrings fausses;
- branches impossibles;
- code de test dans le moteur métier.

Exécute uniquement les outils déjà configurés :
- lint;
- type checking;
- couverture;
- vérification d’imports.

N’installe rien sans autorisation.

## 18. Audit documentation

Compare :
- code;
- tests;
- migrations;
- `CHANGELOG.md`;
- documentation Phase 3;
- payloads;
- limites connues.

Repère :
- noms obsolètes;
- nombres de tests périmés;
- ancien hash;
- terminologie de seed incorrecte;
- journal brut présenté à tort comme identique;
- reconstruction event-sourced surpromue;
- pause/reprise mal décrite;
- événements enrichis non documentés;
- limites non documentées.

Ne fusionne pas les documents post-audit dans le dossier maître v0.2.

## 19. Frontière vers la Phase 4

Sans concevoir la Phase 4, vérifie que le moteur expose assez de contrats pour qu’une future couche administrative puisse :
- lire l’état;
- préparer une commande;
- valider;
- appliquer;
- journaliser;
- expliquer un refus;
- confirmer une modification profonde;
- ne jamais écrire directement dans SQLite.

Classe les préconditions manquantes :
- bloquant avant Phase 4;
- utile pendant Phase 4;
- reportable.

Ne crée pas encore Command API, Prepared Change, autorisation, confirmations, interface web ou Discord.

## 20. Recherche de contournements

Recherche dans le dépôt :
- `INSERT`;
- `UPDATE`;
- `DELETE`;
- accès direct aux tables métier;
- helpers privés;
- `_conn`;
- `_materialize`;
- `_advance_clock`;
- `Clock.now`;
- `datetime.now`;
- `uuid4`;
- requêtes sans `ORDER BY`;
- float;
- `REAL`;
- `random`;
- `set`;
- dictionnaires utilisés pour choix;
- `except Exception`;
- commits explicites;
- rollbacks;
- chemins CLI.

Classe chaque résultat pertinent :
- conforme;
- suspect;
- violation;
- hors périmètre.

## 21. Matrice des invariants

Produis une matrice :

```text
Invariant
Module responsable
Preuve dans le code
Preuve par test
Preuve par schéma
État
Risque
Action
```

États autorisés :
- `PROUVÉ`;
- `PARTIELLEMENT PROUVÉ`;
- `NON PROUVÉ`;
- `VIOLÉ`;
- `NON APPLICABLE`.

Inclure au minimum :

### Monde et temps
- temps monotone;
- pause;
- reprise;
- horloge/état atomiques;
- redémarrage;
- absence de temps mural dans les décisions.

### Espace
- position unique;
- adjacency;
- trajet atomique;
- coût exact;
- aucune téléportation.

### Besoins
- bornes;
- entier;
- restes;
- taux canonique;
- matérialisation;
- lecture pure.

### Activités
- activité unique;
- transitions;
- régimes;
- aucune double fin;
- redémarrage.

### Blessures
- seuils;
- récupération;
- terminalité;
- causalité;
- effets;
- guérison exacte.

### Journal
- append-only;
- séquences;
- causalité;
- monotonie;
- structure;
- projection;
- audit de chaîne.

### Reproductibilité
- runs indépendants;
- segmenté;
- redémarré;
- crash;
- pause;
- endurance.

## 22. Classification des constats

Classe chaque constat :

### Bloquant de fermeture
Corruption possible, transaction non atomique, contournement public, temps incohérent, garantie fausse, schéma divergent ou causalité invalide.

### Correctif recommandé avant Phase 4
Pas de corruption immédiate, mais risque sérieux pour la prochaine couche.

### Dette documentable
Amélioration reportable.

### Observation
Aucun changement requis.

Pour chaque constat :
- identifiant;
- sévérité;
- preuve;
- reproduction;
- impact;
- correction minimale;
- fichiers;
- migration ou non;
- tests nécessaires;
- dépendances.

## 23. Scénarios adversariaux obligatoires

Raisonne et, si possible, teste sans modifier le dépôt :

1. crash après état mais avant événement;
2. crash après événement mais avant état;
3. crash entre deux personnages;
4. mouvement refusé après matérialisation;
5. blessure guérie puis rematérialisation;
6. activité terminée deux fois;
7. énergie exacte à zéro;
8. chemin multi-arêtes partiel;
9. pause pendant activité;
10. reprise après longue indisponibilité;
11. redémarrage avec WAL;
12. causalité supprimée ou seq altéré;
13. payload falsifié;
14. erreur compensée;
15. ordre SQL modifié;
16. UUID différents;
17. horloge murale reculant;
18. cible antérieure;
19. deux appels simultanés potentiels;
20. définition de besoin modifiée après événements historiques.

Pour chacun :
- protection existante;
- test existant;
- résultat attendu;
- risque résiduel.

## 24. Verdict attendu

Termine par un verdict parmi :

### `FERMETURE APPROUVABLE`
Aucun bloquant.

### `FERMETURE APPROUVABLE AVEC CORRECTIFS MINEURS`
Aucun risque de corruption, mais correctifs bornés nécessaires.

### `FERMETURE REFUSÉE`
Au moins un bloquant technique réel.

Le verdict doit être fondé sur les preuves, pas sur le nombre de tests.

## 25. Format exact de la réponse

1. Résumé exécutif
2. État réel inspecté
3. Carte des modules et de l’autorité
4. Carte des transactions
5. Audit schéma et migrations
6. Audit temporel
7. Audit espace et déplacements
8. Audit besoins
9. Audit activités
10. Audit blessures
11. Audit politique
12. Audit simulateur
13. Audit journal et reproductibilité
14. Audit erreurs et lectures pures
15. Audit tests
16. Audit qualité du code
17. Audit documentation
18. Frontière vers Phase 4
19. Matrice des invariants
20. Constats classés
21. Scénarios adversariaux
22. Risques résiduels
23. Correctifs proposés
24. Verdict de fermeture
25. Décisions nécessitant une approbation

Pour chaque constat, cite :
- fichier;
- fonction;
- migration ou test;
- comportement observé.

Ne produis pas de généralités sans preuve dans le dépôt.

## 26. Livrable et arrêt

Ne modifie rien.

Ne crée aucun fichier.

Ne crée aucun commit.

Ne lance aucune migration destructive.

Tu peux exécuter tests, requêtes de lecture, inspections de schéma et diagnostics non destructifs.

À la fin, demande explicitement l’approbation avant tout correctif.

Termine exactement par :

> Audit technique de fermeture terminé. Aucun fichier n’a été modifié. J’attends votre décision avant tout correctif, consolidation documentaire ou travail de Phase 4.
