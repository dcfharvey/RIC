# Work order 89 — préparation pré-rodage V2

**Statut :** OUVERT — **89A FERMÉ**; **89B PRÊT, alignement local requis avant fermeture**.

**Base documentaire de départ :** `bbdac5c737c6fa0b28f23657b826b008b5b12fd2` (`docs: close WO88 formally`).

**Base fonctionnelle héritée de WO88 :** `fe1d24a0cd5f32463c594d2de6bf2e3ba7ad0667`, validée par `python -m compileall -q src tests` puis **1029 tests réussis en 392,09 s, 0 échec** sous Windows Server 2025 / Python 3.12.10.

**État de référence au départ :** package `0.1.0a15`; schéma de code 55; dernière migration `0055_sleep_completion_authorization.sql`; WO88 fermé; aucun cutover de résidence persistante autorisé.

**Dépendance fermée :** `docs/88_WORK_ORDER_RUNTIME_CIRCADIEN_ACTIF_V1.md`.

## 0A. Verdict 89A — photographie de release

89A est fermé sur la photographie suivante :

- branche distante de travail : `chatgpt/wo89-pre-rodage-v2` ;
- HEAD documentaire de 89A avant consignation : `a5ef14d6b7d4a3c61d6d4305ee338319582d211c` ;
- version déclarée dans `pyproject.toml` et `src/vivarium/__init__.py` : `0.1.0a15` ;
- schéma de code : **55** ; dernière migration : `0055_sleep_completion_authorization.sql` ;
- baseline fonctionnelle héritée : HEAD `fe1d24a0cd5f32463c594d2de6bf2e3ba7ad0667`, compilation verte et **1029 tests réussis** ;
- `README.md` contient encore une photographie présentée comme courante au schéma 39 / 767 tests ;
- `docs/15_ROADMAP_ACTIVE.md` et `docs/99_PASSATION_COURANTE.md` contiennent encore des photographies historiques au schéma 48 / 929 tests sous leurs blocs prioritaires WO88 ;
- `CHANGELOG.md` conserve l'historique `0.1.0a15`, mais ne porte pas encore le futur jalon Rodage V2.

### Décision de version 89A

**Version produit retenue pour la base du Rodage V2 : `0.2.0a1`.**

Le bump n'est pas appliqué pendant 89A. Les sources de version seront synchronisées après stabilisation du chemin de rodage et avant fermeture 89E.

### Critère de sortie 89A

**SATISFAIT.** Version cible, HEAD, schéma, migration, baseline de tests et divergences documentaires sont consignés. Aucun SQLite de rodage n'a été touché.

## 0B. État 89B — graphe Git et base candidate

Le graphe distant a été vérifié avant toute intégration :

- `main` = `a8a8f31c49f1bf643b8b3c17f2d2415b97c05e16` ;
- `chatgpt/wo88-final-validation` = `bbdac5c737c6fa0b28f23657b826b008b5b12fd2` ;
- `main` est l'ancêtre direct de la fermeture WO88 : comparaison GitHub `ahead_by=55`, `behind_by=0`, merge-base = `main` ;
- la branche WO89 descend directement de WO88 ; avant cette consignation, son HEAD était `3d63b08e9ee99d23a52edf88d04f863caf02cb2e`, à trois commits documentaires de la fermeture WO88 ;
- aucune divergence ou merge conflict n'est à résoudre entre `main`, WO88 et WO89 ;
- `main` n'a pas été avancé : aucune branche de référence partagée n'est modifiée silencieusement pendant 89B ;
- une tentative de créer une branche de candidat séparée via le connecteur GitHub a été refusée par la couche de sécurité OpenAI. Aucun contournement n'a été tenté et aucune référence existante n'a été déplacée à cause de cet échec.

### Stratégie Git retenue pour WO89

`chatgpt/wo89-pre-rodage-v2` reste la branche de préparation unique jusqu'à fermeture de WO89. Le dernier HEAD de cette branche est la seule lignée candidate autorisée pour 89C–89E.

Le Rodage V2 officiel ne démarrera pas sur une branche de réparation historique. À 89E, Codex déterminera à partir du graphe réel si la lignée finale doit être fast-forwardée vers `main` ou matérialisée sous une branche de release/rodage dédiée. Cette opération sera explicitée avant toute modification d'une référence partagée.

Le dernier checkout local confirmé est encore `chatgpt/wo88-final-validation` au HEAD `bbdac5c737c6fa0b28f23657b826b008b5b12fd2`, fichiers suivis propres. **89B ne sera marqué FERMÉ qu'après alignement local propre vers `chatgpt/wo89-pre-rodage-v2`.**

### Critère de sortie 89B

**PARTIELLEMENT SATISFAIT.** Graphe distant, lignée candidate et stratégie d'intégration sont non ambigus. Il reste une seule précondition opérationnelle : aligner le checkout local sur la branche WO89 sans supprimer les artefacts non suivis. Tant que cette vérification n'est pas faite, 89C ne démarre pas.

## 1. Intention

Préparer une base de rodage fraîche, identifiable, observable et reproductible **sans commencer encore l'histoire persistante du Rodage V2**.

Ce work order est volontairement court. Il ne doit pas devenir une nouvelle phase de développement fonctionnel. Son rôle est de supprimer les ambiguïtés de version, de branche, d'observabilité et de bootstrap qui rendraient un nouveau rodage difficile à diagnostiquer ou à reproduire.

À sa fermeture, on doit pouvoir répondre sans ambiguïté à cinq questions : quel commit exact constitue la base du prochain rodage; quel numéro de version produit lui est associé; quel schéma et quelles migrations sont attendus; comment observer H/φ/P sans modifier la simulation; comment construire et valider un T0 neuf avant de laisser l'histoire commencer.

## 2. Hors périmètre

WO89 n'autorise pas la migration/reprise de l'ancien `data/vivarium-rodage.sqlite`, la création de l'histoire persistante officielle avant fermeture, la reconstruction d'un passé physiologique, l'ajout opportuniste de nouveaux modèles cognitifs/sociaux/affectifs/comportementaux/physiologiques, une refonte UI, un changement du contrat `LLM propose, moteur valide`, une écriture cognitive directe dans le canon, ni le retour de `repos`/`energie` comme causes actives sur un monde `physiology=active`.

Si une anomalie fonctionnelle réelle apparaît pendant WO89, elle devient un problème unique traité séquentiellement : reproduction, diagnostic, correction ciblée, tests ciblés, suite complète, puis reprise du lot.

## 3. Gouvernance

Ce lot est principalement un lot d'ingénierie/release et d'observabilité. Il n'introduit aucun nouveau modèle vivant nécessitant une nouvelle revue scientifique.

- ChatGPT fixe le contrat fonctionnel, les invariants et la documentation de lot.
- Codex choisit l'implantation réelle, l'ordre technique, les migrations éventuelles, les tests et la stratégie d'intégration Git à partir du dépôt réel.
- Le propriétaire conserve la décision finale sur le numéro de version produit et sur le T0 canonique du Rodage V2.

## 4. Lot 89A — identité de release et photographie de référence — FERMÉ

Décision produit : `0.2.0a1`. Photographie HEAD/schéma/migration/tests et divergences documentaires consignées. Aucun bump appliqué pendant 89A.

## 5. Lot 89B — base Git canonique du prochain rodage — ALIGNEMENT LOCAL REQUIS

Le Rodage V2 ne doit pas démarrer sur une branche de réparation ou un worktree ambigu.

Exigences : un seul HEAD candidat vérifiable; aucun changement suivi non committé; aucune dépendance à un worktree temporaire; historique WO88 traçable; aucune référence partagée modifiée sans stratégie explicite; aucun SQLite réel touché.

Le graphe distant satisfait ces exigences. La fermeture 89B attend seulement la confirmation locale de `chatgpt/wo89-pre-rodage-v2` propre.

## 6. Lot 89C — observabilité opérateur de H/φ/P

Le système physiologique actif ne doit pas être une boîte noire pendant le rodage.

Pour chaque personnage explicitement demandé, le chemin opérateur read-only doit exposer au minimum : statut physiologique du monde; H; φ; P; ancre persistée; temps canonique de projection éventuelle; stabilité/sommeil si ce sous-état est déjà possédé par le système.

Si une projection owner-backed est calculée sans matérialisation, la sortie doit distinguer explicitement **état persisté** et **projection read-only dérivée**.

Invariants : aucune écriture ni événement dû à la lecture; aucune progression d'ancre; aucune API `_synthetic` dans le chemin opérateur actif; mondes `inactive/prepared` non matérialisés; `repos/energie` jamais étiquetés comme physiologie active; aucune donnée subjective promue en fait canonique.

Falsifications minimales : compteurs/ancres avant-après identiques; lecture répétée idempotente; monde actif fournit H/φ/P avec provenance temporelle; monde non actif ne matérialise rien; monkeypatch des APIs `_synthetic` interdites sans casser l'observation active; projection dérivée distinguable du persisté.

## 7. Lot 89D — répétition générale T0 sur base jetable

Sur une base neuve et jetable : appliquer les migrations réelles; construire résidence et habitantes par les chemins supportés; fixer un T0 explicite; installer les politiques; préparer/activer la physiologie depuis un manifeste T0 scellé; exécuter `mvp-preflight`; vérifier l'observation 89C; effectuer au besoin un smoke runtime court; classer ensuite la base comme artefact jetable.

Aucun état physiologique historique ne vient de l'ancien rodage. Toute valeur T0 nécessitant encore une décision produit est remontée au propriétaire plutôt qu'inventée.

## 8. Lot 89E — validation et fermeture

Après 89A–D : tests ciblés; `python -m compileall -q src tests`; suite complète sur le HEAD exact; dépôt suivi propre; aucun SQLite réel modifié; harmonisation roadmap/passation/changelog/README/métadonnées de version; enregistrement du HEAD, version, schéma, migration, compte de tests et environnement; retrait uniquement des artefacts WO89 réellement jetables.

## 9. Porte de fermeture

WO89 est fermé seulement si : identité/version cohérentes; HEAD Git final unique; H/φ/P observables read-only avec persisté/dérivé distincts; répétition T0 neuve réussie; tests/compilation/suite complète verts; aucun SQLite réel touché; documentation active harmonisée; preuves consignées.

**La fermeture de WO89 autorise seulement le démarrage du Rodage V2. Elle n'est pas le premier événement de cette histoire.**

## 10. Ordre d'exécution obligatoire

1. 89A — FERMÉ ;
2. 89B — graphe distant prêt, alignement local requis ;
3. 89C — après fermeture 89B seulement ;
4. 89D — après fermeture 89C seulement ;
5. 89E — validation complète et documentation ;
6. seulement ensuite : Rodage V2 officiel.
