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

## État vérifié

- version logicielle : `0.0.2.dev0` (**pré-alpha**). Les numéros de documents
  et de commits ne sont pas des versions de produit; voir `docs/15_ROADMAP_ACTIVE.md` ;
- commencer par `git status --short` et `git log -1 --oneline` : un arbre propre
  signifie que cette passation décrit l'état de `HEAD` ;
- derniers lots : 4.2I (pipeline métier de changement préparé) puis 4.2J
  (exposition HTTP locale du même pipeline) ;
- migration courante : `0023_character_possession.sql` ;
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
- aucune modification de l'interface visuelle dans les lots 4.2I/4.2J.

## Capacités récentes

- registre de composants versionnés, gabarits publiés et instances avec
  provenance figée ;
- cinq résidentes MVP : Sophie, Erika, Luna, Chuu et Patoune, instanciées
  ensemble par le monde d'intégration atomique ;
- ressources génériques à bandes et effets déclaratifs, sans imposer une
  émotion ou narration ;
- contrat fermé moteur–cognition v1 : une intention de traversée peut être
  acceptée ou refusée sans LLM, avec provenance sur le fait canonique ;
- perception factuelle locale : candidates immuables, limitées à la présence,
  objets visibles et connecteurs adjacents de l'observateur ;
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

Le banc d'essai minimal est maintenant livré (`vivarium.bench`) : scénarios
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
