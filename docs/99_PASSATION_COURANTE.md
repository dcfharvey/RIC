# Passation courante — RIC

**Mise à jour :** 8 août 2026  
**But :** point d'entrée opérationnel obligatoire pour toute nouvelle instance de Codex.  
**Projet :** RIC — Reality · Interaction · Cognition (anciennement Vivarium social).

> Commencer ici. Ne pas reconstruire l'histoire du projet à partir des anciens lots.
> Vérifier le dépôt réel avant toute écriture.

---

## 1. Philosophie et gouvernance

Deux maximes structurent le travail :

> **Flexible creativity. Rigorous execution.**
>
> **Verify twice. Commit once.**

La première concerne la conception : exploration ouverte tant qu'aucune décision n'est engagée, puis spécification et exécution rigoureuses dès qu'une idée devient architecture, code ou canon.

La seconde concerne le développement : avant une modification importante, vérifier hypothèses, dépendances, invariants, conséquences, migrations et tests; ne committer qu'après preuve suffisante.

Répartition des responsabilités :

- **ChatGPT** : recherche scientifique/technique, conception fonctionnelle, cohérence conceptuelle, documentation R&D et préparation des work orders;
- **Grok** : contre-audit scientifique adversarial indépendant;
- **Codex** : autorité sur l'architecture réelle, le code, les migrations, les propriétaires persistants, les invariants techniques, les tests et l'ordre d'implantation;
- **propriétaire** : autorité finale sur les choix de produit et de design.

Codex ne doit pas suivre aveuglément une proposition R&D si le dépôt réel impose une autre implantation. Il doit signaler la divergence et l'expliquer. Inversement, une décision d'ingénierie ne doit jamais être présentée comme une loi scientifique.

Pour tout modèle comportemental, cognitif, social ou physiologique, conserver explicitement la séparation suivante :

1. résultats empiriques;
2. conclusions raisonnables mais incertaines;
3. hypothèses de modélisation;
4. choix de design/ingénierie.

---

## 2. Architecture conceptuelle RIC

Les noms suivants sont **conceptuels**. Ils ne constituent pas une instruction de renommer des packages, classes ou services existants.

- **Reality Engine** : ce qui est objectivement vrai, possible et causal dans la simulation;
- **Interaction Engine** : ce qui rend agents et réalité mutuellement accessibles et structure leurs interactions;
- **Cognitive Engine** : ce que chaque agent perçoit, interprète, mémorise, priorise et décide subjectivement.

Le mapping de ces concepts sur le code réel doit être établi à partir du dépôt, pas supposé depuis les noms.

### Invariants fondamentaux

```text
réalité/canon ≠ perception ≠ croyance
parole ≠ fait
relation ≠ permission ≠ consentement
LLM propose, moteur valide
aucun composant cognitif n'écrit directement la réalité canonique
provenance d'audit ≠ source subjectivement mémorisée
un seul propriétaire persistant par état
pas d'omniscience implicite des agents
mécanisme générique > script propre à un personnage
```

Ces invariants priment sur les commodités d'implémentation.

---

## 3. Hiérarchie de vérité pour une reprise

Lorsqu'une documentation ancienne contredit le dépôt courant, utiliser cet ordre :

1. **HEAD réel + migrations + tests exécutés**;
2. **documentation normative active** (`docs/00_DOSSIER_MAITRE_IA.md`, registre de décisions et changements approuvés postérieurs);
3. **cette passation courante** pour l'état opérationnel et les priorités immédiates;
4. **CHANGELOG et documents de version récents**;
5. documents de lot historiques et `sources/` pour provenance seulement.

Ne jamais réconcilier silencieusement deux exigences incompatibles.

### Documents à lire avec leur portée documentaire

- `docs/00_DOSSIER_MAITRE_IA.md` conserve des références historiques de commit/tests de fermeture de Phase 3;
- `README.md` et `docs/15_ROADMAP_ACTIVE.md` portent maintenant une photographie opérationnelle synchronisée, mais leurs sections historiques restent contextuelles.

Pour les compteurs de version ou la photographie de HEAD, vérifier toujours `pyproject.toml`, `CHANGELOG.md`, les migrations, les tests et `git log`.

---

## 4. État technique vérifié au dernier lot de code

Référence fonctionnelle actuelle :

- version logicielle : **`0.1.0a15`**;
- schéma SQLite : **39**;
- migration la plus récente : `0039_scc1b_provider_provenance.sql`;
- dernière validation complète connue : **767 tests réussis**;
- dernier commit fonctionnel courant : clôture de la baseline SCC-1B1 livrée après `3472aa6`;
- `1cf8278` est la photographie documentaire R&D SCC-1B; les commits `.gitignore` historiques ne font pas partie de l'état fonctionnel courant.

Toujours revérifier localement avant d'agir :

```bash
git status --short
git log -5 --oneline
python -m pytest
```

Adapter la commande Python à l'environnement local (`.venv/Scripts/python.exe -m pytest` sous Windows si nécessaire).

### Évolution récente réellement livrée

- `0.1.0a11` : une occasion sociale factuelle est observée **avant** que l'autonomie sapiente ne remplace l'attente qui la source;
- `0.1.0a12` : la latence LLM ne peut plus faire passer une proposition subjective devant une échéance déterministe déjà exigible;
- `0.1.0a13` : première agence non sapiente générique **CAT-0**, sans LLM et sans branche codée au nom/à l'espèce de Patoune; intentions courtes, passages adjacents, attente et abandon après échecs bornés;
- `0.1.0a14` : les tours sociaux bloqués par budget sont différés jusqu'à leur renouvellement au lieu d'être repollés à chaque tick; temps simulé et temps mural restent distincts;
- `0.1.0a15` : l'horloge canonique ne progresse que pendant une session runtime; arrêt propre = gel, crash = récupération au dernier instant durable, sans rattrapage accidentel hors ligne.

Documents récents associés :

- `docs/67_REPONSE_TECHNIQUE_R_D_POST_RODAGE_0_1_0A10.md`;
- `docs/68_CORRECTIF_ARBITRAGE_SOCIAL_0_1_0A11.md`;
- `docs/69_CORRECTIF_LATENCE_CHRONOLOGIQUE_0_1_0A12.md`;
- `docs/70_GEL_HORS_LIGNE_ET_RECUPERATION_CRASH_0_1_0A15.md`;
- `docs/71_R_D_SOCIAL_CONSEQUENCE_CORE.md`;
- `docs/72_R_D_SCC1_INTERPRETATION_SOCIALE.md`;
- `docs/73_R_D_SCC1B_PROVIDER_ET_CALIBRATION.md` décrit le banc SCC-1B2A;
  son implantation est `vivarium.social_interpretation_bench` et sa commande
  opérateur est `python -m vivarium social-interpretation-bench --level T0`;
- `CHANGELOG.md` pour `a13` et `a14`.

---

## 5. Ce qui est solide et ce qui ne l'est pas encore

### Solide / réellement matérialisé

- autorité canonique locale et transactions;
- journal canonique append-only;
- séparation temps simulé / temps mural / état runtime;
- monde, graphe, connecteurs, traversée, objets, contenance, possession;
- besoins, activités, ressources, blessures et transitions déterministes;
- cinq résidentes MVP et monde d'intégration;
- perception factuelle locale et attention technique bornée;
- premières traces subjectives, croyances sourcées, affect, buts/intention, relations/limites/permissions comme services contrôlés;
- frontière LLM locale structurée et validée;
- scènes sociales alpha;
- bancs d'essai, prévol, télémétrie et gardien local;
- CAT-0 non sapient générique;
- protection de chronologie contre latence LLM et arrêt hors ligne.

SCC-1B2A a été durci avec 30 IDs, 31 variantes déclarées, 27 fixtures T0
déterministes et 788 tests passants. B26–B29 sont explicitement `deferred`;
B20–B23 sont T0-only. Le smoke T1 borné du 9 août 2026 utilise
`google/gemma-4-12b-qat`, recette `scc1b1-native-v2`, pour 11 appels : 11
sorties valides, sans hard blocker ni fuite de canary. Cela mesure le transport
et le contrat; cela ne qualifie pas le modèle et T2 reste interdit jusqu'à audit.

### Présent mais encore mince / alpha

Le rodage a montré que plusieurs services subjectifs existent sans encore participer causalement de façon riche à la vie courante. Ne pas confondre **API implémentée** et **mécanisme vivant raccordé**.

Placeholders alpha à ne pas fossiliser :

- hiérarchie globale `intention > physiologie > objectif`;
- `idle` comme principal déclencheur cognitif;
- attention surtout technique;
- activités volontaires peu nombreuses et calibrations uniformes;
- scène dyadique bornée à quatre tours;
- co-présence/co-attente comme proxy social;
- topologie sociale réduite essentiellement à la pièce;
- petite taxonomie des actes de parole;
- relation résumée par quelques dimensions scalaires;
- mémoire essentiellement récente et exacte;
- mouvement incompatible avec activité;
- sommeil et motivation encore simplifiés.

Le rodage a notamment montré : small talk circulaire, concentration de certaines activités, socialité pauvre malgré des phrases lexicalement variées, absence d'anticipation riche, topologie sociale trop grossière, et distinction insuffisante entre activité/attente/intention/engagement.

---

## 6. Direction R&D actuelle — ne pas coder sans work order

La prochaine grosse étape conceptuelle n'est **pas** « générer davantage de texte ».

La direction R&D est de donner aux événements une conséquence subjective située, incertaine, mémorisable et révisable, tout en préservant les frontières RIC.

Les blocs actuellement préparés en amont sont notamment :

1. **Social Consequence Core** : interprétation sociale située et conséquences candidates séparées, sans `speech_act -> relation_delta` mécanique;
2. **mémoire minimale** : encodage, récupération, reconstruction, source monitoring, oubli/consolidation et mémoire prospective;
3. **Cognitive Admission** : accessible ≠ remarqué; sélection événementielle sans omniscience;
4. **topologie socio-spatiale** : visibilité, audibilité, orientation, distance qualitative, portes, privacité, participation et overhearing;
5. **Conversation State** : conversation ≠ compteur de tours; séquences ouvertes, repair, participation, adressage, floor et clôture;
6. **Behavioral Opportunity Layer** : remplacer la priorité globale fixe par un champ local de possibilités et de raisons structurées;
7. **agence non sapiente** : étendre CAT-0 sans transformer l'animal en petit humain ni en script d'espèce;
8. scénarios d'acceptation/falsification inter-systèmes.

Ces blocs sont des **contrats fonctionnels en préparation**. Codex conserve l'autorité sur leur traduction dans l'architecture réelle. Ne pas créer de nouvelles tables/classes juste à partir de cette liste.

---

## 7. Politique de travail pour la nouvelle instance Codex Luna

**Modèle de base recommandé : Luna.** Le but est de lui fournir des lots suffisamment spécifiés pour que le raisonnement scientifique et produit ait déjà été fait en amont.

Luna peut normalement traiter :

- inspection ciblée;
- implémentation locale bien spécifiée;
- tests définis;
- correctifs et refactors bornés;
- documentation technique liée au lot.

### Critères d'escalade

Arrêter et produire un rapport d'escalade au lieu de deviner si le travail rencontre :

- propriétaire persistant ambigu ou multiple;
- contradiction entre invariants;
- migration risquée ou irréversible sur une histoire persistante;
- changement architectural transversal important;
- plusieurs implantations incompatibles sans critère produit/architecture clair;
- bug non local dont la cause reste ambiguë après inspection et tests ciblés;
- besoin de remettre en cause un contrat scientifique/fonctionnel plutôt que son implantation.

Dans ces cas : **ne pas brute-force**. Expliquer les faits, options, risques et recommander Terra ou Sol si nécessaire.

### Règle de sécurité dépôt

Par défaut :

- ne supprimer aucun fichier/dossier;
- ne nettoyer aucun historique;
- ne rebase/force-push rien;
- ne lancer aucune reconstruction destructive (`init --force` ou équivalent) sur un monde qui compte;
- ne modifier aucune base persistante pour « réparer » silencieusement un problème;
- ne faire aucun ménage parce qu'un fichier « a l'air temporaire » sans vérifier ses références et sa provenance.

Tout ménage doit d'abord être classé `KEEP / GENERATED / OBSOLETE? / REVIEW / SAFE TO REMOVE` et approuvé avant suppression.

---

## 8. Procédure de reprise obligatoire

Pour une nouvelle conversation Codex :

1. lire ce fichier en entier;
2. exécuter `git status --short` et `git log -5 --oneline`;
3. vérifier `pyproject.toml`, dernière migration et tête de `CHANGELOG.md`;
4. lire les parties pertinentes de `docs/00_DOSSIER_MAITRE_IA.md`;
5. lire `docs/67_REPONSE_TECHNIQUE_R_D_POST_RODAGE_0_1_0A10.md` et les correctifs `68` à `70`;
6. inspecter le code réel uniquement là où nécessaire pour confirmer la photographie;
7. exécuter la suite de tests avant une modification significative;
8. signaler toute divergence entre cette passation et le dépôt;
9. **au premier tour, ne modifier aucun fichier** : rendre une photographie de reprise concise et attendre le work order suivant.

La première réponse attendue n'est pas un nouveau plan d'architecture. Elle doit confirmer que Codex comprend le système qu'il reprend et isoler toute divergence réelle.

---

## 9. Format de réponse de reprise attendu

Répondre brièvement avec :

```text
HEAD / arbre de travail :
Version / schéma / tests :
État général :
Invariants critiques compris :
Écarts passation ↔ dépôt :
Risques immédiats :
Prêt pour work order Luna : OUI/NON
Escalade nécessaire maintenant : OUI/NON + raison
```

Aucune écriture sur ce premier tour.

---

## 10. Rappel final

Le but de RIC n'est pas de faire croire qu'un LLM est la réalité.

Le moteur établit ce qui est vrai et possible. L'interaction établit ce qui est accessible. La cognition établit ce qui est subjectivement compris, mémorisé, priorisé et décidé. Les trois couches peuvent se répondre, mais aucune ne doit être silencieusement confondue avec une autre.
