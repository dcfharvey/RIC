# Roadmap active — du moteur au Vivarium MVP

**Version :** 1.2
**Mise à jour :** 6 août 2026
**Statut :** trajectoire opérationnelle. Elle remplace l'ordre immédiat des
anciennes feuilles de route historiques, sans effacer leur valeur documentaire.

## Principe de conduite

Chaque capacité importante doit avoir un moyen reproductible d'être mise en
situation, observée et comparée **avant** de contaminer le monde MVP. Le banc
d'essai n'est donc pas une interface de fin de projet : c'est une couche de
validation du moteur qui croît avec lui.

## État actuel

**Version logicielle actuelle :** `0.0.2.dev0` — pré-alpha.

- moteur déterministe, journal canonique, transactions et audits : livrés ;
- contrats/personnages versionnés, ressources et effets déclaratifs : livrés ;
- premiers changements administratifs préparés (renommage, ajout de passage) :
  livrés ;
- cinq résidentes MVP et leur contexte d'arrivée : assemblables atomiquement
  dans le monde d'intégration ;
- objets portables, installations fixes, contenance objet‑dans‑objet et
  possession par personnage : livrés; équipement, liquides et formes restent
  futurs ;
- presets de lieux et connecteurs versionnés : livrés; leur instanciation
  propre par blueprint est livrée; les connecteurs à état simple sont livrés;
  la traversée validée initiale est livrée; le monde d'intégration devient le
  prochain jalon avant la cognition ;
- règles standard de résidence installables hors du seed technique : livrées;
  la calibration déclarative de Chuu et l'arrivée initiale commune à la boîte
  aux lettres sont définies; l'instanciation réelle peut être préparée ;
- cognition, perception, mémoire et social : futurs ;
- banc d'essai minimal : livré (`vivarium.bench`), avant ces systèmes subjectifs.

## Jalons de version produit

| Version | Place dans la roadmap | Signification |
| --- | --- | --- |
| `0.0.0.dev0` | État actuel | Pré-alpha : fondations rigoureuses, mais pas encore de boucle sociale complète. |
| `0.0.1.dev0` | Jalon atteint après le banc minimal | Les interactions du moteur peuvent être mises en situation et comparées de façon reproductible. |
| `0.0.2.dev0` | État actuel, après le monde d'intégration | Les cinq vraies configurations peuvent être assemblées et réinitialisées sans histoire officielle. |
| `0.1.0a1` | Fin de l'étape 5 | **Premier MVP alpha** : boucle sociale minimale complète et présentable, encore réinitialisable. |
| `0.1.0b1` | Après essais prolongés | Bêta : le MVP tourne durablement; les défauts restants sont recherchés par observation réelle. |
| `1.0.0` | Lancement | Usage normal et persistance suffisamment fiables pour que l'histoire compte durablement. |

Les suffixes suivent la convention Python/PEP 440 : `dev0` = développement,
`a1` = alpha 1 et `b1` = bêta 1. Un jalon est publié seulement lorsque ses
critères sont réellement atteints, jamais parce qu'un calendrier l'exige.

## Ordre de travail

La trajectoire détaillée jusqu'aux premiers systèmes cognitifs est dans
`docs/21_TRAJECTOIRE_VERS_COGNITION.md`. Elle fixe les portes de qualité :
blueprint, connecteurs à état, traversée validée, monde d'intégration, puis
contrat moteur–cognition, perception, état interne, mémoire, social et LLM.

### 1. Sûreté de l'univers administratif — fermeture de passage livrée

La fermeture de passage détecte maintenant l'isolement dans les deux sens du
graphe et suit le protocole préparé. Les premiers lieux/objets attendent encore
un cas concret; aucune suppression ne doit devenir une voie rapide. Voir
`docs/17_PLAN_LOT_4_2L_FERMETURE_PASSAGE.md`.

### 2. Banc d'essai minimal du moteur — livré

Construire un outil sans LLM et sans interface graphique qui :

- crée une base isolée et temporaire à partir d'un scénario déclaratif ;
- fixe l'horloge, le monde initial et les actions injectées ;
- exécute le moteur jusqu'à une borne choisie ;
- produit un rapport lisible, le digest d'état, les événements et les refus ;
- compare deux exécutions identiques ou deux variantes ;
- ne modifie jamais une base MVP ou un monde de développement existant.

La première version est un outil pour l'IA et les tests automatisés. Voir
`docs/16_BANC_ESSAI_MOTEUR.md`. Une interface d'exploration humaine pourra
venir ensuite, si elle répond à une friction observée.

### 3. Scénarios d'acceptation inter-systèmes

Ajouter progressivement des situations de référence : passage ouvert/fermé,
ressource qui bloque une capacité, blessure et trajet, pause/reprise,
intervention admin et redémarrage. Chaque nouveau système devra fournir ses
propres scénarios reproductibles avant d'être activé dans le monde MVP.

### 4. Monde d'intégration pré-MVP propre — livré

Une base séparée de tout monde technique construit la résidence et
instancier Sophie, Erika, Luna, Chuu et Patoune par les gestionnaires réels, avec
une validation rapide du propriétaire sur leurs fiches détaillées. Ce monde
d'intégration permet de tester les vraies configurations sans transformer des
bugs précoces en histoire officielle. Les téléphones initiaux sont maintenant
portés par leurs propriétaires; l'équipement et la buanderie restent des lots
ultérieurs.

### 5. Couches vivantes puis MVP présentable

Ajouter ces couches dans cet ordre, avec le banc d'essai comme critère de sortie
de chaque lot. Le LLM n'entre qu'après le contrat moteur–LLM, avec sorties
structurées, validation et coût borné. Le **MVP** est atteint seulement lorsque
le simulateur social est suffisamment cohérent, stable et lisible pour être
présenté : il ne se confond pas avec le simple monde d'intégration. Ce jalon
correspond à `0.1.0a1`, pas à une date arbitraire.

## Frontières explicites

- Les tests unitaires actuels restent la preuve des règles locales.
- Le banc d'essai prouve les interactions de systèmes et les "what if".
- Le monde MVP est une histoire persistante, jamais une poubelle de test.
- Un test emergent intéressant n'est pas une règle : il doit être reproduit,
  expliqué et décidé avant de devenir du canon.
