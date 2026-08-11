# R&D — Cycle diurne, circadien et régulation veille–sommeil

**Version R&D :** 1.0  
**Date :** 11 août 2026  
**Référence logicielle vérifiée :** `0.1.0a15`, schéma 44, HEAD de départ `802a073f44467698a7d206aa8fa7cd22602642a0`  
**Statut :** contrat scientifique et fonctionnel consolidé après deux contre-audits adversariaux et un audit quantitatif ciblé. Ce document ne prescrit ni architecture Python/SQLite, ni migration concrète, ni équations finales, ni ordre d'implantation. Codex reste autorité sur la traduction technique réelle.

---

## 1. But

RIC possède une horloge canonique, mais son alpha actuel ne possède pas encore de véritable cycle diurne physiologiquement opérant ni de rythme circadien individuel. Le but de ce dossier est de définir le **plus petit modèle fonctionnel défendable** permettant de produire des rythmes veille–sommeil plausibles, déphasables, adaptatifs et falsifiables sans confondre :

```text
heure du monde
≠ lumière effectivement reçue
≠ état circadien
≠ homéostasie de sommeil
≠ capacité physique
≠ propension sommeil/éveil
≠ somnolence subjective
≠ motivation
≠ décision
≠ action
```

Le cadre scientifique principal est inspiré du Two-Process Model de la régulation du sommeil, mais RIC **ne prétend pas simuler littéralement Process S, Process C, le SCN, la SWA EEG ou une architecture neuronale réelle**. Le modèle est une abstraction fonctionnelle contrainte par la littérature.

---

## 2. Légende épistémique

Les affirmations du dossier sont classées ainsi :

- **[A] Résultat empirique** : observation relativement robuste dans la littérature pertinente.
- **[B] Conclusion raisonnable mais incertaine** : synthèse compatible avec les données, sans être une loi universelle.
- **[C] Hypothèse de modélisation RIC** : abstraction choisie pour reproduire des phénomènes utiles.
- **[D] Choix de design/ingénierie** : décision de portée, calibration, garde-fou ou implantation; ne doit jamais être présentée comme science.

Une valeur numérique publiée peut être [A] dans son protocole d'origine et rester **inappropriée comme constante RIC**.

---

## 3. État alpha vérifié et problème de double comptage

### 3.1 Besoins actuels

L'alpha possède quatre besoins génériques : `satiete`, `repos`, `energie`, `hygiene`. Leur évolution est une réserve numérique à taux rationnels simples. `repos` et `energie` diminuent passivement et augmentent sous certaines activités.

Le seed actuel applique notamment :

```text
passif : repos -60/36 s ; energie -50/36 s
rest    : repos +30/36 s ; energie +27/36 s
sleep   : repos +80/36 s ; energie +50/36 s
```

### 3.2 Politique actuelle

La politique alpha utilise directement ces déficits :

- `repos` critique ou `energie` critique peut mener à `sleep`;
- `repos` déficient mène naturellement à `sleep`;
- `energie` seule modérément déficiente mène à `rest`.

L'heure du jour et une phase circadienne n'entrent pas dans cette décision.

### 3.3 Fin de sommeil actuelle

Le sommeil alpha est planifié jusqu'à l'atteinte simultanée de deux cibles :

```text
repos   >= 98 000
energie >= 95 000
```

avec une durée maximale de `28 800 s` (8 h).

Ces cibles sont des règles d'ingénierie alpha, pas une physiologie scientifique.

### 3.4 Diagnostic

`repos` mélange actuellement plusieurs sens : récupération, « restedness », déclencheur comportemental et approximation inversée d'une pression de sommeil. `energie` mélange encore capacité physique et régulation de repos/sommeil.

Ajouter simplement une nouvelle homéostasie de sommeil et un circadien par-dessus ces deux variables créerait un double ou triple comptage.

**Décision fonctionnelle :** la sémantique actuelle doit être nettoyée avant toute intégration circadienne.

---

## 4. Invariants non négociables

```text
cycle diurne objectif ≠ exposition lumineuse reçue
exposition lumineuse ≠ phase circadienne
phase circadienne ≠ homéostasie de sommeil
homéostasie de sommeil ≠ capacité physique
état physiologique ≠ sensation subjective
sensation subjective ≠ motivation
motivation ≠ action
relation entre S/C ≠ ordre de dormir
energie basse ≠ somnolence
repos legacy ≠ Process S
rest éveillé ≠ sleep
LLM propose, moteur valide
un seul propriétaire persistant par état
```

Autres contraintes :

1. Aucun composant cognitif ne peut écrire directement un état physiologique canonique.
2. Une agente peut vouloir rester éveillée malgré une forte pression de sommeil; sa volonté ne garantit pas une capacité physiologique stable à le faire indéfiniment.
3. Dormir le jour et rester éveillé la nuit doivent rester possibles.
4. Le rythme circadien ne crée pas directement une croyance, une émotion ou une action.
5. Quand le temps canonique est gelé, les états physiologiques dépendant de ce temps doivent également être gelés. Le contrat alpha de non-rattrapage hors ligne reste applicable.
6. Aucun comportement de sommeil propre à un personnage ne doit être codé par identité si un mécanisme générique paramétrable suffit.

---

## 5. Fondations empiriques

### 5.1 [A/B] Deux influences temporelles distinctes mais interactives sont nécessaires

Le Two-Process Model distingue historiquement une composante homéostatique liée à l'historique veille–sommeil et une composante circadienne liée à l'horloge biologique. Le cadre demeure central et productif, mais les travaux récents insistent sur le fait que les deux influences ne doivent pas être prises comme deux mécanismes parfaitement indépendants ou simplement additifs.

**Sources :** Borbély (2022), *The two-process model of sleep regulation: Beginnings and outlook*, J Sleep Res, DOI `10.1111/jsr.13598`, PMID `35502706`; Skeldon & Dijk (2025), *The complexity and commonness of the two-process model of sleep regulation from a mathematical perspective*, npj Biological Timing and Sleep, DOI `10.1038/s44323-025-00039-z`; Dijk (2026), *Human data at odds and in confirmation of the two-process model of sleep regulation—a perspective*, DOI `10.1038/s44323-026-00083-3`.

**Portée :** soutient la séparation fonctionnelle homéostasie/circadien. Ne justifie pas que leur combinaison mathématique dans RIC soit littéralement celle d'une théorie particulière.

### 5.2 [A/B] L'historique veille–sommeil produit une dynamique homéostatique

L'activité EEG lente au cours du sommeil est classiquement plus élevée après une longue veille et décroît au fil du sommeil. Des ajustements individuels du modèle montrent aussi une forte variabilité des constantes estimées.

**Source primaire illustrative :** Rusterholz et al. (2010), *Inter-individual differences in the dynamics of sleep homeostasis*, Sleep 33(4):491–498, DOI `10.1093/sleep/33.4.491`, PMID `20394318`.

**Portée :** la SWA est un proxy utile mais partiel. Les constantes ajustées ne sont pas des constantes physiologiques universelles et ne doivent pas être copiées telles quelles dans RIC.

### 5.3 [A] La restriction chronique produit des déficits cumulatifs que la sensation subjective reflète imparfaitement

Une restriction répétée à 4 ou 6 h de temps au lit pendant 14 jours produit des déficits cognitifs cumulatifs importants alors que l'augmentation subjective de somnolence est proportionnellement limitée.

**Source :** Van Dongen et al. (2003), *The cumulative cost of additional wakefulness: dose-response effects on neurobehavioral functions and sleep physiology from chronic sleep restriction and total sleep deprivation*, Sleep 26(2):117–126, DOI `10.1093/sleep/26.2.117`, PMID `12683469`.

Une nuit de récupération après restriction chronique ne normalise pas nécessairement immédiatement tous les résultats mesurés.

**Source :** Banks et al. (2010), *Neurobehavioral dynamics following chronic sleep restriction: dose-response effects of one night for recovery*, Sleep 33(8):1013–1026, DOI `10.1093/sleep/33.8.1013`, PMID `20815182`.

**Portée :** justifie de falsifier une récupération RIC absurdement complète après une seule nuit. Ne justifie pas, à elle seule, une nouvelle variable persistante séparée de « dette chronique » en V1.

### 5.4 [A/B] La stabilité de l'éveil se dégrade progressivement sous privation

Les performances de vigilance sous privation montrent un comportement de « state instability » : alternance croissante entre réponses préservées et lapses, plutôt qu'un seuil universel unique où l'éveil devient soudain impossible.

**Source :** Doran, Van Dongen & Dinges (2001), *Sustained attention performance during sleep deprivation: evidence of state instability*, Arch Ital Biol, PMID `11330205`.

**Portée :** soutient des défaillances involontaires graduelles. Ne fixe ni seuil universel, ni probabilité par minute, ni mécanique de microsommeil exacte pour RIC.

### 5.5 [A] La réponse circadienne à la lumière dépend de la phase biologique

Une même exposition lumineuse peut avancer ou retarder la phase selon le moment biologique de l'exposition.

**Source :** Khalsa et al. (2003), *A phase response curve to single bright light pulses in human subjects*, J Physiol 549:945–952, DOI `10.1113/jphysiol.2003.040477`, PMID `12717008`.

La réponse dépend également de propriétés de l'exposition et ne se réduit pas à une règle « matin = avance / soir = retard ».

**Source complémentaire :** Rüger et al. (2013), *Human phase response curve to a single 6.5 h pulse of short-wavelength light*, J Physiol 591:353–363, DOI `10.1113/jphysiol.2012.239046`, PMID `23090946`.

### 5.6 [A/B] La période intrinsèque humaine est proche de 24 h, mais sa mesure est protocole-dépendante

Sous forced desynchrony contrôlée, une étude classique estime une moyenne de 24,18 h.

**Source :** Czeisler et al. (1999), *Stability, precision, and near-24-hour period of the human circadian pacemaker*, Science 284:2177–2181, DOI `10.1126/science.284.5423.2177`, PMID `10381883`.

**Portée :** ordre de grandeur pertinent. `24.18 h` n'est pas « la bonne constante RIC ».

### 5.7 [A/B] Le chat possède une homéostasie de sommeil et une organisation plus distribuée que le sommeil humain monophasique typique

Chez le chat domestique, la privation produit une réponse homéostatique du sommeil; dans certaines conditions contrôlées, le sommeil reste largement distribué sur le cycle plutôt que concentré en un unique bloc nocturne.

**Source :** *Sleep and EEG slow-wave activity in the domestic cat: effect of sleep deprivation*, PMID `2322413`.

Les rythmes d'activité félins sont plastiques et fortement dépendants de l'environnement, des routines et de l'accès extérieur; des pics crépusculaires observés ne doivent donc pas devenir une règle universelle.

**Source complémentaire :** étude indoor/outdoor de rythmes locomoteurs et alimentaires, PMID `36139300`.

---

## 6. Conclusions raisonnables mais incertaines

### [B/C] 6.1 Une homéostasie globale unique suffit comme première abstraction

La biologie réelle comprend des phénomènes locaux et use-dependent. RIC n'a toutefois pas besoin d'une carte cérébrale de sommeil local pour produire les phénomènes sociaux et temporels visés en V1. Une variable globale abstraite est donc acceptable jusqu'à falsification.

### [B/C] 6.2 Une phase circadienne individuelle persistante suffit comme noyau C

La phase est le minimum nécessaire pour qu'une agente puisse être alignée ou déphasée par rapport au monde. Une sensibilité lumineuse individuelle est utile pour produire de la diversité d'entrainment. Une amplitude individuelle n'est pas nécessaire en V1.

### [B/C] 6.3 La période intrinsèque individuelle peut rester grossière

Une variation de `tau` peut produire des divergences utiles, mais phase et sensibilité lumineuse capturent déjà une grande partie de la diversité observable à court terme. La présence et la granularité de `tau` doivent donc prouver leur utilité dans les bancs d'essai, pas être conservées par prestige scientifique.

### [B/C] 6.4 La polyphasie féline doit être tentée avec le mécanisme générique avant d'ajouter un oscillateur ultradien

Le premier test est de voir si des paramètres félins et des opportunités de sommeil différentes suffisent à produire plusieurs épisodes courts. Un mécanisme supplémentaire ne sera justifié qu'en cas de falsification répétée.

---

## 7. Hypothèses de modélisation RIC retenues

### 7.1 États persistants minimaux

Le contrat fonctionnel exige seulement les états durables nécessaires pour que l'histoire physiologique ne soit pas reconstruite arbitrairement :

1. **État lumineux objectif du monde** lorsque cette information ne peut pas être purement dérivée du temps/scénario.
2. **État homéostatique de sommeil individuel**, abstrait et normalisé selon un choix de calibration RIC.
3. **Phase circadienne individuelle**.
4. **Capacité physique individuelle**, héritière conceptuellement resserrée de l'actuel `energie`.

La manière de les persister, leur propriétaire logiciel et la possibilité de dériver certains d'entre eux restent à décider par Codex.

### 7.2 Paramètres individuels potentiels

- sensibilité lumineuse;
- période intrinsèque `tau`, si sa valeur émergente est démontrée;
- paramètres d'homéostasie nécessaires à la calibration;
- paramètres biologiques fictionnels pour espèces non humaines ou fictives.

Ces paramètres ne constituent pas automatiquement des traits psychologiques ni des étiquettes de chronotype.

### 7.3 Grandeurs dérivées, non autonomes

Les grandeurs suivantes doivent être calculables à partir de leurs causes plutôt que devenir par défaut de nouvelles jauges persistantes :

- signal circadien courant;
- propension relative sommeil/éveil;
- stabilité du maintien de l'éveil;
- exposition lumineuse pertinente intégrée sur une fenêtre récente.

Si Codex juge qu'une matérialisation technique est nécessaire pour performance, audit ou reprise, elle ne doit pas transformer la grandeur en nouveau propriétaire causal indépendant.

---

## 8. Contrat causal fonctionnel

### 8.1 Cycle du monde

```text
temps canonique + scénario/environnement
-> lumière environnementale objective
```

Le jour, le crépuscule et la nuit sont des propriétés du monde ou des dérivations du monde. Ils ne disent rien directement sur la somnolence d'un individu.

### 8.2 Exposition située

```text
lumière environnementale
+ lieu / obstacles / éclairage intérieur / situation
-> exposition effectivement reçue
```

L'Interaction Engine détermine ce qui atteint réellement l'organisme. Une lumière inaccessible ou non reçue ne peut pas entraîner son horloge.

### 8.3 Circadien

```text
phase précédente
+ temps canonique écoulé
+ exposition lumineuse pertinente
-> nouvelle phase circadienne
```

L'entrainment est progressif; aucun changement du cycle lumineux ne peut réinitialiser instantanément la phase.

### 8.4 Homéostasie

```text
historique veille/sommeil canonique
-> état homéostatique
```

L'éveil fait augmenter la charge homéostatique vers une saturation relative. Le sommeil la réduit, plus rapidement au début qu'à la fin selon la calibration retenue.

### 8.5 Propension et motivation

```text
homéostasie
+ état circadien
-> propension sommeil/éveil dérivée
-> motif physiologique éventuel
-> arbitrage avec autres motifs / buts / intentions
-> décision proposée
-> validation moteur
```

La propension n'est ni une émotion ni une décision.

### 8.6 Instabilité involontaire

```text
homéostasie fortement défavorable
+ soutien circadien insuffisant
+ contexte/stimulation
-> stabilité de l'éveil dégradée
-> défaillance involontaire éventuellement possible
```

Une motivation forte peut repousser ou compenser temporairement certaines conséquences, mais ne peut pas garantir un éveil stable sans limite.

---

## 9. Décision sur `repos`

**Décision [C/D] : `repos` est déprécié puis doit disparaître comme besoin physiologique générique.**

Il ne doit pas être :

- renommé silencieusement en Process S;
- converti numériquement vers la nouvelle homéostasie;
- utilisé comme preuve du passé circadien des habitantes;
- conservé comme « restedness » sans phénomène distinct démontré.

Les anciennes valeurs et événements restent historiquement vrais **selon la sémantique alpha qu'ils avaient à leur époque**. La migration future ne réécrit pas ce passé.

---

## 10. Décision sur `energie`

**Décision [C/D] : conserver l'abstraction, mais la resserrer strictement vers la capacité physique disponible pour supporter un effort.**

Usages acceptables en V1 :

- coût d'un déplacement ou d'un effort;
- limitation d'une activité physique;
- contraintes liées à une blessure;
- récupération physique partielle lors d'un repos éveillé ou du sommeil.

Usages interdits :

- motif de sommeil;
- proxy de somnolence;
- proxy d'alertness circadienne;
- fatigue subjective générale;
- réserve globale de bien-être;
- explication universelle de « ne pas avoir envie ».

Le terme conceptuel **capacité physique** est préférable à « énergie » dans la documentation future. Le renommage technique éventuel appartient à Codex et doit tenir compte de la compatibilité/migration.

Critère de décomposition future : si une seule capacité physique ne peut plus expliquer proprement endurance, effort local, récupération ou blessures sans contradictions répétées, le modèle doit retourner en R&D avant d'ajouter des sous-jauges.

---

## 11. `rest` et `sleep`

### 11.1 `rest`

`rest` est une activité **éveillée**.

En V1, elle peut :

- réduire l'intensité de certains coûts physiques;
- restaurer partiellement la capacité physique;
- permettre une récupération de blessure selon les règles du domaine physique.

Par hypothèse de parcimonie [C], son effet sur l'homéostasie de sommeil est négligeable en V1. Cette simplification peut être revisitée si un phénomène utile exige de distinguer repos calme, yeux fermés, méditation, etc.

### 11.2 `sleep`

`sleep` est le principal état qui dissipe l'homéostasie de sommeil.

Il ne doit plus être planifié principalement par les anciennes cibles `repos >= 98 000` et `energie >= 95 000`.

La continuité et la terminaison du sommeil doivent dépendre de la viabilité relative sommeil/éveil issue au minimum de :

- état homéostatique;
- phase circadienne;
- événements environnementaux assez forts pour interrompre le sommeil;
- contexte de simulation pertinent.

Un hard cap reste acceptable uniquement comme garde-fou technique [D], clairement documenté comme non physiologique.

RIC V1 ne simule pas les stades NREM/REM. Il accepte donc de perdre l'architecture ultradienne interne et les variations fines de profondeur du sommeil.

---

## 12. Instabilité de l'éveil — portée V1

Le mécanisme V1 doit pouvoir produire une **dégradation involontaire observable** de l'éveil sous privation sévère. Il n'a pas besoin de prétendre identifier un microsommeil EEG.

Abstraction fonctionnelle candidate :

```text
stable
-> fragile
-> lapses / échecs brefs possibles
-> intrusions de sommeil plus sévères possibles
```

Ces catégories sont [C]; leurs frontières ne sont pas des seuils biologiques universels.

Contraintes :

1. Leur cause doit être traçable à l'état physiologique et au contexte.
2. Une forte stimulation peut améliorer temporairement la stabilité, jamais annuler la dette d'éveil.
3. Aucun « jet de dés fatigue » indépendant des causes n'est acceptable.
4. Une éventuelle stochasticité future doit rester bornée et conditionnée par les causes; le hasard peut choisir entre issues plausibles, pas fabriquer la causalité.
5. Un seuil unique du type `S > X -> sommeil forcé` est rejeté comme pseudo-précision.
6. Un compteur déterministe de microsommeils est également rejeté.

La décision exacte d'imposer ou non une transition complète vers `sleep` dans les états extrêmes reste un choix de modèle à calibrer et tester. Le moteur peut en revanche posséder des défaillances physiologiques involontaires; elles ne sont pas des décisions du LLM.

---

## 13. Lumière et entrainment — portée V1

Le modèle lumineux minimal doit conserver :

- intensité approximative;
- durée d'exposition;
- timing relativement à la phase circadienne;
- histoire récente bornée de l'exposition lorsque nécessaire pour éviter un effet de reset instantané.

### 13.1 PRC

Une phase-response curve qualitative ou semi-quantitative est suffisante : régions favorisant avance, retard ou faible effet. Une courbe fine produisant des minutes de déplacement « scientifiques » est différée.

### 13.2 Dose

La relation ne doit pas être réduite à une multiplication linéaire naïve `intensité × minutes`. L'effet lumineux est non linéaire et dépend du protocole, de la phase et de l'histoire d'exposition.

### 13.3 Naturel vs artificiel

La physiologie ne reçoit aucun bonus intrinsèque « soleil ». Naturel/artificiel peut rester une distinction du monde et de la perception, mais l'entrainment réagit aux propriétés pertinentes de l'exposition.

Le spectre, la mélanopsine/ipRGC et une photobiologie détaillée sont différés. Cette simplification peut notamment sous-estimer les différences entre deux sources lumineuses de même intensité photopique mais de composition spectrale différente.

---

## 14. Calibration quantitative — politique anti-pseudo-précision

### 14.1 Ne pas copier les constantes de littérature

Les valeurs suivantes sont des résultats/propriétés de modèles expérimentaux, pas des constantes prêtes à implanter :

- période circadienne humaine moyenne autour de `24.15–24.18 h` sous forced desynchrony;
- plages de constantes d'accumulation homéostatique ajustées autour de `14–26 h` dans certaines études;
- constantes de décroissance ajustées de l'ordre de `1–4 h` selon mesure/protocole.

**Règle : NE PAS COPIER COMME CONSTANTE RIC.**

Elles servent à détecter un ordre de grandeur manifestement absurde et à construire des scénarios de calibration.

### 14.2 Forme homéostatique candidate

Une montée saturante pendant l'éveil et une décroissance plus rapide au début du sommeil sont préférables à une réserve strictement linéaire. La forme mathématique exacte reste [C/D].

Une échelle normalisée (`0..1`, `0..1000` ou autre) est un choix d'ingénierie, pas une mesure de SWA.

### 14.3 Restriction chronique

V1 n'ajoute pas automatiquement une deuxième variable persistante de « dette chronique ». Le banc d'essai doit d'abord falsifier la dynamique simple : si plusieurs jours de restriction sont effacés de manière manifestement irréaliste par une seule nuit, le modèle retourne en R&D avant tout ajout de mécanisme.

### 14.4 `tau`

L'individualisation fine de `tau` n'est pas obligatoire. Une variation grossière ou même un paramètre commun initial peut être préférable si phase + sensibilité lumineuse produisent déjà la diversité utile. Le paramètre n'est conservé que s'il produit un phénomène observable pertinent sur les horizons de RIC.

---

## 15. Espèces et généralité

### 15.1 Humains

Les paramètres de référence doivent être cadrés par la littérature humaine, puis calibrés pour reproduire des phénomènes plutôt que des biomarqueurs exacts.

### 15.2 Patoune — chat domestique

V1 tente d'abord le mécanisme générique : homéostasie + circadien + opportunités/contextes + paramètres félins.

Aucun script :

```text
si personnage == Patoune -> dormir à telle heure
```

n'est acceptable.

La crépuscularité est une tendance contextuelle possible, pas une règle fixe.

Un mécanisme ultradien explicite sera étudié seulement si le modèle générique échoue à produire une polyphasie plausible.

### 15.3 Luna et Chuu

Leur physiologie circadienne relève du **canon biologique fictionnel**, pas d'une extrapolation scientifique automatique.

Méthode :

1. définir les phénomènes biologiques souhaités;
2. les produire autant que possible par le mécanisme générique;
3. déclarer les paramètres fictionnels comme tels;
4. documenter tout emprunt/inspiration animale sans le présenter comme preuve;
5. falsifier les sorties plutôt que coder des comportements nominatifs.

---

## 16. Migration du monde vivant

La résidence existante ne doit pas être réinitialisée pour introduire ce système.

### 16.1 Non-rétroactivité

- aucune conversion `repos -> homéostasie de sommeil`;
- aucun calcul rétroactif prétendant découvrir une ancienne phase circadienne;
- aucun événement passé n'est réinterprété comme s'il avait été généré par le nouveau modèle;
- l'ancien `repos` garde sa signification historique alpha.

### 16.2 Initialisation

Les nouveaux états commencent à un instant de migration explicite avec provenance du type :

```text
post_migration_initialization
```

La valeur exacte, son format, son stockage et la stratégie technique appartiennent à Codex. Fonctionnellement :

- l'homéostasie initiale ne doit être ni automatiquement nulle, ni saturée;
- les personnages ne doivent pas être rendus artificiellement identiques si une variation initiale documentée est justifiée;
- la phase initiale peut être approximativement alignée au cycle courant et individualisée de façon déclarée;
- une condition canonique fictionnelle comme « couche-tard » peut informer une condition initiale seulement si elle est explicitement classée comme canon/design et non comme conclusion scientifique reconstruite.

### 16.3 Période d'adaptation

Les premiers jours post-migration peuvent constituer une vraie période d'entrainment depuis les conditions initiales. Ce n'est pas un passé reconstruit : c'est la première histoire circadienne réellement simulée par RIC.

### 16.4 Temps hors ligne

Le contrat `70_GEL_HORS_LIGNE_ET_RECUPERATION_CRASH_0_1_0A15.md` reste prioritaire : si le temps canonique est gelé hors runtime, aucune progression circadienne ou homéostatique accidentelle n'est créée hors ligne.

---

## 17. Falsifications obligatoires

Le modèle ne doit pas être accepté sur la seule base de tests unitaires d'équations. Il doit produire ou préserver les propriétés suivantes sur des scénarios comparatifs.

### A. Double comptage

- `energie`/capacité physique basse seule ne crée pas de motif de sommeil.
- `rest` éveillé ne dissipe pas l'homéostasie presque autant que `sleep`.
- aucune valeur legacy `repos` n'initialise automatiquement l'homéostasie.
- aucun motif de sommeil post-migration ne dépend encore d'un ancien `repos` actif.

### B. Circadien

- sans zeitgeber, un oscillateur dont `tau != 24 h` peut dériver progressivement;
- sous cycle lumineux stable, la phase s'entraîne progressivement;
- un déplacement brutal d'environ 8 h du cycle lumineux ne produit jamais un reset complet en moins d'un jour par simple assignation;
- même homéostasie + phases différentes peuvent produire des propensions/stabilités différentes.

### C. Liberté comportementale

- dormir le jour reste possible;
- rester éveillé la nuit reste possible;
- une motivation forte peut repousser le coucher;
- aucune motivation ne permet un éveil physiologiquement stable sans limite.

### D. Instabilité de l'éveil

- la fréquence/sévérité des défaillances doit augmenter sous privation sévère dans les conditions défavorables;
- ces défaillances ne doivent pas apparaître comme des événements aléatoires indépendants de l'état;
- une stimulation forte peut modifier temporairement la stabilité sans remettre l'homéostasie à zéro.

### E. Restriction chronique

- plusieurs jours de restriction doivent produire une trajectoire différente d'une seule nuit courte isolée;
- si une seule nuit standard efface systématiquement toute conséquence observable après plusieurs jours de restriction, la calibration est considérée suspecte et le modèle retourne en R&D;
- aucune « dette chronique » séparée n'est ajoutée uniquement pour faire passer ce test sans justification.

### F. Lumière

- la réponse à une exposition dépend de la phase;
- changement d'intensité/durée ne doit pas être traité comme une simple proportion linéaire universelle;
- une lumière artificielle suffisamment forte et bien timed peut influencer la phase;
- le soleil ne possède pas d'effet magique indépendant de ses propriétés modélisées.

### G. Patoune

Hypothèse générique falsifiée si, malgré une calibration raisonnable :

- elle converge systématiquement vers un unique long bloc nocturne de type humain;
- aucun épisode diurne n'apparaît dans des conditions favorables;
- les épisodes sont systématiquement trop longs et peu nombreux;
- un comportement félin plausible exige finalement un script identitaire.

Dans ce cas, retour R&D avant ajout d'un mécanisme ultradien.

### H. Migration et temps

- aucun état circadien pré-migration n'est inventé;
- la provenance de l'initialisation est auditable;
- les événements historiques restent inchangés;
- un arrêt runtime avec temps canonique gelé ne fait pas progresser la physiologie;
- une reprise ne crée aucun rattrapage circadien hors ligne.

---

## 18. Portée explicitement différée

La V1 ne doit pas implémenter sans nouvelle justification R&D :

- stades NREM/REM;
- oscillateurs périphériques multiples;
- sommeil local / EEG local;
- microsommeil défini par critères EEG;
- sleep inertia détaillée;
- dette chronique persistante séparée;
- somnolence subjective comme état persistant riche;
- effets circadiens directs sur humeur, colère, croyance ou qualité morale de décision;
- spectre lumineux détaillé, mélanopsine/ipRGC;
- repas, exercice, température ou social comme zeitgebers centraux;
- amplitude circadienne individuelle obligatoire;
- oscillateur ultradien explicite du chat;
- latitude, météo et saison détaillées si elles ne sont pas nécessaires au scénario courant.

Un élément différé peut revenir si un phénomène observable important est impossible à produire sans lui.

---

## 19. Prédictions émergentes attendues

Le système doit permettre, sans scripts narratifs :

- deux habitantes exposées à des routines lumineuses différentes qui se déphasent progressivement;
- une nuit tardive qui augmente la vulnérabilité au sommeil le lendemain sans ordonner automatiquement de dormir;
- un personnage qui continue une activité engageante malgré une forte propension au sommeil, puis devient moins stable;
- une adaptation sur plusieurs jours après changement d'horaire lumineux;
- une sieste diurne sans « permission horaire » spéciale;
- une divergence de rythmes entre humains et chat;
- des rythmes fictionnels propres à Luna/Chuu produits par paramètres biologiques documentés plutôt que scripts;
- une histoire circadienne qui n'existe réellement qu'à partir de l'introduction du système dans le monde persistant.

Ces prédictions sont des propriétés de banc d'essai, pas des scénarios obligatoires à chaque exécution.

---

## 20. Frontière avec la cognition

V1 peut créer un motif physiologique de sommeil sans persister encore une riche expérience subjective de « je me sens somnolente ».

Lorsqu'une future interoception sera introduite, elle devra respecter :

```text
état biologique réel
-> signal/interoception accessible
-> interprétation subjective éventuelle
```

Une agente ne doit jamais recevoir directement toute la physiologie cachée comme connaissance consciente parfaite.

Le LLM ne doit pas déduire la somnolence uniquement de l'heure civile; si une sensation subjective est exposée, elle doit provenir d'un mécanisme physiologique/interoceptif autorisé.

---

## 21. Mandat remis à Codex

Ce dossier autorise le passage à la **conception technique**, pas l'implantation aveugle d'une formule.

Codex doit déterminer, à partir de l'architecture réelle :

- quels états doivent véritablement être persistés et qui en est l'unique propriétaire;
- quelles grandeurs peuvent rester purement dérivées;
- comment déprécier puis retirer `repos` sans casser l'histoire ni les invariants;
- comment resserrer `energie`/capacité physique sans usages résiduels dans le sommeil;
- comment versionner et initialiser les nouveaux états avec provenance;
- comment intégrer lumière/exposition sans contourner Reality/Interaction;
- comment représenter l'évolution homéostatique et circadienne de façon déterministe, ou avec stochasticité conditionnée si elle est justifiée;
- comment conserver le gel hors ligne actuel;
- quel ordre de lots, migrations et tests minimise le risque sur la résidence persistante;
- comment exposer les métriques nécessaires aux falsifications sans transformer des diagnostics en états canoniques.

Avant modification importante, Codex doit vérifier les dépendances actuelles de `repos`, `energie`, `rest`, `sleep`, motifs physiologiques, blessures, activités et décision. Toute proposition technique qui introduit une nouvelle causalité biologique substantielle non couverte ici doit être renvoyée à la R&D scientifique avant implantation.

---

## 22. Critères de sortie R&D

Le domaine est considéré suffisamment mûr pour conception technique parce que :

1. le problème de double comptage est explicitement tranché;
2. la frontière environnement/exposition/physiologie/cognition/action est définie;
3. les états minimaux et les grandeurs dérivées sont séparés conceptuellement;
4. les phénomènes quantitatifs attendus sont définis sans imposer de pseudo-constantes;
5. deux contre-audits adversariaux puis un audit quantitatif ont attaqué successivement le modèle;
6. les principales hypothèses de V1 possèdent des falsifications explicites;
7. les phénomènes avancés sont différés plutôt qu'imités superficiellement.

Une réouverture R&D est obligatoire si le rodage révèle un échec structurel : récupération chronique absurde, rythmes trop réguliers, incapacité à produire une polyphasie féline, instabilité de l'éveil artificielle, double comptage résiduel ou nécessité d'une causalité non étudiée.

---

## 23. Bibliographie de référence

### Cadre veille–sommeil

- Borbély, A. A. (2022). *The two-process model of sleep regulation: Beginnings and outlook*. Journal of Sleep Research, 31(4), e13598. DOI `10.1111/jsr.13598`. PMID `35502706`. — Revue historique/conceptuelle.
- Skeldon, A. C., & Dijk, D.-J. (2025). *The complexity and commonness of the two-process model of sleep regulation from a mathematical perspective*. npj Biological Timing and Sleep. DOI `10.1038/s44323-025-00039-z`. — Analyse mathématique/conceptuelle récente.
- Bes, F. (2025). *Treatise on an alternative perspective on the two-process model of sleep regulation*. npj Biological Timing and Sleep. DOI `10.1038/s44323-025-00038-0`. — Perspective alternative; ne constitue pas un remplacement empirique établi.
- Dijk, D.-J. (2026). *Human data at odds and in confirmation of the two-process model of sleep regulation—a perspective*. npj Biological Timing and Sleep. DOI `10.1038/s44323-026-00083-3`. — Perspective critique récente.

### Homéostasie, restriction et stabilité de l'éveil

- Rusterholz, T. et al. (2010). *Inter-individual differences in the dynamics of sleep homeostasis*. Sleep, 33(4), 491–498. DOI `10.1093/sleep/33.4.491`. PMID `20394318`. — Primaire; ajustements SWA sur petit échantillon masculin jeune.
- Doran, S. M., Van Dongen, H. P. A., & Dinges, D. F. (2001). *Sustained attention performance during sleep deprivation: evidence of state instability*. Archives Italiennes de Biologie. PMID `11330205`. — Primaire; PVT et privation totale.
- Van Dongen, H. P. A. et al. (2003). *The cumulative cost of additional wakefulness: dose-response effects on neurobehavioral functions and sleep physiology from chronic sleep restriction and total sleep deprivation*. Sleep, 26(2), 117–126. DOI `10.1093/sleep/26.2.117`. PMID `12683469`. — Primaire; restriction chronique contrôlée.
- Banks, S. et al. (2010). *Neurobehavioral dynamics following chronic sleep restriction: dose-response effects of one night for recovery*. Sleep, 33(8), 1013–1026. DOI `10.1093/sleep/33.8.1013`. PMID `20815182`. — Primaire; récupération après restriction.

### Circadien et lumière

- Czeisler, C. A. et al. (1999). *Stability, precision, and near-24-hour period of the human circadian pacemaker*. Science, 284(5423), 2177–2181. DOI `10.1126/science.284.5423.2177`. PMID `10381883`. — Primaire; forced desynchrony.
- Khalsa, S. B. S. et al. (2003). *A phase response curve to single bright light pulses in human subjects*. Journal of Physiology, 549, 945–952. DOI `10.1113/jphysiol.2003.040477`. PMID `12717008`. — Primaire; PRC lumière.
- Rüger, M. et al. (2013). *Human phase response curve to a single 6.5 h pulse of short-wavelength light*. Journal of Physiology, 591, 353–363. DOI `10.1113/jphysiol.2012.239046`. PMID `23090946`. — Primaire; lumière courte longueur d'onde.

### Chat domestique

- *Sleep and EEG slow-wave activity in the domestic cat: effect of sleep deprivation*. PMID `2322413`. — Primaire; homéostasie et distribution du sommeil félin.
- *Comparison of locomotor and feeding rhythms between indoor and outdoor cats living in captivity*. PMID `36139300`. — Primaire; plasticité des rythmes d'activité selon environnement.

---

## 24. Résumé normatif

```text
CONSERVER
- séparation monde / exposition / physiologie / cognition / action
- homéostasie de sommeil dédiée
- phase circadienne individuelle
- lumière comme zeitgeber principal V1
- capacité physique distincte du sommeil
- propension et stabilité dérivées
- liberté de dormir le jour / veiller la nuit
- défaillances involontaires possibles sous privation sévère
- migration non rétroactive

DÉPRÉCIER PUIS RETIRER
- repos comme besoin générique

RESSERRER
- energie -> capacité physique disponible pour effort

DIFFÉRER
- somnolence subjective riche
- NREM/REM
- dette chronique séparée
- sleep inertia fine
- photobiologie spectrale
- oscillateurs périphériques
- ultradien félin explicite
- effets émotionnels/cognitifs directs

REJETER
- repos legacy = Process S
- energie basse = motif de sommeil
- sleep fixé par 98/95 comme physiologie future
- seuil universel de sommeil forcé
- hasard indépendant de la physiologie
- matin = avance / soir = retard comme règle absolue
- constantes de littérature copiées telles quelles
- crépuscularité féline codée en dur
- reconstruction rétroactive d'une biologie circadienne passée
```
