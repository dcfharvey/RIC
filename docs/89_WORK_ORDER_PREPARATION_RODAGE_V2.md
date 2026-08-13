# Work order 89 — préparation pré-rodage V2

**Statut :** OUVERT — **89A FERMÉ**; prochaine étape autorisée : 89B seulement.

**Base documentaire de départ :** `bbdac5c737c6fa0b28f23657b826b008b5b12fd2` (`docs: close WO88 formally`).

**Base fonctionnelle héritée de WO88 :** `fe1d24a0cd5f32463c594d2de6bf2e3ba7ad0667`, validée par `python -m compileall -q src tests` puis **1029 tests réussis en 392,09 s, 0 échec** sous Windows Server 2025 / Python 3.12.10.

**État de référence au départ :** package `0.1.0a15`; schéma de code 55; dernière migration `0055_sleep_completion_authorization.sql`; WO88 fermé; aucun cutover de résidence persistante autorisé.

**Dépendance fermée :** `docs/88_WORK_ORDER_RUNTIME_CIRCADIEN_ACTIF_V1.md`.

## 0A. Verdict 89A — photographie de release

89A est fermé sur la photographie suivante :

- branche distante de travail : `chatgpt/wo89-pre-rodage-v2` ;
- HEAD documentaire de 89A avant consignation : `a5ef14d6b7d4a3c61d6d4305ee338319582d211c` ;
- dernier checkout local confirmé avant l'ouverture de WO89 : branche `chatgpt/wo88-final-validation`, HEAD `bbdac5c737c6fa0b28f23657b826b008b5b12fd2`, fichiers suivis propres ; l'alignement local vers la base de rodage appartient à 89B ;
- version déclarée dans `pyproject.toml` : `0.1.0a15` ; `src/vivarium/__init__.py` expose également `0.1.0a15` ;
- schéma de code : **55** ; le runner `migrations.py` définit le registre de migrations comme autorité de version et la dernière migration présente est `0055_sleep_completion_authorization.sql` ;
- baseline fonctionnelle héritée : HEAD `fe1d24a0cd5f32463c594d2de6bf2e3ba7ad0667`, compilation verte et **1029 tests réussis** ; les commits de fermeture WO88 postérieurs à ce HEAD n'ont pas modifié `src/` ni `tests/` ;
- `README.md` contient encore une photographie présentée comme courante au schéma 39 / 767 tests ;
- `docs/15_ROADMAP_ACTIVE.md` contient, sous son bloc prioritaire WO88, une ancienne section « État actuel » au schéma 48 / 929 tests ;
- `docs/99_PASSATION_COURANTE.md` contient, sous son bloc prioritaire WO88, une ancienne photographie technique au schéma 48 / 929 tests ;
- `CHANGELOG.md` conserve correctement l'historique `0.1.0a15`, mais son sommet ne contient pas encore une entrée de release correspondant à la fermeture WO88 et au futur Rodage V2 ;
- ces divergences sont documentaires : elles ne changent pas la hiérarchie de vérité HEAD + migrations + tests, mais elles devront être harmonisées avant fermeture de WO89.

### Décision de version 89A

**Version produit retenue pour la base du Rodage V2 : `0.2.0a1`.**

Motif produit : l'activation H/φ/P comme causes runtime owner-backed, combinée à un T0 neuf et à une nouvelle histoire persistante, constitue une séparation fonctionnelle suffisamment nette avec le cycle `0.1.0aN` pour mériter un nouveau jalon alpha mineur. Ce numéro ne prétend ni à une stabilité API, ni à une maturité bêta, ni à une rupture de compatibilité imposée par SemVer ; il sert de marqueur produit traçable pour le nouveau cycle de rodage.

Le bump n'est **pas** appliqué pendant 89A : la photographie doit précéder les changements de métadonnées. Les sources de version seront synchronisées dans la séquence WO89 après stabilisation de la base Git et avant fermeture 89E.

### Critère de sortie 89A

**SATISFAIT.** Version cible choisie : `0.2.0a1`; photographie HEAD/schéma/migration/tests et portée des documents historiques enregistrées. Aucune base SQLite de rodage n'a été touchée.

## 0. Intention

Préparer une base de rodage fraîche, identifiable, observable et reproductible **sans commencer encore l'histoire persistante du Rodage V2**.

Ce work order est volontairement court. Il ne doit pas devenir une nouvelle phase de développement fonctionnel. Son rôle est de supprimer les ambiguïtés de version, de branche, d'observabilité et de bootstrap qui rendraient un nouveau rodage difficile à diagnostiquer ou à reproduire.

À sa fermeture, on doit pouvoir répondre sans ambiguïté à cinq questions :

1. quel commit exact constitue la base du prochain rodage ;
2. quel numéro de version produit lui est associé ;
3. quel schéma et quelles migrations sont attendus ;
4. comment observer H/φ/P sans modifier la simulation ;
5. comment construire et valider un T0 neuf avant de laisser l'histoire commencer.

## 1. Hors périmètre

WO89 n'autorise pas :

- la migration ou la reprise de l'ancien `data/vivarium-rodage.sqlite` ;
- la création d'une nouvelle histoire persistante officielle avant la fermeture du lot ;
- la reconstruction d'un passé physiologique ;
- un nouveau modèle cognitif, social, affectif, comportemental ou physiologique ;
- l'enrichissement général des activités ou des conversations ;
- une refonte de l'interface ;
- une modification du contrat fondamental `LLM propose, moteur valide` ;
- une écriture cognitive directe dans le canon ;
- la remise en concurrence de `repos`/`energie` avec H/φ/P sur un monde `physiology=active` ;
- la résolution opportuniste de défauts alpha non bloquants qui n'empêchent ni l'observation ni le lancement propre du rodage ;
- la pérennisation du bridge de développement, qui reste un chantier séparé.

Si une anomalie fonctionnelle réelle est découverte pendant WO89, elle devient un problème unique à traiter séquentiellement : reproduction, diagnostic, correction ciblée, tests ciblés, suite complète, puis reprise de WO89.

## 2. Gouvernance

Ce lot est principalement un lot d'ingénierie/release et d'observabilité. Il n'introduit aucun nouveau modèle vivant nécessitant une nouvelle revue de littérature scientifique.

- ChatGPT fixe le contrat fonctionnel, les invariants et la documentation de lot.
- Codex choisit l'implantation réelle, l'ordre technique, les migrations éventuelles, les tests et la stratégie d'intégration Git à partir du dépôt réel.
- Le propriétaire conserve la décision finale sur le numéro de version produit et sur le T0 canonique du Rodage V2.

Aucune préférence de branche ou de structure de code décrite ici ne doit être interprétée comme une prescription silencieuse à Codex.

## 3. Lot 89A — identité de release et photographie de référence — FERMÉ

Avant tout autre changement fonctionnel :

1. relever le HEAD réel, le statut Git et la branche de travail ;
2. confirmer la dernière migration réellement chargée ;
3. confirmer la version déclarée dans `pyproject.toml` et les références de version dans les documents actifs ;
4. identifier les photographies historiques manifestement périmées dans `docs/15_ROADMAP_ACTIVE.md`, `docs/99_PASSATION_COURANTE.md`, `CHANGELOG.md` et toute autre source présentée comme état courant ;
5. proposer un numéro de version cohérent pour la base du Rodage V2 sans le changer silencieusement.

### Décision de version

Le numéro de version est un marqueur produit, pas un compteur de work orders.

Deux familles étaient acceptables au départ :

- poursuivre l'alpha `0.1.0aN` si le nouveau rodage était considéré comme une évolution interne du même MVP ;
- ouvrir `0.2.0a1` si l'activation H/φ/P et le nouveau T0 étaient considérés comme une nouvelle génération fonctionnelle de l'alpha.

**Décision 89A : `0.2.0a1`.**

### Critère de sortie 89A

Une photographie unique est enregistrée : version choisie, HEAD candidat, schéma, dernière migration, suite de tests de référence et portée exacte des documents historiques conservés.

**Verdict : satisfait.**

## 4. Lot 89B — base Git canonique du prochain rodage

Le Rodage V2 ne doit pas démarrer sur une branche de réparation ou un worktree ambigu.

Codex doit déterminer, à partir du graphe Git réel, le chemin d'intégration le plus sûr pour obtenir une base de rodage stable contenant la fermeture fonctionnelle de WO88 et sa documentation, sans réintroduire de scripts/workflows jetables retirés à la clôture.

Exigences fonctionnelles :

- un seul HEAD candidat clairement nommé et vérifiable ;
- aucun changement suivi non committé ;
- aucune dépendance à un worktree temporaire pour lancer le rodage ;
- l'historique WO88 fonctionnel et ses preuves restent traçables ;
- la stratégie de merge/rebase/fast-forward appartient à Codex et doit être explicitée avant exécution si elle modifie une branche de référence partagée ;
- aucune résidence SQLite réelle n'est touchée par l'intégration Git.

### Critère de sortie 89B

Le futur rodage possède une base Git exacte et stable, avec SHA enregistré. Les branches historiques peuvent rester présentes; aucune suppression n'est requise pour fermer ce lot.

## 5. Lot 89C — observabilité opérateur de H/φ/P

Le système physiologique actif ne doit pas être une boîte noire pendant le rodage.

Le read-model Hugin/Munin ou son chemin opérateur existant doit pouvoir exposer, pour un monde `physiology=active`, un état physiologique lisible **sans aucune écriture**.

### Minimum observable

Pour chaque personnage explicitement demandé, le rapport structuré doit permettre d'identifier au minimum :

- le statut physiologique du monde ;
- H (pression/régulation homéostatique) ;
- φ (phase circadienne) ;
- P (capacité physique) ;
- l'ancre persistée correspondante ;
- le temps canonique auquel une éventuelle projection read-only est évaluée ;
- l'état de stabilité/sommeil déjà possédé par le sous-système si celui-ci est exposé comme cause opératoire.

Le choix des noms de champs, classes et méthodes appartient à Codex.

### Distinction obligatoire : persisté vs dérivé

Si l'affichage calcule une projection owner-backed jusqu'au temps canonique courant sans la matérialiser, le rapport doit distinguer explicitement :

- **état persisté** à son ancre ;
- **projection read-only dérivée** à un autre instant.

Une projection non matérialisée ne doit jamais être présentée comme une nouvelle écriture canonique. Le rapport ne doit pas faire croire que le simple passage du temps a persisté H/φ/P.

### Invariants d'observation

- aucune mutation de base ni événement canonique causé par la lecture ;
- aucun changement d'ancre dû à Hugin/Munin/Admin/Guardian ;
- aucune API publique `_synthetic` utilisée par le chemin opérateur actif ;
- les mondes `inactive`/`prepared` restent compatibles et ne se voient pas attribuer artificiellement des états H/φ/P ;
- `repos`/`energie` peuvent rester visibles comme données legacy/historiques si nécessaire, mais ne doivent pas être étiquetés comme physiologie active actuelle ;
- aucune donnée subjective d'un agent ne devient un fait canonique par la présentation opérateur.

### Falsifications minimales 89C

- compteurs/ancres avant et après lecture identiques ;
- lecture répétée idempotente ;
- lecture d'un monde actif fournit H/φ/P avec provenance temporelle ;
- lecture d'un monde non actif ne matérialise rien ;
- remplacement volontaire des APIs `_synthetic` interdites par des erreurs de test => le chemin opérateur actif reste fonctionnel ;
- une projection read-only éventuelle est distinguable de l'état persisté dans la sortie structurée.

## 6. Lot 89D — répétition générale T0 sur base jetable

Avant l'histoire officielle, exécuter une répétition générale sur **une base neuve et jetable** en empruntant les mêmes chemins supportés que le futur Rodage V2.

La répétition doit :

1. créer une base vide par les migrations réelles ;
2. construire la résidence et les habitantes prévues par les mécanismes supportés ;
3. fixer un temps T0 explicite ;
4. installer les politiques requises ;
5. préparer puis activer la physiologie depuis un manifeste T0 explicite et scellé ;
6. exécuter `mvp-preflight` sans correction cachée ;
7. vérifier que l'observation opérateur de 89C peut lire l'état initial ;
8. exécuter un smoke runtime court et borné si Codex juge cela nécessaire pour prouver le chemin de lancement ;
9. classer la base comme artefact jetable hors de l'histoire officielle après la preuve.

### Manifeste T0

Aucun état physiologique historique ne doit être déduit de l'ancien rodage.

Les valeurs T0 doivent venir d'un manifeste explicite. Si une valeur requiert une décision de produit ou une calibration non déjà approuvée, elle doit être remontée au propriétaire au lieu d'être inventée silencieusement.

Les habitantes peuvent être différenciées seulement par des paramètres réellement supportés et causalement connectés aux mécanismes génériques. Aucun script propre à un personnage n'est autorisé pour obtenir un comportement désiré.

### Critère de sortie 89D

Une base jetable créée de zéro atteint un prévol sain, active H/φ/P proprement, est observable sans mutation et peut franchir le chemin de démarrage prévu sans dépendre de l'ancien rodage.

## 7. Lot 89E — validation et fermeture

Après 89A–D seulement :

- exécuter les tests ciblés du polish réellement modifié ;
- exécuter `python -m compileall -q src tests` ;
- exécuter la suite complète sur le **HEAD exact** candidat ;
- vérifier que le dépôt suivi est propre ;
- vérifier qu'aucun fichier de rodage réel n'a été modifié ;
- mettre à jour `docs/15_ROADMAP_ACTIVE.md`, `docs/99_PASSATION_COURANTE.md`, le changelog et les métadonnées de version nécessaires ;
- enregistrer le HEAD exact, la version, le schéma, la dernière migration, le nombre de tests et l'environnement de validation ;
- retirer seulement les scripts/workflows temporaires créés exclusivement pour WO89 après confirmation qu'ils ne sont plus nécessaires.

Aucun nouveau chantier fonctionnel ne doit être ajouté pour « profiter du passage ».

## 8. Porte de fermeture

WO89 est fermé seulement si :

1. l'identité de release et le numéro de version sont décidés et cohérents dans les sources actives ;
2. un HEAD Git unique et stable est désigné comme base du Rodage V2 ;
3. H/φ/P sont inspectables par un chemin opérateur read-only avec distinction persisté/dérivé ;
4. une répétition T0 complète réussit sur base jetable neuve ;
5. les tests ciblés, compilation et suite complète passent sur le HEAD final exact ;
6. aucun SQLite de rodage réel n'a été migré, repris ou modifié ;
7. la roadmap, la passation et le changelog reflètent le même état ;
8. les preuves de fermeture sont consignées dans ce document.

**La fermeture de WO89 autorise seulement le démarrage du Rodage V2. Elle ne constitue pas elle-même le premier événement de cette histoire.**

## 9. Ordre d'exécution obligatoire

Une seule étape importante à la fois :

1. 89A — photographie et décision de version ;
2. 89B — base Git stable ;
3. 89C — observabilité H/φ/P ;
4. 89D — répétition générale T0 jetable ;
5. 89E — validation complète et documentation de fermeture ;
6. seulement ensuite : création et démarrage du Rodage V2 officiel.

Un échec découvert à une étape bloque la suivante jusqu'à correction et revalidation.

## 10. Première action autorisée

89A est fermé. La prochaine action autorisée est **89B uniquement** : établir une base Git canonique et stable pour le futur Rodage V2. Ne pas toucher encore à une base de rodage et ne pas commencer 89C tant que 89B n'est pas fermé.