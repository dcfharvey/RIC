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

- version logicielle : `0.0.1.dev0` (**pré-alpha**). Les numéros de documents
  et de commits ne sont pas des versions de produit; voir `docs/15_ROADMAP_ACTIVE.md` ;
- commencer par `git status --short` et `git log -1 --oneline` : un arbre propre
  signifie que cette passation décrit l'état de `HEAD` ;
- derniers lots : 4.2I (pipeline métier de changement préparé) puis 4.2J
  (exposition HTTP locale du même pipeline) ;
- migration courante : `0020_environment_blueprint.sql` ;
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
- aucune modification de l'interface visuelle dans les lots 4.2I/4.2J.

## Capacités récentes

- registre de composants versionnés, gabarits publiés et instances avec
  provenance figée ;
- cinq gabarits MVP : Sophie, Erika, Luna, Chuu et Patoune; pas encore
  instanciés comme résidentes réelles ;
- ressources génériques à bandes et effets déclaratifs, sans imposer une
  émotion ou narration ;
- objets portables, installations fixes et contenance objet‑dans‑objet,
  avec lieu effectif matérialisé, capacité et refus des cycles ;
- presets de lieux et connecteurs validés, publiés et immuables, prêts pour
  le futur instanciateur de blueprint ;
- blueprints versionnés et instanciation atomique d'un monde neuf, avec
  provenance logique figée des lieux et des connecteurs ;
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
`docs/20_PRESETS_ENVIRONNEMENT.md` et `docs/22_BLUEPRINTS_ENVIRONNEMENT.md`.
Le prochain lot recommandé est le connecteur à état simple, puis la traversée
validée et des scénarios d'acceptation inter-systèmes. Ne pas commencer par
modifier une habitante ou créer le monde MVP sans le protocole renforcé
correspondant.
