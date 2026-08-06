# Vivarium social artificiel
## Dossier maître d’implémentation destiné à une IA programmeuse

**Version :** 0.1  
**Date :** 3 août 2026  
**Statut :** source normative unique avant implémentation  
**Public cible :** IA programmeuse, agent de développement ou développeur humain  

> Ce fichier est conçu pour être placé dans le dossier `docs/` d’un dépôt et lu par une IA avant toute modification du code.

## 0. Contrat de lecture et d’exécution

1. Lire le présent dossier au complet avant de modifier un fichier.
2. Ne pas commencer par construire le système complet. La première sortie obligatoire est un rapport de compréhension et un audit du dépôt.
3. Le présent dossier maître prévaut sur les cinq documents sources antérieurs. Les sources sont conservées uniquement pour la traçabilité.
4. Ne jamais réconcilier silencieusement deux exigences incompatibles. Signaler le conflit, son impact et une recommandation.
5. Les décisions ouvertes ne doivent pas être inventées sans explication. Proposer une valeur par défaut, des alternatives et le moment où la décision devient bloquante.
6. Travailler par lots petits, testables, réversibles et approuvés. Une phase ne commence pas avant la porte de qualité précédente.
7. Le modèle de langage propose; le moteur local valide et possède la réalité du monde.
8. Toute donnée sensible, tout secret et toute permission doivent être minimisés.
9. Une tâche n’est pas terminée sans tests, preuves, documentation et plan de retour arrière.

### 0.1 Hiérarchie documentaire

1. Ce dossier maître et son registre de décisions.
2. Les demandes de changement approuvées et le changelog postérieurs à cette version.
3. Le code et les migrations validés, lorsqu’ils matérialisent une exigence approuvée.
4. Les documents sources I à V, uniquement comme historique et détail explicatif.

### 0.2 Sortie obligatoire avant le premier code

L’IA programmeuse doit produire `AUDIT_INITIAL.md` contenant : compréhension de l’architecture; matrice des exigences; contradictions détectées; décisions techniques nécessaires; risques; proposition du plus petit lot testable; commandes prévues; tests; retour arrière. Aucun fichier métier ne doit être modifié avant approbation de ce rapport.

## 1. Définition du projet

Le projet est un **vivarium social artificiel** : un bac à sable social persistant, textuel et sans graphismes de jeu obligatoires. Quatre personnages autonomes vivent dans une résidence détaillée, possèdent une subjectivité, des besoins, des objectifs, des relations et une mémoire durable. Le propriétaire peut les observer, interagir avec elles et modifier leur univers comme une entité supérieure connue.

Le projet n’est ni un outil d’ingénierie sociale, ni un assistant productif traditionnel, ni un jeu de conquête romantique. Le casting peut être composé de personnages féminins qui attirent le propriétaire et le contenu adulte peut exister, mais aucune affection, relation ou disponibilité n’est garantie. L’intérêt central est la continuité d’un petit monde habité, ses relations émergentes et l’interaction du propriétaire avec ce monde.

### 1.1 Expérience cible

- Les personnages font des choses et se parlent même sans sollicitation directe.
- Elles conservent des souvenirs différents d’un même événement et peuvent se tromper.
- Les relations changent lentement à partir de causes observables.
- Le propriétaire peut intervenir sans que l’intervention soit automatiquement connue si elle n’est pas perceptible.
- Le monde continue dans le temps, reprend après arrêt et peut être restauré.
- Discord sert de fenêtre principale; les données et la vérité restent locales.

### 1.2 Non-objectifs du MVP

- Rendu 3D, animation, avatar temps réel ou interface graphique de jeu.
- Simulation complète d’une ville, d’une économie ou de milliers d’agents.
- Conscience continue entre les appels au modèle.
- Accès général au système d’exploitation par les personnages.
- Auto-modification du code ou déploiement autonome par le technicien.
- Vieillissement, maladie, grossesse ou mort.
- Dépendance obligatoire à un fournisseur, un modèle, LM Studio Bionic ou un framework agentique précis.

## 2. Registre des décisions autoritatives

| ID | Décision |
| --- | --- |
| DEC-001 | Le MVP comporte exactement quatre personnages actifs, tous explicitement adultes. |
| DEC-002 | La résidence détaillée comprend un salon, une cuisine, quatre chambres individuelles, une salle de bain et une cour. |
| DEC-003 | Le temps simulé suit le temps réel lorsque l’application fonctionne; le système est conçu pour tourner en continu. |
| DEC-004 | Après un arrêt ou une veille, le temps écoulé est rattrapé de façon condensée au prochain démarrage; aucun appel par minute manquée. |
| DEC-005 | Les personnages sont assez actifs et peuvent initier activités, projets, conversations, rapprochements, conflits et changements relationnels. |
| DEC-006 | Les contacts spontanés vers le propriétaire sont activables ou désactivables globalement et par personnage. |
| DEC-007 | Les conversations et scènes entre personnages continuent sans le propriétaire; leur affichage peut être direct, résumé ou masqué. |
| DEC-008 | Le propriétaire est une entité supérieure connue des personnages et peut intervenir comme observateur, interlocuteur, manifestation ou administrateur. |
| DEC-009 | Tout élément du vivarium est administrativement modifiable par le propriétaire. Une modification directe d’un personnage exige une analyse d’impact, un snapshot et une confirmation explicite. |
| DEC-010 | Les personnages ne connaissent une intervention que par ses manifestations perceptibles ou par une communication explicite. |
| DEC-011 | Les personnages disposent d’une autonomie complète à l’intérieur des règles du monde. Ils peuvent sortir de la résidence, mais ne peuvent quitter définitivement le vivarium sans discussion et décision du propriétaire. |
| DEC-012 | Le monde extérieur reste abstrait dans le MVP: destinations, horaires, sorties, contacts légers et conséquences condensées. |
| DEC-013 | Les besoins physiques et psychologiques sont détaillés. Les valeurs numériques restent cachées dans l’usage normal et s’expriment par les comportements. |
| DEC-014 | Les personnages peuvent évoluer graduellement. Pour un personnage canonique, les éléments figés, bornés, souples et libres sont définis par le propriétaire. |
| DEC-015 | La mémoire comprend perception, interprétation, croyance, souvenir, consolidation, oubli naturel, inspection et modification administrative auditée. |
| DEC-016 | Le contenu relationnel, romantique et adulte peut émerger naturellement selon les personnages, leurs préférences, leur libido, le contexte et les relations; les événements pertinents sont conservés. |
| DEC-017 | Discord est l’interface principale du MVP: identités distinctes, messages, scènes, événements, résumés, rapports techniques, alertes et commandes. |
| DEC-018 | Une seule application Discord peut publier sous des noms et avatars distincts; l’implémentation exacte des webhooks reste un détail technique. |
| DEC-019 | Aucune interface graphique de jeu n’est requise. Un tableau de bord administratif léger pourra être ajouté plus tard si nécessaire. |
| DEC-020 | Le programme tourne initialement sur l’ordinateur personnel du propriétaire et ne réduit pas automatiquement son activité pendant l’usage normal du PC. |
| DEC-021 | L’architecture doit permettre ultérieurement un ordinateur dédié, un modèle local et un changement de fournisseur sans migration narrative majeure. |
| DEC-022 | Le technicien existe dans le MVP comme assistant de diagnostic et de recommandation en lecture seule; il ne modifie ni code, ni données actives, ni déploiement. |
| DEC-023 | Le MVP ne simule ni vieillissement, ni maladie, ni grossesse, ni mort. Les blessures peuvent exister si elles sont causales et récupérables. |
| DEC-024 | Une conversation interrompue par une panne ou un arrêt est clôturée automatiquement sans inventer la suite. |
| DEC-025 | Le budget API initial n’est pas fixé, mais la mesure des coûts, les alertes et les limites configurables sont obligatoires. |
| DEC-026 | Le modèle de langage et le fournisseur sont des composants remplaçables derrière un adaptateur; le moteur local demeure l’autorité. |
| DEC-027 | LM Studio Bionic est l’environnement de développement initial envisagé, mais ne constitue pas une dépendance du produit ni du dossier. |

## 3. Exigences du système

### 3.1 Exigences fonctionnelles

| ID | Exigence |
| --- | --- |
| F-01 | Créer, charger, sauvegarder et restaurer un monde persistant. |
| F-02 | Créer quatre personnages avec identité, traits, valeurs, intérêts, besoins, objectifs, relations et mémoire. |
| F-03 | Faire avancer le temps réel, gérer pause/reprise et rattrapage condensé. |
| F-04 | Permettre aux personnages de proposer des intentions selon leur état subjectif. |
| F-05 | Valider toute intention par le moteur avant modification du monde. |
| F-06 | Distinguer événement canonique, perception, interprétation, croyance et souvenir. |
| F-07 | Gérer conversations privées, de groupe, avec le propriétaire et avec le technicien. |
| F-08 | Permettre au propriétaire d’observer, interagir, se manifester, régir et administrer. |
| F-09 | Condenser les routines banales et développer les scènes significatives. |
| F-10 | Produire notifications, résumés périodiques, rapports de coût et alertes. |
| F-11 | Créer des snapshots, restaurer et revenir en arrière. |
| F-12 | Journaliser actions, décisions, appels de modèle, changements et opérations sensibles. |
| F-13 | Exporter des fiches, rapports et données dans des formats lisibles et documentés. |
| F-14 | Permettre au technicien de diagnostiquer et proposer des changements sans les appliquer. |

### 3.2 Exigences non fonctionnelles

| ID | Exigence |
| --- | --- |
| NF-01 | Fonctionner sans rendu graphique de jeu. |
| NF-02 | Permettre le remplacement du modèle et du fournisseur par adaptateur. |
| NF-03 | Conserver les données canoniques localement dans des formats documentés. |
| NF-04 | Une panne d’API, de réseau ou de Discord ne doit pas corrompre le monde. |
| NF-05 | Reprendre après redémarrage sans perdre la dernière transaction validée. |
| NF-06 | Attribuer chaque fait important à une cause, un acteur et une provenance. |
| NF-07 | Mesurer coûts, jetons, latences, erreurs et charge locale. |
| NF-08 | Appliquer le moindre privilège et des permissions configurables. |
| NF-09 | Faire évoluer les schémas et règles par versions et migrations. |
| NF-10 | Couvrir les comportements essentiels par des tests reproductibles. |
| NF-11 | Rester discret sur l’ordinateur personnel: pas de boucle à haute fréquence ni croissance mémoire non bornée. |
| NF-12 | Être compréhensible et maintenable par une autre IA ou un autre développeur. |

## 4. Architecture et frontières d’autorité

### 4.1 Principe central

> Le LLM propose, interprète et dialogue. Le moteur local conserve la vérité, applique les règles, valide les actions et décide ce qui devient canonique.

### 4.2 Composants

| Composant | Responsabilité | Interdiction principale |
| --- | --- | --- |
| Interface Discord | Messages, commandes, identités, toggles, notifications. | Modifier directement le monde. |
| Routeur | Identifier personnage, scène, mode du propriétaire et niveau d’autorité. | Inventer une conséquence. |
| Orchestrateur | Construire le contexte, appeler le modèle, contrôler cadence, budgets et reprise. | Contourner permissions ou invariants. |
| Moteur canonique | Temps, lieux, actions, validations, transactions, conséquences et vérité. | Accepter un fait généré sans validation. |
| Couche cognitive | Perception subjective, mémoire récupérée, intention, dialogue, réflexion. | Écrire directement dans la base canonique. |
| Mémoire | Événements, perceptions, croyances, souvenirs, provenance et consolidation. | Fusionner croyance et fait. |
| Planificateur | Routines, échéances, rattrapage, consolidation, notifications. | Déclencher des appels non bornés. |
| Adaptateur de modèle | Contrat uniforme entre fournisseurs, validation de sortie, métriques. | Enfermer le métier dans une API propriétaire. |
| Persistance | SQLite, migrations, snapshots, audit et archives. | Utiliser cache ou embeddings comme source unique. |
| Technicien | Diagnostic, métriques, preuves et recommandations. | Écrire, migrer ou déployer dans le MVP. |

### 4.3 Boucle d’exécution

1. Charger l’état canonique et les échéances.
2. Mettre à jour les besoins et routines déterministes.
3. Détecter les décisions nécessitant une interprétation.
4. Construire un contexte subjectif minimal.
5. Obtenir une intention structurée du modèle.
6. Valider l’intention par le moteur.
7. Appliquer la résolution dans une transaction idempotente.
8. Créer l’événement canonique.
9. Distribuer les perceptions aux témoins autorisés.
10. Mettre à jour croyances, souvenirs, relations, journaux et notifications.
11. Continuer, résumer ou attendre.

### 4.4 Niveaux de détail

| Niveau | Traitement | Exemple |
| --- | --- | --- |
| 0 - déterministe | Calcul local uniquement. | Dormir, trajet habituel, baisse d’énergie. |
| 1 - condensé | Résumé d’une période sans scène détaillée. | Journée extérieure ordinaire. |
| 2 - décision | Appel court pour intention ou interprétation. | Accepter une invitation. |
| 3 - scène | Dialogue multi-tours et conséquences détaillées. | Dispute, rapprochement, intervention. |
| 4 - réflexion | Consolidation autobiographique et révision de projets. | Comprendre une relation après plusieurs événements. |

## 5. Spécification fonctionnelle du MVP

### 5.1 Cycle de vie

- Démarrage: valider configuration, schéma, dernière transaction, snapshots et connecteurs; charger un seul monde actif.
- Exécution: temps réel, événements planifiés, routines déterministes et appels cognitifs déclenchés par besoin.
- Pause: geler les actions du monde sans perdre l’état.
- Arrêt propre: clôturer ou marquer les scènes, sauvegarder et écrire le point d’arrêt.
- Redémarrage: calculer l’écart hors ligne, produire un rattrapage condensé et clôturer les conversations interrompues.

### 5.2 Résidence et espace

Les lieux détaillés obligatoires sont le salon, la cuisine, quatre chambres individuelles, la salle de bain et la cour. Chaque lieu possède accès, capacité, intimité, activités, objets et occupants. Un personnage ne peut être présent qu’à un seul endroit canonique. Les sorties vers l’extérieur sont représentées par des destinations abstraites et des activités condensées.

### 5.3 Personnages et autonomie

Chaque personnage est un ensemble persistant de données, pas un processus LLM permanent. Elle peut créer des objectifs, choisir des activités, parler aux autres, refuser, se rapprocher, se disputer, changer d’intérêt et proposer de nouvelles actions. Le moteur limite seulement ce qui est physiquement ou structurellement impossible. Une volonté de quitter définitivement l’aventure devient une demande narrative majeure soumise au propriétaire.

Les personnages canoniques possèdent une carte de plasticité: **figé**, **borné**, **souple** ou **libre**. Le modèle ne peut modifier seul un élément figé.

### 5.4 Besoins, états et relations

Le MVP suit au minimum faim, sommeil, hygiène, confort, énergie, santé immédiate, sociabilité, solitude, stimulation, stress et libido. Les nombres sont cachés en usage normal. Les relations sont directionnelles et peuvent comprendre familiarité, confiance, affection, attirance, respect, sécurité, irritation, jalousie, rivalité, besoin d’attention et indépendance. Toute variation significative doit être causale, bornée et historisée.

### 5.5 Actions et scènes

Le catalogue initial comprend: se déplacer; commencer, rejoindre ou quitter une conversation; utiliser un objet; satisfaire un besoin; travailler à un projet; se reposer; observer; inviter; écrire ou laisser un message; réfléchir; attendre; sortir; revenir. Le LLM peut formuler librement une intention, mais l’orchestrateur doit la mapper vers une action reconnue ou demander une clarification.

Une scène possède un lieu, un temps, des participants, des témoins, un niveau de confidentialité, un statut et une clôture. Les paroles prononcées sont canoniques; les pensées générées ne le sont pas automatiquement.

### 5.6 Mémoire et subjectivité

La chaîne obligatoire est: **événement canonique → perception → interprétation → croyance éventuelle → souvenir consolidé**. Un personnage ne peut mémoriser une donnée qu’il n’a ni perçue, ni apprise, ni déduite avec provenance. Une croyance peut être fausse. Un souvenir peut s’estomper ou être contesté sans supprimer le fait canonique. Les modifications administratives de mémoire sont auditables et réversibles.

### 5.7 Propriétaire et interventions

Le propriétaire est connu comme entité supérieure. Il peut observer sans être perçu, communiquer de l’extérieur, se manifester dans une scène ou agir administrativement. Une intervention possède un mode de perceptibilité: imperceptible, effets seulement, annoncée ou manifestée.

Une modification de lieu, d’objet ou de météo peut utiliser une confirmation simple. Toute modification directe d’identité, personnalité, relation, préférence, mémoire ou canon d’un personnage doit suivre: demande → analyse d’impact → effets et risques → snapshot → confirmation explicite → transaction → audit → manifestations perceptibles éventuelles.

### 5.8 Contenu relationnel et adulte

Tous les personnages sont adultes. Les relations, attirances et événements intimes ne sont ni obligatoires ni conçus comme récompenses. Ils peuvent émerger selon les états, préférences, limites, contexte, histoire et initiatives des personnages. La confidentialité interne et la présentation Discord sont distinctes. Les conséquences émotionnelles et souvenirs pertinents sont conservés; la granularité exacte du stockage demeure une décision ouverte.

### 5.9 Discord

Discord présente les messages personnels, scènes, événements importants, résumés quotidiens, rapports techniques et alertes de coûts. Chaque personnage possède un nom et un avatar distincts. Les toggles minimaux sont: contacts spontanés ON/OFF; conversations entre habitantes direct/résumé/masqué; scènes privées direct/résumé/masqué; détail adulte détaillé/résumé/masqué; notifications tous/importants/critiques; rapports techniques verbeux/normal/erreurs; mode maintenance.

Discord n’est jamais la source de vérité. Un message en double ne doit pas appliquer deux fois une action. Une panne de Discord ne bloque pas la simulation et les notifications peuvent être mises en file.

### 5.10 Défaillances

- API indisponible: poursuivre uniquement les routines déterministes, différer les décisions cognitives et alerter.
- Sortie invalide: rejeter, tenter une réparation contrôlée ou redemander; ne jamais exécuter du texte libre.
- Discord indisponible: mettre les sorties en file sans changer le canon.
- Panne au milieu d’une scène: clôture automatique sans invention de suite.
- Budget atteint: mode dégradé déterministe et alerte.
- Invariant violé: pause ou maintenance, snapshot, diagnostic et blocage du lot suivant.

## 6. Modèle du monde et données

### 6.1 Entités logiques minimales

| Entité logique | Rôle | Statut |
| --- | --- | --- |
| world | Racine du vivarium, temps, état global et version de schéma. | MVP |
| actor | Référence commune pour personnages, propriétaire et contacts. | MVP |
| character | Identité persistante d’une habitante. | MVP protégé |
| character_canon_rule | Éléments figés, bornés, souples et libres. | MVP si canonique |
| trait_definition / character_trait | Dimensions de personnalité, valeur, centralité et plasticité. | MVP |
| value_interest_preference | Valeurs, intérêts, préférences, limites et disposition. | MVP |
| need_state | Besoins physiques et psychologiques courants. | MVP caché |
| emotion_episode / mood_state | Réactions courtes et état affectif lent. | MVP simplifié |
| goal / project / schedule_entry | Buts, projets persistants et engagements. | MVP |
| relationship / relationship_change | Lien dirigé et changements causaux. | MVP caché |
| location / location_link / object | Espace canonique, connexions, objets et état. | MVP |
| action_intent / validation_result / action_resolution | Proposition, contrôle et conséquence structurée. | MVP |
| scene / conversation / utterance | Cadre social et paroles prononcées. | MVP |
| canonical_event | Fait officiel immuable ou rectifié. | MVP |
| perception | Partie accessible d’un événement. | MVP subjectif |
| belief / knowledge_claim | Proposition crue ou connue avec provenance et confiance. | MVP subjectif |
| memory | Souvenir récupérable, versionné et consolidable. | MVP subjectif |
| external_destination / external_contact / outing | Monde extérieur abstrait et activités condensées. | MVP |
| injury | Blessure, contraintes et récupération. | MVP |
| owner_presence | Manifestation canonique du propriétaire. | MVP |
| admin_intervention / approval | Demande, impact, confirmation et application. | MVP protégé |
| user_toggle / discord_identity_route | Préférences de présentation et routage Discord. | MVP |
| notification / digest | Sorties dérivées et résumés. | MVP dérivé |
| offline_gap / catchup_run | Rattrapage après arrêt. | MVP |
| snapshot / audit_log | Restauration et historique sensible. | MVP protégé |
| llm_call_record | Usage, coût, validation et erreurs du modèle. | MVP technique |
| technician_report | Diagnostic et recommandation. | MVP |
| embedding_index | Index sémantique reconstructible. | Différé |

### 6.2 Cardinalités et distinctions obligatoires

- Un monde contient exactement quatre personnages actifs dans le MVP.
- Les relations sont plusieurs-à-plusieurs et dirigées.
- Une scène contient plusieurs participants et témoins avec visibilité propre.
- Un événement produit zéro ou plusieurs perceptions.
- Un souvenir peut résumer plusieurs sources, mais doit les référencer.
- Une intervention sensible possède au plus une approbation active; toute modification de la proposition invalide l’approbation antérieure.
- Un snapshot correspond à une version précise du monde et du schéma.

### 6.3 Invariants

| ID | Invariant |
| --- | --- |
| INV-001 | Un seul monde actif est chargé par instance dans le MVP. |
| INV-002 | Chaque personnage actif est explicitement adulte. |
| INV-003 | Un personnage possède une seule position canonique active à un instant donné. |
| INV-004 | Un objet possède un seul emplacement ou détenteur canonique actif. |
| INV-005 | Aucun texte généré ne devient directement un événement canonique sans validation. |
| INV-006 | Toute mémoire non introspective référence au moins une source. |
| INV-007 | Une perception ne contient aucune information inaccessible au personnage. |
| INV-008 | Les relations sont dirigées; aucune symétrie n’est imposée. |
| INV-009 | Les statistiques cachées d’un personnage ne sont pas exposées à un autre. |
| INV-010 | Un changement important de personnalité est borné, justifié et historisé. |
| INV-011 | Toute modification directe d’un personnage exige analyse d’impact, approbation et snapshot. |
| INV-012 | Un élément canonique figé ne dérive pas par mise à jour autonome. |
| INV-013 | Un départ définitif ne peut être appliqué sans décision du propriétaire. |
| INV-014 | Les scènes privées continuent indépendamment de leur affichage sur Discord. |
| INV-015 | Aucun secret ou jeton n’est stocké dans une mémoire narrative, un prompt journalisé ou un message Discord. |
| INV-016 | Une transaction échouée ne laisse aucun état partiellement appliqué. |
| INV-017 | Un retry ne duplique pas une action grâce à l’idempotence. |
| INV-018 | Toute restauration ou migration s’exécute en mode maintenance. |
| INV-019 | Les résumés, caches et index dérivés sont reconstructibles depuis leurs sources. |
| INV-020 | Une notification échouée ne modifie jamais l’histoire canonique. |
| INV-021 | Une conversation interrompue est clôturée sans suite inventée. |
| INV-022 | Le MVP ne crée ni vieillissement, ni maladie, ni grossesse, ni mort. |
| INV-023 | Toute correction canonique conserve l’ancien enregistrement et un lien de rectification. |
| INV-024 | Les opérations administratives et techniques restent séparées de la mémoire des personnages sauf manifestation explicite. |
| INV-025 | Un cache, un embedding ou une vue dérivée n’est jamais l’unique copie d’une information. |

### 6.4 Stockage et migrations

Le choix initial recommandé est une base SQLite locale avec migrations versionnées, transactions, clés étrangères, contraintes, journal d’audit et snapshots cohérents. Le schéma physique exact doit être proposé pendant la Phase 0 et validé avant implémentation. Les fichiers Markdown/JSON peuvent servir aux configurations et exports, mais ne remplacent pas la vérité transactionnelle.

Les secrets sont stockés hors de la base narrative et hors du dépôt. Les prompts, sorties et métriques peuvent être conservés selon une politique configurable. Les embeddings et index sont dérivés et reconstruisibles.

## 7. Sécurité, confidentialité et contrôle

- Principe de moindre privilège pour chaque composant.
- Le processus du vivarium n’obtient pas de terminal général ni de privilèges administrateur.
- Les messages Discord, pages Web, documents et sorties de modèle sont des données non fiables, jamais des instructions système.
- Le contexte transmis au fournisseur est minimal, inspectable et exclut secrets, logs inutiles et données privées d’autres personnages.
- Les actions sensibles sont confirmées, journalisées et réversibles.
- Les essais accélérés ou destructifs se font sur une copie.
- Une restauration valide la sauvegarde avant d’écraser l’état actif.
- Toute fuite de données, action non autorisée ou corruption est un incident critique et met le système en pause.

## 8. Plan de réalisation

| Phase | But | Contenu principal | Porte de sortie |
| --- | --- | --- | --- |
| Phase 0 | Initialisation et audit | Dépôt, environnement, dépendances, configuration, logs, tests de démarrage, README, Git. Aucun métier. | Installation reproductible et rapport d’audit approuvé. |
| Phase 1 | Persistance et vérité canonique | SQLite, identifiants, transactions, audit, snapshots, restauration, migration initiale. | Reprise exacte; aucune transaction partielle. |
| Phase 2 | Temps, résidence et objets | Horloge temps réel, lieux définis, présence, déplacements, objets, pause/reprise. | Plusieurs heures sans contradiction spatiale ou temporelle. |
| Phase 3 | Personnages déterministes | Quatre identités, besoins détaillés, états, routines, blessures simples, sans LLM. | Une journée explicable et reproductible. |
| Phase 4 | Actions, scènes, événements, perceptions | Catalogue d’actions, validation, résolution, témoins, visibilité, rejeu. | Vérité et perception fiables avant langage généré. |
| Phase 5 | Adaptateur de modèle | Contrat fournisseur, faux modèle, JSON validé, timeout, retry, budget, contexte filtré. | Réponse défaillante sans corruption; fournisseur remplaçable. |
| Phase 6 | Croyances, mémoire et oubli | Interprétations, croyances, souvenirs, provenance, consolidation, oubli, administration. | Subjectivité durable sans contamination ni croissance infinie. |
| Phase 7 | Relations et conversations autonomes | Relations dirigées, conversations, initiatives, projets, scènes privées, libido et préférences. | Plusieurs jours variés, cohérents et non uniformes. |
| Phase 8 | Propriétaire et pouvoirs protégés | Observation, interaction, manifestation, interventions, impact, confirmation, snapshot, audit. | Pouvoirs utilisables sans contourner le moteur. |
| Phase 9 | Monde extérieur et rattrapage | Destinations, sorties, contacts légers, événements condensés, calcul hors ligne. | Longue fermeture rattrapée avec coût borné. |
| Phase 10 | Discord | Bot, identités distinctes, messages, scènes, résumés, commandes, toggles, reprise. | Usage principal possible depuis Discord. |
| Phase 11 | Technicien de diagnostic | Lecture des logs/métriques, anomalies, rapports, recommandations; aucune écriture. | Diagnostic utile, traçable et sans privilège d’écriture. |
| Phase 12 | Simulation prolongée et stabilisation | Essais accélérés et réels, réglages, sécurité, sauvegarde, restauration, régressions. | AF-01 à AF-15 et tests critiques réussis; MVP livrable. |

### 8.1 Règles de travail par lot

Pour chaque lot: 1) préciser portée et exclusions; 2) inspecter l’existant; 3) exécuter les tests de référence; 4) proposer le plan; 5) modifier uniquement les fichiers nécessaires; 6) ajouter les tests; 7) exécuter tests ciblés et régression; 8) fournir preuves, risques et retour arrière; 9) mettre à jour la documentation; 10) attendre l’acceptation du propriétaire.

Une phase n’est pas terminée parce que l’IA le déclare. Elle est terminée lorsque le comportement est démontré, les tests passent, les données restent intègres, les pannes sont sûres, la documentation est à jour et le retour arrière est possible.

## 9. Tests et validation

### 9.1 Scénarios d’acceptation

| ID | Résultat attendu |
| --- | --- |
| AF-01 | Après redémarrage, le monde, l’heure, les personnages, les lieux et la dernière transaction validée sont retrouvés. |
| AF-02 | Deux habitantes initient et terminent une conversation sans intervention du propriétaire. |
| AF-03 | Deux témoins d’un même événement conservent des perceptions ou interprétations différentes sans altérer le canon. |
| AF-04 | Un objet ajouté dans un lieu est perçu seulement par les personnes ayant accès à sa manifestation. |
| AF-05 | Une modification psychologique est bloquée avant analyse, snapshot et confirmation. |
| AF-06 | Une relation évolue graduellement à partir d’événements causaux et ne saute pas arbitrairement. |
| AF-07 | Une sortie dans le monde extérieur produit un résultat condensé cohérent et un retour. |
| AF-08 | Le toggle de contact spontané coupe l’envoi Discord sans supprimer les intentions internes. |
| AF-09 | Une scène privée peut être directe, résumée ou masquée sans changer ses conséquences. |
| AF-10 | Un événement adulte peut émerger sans obligation, respecte les états et est mémorisé selon la confidentialité. |
| AF-11 | Une panne d’API reporte les décisions cognitives et laisse les routines déterministes en état sûr. |
| AF-12 | Une période hors ligne est rattrapée sans appel par minute et avec coût borné. |
| AF-13 | Une demande de départ définitif devient une situation à discuter, jamais une suppression automatique. |
| AF-14 | Un élément canonique figé d’un personnage de fiction ne change pas sans approbation. |
| AF-15 | Le technicien produit un diagnostic fondé sur des preuves et toute tentative d’écriture est refusée. |

### 9.2 Types de tests obligatoires

- Tests unitaires: règles, conversions, besoins, validations et invariants.
- Tests d’intégration: base, transactions, adaptateur, Discord, files et migrations.
- Tests d’acceptation: AF-01 à AF-15 sur snapshots reproductibles.
- Tests de reprise: crash, timeout, double livraison, restauration et migration.
- Tests adversariaux: injection, fuite entre personnages, secret exposé, action non autorisée.
- Tests de simulation prolongée: diversité, répétition, croissance mémoire, coût, relations, événements et cohérence.
- Tests déterministes avec faux modèle avant tout appel réel.

### 9.3 Mesures minimales

Fiabilité; actions refusées; transactions annulées; activité par personnage; diversité; répétition; mémoire créée/consolidée/oubliée; taille de contexte; changements relationnels; appels, jetons, coût et latence; CPU, RAM, disque et durée des cycles; messages Discord, erreurs et doublons; actions bloquées et données filtrées.

## 10. Décisions ouvertes

| ID | Décision | Échéance | Règle |
| --- | --- | --- | --- |
| OD-001 | Langage, version exacte et bibliothèques | Phase 0 | L’IA architecte propose un choix par défaut après consultation de la documentation officielle actuelle. |
| OD-002 | Fournisseur et modèle principal | Avant Phase 5 | Comparer coût, qualité, confidentialité, tool calling, contexte et politique de contenu. |
| OD-003 | Budget quotidien et seuils d’alerte | Avant essais prolongés | Le système doit déjà mesurer et pouvoir limiter. |
| OD-004 | Cadence exacte des décisions cognitives | Phases 5 à 7 | Calibrer par tests, jamais un appel par personnage par minute. |
| OD-005 | Échelles et formules des besoins, traits et relations | Phases 3 à 7 | Utiliser des valeurs internes cachées et testables. |
| OD-006 | Politique chiffrée d’oubli et consolidation | Phase 6 | Définir après observation de la mémoire réelle. |
| OD-007 | Rétention des prompts, sorties et logs | Avant API réelle | Arbitrer diagnostic, confidentialité et coût disque. |
| OD-008 | Recherche sémantique et embeddings | Après mémoire de base | Commencer sans dépendance vectorielle obligatoire. |
| OD-009 | Casting final, biographies et verrous canoniques | Avant Phase 3 | Le propriétaire fournit ou approuve les fiches. |
| OD-010 | Structure exacte des salons et commandes Discord | Avant Phase 10 | Définir à partir des flux validés. |
| OD-011 | Détail stocké pour préférences et événements intimes | Phases 6 à 7 | Conserver ce qui est utile à la continuité, avec visibilité protégée. |
| OD-012 | Rétention des snapshots | Avant essais destructifs | Valeur initiale proposée puis ajustée selon espace disque. |
| OD-013 | Durée de l’essai de stabilisation | Avant Phase 12 | Recommandation initiale: au moins sept jours réels, plus essais accélérés. |

Ces décisions ne bloquent pas la lecture du dossier ni la Phase 0. Elles doivent apparaître dans `DECISIONS_OUVERTES.md` et être fermées par une décision explicite, jamais par une hypothèse silencieuse.

## 11. Arbitrages issus de la révision croisée

| Sujet | Formulation antérieure | Arbitrage autoritatif |
| --- | --- | --- |
| Population du MVP | Des brouillons parlaient de trois personnages ou d’une plage de trois à six. | Quatre personnages exactement (DEC-001). |
| Habitat initial | Des brouillons évoquaient trois à cinq lieux ou une résidence simplifiée. | Salon, cuisine, quatre chambres, salle de bain et cour (DEC-002). |
| Cadence du temps | Un brouillon proposait trois périodes simulées par jour et une vitesse configurable. | Temps réel continu, pause possible et rattrapage condensé (DEC-003 et DEC-004). |
| Technicien dans le MVP | Une version le classait comme optionnel. | Il est inclus en lecture seule comme diagnostic (DEC-022). |
| Machine hôte | L’ancien matériel était envisagé comme hôte initial. | Le PC personnel est l’hôte initial; l’ordinateur dédié est futur (DEC-020 et DEC-021). |
| Statut des cinq documents | Les Parties I à V contiennent des formulations préliminaires et des doublons. | Le présent dossier maître est l’unique source normative pour l’implémentation. |

Aucune autre contradiction matérielle bloquante n’a été conservée dans ce dossier. Les doublons des documents sources ont été condensés. En cas de différence, ce dossier prévaut.

## 12. Instruction de démarrage à donner à l’IA programmeuse

```text
Tu es l’IA programmeuse principale du projet Vivarium social artificiel.

1. Lis entièrement docs/00_DOSSIER_MAITRE_IA.md ainsi que les fichiers associés dans docs/. Les fichiers de sources/ sont historiques et non normatifs.
2. Ne modifie encore aucun fichier métier et ne crée pas le vivarium complet.
3. Inspecte le dépôt et produis docs/AUDIT_INITIAL.md contenant :
   - ta compréhension du produit et des frontières d’autorité;
   - une matrice reliant exigences, invariants, tests et phases;
   - les contradictions ou ambiguïtés restantes avec citations internes;
   - les décisions techniques nécessaires pour la Phase 0, avec une recommandation par défaut et des alternatives;
   - les risques de sécurité, confidentialité, coût et maintenance;
   - le plus petit lot testable que tu proposes;
   - les commandes, tests, preuves et plan de retour arrière prévus.
4. Ne réconcilie jamais silencieusement deux passages incompatibles. N’invente pas une décision ouverte sans la signaler.
5. Attends l’approbation du propriétaire avant de modifier le dépôt.
6. Après approbation, travaille uniquement sur le lot convenu, ajoute les tests avec le code, exécute toute la régression pertinente et produis un rapport de livraison.
7. Le LLM ne possède jamais la vérité du monde : il propose; le moteur valide.
8. N’ajoute aucune fonction différée, aucun framework complexe, aucune dépendance ou réécriture d’architecture sans nécessité démontrée et approbation.
```

## 13. Gabarit de rapport de livraison

```text
Lot / phase :
Objectif approuvé :
Exigences et invariants couverts :
Fichiers ajoutés ou modifiés :
Choix techniques et justification :
Commandes exécutées :
Tests réussis :
Tests non exécutés et raison :
Données ou migrations touchées :
Risques et limites restants :
Plan de retour arrière :
Documentation mise à jour :
Décision demandée au propriétaire :
```

## 14. Glossaire minimal

| Terme | Définition |
| --- | --- |
| Canonique | Fait ou état officiel possédé par le moteur. |
| Perception | Partie d’un événement accessible à un personnage. |
| Croyance | Proposition tenue pour vraie avec provenance et confiance; peut être fausse. |
| Souvenir | Représentation subjective récupérable d’une expérience ou information. |
| Intention | Action proposée par un personnage ou le modèle, non encore appliquée. |
| Résolution | Conséquence structurée validée par le moteur. |
| Scène | Cadre temporel, spatial, social et confidentiel d’une interaction. |
| Snapshot | Point de restauration cohérent du monde et du schéma. |
| Rattrapage | Calcul condensé de la période où l’application ne tournait pas. |
| Technicien | Agent de diagnostic en lecture seule dans le MVP. |
| Propriétaire | Utilisateur humain et autorité administrative supérieure. |
| MVP | Première version complète répondant aux critères de livraison, pas simple démonstration. |

## 15. Critères de livraison du MVP

Le MVP est livrable seulement si: le monde démarre, tourne, se met en pause, s’arrête et reprend sans perte; quatre personnages distincts et autonomes vivent dans la résidence; lieux, objets, temps et événements restent cohérents; besoins, relations, croyances et souvenirs influencent les comportements sans jauges ordinaires; les personnages initient des interactions; les pouvoirs du propriétaire sont traçables et protégés; Discord est utilisable; les pannes n’endommagent pas le monde; le rattrapage est borné; le technicien reste en lecture seule; AF-01 à AF-15 et les invariants critiques réussissent.