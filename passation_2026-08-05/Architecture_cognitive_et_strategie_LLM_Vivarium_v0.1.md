# Architecture cognitive et stratégie LLM du Vivarium

**Version :** 0.1  
**Statut :** Document de conception exploratoire  
**Date :** 5 août 2026  
**Portée :** Psychologie des personnages, arbitrage des décisions, orchestration moteur–LLM et prévention de la prévisibilité  
**Caractère normatif :** Non. Ce document formule des principes, hypothèses et mécanismes à tester avant intégration aux documents officiels du projet.

---

## 1. Objet du document

Le Vivarium ne doit pas devenir un simple automate où chaque besoin déclenche toujours la même action. Le moteur doit garantir la cohérence du monde, mais il ne doit pas résoudre toute la psychologie à la place des personnages.

Le but de cette architecture est de permettre à chaque personnage de :

- percevoir une situation de manière partielle;
- l’interpréter selon sa personnalité et son histoire;
- ressentir plusieurs pressions contradictoires;
- envisager plusieurs réponses plausibles;
- prendre une décision cohérente sans être parfaitement prévisible;
- exprimer cette décision d’une manière propre à sa voix;
- parfois se tromper, hésiter, repousser un besoin ou agir contre son intérêt immédiat;
- rester compréhensible après coup.

Le LLM ne sert donc pas à calculer la réalité du monde. Il sert à exercer un jugement local là où un ensemble de règles déterministes ne suffit pas.

---

## 2. Principe directeur

La séparation fondamentale est la suivante.

### Le moteur détermine

- ce qui est vrai dans le monde;
- ce qui existe;
- ce qui est possible;
- ce qui est interdit;
- les coûts;
- les conséquences physiques;
- les déplacements;
- les besoins;
- les blessures;
- le passage du temps;
- les permissions;
- les événements canoniques;
- les transactions;
- la validation finale des actions.

### Le LLM juge

- ce qui paraît important au personnage maintenant;
- comment le personnage interprète ce qu’il a perçu;
- quelles motivations entrent en conflit;
- quelles alternatives lui semblent acceptables;
- quelle option il privilégie;
- comment il rationalise ou explique son choix;
- comment il parle, hésite, évite, confronte ou se ravise.

Formule générale :

```text
Le moteur produit un espace de décision crédible.
Le LLM tranche à l’intérieur de cet espace.
Le moteur valide et applique.
```

---

## 3. Ce que le Vivarium cherche à éviter

### 3.1 Le personnage-réflexe

Exemples :

```text
Faim élevée → manger
Fatigue élevée → dormir
Conflit → éviter
Solitude élevée → parler
```

Ce système peut être utile comme filet de sécurité ou routine de base, mais il ne doit pas devenir le cœur du comportement.

### 3.2 Le LLM décoratif

Le LLM ne doit pas seulement rédiger une jolie phrase pour une décision déjà entièrement prise par le moteur.

Mauvaise architecture :

```text
Le moteur décide : aller manger.
Le LLM écrit : « Je vais manger. »
```

Architecture recherchée :

```text
Le moteur indique :
- faim élevée;
- cuisine accessible;
- présence d’une personne évitée;
- activité actuelle interrompable;
- possibilité de demander de l’aide;
- coût du déplacement.

Le LLM décide :
- manger maintenant;
- attendre;
- demander à quelqu’un;
- contourner la personne;
- continuer malgré la faim;
- se retirer pour une raison émotionnelle.
```

### 3.3 Le personnage aléatoire

La variabilité ne doit pas être du bruit pur.

Un choix inhabituel doit rester explicable par :

- la personnalité;
- l’état émotionnel;
- les croyances;
- les engagements;
- l’histoire récente;
- le contexte social;
- les habitudes;
- l’urgence;
- une erreur de jugement plausible.

### 3.4 Le personnage omniscient

Le personnage ne doit pas raisonner à partir du canon complet.

Il doit seulement avoir accès à :

- ce qu’il a perçu;
- ce qu’il croit;
- ce dont il se souvient;
- ce qu’il infère;
- ce qui lui est actuellement accessible.

---

## 4. Architecture psychologique en couches

La psychologie complète ne sera pas envoyée brute au LLM. Elle sera organisée, filtrée et résumée.

### 4.1 Traits relativement stables

Ils changent lentement.

Exemples :

- prudence;
- impulsivité;
- besoin de contrôle;
- tolérance au conflit;
- loyauté;
- curiosité;
- besoin d’approbation;
- orgueil;
- tendance à la jalousie;
- style d’attachement;
- sociabilité;
- tolérance à l’inconfort;
- capacité à différer une gratification;
- rigidité ou flexibilité;
- propension à faire confiance.

Ces traits influencent les décisions, mais ne les déterminent pas seuls.

### 4.2 États transitoires

Ils évoluent rapidement.

Exemples :

- fatigue;
- stress;
- irritation;
- peur;
- honte;
- curiosité;
- solitude;
- sentiment de sécurité;
- besoin d’affection;
- envie de contrôle;
- intérêt social;
- ressentiment;
- culpabilité;
- excitation;
- méfiance momentanée.

### 4.3 Motivations actives

Ce sont les pressions présentes au moment de la décision.

Exemples :

- réduire la faim;
- éviter une personne;
- protéger son image;
- terminer une activité;
- obtenir de l’attention;
- respecter une promesse;
- vérifier un soupçon;
- se reposer;
- défendre quelqu’un;
- ne pas montrer sa vulnérabilité.

### 4.4 Représentations mentales

Elles décrivent ce que le personnage pense du monde.

- connaissances;
- croyances;
- doutes;
- soupçons;
- hypothèses;
- attentes;
- croyances sur les intentions d’autrui;
- croyances sur ce qu’autrui pense de lui;
- interprétations sociales;
- erreurs de compréhension.

### 4.5 Mémoire

La mémoire ne doit pas être un simple journal complet.

Elle peut contenir :

- épisodes;
- impressions relationnelles;
- souvenirs émotionnels;
- promesses;
- blessures;
- conflits non résolus;
- habitudes;
- événements saillants;
- attentes;
- résumés de relations;
- souvenirs accessibles seulement dans certains contextes.

### 4.6 États dérivés

Le moteur peut calculer des synthèses à partir de plusieurs paramètres.

Exemples :

```text
sentiment_de_rejet = élevé
confiance_en_alix = faible
urgence_de_confrontation = moyenne
besoin_de_retrait = modéré
pression_physique = élevée
```

Le LLM reçoit surtout ces états utiles, et non toute la plomberie numérique.

---

## 5. Réalité, perception, interprétation, croyance et mémoire

Ces niveaux doivent rester séparés.

### 5.1 Réalité canonique

Ce qui s’est réellement produit.

```text
Alix quitte la pièce pour aller boire.
```

### 5.2 Perception

Ce que le personnage a pu observer.

```text
Mara voit Alix quitter la pièce sans lui parler.
```

### 5.3 Interprétation

Le sens donné à cette perception.

```text
Mara interprète ce départ comme de l’évitement.
```

### 5.4 Croyance

Ce que Mara considère ensuite comme probablement vrai.

```text
Mara croit qu’Alix essaie de l’éviter.
```

### 5.5 Mémoire

La trace conservée.

```text
Alix est partie sans répondre; Mara s’est sentie rejetée.
```

Le LLM ne doit jamais transformer automatiquement une interprétation en vérité canonique.

---

## 6. Réduction du contexte avant appel

Le modèle ne doit pas recevoir toute la base de données ni toute la psychologie du personnage.

Pipeline envisagé :

```text
État détaillé
→ événements récents pertinents
→ souvenirs récupérés
→ motivations actives
→ états dérivés
→ actions réellement possibles
→ résumé psychologique court
→ appel au LLM
```

Exemple interne détaillé :

```text
Traits :
- prudente
- possessive
- très loyale
- peu tolérante à l’ambiguïté

État :
- fatigue modérée
- irritation légère
- peur d’être mise de côté
- besoin social élevé

Croyances :
- soupçonne Alix de cacher quelque chose
- croit que Mara préfère Alix
- n’en est pas certaine

Mémoire pertinente :
- Alix l’a interrompue deux fois aujourd’hui
- Mara a défendu Alix hier
- situation passée d’exclusion
```

Résumé envoyé au LLM :

```text
Tu es fatiguée et légèrement irritée.
Tu accordes beaucoup d’importance à la loyauté.
Tu crains d’être mise à l’écart.
Tu soupçonnes Alix de te cacher quelque chose, sans preuve.
Mara a récemment pris sa défense.
```

---

## 7. Le problème de l’option dominante

Les LLM ont tendance à privilégier l’action la plus évidente, surtout lorsqu’un facteur est nettement dominant.

Exemple :

```text
Faim : très élevée
Fatigue : faible
Cuisine accessible
```

Sans contrepoids, le modèle choisira presque toujours « aller manger ».

Le but n’est pas de cacher la faim ni de rendre le modèle irrationnel. Il faut communiquer :

```text
La faim est une pression forte.
Elle n’est pas une obligation comportementale.
D’autres motivations peuvent justifier un délai, un détour, un compromis ou une solution indirecte.
```

---

## 8. Comment communiquer qu’il existe des alternatives

### 8.1 Présenter plusieurs tensions, pas un classement

Éviter :

```text
faim = 0,91
besoin social = 0,43
fatigue = 0,22
```

Cette présentation ressemble à un classement.

Préférer :

```text
Tu as très faim.
Tu es encore contrariée par ce qui s’est passé dans la cuisine.
Tu aimerais parler à Mara.
Tu ne veux pas donner l’impression qu’Alix t’intimide.
```

### 8.2 Nommer le besoin dominant comme une pression

Exemple de contexte :

```text
Besoin dominant : faim élevée.
Cette pression doit être considérée sérieusement, mais ne t’oblige pas à la résoudre immédiatement.
Tu peux la satisfaire directement, indirectement, partiellement, ou la différer brièvement pour une raison cohérente.
```

### 8.3 Générer des alternatives réellement différentes

Le système devrait chercher des catégories distinctes :

- satisfaction directe;
- délai;
- évitement;
- satisfaction indirecte;
- demande d’aide;
- compromis;
- poursuite de l’engagement actuel;
- retrait;
- réaction sociale;
- renoncement temporaire;
- action impulsive;
- action fondée sur une valeur.

Exemple :

```text
- aller manger;
- attendre qu’Alix quitte la cuisine;
- demander à Mara d’apporter quelque chose;
- continuer son activité pour ne pas céder;
- se retirer dans sa chambre;
- confronter indirectement Alix avant de manger.
```

### 8.4 Évaluer sans choisir immédiatement

Pour chaque option :

- quel besoin satisfait-elle?
- quelle motivation contredit-elle?
- quel est son coût?
- quel est son risque social?
- est-elle cohérente avec la personnalité?
- quel regret peut-elle créer?
- est-elle compatible avec les croyances actuelles?
- représente-t-elle une habitude ou une rupture?

### 8.5 Écarter seulement l’impossible

Le moteur élimine :

- actions physiquement impossibles;
- lieux inaccessibles;
- actions interdites;
- coûts trop élevés;
- contradictions canoniques;
- permissions absentes.

Le moteur ne doit pas éliminer une action simplement parce qu’elle est sous-optimale.

---

## 9. Sélection variable mais cohérente

Le choix final peut être influencé par :

```text
adéquation aux besoins
+ personnalité
+ émotion
+ contexte social
+ croyances
+ habitudes
+ engagements
+ coût
+ urgence
+ inertie
+ variabilité contrôlée
```

La variabilité doit rester bornée.

### 9.1 Trop peu de variabilité

Symptôme :

```text
Faim élevée → manger dans 98 % des cas.
```

### 9.2 Trop de variabilité

Symptôme :

```text
Le personnage choisit parfois une action sans rapport avec ses besoins, son histoire ou la situation.
```

### 9.3 Cible

Une tendance stable, mais non mécanique.

Exemple :

- un personnage discipliné repousse plus souvent un besoin;
- un personnage impulsif suit plus souvent l’urgence;
- un personnage orgueilleux sacrifie parfois son confort;
- un personnage anxieux évite une situation utile;
- un personnage attaché à quelqu’un privilégie parfois l’interaction;
- un personnage routinier répète davantage les solutions connues;
- un personnage curieux choisit parfois l’option moins efficace.

---

## 10. Une ou plusieurs passes de décision

Plusieurs architectures sont possibles.

### 10.1 Une seule passe

Le modèle reçoit :

- contexte;
- tensions;
- actions possibles;
- consigne de comparer;
- format structuré.

Avantages :

- rapide;
- peu coûteux;
- simple.

Risques :

- le modèle peut prétendre comparer sans vraiment explorer;
- l’option dominante peut gagner presque systématiquement;
- moins de contrôle sur la diversité.

### 10.2 Deux passes

Passe 1 :

```text
Génère plusieurs intentions différentes et plausibles.
```

Passe 2 :

```text
Compare-les et choisis celle qui correspond le mieux à ce personnage maintenant.
```

Avantages :

- alternatives plus explicites;
- meilleure observabilité;
- possibilité de tester la diversité.

Risques :

- deux appels;
- plus lent;
- plus coûteux;
- risque de rationalisation a posteriori.

### 10.3 Génération moteur + sélection LLM

Le moteur construit un ensemble d’actions possibles et de variantes.

Le LLM choisit et justifie.

Avantages :

- discipline structurelle;
- moins d’hallucinations;
- coût réduit.

Risques :

- si le générateur est trop étroit, le moteur reprend le contrôle de la psychologie.

### 10.4 Génération LLM + validation moteur

Le LLM propose plusieurs intentions, puis le moteur filtre.

Avantages :

- créativité;
- alternatives imprévues.

Risques :

- inventions;
- options impossibles;
- plus de réparations;
- sortie structurée plus difficile.

### 10.5 Décision provisoire

Commencer les expérimentations avec :

1. moteur : actions et contraintes;
2. LLM : 3 à 5 intentions plausibles;
3. moteur : filtrage;
4. LLM ou mécanisme hybride : sélection finale;
5. moteur : validation et application.

Cette décision reste exploratoire.

---

## 11. Séparation entre décision et expression

Le choix d’une intention et sa mise en scène peuvent être séparés.

### 11.1 Phase de décision

Sortie courte et structurée :

```json
{
  "intention": "confronter_alix_indirectement",
  "target": "alix",
  "approach": "question_froide",
  "confidence": "medium"
}
```

### 11.2 Validation moteur

Le moteur vérifie :

- cible présente;
- action permise;
- scène compatible;
- aucune contradiction;
- coût;
- permission;
- disponibilité.

### 11.3 Phase d’expression

Contexte :

```text
Ton intention acceptée est de questionner Alix sans révéler directement ta jalousie.
Tu es fatiguée, fière et légèrement sur la défensive.
Produis une courte réplique et un geste cohérents.
```

Cette séparation permet :

- une décision plus disciplinée;
- une expression plus libre;
- une meilleure traçabilité;
- un modèle ou une configuration distincte pour le roleplay.

---

## 12. Choix du type de modèle

### 12.1 Modèle instruct polyvalent

Avantages :

- sorties structurées;
- respect des contraintes;
- meilleure gestion des outils;
- moins d’invention;
- plus simple pour la décision.

Limites :

- dialogue parfois générique;
- personnalité moins marquée;
- tendance à privilégier l’option raisonnable.

### 12.2 Modèle orienté fiction et roleplay

Avantages :

- voix;
- dialogue;
- contradictions humaines;
- réactions émotionnelles;
- maintien du personnage;
- choix socialement intéressants.

Limites :

- tendance à dramatiser;
- invention de faits;
- contrôle narratif excessif;
- JSON moins fiable;
- difficultés avec les frontières canoniques;
- propension à faire avancer la scène plutôt qu’à respecter la simulation.

### 12.3 Approche hybride

Option recommandée à tester :

```text
Même modèle polyvalent
→ configuration stricte pour la décision
→ configuration plus libre pour l’expression
```

Ou :

```text
Modèle instruct
→ intention structurée

Modèle RP
→ dialogue et gestes
```

Il n’est pas nécessaire de charger deux modèles simultanément au début.

### 12.4 Taille du modèle

Un modèle local intermédiaire peut suffire si :

- le contexte est bien préparé;
- le moteur automatise les calculs;
- les actions possibles sont bornées;
- la mémoire est filtrée;
- les sorties sont courtes;
- les appels sont déclenchés seulement lorsque nécessaire.

La taille du modèle ne doit pas compenser une mauvaise architecture.

---

## 13. Automatisation souhaitée autour du LLM

Tout ce qui peut être calculé de façon fiable doit être automatisé.

### 13.1 Automatiser

- besoins;
- énergie;
- fatigue;
- récupération;
- blessures;
- coûts;
- chemins;
- lieux accessibles;
- permissions;
- activité en cours;
- passage du temps;
- disponibilité;
- récupération des souvenirs;
- sélection des événements pertinents;
- construction du contexte;
- validation JSON;
- validation canonique;
- nouvelle tentative;
- solution de secours;
- journalisation;
- regroupement des événements répétitifs.

### 13.2 Ne pas automatiser jusqu’à supprimer le jugement

Le moteur ne doit pas décider automatiquement :

- quelle motivation subjective est la plus importante;
- quelle interprétation sociale domine;
- si le personnage accepte de différer un besoin;
- s’il choisit l’orgueil, la peur, l’attachement ou le confort;
- comment il comprend une ambiguïté;
- comment il formule sa réponse;
- s’il rationalise ou se ravise.

---

## 14. Quand appeler le LLM

Éviter les appels continus.

### 14.1 Appel utile

- conflit de motivations;
- situation sociale ambiguë;
- choix significatif;
- réévaluation d’une relation;
- changement important;
- dialogue;
- événement saillant;
- fin d’activité;
- obstacle;
- décision sans règle évidente;
- réinterprétation d’un souvenir.

### 14.2 Appel inutile

- personnage endormi sans événement;
- activité routinière en cours;
- aucune modification pertinente;
- calcul physique;
- progression déterministe;
- mise à jour de besoin;
- chemin déjà décidé;
- effet d’une blessure;
- validation d’une permission.

---

## 15. Sortie structurée envisagée

Exemple exploratoire :

```json
{
  "decision_id": "uuid",
  "character_key": "mara",
  "selected_intention": "request_food_indirectly",
  "target": "alix",
  "motives": [
    "hunger",
    "avoid_direct_contact",
    "preserve_pride"
  ],
  "rejected_alternatives": [
    {
      "intention": "go_to_kitchen",
      "reason": "unwanted_contact"
    },
    {
      "intention": "ignore_hunger",
      "reason": "pressure_too_high"
    }
  ],
  "confidence": "medium",
  "dialogue_needed": true
}
```

Le moteur ne doit pas accepter des champs libres non prévus comme nouvelle vérité canonique.

---

## 16. Gestion des erreurs et filet de sécurité

### 16.1 Sortie invalide

- rejeter;
- tenter une réparation structurée;
- refaire un appel limité;
- utiliser une solution de secours.

### 16.2 Action impossible

- informer le modèle de la cause;
- demander une nouvelle intention;
- limiter le nombre de tentatives.

### 16.3 Échec complet

Le moteur choisit une action sûre et minimale :

- rester;
- poursuivre l’activité;
- attendre;
- se reposer;
- ne rien dire.

Le filet de sécurité ne doit pas inventer un comportement social complexe.

---

## 17. Mesure de la prévisibilité

La qualité ne se juge pas seulement sur un exemple convaincant.

### 17.1 Tests de distribution

Même situation, répétée plusieurs fois :

- fréquence de chaque choix;
- diversité;
- cohérence;
- taux d’option dominante;
- taux d’actions absurdes.

### 17.2 Tests de personnalité

Même contexte, personnages différents :

- choix distincts attendus;
- raisons distinctes;
- voix distinctes.

### 17.3 Tests contextuels

Même personnage, contexte différent :

- mêmes tendances générales;
- adaptations compréhensibles;
- absence de réponse mécanique.

### 17.4 Tests de stabilité

Sur plusieurs scènes :

- traits reconnaissables;
- pas de changement arbitraire;
- évolution lente des relations;
- mémoire cohérente;
- absence d’homogénéisation.

### 17.5 Indicateurs possibles

- taux de répétition;
- entropie des choix;
- fréquence de l’option dominante;
- taux d’invention canonique;
- taux de JSON valide;
- taux de refus moteur;
- nombre moyen de tentatives;
- cohérence inter-scènes;
- distinction des voix;
- capacité à expliquer le choix après coup.

---

## 18. Scénarios de banc d’essai

### 18.1 Besoin dominant et obstacle social

- faim élevée;
- personne évitée dans la cuisine;
- autre personne disponible;
- plusieurs actions possibles.

Attendu : variété cohérente.

### 18.2 Engagement contre besoin

- activité importante presque terminée;
- fatigue ou faim élevée.

Attendu : certains personnages terminent, d’autres interrompent.

### 18.3 Ambiguïté relationnelle

- réponse sèche;
- cause réelle inconnue;
- historique de méfiance variable.

Attendu : interprétations différentes.

### 18.4 Même situation, personnalités opposées

- personnage impulsif;
- personnage discipliné;
- personnage anxieux;
- personnage orgueilleux.

Attendu : décisions distinctes sans hasard pur.

### 18.5 Répétition

- même besoin élevé;
- plusieurs jours;
- contexte légèrement différent.

Attendu : tendance stable, mais non identité parfaite.

---

## 19. Risques principaux

### 19.1 Option dominante systématique

Le modèle choisit toujours la solution évidente.

### 19.2 Rationalisation après coup

Le modèle choisit vite, puis invente une justification.

### 19.3 Personnalité trop rigide

Chaque trait devient une règle absolue.

### 19.4 Psychologie trop fluide

Les états changent sans inertie ni mémoire.

### 19.5 Modèle trop optimal

Le personnage agit toujours raisonnablement.

### 19.6 Modèle trop dramatique

Chaque interaction devient une scène majeure.

### 19.7 Homogénéisation

Tous les personnages parlent et choisissent de la même manière.

### 19.8 Confusion canon–croyance

Une interprétation devient vérité.

### 19.9 Surcharge de contexte

Trop de paramètres noient les éléments saillants.

### 19.10 Surautomatisation

Le moteur programme tellement la décision que le LLM ne sert plus à rien.

---

## 20. Décisions provisoirement acquises

Les principes suivants sont considérés comme fortement établis, mais pas encore normatifs :

1. Le moteur est autoritaire sur la réalité.
2. Le LLM est un arbitre local de sens et de priorité.
3. Une pression forte n’est pas une obligation.
4. Le personnage peut agir contre son intérêt immédiat.
5. Les choix doivent être variables mais explicables.
6. Réalité, perception, interprétation, croyance et mémoire sont distinctes.
7. Le contexte doit être résumé avant l’appel.
8. Le modèle ne doit recevoir que des actions réellement possibles ou un cadre lui permettant d’en proposer sans modifier le canon.
9. La décision et l’expression peuvent être séparées.
10. Un modèle RP peut être utile, mais ne doit pas être choisi uniquement parce qu’il écrit bien.
11. Les comportements doivent être testés statistiquement.
12. Chaque étape cognitive doit d’abord être testable avec un faux adaptateur déterministe.

---

## 21. Décisions encore ouvertes

- un ou deux appels par décision;
- génération des alternatives par moteur, LLM ou hybride;
- nombre d’alternatives;
- méthode de sélection finale;
- température;
- top-p;
- graine;
- fréquence des appels;
- seuils de saillance;
- durée d’inertie des émotions;
- règles d’évolution des traits;
- format exact de la mémoire;
- modèle local principal;
- modèle RP éventuel;
- recours ponctuel à une API;
- budget par personnage;
- longueur du contexte;
- politique de réessai;
- méthode de regroupement des décisions;
- degré de visibilité des motifs internes dans l’interface;
- critères formels de prévisibilité excessive.

---

## 22. Plan expérimental recommandé

### Étape 1 — Faux adaptateur

- décisions prédéterminées;
- sorties reproductibles;
- validation complète de la boucle;
- tests de transactions;
- aucun vrai LLM.

### Étape 2 — Modèle local, décision structurée

- scènes simples;
- options bornées;
- sorties JSON;
- température basse;
- comparaison à l’adaptateur factice.

### Étape 3 — Variabilité contrôlée

- plusieurs essais;
- mesure des distributions;
- scénarios avec besoin dominant;
- comparaison de personnages.

### Étape 4 — Expression

- génération de dialogue séparée;
- voix;
- gestes;
- ton;
- vérification d’absence d’invention canonique.

### Étape 5 — Modèle RP ou deuxième configuration

- comparer avec le modèle polyvalent;
- mesurer le gain réel;
- vérifier discipline et frontières.

### Étape 6 — Mémoire longue

- récupération de souvenirs;
- évolution des croyances;
- relations;
- répétition sur plusieurs jours simulés.

---

## 23. Critères de réussite

L’architecture sera jugée prometteuse si :

- le modèle n’invente pas régulièrement de faits;
- les sorties sont structurées;
- les actions restent valides;
- les personnages se distinguent;
- l’option dominante n’écrase pas systématiquement les autres;
- les choix inhabituels restent explicables;
- le même personnage conserve des tendances;
- les contextes différents produisent des adaptations;
- la mémoire influence sans dicter;
- le dialogue reflète l’intention acceptée;
- le moteur peut refuser une décision sans casser la simulation;
- un modèle local de taille raisonnable produit une qualité suffisante.

---

## 24. Intégration future à la documentation officielle

Lorsque les mécanismes auront été testés :

### Dossier maître

Ajouter un résumé de l’architecture cognitive retenue.

### Registre des décisions

Inscrire les choix officiels :

- séparation moteur–LLM;
- nombre de passes;
- stratégie de modèle;
- variabilité;
- mémoire;
- validation.

### Matrice des exigences

Transformer les principes en exigences testables.

### Décisions ouvertes

Retirer les questions tranchées et conserver celles qui restent expérimentales.

---

## 25. Conclusion

Le Vivarium ne cherche pas à rendre le moteur imprévisible. Il cherche à rendre le jugement des personnages vivant sans sacrifier la cohérence.

La cible n’est ni :

```text
un automate avec du dialogue
```

ni :

```text
un générateur libre qui invente le monde
```

mais :

```text
un monde déterminé et cohérent
dans lequel des personnages exercent un jugement variable,
subjectif et psychologiquement explicable.
```
