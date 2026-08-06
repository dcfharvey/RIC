# Vivarium Social — Audit d’incarnation, routines et mémoire prospective

**Version :** 0.1  
**Date :** 5 août 2026  
**Statut :** RECHERCHE TERMINÉE — conclusions intégrables  
**Portée :** deuxième vague de recherche autonome  
**Domaines :** incarnation interspécifique, comportement félin, différences loup/chien, habitudes, intentions différées et mémoire d’agents

---

## 1. Verdict synthétique

Cette vague produit six décisions importantes :

1. **Une espèce ne doit pas être réduite à une liste de bonus sensoriels.**  
   Son incarnation doit modifier ce qu’elle remarque, ce qu’elle peut faire, ce qui lui coûte un effort et la manière dont elle utilise l’espace.

2. **La louve ne doit pas être écrite comme un gros chien domestique.**  
   Les loups sont socialement attentifs et coopératifs, mais leur rapport aux humains ne découle pas du même historique de domestication ni des mêmes attentes interactionnelles que celui du chien.

3. **Le chat ne doit pas fonctionner comme une jauge ambulante.**  
   L’initiation du contact, la possibilité de se retirer, les lieux préférés et le respect de ses demandes influencent la durée et la qualité de ses interactions.

4. **Les routines ne sont pas des scripts horaires rigides.**  
   Elles sont des solutions habituelles, contextuelles et imparfaites qui réduisent l’effort de décision tout en restant susceptibles d’échec, d’interruption et de révision.

5. **Une intention future doit exister indépendamment du souvenir d’un événement passé.**  
   Se rappeler de faire quelque chose plus tard est une fonction distincte : elle peut être déclenchée par une heure, un événement, un lieu, une personne ou une condition.

6. **La mémoire doit être budgétée par fonction, pas seulement par importance.**  
   Les souvenirs autobiographiques, les croyances, les habitudes, les engagements futurs et les résumés relationnels ne doivent pas être jetés dans le même réservoir.

---

## 2. Doctrine d’incarnation

### 2.1 Quatre axes obligatoires

Chaque type de corps doit être défini au minimum par :

```yaml
perception:
  modalities
  sensitivity
  blind_spots
  attention_biases

affordances:
  actions_easy
  actions_possible
  actions_impossible
  required_tools

costs:
  effort
  fatigue
  discomfort
  recovery

environment_fit:
  compatible_spaces
  problematic_spaces
  preferred_surfaces
  privacy_and_care_requirements
```

### 2.2 Anti-modèle rejeté

```yaml
wolf:
  smell_bonus: +40
  hearing_bonus: +20
```

Ce modèle ne suffit pas. Il augmente des nombres sans modifier réellement la perception, les choix ou l’organisation du monde.

### 2.3 Conséquence

Une différence corporelle n’entre dans le moteur que si elle peut :

- changer ce qui est perçu;
- rendre une action différente;
- modifier un coût;
- créer une préférence;
- produire une contrainte environnementale;
- influencer une interaction sociale.

---

## 3. La louve anthro

### 3.1 Principe

La louve est une personne sapiente ayant une morphologie et certains héritages perceptifs lupins. Elle n’est ni un chien domestique, ni un loup biologique transposé sans adaptation, ni une humaine décorée d’oreilles.

### 3.2 Conséquences de conception

À étudier et décider lors de la création du personnage :

- importance relative de l’odorat;
- localisation et discrimination des sons;
- perception fine des postures et mouvements;
- communication volontaire ou involontaire des oreilles, de la queue et du pelage;
- thermorégulation;
- tolérance aux températures;
- espace requis par la morphologie;
- mobilier, vêtements et literie;
- entretien corporel;
- réaction aux inconnus;
- histoire culturelle de ses interactions avec les humains.

### 3.3 Garde-fou domestication

Les études comparatives indiquent que les loups correctement socialisés peuvent être très attentifs aux humains et aux congénères. Les différences avec les chiens portent notamment sur les attitudes générales, la sociabilité dirigée vers l’humain, les habitudes de coopération et l’expérience.

Le Vivarium ne doit donc pas appliquer :

```text
louve
→ craint les humains
```

ni :

```text
louve
→ comprend naturellement tous les signaux humains comme un chien de compagnie
```

Sa compréhension dépendra du monde fictionnel, de son éducation, de son expérience et de ses traits personnels.

---

## 4. Le chat domestique

### 4.1 Statut

Le chat reste nonsapient, mais il possède :

- préférences;
- mémoire associative;
- attentes;
- routines;
- confort;
- stress;
- attachement;
- initiative;
- stratégies d’approche et d’évitement.

### 4.2 Interaction sociale

Le moteur doit tenir compte de :

- qui initie le contact;
- possibilité réelle de retrait;
- durée tolérée;
- zone du corps sollicitée;
- familiarité;
- humeur et activité en cours;
- lieu préféré;
- historique des interactions;
- respect ou non de ses signaux.

### 4.3 Principe de consentement animal

Le chat ne donne pas un consentement verbal, mais son comportement fournit des signaux d’approche, de maintien, d’évitement et d’arrêt.

Une interaction positive doit être plus probable lorsque :

- le chat choisit d’approcher;
- sa liberté de partir est préservée;
- ses signaux sont respectés;
- le contact correspond à ses préférences;
- l’humain adapte son comportement.

### 4.4 Représentation recommandée

```yaml
cat_state:
  location_preference
  social_availability
  arousal
  comfort
  hunger
  play_motivation
  withdrawal_threshold
  current_target
  familiar_relationships
```

Éviter les pensées humaines verbalisées. Le chat agit à partir de dispositions, de perception et d’apprentissage, pas d’un monologue de personnage humain miniature.

---

## 5. L’humaine et la slime

### 5.1 Humaine

L’humaine sert de point de référence pratique, pas de valeur neutre universelle. Son corps doit également imposer :

- sommeil;
- fatigue;
- force;
- douleur;
- hygiène;
- température;
- intimité;
- contraintes posturales;
- besoins d’outils et de mobilier.

### 5.2 Slime

Il n’existe pas de modèle scientifique direct applicable. Sa conception doit donc être une spécification fictionnelle cohérente.

Questions obligatoires avant implémentation avancée :

- limites de conservation de forme;
- masse et volume;
- rigidité volontaire ou structurelle;
- locomotion;
- manipulation d’objets;
- perception;
- nutrition;
- repos;
- thermorégulation;
- douleur;
- blessure et récupération;
- saleté et nettoyage;
- vêtements;
- intimité corporelle;
- effet de l’émotion sur la forme.

### 5.3 Règle pour la slime

Toute capacité extraordinaire doit aussi préciser :

```text
capacité
+ coût
+ limites
+ signes perceptibles
+ conséquences environnementales
```

Sans cela, la slime risque de devenir une solution universelle qui contourne toutes les contraintes du monde.

---

## 6. Habitudes et routines

### 6.1 Distinctions

```text
routine
= organisation habituelle d’une période ou d’une activité

habitude
= réponse rendue probable par un contexte récurrent

obligation
= engagement ou contrainte normative

plan
= séquence envisagée en vue d’un objectif

intention future
= action à rappeler dans une condition ultérieure
```

Ces concepts ne doivent pas être fusionnés.

### 6.2 Routines non rigides

Une routine doit contenir :

```yaml
routine:
  context_cues
  preferred_window
  usual_sequence
  flexibility
  interruption_tolerance
  recovery_strategy
  exceptions
  confidence
```

### 6.3 Erreurs réalistes

Les personnages peuvent :

- oublier;
- commencer en retard;
- être interrompus;
- improviser;
- choisir une autre méthode;
- compenser avec une note ou un rappel;
- reprendre au mauvais endroit;
- abandonner;
- remettre à plus tard.

L’erreur doit être causale et contextuelle, pas purement aléatoire.

---

## 7. Mémoire prospective

### 7.1 Définition opérationnelle

La mémoire prospective représente le fait de se souvenir d’exécuter une intention dans le futur.

Déclencheurs possibles :

```yaml
trigger:
  type: time | event | location | person | condition
  specification
  tolerance_window
```

Exemples :

- sortir le plat à 18 h;
- parler à une résidente lorsqu’elle revient;
- acheter quelque chose lors de la prochaine sortie;
- terminer une tâche quand la salle de bain se libère.

### 7.2 Données minimales

```yaml
prospective_intention:
  intention_id
  owner
  desired_action
  trigger
  priority
  commitment_strength
  creation_context
  expiration
  postponements
  external_aids
  status
```

### 7.3 Relation avec la cognition

Au moment opportun :

```text
condition canonique satisfaite
→ rappel possible
→ concurrence avec activité actuelle
→ décision de faire, reporter ou abandonner
→ conséquence sociale ou pratique
```

Un rappel n’oblige donc pas automatiquement l’action.

---

## 8. Architecture mémoire fonctionnelle

Séparer au moins :

- mémoire épisodique;
- connaissances et croyances;
- résumés relationnels;
- habitudes et routines;
- intentions prospectives;
- fils non résolus;
- mémoire de travail;
- traces techniques d’audit.

### 8.1 Importance insuffisante

Un souvenir très important peut devenir inutile, tandis qu’un détail banal peut être crucial pour une intention future.

La rétention doit considérer :

- fonction;
- récence;
- fréquence d’usage;
- conséquence future;
- lien avec un fil non résolu;
- confiance;
- coût;
- possibilité de reconstruction.

### 8.2 Compression

La compression ne doit pas transformer :

```text
« Elle a promis de nettoyer après le repas »
```

en :

```text
« Elle est généralement responsable »
```

La première information est un engagement précis; la seconde est une interprétation globale. Les deux peuvent coexister mais ne sont pas substituables.

---

## 9. Exigences proposées

### EMB-001 — Incarnation causale

Une propriété corporelle n’est conservée que si elle modifie perception, affordance, coût, préférence ou contrainte.

### EMB-002 — Aucun humain par défaut

L’humaine, la louve et la slime possèdent chacune une incarnation explicite. Les comportements corporels humains ne sont pas appliqués automatiquement aux autres morphologies.

### EMB-003 — Capacité et coût

Toute capacité non ordinaire déclare ses limites, son coût, ses signes perceptibles et ses conséquences environnementales.

### WLF-001 — Louve non canine domestique

La louve ne reçoit pas automatiquement les attitudes, attentes ou compétences sociales d’un chien domestique.

### CAT-001 — Chat nonsapient cohérent

Le chat conserve perception, préférences, apprentissage et initiative sans cognition verbale humaine.

### CAT-002 — Interaction initiée et réversible

L’initiation du contact, les signaux d’arrêt et la possibilité de retrait influencent l’état et la relation du chat.

### HAB-001 — Routine flexible

Une routine comprend contexte, fenêtre, flexibilité, interruptions, exceptions et stratégie de reprise.

### HAB-002 — Habitude distincte du plan

Une habitude influence la probabilité d’une réponse sans constituer automatiquement une intention consciente.

### MEM-P-001 — Intention prospective

Une intention future est stockée séparément des souvenirs épisodiques et peut être déclenchée par temps, événement, lieu, personne ou condition.

### MEM-P-002 — Rappel non impératif

Le déclenchement d’une intention crée une option saillante; l’agente peut agir, reporter, déléguer ou abandonner.

### MEM-F-001 — Mémoire par fonction

La consolidation et l’oubli tiennent compte de la fonction du contenu, pas seulement d’un score d’importance générique.

---

## 10. Scénarios de test

1. Le chat approche une résidente, puis tente de partir pendant le contact.
2. Deux résidentes sollicitent le chat simultanément.
3. La louve détecte un indice sensoriel que l’humaine ne peut pas percevoir.
4. La louve interprète correctement un humain familier sans posséder une compréhension canine universelle.
5. La slime utilise une capacité corporelle dont le coût influence sa décision suivante.
6. Une routine matinale est interrompue et reprise.
7. Une résidente se souvient d’une promesse en voyant la personne concernée.
8. Une intention temporelle est rappelée pendant une activité plus importante.
9. Une agente utilise un rappel externe après plusieurs oublis.
10. Une mémoire relationnelle résumée conserve correctement une promesse encore ouverte.

---

## 11. Références principales

- Turner, D. C. (2021). *The Mechanics of Social Interactions Between Cats and Their Owners*. Frontiers in Veterinary Science.
- Rault et al. (2020). *The Power of a Positive Human–Animal Relationship for Animal Welfare*. Frontiers in Veterinary Science.
- Range et al. (2013). *Social learning from humans or conspecifics: differences and similarities between wolves and dogs*. Frontiers in Psychology.
- Lazzaroni et al. (2020). *The Effect of Domestication and Experience on the Social Interaction of Dogs and Wolves With a Human Companion*. Frontiers in Psychology.
- Kujala et al. et revue (2020). *How Dogs Perceive Humans and How Humans Should Treat Their Pet Dogs*.
- Wood & Rünger (2016), synthèses sur les habitudes et routines quotidiennes.
- Einstein & McDaniel et littérature sur la mémoire prospective.
- Meta-analyse récente des tâches de mémoire prospective en contexte naturel.
- Alqithami (2025). *Forgetful but Faithful: A Cognitive Memory Architecture and Benchmark for Privacy-Aware Generative Agents* — piste émergente, à ne pas traiter comme consensus établi.
