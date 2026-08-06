# Vivarium Social — Registre des audits scientifiques et techniques

**Version :** 0.7  
**Date :** 4 août 2026  
**Statut :** actif  
**Rôle :** suivre les audits rétroactifs, leurs verdicts et le travail restant avant de reprendre la conception de nouveaux systèmes.

## 1. Règle méthodologique

Pour chaque modèle ou système psychologique, cognitif, social ou technique :

1. consulter la littérature scientifique ou technique appropriée;
2. distinguer résultats robustes, débats ouverts et choix d’ingénierie;
3. comparer la littérature avec la conception actuelle;
4. conserver, corriger, restructurer ou reprendre le système;
5. produire une version opérationnelle adaptée au vivarium;
6. définir entrées, états, transitions, stockage, événements, interactions et portée MVP;
7. obtenir la validation du propriétaire;
8. transférer ensuite les décisions dans la documentation normative.

La conception de nouveaux systèmes est temporairement suspendue jusqu’à la fermeture de l’audit rétroactif.

## 2. Statuts

- **VALIDÉ** : fondation suffisante; aucun changement structurel majeur.
- **VALIDÉ AVEC CORRECTIONS** : fondation bonne; mécanismes importants à ajuster.
- **VALIDÉ AVEC RESTRUCTURATION** : phénomènes pertinents, mais catégories ou architecture à réorganiser.
- **À REPRENDRE** : fondation trop fragile ou incompatible.
- **DÉCISION DE PRODUIT** : choix relevant principalement du propriétaire.
- **OUVERT** : audit ou conception non commencé.

## 3. Audits majeurs terminés

### AUD-01 — Attention et perception

**Verdict : VALIDÉ AVEC CORRECTIONS**

Principales corrections :

- ajouter un enregistrement sensoriel préconscient;
- remplacer les perceptions dites automatiques par des priorités élevées mais faillibles;
- séparer charge perceptive, cognitive et de contrôle;
- modéliser orientation ouverte, orientation couverte, surveillance et exploration;
- autoriser omissions et fausses alertes;
- pondérer l’intégration multisensorielle selon fiabilité et cause commune probable;
- rendre l’habituation spécifique au stimulus et au contexte;
- modéliser la fatigue de vigilance;
- séparer strictement perception et interprétation.

### AUD-02 — Interprétation, hypothèses et croyances

**Verdict : VALIDÉ AVEC CORRECTIONS**

Principales corrections :

- séparer génération d’hypothèses, évaluation des preuves et mise à jour;
- introduire des questions épistémiques;
- conserver une hypothèse résiduelle « autre / inconnu »;
- représenter la provenance et les modèles de source;
- séparer confiance épistémique, acceptation pratique, désirabilité et coût de révision;
- gérer les dépendances entre preuves;
- ajouter calibration métacognitive;
- encadrer les inférences sur les intentions et traits d’autrui;
- conserver les contradictions et la généalogie des croyances;
- transformer certaines incertitudes importantes en objectifs d’enquête.

### AUD-03 — Besoins et motivation

**Verdict : VALIDÉ AVEC RESTRUCTURATION**

Principales corrections :

- abandonner les réservoirs psychologiques universels;
- séparer variables régulées, déficits, motifs, désirs et objectifs;
- ajouter régulation prédictive et allostatique;
- séparer wanting, liking et apprentissage;
- retenir autonomie, compétence et relation à autrui comme besoins psychologiques généraux;
- traiter sécurité comme régulation de menace;
- traiter ennui comme signal de désengagement;
- traiter surcharge et récupération comme régulation de charge;
- traiter sexualité comme motivation incitative et contextuelle;
- produire des objets `MotiveCandidate` avant toute décision;
- distinguer pression, urgence, plaisir attendu, importance et coût.

### AUD-04 — Personnalité et attachement

**Verdict : VALIDÉ AVEC RESTRUCTURATION**

Principales corrections :

- traiter les traits comme distributions d’états, non comme commandes;
- conserver Big Five et facettes ciblées;
- ajouter variabilité, inertie et signatures situationnelles;
- faire moduler à la personnalité les mécanismes d’attention, interprétation, émotion, motivation et décision;
- séparer profil dispositionnel, conception de soi et réputation;
- permettre un changement lent par apprentissage et généralisation;
- conserver anxiété et évitement comme dimensions;
- ajouter une hiérarchie général / domaine / relation;
- activer l’attachement surtout sous vulnérabilité, détresse, séparation ou rejet possible;
- représenter hyperactivation et désactivation comme stratégies;
- mettre à jour l’attachement par preuves relationnelles spécifiques.

### AUD-05 — Valeurs, principes et limites personnelles

**Verdict : VALIDÉ AVEC RESTRUCTURATION**

Principales corrections :

- séparer valeurs, principes, limites, normes, lois et contraintes du monde;
- utiliser Schwartz comme bibliothèque de référence, sans en faire une prison;
- représenter les valeurs comme priorités relatives;
- faire des principes des règles contextuelles auto-endossées;
- séparer importance, moralisation, centralité identitaire et résistance au compromis;
- traiter les limites comme politiques contextuelles d’accès;
- distinguer franchissement objectif et violation perçue;
- conserver les conflits entre valeurs;
- permettre la violation consciente d’un principe et ses conséquences;
- séparer valeurs réelles, endossées, déclarées et attribuées;
- permettre une évolution lente et traçable.

### AUD-08 — Ontologie des entités, corps, formes et capacités

**Verdict : VALIDÉ AVEC RESTRUCTURATION MAJEURE**

Principales corrections :

- distinguer référent du monde, entité suivie et enregistrement technique;
- séparer identité, type constitutif, phase, rôle, qualité et relation;
- faire de l'agent une organisation fonctionnelle plutôt qu'une classe d'identité;
- séparer sujet cognitif, contrôleur, corps, manifestation, forme et présence;
- inférer les capacités depuis les composants et l'état;
- représenter les affordances comme des relations situées entre acteur, action, cible et environnement;
- séparer capacité, compétence, possibilité actuelle, permission et autorisation;
- traiter copies, séparations, fusions et remplacements par des transitions d'identité explicites;
- séparer les axes de cycle de vie, d'existence, d'accessibilité et d'archivage;
- conserver des relations temporelles et une provenance inspectable.

### AUD-09 — Sauvegarde, snapshots et personnages réutilisables

**Verdict : VALIDÉ AVEC RESTRUCTURATION IMPORTANTE**

Principales corrections :

- adopter un event sourcing sélectif plutôt qu’universel;
- distinguer commande, proposition LLM, événement canonique et effet externe;
- maintenir journal et état courant dans la même transaction;
- séparer état courant, projections, snapshots, checkpoints, backups et exports;
- rendre le replay indépendant du LLM et capturer les sources de non-déterminisme;
- versionner les événements, réducteurs, projections et migrations;
- traiter les snapshots comme caches reconstruisibles;
- utiliser une outbox persistante pour Discord et les autres effets externes;
- séparer stockage canonique, diagnostics LLM, actifs et contenus sensibles;
- distinguer modèle, version publiée, instance, snapshot d’instance et continuation;
- figer la définition résolue à l’instanciation et interdire toute propagation silencieuse;
- valider les exports par manifeste, provenance et sommes de contrôle;
- tester réellement les sauvegardes par restauration.

### AUD-10 — Interface administrative, registre de composants et validation

**Verdict : VALIDÉ AVEC RESTRUCTURATION IMPORTANTE**

Principales corrections :

- faire de l’interface un client du service canonique, sans écriture SQLite directe;
- utiliser des commandes métier plutôt qu’un CRUD générique pour les changements sensibles;
- versionner et rendre immuables les définitions publiées de composants et capacités;
- séparer définition, instance, état dérivé et présentation;
- utiliser JSON Schema pour la structure et des validateurs distincts pour les invariants sémantiques, temporels, ontologiques et de monde;
- normaliser les unités et séparer valeur canonique de l’affichage;
- produire des résultats de validation structurés avec codes, sévérités, preuves et chemins;
- préparer un plan immuable avant confirmation;
- lier la confirmation à un hash, une version du monde et des cibles;
- refuser les plans devenus obsolètes par concurrence optimiste;
- calculer un rapport d’impact sémantique, pas seulement un diff technique;
- séparer journal canonique, audit administratif et diagnostic;
- appliquer autorisation et moindre privilège côté serveur;
- créer l’univers, la résidence et les personnages par les outils réels du MVP;
- intégrer accessibilité, sécurité locale, idempotence et tests de reprise.

## 4. Audits majeurs restants

**Aucun. Les dix audits majeurs sont terminés.**

## 5. Contrôles de cohérence restants

Ces systèmes ont déjà été explicitement fondés dans la littérature. Ils feront l’objet d’un contrôle plus léger, sauf lacune découverte.

### CTRL-01 — Mémoire

**Verdict : VALIDÉ AVEC CORRECTIONS CIBLÉES**

Principales corrections :

- remplacer l’idée d’une trace originale objective par un enregistrement immuable de l’encodage subjectif;
- étendre la segmentation aux changements internes de buts, émotions, motivations et compréhension;
- séparer encodage, consolidation, représentation stockée, récupération et reconstruction;
- distinguer accessibilité, précision, confiance, vivacité et confiance de source;
- rendre la récupération faillible, guidée par des indices et capable de produire substitutions ou intrusions;
- ne pas traiter chaque rappel comme une reconsolidation;
- représenter la consolidation comme stabilisation, transformation et abstraction;
- conserver un oubli multicausal;
- relier mémoire, croyance, émotion, relation et modèle de soi sans les confondre;
- intégrer la mémoire prospective aux objectifs, à l’attention et à la décision.

### CTRL-02 — Relations

**Verdict : VALIDÉ AVEC CORRECTIONS CIBLÉES ET EXTENSION DE RÉSEAU SOCIAL**

Principales corrections :

- séparer perception de fiabilité, confiance accordée dans une situation et comportement vulnérable;
- rendre la confiance directionnelle, propre à un domaine, un risque et un contexte;
- faire de l’intimité un processus de divulgation et de responsiveness plutôt qu’une simple jauge de proximité;
- ajouter la proximité actuelle, désirée et l’écart toléré par domaine;
- décomposer engagement, satisfaction, investissements, alternatives, prévision future et obligation;
- conserver plusieurs cadres relationnels simultanés;
- rendre pouvoir et dépendance directionnels, structurels et propres à un domaine;
- éviter toute décroissance relationnelle universelle;
- décomposer excuse, pardon, réconciliation, contact et restauration de confiance;
- exiger des preuves comportementales ultérieures pour certaines réparations;
- ajouter une couche de réseau social et de relation collective;
- connecter consentement et secrets sans les absorber dans la relation.

### CTRL-03 — Émotions

**Statut : À VÉRIFIER**

Vérifier couverture, compatibilité avec motivation, décision, expression et régulation.

## 6. Travail futur après l’audit

Une fois l’audit fermé, reprendre la conception des systèmes encore inexistants, toujours avec revue préalable :

- actions et interactions;
- conversations et scènes;
- consentement, permissions, normes et transgressions;
- modèle de soi;
- apprentissage et évolution;
- secrets et circulation de l’information;
- orchestration globale et récupération de contexte LLM.

## 7. État résumé

```text
Audits majeurs terminés : 10
Audits majeurs restants : 0
Contrôles de cohérence restants : 1
Nouvelle conception suspendue : oui
Prochain contrôle : émotions
```

## 8. Règle d’entretien

Mettre ce registre à jour après chaque audit ou contrôle :

- verdict;
- principales corrections;
- conséquences sur les systèmes voisins;
- décisions validées;
- éléments à transférer dans l’index maître et la mémoire détaillée;
- références bibliographiques conservées dans le dossier détaillé de l’audit.
