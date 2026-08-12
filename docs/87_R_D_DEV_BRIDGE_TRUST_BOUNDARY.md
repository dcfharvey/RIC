# R&D — RIC Dev Bridge trust boundary

Statut : CANDIDAT / NON ACTIVÉ

Ce document ne change aucune permission runtime. `REPO_WRITE`, `RUNTIME_CONTROL`, `REAL_WORLD_WRITE` et `DESTRUCTIVE` restent interdits tant qu'un cutover de sécurité distinct n'a pas été revu et autorisé.

## 1. Résultats empiriques

### Documentation GitHub

GitHub Actions OIDC expose, pour un job exécuté dans un workflow réutilisable, des claims distincts pour le workflow appelant et le workflow appelé. Les claims pertinents incluent notamment `workflow_ref`, `workflow_sha`, `job_workflow_ref`, `job_workflow_sha`, `repository`, `repository_id`, `actor_id`, `ref`, `sha`, `aud`, `iss`, `iat`, `nbf` et `exp`.

GitHub documente explicitement l'usage de `job_workflow_ref` afin de définir une condition de confiance sur un workflow réutilisable précis, y compris un ref/SHA précis.

Sources primaires :
- GitHub Docs — Using OpenID Connect with reusable workflows.
- GitHub Docs — OpenID Connect reference.

### POC RIC du 2026-08-12

Workflow appelé :
`dcfharvey/RIC/.github/workflows/oidc-trusted-poc.yml@bdf0b4c3d4ed62c244ec02a69ffb4b11bcfdfdbb`

Workflow appelant :
`dcfharvey/RIC/.github/workflows/oidc-caller-poc.yml@refs/heads/chatgpt/oidc-caller-poc`

Run : `31648705411`

Claims non sensibles observés :
- `iss = https://token.actions.githubusercontent.com`
- `aud = ric-dev-bridge`
- `repository = dcfharvey/RIC`
- `repository_id = 1328282903`
- `repository_owner_id = 314814044`
- `actor_id = 314814044`
- `event_name = push`
- `ref = refs/heads/chatgpt/oidc-caller-poc`
- `sha = eeea673b6c4fb2621a6624774c8f009f2ac9507f`
- `workflow_sha = eeea673b6c4fb2621a6624774c8f009f2ac9507f`
- `job_workflow_ref = dcfharvey/RIC/.github/workflows/oidc-trusted-poc.yml@bdf0b4c3d4ed62c244ec02a69ffb4b11bcfdfdbb`
- `job_workflow_sha = bdf0b4c3d4ed62c244ec02a69ffb4b11bcfdfdbb`
- `runner_environment = github-hosted`

Le POC démontre donc dans le dépôt RIC que le workflow appelant mutable et le workflow réutilisable épinglé sont distinguables cryptographiquement dans le jeton OIDC émis par GitHub.

Le jeton brut n'a pas été journalisé ni persisté par le POC.

## 2. Conclusion raisonnable mais encore non activée

Une frontière de confiance plus forte que le bearer GitHub Actions actuel est réalisable sans donner au request writer un secret longue durée.

Le gateway local pourrait accepter une requête seulement si un jeton OIDC GitHub valide prouve simultanément :
- l'issuer GitHub attendu ;
- une audience dédiée RIC ;
- le dépôt et l'identité de dépôt attendus ;
- le workflow réutilisable trusted attendu ;
- le SHA exact de ce workflow trusted ;
- une fenêtre temporelle valide ;
- un caller/ref autorisé ;
- un jeton non rejoué.

Cette conclusion est supportée par la documentation GitHub et le POC RIC, mais l'implémentation locale du vérificateur reste à concevoir/revoir/tester.

## 3. Hypothèse d'ingénierie à falsifier

Hypothèse : un transport OIDC avec workflow trusted épinglé peut remplacer le bearer longue durée pour les endpoints de développement, tout en permettant à Sol d'émettre des requêtes depuis un caller mutable sans pouvoir modifier l'autorité qui lui accorde les permissions locales.

Falsifications requises avant activation :
- signature JWT invalide refusée ;
- mauvais issuer/audience refusé ;
- mauvais repository/repository_id refusé ;
- mauvais `job_workflow_ref` refusé ;
- mauvais `job_workflow_sha` refusé ;
- token expiré/not-before refusé ;
- replay du même `jti` refusé ;
- caller/ref non autorisé refusé ;
- modification du caller sans modification du trusted workflow ne permet pas d'élargir les routes/permissions ;
- workflow trusted à un autre SHA refusé même s'il porte le même nom ;
- aucune régression du bearer bootstrap tant qu'il reste nécessaire à Phase A.

## 4. Choix de design candidat

Candidat V1 :

`Sol -> caller GitHub mutable -> reusable workflow trusted @ immutable SHA -> GitHub OIDC -> gateway local -> permission gate -> operation`

Le caller transmet seulement une requête structurée. Le workflow trusted valide lui-même le schéma et l'allowlist avant de demander un jeton OIDC et d'appeler le gateway.

Le gateway valide cryptographiquement le jeton et les claims avant de considérer la permission demandée.

Le bearer actuel reste un bootstrap Phase A READ/TEST_EXEC seulement. Il ne doit pas devenir l'autorité de `REPO_WRITE`.

## 5. Choix non décidés

À décider séparément avant code actif :
- bibliothèque de validation JWT/OIDC vs implémentation dédiée ;
- politique de cache JWKS et comportement hors réseau ;
- audience définitive ;
- branche/ref caller définitive ;
- politique de replay `jti` ;
- stockage de l'URL du tunnel ;
- remplacement du Quick Tunnel éphémère par un endpoint stable éventuel ;
- séquence de retrait du bearer GitHub Actions.

Aucun de ces choix n'est une loi scientifique ou une propriété actuelle de RIC.

## 6. Invariants de sécurité

- LLM propose, moteur/gateway valide.
- Un caller mutable ne définit jamais sa propre permission locale.
- Les permissions futures restent fail-closed.
- Aucun secret longue durée ne doit être nécessaire au caller final si OIDC est retenu.
- Le workflow trusted doit être identifiable par contenu/SHA, pas seulement par nom ou branche.
- Le canal de développement ne doit jamais devenir un canal implicite d'écriture du monde réel.
- `data/vivarium-rodage.sqlite` reste hors écriture du bridge tant qu'un lot distinct ne l'autorise pas explicitement.
