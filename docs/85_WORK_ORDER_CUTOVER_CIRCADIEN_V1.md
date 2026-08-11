# Work order — cutover circadien V1 de la résidence persistante

**Statut :** accepté et clos par Sol ; aucune implémentation ni activation autorisée par ce document.

**HEAD audité :** `2d7e45a8b3ebeadec6d95ea4f5401df2d65a31e2` (`main`).
**État de code :** schéma 48 ; lot 4 shadow accepté.
**État de la résidence :** `data/vivarium-rodage.sqlite` reste au schéma 44, runtime absent, session `runtime_session.id = 4` conservée comme crash.

Ce document prolonge `docs/79_R_D_CYCLE_DIURNE_CIRCADIEN_SOMMEIL.md` et les lots 80–84. Il définit le travail nécessaire pour un futur cutover atomique et explicable. Il ne donne jamais l'autorisation de toucher la résidence réelle.

## 1. Périmètre et protections absolues

Le futur lot remplacera ensemble le pilotage legacy de `repos` et la partie physique de `energie` par la physiologie V1 H/phi/P validée en banc. Il doit fournir un arbitre exécutable, une terminaison de sommeil, des frontières runtime et une conséquence moteur bornée de stabilité critique.

Il ne doit jamais :

- convertir `repos` en H, ni `energie` en P ;
- supprimer les lignes legacy, les migrations ou l'histoire existante ;
- créer une histoire physiologique avant l'instant d'activation ;
- exposer la provenance technique d'initialisation comme fait vécu, Hugin, Munin ou mémoire ;
- laisser un LLM, Policy cognitive, Motivation, Attention ou un provider écrire H/phi/P, une activité ou le canon ;
- reprendre la session 4 autrement que par `RuntimeSessionService.start()` ;
- dériver une heure courante du flag `running` orphelin avant cette récupération officielle ;
- utiliser le quantum synthétique d'une seconde comme cadence runtime.

Les invariants demeurent : réalité/canon != perception != croyance ; parole != fait ; un seul propriétaire persistant par état ; le moteur valide et applique toute mutation canonique.

## 2. État réel à commuter et groupes atomiques

`circadian_shadow.LEGACY_CONSUMERS` est le manifeste exécutable de départ ; la recherche de consommateurs sera relancée juste avant implémentation et activation.

| Groupe | Implémentations actuelles | Cutover requis |
|---|---|---|
| Décision comportementale | `DecisionPolicy`, `SimulationEngine`, `MotivationService`, `AttentionService`, `DecisionFrameService` | remplacer `repos` comme cause de sommeil, intégrer arbitre, réévaluations et sommeil dans le même déploiement |
| Cycle d'activité | `ActivityEngine` | remplacer validation et fin de `sleep` fondées sur `SLEEP_REPOS_TARGET` / `SLEEP_ENERGIE_TARGET`; garder `rest` éveillé ; appliquer l'interruption critique idempotente |
| Capacité physique | `ActivityEngine`, `CharacterEngine` | déplacer coûts d'activité et de mouvement qui lisent/écrivent `energie` vers P, sans conversion de stock |
| Lecture opérateur | `AdminReadService`, Hugin | présenter P comme capacité distincte et l'état physiologique actif, jamais les besoins legacy comme valeurs V1 actuelles |
| Conservation historique | `WorldEngine`, `WorldRuleService`, `InstanceService`, `seed.py`, reproductibilité | conserver définitions, états et événements legacy ; empêcher seulement leur lecture dans le runtime circadien actif |

Le comportement legacy doit rester identique pour les mondes `inactive` et `prepared`. Un monde `active` ne peut jamais laisser en concurrence une voie legacy et une voie circadienne qui choisissent ou terminent le sommeil.

## 3. Ownership final et résultats dérivés

| État ou résultat | Persistance / propriétaire | Règle |
|---|---|---|
| H, phi, résidus, P et reste de capacité | `SleepPhysiologyService` | seul écrivain physiologique, à ancre canonique commune ; les autres moteurs lui demandent une application validée |
| `previous_band` | `SleepPhysiologyService` | état dense minimal d'hystérésis ; absence = intégrité invalide |
| activité, position, `aborted`, événement de cause | `ActivityEngine` / moteur | activité abortée = garde anti-répétition ; aucun cache physiologique concurrent |
| calendrier, profil lumineux, position, type d'activité | propriétaires Reality/activité | seules sources admises pour l'exposition effective V1 |
| propension, stabilité, motif sommeil, prochaine frontière | projections pures | recalculables, non persistées, aucune lecture ne progresse le temps |
| calibration d'arbitrage et classes d'activité | configuration versionnée à créer | donnée de produit/ingénierie, pas donnée cognitive ou biologique cachée |
| `post_migration_initialization` | journal opérateur append-only séparé | provenance technique, ni événement vécu ni trace subjective |

H est l'homéostasie abstraite ; P est une capacité physique. P ne participe jamais au motif de sommeil et H ne devient jamais une réserve d'effort. Les résidus H/phi sont des détails numériques de représentation, non des variables biologiques ou souvenirs de lumière.

`ActivityEngine` et `CharacterEngine` sont des demandeurs de coûts, jamais des écrivains de P : ils déterminent et valident la cause canonique (activité ou déplacement), puis appellent une API transactionnelle de `SleepPhysiologyService` qui matérialise et applique le débit. Toute écriture SQL de `physical_capacity_state`, y compris un débit de mouvement, reste confinée à ce service.

## 4. Sources causales et matérialisation

### 4.1 Résolveur de production

Les `RegulationInput` libres et APIs `_synthetic` ne peuvent pas être promus. Le lot introduira un résolveur pur, appelé par le moteur dans sa transaction, qui construit l'input seulement depuis :

1. l'instant canonique et le calendrier lumineux versionné ;
2. le lieu canonique courant et son profil d'exposition ;
3. le statut/type de l'activité canonique (`wake`, `rest`, `sleep`) ;
4. l'occlusion objectivement validée — V1 l'applique pour `sleep` ;
5. une stimulation issue d'un propriétaire moteur borné.

Il n'existe pas de source canonique bornée de stimulation aujourd'hui. Au premier cutover elle sera donc explicitement absente/à zéro : ni cognition, ni trait, ni LLM ne peuvent la fournir. Lampes, rideaux ou autres états physiques futurs s'ajouteront comme causes Reality au résolveur, non comme jauges spéciales de physiologie.

### 4.2 Frontières et ordre transactionnel

Dans la même transaction, le moteur matérialise d'abord l'ancien segment jusqu'à la frontière, puis applique la mutation canonique qui crée la source suivante. Les frontières sont :

- démarrage, fin, extension ou abandon d'activité ;
- chaque étape de déplacement, avant que le nouveau lieu prenne effet ;
- transition objective du calendrier lumineux applicable ;
- première frontière calculée où la stabilité devient critique ;
- échéance de réévaluation de sommeil ou de décision.

Les appels à la même ancre sont idempotents (`dt = 0`). `SimulationEngine` remplacera sa seule échéance `MIN(activity.planned_end_at)` par une échéance déterministe minimale incluant ces frontières et appellera une API moteur de transition. Il ne matérialisera pas à chaque pulse mural. Le scanner interne d'hystérésis peut garder sa résolution de banc pour détecter les crossings sans exposer cette seconde comme cadence runtime.

Hugin, admin et les projections d'arbitrage relisent l'ancre déjà matérialisée ; ils ne créent jamais de progression.

## 5. Arbitre exécutable : contrat manquant bloquant

Le shadow compare `highest_explicit_score` à une propension [0,1]. Cela falsifie une priorité absolue de catégorie, mais n'autorise pas la comparaison de ces nombres en production : l'intention active actuelle n'a pas de score exécutable commun ; elle ne fournit qu'un plan et un but, dont importance/urgence sont subjectives.

### 5.1 `ArbitrationScale` obligatoire

Avant code comportemental, Sol/propriétaire doivent approuver une politique versionnée d'**échelle de priorité de proposition**, pas une mesure psychologique. Chaque option devra publier :

- `option_key` et l'action proposée ;
- `source_kind` (`physiological_sleep`, besoin moteur, intention, objectif, récupération physique, etc.) ;
- ses entrées brutes et leurs owners ;
- sa transformation versionnée vers l'échelle commune ;
- contraintes, permissions et faisabilité moteur ;
- version et provenance de calibration.

La propension additive H/phi est une entrée du mapping du motif sommeil, pas son score arbitral automatiquement commensurable. Une intention ne devient jamais prioritaire parce qu'elle est active : elle passe par le même contrat explicite. P peut proposer une récupération physique (`rest`/activité légère), jamais le sommeil.

Ce mapping et ses coefficients sont un choix de produit/calibration [D], à falsifier sur mondes synthétiques ; ils ne seront pas présentés comme une loi biologique. Sans contrat approuvé pour mapping, égalité et absence de score, le cutover est **NO-GO**. Aucun fallback `active_intention > motif`, ni tie-break de catégorie, n'est autorisé. L'arbitre production est moteur-owned, déterministe et auditable ; un LLM ne peut ni lui donner son échelle ni appliquer son résultat.

### 5.2 Réévaluation

Une intention qui gagne ne vaut que pour la décision présente. H/phi continuent d'évoluer ; le scheduler programme la prochaine frontière de motif, stabilité ou activité. À cette frontière, une nouvelle frame est bâtie depuis le canon. Une conséquence critique ouvre elle aussi une nouvelle frame.

## 6. Sommeil et stabilité involontaire

### 6.1 Début et fin de `sleep`

`ActivityEngine` reste propriétaire de `activity_started`, `activity_completed` et `activity_aborted`. En monde circadien actif, il valide le début de sommeil sur la proposition gagnante de l'arbitre et les contraintes du monde ; il ne lit plus les seuils legacy `repos`/`energie`.

`rest` reste éveillé : il restaure P selon le profil, avec effet négligeable sur H V1. `sleep` dissipe H et peut restaurer P ; P ne décide jamais son début ni sa fin.

La fin devient un `SleepTerminationPolicy` explicite : projection H/phi de viabilité relative sommeil/veille, événements externes canoniques déjà supportés et hard cap technique séparé. Le hard cap ne justifie aucune valeur biologique. L'activité planifie une **prochaine réévaluation**, non une fin pilotée par les anciennes cibles 98/95 ; à l'échéance le moteur termine ou prolonge transactionnellement. Fonction, paramètres, événements externes admis et garde-fou technique restent une décision R&D/produit [D] : absence du contrat = NO-GO.

### 6.2 Stabilité critique

À la frontière calculée, `SleepPhysiologyService` expose seulement projection et éligibilité. Une méthode dédiée d'`ActivityEngine` :

1. re-matérialise et revalide dans la transaction ;
2. vérifie que l'activité est encore active et exige une veille soutenue ;
3. transitionne une fois vers `aborted` avec cause `wake_stability_critical` dans l'événement moteur ;
4. laisse `SimulationEngine` reconstruire la situation puis l'arbitre.

Elle ne force pas `sleep`, ne roule pas et ne se produit pas à chaque pulse. La classification data-driven `requires_sustained_wakefulness`, ses valeurs pour les activités existantes et sa migration sont une décision de configuration [D] à approuver ; aucune valeur ne sera inventée tacitement.

## 7. Coûts physiques vers P

Le lot créera une politique versionnée de coûts physiques : taux d'activité, récupération `rest`/`sleep` et surcharge de mouvement. Ces valeurs sont des calibrations d'ingénierie [C/D], pas une conversion numérique de `energie`.

Dans un monde actif :

- `ActivityEngine` détermine le régime et demande au propriétaire physiologique de matérialiser/appliquer P avec le régime de l'activité ;
- `CharacterEngine` détermine/valide le coût de déplacement et demande son application à `SleepPhysiologyService`, après matérialisation à la frontière ; il n'écrit jamais P directement ;
- les contrôles de blessure qui lisent `energie` reçoivent une projection P explicitement, sans écrire H/P ;
- `repos` et `energie` ne sont plus lus pour décision, validation, durée ou coût actif.

Les `need_state`, champs de définition et événements legacy restent inchangés et lisibles comme histoire. Un monde non actif conserve l'ancien chemin. Seed/règles/instances choisissent explicitement un profil de monde ; ils ne supposent jamais qu'une valeur legacy est une valeur V1.

## 8. Schéma, activation et observabilité

Les migrations 0045–0048 restent additives et ne seront pas réécrites. L'implémentation doit ajouter uniquement des migrations forward-only pour :

- contrat versionné de configuration de cutover/arbitrage ;
- politique de coûts P et classifications d'activité ;
- échéance/règle de réévaluation de sommeil si son owner exige une donnée persistante ;
- audit opérateur d'initialisation/activation si les tables actuelles ne permettent pas une séparation stricte du canon vécu.

Le schéma exact sera choisi après les contrats ci-dessus. Aucune migration ne crée H/phi/P dans une résidence existante ni ne transforme les besoins legacy.

### 8.1 Contrat obligatoire du manifeste initial T0

Avant l'activation réelle, un `InitialPhysiologyManifest` versionné, approuvé et relisible doit couvrir **chaque** personnage de la résidence. Chaque entrée contient au minimum : profil biologique et version sélectionnés ; H initiale ; phi initiale ; P initiale ; `previous_band` initial ; règle explicite des résidus H/phi et du reste P ; provenance et justification de chacun de ces choix. Le manifeste porte aussi une ancre T0 canonique unique pour tous les personnages.

Les valeurs sont des conditions initiales de modèle [D], non des mesures récupérées de la résidence : aucune ne provient de `repos` ou `energie`, aucun passé circadien n'est reconstruit, et aucune physiologie fictionnelle n'est déduite sans provenance canonique explicite. La règle de résidus doit être déclarée avant code ; elle ne peut pas utiliser les résidus pour encoder un historique absent. Sans manifeste complet approuvé, l'activation réelle est **NO-GO**.

Préflight doit séparer :

- **prepared complete** : modèle `ric.sleep.additive.v1`, profils/lumière complets, aucun état physiologique ;
- **active integrity** : manifeste complet, H/phi/P/résidus/hystérésis denses à même ancre, politiques/classes valides, aucun consommateur legacy autorisé sur chemin actif.

Hugin peut montrer l'état physiologique actif et P avec leur label propre. Il ne montre jamais `post_migration_initialization`. Munin n'acquiert aucun état subjectif ; Patoune reste non sapiente. L'admin étiquette explicitement les valeurs legacy comme historiques. Télémétrie/audit conservent options, mappings et versions de calibration, réévaluations, transitions sommeil et interruptions sans fabriquer de narration.

## 9. Déploiement futur : récupération puis activation atomique

Cette procédure est future et distincte du présent work order. Elle sépare récupération opérationnelle du crash et activation physiologique.

1. **Arrêt et preuve.** Confirmer runtime absent ; sauvegarde, hash, `integrity_check` et `foreign_key_check` en lecture. Ne pas appeler `WorldEngine.read_canonical_time`.
2. **Upgrade structurel/configuration inerte.** Migrer 44 vers le schéma final validé. Les migrations, catalogues et assignations purement techniques sont possibles ici s'ils n'avancent ni l'horloge ni la physiologie. Le monde reste `inactive` : il est impossible de réclamer `prepared` tant que la session 4 est ouverte, car `prepare_world()` appelle `_assert_preparable()`.
3. **Récupération officielle.** Chemin normal : `RuntimeSessionService.start()` ferme exactement id 4 avec `crash_recovered`, écrit son `runtime_session_event`, réancre au dernier instant durable sans rattrapage offline et ouvre une nouvelle session. Vérifier les artefacts.
4. **Gel contrôlé.** Sans faire tourner la simulation, arrêt propre officiel de cette nouvelle session. Il fixe T0 et laisse le monde sans session ouverte. Id 4 reste la preuve du crash.
5. **Préparation réelle.** Maintenant seulement, appeler `SleepPhysiologyFoundationService.prepare_world()` : ses validations officielles confirment modèle, lumière, profils et absence de session ouverte, puis le monde devient `prepared`. Préflight `prepared complete`, toujours sans H/phi/P.
6. **Transaction d'activation.** Runtime arrêté : valider à T0 le manifeste initial, profils, lumière, modèle et politiques. Dans une transaction unique, insérer H/phi/P/résidus/hystérésis denses à T0, écrire l'audit opérateur `post_migration_initialization`, activer le système et le chemin comportemental V1. Aucun `canonical_event`, aucune conversion de besoin, aucun intervalle antérieur à T0.
7. **Préflight actif.** Vérifier intégrité, ancres, digest/séquences de l'histoire préexistante (inchangés hors nouvelles tables/audit technique) et absence de session ouverte.
8. **Reprise contrôlée.** Démarrer une nouvelle session officielle puis le runtime. L'intégration commence à T0 ; aucun temps offline ne progresse.

L'étape 6 est tout-ou-rien : précondition ou écriture en échec laisse gate non actif, aucune ligne partielle et chemin legacy intact. Après engagement, aucun rollback silencieux par écritures inverses : arrêt protecteur, conservation des preuves et décision humaine à partir de la sauvegarde.

## 10. Lots après revue

1. **Contrats fonctionnels clos.** `ArbitrationScale`, `SleepTerminationPolicy`, classes de veille soutenue, coûts P et manifeste T0 sont approuvés côté R&D/produit ; leur traduction technique est le work order 86.
2. **Infrastructure inactive.** Migrations, résolveur causal, scheduler de frontières et APIs transactionnelles derrière gate non activable sans contrat complet.
3. **Arbitre/cycle sur copies synthétiques.** Début/fin sommeil, P, stabilité, interruption et réévaluation ; aucun runtime réel.
4. **Compatibilité.** Tests de tous consommateurs manifestés, préflight, observabilité et preuve de zéro lecture legacy active.
5. **Répétition sur copie de résidence.** Migration 44 vers final, récupération/gel simulés, activation atomique, restart.
6. **Revue GO/NO-GO Sol/propriétaire.** Seulement ensuite, procédure de section 9 sur la résidence réelle.

## 11. Falsifications et GO/NO-GO

Avant activation réelle, il faut au minimum :

- migration d'une copie 44 : besoins legacy, événements, séquences et histoire préexistante inchangés ; initialisation sans histoire rétroactive et audit non narratif ;
- injection d'échec à chaque écriture d'activation : aucun hybride ;
- recovery id 4 officielle sans saut offline, nouvelle session puis arrêt propre avant activation ;
- inactive/prepared : décisions et activités legacy compatibles ; active : recherche statique et spies prouvent l'absence de lecture `repos`/`energie` dans groupes commutés ;
- H/phi/P : lecture pure, restart, partitions irrégulières, aucune cadence runtime 1 s, frontières lumière/mouvement/activité correctes ;
- P : coût, insuffisance, récupération par rest/sleep, aucun motif sommeil même P faible, aucun transfert depuis `energie` ;
- arbitrage : score avec mapping/version/owner ; intention et motif peuvent gagner sans priorité de catégorie ; égalité/absence de score régies explicitement ;
- sommeil : report volontaire possible mais H/stabilité continuent, fin sans cible legacy, hard cap testé comme garde-fou ;
- stabilité : au plus une transition moteur par activité, jamais sommeil forcé, suivie d'un nouveau cycle d'arbitrage ;
- Hugin/admin distincts de legacy ; Munin/cognition ne reçoivent ni provenance ni omniscience.

**GO seulement si** les contrats approuvés sont traduits, les tests sont verts sur copie, les migrations sont forward-only, le manifeste est complet, le préflight actif est sain, la récupération id 4 est répétée sur copie et Sol/propriétaire autorisent explicitement la section 9.

**NO-GO si** un score shadow brut devient score production, une voie legacy reste active, une session est ouverte à l'initialisation, une cause n'a pas d'owner, une migration dérive le temps/crée une histoire ou un test révèle un état hybride.

## 12. Contrats à traduire techniquement

1. `ArbitrationScale` et son audit privé, incluant le lien intention -> action.
2. `SleepTerminationPolicy`, checkpoints, réévaluation et hard cap protecteur.
3. Classification `requires_sustained_wakefulness` dans le catalogue versionné.
4. Politique de coûts P et `InitialPhysiologyManifest` de résidence (H, phi, P, bande, résidus, profil, provenance et T0 commun).

Ces contrats ne donnent toujours pas le feu vert de code comportemental sur la résidence : leur implantation et leurs bancs doivent d'abord être revus.
