# Inventaire de l’interface du Vivarium — brouillon de travail v0.1

Date : 4 août 2026  
Statut : document de préparation pour la discussion visuelle  
But : déterminer **ce qu’il faut voir, pourquoi, et comment l’afficher**, avant de demander une nouvelle implémentation à DeepSeek.

---

## 1. Objectif réel de l’interface

Le tableau de bord ne doit pas seulement prouver que les API fonctionnent. Il doit permettre de comprendre rapidement :

1. **Dans quel état est le Vivarium?**
2. **Que font les habitantes en ce moment?**
3. **Est-ce qu’il se passe quelque chose d’important?**
4. **Sur qui ou quoi faut-il cliquer pour en savoir plus?**
5. **Quelles actions administratives sont disponibles?**
6. **Est-ce que l’information affichée est humaine ou seulement technique?**

L’utilisateur ne devrait pas devoir interpréter des clés de base de données, des dates ISO, des événements répétitifs ou des valeurs internes.

---

## 2. Principes d’affichage

### 2.1 Priorité à la compréhension

Chaque élément doit répondre à une question identifiable.

- Le nom du monde répond à : « Quel Vivarium est ouvert? »
- Le statut répond à : « Est-il actif ou en pause? »
- La liste des personnages répond à : « Qui est là et que font-elles? »
- La fiche répond à : « Quel est l’état de cette personne? »
- Le journal répond à : « Qu’est-ce qui vient de se passer? »
- Les commandes répondent à : « Qu’est-ce que je peux modifier maintenant? »

Tout élément qui ne répond à aucune question utile doit être retiré, déplacé dans un détail secondaire ou réservé à un écran technique.

### 2.2 Données humaines en premier

Toujours afficher en premier :

- noms lisibles;
- lieux lisibles;
- heures locales;
- pourcentages correctement convertis;
- phrases compréhensibles;
- états résumés.

Les identifiants techniques peuvent rester accessibles en petit texte secondaire, mais ne doivent pas être l’information principale.

### 2.3 Densité sans entassement

L’interface doit être compacte, mais chaque zone doit avoir :

- un titre clair;
- une hiérarchie visuelle;
- assez d’espace pour distinguer les informations;
- une hauteur cohérente;
- un comportement de débordement prévu.

« Compact » ne veut pas dire « tout coller dans une ligne ».

### 2.4 Pas de faux temps réel

Tant que l’interface n’est pas automatiquement synchronisée :

- afficher clairement l’heure de la dernière actualisation;
- conserver un bouton **Rafraîchir**;
- éviter de laisser croire que chaque valeur évolue en direct.

---

## 3. Hiérarchie globale recommandée

L’écran doit être divisé en trois niveaux.

### Niveau 1 — état général du Vivarium

Toujours visible en haut :

- nom du monde;
- statut actif / en pause;
- heure canonique convertie en heure locale;
- heure de la dernière actualisation;
- bouton Rafraîchir;
- indicateur d’erreur globale si le serveur ne répond plus.

### Niveau 2 — ce qui se passe maintenant

Zone principale :

- personnages;
- lieu actuel;
- activité actuelle;
- énergie;
- état inhabituel ou avertissement;
- sélection d’un personnage.

### Niveau 3 — détails et administration

Zone secondaire :

- fiche détaillée du personnage sélectionné;
- commandes;
- journal récent;
- informations techniques facultatives.

---

## 4. Proposition de disposition générale

### 4.1 Version bureau recommandée

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ VIVARIUM · Monde principal     ACTIF     22:04     [Rafraîchir]             │
├──────────────────────────────────────────────────────────────────────────────┤
│ APERÇU DES PERSONNAGES                                    ÉTAT DU MONDE      │
│ ┌──────────────────────────────────────────────────────┐  ┌───────────────┐ │
│ │ Personnage 1 · cuisine · mange · 69 %                │  │ Heure         │ │
│ │ Personnage 2 · chambre · dort · 82 %                 │  │ Événements    │ │
│ │ Personnage 3 · cour · inactive · 91 %                │  │ Avertissements│ │
│ │ Chat · salon · dort                                  │  └───────────────┘ │
│ └──────────────────────────────────────────────────────┘                    │
├───────────────────────────────────────┬──────────────────────────────────────┤
│ PERSONNAGE SÉLECTIONNÉ                │ COMMANDES                            │
│ Nom, lieu, activité, besoins, état    │ Pause / Reprendre                    │
│ informations détaillées              │ Renommer / Déplacer                  │
├───────────────────────────────────────┴──────────────────────────────────────┤
│ ACTIVITÉ RÉCENTE / JOURNAL HUMAIN                                            │
│ 22:04 · Personnage 1 commence à manger dans la cuisine                      │
│ 22:02 · Personnage 2 entre dans sa chambre                                  │
│ 21:58 · Le Vivarium reprend                                                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Raison de cette disposition

- Les personnages sont la raison d’être du Vivarium : ils doivent occuper la zone principale.
- Le journal doit être large, car une phrase est plus lisible horizontalement que dans une colonne étroite.
- Les commandes doivent être compactes et clairement séparées de l’observation.
- La liste des mondes ne mérite pas une grande colonne permanente tant qu’il n’existe qu’un seul monde.
- Le grand espace noir actuellement inutilisé doit disparaître.

---

## 5. Barre supérieure

### 5.1 Éléments nécessaires

| Élément | Affichage recommandé | Priorité |
|---|---|---|
| Nom du produit | `VIVARIUM` | Élevée |
| Nom du monde | Nom lisible complet | Élevée |
| Statut | `ACTIF` ou `EN PAUSE`, texte + couleur | Élevée |
| Heure du monde | Format local compact | Élevée |
| Dernière actualisation | Petit texte secondaire | Moyenne |
| Rafraîchir | Bouton visible | Élevée |
| Serveur inaccessible | Bandeau ou état rouge lisible | Élevée en cas d’erreur |

### 5.2 Format

Exemple :

```text
VIVARIUM   Monde principal   ACTIF   4 août · 22:04   Actualisé il y a 8 s   [Rafraîchir]
```

### 5.3 À éviter

- date ISO brute;
- millisecondes;
- fuseau `+00:00`;
- nom du monde tronqué sans moyen de le lire;
- statut transmis seulement par la couleur;
- messages de succès permanents.

---

## 6. Sélecteur de monde

### 6.1 Besoin actuel

Il existe une liste de mondes, mais un grand panneau permanent est inutile s’il n’y en a qu’un.

### 6.2 Affichage recommandé

- Un sélecteur compact dans la barre supérieure ou juste dessous.
- Si un seul monde existe : afficher son nom sans liste ouverte.
- Si plusieurs mondes existent : menu déroulant ou petite liste latérale repliable.

### 6.3 Informations visibles

- nom du monde;
- statut;
- éventuellement nombre de personnages.

### 6.4 À éviter

- consacrer 200 à 300 pixels de largeur à une seule entrée;
- afficher l’identifiant numérique comme information principale;
- laisser un panneau presque vide occuper toute la hauteur.

---

## 7. Aperçu des personnages

C’est la zone la plus importante de l’écran.

### 7.1 Une ligne ou carte doit montrer

Information principale :

- nom lisible;
- activité actuelle;
- lieu actuel.

Information secondaire :

- énergie;
- avertissement;
- état de sélection.

Exemple :

```text
Personnage 1
Cuisine · mange                                      Énergie 69 %
```

Ou en ligne compacte :

```text
Personnage 1       cuisine       mange                         69 %
```

### 7.2 Champs souhaités

#### Minimum actuel

- nom;
- clé technique en secondaire seulement;
- lieu;
- énergie;
- activité;
- blessure ou avertissement important.

#### Plus tard

- besoin le plus pressant;
- humeur générale;
- relation ou compagnie actuelle;
- action planifiée;
- sommeil;
- indicateur d’attention requise.

### 7.3 États visuels

- sélectionné;
- normal;
- en activité;
- endormi;
- en difficulté;
- blessé;
- donnée indisponible.

### 7.4 Règles

- énergie affichée de 0 à 100 %;
- maximum deux décimales;
- pas de `null`, `undefined` ou objet brut;
- activité absente : `Aucune activité`;
- lieu absent : `Lieu inconnu`;
- blessure absente : ne pas encombrer la ligne avec `—` si elle n’est pas utile;
- une alerte importante doit être visible sans ouvrir la fiche.

### 7.5 Questions à trancher

- Veut-on voir les quatre personnages en lignes ou en cartes?
- Veut-on montrer les besoins directement?
- Quelle information doit être la plus visible après le nom : activité ou lieu?
- Le chat doit-il être présenté de la même manière que les personnages sapients?

---

## 8. Fiche du personnage sélectionné

La fiche doit expliquer l’état du personnage, pas simplement répéter la liste.

### 8.1 En-tête

- nom;
- type ou espèce, lorsqu’il existe réellement;
- clé technique en petit;
- lieu actuel;
- activité actuelle.

### 8.2 État physique

- énergie;
- faim;
- soif;
- fatigue;
- confort;
- blessure;
- repos ou sommeil;
- autre besoin réellement modélisé.

Chaque besoin doit préciser son sens. Une simple valeur `68 %` est ambiguë si on ne sait pas si 100 % signifie « rassasiée » ou « affamée ».

Exemples possibles :

```text
Énergie       69 %   correcte
Faim          22 %   faible
Fatigue       61 %   élevée
```

ou

```text
Énergie       ███████░░░ 69 %
```

Les barres sont optionnelles. Elles ne doivent pas remplacer le chiffre ni le texte.

### 8.3 État mental et social — plus tard

À réserver tant que ces systèmes ne sont pas implémentés :

- humeur;
- émotions;
- intentions;
- souvenirs pertinents;
- relations;
- croyances;
- perception de l’administrateur;
- objectif courant.

Ne pas inventer de données pour remplir l’espace.

### 8.4 Historique personnel

Plus tard, prévoir un onglet ou une section :

- dernières activités;
- derniers déplacements;
- événements impliquant ce personnage;
- blessures;
- interactions sociales.

Le journal général ne doit pas être le seul moyen de suivre un personnage.

### 8.5 Actions liées au personnage

- déplacer;
- ouvrir son historique;
- voir les détails techniques;
- plus tard : modifier la fiche canonique avec confirmation.

Les commandes globales du monde ne doivent pas se mélanger avec les actions propres au personnage.

---

## 9. État du monde

Une petite zone de synthèse peut afficher :

- actif / en pause;
- heure canonique;
- nombre de personnages;
- lieu de chaque personnage sous forme résumée;
- nombre d’événements depuis la dernière actualisation;
- alertes actives;
- activité globale éventuelle.

### 9.1 Utilité

Cette zone doit signaler les anomalies sans obliger à lire chaque fiche.

Exemples :

```text
4 habitantes
1 activité en cours
0 blessure grave
2 événements nouveaux
```

### 9.2 À éviter

- remplir le panneau avec des métriques techniques sans signification;
- afficher des nombres sans unité;
- dupliquer exactement la barre supérieure.

---

## 10. Commandes administratives

Les commandes doivent être visibles, mais ne doivent pas dominer l’écran.

### 10.1 Commandes globales

- Pause;
- Reprendre;
- Renommer le monde.

### 10.2 Commandes liées au personnage

- Déplacer le personnage sélectionné.

### 10.3 Présentation recommandée

Deux groupes clairement séparés :

```text
MONDE
[Pause] [Reprendre]
Nom du monde [________________] [Enregistrer]

PERSONNAGE SÉLECTIONNÉ
Destination [clé du lieu____________] [Déplacer]
```

### 10.4 Comportements

- désactiver Pause lorsque le monde est déjà en pause;
- désactiver Reprendre lorsque le monde est actif;
- afficher les erreurs près de la commande concernée;
- afficher les succès temporairement;
- ne pas effacer tout l’écran après une erreur;
- ne pas cacher les conséquences d’une commande;
- plus tard, remplacer la clé de lieu libre par une liste de destinations valides.

### 10.5 Problème actuel

Le champ « Destination (clé de lieu) » est techniquement fonctionnel, mais peu compréhensible pour l’utilisateur. Il faudra tôt ou tard que l’API expose :

- les lieux;
- les liens entre lieux;
- les destinations actuellement possibles;
- le coût ou les restrictions du déplacement.

---

## 11. Journal

Il faut distinguer deux usages différents.

### 11.1 Journal humain

But : comprendre ce qui se passe dans le Vivarium.

Exemples :

```text
22:04 · Personnage 1 commence à manger dans la cuisine
22:02 · Personnage 2 entre dans sa chambre
21:58 · Le Vivarium reprend
```

Il doit montrer :

- heure locale compacte;
- phrase compréhensible;
- acteur;
- lieu si pertinent;
- importance visuelle éventuelle.

### 11.2 Journal technique

But : diagnostic et audit.

Exemples actuels :

- Besoins matérialisés;
- Monde mis en pause;
- séquence;
- type d’événement;
- payload.

Ce journal peut être accessible dans :

- un onglet technique;
- un panneau repliable;
- une vue séparée;
- un mode administrateur détaillé.

Il ne doit pas noyer le journal humain.

### 11.3 Problèmes observés

- répétition massive de « Besoins matérialisés »;
- événements techniques dominants;
- manque de contexte humain;
- même heure répétée;
- difficulté à comprendre qui a fait quoi;
- aucun regroupement.

### 11.4 Règles recommandées

- 15 à 20 entrées visibles;
- plus récent en premier;
- défilement interne;
- largeur suffisante;
- regroupement des répétitions techniques;
- possibilité de filtrer :
  - Tout;
  - Personnages;
  - Monde;
  - Système;
  - Alertes.
- possibilité future de cliquer sur un événement pour voir les détails.

### 11.5 Regroupement possible

Au lieu de :

```text
22:04 · Besoins matérialisés
22:04 · Besoins matérialisés
22:04 · Besoins matérialisés
22:04 · Besoins matérialisés
```

Afficher :

```text
22:04 · Besoins mis à jour pour 4 personnages
```

Cette transformation doit idéalement être faite par une couche de présentation explicite, sans altérer le journal canonique.

---

## 12. Messages et notifications

### 12.1 Catégories

- succès;
- avertissement;
- erreur locale;
- erreur globale;
- chargement.

### 12.2 Comportement recommandé

- succès : disparaît après 3 à 5 secondes;
- erreur de commande : reste près du formulaire jusqu’à la prochaine action;
- serveur inaccessible : bandeau persistant;
- vue actualisée : message très discret ou simple mise à jour de l’heure;
- pas de message vert permanent occupant un panneau.

### 12.3 À éviter

- `alert()` navigateur;
- messages techniques;
- erreurs JavaScript brutes;
- codes seuls sans phrase;
- notification au bas de l’écran trop éloignée de l’action.

---

## 13. Lieux et déplacements

L’interface actuelle exige une clé textuelle. Ce n’est pas une solution finale.

### 13.1 Ce qu’il faudra voir

- lieu actuel;
- destinations adjacentes;
- destination sélectionnée;
- coût énergétique;
- restriction éventuelle;
- raison d’un refus.

### 13.2 Forme future possible

```text
Lieu actuel : cuisine

Destinations possibles
○ salon        coût 1
○ couloir      coût 1
○ cour         coût 2
```

### 13.3 Carte

Une carte graphique n’est pas nécessaire pour le moment. Une liste de lieux et de connexions suffit.

---

## 14. Informations techniques

Certaines informations sont utiles, mais ne doivent pas être constamment au premier plan.

### 14.1 Informations techniques possibles

- clé du personnage;
- identifiant du monde;
- numéro de séquence;
- heure canonique brute;
- type d’événement;
- payload;
- version du schéma;
- état de connexion;
- commit du projet.

### 14.2 Présentation

Les placer dans :

- une section « Détails techniques » repliable;
- une page diagnostic;
- une infobulle;
- une vue administrateur avancée.

Ne pas les confondre avec les informations de simulation.

---

## 15. Éléments futurs à prévoir sans les afficher maintenant

L’interface devra pouvoir évoluer pour montrer :

### Personnages

- portrait ou avatar;
- espèce;
- traits;
- besoins;
- humeur;
- émotions;
- objectifs;
- préférences;
- blessures;
- souvenirs;
- relations;
- perception;
- croyances;
- activité planifiée;
- dialogues récents.

### Monde

- lieux;
- objets;
- occupants par lieu;
- heure;
- météo éventuelle;
- état global;
- activités en cours;
- alertes;
- historique.

### Administration

- création et édition de personnage;
- modification d’un lieu;
- contrôle du temps;
- confirmations de changements profonds;
- audit;
- sauvegarde;
- restauration;
- réglages du moteur;
- connexion Discord;
- état du LLM.

Ces éléments ne doivent pas être ajoutés visuellement avant que leur modèle de données existe.

---

## 16. Ce qui peut être retiré ou réduit dans l’écran actuel

- le grand panneau permanent « Mondes » lorsqu’il n’y en a qu’un;
- l’espace vide sous les commandes;
- l’affichage brut des clés en premier;
- les tirets `—` répétés pour chaque donnée absente;
- le message « Vue actualisée » au milieu ou au bas de l’écran;
- la répétition d’événements techniques identiques;
- le panneau de commandes trop large;
- le nom du monde tronqué dans son champ;
- les informations identiques montrées à plusieurs endroits.

---

## 17. Ce qui doit absolument rester visible

À tout moment :

- monde sélectionné;
- actif ou en pause;
- heure du monde;
- dernière actualisation;
- personnages présents;
- lieu et activité de chacun;
- personnage sélectionné;
- état physique essentiel du personnage;
- alertes importantes;
- accès à Pause/Reprendre;
- journal humain récent;
- erreur de connexion ou de commande.

---

## 18. Questions à décider lors de la prochaine discussion

### Structure

1. Veut-on une page unique ou plusieurs onglets?
2. Le journal doit-il être en bas, à droite ou dans un onglet?
3. La fiche du personnage doit-elle être toujours visible?
4. Faut-il garder un panneau permanent pour les mondes?
5. Quelle part de l’écran doit appartenir aux personnages?

### Personnages

6. Ligne compacte ou carte?
7. Nom, activité ou lieu : quelle information doit dominer?
8. Quels besoins doivent être visibles sans ouvrir la fiche?
9. Le chat doit-il avoir une présentation distincte?
10. Les clés techniques doivent-elles être cachées par défaut?

### Journal

11. Veut-on un journal humain et un journal technique séparés?
12. Quels événements sont réellement intéressants?
13. Doit-on regrouper les événements répétitifs?
14. Veut-on des filtres?
15. Combien d’entrées visibles?

### Commandes

16. Les commandes doivent-elles être toujours visibles?
17. Renommer doit-il être derrière un bouton « Modifier »?
18. Déplacer doit-il devenir une liste de destinations?
19. Quelles commandes exigent une confirmation?

### Style

20. Quelle densité est confortable?
21. Quelle taille de texte minimale?
22. Quel niveau de contraste?
23. Bordures visibles ou panneaux séparés surtout par l’espace?
24. Couleur d’accent neutre, bleue, verte ou autre?
25. Veut-on garder le côté « outil technique » ou commencer à donner une personnalité au Vivarium?

---

## 19. Critères de réussite de la prochaine version

La prochaine interface sera considérée compréhensible si, sans explication préalable, l’utilisateur peut répondre en moins de dix secondes à ces questions :

1. Quel monde est ouvert?
2. Est-il actif ou en pause?
3. Quelle heure est-il dans le monde?
4. Qui habite actuellement le Vivarium?
5. Où se trouve chaque personnage?
6. Que fait chaque personnage?
7. Qui est sélectionné?
8. Son état est-il normal?
9. Qu’est-ce qui vient de se passer?
10. Où cliquer pour mettre en pause, reprendre ou déplacer?

Elle sera considérée correctement organisée si :

- aucun grand panneau n’est presque vide;
- aucun journal ne fait grandir la page indéfiniment;
- aucune valeur interne n’est présentée comme une donnée humaine;
- aucune information importante n’est cachée dans une colonne étroite;
- les commandes ne dominent pas l’observation;
- les données techniques restent disponibles sans parasiter la lecture normale.

---

## 20. Décision provisoire

Ne pas envoyer immédiatement un nouveau prompt de redesign à DeepSeek.

La prochaine étape devrait être :

1. discuter de cette liste;
2. décider ce qui est essentiel;
3. choisir une disposition;
4. produire une maquette précise;
5. seulement ensuite rédiger un prompt d’implémentation contraignant.

Le document est volontairement plus large que le MVP actuel afin d’éviter de refaire l’interface à l’aveugle à chaque nouveau système.
