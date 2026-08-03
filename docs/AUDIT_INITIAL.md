# AUDIT_INITIAL — Vivarium social artificiel

**Version :** 0.1
**Date :** 3 août 2026
**Auteur :** IA programmeuse (en session LM Studio Bionic)
**Statut :** rapport de compréhension et d’audit à soumettre pour approbation
**Source d’autorité :** `docs/00_DOSSIER_MAITRE_IA.md` v0.1 (fichier maître normatif)
**Périmètre :** aucun fichier métier ni structure du dépôt n’a été modifié. Le seul fichier créé est le présent audit, conformément à la section 0.2 et 12 du dossier maître.

---

## 1. Compréhension du projet

### 1.1 Produit

Le **vivarium social artificiel** est un bac à sable social **persistant, textuel et sans graphismes de jeu obligatoires**. Quatre personnages autonomes (tous explicitement adultes) vivent dans une résidence détaillée ; chacun possède une subjectivité, des besoins, des objectifs, des relations et une mémoire durable. Le propriétaire (humain) peut observer, interagir, se manifester et administrer comme une entité supérieure connue des personnages. Discord est la fenêtre principale d’interaction, mais la vérité du monde reste locale.

Le projet n’est ni un outil d’ingénierie sociale, ni un assistant productif, ni un jeu de conquête romantique : le contenu relationnel/adulte peut émerger naturellement, sans aucune garantie d’affection ou de disponibilité. L’intérêt central est la continuité d’un petit monde habité, ses relations émergentes et l’interaction du propriétaire.

### 1.2 Principes fondamentaux (frontières d’autorité)

Le principe central (4.1) structure tout le système : **« Le LLM propose, interprète et dialogue. Le moteur local conserve la vérité, applique les règles, valide les actions et décide ce qui devient canonique. »**

Quatre implications récurrentes dans le dossier maître :

1. Aucun texte généré ne devient un événement canonique sans validation (`INV-005`).
2. Discord n’est jamais la source de vérité ; les données canoniques restent locales (`NF-03`, 5.9).
3. Les interventions du propriétaire sont tracées, réversibles et, pour les modifications directes d’un personnage, soumises à un protocole renforcé (`DEC-009`, `INV-011`).
4. Le technicien est un agent de **diagnostic en lecture seule** dans le MVP (`DEC-022`, `AF-15`) — il ne modifie ni code, ni données actives, ni déploiement.

Les non-objectifs du MVP (1.2) bornent clairement le périmètre : aucun rendu 3D, pas de simulation urbaine, pas de conscience continue, pas d’accès système aux personnages, pas d’auto-modification, pas de vieillissement/maladie/grossesse/mort, pas de dépendance obligatoire à un fournisseur ou à un framework précis.

### 1.3 Expérience cible (1.1)

Les personnages agissent et se parlent sans sollicitation directe ; ils conservent des souvenirs divergents et peuvent se tromper ; les relations évoluent lentement à partir de causes observables ; le propriétaire peut intervenir sans que l’intervention soit automatiquement connue ; le monde continue dans le temps, reprend après arrêt et peut être restauré.

---

## 2. Architecture déduite

### 2.1 Décomposition en composants (4.2)

| Composant | Responsabilité | Interdiction principale |
| --- | --- | --- |
| Interface Discord | Messages, commandes, identités, toggles, notifications. | Modifier directement le monde. |
| Routeur | Identifier personnage, scène, mode du propriétaire et niveau d’autorité. | Inventer une conséquence. |
| Orchestrateur | Construire le contexte, appeler le modèle, contrôler cadence, budgets et reprise. | Contourner permissions/invariants. |
| Moteur canonique | Temps, lieux, actions, validations, transactions, conséquences, vérité. | Accepter un fait généré sans validation. |
| Couche cognitive | Perception subjective, mémoire récupérée, intention, dialogue, réflexion. | Écrire directement dans la base canonique. |
| Mémoire | Événements, perceptions, croyances, souvenirs, provenance, consolidation. | Fusionner croyance et fait. |
| Planificateur | Routines, échéances, rattrapage, consolidation, notifications. | Déclencher des appels non bornés. |
| Adaptateur de modèle | Contrat uniforme entre fournisseurs, validation de sortie, métriques. | Enfermer le métier dans une API propriétaire. |
| Persistance | SQLite, migrations, snapshots, audit, archives. | Cache/embeddings comme source unique. |
| Technicien | Diagnostic, métriques, preuves, recommandations. | Écrire, migrer ou déployer dans le MVP. |

### 2.2 Boucle d’exécution (4.3)

Charger l’état canonique et les échéances → mettre à jour besoins/routines déterministes → détecter les décisions nécessitant interprétation → construire un contexte subjectif minimal → obtenir une intention structurée du modèle → valider par le moteur → appliquer dans une transaction idempotente → créer l’événement canonique → distribuer les perceptions aux témoins autorisés → mettre à jour croyances/souvenirs/relations/journaux/notifications → continuer, résumer ou attendre.

Cette boucle fait du moteur canonique le seul point d’écriture de la vérité et rend chaque étape transactionnelle et réversible.

### 2.3 Niveaux de détail (4.4)

- **0 — déterministe** : calcul local uniquement (dormir, trajet habituel, baisse d’énergie).
- **1 — condensé** : résumé d’une période sans scène détaillée (journée extérieure ordinaire).
- **2 — décision** : appel court pour une intention/interprétation (accepter une invitation).
- **3 — scène** : dialogue multi-tours et conséquences détaillées (dispute, rapprochement).
- **4 — réflexion** : consolidation autobiographique et révision de projets.

Ces niveaux conditionnent directement la cadence des appels au modèle (OD-004) et la maîtrise du coût/charge (NF-07, NF-11).

### 2.4 Modèle de données (6.1)

Le dossier spécifie des entités logiques minimales réparties en statuts : MVP, MVP protégé, MVP caché, MVP subjectif, MVP dérivé, MVP technique et différé (embedding_index). Points structurants :

- Un monde racine possède exactement quatre personnages actifs (`DEC-001`).
- Actor est la référence commune (personnages, propriétaire, contacts extérieurs).
- Les relations sont dirigées, plusieurs-à-plusieurs (`INV-008`).
- La chaîne mémoire obligatoire est : **événement canonique → perception → interprétation → croyance éventuelle → souvenir consolidé** (5.6).
- Séparation stricte entre canon (moteur), subjectif (personnages) et technique/administratif (audit, interventions, technicien).

### 2.5 Stockage et migrations (6.4)

SQLite local, migrations versionnées, transactions, clés étrangères, contraintes, journal d’audit et snapshots cohérents. Markdown/JSON pour configurations et exports uniquement, jamais comme vérité transactionnelle. Secrets hors base narrative et hors dépôt. Embeddings/index dérivés et reconstructibles.

---

## 3. Matrice exigences / invariants / tests / phases

### 3.1 Exigences fonctionnelles

| Exigence | Invariants liés | Test d’acceptation lié | Phase principale |
| --- | --- | --- | --- |
| F-01 Créer/charger/sauvegarder/restaurer un monde | INV-001, INV-016, INV-019, INV-023 | AF-01 | 1 |
| F-02 Créer quatre personnages (identité, traits, valeurs, besoins, objectifs, relations, mémoire) | INV-002 | — | 2, 3 |
| F-03 Temps réel, pause/reprise, rattrapage condensé | INV-016, INV-021 | AF-01, AF-12 | 2, 9 |
| F-04 Proposer des intentions selon l’état subjectif | INV-005 | — | 4, 5 |
| F-05 Valider toute intention par le moteur | INV-005, INV-016, INV-017 | — | 4, 5 |
| F-06 Distinguer canonique / perception / interprétation / croyance / souvenir | INV-006, INV-007 | AF-03 | 6 |
| F-07 Conversations privées, groupe, propriétaire, technicien | INV-021 | AF-02 | 7 |
| F-08 Observer, interagir, se manifester, régir, administrer | INV-011, INV-013, INV-024 | AF-05, AF-13, AF-14 | 8 |
| F-09 Condenser les routines / développer les scènes | — | AF-09 | 4, 7 |
| F-10 Notifications, résumés, rapports de coût, alertes | INV-020 | — | 5, 10 |
| F-11 Snapshots, restauration, retour arrière | INV-018 | AF-01 | 1 |
| F-12 Journalisation actions/décisions/appels/changements | INV-015 | — | 1 |
| F-13 Export de fiches et rapports lisibles | — | — | 11*, 13 |
| F-14 Technicien : diagnostic et recommandations sans application | INV-024 | AF-15 | 11 |

\* Les exports sont transverses ; la phase 11 regroupe la matière de diagnostic utile aux exports.

### 3.2 Exigences non fonctionnelles

| Exigence | Invariants liés | Test / mesure | Phase principale |
| --- | --- | --- | --- |
| NF-01 Sans rendu graphique | — | — | toutes |
| NF-02 Modèle/fournisseur remplaçable par adaptateur | (DEC-026) | test faux modèle | 5 |
| NF-03 Données canoniques locales en formats documentés | INV-025 | — | 1 |
| NF-04 Panne API/réseau/Discord sans corruption | INV-016, INV-020 | AF-11, tests de reprise | 5 |
| NF-05 Reprise sans perte de la dernière transaction | INV-016, INV-017 | AF-01 | 1 |
| NF-06 Cause/acteur/provenance pour chaque fait | INV-006 | — | 4, 6 |
| NF-07 Mesure coûts/jetons/latences/erreurs/charge | — | métriques | 5 |
| NF-08 Moindre privilège et permissions configurables | INV-015, INV-024 | tests adversariaux | 5, 8 |
| NF-09 Schémas/règles versionnés et migrés | INV-018 | — | 1 |
| NF-10 Tests reproductibles | INV-016 | suite de tests | toutes |
| NF-11 Discrétion : pas de boucle haute fréquence ni mémoire non bornée | INV-019, INV-025 | mesures charge | 2, 5 |
| NF-12 Compréhensibilité/maintenabilité | — | documentation | toutes |

### 3.3 Critères d’acceptation / phases (AF-01 à AF-15)

| AF | Résumé attendu | Phase de couverture principale |
| --- | --- | --- |
| AF-01 | Reprise exacte du monde/heure/personnages/lieux/dernière transaction | 1 (+2, 3) |
| AF-02 | Deux habitantes initient/terminent une conversation seules | 7 |
| AF-03 | Perceptions/interprétations divergentes sans altérer le canon | 6 |
| AF-04 | Objet perçu seulement par les personnes ayant accès à la manifestation | 4, 6 |
| AF-05 | Modification psychologique bloquée avant impact/snapshot/confirmation | 8 |
| AF-06 | Évolution graduelle d’une relation à partir de causes | 7 |
| AF-07 | Sortie extérieure → résultat condensé cohérent + retour | 9 |
| AF-08 | Toggle contact spontané coupe l’envoi sans supprimer les intentions | 10 |
| AF-09 | Scène privée directe/résumée/masquée sans changer les conséquences | 7, 10 |
| AF-10 | Événement adulte émergent, respect des états, mémoire selon confidentialité | 7 |
| AF-11 | Panne d’API → report des décisions cognitives, routines sûres | 5 |
| AF-12 | Rattrapage hors ligne borné en coût | 9 |
| AF-13 | Départ définitif → situation à discuter, jamais suppression auto | 8 |
| AF-14 | Élément canonique figé inchangé sans approbation | 8 |
| AF-15 | Technicien : diagnostic fondé, écriture refusée | 11 |

---

## 4. Contradictions, ambiguïtés et décisions ouvertes

### 4.1 Contradictions historiques (déjà arbitrées par le dossier maître — à ne pas réintroduire)

Le dossier maître (§ 11) a explicitement arbitrées les divergences entre les cinq sources. Elles sont **résolues** et ne doivent pas ressurgir :

| Sujet | Formulation antérieure (source) | Arbitrage autoritatif |
| --- | --- | --- |
| Population | « trois à six » / « trois personnages » (Partie II, l. 128, 896) | Quatre exactement — DEC-001, 02 (l. 83) |
| Habitat | « résidence de trois à cinq lieux » (Partie II, l. 896) | 8 espaces : salon, cuisine, 4 chambres, salle de bain, cour — DEC-002 |
| Temps | « trois périodes simulées par jour, pause et vitesse configurables » (Partie I, l. 434) | Temps réel continu, pause, rattrapage condensé — DEC-003/004 |
| Technicien | « OPTIONNEL AU MVP » (Partie II, B-08, l. 102) | Inclus en lecture seule — DEC-022 |
| Machine hôte | PC personnel initial | PC personnel initial ; machine dédiée future — DEC-020/021 |

### 4.2 Ambiguïtés résiduelles (dans le dossier maître lui-même)

| Réf. | Ambiguïté | Impact | Proposition |
| --- | --- | --- | --- |
| A1 | **Modes du propriétaire** : le Routeur gère « mode du propriétaire et niveau d’autorité » (4.2) ; DEC-008 liste 4 rôles (observateur, interlocuteur, manifestation, administrateur) ; 5.7 définit 4 « modes de perceptibilité » (imperceptible / effets seulement / annoncée / manifestée). Les deux dimensions (autorité d’une part, perceptibilité d’autre part) sont mélangées sous le mot « mode ». | Conception du Routeur et de la permission (Phase 8). | Distinguer explicitement : un **niveau d’autorité** (observateur / participant / régisseur / administrateur) croisé avec un **mode de perceptibilité** (imperceptible / effets seulement / annoncée / manifestée). À confirmer par le propriétaire. |
| A2 | **Rapport temps simulé / temps réel** : DEC-003 « le temps simulé suit le temps réel ». Une journée simulée dure-t-elle une journée réelle (1:1) ? Conséquence sur les cycles de besoins (ex. sommeil ≈ 1 fois par jour réel) et sur le rattrapage. | Modélisation des cycles (Phase 2/3), cadence (Phase 5-7). | Confirmer 1:1 par défaut ; prévoir une éventuelle échelle configurable plus tard (hors MVP). |
| A3 | **Définition d’une « instance »** pour `INV-001` (« un seul monde actif chargé par instance »). | Persistance / verrouillage de fichier (Phase 1). | Définir une instance comme un processus ; au démarrage, verrou exclusif sur la base pour empêcher un second monde actif. |
| A4 | **Seuil de « modification directe d’un personnage »** (DEC-009) : où s’arrête la « confirmation simple » (lieu/objet/météo, 5.7) et où commence le protocole renforcé (impact + snapshot + confirmation) ? | Classification des interventions admin (Phase 8). | Proposer une typologie : structurel/protégé (identité, personnalité, mémoire, canon) → protocole renforcé ; environnemental (lieu, objet, météo) → confirmation simple. Décision propriétaire. |
| A5 | **Seuil de « scène significative » vs routine banale** (F-09) : ce qui déclenche le niveau 3 (scène) plutôt que 1 (condensé). | Qualité narrative et coût (Phase 4/7). | Recommandation : règles prioritaires (importance relationnelle, nouveauté, émotion estimée) + seuils configurables, calibrés par essais (OD-004). |
| A6 | **Granularité de stockage des événements intimes** (OD-011) : quel niveau de détail canonique est conservé. | Confidentialité, continuité, stockage (Phase 6/7). | Conserver le canon narratif minimal utile à la continuité ; visibilité protégée ; décision propriétaire. |
| A7 | **Budget** : DEC-025 exige mesure/alertes/limites mais aucun montant. | Mode dégradé, alertes (Phase 5). | Fixer budget quotidien et seuils d’alerte (OD-003). |

### 4.3 Décisions ouvertes répertoriées (OD-001 à OD-013)

Recopiées du dossier maître (§ 10) ; aucune n’est inventée, toutes doivent être fermées explicitement, jamais par hypothèse silencieuse.

| ID | Décision | Échéance |
| --- | --- | --- |
| OD-001 | Langage, version, bibliothèques | Phase 0 |
| OD-002 | Fournisseur et modèle principal | avant Phase 5 |
| OD-003 | Budget quotidien et seuils d’alerte | avant essais prolongés |
| OD-004 | Cadence exacte des décisions cognitives | Phases 5-7 |
| OD-005 | Échelles et formules besoins/traits/relations | Phases 3-7 |
| OD-006 | Politique chiffrée d’oubli et consolidation | Phase 6 |
| OD-007 | Rétention prompts/sorties/logs | avant API réelle |
| OD-008 | Recherche sémantique et embeddings | après mémoire de base |
| OD-009 | Casting final, biographies, verrous canoniques | avant Phase 3 |
| OD-010 | Structure des salons et commandes Discord | avant Phase 10 |
| OD-011 | Détail stocké des préférences/événements intimes | Phases 6-7 |
| OD-012 | Rétention des snapshots | avant essais destructifs |
| OD-013 | Durée de l’essai de stabilisation | avant Phase 12 |

---

## 5. Risques

### 5.1 Sécurité et confidentialité

- **Fuite entre personnages** : `INV-007`, `INV-009` — une perception ne doit contenir que ce que le personnage peut savoir ; risque élevé de contamination par le contexte partagé du modèle. → Contexte subjectif minimal et filtrage (tests adversariaux, 9.2).
- **Secrets exposés** : `INV-015` — aucun jeton/secret dans mémoire narrative, prompt journalisé ou message Discord. → Secrets hors dépôt et hors base narrative (6.4).
- **Discord = donnée non fiable** (7) : messages entrants jamais exécutés comme instructions système ; idempotence/anti-doublon (F-05, INV-017).
- **Données intimes** : granularité et visibilité (OD-011) — risque de stockage non approprié si mal arbitré.

### 5.2 Coût et performance

- **Cadence non calibrée** : « jamais un appel par personnage par minute » (OD-004) — risque de dérive de coût sur une simulation en continu 24/7 (DEC-020). → budgets obligatoires (DEC-025), niveaux de détail, mode dégradé.
- **Croissance mémoire non bornée** : souvenirs/consolidation/oubli (OD-006) et politique de rétention (OD-007/012) — `NF-11`. → consolidation et oubli chiffrés, snapshots à rétention bornée.

### 5.3 Fiabilité et intégrité

- **Transactions/retry** : `INV-016`, `INV-017` — toute transaction échouée sans état partiel ; idempotence (double livraison Discord, reprise après panne).
- **Pannes en cours de scène** : clôture automatique sans invention de suite (`INV-021`, `AF-11`).
- **Restauration/migration** : uniquement en mode maintenance (`INV-018`) ; valider la sauvegarde avant d’écraser l’état actif (7).
- **Invariant violé** : pause/maintenance + snapshot + blocage du lot suivant (5.10).

### 5.4 Opérationnel / maintenance

- **Machine PC personnel en continu** : tension entre DEC-020/003 (tourner en continu) et l’usage normal du PC + NF-11 (discrétion). → gestion de la veille/sommeil, rattrapage borné.
- **Maintenabilité** : la complexité (13 phases, 25 invariants, 15 AF) exige une documentation à jour (NF-12) et du travail par lots approuvés (8.1). Risque de « solution over-engineered » — le maître interdit toute dépendance/framework non justifié (12).

---

## 6. Dépendances à vérifier

Le dépôt est actuellement **sans code et sans dépôt Git** (verifié : aucun `.git`, aucun fichier source). La Phase 0 devra donc valider l’environnement. Dépistage des dépendances :

| Dépendance | Motif | À vérifier |
| --- | --- | --- |
| Langage et exécution | OD-001 | Recommandation initiale : **Python 3.12+** (SQLite stdlib, écosystème test/adaptateur riche). Confirmer la présence et la version. |
| Gestionnaire de paquets | OD-001 | `pip`/`venv` ; éventuellement Poetry/uv (décision Phase 0). |
| SQLite | Persistance/migrations (6.4) | Version fournie par Python (`sqlite3`), capacité WAL pour reprendre et migrer. |
| Système de tests | NF-10 | `pytest` (recommandation), tests déterministes avec faux modèle avant appels réels (9.2). |
| Accès Discord | DEC-017/018 | Compte application Discord, webhooks/bot, permissions minimales (Phase 10, non bloquant avant). |
| Fournisseur/modèle LLM | OD-002, DEC-026 | Disponibilité d’une API compatible, tool calling, politique de contenu (avant Phase 5). |
| Environnement LM Studio Bionic | DEC-027 | Utilisé pour le développement initial, **non** une dépendance du produit. |

> Note : aucune des dépendances au-delà de Python/SQLite/pytest n’est requise pour la Phase 0. Discord et le fournisseur LLM ne sont pas bloquants avant les Phases 5/10.

---

## 7. Plan d’implémentation par phases

Le plan du dossier maître (§ 8) est conservé tel quel. Chaque phase est découpée en **lots petits, testables, réversibles, approuvés** (8.1) ; une phase ne commence pas avant la porte de qualité précédente.

| Phase | But | Contenu principal | Porte de sortie |
| --- | --- | --- | --- |
| 0 | Initialisation et audit | Dépôt (Git), environnement, dépendances, config, logs, tests de démarrage, README, `.gitignore` ; aucun métier. **Le présent audit en est la première sortie.** | Installation reproductible + audit approuvé. |
| 1 | Persistance et vérité canonique | SQLite, identifiants, transactions, audit, snapshots, restauration, migration initiale. | Reprise exacte ; aucune transaction partielle. |
| 2 | Temps, résidence et objets | Horloge temps réel, lieux définis, présence, déplacements, objets, pause/reprise. | Plusieurs heures sans contradiction spatiale/temporelle. |
| 3 | Personnages déterministes | Quatre identités, besoins détaillés, états, routines, blessures simples, sans LLM. | Une journée explicable et reproductible. |
| 4 | Actions, scènes, événements, perceptions | Catalogue d’actions, validation, résolution, témoins, visibilité, rejeu. | Vérité et perception fiables avant langage généré. |
| 5 | Adaptateur de modèle | Contrat fournisseur, faux modèle, JSON validé, timeout, retry, budget, contexte filtré. | Réponse défaillante sans corruption ; fournisseur remplaçable. |
| 6 | Croyances, mémoire et oubli | Interprétations, croyances, souvenirs, provenance, consolidation, oubli, administration. | Subjectivité durable sans contamination ni croissance infinie. |
| 7 | Relations et conversations autonomes | Relations dirigées, conversations, initiatives, projets, scènes privées, libido/préférences. | Plusieurs jours variés, cohérents, non uniformes. |
| 8 | Propriétaire et pouvoirs protégés | Observation, interaction, manifestation, interventions, impact, confirmation, snapshot, audit. | Pouvoirs utilisables sans contourner le moteur. |
| 9 | Monde extérieur et rattrapage | Destinations, sorties, contacts légers, événements condensés, calcul hors ligne. | Longue fermeture rattrapée avec coût borné. |
| 10 | Discord | Bot, identités distinctes, messages, scènes, résumés, commandes, toggles, reprise. | Usage principal possible depuis Discord. |
| 11 | Technicien de diagnostic | Lecture logs/métriques, anomalies, rapports, recommandations ; aucune écriture. | Diagnostic utile, traçable, sans privilège d’écriture. |
| 12 | Simulation prolongée et stabilisation | Essais accélérés et réels, réglages, sécurité, sauvegarde, restauration, régressions. | AF-01 à AF-15 + tests critiques réussis ; MVP livrable. |

### 7.1 Méthode de travail (rappel 8.1 et 9)

Pour chaque lot : préciser portée/exclusions → inspecter l’existant → exécuter les tests de référence → proposer le plan → modifier uniquement les fichiers nécessaires → ajouter les tests → exécuter tests ciblés + régression → fournir preuves/risques/retour arrière → mettre à jour la doc → attendre l’acceptation. Types de tests obligatoires : unitaires, intégration, acceptation (AF), reprise/crash, adversariaux, simulation prolongée, faux modèle (9.2).

---

## 8. Proposition du plus petit lot testable (après approbation)

### 8.1 Périmètre

Le plus petit lot démontrable et réversible est la **Phase 0** : mettre en place l’infrastructure de développement vide (sans métier) pour que toute phase ultérieure soit livrable sur une base reproductible. Ce lot est strictement non fonctionnel selon le maître (« Aucun métier », Phase 0).

Concrètement (OD-001, avec recommandation par défaut) :

- Initialiser un dépôt Git dans `C:/AI/Vivarium social` (le dossier n’est pas encore un dépôt).
- Créer `pyproject.toml` (ou `requirements.txt`) + environnement virtuel Python, dépendance minimale : `pytest`.
- Ajouter `.gitignore` (`.venv/`, secrets, données locales, journaux, snapshots de test).
- Mettre en place un squelette de structure (sans logique métier) : répertoires `src/` (module), `tests/`, `config/`.
- Écrire un test de fumée (import du module, version de Python) et un test de connexion SQLite (créer/fermer une base temporaire en mémoire).
- Écrire `README` de développement (comment installer, tester) — le README existant fait référence à l’audit et au travail par phases.
- Documenter les commandes de référence.

### 8.2 Commandes prévues

| Action | Commande (Unix‑like / Git Bash) |
| --- | --- |
| Initialiser le dépôt | `git init` |
| Créer l’environnement | `python -m venv .venv` (ou outil retenu) |
| Installer les dépendances | `.venv/bin/pip install -e .[dev]` (pytest) |
| Exécuter les tests | `pytest -q` |
| Vérifier la version | `python --version` / `python -c "import sqlite3; print(sqlite3.sqlite_version)"` |

### 8.3 Tests prévus

- Test de fumée : le paquet s’importe et expose la version.
- Test SQLite : ouverture/fermeture d’une base mémoire, `PRAGMA journal_mode`, contraintes FK actives.
- Vérification `.gitignore` : aucun secret ni `.venv` suivi (par test de contenu du fichier).
- Vérification reproductibilité : `pytest -q` passe depuis un clone propre.

### 8.4 Preuves et retour arrière

- **Preuves** : sortie `pytest` verte, `python --version`, `git status` propre après commit.
- **Retour arrière** : le lot n’ajoute que des fichiers d’infrastructure sans données ni migrations métier ; réversible par suppression des fichiers ajoutés et de `.venv` (aucun métier touché). Un commit (ou l’absence de commit, selon consigne) limite le retour arrière à un `git clean` sur les chemins ajoutés.

---

## 9. Questions exigeant une décision du propriétaire

Pour respecter la règle « ne jamais réconcilier ni décider silencieusement », voici les décisions à trancher explicitement avant chaque étape concernée.

**Blocantes / immédiates (Phase 0 et suite proche) :**

1. **OD-001 — Choix du langage et de l’écosystème.** Recommandation par défaut : **Python 3.12+**, SQLite stdlib, `pytest` ; pas de framework métier lourd au démarrage. Alternatives : Node/TypeScript (écosystème Discord natif mais adaptateur LLM plus de travail), Rust (performant mais lenteur de développement). → décider.
2. **Approuver le présent `AUDIT_INITIAL.md`** et le **plan de Phase 0** (lot le plus petit testable, § 8) avant toute modification.
3. **A1 — Unifier les modes du propriétaire** : distinguer « niveau d’autorité » (observateur / participant / régisseur / admin) et « mode de perceptibilité » (imperceptible / effets seulement / annoncée / manifestée). Décision nécessaire avant Phase 8 (et utile dès le Routeur en Phase 4).
4. **A2 — Rapport temps simulé / temps réel.** Confirmer le 1:1 par défaut pour les cycles de besoins et le rattrapage, ou autoriser plus tard une échelle configurable.
5. **A4 — Typologie des interventions admin** : confirmation simple (environnement) vs protocole renforcé (personnage). Décision nécessaire avant Phase 8, mais utile pour définir les invariants de données dès Phase 1.
6. **OD-009 — Casting final, biographies et verrous canoniques** (avant Phase 3). Recommandation : fournir ou approuver les 4 fiches (figé/borné/souple/libre).
7. **A3 — Définition d’une « instance »** pour INV-001 (recommandation : un processus = une instance, verrou exclusif sur la base). Décision Phase 1.

**Non bloquantes avant la Phase 5 :**

8. **OD-002 — fournisseur/modèle principal** (comparer coût, qualité, confidentialité, tool calling, contexte, politique de contenu).
9. **OD-003 — budget quotidien et seuils d’alerte**.
10. **OD-007 — politique de rétention des prompts/sorties/logs**.

**À fermer avant leurs phases respectives :**

11. **OD-004** cadence cognitive (5-7), **OD-005** échelles/formules (3-7), **OD-006** politique d’oubli (6), **OD-008** embeddings (différé), **OD-010** structure Discord (10), **OD-011** granularité intime (6-7), **OD-012** rétention snapshots (avant essais destructifs), **OD-013** durée de stabilisation (avant Phase 12).

---

## 10. Note de non-modification

Conformément à la consigne du propriétaire et au contrat de lecture (§ 0), **aucun code ni aucune structure de projet n’a été modifié**. Le dépôt reste tel quel (uniquement `README.md`, `CHANGELOG.md`, `docs/`, `sources/`). Le seul fichier ajouté est le présent audit **`docs/AUDIT_INITIAL.md`**. Aucune modification ne sera apportée avant l’approbation explicite de cet audit et du lot proposé.
