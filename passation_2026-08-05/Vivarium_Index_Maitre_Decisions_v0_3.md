# Vivarium Social — Index maître des décisions actives

**Version :** 0.3  
**Date :** 4 août 2026  
**Statut :** index de navigation et registre synthétique des décisions courantes  
**Public principal :** propriétaire, assistante architecte et préparation des instructions à l’IA exécutante  

> Ce document sert de porte d’entrée. Il ne remplace ni le code, ni les migrations, ni les tests, ni le dossier maître du dépôt. Il indique rapidement ce qui est implémenté, décidé, différé, encore ouvert ou en attente de transfert normatif.

---

## 1. Hiérarchie des sources

En cas de doute, utiliser cet ordre :

1. **Code, migrations et tests validés**  
   Ils décrivent ce qui existe réellement.

2. **Dossier maître présent dans le dépôt**  
   Il reste l’autorité d’implémentation tant que la demande post-audit n’y a pas été fusionnée.

3. **Demande de changement post-audit et exigences normatives approuvées**  
   Elles décrivent la direction autorisée mais non encore implémentée :
   - `Vivarium_Demande_Changement_Post_Audit_v0_2.md`;
   - `Vivarium_Exigences_Normatives_Post_Audit_v0_1.md`.

4. **Décisions explicites les plus récentes du propriétaire**  
   Elles peuvent préciser ou suspendre une décision avant son transfert documentaire.

5. **Présent index maître**  
   Il résume l’état courant et signale les écarts à réconcilier.

6. **Registre des audits et dossiers détaillés**  
   Ils conservent les verdicts, justifications et corrections :
   - `Vivarium_Registre_Audits_v0_8.md`.

7. **Mémoire de travail de l’assistante**  
   Elle contient le contexte détaillé de continuité.

8. **Cadre de flexibilité des entités et univers**  
   Il contient les cas ontologiques avancés.

Une proposition n’est jamais présentée comme déjà codée. Une décision produit ne devient pas automatiquement une fonctionnalité tant que son lot d’implémentation n’est pas livré et testé.

---

## 2. Photographie immédiate du projet

| Élément | État courant |
|---|---|
| Dernier commit confirmé | `f1335ca` |
| Dernier sous-lot livré | Phase 3.3B1 — blessures persistantes, causalité, récupération et guérison exacte |
| Tests confirmés | 164 |
| Prochain sous-lot | Phase 3.3B2 — effets mécaniques des blessures |
| Prompt préparé | `Vivarium_Prochain_Prompt_DeepSeek_3_3B2.md` |
| Étape demandée à DeepSeek | produire d’abord un plan détaillé, sans code |
| Étape suivante prévue | Phase 3.3C — fermeture reproductible de la Phase 3 |
| IA exécutante principale | DeepSeek via LM Studio Bionic |
| Modèle local Gemma | ne doit pas modifier le projet sans autorisation explicite |
| Persistance actuelle | SQLite, migrations et journal canonique append-only |
| Interface sociale prévue | Discord |
| Interface administrative désormais requise dans le MVP | application web locale minimale |

---

## 3. Définition actuelle du produit

Le Vivarium Social est un simulateur social textuel persistant. Le moteur local possède la réalité canonique. Les agents continuent d’exister entre les interventions du propriétaire, poursuivent des activités, perçoivent le monde selon leurs capacités, forment des croyances, conservent des souvenirs et développent des relations.

Le propriétaire est une entité supérieure connue des personnages. Son pouvoir d’intervention peut être très large, mais il ne possède pas nécessairement une omniscience passive. La perception qu’ont les personnages de ses limites peut évoluer par observation, croyance, enquête et expérience.

La ligne directrice est :

> **Structure rigoureuse, contenu flexible.**

Le système doit rester strict sur la cohérence, tout en permettant des représentations créatives très différentes.

---

## 4. Expérience utilisateur et interfaces

### 4.1 Discord

**Rôle décidé : interface sociale**

Discord sert à :

- observer les scènes;
- discuter avec les personnages;
- recevoir des initiatives, messages et alertes;
- intervenir dans une scène;
- utiliser des commandes simples;
- afficher ou masquer certaines scènes sans modifier leur existence canonique.

Discord ne sert pas à construire des profils complexes, modifier des graphes de lieux ou administrer directement SQLite.

### 4.2 Interface web locale

**Rôle décidé : administration du monde**

Elle doit être utilisable dès la création définitive des quatre profils de référence. Le MVP doit devenir le premier utilisateur de ses propres outils.

Écrans minimaux :

- tableau de bord;
- univers;
- lieux et connexions;
- objets et ressources;
- entités;
- création et modification;
- validation;
- journal et diagnostic.

Aucune interface ne doit écrire directement dans la base :

```text
interface
→ API administrative
→ validation
→ moteur canonique
→ événements
→ SQLite
```

---

## 5. Portée actuelle du MVP

### 5.1 Scénario initial

- un univers actif;
- une résidence contemporaine;
- neuf lieux : salon, cuisine, salle de bain, cour, couloir et quatre chambres;
- quatre profils d’entités de référence;
- temps 1:1 lorsque le monde est actif;
- pause possible;
- rattrapage condensé après une période hors ligne;
- extérieur abstrait possible;
- pas de simulation détaillée d’une ville entière.

### 5.2 Les quatre profils de référence

1. **Humaine sapiente standard**  
   Cas témoin : corps biologique stable, psychologie complète, besoins humains standards.

2. **Louve anthro sapiente**  
   Physiologie et perceptions non humaines, morphologie humanoïde, communication corporelle, psychologie complète sans déterminisme d’espèce.

3. **Chat domestique non sapient**  
   Agent autonome doté de cognition associative, spatiale et sociale, d’habitudes, d’attachement, d’intentions courtes et de communication non verbale.

4. **Slime sapient à apparence féminine**  
   Un corps continu et déformable; hydratation, masse structurelle et énergie; cohésion et précision morphologique dérivées; forme amorphe et silhouette féminine comme configurations du même corps.

### 5.3 Portée du moteur, distincte du scénario

Le moteur ne doit pas coder en dur :

- quatre entités;
- quatre chambres;
- une résidence;
- l’espèce humaine;
- une seule forme;
- une seule conscience;
- une seule manifestation;
- une psychologie humaine complète.

Le MVP utilise quatre profils, mais le noyau doit employer des composants et capacités génériques.

---

## 6. Invariants architecturaux actifs

### ARC-001 — Autorité canonique

Le moteur est l’unique autorité sur la réalité. Le LLM propose, interprète et formule; il ne modifie jamais directement la base.

### ARC-002 — Séparation subjective

```text
réalité canonique
≠ perception
≠ interprétation
≠ croyance
≠ mémoire
```

Une croyance fausse ou un souvenir dégradé ne réécrit pas l’événement réel.

### ARC-003 — Identité persistante

L’identité ne doit pas être confondue avec le nom, l’espèce, le corps, la forme, la position ou une manifestation particulière.

### ARC-004 — Composition générique

Les différences entre entités proviennent de composants, ressources, capacités, canaux perceptifs, profils cognitifs et règles de monde.

Interdiction conceptuelle :

```text
if species == "wolf"
if species == "cat"
if species == "slime"
```

### ARC-005 — Capacités plutôt qu’étiquettes

Une action vérifie les capacités et conditions effectives, pas une catégorie narrative.

### ARC-006 — Événements append-only

Les changements importants sont journalisés. Le passé n’est pas silencieusement écrasé.

### ARC-007 — Calculs déterministes

Les systèmes physiques et temporels emploient des calculs reproductibles, des entiers à précision fixe et des lectures sans effets de bord.

### ARC-008 — Modifications administratives contrôlées

Une modification profonde d’un personnage exige :

- analyse d’impact;
- snapshot;
- confirmation explicite;
- transaction;
- audit.

### ARC-009 — Vie privée distincte de l’affichage

Une scène continue d’exister même si elle n’est pas affichée spontanément. Le propriétaire peut l’inspecter explicitement selon les règles administratives.

### ARC-010 — Sobriété d’implémentation

Concevoir largement ne signifie pas implémenter immédiatement les cas extrêmes. Chaque module du MVP doit servir une fonction utilisée dès sa livraison.

---

## 7. État technique déjà implémenté

### Phase 0

Dépôt, environnement et tests initiaux.

### Phase 1

- SQLite;
- migrations;
- monde persistant;
- événements canoniques append-only;
- moteur comme seul chemin d’écriture.

### Phase 2

- horloge 1:1 dérivée;
- pause et reprise atomiques;
- lectures sans écriture;
- graphe dirigé des lieux;
- calcul de chemin;
- couloir et neuf lieux au total.

### Phase 3 livrée jusqu’ici

- quatre personnages techniques persistants;
- position canonique;
- besoins à précision fixe;
- activités et effets temporels;
- politique déterministe;
- simulation reproductible;
- attente dynamique;
- sommeil naturel;
- blessures persistantes;
- causalité des blessures;
- récupération et guérison exacte.

Les quatre personnages techniques existants doivent être considérés comme des **sujets de test ou placeholders**, sauf décision explicite de les migrer. Les quatre profils définitifs devront passer par le futur gestionnaire d’entités.

---

## 8. Modules administratifs nécessaires au MVP

### ADM-001 — Registre de composants et capacités

Définit les briques disponibles :

- corps;
- formes;
- ressources;
- besoins;
- cognition;
- perception;
- langage;
- capacités;
- vulnérabilités;
- dépendances;
- unités;
- limites;
- incompatibilités.

La première version ne contient que ce qui sert aux quatre profils et à la résidence.

### ADM-002 — API administrative canonique

Doit permettre :

- préparer une opération;
- valider;
- afficher les impacts;
- confirmer;
- appliquer atomiquement;
- produire des événements;
- créer un snapshot;
- archiver et restaurer.

### ADM-003 — Gestionnaire d’univers et d’environnement

Doit gérer :

- règles principales de l’univers;
- lieux;
- connexions;
- accès;
- objets;
- ressources;
- propriétés physiques utiles;
- cycle de vie des éléments.

### ADM-004 — Gestionnaire d’entités

Doit gérer :

- brouillons;
- presets;
- composants;
- corps et formes;
- besoins;
- perceptions;
- capacités;
- cognition;
- psychologie disponible;
- validation;
- activation;
- modification;
- départ;
- archivage;
- inspection.

### ADM-005 — Validateurs

Deux niveaux :

1. cohérence interne du profil;
2. compatibilité entre l’entité et l’univers.

Résultats :

- erreur bloquante;
- avertissement;
- information.

### ADM-006 — Journal administratif et diagnostic

Conserve les opérations, refus, avertissements ignorés, snapshots, événements produits et raisons explicables.

---

## 9. Sauvegarde et persistance

### SAV-001 — Structure d’une entité

Une entité persistante est reconstruite à partir de :

- identité stable;
- composants;
- état courant;
- psychologie;
- relations;
- croyances;
- souvenirs;
- objectifs et engagements;
- historique canonique.

### SAV-002 — État et histoire

Les tables d’état indiquent la situation actuelle. Le journal canonique explique comment elle a été atteinte.

### SAV-003 — Snapshots

Les snapshots accélèrent le chargement et sécurisent les modifications profondes. Ils ne remplacent pas le journal.

### SAV-004 — JSON borné

Le JSON peut contenir des détails extensibles et métadonnées, mais pas l’intégralité opaque d’un personnage.

### SAV-005 — Médias séparés

Les portraits, avatars et médias lourds restent hors de SQLite; la base conserve leurs références.

### SAV-006 — Diagnostic séparable

Les prompts complets, sorties brutes du LLM et traces détaillées peuvent être archivés, compressés ou purgés sans détruire l’état canonique.

---

## 10. Bibliothèque de personnages réutilisables

### LIB-001 — Modèle distinct de l’instance

Un personnage réutilisable est conservé comme modèle indépendant des mondes.

Le modèle contient les paramètres constitutifs initiaux :

- identité de référence;
- apparence;
- morphologie;
- composants;
- besoins;
- perceptions;
- capacités;
- cognition;
- personnalité;
- valeurs et préférences de départ;
- style de langage;
- éléments initiaux facultatifs.

### LIB-002 — Nouvelle vie par instanciation

Ajouter un modèle à un monde crée une nouvelle entité avec un nouvel identifiant et sans l’histoire acquise dans une instance précédente.

### LIB-003 — Pas de propagation silencieuse

Modifier le modèle ne modifie pas automatiquement les instances déjà actives.

### LIB-004 — Export portable

Un modèle pourra être exporté avec manifeste, données structurées, version de schéma et médias.

---


## 11. Fondation psychologique après audit

**Statut : consolidé normativement, non implémenté dans son ensemble**

### PSY-001 — Chaîne générale

```text
monde canonique
→ signaux accessibles
→ perception
→ interprétation et croyances
→ appraisal et émotions
→ régulation et motifs
→ objectifs, engagements et intentions
→ options
→ arbitrage borné
→ action validée
→ conséquences
→ mémoire, relations et apprentissage
```

### PSY-002 — Distinctions obligatoires

```text
besoin ≠ motif ≠ objectif
trait ≠ état
valeur ≠ principe ≠ limite ≠ norme
objectif ≠ intention ≠ plan ≠ action
émotion ≠ humeur ≠ étiquette
souvenir ≠ croyance
affection ≠ confiance ≠ consentement
```

### PSY-003 — Décision

Une intention continue par défaut. L’arbitrage génère peu d’options, élimine l’impossible, conserve les conflits personnels et sociaux, puis sélectionne une solution suffisamment acceptable.

### PSY-004 — Mémoire

La mémoire conserve l’encodage subjectif, les épisodes, le gist, les détails, la provenance, les reconstructions, les révisions et l’oubli multicausal.

### PSY-005 — Relations

Les relations sont directionnelles, multidimensionnelles et fondées sur des preuves. Confiance, intimité, pouvoir, engagement, réparation et réseau social sont distincts.

### PSY-006 — Émotions

Les émotions sont des processus multi-composants produits par des appraisals. La régulation peut être personnelle ou interpersonnelle et reste soumise aux permissions.

### PSY-007 — Référence normative

Le détail se trouve dans :

- `Vivarium_Exigences_Normatives_Post_Audit_v0_1.md`;
- `Vivarium_Registre_Audits_v0_8.md`;
- les dix audits et trois contrôles associés.

## 12. Rôle et coût du LLM

Le LLM sert surtout à :

- générer des options sociales plausibles;
- interpréter une situation ambiguë;
- formuler un dialogue;
- produire une réaction nuancée;
- aider à consolider ou résumer certains éléments.

Il ne doit pas être appelé pour chaque tick, déplacement, besoin ou routine.

Le coût principal du projet dépendra de :

- la fréquence des appels;
- la taille du contexte;
- le nombre d’agents impliqués;
- la récupération ciblée des souvenirs;
- la capacité à regrouper ou éviter les appels.

Le moteur déterministe, SQLite, les validations, besoins, déplacements et journaux doivent rester légers sur une machine ordinaire.

---


## 13. Ordre de travail courant

### Immédiat — fermer la Phase 3

1. relire le prompt de 3.3B2 contre les exigences post-audit;
2. demander à DeepSeek un plan détaillé sans code;
3. approuver puis faire implémenter 3.3B2;
4. vérifier tests, régression, événements et commit;
5. préparer et livrer 3.3C;
6. effectuer l’audit de fermeture technique.

### Ensuite — intégrer la norme au dépôt

1. fusionner `Vivarium_Demande_Changement_Post_Audit_v0_2.md` dans un dossier maître v0.2;
2. ajouter une matrice de traçabilité;
3. arrêter l’ordre réel des nouveaux lots.

### Vertical slice administratif

1. registre minimal de composants, capacités et unités;
2. validation structurelle et sémantique;
3. API `prepare / validate / impact / confirm`;
4. journal administratif;
5. gestionnaire d’univers;
6. gestionnaire de modèles et d’entités;
7. interface web locale;
8. création ou migration de la résidence;
9. création ou migration des quatre profils définitifs.

### Puis

- actions et affordances;
- permissions, limites et consentement;
- manifestations et scènes;
- perception;
- cognition et mémoire;
- émotions et motivation;
- décision;
- conversations et relations;
- Discord.

La feuille de route détaillée est `Vivarium_Feuille_Route_Post_Audit_v0_1.md`.

## 14. Éléments différés

- duplication et clones conscients;
- fusion;
- possession;
- plusieurs corps actifs;
- consciences collectives;
- temporalité subjective complexe;
- dépendances existentielles avancées;
- absorption d’autres agents par le slime;
- fragmentation autonome du slime;
- copie identitaire parfaite;
- masse ou régénération illimitées;
- maladies;
- vieillissement;
- grossesse;
- mort dans l’univers initial;
- amputation ou dommage corporel involontaire permanent dans l’univers initial;
- respawn;
- simulation détaillée d’une ville;
- éditeur psychologique avancé avant l’existence des systèmes correspondants;
- moteur de plugins universel;
- appels LLM systématiques pour les routines;
- interface finale polie avant validation du vertical slice.

---

## 15. Décisions encore ouvertes, non bloquantes

### Produit et personnages

- noms, biographies, apparences et avatars définitifs;
- traits concrets des trois personnages sapients;
- sexe, âge de vie et détails individuels du chat;
- paramètres exacts de nutrition, hydratation et cohésion du slime;
- degré de chaos et d’imprévisibilité recherché;
- limites morales et sociales détaillées de l’univers initial.

### Propriétaire

- ce que les personnages savent exactement de ses capacités d’observation;
- règles précises de manifestation et d’attention;
- traitement des secrets et accords privés avec lui.

### Environnement

- détails des portes, serrures et permissions permanentes;
- gravité sociale par défaut d’une intrusion;
- objets et ressources définitifs de la résidence.

### Interfaces et exploitation

- technologie web retenue;
- structure exacte des salons Discord;
- fréquence des messages spontanés;
- durée de conservation des logs techniques et conversations brutes;
- format final des paquets exportables de personnages.

Ces choix ne bloquent pas 3.3B2 ou 3.3C.

---

## 16. Réconciliations et formulations remplacées

### REC-001 — « Discord est l’interface principale »

Formulation actuelle :

- Discord est l’interface sociale principale;
- l’application web locale est l’interface administrative;
- les deux appartiennent au MVP.

### REC-002 — « Quatre personnages fixes » contre moteur flexible

Formulation actuelle :

- le scénario MVP utilise quatre profils de référence;
- le moteur ne doit pas imposer une population fixe.

### REC-003 — Personnages techniques déjà seedés

Formulation actuelle :

- les entités existantes servent à tester le moteur déterministe;
- les quatre profils définitifs doivent être créés ou instanciés avec le gestionnaire réel;
- une migration ou un remplacement contrôlé sera décidé lors du lot administratif.

### REC-004 — « Quatre habitantes adultes »

Cette formulation historique n’est plus assez précise depuis l’ajout d’un chat non sapient.

Formulation de travail :

- trois personnages sapients à apparence féminine dans le casting de référence;
- un chat domestique non sapient;
- l’âge, le sexe et les détails individuels du chat seront fixés avant son instanciation;
- toute entité sapiente impliquée dans du contenu adulte doit être explicitement adulte.

### REC-005 — Résidence codée comme vérité universelle

Formulation actuelle :

- la résidence contemporaine est le preset initial;
- l’univers et les lieux doivent pouvoir être créés par des mécanismes génériques.

### REC-006 — Plan de Phase 4 antérieur

Le dossier de travail prévoit actions, scènes, événements et perceptions en Phase 4. La décision plus récente rend également nécessaire un vertical slice administratif avant la création définitive des quatre profils.

Action requise :

- ne pas réordonner silencieusement le dépôt;
- produire une demande de changement après la fermeture de la Phase 3;
- conserver les contrats d’actions et de perceptions, mais intégrer le gestionnaire au chemin critique.

---


## 17. Carte documentaire

| Document | Usage |
|---|---|
| `Vivarium_Index_Maitre_Decisions_v0_3.md` | porte d’entrée et état synthétique |
| `Vivarium_Memoire_Assistante_v10.md` | mémoire détaillée de continuité |
| `Vivarium_Registre_Audits_v0_8.md` | clôture des dix audits et trois contrôles |
| `Vivarium_Exigences_Normatives_Post_Audit_v0_1.md` | invariants vérifiables issus des audits |
| `Vivarium_Demande_Changement_Post_Audit_v0_2.md` | delta à fusionner dans le dossier maître |
| `Vivarium_Feuille_Route_Post_Audit_v0_1.md` | ordre des lots après audit |
| `Vivarium_Cadre_Flexibilite_Entites_Univers_v0_3.md` | cas ontologiques avancés |
| `Vivarium_Prochain_Prompt_DeepSeek_3_3B2.md` | prompt actuel à relire avant transmission |
| `Dossier_maitre_IA_vivarium_social_v0_1.md` | autorité actuelle du dépôt avant fusion |
| `Vivarium_social_paquet_IA_v0_1.zip` | ancien paquet documentaire consolidé |

## 18. Format obligatoire d’un futur prompt d’implémentation

Chaque prompt à DeepSeek doit contenir uniquement ce qui sert au lot :

1. commit et tests de départ;
2. état existant à inspecter;
3. objectif borné;
4. invariants concernés;
5. fichiers ou systèmes probablement touchés;
6. exclusions explicites;
7. transactions et événements attendus;
8. matrice de tests;
9. format du rapport de livraison;
10. ordre d’arrêt.

La documentation complète sert à préparer le lot; elle ne doit pas être injectée en bloc dans chaque prompt.

---

## 19. Règle d’entretien de cet index

Mettre à jour l’index lorsqu’un des événements suivants arrive :

- nouveau commit livré;
- changement du nombre de tests;
- décision explicite du propriétaire;
- changement du chemin critique;
- ajout ou retrait d’un élément du MVP;
- résolution d’une décision ouverte;
- conflit détecté entre code, dossier maître et mémoire;
- création d’un nouveau document normatif.

Ne pas supprimer silencieusement les anciennes décisions. Les déplacer dans les réconciliations, les marquer comme remplacées ou les conserver dans l’historique détaillé.

---

## 20. Prochaine action documentaire

Après livraison de 3.3B2 :

- actualiser la photographie technique;
- consigner les seuils et règles effectivement livrés;
- retirer les hypothèses devenues fausses;
- préparer le prompt exact de 3.3C.

Après fermeture de la Phase 3 :

- produire une demande de changement normative intégrant le vertical slice administratif;
- arrêter le nouvel ordre des phases avec l’état réel du dépôt;
- préparer le premier lot du registre minimal de composants et capacités.

## 21. Audit rétroactif des systèmes

**TERMINÉ**

```text
Audits majeurs terminés : 10
Contrôles de cohérence terminés : 3
Éléments ouverts dans l’audit : 0
```

Verdicts :

- attention et perception — validé avec corrections;
- croyances — validé avec corrections;
- besoins — validé avec restructuration;
- personnalité — validé avec restructuration;
- valeurs et limites — validé avec restructuration;
- objectifs et intentions — validé avec restructuration importante;
- décision — validé avec restructuration majeure;
- ontologie — validé avec restructuration majeure;
- persistance — validé avec restructuration importante;
- administration — validé avec restructuration importante;
- mémoire — validé avec corrections ciblées;
- relations — validé avec corrections ciblées et extension réseau;
- émotions — validé avec corrections ciblées et régulation interpersonnelle.

## 22. Consolidation normative

**TERMINÉE**

Produits :

- exigences normatives post-audit;
- demande de changement v0.2;
- feuille de route;
- index maître v0.3;
- mémoire de continuité v10;
- registre d’audit v0.9.

La norme post-audit décrit la direction autorisée. Elle ne doit pas être présentée comme déjà implémentée.

## 23. Prochaine action

Relire et réviser `Vivarium_Prochain_Prompt_DeepSeek_3_3B2.md`, puis l’envoyer à DeepSeek pour produire **un plan seulement, sans code**.
