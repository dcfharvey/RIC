# Banc de calibration circadien V1

Ce banc est une couche déterministe **inactive** :

```text
paramètres versionnés + causes objectives synthétiques
-> H / phase / capacité / projections dérivées
-> rapport de falsification
```

Il n'ouvre aucune résidence, ne crée aucune base persistante, ne lit pas
`repos` ou `energie`, ne contacte pas de LLM et ne peut pas activer le domaine.

Commande :

```powershell
.venv\Scripts\python.exe -m vivarium sleep-calibration-bench
```

## Modèle testé

- Éveil : `H' = 1 - (1-H) exp(-dt/tau_wake)`.
- Sommeil : `H' = H exp(-dt/tau_sleep)`.
- Phase : période intrinsèque plus forcing lumineux saturant et dépendant de
  la phase. La sinusoïde est une abstraction RIC [C], pas une PRC humaine
  littérale.
- La lumière effective résulte du niveau environnemental, de l'exposition du
  lieu, de la sensibilité du profil et d'une atténuation forte pendant le
  sommeil/occlusion.
- La propension compare deux familles réellement distinctes : additive
  `H + influence C`, et une famille où `C` module la **sensibilité** de la
  réponse lisse à `H`. Le banc cherche explicitement le meilleur poids additif
  simple et refuse l'alternative si cette reparamétrisation suffit à la
  reproduire. Il n'en maintient jamais deux dans le runtime.
- La stabilité applique une réduction de stimulation strictement bornée et une
  porte anti-répétition par activité. Dès que la physiologie brute atteint la
  bande `critical`, la stimulation peut réduire la manifestation continue mais
  ne peut plus retirer la conséquence moteur potentielle. Elle ne force pas
  `sleep`.

## Provenance des candidats chiffrés

Les chiffres de `human_reference_candidate.v1` sont des **ancres de
calibration RIC** [C/D]. Ils servent à produire des protocoles falsifiables,
pas à déclarer une physiologie humaine mesurée. La période candidate est
proche de 24 h sans copier 24,18 h. Les constantes homéostatiques ne copient
pas les plages de la littérature. L'amplitude lumineuse candidate a été
retenue parce que le banc phase-locke sous deux zeitgebers, pas comme mesure
biologique.

`generic_feline_hypothesis.v1` est explicitement [C] : ses cinétiques
différentes testent la possibilité d'épisodes plus distribués. Elles ne sont
ni une donnée féline précise, ni une règle crépusculaire, ni une règle pour
Patoune.

## Falsifications présentes

- convergence numérique au découpage sous causes constantes, y compris des
  frontières non alignées : H/P sont identiques à l'arrondi machine et la
  phase doit rester sous `1e-8` tour ;
- durée nulle = gel complet ;
- free-running sans zeitgeber ;
- phase-lock sous zeitgeber stable, puis réentrainment graduel vers un lock
  différent après déplacement du zeitgeber ;
- forcing lumineux de signe dépendant de la phase ;
- atténuation pendant le sommeil ;
- nuit normale et dissipation de H dans une équation de sommeil diurne ; la
  propension post-privation est testée séparément, sans forcer la décision ;
- `rest` agit sur P, tandis que seul `sleep` dissipe H ;
- P ne modifie pas la propension ;
- comparaison des deux familles de propension avec test explicite de
  non-équivalence à un simple poids additif ;
- stabilité critique : une interruption au plus par activité et stimulation
  incapable d'annuler entièrement une instabilité sévère ;
- accumulation pendant une restriction répétée ;
- absence volontaire de mémoire cachée après convergence de `H`, `phi` et `P` ;
- plusieurs épisodes possibles dans un sandbox d'occasions génériques pour le
  profil félin hypothétique.

Le sandbox félin n'est pas une prévision comportementale ni un script : il
vérifie seulement que le mécanisme peut proposer plusieurs épisodes lorsqu'il
rencontre des occasions appropriées. Une convergence complète de `H`, `phi`
et `P` met fin à l'information historique que ce modèle markovien peut
légitimement conserver : aucune dette chronique supplémentaire n'est fabriquée
pour contourner cette limite.

## Trajectoires rapportées

Le JSON du banc conserve les séries, pas seulement un verdict : phase quotidienne
en free-running, phase quotidienne avant/après déplacement du zeitgeber, H sous
restriction puis récupération, stabilité sans/avec stimulation maximale, et
paires de sorties des deux familles de propension. Ces traces sont des artefacts
de calibration temporaires : elles ne deviennent ni canon, ni état subjectif.
