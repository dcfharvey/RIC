> **SOURCE HISTORIQUE NON NORMATIVE.** En cas de différence, `docs/00_DOSSIER_MAITRE_IA.md` prévaut.

DOCUMENT DE CADRAGE PRÉLIMINAIRE

Vivarium social artificiel

Simulateur social persistant multi-agents

____________________________________________

Petit monde textuel habité par des personnages autonomes,
observable, interactif et modifiable par son propriétaire

Version 0.2 - Recentrage conceptuel

| But du document Transformer l'idée de vivarium en projet compréhensible, délimité et testable, sans supposer de connaissances en programmation ou en game design. Ce document fixe le sens du projet avant les choix techniques. |

| --- |

Statut : document vivant, non contractuel

## 0. Comment utiliser ce document

Ce document n'est ni un plan de programmation complet ni une promesse que toutes les idées seront faciles à réaliser. Il sert à fixer une direction, à empêcher le projet de grossir sans contrôle et à donner à une future IA architecte ou programmeuse une base stable à transformer en spécification technique.

| Changement principal de la version 0.2 Le projet n'est plus cadré comme une simulation de harem. Il est défini comme un simulateur social bac à sable, avec des personnages autonomes, des interactions relationnelles possibles et des traits de god game. Le choix d'un casting féminin ou attirant pour l'utilisateur relève de la direction du monde, pas de sa finalité mécanique. |

| --- |

### Lecture rapide

- Les sections 1 à 4 définissent la nature du projet et ses principes stables.

- Les sections 5 à 11 décrivent le fonctionnement conceptuel du vivarium.

- Les sections 12 à 16 définissent le premier prototype, son développement et sa validation.

- Les annexes fournissent des fiches de travail réutilisables.

## 1. Définition du projet

| Un vivarium social artificiel est un petit monde persistant dans lequel plusieurs personnages fictifs possèdent une personnalité, des intérêts, des buts, des relations, une mémoire subjective et une perception limitée de leur environnement. L'utilisateur peut observer ce monde, y interagir et en modifier les conditions à différents niveaux d'autorité. |

| --- |

Le projet se rapproche d'un simulateur social et d'un god game, mais sans exiger de graphismes, de construction de ville ou de gameplay traditionnel. Son cœur est la continuité des personnages et des relations dans un environnement textuel structuré.

### 1.1 Positionnement

| Ce que le projet est | Ce que le projet n'est pas |

| --- | --- |

| Un simulateur social persistant | Une collection de chatbots indépendants |

| Un bac à sable relationnel | Un scénario romantique prédéterminé |

| Un monde dont les personnages ont leurs propres trajectoires | Un système ou tous convergent automatiquement vers l'utilisateur |

| Un environnement modifiable par son propriétaire | Une simulation entièrement contrôlée par le modèle de langage |

| Une expérience observable et expérimentale | Un substitut à une conscience ou à une vie réelle |

## 2. Expérience recherchée

### 2.1 Ce que l'utilisateur devrait ressentir

- Les personnages ont une continuité et ne repartent pas à zéro après chaque conversation.

- Ils peuvent avoir des opinions, des projets et des relations qui ne tournent pas autour de l'utilisateur.

- Le monde produit des changements observables entre les visites, sans simuler chaque minute en détail.

- Une même situation peut être comprise et racontée différemment selon la perception de chaque personnage.

- L'utilisateur peut parler à une habitante, participer à une scène, observer sans intervenir ou modifier le monde comme administrateur.

- Les rapprochements, rivalités, amitiés et conflits apparaissent comme des conséquences, pas comme des objectifs forcés.

- Le technicien peut expliquer, mesurer et faire évoluer le système sans exiger que le propriétaire connaisse le code.

### 2.2 Sources de plaisir possibles

| Source | Description |

| --- | --- |

| Observation | Regarder les habitudes, projets, affinités et tensions se transformer dans le temps. |

| Interaction | Parler, proposer une activité, offrir une ressource, entrer dans une scène ou influencer une décision. |

| Relation | Construire une histoire différente avec chaque personnage sans résultat garanti. |

| Création | Ajouter des lieux, objets, règles, personnages et événements au vivarium. |

| Expérimentation | Modifier une condition du monde et observer ses effets sociaux. |

| Découverte | Apprendre ce qui s'est passé pendant une absence et comparer les versions subjectives. |

## 3. Périmètre et limites du concept

### 3.1 Choix du casting et contenu adulte

Le propriétaire peut choisir un casting composé uniquement de personnages féminins qui l'attirent. Il peut aussi souhaiter des relations romantiques, sensuelles, sexuelles ou corporelles. Ces choix sont compatibles avec le projet, mais ils ne définissent pas son moteur principal.

| Principe de cadrage La possibilité d'une interaction intime est une capacité du bac à sable. Elle ne transforme pas automatiquement chaque personnage en partenaire, ne remplace pas ses buts propres et ne fixe pas l'issue de ses relations. |

| --- |

### 3.2 Ce que le projet ne doit pas devenir

- Un groupe de personnages dont les voix et les réactions se confondent.

- Une machine à créer du drame, de la séduction ou de la disponibilité permanente.

- Une simulation qui dépense des tokens pour inventer des routines sans conséquence.

- Un système où le modèle modifie rétroactivement les faits pour rendre une scène plus intéressante.

- Un agent ayant libre accès au PC, aux comptes ou aux fichiers personnels.

- Un projet si vaste qu'aucune version de base ne peut être terminée.

## 4. Principes de conception stables

| Principe | Application |

| --- | --- |

| Le monde a une vérité officielle | Les événements réels sont conservés par le moteur; les personnages n'en possèdent que des perceptions partielles. |

| Les personnages ne sont pas le modèle | Leur identité réside dans des données persistantes; le modèle ne fait que les interpréter ponctuellement. |

| Le moteur garde le dernier mot | Le temps, les lieux, les ressources, les conséquences et les invariants sont gérés par du code. |

| La profondeur est sélective | Les scènes importantes sont détaillées; les routines sont condensées. |

| Les relations sont directionnelles | A envers B peut différer de B envers A. |

| Le propriétaire possède plusieurs modes d'intervention | Parler dans le monde et modifier le monde ne produisent pas les mêmes effets. |

| Les changements sont réversibles | Sauvegardes, tests et retour arrière précèdent toute évolution importante. |

| Le modèle est remplaçable | La mémoire, les règles et les outils ne doivent pas être enfermés chez un fournisseur. |

## 5. Couches du système et autorité

Le vivarium ne doit pas être un seul grand prompt. Il est composé de couches qui ont chacune une responsabilité et une autorité différentes.

| Couche | Responsabilité | Ce qu'elle ne doit pas faire |

| --- | --- | --- |

| Propriétaire | Définit les attentes, interagit et approuve les changements importants. | Être obligé de diriger techniquement chaque modification. |

| Interface | Montre le monde, les conversations, les contrôles et les journaux. | Décider des conséquences du monde. |

| Moteur de simulation | Conserve la réalité, avance le temps, applique les règles et valide les actions. | Improviser librement des faits narratifs. |

| Personnages | Choisissent des intentions et dialoguent selon leur état et leur perception. | Modifier leurs statistiques ou connaître des faits cachés. |

| Régisseur du monde | Génère des variations et événements extérieurs dans les limites fixées. | Forcer artificiellement le drame ou les relations. |

| Agent technicien | Analyse, code, teste, documente et prépare les mises à jour. | Changer directement le monde principal sans approbation. |

| Adaptateur de modèle | Traduit le format interne vers une API ou un modèle local. | Devenir le dépôt de la mémoire ou des règles du projet. |

## 6. Modes de présence de l'utilisateur

Le système doit distinguer clairement la façon dont l'utilisateur agit. Une parole prononcée dans le monde, une modification administrative et une demande au technicien ne sont pas le même type d'événement.

| Mode | Action typique | Perception par les personnages |

| --- | --- | --- |

| Observateur | Consulter le journal, suivre une scène ou demander un résumé. | Aucune, sauf si le monde comporte explicitement une observation visible. |

| Interlocuteur | Parler directement à un personnage depuis une interface de conversation. | La conversation devient un événement vécu et mémorisable. |

| Participant | Entrer dans un lieu, proposer une activité, agir dans la scène. | L'utilisateur existe comme acteur du monde et subit ses règles. |

| Régisseur | Ajouter un objet, déclencher une panne, changer la météo, ouvrir un lieu. | Les conséquences sont perçues; la source peut rester inconnue. |

| Administrateur | Modifier une fiche, une règle, une mémoire ou l'état sauvegardé. | La modification est hors monde, sauf si le propriétaire choisit d'en faire un événement. |

| Commanditaire du technicien | Demander une nouvelle mécanique ou une correction. | Aucune perception directe; il s'agit du logiciel, pas de leur univers. |

| Règle de transparence L'interface doit toujours indiquer dans quel mode agit l'utilisateur avant une opération susceptible de modifier le monde. Cela évite de confondre roleplay, intervention divine et édition de données. |

| --- |

## 7. Modèle du monde

### 7.1 Habitat détaillé

Le premier monde est une résidence ou un petit ensemble de lieux. Chaque lieu possède une capacité, des objets, des activités possibles, un niveau de confidentialité et des effets simples sur les personnages.

| Élément | Exemples | Rôle |

| --- | --- | --- |

| Lieux | Chambres, salon, cuisine, atelier, jardin, salle commune | Déterminent qui peut se rencontrer et quelles activités sont possibles. |

| Objets | Ordinateur, livres, lit, plante, console, outils | Servent de ressources, de sujets d'interaction ou de supports de projet. |

| Ressources | Temps, argent abstrait, matériaux, énergie, intimité | Imposent des choix et évitent que toute action soit gratuite. |

| Règles | Horaires, accès, propriété, bruit, visite, confidentialité | Donnent une structure au monde et rendent les conséquences prévisibles. |

| Événements | Invitation, bris, retard, visite, opportunité, changement de saison | Créent des variations sans devenir un scénario imposé. |

### 7.2 Monde extérieur abstrait

Le monde extérieur existe surtout comme source de contexte. Le moteur le condense et n'ouvre une scène détaillée que lorsqu'un événement affecte une habitante ou la résidence.

| Niveau | Traitement | Exemple |

| --- | --- | --- |

| Routine | Résolution automatique | Journée normale au travail ou aux études. |

| Variation mineure | Court résumé et effet temporaire | Trajet pénible, compliment, petit retard. |

| Événement pertinent | Événement officiel et possible appel au modèle | Conflit, invitation, occasion personnelle. |

| Événement majeur | Scène détaillée et conséquences durables | Déménagement proposé, rupture externe, perte d'emploi. |

| Règle de rareté La majorité des périodes extérieures doivent rester ordinaires. Un monde où chaque jour apporte une catastrophe ou une révélation finit par paraître artificiel. |

| --- |

## 8. Modèle d'un personnage

Un personnage est une identité persistante représentée par des données structurées. Le modèle de langage ne contient pas la personne : il reçoit seulement les informations pertinentes pour une décision ou une conversation.

| Catégorie | Contenu | Stabilité |

| --- | --- | --- |

| Identité | Nom, âge adulte, description, occupation, origine | Stable, modifiable administrativement |

| Personnalité | Traits, valeurs, manières de réagir, contradictions | Évolue lentement |

| Intérêts | Sujets, activités, préférences esthétiques, aversions | Peuvent se développer ou se perdre |

| Besoins | Repos, solitude, stimulation, proximité, sécurité | Variables gérées par le moteur |

| État actuel | Humeur, fatigue, lieu, activité, préoccupations | Temporaire |

| Objectifs | But long, projet actif, intention immédiate | Révisés selon les événements |

| Relations | Confiance, affection, attirance, respect, tension | Directionnelles et contextuelles |

| Limites | Préférences, inconforts, refus, conditions personnelles | Stables mais pas absolues ni identiques selon le contexte |

| Mémoire | Faits vécus, croyances, promesses, griefs, interprétation | Sélectionnée, subjective, consolidable |

| Voix | Style de langage, rythme, vocabulaire, expressivité | Reconnaissable sans devenir une caricature |

### 8.1 Trois choses à ne pas confondre

| Niveau | Question | Exemple |

| --- | --- | --- |

| Personnalité | Comment a-t-elle tendance à fonctionner? | Réservée, curieuse, fière. |

| État | Comment se sent-elle maintenant? | Fatiguée et irritée après une mauvaise journée. |

| Comportement | Qu'a-t-elle effectivement fait? | Elle a refusé une invitation et s'est isolée. |

### 8.2 Exemple de fiche abrégée

| Mira - exemple fictif 29 ans. Curieuse, fière, loyale, réservée sous pression. Intérêts : botanique, musique électronique, organisation. But long : créer un jardin intérieur partagé. Projet actuel : convaincre deux habitantes de l'aider. État : fatiguée mais satisfaite. Relation envers l'utilisateur : confiance élevée, affection modérée, attirance possible, jalousie faible. Souvenirs actifs : une promesse d'étagère et un désaccord récent sur l'usage du salon. |

| --- |

## 9. Simulation sociale et relations

La simulation sociale ne doit pas réduire une relation à une jauge d'affection. Plusieurs dimensions évoluent séparément et expliquent des comportements différents.

| Dimension | Question représentée |

| --- | --- |

| Affection | Cette personne lui est-elle chère? |

| Confiance | Peut-elle croire ses paroles et compter sur elle? |

| Attirance | Existe-t-il un intérêt romantique ou physique? |

| Sécurité relationnelle | Se sent-elle respectée, stable et libre dans cette relation? |

| Respect | Admire-t-elle ses capacités, son jugement ou ses principes? |

| Familiarité | Combien d'expériences communes ont-elles accumulées? |

| Tension | Existe-t-il un conflit, un malaise ou une attente non résolue? |

| Jalousie | Perçoit-elle une menace sur sa place, son lien ou son accès à une ressource affective? |

### 9.1 Autonomie personnelle et limites

Chaque personnage possède ses propres préférences, limites et dispositions. Une attirance ou une affection élevée ne suffit pas à produire un comportement donné. Cette règle ne doit pas devenir le thème central du vivarium : elle sert simplement à préserver la cohérence et l'autonomie simulée des habitantes.

### 9.2 Dynamique de groupe

- Les relations entre les habitantes existent indépendamment de l'utilisateur.

- Des amitiés, alliances, rivalités ou rapprochements peuvent apparaître sans objectif prédéfini.

- Une période de solitude peut être un résultat positif plutôt qu'un échec social.

- La jalousie peut mener à une demande, un retrait, une réflexion ou une rivalité; pas seulement à une dispute.

- Les conflits importants laissent des traces et ne disparaissent pas après une seule scène agréable.

- Le système doit tolérer l'indifférence, l'antipathie ou une relation strictement amicale envers l'utilisateur.

## 10. Temps et boucle de simulation

Le vivarium progresse par cycles. Un cycle peut représenter une période de la journée, un déclencheur externe ou une scène active. Le système n'appelle pas le modèle pour chaque geste banal.

1.  Le moteur avance le temps et met à jour les besoins simples.

2.  Il détermine les routines probables, les lieux et les rencontres possibles.

3.  Il détecte les situations significatives : conflit d'objectifs, interaction sociale, intervention de l'utilisateur ou événement extérieur.

4.  Il prépare pour chaque personnage un contexte limité à ce qu'il sait et perçoit.

5.  Le modèle propose une intention, une réaction ou un dialogue dans un format structuré.

6.  Le moteur valide l'action, applique les conséquences et crée un événement officiel.

7.  Les témoins reçoivent une mémoire subjective différente selon leur perception.

8.  Le système consolide les souvenirs anciens, met à jour les projets et produit un journal lisible.

### 10.1 Niveaux de détail

| Niveau | Quand l'utiliser | Traitement |

| --- | --- | --- |

| Détaillé | Scène observée, interaction avec l'utilisateur, événement important | Dialogue et décisions fines par modèle |

| Simplifié | Personnage actif mais hors champ | Règles, routines et appels ponctuels |

| Condensé | Période lointaine ou sans enjeu | Resume d activités et effets agrégés |

## 11. Mémoire, connaissance et perception

Le moteur doit distinguer ce qui s'est réellement passé de ce que chaque personnage croit savoir. Sans cette séparation, le groupe devient une conscience collective et les dialogues perdent leur crédibilité.

| Registre | Contenu | Autorité |

| --- | --- | --- |

| Chronologie officielle | Événements réels, date, lieu, participants, conséquences | Moteur uniquement |

| Mémoire épisodique | Expérience vecue par un personnage | Dérive d'un événement officiel |

| Croyance | Interprétation, supposition ou information reçue | Peut être vraie, fausse ou incomplète |

| Mémoire consolidée | Résumé durable d'une relation, d'un projet ou d'une période | Créé avec provenance |

| Oubli | Perte de détails ou baisse de pertinence | Règle explicite, jamais suppression arbitraire de faits critiques |

| Journal utilisateur | Résumé lisible de ce qui s'est passé | Vue externe, non accessible automatiquement aux personnages |

### 11.1 Exemple de propagation

| Événement Mira refuse d'aider Nao parce qu'elle protège du temps pour son projet. Mira interprète son refus comme une limite raisonnable. Nao le vit comme un manque de soutien. Une troisième habitante ne sait rien avant que Nao lui raconte sa version. La chronologie conserve le fait; chaque mémoire conserve une lecture différente. |

| --- |

## 12. Agent technicien et évolution du vivarium

L'agent technicien est un assistant de développement et de maintenance. Il reçoit les demandes du propriétaire, transforme une intention en comportement observable, consulte la documentation, modifie une copie du projet, exécute des tests et prépare une mise à jour réversible.

### 12.1 Cycle de travail obligatoire

1.  Reformuler la demande en résultat observable.

2.  Identifier les composants touchés et les risques de régression.

3.  Vérifier les versions installées et consulter la documentation officielle pertinente.

4.  Proposer le plus petit changement utile et le test qui prouvera son fonctionnement.

5.  Créer une sauvegarde ou une branche de développement.

6.  Implémenter, lancer les tests et comparer avec la version stable.

7.  Présenter un résumé compréhensible, les limites et les effets possibles.

8.  Attendre l'approbation avant le déploiement dans le monde principal.

### 12.2 Permissions initiales

| Action | Statut initial |

| --- | --- |

| Lire le code, la documentation et les journaux du projet | Autorisé |

| Modifier une copie de développement | Autorisé |

| Lancer les tests et produire un diagnostic | Autorisé |

| Consulter la documentation Web | Autorisé avec journalisation |

| Modifier directement la simulation principale | Interdit |

| Déployer une version | Approbation obligatoire |

| Installer un logiciel système ou obtenir des droits administrateur | Interdit |

| Accéder aux autres fichiers personnels | Interdit |

## 13. Prototype minimum viable (MVP)

Le MVP doit démontrer que des personnages différents peuvent vivre dans un monde persistant, se souvenir, développer des relations et réagir aux interventions de l'utilisateur. Il n'a pas besoin d'une interface spectaculaire ni d'un monde immense.

| Élément | Décision recommandée pour v0.2 |

| --- | --- |

| Population | 4 personnages adultes plus une présence utilisateur optionnelle |

| Lieu | Une résidence avec 5 à 7 espaces textuels |

| Temps | Trois périodes simulées par jour; pause et vitesse configurables |

| Interface | Page Web locale simple ou interface de conversation |

| Modèle | Une API interchangeable; un seul modèle joue les personnages à tour de rôle |

| Mémoire | SQLite pour les données; exports JSON et résumés Markdown |

| Actions | Parler, se déplacer, poursuivre une activité, proposer, refuser, attendre, se reposer |

| Modes utilisateur | Observateur, interlocuteur et administrateur limité dans le MVP |

| Monde extérieur | Résumés automatiques et rares événements pertinents |

| Technicien | Mode assistant : propose et prépare, mais ne déploie pas seul |

| Journalisation | Événements, décisions importantes, erreurs et modifications conservées |

| Sauvegarde | Copie automatique quotidienne et retour arrière manuel |

### 13.1 Critères de réussite

- Après redémarrage, chaque personnage retrouve son état, ses relations, ses souvenirs et ses projets.

- Deux personnages réagissent différemment à la même situation pour des raisons traçables.

- Un personnage ne connaît pas automatiquement un événement auquel il n'a pas assisté.

- Une relation évolue à la suite d'événements enregistrés, pas par changement arbitraire.

- Le monde peut progresser plusieurs jours sans contradiction majeure ni répétition dominante.

- Le propriétaire peut obtenir un résumé fiable de ce qui s'est passé pendant son absence.

- Une modification du technicien peut être testée et annulée sans perdre le monde sauvegardé.

## 14. Ordre de développement recommandé

| Phase | Travail | Preuve de passage |

| --- | --- | --- |

| 0 - Cahier de concept | Fixer la vision, les modes utilisateur, les personnages d'essai et les critères de réussite. | Document approuvé |

| 1 - Monde déterministe | Créer le temps, les lieux, les états, les actions, la sauvegarde et les journaux sans IA. | Le monde avance et reprend après redémarrage |

| 2 - Un personnage | Brancher un modèle et produire décisions, dialogues et souvenirs dans un contexte limité. | Identité cohérente pendant plusieurs jours |

| 3 - Deux personnages | Ajouter relations directionnelles, perception distincte, témoins et conversation. | Deux versions plausibles du même événement |

| 4 - Résidence | Passer à quatre personnages, routines, scènes de groupe et projets concurrents. | Vie de groupe stable sans drame permanent |

| 5 - Modes utilisateur | Ajouter observateur, interlocuteur, participant limité et édition administrative. | Chaque mode produit les effets attendus |

| 6 - Monde extérieur | Ajouter routines condensées et événements rares. | Le dehors influence sans envahir |

| 7 - Technicien | Ajouter analyse, tests automatiques, branche de développement et mise à jour réversible. | Une mécanique est ajoutée sans perte de données |

| 8 - Stabilisation | Mesures, réglages, meilleure mémoire, interface et ajout progressif de contenu. | Le système demeure stable après évolution |

| Règle de progression Ne pas ajouter plusieurs personnages tant qu'un personnage ne peut pas vivre, se souvenir et reprendre après redémarrage. Ne pas donner de pouvoir autonome au technicien tant que les tests, les sauvegardes et le retour arrière ne sont pas fiables. |

| --- |

## 15. Tests et mesures

Comme les sorties du modèle sont probabilistes, les tests ne vérifient pas seulement une phrase exacte. Ils vérifient des invariants, des contraintes et des tendances sur plusieurs exécutions.

| Type de test | Exemple |

| --- | --- |

| Invariant du monde | Un personnage ne peut pas être dans deux lieux au même moment. |

| Connaissance | Un témoin absent ne révèle pas un détail secret. |

| Personnalité | Les réactions restent compatibles avec les traits sans être identiques mot pour mot. |

| Autonomie | Une préférence ou une limite explicite n'est pas ignorée uniquement pour satisfaire l'utilisateur. |

| Mémoire | Une promesse importante réapparaît dans un contexte pertinent. |

| Causalité | Un changement relationnel important possède un événement explicatif. |

| Répétition | La même scène, phrase ou crise ne domine pas les cycles successifs. |

| Équilibre | La fréquence des conflits, retraits et interactions positives reste dans une plage choisie. |

| Reprise | Après un arrêt brutal, le dernier état valide est restauré. |

| Coût | Le budget quotidien ou mensuel d'API n'est pas dépassé. |

| Mise à jour | Une nouvelle version passe les scénarios de référence avant déploiement. |

## 16. Risques principaux

| Risque | Cause probable | Réponse de conception |

| --- | --- | --- |

| Personnalités qui se mélangent | Contexte trop large ou fiches vagues | Contextes séparés, voix de référence et tests comparatifs |

| Tout tourne autour de l'utilisateur | Objectifs propres trop faibles | Projets indépendants, relations internes et temps hors champ |

| Drame ou séduction permanents | Le modèle confond intéressant et intense | Routines positives, rareté explicite et mesures de fréquence |

| Mémoire incohérente | Résumés contradictoires ou faits inventés | Chronologie officielle, provenance et correction explicite |

| God mode confus | Modes d'intervention non distingués | Interface et journal indiquant clairement le niveau d'autorité |

| Illusion d'autonomie vide | Journaux sans ressources ni conséquences | Projets persistants, contraintes et résultats concrets |

| Coût API élevé | Trop d'appels ou contexte trop long | Simulation déterministe, niveaux de détail, cache et budgets |

| Technicien destructeur | Modification directe sans tests | Branche séparée, revue, sauvegarde et approbation |

| Surconception | Vouloir une ville ou une simulation totale | MVP fermé et critères de passage |

| Dépendance fournisseur | Données et logique liées à une API | Adaptateur de modèle et formats ordinaires |

## 17. Décisions à prendre par le propriétaire

Ces décisions ne demandent aucune connaissance technique. Elles définissent l'expérience recherchée et permettront ensuite à une IA architecte de choisir les composants.

1.  Combien de personnages dans le premier essai : 3, 4 ou 6?

2.  L'utilisateur existe-t-il comme personne dans le monde, comme présence extérieure, ou peut-il changer de mode?

3.  Le temps réel et le temps simulé avancent-ils au même rythme?

4.  Combien de cycles autonomes par jour sont acceptables?

5.  Les personnages peuvent-ils démarrer une conversation avec l'utilisateur? À quelle fréquence maximale?

6.  Quelle place donner aux relations entre les habitantes indépendamment de l'utilisateur?

7.  Quel niveau de détail souhaite-t-on pour les interactions corporelles ou intimes?

8.  Quelles modifications administratives doivent être visibles ou ressenties dans le monde?

9.  Quelles actions du technicien exigent toujours une approbation?

10.  Quel budget mensuel d'API est acceptable?

11.  Quel niveau de journal souhaite-t-on voir par défaut?

12.  Quelles données doivent être exportables pour changer de modèle ou de logiciel?

## 18. Première séance de travail suggérée

La prochaine étape utile n'est pas de choisir un framework. Elle consiste à compléter le concept avec quelques décisions observables, puis à créer des personnages d'essai suffisamment différents pour tester la simulation.

1.  Choisir les modes d'intervention disponibles dans le premier prototype.

2.  Définir quatre personnages adultes en une demi-page chacun.

3.  Décrire la résidence en cinq à sept lieux, avec les activités permises.

4.  Choisir trois projets personnels et deux tensions initiales possibles.

5.  Définir une journée ordinaire et un événement significatif de référence.

6.  Écrire dix invariants que le monde ne doit jamais violer.

7.  Fixer la vitesse du temps, le budget API et le niveau de journalisation.

8.  Demander ensuite à une IA architecte une spécification technique, sans obligation de choisir un framework avant la comparaison des options.

## Annexe A - Fiche de personnage à remplir

| Champ | Réponse |

| --- | --- |

| Nom et âge adulte |  |

| Rôle ou occupation |  |

| Description en deux phrases |  |

| Traits principaux |  |

| Valeurs importantes |  |

| Intérêts et activités |  |

| Aversions |  |

| Besoin relationnel dominant |  |

| Façon de gérer la tension ou la jalousie |  |

| Préférences et limites personnelles |  |

| But à long terme |  |

| Projet du moment |  |

| Relation initiale avec l'utilisateur |  |

| Relations initiales avec les autres |  |

| Style de parole |  |

| Contradiction ou vulnérabilité intéressante |  |

## Annexe B - Fiche d'événement

| Champ | Description |

| --- | --- |

| Événement officiel | Ce qui s'est réellement produit dans le monde. |

| Moment et lieu | Quand et où. |

| Participants | Personnes directement impliquées. |

| Témoins | Personnes présentes ou informées directement. |

| Cause | Événement ou décision précédente qui l'a déclenché. |

| Conséquences mesurables | Changements d'état, de relation, de ressource ou de projet. |

| Interprétation par personnage | Version subjective et émotionnelle. |

| Propagation | À qui l'information a été racontée et sous quelle forme. |

| Importance | Banal, mineur, significatif ou majeur. |

| Durée de conservation | Brut, résumé durable ou oubli progressif. |

## Annexe C - Glossaire minimal

| Terme | Sens dans ce projet |

| --- | --- |

| Vivarium | Petit monde persistant, fermé et observable, dont les conditions peuvent être modifiées. |

| Agent | Système qui reçoit un état, choisit une action et peut utiliser des outils. |

| Personnage agentique | Identité persistante dont les décisions sont produites à partir de données et d'un contexte limité. |

| Moteur de simulation | Code qui conserve la réalité du monde et applique les règles. |

| Événement officiel | Enregistrement de ce qui s'est réellement produit. |

| Mémoire subjective | Ce qu'un personnage croit se rappeler et la signification qu'il attribue à l'événement. |

| Cycle | Étape au cours de laquelle le temps avance et certaines décisions sont résolues. |

| Mode utilisateur | Niveau d'autorité et de présence choisi pour une intervention. |

| MVP | Plus petite version qui démontre que l'idée fonctionne réellement. |

| Invariant | Règle qui doit toujours rester vraie, quelle que soit la sortie du modèle. |

| Agent technicien | Agent distinct chargé d'aider à modifier, tester et documenter le logiciel. |

| Déploiement | Passage d'une version testée vers la simulation principale. |

| Retour arrière | Restauration de la dernière version stable. |

| Contexte | Informations sélectionnées et transmises au modèle pour une décision particulière. |

## Annexe D - État du document

| Élément | Valeur |

| --- | --- |

| Version | 0.2 |

| Type | Cadrage conceptuel préliminaire |

| Nom de travail | Vivarium social artificiel |

| Hypothèse principale | Résidence textuelle fermée, 4 personnages adultes, modèle via API |

| Recentrage | Simulateur social bac à sable avec modes de god game; aucune finalité romantique obligatoire |

| Décisions techniques | Non arrêtées |

| Prochaine révision | Après définition des modes utilisateur et des quatre personnages d'essai |

| Ce document peut devenir | Cahier des charges fonctionnel, spécification technique et plan de tests |