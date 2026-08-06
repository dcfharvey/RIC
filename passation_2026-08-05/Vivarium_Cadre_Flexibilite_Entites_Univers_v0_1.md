# Vivarium Social — Cadre de flexibilité des entités, corps et univers

**Version :** 0.1  
**Date :** 4 août 2026  
**Statut :** proposition d’architecture à intégrer au dossier maître après validation  
**Objet :** permettre une création extrêmement libre sans abandonner l’exécution rigoureuse du moteur

> Philosophie directrice : **simulateur rigoureux dans son exécution, créatif dans sa représentation.**
>
> Le système doit être fermé sur la cohérence et ouvert sur l’imagination.

---

## 1. But du document

Ce document définit une architecture capable de représenter, dans une même réalité canonique :

- des humains ordinaires;
- des animaux non sapients;
- des créatures intelligentes non humaines;
- des personnages anthropomorphes;
- des shapeshifters;
- des fantômes, robots, IA et objets conscients;
- des consciences collectives;
- des entités distribuées sur plusieurs corps;
- plusieurs consciences dans un même corps;
- des créatures eldritch;
- des êtres dont l’existence, la cognition ou la temporalité diffère radicalement de celles des humains.

Le but n’est pas d’implémenter tous ces cas dans le MVP. Le but est d’éviter que les choix structurels du MVP rendent leur ajout ultérieur impossible ou nécessitent une réécriture du moteur.

---

## 2. Principe fondamental : structure rigoureuse, contenu flexible

**DÉCIDÉ EN PRINCIPE**

Tout élément créatif peut être inventé. Toutefois, tout élément qui produit un effet réel doit déclarer comment il s’insère dans les systèmes du moteur.

Une description narrative peut affirmer qu’une dragonne possède de grandes ailes bronze. Cela reste décoratif tant qu’aucune conséquence mécanique n’est attendue.

Si ces ailes permettent de voler, gênent le passage dans un couloir, peuvent être blessées ou produisent un déplacement d’air, leurs propriétés pertinentes doivent être structurées.

Le moteur ne doit pas comprendre le mot « dragonne » comme une règle magique. Il doit comprendre :

- quelles capacités existent;
- quelles conditions les activent;
- quels coûts elles exigent;
- quelles contraintes les limitent;
- quels effets elles produisent;
- quels événements sont journalisés.

### 2.1 Règle d’or

> La création définit ce qui existe. Les contrats définissent comment cela agit.

### 2.2 Ce qui doit rester universel

- identité persistante;
- causalité canonique;
- versionnement;
- validation;
- événements append-only;
- références historiques stables;
- permissions d’écriture;
- contrats des capacités;
- règles explicites du monde;
- distinction entre données descriptives et effets mécaniques.

### 2.3 Ce qui doit rester configurable

- nombre de personnages;
- nature des personnages;
- nombre et nature des lieux;
- temporalité;
- mortalité;
- physiologie;
- besoins;
- formes corporelles;
- capacités;
- statut juridique et social;
- règles de population;
- limites d’espace;
- canaux de perception;
- organisation de la conscience;
- relation entre identité, corps et manifestations.

---

## 3. Ne pas confondre les concepts fondamentaux

L’architecture doit séparer plusieurs notions souvent fusionnées dans les jeux ou simulateurs simples.

### 3.1 Entité

Une **entité** est quelque chose qui possède une identité canonique persistante dans le monde.

Exemples :

- une personne;
- une marmotte;
- une IA;
- une guilde;
- une épée consciente;
- une manifestation temporaire;
- un corps;
- une pièce consciente;
- un objet ordinaire.

Toutes les entités ne sont pas des agents. Toutes les entités n’ont pas de corps. Toutes les entités ne sont pas vivantes.

### 3.2 Agent

Un **agent** est une entité, ou un composant d’entité, capable de sélectionner ou proposer des actions selon un état interne.

Un agent peut être :

- réactif;
- associatif;
- social;
- délibératif;
- réflexif.

L’agentivité n’implique ni langage, ni sapience humaine, ni conscience de soi.

### 3.3 Identité

L’**identité** répond à la question : « de qui ou de quoi parle-t-on à travers le temps? »

Elle doit rester distincte :

- du corps actuel;
- du nom visible;
- de la forme active;
- du rôle social;
- du lieu occupé;
- du niveau cognitif actuel.

### 3.4 Conscience ou centre cognitif

Un **centre cognitif** possède tout ou partie de :

- perceptions;
- mémoire;
- croyances;
- émotions;
- objectifs;
- capacité de décision;
- continuité subjective.

Une entité peut avoir zéro, un ou plusieurs centres cognitifs.

### 3.5 Corps

Un **corps** est une structure physique ou fonctionnelle servant de support à certaines actions, perceptions et conditions.

Une identité peut :

- n’avoir aucun corps;
- avoir un seul corps;
- changer de corps;
- posséder plusieurs corps simultanément;
- partager un corps avec une autre conscience.

### 3.6 Forme

Une **forme** est une configuration cohérente des propriétés d’un corps ou d’une manifestation.

Elle peut modifier :

- morphologie;
- dimensions;
- locomotion;
- besoins;
- vulnérabilités;
- capacités;
- perception;
- compatibilité avec les objets et lieux.

### 3.7 Manifestation

Une **manifestation** est une présence locale par laquelle une entité peut être perçue ou agir.

Exemples :

- corps principal;
- avatar;
- projection;
- copie temporaire;
- tentacule apparaissant dans une pièce;
- voix dans un miroir;
- hologramme;
- présence dans un rêve.

Une manifestation ne doit pas être confondue automatiquement avec une identité complète.

### 3.8 Personnage

« Personnage » reste un terme d’expérience utilisateur. Techniquement, un personnage est une composition d’entité, d’agentivité, de cognition, de présence et éventuellement de corps.

---

## 4. Relation non obligatoire entre identité, conscience, corps et présence

**PROPOSÉ COMME INVARIANT ARCHITECTURAL**

Le moteur ne doit jamais supposer :

```text
1 identité = 1 conscience = 1 corps = 1 position
```

Il doit accepter les relations suivantes.

### 4.1 Cas ordinaire

```text
1 identité
→ 1 centre cognitif
→ 1 corps
→ 1 manifestation physique
→ 1 position principale
```

Humain ordinaire, animal ordinaire, dragonne anthro stable.

### 4.2 Shapeshifter

```text
1 identité
→ 1 centre cognitif
→ 1 corps persistant ou remplaçable
→ plusieurs formes possibles
→ 1 forme active à la fois, sauf règle contraire
```

### 4.3 Plusieurs consciences dans un corps

```text
plusieurs identités ou centres cognitifs
→ 1 corps partagé
→ contrôle exclusif, alterné ou conjoint
```

Exemples : possession, symbiote, pluralité fictive, pilote et organisme.

### 4.4 Une conscience dans plusieurs corps

```text
1 identité
→ 1 centre cognitif partagé
→ plusieurs corps ou manifestations
→ mémoire et décision centralisées ou synchronisées
```

Exemples : ruche, IA distribuée, créature eldritch.

### 4.5 Copie et divergence

```text
1 identité historique initiale
→ événement de duplication
→ 2 nouvelles continuités identitaires
→ souvenirs communs jusqu’au point de divergence
```

Le moteur doit conserver la filiation sans prétendre que les copies restent la même personne indéfiniment.

### 4.6 Fusion

```text
plusieurs identités préexistantes
→ événement de fusion
→ nouvelle identité ou identité composite
→ règles explicites de mémoire, relations et responsabilité
```

### 4.7 Agent sans corps

```text
1 identité
→ cognition
→ aucune présence physique permanente
→ actions via réseau, objets, projections ou permissions du monde
```

### 4.8 Objet-agent

```text
1 entité
→ propriétés d’objet
+ cognition ou agentivité
```

Une épée consciente peut être transportée comme objet et participer aux relations comme agent.

---

## 5. Modèle à composants

**PROPOSÉ**

Les entités doivent être composées de modules activables, plutôt que dériver d’une classe monolithique « personnage humain ».

### 5.1 Noyau minimal d’une entité

- identifiant permanent;
- type technique générique;
- nom et descriptions visibles;
- statut de cycle de vie;
- version de schéma;
- métadonnées de provenance;
- journal des événements associés.

### 5.2 Composants facultatifs

- `agency` : capacité de sélectionner des actions;
- `cognition` : perceptions, croyances, mémoire, délibération;
- `body` : état physique et morphologie;
- `form_set` : formes disponibles;
- `manifestation_set` : présences locales;
- `needs` : pressions internes;
- `emotion` : émotions et humeur;
- `personality` : dispositions;
- `values` : principes;
- `goals` : objectifs;
- `commitments` : engagements;
- `relations` : liens ciblés;
- `language` : moyens d’expression et compréhension;
- `inventory` : possession ou contrôle d’objets;
- `legal_status` : personne, animal, propriété, citoyen, etc.;
- `social_roles` : résidente, invitée, gardienne, familière;
- `capabilities` : actions et effets accessibles;
- `perception_channels` : vision, audition, télépathie, etc.;
- `existence_dependencies` : lien à un objet, invocateur ou condition;
- `subjective_time` : rapport propre au temps;
- `ownership` : droits sur espaces et objets.

### 5.3 Absence d’un composant

L’absence doit être valide et signifiante.

Exemples :

- une marmotte n’utilise pas nécessairement les valeurs morales complexes;
- une IA n’a pas de faim biologique;
- un fantôme n’a pas de masse;
- une plante consciente n’a pas de locomotion;
- une entité eldritch n’utilise pas forcément la psychologie humaine complète;
- un objet ordinaire n’a ni cognition ni agentivité.

Le système ne doit pas créer automatiquement de fausses valeurs par défaut pour remplir les cases.

---

## 6. Profils cognitifs modulaires

**PROPOSÉ**

La cognition ne doit pas être binaire : « humaine » ou « absente ».

### 6.1 Capacités cognitives indépendantes

- réaction aux stimuli;
- apprentissage associatif;
- reconnaissance d’entités;
- mémoire épisodique;
- mémoire sémantique;
- émotions;
- attachement social;
- anticipation simple;
- objectifs persistants;
- planification;
- compréhension du langage;
- production du langage;
- théorie de l’esprit;
- valeurs abstraites;
- engagements explicites;
- réflexion sur soi;
- raisonnement contrefactuel.

### 6.2 Profils pratiques

Les profils sont des presets, pas des catégories ontologiques rigides.

#### Réactif

Réflexes, attraction, évitement, douleur, peur.

#### Associatif

Apprentissage, habitudes, reconnaissance, anticipation locale.

#### Social

Attachement, signaux sociaux, hiérarchie, coopération simple.

#### Délibératif

Objectifs, choix entre options, planification limitée.

#### Réflexif

Valeurs, identité personnelle, croyances complexes, métacognition.

### 6.3 Exemple : marmotte

Composants probables :

- corps;
- besoins physiques;
- perception;
- mémoire associative;
- émotions simples;
- attachement;
- habitudes;
- agentivité réactive et associative.

Composants probablement absents :

- valeurs abstraites;
- engagements verbaux;
- objectifs de vie complexes;
- langage symbolique élaboré.

### 6.4 Exemple : Vaporeon

Le preset d’espèce ne suffit pas. Le créateur doit définir son statut cognitif dans l’univers :

- animal intelligent non verbal;
- compagnon sapient;
- personne non humaine;
- télépathe;
- créature magique à cognition partielle.

Espèce, cognition, langage, statut social et autonomie doivent rester distincts.

---

## 7. Corps, morphologie et physiologie

### 7.1 Le corps comme assemblage

Un corps peut déclarer :

- structure générale;
- dimensions;
- masse;
- segments ou organes fonctionnels;
- modes de locomotion;
- sens;
- besoins biologiques;
- réserves;
- vulnérabilités;
- résistances;
- blessures possibles;
- compatibilité avec objets et lieux;
- conditions environnementales nécessaires.

### 7.2 Morphologie sans sursimulation

Le moteur ne doit pas simuler chaque os ou muscle par défaut.

Il faut représenter uniquement les propriétés ayant une conséquence dans l’expérience :

- hauteur ou largeur pertinentes aux passages;
- nombre de membres si cela change les actions;
- ailes si elles servent au vol ou peuvent être blessées;
- queue si elle manipule ou gêne;
- quadrupédie si elle affecte les objets utilisables;
- branchies si l’environnement aquatique compte.

### 7.3 Attribut descriptif contre attribut mécanique

```text
Description : écailles bronze brillantes
Mécanique : aucune
```

```text
Description : écailles ignifuges
Mécanique : résistance thermique déclarée
```

Le créateur doit pouvoir laisser un attribut purement esthétique sans lui inventer un effet artificiel.

### 7.4 Besoins modulaires

Les besoins ne sont pas universellement imposés.

Un corps peut :

- manger normalement;
- absorber de l’énergie;
- ne jamais manger;
- dormir;
- entrer en veille;
- se régénérer;
- dépendre de l’eau;
- exiger une température particulière;
- être intemporel.

Chaque besoin activé utilise un contrat commun : état, évolution, seuils, modes de satisfaction et conséquences.

---

## 8. Formes et transformation

### 8.1 Formes déclarées

Une forme doit contenir un ensemble cohérent de :

- morphologie;
- dimensions;
- capacités;
- vulnérabilités;
- besoins;
- perception;
- apparence;
- compatibilités.

### 8.2 Transformation comme action canonique

Une transformation doit déclarer :

- forme source;
- forme cible;
- conditions;
- durée;
- coût;
- lieu requis ou interdit;
- interruption possible;
- effets produits;
- conservation des objets;
- continuité des blessures;
- continuité des besoins;
- événements émis.

### 8.3 Continuité configurable

Pour chaque état, il faut pouvoir dire s’il appartient :

- à l’identité;
- au centre cognitif;
- au corps;
- à la forme;
- à la manifestation.

Exemples :

- une promesse appartient à l’identité;
- une aile blessée peut appartenir à la forme draconique;
- la fatigue peut être transversale;
- une armure portée peut rester au sol lors de la transformation;
- une mémoire peut être partagée ou inaccessible selon la forme.

### 8.4 Métamorphose progressive

Le moteur doit pouvoir représenter une transformation graduelle par une suite d’événements et de versions de corps, plutôt que seulement un changement instantané.

---

## 9. Manifestations multiples et présence

### 9.1 Modèles de présence

- unique;
- multiple;
- distribuée;
- projetée;
- abstraite;
- conditionnelle;
- imbriquée dans une autre entité.

### 9.2 Position

La position ne doit pas appartenir obligatoirement à l’identité entière. Elle appartient généralement à une manifestation.

Ainsi, une entité distribuée peut avoir plusieurs positions actives.

### 9.3 Action à travers une manifestation

Chaque manifestation déclare :

- quelles capacités elle porte;
- quels sens elle utilise;
- quelle part de l’état elle partage;
- qui la contrôle;
- ce qui arrive lorsqu’elle est détruite ou dissipée.

### 9.4 Synchronisation

Pour plusieurs corps ou avatars, préciser :

- mémoire instantanément partagée;
- mémoire synchronisée avec délai;
- mémoire séparée puis fusionnée;
- contrôle central;
- contrôle autonome local;
- perte d’information à la disparition.

---

## 10. Capacités contractuelles

**DÉCIDÉ EN PRINCIPE**

Les actions doivent dépendre de capacités déclarées, jamais d’un test direct sur l’espèce.

Mauvais :

```text
si espèce == dragonne : autoriser_vol
```

Correct :

```text
si capacité(vol)
et environnement compatible
et état corporel compatible
et coût payable
alors proposer ou autoriser l’action
```

### 10.1 Contrat minimal d’une capacité

- identifiant stable;
- version;
- source ou porteur;
- actions exposées;
- conditions d’activation;
- cibles valides;
- portée;
- coût;
- durée;
- effets canoniques;
- risques;
- temps de récupération;
- interactions connues;
- événements produits;
- règles d’échec;
- permissions requises.

### 10.2 Capacités passives

Exemples :

- résistance au feu;
- vision nocturne;
- perception télépathique;
- immunité à un besoin;
- existence non locale.

Une capacité passive doit encore préciser quand et comment elle s’applique.

### 10.3 Capacités extraordinaires

Même une capacité qui « brise une règle » doit déclarer :

- quelle règle elle contourne;
- à quel niveau;
- sous quelles conditions;
- quelles règles restent applicables;
- quelles traces elle laisse.

Une créature eldritch ne peut pas simplement avoir `ignore_rules = true`.

---

## 11. Perception non humaine

Les canaux de perception doivent être modulaires.

Exemples :

- vision;
- audition;
- odorat;
- écholocation;
- vision thermique;
- perception magique;
- télépathie;
- perception des émotions;
- perception des rêves;
- perception d’objets marqués;
- perception non locale;
- souvenirs du futur;
- conscience des événements dirigés vers soi.

Chaque canal déclare :

- source;
- portée;
- résolution;
- conditions;
- obstacles;
- latence;
- fiabilité;
- type d’information produit;
- coût éventuel;
- possibilité d’être détecté.

Le canal produit une perception subjective; il ne copie pas automatiquement toute la vérité canonique.

---

## 12. Duplication, copie et divergence

### 12.1 Événement de duplication

Une duplication doit créer :

- une relation de provenance;
- un point de divergence;
- des identifiants distincts;
- un état partagé initial clairement défini;
- une politique de propriété et d’engagements;
- une règle de reconnaissance sociale.

### 12.2 Ce qui ne doit pas être implicite

- que les copies sont juridiquement la même personne;
- qu’elles partagent encore leurs souvenirs;
- qu’un engagement pris avant duplication oblige les deux de la même façon;
- qu’une relation romantique se transfère automatiquement;
- qu’une possession appartient à toutes les copies.

### 12.3 Fusion ultérieure

Une fusion de copies doit être un nouvel événement explicite avec politique de résolution des divergences.

---

## 13. Fusion

Une fusion doit préciser :

- identités sources;
- identité résultante;
- durée;
- contrôle;
- mémoire accessible;
- personnalité résultante;
- relations héritées;
- engagements hérités;
- possessions;
- responsabilité juridique;
- possibilité de séparation;
- changements physiques.

Le moteur ne doit pas « moyenner » automatiquement deux psychologies sans règle déclarée.

---

## 14. Possession et contrôle partagé

### 14.1 Séparer les rôles

- propriétaire du corps;
- occupant ou conscience présente;
- contrôleur actuel;
- décideur;
- auteur physique de l’action;
- responsable perçu;
- mémoire de l’événement.

### 14.2 Modes de contrôle

- exclusif;
- alterné;
- négocié;
- majoritaire;
- hiérarchique;
- réflexes corporels autonomes;
- contrôle partiel de certains membres ou capacités.

### 14.3 Consentement et contrainte

Une possession volontaire, forcée ou inconsciente ne doit pas être représentée de la même façon.

---

## 15. Conscience collective

Une conscience collective peut être représentée comme :

- une identité collective avec plusieurs manifestations;
- plusieurs identités liées par un réseau cognitif;
- une identité supérieure composée de membres autonomes;
- un partage partiel de mémoire et d’émotions.

Le système doit préciser :

- niveau d’autonomie locale;
- partage de mémoire;
- partage des objectifs;
- conflits internes;
- identité sociale des membres;
- conséquences de la perte d’un corps;
- possibilité de séparation.

---

## 16. Temporalité subjective

Le temps canonique du monde et le temps subjectif d’une entité doivent être séparables.

Cas possibles :

- pensée accélérée;
- hibernation;
- stase;
- existence intemporelle;
- boucle locale;
- perception du futur;
- mémoire rétrocausale;
- actions seulement lors des scènes.

### 16.1 Garde-fou

Une temporalité étrange doit toujours déclarer comment elle se projette sur l’ordre canonique des événements.

Le journal canonique reste ordonné même si une entité le perçoit autrement.

---

## 17. Dépendances existentielles

Une entité peut dépendre de :

- un objet-ancre;
- un lieu;
- une personne;
- un serveur;
- un rituel;
- une croyance collective;
- une condition environnementale;
- une source d’énergie.

Le contrat doit déclarer :

- condition d’existence ou d’activité;
- comportement lorsque la condition cesse;
- délai;
- persistance de la mémoire;
- possibilité de restauration;
- événements produits.

---

## 18. Statut social, légal et moral

**PROPOSÉ**

L’espèce et la cognition ne déterminent pas automatiquement le statut social ou juridique.

Le monde peut distinguer :

- personne juridique;
- résidente;
- invitée;
- animal;
- animal protégé;
- propriété;
- citoyenne;
- familière;
- entité dangereuse;
- souveraine;
- objet conscient reconnu ou non reconnu.

Ces statuts appartiennent aux règles de l’univers et peuvent être injustes ou contestés par les personnages.

---

## 19. Environnement et compatibilité

Les lieux sont eux aussi composables.

### 19.1 Propriétés possibles

- dimensions;
- volume;
- topologie;
- connexions;
- capacité dure;
- capacité de confort;
- température;
- pression;
- atmosphère;
- gravité;
- eau;
- ventilation;
- lumière;
- matériaux;
- inflammabilité;
- intimité;
- propriété;
- accès;
- fonctions;
- règles locales;
- compatibilités corporelles.

### 19.2 Pas de réalisme obligatoire

Une bulle intemporelle peut avoir un espace non borné. Un couloir réaliste peut limiter une grande envergure. Une porte magique peut adapter sa taille.

Le moteur applique les propriétés déclarées, pas une conception universelle de l’architecture humaine.

### 19.3 Ressources et affordances

Une action est disponible parce qu’un lieu, un objet ou une capacité fournit l’affordance nécessaire.

Une cuisine ne permet pas de cuisiner parce qu’elle porte l’étiquette `kitchen`, mais parce qu’elle contient les ressources et fonctions pertinentes.

---

## 20. Presets, prototypes et instances

### 20.1 Preset

Un preset est un ensemble de valeurs proposées pour accélérer la création.

Exemples :

- humaine adulte;
- marmotte;
- Vaporeon sapient;
- dragonne anthro;
- fantôme;
- IA domestique;
- bulle intemporelle;
- résidence contemporaine.

### 20.2 Prototype

Un prototype peut être hérité puis modifié, mais l’instance doit conserver une version résolue et validable de ses propriétés.

### 20.3 Instance

Une instance peut contredire son preset.

Exemple : une dragonne sans vol, végétarienne et vulnérable au feu.

Le mot « dragonne » ne doit pas réimposer silencieusement les valeurs du preset après la création.

### 20.4 Versionnement

Les presets doivent être versionnés. Modifier le preset futur ne doit pas modifier rétroactivement les instances existantes sans migration explicite.

---

## 21. Validation à la création

Avant activation, le moteur ou l’outil de création doit produire un rapport.

### 21.1 Validation structurelle

- identifiants uniques;
- composants compatibles;
- références valides;
- contrats complets;
- versions supportées;
- absence de cycles invalides dans les dépendances.

### 21.2 Validation de cohérence

- modes de déplacement utilisables;
- environnement respirable ou règle d’immunité;
- besoins satisfaisables ou conséquences acceptées;
- forme active valide;
- contrôle des manifestations défini;
- capacité avec coûts et effets;
- cognition compatible avec les modules utilisés.

### 21.3 Compatibilité avec le monde

Le rapport doit distinguer :

- **bloquant** : contradiction logique ou contrat incomplet;
- **dangereux** : création valide, mais conséquences graves prévisibles;
- **inconfortable** : compatibilité partielle faisant partie du scénario;
- **informatif** : différence notable sans problème.

Exemple :

```text
Création valide : oui
- peut respirer dans la résidence : oui
- peut utiliser les passages principaux : oui
- ailes impossibles à déployer dans le couloir : inconfortable
- souffle de feu en intérieur : dangereux
- nourriture disponible : partielle
```

### 21.4 Ne pas surbloquer

Une incompatibilité narrative intéressante ne doit pas être refusée.

Une dragonne trop grande pour sa chambre peut exister. Le moteur doit seulement rendre cette contrainte réelle.

---

## 22. Extension contrôlée du moteur

### 22.1 Configuration contre nouvelle mécanique

Le système doit distinguer :

- nouvelle combinaison de mécanismes connus;
- nouvelle valeur d’un mécanisme connu;
- nouvelle capacité utilisant un contrat connu;
- nouvelle mécanique exigeant du code.

### 22.2 Exemple

Un griffon volant peut réutiliser le contrat `flight`.

Une créature qui voyage en supprimant temporairement la causalité exige probablement une nouvelle mécanique et ne doit pas être simulée par un simple texte libre.

### 22.3 Registre des mécaniques

Chaque mécanique disponible doit être enregistrée avec :

- identifiant;
- version;
- contrat;
- systèmes touchés;
- tests;
- limites;
- compatibilités.

Le LLM peut proposer qu’une nouvelle mécanique soit nécessaire, mais ne peut pas la créer canoniquement pendant une scène.

---

## 23. Garde-fous contre le free for all

### 23.1 Aucun effet mécanique implicite

Une description ne modifie pas le monde sans traduction structurée.

### 23.2 Aucun pouvoir absolu non borné

Éviter :

```text
peut tout faire
ignore toutes les règles
omniscient sans condition
invincible de toute façon
```

Remplacer par des capacités explicites ou par une autorité du monde clairement définie.

### 23.3 Pas de champs arbitraires exécutés

Les métadonnées libres peuvent enrichir la narration, mais le moteur n’exécute que les propriétés reconnues par un contrat versionné.

### 23.4 Pas d’héritage magique incontrôlé

Les presets ne doivent pas injecter de nouvelles propriétés après activation.

### 23.5 Pas de suppression du passé

Transformation, départ, destruction, fusion ou duplication produisent des événements. Ils ne réécrivent pas l’historique.

### 23.6 Pas de LLM comme arbitre ontologique

Le LLM ne décide pas seul :

- qu’une capacité existe;
- qu’une forme possède une nouvelle immunité;
- qu’un personnage est soudain sapient;
- qu’une copie est la même identité;
- qu’une loi physique cesse de s’appliquer.

### 23.7 Budgets de complexité

Le moteur peut imposer des limites opérationnelles configurables :

- nombre de manifestations actives;
- fréquence de transformations;
- profondeur de plans;
- volume de mémoire partagé;
- coût des perceptions globales;
- nombre d’appels LLM.

Ces limites protègent les performances sans devenir des limites ontologiques permanentes.

---

## 24. Edge cases couverts par cette architecture

### 24.1 Dragonne anthro

- entité sapiente;
- corps humanoïde non humain;
- ailes, queue, force, résistances;
- capacités contractuelles;
- compatibilité des lieux;
- psychologie commune aux autres agentes lorsque pertinente.

### 24.2 Shapeshifter

- identité stable;
- formes multiples;
- transformation canonique;
- continuité des états configurable.

### 24.3 Créature eldritch

- présence distribuée;
- perceptions non locales;
- cognition atypique;
- capacités extraordinaires explicites;
- plusieurs manifestations;
- aucune permission générale de « transcender les règles ».

### 24.4 Marmotte

- cognition partielle;
- besoins et apprentissage;
- relations simples;
- absence de psychologie humaine complète.

### 24.5 Vaporeon

- espèce distincte du niveau de cognition;
- locomotion et physiologie aquatiques;
- statut social configurable;
- langage ou télépathie facultatifs.

### 24.6 IA ou robot

- agent sans besoins biologiques;
- corps optionnel;
- énergie et maintenance propres;
- mémoire et psychologie possibles.

### 24.7 Fantôme

- manifestation non matérielle;
- dépendance possible à un lieu ou objet;
- perception et interaction restreintes;
- corps physique absent.

### 24.8 Épée consciente

- objet et agent simultanément;
- transportée par une autre entité;
- cognition et relations;
- capacités accessibles au porteur selon contrat.

### 24.9 Clone

- provenance commune;
- identités divergentes;
- souvenirs partagés jusqu’au point de copie;
- relations et droits non automatiquement dupliqués.

### 24.10 Possession

- corps, conscience et contrôleur séparés;
- mémoire et responsabilité explicites.

### 24.11 Ruche

- plusieurs corps;
- cognition partagée ou hiérarchique;
- synchronisation explicite.

### 24.12 Fusion

- événement transformateur;
- règles explicites d’héritage;
- pas de mélange implicite.

### 24.13 Animal devenant sapient

- activation progressive de modules cognitifs;
- identité conservée;
- changement de statut social non automatique.

### 24.14 Entité liée à un objet

- dépendance existentielle déclarée;
- cycle de vie et restauration définis.

### 24.15 Entité à temps subjectif différent

- temps subjectif séparé;
- journal canonique unique;
- conversion explicite des actions vers le temps du monde.

---

## 25. Edge cases encore volontairement différés

Cette architecture les rend envisageables, mais leur mécanique détaillée n’est pas spécifiée :

- voyage temporel modifiant le passé;
- rétrocausalité réelle;
- univers parallèles et fusion de branches;
- effacement d’identité;
- omniscience véritable;
- pouvoir de réécriture des règles en cours de scène;
- résurrection et respawn;
- transfert complet de conscience;
- copie parfaite avec débats métaphysiques sur l’identité;
- personnages joués simultanément par plusieurs propriétaires humains.

Ces sujets nécessiteront des documents spécifiques avant implémentation.

---

## 26. Impact recommandé sur le MVP

### 26.1 À garantir dès maintenant

- aucun nombre de personnages codé en dur;
- aucun nombre de lieux codé en dur;
- personnages créés par une API générique;
- lieux créés par une API générique;
- identité distincte du nom visible;
- statut actif, absent, parti, archivé;
- capacité d’ajouter et retirer sans supprimer l’historique;
- actions basées sur des capacités;
- composants facultatifs;
- presets traités comme données;
- règles du monde explicites;
- aucune dépendance structurelle à l’espèce humaine;
- aucune dépendance structurelle à une seule position par identité dans les tables les plus centrales, ou au minimum prévoir une migration claire.

### 26.2 À implémenter plus tard

- formes multiples;
- manifestations multiples;
- cognition non humaine avancée;
- duplication;
- fusion;
- possession;
- temporalité subjective;
- dépendances existentielles complexes.

### 26.3 Compromis acceptable

Le MVP peut utiliser une implémentation simplifiée « une identité active, un corps, une position » tant que :

- cette simplification est explicitement localisée dans un composant;
- les identifiants et références ne fusionnent pas définitivement ces concepts;
- le schéma ne nomme pas la position comme propriété ontologique immuable du personnage;
- les extensions futures sont prévues dans le plan de migration.

---

## 27. Modèle de données conceptuel proposé

```text
World
  ├── RuleProfile
  ├── Entity*
  ├── Location*
  ├── CapabilityDefinition*
  └── CanonicalEvent*

Entity
  ├── IdentityRecord
  ├── LifecycleState
  ├── ComponentInstance*
  ├── CognitiveCenter*
  ├── Body*
  ├── Manifestation*
  └── Relationship*

Body
  ├── FormState
  ├── PhysiologyComponent*
  ├── NeedState*
  ├── InjuryState*
  └── CapabilityGrant*

Manifestation
  ├── Location
  ├── Controller
  ├── PerceptionChannel*
  ├── CapabilityGrant*
  └── LocalState

CognitiveCenter
  ├── Perception*
  ├── Belief*
  ├── Memory*
  ├── Emotion*
  ├── Goal*
  ├── Commitment*
  └── DecisionPolicy
```

Ce diagramme est conceptuel. Il ne prescrit pas encore les tables SQL exactes.

---

## 28. Cycle de création proposé

```text
1. Choisir ou créer un preset.
2. Définir l’identité et le statut de l’entité.
3. Ajouter les composants nécessaires.
4. Définir corps, formes et manifestations.
5. Définir cognition et niveau d’agentivité.
6. Accorder des capacités versionnées.
7. Définir besoins, contraintes et dépendances.
8. Valider structure et cohérence.
9. Produire un rapport de compatibilité avec le monde.
10. Corriger ou accepter les avertissements.
11. Activer l’entité par un événement canonique.
12. Conserver la configuration résolue et sa provenance.
```

---

## 29. Tests d’acceptation architecturaux

### Test A — Cinquième résidente

Ajouter une cinquième agente sans modifier le code du moteur. L’absence de chambre doit produire une situation du monde, pas une erreur structurelle.

### Test B — Marmotte

Ajouter une marmotte avec besoins, mémoire associative et attachement, sans valeurs ni langage. Elle doit vivre sans exiger les composants humains absents.

### Test C — Dragonne anthro

Ajouter une dragonne capable de voler. Le moteur doit vérifier la capacité, le coût et la compatibilité du lieu, sans test sur l’espèce.

### Test D — Vaporeon sapient

Ajouter une créature quadrupède sapiente avec langage télépathique. Elle doit utiliser la psychologie complexe sans être humanoïde.

### Test E — IA sans corps

Ajouter une IA présente via des terminaux. Elle doit percevoir et parler sans position physique unique ni besoins biologiques.

### Test F — Shapeshifter

Changer de forme et vérifier que les capacités actives, dimensions et vulnérabilités changent, tandis que les relations et engagements persistent.

### Test G — Manifestations multiples

Une même entité agit par deux manifestations. Les positions doivent rester distinctes et les événements attribués correctement.

### Test H — Copie

Dupliquer une agente. Les copies partagent le passé, obtiennent des identifiants différents et divergent ensuite sans collision de mémoire.

### Test I — Objet conscient

Une épée consciente doit être simultanément possédée, déplacée comme objet et capable de percevoir ou communiquer selon ses canaux.

### Test J — Archivage

Retirer un personnage ou un lieu du monde actif sans casser les souvenirs, relations ou événements historiques qui le référencent.

---

## 30. Risques principaux

### 30.1 Système de composants trop générique

Risque : tout devient une collection de dictionnaires opaques.

Protection : contrats versionnés, types reconnus, validation stricte, aucune exécution de champs libres.

### 30.2 Explosion combinatoire

Risque : chaque composant interagit avec tous les autres.

Protection : interfaces limitées, événements, capacités explicites, matrice d’interaction, tests par famille.

### 30.3 Sursimulation

Risque : modéliser chaque détail biologique ou métaphysique.

Protection : ne structurer que ce qui produit une conséquence utile.

### 30.4 Faux sentiment de flexibilité

Risque : les données sont configurables, mais le code contient encore des hypothèses humaines cachées.

Protection : tests réguliers avec une entité non humaine, sans corps et à cognition partielle.

### 30.5 LLM qui invente des propriétés

Risque : une narration accorde soudain une nouvelle capacité.

Protection : le contexte LLM distingue clairement description, capacités reconnues et demandes de changement non canoniques.

### 30.6 Migration trop lourde

Risque : vouloir implémenter tous les edge cases avant le MVP.

Protection : séparation entre compatibilité architecturale et fonctionnalités effectivement livrées.

---

## 31. Décisions qui nécessiteront encore le propriétaire

Le cadre peut être préparé sans intervention supplémentaire. Les choix suivants dépendront toutefois de l’expérience voulue :

- jusqu’où l’outil de création expose les options avancées;
- si les créations incohérentes peuvent être activées malgré des avertissements;
- niveau de détail corporel par défaut;
- manière de présenter les profils cognitifs;
- statut par défaut des animaux et créatures sapientes;
- pouvoirs administratifs permettant de modifier une entité active;
- traitement éventuel de la résurrection, du respawn et du voyage temporel;
- univers ou presets fournis avec la première version publique.

Aucun de ces choix ne bloque la conception conceptuelle actuelle.

---

## 32. Recommandation finale

Le moteur doit traiter l’humain adulte ordinaire comme **un preset fréquent**, pas comme l’unité fondamentale de toute existence.

L’unité fondamentale devrait être :

> une entité persistante, composée de modules versionnés, pouvant posséder zéro ou plusieurs centres cognitifs, corps, formes et manifestations, et agissant seulement au moyen de capacités dont les effets sont explicitement contractuels.

Pour le MVP, on peut n’activer qu’une fraction de cette architecture. Toutefois, les identifiants, références, APIs de création et limites des composants doivent être conçus de façon à ne pas enfermer le projet dans :

```text
une personne = une humaine = un corps = une position = une psychologie complète
```

La flexibilité recherchée ne consiste pas à laisser le moteur improviser n’importe quoi. Elle consiste à lui permettre d’exécuter rigoureusement une grande diversité de réalités déclarées.
