# Work order — contrats exécutables avant cutover circadien V1

**Statut :** conception technique et bancs inactifs à revoir par Sol avant code comportemental.

**Base auditée :** `098c4302a6edd503a9857447fdebeeb6c97e481f` (`main`), schéma de code 48.
**Hors périmètre absolu :** runtime réel, `data/vivarium-rodage.sqlite`, recovery de la session 4, migration réelle, `prepare_world()`, activation, conversion `repos -> H` / `energie -> P`, et tout cutover.

Ce document traduit les quatre contrats fonctionnels approuvés après le work order 85. Il ne modifie pas leurs invariants et ne transforme aucune valeur de calibration [C/D] en constante biologique.

## 1. Constats d'architecture et incompatibilités à résoudre

| Contrat approuvé | État réel | Traduction requise |
|---|---|---|
| Arbitrage d'actions | `DeterministicPolicy` compare des déficits legacy et `DecisionFrameService` affiche `active_intention > motives > goals` | nouveau service moteur d'arbitrage d'actions, séparé de `DecisionFrameService` |
| Intention subjective | `subjective_intention` contient un plan JSON opaque et `GoalService.active_intention()` ne retourne ni importance/urgence ni action validable | contrat explicite de contribution intention -> action ; aucune action inférée d'un plan opaque |
| Sommeil réévaluable | `ActivityEngine` déduit `planned_end_at` des cibles legacy et clôt automatiquement | checkpoint de sommeil détenu par `ActivityEngine`, avec réévaluation ou signal protecteur |
| P | `SleepPhysiologyService` est le propriétaire prévu de P, mais `CharacterEngine` écrit directement `need_state.energie` pour le mouvement | API de demande de coût ; seul le service physiologique écrit `physical_capacity_state` |
| Activités | `activity_definition` ne contient ni exigence de veille ni intensité physique | champs data-driven versionnés et préflight refusant toute activité non classée en monde actif |

Ces écarts sont des manques techniques normaux. Ils interdisent de promouvoir le shadow : `highest_explicit_score` reste un test structurel et ne devient pas l'arbitre production.

## 2. Contrat moteur d'arbitrage d'actions

### 2.1 Owner et frontière épistémique

Créer un `ActionArbitrationService` déterministe, appelé par `SimulationEngine` seulement dans le chemin d'un monde physiologique `active`. Il construit une `ActionArbitrationFrame` depuis : physiologie (H/phi -> propension additive, P -> éligibilité physique), besoins actifs de satiété/hygiène, objectifs/intention subjectifs lus via `GoalService`, activité canonique courante et faisabilité Reality/Interaction.

Le service ne persiste aucune cognition et n'applique aucune activité. `ActivityEngine` valide l'action gagnante et demeure owner de la mutation canonique. LLM, Motivation, Attention et providers ne peuvent ni écrire H/phi/P ni appliquer l'action. `DecisionFrameService` ne doit pas être réutilisé comme arbitre : sa hiérarchie actuelle est une projection legacy incompatible.

### 2.2 Contributions, corrélation et résultat

Une frame compare des **actions candidates**, chacune soutenue par des `ArbitrationContribution` : `action_key`, source brute, owner, `correlation_group`, transformation versionnée, provenance, faisabilité et score transformé. H et C sont déjà combinés dans une unique contribution `sleep_regulation` issue de la propension additive ; ils ne sont jamais double-comptés.

Le profil immutable/versionné `action_arbitration_policy`, assigné au monde, définit mappings vers l'échelle d'ingénierie commune, groupes corrélés, agrégation saturante des groupes indépendants, inertie bornée de l'action courante, seuil de quasi-égalité et horizon de réévaluation. Forme candidate à banc : maximum dans chaque groupe corrélé, puis agrégation saturante monotone des groupes indépendants. Mappings, plafond d'inertie, poids et bande d'égalité restent [D].

Le résultat porte toutes les contributions, la politique/version et la raison de non-transition. En égalité/quasi-égalité, si l'action courante est leader, le résultat est `continue_current_until_boundary`; sinon `reassess_at_boundary`. Aucun tie-break de catégorie n'est permis. Sans transition imposée, l'état courant continue jusqu'à la prochaine frontière causale.

### 2.3 Intentions vers actions

Le plan et `resume_context_json` actuels sont opaques. Il est interdit de les parser heuristiquement pour inventer « finir le boss » ou toute autre action. Ajouter `subjective_intention_action_link`, append-only et owned par `GoalService` : une intention déclare explicitement une ou plusieurs actions candidates validables par le moteur, avec contribution subjective et provenance. Une intention legacy sans lien ne produit aucune contribution exécutable ; elle reste subjective sans privilège caché.

Le lien référence une action du catalogue moteur et ses contraintes, pas du texte libre. `GoalService` garde l'ownership du lien ; `ActionArbitrationService` le lit et le transforme selon la politique. Ainsi, deux agentes peuvent diverger à physiologie égale sans faire d'une valeur subjective un fait canonique.

### 2.4 Audit privé

Le détail des contributions peut contenir des données subjectives. Ajouter un journal opérateur append-only `action_arbitration_audit` : digest de frame, options, sources/owners, politique/calibration, résultat, instant canonique et raison. Il n'entre ni dans `canonical_event`, ni Hugin, ni Munin. `activity_started` garde l'action canonique et au plus une référence technique opaque.

## 3. Politique de terminaison de sommeil

`SleepPhysiologyService` fournit une projection H/phi et une viabilité de veille pure. `ActivityEngine` possède le cycle de **son** activité `sleep`, ses checkpoints, sa complétion et ses interruptions. La mémoire d'hystérésis de sortie est donc un état de planification d'activité : `activity_sleep_checkpoint`, lié à l'activité active, contient `next_reassessment_at`, la bande `continue_sleep|wake_admissible` et le garde-fou technique. Ce n'est pas un second état H/phi. `previous_band` de stabilité de veille reste physiologique et détenu par `SleepPhysiologyService`.

Au checkpoint, dans une transaction : matérialiser le segment de sommeil, lire projection et bande, appliquer l'hystérésis sommeil/veille, puis compléter `sleep`, ou poursuivre avec un prochain checkpoint, ou accepter un réveil externe réellement perceptible, ou signaler le hard cap au runtime/Guardian. Le hard cap ne termine ni ne réveille l'activité. Après complétion, une nouvelle frame décide de la suite ; se réveiller ne signifie pas décider de se lever.

Le code actuel ne possède pas d'événement externe typé avec contrat d'accessibilité pour le réveil. V1 doit donc garder cette extension vide/pluggable plutôt que transformer tout `canonical_event` en réveil omniscient. Les engagements temporels restent absents.

## 4. Définition générique des activités et P

Étendre `activity_definition` avec `requires_sustained_wakefulness` (booléen) et `physical_load_class` (`none`, `light`, `moderate`, `vigorous`). La classe est une propriété générique, non un coût chiffré.

Créer un profil immutable/versionné `physical_capacity_policy`, assigné au monde, qui traduit classe d'activité, `rest`, `sleep` et traversée d'arête en coûts/récupérations P. Il remplace l'unique coût synthétique de tout `wake`, qui ne peut pas devenir le régime production par défaut.

`CharacterEngine` détermine chemin, nombre d'arêtes et surcharge de blessure ; `ActivityEngine` détermine l'activité/régime. Ils transmettent une `PhysicalCostRequest` validée à `SleepPhysiologyService`, qui seul matérialise et débite P dans la transaction. Les coûts de déplacement sont génériques par arête, car le graphe n'expose pas encore terrain ou charge ; un futur owner Reality pourra enrichir la demande.

### 4.1 Classification V1 approuvée

| `requires_sustained_wakefulness = false` | `requires_sustained_wakefulness = true` |
|---|---|
| `sleep`, `rest`, `idle` | `eat`, `clean`, `gaming`, `photography`, `sport`, `girly_care`, `socialize`, `watch_tv` |

Cette liste est appliquée par migration de données contrôlée et préflight, non par `if activity_type == ...`. Les classes physiques initiales et coûts restent calibration [C/D] : `unclassified` est tolérable legacy mais interdit l'activation. P faible peut rendre une requête coûteuse non faisable et soutenir `rest`; il ne crée jamais `sleep_regulation`. Le chemin actif ne lit ni ne convertit `energie`.

## 5. Manifeste initial T0

Ajouter `initial_physiology_manifest` et `initial_physiology_manifest_entry`, catalogues techniques immutables/versionnés. Chaque entrée fixe personnage, profil/version biologique assignés, H, phi, P, `previous_band`, résidus H/phi, reste P, provenance et justification. Le manifeste fixe modèle `ric.sleep.additive.v1` et ancre T0 canonique commune.

Il est enregistré pendant la fenêtre runtime arrêtée, seulement après recovery officielle et arrêt propre, lorsque T0 est connu. `SleepPhysiologyFoundationService` valide couverture, profils, bornes, ancre et absence de session ; `SleepPhysiologyService` l'appliquera atomiquement lors d'une activation future. C'est une condition initiale [D], auditée comme `post_migration_initialization`, jamais un événement vécu ou une reconstruction.

Les résidus sont explicites et ne peuvent encoder une histoire absente. Candidat parcimonieux à banc : H/phi/P choisis à précision persistée, résidus H/phi et reste P zéro, puis première intégration seulement après T0. Le manifeste, pas un fallback caché, décide les valeurs finales.

## 6. Migrations forward-only et ordre de code

1. Étendre les définitions d'activité, inscrire la classification de section 4.1 et laisser la charge physique non classée hors monde actif.
2. Ajouter `physical_capacity_policy` et son assignment, avec validateur de complétude ; aucune écriture P ni runtime.
3. Ajouter `action_arbitration_policy`, assignment monde, liens subjectifs intention -> action et audit technique privé.
4. Ajouter checkpoints de sommeil, API pure de terminaison, hard-cap protecteur et préflight ; aucun réveil forcé.
5. Ajouter manifeste/version/entrées et validateur T0, sans initialiser de résidence.
6. Raccorder uniquement des mondes synthétiques/copies : demandes P, arbitre, scheduler de frontières et `ActivityEngine`.
7. Après revue seulement, commuter les consommateurs legacy ensemble dans un monde de test actif ; la résidence réelle reste hors de portée.

Le gate existant `inactive|prepared|active` est le commutateur unique. Il passe à `active` seulement dans la transaction du work order 85, après politiques et états complets. Aucun flag secondaire ne pilote le sommeil en parallèle.

## 7. Bancs et falsifications hors runtime réel

| Banc | Paramètres testables [C/D] | Falsifications minimales |
|---|---|---|
| `action_arbitration_lab` | mappings, saturation, corrélation, inertie, égalité | aucune priorité de catégorie ; H/C comptés une fois ; deux profils subjectifs divergent ; P ne crée pas sommeil ; égalité continue ou réévalue sans tie-break |
| `sleep_termination_lab` | seuils/bandes, horizon checkpoint, garde technique | aucune cible legacy/durée fixe ; réveil stable ; pas d'oscillation ; wake externe inaccessible refusé ; hard cap sans `activity_completed` fictif |
| `physical_capacity_lab` | classes, coût/arête, récupération, limite effort | attente sans coût arbitraire ; activité/mouvement limitent P ; rest/sleep restaurent P ; rest ne baisse pas H ; P faible ne propose jamais sommeil |
| `initial_manifest_lab` | valeurs T0, résidus, profils | couverture complète ; T0 commun ; aucun besoin legacy ; aucun événement vécu ; restart fidèle à l'ancre |
| intégration synthétique | contrats ci-dessus | critical au plus une fois ; abort -> nouvelle frame ; lecture pure ; partitions/restart ; zéro chemin legacy actif |

Les paramètres explorables ici sont seulement ceux des politiques et bancs : mappings, saturation/inertie/égalité, seuils/horizon de fin sommeil, hard cap, charges/récupérations P et valeurs T0. Aucun réglage ne touche le runtime vivant ou la résidence.

## 8. GO / NO-GO

**GO code inactif :** owners et schémas confirmés, APIs sans écriture hors owner, profils versionnés et bancs/faux positifs de préflight définis.

**NO-GO comportemental :** intention sans lien d'action validable ; mapping sans provenance ; activité non classée ; hard cap qui réveille ; external wake sans accessibilité ; écriture P hors service owner ; lecture de `repos`/`energie` dans un monde actif ; ou toute opération sur la résidence réelle.

Le prochain code, après revue, reste additif et s'exécute uniquement sur mondes synthétiques ou copies contrôlées.
