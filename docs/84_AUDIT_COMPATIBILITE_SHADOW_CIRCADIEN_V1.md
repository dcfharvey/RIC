# Lot 4 — audit de compatibilité et shadow circadien V1

**Statut :** audit et banc synthétique ; cutover comportemental interdit.

**HEAD audité :** `1da3f7471d8ce4b643fd87f5937cc0ce51a3f8e6`

Ce lot ne démarre pas le runtime, ne lit pas `data/vivarium-rodage.sqlite`, ne
consulte pas la session `runtime_session.id = 4` et ne modifie ni la résidence
réelle ni le schéma 44. Les APIs du banc sont pures ou opèrent sur un double de
moteur en mémoire.

## Consommateurs legacy recensés

Le manifeste exécutable est `vivarium.circadian_shadow.LEGACY_CONSUMERS` et
`audit_legacy_consumers()` vérifie les chemins, les symboles et les occurrences
non listées sous `src/vivarium`.

| Groupe | Propriétaires actuels | Rôle | Traitement au cutover |
|---|---|---|---|
| comportement | `DecisionPolicy`, `SimulationEngine`, `ActivityEngine`, `MotivationService`, `AttentionService`, `DecisionFrameService` | `repos`/`energie` sont encore des causes exécutables de sommeil/repos | commutation atomique vers motif, arbitrage, fin de sommeil et réévaluation |
| capacité physique | `CharacterEngine`, coûts `ActivityEngine` | `energie` paie encore certains déplacements et les taux d'activité | commutation simultanée vers P, sans conversion de valeur |
| observabilité | `AdminReadService` | projection de la colonne legacy `energy` | nouveau champ P éventuel, valeurs legacy conservées comme historique |
| préservation | `WorldEngine`, `WorldRulesService`, `InstanceService`, `Seed`, `Reproducibility` | définitions, bootstrap et digests historiques | conserver l'archive et la provenance ; ne pas piloter la physiologie |

`circadian_model.py` contient également une garde négative : le noyau pur ne
doit jamais écrire ni convertir les besoins legacy.

## Shadow volontaire et stabilité involontaire

`SleepMotiveProjection.from_propensity()` offre uniquement le candidat générique
`sleep_regulation` depuis la propension additive. P n'est pas une entrée du
motif. `arbitrate_voluntary()` compare les scores explicites des options ; une
intention peut gagner, le motif peut gagner, et une égalité demande une
réévaluation. Aucun ordre `active_intention > motives[0]` n'est exécutable.

`wake_stability_eligibility()` ne produit qu'une cause et une éligibilité. Le
double `SyntheticActivityEngine` applique ensuite une transition bornée vers
`aborted`; les appels répétés et les reconstructions après restart sont
idempotents. La physiologie n'écrit pas une activité et ne force pas un
sommeil.

La stimulation réduit temporairement l'instabilité projetée, mais ne modifie
pas H, φ ou P et ne garantit pas une veille indéfinie. `repos` n'est jamais
converti en H et `energie` n'est jamais convertie en P.

## Falsifications livrées

- intention gagnante et motif gagnant dans deux cadres explicites ; égalité sans
  priorité de catégorie ;
- P différent avec H/φ identiques : motif identique ;
- criticité bornée, une seule conséquence moteur et aucune tempête après
  restart ;
- stimulation protectrice de la manifestation seulement, sans remise à zéro
  de H/φ/P ;
- audit statique exhaustif des consommateurs et des groupes de commutation.

Le prochain travail est une revue Sol séparée du contrat d'arbitrage
exécutable, de la fin de sommeil, de la migration des coûts vers P et du
cutover atomique. Aucun de ces éléments n'est engagé ici.
