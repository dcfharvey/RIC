# Sélection et robustesse de calibration circadienne V1

Ce document rapporte une passe **inactive**, déterministe et reproductible du banc circadien.
Elle ne touche ni SQLite, ni le runtime, ni `repos`/`energie`, et ne transforme
aucune valeur en constante biologique ou en profil actif.

Commande :

```powershell
.venv\Scripts\python.exe -m vivarium sleep-calibration-bench --selection
```

## Famille H/C retenue pour la future production

La recommandation V1 est **`additive`** : `H + k × influence circadienne`,
passé dans la même réponse lisse que le banc. C'est un choix de parcimonie et
d'interprétabilité [D], pas une affirmation sur la combinaison biologique
littérale de Process S et C.

La famille `sensitivity_modulated` reste seulement un comparateur de banc. Sur
les mêmes états synthétiques, les deux passent les falsifications communes :
cycle normal, H élevée malgré une phase favorable à l'éveil, sieste, privation
et sommeil diurne post-privation. Les trajectoires de H, phase, lumière,
free-running et zeitgeber leur sont communes : ces familles ne modifient que
la projection dérivée de propension.

La divergence notable apparaît à H modérée en phase défavorable à l'éveil :
la famille de sensibilité rend alors une transition plus graduelle. Aucun
phénomène contractuel du V1 ne demande cette propriété, tandis que la forme
additive l'exprime avec un seul poids directement lisible. La famille de
sensibilité n'est donc pas retenue avant le raccord futur.

## Région humaine explorée

Les valeurs ci-dessous sont des points de test [C/D], non des intervalles
biologiques humains. Le banc exécute chaque axe sur les falsifications V1,
puis une grille conjointe période intrinsèque × forcing lumineux.

| Groupe | Voisinage exploré | Lecture actuelle |
|---|---|---|
| `tau_wake` | 14 h, 18 h, 22 h | Les trois conservent les phénomènes ; faiblement identifié par ce banc. |
| `tau_sleep` | 2 h, 3 h, 4 h | Les trois conservent les phénomènes ; à contraindre plus tard par des trajectoires de sommeil réelles. |
| période × forcing | 23 h 30 à 24 h 40 × 3 000 à 6 000 | Couplage sensible : 23 h 45, 24 h 10 et 24 h 20 restent verts sur toute la grille. 24 h pile ne permet pas le free-running requis ; les bords demandent davantage de forcing. |
| demi-saturation / occlusion | 20–45 k / 2–10 k | Tous les points locaux passent : faiblement identifiables, non « redondants ». |
| poids circadien additif | 0,16–0,32 | Tous les points locaux passent ; il reste un paramètre de calibration, pas une constante. |
| stabilité | poids H 0,65–0,90 ; bandes basse/référence/haute | Sensible : poids H 0,65 et bandes hautes ne peuvent plus atteindre correctement `critical` dans le scénario extrême. |
| P | coût 0,015–0,035 ; récupération rest 0,030–0,060 ; sommeil 0,050–0,090 | Les points passent la séparation P/H ; les cinétiques restent faiblement identifiées hors d'activités physiques concrètes. |

La région recommandée avant revue finale est un **voisinage**, centré sur le
candidat actuel 18 h / 3 h / 24 h 10 / forcing 5 000, et non un optimum.
La grille conjointe est conservée parce que période et forcing sont
partiellement compensatoires : les ajuster isolément masquerait la fragilité.

## Falsifications rencontrées

- période exactement 24 h : plus de free-running observable sous ce contrat ;
- 24 h 40 isolé : réentrainment insuffisant avec le forcing de référence ;
- poids homéostatique de stabilité à 0,65 : physiologie extrême non assez
  critique dans le scénario d'interruption ;
- bandes de stabilité hautes : même falsification de non-viabilité.

Ces frontières ne déclenchent pas l'ajout de coefficients : elles limitent la
région V1 et rendent le couplage visible.

## Profil félin générique

Trois hypothèses de cinétique (plus lente, référence, plus rapide) conservent
plusieurs épisodes dans le sandbox d'occasions génériques. C'est une capacité
du mécanisme, jamais une prédiction d'un nombre d'épisodes, une physiologie
féline chiffrée ou une règle pour Patoune. Aucun ultradien, crépuscularité ou
script nominatif n'est ajouté.

## Ce qui reste ouvert

- Les constantes versionnées restent des ancres de calibration [C/D].
- Les données futures de résidence pourront contraindre les cinétiques H/P,
  l'intensité lumineuse effective et l'arbitrage, mais pas rétroactivement.
- Le choix `additive` est arrêté pour préparer le raccord ; les paramètres
  restent révisables seulement par une nouvelle passe de calibration/R&D.
