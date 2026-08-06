# Vivarium Social — Feuille de route après audit

**Version :** 0.1  
**Date :** 4 août 2026  
**Statut :** actif  
**But :** transformer les conclusions normatives en lots bornés sans perdre le travail technique déjà livré

---

## 1. État de départ

```text
Dernier commit confirmé : f1335ca
Tests confirmés : 164
Dernier lot livré : Phase 3.3B1
Prochain lot de code : Phase 3.3B2
Audit rétrospectif : terminé
Consolidation documentaire : terminée
```

L’audit ne modifie pas le code existant. Les nouveaux contrats devront être intégrés progressivement et sans réécrire les phases déjà validées sans nécessité.

---

## 2. Séquence immédiate

### LOT A1 — Phase 3.3B2

Effets mécaniques des blessures.

Portée déjà proposée :

- blessure légère : aucun effet mécanique;
- blessure modérée : coût de déplacement;
- blessure sévère : mouvement autonome bloqué;
- matérialisation exacte avant validation;
- événements et tests reproductibles.

Le prompt existant reste le point de départ, mais doit être relu pour vérifier sa cohérence avec les invariants post-audit.

### LOT A2 — Phase 3.3C

Fermeture reproductible de la Phase 3 :

- simulation déterministe;
- seeds;
- rapports;
- reprise;
- tests longue durée;
- vérification du journal;
- documentation du commit final.

### LOT A3 — Audit de fermeture technique

Comparer :

- code;
- migrations;
- tests;
- dossier maître;
- demande de changement post-audit.

Sortie :

- état réel;
- dettes;
- écarts;
- décision de migration ou remplacement des personnages techniques.

---

## 3. Intégration normative au dépôt

### LOT B1 — Dossier maître v0.2

Fusionner :

- décisions remplacées;
- DEC-036 à DEC-060;
- exigences normatives;
- nouveau chemin critique;
- scénarios d’acceptation.

### LOT B2 — Matrice de traçabilité

Créer une table :

```text
décision
→ exigence
→ composant
→ migration
→ événement
→ test
→ commit
```

### LOT B3 — Contrat de lot standard

Chaque nouveau prompt d’implémentation doit déclarer :

- dépendances;
- exclusions;
- invariants;
- contrat de données;
- événements;
- transactions;
- stratégie de migration;
- tests;
- arrêt obligatoire.

---

## 4. Vertical slice administratif

### LOT C1 — Registre minimal

Implémenter seulement les contrats nécessaires à :

- humaine;
- louve;
- chat;
- slime;
- résidence initiale.

Inclure :

- versions;
- dépendances;
- unités;
- champs sources et dérivés;
- validateurs liés.

### LOT C2 — Pipeline de validation

Implémenter :

```text
structure
→ références
→ sémantique
→ inter-composants
→ monde
→ transition
```

Les couches ontologique, capacité, impact et concurrence sont ajoutées dès qu’un lot les utilise réellement.

### LOT C3 — API de changement

Première boucle verticale :

```text
draft
→ prepare
→ validate
→ impact
→ confirm
→ transaction
→ audit
```

### LOT C4 — Gestionnaire d’univers

Créer ou importer la résidence par l’API :

- profil du monde;
- neuf lieux;
- connexions;
- chambres assignées;
- objets de base;
- règles initiales.

### LOT C5 — Gestionnaire d’entités et modèles

Créer :

- brouillon;
- version publiée;
- instanciation;
- activation;
- archive;
- inspection.

### LOT C6 — Interface web locale minimale

Écrans prioritaires :

- tableau de bord;
- univers;
- lieux;
- entités;
- validation;
- changements préparés;
- événements et diagnostics.

### LOT C7 — Migration des presets

Décider explicitement :

- conserver et migrer les personnages techniques;
- ou créer les quatre profils définitifs puis archiver les placeholders.

Aucune édition directe de SQLite.

---

## 5. Boucle action et perception

### LOT D1 — Registre d’actions et capacités

Définir :

- action;
- paramètres;
- préconditions;
- coûts;
- risques;
- effets;
- cibles;
- validations;
- événements.

### LOT D2 — Affordances

Produire les actions actuellement tentables depuis :

- acteur;
- capacités;
- cible;
- distance;
- environnement;
- état.

### LOT D3 — Permissions et limites

Distinguer :

- possibilité;
- permission;
- autorisation;
- transgression;
- consentement requis.

Le système de consentement complet fera l’objet d’une revue séparée.

### LOT D4 — Scènes et manifestations

Un événement canonique produit des manifestations accessibles, pas une copie complète de son payload.

### LOT D5 — Perception et attention

Implémenter la chaîne auditée :

```text
accessibilité du signal
→ enregistrement
→ compétition
→ orientation
→ perception consciente ou partielle
→ éventuel encodage
```

---

## 6. Boucle cognitive minimale

Ordre recommandé :

1. questions, hypothèses et croyances;
2. modèles de source;
3. encodage et mémoire épisodique;
4. appraisal et épisodes émotionnels;
5. signaux régulatoires et motifs;
6. objectifs et intentions;
7. épisode décisionnel;
8. proposition d’action;
9. conséquences et apprentissage.

Chaque étape doit fonctionner avec un faux adaptateur déterministe avant l’intégration d’un vrai LLM.

---

## 7. Boucle sociale

Après la première boucle cognitive :

1. conversations structurées;
2. engagements sociaux;
3. relations directionnelles;
4. intimité et confiance située;
5. réparation;
6. réseau social léger;
7. Discord;
8. initiatives spontanées.

Les conversations ne doivent pas être un simple texte libre : elles produisent des actes de parole, perceptions, croyances, engagements et effets relationnels validés.

---

## 8. Nouveaux systèmes à rechercher avant conception

### Système 1 — Consentement opérationnel

Doit couvrir :

- demande;
- compréhension;
- capacité à consentir;
- spécificité;
- durée;
- révocation;
- pression;
- pouvoir;
- refus;
- négociation;
- actions en cours.

### Système 2 — Modèle de soi

Doit couvrir :

- conceptions de soi;
- identité narrative;
- rôles;
- continuité;
- estime;
- efficacité;
- réputation intériorisée;
- conflits identitaires.

### Système 3 — Apprentissage

Doit couvrir :

- habitudes;
- valeurs incitatives;
- compétences;
- modèles causaux;
- généralisation;
- extinction;
- changement dispositionnel lent.

### Système 4 — Secrets et circulation de l’information

Doit couvrir :

- connaissance du contenu;
- connaissance de l’existence du secret;
- engagements de confidentialité;
- rumeurs;
- sources;
- transmission;
- preuve;
- visibilité;
- conséquences relationnelles.

### Système 5 — Orchestration LLM

Doit couvrir :

- déclencheurs d’appel;
- récupération de contexte;
- budget;
- compression;
- sorties structurées;
- validation;
- fallback;
- interruption;
- observabilité.

---

## 9. Critère de passage à l’étape suivante

Un lot est fermé lorsque :

- ses migrations sont appliquées;
- les anciens tests passent;
- ses nouveaux tests passent;
- les événements sont inspectables;
- les lectures sont sans effets de bord;
- les échecs sont atomiques;
- les documents indiquent ce qui est réellement livré;
- aucun cas différé n’est prétendu implémenté.

---

## 10. Prochaine action concrète

Relire le prompt `Vivarium_Prochain_Prompt_DeepSeek_3_3B2.md` contre les exigences post-audit, puis produire une version révisée à transmettre à DeepSeek pour **planification seulement, sans code**.
