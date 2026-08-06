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

- commencer par `git status --short` et `git log -1 --oneline` : un arbre propre
  signifie que cette passation décrit l'état de `HEAD` ;
- derniers lots : 4.2I (pipeline métier de changement préparé) puis 4.2J
  (exposition HTTP locale du même pipeline) ;
- migration courante : `0015_admin_change_actions.sql` ;
- dernier test complet avant 4.2J : **469 passed** ;
- tests HTTP ciblés après 4.2J : **112 passed** ;
- test complet après 4.2J : **477 passed** ;
- test complet après 4.2K : **486 passed** ;
- aucune modification de l'interface visuelle dans les lots 4.2I/4.2J.

## Capacités récentes

- registre de composants versionnés, gabarits publiés et instances avec
  provenance figée ;
- cinq gabarits MVP : Sophie, Erika, Luna, Chuu et Patoune; pas encore
  instanciés comme résidentes réelles ;
- ressources génériques à bandes et effets déclaratifs, sans imposer une
  émotion ou narration ;
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

## Prochaine action recommandée

Le prochain changement utile est la **fermeture** d'un passage : il doit analyser
si des lieux deviennent inaccessibles avant confirmation. Ne pas commencer par
modifier une habitante ou créer le monde MVP sans le protocole renforcé
correspondant.
