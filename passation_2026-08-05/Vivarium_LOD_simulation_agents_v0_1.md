# Fidélité adaptative des agents (LOD de simulation)

**Version :** 0.1  
**Statut :** Idée documentée — reportée après le MVP  
**Date :** 5 août 2026  
**Portée :** Visiteurs, personnages secondaires, figurants et agents extérieurs au foyer  
**Caractère normatif :** Non. Ce document décrit un prototype conceptuel à réévaluer après stabilisation du MVP.

---

## 1. Idée centrale

Le Vivarium ne simulera pas tous les agents avec la même profondeur.

Le niveau de détail de simulation augmentera selon la pertinence réelle d’un agent pour le foyer, la scène en cours et la continuité du monde.

```text
Faible pertinence
→ rôle, routine et réactions mécaniques

Pertinence croissante
→ état local, mémoire, croyances, relations, décisions LLM

Pertinence maximale
→ simulation complète et persistante
```

Le principe est comparable à un **LOD (Level of Detail)** en 3D, mais appliqué à :

- la physiologie;
- la cognition;
- les émotions;
- la mémoire;
- les relations;
- la planification;
- la vie hors champ;
- la fréquence des mises à jour;
- les appels LLM.

---

## 2. Objectif

Permettre au monde de contenir des visiteurs, travailleurs, voisins et autres personnages sans devoir leur attribuer dès le départ la même profondeur qu’aux membres du foyer.

Exemple :

- un facteur ordinaire peut être une coquille fonctionnelle;
- un incident avec la louve peut modifier sa manière de livrer;
- cette conséquence peut justifier une mémoire persistante et une routine adaptée;
- il reste néanmoins beaucoup moins simulé qu’un résident.

La règle générale est :

> Simuler ce qui est pertinent, au moment où cela devient pertinent, sans effacer les conséquences persistantes.

---

## 3. Niveaux proposés

### BACKGROUND

Agent fonctionnel de fond.

Conserve seulement :

- rôle;
- tâche;
- position approximative;
- fenêtre de présence;
- capacités minimales;
- réactions génériques.

Exemples :

- facteur sans incident;
- livreur anonyme;
- passant;
- technicien présent uniquement pour une tâche.

Aucun appel LLM.

### CONTEXTUAL

Agent directement impliqué dans une scène.

Ajouts temporaires :

- perception locale;
- état émotionnel simple;
- objectif immédiat;
- conflit local;
- mémoire de scène;
- règles sociales minimales.

Appel LLM seulement si une ambiguïté importante ne peut pas être résolue mécaniquement.

### PERSISTENT

Personnage secondaire ayant acquis une continuité.

Ajouts :

- identité stable;
- quelques traits;
- croyances locales;
- souvenirs importants;
- relation simple avec les résidents;
- routine adaptée;
- fils non résolus;
- appels LLM ciblés lors d’interactions significatives.

### RESIDENT

Membre du foyer.

Simulation complète et permanente :

- corps;
- besoins;
- perception;
- croyances;
- mémoire;
- émotions;
- relations;
- intentions;
- routines;
- continuité;
- décisions LLM selon les déclencheurs cognitifs normaux.

---

## 4. Pertinence

La pertinence ne devrait pas être définie comme une importance narrative décidée d’avance.

Elle devrait résulter de conséquences observables.

### 4.1 Pertinence structurelle

Elle vient du rôle permanent de l’agent.

Exemples :

- résident : niveau maximal permanent;
- ami proche récurrent : plancher élevé;
- voisin occasionnel : plancher moyen;
- facteur anonyme : plancher minimal.

### 4.2 Pertinence situationnelle

Elle augmente pendant une implication actuelle.

Signaux :

- présence sur les lieux;
- proximité d’un résident;
- interaction directe;
- conversation;
- cible d’une action;
- obstacle;
- danger;
- action conjointe;
- observation d’un événement important;
- intervention explicite du propriétaire.

### 4.3 Pertinence persistante

Elle augmente lorsqu’une conséquence survit à la scène.

Signaux :

- mémoire importante;
- peur;
- promesse;
- dette;
- conflit;
- croyance nouvelle;
- changement de routine;
- relation créée;
- objet confié;
- retour futur prévu;
- fil non résolu;
- intérêt explicite du propriétaire.

---

## 5. Autorité sur la pertinence

Le niveau de fidélité devrait être géré par un **moteur de pertinence déterministe**.

Chaîne envisagée :

```text
événement canonique
→ implication détectée
→ conséquences détectées
→ pertinence recalculée
→ déclencheurs de promotion
→ modules activés
→ appel LLM éventuel pour ambiguïté
→ niveau de fidélité retenu
```

Le LLM peut proposer qu’un événement a eu une importance subjective particulière, mais il ne doit pas promouvoir seul un personnage ni créer arbitrairement une persistance.

Le propriétaire doit pouvoir imposer :

```text
Conserver ce personnage comme secondaire persistant.
```

---

## 6. Promotion

Déclencheurs possibles :

```text
entrée sur les lieux
→ BACKGROUND vers CONTEXTUAL

interaction directe
→ maintien en CONTEXTUAL

conséquence persistante
→ PERSISTENT

désignation du propriétaire
→ PERSISTENT

membre du foyer
→ RESIDENT
```

Une promotion ne doit créer que les détails nécessaires.

Lorsqu’un figurant devient pertinent, le système peut créer :

- une identité minimale;
- quelques traits utiles;
- une mémoire;
- une croyance locale;
- une routine modifiée.

Il ne doit pas inventer immédiatement une biographie complète.

Les champs inconnus restent inconnus.

---

## 7. Dépromotion et compression

Une baisse de fidélité ne doit pas effacer l’histoire.

```text
niveau de simulation faible
≠
amnésie
```

Lorsqu’une scène se termine :

- les états temporaires peuvent être abandonnés;
- les conséquences importantes sont compressées;
- les souvenirs utiles restent;
- les routines modifiées restent;
- les fils non résolus restent.

Exemple :

```text
Avant compression :
- peur 0,64;
- gêne 0,22;
- plusieurs événements de visite;
- évitement actif.

Après compression :
- craint la louve;
- utilise la boîte latérale;
- reste professionnel;
- peut réviser son opinion après des contacts sûrs.
```

---

## 8. Modules activables

Un niveau ne doit pas nécessairement être monolithique.

Exemple conceptuel :

```yaml
physical_basic: true
physical_full: false
local_emotion: true
episodic_memory: true
beliefs: true
relationships: true
long_term_goals: false
llm_decision: conditional
offscreen_simulation: summary_only
```

Un facteur peut avoir une peur persistante et une routine modifiée sans simulation détaillée de faim, de sommeil ou de vie personnelle.

---

## 9. Exemple du facteur

```text
1. Une livraison est planifiée.
2. Un facteur BACKGROUND est matérialisé.
3. Il suit sa routine.
4. La louve entre dans son champ perceptif.
5. Une interaction inhabituelle survient.
6. Il monte en CONTEXTUAL.
7. Une peur locale est calculée.
8. Il modifie sa manière de livrer.
9. La modification doit survivre à la scène.
10. Il devient PERSISTENT.
11. Une mémoire et une routine adaptée sont enregistrées.
12. Il quitte les lieux.
13. Sa simulation est compressée hors champ.
14. À la prochaine visite, son dossier minimal est rechargé.
```

---

## 10. Données conceptuelles

```yaml
AgentFidelityRecord:
  agent_id: string
  fidelity_floor: BACKGROUND | CONTEXTUAL | PERSISTENT | RESIDENT
  fidelity_current: BACKGROUND | CONTEXTUAL | PERSISTENT | RESIDENT
  relevance_score: number
  promotion_reasons: list
  active_modules: list
  last_relevance_at: datetime
  persistent_summary: list
  unresolved_threads: list
```

Le `fidelity_floor` empêche un résident de devenir abstrait.

---

## 11. Garde-fous

- pas de promotion après chaque contact banal;
- pas de dépromotion pendant une scène active;
- pas d’effacement des conséquences;
- pas de biographie rétroactive incontrôlée;
- même monde canonique et mêmes lois physiques pour tous;
- fidélité faible ne signifie pas personnage inexistant;
- hystérésis pour éviter les changements incessants de niveau;
- limite ou politique de conservation des secondaires persistants;
- audit des raisons de promotion;
- possibilité de promotion ou de maintien manuel par le propriétaire.

---

## 12. Risques

- promotion trop fréquente;
- accumulation infinie de personnages persistants;
- dépromotion trop rapide;
- oscillation entre niveaux;
- création excessive de détails;
- perte de souvenirs;
- LLM appelé inutilement;
- comportement différent selon le niveau au point de violer les règles du monde;
- pertinence calculée seulement par proximité physique;
- confusion entre intérêt du propriétaire et importance causale.

---

## 13. Prototype recommandé après le MVP

Commencer par quatre catégories fixes :

```text
BACKGROUND
CONTEXTUAL
PERSISTENT
RESIDENT
```

Première version sans score sophistiqué :

- promotions par événements explicites;
- compression simple;
- aucun LLM requis pour le système de fidélité lui-même;
- raison de promotion enregistrée;
- tests déterministes;
- interface administrative minimale.

Une version ultérieure pourra ajouter :

- score continu;
- causalité;
- fréquence de retour;
- importance pour un résident;
- hystérésis avancée;
- activation granulaire de modules;
- politique de budget LLM.

---

## 14. Position dans la feuille de route

Cette idée est **reportée après le MVP**.

Elle ne doit pas retarder :

- le foyer initial;
- les quatre résidents;
- les actions essentielles;
- la perception;
- la mémoire;
- les relations;
- la cognition de base;
- l’adaptateur LLM;
- la première boucle autonome fonctionnelle.

Elle devient pertinente lorsque le projet commence à intégrer :

- visiteurs;
- agents extérieurs;
- scènes avec personnages non résidents;
- vie hors champ;
- monde plus peuplé;
- budgets d’appels LLM.

---

## 15. Décision actuelle

**Décision : documenter maintenant, ne pas implémenter avant le MVP.**

À reprendre après stabilisation de la première simulation autonome du foyer.
