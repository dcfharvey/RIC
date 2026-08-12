# R&D — Frontière de confiance du RIC Dev Bridge

**État :** candidat final, non activé localement tant que le cutover du gateway n'est pas validé sur le poste Windows.  
**Portée :** outillage de développement seulement. Aucun effet sur la réalité canonique, la résidence, le cutover circadien ou SCC-1B.

## 1. Objectif

Permettre à Sol d'exécuter une boucle de développement bornée :

`inspecter -> modifier -> tester -> observer -> corriger -> committer/pousser une branche de travail`

sans transformer le bridge en agent Windows général ni en autorité runtime RIC.

## 2. Résultats empiriques déjà observés

- Le chemin GitHub Actions -> Quick Tunnel Cloudflare -> gateway local -> LM Studio -> `qwen3-14b` a été validé avec `PONG`.
- Sol a utilisé le bridge Phase A depuis ChatGPT pour lire `/capabilities`, lire Git, lancer des pytest ciblés et inspecter le monde RIC sans intervention humaine.
- Le RPC bootstrap a été durci pour ancrer chaque requête au SHA Git déclencheur et publier un résultat immuable par `request_id`.
- Un POC GitHub Actions OIDC exécuté dans le vrai dépôt RIC a confirmé la présence distincte de `workflow_ref`/`workflow_sha` pour le caller et de `job_workflow_ref`/`job_workflow_sha` pour le workflow réutilisable appelé.
- Le caller final `bridge/sol-rpc-final` a exécuté le workflow trusted épinglé et a atteint le gateway local existant. Le HTTP 401 observé avant installation du control plane final est attendu : l'ancien gateway est encore bearer-only.

## 3. Choix d'ingénierie

### 3.1 Deux couches locales

Après activation :

`Quick Tunnel -> control plane 127.0.0.1:8787 -> gateway Phase A 127.0.0.1:8788 -> LM Studio 127.0.0.1:1234`

Le control plane est installé dans une copie épinglée hors du workspace mutable RIC. Il n'importe aucun module runtime RIC.

### 3.2 Auth publique

Les routes de développement utilisent un jeton GitHub Actions OIDC court et signé.

La politique vérifie notamment :

- issuer GitHub Actions ;
- signature RS256 via JWKS GitHub ;
- dépôt, IDs dépôt/propriétaire et actor ;
- `job_workflow_ref` et `job_workflow_sha` exacts du workflow trusted ;
- caller `ref`, `workflow_ref` et événement exacts ;
- dépôt privé et runner GitHub-hosted ;
- fenêtre temporelle ;
- `jti` anti-replay.

L'audience du jeton est liée à la requête exacte : méthode, route, corps et UUID `request_id`.

### 3.3 Bearer legacy

Le bearer historique reste interne aux deux couches locales et peut conserver la compatibilité des routes LM Studio (`/v1/models`, chat/responses). Il n'autorise pas `/dev/write` ou `/dev/repo`.

### 3.4 Écritures de fichiers

`/dev/write` autorise uniquement :

- `write_file` ;
- `replace_text` ;
- `create_file`.

Contraintes : UTF-8, taille bornée, racines approuvées, fichiers sensibles refusés, traversal/reparse points refusés, bridge/security files protégés, hash SHA-256 attendu pour les fichiers existants, remplacement atomique et revalidation immédiate avant commit de l'écriture. Cette protection est un CAS optimiste, pas une transaction OS inter-processus parfaite.

### 3.5 Git d'écriture

`/dev/repo` autorise uniquement :

- création de branche `chatgpt/...` ;
- commit de fichiers explicitement approuvés ;
- push non-force vers la branche `chatgpt/...` courante.

Aucun merge, reset, clean, suppression de branche, force-push ou écriture directe sur `main` n'est exposé.

## 4. Permissions

- `READ` : autorisé ;
- `TEST_EXEC` : autorisé, pytest contrôlé, pas un sandbox OS ;
- `REPO_WRITE` : candidat `ALLOW_OIDC_CAS_GIT` après activation locale validée ;
- `RUNTIME_CONTROL` : DENY ;
- `REAL_WORLD_WRITE` : DENY ;
- `DESTRUCTIVE` : DENY.

## 5. Limite de sécurité assumée

`TEST_EXEC` n'est pas un sandbox OS. Une fois que Sol peut modifier du code Python puis lancer pytest, ce code s'exécute sous le compte Windows de l'utilisateur. Les frontières API réduisent fortement les erreurs accidentelles et les écritures directes non prévues, mais elles ne constituent pas une VM, un conteneur ou un compte Windows isolé.

Cette limite doit rester explicitement visible dans `/capabilities` et dans toute extension future.

## 6. Références de confiance candidates

Workflow trusted final :

`dcfharvey/RIC/.github/workflows/ric-dev-trusted.yml@bcf38918c0ed746bf3d9440b91b2e325b3860530`

Caller final :

`refs/heads/bridge/sol-rpc-final`

Le workflow trusted ne doit pas être modifié silencieusement : tout changement produit un nouveau SHA et exige une nouvelle revue de confiance ainsi qu'une nouvelle installation/pin local.

## 7. Gate d'activation locale

Avant de déclarer le bridge final actif :

1. matérialiser le candidat propre dans le checkout Windows sans perdre les untracked locaux ;
2. exécuter la suite complète sur le poste réel ;
3. installer le control plane hors workspace ;
4. déplacer le gateway Phase A à 8788 et mettre le control plane à 8787 sans redémarrer inutilement le tunnel ;
5. confirmer OIDC `/health` et `/capabilities` ;
6. confirmer que le bearer legacy ne peut pas utiliser les routes d'écriture ;
7. falsifier une écriture hors scope/protected ;
8. effectuer une écriture sûre et réversible ;
9. créer/committer/pousser une branche `chatgpt/...` de test ;
10. confirmer qu'aucune donnée canonique/runtime n'a été modifiée.

Aucun merge vers `main` n'est implicite dans cette activation.
