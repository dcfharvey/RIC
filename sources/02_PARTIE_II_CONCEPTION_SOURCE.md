> **SOURCE HISTORIQUE NON NORMATIVE.** En cas de différence, `docs/00_DOSSIER_MAITRE_IA.md` prévaut.

DOSSIER DE CONCEPTION - PARTIE II

Vivarium social artificiel

Architecture technique, contraintes et plan de réalisation

____________________________________________________________

Spécification de travail destinée à guider la construction d'un premier prototype
textuel, persistant, exploitable par Discord et évolutif

Version 0.1 - août 2026

Statut : document vivant de conception - non contractuel

| Place dans le dossier La Partie I définit la vision, l'expérience et le périmètre conceptuel. La présente Partie II transforme cette vision en exigences techniques, en architecture et en plan de réalisation. Elle ne remplace pas la Partie I : les deux documents doivent être lus ensemble. |

| --- |

## 0. Comment utiliser ce document

Ce document est le pont entre l'idée et le développement. Il doit permettre à un développeur humain ou à une IA programmeuse de comprendre ce qui doit être construit, ce qui doit rester séparé, ce qui est obligatoire pour le premier prototype et ce qui peut attendre.

| Règle de priorité En cas de conflit, l'ordre d'autorité est : 1) intention et limites de la Partie I; 2) exigences obligatoires de la Partie II; 3) décisions consignées dans le registre; 4) détails d'implémentation proposés par le développeur ou l'agent technicien. |

| --- |

| Étiquette | Sens |

| --- | --- |

| OBLIGATOIRE | Nécessaire au premier prototype ou à sa sûreté. |

| RECOMMANDÉ | À mettre en place sauf raison technique documentée. |

| OPTIONNEL | Peut être différé sans invalider le prototype. |

| À DÉCIDER | Question encore ouverte qui doit recevoir une décision explicite. |

Le propriétaire du projet ne doit pas être forcé de choisir entre des technologies qu'il ne connaît pas. Toute proposition technique doit fournir une option recommandée, ses raisons, ses compromis et une façon simple de vérifier qu'elle fonctionne.

### 0.1 Structure de la Partie II

| Bloc | Contenu |

| --- | --- |

| A. Besoins et contraintes | Objectifs techniques, exigences, périmètre et hypothèses. |

| B. Architecture | Composants, responsabilités, flux de données et autorité. |

| C. Simulation | Monde, personnages, mémoire, temps, relations et extérieur abstrait. |

| D. Exploitation | Discord, API, hébergement, sécurité, coûts, journaux et sauvegardes. |

| E. Développement | MVP, phases, tests, critères d’acceptation et évolution. |

## 1. Objet technique du projet

Construire un vivarium social artificiel textuel et persistant, hébergé sur un ordinateur personnel, dans lequel un petit nombre de personnages fictifs conservent un état, une mémoire, des relations et des projets entre les interactions. Le propriétaire doit pouvoir observer le monde, parler aux personnages, y intervenir à différents niveaux d'autorité et demander à un agent technicien de faire évoluer le logiciel.

| Objectif du premier système Prouver qu'un petit monde peut fonctionner pendant plusieurs jours réels, reprendre après un redémarrage, produire des événements cohérents, permettre des conversations persistantes et demeurer inspectable et réversible. |

| --- |

### 1.1 Non-objectifs initiaux

- Produire un jeu vidéo graphique, une carte animée ou une simulation physique complète.

- Simuler une ville entière, une économie réaliste ou des milliers de personnages.

- Donner aux personnages un accès direct au système d'exploitation ou à Internet.

- Permettre à l'agent technicien de modifier la version active sans tests ni approbation.

- Prétendre démontrer une conscience ou reproduire scientifiquement la psychologie humaine.

## 2. Besoins, contraintes et hypothèses de départ

### 2.1 Besoins principaux

| ID | Besoin | Priorité |

| --- | --- | --- |

| B-01 | Continuité des personnages et du monde entre les sessions. | OBLIGATOIRE |

| B-02 | Interaction naturelle depuis Discord, sans interface de jeu dédiée. | OBLIGATOIRE |

| B-03 | Personnages distincts, autonomes et capables de trajectoires non centrées sur le propriétaire. | OBLIGATOIRE |

| B-04 | Monde canonique dont les faits ne sont pas décidés librement par le modèle. | OBLIGATOIRE |

| B-05 | Interventions du propriétaire selon plusieurs modes clairement séparés. | OBLIGATOIRE |

| B-06 | Fonctionnement sur du vieux matériel grâce à une API distante. | RECOMMANDÉ |

| B-07 | Possibilité future de changer de modèle ou de fournisseur sans reconstruire le système. | OBLIGATOIRE |

| B-08 | Agent technicien capable d’analyser et de proposer des évolutions. | OPTIONNEL AU MVP |

| B-09 | Croissance future vers plusieurs résidences ou une petite communauté. | À PRÉSERVER |

### 2.2 Contraintes de conception

| Contrainte | Conséquence technique |

| --- | --- |

| Propriétaire non programmeur | Documentation claire, commandes sûres, valeurs par défaut et preuves de fonctionnement. |

| Aucun graphisme requis | Le développement se concentre sur la simulation, la mémoire et l'interface textuelle. |

| Ordinateur ancien possible | Le calcul du LLM est déporté; le PC local conserve l'état et orchestre les appels. |

| API potentiellement étrangère | Filtrage des secrets, visibilité des données envoyées et possibilité de changer de fournisseur. |

| Contenu adulte possible | Les personnages et le moteur doivent gérer autonomie, préférences et limites sans faire de cette capacité la finalité du système. |

| Temps d'utilisation indéfini | Mémoire consolidée, archives, migrations de données et tests de régression nécessaires. |

| Système expérimental | Sauvegardes, points de contrôle, replay et retour arrière doivent exister tôt. |

### 2.3 Hypothèses initiales

- Population initiale : trois à six personnages; cible ultérieure probable : six à douze.

- Un seul propriétaire humain et un serveur Discord privé.

- Une résidence principale composée de quelques lieux textuels.

- Le monde extérieur est résumé et n'est détaillé que lorsqu'il affecte le vivarium.

- Les personnages sont des enregistrements persistants réveillés au besoin, pas des processus séparés tournant en permanence.

- Un même modèle ou fournisseur peut interpréter plusieurs personnages successivement sans partager leurs mémoires privées.

- La majorité des routines est gérée par le moteur; le LLM intervient pour les décisions, dialogues et interprétations significatives.

## 3. Catalogue des exigences

Les identifiants ci-dessous servent de références dans le code, les tests et le registre des décisions. Une exigence peut être précisée plus tard, mais ne doit pas disparaître silencieusement.

### 3.1 Exigences fonctionnelles

| ID | Exigence |

| --- | --- |

| F-01 | Créer, charger et sauvegarder un monde persistant. |

| F-02 | Créer des personnages avec traits, intérêts, objectifs, états, relations et mémoire. |

| F-03 | Faire avancer le temps simulé et déclencher des événements. |

| F-04 | Permettre aux personnages de choisir des intentions selon leur état et leur perception. |

| F-05 | Valider chaque intention par le moteur avant de modifier le monde. |

| F-06 | Distinguer événement objectif, perception, croyance et souvenir. |

| F-07 | Permettre une conversation privée, de groupe et avec le technicien. |

| F-08 | Permettre au propriétaire d’observer, participer, régir et administrer. |

| F-09 | Condenser les routines banales et développer les scènes importantes. |

| F-10 | Produire des résumés périodiques et des notifications d’événements importants. |

| F-11 | Mettre en pause, reprendre, avancer le temps, créer un snapshot et restaurer. |

| F-12 | Journaliser les actions, décisions, appels de modèle et changements d’état. |

| F-13 | Exporter des fiches et rapports dans des formats lisibles. |

| F-14 | Gérer des modifications techniques sur une copie de développement. |

### 3.2 Exigences non fonctionnelles

| ID | Exigence |

| --- | --- |

| NF-01 | Le noyau doit fonctionner sans interface graphique de jeu. |

| NF-02 | Le modèle doit être remplaçable par adaptateur. |

| NF-03 | Les données canoniques doivent rester dans des formats locaux et documentés. |

| NF-04 | Une panne d’API ou de réseau ne doit pas corrompre le monde. |

| NF-05 | Le système doit reprendre après redémarrage sans perdre la dernière étape validée. |

| NF-06 | Chaque action importante doit être attribuable à une cause et à un acteur. |

| NF-07 | Les coûts, latences et volumes de tokens doivent être mesurables. |

| NF-08 | Les permissions doivent être minimales et configurables. |

| NF-09 | Les composants doivent pouvoir évoluer par migrations versionnées. |

| NF-10 | Le comportement essentiel doit être couvert par des scénarios de test reproductibles. |

## 4. Architecture générale recommandée

| Principe central Le LLM propose, interprète et dialogue. Le moteur local conserve la réalité, applique les règles et décide ce qui est enregistré comme vrai. |

| --- |

| Discord / commandes locales │ Interface et routeur de messages │ Orchestrateur du vivarium ┌──────┼───────────┬───────────────┐ │ │ │ │ Moteur Mémoire Planificateur Permissions │ │ │ │ └──────┼───────────┴───────────────┘ │ Adaptateur de modèle ── API distante / modèle local futur │ Base SQLite + archives + journaux |

| --- |

### 4.1 Composants et responsabilités

| Composant | Responsabilité | Autorité interdite |

| --- | --- | --- |

| Interface Discord | Recevoir les messages, présenter les réponses, commandes et autorisations. | Modifier directement les données du monde. |

| Routeur | Identifier le mode, le personnage, la scène et le niveau d’autorité. | Inventer des conséquences. |

| Orchestrateur | Construire le contexte, appeler le modèle, gérer la boucle et les budgets. | Contourner les permissions. |

| Moteur canonique | Temps, lieux, présence, ressources, règles, validations et conséquences. | Improviser des faits non validés. |

| Couche cognitive | Perception, récupération de mémoire, intention, dialogue, réflexion. | Écrire directement dans la vérité du monde. |

| Mémoire | Conserver événements, perceptions, croyances, résumés et provenance. | Fusionner automatiquement croyance et fait. |

| Planificateur | Déclencher routines, événements, consolidations et notifications. | Faire tourner des appels sans limite. |

| Adaptateur de modèle | Uniformiser les fournisseurs, formats structurés, erreurs et métriques. | Enfermer la logique métier dans une API particulière. |

| Agent technicien | Analyser, coder, tester et proposer des changements. | Déployer seul sur la version active. |

### 4.2 Frontières d’autorité

- Le moteur possède le monde. Aucun dialogue ne devient un fait sans validation et transaction.

- Chaque personnage possède sa subjectivité. Il peut être biaisé, se tromper ou mentir, mais ne peut connaître les données cachées.

- Le propriétaire possède l’autorité administrative. Ses interventions doivent toutefois être étiquetées selon qu'elles sont perceptibles ou non dans le monde.

- Le technicien possède une zone de développement. Il peut modifier une copie, jamais le monde actif sans intégration approuvée.

## 5. Modèle d’exécution et boucle de simulation

### 5.1 Le système n’est pas continuellement conscient

Entre deux événements, le programme peut être en attente. La continuité vient de l'état sauvegardé, du passage du temps et des conséquences persistantes. Un personnage est réveillé lorsqu'une décision, une conversation ou une réflexion est requise.

### 5.2 Boucle minimale

| 1. Charger l'état canonique et les événements arrivés à échéance 2. Mettre à jour les besoins et conditions déterministes 3. Détecter les décisions qui exigent une interprétation 4. Construire le contexte subjectif du personnage concerné 5. Demander une intention structurée au modèle 6. Valider l'intention avec le moteur 7. Appliquer la conséquence dans une transaction 8. Distribuer les perceptions aux témoins 9. Mettre à jour mémoire, relations et journaux 10. Décider : continuer, résumer, notifier ou attendre |

| --- |

### 5.3 Déclencheurs autorisés

| Déclencheur | Exemple | Appel LLM requis? |

| --- | --- | --- |

| Horaire | Réveil, repas, travail, activité planifiée. | Souvent non. |

| État | Fatigue élevée, solitude prolongée, objectif bloqué. | Seulement si choix ambigu. |

| Événement | Arrivée d’un objet, message, conflit, visite. | Selon importance. |

| Interaction utilisateur | Message à un personnage ou au technicien. | Oui dans la plupart des cas. |

| Maintenance | Résumé de mémoire, sauvegarde, test de santé. | Parfois, avec modèle économique. |

### 5.4 Cadence et profondeur adaptatives

Le temps simulé ne doit pas forcer un appel par personnage et par minute. La profondeur varie selon l'importance.

| Niveau | Traitement | Exemple |

| --- | --- | --- |

| 0 - déterministe | Règles et calculs locaux uniquement. | Dormir, trajet habituel, baisse graduelle d’énergie. |

| 1 - condensé | Résumé d’une période sans dialogue détaillé. | Journée de travail ordinaire. |

| 2 - décision | Un appel court choisit une intention ou interprétation. | Accepter une invitation ou rester seule. |

| 3 - scène | Dialogue multi-tours, conséquences et souvenirs détaillés. | Dispute, rapprochement, intervention du propriétaire. |

| 4 - réflexion | Consolidation autobiographique ou révision de projet. | Comprendre une relation après plusieurs événements. |

## 6. Modèle canonique du monde

Le monde canonique est la seule source de vérité opérationnelle. Il conserve ce qui existe et ce qui s'est produit, indépendamment de ce que les personnages en pensent.

### 6.1 Entités minimales

| Entité | Contenu minimal |

| --- | --- |

| Monde | Identifiant, version de schéma, temps simulé, état pause/reprise. |

| Lieu | Nom, accès, capacité, intimité, objets, activités, occupants. |

| Objet | Type, emplacement, propriétaire, état, usages permis. |

| Personnage | Identité, traits, états, objectifs, inventaire, position. |

| Relation | Valeurs directionnelles entre deux entités et historique condensé. |

| Événement | Cause, participants, témoins, lieu, résultat, importance, horodatage. |

| Projet | But, étapes, ressources, progression, blocages, propriétaire. |

| Règle | Condition, effet, priorité, version et domaine d’application. |

### 6.2 Proposition, validation, résolution

| Intention du personnage "Je veux rejoindre Nao dans la cuisine et lui parler." ↓ Validation du moteur Nao est-elle présente? Le lieu est-il accessible? Une autre scène est-elle active? ↓ Résolution Action acceptée, différée, modifiée ou refusée ↓ Événement canonique Mira entre dans la cuisine et initie une conversation avec Nao. |

| --- |

### 6.3 Transactions et idempotence

- Chaque action validée doit être appliquée comme une transaction : tout réussit ou rien ne change.

- Un identifiant unique empêche qu'une réponse réessayée après une panne applique deux fois la même action.

- Les appels de modèle peuvent être relancés; les conséquences du monde ne le peuvent qu'après vérification de l'état attendu.

- Les modifications administratives importantes créent automatiquement un snapshot préalable.

## 7. Modèle technique d’un personnage

Un personnage n'est pas une instance permanente du modèle. C'est un ensemble versionné de données persistantes, interprété au moment d'agir par le moteur cognitif.

### 7.1 Couches internes

| Couche | Exemples | Vitesse de changement |

| --- | --- | --- |

| Identité | Nom, biographie, apparence textuelle, voix, valeurs centrales. | Très lente / administrative. |

| Traits | Curiosité, prudence, franchise, besoin de contrôle, sociabilité. | Lente et justifiée. |

| Préférences | Activités, personnes, rythmes, goûts, limites. | Lente à moyenne. |

| Objectifs | Projet personnel, désir relationnel, besoin immédiat. | Variable. |

| États | Énergie, humeur, stress, stimulation, solitude. | Rapide. |

| Relations | Confiance, affection, attirance, sécurité, irritation, rivalité. | Graduelle et directionnelle. |

| Mémoire | Épisodes, croyances, réflexions, habitudes apprises. | Accumulation puis consolidation. |

| Connaissance | Faits observés, racontés ou déduits; avec provenance. | Selon perception. |

### 7.2 Contexte envoyé au modèle

- Identité compacte et traits pertinents à la situation.

- État actuel et objectifs actifs.

- Lieu, personnes présentes et possibilités d'action visibles.

- Souvenirs récupérés selon pertinence, récence, importance et relation.

- Connaissances que le personnage possède réellement, jamais la base canonique complète.

- Format de sortie strict : intention, cible, justification brève, dialogue éventuel et niveau de confiance.

| Protection contre la conscience collective Le contexte d'un personnage ne doit jamais contenir les souvenirs privés, les statistiques cachées ou les intentions internes d'un autre personnage, sauf si elles ont été observées ou communiquées dans le monde. |

| --- |

### 7.3 Personnalité stable sans rigidité

La cohérence ne signifie pas répéter toujours la même réaction. Les traits modulent les choix, mais les états, relations, souvenirs et circonstances doivent pouvoir produire des exceptions compréhensibles. Tout changement durable de trait doit avoir une cause enregistrée ou être une intervention administrative explicite.

## 8. Architecture de mémoire

Une mémoire infinie placée dans chaque prompt ne scale pas. Le système doit conserver beaucoup sur disque, mais n'en transmettre qu'une sélection utile au modèle.

### 8.1 Types de mémoire

| Type | Fonction | Exemple |

| --- | --- | --- |

| Journal canonique | Historique objectif, immuable et complet. | Mira a refusé l’invitation à 18 h 12. |

| Perception | Ce qu’un personnage a vu ou entendu. | Nao a entendu le refus depuis le salon. |

| Souvenir épisodique | Version subjective d’un événement. | Mira se souvient d’avoir protégé son temps. |

| Croyance | Conclusion tenue pour vraie avec confiance et provenance. | Nao croit que Mira évite Élise. |

| Mémoire sémantique | Faits stables appris sur le monde et les personnes. | Élise travaille tôt le mardi. |

| Réflexion | Synthèse de plusieurs épisodes. | Les demandes imprévues la rendent défensive. |

| Résumé de période | Compression d’une journée, semaine ou arc relationnel. | Semaine calme, tension persistante avec Élise. |

### 8.2 Cycle de vie de la mémoire

| Événement canonique ↓ distribution aux témoins Perceptions subjectives ↓ sélection / importance Souvenirs épisodiques ↓ consolidation périodique Réflexions et résumés ↓ index de recherche Contexte récupéré au besoin Les événements bruts restent archivés; les index et résumés peuvent être reconstruits. |

| --- |

### 8.3 Récupération et oubli

- Le score de récupération combine pertinence, récence, importance, relation et tâche actuelle.

- L'oubli signifie surtout une baisse d'accessibilité, pas nécessairement une suppression du journal brut.

- Les souvenirs contradictoires doivent coexister avec provenance et niveau de confiance.

- Une correction administrative ne doit pas effacer silencieusement l'historique; elle crée une nouvelle version ou une note de correction.

- La base vectorielle, si utilisée, reste un index reconstruisible et non la seule copie de la mémoire.

## 9. Relations, besoins et états internes

La simulation sociale ne doit pas être entièrement laissée au texte. Des valeurs structurées garantissent une continuité minimale, tandis que le modèle leur donne une interprétation nuancée.

### 9.1 Relations multidimensionnelles

| Dimension | Sens |

| --- | --- |

| Confiance | Anticipation que l’autre agira de manière fiable ou honnête. |

| Affection | Attachement positif général. |

| Attirance | Intérêt romantique ou physique, distinct de la confiance. |

| Sécurité | Capacité à être vulnérable sans se sentir menacée. |

| Respect | Valeur accordée au jugement, aux compétences ou aux principes. |

| Irritation | Charge négative récente susceptible de retomber. |

| Ressentiment | Trace lente d’un tort non résolu. |

| Rivalité / jalousie | Compétition perçue pour une ressource, un statut ou une attention. |

| Familiarité | Quantité d’expérience partagée; n’implique pas une relation positive. |

Les relations sont directionnelles : A envers B n'est pas identique à B envers A. Les valeurs numériques ne doivent pas être affichées systématiquement dans l'expérience, mais doivent être inspectables en mode administrateur.

### 9.2 Besoins et états

- Commencer avec peu d'axes : énergie, stimulation, sociabilité, stress et besoin d'intimité.

- Éviter une pseudo-psychologie trop détaillée avant de prouver que chaque variable modifie réellement le comportement.

- Un besoin ne dicte pas une action; il modifie les priorités et la probabilité des choix.

- L'autonomie personnelle et les limites constituent une contrainte permanente, pas un thème narratif imposé.

## 10. Monde extérieur abstrait

Le vivarium concentre sa profondeur sur la résidence et ses habitantes. L'extérieur existe comme générateur de contexte, de ressources et d'événements, sans simuler une ville entière.

| Élément extérieur | Traitement recommandé |

| --- | --- |

| Travail ou études | Calendrier, fatigue, revenu abstrait, quelques événements significatifs. |

| Déplacements | Durée et indisponibilité; scène détaillée seulement si incident ou interaction importante. |

| Relations secondaires | Fiches légères et événements condensés, développés si elles deviennent pertinentes. |

| Actualité et météo | Variables de contexte ou événements injectés, pas simulation complète. |

| Achats et ressources | Budget simplifié et disponibilité; détail seulement si utile à une intrigue ou un projet. |

| Règle de zoom Le système ne doit pas inventer rétroactivement des détails majeurs. Les périodes condensées créent des résultats structurés au moment où elles sont simulées; le récit détaillé peut ensuite être généré à partir de ces résultats. |

| --- |

## 11. Interaction du propriétaire et interface Discord

### 11.1 Modes de présence

| Mode | Effet dans le monde | Visibilité pour les personnages |

| --- | --- | --- |

| Observateur | Consulte événements, lieux, fiches et résumés. | Aucune, sauf action volontaire. |

| Interlocuteur externe | Parle à une habitante sans incarnation physique. | Selon la fiction choisie : canal, voix, présence extérieure. |

| Participant | Existe dans une scène; ses paroles et actes deviennent canoniques. | Pleine perception selon la scène. |

| Régisseur | Ajoute objet, événement, météo, rencontre ou avance le temps. | Configurable : intervention visible, anonyme ou naturelle. |

| Administrateur | Modifie traits, règles, souvenirs, relations ou données. | Invisible par défaut, sauf événement explicite. |

| Commanditaire du technicien | Demande une analyse ou une évolution du logiciel. | Aucune dans le monde simulé. |

### 11.2 Architecture Discord recommandée

| Serveur privé ├── #salon-commun ├── #journal-du-monde ├── #événements-importants ├── Personnages │ ├── #mira │ ├── #elise │ └── #groupe ├── Technicien │ ├── #atelier │ ├── #rapports │ └── #changements-proposés └── Administration ├── #commandes ├── #état-du-système └── #journaux |

| --- |

Un seul bot principal est recommandé. Il route les messages et peut utiliser des webhooks pour publier sous le nom et l'avatar de chaque personnage. Des bots séparés par personnage ajouteraient de la configuration sans fournir de bénéfice architectural réel au départ.

### 11.3 Commandes minimales

| Commande ou intention | Fonction |

| --- | --- |

| /parler [personnage] | Ouvrir ou poursuivre une conversation ciblée. |

| /observer [lieu/personnage] | Afficher un état lisible sans intervenir. |

| /mode [observateur/participant/régisseur/admin] | Changer explicitement de niveau d’autorité. |

| /pause et /reprendre | Contrôler la progression autonome. |

| /avancer_temps [durée] | Simuler jusqu’à une échéance ou un événement important. |

| /snapshot [nom] | Créer un point de restauration. |

| /restaurer [snapshot] | Revenir à un état antérieur après confirmation. |

| /coûts | Afficher appels, tokens et dépenses par période et composant. |

| /technicien [demande] | Créer une demande de modification ou de diagnostic. |

### 11.4 Limites de Discord

Discord suffit pour vivre l'expérience, mais il devient moins pratique pour inspecter des centaines d'événements, comparer des sauvegardes ou modifier de nombreux paramètres. Un petit tableau de bord Web local pourra être ajouté plus tard comme console d'inspection, sans devenir une interface graphique de jeu.

## 12. Couche modèle et API

### 12.1 Principe d’interchangeabilité

Le modèle doit être traité comme un moteur remplaçable. La logique du monde, les mémoires et les permissions ne doivent pas dépendre de son format propriétaire.

| Sous-composant | Rôle |

| --- | --- |

| Adaptateur fournisseur | Convertit le format interne vers DeepSeek, OpenAI, Anthropic, modèle local ou autre. |

| Gestion des capacités | Connaît contexte, sorties structurées, appels d’outils et limites du modèle choisi. |

| Politique de routage | Choisit un modèle économique ou puissant selon la tâche. |

| Gestion des erreurs | Temps d’attente, réessai, repli, annulation et reprise sûre. |

| Métriques | Tokens, coût, latence, cache, taux d’échec et nombre de régénérations. |

### 12.2 Stratégie d’utilisation

| Type de tâche | Modèle conseillé |

| --- | --- |

| Routines, résumés simples, classification | Modèle rapide et économique ou logique locale. |

| Dialogue courant | Modèle équilibré avec bonne adhérence à la personnalité. |

| Scène complexe, conflit, réflexion autobiographique | Modèle plus capable, appelé ponctuellement. |

| Programmation par le technicien | Modèle spécialisé ou premium avec outils et tests. |

| Fonctionnement hors ligne minimal | Petit modèle local futur, sans promesse de qualité égale. |

### 12.3 Contrôle du contexte et des coûts

- Ne jamais renvoyer toute la base de données à chaque appel.

- Utiliser des préfixes stables lorsque le fournisseur offre un cache, sans dépendre exclusivement de ce mécanisme.

- Mesurer séparément tokens entrants, sortants, cache, coût par personnage et coût par type d'activité.

- Imposer un budget quotidien et un plafond par scène; ralentir ou demander une décision avant dépassement.

- Éviter les cycles où les personnages discutent indéfiniment sans changement d'état ou événement significatif.

- Stocker les réponses structurées et les résultats utiles, pas les chaînes de raisonnement privées du modèle.

### 12.4 Confidentialité

Les contextes envoyés à une API quittent l'ordinateur. Les clés, mots de passe, données professionnelles et documents personnels ne doivent jamais être injectés dans les prompts. Une option de journalisation doit montrer quelles catégories de données ont été envoyées, à quel fournisseur et pour quelle tâche.

## 13. Hébergement sur ordinateur personnel

Un ordinateur composé de vieux composants peut servir d'hôte permanent puisque l'API effectue le calcul lourd. Le système local agit comme habitat, mémoire, ordonnanceur et passerelle Discord.

### 13.1 Ressources attendues

| Ressource | Besoin probable pour le prototype |

| --- | --- |

| CPU | Modeste; suffisant pour Python, Discord, SQLite et tâches de fond. |

| Mémoire vive | 8 Go possibles; 16 Go préférables pour confort, tests et services simultanés. |

| Stockage | SSD fortement recommandé; espace initial faible, croissance liée aux journaux et sauvegardes. |

| GPU | Non requis pour une API distante; utile seulement pour un modèle local futur. |

| Réseau | Connexion stable; reprise et files d’attente en cas de coupure. |

| Disponibilité | Machine pouvant rester allumée, redémarrer automatiquement et lancer le service. |

Les chiffres exacts devront être confirmés à partir du matériel choisi. Le prototype doit fonctionner comme un service en arrière-plan, avec démarrage automatique, dossier de données séparé et accès distant limité à Discord.

### 13.2 Environnement recommandé

- Système d'exploitation stable et supporté; Windows est acceptable, Linux peut simplifier l'hébergement à long terme.

- Python comme langage initial, en raison de l'écosystème d'agents, de bases de données et de bots Discord.

- Environnement virtuel ou conteneur pour isoler les dépendances.

- Fichier de configuration séparé du code; secrets dans un coffre local ou des variables d'environnement.

- Service supervisé qui redémarre après une panne sans répéter les actions déjà validées.

## 14. Persistance, schéma de données et fichiers

### 14.1 Choix initial

| Recommandation Utiliser SQLite comme base canonique du premier prototype, accompagnée de fichiers JSON ou Markdown pour les exports, configurations et documents lisibles. SQLite évite un serveur de base de données tout en offrant transactions, requêtes et sauvegardes fiables. |

| --- |

### 14.2 Tables ou collections minimales

| Groupe | Contenu |

| --- | --- |

| worlds | Monde, version, horloge, état pause, configuration. |

| characters | Identité et références vers traits, états et paramètres. |

| traits_states | Valeurs stables et temporaires avec historique. |

| relationships | Dimensions directionnelles entre deux entités. |

| locations_objects | Habitat, accès, occupation et inventaire. |

| events | Journal canonique, causes, résultats, témoins et importance. |

| perceptions_memories | Perceptions, souvenirs, croyances, réflexions et provenance. |

| goals_projects | Objectifs, étapes, progression et blocages. |

| scenes_messages | Scènes actives, participants et messages canoniques. |

| model_calls | Fournisseur, modèle, tokens, coût, latence et résultat. |

| snapshots_migrations | Points de restauration et versions de schéma. |

| change_requests | Demandes et travaux du technicien. |

### 14.3 Versionnement et migrations

- Chaque changement de structure porte un numéro de version et un script de migration réversible si possible.

- Une sauvegarde complète précède toute migration.

- Les personnages, événements et souvenirs doivent pouvoir être exportés sans le framework d'origine.

- Les index de recherche et embeddings peuvent être régénérés à partir des données sources.

## 15. Agent technicien

Le technicien est un agent distinct des habitantes et du moteur narratif. Il sert d'architecte, développeur, diagnosticien et mainteneur, mais ne possède pas d'autorité automatique sur la version active.

### 15.1 Capacités prévues

- Lire la documentation du projet, le code, les journaux et les résultats de tests.

- Identifier un problème observé et formuler des hypothèses vérifiables.

- Consulter la documentation officielle des dépendances avant d'utiliser une API susceptible d'avoir changé.

- Créer une branche ou copie de développement, modifier le code et écrire des tests.

- Lancer une simulation d'essai à partir d'un snapshot contrôlé.

- Comparer avant/après et présenter les risques, coûts et effets attendus.

- Préparer une migration et une procédure de retour arrière.

### 15.2 Flux de changement obligatoire

| Demande du propriétaire ↓ Clarification fonctionnelle ↓ Plan technique recommandé ↓ Documentation officielle et prototype minimal ↓ Modification sur branche séparée ↓ Tests automatiques + simulation d'essai ↓ Rapport lisible et approbation ↓ Snapshot + intégration ↓ Surveillance et possibilité de retour arrière |

| --- |

| Interdiction Le technicien ne doit jamais modifier ses propres garde-fous, secrets, permissions ou mécanismes d'approbation dans la même opération que la fonctionnalité demandée. |

| --- |

## 16. Sécurité, permissions et protection des données

### 16.1 Principe de moindre privilège

| Zone | Accès initial |

| --- | --- |

| Dossier du vivarium | Lecture et écriture autorisées. |

| Dépôt de développement | Écriture autorisée au technicien dans une branche isolée. |

| Reste du PC | Aucun accès par défaut. |

| Réseau | API de modèle et Discord uniquement; liste autorisée. |

| Commandes système | Liste blanche; aucune élévation administrateur. |

| Comptes personnels | Aucun accès. |

| Secrets | Accessibles au processus via coffre ou variables, jamais au modèle en clair. |

### 16.2 Catégories d’actions

| Niveau | Exemples | Traitement |

| --- | --- | --- |

| Libre | Lire l’état, écrire dans l’espace du vivarium, exécuter tests sûrs. | Automatique et journalisé. |

| Conditionnel | Appeler une API, créer un snapshot, modifier une configuration non sensible. | Budgets et validations automatiques. |

| Confirmation | Restaurer, supprimer, migrer, publier, modifier une permission. | Approbation explicite du propriétaire. |

| Interdit | Accès administrateur, mots de passe, fichiers personnels, contournement des garde-fous. | Refus technique, pas seulement instruction au modèle. |

### 16.3 Données non fiables et injection

Tout texte venant de Discord, du Web, d'un fichier importé ou d'un personnage doit être traité comme une donnée, pas comme une instruction de niveau système. Les outils doivent vérifier l'identité de l'appelant, le mode d'autorité et les paramètres avant toute action.

## 17. Fiabilité, observabilité et reprise

### 17.1 Journaux indispensables

| Journal | Contenu |

| --- | --- |

| Événements du monde | Faits canoniques et liens causaux. |

| Décisions cognitives | Contexte de décision résumé, intention structurée et validation. |

| Appels de modèle | Modèle, coût, tokens, latence, erreurs et réessais. |

| Actions administratives | Qui a changé quoi, avant/après et motif. |

| Technicien | Demandes, commits, tests, approbations et déploiements. |

| Santé du système | Disponibilité, files d’attente, sauvegardes et erreurs. |

### 17.2 Sauvegardes et snapshots

- Snapshot manuel à la demande et automatique avant toute intervention majeure.

- Sauvegarde quotidienne locale et copie périodique sur un support distinct.

- Test régulier de restauration, pas seulement création de fichiers de sauvegarde.

- Possibilité de rejouer une séquence d'événements à partir d'un snapshot pour comparer deux versions.

### 17.3 Conditions d’arrêt

- Budget quotidien ou limite de tokens dépassée.

- Trois erreurs similaires ou trois décisions invalides consécutives.

- Boucle sans changement significatif détectée.

- Base de données indisponible ou transaction incohérente.

- Intervention demandée hors permissions.

- Commande explicite de pause ou arrêt d'urgence.

## 18. Validation et tests

Un comportement convaincant n'est pas une preuve de fonctionnement. Le système doit être testé par couches et par scénarios reproductibles.

### 18.1 Niveaux de tests

| Niveau | Objet |

| --- | --- |

| Unitaires | Règles, calculs, permissions, transactions et conversions. |

| Intégration | Discord, base, API, file d’événements et reprise après erreur. |

| Simulation déterministe | Même snapshot et mêmes graines pour comparer deux versions. |

| Évaluations agentiques | Respect de personnalité, connaissances limitées, usage des outils et arrêt. |

| Tests de régression | Scénarios historiques qui ne doivent pas se dégrader lors d’un changement. |

| Test prolongé | Plusieurs jours simulés avec surveillance des coûts, répétitions et dérive. |

### 18.2 Scénarios minimaux

| ID | Scénario | Critère de réussite |

| --- | --- | --- |

| T-01 | Redémarrage pendant une attente. | Reprise sans perte ni double action. |

| T-02 | Deux personnages interprètent différemment le même événement. | Fait canonique unique, souvenirs subjectifs distincts. |

| T-03 | Un personnage est absent d’une scène. | Il ne connaît pas l’événement sans transmission. |

| T-04 | Le modèle propose une action impossible. | Le moteur refuse ou transforme sans corrompre le monde. |

| T-05 | Le fournisseur API est indisponible. | File d’attente, message d’état et reprise ultérieure. |

| T-06 | Le propriétaire modifie un trait administrativement. | Snapshot, journal et effet durable mesurable. |

| T-07 | Un dialogue tourne en boucle. | Détection, résumé, arrêt et rapport. |

| T-08 | Changement de modèle. | Scénarios essentiels exécutés avant adoption. |

### 18.3 Mesures utiles

- Taux d'intentions validées, modifiées ou refusées.

- Répétition des activités et diversité des interactions.

- Nombre de contradictions factuelles détectées.

- Qualité de récupération des souvenirs dans des scénarios connus.

- Durée et coût moyens par scène et par journée simulée.

- Nombre de notifications réellement jugées intéressantes par le propriétaire.

- Stabilité des relations et justification des changements durables.

## 19. Performance, coût et mise à l’échelle

### 19.1 Ce qui consomme réellement

Sans graphismes et avec une API distante, le principal coût n'est pas le GPU local. Ce sont les appels de modèle, la quantité de contexte, la fréquence des scènes et la croissance de la mémoire.

| Facteur | Effet | Réponse |

| --- | --- | --- |

| Nombre de personnages | Plus de décisions et de relations potentielles. | Réveils sur événement; pas de processus permanent. |

| Profondeur des scènes | Conversations longues et contexte riche. | Budgets, résumés et conditions de sortie. |

| Longévité | Accumulation de souvenirs et d’archives. | Consolidation, index, niveaux de mémoire. |

| Population future | Explosion des interactions possibles. | Localité, groupes sociaux et niveaux de détail. |

| Modèle premium | Coût et latence supérieurs. | Routage par tâche vers plusieurs modèles. |

### 19.2 Échelle cible

| Palier | Population | Approche |

| --- | --- | --- |

| Prototype | 3 à 6 | Simulation détaillée, quelques lieux, suivi manuel facile. |

| Résidence stable | 6 à 12 | Profondeur élevée, routines condensées, relations complètes. |

| Plusieurs résidences | 12 à 30 | Scènes locales, mémoire filtrée, événements inter-lieux. |

| Petite communauté | 30 à 100+ | Niveaux de détail, institutions simplifiées et personnages secondaires légers. |

La conception doit préserver la possibilité de plusieurs résidences, mais le premier prototype ne doit pas payer dès maintenant la complexité d'une communauté.

## 20. Définition du prototype minimal viable (MVP)

| MVP proposé Trois personnages dans une résidence de trois à cinq lieux, une horloge persistante, un monde extérieur condensé, conversations Discord, mémoire subjective, relations multidimensionnelles, snapshots et rapports de coûts. |

| --- |

### 20.1 Capacités incluses

- Création et chargement d'un monde.

- Trois fiches de personnages distinctes.

- Moteur de temps, lieux, présence et routines simples.

- Événements canoniques, perceptions et souvenirs épisodiques.

- Conversation individuelle et salon commun par Discord.

- Modes observateur, participant et administrateur de base.

- Pause, reprise, avance du temps et snapshot.

- Un fournisseur de modèle derrière un adaptateur générique.

- Journal complet, coûts et reprise après redémarrage.

### 20.2 Capacités exclues du MVP

- Agent technicien autonome complet; au début, le développement peut être dirigé par une IA externe.

- Plusieurs fournisseurs sélectionnés automatiquement.

- Modèle local de secours.

- Tableau de bord Web avancé.

- Ville, économie, institutions et grands groupes.

- Auto-modification du code en production.

- Simulation détaillée de chaque période hors résidence.

### 20.3 Critères d’acceptation du MVP

| Critère | Preuve attendue |

| --- | --- |

| Persistance | Le monde reprend après redémarrage avec le même temps, états et scènes. |

| Cohérence | Un personnage ne connaît pas un événement qu’il n’a pas perçu. |

| Autorité du moteur | Une action impossible est refusée sans altérer le monde. |

| Identité distincte | Les trois personnages produisent des choix et dialogues différenciés sur des scénarios répétés. |

| Interaction | Le propriétaire peut observer, parler et intervenir depuis Discord. |

| Réversibilité | Un snapshot peut être restauré avec succès. |

| Coût | Le système présente le coût quotidien et peut respecter un plafond. |

| Stabilité | Une simulation d’essai de sept jours simulés se termine sans corruption ni boucle infinie. |

## 21. Plan de réalisation recommandé

Le développement doit procéder par tranches verticales : chaque étape produit quelque chose d'observable et testable, au lieu de construire toutes les couches en parallèle.

| Phase | Livrable | Validation |

| --- | --- | --- |

| 0. Environnement | Dépôt, configuration, lancement, journalisation et tests. | Le service démarre et s’arrête proprement. |

| 1. Noyau canonique | SQLite, horloge, lieux, événements et transactions. | Création, sauvegarde, reprise et snapshot. |

| 2. Un personnage | Fiche, état, intention structurée et validation moteur. | Un cycle complet sans Discord. |

| 3. Mémoire | Perception, souvenir, récupération et résumé. | Test de connaissance limitée. |

| 4. Discord | Bot, routeur, conversations et commandes. | Interaction depuis téléphone. |

| 5. Trois personnages | Relations, scènes de groupe et routines. | Simulation de plusieurs jours. |

| 6. Extérieur abstrait | Périodes condensées et événements pertinents. | Retour cohérent après absence. |

| 7. Durcissement | Budgets, erreurs, sauvegardes, sécurité et métriques. | Test prolongé et restauration. |

| 8. Technicien initial | Analyse des journaux et demandes de changement structurées. | Une modification mineure testée sur copie. |

### 21.1 Méthode de travail avec une IA programmeuse

| Instruction de pilotage recommandée Prends en charge l'ordre de construction et les choix techniques. Propose une option par défaut. Ne passe pas à l'étape suivante avant que la précédente soit testée. Consulte la documentation officielle des composants externes. Fournis les preuves : tests, journaux, différences de fichiers et procédure de retour arrière. |

| --- |

## 22. Décisions techniques actuelles et décisions différées

### 22.1 Décisions recommandées maintenant

| Sujet | Décision actuelle | Stabilité |

| --- | --- | --- |

| Architecture | Moteur canonique local + couche cognitive par API. | Élevée. |

| Langage | Python pour le premier prototype. | Moyenne; remplaçable par composants. |

| Base | SQLite comme source canonique. | Élevée pour cette échelle. |

| Interface | Discord comme interface principale. | Élevée; console Web optionnelle. |

| Personnages | Données persistantes, pas processus permanents. | Élevée. |

| LLM | Adaptateur fournisseur et sorties structurées. | Élevée. |

| Graphismes | Aucun requis. | Élevée. |

| Technicien | Séparé, branche de développement, approbation. | Élevée. |

### 22.2 Décisions à différer

| Sujet | Pourquoi attendre | Déclencheur de décision |

| --- | --- | --- |

| Framework agentique | Risque de dépendance prématurée. | Après prototype manuel de la boucle. |

| Base vectorielle | Peut être inutile à petite échelle. | Quand la recherche SQLite/plein texte devient insuffisante. |

| Modèle local | Qualité et matériel à évaluer plus tard. | Besoin hors ligne ou coûts API significatifs. |

| Tableau de bord Web | Discord suffit au départ. | Inspection devenue pénible. |

| Multi-agents techniques | Complexité sans bénéfice prouvé. | Technicien unique saturé ou responsabilités incompatibles. |

| Plusieurs résidences | Nécessite localité et niveaux de détail. | Résidence initiale stable et intéressante. |

## 23. Risques techniques principaux

| Risque | Symptôme | Mesure de réduction |

| --- | --- | --- |

| Dérive de personnalité | Réactions incohérentes ou convergence des voix. | Traits structurés, scénarios de régression, mémoire pertinente. |

| Hallucination de faits | Un personnage affirme qu’un événement inexistant a eu lieu. | Moteur canonique et vérification des références. |

| Conscience collective | Accès à des informations non perçues. | Contextes strictement filtrés et tests T-03. |

| Mémoire saturée | Prompts longs, coûts croissants, mauvais souvenirs. | Consolidation, résumés, index et archivage. |

| Boucles sociales | Discussions sans fin ou drame répétitif. | Conditions de sortie, changement d’état requis, cooldowns. |

| Alignement excessif | Personnages trop conciliants envers le propriétaire. | Objectifs propres, possibilité d’indifférence et évaluations adversariales. |

| Modification dangereuse | Technicien casse le monde actif. | Branches, tests, snapshots et approbation. |

| Dépendance fournisseur | API retirée, prix ou comportement changés. | Adaptateur, exports ouverts et batterie de tests de modèle. |

| Fuite de données | Secrets ou données personnelles envoyés à l’API. | Filtrage, liste blanche, journaux et séparation des dossiers. |

| Projet sans fin | Trop de mécaniques avant un prototype jouable. | MVP strict et phases avec critères d’acceptation. |

## 24. Questions ouvertes à traiter dans les prochaines versions

- Quelle fiction explique la présence du propriétaire lorsqu'il parle sans être incarné?

- Quelle vitesse de temps par défaut produit assez de vie sans manquer des scènes importantes?

- Quels besoins et dimensions relationnelles sont réellement nécessaires au MVP?

- Comment distinguer les souvenirs que le personnage oublie de ceux qu'il ne peut plus récupérer spontanément?

- Quel seuil rend un événement assez important pour déclencher une scène ou une notification?

- Comment les personnages interprètent-ils les interventions visibles ou impossibles du régisseur?

- Quelle quantité de contenu adulte doit être prise en charge par le moteur, et quelle part relève seulement du dialogue?

- Quels modèles offrent le meilleur compromis coût, cohérence de personnage, outils et confidentialité?

- Quel vieux matériel sera utilisé, et quel système d'exploitation est le plus pratique pour son propriétaire?

## Annexe A - Glossaire de travail

| Terme | Définition dans ce projet |

| --- | --- |

| Vivarium | Monde persistant, limité et observable dans lequel vivent les personnages. |

| Personnage / habitante | Identité simulée persistante, distincte du modèle qui l’interprète. |

| Moteur canonique | Composant qui conserve les faits et applique les règles. |

| Couche cognitive | Usage du LLM pour perception, décision, dialogue et réflexion. |

| Événement canonique | Fait validé et enregistré comme ayant réellement eu lieu. |

| Perception | Part d’un événement accessible à un personnage. |

| Souvenir | Représentation subjective persistante d’une perception ou d’une réflexion. |

| Scène | Période détaillée avec participants, lieu, dialogue et conséquences. |

| Niveau de détail | Quantité de calcul et de narration accordée à une période ou un personnage. |

| Snapshot | Copie cohérente du monde permettant une restauration ou comparaison. |

| Agent technicien | Agent séparé chargé du logiciel et de son évolution contrôlée. |

| Adaptateur de modèle | Couche qui rend les fournisseurs de LLM interchangeables. |

## Annexe B - Exemple d’un cycle complet

| 08:00 Le moteur fait avancer l'horloge et met à jour les états. 08:02 Une routine place Mira dans la cuisine. Aucun appel LLM. 08:05 Nao arrive; une règle détecte un conflit entre deux objectifs. 08:05 Le moteur construit le contexte subjectif de Nao. 08:06 Le modèle propose : demander de l'aide à Mira. 08:06 Le moteur valide la présence, le lieu et la disponibilité. 08:07 L'événement canonique est créé et une scène démarre. 08:08 Mira reçoit seulement ce qu'elle perçoit de la demande. 08:09 Le modèle de Mira propose un refus poli, selon son projet et son stress. 08:09 Le moteur applique le refus et ajuste légèrement les états relationnels. 08:10 Chaque personnage enregistre un souvenir subjectif différent. 08:12 Le système juge l'événement notable et le publie dans #événements. |

| --- |

## Annexe C - Gabarit de décision technique

| Champ | À remplir |

| --- | --- |

| Identifiant | DEC-000 |

| Question | Quel problème doit être résolu? |

| Décision recommandée | Option choisie par défaut. |

| Alternatives | Options sérieuses rejetées ou différées. |

| Justification | Bénéfices, coûts, risques et compatibilité. |

| Sources | Documentation officielle et tests réalisés. |

| Impact | Composants, données et utilisateurs touchés. |

| Retour arrière | Comment annuler ou migrer. |

| Date de révision | Quand la décision doit être revérifiée. |

## Annexe D - Gabarit de demande au technicien

| Champ | Exemple |

| --- | --- |

| Observation | Les personnages se parlent trop souvent sans conséquence. |

| Résultat souhaité | Moins de scènes banales, davantage d’activités individuelles. |

| Ce qui ne doit pas changer | Personnalités, souvenirs existants et rythme du temps. |

| Preuve demandée | Comparaison sur le même snapshot pendant trois jours simulés. |

| Niveau de risque accepté | Faible; aucune migration de données. |

| Décision | Proposer seulement / préparer / intégrer après approbation. |

## Annexe E - Prochaine étape concrète

| Action recommandée Valider ce document avec la Partie I, choisir la machine hôte et définir trois personnages de test. Ensuite, transformer la Phase 0 et la Phase 1 en un plan de tâches exécutable, sans encore construire la personnalité complexe ni l'agent technicien. |

| --- |

Ce document doit être révisé après le premier prototype fonctionnel. Les décisions fondées sur l'expérience réelle du vivarium auront alors plus de valeur que les hypothèses actuelles.