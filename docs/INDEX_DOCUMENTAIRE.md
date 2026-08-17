# Index documentaire RIC

**Statut :** actif  
**Date :** 16 août 2026  
**But :** distinguer les documents qui gouvernent le produit courant des documents de R&D, des preuves opérationnelles et des archives historiques.

Cet index ne remplace pas les décisions autoritatives. Il indique où chercher et quel poids donner à chaque famille documentaire.

## 1. Ordre de priorité

En cas de contradiction apparente, ne pas choisir silencieusement le document le plus récent par nom ou numéro. Vérifier d'abord l'état réel du produit et les documents ci-dessous.

1. `docs/01_REGISTRE_DECISIONS.md` — décisions autoritatives et statut des décisions.
2. `docs/GOUVERNANCE_GIT.md` — référence produit, isolation des runtimes et règles Git.
3. `docs/00_DOSSIER_MAITRE_IA.md` — noyau normatif stable et invariants conceptuels.
4. `docs/03_DECISIONS_OUVERTES.md` — arbitrages réellement ouverts; ne constitue pas une décision fermée.
5. `docs/15_ROADMAP_ACTIVE.md` — ordre R&D actif; n'est pas une photographie du code.
6. `docs/99_PASSATION_COURANTE.md` — photographie opérationnelle courante.
7. `CODEX_TASK.md` — mandat technique courant; doit être considéré périssable.

L'état technique réel reste celui du `PRODUCT_HEAD` vérifié sur `product/current`. Un document ne peut pas rendre vrai un état de code qui n'existe pas.

## 2. Normatif actif

Documents à maintenir intentionnellement stables :

- `docs/00_DOSSIER_MAITRE_IA.md`
- `docs/01_REGISTRE_DECISIONS.md`
- `docs/02_MATRICE_EXIGENCES.md`
- `docs/GOUVERNANCE_GIT.md`
- `docs/08_CASTING_MVP.md` lorsque le casting de référence est concerné
- documents de contrat encore utilisés par le produit, sous réserve de leur statut explicite et du registre des décisions

Les numéros de fichier sont historiques et ne déterminent pas à eux seuls l'autorité d'un document.

## 3. R&D active

Documents de recherche/conception qui peuvent guider une future spécification mais ne décrivent pas nécessairement le runtime actuel :

- `docs/71_R_D_SOCIAL_CONSEQUENCE_CORE.md`
- `docs/72_R_D_SCC1_INTERPRETATION_SOCIALE.md`
- `docs/73_R_D_SCC1B_PROVIDER_ET_CALIBRATION.md`
- `docs/74_R_D_SCC1C_ADMISSION_COGNITIVE.md`
- `docs/75_R_D_CONVERSATION_STATE.md`
- `docs/79_R_D_CYCLE_DIURNE_CIRCADIEN_SOMMEIL.md`
- autres dossiers R&D explicitement identifiés comme tels

Règle : résultats empiriques, conclusions raisonnables mais incertaines, hypothèses de modélisation et choix d'ingénierie doivent rester distingués.

## 4. Opérationnel courant

Documents qui vieillissent rapidement et doivent être relus contre `product/current` avant usage :

- `CODEX_TASK.md`
- `docs/03_DECISIONS_OUVERTES.md`
- `docs/15_ROADMAP_ACTIVE.md`
- `docs/35_ROUTINE_AUDIT_SILENCIEUX.md`
- `docs/77_HUGIN_MUNIN_OBSERVATION_V0.md`
- `docs/78_HUGIN_MUNIN_RODAGE_CONSOLE_V01.md`
- `docs/99_PASSATION_COURANTE.md`

Une ancienne passation, un ancien WO ou un protocole de rodage terminé ne redevient jamais autoritatif parce qu'il contient plus de détails.

## 5. Historique conservé en place

Plusieurs documents antérieurs restent actuellement à la racine de `docs/` pour préserver les références et éviter un déplacement massif pendant un rodage actif. Ils doivent être considérés comme historiques lorsqu'ils décrivent un lot, une alpha, un correctif ou un work order déjà fermé.

Familles concernées notamment :

- anciens plans de lots `04_*` à `17_*` lorsqu'ils décrivent des lots déjà fermés;
- documents alpha/correctifs/rodages `58_*` à `70_*`;
- work orders circadiens et rodage V2 `80_*` à `91_*` lorsqu'ils sont fermés;
- anciens bancs de qualification dont la fonction est désormais probatoire/historique.

Ils ne sont pas supprimés : ils conservent la provenance, les décisions de l'époque et les contrats de régression. Leur déplacement physique éventuel sous `docs/history/` doit être fait séparément, avec vérification des références.

## 6. Archive explicite

`docs/history/` contient déjà des documents historiques non autoritatifs. Voir `docs/history/README.md`.

`passation_2026-08-05/` est une capsule historique de passation antérieure et n'est pas une source de vérité courante. Voir son `README.md`.

## 7. Sources de conception

`sources/` contient les matériaux source initiaux de conception. Ils sont utiles pour la provenance et la recherche, mais ne remplacent ni le registre de décisions ni l'état du code. Voir `sources/README.md`.

## 8. Collisions de numérotation

Le dépôt contient volontairement des préfixes numériques dupliqués (`05_*`, `75_*`, `76_*`). Ne pas renommer massivement ces fichiers uniquement pour rendre la séquence esthétique : cela casserait des références et produirait du churn sans gain fonctionnel.

À partir de maintenant, l'identité d'un document repose sur son chemin complet et son rôle explicite, pas sur son numéro seul.

## 9. Politique d'archivage

Avant de déplacer ou supprimer un document :

1. déterminer s'il protège une décision, un invariant, une preuve de qualification ou une référence de test;
2. chercher les références entrantes dans le dépôt;
3. préférer un déplacement traçable à une suppression lorsque la valeur historique subsiste;
4. mettre à jour les index/liens affectés;
5. ne jamais profiter d'un archivage documentaire pour modifier le runtime ou réinterpréter rétroactivement un résultat expérimental.

## 10. Maintenance de cet index

Cet index ne doit pas contenir de SHA produit, compteur de tests, session de rodage ou autre valeur appelée à changer à chaque intégration. Ces informations appartiennent aux documents opérationnels périssables.

Lorsqu'un chantier change de statut, mettre à jour sa classification ici seulement si son rôle documentaire change. L'état fonctionnel détaillé reste dans la passation courante, la roadmap et le registre de décisions.