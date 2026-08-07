# Passation courante — Vivarium social

**Mise à jour :** 6 août 2026
**But :** point d'entrée opérationnel pour une nouvelle instance de Codex.
Lire ensuite `README.md`, `docs/00_DOSSIER_MAITRE_IA.md`, les documents de lot
cités et le diff Git avant toute écriture.

## Direction non négociable

> Exécution rigoureuse, création flexible.

Le moteur canonique est l'autorité unique sur les faits et leurs conséquences.
Le LLM proposera plus tard intentions, interprétations et paroles, mais ne
écrira jamais directement dans SQLite et ne créera pas de fait non validé.

**Méthode obligatoire :** avant tout nouveau système vivant, cognitif, social
ou physique, consulter la littérature scientifique ou technique pertinente,
séparer résultats robustes, débats ouverts et choix d'ingénierie, puis conserver
sources et limites dans la documentation du lot. Voir DEC-036 dans
`docs/01_REGISTRE_DECISIONS.md`.

## État vérifié

- version logicielle : `0.1.0a6` (**MVP alpha, cohérence temporelle des décisions LLM**). Les numéros de documents
  et de commits ne sont pas des versions de produit; voir `docs/15_ROADMAP_ACTIVE.md` ;
- commencer par `git status --short` et `git log -1 --oneline` : un arbre propre
  signifie que cette passation décrit l'état de `HEAD` ;
- derniers lots : 4.2I (pipeline métier de changement préparé) puis 4.2J
  (exposition HTTP locale du même pipeline) ;
- migration courante : `0033_orchestrator_cursor.sql` ;
- dernier test complet avant 4.2J : **469 passed** ;
- tests HTTP ciblés après 4.2J : **112 passed** ;
- test complet après 4.2J : **477 passed** ;
- test complet après 4.2K : **486 passed** ;
- test complet après le banc minimal : **495 passed** ;
- test complet après fermeture sûre de passage : **502 passed** ;
- test complet après politique topologique : **504 passed** ;
- test complet après objets et contenance : **514 passed** ;
- test complet après presets d'environnement : **520 passed** ;
- test complet après blueprints d'environnement : **525 passed** ;
- test complet après connecteurs à état : **528 passed** ;
- test complet après traversée validée : **532 passed** ;
- test complet après règles standard de monde : **535 passed** ;
- test complet après calibration de Chuu et profils de ressource atomiques :
  **541 passed** ;
- test complet après catalogue et blueprint de résidence : **547 passed** ;
- test complet après assemblage du monde d'intégration : **551 passed** ;
- test complet après possession de personnage : **559 passed** ;
- test complet après contrat d'action moteur–cognition v1 : **564 passed** ;
- test complet après perception factuelle locale : **568 passed** ;
- test complet après attention déterministe : **573 passed** ;
- test complet après flux d'événements perceptibles : **576 passed** ;
- test complet après première trace subjective : **578 passed** ;
- test complet après rappel subjectif minimal : **579 passed** ;
- test complet après audit subjectif séparé : **580 passed** ;
- test complet après croyances sourcées et révisions auditées : **624 passed** ;
- test complet après états affectifs subjectifs : **629 passed** ;
- test complet après relations, limites et permissions : **634 passed** ;
- test complet après cadre décisionnel initial : **636 passed** ;
- test complet après scènes sociales structurées : **638 passed** ;
- test complet après orchestrateur autonome initial : **640 passed** ;
- test complet après banc vivant jetable : **642 passed** ;
- test complet après console d'observation du banc vivant : **643 passed** ;
- test complet après banc de calibration locale LLM : **650 passed** ;
- test complet après premier tour social LLM : **658 passed** ;
- test complet après banc social multi-tours : **664 passed** ;
- test complet après porte de prévol MVP : **670 passed** ;
- test complet de livraison alpha : **686 passed** ;
- test complet après frontière LLM locale et banc de fumée : **592 passed** ;
- test complet après politique pure d'admissibilité des appels LLM :
  **599 passed** ;
- test complet après journal append-only d'admission LLM : **602 passed** ;
- test complet après routeur LLM événementiel et fumée intégrée :
  **606 passed** ;
- test complet après banc de calibration des appels LLM : **609 passed** ;
- test complet après première projection de motifs physiologiques :
  **613 passed** ;
- test complet après première disposition canonique de personnalité :
  **616 passed** ;
- test complet après valeurs et préférences initiales : **618 passed** ;
- test complet après objectifs et intentions persistantes : **620 passed** ;
- test complet après activités autonomes événementielles : **704 passed** ;
- test complet après correction de la latence temporelle LLM : **706 passed** ;
- aucune modification de l'interface visuelle dans les lots 4.2I/4.2J.

## Correctif alpha 0.1.0a2

- le tableau d'observation se rafraîchit localement toutes les deux secondes
  quand son onglet est visible; il n'exécute aucune commande ni écriture;
- l'arrivée initiale déjà déclarée dans le contrat d'admission est maintenant
  raccordée : chaque résidente sapiente reçoit une occasion unique, sourcée et
  validée de traverser avant l'initialisation des activités automatiques;
- Patoune reste hors des appels LLM; une arrivée déjà dépassée ou un retry est
  refusé/dédupliqué explicitement, jamais rejoué silencieusement.

Voir `docs/59_CORRECTIF_ALPHA_0_1_0A2.md`.

Validation de code : **692 passed**. Un lancement réel local a confirmé les
quatre décisions d'arrivée Gemma, les traversées validées et le démarrage de
scènes; l'inspection graphique reste à refaire si l'interface évolue encore.

## Livraison alpha 0.1.0a1

- `ActionOptionService` ne propose une traversée visible qu'après une nouvelle
  vérification du connecteur par le moteur;
- `SocialSceneCycle` transforme une co-présence canonique en scène bornée,
  sans jamais convertir une parole en fait. La première scène est ancrée dans
  le contexte initial commun; Patoune est hors de la boucle sapiente;
- `MVPRuntime` assemble simulation, orchestrateur et scène au plus une fois par
  tick, respecte la pause et interrompt proprement les scènes à l'arrêt;
- `mvp-init`, `mvp-preflight` et `mvp-run` constituent le parcours opérateur.
  Le dernier expose la console locale et peut activer Gemma via LM Studio;
- le tableau local affiche les scènes et leurs paroles en plus du journal;
- l'adaptateur local normalise seulement la forme Gemma
  `action: "greet"`/`act_kind: "greet"` en acte de parole contractuel;
- documentation de portée : `docs/58_MVP_ALPHA_0_1_0A1.md`.

Pour reproduire un lancement sans toucher une histoire existante :

```powershell
.\.venv\Scripts\python.exe -m vivarium mvp-init --db data\vivarium-alpha.sqlite
.\.venv\Scripts\python.exe -m vivarium mvp-run --db data\vivarium-alpha.sqlite --enable-local-llm
```

Le test local réel de cette livraison a créé une résidence jetable, effectué
quatre tours Gemma admis et enregistrés, fermé la scène à sa borne, puis passé
le prévol. L'interface a aussi été inspectée avec une scène réellement
enregistrée; pause/reprise et le panneau de scène ont répondu.

## Capacités récentes

- registre de composants versionnés, gabarits publiés et instances avec
  provenance figée ;
- cinq résidentes MVP : Sophie, Erika, Luna, Chuu et Patoune, instanciées
  ensemble par le monde d'intégration atomique ;
- ressources génériques à bandes et effets déclaratifs, sans imposer une
  émotion ou narration ;
- contrat fermé moteur–cognition v2 : une traversée ou une activité disponible
  peut être acceptée ou refusée sans autorité du LLM, avec provenance sur le
  fait canonique et rollback intégral ;
- perception factuelle locale : candidates immuables, limitées à la présence,
  objets visibles et connecteurs adjacents de l'observateur ;
- attention déterministe minimale : besoins sous seuil, blessure et effets de
  ressources propres à l'observateur, plus indices perceptibles, classés dans
  une liste bornée sans mémoire ni émotion ;
- flux d'événements perceptibles directs : curseur canonique en lecture seule,
  faits propres à la résidente réduits avant export; aucune reconstruction
  spéculative des événements passés d'autrui ;
- première mémoire subjective : migration et service de trace encodée, rappel
  privé borné et audit séparé sont livrés; consolidation, oubli, croyances et
  mémoire narrative restent futurs. Voir `docs/38_PLAN_PREMIERE_MEMOIRE_SUBJECTIVE.md` ;
- frontière LLM locale livrée : contexte borné, sortie JSON strictement vérifiée,
  refus des actions non perceptibles et passage obligé par le contrat canonique;
  une boucle autonome événementielle sur nouvel `idle`, sans écriture LLM
  directe. Le diagnostic `llm-status` et l'essai
  jetable `llm-smoke` utilisent désormais l'API native LM Studio avec raisonnement
  désactivé pour Gemma. Voir `docs/40_ADAPTATEUR_LLM_LOCAL.md`.
- porte d'appel LLM événementielle : première politique pure livrée;
  déclencheurs fermés, déduplication, debounce et budget sont vérifiables sans
  réseau ni écriture canonique. Ses admissions techniques sont append-only,
  idempotentes et distinctes des traces subjectives. Le routeur ne laisse
  actuellement passer qu'un événement direct réellement perceptible; les autres
  motifs restent fermés jusqu'à leur contrat source. Voir
  `docs/41_PLAN_PORTE_APPEL_LLM.md`.
- banc de calibration des chronologies d'appels livré, sans réseau ni SQLite;
  il compare des limites candidates avant toute décision de cadence produit.
  Voir `docs/42_BANC_CALIBRATION_APPELS_LLM.md`.
- calibration locale répétée livrée : chaque tour réel Gemma repart d'une
  base mémoire et d'une horloge identiques, puis rapporte durée, contrat,
  décision, validation et panne explicite. Voir
  `docs/54_CALIBRATION_LOCALE_LLM.md`.
- premier tour social LLM livré : scène active et co-localisée, contexte
  subjectif borné, admission `scene_turn`, schéma de parole distinct,
  validation de destinataire et idempotence. Le texte ne produit encore aucun
  effet social automatique. Voir `docs/55_TOUR_SOCIAL_LLM.md`.
- banc social multi-tours livré : des occasions alternées et bornées testent
  une courte conversation sans créer d'histoire partagée. Voir
  `docs/56_BANC_SCENE_SOCIALE.md`.
- porte de prévol MVP livrée : `python -m vivarium mvp-preflight --db <base>`
  inspecte strictement en lecture seule l'intégrité SQLite, le casting, le
  contexte et les audits de journaux d'un monde candidat. Voir
  `docs/57_STRATEGIE_QUALITE_MVP.md`.
- première projection de candidats de motifs physiologiques livrée; pression,
  urgence, importance et actions possibles sont bornées par le contexte
  déterministe, sans inventer plaisir, coût ou personnalité. Voir
  `docs/43_MOTIFS_PHYSIOLOGIQUES.md`.
- première disposition de personnalité livrée : Big Five, attachement général,
  distributions et signatures situationnelles issus des gabarits v2 immuables;
  aucune action n'est imposée par les traits. Voir
  `docs/44_PERSONNALITE_CANONIQUE.md`.
- idées retenues de scénarios et de systèmes futurs : jeux à information privée,
  effort physique et affrontements arbitrés; voir
  `docs/39_BACKLOG_SCENARIOS_ET_SYSTEMES.md`.
- objets portables, installations fixes et contenance objet‑dans‑objet,
  avec lieu effectif matérialisé, capacité et refus des cycles ;
- possession physique générique : un objet portable suit son personnage sans
  être confondu avec un vêtement équipé; les quatre résidentes sapientes ont
  chacune un téléphone initial ;
- presets de lieux et connecteurs validés, publiés et immuables, prêts pour
  le futur instanciateur de blueprint ;
- blueprints versionnés et instanciation atomique d'un monde neuf, avec
  provenance logique figée des lieux et des connecteurs ;
- connecteurs de monde identifiés et journalisés, avec états `available`,
  `closed` et `blocked` sans confusion avec le graphe brut ;
- `TraversalEngine` valide le franchissement par connecteur; les déplacements
  d'un monde blueprint respectent aussi ces états et journalisent la cause ;
- les règles standard de résidence s'installent hors seed, avec vérification
  stricte et idempotence, prêtes pour le monde d'intégration ;
- les ressources peuvent recevoir d'un coup leurs bandes et effets déclaratifs;
  Chuu dispose de sa calibration MVP, sans branche spécifique du moteur ;
- le catalogue de la résidence initiale est publié, validé et instanciable;
  voir `docs/31_BLUEPRINT_RESIDENCE_INITIALE.md` ;
- plan admin pour `rename_world` : hash, expiration, version optimiste par
  séquence canonique, audit séparé, application atomique et retry idempotent ;
- plan admin pour `add_link` : passage entre deux lieux existants, une ou deux
  arêtes, impact topologique explicite et même protocole de confirmation ;
- routes HTTP locales livrées par 4.2J : prepare, validate,
  impact, confirm; jeton local obligatoire y compris pour les deux lectures.

## Verrous de conception utiles

- Casting MVP : Sophie et Erika (humaines sapientes), Luna (louve anthro
  sapiente), Chuu (slime sapiente dont la cognition dépend de l'hydratation),
  Patoune (chatte noire non sapiente). Voir `docs/08_CASTING_MVP.md`.
- Les ressources servent à la fois aux capacités directes (munitions, mana,
  hydratation) et aux signaux généraux (stress/nicotine, likes/influenceuse).
- Les mutations profondes de personnage exigeront versions de cible, impact et
  snapshot : ne pas les ajouter par la voie de renommage actuelle.
- L'interface peut attendre; lorsque touchée, elle doit être inspectée
  visuellement. Style : console sombre, dense et lisible, jamais dashboard SaaS
  ou papier texturé.
- Le monde d'intégration pré-MVP doit être une base propre, séparée des mondes
  techniques et des exécutions de banc d'essai. Le MVP est le simulateur social
  présentable atteint après les couches vivantes. Voir `docs/15_ROADMAP_ACTIVE.md`.
- La trajectoire vers cognition est détaillée dans
  `docs/21_TRAJECTOIRE_VERS_COGNITION.md`; commencer par le blueprint et son
  instanciateur atomique, pas par un appel LLM.

## Prochaine action recommandée

L'alpha est livré. La prochaine étape n'est pas une nouvelle grosse couche :
faire tourner quelques sessions observées, conserver les bases qui comptent,
et classer les défauts ou frictions mesurés avant de choisir le lot de bêta.
Les conséquences sociales causales, la vie autonome générale et les systèmes
futurs restent explicitement hors de la version actuelle. Pour l'historique
antérieur, le banc d'essai minimal est maintenant livré (`vivarium.bench`) : scénarios
isolés, actions déclaratives fermées, rapports/audits et comparaison de runs.
Les objets, leur contenance, les presets et les blueprints d'environnement sont
aussi livrés; voir `docs/19_OBJETS_ET_CONTENANCE.md`,
`docs/20_PRESETS_ENVIRONNEMENT.md`, `docs/22_BLUEPRINTS_ENVIRONNEMENT.md` et
`docs/23_CONNECTEURS_ETAT.md` et `docs/24_TRAVERSEE_VALIDEE.md`. Le prochain
le monde d'intégration peut désormais être assemblé atomiquement; voir
`docs/32_ASSEMBLAGE_MONDE_INTEGRATION.md`. Les cinq résidentes arrivent ensemble
à l'entrée extérieure, à côté de la boîte aux lettres. Voir
`docs/25_REGLES_MONDE_STANDARD.md` et
`docs/26_CALIBRATION_CHUU.md` et `docs/27_CONTEXTE_INITIAL_RESIDENTES.md`.
Elles savent uniquement qu'elles ont volontairement accepté cette colocation
financée avec allocation; les relations initiales sont neutres. La résidence
prévue comporte aussi une buanderie; sa gestion fonctionnelle de vêtements est
un lot environnemental ultérieur, décrit dans `docs/28_VETEMENTS_ET_BUANDERIE.md`.
L'inventaire concret de la résidence est dans
`docs/29_INVENTAIRE_RESIDENCE_INITIALE.md`; le plan de ses connexions est suivi
dans `docs/30_PLAN_SPATIAL_RESIDENCE.md` et sa recette publiée dans
`docs/31_BLUEPRINT_RESIDENCE_INITIALE.md`. Ne pas créer le monde MVP sans le
protocole renforcé correspondant.
