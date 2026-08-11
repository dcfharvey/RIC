# Work order — raccord persistant inactif du cycle circadien V1

**Statut :** raccord persistant inactif livré ; cutover comportemental toujours interdit.
**État :** schéma de code 47 après migration forward-only 0047.
**Portée :** raccord persistant testable, sans modifier le comportement legacy.
**Hors portée absolue :** `data/vivarium-rodage.sqlite`, démarrage du runtime, session crashée `runtime_session.id = 4`, migration réelle, activation, conversion `repos → H` ou `energie → P`, et toute histoire physiologique rétroactive.

Ce document traduit les contrats de `docs/79_R_D_CYCLE_DIURNE_CIRCADIEN_SOMMEIL.md`, les fondations de `docs/80_WORK_ORDER_CYCLE_DIURNE_CIRCADIEN_SOMMEIL_V1.md` et la sélection `additive` de `docs/82_SELECTION_ROBUSTESSE_CALIBRATION_CIRCADIEN_V1.md`. Il ne constitue pas une autorisation d'implémentation ni de cutover.

## 1. État réel et dette legacy à traiter au cutover

Les migrations 0045 à 0047 ont créé les fondations additives : profils lumineux versionnés, profils biologiques versionnés, assignations, préparation de monde, gate (`inactive` / `prepared` / futur `active`), tables vides H/phase/P et mémoire d'hystérésis vide. `SleepPhysiologyFoundationService` gère les catalogues, assignations et la préparation ; `SleepPhysiologyService` relit et projette seulement des états déjà présents dans un monde synthétique `active`. Il n'intègre aucun intervalle et le runtime ne lit aucune de ces tables.

Le comportement actuel reste entièrement piloté par les besoins alpha legacy :

- `DecisionPolicy` (`policy.py`) traite `repos` et `energie` comme des causes exécutables de `sleep` / `rest`, y compris dans les seuils critiques ;
- `SimulationEngine` (`simulation.py`) construit ce `PolicyContext` et démarre les activités ;
- `ActivityEngine` (`activities.py`) planifie et termine `sleep` avec les cibles legacy `repos` et `energie` ;
- `MotivationService` et `AttentionService` projettent encore ces deux besoins ;
- `CharacterEngine` consomme directement `energie` pour certains coûts de mouvement liés aux blessures ;
- l'UI/admin et les règles de monde lisent encore les besoins legacy.

Ces consommateurs ne seront **pas** changés dans le raccord inactif. Au futur cutover, ils doivent être remplacés ensemble : retirer seulement `repos` avant que le motif, l'arbitre, le sommeil et la stabilité soient actifs créerait une veille stable sans limite ; retirer seulement `energie` avant P briserait les capacités physiques. Les valeurs legacy restent historiques et auditées ; leur absence de réécriture est un invariant.

## 2. Ownership, états persistants et projections

### 2.1 Propriétaire unique

`SleepPhysiologyService` est le raccord déterministe distinct de la couche de catalogue. Il est aujourd'hui lecture/projection seule ; au lot ultérieur de matérialisation, il sera l'unique écrivain de :

- `sleep_regulation_state` : H normalisée et phase circadienne `phi`, ancrées à un instant canonique ;
- `physical_capacity_state` : P, son ancre et le reste de calcul entier ;
- la mémoire physiologique minimale d'hystérésis (`previous_band`) seulement si le modèle actif en a réellement besoin.

`SleepPhysiologyFoundationService` reste propriétaire des profils, des assignations et de `world_physiology_system`. Les autres services demandent une matérialisation ou lisent une projection ; ils ne mettent jamais à jour H, `phi`, P ou l'hystérésis directement. Le moteur reste propriétaire des activités, des déplacements, des interruptions et des événements canoniques qu'il valide.

### 2.2 Données conservées

| Donnée | Persistée | Owner | Rôle |
|---|---:|---|---|
| H, `phi`, `anchor_at` | oui | `SleepPhysiologyService` | état minimal dont `phi` intègre déjà l'effet passé de la lumière |
| P, `rate_remainder`, `anchor_at` | oui | `SleepPhysiologyService` | capacité physique distincte de H |
| profil / modèle / version | oui, immuable | fondations | paramètres et provenance sélectionnés explicitement |
| bande précédente | oui, état dense par personnage `active` | `SleepPhysiologyService` | mémoire physiologique minimale, y compris après restart ; absence = intégrité invalide |
| interruption déjà appliquée | déjà reconstructible | `ActivityEngine` / état `activity` | une activité `aborted` ne peut plus être interrompue ; l'événement moteur en conserve la cause |
| exposition effective | non | résolveur pur | dérivée du calendrier objectif, du lieu et de l'état agent |
| propension sommeil additive | non | projection pure | combinaison H + influence circadienne, jamais une jauge autonome |
| stabilité de veille | non | projection pure | H, `phi`, contexte et stimulation bornés |
| motif de sommeil | non | projection/arbitre futur | candidat explicable, pas un ordre ni un état cognitif |

V1 n'ajoute pas d'historique lumineux séparé : la phase `phi` est l'état intégrateur minimal retenu. Si une future fonction exige une histoire plus riche, il faudra soit la reconstruire depuis les causes canoniques, soit ajouter un état suffisant explicitement détenu par ce service — jamais le fabriquer à la lecture.

Le modèle persistant doit identifier explicitement `ric.sleep.additive.v1` / famille `additive`. `sensitivity_modulated` reste un comparateur de banc et ne peut pas être choisi par une assignation de production.

## 3. Flux causal visé, sans raccorder encore le comportement

```text
calendrier objectif + exposition du lieu + état physique pertinent
                         │
                         ▼
              drive lumineux effectif (pur)
                         │
                         ▼
          H / phi / P matérialisés à une frontière canonique
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
propension additive (pure)        stabilité de veille (pure)
        │                                 │
        ▼                                 ▼
motif de sommeil candidat       interruption moteur bornée
        │                                 │
        └──── futur arbitre sans priorité absolue ────┘
                              │
                              ▼
                   proposition d'activité validée
                              │
                              ▼
              Activity/World Engine propriétaire canonique
```

L'état `sleep` ou l'occlusion atténue fortement le drive lumineux ; `rest` reste éveillé. La lumière ne devient pas « naturelle » ou « artificielle » par privilège : seuls les paramètres objectifs du monde déterminent son drive. La stimulation peut atténuer la manifestation de l'instabilité, mais ne modifie ni H ni `phi` et ne peut annuler une non-viabilité extrême.

Ni H, ni P, ni le motif ne sont une croyance ou une mémoire. Ils ne sont pas injectés au LLM et aucun composant cognitif ne peut les réécrire. Patoune peut avoir un profil `generic_feline`, sans lui créer une cognition sentiente.

## 4. Frontières de matérialisation et lecture pure

Une lecture reconstitue les projections depuis l'ancre persistée et **n'écrit rien**. Le temps canonique arrêté ou pausé gèle donc la physiologie ; le temps mural n'est jamais une source d'intégration.

Lorsque le système sera `active`, le service matérialisera d'abord l'ancien segment de causes, dans la même transaction que la mutation canonique qui le clôt :

1. juste avant le démarrage, la fin, l'abandon ou le changement d'activité ;
2. juste avant un déplacement ou une modification de position, puis le nouveau lieu influencera uniquement l'intervalle suivant ;
3. à la frontière d'un changement lumineux objectif (calendrier, profil de lieu et, plus tard, lampe/rideau possédés par Reality) ;
4. à une frontière interne planifiée de stabilité critique, avant que le moteur n'interrompe éventuellement une activité.

Le chemin de démarrage d'activité peut aussi déplacer le personnage au même instant. Les appels à la même ancre doivent être idempotents (`dt = 0`) afin qu'il n'y ait ni double intégration ni churn persistant. `ActivityEngine.advance_to` doit segmenter activité active, transition et état passif ; aucun appel ne doit sauter une frontière de causes. Les calculs H et phase gardent le contrat de convergence numérique du banc sur partitions non alignées ; P conserve son reste rationnel afin que les découpages ne créent pas de dérive arbitraire.

Le résolveur V1 de calendrier devra valider un JSON versionné couvrant sans chevauchement `[0, 86400)` (phase relative au temps canonique), puis résoudre la dernière assignation effective à l'instant demandé. `exposure_milli` du lieu reste un multiplicateur de propriété du lieu, non son éclairage présent. Aucun état dynamique spéculatif de lampe ou de rideau n'est créé dans ce lot.

## 5. Profils et initialisation non rétroactive

Les profils traduisent `CircadianParameters` dans un payload immuable versionné et avec provenance : référence humaine commune ; profil félin générique ; profils `fictional_canon` seulement lorsque le produit fournit leur provenance explicite. Aucun chronotype ne provient d'un trait de personnalité. Patoune ne reçoit aucune branche nominative ; Luna/Chuu ne reçoivent aucune physiologie réelle déduite d'une espèce fictionnelle.

La migration 0047 étend le gate de système pour permettre `active` et ajoute `sleep_wake_hysteresis_state` pour la mémoire d'hystérésis retenue. Le contrat est **dense** : chaque personnage `active` doit avoir H/φ, P et une ligne `previous_band`; une absence est une erreur d'intégrité, jamais l'alias implicite de `stable`. Elle ne crée pas de garde physiologique pour « interruption déjà appliquée » : ce fait appartient à l'activité moteur. Elle est forward-only et ne crée ni état physiologique, ni événement canonique, ni conversion de besoins. La contrainte SQLite de 0046 est remplacée par une table contrôlée, jamais par l'édition rétrospective d'une migration publiée.

L'initialisation est une opération distincte, explicite et atomique :

1. runtime proprement arrêté, sans session ouverte ;
2. validation en lecture de toutes les assignations et d'un manifeste complet d'états initiaux H/`phi`/P, au même instant canonique durable ;
3. dans une transaction : insert des états, ancre commune, garde neutre, audit append-only `post_migration_initialization`, puis bascule `active` ;
4. aucun `canonical_event`, aucune narration Hugin, aucune mémoire Munin ;
5. aucune déduction depuis `repos`, `energie`, ni intervalle pré-activation.

La provenance est un artefact opérateur ; l'état devient réel à partir de l'activation, mais la raison technique de son insertion ne devient jamais un fait vécu.

## 6. Feature gate et raccord inactif

| État du système | Autorisé | Interdit |
|---|---|---|
| `inactive` | catalogues, assignations, banc et préflight diagnostique | états H/P, intégration, lecture par comportement |
| `prepared` | contrôle de complétude, manifeste hors session et seul modèle `ric.sleep.additive.v1` | toute décision, activité, autonomie, motivation ou LLM |
| `active` (encore synthétique seulement) | service et projections de test | scheduler runtime, activité, autonomie ou chemin legacy concurrent |

Le raccord persistant inactif devra donc être inaccessible à `Policy`, `Activity`, `Simulation`, `Autonomy`, `Motivation`, `Attention`, `DecisionFrame` et aux providers tant que le gate n'est pas `active`. Un préflight futur distinguera par lecture SQL directe `inactive`, `prepared_complete` et `active_integrity`, sans appeler `WorldEngine.read_canonical_time()`.

### Frontière des sources au lot synthétique

Les APIs de banc explicitement suffixées `_synthetic` acceptent un
`RegulationInput` libre afin de falsifier le modèle. Elles ne sont pas une
interface de production. Le futur raccord causal devra construire ses causes
depuis leurs propriétaires : lumière depuis calendrier/lieu/Reality ;
wake/rest/sleep depuis activité ou état canonique ; occlusion depuis état
physique validé ; stimulation depuis contexte moteur borné. Une cognition ou
un LLM ne pourra pas choisir ces entrées pour modifier sa physiologie.

## 7. Contrats futurs d'arbitrage et de stabilité

### Arbitrage volontaire

`SleepMotiveProjection` sera une projection pure qui offre un candidat générique `sleep_regulation` depuis la propension additive. P n'est jamais une entrée de ce motif. Le futur arbitre recevra motifs, buts, intention active, contraintes et opportunités, mais aucune catégorie ne possède une priorité absolue. Une intention peut gagner temporairement ; l'ignorance ne réduit pas H et doit entraîner une prochaine réévaluation causale.

Le `DecisionFrameService` actuel reste une explication de la hiérarchie legacy, pas l'algorithme à recopier. La fonction de compromis concrète doit être revue avant le cutover ; le raccord inactif ne doit pas la faire entrer dans le chemin exécutable.

### Stabilité involontaire

La projection `wake_stability` utilise H, `phi`, contexte/stimulation et l'hystérésis du modèle sélectionné. À une frontière critique planifiée, la physiologie ne fournit qu'une éligibilité explicable. Le moteur valide ensuite et peut interrompre une activité qui exige le maintien de l'éveil ; il ne force pas directement un sommeil complet. L'interruption ouvre une nouvelle situation d'arbitrage où le motif demeure.

La mémoire `previous_band` appartient à `SleepPhysiologyService` si l'hystérésis ne peut pas être dérivée de manière suffisante. En revanche, l'anti-répétition d'une conséquence appartient déjà au propriétaire moteur : `ActivityEngine` vérifie l'activité canonique active, applique sa transition vers `aborted` et émet l'événement d'interruption avec sa cause. Une activité déjà `aborted` n'est plus éligible ; le fait est reconstructible depuis son état canonique et l'événement moteur, sans double état physiologique. La future API moteur doit rendre cette application idempotente plutôt que déclencher une exception au second appel concurrent. Aucune interruption par pulse, aucune roulette et aucune stochasticité V1.

## 8. Lots proposés

1. **Revue de ce work order.** Complétée, avec clarification d'ownership.
2. **Raccord persistant inactif.** Complété : migration 0047, service de lecture/projection, résolveur de sources, mémoire d'hystérésis, préflight diagnostique et aucune injection runtime.
3. **Exécution synthétique.** Complété dans des mondes de test `active` seulement : matérialisation H/φ/P avec reste rationnel de P, segmentation explicite, hystérésis dense, projections additive/stabilité et scheduler de frontière en lecture. Les APIs sont suffixées `_synthetic`; elles n'activent ni résidence ni politique legacy.
4. **Compatibilité et shadow.** Audit exhaustif des consommateurs `repos` et `energie`; essais de l'arbitre/motif/stabilité ensemble sur copies synthétiques, sans écrire dans le monde réel.
5. **Work order de cutover séparé.** Définition de l'arbitre exécutable, terminaison de sommeil, migration des coûts physiques vers P et bascule atomique. Cette étape exige nouvelle revue Sol/R&D.
6. **Déploiement réel ultérieur.** Uniquement après reprise officielle de la session crashée, arrêt propre séparé, validation et approbation explicite.

## 9. Tests de non-régression et falsification

- migration de test 46 → raccord : digest, séquences et compteurs d'histoire canonique identiques ; aucune ligne H/P et aucun événement ;
- `inactive`/`prepared` : mêmes décisions, activités et sorties runtime que le monde legacy témoin ; des spies démontrent l'absence de lecture physiologique par les consommateurs interdits ;
- service actif synthétique : seul son owner peut écrire H/`phi`/P/hystérésis, lectures sans écriture, `dt=0` idempotent, restart sans double intégration ;
- frontières : mouvement, démarrage/fin/abandon de `sleep`, `rest`, lumière et partitions irrégulières produisent les segments attendus ; occlusion de sommeil appliquée ; `rest` récupère P mais ne dissipe pas matériellement H ;
- temps : monde arrêté/pausé et grand décalage mur/canon ne progressent jamais H/`phi`/P ;
- profils : immutabilité, assignments effectifs, modèle `additive` obligatoire, profil félin générique sans cognition Patoune ;
- stabilité : passage critique borné, physiologie qui ne fait que proposer l'éligibilité, interruption idempotente détenue par `ActivityEngine`, hystérésis et reprise après changement causal, aucune tempête après reconstruction ;
- arbitrage synthétique : une intention et le motif peuvent chacun gagner selon leurs entrées explicites, sans priorité de catégorie ; P ne peut jamais créer le motif ;
- atomicité future : configuration incomplète ou écriture en échec laisse le monde legacy et les états physiologiques inchangés.

Les falsifications quantitatives déjà établies par le banc (free-running, phase-lock, réentrainment, restriction/récupération, stimulation bornée, séparation H/P) restent des prérequis de régression du noyau pur.

## 10. Procédure future de cutover atomique

Le cutover ne devient envisageable que lorsque l'arbitre volontaire **et** le minimum de stabilité involontaire sont validés ensemble. Il aura lieu après un arrêt propre, dans une transaction de configuration/activation qui valide le manifeste complet et ne laisse jamais ancien et nouveau mécanismes piloter le sommeil simultanément. Le même déploiement basculera la politique, la planification/fin de sommeil, les coûts physiques et les déclencheurs de réévaluation. En cas de précondition manquante, rollback complet : le monde reste legacy.

Le hard cap de sommeil restera un garde-fou technique explicitement séparé de la règle physiologique. Sa valeur et la fonction exécutable de compromis sont des décisions encore ouvertes, pas des constantes introduites par ce work order.

## 11. Reprise distincte de la session crashée id=4

La migration et le raccord ne doivent jamais fermer, réécrire ou consulter une « heure actuelle » dérivée du flag `running` orphelin de la session 4. La procédure future, séparée du cutover circadien, est :

1. confirmer runtime absent et intégrité SQLite par lectures sûres ;
2. appliquer les migrations additives approuvées et préflighter sans dérivation murale du temps canonique ;
3. lancer normalement le runtime ;
4. laisser exclusivement `RuntimeSessionService.start()` marquer la session 4 `crash_recovered`, écrire son événement technique, réancrer l'horloge sans rattrapage offline et ouvrir la nouvelle session ;
5. vérifier ces artefacts avant toute reprise normale.

Cette récupération opérationnelle ne matérialise aucune physiologie et ne doit pas être confondue avec l'activation future du cycle circadien.

## 12. Décisions encore nécessaires avant le cutover

- contrat exécutable, explicable et calibrable de compromis entre motifs, intentions, buts et contraintes ;
- définition de quelles activités exigent suffisamment de stabilité pour une interruption moteur ;
- paramétrage et provenance du manifeste initial par résidence ;
- règle physiologique de fin de sommeil et hard cap de sûreté ;
- confirmation, après code du raccord, que la mémoire d'hystérésis est réellement nécessaire plutôt qu'une dérivation suffisante depuis les causes canoniques.

Aucune de ces décisions ne doit être déduite silencieusement au cours du lot inactif.
