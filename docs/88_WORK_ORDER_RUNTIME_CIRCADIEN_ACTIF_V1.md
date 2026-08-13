# Work order 88 — runtime circadien actif V1

**Statut :** FERMÉ — validation fonctionnelle terminée; aucun cutover de résidence persistante n'est autorisé par cette clôture.

**Base de développement :** `b0568de5db9af68e13d51b112535b23894a7c73b`.

**HEAD fonctionnel validé :** `fe1d24a0cd5f32463c594d2de6bf2e3ba7ad0667`.

**Preuve de validation finale :** GitHub Actions, Windows Server 2025, Python 3.12.10, `python -m compileall -q src tests`, puis **1029 tests réussis en 392,09 s, 0 échec**. Le correctif final owner-backed avait également passé **15 tests ciblés** avant la suite complète.

**Dépendances fermées :** `docs/85_WORK_ORDER_CUTOVER_CIRCADIEN_V1.md` et `docs/86_WORK_ORDER_CONTRATS_CUTOVER_CIRCADIEN_V1.md`.

**Hors périmètre absolu de ce lot :** `data/vivarium-rodage.sqlite`, reprise de la session réelle, activation ou migration d'une résidence persistante existante, conversion `repos -> H`, conversion `energie -> P`, reconstruction d'un passé physiologique, suppression des données legacy.

## 0. Verdict de clôture

WO88 est fermé avec les constats suivants :

- le runtime `physiology=active` utilise H/phi/P et des causes owner-backed ;
- `repos` et `energie` ne sont plus des causes concurrentes sur le chemin actif ;
- l'arbitrage owner-backed ne traverse plus `project_synthetic()` ; les APIs `_synthetic` restent des entrées de banc ;
- les mondes `inactive` et `prepared` conservent le comportement legacy ;
- l'activation T0 atomique depuis un manifeste scellé appartient au service de fondation physiologique; après activation, `SleepPhysiologyService` est l'écrivain runtime de H/phi/P/résidus/hystérésis ;
- `ActivityEngine` reste propriétaire des activités; `ActiveSimulationEngine` ordonnance les frontières des mondes actifs, tandis que `SimulationEngine` reste le scheduler legacy des mondes non actifs ;
- les frontières imbriquées restent transactionnelles via la transaction externe et les savepoints internes ;
- aucune couche cognitive ni LLM n'a obtenu de droit d'écriture canonique supplémentaire ;
- le diff depuis la base est linéaire et n'ajoute/modifie aucune migration dans WO88 ;
- aucun fichier SQLite réel ni résidence persistante n'a été modifié ;
- après le HEAD fonctionnel validé, seuls les workflows/scripts WO88 jetables ont été retirés et la documentation de clôture a été mise à jour; aucun `src/` ni `tests/` n'a changé ;
- la prochaine étape autorisée est Rodage V2 sur base neuve avec manifeste T0 explicite et politiques complètes, sans migration de l'ancien rodage par défaut.

## 1. But

Fermer le chemin d'exécution des mondes dont `world_physiology_system.status = 'active'` sans promouvoir les APIs de banc `_synthetic` en production et sans laisser deux propriétaires concurrents pour le sommeil ou la capacité physique.

À la sortie du lot :

- les mondes `inactive` et `prepared` conservent exactement le comportement legacy ;
- un monde de test `active` utilise H/phi/P et les contrats d'arbitrage/checkpoint déjà fondés ;
- le chemin actif ne lit ni `repos` ni `energie` pour choisir, valider, terminer ou coûter une action ;
- l'activation T0 atomique appartient au service de fondation physiologique, puis `SleepPhysiologyService` reste l'écrivain runtime persistant de H/phi/P/résidus/hystérésis ;
- `ActivityEngine` reste propriétaire des activités; `ActiveSimulationEngine` ordonnance les frontières actives et `SimulationEngine` conserve l'ordonnancement legacy des mondes non actifs ;
- aucune couche cognitive ni LLM n'obtient un droit d'écriture canonique supplémentaire.

Ce work order ne constitue pas une autorisation de cutover réel.

## 2. Décision d'architecture

Le runtime actif est construit par raccordement des owners existants, pas par un second moteur parallèle.

La logique mathématique pure peut être extraite dans un noyau sans persistance lorsque cela évite une duplication, sur le même modèle que la séparation `circadian_model.py` / `sleep_physiology.py`. L'ownership persistant ne change pas : les calculs purs proposent un résultat, `SleepPhysiologyService` valide et écrit P en runtime après activation T0.

Le module `synthetic_action_arbitration.py` est un banc. Les contrats physiques génériques qu'il contient aujourd'hui ne doivent pas rester owned par un module nommé `synthetic` s'ils deviennent nécessaires au runtime. Ils seront déplacés/réutilisés sans conserver deux implémentations divergentes.

## 3. Lot 88A — noyau P et matérialisation owner-backed

### 3.1 Contrat P commun

Unifier les types et calculs de demande physique utilisés par le banc et le futur runtime :

- requête d'activité par `physical_load_class` ;
- requête de traversée par nombre d'arêtes ;
- évaluation de faisabilité depuis la politique P assignée ;
- débit/récupération temporels en milli-unités avec reste exact ;
- coût discret de traversée séparé du débit temporel.

Les classes restent `none|light|moderate|vigorous`. Les coefficients restent des données versionnées [D], jamais des constantes biologiques cachées.

Le calcul doit être invariant au partitionnement temporel. Une saturation à 0 ou 100000 remet le reste numérique à zéro. Un coût discret de traversée ne crée pas un faux intervalle de temps.

### 3.2 Résolution des causes

Le runtime n'accepte aucun `RegulationInput` libre. Pour chaque personnage, à une frontière canonique explicite, la source est reconstruite depuis les owners objectifs déjà persistés :

- temps canonique ;
- calendrier lumineux assigné ;
- lieu canonique et profil d'exposition ;
- activité canonique courante ;
- `physical_load_class` / `requires_sustained_wakefulness` de la définition d'activité ;
- occlusion objective de sommeil ;
- stimulation = 0 tant qu'aucun owner Reality borné n'existe.

L'input dérivé conserve sa provenance et son fingerprint. Une lecture seule ne fait jamais progresser H/phi/P.

### 3.3 Matérialisation

Ajouter une API owner-backed qui matérialise l'ancien segment jusqu'à `target_at` avant toute mutation qui change sa cause.

Invariants :

- monde obligatoirement `active` et cohérent ;
- ancre cible canonique, entière et >= ancre persistée ;
- `dt = 0` idempotent ;
- H/phi utilisent le modèle circadien sélectionné et la source owner-backed ;
- P utilise la politique physique assignée et la classe objective de l'activité ;
- `rest` et `sleep` utilisent leurs récupérations P dédiées ;
- aucune lecture/écriture `need_state.energie` ou `need_state.repos` ;
- H/phi/P/résidus/hystérésis avancent à une ancre commune dans une transaction ;
- aucune cadence runtime n'est déduite du quantum synthétique d'une seconde.

La détection interne d'un crossing de stabilité peut employer une résolution numérique bornée, mais ce pas reste un détail de calcul, pas un tick du moteur.

## 4. Lot 88B — frontières ActivityEngine

Raccorder ensuite `ActivityEngine` sur les mondes de test actifs.

Ordre obligatoire à toute frontière causale :

1. relire et revalider le contexte canonique ;
2. matérialiser le segment physiologique qui se termine ;
3. valider faisabilité et politique P si l'action suivante l'exige ;
4. appliquer la mutation canonique d'activité/position ;
5. appliquer le coût discret éventuel appartenant à cette mutation ;
6. écrire l'événement canonique et les états owner-backed dans la même transaction ;
7. programmer/reconstruire la prochaine frontière depuis le nouvel état.

Pour `sleep`, le chemin actif ne lit plus `SLEEP_REPOS_TARGET` ni `SLEEP_ENERGIE_TARGET`. Le début provient d'une action gagnante validée ; la poursuite/fin provient du checkpoint de sommeil et de la viabilité owner-backed. `rest` reste éveillé.

Une stabilité `critical` n'impose jamais automatiquement `sleep` : elle peut seulement rendre l'activité exigeant une veille soutenue inéligible/abortable selon le contrat déjà approuvé, puis provoquer une nouvelle frame d'arbitrage.

## 5. Lot 88C — déplacement et coût P

Le déplacement actif reste validé par le graphe Reality existant.

- le chemin complet est validé avant mutation ;
- la faisabilité P tient compte du nombre d'arêtes prévu ;
- la traversée et son coût P sont atomiques selon le contrat de l'action ;
- aucun débit P n'est écrit directement par `CharacterEngine` ;
- une traversée rejetée ou abortée avant mutation coûte P = 0 ;
- aucune téléportation ni conversion depuis `energie`.

Si l'architecture actuelle impose plusieurs événements `character_moved` pour un déplacement multi-arêtes, le coût et le rollback doivent rester cohérents avec cette granularité sans laisser une moitié de déplacement validée comme succès complet.

## 6. Lot 88D — arbitre actif et scheduler

Une fois 88A–C fermés :

- promouvoir le contrat d'arbitrage déjà persisté vers un service non synthétique sans changer son échelle silencieusement ;
- construire les contributions depuis leurs owners ;
- exécuter l'action gagnante seulement via `ActionOrchestrator` et les moteurs canoniques ;
- garder l'audit d'arbitrage privé distinct du canon vécu ;
- remplacer, pour les mondes `active`, l'échéance legacy unique de `SimulationEngine` par le minimum déterministe des frontières pertinentes : activité, checkpoint sommeil, réévaluation d'arbitrage, transition lumineuse et crossing critique calculé.

Aucun pulse mural ne matérialise la physiologie par simple passage du temps.

## 7. Lot 88E — fermeture des consommateurs legacy actifs

Relancer le manifeste `circadian_shadow.LEGACY_CONSUMERS` et une recherche structurée juste avant fermeture.

Le lot ne peut être déclaré fermé tant qu'un monde `active` peut encore lire `repos` ou `energie` comme cause actuelle dans :

- décision/motivation/attention/frame de décision ;
- validation, coût, durée ou terminaison d'activité ;
- mouvement et blessure lorsqu'ils exigent une capacité physique ;
- lectures opérateur présentées comme état physiologique courant.

Les données et événements legacy restent conservés comme histoire et pour les mondes non actifs.

## 8. Falsifications obligatoires

Au minimum :

- `inactive` et `prepared` restent bit-for-bit compatibles sur les scénarios de référence ;
- aucun accès legacy actif détecté par les gardes dédiées ;
- partitionnement temporel différent => même H/phi/P/ancre/résidus ;
- `dt=0` => aucune mutation ni événement ;
- P bas rend une activité coûteuse ou traversée infaisable sans créer de motif sommeil ;
- `rest` restaure P sans devenir `sleep` ;
- sommeil avance H/phi/P avec owners objectifs seulement ;
- changement de lieu/activité matérialise l'ancienne cause avant la nouvelle ;
- rollback complet si une étape post-validation échoue ;
- retry d'une même frame/action reste idempotent ;
- crossing critique abort une seule fois une activité exigeant une veille soutenue et ne force pas le sommeil ;
- lecture Hugin/Admin/Guardian ne matérialise rien ;
- aucun LLM n'est requis pour faire progresser la physiologie ou valider une mutation canonique.

Chaque sous-lot exécute ses tests ciblés puis la suite complète avant commit de fermeture.

## 9. Rodage V2

Un nouveau rodage propre est l'étape suivante, pas un raccourci autour du runtime actif.

Il sera créé seulement après fermeture de 88A–E, depuis une base neuve :

- aucun passé physiologique inventé ;
- manifeste T0 explicite ;
- politiques/versionnements complets ;
- profils des habitantes réellement différenciés et causalement connectés aux mécanismes génériques ;
- ancien `data/vivarium-rodage.sqlite` conservé comme artefact historique, non migré par défaut.

La décision de créer Rodage V2 n'autorise toujours pas une écriture dans une résidence réelle existante.

## 10. Porte de fermeture

WO88 est fermé seulement si :

1. tous les tests ciblés et la suite complète passent sur la branche de travail ;
2. le chemin actif n'a plus de concurrence legacy sur les domaines commutés ;
3. les mondes non actifs gardent leur compatibilité ;
4. le diff et les migrations sont auditables et forward-only ;
5. aucun fichier runtime/SQLite réel n'a été modifié ;
6. la passation et la roadmap sont mises à jour avec les preuves exactes du HEAD testé.

**Verdict : critères 1–6 satisfaits. WO88 fermé.**

## 11. Roadmap d'exécution séquentielle

Cette section impose l'ordre de travail pour éviter les validations concurrentes et les HEAD ambigus.

### Règle de cadence

- une seule étape active à la fois ;
- aucun nouveau correctif tant que les tests de l'étape courante ne sont pas terminés ;
- aucun nouveau workflow de réparation pendant une suite complète ;
- après chaque commit généré, relire le HEAD avant toute action suivante ;
- un échec de test est traité comme un seul problème jusqu'à résolution ou diagnostic explicite.

### Étape 1 — figer et vérifier le HEAD courant — FERMÉE

Référence de reprise initiale : branche `chatgpt/wo88-final-validation`, HEAD observé `0b1883364368e28752e1511d9c08fbf598d89f12`.

Critère de sortie satisfait : un HEAD unique et stable a été identifié avant validation.

### Étape 2 — suite complète sur ce HEAD exact — FERMÉE

Après correction du dernier chemin `_synthetic`, validation fonctionnelle finale au HEAD `fe1d24a0cd5f32463c594d2de6bf2e3ba7ad0667` : **1029 passed**, 0 échec.

### Étape 3 — audit WO88E des consommateurs legacy — FERMÉE

Le manifeste `circadian_shadow.LEGACY_CONSUMERS` et les chemins actifs ont été audités. Aucun consommateur `repos`/`energie` causal concurrent n'est resté sur les mondes physiologiques `active`.

### Étape 4 — audit des invariants et du diff — FERMÉE

Ownership persistant, frontières transactionnelles, absence d'écriture cognitive directe, absence de cutover réel, compatibilité `inactive`/`prepared` et caractère forward-only ont été vérifiés. Le seul défaut trouvé — arbitrage owner-backed passant encore par `project_synthetic()` — a été corrigé et falsifié avant la suite complète.

### Étape 5 — fermeture documentaire WO88 — FERMÉE

La passation et la roadmap portent désormais le HEAD exact testé et le compteur de tests. Les workflows/scripts WO88 jetables ont été retirés seulement après la validation complète. Une comparaison post-validation confirme qu'aucun `src/` ni `tests/` n'a changé après `fe1d24a0…`.

### Étape 6 — Rodage V2 — PROCHAINE ÉTAPE

Cette étape commence seulement après la présente fermeture formelle de WO88.

Action unique initiale : préparer le bootstrap d'une base neuve avec manifeste T0 explicite et politiques complètes, sans reprendre ni migrer l'ancien rodage par défaut.