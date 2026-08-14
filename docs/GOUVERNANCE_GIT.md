# Gouvernance Git — référence produit RIC

**Statut :** actif
**Adopté :** 14 août 2026

Cette règle évite qu’un WO, un audit ou une validation soit exécuté silencieusement sur une base différente de celle du produit réellement reconnu.

## 1. Référence autoritative

La branche distante `product/current` est l’unique référence autoritative du **HEAD produit courant**.

Le SHA exact de `origin/product/current` au début d’un travail est la base de référence de ce travail.

`main`, une branche de WO, une branche de rodage, un checkout partagé, un worktree local ou « le dernier commit disponible localement » ne remplacent jamais implicitement `product/current`.

## 2. Préflight obligatoire avant tout WO

Avant toute modification, Codex doit :

1. effectuer un fetch du remote pertinent;
2. résoudre `origin/product/current` vers un SHA exact;
3. annoncer ce SHA comme `PRODUCT_HEAD`;
4. vérifier que le commit existe localement;
5. créer le worktree/branche de travail depuis **ce SHA exact**;
6. vérifier que le worktree créé a bien ce SHA comme base.

Si `origin/product/current` ne peut pas être résolu ou récupéré, le travail s’arrête avec `STOP — PRODUCT_HEAD UNAVAILABLE`.

**Aucun fallback silencieux vers un autre HEAD n’est permis.**

## 3. Isolation du runtime

Le HEAD d’un runtime actif est un **snapshot de runtime**, pas une base de développement.

Un runtime ou rodage peut volontairement rester sur un ancien SHA pendant qu’un produit plus récent existe. Cette divergence doit être déclarée explicitement sous la forme :

- `PRODUCT_HEAD = <sha>`
- `RUNTIME_HEAD = <sha>`

Un checkout/runtime actif ne doit pas être rebasé, reset, changé de branche ou modifié pour « se synchroniser » pendant un rodage sans autorisation explicite du propriétaire.

## 4. Cycle d’un WO

Le cycle normal est :

`product/current` → worktree isolé → implémentation → tests → intégration → validation → déplacement de `product/current`.

Un WO testé sur sa branche n’est pas encore fermé au sens produit.

Statuts :

- `READY FOR INTEGRATION` : implémenté et validé sur sa base de travail;
- `REVALIDATION REQUIRED` : `product/current` a avancé depuis la base du WO;
- `CLOSED` : le changement est intégré et validé sur le produit courant, puis `product/current` pointe sur le résultat reconnu;
- `CLOSED WITH FOLLOW-UP` : fonctionnellement validé, mais une exigence d’intégration ou de validation reste explicitement ouverte;
- `STOP` : précondition essentielle non satisfaite.

## 5. Avancement de `product/current`

`product/current` ne bouge qu’après une intégration reconnue comme valide.

Le déplacement doit normalement être **forward-only**. Toute régression volontaire de la référence exige une décision explicite du propriétaire et une justification d’incident/récupération.

Après chaque déplacement de `product/current`, le nouveau SHA doit être annoncé comme nouvelle référence commune avant d’ouvrir un autre WO.

## 6. Travaux concurrents

Plusieurs WO peuvent partir du même `PRODUCT_HEAD`, mais aucun ne peut présumer que sa base est encore courante au moment de l’intégration.

Si `product/current` a avancé pendant le travail :

1. intégrer/reporter le WO sur le nouveau `PRODUCT_HEAD`;
2. réexécuter les validations affectées;
3. inspecter le diff final;
4. seulement ensuite fermer le WO.

## 7. Gouvernance des acteurs

- **ChatGPT** : raisonne et documente en utilisant `product/current` comme état produit de référence lorsqu’une réponse dépend du code réel.
- **Grok** : reçoit le SHA `PRODUCT_HEAD` dans tout mandat de contre-audit portant sur l’état du produit.
- **Codex** : est responsable du préflight Git, des worktrees, de l’intégration, des migrations, des tests et de la preuve du SHA réellement utilisé.
- **Utilisateur** : autorité finale pour accepter une intégration, une exception ou un déplacement non standard de la référence produit.

Aucun acteur ne doit présenter une branche locale ou historique comme « le produit courant » sans vérifier `product/current`.

## 8. Rapport minimal obligatoire

Tout rapport technique de WO doit inclure au minimum :

- `PRODUCT_HEAD` au démarrage;
- branche/worktree utilisé;
- HEAD de travail final;
- état de `product/current` au moment de l’intégration;
- tests exécutés et résultats;
- état du runtime actif s’il est pertinent;
- verdict final.

## 9. Principe

**Verify twice. Commit once.**

La créativité reste flexible pendant l’exploration; dès qu’un changement devient du code ou du canon technique, sa provenance Git doit être exacte, vérifiable et commune à tous.
