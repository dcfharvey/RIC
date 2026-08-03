> **SOURCE HISTORIQUE NON NORMATIVE.** En cas de différence, `docs/00_DOSSIER_MAITRE_IA.md` prévaut.

DOSSIER DE CONCEPTION - PARTIE V

Vivarium social artificiel

Plan de réalisation, de tests et de validation

__________________________________________________________________

Méthode de développement incrémentale, phases de livraison, critères d'acceptation,
assurance qualité, gestion des changements et consignes à l'IA programmeuse

Version 0.1 - août 2026

Statut : plan initial de réalisation - document vivant

Place dans le dossier : les Parties I à IV définissent le projet, son'architecture,
son comportement et ses données. La Partie V explique comment le construire et prouver qu'il fonctionne.

## 0. Comment utiliser ce document

La présente Partie V transforme les spécifications précédentes en un programme de travail contrôlé. Elle ne remplace ni la vision, ni l'architecture, ni les exigences fonctionnelles, ni le modèle de données. Elle établit l'ordre de réalisation, les preuves attendues à chaque étape et la manière de travailler avec une IA programmeuse sans lui laisser réinterpréter silencieusement le projet.

| Règle de priorité documentaire La Partie I fixe l'intention générale; la Partie II fixe l'architecture et les contraintes techniques; la Partie III fixe le comportement observable; la Partie IV fixe le sens des données; la Partie V fixe le processus de réalisation et de validation. En cas de contradiction, l'IA programmeuse doit suspendre la tâche concernée, citer les passages et demander une décision. |

| --- |

### 0.1 Lecteurs visés

- Le propriétaire du vivarium, qui approuve les comportements, priorités et changements importants.

- Toute IA programmeuse utilisée dans un environnement agentique de développement.

- Un développeur humain éventuel chargé de reprendre, auditer ou maintenir le projet.

- L'agent technicien du vivarium, lorsqu'il sera suffisamment mature pour analyser les diagnostics sans modifier le code de lui-même.

### 0.2 Statuts employés

| Statut | Signification |

| --- | --- |

| À FAIRE | Travail non commencé. |

| EN COURS | Travail commencé, mais non validé. |

| BLOQUÉ | Une décision, une dépendance ou une correction'est requise. |

| À RÉVISER | Résultat disponible, mais non'accepté. |

| VALIDÉ | Critères d'acceptation réussis et preuve conservée. |

| DIFFÉRÉ | Prévu plus tard; ne doit pas être implanté par anticipation. |

### 0.3 Principe de progression

| Une phase à la fois Aucune phase ne doit être considérée comme terminée parce que le code existe. Elle est terminée seulement lorsque ses tests automatiques, essais manuels, journaux et critères d'acceptation sont réussis, puis approuvés. Une nouvelle phase ne doit pas masquer une faiblesse de la précédente. |

| --- |

## 1. Objectifs du plan de réalisation

| ID | Objectif |

| --- | --- |

| RÉAL-001 | Construire le noyau le plus simple capable de satisfaire les exigences du prototype, sans ajouter de fonctions spéculatives. |

| RÉAL-002 | Rendre chaque étape observable, testable, réversible et compréhensible par un non-programmeur. |

| RÉAL-003 | Séparer le moteur déterministe, les données, les interfaces et les modèles de langage afin de permettre leur remplacement. |

| RÉAL-004 | Éviter qu'une IA programmeuse modifie plusieurs fondations en même temps ou réécrive l'architecture sans approbation. |

| RÉAL-005 | Conserver des preuves de fonctionnement : tests, journaux, rapports, snapshots et scénarios rejouables. |

| RÉAL-006 | Préparer le transfert futur vers un ordinateur dédié et l'ajout éventuel d'un modèle local, sans les implanter dans le MVP. |

| RÉAL-007 | Aboutir à un prototype utilisable sur l'ordinateur personnel du propriétaire, accessible par Discord et stable sur une simulation prolongée. |

## 2. Principes de développement non négociables

| ID | Principe | Conséquence pratique |

| --- | --- | --- |

| DEV-001 | Déterministe avant génératif | Le temps, les lieux, les transactions, les permissions et la persistance sont construits avant les décisions par LLM. |

| DEV-002 | Petit lot de travail | Une tâche doit produire un changement limité, vérifiable et réversible. |

| DEV-003 | Tests avec le code | Toute fonction durable arrive avec ses tests; les tests ne sont pas reportés à la fin. |

| DEV-004 | Données avant narration | L'événement canonique et ses effets sont enregistrés avant la formulation narrative. |

| DEV-005 | Aucune correction silencieuse | Une contradiction documentaire, une migration risquée ou une modification d'architecture exige un rapport et une approbation. |

| DEV-006 | Compatibilité remplaçable | Le fournisseur de modèle, Discord et le stockage sont derrière des interfaces claires. |

| DEV-007 | Retour arrière garanti | Toute version intégrée doit posséder un commit, une migration réversible ou une procédure de restauration. |

| DEV-008 | Observabilité par défaut | Les actions importantes laissent des journaux structurés et lisibles. |

| DEV-009 | Pas d'auto-amélioration en production | Le technicien peut diagnostiquer et proposer; il ne modifie pas le programme actif sans processus de développement. |

| DEV-010 | Portée explicite | Ce qui est hors périmètre d'une phase doit rester absent, même si cela semble facile à ajouter. |

## 3. Rôles et responsabilités

| Rôle | Responsabilités | Ne doit pas faire |

| --- | --- | --- |

| Propriétaire | Fixer les attentes; approuver les changements sensibles; tester l'expérience; décider des ambiguïtés; autoriser les versions. | Choisir seul les détails techniques lorsqu'une recommandation'argumentée peut être fournie. |

| IA programmeuse | Lire les documents; proposer un plan limité; modifier le dépôt; exécuter les tests; expliquer les résultats et les risques. | Inventer des exigences, ignorer un test, modifier plusieurs couches sans permission ou déclarer une tâche réussie sans preuve. |

| Moteur de tests | Exécuter les vérifications automatiques, scénarios rejouables et mesures de performance. | Modifier les données de production ou dépendre d'un modèle externe sans contrôle. |

| Agent technicien du vivarium | Lire les diagnostics, détecter des anomalies, produire des recommandations et rapports. | Éditer ou déployer le code actif dans le prototype initial. |

| Développeur humain éventuel | Auditer l'architecture, reprendre le dépôt, résoudre un blocage ou valider une décision importante. | Devoir reconstruire le sens du projet à partir du code seul. |

| Contexte initial L'environnement de développement prévu au départ est LM Studio Bionic sur l'ordinateur personnel du propriétaire. Cette information'est opérationnelle, non'architecturale : le dossier doit demeurer utilisable par n'importe quelle IA programmeuse et n'importe quel'environnement équivalent. |

| --- |

## 4. Organisation du dépôt et des livrables

Le projet doit être conservé dans un dépôt Git unique. Les documents, le code, les tests et les migrations doivent évoluer ensemble. Les noms exacts peuvent être ajustés par l'IA architecte, mais les responsabilités des dossiers doivent rester distinctes.

| vivarium-social/ ├── docs/ # dossier maître, décisions, rapports et guides ├── src/ # code de l'application │ ├── core/ # horloge, événements, règles et orchestration │ ├── domain/ # personnages, relations, mémoire et monde │ ├── adapters/ # modèles, Discord, stockage, notifications │ └── interfaces/ # commandes et points d'entrée ├── tests/ │ ├── unit/ │ ├── integration/ │ ├── acceptance/ │ └── fixtures/ ├── migrations/ # évolution versionnée de la base ├── config/ # paramètres non secrets et exemples ├── prompts/ # contrats et gabarits versionnés ├── scripts/ # installation, diagnostic, sauvegarde, restauration ├── var/ # données locales ignorées par Git ├── .env.example ├── README.md └── CHANGELOG.md |

| --- |

### 4.1 Livrables obligatoires à chaque phase

- Le code ou la configuration correspondant uniquement à la portée de la phase.

- Les tests automatiques associés et leur résultat complet.

- Un rapport bref indiquant les fichiers modifiés, les choix effectués, les limites et les risques restants.

- Une mise à jour de la documentation lorsque le comportement, les données ou l'architecture ont changé.

- Un commit Git identifiable et un point de restauration lorsqu'une donnée persistante peut être affectée.

## 5. Méthode de travail avec une IA programmeuse

Chaque lot suit le même cycle. L'objectif est de remplacer la confiance aveugle par des preuves reproductibles.

1. Lire les documents et les fichiers concernés sans modifier le dépôt.

1. Reformuler la tâche, ses limites, ses dépendances et ses critères d'acceptation.

1. Inspecter l'état actuel du code et exécuter les tests de référence.

1. Proposer un plan de changement limité et signaler toute contradiction.

1. Après approbation, implanter uniquement le lot convenu.

1. Exécuter les tests ciblés, puis la suite complète pertinente.

1. Présenter les différences, preuves, limites et éventuelles questions.

1. Créer le commit seulement lorsque le propriétaire accepte le résultat.

### 5.1 Première mission de l'IA programmeuse

| Audit avant code La première mission dans un dépôt nouveau est de lire les cinq parties, produire une matrice des exigences, relever contradictions, doublons et décisions ouvertes, puis proposer une architecture minimale et un plan de phases. Aucun code de simulation ne doit être écrit avant l'approbation de ce rapport. |

| --- |

### 5.2 Comportements interdits

- Créer plusieurs milliers de lignes avant d'avoir exécuté un premier test de démarrage.

- Remplacer une technologie ou un schéma de données parce qu'une autre option semble plus moderne, sans demande explicite.

- Masquer une erreur par une valeur par défaut, un bloc try/except général ou la désactivation d'un test.

- Ajouter une dépendance non nécessaire, non documentée ou non maintenue.

- Faire dépendre les tests d'un service payant lorsque des doubles de test peuvent suffire.

- Modifier les documents pour faire correspondre les spécifications au code après coup sans approbation.

- Déployer une migration irréversible sans sauvegarde et répétition sur une copie.

## 6. Gestion des versions, branches et changements

| Élément | Règle recommandée |

| --- | --- |

| Branche principale | Toujours exécutable et validée; aucune expérimentation directe. |

| Branche de travail | Une branche par lot ou correction; nom descriptif et courte durée. |

| Commit | Petit, cohérent, accompagné de tests; message décrivant le résultat plutôt que l'activité. |

| Version | Versionnement sémantique du programme : majeur.mineur.correctif. |

| Tag | Créé pour chaque jalon validé et chaque version utilisable. |

| Changelog | Résumé lisible des fonctions, corrections, migrations et ruptures. |

| Migration | Numérotée, testée sur copie, journalisée et accompagnée d'une stratégie de retour. |

| Snapshot | Pris avant une modification de données, une migration ou une restauration risquée. |

### 6.1 Classification des changements

| Classe | Exemple | Approbation |

| --- | --- | --- |

| Mineur | Correction de texte, journal supplémentaire, test ajouté sans changement de comportement. | Rapport bref; validation normale. |

| Fonctionnel | Nouvelle action, changement de rythme, nouveau toggle Discord. | Critères d'acceptation et essai manuel. |

| Structurel | Nouveau composant, modification du modèle de données, nouvelle frontière d'autorité. | Proposition écrite, analyse d'impact, sauvegarde et approbation explicite. |

| Sensible | Modification des personnages, mémoire, confidentialité, contenu privé ou permissions. | Confirmation renforcée et scénario de restauration. |

## 7. Environnements et isolation sur un seul'ordinateur

Le développement initial et l'exécution du prototype auront lieu sur le même ordinateur personnel. Cela n'autorise pas le mélange des données. Trois environnements logiques doivent être séparés, même s'ils partagent la même machine.

| Environnement | Usage | Données |

| --- | --- | --- |

| Développement | Édition du code et essais rapides. | Base jetable ou fixtures. Jamais la seule copie du monde réel. |

| Test / préproduction | Répétition des migrations, scénarios prolongés et validations. | Copie anonymisée ou snapshot contrôlé. |

| Vivarium actif | Expérience personnelle courante. | Base officielle, sauvegardée, avec secrets et accès minimaux. |

- Chaque environnement possède son fichier de configuration, sa base et ses journaux.

- Les clés API et jetons Discord ne sont jamais commis dans Git.

- Le vivarium actif n'est pas utilisé comme banc d'essai pour une fonction nouvelle.

- Le programme doit pouvoir être mis en pause, sauvegardé et fermé proprement avant une mise à jour.

## 8. Portes de qualité et décisions de passage

| Porte | Condition minimale |

| --- | --- |

| G0 - Prêt à coder | Documents lus; matrice des exigences produite; contradictions bloquantes résolues; architecture minimale approuvée. |

| G1 - Lot implanté | Code limité à la portée; revue des différences; aucun fichier inattendu. |

| G2 - Tests réussis | Tests ciblés et suite de régression pertinents au vert; résultats conservés. |

| G3 - Données sûres | Migration répétée sur copie; sauvegarde et restauration démontrées. |

| G4 - Essai utilisateur | Scénario observable réussi par le propriétaire; comportement compréhensible. |

| G5 - Intégration | Documentation mise à jour; commit et changelog; aucun blocage critique. |

| G6 - Passage de phase | Tous les critères de la phase validés; risques connus consignés; décision explicite de poursuivre. |

| Interdiction de progression cosmétique Une interface agréable, un dialogue convaincant ou une démonstration réussie ne compense pas une persistance incertaine, une mémoire contaminée, une migration non testée ou l'absence de retour arrière. |

| --- |

## 9. Feuille de route du prototype

Les phases suivantes constituent l'ordre recommandé. Une phase peut être subdivisée, mais ne doit pas être fusionnée avec une phase ultérieure si cela réduit la capacité de tester séparément les fondations.

| Phase | Résultat principal | LLM | Discord |

| --- | --- | --- | --- |

| 0 | Dépôt, environnement, tests, documentation et scripts de base. | Non | Non |

| 1 | État canonique, SQLite, transactions, sauvegarde et restauration. | Non | Non |

| 2 | Horloge, résidence réaliste, lieux, objets et temps continu. | Non | Non |

| 3 | Quatre personnages déterministes, besoins détaillés et routines. | Non | Non |

| 4 | Actions, scènes, événements, perceptions simples et rejeu. | Non | Non |

| 5 | Adaptateur de modèle et intentions structurées contrôlées. | Oui | Non |

| 6 | Croyances, mémoire, oubli, consolidation et subjectivité. | Oui | Non |

| 7 | Relations, conversations autonomes et évolution sociale. | Oui | Non |

| 8 | Présence du propriétaire, pouvoirs, confirmations et audit. | Oui | Optionnel |

| 9 | Monde extérieur abstrait, absences et rattrapage hors ligne. | Oui | Non |

| 10 | Interface Discord complète et identités distinctes. | Oui | Oui |

| 11 | Technicien de diagnostic en lecture seule. | Oui | Oui |

| 12 | Simulation prolongée, réglage, sécurité et stabilisation MVP. | Oui | Oui |

## 10. Phases de réalisation détaillées

### 10.1 Phase 0 - Initialisation et audit du projet

| Rubrique | Contenu |

| --- | --- |

| Objectif | Créer un dépôt compréhensible, reproductible et prêt à être testé, sans fonction de simulation. |

| Inclut | Structure des dossiers; environnement Python; gestion des dépendances; configuration; journalisation de base; tests de démarrage; README; Git; script de diagnostic. |

| Exclut | Base métier, personnage, API de modèle, Discord et boucle autonome. |

| Preuves | Installation depuis un dossier vierge; commande de test unique; démarrage et arrêt propres; aucune clé secrète dans le dépôt. |

| Porte de sortie | Un'autre agent ou développeur peut cloner le dépôt, installer, exécuter les tests et comprendre où ajouter le code. |

### 10.2 Phase 1 - Persistance et vérité canonique

| Rubrique | Contenu |

| --- | --- |

| Objectif | Implanter l'état global, la version du schéma, les transactions et la persistance SQLite. |

| Inclut | Création de base; identifiants; timestamps; événements canoniques minimaux; journal d'audit; snapshots; restauration; migration initiale. |

| Exclut | Décision de personnage et texte généré. |

| Tests | Création, lecture, mise à jour transactionnelle, reprise après interruption simulée, double exécution idempotente, restauration bit à bit des entités critiques. |

| Porte de sortie | Le même état est retrouvé après redémarrage; une transaction incomplète ne laisse pas de monde partiellement modifié. |

### 10.3 Phase 2 - Temps, résidence et objets

| Rubrique | Contenu |

| --- | --- |

| Objectif | Faire exister un monde spatial cohérent et une horloge temps réel. |

| Inclut | Salon, cuisine, quatre chambres, salle de bain, cour; présence; déplacements validés; objets; pause; reprise; calendrier. |

| Exclut | Autonomie cognitive et monde extérieur détaillé. |

| Tests | Un seul lieu par personnage; déplacement impossible refusé; objet ajouté persiste; pause gèle l'avancement; redémarrage conserve l'heure et calcule l'écart. |

| Porte de sortie | Le monde peut avancer plusieurs heures sans contradiction de lieu, temps ou inventaire. |

### 10.4 Phase 3 - Personnages déterministes, besoins et routines

| Rubrique | Contenu |

| --- | --- |

| Objectif | Créer quatre personnages persistants qui vivent selon des règles simples sans LLM. |

| Inclut | Identité; traits; besoins détaillés; états temporaires; routines; repos; alimentation; hygiène; sociabilité; solitude; blessures simples. |

| Exclut | Dialogue libre, mémoire subjective et évolution complexe. |

| Tests | Besoins évoluent avec le temps; routine répond à un besoin; aucune jauge affichée dans l'interface ordinaire; comportement reproductible avec une graine fixe. |

| Porte de sortie | Une journée complète peut être simulée et expliquée par les données sans intervention du modèle. |

### 10.5 Phase 4 - Actions, scènes, événements et perceptions

| Rubrique | Contenu |

| --- | --- |

| Objectif | Implanter la chaîne intention -> validation -> résolution -> événement -> perception. |

| Inclut | Catalogue d'actions; conditions; résultats; scènes; participants; témoins; visibilité; journal canonique; rejeu. |

| Exclut | Interprétation complexe par LLM. |

| Tests | Une action impossible est refusée; un témoin'absent ne reçoit pas la perception; un événement rejoué ne double pas ses effets; une panne clôture la scène proprement. |

| Porte de sortie | La vérité du monde et l'accessibilité perceptive sont fiables avant tout langage généré. |

### 10.6 Phase 5 - Adaptateur de modèle et décisions structurées

| Rubrique | Contenu |

| --- | --- |

| Objectif | Permettre au modèle de proposer une intention sans lui céder l'autorité. |

| Inclut | Interface fournisseur; faux modèle de test; schéma JSON validé; délais; reprises; budgets; journal des appels; filtrage du contexte. |

| Exclut | Dépendance à un fournisseur unique et exécution libre de texte. |

| Tests | JSON invalide refusé ou réparé de façon contrôlée; timeout sans corruption; même contrat pour un faux fournisseur; action hors catalogue non exécutée; coût comptabilisé. |

| Porte de sortie | Changer de fournisseur ne modifie pas les règles du monde et une réponse défaillante laisse le système en état sûr. |

### 10.7 Phase 6 - Croyances, mémoire et oubli

| Rubrique | Contenu |

| --- | --- |

| Objectif | Donner à chaque personnage une histoire subjective durable et isolée. |

| Inclut | Perceptions interprétées; croyances avec confiance; souvenirs; importance; consolidation; oubli; provenance; inspection et modification'administrative. |

| Exclut | Recherche vectorielle complexe obligatoire. |

| Tests | Deux témoins conservent des versions différentes; un non-témoin ignore l'événement; un souvenir supprimé n'efface pas le canon; un résumé renvoie vers ses sources; oubli selon politique. |

| Porte de sortie | La mémoire influence les décisions sans contaminer la vérité ni devenir infinie. |

### 10.8 Phase 7 - Relations et conversations autonomes

| Rubrique | Contenu |

| --- | --- |

| Objectif | Produire une dynamique sociale crédible entre les quatre habitantes. |

| Inclut | Relations dirigées et multidimensionnelles; conversations; initiatives; projets; évolution graduelle; scènes privées; libido et préférences comme états internes pertinents. |

| Exclut | Obligation romantique, score de victoire et scénario imposé. |

| Tests | Conversation sans propriétaire; changement relationnel causé et borné; personnalités distinctes; possibilité de désaccord; confidentialité et toggle d'observation respectés. |

| Porte de sortie | Plusieurs jours simulés produisent des interactions variées, compréhensibles et non uniformes. |

### 10.9 Phase 8 - Propriétaire, pouvoirs et modifications protégées

| Rubrique | Contenu |

| --- | --- |

| Objectif | Permettre au propriétaire d'observer, d'interagir et de modifier le vivarium avec traçabilité. |

| Inclut | Présence supérieure connue; observation; interlocution; manifestations; ajout ou modification du monde; analyse d'impact; confirmation renforcée pour un personnage; snapshot; audit. |

| Exclut | Modification'automatique par le technicien. |

| Tests | Ajout perceptible selon les témoins; modification psychologique annulable; refus avant confirmation; personnage canonique protégé; intervention invisible non'attribuée automatiquement. |

| Porte de sortie | Le propriétaire peut exercer ses pouvoirs sans contourner le moteur ni perdre la provenance. |

### 10.10 Phase 9 - Monde extérieur et rattrapage hors ligne

| Rubrique | Contenu |

| --- | --- |

| Objectif | Donner une continuité hors de la résidence sans simuler une ville complète. |

| Inclut | Destinations abstraites; sorties; horaires; événements condensés; contacts simplifiés; retour; calcul d'absence; résumé; événement majeur. |

| Exclut | Population extérieure complète et départ définitif automatique. |

| Tests | Absence cohérente; rattrapage borné; aucun'appel par minute manquée; blessure possible mais rare et causale; demande de quitter l'aventure portée au propriétaire. |

| Porte de sortie | Une longue fermeture peut être résumée et appliquée sans explosion de coût ni saut narratif arbitraire. |

### 10.11 Phase 10 - Interface Discord

| Rubrique | Contenu |

| --- | --- |

| Objectif | Faire de Discord l'interface principale sans en faire la source de vérité. |

| Inclut | Bot principal; webhooks ou identité dynamique; avatars; messages directs; scènes; résumés; alertes; commandes; toggles; permissions; reprise de connexion. |

| Exclut | Interface graphique de jeu et panneau Web complet. |

| Tests | Chaque personnage publie avec son identité; toggle coupe les contacts spontanés; scène privée visible ou résumée selon option; doublon Discord ne double pas l'action; panne Discord n'arrête pas le monde. |

| Porte de sortie | Le propriétaire peut utiliser les fonctions principales depuis Discord avec un historique compréhensible. |

### 10.12 Phase 11 - Technicien de diagnostic

| Rubrique | Contenu |

| --- | --- |

| Objectif | Ajouter une entité capable d'analyser le système en lecture seule. |

| Inclut | Accès aux journaux et métriques; détection d'anomalies; rapports; propositions; demandes d'information; diagnostic de coût et répétition. |

| Exclut | Édition du code, déploiement, migration ou correction'automatique. |

| Tests | Tentative d'écriture refusée; rapport cite les preuves; diagnostic ne reçoit pas les données privées inutiles; absence d'hallucination présentée comme fait. |

| Porte de sortie | Le technicien'aide réellement à comprendre un problème sans pouvoir modifier le système. |

### 10.13 Phase 12 - Simulation prolongée et stabilisation

| Rubrique | Contenu |

| --- | --- |

| Objectif | Démontrer que le prototype reste cohérent, abordable et récupérable sur une durée significative. |

| Inclut | Essais accélérés; fonctionnement réel; régressions; réglage des cadences; métriques; sécurité; sauvegarde; restauration; documentation d'exploitation. |

| Exclut | Nouvelles grandes fonctions non nécessaires au MVP. |

| Tests | Voir sections 11 à 18; au moins une simulation prolongée sur copie et une période réelle sur le vivarium actif. |

| Porte de sortie | Critères de la définition du MVP réussis, risques critiques fermés et procédure quotidienne utilisable par le propriétaire. |

## 11. Stratégie générale de tests

| Niveau | But | Exemple |

| --- | --- | --- |

| Unitaire | Vérifier une règle isolée rapidement. | Décroissance d'un besoin, borne d'une relation, validation d'une action. |

| Intégration | Vérifier plusieurs composants ensemble. | Transaction SQLite + événement + perception. |

| Contrat | Garantir une interface stable. | Même schéma d'intention pour deux fournisseurs de modèle. |

| Acceptation | Prouver une exigence observable de la Partie III. | AF-04 : apparition d'un objet perceptible. |

| Régression | Empêcher le retour d'un défaut corrigé. | Un souvenir privé n'est jamais envoyé au mauvais personnage. |

| Simulation | Observer le système sur des centaines ou milliers de cycles. | Diversité des activités et absence de boucle. |

| Sécurité | Tester permissions, secrets et données non fiables. | Injection dans un message Discord ne devient pas une commande. |

| Manuel | Évaluer l'expérience et la lisibilité pour le propriétaire. | Les statistiques cachées sont perceptibles sans être affichées. |

### 11.1 Tests déterministes et modèles de remplacement

- Les règles classiques doivent être testables avec une graine aléatoire fixe.

- Un faux fournisseur de LLM doit retourner des réponses prédéfinies, invalides, lentes ou contradictoires.

- Les tests automatiques ordinaires ne doivent pas consommer de jetons payants.

- Les tests nécessitant un vrai modèle sont identifiés séparément, plafonnés et exécutés volontairement.

- Les scénarios importants possèdent un état initial figé et un résultat attendu structurel, sans exiger mot pour mot le même dialogue.

### 11.2 Tolérance au caractère probabiliste

Un test ne doit pas échouer parce qu'un modèle emploie une autre phrase. Il doit vérifier les propriétés observables : action'autorisée, respect des connaissances, cohérence de la personnalité, absence de fuite privée, format valide, limites respectées et effet canonique correct.

## 12. Matrice d'acceptation du prototype

Les scénarios AF-01 à AF-15 définis dans la Partie III doivent être automatisés autant que possible et complétés par un essai manuel. La matrice ci-dessous indique le principal jalon où chacun devient obligatoire.

| Scénario | Phase cible | Preuve principale |

| --- | --- | --- |

| AF-01 - Persistance après redémarrage | 1 | État identique après arrêt et reprise. |

| AF-02 - Conversation'autonome | 7 | Scène créée sans commande du propriétaire. |

| AF-03 - Perceptions différentes | 4 / 6 | Témoins et croyances distincts. |

| AF-04 - Ajout d'objet perceptible | 8 | Objet canonique, témoins corrects et audit. |

| AF-05 - Modification psychologique protégée | 8 | Analyse, confirmation, snapshot et restauration. |

| AF-06 - Évolution relationnelle graduelle | 7 | Historique causal et bornes respectées. |

| AF-07 - Monde extérieur abstrait | 9 | Sortie, condensation et retour cohérents. |

| AF-08 - Contact spontané toggle | 10 | Activation et désactivation sans perdre l'autonomie interne. |

| AF-09 - Scène privée et visibilité | 7 / 10 | Confidentialité interne distincte de l'affichage. |

| AF-10 - Contenu adulte émergent | 7 | Émergence cohérente, mémoire et confidentialité, sans obligation. |

| AF-11 - Panne de l'API | 5 | Mode sûr, aucun état partiel et reprise. |

| AF-12 - Rattrapage hors ligne | 9 | Calcul condensé, budget borné et résumé. |

| AF-13 - Demande de départ | 9 | Aucun départ automatique; événement transmis au propriétaire. |

| AF-14 - Personnage canonique | 3 / 8 | Verrous de canon respectés et changement approuvé. |

| AF-15 - Technicien en lecture seule | 11 | Écriture impossible et rapport fondé sur les journaux. |

### 12.1 Tests du modèle de données

Les vingt tests d'acceptation de la Partie IV sont également obligatoires. Ils doivent être rattachés à des tests exécutables ou, lorsqu'ils restent manuels, à une procédure reproductible. Aucun scénario fonctionnel ne doit contourner un invariant de données pour paraître réussi.

## 13. Scénarios de simulation prolongée

| Essai | Durée / volume | But |

| --- | --- | --- |

| Fumée | 100 cycles déterministes | Détecter les erreurs immédiates et fuites de ressources. |

| Journée accélérée | 24 heures simulées | Vérifier besoins, routines, interactions et sommeil. |

| Semaine accélérée | 7 jours simulés | Observer répétition, relations et mémoire. |

| Mois accéléré sur copie | 30 jours simulés | Tester consolidation, oubli, coût et croissance de la base. |

| Coupure brutale | À plusieurs étapes critiques | Prouver transactions, clôture de scène et reprise. |

| Absence prolongée | 24 h à 14 jours hors ligne | Valider le rattrapage condensé. |

| Usage réel | Au moins 7 jours calendaires | Évaluer Discord, rythme, notifications et charge sur le PC. |

- Les essais accélérés sont réalisés sur une copie, jamais sur le seul monde actif.

- Les résultats doivent inclure statistiques, anomalies, exemples d'événements et évolution de la taille de la base.

- Un essai peut être déclaré non concluant si la configuration du modèle a changé pendant son exécution.

## 14. Mesures et observabilité

| Catégorie | Mesures minimales |

| --- | --- |

| Fiabilité | Erreurs par cycle; actions refusées; reprises; transactions annulées; incidents de données. |

| Activité | Actions par personnage; temps inactif; projets; conversations; événements significatifs. |

| Diversité | Répartition des activités; répétition de formulations; concentration des interactions; isolement. |

| Mémoire | Souvenirs créés, consolidés, oubliés; taille moyenne du contexte; sources par résumé. |

| Relations | Amplitude et vitesse des changements; conflits; réconciliations; asymétries. |

| LLM | Appels; jetons; coût; latence; échecs de format; fournisseurs utilisés. |

| Système | CPU, mémoire, disque, durée des cycles, taille de la base et des journaux. |

| Discord | Messages envoyés; erreurs; délais; doublons évités; toggles actifs. |

| Sécurité | Actions bloquées; accès refusés; données privées filtrées; tentatives d'injection. |

| Les métriques ne sont pas le jeu Les mesures servent à diagnostiquer la simulation. Elles ne doivent pas transformer les relations en tableau de progression visible ni remplacer l'observation des comportements, conformément à la Partie III. |

| --- |

## 15. Performance, coût et charge sur l'ordinateur personnel

Le prototype utilise une API distante au départ. Le coût principal est donc le nombre d'appels, la taille du contexte et la fréquence des décisions, plutôt que le rendu graphique. Le programme local doit toutefois rester discret pendant l'usage normal du PC.

| Contrôle | Exigence initiale |

| --- | --- |

| Planification | Aucun réveil permanent à haute fréquence; événements et temporisateurs regroupés. |

| CPU / mémoire | Mesurés pendant les essais; absence de croissance continue non expliquée. |

| Disque | Rotation des journaux et politique de conservation; sauvegardes compressées. |

| API | Compteur par fournisseur, personnage, fonction et journée. |

| Budget | Configurable même si aucune limite financière n'est fixée au départ; alerte avant blocage. |

| Contexte | Récupération sélective; pas d'envoi automatique de tout l'historique. |

| Dégradation | En cas de forte latence, routines déterministes continuent et décisions cognitives sont différées. |

### 15.1 Tests de performance minimaux

- Mesurer un cycle sans appel au modèle et un cycle avec appel.

- Mesurer le redémarrage avec une base vide, puis avec un mois simulé.

- Vérifier que le rattrapage n'effectue pas un'appel par minute absente.

- Vérifier que les journaux et souvenirs ne croissent pas sans politique de consolidation.

- Établir une ligne de base avant toute optimisation.

## 16. Sécurité, confidentialité et tests adversariaux

| Risque | Test requis |

| --- | --- |

| Injection dans Discord | Un message contenant de fausses instructions système reste une donnée de conversation. |

| Fuite entre personnages | Un personnage ne reçoit pas une scène privée, pensée ou souvenir auquel il n'a pas accès. |

| Secret exposé | Clés et jetons absents des prompts, journaux ordinaires et commits. |

| Commande dangereuse | Le vivarium actif ne dispose pas d'un terminal général ou de privilèges administrateur. |

| Modification sensible | Un changement de personnage ne s'applique jamais avant analyse, confirmation et snapshot. |

| Données envoyées à l'API | Le contexte est inspectable et limité aux informations nécessaires. |

| Technicien'abusif | Toute tentative d'écriture, déploiement ou migration'est refusée et journalisée. |

| Restauration malveillante | Une sauvegarde est validée avant d'écraser l'état actif. |

### 16.1 Revue avant connexion à un service externe

- Lire les conditions et politiques du fournisseur au moment de l'implantation.

- Documenter les données qui peuvent quitter l'ordinateur.

- Vérifier les mécanismes de suppression, rétention et désactivation de l'entraînement lorsque disponibles.

- Prévoir un mode sans fournisseur ou un faux fournisseur pour les tests et pannes.

## 17. Gestion des erreurs, incidents et défauts

| Gravité | Définition | Réponse |

| --- | --- | --- |

| Critique | Corruption, fuite privée, action non'autorisée, perte de contrôle ou impossibilité de restaurer. | Mettre en pause, isoler, sauvegarder les preuves, restaurer si nécessaire; aucune nouvelle phase. |

| Élevée | Incohérence canonique, mémoire attribuée au mauvais personnage, boucle coûteuse ou panne récurrente. | Bloquer la fonction, créer un test de régression et corriger avant usage normal. |

| Moyenne | Comportement incohérent mais récupérable, notification erronée, répétition importante. | Consigner, prioriser, corriger dans un lot dédié. |

| Faible | Problème cosmétique, formulation ou confort sans effet sur les données. | Corriger lorsque pratique sans interrompre la feuille de route. |

### 17.1 Rapport de défaut minimal

- Version du programme, configuration et fournisseur de modèle.

- État initial ou snapshot permettant de reproduire.

- Actions observées et résultat attendu.

- Journaux, événements et identifiants concernés.

- Gravité, contournement éventuel et test à ajouter.

## 18. Gestion documentaire et contradictions

Les documents sont des composants du projet. Ils doivent être versionnés, relus et liés au code. Le dossier consolidé sera produit après la révision croisée des cinq parties.

| Situation | Action obligatoire |

| --- | --- |

| Deux documents se contredisent | Ne pas coder; produire une note citant les passages, l'impact et une recommandation. |

| Le code révèle une contrainte inconnue | Proposer une décision technique; ne pas réécrire la fonction demandée sans approbation. |

| Le propriétaire change d'avis | Créer une demande de changement et mettre à jour les parties touchées avant ou avec le code. |

| Une fonction'est différée | La marquer explicitement; ne pas laisser un comportement partiel ambigu. |

| Une exigence est remplacée | Conserver l'historique dans le changelog et identifier la nouvelle exigence. |

| Un terme change | Mettre à jour le glossaire et vérifier toutes les occurrences. |

### 18.1 Hiérarchie de précision

| Règle de lecture Pour une question d'intention, consulter la Partie I. Pour une frontière de composant, la Partie II. Pour un comportement observable, la Partie III. Pour la signification d'une donnée, la Partie IV. Pour l'ordre de construction et la preuve attendue, la Partie V. La date la plus récente ne suffit pas à elle seule à résoudre une contradiction. |

| --- |

## 19. Processus de demande de changement

1. Décrire le besoin en langage ordinaire et l'exemple qui motive le changement.

1. Identifier les exigences, données, phases et tests touchés.

1. Classer le changement : mineur, fonctionnel, structurel ou sensible.

1. Proposer au moins une solution recommandée, ses effets et ses alternatives.

1. Mettre à jour les documents concernés ou préparer les modifications ensemble avec le code.

1. Implanter sur une branche, tester sur une copie et présenter les différences.

1. Après approbation, intégrer, migrer, documenter et surveiller.

### 19.1 Règle spéciale pour les personnages canoniques

Toute modification d'un élément marqué comme canonique ou verrouillé doit expliciter : la caractéristique actuelle, la modification proposée, la justification dans l'univers du personnage, les effets probables sur la simulation et la possibilité de revenir à l'état précédent.

## 20. Définition de terminé

Une tâche ou une phase n'est pas terminée parce que l'IA programmeuse affirme qu'elle fonctionne. Les éléments suivants sont tous requis, sauf exclusion explicitement justifiée.

| Critère | Question de contrôle |

| --- | --- |

| Portée | Le travail correspond-il exactement au lot approuvé? |

| Code | Le code est-il lisible, typé ou validé, sans duplication majeure ni dépendance inutile? |

| Tests | Les tests ciblés et de régression réussissent-ils? |

| Données | Les invariants et migrations sont-ils protégés? |

| Erreurs | Les pannes prévues laissent-elles un état sûr? |

| Sécurité | Les permissions, secrets et données privées sont-ils respectés? |

| Documentation | Les décisions et comportements modifiés sont-ils à jour? |

| Preuve | Les commandes, résultats et scénarios sont-ils fournis? |

| Retour arrière | Peut-on'annuler ou restaurer? |

| Acceptation | Le propriétaire a-t-il observé le résultat attendu? |

## 21. Critères de livraison du MVP

| Domaine | Critère de livraison |

| --- | --- |

| Fonctionnement | Le vivarium démarre, tourne en continu, se met en pause, s'arrête et reprend sans perte. |

| Population | Quatre habitantes persistantes, distinctes et autonomes vivent dans la résidence définie. |

| Monde | Lieux, objets, temps, sorties et événements canoniques restent cohérents. |

| Psychologie | Besoins détaillés, états, relations, croyances et souvenirs influencent les comportements sans jauges ordinaires. |

| Social | Les habitantes initient des activités et conversations, y compris sans le propriétaire. |

| Propriétaire | Observation, interaction et pouvoirs administratifs fonctionnent avec confirmations et audit. |

| Discord | Identités distinctes, toggles, résumés, alertes et commandes principales sont utilisables. |

| Pannes | API ou Discord indisponible ne corrompt pas le monde; scènes interrompues sont clôturées. |

| Rattrapage | Une période hors ligne est condensée avec coût borné et conséquences justifiables. |

| Technicien | Diagnostic utile en lecture seule; aucune modification'automatique. |

| Qualité | AF-01 à AF-15 et tests critiques de la Partie IV réussissent. |

| Exploitation | Sauvegarde, restauration, mise à jour et consultation des journaux sont documentées. |

| Décision de livraison Le MVP peut être livré avec des limites connues si elles sont documentées, contournables et non critiques. Il ne peut pas être livré avec une corruption possible, une fuite de données, une autorité mal séparée ou une restauration non démontrée. |

| --- |

## 22. Mise en service et routine d'exploitation

### 22.1 Avant la première mise en service

- Créer la base officielle vide ou importer un état approuvé.

- Configurer les secrets hors du dépôt et vérifier leurs permissions.

- Exécuter toute la suite de tests et un essai de restauration.

- Vérifier les toggles Discord et la visibilité des scènes privées.

- Fixer les valeurs de cadence initiales, même si le budget financier reste ouvert.

- Prendre un snapshot initial et taguer la version.

### 22.2 Routine normale

| Fréquence | Action |

| --- | --- |

| À chaque démarrage | Diagnostic, version du schéma, espace disque, intégrité de la base et connexion'aux services. |

| Quotidien | Résumé du monde, coût, erreurs, backlog du technicien et sauvegarde incrémentale. |

| Hebdomadaire | Sauvegarde complète, test de restauration sur copie, revue des répétitions et croissance des données. |

| Avant mise à jour | Pause, snapshot, tests, migration sur copie, changelog et plan de retour. |

| Après mise à jour | Tests de fumée, scénarios critiques et surveillance renforcée. |

## 23. Évolution'après le MVP

Les extensions suivantes sont possibles, mais doivent rester différées jusqu'à la stabilisation du noyau. Elles ne doivent pas influencer l'architecture au point de compliquer inutilement le prototype.

| Extension | Précondition |

| --- | --- |

| Ordinateur dédié | Installation reproductible, sauvegardes portables et dépendances documentées. |

| Modèle local | Adaptateur stable, batterie de contrats et mesure comparative de qualité. |

| Tableau de bord Web | Besoin réel démontré pour inspecter des données que Discord présente mal. |

| Plus de personnages | Stabilité des quatre habitantes, coûts connus et mémoire scalable. |

| Monde extérieur détaillé | Rattrapage et abstraction déjà fiables; besoin narratif démontré. |

| Technicien capable de coder | Environnement isolé, dépôt de développement, tests, revue et approbation obligatoires. |

| Graphismes ou avatar | Aucun impact sur l'autorité du moteur et avantage clair pour l'expérience. |

| Multi-modèles spécialisés | Mesure montrant un bénéfice supérieur à la complexité ajoutée. |

## 24. Décisions encore ouvertes mais non bloquantes

| Décision | Moment recommandé |

| --- | --- |

| Langage et versions exactes des bibliothèques | Audit architectural avant la Phase 0. |

| Fournisseur initial de modèle | Juste avant la Phase 5, après comparaison'actuelle. |

| Budget quotidien et seuils d'alerte | Avant les premiers essais prolongés avec API réelle. |

| Cadence exacte des décisions cognitives | Réglage pendant les Phases 5 à 7. |

| Politique chiffrée d'oubli et de consolidation | Après les premiers essais de mémoire. |

| Noms, biographies et verrous des quatre personnages | Avant la Phase 3 ou pendant sa préparation. |

| Structure exacte des salons Discord | Avant la Phase 10. |

| Durée minimale de l'essai réel de stabilisation | Avant la Phase 12; recommandation initiale : au moins sept jours. |

## Annexe A - Fiche standard d'une phase

| Phase / lot : Objectif observable : Exigences couvertes : Données et composants touchés : Inclus : Explicitement exclu : Dépendances : Risques : Plan de modification : Tests automatiques : Essais manuels : Preuves attendues : Plan de retour arrière : Documents à mettre à jour : Décision : À faire / En cours / Bloqué / Validé |

| --- |

## Annexe B - Instruction générique à une IA programmeuse

| Lis d'abord tous les documents du dossier docs dans leur ordre numérique. Ne modifie aucun fichier avant d'avoir produit un rapport de compréhension. Dans ce rapport, résume l'architecture, dresse la matrice des exigences, signale les contradictions et propose le plus petit prochain lot testable. Ne réconcilie jamais silencieusement deux passages incompatibles. Après approbation du lot, inspecte le dépôt, exécute les tests de référence, puis modifie uniquement les fichiers nécessaires. Ajoute ou adapte les tests avec le code. N'ignore pas un test en échec. Présente les fichiers modifiés, les commandes exécutées, les résultats, les risques restants, le plan de retour arrière et les documents à mettre à jour. N'intègre pas de fonction différée et ne change pas l'architecture sans autorisation. |

| --- |

## Annexe C - Rapport de livraison d'un lot

| Lot : Résumé du résultat : Exigences satisfaites : Fichiers ajoutés ou modifiés : Choix techniques et justification : Commandes exécutées : Tests réussis : Tests non exécutés et raison : Limites ou risques restants : Migration / données touchées : Retour arrière : Documentation mise à jour : Décision demandée au propriétaire : |

| --- |

## Annexe D - Gabarit de demande de changement

| Titre du changement : Besoin ou problème observé : Exemple concret : Comportement actuel : Comportement souhaité : Exigences et données touchées : Classe : mineur / fonctionnel / structurel / sensible Solution recommandée : Alternatives : Risques et impacts : Tests d'acceptation : Migration et retour arrière : Documents à modifier : Approbation : |

| --- |

## Annexe E - Gabarit de rapport d'incident

| Date et heure : Version / commit : Environnement : Gravité : État initial / snapshot : Étapes de reproduction : Résultat observé : Résultat attendu : Personnages, événements et identifiants concernés : Journaux et captures : Mesure immédiate prise : Cause confirmée ou hypothèse : Correction proposée : Test de régression à ajouter : Statut : |

| --- |

## Annexe F - Checklist de remise à l'environnement de développement

- Les cinq parties sont présentes en formats lisibles et portent un numéro de version.

- Un index précise la hiérarchie documentaire et la règle de contradiction.

- Les décisions encore ouvertes sont isolées et ne bloquent pas la première phase.

- Le dépôt Git est initialisé et la branche principale est propre.

- Les secrets ne figurent pas dans les documents ni le dépôt.

- La première demande est un'audit, pas la construction complète du vivarium.

- Le lot suivant possède une portée, des exclusions, des tests et une décision de passage.

- Le propriétaire sait comment arrêter l'agent de développement et restaurer le dépôt.

## Annexe G - Passage au dossier consolidé

Après validation de cette Partie V, les cinq documents doivent faire l'objet d'une révision croisée. Les contradictions, doublons, termes divergents et décisions anciennes doivent être consignés dans un rapport. Une fois les arbitrages effectués, un dossier maître consolidé peut être produit pour lecture continue, accompagné des documents séparés comme sources versionnées.

| Étape suivante recommandée Ne pas remettre immédiatement l'ordre de construire tout le projet. La prochaine étape est un'audit croisé des Parties I à V, puis la création de l'index, de la matrice des exigences et du dossier consolidé destiné à l'IA programmeuse. |

| --- |

## Fin de la Partie V

La Partie V complète le dossier de conception initial. Elle définit une méthode de développement progressive, vérifiable et indépendante de l'outil. Les prochaines productions sont des documents de consolidation et de contrôle, non une nouvelle partie conceptuelle obligatoire.