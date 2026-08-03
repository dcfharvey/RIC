> **SOURCE HISTORIQUE NON NORMATIVE.** En cas de différence, `docs/00_DOSSIER_MAITRE_IA.md` prévaut.

DOSSIER DE CONCEPTION - PARTIE III

Vivarium social artificiel

Spécification fonctionnelle du prototype initial

__________________________________________________________________

Définition des comportements, interactions, pouvoirs du propriétaire,
persistance et critères d'acceptation de la première version exploitable

Version 0.1 - août 2026

Statut : spécification de travail validée au niveau fonctionnel - document vivant

Place dans le dossier : la Partie I fixe la vision, la Partie II l'architecture générale,
et la Partie III décrit ce que le prototype doit effectivement faire.

## 0. Comment utiliser ce document

Cette Partie III transforme les intentions des Parties I et II en comportements observables. Elle ne dicte pas encore le schema SQL, les classes Python ou les bibliothèques à employer. Elle fixe plutot ce que l'utilisateur, les personnages, le moteur et le technicien doivent pouvoir faire dans le premier prototype, ainsi que les résultats attendus.

| Règle de priorité Pour le prototype initial, cette Partie III prévaut lorsqu'une formulation plus générale des Parties I ou II laisse plusieurs interprétations possibles. Une contradiction explicite doit être signalée avant le codage, et non résolue silencieusement par l'IA programmeuse. |

| --- |

### 0.1 Lecteurs vises

- Le propriétaire du projet, qui valide l'expérience et les règles sans devoir connaitre la programmation.

- Une IA architecte ou programmeuse, qui doit traduire les exigences en composants testables.

- Un futur developpeur humain, qui doit pouvoir comprendre les choix sans reconstruire toute la conversation d'origine.

- L'agent technicien, lorsqu'il devra diagnostiquer le comportement ou proposer une évolution du vivarium.

### 0.2 Statut des exigences

| Etiquette | Sens |

| --- | --- |

| OBLIGATOIRE | Necessaire pour déclarer le prototype conforme à cette spécification. |

| CONFIGURABLE | Fonction obligatoire dont le comportement peut être activée, désactivée ou ajustée par le propriétaire. |

| RECOMMANDÉ | Valeur par défaut retenue, modifiable si les essais montrent une meilleure option. |

| DIFFÉRÉ | Capacité volontairement exclue du prototype, mais dont l'architecture ne doit pas bloquer l ajout futur. |

### 0.3 Définition de "prototype initial"

Le prototype initial n'est pas une demonstration jetable. Il s'agit de la première version persistante que le propriétaire peut laisser fonctionner sur son ordinateur personnel, observer dans Discord, interrompre, redemarrer et faire évoluer sans perdre le monde. Il peut être rudimentaire dans sa présentation, mais ses règles de vérité, de mémoire et d'autorité doivent déjà être saines.

## 1. Résultat attendu du prototype

| Objectif fonctionnel Faire vivre en continu quatre personnages adultes dans une résidence textuelle persistante. Elles agissent, discutent, se souviennent, evoluent et reagissent aux interventions d'un propriétaire connu comme entite supérieure. Discord sert de principale fenetre d'interaction; le monde officiel reste gere par un moteur local et non par le texte improvise du modèle. |

| --- |

### 1.1 Expérience minimale réussie

- Le propriétaire peut revenir après plusieurs heures et constater que des activités et interactions cohérentes ont eu lieu.

- Chaque personnage conserve une voix, des préférences, des objectifs et une histoire relationnelle reconnaissables.

- Deux personnages peuvent percevoir, interpreter et raconter différemment un même événement sans que le monde canonique se contredise.

- Le propriétaire peut parler à une personne ou au groupe, observer les scènes entre elles et modifier le monde selon son niveau d'autorité.

- Une fermeture du programme ne remet pas les personnages à zéro; le redémarrage consolide la période d'absence et reprend à partir d'un état valide.

- Les routines banales ne saturent pas Discord et ne consomment pas inutilement des appels de modèle.

### 1.2 Population et habitat de départ

| Élément | Définition retenue |

| --- | --- |

| Population | Quatre personnages adultes persistants. |

| Résidence | Un salon, une cuisine, quatre chambres individuelles, une salle de bain et une cour. |

| Représentation | Textuelle et structurée; aucun graphisme de jeu n'est requis. |

| Monde extérieur | Abstrait, accessible pour des sorties et occupations, sans simulation détaillée de toute une population. |

| Propriétaire | Entite supérieure connue des personnages, capable de communiquer, observer et intervenir. |

| Interface principale | Serveur Discord prive avec identité visuelle distincte pour chaque personnage. |

### 1.3 Non-objectifs du prototype

- Simuler une ville, une économie complète ou des centaines d'habitants.

- Produire des animations, une carte graphique ou un moteur physique.

- Reproduire scientifiquement la psychologie humaine.

- Donner au technicien le droit de modifier automatiquement le code actif.

- Faire vieillir les personnages, gérer les maladies, la mort ou la grossesse.

- Faire fonctionner des modèles locaux dans la première version, même si l'architecture doit permettre cette migration plus tard.

## 2. État global, démarrage et fonctionnement continu

Le vivarium fonctionne sur l'ordinateur personnel du propriétaire. Tant que l'application est active, le temps simulé suit le temps réel et le moteur traite les événements, routines et décisions selon leur cadence. L'utilisation normale de l'ordinateur, y compris le jeu, ne met pas automatiquement le vivarium en pause.

### 2.1 Cycle de vie de l'application

| État | Comportement attendu |

| --- | --- |

| Démarrage | Charger le dernier état valide, vérifier l'intégrité, calculer la période d absence, puis reprendre le temps réel. |

| Fonctionnement normal | Maintenir l'horloge, résoudre les routines, déclencher les décisions significatives et publier selon les réglages Discord. |

| Pause administrative | Geler les nouvelles actions tout en permettant inspection, sauvegarde et maintenance. |

| Arrêt ordonne | Clôturer les scènes ouvertes, sauvegarder l état et enregistrer l'heure d arrêt. |

| Arrêt inattendu | Reprendre depuis la derniere transaction valide et clôturer automatiquement les conversations interrompues. |

| Maintenance | Désactiver temporairement les appels de modèle et les sorties Discord sans corrompre le temps ni les données. |

### 2.2 Rattrapage après une période hors ligne

Lorsque l'ordinateur était éteint, en veille ou que l'application ne fonctionnait pas, le système ne rejoue pas chaque minute. Au redémarrage, il calcule une période condensée en combinant horaires, routines, besoins, projets, relations et événements probables. Les événements importants deviennent canoniques; les détails banals sont résumés.

1.  Mesurer la durée écoulée depuis la derniere sauvegarde valide.

2.  Appliquer les evolutions déterministes : sommeil, faim, fatigue, horaires, récupération et durees de projet.

3.  Identifier les rencontres et décisions qui auraient raisonnablement pu produire un événement significatif.

4.  Utiliser le modèle seulement pour les quelques choix ou interactions qui méritent une interprétation cognitive.

5.  Produire un résumé de rattrapage et reprendre au temps réel courant.

| Critère important Le rattrapage ne doit ni inventer une semaine de drames pour remplir le vide, ni prétendre que rien ne s'est passe. Sa densité doit rester proportionnelle a la durée, aux routines et aux relations existantes. |

| --- |

### 2.3 Conversations interrompues

Une conversation interrompue par une fermeture ou une panne ne reprend pas au milieu d'une phrase. Le moteur conserve les messages déjà émis, marque la scène comme interrompue, crée une clôture contextuelle minimale et met à jour les souvenirs uniquement à partir de ce qui a effectivement eu lieu.

## 3. Résidence et monde spatial

La résidence est le niveau de simulation détaillé. Les lieux ne sont pas de simples salons Discord : ils possedent une existence canonique, des occupants, des objets, une confidentialité et des actions possibles. Discord ne fait que présenter une partie de cet état.

### 3.1 Lieux obligatoires

| Lieu | Fonctions minimales | Confidentialité par défaut |

| --- | --- | --- |

| Salon | Conversation de groupe, repos, loisirs, objets communs, événements collectifs. | Public au sein de la résidence. |

| Cuisine | Preparation et prise de repas, rangement, discussions informelles. | Public au sein de la résidence. |

| Chambres 1 à 4 | Sommeil, solitude, projets personnels, rangement et scènes privées. | Privée; accès selon relation, invitation et règles. |

| Salle de bain | Hygiène, besoins corporels, récupération et accès exclusif selon occupation. | Privée; une personne ou groupe autorisé selon contexte. |

| Cour | Activités extérieures, detente, rencontres et transitions vers le monde extérieur. | Semi-public au sein du vivarium. |

### 3.2 Propriétés fonctionnelles d'un lieu

- Nom, type et description persistante.

- Liste des personnes présentes et historique récent des passages.

- Objets et activités disponibles.

- Capacité ou contraintes d'occupation lorsque pertinentes.

- Niveau de confidentialité et conditions d'accès.

- Ambiance temporaire : propreté, bruit, éclairage, température narrative ou événement particulier.

- Liens vers les autres lieux et vers le monde extérieur abstrait.

### 3.3 Sorties hors de la résidence

Les personnages peuvent quitter physiquement la résidence pour travailler, magasiner, se divertir, rencontrer des contacts ou poursuivre un projet. Ces sorties sont condensées tant qu'aucune scène importante n'exige un zoom narratif. Quitter la résidence ne signifie pas quitter le vivarium.

| Départ définitif protégé Aucun personnage ne peut être supprimé, abandonner silencieusement l'aventure ou devenir inaccessible par une décision routinière. Un désir de partir définitivement doit devenir un événement majeur, être exprimé au propriétaire et attendre une décision administrative explicite. |

| --- |

## 4. Personnages, identité et autonomie

Chaque personnage est une identité persistante et non un simple prompt. Son état est conserve dans les données du vivarium; le modèle de langage l'interprète au moment de parler, decider ou réfléchir. Les quatre personnages disposent d'une autonomie complète à l'intérieur des possibilités du monde.

### 4.1 Capacités autonomes

- Choisir ses activités quotidiennes et modifier son plan selon les circonstances.

- Créer, poursuivre, suspendre ou abandonner des projets personnels.

- Parler aux autres, rechercher leur présence, éviter une interaction ou demander de l'intimité.

- Developper des amities, attirances, rivalités, conflits, alliances et habitudes de groupe.

- Changer graduellement d'intérêts, de priorités, de croyances et de comportement.

- Contacter spontanément le propriétaire lorsque cette option est activee.

- Sortir dans le monde extérieur abstrait et revenir selon ses horaires et intentions.

- Exprimer un désaccord avec le propriétaire ou réagir aux interventions qu'elle perçoit.

### 4.2 Limites structurelles

| Limite | Raison fonctionnelle |

| --- | --- |

| Aucune sortie définitive automatique | La permanence du casting est une règle du vivarium et une modification majeure exigeant le propriétaire. |

| Aucun accès direct au PC ou à Internet | Les personnages agissent dans le monde simulé; les outils système appartiennent au moteur ou au technicien. |

| Aucune modification du monde canonique par narration | Une intention ou une réplique ne suffit pas à créer un objet, déplacer une personne ou modifier un souvenir. |

| Aucune connaissance omnisciente | Chaque personne ne connait que ses perceptions, souvenirs, informations recues et connaissances generales autorisées. |

| Aucune alteration de ses propres règles de sécurité | Un personnage peut souhaiter un changement, mais ne peut contourner les permissions administratives. |

### 4.3 Personnages originaux et personnages canoniques

Un personnage original peut évoluer librement dans les limites de sa cohérence. Pour un personnage canonique de fiction, le propriétaire definit une fiche de fidélité distinguant les éléments figés, les éléments souples et les éléments libres.

| Catégorie | Exemples | Règle |

| --- | --- | --- |

| Figé | Identité fondamentale, histoire de référence, valeurs essentielles, traits iconiques. | Ne change pas sans intervention administrative confirmée. |

| Souple | Habitudes, opinions secondaires, intérêts non centraux, style relationnel. | Peut évoluer lentement si les événements le justifient. |

| Libre | Humeur, projets du moment, souvenirs du vivarium, relations créées dans le monde. | Évolue normalement avec la simulation. |

Tous les personnages utilises dans le prototype doivent être explicitement adultes dans la version représentée. Toute ambiguite d'âge doit être résolue avant leur création.

## 5. Besoins, états et activité quotidienne

Le prototype suit des besoins assez détaillés afin que le comportement ne repose pas uniquement sur une biographie textuelle. Les valeurs exactes restent cachées à l'utilisateur en fonctionnement normal. Elles influencent les actes et deviennent visibles à travers les comportements, les paroles et les conséquences.

### 5.1 Besoins minimaux

| Besoin ou état | Effets attendus |

| --- | --- |

| Faim et alimentation | Déclenche repas, recherche de nourriture, irritabilite ou baisse d'énergie si négligé. |

| Sommeil et fatigue | Influence l'horaire, la concentration, l'humeur et la récupération. |

| Hygiène | Génère des routines, inconfort et conséquences sociales raisonnables. |

| Confort physique | Tient compte du lieu, du repos, de la température narrative et des blessures. |

| Sociabilité | Pousse vers la compagnie, les conversations ou les activités communes. |

| Besoin de solitude | Peut entrer en conflit avec la sociabilité et justifier le retrait. |

| Stimulation et ennui | Encourage loisirs, curiosité, projets et recherche de nouveauté. |

| Libido | État individuel influencé par les préférences, l'humeur, la relation, le contexte et les limites. |

| Humeur | État composite qui colore la perception et la prise de décision sans dicter une action unique. |

| Stress ou tension | Peut ralentir les projets, modifier les interactions et demander récupération ou soutien. |

### 5.2 Valeurs cachées et lisibilite comportementale

Le propriétaire ne voit pas en permanence des jauges numériques. Le système doit produire des indices observables : une personne fatiguée écourte une conversation, une personne isolée recherche la compagnie, une personne irritée répond différemment. Le mode administrateur peut inspecter les valeurs brutes lorsque necessaire au diagnostic.

| Principe de conception Les statistiques servent à maintenir la continuité; elles ne doivent pas transformer la relation en tableau de scores ni garantir une réaction. Plusieurs états peuvent tirer une personne dans des directions opposées. |

| --- |

### 5.3 Niveau d'activité

Les personnages sont configurées comme assez actives. Elles doivent produire plusieurs actions quotidiennes, mais seules les actions porteuses de conséquence sociale, personnelle ou narrative nécessitent un appel de modèle et une publication Discord.

| Niveau | Traitement |

| --- | --- |

| Routine banale | Moteur déterministe ou règles probabilistes; trace condensée. |

| Choix personnel simple | Règles + contexte; appel de modèle seulement si plusieurs options ont un sens psychologique. |

| Interaction sociale significative | Appel de modèle pour les intentions et le dialogue; résolution canonique par le moteur. |

| Événement majeur | Scène détaillée, mémoire durable, notification et possibilité d'intervention du propriétaire. |

## 6. Relations et dynamique sociale

Les relations existent entre toutes les paires de personnages ainsi qu'entre chaque personnage et le propriétaire. Elles sont multidimensionnelles, asymétriques et partiellement cachées. Une relation ne se résume pas à l'affection.

### 6.1 Dimensions relationnelles minimales

| Dimension | Interprétation |

| --- | --- |

| Familiarité | Quantité et profondeur de l'histoire partagee. |

| Confiance | Attente que l'autre soit fiable, honnête ou protectrice. |

| Affection | Chaleur émotionnelle et désir de proximité. |

| Attirance | Intérêt romantique ou sexuel, distinct de l affection et de la confiance. |

| Respect | Reconnaissance des capacités, valeurs ou limites de l'autre. |

| Sécurité | Sentiment de pouvoir être vulnérable sans danger relationnel. |

| Irritation | Tension récente ou chronique susceptible de colorer les interactions. |

| Jalousie ou possessivité | Réaction possible à la répartition de l'attention ou a certaines relations, selon le personnage. |

### 6.2 Règles d évolution

- Les changements importants exigent un événement ou une accumulation d'expériences plausibles.

- Les dimensions peuvent évoluer dans des directions differentes : attirance élevée et confiance faible, affection élevée et irritation temporaire, etc.

- Une scène positive ne supprimé pas automatiquement un conflit ancien.

- Les relations entre habitantes ont autant de legitimite que leurs relations avec le propriétaire.

- L'indifférence, l'antipathie ou une relation non romantique avec le propriétaire sont des résultats valides.

- Le moteur detecte les sauts inhabituels et peut demander une justification ou régénérer la décision.

### 6.3 Activités de groupe et conversations sans le propriétaire

Les personnages peuvent discuter et agir entre elles sans la participation du propriétaire. Ces interactions continuent même lorsque leur affichage en direct est désactivé. Elles produisent des conséquences, des souvenirs et des changements relationnels normaux.

## 7. Perception, croyances et mémoire

La mémoire est organisée pour séparer la vérité du monde de la version subjective de chaque personnage. Cette séparation est obligatoire afin de permettre les malentendus, les secrets et les souvenirs différents sans corrompre l'état canonique.

### 7.1 Chaîne de transformation d'un événement

| Événement canonique -> Perception disponible pour chaque témoin -> Interprétation subjective -> Souvenir épisodique -> Croyance ou réflexion consolidée -> Influence sur les décisions futures |

| --- |

### 7.2 Types de mémoire obligatoires

| Type | Contenu | Durée |

| --- | --- | --- |

| Mémoire récente | Scènes, conversations et états des dernières heures ou journées. | Détaillée, puis résumée. |

| Mémoire épisodique | Événements vecus avec date, personnes, lieu et interprétation. | Variable selon importance et rappels. |

| Connaissances | Faits appris sur le monde, les autres et le propriétaire. | Jusqu'à correction, oubli ou invalidation. |

| Réflexions | Conclusions générales tirées de plusieurs souvenirs. | Long terme, avec provenance. |

| Mémoire relationnelle | Moments determinants d'une relation et attentes associées. | Long terme, mise à jour graduelle. |

| Mémoire intime | Événements adultes ou prives pertinents, protégés par les règles de visibilité. | Préservée selon importance, avec accès administratif. |

### 7.3 Oubli et consolidation

- Les détails ordinaires perdent progressivement leur précision ou sont regroupés en résumé.

- Les événements importants, souvent rappeles ou fortement émotionnels restent accessibles plus longtemps.

- Oublier un détail n'efface pas automatiquement les effets relationnels déjà produits.

- Les souvenirs contradictoires sont conserves avec leur provenance plutot que fusionnés arbitrairement.

- La mémoire brute reste archivable pour audit, même lorsqu'elle n'est plus envoyée au modèle.

### 7.4 Inspection et modification administrative

Le propriétaire peut inspecter les souvenirs, croyances et réflexions. Il peut demander une correction, un ajout, une suppression ou une recontextualisation. Toute modification psychologique suit le protocole de confirmation de la section 10 et conserve une trace administrative.

## 8. Actions, scènes et conversations

Une action passe toujours par trois étapes : intention du personnage, validation par le moteur, puis conséquence canonique. Les dialogues peuvent être libres dans leur formulation, mais les changements du monde qu'ils impliquent restent structurés.

### 8.1 Catalogue d'actions initial

| Action | Exemples de paramètres | Résultat canonique |

| --- | --- | --- |

| Se déplacer | Lieu de départ, destination, motif. | Présence mise à jour si le trajet est possible. |

| Démarrer une conversation | Interlocutrice, lieu, sujet, confidentialité. | Scène ouverte et participantes enregistrees. |

| Quitter une conversation | Motif et destination eventuelle. | Scène mise à jour ou clôturée. |

| Utiliser un objet | Objet, lieu, activité. | État de l'objet et activité mis à jour. |

| Travailler à un projet | Projet, durée, ressource. | Progression et fatigue calculees. |

| Se reposer ou dormir | Lieu, durée souhaitee. | Besoins et horaire mis à jour. |

| Manger ou cuisiner | Repas, ressources, participantes. | Faim, inventaire et événement social résolu. |

| Observer | Cible ou environnement. | Perception créée sans connaissance automatique des intentions. |

| Écrire ou envoyer un message | Destinataire, canal, contenu. | Message livré selon les règles du monde et de Discord. |

| Sortir | Destination abstraite, but, durée. | Absence de la résidence et résultat condensé. |

| Attendre ou ne rien faire | Durée ou condition. | Temps avance sans action forcée. |

### 8.2 Scènes

Une scène regroupe un lieu, une période, des participantes, un niveau de confidentialité et une succession d'actions. Elle peut être publique, privée ou administrative. Le moteur decide quand elle commence, quand elle se termine et quelles informations deviennent perceptibles pour les autres.

### 8.3 Conversations

- Une conversation a un objectif ou un sujet initial, sans script prédéterminé.

- Les participantes peuvent changer de sujet, quitter, inviter quelqu'un ou demander de l'intimité.

- Le moteur limite les tours inutiles et clôture une conversation devenue répétitive ou inactive.

- Une conversation privée n'est pas automatiquement connue des absentes.

- Le propriétaire peut voir les conversations en direct lorsque le réglage correspondant est actif.

- Les conséquences importantes sont extraites en événements et souvenirs; le verbatim integral peut être archivé séparément.

## 9. Présence et pouvoirs du propriétaire

Le propriétaire est connu des personnages comme une entité supérieure capable d'observer, de communiquer et de modifier leur univers. Elles ne connaissent toutefois que les interventions qu'elles peuvent percevoir ou dont elles ont été informées.

### 9.1 Formes d interaction

| Mode | Ce que fait le propriétaire | Perception des personnages |

| --- | --- | --- |

| Observation | Consulte scènes, états ou historiques sans intervenir. | Aucune, sauf si une règle particuliere rend l'observation perceptible. |

| Communication | Parle à une personne ou à un groupe comme entite supérieure. | Message ou manifestation connue des destinataires. |

| Intervention de monde | Ajoute un objet, change un lieu, déclenche un événement, avance ou modifie le temps. | Percoivent les effets accessibles; l'origine depend de ce qui est manifesté. |

| Administration | Inspecte ou modifie données, traits, relations, souvenirs et règles. | Aucune connaissance automatique de l'opération interne. |

| Maintenance | Met en pause, sauvegarde, restaure ou demande un diagnostic. | Effets narratifs seulement si le propriétaire choisit de les rendre perceptibles. |

### 9.2 Principe de perceptibilite

Une intervention ne devient une connaissance du personnage que si elle peut l'observer, en subir les effets de façon identifiable, recevoir l'information d'une autre source ou être explicitement avertie par le propriétaire. Le moteur ne doit pas transformer la conscience administrative du propriétaire en omniscience collective.

### 9.3 Relation avec le propriétaire

Chaque personnage conserve une relation subjective avec le propriétaire. Elle peut ressentir confiance, affection, attirance, respect, crainte, irritation, gratitude ou ambivalence. Le fait de reconnaitre ses pouvoirs ne force ni admiration ni soumission.

## 10. Modifications administratives et confirmation

Le propriétaire peut modifier n'importe quel élément du vivarium. Les modifications portant sur un personnage ou susceptibles d'altérer fortement son histoire exigent toutefois un processus de confirmation après présentation des implications.

### 10.1 Actions pouvant être appliquées directement

- Ajouter, retirer ou déplacer un objet non critique.

- Modifier une description de lieu, une ambiance ou un paramètre de présentation.

- Activer ou désactiver un réglage d'affichage, de notification ou de visibilité.

- Mettre en pause, reprendre, sauvegarder ou demander un résumé.

- Créer un événement externe mineur dont les effets sont clairement annoncés.

### 10.2 Actions exigeant confirmation

- Modifier un trait, une valeur, une préférence, une libido, une limite ou un élément canonique.

- Modifier directement une relation ou un état emotionnel important.

- Ajouter, supprimer ou réécrire un souvenir ou une croyance.

- Forcer une décision, une attirance, une réconciliation ou une rupture.

- Autoriser un départ définitif, retirer un personnage ou restaurer un état ancien qui efface des événements.

- Changer une règle du monde dont les effets pourraient altérer plusieurs trajectoires.

### 10.3 Séquence obligatoire

1. Interpréter la demande et identifier précisément les données touchées.

1. Expliquer les effets directs, effets secondaires probables et limites d'incertitude.

1. Créer automatiquement un snapshot avant modification.

1. Présenter une demande de confirmation explicite avec possibilité d'annuler ou d'ajuster.

1. Appliquer la modification comme transaction après confirmation.

1. Journaliser la demande, l'analyse, la confirmation, le changement et son identifiant de retour arrière.

| Exemple Demande : 'Rends-la beaucoup plus extravertie.' Le système doit préciser que cela peut modifier sa fréquence de contact, ses besoins de solitude, ses habitudes et certaines relations. Il ne doit pas appliquer silencieusement un chiffre ou réécrire son passé. |

| --- |

## 11. Monde extérieur abstrait

Le monde extérieur donne aux personnages des occupations, des occasions et des pressions sans exiger la simulation détaillée d'une ville. Il est une source de contexte, pas un second vivarium complet.

### 11.1 Éléments supportes

- Travail, études, courses, loisirs, rendez-vous et déplacements.

- Lieux externes nommés mais non cartographies en détail.

- Contacts secondaires représentés par des fiches légères.

- Événements ordinaires ou exceptionnels pouvant affecter l'humeur, les projets, les ressources ou les relations.

- Possibilité de transformer plus tard un contact ou un lieu externe en entité plus détaillée.

### 11.2 Règles de condensation

| Situation | Traitement |

| --- | --- |

| Journée ordinaire | Résumé en quelques faits : activité, énergie, humeur, progression et interaction notable. |

| Incident mineur | Événement canonique bref, perception et conséquence limitée. |

| Décision personnelle importante | Appel de modèle et souvenir durable. |

| Scène pertinente pour le propriétaire | Peut être ouverte en détail sur demande ou selon une règle de notification. |

| Contact secondaire récurrent | Fiche enrichie graduellement, sans devenir automatiquement un agent complet. |

### 11.3 Départ de l'aventure

Une personne peut exprimer de la lassitude, souhaiter vivre ailleurs ou demander un changement majeur. Le moteur peut laisser émerger ces idées, mais il ne doit jamais convertir automatiquement une humeur passagère en suppression du personnage. Toute demande de départ définitif est adressée au propriétaire et reste en attente d'une décision.

## 12. Contenu relationnel, romantique et adulte

Le vivarium est un simulateur social bac à sable. Les relations romantiques, sensuelles ou sexuelles sont des possibilités parmi d'autres, et non un objectif forcé. Elles peuvent apparaître naturellement lorsque les personnages, leurs préférences, leur état et leur relation rendent la situation plausible.

### 12.1 Conditions fonctionnelles

- Tous les personnages sont explicitement adultes.

- Chaque personne possède libido, préférences, attirances, limites, dispositions et historique propres.

- L'affection, l'attirance et la libido sont distinctes et ne garantissent pas une interaction.

- Les initiatives peuvent venir du propriétaire ou des personnages.

- Une interaction peut être refusee, interrompue, reportée ou réinterprétée selon l'état et le contexte.

- Les conséquences émotionnelles et relationnelles sont traitées comme celles de toute autre scène importante.

### 12.2 Mémoire et confidentialité

Les événements adultes pertinents sont préservés dans la mémoire des participantes selon leur importance et leur interprétation. Les détails peuvent rester archives, tandis que le contexte courant utilise des résumés suffisants. Leur affichage en direct, leur niveau de détail et leur inclusion dans les résumés Discord sont configurables.

### 12.3 Absence de logique de récompense obligatoire

| Règle Le système ne doit pas traiter une interaction romantique ou adulte comme une récompense automatique, un niveau à débloquer ou la finalité commune des quatre personnages. La trajectoire de chaque relation demeure autonome. |

| --- |

## 13. Blessures et conséquences physiques

Le prototype ne gère ni vieillissement, ni maladie, ni mort, ni grossesse. Les blessures peuvent toutefois exister lorsqu'une action ou un événement les justifie.

### 13.1 Données minimales d'une blessure

- Cause et moment de l'événement.

- Zone ou type de blessure dans un vocabulaire fonctionnel, sans simulation médicale exhaustive.

- Gravité, douleur, limitations et durée estimée de récupération.

- Soins ou repos requis dans le cadre du monde.

- Perceptions, souvenirs et effets émotionnels associés.

- Effets sur les activités, l'humeur et les relations.

### 13.2 Limites

Une blessure ne doit pas être générée uniquement pour créer du drame. Le moteur doit pouvoir expliquer sa cause et ses conséquences. Le propriétaire peut modifier ou annuler une blessure, avec le protocole de confirmation si cela réécrit une expérience significative.

## 14. Interface Discord

Discord est l'interface principale de la première version. Le système peut utiliser une seule application et publier les messages des personnages sous des noms et avatars distincts, notamment au moyen de webhooks ou d'un mécanisme équivalent. Il n'est pas nécessaire de maintenir un bot separe par personnage.

### 14.1 Flux publiés

| Flux | Contenu | Réglage |

| --- | --- | --- |

| Messages personnels | Contacts spontanés, réponses et conversations avec une personne. | Activation globale et par personnage. |

| Scènes entre personnages | Conversation et actions observées en direct. | Visible, résumé ou masque; configurable. |

| Événements importants | Conflit, rapprochement, projet, blessure, départ demandé, intervention majeure. | Niveau de sévérité configurable. |

| Résumé quotidien | Activités, relations, projets, absences et faits notables. | Activation et horaire configurables. |

| Rapport de rattrapage | Ce qui a été calculé après une période hors ligne. | Publié au redémarrage selon le seuil. |

| Rapports techniques | Erreurs, reprises, diagnostic et état du technicien. | Salon administratif. |

| Alertes de coût | Usage de l'API, anomalies ou seuil atteint. | Seuil à définir plus tard. |

### 14.2 Toggles obligatoires

- Contacts spontanés : ON/OFF global et, idéalement, par personnage.

- Visibilité des conversations entre personnages : direct, résumé, masque.

- Visibilité des scènes privées : direct, résumé, masque.

- Résumé quotidien : ON/OFF et heure configurable.

- Notifications d'événements : filtre par importance.

- Détail du contenu adulte dans les flux : détaillé, résumé, non affiché.

- Rapports techniques : normal, verbeux ou erreurs seulement.

### 14.3 Identité distincte des personnages

Chaque personnage apparaît avec un nom et un avatar propres. Le moteur doit conserver l'identité technique du message afin d'éviter qu'une réplique soit attribuée au mauvais personnage. Les messages administratifs et ceux du technicien utilisent des identités séparées des habitantes.

### 14.4 Commandes fonctionnelles minimales

| Commande conceptuelle | Effet |

| --- | --- |

| Parler à <personnage ou groupe> | Ouvre ou poursuit une communication avec la cible. |

| Observer <lieu ou scène> | Affiche la situation sans intervention perceptible. |

| État du vivarium | Résumé le temps, les présences, projets et alertes. |

| Pause / Reprendre | Controle l'exécution du monde. |

| Ajouter / Modifier <élément> | Demande une intervention de monde ou administrative. |

| Confirmer / Annuler | Valide ou refuse une modification protégée. |

| Snapshot / Restaurer | Crée ou restaure un point de controle. |

| Réglages | Affiche et modifie les toggles. |

| Technicien : diagnostiquer <problème> | Demande une analyse sans modification automatique du code. |

## 15. Agent technicien du prototype

Le technicien est présent dès la première version comme assistant de diagnostic, de documentation et de recommandation. Il n'est pas un personnage du vivarium et ne possède aucun droit d'écriture automatique sur le code actif.

### 15.1 Capacités autorisées

- Lire les journaux, états, erreurs, métriques et spécifications auxquelles il est autorisé.

- Expliquer un comportement observe et distinguer fait, hypothèse et incertitude.

- Vérifier la cohérence de la base de données et des événements.

- Proposer un changement de configuration, un test ou une modification de code.

- Préparer un rapport destiné à une IA programmeuse ou à Bionic.

- Comparer le comportement avant et après une modification dans un environnement de test futur.

### 15.2 Interdictions

- Modifier le code actif, installer une dépendance ou lancer une migration sans approbation.

- Changer les souvenirs, relations ou règles pour masquer un bogue.

- Inventer une reussite de test ou déclarer une correction sans preuve.

- Contourner les sauvegardes, confirmations ou permissions.

- Prendre le controle des personnages ou intervenir dans leur monde comme acteur cache.

| Positionnement Dans le prototype, le technicien est un mécanicien qui inspecte et conseille. L'automatisation du développement viendra seulement après la mise en place d'une zone de travail séparée, de tests et d'un processus d'approbation. |

| --- |

## 16. Gestion des erreurs et états de secours

Le vivarium doit privilégier un état cohérent plutôt qu'une continuité artificielle. Une panne de modèle ou de Discord ne doit pas corrompre le monde.

| Incident | Comportement attendu |

| --- | --- |

| API indisponible | Reporter les décisions cognitives; poursuivre seulement les routines déterministes; alerter le propriétaire. |

| Réponse invalide ou non structurée | Refuser l'action, tenter une régénération limitée, puis journaliser et reporter. |

| Action impossible | Retourner la raison au personnage et lui permettre de choisir une autre intention. |

| Discord indisponible | Mettre les publications en file locale et poursuivre le monde selon la politique configuree. |

| Base verrouillée ou erreur d'écriture | Mettre la simulation en pause sûre, ne pas appliquer de transaction partielle. |

| Coût ou quota atteint | Désactiver les appels non essentiels, notifier et attendre une décision. |

| Panne du programme | Reprendre depuis le dernier état valide et clôturer les scènes interrompues. |

| Boucle répétitive | Arreter la scène ou le projet, produire un diagnostic et appliquer une période de refroidissement. |

### 16.1 Règle de reprise

Aucune action canonique ne doit être appliquée deux fois après une reprise. Chaque action possède un identifiant et une transaction. Les réponses du modèle peuvent être régénérées; les conséquences déjà validées ne sont rejouées que si l'état prouve qu'elles n'ont pas été appliquées.

## 17. Paramètres configurables du prototype

Les valeurs ci-dessous doivent pouvoir être ajustées sans modifier le code source. Les valeurs exactes seront calibrées pendant les essais et consignées dans la Partie IV ou dans la configuration du monde.

| Paramètre | Valeur initiale ou statut |

| --- | --- |

| Nombre de personnages | 4, fixe pour le MVP. |

| Vitesse du temps | Temps réel, avec rattrapage condensé. |

| Niveau d'activité | Assez actif; seuil exact à calibrer. |

| Contacts spontanés Discord | Toggle ON/OFF. |

| Visibilité inter-personnages | Direct / résumé / masque. |

| Visibilité scènes privées | Direct / résumé / masque. |

| Résumé quotidien | Toggle et heure. |

| Détail adulte Discord | Détaillé / résumé / masque. |

| Fréquence des appels de modèle | À calibrer avec limites par cycle. |

| Budget et seuils de coût | Non décidés; infrastructure d'alertes obligatoire. |

| Fournisseur et modèle | Remplaçables; choix au moment de l'implémentation. |

| Modèles locaux | Différés, mais adaptateur prévu. |

| Ordinateur dédié | Différé; aucune dépendance au PC actuel dans les données. |

## 18. Scénarios d'acceptation fonctionnelle

Les scénarios suivants décrivent ce que le prototype devra démontrer avant d'être considéré comme exploitable. Ils ne remplacent pas les tests techniques de la Partie V, mais constituent leurs critères fonctionnels.

### AF-01 - Persistance après redémarrage

| Précondition ou action | Résultat attendu |

| --- | --- |

| Les quatre personnages ont des activités, relations et souvenirs. Le programme est arrêté puis relance. | Le même monde est rechargé; les données ne sont pas réinitialisées; les conversations ouvertes sont clôturées; un résumé de rattrapage est produit. |

### AF-02 - Conversation autonome entre habitantes

| Précondition ou action | Résultat attendu |

| --- | --- |

| Deux personnages se trouvent dans le salon avec un sujet ou un besoin social pertinent. | Elles peuvent commencer une conversation sans le propriétaire; la scène est visible, resumee ou masquee selon le toggle; les conséquences restent les memes. |

### AF-03 - Perceptions différentes

| Précondition ou action | Résultat attendu |

| --- | --- |

| Un événement ambigu se produit devant deux témoins. | Le monde conserve un seul fait canonique; chaque témoin peut produire une interprétation et un souvenir différents, sans connaissance de données cachées. |

### AF-04 - Ajout d objet perceptible

| Précondition ou action | Résultat attendu |

| --- | --- |

| Le propriétaire ajoute un piano dans le salon sans annoncer son origine. | Le piano existe après sauvegarde; seules les personnes capables de le voir peuvent le découvrir; elles ne savent pas automatiquement qui l a ajouté. |

### AF-05 - Modification psychologique protégée

| Précondition ou action | Résultat attendu |

| --- | --- |

| Le propriétaire demande de rendre un personnage beaucoup plus extraverti. | Le système explique les implications, cree un snapshot et attend une confirmation. Aucun changement n'est appliqué avant confirmation. |

### AF-06 - Évolution relationnelle graduelle

| Précondition ou action | Résultat attendu |

| --- | --- |

| Deux personnages vivent plusieurs interactions positives et une dispute. | Leur relation montre des effets différenciés; la dispute ne disparaît pas après une seule réplique agréable; aucun saut arbitraire n'apparait. |

### AF-07 - Monde extérieur abstrait

| Précondition ou action | Résultat attendu |

| --- | --- |

| Une personne part travailler plusieurs heures. | Elle est absente de la résidence, revient avec un résultat condensé et quelques effets; aucune ville complète n'a été simulée. |

### AF-08 - Contact spontané toggle

| Précondition ou action | Résultat attendu |

| --- | --- |

| Un personnage a une raison plausible de contacter le propriétaire. | Avec le toggle ON, elle peut envoyer un message. Avec le toggle OFF, l'intention peut être retenue ou journalisee, mais aucun message spontané n'est envoyé. |

### AF-09 - Scène privée et visibilité

| Précondition ou action | Résultat attendu |

| --- | --- |

| Deux personnages commencent une scène privée. | Le passage entre direct, résumé et masque change uniquement la présentation au propriétaire, pas la scène ni ses conséquences. |

### AF-10 - Contenu adulte émergent

| Précondition ou action | Résultat attendu |

| --- | --- |

| Des personnages adultes disposent d'une relation, d'une disposition et d'un contexte compatibles. | Une initiative peut apparaître naturellement sans être forcee; les préférences et limites restent determinantes; la mémoire pertinente est préservée. |

### AF-11 - Panne de l'API

| Précondition ou action | Résultat attendu |

| --- | --- |

| Le fournisseur devient indisponible pendant une période active. | Le monde reste cohérent, les routines sûres peuvent continuer, les décisions cognitives sont reportées et une alerte est produite. |

### AF-12 - Rattrapage hors ligne

| Précondition ou action | Résultat attendu |

| --- | --- |

| Le vivarium est fermé pendant plusieurs heures ou jours. | Le redémarrage produit un nombre raisonnable d'événements condensés, applique les besoins et horaires, et ne lance pas un appel pour chaque minute manquée. |

### AF-13 - Demande de départ

| Précondition ou action | Résultat attendu |

| --- | --- |

| Un personnage exprime le souhait de quitter définitivement l'aventure. | La demande devient un événement majeur adressé au propriétaire. Le personnage n'est ni supprimé ni rendu inaccessible sans décision administrative. |

### AF-14 - Personnage canonique

| Précondition ou action | Résultat attendu |

| --- | --- |

| Un événement pousse un personnage canonique vers un changement contraire à un élément figé. | Le système préserve l'élément figé, cherche une réaction cohérente ou signale le conflit; il n'altère pas silencieusement le canon. |

### AF-15 - Technicien en lecture seule

| Précondition ou action | Résultat attendu |

| --- | --- |

| Le propriétaire demande au technicien de corriger un comportement. | Le technicien analyse, fournit preuves et recommandation, mais ne modifie pas le code actif ni les données pour simuler une correction. |

## 19. Décisions ouvertes non bloquantes

Les décisions suivantes ne sont pas requises pour valider le comportement général, mais devront être tranchées avant ou pendant l'implémentation. L'IA programmeuse doit proposer des valeurs par défaut plutot que forcer le propriétaire a choisir sans explication.

| Décision | Moment recommandé |

| --- | --- |

| Fournisseur API et modèle principal | Juste avant l'implémentation de la couche cognitive. |

| Budget quotidien et seuils d'alerte | Avant une simulation continue avec appels reels. |

| Fréquence exacte des cycles et appels | Pendant les tests de charge et de crédibilité. |

| Formules de besoins et vitesse de variation | Partie IV et calibration du prototype. |

| Dimensions relationnelles finales et échelles internes | Partie IV; ne pas exposer comme scores de gameplay. |

| Politique précise d oubli et de consolidation | Partie IV, avec tests long terme. |

| Noms de salons Discord et commandes exactes | Lors de l'intégration Discord. |

| Niveau de détail narratif par type de scène | Configuration utilisateur et essais. |

| Politique de file d attente lorsque Discord est hors ligne | Avant le déploiement continu. |

| Sauvegardes automatiques et rétention | Partie V, avant les tests destructifs. |

## 20. Passage aux documents suivants

La Partie III fournit maintenant une cible fonctionnelle suffisamment précise pour produire les deux documents suivants sans demander à l'IA de deviner le fonctionnement du vivarium.

| Document suivant | But |

| --- | --- |

| Partie IV - Modèle du monde et dictionnaire des données | Definir exactement les entités, champs, relations, états, événements, souvenirs, permissions et règles de versionnement. |

| Partie V - Plan de réalisation et validation | Découper le développement en phases, definir les tests, les livrables et les conditions de passage entre etapes. |

| Instruction de remise à une IA architecte Lire les Parties I, II et III dans l'ordre. Ne pas coder immediatement. Produire d'abord la liste des contradictions, inconnues et décisions techniques nécessaires. Respecter la hiérarchie des documents et proposer un plan incrémental dont chaque phase est testable et réversible. |

| --- |

## Annexe A - Matrice des toggles utilisateur

| Toggle | Options minimales | Effet sur le monde |

| --- | --- | --- |

| Contacts spontanés | ON / OFF, global et par personnage. | Aucun effet sur les intentions internes; seulement sur l'envoi vers Discord. |

| Conversations entre habitantes | Direct / Résumé / Masque. | Aucun effet sur les actions ou conséquences. |

| Scènes privées | Direct / Résumé / Masque. | Aucun effet sur la confidentialité interne. |

| Résumé quotidien | ON / OFF + horaire. | Aucun effet sur la simulation. |

| Notifications d'événements | Tous / importants / critiques. | Aucun effet sur la survenue des événements. |

| Détail adulte | Détaillé / résumé / masque. | Aucun effet sur l'existence ou la mémoire de la scène. |

| Rapports techniques | Verbeux / normal / erreurs. | Aucun effet sur les journaux internes. |

| Mode maintenance | ON / OFF. | Suspend les appels et actions selon la politique, sans effacer le temps. |

## Annexe B - Fiche fonctionnelle d'un personnage

Cette fiche ne definit pas encore le schema de données. Elle indique les categories que la Partie IV devra representer.

| Catégorie | Contenu à définir |

| --- | --- |

| Identité | Nom, version, statut adulte, origine originale ou canonique, avatar Discord. |

| Canon | Éléments figés, souples et libres; sources de référence. |

| Personnalité | Traits stables, valeurs, style de communication, forces et vulnérabilités. |

| Intérêts | Activités aimées, aversions, curiosités, compétences et habitudes. |

| Buts | Objectifs de long terme, projets actifs et priorités du moment. |

| Besoins | Faim, sommeil, hygiène, confort, sociabilité, solitude, stimulation, libido, stress. |

| Préférences relationnelles | Attirances, limites, style d'attachement, jalousie, besoin d'attention et d'indépendance. |

| Relations initiales | État envers chaque autre personnage et envers le propriétaire. |

| Mémoire initiale | Connaissances de départ, souvenirs du canon, première conscience du vivarium. |

| Évolution | Ce qui peut changer naturellement, vitesse de changement et seuils de protection. |

## Annexe C - Registre des choix valides

| ID | Choix |

| --- | --- |

| D-III-01 | Le premier prototype contient quatre personnages adultes. |

| D-III-02 | La résidence détaillée comprend salon, cuisine, quatre chambres, salle de bain et cour. |

| D-III-03 | Le temps suit le temps réel et le système fonctionne continuellement lorsque l'application tourne. |

| D-III-04 | La période hors ligne est calculee de facon condensée au redémarrage. |

| D-III-05 | Les personnages sont assez actives et disposent d'une autonomie complète dans le vivarium. |

| D-III-06 | Elles peuvent sortir de la résidence, mais aucun départ définitif ne se produit sans discussion et décision du propriétaire. |

| D-III-07 | Le propriétaire est connu comme entite supérieure. |

| D-III-08 | Tout est administrativement modifiable; les changements portant sur les personnages exigent analyse, snapshot et confirmation. |

| D-III-09 | Une intervention n'est connue des personnages que si elle est perceptible ou communiquée. |

| D-III-10 | Le monde extérieur reste abstrait dans le prototype. |

| D-III-11 | Les besoins sont assez détaillés; les valeurs numériques restent cachées en usage normal. |

| D-III-12 | Les personnages peuvent évoluer; les personnages canoniques utilisent des zones figees, souples et libres. |

| D-III-13 | La mémoire inclut oubli naturel, préservation durable et inspection ou modification administrative. |

| D-III-14 | Le contenu adulte peut emerger naturellement et les événements pertinents sont préservés. |

| D-III-15 | Discord publie messages, scènes, événements, résumés, rapports techniques et alertes; plusieurs flux sont togglables. |

| D-III-16 | Chaque personnage dispose d'une apparence Discord distincte, sans exiger un bot complet par personnage. |

| D-III-17 | Le fonctionnement ne se réduit pas automatiquement pendant l'usage normal du PC. |

| D-III-18 | Le technicien est présent comme assistant de diagnostic sans modification automatique du code. |

| D-III-19 | L'architecture doit permettre plus tard un ordinateur dédié et des modèles locaux. |

| D-III-20 | Le prototype exclut vieillissement, maladie, mort et grossesse; les blessures sont possibles. |

| D-III-21 | Les personnages savent que le propriétaire est une entité supérieure. |

| D-III-22 | Les scènes privées peuvent être visibles en direct, résumées ou masquees. |

| D-III-23 | Les conversations interrompues sont clôturées automatiquement plutot que reprises au milieu. |

| D-III-24 | Le budget API initial reste à définir. |

## Fin de la Partie III

Cette version 0.1 fixe le comportement attendu du premier vivarium exploitable. Toute modification importante de ces choix doit être inscrite au registre de décisions et répercutée dans les Parties IV et V avant d'être remise à une IA programmeuse.