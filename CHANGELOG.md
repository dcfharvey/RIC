# Changelog

## Lot 4 circadien — compatibilité et shadow (11 août 2026)

- Audite exhaustivement les consommateurs legacy de `repos` et `energie` et
  documente les groupes qui devront être commutés ensemble au futur cutover.
- Ajoute un motif de sommeil synthétique, un arbitrage volontaire sans priorité
  de catégorie et une éligibilité de stabilité appliquée par un double moteur,
  sans branchement runtime ni écriture canonique.
- P, H et φ restent séparés; aucune conversion `repos → H` ou `energie → P` et
  aucune modification de la résidence réelle.

## SCC-2A — correctif de contrat provider v2

- Supprime le faux positif lexical `ment` et n'interdit plus globalement
  `intention` dans les justifications de candidates.
- Fait converger les contraintes structurelles du parser provider et du service
  persistant avant écriture; aucune migration SQLite n'est nécessaire.
- Reformule la justification comme routage non autoritatif et versionne le
  provider en `scc2a-appraisal-v2`.
- Retire la justification du snapshot provider SCC-3A; l'observation peut encore
  l'afficher, mais aucun propriétaire aval ne la traite comme une preuve.

## Préparation du prochain burn-in — instrumentation diagnostique (11 août 2026)

- Synchronise la photographie active sur le schéma 44 et le rodage vivant après
  `da30d5d`.
- Ajoute une instrumentation JSONL locale, désactivée par défaut et bornée, pour
  relier les appels `scene_turn` et SCC-2A à leur contexte, sortie provider,
  validation et provenance technique.
- Les traces diagnostiques restent séparées du canon et des états subjectifs;
  aucun contrat, budget, prompt, provider ou comportement cognitif n’est modifié.
- La répétition dialogique et les `invalid_appraisal` SCC-2A restent des signaux
  de rodage non résolus; le prochain jalon est un burn-in court après validation
  de cette instrumentation.

## SCC-3A — conséquence affective owner-governed (10 août 2026)

- Ajoute la décision SCC-3A affect et la migration forward-only 0044.
- Une candidate affect peut produire `no_change` ou un épisode privé via
  `AffectService`; aucune humeur, expression, action ou conséquence d'un autre
  domaine n'est activée.

## SCC-2A — appraisal social situé (10 août 2026)

- Ajoute `social_appraisal`, les candidates génériques et le journal technique
  SCC-2A via la migration forward-only 0043.
- Raccorde optionnellement le runtime après SCC-1B avec snapshot fermé,
  validation stricte et arrêt avant SCC-3.
- Aucun effet d'affect, croyance, relation, but, action ou canon n'est produit.

## SCC-1C — admission cognitive sélective (10 août 2026)

- Ajoute une admission SCC-1C bornée depuis une `subjective_trace` sociale
  SCC-0 explicitement fournie, avec sélection ou non-sélection immuable.
- Sépare les tentatives techniques différées/indisponibles des décisions
  cognitives; `SocialInterpretationService` reste l'unique propriétaire SCC-1B.
- Ajoute la migration forward-only `0041_scc1c_admission.sql`, les audits,
  projections et tests déterministes. Aucun raccordement runtime, rattrapage
  historique ou effet causal n'est ajouté.

## SCC-1C runtime — chaîne sociale vivante

- Raccorde un nouvel acte social runtime à SCC-0, SCC-1C puis SCC-1B, avec
  ownership privé, budget technique séparé, dégradation provider et retry borné.
- Ajoute la migration forward-only `0042_social_interpretation_call_trigger.sql`
  pour préserver les admissions techniques existantes et autoriser le trigger
  `social_interpretation`.
- Aucun scan historique, effet SCC-2/SCC-3, attribution imbriquée ou changement
  canonique n'est ajouté.

## SCC-1B2D4 — namespace atomique des artefacts Screen-47

- Les chemins review/paired sont désormais dérivés du principal fourni par
  `--report`, sans collision avec un autre candidat.
- Les vues review/paired Screen-47 restent reconstructibles intégralement depuis
  le rapport principal, sans nouvel appel LLM.

## SCC-1B2D1 — correctif runner pairé et validation bornée

- Le runner B15/B16 conserve désormais une erreur initiale provider/parse/semantic
  comme donnée et n'essaie plus de construire une révision inaccessible; le faux
  `revision_not_accessible` consécutif à une initiale non persistée est fermé.
- Cause établie : quatre modèles récupérés produisaient une initiale B15 non JSON
  (Markdown autour du JSON), tandis que la paire réelle Qwen3 14B traversait le
  même chemin avec owner, supports, provenance et fingerprints valides.
- Validation réelle bornée : une paire B15/B16 Qwen3 14B, deux appels, valide;
  aucun Screen-47 complet, T2a ou T2b relancé.

## 0.1.0a15 — 8 août 2026

- SCC-0 ajoute l'encodage privé idempotent d'une parole sociale acceptée,
  depuis sa source persistante et sa preuve d'appartenance historique à la scène,
  sans interprétation ni conséquence cognitive automatique.
- SCC-1A ajoute des interprétations sociales privées, bornées, owner-scoped et
  révisables, sans LLM ni conséquence causale.
- SCC-1A durcit la révision : toute trace subjective privée du même propriétaire
  peut servir de preuve secondaire; les hypothèses sont trimées et dédupliquées
  exactement, avec persistance et invariants append-only vérifiés.
- SCC-1B1 ajoute un snapshot subjectif historique owner-scoped, un provider LLM
  borné, une provenance technique persistante, la révision explicite et le replay
  idempotent, sans raccordement runtime ni conséquence cognitive.
- SCC-1B1 est durci avant calibration : snapshot profondément immuable, fingerprint
  du wire exact, séparation de l'identité technique du contenu cognitif, prompt
  contractuel explicite, provenance auditée et validations pré-provider.
- Clôture SCC-1B1 : recette provider/prompt versionnée en `scc1b1-native-v2` et
  contexte borné à trois traces supplémentaires explicitement sélectionnées.
- SCC-1B2A durcit le banc jetable `social-interpretation-bench` : 30 IDs,
  31 variantes déclarées, fixtures T0 déterministes, cas deferred explicites,
  smoke T1 borné et diagnostics JSON bruts; T2 reste désactivé.
- SCC-1B2A finalise la readiness T2 : contraste B17/B18 honnête, diagnostics
  mention/compliance B24/B25, métriques métamorphiques multi-trial, provenance
  et partial-write hard blockers, runner pairé B15/B16 et campagne T2a réelle
  en deux segments (105 appels génériques + 10 appels pairés; artefacts sous
  `data/bench/`). Le faux positif de provenance du runner pairé est couvert par
  une régression dédiée, sans modification de SCC-1B1.
- SCC-1B2C rend le tooling T2 model-agnostic, ajoute `llm-inventory`, le plan
  Screen-47 borné à 47 appels et des artefacts model-specific collision-safe;
  aucune campagne comparative n'est exécutée dans ce lot.
- SCC-1B2C1 durcit la validation de déploiement (instance id, configuration
  réelle, multiplicité, mismatch de contexte), l'état d'échec du warm-up et
  l'agrégation des métriques scored-only; inventaire final LM Studio réécrit.
- L'horloge canonique distingue maintenant la pause administrative de l'arrêt
  du runtime. Un arrêt propre gèle immédiatement le temps simulé; le lancement
  suivant repart de ce point sans rattrapage hors ligne.
- Les sessions runtime possèdent un battement persistant. Une session laissée
  ouverte par un crash est fermée comme `crash_recovered`, puis l'horloge est
  réancrée au dernier instant durable sans jamais précéder un événement canonique.
- Les battements restent un registre opérationnel mutable et compact; seules
  les transitions de cycle de vie sont recopiées dans un journal append-only.
- Le schéma SQLite passe en version 38 avec le durcissement des preuves secondaires SCC-1A.
- Validation complète : **753 tests**.

## 0.1.0a14 — 7 août 2026

- Une occasion sociale refusée par le budget est maintenant suspendue jusqu'à
  son instant canonique de renouvellement, au lieu d'être repollée et
  journalisée toutes les deux secondes. La suspension est technique,
  reconstructible depuis les admissions et n'ajoute aucune vérité au monde.
- Le runtime conserve son ordonnanceur social entre les ticks afin de suivre
  ces échéances tout en laissant les autres scènes et le déterminisme avancer.
- La télémétrie n'applique plus la taxonomie d'activités sapientes aux attentes
  CAT-0 : leur variété se trouve dans les décisions et déplacements animaux.
- L'enquête a aussi établi qu'une échéance simulée ne doit jamais être comparée
  directement à l'heure murale : le temps de calcul LLM est volontairement
  exclu du temps vécu par le monde.
- Validation complète : **730 tests**.

## 0.1.0a13 — 7 août 2026

- Première couche d'agence animale générique (`CAT-0`) : un personnage non
  sapient configuré observe uniquement les passages adjacents, forme une
  intention courte et se déplace sans appel LLM par les moteurs canoniques.
- Les attentes sont bornées et réactivées par une échéance ou un changement de
  passage local. Une cible durablement bloquée est abandonnée après trois
  échecs explicites afin de permettre une solution locale alternative.
- Intentions, transitions et décisions sont append-only, attribuées à leur
  événement source et indépendantes du nom ou de l'espèce du personnage.
- Les gabarits MVP immuables passent en v4; seule Patoune reçoit le nouveau
  composant. Le schéma SQLite passe en version 34.
- Validation complète : **728 tests**.

## 0.1.0a12 — 7 août 2026

- Correction d'un dépassement chronologique observé en rodage : la latence
  d'un appel LLM ne peut plus laisser une action subjective franchir une fin
  d'activité déterministe encore en attente.
- Le runtime réévalue les échéances après chaque phase vivante potentiellement
  lente et rend immédiatement la main au simulateur si l'une devient exigible.
- Le contrat d'action refuse en dernier ressort toute proposition située à ou
  après une échéance déterministe pendante, sans mutation partielle.
- Deux régressions couvrent l'arbitrage interphase et la barrière
  transactionnelle. Validation complète : **721 tests**.

## 0.1.0a11 — 7 août 2026

- Correction d'une famine sociale découverte en rodage : l'autonomie ne peut
  plus consommer une nouvelle attente commune avant que le cycle social ait eu
  la possibilité de l'observer.
- L'ordre du runtime devient déterminisme, social, autonomie puis événements
  directs. La scène reste issue d'un `idle` canonique unique; aucune minuterie
  conversationnelle ni parole forcée n'est ajoutée.
- Régression couverte : une scène est ouverte avant le remplacement atomique de
  l'`idle`, et l'activité choisie demeure ensuite applicable.
- Validation complète : **719 tests**.

## 0.1.0a10 — 7 août 2026

- Contre-audit scientifique `0.1.0a9` archivé et traduit en matrice d'écarts
  sans transformer ses propositions R&D en canon technique.
- Contrats renforcés : parole, refus et excuse ne produisent automatiquement
  ni croyance, ni affect, ni relation, ni permission; une relation positive
  n'implique jamais une permission ou un consentement.
- Télémétrie locale en lecture seule : répétition des paroles, scènes vides,
  interruptions et monoculture d'activités sont des signaux heuristiques,
  jamais des faits psychologiques.
- Le gardien conserve ces signaux dans son journal; les résultats techniques
  d'arrivée, d'autonomie et de dialogue alimentent un JSONL append-only séparé.
- Validation complète : **718 tests**.

## 0.1.0a9 — 7 août 2026

- La planification d'un retry cognitif invalide est désormais figée à l'instant
  d'admission précédant l'appel LLM, jamais à l'heure murale suivant sa latence.
- Régression vivante couverte : une réponse invalide lente ne peut plus placer
  le retry après une échéance canonique déjà pendante.
- Le gardien `0.1.0a8` a détecté cette anomalie en exploitation et arrêté le
  runtime avant le contrôle suivant, sans réparation silencieuse.
- `SimulationEngine.run_to` borne maintenant toute cible murale déjà dépassée
  à l'instant canonique courant, empêchant un recul d'une milliseconde pendant
  l'initialisation des activités.
- Le gardien conserve son bilan horaire et réaudite aussi immédiatement après
  toute progression du numéro d'événement canonique.

## 0.1.0a8 — 7 août 2026

- Gardien local intégré au runtime : contrôle immédiat, puis horaire par défaut,
  sans appel génératif ni consommation de quota Codex.
- Audit du prévol canonique, des échéances actives, de LM Studio et du thread du
  tableau de contrôle; résultats `SAIN`, `ATTENTION` ou `CRITIQUE`.
- Rapports append-only dans `logs/guardian.jsonl`.
- Une conclusion critique provoque un arrêt protecteur et une fermeture propre;
  le gardien ne tente jamais de réécrire ou de masquer l'histoire canonique.

## 0.1.0a7 — 6 août 2026

- Une réponse cognitive invalide ne condamne plus une résidente à attendre la
  fin complète de son `idle` déterministe.
- Le cycle autonome remplace cet `idle` par une fenêtre de reprise traçable de
  dix minutes, interdit les appels en rafale pendant cinq minutes, puis ouvre
  une nouvelle occasion de décision.
- Le comportement non sapient de Patoune demeure déterministe et indépendant
  des appels LLM.
- Régression couverte : réponse invalide, absence de retry précoce, puis seconde
  réponse valide et activité canonique acceptée.

## Unreleased

## 0.1.0a6 — 6 août 2026

- Correction d'une régression temporelle découverte en rodage : la latence du
  LLM ne peut plus horodater une action après une échéance encore pendante.
- Une action cognitive est exécutée à l'instant observé par son contexte; le
  temps de calcul du modèle n'est pas du temps simulé vécu.
- Le numéro du dernier événement observé forme une garde optimiste. Toute
  mutation concurrente rend la proposition périmée et la fait refuser sans
  écriture (`stale_decision_context`).
- Traversées, abandon d'idle et démarrage d'activité partagent le même instant
  effectif validé.
- Validation complète : **706 tests**.

## 0.1.0a5 — 6 août 2026

- Première boucle d'activités autonomes réellement vivante : chaque nouvel
  `idle` d'une résidente sapiente ouvre une unique réflexion événementielle.
- Le LLM choisit seulement parmi des activités et destinations calculées par
  le moteur (`gaming`, `photography`, `sport`, `girly_care`, `watch_tv`,
  `socialize`); l'exécution repasse par le contrat canonique v2.
- Le remplacement atomique de l'attente garantit un rollback intégral en cas
  de refus. La provenance et les retries restent vérifiables et idempotents.
- Les anciennes bases reçoivent les nouvelles règles au lancement de façon
  additive; Patoune est exclue de tous les appels cognitifs directs.
- Essai réel Gemma validé sur monde mémoire : choix `photography`, adaptation
  syntaxique étroite, validation canonique acceptée et activité visible.
- Validation complète : **704 tests**.

## 0.1.0a1 — 6 août 2026

- Premier MVP alpha présentable : création sûre d'une résidence par `mvp-init`,
  prévol bloquant, runtime persistant `mvp-run` et tableau de contrôle local.
- Boucle sociale minimale : co-présence canonique, scène append-only bornée à
  quatre occasions de parole, fermeture explicite et interruption propre à
  l'arrêt; le texte ne produit aucun fait ni effet social automatique.
- Les traversées visibles proposées au LLM sont maintenant revérifiées par le
  moteur avant exposition. Le contexte initial commun peut amorcer une unique
  rencontre de départ sans inventer un événement.
- Adaptateur Gemma local durci pour une variation JSON redondante observée,
  sans assouplir le contrat interne de décision.
- La console montre désormais les scènes et paroles enregistrées. La livraison
  reste alpha/réinitialisable; conséquences sociales causales et vie autonome
  générale sont explicitement hors de portée.

- Ajout de `mvp-preflight`, contrôle déterministe et strictement en lecture
  seule d'une base candidate au MVP.
- Documentation de la stratégie de couverture : règles, bancs, LLM borné,
  prévol et inspection opérateur restent des preuves complémentaires.

- Ajout du banc local `llm-calibrate` : plusieurs tours LLM réels, chacun dans
  sa base mémoire neuve, avec durée, décision, validation et erreur explicite.
  Il mesure la frontière sans créer d'histoire partagée ni fixer une cadence
  produit.
- Ajout du premier tour de parole LLM dans une scène co-localisée : schéma
  distinct, admission `scene_turn`, validation stricte et idempotence de
  l'acte. Une parole reste une expression, jamais une vérité ou une
  conséquence sociale automatique.
- Ajout du banc social multi-tours : occasions de parole alternées et bornées,
  monde mémoire neuf, arrêt explicite en cas d'anomalie.

## 0.56 — 6 août 2026

- Commande `vivarium living-bench` : affiche en direct les ticks, appels et
  résultats du banc vivant dans une console, sans ouvrir de monde persistant.

## 0.55 — 6 août 2026

- Banc vivant jetable : monde d’intégration réel en mémoire, événement
  perceptible, orchestrateur, fournisseur injectable, digest et audit final.
  Il prépare l’essai local de Gemma sans toucher aucun monde persistant.

## 0.54 — 6 août 2026

- Orchestrateur autonome initial : événements directs perceptibles bornés,
  curseur technique persistant, journal de résultat et mode dégradé explicite
  lorsque le LLM local est indisponible. Migration `0033`.

## 0.53 — 6 août 2026

- Première scène sociale persistante : participantes co-localisées, actes de
  parole structurés append-only et clôture explicite ou sûre après interruption.
  Une phrase reste une expression, jamais un fait ou consentement automatique.
  Migration `0032`.

## 0.52 — 6 août 2026

- Cadre décisionnel pur reliant intention active, objectifs et motifs connus,
  sans exécution implicite ni nouvelle écriture dans le monde.

## 0.51 — 6 août 2026

- Relations privées directionnelles, multidimensionnelles et sourcées : une
  variation est petite, auditée et jamais inférée dans le sens inverse.
- Limites personnelles et permissions situationnelles explicites/révocables,
  séparées de la capacité canonique, de la relation et du consentement.
  Migration `0031`; contexte LLM v4.

## 0.50 — 6 août 2026

- États affectifs subjectifs initiaux : humeur diffuse (valence/activation) et
  épisodes émotionnels causés, privés et auditables. Une émotion ne peut pas
  être créée depuis une information inaccessible à la résidente.
- Les résolutions restent historisées et l'affect est exposé de façon bornée
  dans le contexte LLM v3, sans aucun droit d'écriture. Migration `0030`.

## 0.49 — 6 août 2026

- Premier registre de croyances subjectives sourcées : une résidente ne peut
  adopter qu'à partir de sa propre trace, sans convertir cette croyance en fait
  canonique.
- Les révisions sont traçables et append-only : nouvelle croyance, preuve,
  événement, puis statut `contested` contrôlé de l'ancienne. Digest et audit
  subjectifs séparés; migration `0029`. Le contexte LLM passe en schéma v2.

## 0.48 — 6 août 2026

- Objectifs subjectifs structurés et intentions persistantes : origine, cible,
  succès, faisabilité perçue, importance, urgence, plan et contexte de reprise.
- Une nouvelle intention interrompt explicitement l'ancienne; rien ne devient
  une action ou un résultat canonique sans le moteur. Migration `0028`.

## 0.47 — 6 août 2026

- Valeurs et préférences initiales séparées, hiérarchisées et immuables depuis
  les gabarits MVP v3; aucune n'est traitée comme une règle, limite ou action.
- Migration `0027`; digest et banc incluent ces deux profils. Tests : 618 réussis.

## 0.46 — 6 août 2026

- Première disposition de personnalité canonique : Big Five continus,
  distribution déclarative (moyenne, variabilité, inertie, signatures de
  situation) et attachement général, depuis des gabarits v2 immuables.
- Les traits ne décident rien : ils sont stockés et exposés comme modulations
  déclaratives seulement. Patoune conserve l'absence valide de ce composant.
- Migration `0026`; conception de soi, réputation, valeurs, relations et
  plasticité restent explicitement hors de ce lot. Voir
  `docs/44_PERSONNALITE_CANONIQUE.md`.

## 0.45 — 6 août 2026

- Première projection de `MotiveCandidate` : les déficits physiologiques connus
  deviennent des candidats bornés avec pression, urgence, importance et
  actions actuellement accessibles.
- Les dimensions non mesurées (plaisir attendu et coût) restent explicitement
  absentes; la projection demeure isolée jusqu'à une intégration prouvée sans
  régression. Tests : 613 réussis.

## 0.44 — 6 août 2026

- Banc de calibration des appels cognitifs : une chronologie de signaux peut
  être rejouée avec des limites candidates, séparément pour chaque résidente,
  avec rapports JSON de raisons (`eligible`, `debounced`, budget, doublon).
- Le banc n'appelle aucun LLM et n'écrit aucune base; il prépare la mesure
  réelle de cadence et de qualité avant toute boucle autonome. Tests : 609
  réussis.

## 0.43 — 6 août 2026

- Routeur cognitif explicite : le seul déclencheur actuellement raccordé,
  `direct_event`, doit désigner un événement réellement perceptible par la
  résidente. Un déclencheur sans contrat source est refusé avant admission ou
  réseau.
- Le routeur consulte l'admission append-only avant d'appeler le fournisseur;
  un retry ne joint donc pas Gemma. Un fournisseur indisponible donne un état
  dégradé explicite sans mutation canonique.
- `llm-smoke` passe désormais par ce même chemin dans son monde jetable;
  tests : 606 réussis.

## 0.42 — 6 août 2026

- Journal technique append-only des admissions d'appels cognitifs, migration
  `0025`. Une admission est inscrite avant tout futur appel réseau; son retry
  est dédupliqué de façon stable et un appel différé n'écrit rien.
- Les admissions sont séparées des événements canoniques et des mémoires
  subjectives. Elles utilisent l'heure canonique et un budget propre à chaque
  résidente. Le routeur vers Gemma reste volontairement futur.

## 0.41 — 6 août 2026

- Première porte déterministe d'appel LLM : motifs fermés, clé d'idempotence,
  déduplication durable, debounce et budget explicites. Elle est pure : aucun
  réseau, SQLite ou fait canonique ne peut être modifié par son évaluation.
- Les traces de politique portent explicitement leur résidente; un historique
  mélangé est refusé plutôt que de partager par erreur un budget entre elles.
- Les valeurs de cadence ne sont pas encore choisies pour le produit : le banc
  les injectera et les calibrera avec Gemma avant toute boucle autonome. Voir
  `docs/41_PLAN_PORTE_APPEL_LLM.md`; tests : 599 réussis.

## 0.40 — 6 août 2026

- Première frontière LLM locale : adaptateur LM Studio natif, contexte factuel
  et subjectif privé borné, sortie JSON strictement vérifiée et fournisseur
  interchangeable. Gemma 4 est appelée avec raisonnement désactivé; une décision
  ne peut proposer qu'une attente ou une traversée perceptible, que le moteur
  valide toujours.
- Configuration hors Git dans `config/.env`, priorité aux variables du shell,
  diagnostic local `vivarium llm-status` et aucun poids de modèle dans le dépôt.
- Un essai réel `vivarium llm-smoke` construit un monde d'intégration en mémoire,
  demande un seul tour au modèle et imprime le verdict du moteur sans toucher une
  base persistante. Documentation : `docs/40_ADAPTATEUR_LLM_LOCAL.md`; tests :
  592 réussis.

## 0.39 — 6 août 2026

- Première perception factuelle : chaque observateur reçoit une vue locale,
  pure et immuable de sa position, co-présences, objets visibles et connecteurs
  adjacents. Aucun état interne d'autrui, objet transporté ou fait distant ne
  fuit dans cette vue.
- Documentation : `docs/36_PERCEPTION_FACTUELLE.md`; tests : 568 réussis.

## 0.38 — 6 août 2026

- Première frontière moteur–cognition, sans LLM : intention immuable et
  versionnée, provenance et budget explicites, routeur fermé et résultat
  accepté/refusé stable. La traversée est le premier verbe autorisé.
- Une action acceptée rattache sa proposition à l'événement canonique; les
  `WorldFact` retournés sont profondément immuables. Le banc exerce la
  frontière dans le monde d'intégration.
- Audit silencieux formalisé et appliqué : documentation active remise à jour;
  aucune corruption moteur trouvée. Voir `docs/34_CONTRAT_ACTION_COGNITION.md`
  et `docs/35_ROUTINE_AUDIT_SILENCIEUX.md`; tests : 564 réussis.

## 0.37 — 6 août 2026

- Possession physique générique : un objet portable peut être pris, posé et
  suivre son personnage sans être confondu avec un équipement ou un vêtement.
  Les conteneurs portés entraînent leur contenu dans la même transaction.
- Migration `0023` : unicité du porteur, cohérence inter-mondes, objet portable
  top-level et prise au même lieu; les mutations refusées restent atomiques.
- Le monde d'intégration donne un téléphone canonique à Sophie, Erika, Luna et
  Chuu. La version logicielle atteint `0.0.2.dev0`.
- Documentation : `docs/33_POSSESSION_PERSONNAGE.md`; tests : 559 réussis.

## 0.36 — 6 août 2026

- Assemblage atomique du monde d'intégration et contexte initial partagé,
  immuable et journalisé; migration 0022.
- Transactions imbriquées via savepoints, afin que les services existants
  puissent participer à une même opération atomique.
- Tests : 551 réussis.

## 0.35 — 6 août 2026

- Les blueprints peuvent déclarer l'état initial d'un connecteur; un état fermé
  est refusé si le preset n'est pas fermable.
- Catalogues v1 atomiques pour presets environnementaux et blueprints; aucun
  catalogue invalide ne laisse d'entrée partielle.
- La résidence initiale est une recette publiée et testée : lieux, circulation,
  mobilier fixe, cour, piscine, remise, sous-sol et stationnement.
- Documentation : `docs/31_BLUEPRINT_RESIDENCE_INITIALE.md`; tests : 547 réussis.

## 0.34 — 6 août 2026

- Chuu dispose d'une calibration déclarative d'hydratation : quatre bandes de
  forme/cognition, effets explicites et cadence physiologique calculable.
- Les ressources peuvent maintenant être configurées avec toutes leurs bandes
  et effets dans un unique commit atomique, ou ajustées à une heure donnée avec
  un delta exact et borné.
- Documentation : `docs/26_CALIBRATION_CHUU.md`; tests : 541 réussis.

## 0.33 — 6 août 2026

- Les besoins et activités standards de résidence peuvent maintenant être
  installés explicitement dans un monde neuf, sans dépendre du seed technique.
- Installation atomique, idempotente et conflictuelle par conception : aucune
  définition existante n'est modifiée silencieusement.
- Documentation : `docs/25_REGLES_MONDE_STANDARD.md`; tests : 535 réussis.

## 0.32 — 6 août 2026

- `TraversalEngine` valide un franchissement concret par connecteur : présence,
  sens, destination, état, topologie et garde-fous de déplacement existants.
- Les déplacements de personnages dans un monde blueprint respectent aussi le
  connecteur lié à l'arête et tracent sa clé causale dans l'événement.
- Documentation : `docs/24_TRAVERSEE_VALIDEE.md`; tests : 532 réussis.

## 0.31 — 6 août 2026

- Instances de connecteurs issues des blueprints, liées aux arêtes du graphe
  par des contraintes SQLite de cohérence.
- Premier état canonique fini : disponible, fermé ou bloqué; les changements
  sont atomiques, journalisés et les connecteurs non fermables refusent `closed`.
- Documentation : `docs/23_CONNECTEURS_ETAT.md`; migration 0021; tests : 528 réussis.

## 0.30 — 6 août 2026

- Blueprints environnementaux versionnés et publiables : lieux, connecteurs,
  objets initiaux et politique topologique sont validés comme un ensemble.
- Un blueprint publié instancie atomiquement un monde neuf avec horloge,
  provenance immuable et événement canonique; aucun rowid ne pollue le
  snapshot reproductible.
- Migration 0020; documentation : `docs/22_BLUEPRINTS_ENVIRONNEMENT.md`;
  tests : 525 réussis.

## 0.29 — 6 août 2026

- Presets environnementaux versionnés : lieux et connecteurs disposent de
  contrats validés, brouillons, publication et immuabilité SQLite.
- La migration 0019 est globale : elle ne crée aucun fait dans un monde et ne
  modifie pas le graphe existant.
- Documentation : `docs/20_PRESETS_ENVIRONNEMENT.md`; tests : 520 réussis.

## 0.28 — 6 août 2026

- Gestionnaire d'objets : création et lecture d'installations fixes ou
  d'objets portables, avec journal canonique et déplacement atomique.
- Gestionnaire de contenance : conteneurs explicites, capacité directe,
  sous-arbres, lieu effectif matérialisé et refus des cycles.
- Migration 0018 : cohérence SQLite inter-mondes, parent‑lieu et cycle de
  contenance protégés au niveau de la base.
- Documentation : `docs/19_OBJETS_ET_CONTENANCE.md`; tests : 514 réussis.

## 0.27 — 6 août 2026

- Première fondation de l'environnement composable : la politique topologique
  est déclarée par monde (`strong_anchor` ou `none`), au lieu de supposer un
  salon codé en dur. Le seed technique choisit `salon` comme ancre seulement
  comme donnée de ce monde.
- Documentation d'architecture : `docs/18_ARCHITECTURE_ENVIRONNEMENT.md`.
- Migration 0017; tests : 504 réussis.

## 0.26 — 6 août 2026

- **Phase 4.2L — fermeture sûre de passage préparée** : `remove_link` vérifie
  qu'après l'opération tout lieu reste atteignable depuis le salon et peut y
  revenir. Une fermeture isolante est annulée entièrement, sans événement.
- `preview_remove_link` expose l'impact topologique en lecture pure;
  `AdminChangeService` et `POST /api/admin-changes/remove-passage/prepare`
  ajoutent le protocole plan/hash/confirmation à cette mutation sensible.
- Migration 0016 : extension atomique du registre de plans, avec conservation
  prouvée des plans/audits 0015.
- Tests : 502 réussis.

## 0.25 — 6 août 2026

- **Banc d'essai minimal du moteur** : `vivarium.bench` exécute un scénario
  déclaratif dans une SQLite temporaire isolée, avec horloge injectée et actions
  strictement fermées. Il produit état, journaux, refus attendus et audits, puis
  compare deux runs sans utiliser UUID ni rowid comme preuve.
- Contrat de pause explicite : le temps canonique reste gelé; aucune action à
  une heure future n'est simulée avant une reprise au même instant canonique.
- `canonical_state_digest` inclut maintenant le nom du monde : un renommage ne
  peut plus être invisibilisé par une comparaison de scénarios.
- Documentation : `docs/16_BANC_ESSAI_MOTEUR.md`; jalon logiciel atteint :
  `0.0.1.dev0` (toujours pré-alpha).
- Tests : 495 réussis.

## 0.24 — 6 août 2026

- La version logicielle est corrigée de `0.1.0` à `0.0.0.dev0` : le projet est
  en pré-alpha, pas encore au MVP.
- Jalons produits consignés : `0.1.0a1` = premier MVP alpha; `0.1.0b1` = bêta
  après essais prolongés; `1.0.0` = lancement.

## 0.23 — 6 août 2026

- Clarification de roadmap : la résidence initialisée est un monde
  d'intégration pré-MVP; le MVP est le simulateur social présentable, atteint
  après les couches vivantes.

## 0.22 — 6 août 2026

- Roadmap active ajoutée : le banc d'essai reproductible devient une étape
  centrale avant les systèmes subjectifs et le monde MVP.
- Décision consignée : monde MVP propre, distinct des mondes de test et du
  monde technique de développement.

## 0.21 — 6 août 2026

- **Phase 4.2K — ajout de passage préparé** : nouveau plan `add_link` pour
  ajouter un passage entre deux lieux existants; impact topologique explicite,
  confirmation/hash/expiration/concurrence/retry du pipeline existant.
- Migration 0015 : évolution atomique de l'audit administratif conservant les
  plans et événements 0014; test de migration réelle depuis une base 0014.
- Route locale : `POST /api/admin-changes/add-passage/prepare`.
- Aucune suppression de passage, aucun lieu nouveau, aucun changement de
  personnage, de casting, de cognition, de Discord, LLM ou interface visuelle.
- Tests : 486 réussis.

## 0.20 — 6 août 2026

- **Phase 4.2I — premier pipeline de changement administratif préparé** :
  `AdminChangeService` pour `rename_world`, plan immuable, hash exact,
  expiration, impact sémantique, verrou optimiste par séquence canonique,
  audit administratif séparé et confirmation idempotente.
- Migration 0014 : `admin_change_plan` et `admin_audit_event`; aucune voie
  SQLite parallèle et aucune confusion avec le journal canonique.
- **Phase 4.2J — API HTTP locale du pipeline** : prepare, validate, impact et
  confirm; jeton local requis pour chaque route, UUID canonique obligatoire,
  corps JSON fermés et statuts HTTP stables.
- Aucune modification de l'interface visuelle, du casting, de la cognition, de
  Discord ou d'un fournisseur LLM.
- Tests : 477 réussis.

## 0.19 — 4 août 2026

- **Phase 4.1D — Premier tableau de bord local simple** (`src/vivarium/static/`).
- Interface sombre et compacte, JavaScript natif uniquement (aucun framework,
  aucun CDN, aucune dépendance, aucune étape de build).
- Lectures administratives existantes (mondes, dashboard, personnages, fiche,
  journal) et quatre commandes existantes (pause, resume, rename, move).
- Routes statiques fermées : `GET /`, `GET /static/style.css`, `GET /static/app.js`
  (+ HEAD) ; aucun listing, aucun accès arbitraire, aucun chemin construit depuis
  l'entrée client, aucune connexion SQLite pour le statique.
- Jeton local injecté dans une balise meta (`vivarium-token`) à la diffusion de
  `GET /`, retirée du DOM par `app.js` ; transmis uniquement dans
  `X-Vivarium-Token` pour les POST ; aucun stockage persistant, aucune URL, aucun
  log.
- Rafraîchissement manuel uniquement (bouton « Rafraîchir »), sans polling ni
  `setInterval` ; conservation du monde/personnage sélectionnés et de l'état
  précédent en cas d'échec.
- Sécurité front-end : affichage par `textContent`/`createElement` (jamais par
  concaténation HTML), aucun `eval`/`Function`/`document.write`, aucune ressource
  externe, `encodeURIComponent` sur les segments dynamiques.
- Accessibilité minimale (labels, focus visible, `aria-live`), responsive simple
  (empilement sous ~900 px).
- Aucune migration, aucun seed, aucun changement de casting, aucune logique
  cognitive, aucun Discord, aucun LLM, aucun accès distant.
- Tests : 428 réussis (413 + 15 nouveaux).

### Correctifs visuels et d'affichage (D-1 à D-8)

- **D-1 — Énergie** : l'unité interne confirmée est `value_milli` (millièmes de
  pourcentage) ; affichage humain `value/1000` (ex. 69379 → 69,38 %), deux
  décimales max, zéros décimaux retirés, même format dans la liste et la fiche.
- **D-2 — Dates** : conversion locale via `toLocaleDateString`/`toLocaleTimeString`
  (barre supérieure « 4 août 2026 · 21:50 », journal « 21:49 » ou « 4 août · 21:49 »),
  sans millisecondes ni suffixe UTC ; date invalide → fallback « — ».
- **D-3 — Journal** : 20 événements les plus récents affichés (l'API renvoie en
  ordre croissant, inversé côté présentation), panneau à hauteur contrainte avec
  défilement interne, entrées compactes, aucun payload brut.
- **D-4 — Grille** : deux lignes — MONDES | PERSONNAGES | PERSONNAGE SÉLECTIONNÉ
  puis JOURNAL (large) | COMMANDES (compact) ; empilement sous ~900 px conservé.
- **D-5 — Messages** : succès temporaire (disparaît après 4 s, timer unique),
  erreurs persistantes, aucun `alert()`.
- **D-6 — Liste personnages** : clé en zone principale, lieu secondaire, énergie
  alignée à droite.
- **D-7 — Fiche** : énergie humaine, activité/blessure absentes → « — », aucun
  `null`/`undefined`/objet brut, pas de champ « type » inventé.
- **D-8 — Barre supérieure** : statut ACTIF / EN PAUSE, date/heure locale
  compacte, alignement propre.
- Aucune modification de moteur, de schéma, de seed ou de casting.
- Tests : 436 réussis (428 + 8 nouveaux).

## 0.18 — 4 août 2026

- **Phase 4.1C — Serveur HTTP local minimal** (`src/vivarium/web.py`).
- API publique : `create_server(db_path, host="127.0.0.1", port=0)`, `serve(server)`,
  `shutdown(server)` ; instance exposant `db_path`, `token`, `server_address`.
- Serveur `http.server.HTTPServer` mono-thread, bibliothèque standard uniquement,
  écoute sur `127.0.0.1` uniquement (refus de `0.0.0.0`, `::`, `::1`, `localhost`,
  adresses externes).
- Validation de la base au démarrage strictement en lecture (fichier existant,
  base SQLite lisible, tables requises, version de schéma = 8 migrations) ;
  aucune migration, aucune création implicite de base.
- Protection locale : validation Host (`127.0.0.1`/`localhost` + port réel),
  validation Origin (locale uniquement, refus sur toutes les routes `/api/`),
  jeton local `X-Vivarium-Token` obligatoire pour les POST (généré par
  `secrets.token_urlsafe(32)`, comparé par `secrets.compare_digest`), aucun CORS.
- Routes GET : `/api/worlds`, `/api/worlds/{id}`, `/api/worlds/{id}/characters`,
  `/api/worlds/{id}/characters/{key}`, `/api/worlds/{id}/events`.
- Route POST fermée : `/api/commands/{command}` (pause/resume/rename/move),
  redoublée par le dispatcher fermé d'AdminCommandService ; paramètres
  supplémentaires refusés.
- Enveloppes JSON stables, statuts HTTP exacts (200/400/403/404/405/409/411/413/415/500),
  en-têtes de sécurité (Content-Type, Cache-Control no-store, nosniff,
  Referrer-Policy), aucune CORS permissive.
- Connexion SQLite par requête, fermée dans un `finally` ; aucune connexion ou
  curseur global ; aucune écriture directe ; aucune fuite du jeton (réponses et
  logs) ; erreurs internes masquées en 500 et consignées côté serveur.
- Aucune migration, aucun seed, aucun changement de casting, aucun fichier
  HTML/CSS/JS, aucun travail sur 4.1D.
- Tests : 383 réussis (309 + 74 nouveaux).

### Correctifs de revue (C-2 à C-5)

- **C-2 — Méthodes non permises** : `do_PUT`, `do_PATCH`, `do_DELETE`,
  `do_OPTIONS`, `do_HEAD` définies ; plus aucun comportement HTML 501 hérité.
  Route connue → 405 JSON, route inconnue → 404 JSON, aucun CORS, aucune
  connexion SQLite. `HEAD` renvoie les mêmes statut/en-têtes que la réponse
  équivalente avec `Content-Length` correct et aucun corps.
- **C-3 — Cycle de vie** : état explicite `_serving` sur `VivariumHTTPServer` ;
  `shutdown()` ne bloque jamais si `serve_forever` n'est pas actif (idempotent,
  borné) ; `shutdown sans serve`, double shutdown, port libéré et redémarrage
  fonctionnent.
- **C-4 — Port** : validation propre dans `create_server` (entier non booléen,
  0-65535) ; `True`/`False`/négatif/`>65535`/flottant/chaîne/`None` refusés
  par `WebServerError` (plus de `OverflowError`/`TypeError` bruts).
- **C-5 — world_id** : borne SQLite signée 64 bits ; valeur hors plage → 400,
  maximum syntaxiquement valide → 404, plus aucun `OverflowError` interne.
- **C-1 — Validation base** : conservé `mode=ro` (WAL) ; fichier principal et
  schéma inchangés, aucune migration. La création de sidecars `-wal`/`-shm` par
  l'ouverture normale d'une base WAL est acceptée et documentée (non canonique).
- **C-6 / C-7** : documentées comme limites mineures acceptées (Host
  sensible à la casse, doublons de clés JSON « dernier gagnant », absence de
  timeout applicatif sur corps incomplet).
- Tests : 413 réussis (383 + 30 nouveaux).

## 0.17 — 4 août 2026

- **Phase 4.1B — Commandes administratives sûres et durcissement des frontières**.
- `WorldError` (world.py) avec `code` stable : `invalid_name`, `already_paused`,
  `already_active`.
- `WorldEngine.rename_world` : validation autoritative (chaîne, non vide après
  suppression des espaces, longueur ≤ `WORLD_NAME_MAX_LEN=120`), valeur
  normalisée enregistrée et dans le payload, refus avant toute mutation/événement.
- `WorldEngine.pause_world` / `resume_world` : refus autoritatif des répétitions
  (`already_paused` / `already_active`) dans la même transaction (aucune fenêtre
  lecture-validation-écriture séparée), aucune mutation d'horloge ni événement.
- `CharacterError` porte un `code` stable (world_not_found, world_paused,
  character_not_found, invalid_destination, activity_active, injury_severe,
  insufficient_energy) ; construction historique (message seul) préservée.
- `AdminCommandService` (admin.py) : dispatcher fermé à pause/resume/rename/move,
  format stable `{ok, command, data, error}`, validation des paramètres
  (world_id réel, bool refusé, chaînes non vides), traduction des erreurs par
  type/code (jamais par texte), `unknown_command`, `internal` masqué.
- Aucune migration, aucun changement de seed, de casting, de serveur HTTP ou de
  tableau de bord.
- Tests : 296 réussis (263 + 33 nouveaux).

### Renforcement de couverture (correctifs B-1 / B-4)

- `test_exception_inattendue_masquee_internal` exerce réellement la voie
  `internal` : exception inattendue levée dans la transaction de pause, réponse
  `{ok, command, data, error}` exacte, code `internal`, message générique, aucune
  fuite de détail, rollback complet, connexion réutilisable.
- `test_refus_aucune_mutation_ni_evenement` paramétré : les 14 catégories de
  refus (already_paused, already_active, invalid_name, world_not_found,
  character_not_found, destination_not_found, invalid_destination,
  activity_active, injury_severe, insufficient_energy, world_paused,
  invalid_parameters, unknown_command, internal) sont vérifiées sans mutation
  ni événement (état, nom, statut, horloge, position, énergie, activité,
  blessure, max_seq, digest).
- Aucun fichier de production modifié.
- Tests : 309 réussis.

## 0.16 — 4 août 2026

- **Correctifs 4.1A (A-1, A-2, A-3)** — lecture blessure au régime actif.
- `InjuryEngine.injury_sheet_at(world_id, character_key, target_at, regime)` :
  dérivation pure d'une blessure à un instant donné sous un régime explicite
  (passive/rest/sleep), sans écriture ni matérialisation ; frontières exactes
  (guérison à zéro, changement de niveau).
- `AdminReadService.character_view` : dérive la blessure au régime de
  récupération réellement applicable (régime de l'activité active via
  `recovery_regime`, `passive` sinon) ; plus de blessure obsolète pendant
  rest/sleep.
- `AdminReadService.list_character_views` : un seul snapshot de lecture, un seul
  `observed_canonical_at` pour toute la liste.
- A-3 documenté : pagination par `OFFSET` acceptable pour le petit journal local
  du MVP ; pagination par curseur reportée (non construite).
- Aucune migration, aucun changement de seed, de casting, de commande ou
  d'interface web.
- Tests : 263 réussis (249 + 14 nouveaux).

## 0.15 — 4 août 2026

- **Phase 4.1A — Couche de lecture administrative** (lecture seule).
- `src/vivarium/admin.py` : `AdminReadService` (frontière de lecture SQL confinée),
  `list_worlds`, `dashboard`, `list_character_views`, `character_view`,
  `journal_view` (pagination bornée par `seq`, payload masqué par défaut,
  résumés déterministes, type inconnu → résumé générique).
- Vues composées sous transaction de lecture SQLite (snapshot cohérent),
  `observed_canonical_at` capturé une seule fois, besoins/blessures dérivés à cet
  instant, aucune écriture ni matérialisation.
- Aucune migration, aucun changement de seed, de casting, de `world.py`, de
  commande ou d'interface web.
- Tests : 249 réussis (228 existants + 21 nouveaux dans `tests/test_admin_read.py`).

## 0.14 — 4 août 2026

- **Consolidation documentaire v0.2** — Phase 3 techniquement fermée (`7e5459e`,
  228 tests, `FERMETURE APPROUVABLE`). Aucun changement de code, seed, migration ou test.
- `docs/00_DOSSIER_MAITRE_IA.md` v0.2 : dossier maître consolidé (implémenté /
  normatif futur / historique), moteur canonique déterministe, contrats stabilisés,
  limites, dettes, séquence vers Phase 4 (vertical slice administratif).
- `docs/01_REGISTRE_DECISIONS.md` v0.2 : DEC-001..060 + CLA-001..004 avec statuts
  (implémenté / normatif futur / supersédée) ; casting de référence (femme humaine,
  louve anthro, slime, chat) ; Phase 4 = vertical slice administratif.
- `docs/02_MATRICE_EXIGENCES.md` v0.2 : F/NF/INV/AF avec colonne d'état.
- `docs/03_DECISIONS_OUVERTES.md` v0.2 : OD révisées (OD-009 partiellement fermée).
- `docs/05_GABARITS.md` v0.2 : ajout du contrat de lot standard.
- `README.md` : mise à jour minimale (3.3B2/3.3C et fermeture Phase 3).
- Intégration documentaire des documents post-audit et de traçabilité
  (Exigences v0.1, Demande v0.2, Feuille de route v0.1, Registre des audits v0.9,
  Index maître v0.3, Mémoire v10) ; documents archivés dans `docs/history/` (voir commit de consolidation v0.2).

## 0.13 — 4 août 2026

- **Correctifs de fermeture de la Phase 3 (C-1, C-2, C-3)** — aucun bloquant
  résiduel, aucune migration.
- **C-1** : garde dans `CharacterEngine._move` — aucun déplacement pendant une
  activité active (refus `CharacterError` avant toute matérialisation ou débit,
  sans interruption silencieuse ; position, énergie, blessure, horloge et
  journal inchangés). Le déplacement préparatoire de `start_activity` (avant la
  création de l'activité) et le déplacement direct sans activité restent
  fonctionnels.
- **C-2** : `occurred_at` des mutations administratives situé dans le temps
  canonique du monde (`read_canonical_time`), jamais à l'heure murale :
  `rename_world`, `add_link`, `remove_link`, `create_character`. `recorded_at`
  reste mural et distinct. `pause_world`, `resume_world`, `set_simulated_time`
  et les événements du simulateur sont inchangés (déjà canoniques).
- **C-3** : retrait de l'API publique `WorldEngine.append_event` ; seule
  `_append_event` (interne, dans une transaction métier) subsiste. Plus aucune
  API publique ne peut injecter un `event_type`/`payload`/`occurred_at`
  arbitraire ni un événement sans mutation correspondante.
- Tests : 228 passants (220 + 8 nouveaux, 1 remplacé).

## 0.2 — 3 août 2026

- Approbation de `docs/history/AUDIT_INITIAL.md` par le propriétaire.
- Décisions : Python 3.12 comme référence (OD-001 fermé) ; clarifications CLA-001 (autorité/perceptibilité), CLA-002 (temps 1:1 et rattrapage), CLA-003 (modification directe d’un personnage).
- **Phase 0** réalisée : dépôt Git initialisé, paquet Python minimal (`src/vivarium`), configuration (`config/`), journaux (`logs/`), accès SQLite vérifié, tests de fumée (11 tests passants). Aucune logique métier (personnage, simulation, LLM, Discord, mémoire, technicien) ajoutée.
- Règle de sûreté CLA-004 : `init --force` est destructif, réservé au développement, refusé par défaut pour tout monde réel/persistant/non-développement et non exécutable implicitement par Discord ou une commande propriétaire.

## 0.3 — 3 août 2026

- **Phase 2 — Lot 2.1** : horloge canonique en temps réel 1:1 (dérivée, lecture sans écriture), pause/reprise avec gel exact et reprise sans rattrapage de la pause, horloge injectable déterministe (`Clock`), migration 0002 (contrainte du statut `active`/`paused` par déclencheurs). 44 tests passants.

## 0.4 — 3 août 2026

- **Phase 2 — Lot 2.2** : connectivité spatiale. 9ᵉ lieu `couloir` (circulation),
  graphe orienté `location_link` (migration 0003), BFS dirigé (`find_path`),
  `can_traverse`/`has_physical_connection`/`adjacent_from`, intégrité du graphe,
  modifications administratives atomiques et tracées (un événement par opération
  physique). `init --force` utilisé exceptionnellement pour reconstruire le monde
  de développement ; pratique documentée comme exceptionnelle. 61 tests passants.
- Note d'évolution future EVO-001 : détection d'un saut anormal de l'horloge
  système vers l'avant avant un grand rattrapage (non implémenté).

## 0.5 — 3 août 2026

- **Phase 3 — Lot 3.1** : identités et présence canonique. Table `character`
  (migration 0004, sans `is_dev` ; `key` immuable par déclencheur ; `adult=1` ;
  FK composite `(world_id, location_id)`), 4 habitantes provisoires `character_1..4`
  en `chambre_1..4`, `CharacterEngine` (`create_character`, `character_sheet`,
  `move_character` une arête dirigée, refus en pause/vers le lieu actuel, atomicité),
  procédure non destructive et idempotente `upgrade-dev`. 77 tests passants.

## 0.6 — 3 août 2026

- **Phase 3 — Sous-lot 3.2A** : besoins dérivés et matérialisation. Migration 0005
  (`need_definition`, `need_state` avec `rate_remainder`, FK composites inter-mondes),
  valeur entière `value_milli` 0..100000, taux rationnels entiers, équivalence
  indépendante du découpage, lectures pures, matérialisation groupée (un événement
  `needs_materialized`), pause atomique avec matérialisation, mise à niveau
  non destructive `upgrade-dev`. 89 tests passants.

## 0.7 — 3 août 2026

- **Phase 3 — Sous-lot 3.2B** : activités et effets. Migration 0006 : passage au
  dénominateur canonique 36 (conversion sans perte des taux et restes de 3.2A) +
  `activity_definition`, `activity_allowed_location` (index uniques partiels),
  `activity` (une active/personnage). `start_activity` atomique (déplacements
  pièce par pièce + matérialisation + création), fin conditionnelle du sommeil
  (`max` puis `min` avec reste), clôture d'activité échue à son heure canonique,
  abandon, lecture pure. 104 tests passants.

## 0.8 — 3 août 2026

- **Phase 3 — Sous-lot 3.2C** : politique de décision déterministe et simulation.
  Migration 0007 `character_profile` (entiers, sans REAL ; profils neutres seedés),
  `DeterministicPolicy` pure (`Intent`/`DecisionResult`), `PolicyContext` immuable,
  urgence normalisée par produits croisés, gestion conjointe repos/énergie,
  destination déterministe, `SimulationEngine.run_to` (bornes canoniques, bornes
  simultanées ordonnées, heure cible en milieu d'activité, garde configurable,
  replis bornés). Démo 24 h : ~460 transitions (garde 2000), reproducible. 126 tests passants.

## 0.9 — 3 août 2026

- **Phase 3 — Sous-lot 3.3A** : correction de l'attente et accessibilité du sommeil.
  Attente **dynamique** : `Intent.duration_seconds` obligatoire et borné `1..MAX_IDLE`
  (8 h) pour `idle`, refusé pour `eat`/`clean`/`rest`/`sleep`. L'`idle` se termine à la
  première seconde où la décision changerait (franchissement d'un seuil / palier
  d'urgence / critique), calculée mathématiquement avec le reste rationnel (aucun
  tick par minute), sinon plafond `idle_safety_boundary`. Règle de sommeil naturelle :
  repos/énergie critique ⇒ sleep ; repos déficient ⇒ sleep ; seule énergie modérée
  ⇒ rest ; `rest_preference` ne bloque jamais le sommeil exigé. Aucun retunage de taux.
  Démo 24 h : **84** transitions (vs 460), **28** idle (vs 168), **128** matérialisations
  (vs 692), ≥ 1 sommeil de 8 h par habitante, aucune boucle, reproductible. 143 tests passants.

## 0.10 — 3 août 2026

- **Phase 3 — Sous-lot 3.3B1** : blessures de mobilité — état, causalité et
  récupération. Migration 0008 `injury` (sévérité entière /36, CHECK d'invariants
  `active`/`healed`, une seule active par index partiel, historique immuable), FK +
  `UNIQUE(world_id, cause_event_seq)` vers `canonical_event`, déclencheur de
  terminalité `healed`, `script_accident`/`injure_character`/`inflict_injury`
  (combiné atomique), `started_at = cause.occurred_at`, régimes de récupération
  typés `passive`/`rest`/`sleep`, reste rationnel, guérison à l'heure exacte,
  événements `scripted_accident`/`injury_occurred`/`injury_materialized`/
  `injury_healed`. Effets de mobilité reportés à 3.3B2. 164 tests passants.

## 0.11 — 3 août 2026

- **Phase 3 — Sous-lot 3.3B2** : effets mécaniques des blessures. Classification
  dérivée réutilisée (`level`/`SEV_LIGHT_MAX`/`SEV_MODERATE_MAX`), surcharge de
  déplacement modérée **500 milli-énergie par arête** (`MOVEMENT_SURCHARGE_MILLI`),
  matérialisation canonique de la blessure avant classification dans
  `CharacterEngine._move` (régime réellement actif), blocage canonique du
  déplacement en blessure sévère, `character_moved` enrichi
  (`base_energy_cost`/`injury_energy_surcharge`/`edge_count`/`total_energy_cost`/
  `injury_effect_level`), `seconds_to_level` (généralisation de `seconds_to_heal`),
  `recovery_regime` dans `activities.py`, matérialisation de la blessure aux
  frontières d'activité (`start_activity`/`advance_to`/`abort_activity`), politique
  avertie exactement à la frontière `severe→moderate` (idle dynamique borné),
  filtrage des destinations en niveau sévère (`_accessible`). Aucune migration.
  188 tests passants (164 existants + 24 nouveaux).

## 0.12 — 3 août 2026

- **Phase 3 — Sous-lot 3.3C** : reproductibilité finale et fermeture technique.
  Helper interne `WorldEngine._advance_clock` : chaque transition temporelle
  (`start_activity`, `advance_to`, `abort_activity`) pose atomiquement
  `simulated_now = cible` et `real_updated_at = Clock.now` dans sa transaction
  (rollback annule aussi l'horloge ; aucun `clock_updated`). Outils de
  comparaison `src/vivarium/repro.py` : `canonical_state_digest` (références par
  clés logiques, `character.name` inclus, rowids/UUID/muraux exclus),
  `raw_canonical_event_log` (journal brut complet), `structural_event_audit`
  (séquences continues, aucun trou/doublon, `occurred_at` monotones, JSON et
  causalités valides), `reproducible_semantic_projection` (faits significatifs,
  matérialisation exclue, `seq` absolu renuméroté, causalité normalisée vers la
  position relative de l'événement causal), `materialization_chain_audit`
  (objet D : exactitude mathématique de chaque chaîne de matérialisation —
  blessures recomptées depuis le régime, besoins recomptés depuis le taux
  déclaré et vérifiés contre le taux canonique des règles ; détecte les erreurs
  compensées de valeur et de reste), `max_seq` (invariant séparé),
  `SimulationRunReport`.
  Contrat `needs_materialized` enrichi : `rate_source` (`need_definition`/
  `activity`), `activity_type` (null en passif), `rate_nums`/`rate_dens` par
  besoin — le taux réellement appliqué est porté par l'événement pour une
  vérification non circulaire.
  Correction `occurred_at` canonique pour `needs_materialized` et
  `character_moved`. Scénarios 24 h (84 transitions), blessures, endurance 7 j
  (980 transitions) ; runs comparatifs A-G ; tests de pause/reprise/redémarrage,
  crash/rollback, délai mural, absence de frontière, erreurs compensées.
  Aucune migration, aucun RNG. 220 tests passants (188 + 32).

## 0.1 — 3 août 2026

- Création du dossier maître destiné à une IA programmeuse.
- Consolidation des cinq parties.
- Arbitrage des anciennes formulations sur population, habitat, temps, technicien et machine hôte.
- Ajout du contrat de lecture, du prompt de démarrage et des matrices séparées.
## Unreleased

- **Hugin/Munin V0** : ajout d’un read-model d’observation humaine borné,
  structuré et strictement lecture seule. Hugin sépare actes de parole et faits;
  Munin conserve l’ownership des états subjectifs et la chaîne de provenance.
  Aucun schéma, état persistant ou comportement runtime n’est ajouté.

- **Console de rodage Hugin/Munin V0.1** : ajout de `/observer`, de la route
  locale de lecture bornée, du focus canonique `current_state` et d’un planner
  naturel déterministe optionnel. Les preuves restent dépliables et aucune
  requête ne modifie la simulation.
