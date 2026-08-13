# Codex task — WO91

Implémenter et qualifier `docs/91_WORK_ORDER_DEMARRAGE_REEL_RODAGE_V2.md` sur `chatgpt/wo91-rodage-v2-live-start`.

Base fermée : `ce3bec5d7d9825784f397c8db9c77239f3886b13` (`0.2.0a2`, schéma 56, WO90 fermé).

## Pourquoi ce correctif existe

La revue pré-lancement a trouvé trois trous que WO90 ne falsifiait pas :

1. `character_location_plan` stocke le retour de Sophie à 16 h mais aucun raccord runtime vérifié ne l'exécute à l'échéance;
2. le banc utilisait `photography` pour signifier « travaille », ce qui invente un sous-geste non décidé;
3. le banc physiologique assignait le profil humain à tout le casting. Le catalogue réel ne contient que les candidats humain et félin; Luna est une louve anthropomorphe et Chuu une slime.

Ne démarre aucun SQLite officiel pendant WO91.

## Contrats à satisfaire

Lire intégralement WO91 avant de coder. En particulier :

- rendre les plans de lieu dus causalement exécutables sur une frontière de temps canonique, sans dépendre du LLM et sans cas spécial Sophie;
- représenter génériquement « être en train de travailler » sans inventer la tâche précise;
- garder Sophie/Erika sur le candidat humain et Patoune sur le candidat félin;
- pour Luna/Chuu, utiliser une baseline fictionnelle explicitement provenancée `fictional_canon`, éventuellement quantitative-equivalente au candidat humain comme hypothèse de transfert temporaire, mais jamais étiquetée « physiologie humaine » ni codée par identité;
- initialiser le manifeste officiel sans passé reconstruit : H/P déterminés par la politique T0 neutre/normal-haut, φ par règle T0 compatible avec l'état lumineux, résidus zéro, bande dérivée/validée; ne pas recopier une fixture comme convention cachée;
- fournir un point d'entrée opérateur supporté, one-shot, qui cible `data/vivarium-rodage-v2.sqlite`, refuse l'écrasement et ne touche jamais à `data/vivarium-rodage.sqlite` ni ses sidecars;
- ne pas affaiblir le bridge : il doit continuer à refuser `RUNTIME_CONTROL` et `REAL_WORLD_WRITE`;
- le point d'entrée doit capturer une seule fois le T0 réel EDT et refuser avant toute création si T0 >= 16 h EDT pour le scénario courant;
- avant la première session runtime : préflight read-only, Hugin H/φ/P, provider attendu disponible;
- provider attendu : Qwen3-14B Q4_K_M, FR/FR, interpretation-only; aucune substitution silencieuse.

## Faits T0

- Sophie : au travail comme photographe journalistique; revient au foyer à 16 h; ne pas inventer employeur/média/affectation/sous-tâche.
- Erika : salon, gaming; jeu non spécifié.
- Patoune : dort dans le salon, blotti contre Erika; précision objet/contact seulement si support générique réel.
- Chuu : bain/hygiène, détente, réhydratation, s'apprête à sortir; hydratation via ressource générique, aucun confort persistant.
- Luna : première arrivée en taxi, sac d'effets personnels; contenu indéterminé.

## Exécution

Tu as autorité sur l'architecture réelle, migrations, tests, version et ordre d'implantation. Ne suis pas littéralement une architecture suggérée si le dépôt impose mieux, mais conserve les contrats.

Traite un problème majeur à la fois : reproduction/diagnostic -> correction -> tests ciblés -> suite élargie si utile -> suivant.

Avant fermeture : répétition complète sur SQLite jetable, falsifications WO91, compileall, suite complète, dépôt suivi propre, docs synchronisées. Consigner HEAD fonctionnel/final, version, schéma, migration, tests, environnement et preuve qu'aucun SQLite officiel V2 n'a été créé.

Reviens au propriétaire une seule fois à fermeture complète, ou uniquement si une vraie décision produit non résoluble bloque l'implantation. Après fermeture, ARRÊTE : ne lance pas encore le point d'entrée officiel.