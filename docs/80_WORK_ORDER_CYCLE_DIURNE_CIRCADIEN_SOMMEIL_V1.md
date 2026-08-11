# Work order technique — fondations cycle diurne, circadien et sommeil V1

**Statut :** fondations additives autorisées ; cutover comportemental interdit.
**Source fonctionnelle :** `docs/79_R_D_CYCLE_DIURNE_CIRCADIEN_SOMMEIL.md`.
**Portée :** schéma, ownership, préparation et tests non comportementaux.

## Contrat de cette tranche

Cette tranche ne modifie ni `repos`, ni `energie`, ni les activités legacy,
ni la politique d'autonomie, ni le runtime vivant. Elle n'installe aucun
profil chiffré dans la résidence persistante et n'active aucun état
physiologique.

Le monde reste entièrement legacy tant qu'un cutover ultérieur, arrêté et
atomique, n'a pas été approuvé.

## Owners persistants

- `SleepPhysiologyFoundationService` possède les catalogues de calendrier,
  d'exposition et de biologie, leurs assignations, et l'état de préparation.
- `light_schedule_profile` décrit le cycle objectif de 24 h.
- `location_light_profile` décrit une propriété d'exposition du lieu ; ce
  n'est pas un état lumineux actuel.
- `sleep_biology_profile` est data-driven et classé `human_reference`,
  `generic_feline` ou `fictional_canon`.
- Les futurs `sleep_regulation_state` et `physical_capacity_state` ont leur
  propre propriétaire ; ils restent sans ligne tant que le cutover n'existe
  pas.
- `sleep_physiology_audit` est exclusivement technique et append-only. Il ne
  constitue jamais un `canonical_event`, une mémoire Munin ou une narration
  Hugin.

Les profils sont versionnés et immuables. Une correction future crée une
nouvelle version ou une nouvelle assignation, jamais une réécriture du passé.

## Lumière et histoire d'exposition

V1 ne crée aucun état dynamique de lampe, rideau ou éclairage simplement par
anticipation. La frontière correcte est néanmoins préservée : calendrier
objectif + propriété d'exposition du lieu sont séparés. Un futur état physique
qui modifie l'exposition aura son propriétaire canonique et devra constituer
une frontière d'intégration.

La phase circadienne sera le premier état intégrateur de l'exposition passée.
Si la fonction quantitative finalement retenue a besoin d'une histoire récente
supplémentaire, celle-ci devra être soit reconstruite depuis les causes
canoniques persistées, soit représentée par un état suffisant minimal détenu
par le propriétaire physiologique. Une lecture ne pourra jamais inventer cette
histoire rétroactivement.

## Préparation sans activation

`world_physiology_system` ne connaît ici que deux états : `inactive` et
`prepared`. `prepared` signifie qu'un opérateur a contrôlé une configuration
complète hors session runtime ; il n'a aucun effet comportemental.

La préparation exige :

- un calendrier lumineux assigné ;
- un profil d'exposition pour chaque lieu ;
- un profil biologique pour chaque personnage ;
- aucune session runtime ouverte.

La future activation ne fait pas partie de cette tranche. Elle devra, dans une
seule transaction après arrêt propre : valider la configuration, fixer
l'instant canonique d'activation, créer les états initiaux, écrire l'audit
technique `post_migration_initialization`, basculer le gate, et commuter tous
les consommateurs de `repos`/`energie` vers le nouveau chemin. Aucun événement
vécu ne sera produit par cette opération.

## Cutover explicitement bloqué

Le cutover reste interdit tant que les deux voies suivantes ne sont pas prêtes
et revues ensemble :

1. arbitrage volontaire où motif de sommeil, buts et intentions participent à
   un compromis dynamique, sans priorité absolue de catégorie ;
2. stabilité involontaire de l'éveil ayant une conséquence moteur bornée et
   causale lorsque la viabilité devient mauvaise.

Une intention active ne gagne pas automatiquement. Un motif de sommeil ne
gagne pas automatiquement. Ignorer le motif ne réduit ni l'homéostasie, ni ne
restaure le circadien, ni ne garantit un éveil durablement stable.

## Tests de sortie de tranche

- migrations 44 → fondations : forward-only, sans modification de l'historique
  canonique ;
- catalogues et assignations append-only ;
- préparation inerte : aucune activité, aucun état physiologique initialisé,
  aucun événement vécu ;
- préparation refusée si configuration incomplète ou session runtime ouverte ;
- validation des valeurs initiales purement en lecture ;
- préflight d'un monde migré de test toujours sain.

## Décisions différées avant cutover

- fonction quantitative d'homéostasie ;
- fonction circadienne et entrainment ;
- représentation supplémentaire éventuelle d'histoire lumineuse ;
- profils et conditions initiales de la résidence ;
- contrat exécutable d'arbitrage ;
- mécanisme et calibration minimale de stabilité d'éveil ;
- fin de sommeil et hard cap technique ;
- éventuelle stochasticité conditionnée.

Ces décisions sont des paramètres de modèle et de design à revoir, pas des
constantes biologiques implicites du code.
