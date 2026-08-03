> **SOURCE HISTORIQUE NON NORMATIVE.** En cas de différence, `docs/00_DOSSIER_MAITRE_IA.md` prévaut.

DOSSIER DE CONCEPTION - PARTIE IV

Vivarium social artificiel

Modèle du monde et dictionnaire des données

__________________________________________________________________

Définition de la réalité canonique, des personnages, relations, événements,
perceptions, souvenirs, interventions, règles d'intégrité et cycle de vie des données

Version 0.1 - août 2026

Statut : spécification logique de données - document vivant

Place dans le dossier : la Partie I fixe la vision, la Partie II l'architecture,
la Partie III le comportement du prototype, et la Partie IV définit ce que le système sait et conserve.

## 0. Comment utiliser ce document

La présente Partie IV décrit le modèle logique du vivarium. Elle définit les catégories de données, leurs relations, leur autorité, leur provenance et les règles qui empêchent une narration générée de devenir silencieusement la réalité. Elle doit être lisible par le propriétaire, puis suffisamment précise pour qu'une IA architecte puisse proposer un schéma SQLite sans devoir inventer le sens des informations.

| Règle de priorité La Partie III demeure l'autorité sur le comportement attendu. La Partie IV est l'autorité sur le sens et la structure logique des données. En cas de contradiction, l'IA ne doit pas réconcilier les textes en secret : elle doit citer les passages et demander une décision. |

| --- |

### 0.1 Ce que ce document fixe

- La différence entre réalité canonique, perception, interprétation, croyance et souvenir.

- Les entités minimales du prototype et les champs qu'elles doivent contenir.

- Les données appartenant au moteur, à un personnage, au propriétaire, à Discord ou au technicien.

- Les valeurs protégées, modifiables, versionnées, archivées ou supprimables.

- Les invariants qui doivent rester vrais après chaque action, panne, migration ou intervention administrative.

- Le modèle minimal à implanter maintenant et les extensions prévues sans implémentation immédiate.

### 0.2 Ce que ce document ne fixe pas encore

- Le DDL SQL exact, les noms définitifs des classes Python et les bibliothèques employées.

- Les coefficients finaux de décroissance des besoins, émotions et relations.

- Le fournisseur de modèle, le prix des appels ou la taille exacte des contextes.

- L'interface graphique d'administration éventuelle.

- La totalité des traits et préférences de chaque personnage réel du casting.

### 0.3 Étiquettes utilisées

| Étiquette | Sens |

| --- | --- |

| CANONIQUE | Fait officiel du monde. Seul le moteur ou une intervention administrative validée peut le modifier. |

| SUBJECTIF | Information propre à un personnage : perception, interprétation, croyance, souvenir, intention ou sentiment. |

| PROTÉGÉ | Modification interdite ou soumise à une confirmation renforcée. |

| DÉRIVÉ | Valeur calculée à partir d autres données; elle doit pouvoir être régénérée. |

| JOURNALISÉ | Toute création ou modification doit laisser une trace d audit. |

| DIFFÉRÉ | Prévu dans le modèle, mais non obligatoire dans le premier prototype. |

## 1. Principes fondamentaux du modèle

| ID | Principe |

| --- | --- |

| MD-001 | Le moteur local est la seule source de vérité canonique. |

| MD-002 | Le modèle de langage propose du texte et des intentions; il ne modifie jamais directement les données canoniques. |

| MD-003 | Chaque personnage possède une subjectivité isolée. Il ne reçoit que les informations qu il peut percevoir, apprendre ou se rappeler. |

| MD-004 | Une croyance peut être fausse sans rendre le monde faux. |

| MD-005 | Un souvenir peut être incomplet, biaisé ou contesté, mais doit avoir une provenance identifiable. |

| MD-006 | Les valeurs cachées influencent le comportement sans être affichées comme des jauges ordinaires. |

| MD-007 | Les modifications administratives sont versionnées et séparées de leurs manifestations dans le monde. |

| MD-008 | Les données brutes importantes ne sont pas remplacées par un résumé; les résumés sont des couches dérivées. |

| MD-009 | Toute opération pouvant être rejouée après une panne doit être idempotente. |

| MD-010 | Le modèle doit rester portable vers un autre fournisseur, un autre ordinateur ou un modèle local. |

| Formule conceptuelle Intention -> validation -> résolution -> événement canonique -> perceptions -> interprétations -> souvenirs et croyances. Aucune étape ne doit être sautée lorsqu une conséquence durable est créée. |

| --- |

## 2. Ontologie générale et niveaux de réalité

Le vivarium contient plusieurs niveaux qui peuvent se contredire sans provoquer d'erreur. La contradiction devient un problème seulement lorsque deux faits canoniques incompatibles sont actifs au même moment.

| Niveau | Question | Exemple | Autorité |

| --- | --- | --- | --- |

| Réalité canonique | Qu est-ce qui existe ou s est produit? | Le piano a été ajouté au salon à 14 h 10. | Moteur / administrateur confirmé |

| Accessibilité perceptive | Qui pouvait le voir, l entendre ou en subir les effets? | Mira était dans le salon; Nao était dehors. | Moteur |

| Perception | Qu a capté chaque témoin? | Mira remarque un piano apparu sans bruit. | Personnage, à partir des données accessibles |

| Interprétation | Que pense-t-elle que cela signifie? | Mira suppose que le propriétaire l a offert. | Personnage |

| Croyance | Quelle proposition tient-elle pour vraie? | Le propriétaire veut encourager la musique. | Personnage, avec degré de confiance |

| Souvenir | Que conserve-t-elle de l épisode? | Un cadeau mystérieux est apparu dans le salon. | Personnage, avec consolidation |

| Narration | Comment raconte-t-elle l événement? | Elle embellit ou omet certains détails. | LLM; non canonique sauf contenu explicitement déclaré |

### 2.1 Règle de non-contamination

- Un message de dialogue ne crée pas automatiquement un objet, un déplacement, une blessure ou un changement relationnel.

- Une pensée privée ne devient pas connue des autres personnages.

- Une hypothèse du narrateur ou du modèle doit être enregistrée comme hypothèse, jamais comme fait.

- Une correction administrative d'un souvenir ne réécrit pas silencieusement l'événement canonique d'origine.

- Un résumé peut omettre des détails, mais ne doit pas inverser le sens des événements sources.

## 3. Identifiants, temps, versions et provenance

### 3.1 Identifiants

| Concept | Règle |

| --- | --- |

| Identifiant unique | Chaque entité persistante reçoit un identifiant opaque et immuable, de préférence UUID. Le nom affiché n est jamais une clé technique. |

| Identifiant de corrélation | Toutes les données produites par un même cycle portent un identifiant commun : intention, appel LLM, résolution, événement et notifications. |

| Clé d idempotence | Une action déjà appliquée ne peut pas être appliquée une seconde fois lors d un retry ou d un redémarrage. |

| Version d entité | Les fiches sensibles et configurations portent un numéro de version croissant pour détecter les modifications concurrentes. |

### 3.2 Temps réel et temps simulé

| Champ logique | Sens |

| --- | --- |

| created_at_utc | Moment réel où l enregistrement a été créé. |

| updated_at_utc | Dernière modification réelle. |

| occurred_at_sim | Moment où l événement est réputé avoir eu lieu dans le vivarium. |

| effective_from / effective_to | Période pendant laquelle un état, une règle ou une relation est valide. |

| timezone_display | Fuseau utilisé pour l affichage au propriétaire; les données internes restent en UTC. |

| offline_gap_id | Référence vers la période de rattrapage qui a produit un événement condensé. |

### 3.3 Provenance obligatoire

| Source | Exemples | Exigence |

| --- | --- | --- |

| Moteur déterministe | Décroissance de faim, fin de sommeil, arrivée planifiée. | Règle ou version de calcul enregistrée. |

| Résolution LLM validée | Choix d une intention, interprétation, dialogue. | Modèle, version, prompt logique, schéma de sortie et résultat de validation. |

| Propriétaire | Ajout d objet, modification de personnalité, correction de mémoire. | Demande, implications présentées, confirmation et snapshot préalable si requis. |

| Import / migration | Création initiale d une fiche ou changement de schéma. | Version source, outil de migration et résultat. |

| Technicien | Rapport de diagnostic ou proposition de changement. | Preuves consultées et absence de modification active dans le MVP. |

## 4. État global du monde

Le monde est l'entité racine. Toutes les autres données appartiennent à un monde précis, même si un seul monde existe dans le prototype.

| Champ | Type logique | Obligatoire | Description |

| --- | --- | --- | --- |

| world_id | UUID | Oui | Identifiant stable du vivarium. |

| name | Texte | Oui | Nom interne ou affiché du monde. |

| schema_version | Entier / texte | Oui | Version du modèle de données actuellement chargée. |

| simulation_status | Enum | Oui | running, paused, degraded, maintenance, stopped. |

| simulation_time | Date-heure | Oui | Temps simulé courant, aligné sur le temps réel dans le MVP. |

| last_clean_shutdown_at | Date-heure | Non | Dernière fermeture complète et valide. |

| last_heartbeat_at | Date-heure | Oui | Dernière preuve que le service était actif. |

| active_snapshot_id | UUID | Non | Snapshot de référence utilisé pour reprise ou restauration. |

| configuration_version | Entier | Oui | Version de la configuration fonctionnelle. |

| created_at_utc / updated_at_utc | Date-heure | Oui | Métadonnées techniques. |

### 4.1 États globaux permis

| État | Effet |

| --- | --- |

| running | Horloge active; routines, événements et appels cognitifs permis. |

| paused | Aucun temps simulé ne progresse; consultation et administration permises. |

| degraded | Routines sûres seulement; appels cognitifs ou Discord partiellement indisponibles. |

| maintenance | Aucune action de personnage; migrations, diagnostics ou restauration seulement. |

| stopped | Service inactif; un rattrapage sera calculé au prochain démarrage. |

## 5. Acteurs et personnages

Le modèle distingue l'acteur générique de la fiche détaillée d'un personnage. Cette séparation permet de représenter le propriétaire, un contact extérieur simplifié ou un service technique sans leur attribuer automatiquement des besoins humains complets.

| Entité | Rôle |

| --- | --- |

| actor | Référence commune pour tout participant pouvant être lié à un événement, une relation ou une scène. |

| character | Extension détaillée d un actor pour une habitante complète du vivarium. |

| owner_actor | Acteur spécial représentant le propriétaire comme entité supérieure ou participant manifesté. |

| external_contact | Acteur léger du monde extérieur; peut être promu plus tard en personnage complet. |

| system_actor | Moteur, technicien ou source impersonnelle utilisée pour audit, jamais pour simuler une personne. |

### 5.1 Fiche d identité d un personnage

| Champ | Type | Protection | Description |

| --- | --- | --- | --- |

| character_id | UUID | Immuable | Référence vers actor_id. |

| display_name | Texte | Versionné | Nom affiché. |

| adult_status | Booléen / enum | PROTÉGÉ | Doit être adult_confirmed pour tout personnage du prototype. |

| origin_type | Enum | Versionné | original ou canonical_fiction. |

| source_identity | Texte / références | Selon origine | Oeuvre, version, période ou interprétation retenue pour un personnage canonique. |

| pronouns / grammatical_profile | Structure | Versionné | Accords et formes d adresse. |

| appearance_summary | Texte structuré | Modifiable | Description utile au contexte et à Discord; pas de graphisme requis. |

| voice_profile | Structure | Modifiable avec prudence | Style verbal, longueur, registre, tics permis et interdits. |

| discord_identity_id | UUID | Modifiable | Nom et avatar présentés par webhook. |

| status | Enum | PROTÉGÉ | active, dormant, unavailable, departure_requested, archived. |

| created_at / updated_at | Date-heure | Audit | Métadonnées. |

### 5.2 Canon et plasticité

| Niveau | Sens | Exemple | Modification |

| --- | --- | --- | --- |

| Figé | Élément identitaire qui ne doit pas dériver. | Valeur centrale, histoire déterminante, trait iconique. | Blocage automatique sauf décision administrative explicite renforcée. |

| Borné | Peut évoluer dans une plage compatible. | Sociabilité habituellement faible à moyenne. | Évolution naturelle limitée; dépassement signalé. |

| Souple | Peut changer graduellement avec justification. | Intérêt, habitude, opinion secondaire. | Évolution enregistrée avec causes. |

| Libre | Créé par la simulation sans contrainte canonique. | Nouvelle amitié, projet, souvenir du vivarium. | Évolution normale. |

| Personnages canoniques Les règles de canon appartiennent aux données du personnage, pas seulement au prompt. Lorsqu'une action proposée contredit un élément figé, le moteur doit demander une autre réaction, signaler le conflit ou exiger une intervention administrative. |

| --- |

## 6. Personnalité, valeurs, intérêts et limites

Une personnalité n'est pas un bloc de prose unique. Le modèle conserve une description lisible, des dimensions structurées et un historique des changements. Les dimensions servent à maintenir la continuité; elles ne remplacent pas le jugement du modèle.

| Entité / groupe | Champs minimaux | Règle d évolution |

| --- | --- | --- |

| trait_definition | Nom, description, pôles, comportement attendu, incompatibilités. | Définition globale versionnée. |

| character_trait | Valeur 0-100, centralité, plasticité, confiance, justification. | Variation lente; changement important crée un événement ou une intervention. |

| value | Principe personnel, priorité, conditions de conflit. | Très lente; peut être figée ou bornée. |

| interest | Sujet ou activité, intensité, compétence, curiosité, satiété temporaire. | Peut croître, décroître ou se diversifier. |

| preference | Cible, polarité, intensité, contexte, visibilité. | Lente à moyenne selon expériences. |

| personal_boundary | Domaine, règle, exceptions, communication, fermeté. | Jamais déduite uniquement d une jauge relationnelle; versionnée. |

| communication_style | Directivité, humour, longueur, franchise, vocabulaire. | Souple, mais cohérent avec identité et humeur. |

### 6.1 Représentation numérique

- Les valeurs internes utilisent une échelle normalisée de 0 à 100 lorsqu'une intensité continue est utile.

- Une valeur numérique doit être accompagnée d'une définition. Le chiffre 70 n'a aucun sens sans seuils et comportements associés.

- Les changements enregistrent un delta, une cause et une limite de vitesse; le LLM ne réécrit pas directement la valeur absolue.

- Les étiquettes visibles telles que faible, modéré ou élevé sont dérivées et configurables.

- Les champs textuels conservent les nuances impossibles à réduire à une dimension.

## 7. Besoins, physiologie et états temporaires

Les besoins détaillés fournissent une pression continue au monde sans transformer les habitantes en automates. La plupart des variations sont déterministes; le LLM intervient lorsqu'il faut choisir comment répondre à plusieurs besoins incompatibles.

| Besoin / état | Données minimales | Traitement de base |

| --- | --- | --- |

| Énergie / sommeil | Niveau, dette de sommeil, heure habituelle, qualité du repos. | Décroissance avec activité; récupération pendant le sommeil. |

| Faim / alimentation | Satiété, dernier repas, préférences, contraintes. | Évolution temporelle; choix de repas si décision pertinente. |

| Hydratation | Niveau, dernier apport. | Peut être condensée et rarement narrée. |

| Hygiène | Niveau, activité salissante, préférence personnelle. | Routines déterministes; influence confort et choix. |

| Confort physique | Température, bruit, vêtements, douleur, qualité du lieu. | Dérivé du lieu, des objets et de l état corporel. |

| Santé générale | État stable, blessures actives, limitations. | Pas de maladie, vieillissement ou mort dans le MVP. |

| Besoin social | Désir d interaction, isolement récent, qualité des contacts. | N est pas identique à extraversion; dépend de l historique récent. |

| Besoin de solitude | Saturation sociale, besoin de calme, intimité. | Peut augmenter après une scène intense même chez une personne sociable. |

| Stimulation / ennui | Variété récente, progression, curiosité insatisfaite. | Peut déclencher activité ou projet. |

| Intimité / désir | Libido de base, disposition actuelle, contexte, stress, préférences. | Influence possible, jamais ordre automatique ni substitut aux limites. |

| Humeur globale | Valence, activation, stabilité. | Dérivée des émotions, besoins et événements récents. |

### 7.1 Structure d un état de besoin

| Champ | Description |

| --- | --- |

| need_type_id | Définition du besoin. |

| current_level | Valeur cachée 0-100. Le sens haut/bas est défini par le type. |

| target_range | Zone habituelle ou confortable propre au personnage. |

| rate_profile | Rythme de variation selon heure, activité, traits et environnement. |

| urgency | Valeur dérivée indiquant la pression actuelle. |

| last_satisfied_at | Dernier événement ayant réellement répondu au besoin. |

| trend | stable, rising, falling. |

| source_version | Version de la règle de calcul. |

| Valeurs cachées Le propriétaire peut les inspecter en mode administrateur, mais l'expérience ordinaire ne doit pas afficher des jauges. Les personnages ne connaissent pas leurs nombres exacts; ils perçoivent des sensations et tendances traduites en langage. |

| --- |

## 8. Émotions, humeur et appréciation des événements

Une émotion est une réaction courte à un événement évalué selon les buts, relations, besoins et valeurs du personnage. L'humeur est plus lente et influence l'interprétation de nouveaux événements.

| Entité | Champs | Durée |

| --- | --- | --- |

| emotion_episode | Type, intensité 0-100, cible, événement source, appréciation, expression, régulation. | Minutes à heures; décroît ou se transforme. |

| mood_state | Valence, activation, tension, stabilité, causes dominantes. | Heures à jours; mise à jour graduelle. |

| appraisal | Pertinence, nouveauté, contrôle, responsabilité perçue, compatibilité avec valeurs. | Créée lors d un événement significatif. |

| emotional_baseline | Réactivité, récupération, expressivité, tendances. | Lente; liée aux traits. |

### 8.1 Règles

- Une émotion n'est pas choisie uniquement pour produire une scène intéressante.

- Plusieurs émotions peuvent coexister envers la même personne ou le même événement.

- L'expression observable peut différer de l'état ressenti selon le caractère et le contexte.

- Un épisode émotionnel important peut créer un souvenir; une fluctuation mineure ne le fait pas automatiquement.

- Le système doit conserver les causes dominantes afin qu'une humeur ne paraisse pas arbitraire.

## 9. Objectifs, projets, plans et habitudes

| Entité | But | Champs principaux |

| --- | --- | --- |

| goal | Résultat souhaité, parfois abstrait. | Description, origine, priorité, horizon, statut, critères de progression, conflits. |

| project | Suite d actions persistante. | Propriétaire du projet, étapes, ressources, participants, progression, état. |

| plan | Ordonnancement temporaire. | Période, blocs horaires, flexibilité, dépendances. |

| habit | Comportement récurrent appris. | Déclencheur, action, force, contexte, dernière exécution. |

| intention | Choix immédiat proposé avant validation. | Action visée, motif, urgence, alternatives, contexte. |

### 9.1 Statuts permis

| Objet | Statuts minimaux |

| --- | --- |

| Goal | candidate, active, paused, achieved, abandoned, blocked. |

| Project | proposed, active, waiting, blocked, completed, abandoned. |

| Plan item | scheduled, started, completed, skipped, interrupted. |

| Intention | proposed, rejected, accepted, superseded, expired. |

### 9.2 Autonomie et départ

Les personnages peuvent créer et abandonner leurs buts sans approbation. Une intention de quitter définitivement l'aventure utilise toutefois le statut protégé departure_requested. Elle devient un événement majeur adressé au propriétaire et ne peut pas aboutir à l'archivage du personnage sans décision administrative.

## 10. Relations sociales

Une relation est dirigée : ce que A ressent envers B n'est pas automatiquement identique à ce que B ressent envers A. Le propriétaire est représenté par un acteur spécial et peut donc recevoir une relation sociale normale de chaque personnage, même si ses pouvoirs administratifs sont enregistrés ailleurs.

| Dimension | Sens | Évolution typique |

| --- | --- | --- |

| Familiarité | Quantité et diversité d expérience partagée. | Augmente avec exposition; décroît rarement. |

| Confiance | Attente de fiabilité, honnêteté ou protection. | Lente; sensible aux violations. |

| Affection | Attachement positif général. | Graduelle; peut coexister avec irritation. |

| Respect | Évaluation des capacités, valeurs ou statut. | Dépend des actes observés. |

| Sécurité | Confort à être vulnérable ou authentique. | Lente; dépend de la prévisibilité et du respect des limites. |

| Attirance | Intérêt romantique ou physique. | Influencée par préférences, contexte et histoire; non obligatoire. |

| Irritation | Tension ou frustration accumulée. | Rapide à monter, variable à décroître. |

| Méfiance | Anticipation de risque ou d intention cachée. | Peut rester élevée malgré affection. |

| Jalousie / possessivité | Réaction à une menace perçue sur une relation ou une place. | Dépend de personnalité, sécurité et contexte. |

| Dette / obligation perçue | Sentiment de devoir quelque chose à l autre. | Créé par services, promesses ou réparations. |

### 10.1 Structure relationnelle

| Champ | Description |

| --- | --- |

| relationship_id | Identifiant de la relation dirigée. |

| source_actor_id / target_actor_id | Personne qui ressent et personne visée. |

| dimension_values | Valeurs cachées 0-100 par dimension active. |

| relationship_label | Étiquette dérivée ou déclarée : connaissance, amie, partenaire, rivale, etc. |

| expectations | Attentes conscientes ou implicites, structurées. |

| boundaries_between | Accords ou limites spécifiques à cette relation. |

| shared_history_summary | Résumé dérivé, relié aux événements sources. |

| unresolved_tensions | Références vers conflits, promesses ou besoins de réparation. |

| last_meaningful_interaction_at | Dernière interaction significative. |

| version / updated_at | Contrôle de concurrence et audit. |

### 10.2 Modification graduelle

- Les actions produisent des impacts limités par événement, modulés par la gravité et l'historique.

- Un dialogue agréable ne remet pas automatiquement une tension importante à zéro.

- Les valeurs relationnelles ne sont pas directement écrites par le LLM; il propose des effets justifiés que le moteur borne.

- Les changements importants créent un relationship_change record lié aux événements qui les expliquent.

- Les étiquettes sociales peuvent être contestées ou asymétriques.

## 11. Lieux, déplacements et objets

### 11.1 Lieux détaillés du MVP

| Lieu | Type | Confidentialité par défaut | Notes |

| --- | --- | --- | --- |

| Salon | Commun | Publique aux résidentes présentes | Conversations de groupe, détente, objets partagés. |

| Cuisine | Commun fonctionnel | Publique aux présentes | Repas, routines, interactions brèves. |

| Chambre 1 à 4 | Privé individuel | Accès contrôlé par l occupante | Repos, objets personnels, scènes privées. |

| Salle de bain | Privé fonctionnel | Occupation exclusive par défaut | Hygiène et intimité. |

| Cour | Commun extérieur | Publique aux présentes | Loisirs, calme, activités extérieures. |

| Monde extérieur | Zone abstraite | Selon sortie | Pas un lieu détaillé; utilise outings et destinations légères. |

### 11.2 Données d un lieu

| Champ | Description |

| --- | --- |

| location_id / world_id | Identité et appartenance. |

| name / location_type | Nom et catégorie. |

| description_canonical | Description officielle, indépendante d une narration de scène. |

| privacy_level | public, shared, private, restricted. |

| access_rules | Acteurs permis, conditions, exceptions. |

| capacity | Capacité souple ou stricte. |

| environment_state | Bruit, lumière, température narrative, propreté, ambiance et événements actifs. |

| occupancy | Dérivé des positions actuelles; jamais une liste indépendante contradictoire. |

| available_activities | Actions et usages permis. |

| connected_locations | Liens de déplacement et durées. |

### 11.3 Objets

| Champ | Description |

| --- | --- |

| object_id / object_type | Identité et définition. |

| display_name / description | Nom et apparence textuelle. |

| location_id / holder_actor_id | Une seule position canonique active à la fois. |

| owner_actor_id | Propriété sociale ou personnelle, distincte de la possession physique. |

| state | État fonctionnel structuré : fermé, allumé, endommagé, contenu, etc. |

| affordances | Actions permises : utiliser, lire, déplacer, offrir, ranger. |

| privacy / sensitivity | Contrôle de perception et d exposition. |

| origin_event_id | Événement ayant créé ou introduit l objet. |

| version | Incrément après modification. |

| Invariant spatial Un personnage et un objet ne peuvent pas occuper simultanément deux emplacements exclusifs. Les listes d'occupants et inventaires sont des vues dérivées de la position canonique. |

| --- |

## 12. Actions, scènes et conversations

### 12.1 Chaîne d une action

| action_intent -> validation_result -> action_resolution -> canonical_event(s) -> perception(s) -> memory / belief / relationship effects |

| --- |

| Entité | Contenu minimal | Autorité |

| --- | --- | --- |

| action_intent | Acteur, action proposée, paramètres, motif, urgence, alternatives. | Personnage ou propriétaire. |

| validation_result | Règles examinées, état attendu, autorisation, raison du refus. | Moteur. |

| action_resolution | Résultat structuré, coûts, changements, événements créés. | Moteur; peut utiliser un LLM pour arbitrage narratif borné. |

| scene | Contexte partagé avec lieu, temps, participants, confidentialité et statut. | Moteur. |

| conversation | Sous-ensemble d une scène contenant tours de parole et sujets. | Moteur pour structure; LLM pour contenu. |

| utterance | Locuteur, destinataires, texte, canal, visibilité, acte de langage. | LLM ou propriétaire; non canonique au-delà des mots prononcés. |

### 12.2 Statuts de scène

| Statut | Sens |

| --- | --- |

| open | Scène active; nouveaux événements permis. |

| paused | Suspendue volontairement, sans clôture. |

| interrupted | Arrêt technique ou départ inattendu. |

| closed | Fin normale avec heure et résumé. |

| aborted | Annulée avant conséquence significative. |

| archived | Conservée mais retirée des vues actives. |

### 12.3 Clôture automatique après panne

Lors d'un redémarrage, toute scène open sans heartbeat valide devient interrupted, puis closed par une opération de reprise. Les messages déjà produits restent conservés. Le résumé de clôture ne doit pas inventer un échange complet après le dernier fait enregistré.

## 13. Événements canoniques et causalité

L'événement canonique est l'unité principale de l'histoire du monde. Il décrit un changement ou un fait daté, mais ne contient pas automatiquement ce que chaque personne en pense.

| Champ | Type | Description |

| --- | --- | --- |

| event_id | UUID | Identifiant immuable. |

| event_type | Enum / identifiant | Catégorie : movement, speech, object_change, relationship_incident, injury, admin_effect, etc. |

| occurred_at_sim | Date-heure | Moment dans le vivarium. |

| location_id | UUID / null | Lieu canonique si pertinent. |

| initiator_actor_id | UUID / null | Acteur à l origine, si applicable. |

| participants | Relations | Acteurs directement impliqués et rôles. |

| payload | Structure validée | Faits propres au type d événement. |

| visibility_rule | Structure | Conditions permettant une perception. |

| cause_event_ids | Liste de UUID | Causes ou contexte immédiat. |

| correlation_id | UUID | Cycle ou action ayant produit l événement. |

| importance_system | 0-100 | Importance opérationnelle pour consolidation et notifications. |

| status | Enum | committed, superseded, invalidated; jamais supprimé silencieusement. |

| created_by / provenance | Structure | Moteur, propriétaire, migration ou résolution validée. |

### 13.1 Participants et témoins

- Un participant est directement impliqué dans l'événement; un témoin peut seulement le percevoir.

- La présence dans le même lieu ne garantit pas une perception complète : bruit, attention, confidentialité et état influencent l'accès.

- Les témoins ne sont pas stockés comme vérité définitive avant calcul; des perceptions sont créées individuellement.

- Un événement peut rester sans témoin et avoir néanmoins des conséquences physiques.

### 13.2 Correction d un fait

Un fait canonique commis n'est pas édité en place pour cacher une erreur. Une correction crée un événement de rectification ou marque l'ancien événement superseded avec une référence vers le remplacement. L'historique d'audit reste disponible.

## 14. Perception, connaissance et croyance

### 14.1 Perception

| Champ | Description |

| --- | --- |

| perception_id | Identifiant. |

| character_id | Personnage qui perçoit. |

| source_event_id | Événement canonique source. |

| modality | seen, heard, felt, told, inferred. |

| detail_level | Degré de détail réellement accessible. |

| perceived_content | Résumé structuré sans informations cachées. |

| attention_confidence | Qualité de l attention et fiabilité sensorielle. |

| created_at_sim | Moment de perception. |

| privacy_class | Niveau de confidentialité du contenu perçu. |

### 14.2 Croyance et connaissance

| Concept | Différence | Champs particuliers |

| --- | --- | --- |

| Knowledge claim | Fait que le système considère comme accessible au personnage et correctement compris. | Proposition, portée, source, date, validité. |

| Belief | Proposition tenue pour vraie par le personnage, possiblement fausse. | Confiance 0-100, sources, contre-preuves, statut contesté. |

| Assumption | Hypothèse de travail faible et temporaire. | Confiance basse, expiration rapide. |

| Secret known | Information vraie connue, mais dont le partage est restreint. | Propriétaire du secret, personnes autorisées, origine. |

| Rumor | Information transmise socialement avec chaîne de sources. | Émetteurs, transformations, confiance et portée. |

### 14.3 Contradictions internes

Un personnage peut conserver plusieurs croyances incompatibles si chacune possède sa source et sa confiance. Le moteur ne choisit pas immédiatement une vérité subjective; une réflexion, une preuve ou une discussion peut plus tard renforcer, affaiblir ou remplacer une croyance.

## 15. Mémoire

La mémoire n'est pas le journal complet. Elle représente ce qu'un personnage peut retrouver et utiliser. Le journal canonique demeure séparé, même lorsque le personnage oublie.

| Type | Fonction | Source habituelle |

| --- | --- | --- |

| Mémoire récente | Contexte détaillé des dernières heures ou journées. | Perceptions, conversations, objectifs actifs. |

| Souvenir épisodique | Épisode vécu avec lieu, acteurs, interprétation et émotion. | Un ou plusieurs événements et perceptions. |

| Connaissance sémantique | Faits appris sur le monde ou les personnes. | Conversations, observation, enseignement. |

| Mémoire relationnelle | Résumé de l histoire avec une personne et tensions actives. | Épisodes et changements relationnels. |

| Résumé autobiographique | Compréhension condensée de sa propre trajectoire. | Réflexions périodiques et épisodes importants. |

| Intention différée | Chose à dire ou faire plus tard. | But, message non envoyé, promesse. |

| Mémoire procédurale | Habitude ou manière de faire une activité. | Répétition et apprentissage; DIFFÉRÉ au MVP. |

### 15.1 Champs d un souvenir

| Champ | Description |

| --- | --- |

| memory_id / character_id | Identité et propriétaire subjectif. |

| memory_type | Catégorie ci-dessus. |

| source_ids | Événements, perceptions, messages, réflexions ou intervention administrative. |

| first_person_summary | Contenu subjectif utilisé pour récupération. |

| objective_anchor | Résumé neutre facultatif, inaccessible au personnage dans son contexte ordinaire. |

| importance | Valeur 0-100 pour conservation et récupération. |

| emotional_salience | Intensité et émotions associées. |

| confidence | Confiance subjective dans le souvenir. |

| privacy_level | private, intimate, shared, public. |

| accessibility | Facilité actuelle de rappel, distincte de l importance. |

| last_recalled_at / recall_count | Historique de réactivation. |

| status | active, faded, disputed, superseded, archived. |

| version / provenance | Audit et modifications. |

### 15.2 Consolidation et oubli

| Processus | Effet |

| --- | --- |

| Sélection | Seuls les événements pertinents, surprenants, émotionnels ou liés aux buts deviennent des souvenirs détaillés. |

| Consolidation | Plusieurs souvenirs proches peuvent produire un résumé sans effacer les sources. |

| Rappel | Un souvenir récupéré peut gagner en accessibilité ou être réinterprété; l original reste versionné. |

| Oubli naturel | L accessibilité baisse. Le souvenir n est pas supprimé automatiquement du stockage canonique subjectif. |

| Correction | Une preuve peut marquer le souvenir disputed ou superseded; le personnage peut se souvenir d avoir été dans l erreur. |

| Archivage | Les détails anciens sont exclus du contexte courant, mais disponibles en inspection administrative. |

### 15.3 Modification administrative

Le propriétaire peut inspecter, ajouter, corriger, affaiblir ou retirer un souvenir. Toute demande doit présenter les implications : croyances dépendantes, relations, buts, identité autobiographique et conversations futures. Une confirmation et un snapshot sont requis avant application. L'opération produit une nouvelle version et un audit; elle ne détruit pas l'historique technique.

## 16. Monde extérieur abstrait

Le monde extérieur existe par des sorties, destinations, horaires, contacts et résultats condensés. Il n'est pas simulé comme une ville complète.

| Entité | Champs minimaux | Promotion possible |

| --- | --- | --- |

| external_destination | Nom, type, durée de trajet, activités, risques, horaires. | Peut devenir un lieu détaillé plus tard. |

| external_contact | Nom, rôle, lien aux personnages, importance, derniers événements. | Peut devenir un personnage complet. |

| outing | Personnage, destination, motif, départ, retour prévu, niveau de détail. | Peut ouvrir une scène détaillée si événement important. |

| external_event | Résultat structuré, témoins, impacts, résumé. | Peut créer événements, perceptions et souvenirs. |

| schedule_commitment | Travail, rendez-vous, activité récurrente. | Peut devenir projet ou institution plus tard. |

### 16.1 Rattrapage hors ligne

| Entité | Rôle |

| --- | --- |

| offline_gap | Début, fin, durée, état initial et cause de l interruption. |

| catchup_run | Version de règles, personnages traités, appels utilisés, état final et statut. |

| catchup_summary | Résumé destiné au propriétaire; dérivé des événements créés. |

| condensed_activity | Bloc d activité ordinaire avec effets déterministes et quelques faits significatifs. |

| Règle de rattrapage Le système ne doit pas générer rétroactivement une scène détaillée comme si elle avait été jouée en direct. Il crée au moment du redémarrage des résultats structurés et datés, puis les personnages peuvent s'en souvenir selon les perceptions produites. |

| --- |

## 17. Propriétaire, manifestations et interventions administratives

### 17.1 Présence du propriétaire

| Mode | Donnée canonique | Perception |

| --- | --- | --- |

| Observateur | Aucune présence dans une scène. | Aucune, sauf règle spéciale. |

| Communication supérieure | Message ou manifestation lié à owner_actor. | Destinataires savent que le propriétaire communique. |

| Participant manifesté | owner_presence avec lieu, durée et forme. | Perception normale selon la scène. |

| Régisseur | admin_intervention modifiant le monde. | Les effets sont perçus; l origine dépend de perceptibility_mode. |

| Administrateur | Inspection ou édition directe de données. | Aucune connaissance automatique. |

### 17.2 Intervention administrative

| Champ | Description |

| --- | --- |

| intervention_id | Identifiant et corrélation. |

| requested_by | Toujours le propriétaire dans le MVP. |

| request_text | Demande originale. |

| target_entities | Personnages, objets, lieux, règles ou souvenirs visés. |

| proposed_changes | Diff logique avant application. |

| impact_analysis | Conséquences probables et dépendances. |

| risk_level | low, medium, high, critical. |

| confirmation_required | Toujours vrai pour modification directe d un personnage. |

| approval_id | Référence vers confirmation explicite. |

| pre_snapshot_id | Snapshot obligatoire pour changement sensible. |

| perceptibility_mode | imperceptible, effects_only, announced, manifested. |

| status | draft, awaiting_confirmation, approved, applied, rejected, rolled_back, failed. |

| applied_event_ids | Effets canoniques créés. |

### 17.3 Perceptibilité

| Mode | Ce que les personnages peuvent savoir |

| --- | --- |

| imperceptible | Aucun événement perceptible n est créé; seule la conséquence interne existe. |

| effects_only | Les effets sont observables, mais l origine n est pas révélée. |

| announced | Un message canonique attribue explicitement le changement au propriétaire. |

| manifested | Le propriétaire agit dans une scène et peut être perçu comme acteur de l intervention. |

## 18. Intimité, contenu adulte, confidentialité et blessures

Le modèle de données doit pouvoir représenter des relations et scènes adultes entre personnages explicitement adultes, sans faire de ce contenu une finalité obligatoire. Les détails sont des données privées et sensibles dans le contexte du vivarium.

### 18.1 Disposition et préférences

| Donnée | Règle |

| --- | --- |

| adult_status | Condition structurelle obligatoire et protégée. |

| libido_baseline | Tendance individuelle lente, distincte de la disposition actuelle. |

| current_desire_state | État temporaire influencé par contexte, fatigue, émotions, relation et préférences. |

| intimacy_preferences | Préférences structurées, intensité, contexte, visibilité et capacité d évolution. |

| personal_boundaries | Limites propres au personnage; aucune relation ou jauge ne les annule. |

| relationship_specific_agreements | Accords, habitudes ou limites propres à une relation, versionnés. |

| private_event_memory | Souvenir conservé avec niveau intimate et contrôle strict de diffusion aux autres personnages. |

### 18.2 Confidentialité

| Niveau | Accès ordinaire |

| --- | --- |

| public | Tous les personnages pouvant recevoir l information. |

| shared | Groupe ou liste définie. |

| private | Propriétaire subjectif uniquement, sauf partage volontaire. |

| intimate | Sous-catégorie privée exclue des résumés généraux et notifications ordinaires. |

| admin | Propriétaire en inspection administrative et composants système autorisés. |

| technical_secret | Clés et secrets d infrastructure; jamais envoyés au LLM. |

### 18.3 Blessures

| Champ | Description |

| --- | --- |

| injury_id / character_id | Identité et personne touchée. |

| injury_type / body_area | Nature et localisation générale. |

| severity | Niveau borné; aucune mort dans le MVP. |

| cause_event_id | Événement canonique source obligatoire. |

| limitations | Actions ou activités affectées. |

| pain_level / visibility | État caché et signes perceptibles. |

| recovery_plan | Durée estimée et étapes. |

| status | active, healing, healed, chronic; chronic peut être différé. |

| memories_created | Souvenirs et réactions relationnelles éventuels. |

## 19. Discord et état de présentation

Discord est une interface, pas la source de vérité. Supprimer un message Discord ne supprime pas automatiquement l'événement ou le souvenir correspondant.

| Entité | Champs minimaux |

| --- | --- |

| discord_identity | Actor ou personnage, nom affiché, avatar, webhook ou route, statut actif. |

| discord_channel_route | Type de flux, salon cible, confidentialité, permissions. |

| discord_message_record | Message externe, message interne lié, statut envoyé, erreur, timestamp, id Discord. |

| notification | Type, sévérité, destinataire, contenu dérivé, statut lu ou envoyé. |

| user_toggle | Portée globale ou par personnage, clé, valeur, version, date. |

| daily_digest | Période couverte, événements sources, résumé, statut de publication. |

### 19.1 Toggles fonctionnels

| Clé | Valeurs | Effet sur les données |

| --- | --- | --- |

| spontaneous_contact | on / off, global et par personnage | N affecte pas l intention interne; contrôle seulement la livraison vers Discord. |

| inter_character_scenes | direct / summary / hidden | N affecte ni la scène ni ses conséquences. |

| private_scenes | direct / summary / hidden | Contrôle la présentation au propriétaire. |

| daily_summary | on / off / fréquence | Crée ou non un digest dérivé. |

| technical_reports | on / off / severity | Filtre les notifications, pas les journaux techniques. |

| cost_alerts | on / off / thresholds | Génère des alertes; seuils à définir plus tard. |

### 19.2 Identités distinctes

Un seul bot peut recevoir les commandes tandis qu'un ou plusieurs webhooks publient avec le nom et l'avatar du personnage concerné. Le mapping est une donnée de présentation remplaçable; l'identité du personnage reste character_id, jamais le webhook.

## 20. Agent technicien, diagnostics et données de développement

Dans le prototype, le technicien lit, mesure et recommande. Il ne modifie pas le code actif ni les données pour simuler une correction.

| Entité | Contenu |

| --- | --- |

| technician_request | Demande du propriétaire, portée, priorité et pièces jointes. |

| diagnostic_report | Symptôme, données consultées, hypothèses, preuves, conclusion et confiance. |

| change_proposal | Modification recommandée, risques, tests, migration et retour arrière. |

| evaluation_run | Scénario, version du système, résultats, métriques et verdict. |

| known_issue | Problème identifié, sévérité, contournement et statut. |

| Séparation obligatoire Les rapports du technicien sont des données techniques. Ils ne deviennent pas des souvenirs de personnages et ne modifient pas les événements du monde, sauf intervention explicite du propriétaire. |

| --- |

## 21. Configuration, règles et définitions versionnées

Les définitions partagées doivent être données plutôt que dispersées dans les prompts. Cela permet de modifier une règle, tester son effet et savoir avec quelle version un événement a été produit.

| Groupe | Exemples | Versionnement |

| --- | --- | --- |

| Simulation | Cadence, seuils d importance, rattrapage, activité. | configuration_version globale et historique. |

| Besoins | Définitions, sens des échelles, rythmes par défaut. | need_definition_version. |

| Relations | Dimensions, limites de delta, seuils dérivés. | relationship_rules_version. |

| Mémoire | Importance, consolidation, oubli, récupération. | memory_policy_version. |

| Actions | Schémas de paramètres, préconditions, effets permis. | action_type_version. |

| Modèle | Adaptateur, capacités, schémas de sortie, paramètres. | model_profile_version. |

| Discord | Routes, identités, toggles et formats de notification. | interface_config_version. |

| Canon | Règles propres à un personnage canonique. | character_canon_version. |

## 22. Persistance et stratégie de stockage recommandée

La recommandation reste SQLite comme base canonique locale. Les documents Markdown, JSON et exports servent à la lisibilité et au transfert, mais ne remplacent pas la base active.

| Couche | Contenu | Rôle |

| --- | --- | --- |

| SQLite relationnel | Entités, relations, états, événements, versions et audits. | Source de vérité transactionnelle. |

| Journal append-only | Événements, interventions, appels et erreurs critiques. | Traçabilité et reconstruction. |

| JSON validé | Configurations, schémas d actions, profils exportés. | Portabilité et validation. |

| Markdown | Documents de projet, fiches lisibles, rapports du technicien. | Lecture humaine et contexte Bionic. |

| Snapshots | Copie cohérente de la base et métadonnées. | Retour arrière. |

| Cache reconstructible | Embeddings, index de recherche, résumés de contexte. | Performance; jamais seule copie. |

### 22.1 Transactions

- Une résolution applique tous ses changements dans une transaction ou n'en applique aucun.

- Les événements sont commis avant la création de perceptions et de notifications dérivées.

- Une notification Discord peut échouer sans annuler l'événement du monde.

- Une création de mémoire peut être reprise à partir de l'événement source si le processus est interrompu.

- Une intervention sensible crée le snapshot avant l'écriture et conserve un identifiant de retour arrière.

### 22.2 Sauvegarde et restauration

| Objet | Règle |

| --- | --- |

| Sauvegarde automatique | Périodique et avant toute migration ou intervention sensible. |

| Snapshot nommé | Créé à la demande ou automatiquement, avec description et version du schéma. |

| Restauration | Opération administrative confirmée; service en maintenance; journal distinct. |

| Vérification | Contrôle d intégrité, version du schéma, comptes d entités et dernier événement. |

| Rétention | Politique à définir dans la Partie V; au moins plusieurs points récents et un historique hebdomadaire au départ. |

## 23. Dictionnaire des entités du prototype

Le tableau suivant constitue la liste logique minimale. Une IA architecte peut regrouper certaines entités dans des tables ou les séparer davantage, mais elle ne doit pas supprimer leur distinction sémantique.

| Entité | Rôle | Nature | Statut |

| --- | --- | --- | --- |

| world | Racine du vivarium et état global. | CANONIQUE | MVP |

| actor | Référence commune pour personnages, propriétaire et contacts. | CANONIQUE | MVP |

| character | Identité persistante d une habitante. | CANONIQUE / PROTÉGÉ | MVP |

| character_canon_rule | Éléments figés, bornés, souples ou libres. | PROTÉGÉ | MVP pour personnages canoniques |

| trait_definition | Définition d une dimension de personnalité. | CONFIGURATION | MVP |

| character_trait | Valeur, centralité et plasticité d un trait. | SUBJECTIF STRUCTURÉ | MVP |

| value_interest_preference | Valeurs, intérêts, préférences et limites. | SUBJECTIF / PROTÉGÉ selon champ | MVP |

| need_state | Besoins physiques et psychologiques courants. | SUBJECTIF CACHÉ | MVP |

| emotion_episode | Réaction émotionnelle courte. | SUBJECTIF CACHÉ | MVP simplifié |

| mood_state | État affectif lent. | SUBJECTIF CACHÉ | MVP |

| goal | But personnel. | SUBJECTIF | MVP |

| project | Activité persistante avec progression. | CANONIQUE + SUBJECTIF | MVP |

| schedule_entry | Engagement ou bloc de plan. | CANONIQUE | MVP |

| relationship | Lien dirigé entre deux acteurs. | SUBJECTIF CACHÉ | MVP |

| relationship_change | Delta justifié lié à un événement. | JOURNALISÉ | MVP |

| location | Lieu détaillé ou abstrait. | CANONIQUE | MVP |

| location_link | Connexion et durée de déplacement. | CANONIQUE | MVP |

| object | Objet existant et état. | CANONIQUE | MVP |

| action_intent | Action proposée. | SUBJECTIF / TEMPORAIRE | MVP |

| validation_result | Résultat des règles avant action. | TECHNIQUE | MVP |

| action_resolution | Conséquences structurées validées. | CANONIQUE | MVP |

| scene | Cadre temporel, spatial et social. | CANONIQUE | MVP |

| conversation / utterance | Tours de parole et texte prononcé. | CANONIQUE pour les paroles | MVP |

| canonical_event | Fait ou changement officiel. | CANONIQUE / IMMUABLE | MVP |

| perception | Partie d un événement accessible à un personnage. | SUBJECTIF | MVP |

| belief / knowledge_claim | Proposition crue ou connue. | SUBJECTIF | MVP |

| memory | Souvenir récupérable et versionné. | SUBJECTIF | MVP |

| external_destination | Destination légère du monde extérieur. | CANONIQUE | MVP |

| external_contact | Acteur léger extérieur. | CANONIQUE | MVP |

| outing / condensed_activity | Sortie et résultat condensé. | CANONIQUE | MVP |

| injury | Blessure, limites et récupération. | CANONIQUE + SUBJECTIF | MVP |

| owner_presence | Manifestation du propriétaire dans une scène. | CANONIQUE | MVP |

| admin_intervention | Demande, analyse, confirmation et application. | ADMIN / JOURNALISÉ | MVP |

| approval | Confirmation explicite. | ADMIN / PROTÉGÉ | MVP |

| user_toggle | Préférences d affichage et de notification. | CONFIGURATION | MVP |

| discord_identity_route | Mapping interface et webhooks. | INTERFACE | MVP |

| notification / digest | Présentation dérivée. | DÉRIVÉ | MVP |

| offline_gap / catchup_run | Rattrapage après arrêt. | TECHNIQUE / CANONIQUE | MVP |

| snapshot | Point de restauration cohérent. | TECHNIQUE / PROTÉGÉ | MVP |

| audit_log | Historique des opérations sensibles. | IMMUABLE | MVP |

| llm_call_record | Usage, modèle, coût, validation et erreurs. | TECHNIQUE SENSIBLE | MVP |

| technician_report | Diagnostic et recommandation. | TECHNIQUE | MVP |

| embedding_index | Index sémantique reconstructible. | DÉRIVÉ | DIFFÉRÉ ou optionnel |

## 24. Modèle relationnel conceptuel

| world |-- actors | |-- characters -- traits / needs / goals / memories | |-- owner_actor | `-- external_contacts |-- locations -- objects |-- relationships (actor -> actor) |-- scenes -- conversations -- utterances |-- actions -- resolutions -- canonical_events | |-- perceptions -- beliefs / memories |-- outings / catchup_runs |-- admin_interventions -- approvals -- snapshots `-- settings / discord_routes / audit_logs |

| --- |

### 24.1 Cardinalités importantes

| Relation | Cardinalité logique | Règle |

| --- | --- | --- |

| World -> Character | 1 à plusieurs | Quatre personnages actifs dans le MVP. |

| Character -> Need state | 1 à plusieurs | Un état courant par type de besoin et historique optionnel. |

| Actor -> Relationship -> Actor | Plusieurs à plusieurs, dirigé | Une ligne distincte pour chaque direction. |

| Scene -> Participant | Plusieurs à plusieurs | Rôle, entrée, sortie et visibilité. |

| Event -> Perception | 1 à 0..n | Une perception par personnage et version si réinterprétation. |

| Perception/Event -> Memory | Plusieurs à plusieurs | Un souvenir peut résumer plusieurs sources. |

| Admin intervention -> Approval | 0 ou 1 actif | Obligatoire selon risque; une nouvelle proposition invalide l ancienne approbation. |

| Snapshot -> World version | Plusieurs à 1 | Chaque snapshot correspond à un état et schéma précis. |

## 25. Règles d intégrité et invariants

| ID | Invariant |

| --- | --- |

| INV-001 | Un seul monde actif est chargé par instance du service dans le MVP. |

| INV-002 | Chaque personnage actif est explicitement adulte. |

| INV-003 | Un personnage ne possède qu une position canonique active à un moment donné. |

| INV-004 | Un objet ne possède qu un emplacement ou détenteur canonique actif. |

| INV-005 | Aucun événement canonique ne peut être créé directement à partir de texte non validé. |

| INV-006 | Toute mémoire non introspective doit référencer au moins une source. |

| INV-007 | Une perception ne contient aucune donnée inaccessible selon les règles de visibilité. |

| INV-008 | Les relations sont dirigées; aucune symétrie n est imposée. |

| INV-009 | Les statistiques cachées ne sont pas exposées dans le contexte d un autre personnage. |

| INV-010 | Un changement important de personnalité est borné, justifié et historisé. |

| INV-011 | Une modification directe d un personnage requiert impact_analysis, approval et snapshot. |

| INV-012 | Un élément canonique figé ne peut pas dériver par une mise à jour autonome. |

| INV-013 | Le départ définitif ne peut pas passer de requested à archived sans décision du propriétaire. |

| INV-014 | Les scènes privées continuent indépendamment du toggle de présentation. |

| INV-015 | Aucune clé API ou secret technique n est stocké dans une mémoire, un prompt journalisé ou un message Discord. |

| INV-016 | Une transaction échouée ne laisse pas d état partiellement appliqué. |

| INV-017 | Un retry ne peut pas dupliquer une action grâce à la clé d idempotence. |

| INV-018 | Une restauration ou migration s exécute en mode maintenance. |

| INV-019 | Les résumés dérivés peuvent être supprimés et reconstruits depuis leurs sources. |

| INV-020 | Une notification échouée ne modifie pas l histoire canonique. |

| INV-021 | Les conversations interrompues sont clôturées sans inventer la suite. |

| INV-022 | Le modèle du MVP ne crée ni vieillissement, maladie, grossesse ni mort; seule la blessure est supportée. |

| INV-023 | Toute correction canonique conserve l enregistrement remplacé et le lien de rectification. |

| INV-024 | Les opérations administratives et techniques restent séparées des souvenirs des personnages sauf manifestation explicite. |

| INV-025 | Le cache et les embeddings ne sont jamais l unique copie d une information. |

## 26. Cycle de vie des données

| Catégorie | Création | Mise à jour | Fin de vie |

| --- | --- | --- | --- |

| Fait canonique | Transaction moteur ou intervention validée. | Rectification par nouvel événement; pas d écrasement silencieux. | Archivé; conservé selon rétention. |

| État courant | Calcul ou résolution. | Remplacé avec historique ou delta selon importance. | Anciennes versions compactées. |

| Perception | Distribution d un événement. | Peut être enrichie par réinterprétation, versionnée. | Archive subjective. |

| Croyance | Inférence ou information reçue. | Confiance et statut changent avec preuves. | Superseded, rejected ou archived. |

| Mémoire | Sélection et consolidation. | Rappel, réinterprétation, oubli, correction. | Faded ou archived; suppression admin auditée. |

| Configuration | Installation ou changement approuvé. | Nouvelle version. | Ancienne version conservée pour replay. |

| Donnée dérivée | Calcul depuis sources. | Régénérée. | Peut être purgée. |

| Secret technique | Configuration sécurisée externe à la base narrative. | Rotation. | Révocation et suppression sécurisée. |

### 26.1 Politique de suppression

- La suppression utilisateur doit distinguer masquer, archiver, anonymiser et détruire.

- Les données techniques sensibles peuvent nécessiter une rétention plus courte que l'histoire du monde.

- Les souvenirs modifiés administrativement peuvent être retirés du contexte du personnage tout en restant dans l'audit protégé.

- Un personnage archivé n'est pas effacé par défaut; ses relations et événements historiques restent référentiels.

- Une politique précise de rétention sera fixée dans la Partie V et le manuel d'exploitation.

## 27. Sécurité, accès et visibilité des données

| Rôle | Lecture | Écriture |

| --- | --- | --- |

| Personnage via LLM | Contexte subjectif filtré : identité, états traduits, souvenirs récupérés, scène accessible. | Intentions, dialogues, interprétations proposées; jamais écriture directe. |

| Moteur | Toutes les données nécessaires aux règles. | Données canoniques et dérivées selon transactions. |

| Propriétaire ordinaire | Vues, résumés, conversations selon toggles. | Interactions et demandes. |

| Propriétaire administrateur | Toutes les données narratives et audits, sauf secrets affichés en clair. | Interventions confirmées, réglages, restauration. |

| Technicien MVP | Journaux, métriques, schémas et données nécessaires au diagnostic. | Rapports et propositions seulement. |

| Discord | Contenu explicitement publié. | Messages entrants et accusés de livraison. |

| Fournisseur LLM | Uniquement le contexte construit pour l appel. | Réponse structurée ou texte, soumis à validation. |

### 27.1 Minimisation du contexte

- Ne transmettre que les souvenirs et états pertinents à la décision actuelle.

- Retirer les identifiants techniques, secrets, logs et informations privées d'autres personnages.

- Envoyer des descriptions comportementales plutôt que des jauges brutes lorsque possible.

- Conserver localement les prompts et sorties selon une politique de diagnostic configurable.

- Étiqueter toute donnée provenant du Web ou d'une source externe comme non fiable avant qu'elle puisse influencer une action.

## 28. Exemples de flux de données

### 28.1 Apparition d un piano

1. Le propriétaire crée une admin_intervention ciblant le salon et un nouvel objet piano.

1. Le système présente la portée. Comme l'objet ne modifie pas directement un personnage, la confirmation peut être simple selon la configuration.

1. Une transaction crée object, admin_effect event et origin_event_id.

1. Le mode effects_only n'annonce pas l'origine.

1. Les personnages présents reçoivent une perception; les absentes n'en reçoivent aucune.

1. Une habitante peut former la croyance que le propriétaire est responsable, avec une confiance inférieure à 100.

1. Le message Discord est une notification dérivée de l'événement.

### 28.2 Dispute privée entre deux habitantes

1. Une scène privée est ouverte dans une chambre avec deux participantes.

1. Les paroles sont canoniques comme actes de langage; leurs affirmations ne sont pas automatiquement vraies.

1. La résolution crée des impacts relationnels bornés et des émotions liées aux événements.

1. Chaque participante reçoit une perception et une interprétation distinctes.

1. Le toggle hidden empêche l'affichage en direct, sans interrompre la scène.

1. Un résumé privé peut être créé pour inspection administrative; le résumé quotidien ordinaire n'expose pas les détails intimes.

### 28.3 Modification d un trait

1. Le propriétaire demande de rendre un personnage beaucoup plus extraverti.

1. Le système localise les traits, habitudes, besoin social, besoin de solitude et règles de canon dépendantes.

1. Une impact_analysis décrit les comportements susceptibles de changer.

1. Un snapshot est créé et l'intervention attend une confirmation.

1. Après approbation, une nouvelle version de character_trait est créée; l'ancienne reste historisée.

1. Selon perceptibility_mode, le personnage peut ignorer l'origine, percevoir un changement ou recevoir une explication canonique.

## 29. Modèle minimal à implanter dans le MVP

La première implémentation ne doit pas construire toutes les extensions possibles. Elle doit toutefois préserver les frontières conceptuelles afin de ne pas enfermer le projet dans un historique de conversation plat.

| Bloc | Obligatoire dès la première version | Peut être simplifié |

| --- | --- | --- |

| Monde et temps | world, horloge, statuts, offline_gap, catchup_run. | Un seul monde et un seul fuseau affiché. |

| Personnages | actor, character, canon, traits, besoins, objectifs. | Nombre limité de traits et besoins. |

| Relations | Relations dirigées et deltas justifiés. | Dimensions initiales fixes. |

| Espace | Lieux, connexions, positions et objets. | Pas de géométrie ni carte. |

| Actions | Intentions, validation, résolution, idempotence. | Catalogue réduit. |

| Histoire | Événements canoniques, scènes, conversations. | Types d événements limités. |

| Subjectivité | Perceptions, croyances et souvenirs avec sources. | Consolidation simple au départ. |

| Administration | Interventions, impacts, confirmations, snapshots. | Interface Discord textuelle. |

| Interface | Identités Discord, routes, toggles et notifications. | Pas de tableau de bord Web. |

| Technique | Audit, appels LLM, technicien en lecture seule. | Métriques de base. |

### 29.1 Éléments différés

- Embeddings sophistiqués et moteur vectoriel externe.

- Institutions, économie, ville complète et population massive.

- Modèle local actif, routage multi-modèles avancé et exécution sur ordinateur dédié.

- Apprentissage procédural détaillé et simulation physique.

- Interface Web riche, carte relationnelle et éditeur visuel.

- Agent technicien autorisé à modifier automatiquement une branche de développement.

## 30. Tests d acceptation du modèle de données

| ID | Critère |

| --- | --- |

| AD-01 | Créer un monde, quatre personnages, les lieux obligatoires et recharger le tout sans perte ni duplication. |

| AD-02 | Empêcher un personnage ou objet d être simultanément dans deux lieux exclusifs. |

| AD-03 | Créer un événement ambigu et produire deux perceptions et croyances différentes sans dupliquer la vérité canonique. |

| AD-04 | Vérifier qu un personnage ne reçoit pas le souvenir privé d un autre dans son contexte LLM. |

| AD-05 | Rejouer une requête après panne et prouver que la clé d idempotence empêche une seconde application. |

| AD-06 | Modifier un trait protégé : aucune écriture avant impact, snapshot et confirmation. |

| AD-07 | Corriger un souvenir en conservant version précédente, audit et dépendances. |

| AD-08 | Désactiver l affichage d une scène privée sans changer ses événements ni effets. |

| AD-09 | Échouer une publication Discord tout en conservant l événement du monde et une notification retryable. |

| AD-10 | Fermer brutalement une scène puis redémarrer : statut interrupted, clôture automatique et aucun dialogue inventé. |

| AD-11 | Rattraper 24 heures hors ligne avec activités condensées, heures cohérentes et nombre borné d appels LLM. |

| AD-12 | Créer une croyance fausse puis la contester avec une preuve sans réécrire l événement source. |

| AD-13 | Tester un personnage canonique : une évolution autonome ne dépasse pas une borne figée. |

| AD-14 | Restaurer un snapshot en maintenance et vérifier l intégrité des références. |

| AD-15 | Supprimer un cache ou index dérivé et le reconstruire sans perte narrative. |

| AD-16 | Exporter une fiche lisible puis la réimporter dans un monde de test avec validation de version. |

| AD-17 | Vérifier que toutes les habitantes ont adult_status protégé et qu aucune entité interdite de cycle de vie n est créée. |

| AD-18 | Demander un départ définitif : statut departure_requested sans archivage automatique. |

| AD-19 | Vérifier que le technicien peut produire un rapport sans écrire dans les données actives. |

| AD-20 | Changer de profil de modèle et confirmer que les données canoniques ne dépendent pas du format propriétaire du fournisseur. |

## 31. Décisions encore ouvertes mais non bloquantes

| Décision | Moment recommandé |

| --- | --- |

| Échelle numérique exacte et seuils de chaque besoin, trait et relation. | Pendant les prototypes déterministes et tests de crédibilité. |

| Fréquence de conservation détaillée des historiques de besoins. | Avant simulation continue prolongée. |

| Politique de rétention des prompts, sorties LLM et journaux techniques. | Avant choix du fournisseur et premier usage réel. |

| Moteur de recherche sémantique : SQLite FTS, embeddings locaux ou service externe. | Après validation de la mémoire sans index avancé. |

| Structure exacte des préférences intimes et niveau de détail conservé. | Lors de la bible des personnages et des tests de confidentialité. |

| Format d export/import des personnages canoniques. | Avant création du casting définitif. |

| Politique de suppression définitive et anonymisation. | Avant diffusion à un autre utilisateur ou sauvegarde infonuagique. |

| Durée et nombre de snapshots conservés. | Dans la Partie V et le manuel d exploitation. |

| Possibilité de plusieurs mondes ou branches narratives. | Après stabilité du MVP. |

## Annexe A - Valeurs d énumération recommandées

| Domaine | Valeurs initiales |

| --- | --- |

| simulation_status | running, paused, degraded, maintenance, stopped |

| character_status | active, dormant, unavailable, departure_requested, archived |

| scene_status | open, paused, interrupted, closed, aborted, archived |

| privacy_level | public, shared, private, intimate, admin, technical_secret |

| perceptibility_mode | imperceptible, effects_only, announced, manifested |

| intervention_status | draft, awaiting_confirmation, approved, applied, rejected, rolled_back, failed |

| memory_status | active, faded, disputed, superseded, archived |

| belief_status | active, questioned, rejected, superseded |

| project_status | proposed, active, waiting, blocked, completed, abandoned |

| event_status | committed, superseded, invalidated |

| injury_status | active, healing, healed, chronic |

| delivery_status | pending, sent, failed, retrying, suppressed |

## Annexe B - Gabarit de fiche de champ

| Rubrique | À documenter |

| --- | --- |

| Nom logique | Nom stable et compréhensible. |

| Entité propriétaire | Table ou objet logique auquel il appartient. |

| Définition | Ce que la donnée signifie et ce qu elle ne signifie pas. |

| Type / format | Texte, UUID, date, enum, nombre, structure. |

| Valeurs permises | Plage, enum, nullabilité et défaut. |

| Autorité | Qui peut créer ou modifier. |

| Visibilité | Qui peut lire et dans quel contexte. |

| Source / provenance | Comment la valeur est obtenue. |

| Règle d évolution | Delta, fréquence, validation et dépendances. |

| Rétention | Historique, archive, suppression et reconstruction. |

| Tests | Cas normaux, limites et erreurs. |

## Annexe C - Instruction de remise à une IA architecte

| Instruction recommandée Lire les Parties I à IV dans l'ordre. Ne pas coder immédiatement. Produire d'abord : 1) une carte des entités et cardinalités; 2) la liste des contradictions ou ambiguïtés; 3) un schéma SQLite proposé avec migrations; 4) les invariants traduits en contraintes et tests; 5) un plan d'implémentation minimal. Ne fusionner perception, croyance, mémoire et événement sous aucun prétexte sans justification approuvée. |

| --- |

## Annexe D - Passage à la Partie V

La Partie V devra transformer ce modèle en phases de construction et validation. Elle définira l'ordre des migrations, les tests automatisés, les jeux de données de démonstration, les critères de passage, les sauvegardes, la politique de rétention et la méthode de travail avec Bionic.

| Entrée de la Partie V | Résultat attendu |

| --- | --- |

| Entités MVP de la section 29 | Lots de développement et migrations numérotées. |

| Invariants de la section 25 | Tests unitaires, d intégration et de reprise. |

| Scénarios de la section 30 | Tests d acceptation reproductibles. |

| Décisions ouvertes de la section 31 | Points de calibration et critères pour les trancher. |

| Stratégie de stockage de la section 22 | Procédures de sauvegarde, restauration et audit. |

## Fin de la Partie IV

| État du dossier Les Parties I à IV définissent maintenant la vision, l'architecture générale, le comportement du prototype et le sens des données. Le prochain document est la Partie V - Plan de réalisation, tests et critères de validation. Après cette Partie V, une révision croisée et un dossier maître consolidé pourront être produits pour Bionic. |

| --- |