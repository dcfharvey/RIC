# R&D — SCC-1 : interprétation sociale privée, incertaine et révisable

**Version R&D :** 0.1  
**Date :** 8 août 2026  
**État logiciel de référence :** `0.1.0a15`, schéma 36, migration `0036_subjective_social_speech.sql`, validation complète connue 739 tests, commit fonctionnel `be1cc2a`.  
**Statut :** proposition scientifique et fonctionnelle. Ce document définit des comportements et des frontières; Codex reste autorité sur l'architecture Python/SQLite, les migrations, les propriétaires persistants, les tests et l'ordre d'implantation.

---

## 1. Décision de périmètre

SCC-0 a fermé le chemin :

```text
parole sociale acceptée
-> accès historique prouvé pour une participante
-> trace subjective privée
```

SCC-1 ne doit pas encore produire une conséquence. Son rôle est plus étroit : permettre qu'une observatrice possède une **interprétation privée, hypothétique et révisable** d'une expression sociale qu'elle a effectivement encodée.

Chaîne retenue :

```text
social_speech_act
-> trace subjective SCC-0
-> SCC-1A : interprétation privée structurée, sans LLM/runtime
-> SCC-1B : proposition LLM bornée + contexte subjectif contrôlé
-> SCC-2 : appraisal / mémoire minimale / conséquences candidates
-> SCC-3 : chaque propriétaire accepte ou refuse ses propres mises à jour
```

Ce séquençage est un choix de réduction de risque d'ingénierie, pas une loi psychologique.

---

## 2. Audit R&D de SCC-0

### Verdict : ALIGNÉ pour poursuivre

Le commit `be1cc2a` conserve `SubjectiveMemoryService` comme propriétaire des traces subjectives et ajoute une référence persistante vers la parole sociale. L'encodage relit la source réelle, vérifie l'appartenance historique à la scène et n'écrit ni croyance, ni affect, ni relation, ni permission. La migration 36 est additive.

Les tests ajoutés couvrent destinataire, participante non ciblée, locutrice, co-présente hors scène, accès après fermeture/déplacement, idempotence, source inexistante et anti-inférence.

### Observations techniques à conserver pour Codex — non bloquantes

1. La preuve historique actuelle est un **certificat procédural** : un `social_speech_act` n'existe que parce que `SocialSceneService.speak` a validé la scène, les participantes et leur co-localisation au moment de l'écriture. Le dépôt ne reconstruit pas indépendamment une géométrie passée complète. Cette limite est acceptable sous la sémantique alpha de scène, mais ne doit pas être confondue avec une future preuve acoustique fine.
2. Le schéma impose une seule trace sociale par `(monde, personnage, acte social)`. Avant d'étendre l'API, Codex doit vérifier que le comportement d'une seconde `request_key` visant la même source est volontaire et cohérent avec le précédent des événements directs, plutôt que laisser une erreur SQLite brute devenir l'API par accident.
3. Le digest subjectif expose actuellement l'identifiant entier interne de `social_speech_act`. Codex doit décider, lorsqu'il touchera au digest, si cette identité est suffisamment stable pour les objectifs de reproductibilité ou si une identité persistante plus explicite est préférable. Ce document ne prescrit pas le changement.
4. `spoken_at` est la date persistée par le service de scène. Avant un futur raccordement LLM sensible à la chronologie, vérifier sa sémantique exacte dans le runtime au lieu de supposer silencieusement qu'elle équivaut toujours à un instant canonique vécu.

Aucun de ces points ne justifie de rouvrir SCC-0 avant SCC-1A sauf si Codex découvre un conflit réel pendant l'implantation.

---

## 3. Résultats empiriques et techniques

### 3.1 [A/B — empirique] Accéder aux mêmes mots ne garantit pas la même compréhension

Schober & Clark (1989) ont comparé destinataires et tiers qui entendaient les mêmes paroles. Dans leur tâche, les destinataires comprenaient mieux et pouvaient collaborer au grounding avec le locuteur; les tiers n'avaient pas le même avantage interactionnel.

**Source :** Schober, M. F. & Clark, H. H. (1989), *Understanding by addressees and overhearers*, Cognitive Psychology 21(2), 211–232. DOI `10.1016/0010-0285(89)90008-X`.

**Portée :** soutient `accès ≠ compréhension` et l'importance du rôle interactionnel/common ground. Une participante latérale de RIC n'est pas automatiquement équivalente à l'overhearer expérimental; aucune précision numérique par rôle n'est justifiée.

Clark & Carlson (1982) distinguent également addressees et autres participantes dans la structure des actes multiparty.

**Source :** Clark, H. H. & Carlson, T. B. (1982), *Hearers and Speech Acts*, Language 58(2), 332–373. DOI `10.2307/414102`.

**Portée :** cadre pragmatique utile, pas loi universelle de cognition.

### 3.2 [A/B — empirique] L'intention attribuée n'est pas un accès à l'intention réelle

Malle & Knobe (1997) montrent qu'une notion ordinaire partagée d'intentionnalité mobilise plusieurs composantes — désir, croyance, intention, conscience et habileté — plutôt qu'un simple booléen observable.

**Source :** Malle, B. F. & Knobe, J. (1997), *The Folk Concept of Intentionality*, Journal of Experimental Social Psychology 33(2), 101–121. DOI `10.1006/jesp.1996.1314`.

**Portée :** justifie qu'une attribution de but/motif soit une construction subjective. Elle ne donne aucun accès privilégié aux états mentaux réels d'autrui et ne commande pas une taxonomie unique pour RIC.

### 3.3 [A/B — revue empirique] La provenance remémorée est une attribution faillible

Le source monitoring humain est reconstructif et peut produire des erreurs d'attribution.

**Source :** Johnson, M. K., Hashtroudi, S. & Lindsay, D. S. (1993), *Source monitoring*, Psychological Bulletin 114(1), 3–28. DOI `10.1037/0033-2909.114.1.3`.

**Portée :** renforce l'invariant `provenance d'audit ≠ source subjectivement remémorée`. SCC-1A conserve une provenance technique exacte sans prétendre que l'agent se la remémorera toujours correctement.

### 3.4 [B — technique] Une confiance numérique produite par un LLM n'est pas automatiquement calibrée

Jiang et al. (2021) trouvent une mauvaise calibration sur leurs modèles/tâches de QA et montrent qu'une calibration peut être améliorée par des méthodes dédiées. D'autres travaux montrent que certains modèles et protocoles permettent une auto-évaluation plus utile. La conclusion défendable est donc : **la calibration dépend du modèle, de la tâche et du protocole**.

**Sources :** Jiang et al. (2021), *How Can We Know When Language Models Know?*, TACL 9, 962–977, DOI `10.1162/tacl_a_00407`; Kadavath et al. (2022), *Language Models (Mostly) Know What They Know*, arXiv `2207.05221`.

**Conséquence pour RIC :** SCC-1 ne stocke pas un `confidence=0.87` généré par le modèle comme probabilité psychologique ou vérité épistémique. La première version utilise des états qualitatifs et l'abstention. Toute future confiance scalaire devra être calibrée empiriquement sur le modèle et la tâche réellement utilisés.

---

## 4. Conclusions raisonnables mais incertaines

### [B/C] 4.1 Une unité d'interprétation épisodique est utile

La littérature ne définit pas un objet universel « Social Interpretation Record ». Pour RIC, une unité privée reliant une observation sociale précise à une lecture possible permet toutefois de conserver proprement ambiguïté, divergence entre personnages et révision.

### [B/C] 4.2 Le rôle interactionnel peut influencer la lecture sans la déterminer

Être locutrice, destinataire explicite ou participante latérale fournit une information pertinente sur la situation. Ce rôle ne doit pas devenir un mapping déterministe vers une compréhension ou une émotion.

### [B/C] 4.3 Une hypothèse de but communicatif peut exister sans être obligatoire

Une observatrice peut se représenter « elle essaie peut-être de me rassurer » ou « je ne sais pas pourquoi elle dit ça ». Le système doit pouvoir n'attribuer aucun motif ou conserver plusieurs hypothèses.

---

## 5. Hypothèses de modélisation RIC

Ces choix sont des abstractions de simulation :

1. Une trace sociale peut ne jamais être interprétée.
2. Une interprétation est privée à son propriétaire.
3. Une même trace peut donner des interprétations différentes chez deux propriétaires distincts.
4. Une interprétation peut être `clear`, `ambiguous` ou `unresolved`; `clear` signifie seulement que **le personnage a une lecture nette**, pas que cette lecture est objectivement correcte.
5. Une interprétation peut contenir zéro, une ou plusieurs hypothèses de sens selon son statut.
6. Une hypothèse de but/motif communicatif est facultative et explicitement attribuée à l'observatrice.
7. Une interprétation acceptée n'est jamais écrasée silencieusement; une révision crée une nouvelle version/entrée traçable.
8. Une révision peut redevenir plus ambiguë qu'une version antérieure.
9. L'interprétation existe à son instant de création, pas rétroactivement à l'instant de la parole.
10. L'absence de conséquence ultérieure est un résultat valide.

---

## 6. Frontières de propriété

SCC-1 introduit une nouvelle famille d'état **seulement si Codex confirme qu'elle possède une sémantique persistante distincte**.

Conceptuellement :

```text
trace SCC-0
= ce que le système peut prouver que l'observatrice a encodé de l'expression

interprétation SCC-1
= lecture hypothétique de cet épisode par l'observatrice

croyance
= proposition adoptée par le personnage avec son contrat épistémique propre

émotion
= état affectif appartenant à AffectService

relation
= résumé/état relationnel appartenant au propriétaire social existant
```

Une interprétation telle que « elle me taquine peut-être » n'est pas automatiquement une croyance durable « je crois qu'elle voulait me taquiner ». Si une proposition doit devenir une croyance persistante, le propriétaire de croyance existant doit l'accepter plus tard selon son propre contrat.

SCC-1 ne doit donc pas devenir un second propriétaire de :

- `subjective_trace`;
- croyances;
- humeur/épisodes émotionnels;
- relations;
- limites/permissions/consentement;
- buts/intentions;
- canon.

---

## 7. Contrat fonctionnel SCC-1A

### 7.1 But

Implanter uniquement la **structure persistante et contrôlée d'une interprétation sociale privée**, avec provenance, confidentialité, idempotence, révision et audit.

SCC-1A fonctionne avec un fournisseur contrôlé/factice dans les tests. Il n'appelle pas le LLM et n'est pas raccordé au runtime vivant.

### 7.2 Source admissible

Une interprétation initiale doit partir d'une trace appartenant au même personnage et prouvant une parole sociale SCC-0. Le service relit lui-même cette trace et sa provenance; il ne fait pas confiance à un payload de parole fourni par l'appelant.

Le rôle interactionnel doit être dérivable de la source persistante :

- `speaker` si propriétaire = locutrice;
- `addressee` si propriétaire = destinataire explicite;
- `side_participant` si propriétaire participe à la scène sans être la cible;
- si l'architecture réelle nécessite une valeur distincte lorsque `recipient_key` est nul, Codex peut la définir sans changer le principe.

Aucun rôle ne doit être accepté comme vérité parce qu'un provider l'affirme.

### 7.3 Sortie minimale

Les noms de champs et le stockage sont laissés à Codex. Le contrat doit pouvoir représenter au minimum :

- propriétaire;
- source SCC-0 prouvée;
- rôle interactionnel dérivé;
- statut de compréhension : `clear | ambiguous | unresolved`;
- zéro à quelques hypothèses de sens courtes et bornées;
- zéro à quelques hypothèses de but/motif communicatif courtes, explicitement attribuées et facultatives;
- instant d'interprétation;
- provenance d'audit;
- lignée de révision lorsqu'il s'agit d'une nouvelle lecture.

Le contrat ne requiert **aucun score numérique de confiance**.

### 7.4 Abstention

`unresolved` avec aucune hypothèse est un résultat valide. Une trace peut aussi rester sans aucun enregistrement SCC-1. L'existence d'une trace ou son rappel ne déclenche pas automatiquement une interprétation.

### 7.5 Révision

Une nouvelle interprétation peut réviser une interprétation active/précédente du même propriétaire. Elle doit :

- conserver l'ancienne entrée;
- pointer explicitement vers ce qu'elle révise;
- être soutenue par la source initiale et, lorsque la révision dépend d'une nouvelle observation, par une ou plusieurs nouvelles traces privées du même propriétaire;
- ne jamais transformer une clarification prononcée en accès canonique à l'intention réelle du locuteur.

Exemple : « je plaisantais » peut justifier une nouvelle lecture subjective de la phrase précédente; elle ne prouve pas au moteur que l'intention réelle était humoristique.

### 7.6 Anti-inférence

Créer ou réviser une interprétation ne modifie rien d'autre. En particulier :

- aucun `subjective_belief`;
- aucune humeur/émotion;
- aucun `relationship_view`;
- aucune permission/limite/consentement;
- aucun objectif/intention;
- aucune action;
- aucun événement canonique.

---

## 8. Ce qui est volontairement hors SCC-1A

Ne pas ajouter :

- appel LM Studio / LLM;
- raccordement au cycle social/runtime;
- Cognitive Admission automatique;
- contexte riche de croyances, relations, valeurs ou affect;
- expectancy violation structurée;
- appraisal émotionnel;
- conséquence candidate;
- écriture de croyance;
- changement relationnel;
- création d'émotion;
- mémoire consolidée, rappel associatif ou oubli;
- confiance de source avancée;
- topologie acoustique/privacité fine;
- Conversation State avancé;
- BOL;
- nouvelles actions de parole.

Ces mécanismes peuvent devenir des dépendances des tranches suivantes, mais ne doivent pas fuiter dans SCC-1A.

---

## 9. Scénarios d'acceptation SCC-1A

### I1 — même expression, lectures privées différentes

B et C possèdent chacune une trace SCC-0 de la même parole. Des fournisseurs contrôlés proposent deux interprétations différentes.

**Attendu :** deux états privés séparés, même provenance factuelle, aucune interprétation globale de la parole.

### I2 — destinataire ≠ participante latérale

A parle explicitement à B dans une scène comprenant C.

**Attendu :** le rôle de B est dérivé comme destinataire et celui de C comme participante latérale; leurs lectures peuvent diverger. Aucun rôle n'est fourni arbitrairement par le provider.

### I3 — ambiguïté valide

Une source reçoit `ambiguous` avec deux lectures incompatibles mais plausibles.

**Attendu :** aucune sélection forcée et aucune conséquence.

### I4 — abstention valide

Une source reçoit `unresolved` sans hypothèse.

**Attendu :** état valide ou absence d'interprétation selon le chemin explicitement appelé; aucune invention pour remplir les champs.

### I5 — assertion ≠ croyance/vérité

A dit « B a volé mon téléphone »; C interprète correctement que A accuse B.

**Attendu :** l'interprétation peut représenter « A accuse B »; elle ne crée ni le fait « B a volé », ni une croyance de C que B l'a fait.

### I6 — motif attribué ≠ état mental réel

B propose comme hypothèse « A essaie peut-être de me rassurer ».

**Attendu :** hypothèse privée explicitement attribuée; aucune lecture d'un état privé de A et aucun champ `actual_intent`.

### I7 — provenance forgée refusée

Le caller/provider tente d'utiliser une trace sociale d'un autre personnage ou une trace non sociale.

**Attendu :** refus sans écriture.

### I8 — révision par nouvelle trace

Après une interprétation ambiguë, une nouvelle parole de clarification est encodée par B. Une nouvelle interprétation révise la première.

**Attendu :** ancienne interprétation conservée, nouvelle entrée sourcée, lignée auditable.

### I9 — clarification non omnisciente

La clarification est « je plaisantais ».

**Attendu :** elle peut influencer la nouvelle lecture de B mais ne devient jamais preuve canonique de l'intention réelle de A.

### I10 — idempotence/conflit

Même demande + mêmes sources + même proposition validée => même résultat. Réutilisation incompatible de la clé => conflit explicite.

### I11 — confidentialité

Le service normal ne permet pas à C de lire les interprétations privées de B.

### I12 — anti-conséquence

Les états de croyance, affect, relation, permission, but/intention et canon sont identiques avant/après création ou révision.

### I13 — temporalité

Une vieille trace est interprétée plus tard.

**Attendu :** l'instant source et l'instant d'interprétation restent distincts; aucune rétrodatation cognitive.

### I14 — pas d'interprétation automatique

Une trace SCC-0 peut exister sans aucune interprétation SCC-1.

**Attendu :** aucun watchdog, recall ou hook ne transforme toutes les traces en pensées.

---

## 10. SCC-1B — tranche future, pas encore à coder

Après validation structurelle de SCC-1A, une seconde tranche pourra ajouter un fournisseur LLM local qui propose l'interprétation.

Contrats prévus :

- contexte subjectif borné et appartenant uniquement à l'observatrice;
- source sociale et rôle dérivés, jamais inventés par le modèle;
- sortie structurée avec `clear/ambiguous/unresolved`;
- hypothèses courtes et bornées;
- possibilité explicite de ne rien conclure;
- aucune confiance numérique considérée calibrée par défaut;
- aucun accès aux états privés de l'autre personnage;
- garde de staleness explicite si l'inférence dépend d'un contexte pouvant changer pendant l'appel;
- aucune conséquence causale encore.

Si une confiance numérique devient utile plus tard, elle devra être calibrée/évaluée sur le modèle local et le protocole réel au lieu d'être prise au pied de la lettre.

---

## 11. SCC-2 — direction ultérieure

SCC-2 pourra étudier, avec recherche dédiée :

- quelles informations subjectives doivent être récupérées pour interpréter un événement;
- attentes et violations d'attentes;
- appraisal et pertinence pour buts/valeurs/limites;
- source/fiabilité;
- mémoire minimale, récupération et condensation;
- conséquences candidates indépendantes.

Aucune de ces candidates ne deviendra encore une mise à jour simplement parce qu'elle a été proposée. SCC-3 conservera la validation par chaque propriétaire d'état.

---

## 12. Falsifications futures

Lorsque SCC-1B sera testable avec le modèle réel, surveiller des distributions/patterns plutôt que des scripts de personnage. Le système est suspect si :

- `act_kind` suffit presque toujours à prédire la lecture;
- `ambiguous/unresolved` n'est pratiquement jamais utilisé;
- destinataire et participante latérale reçoivent presque toujours la même lecture malgré des contextes distincts;
- toute excuse est interprétée comme sincère;
- toute assertion est transformée en croyance ou vérité;
- les motifs attribués sont systématiquement certains;
- les informations privées d'autrui apparaissent dans les interprétations;
- une nouvelle source ne permet jamais de révision;
- les interprétations se créent pour toutes les traces sans sélection cognitive;
- la qualité change radicalement avec une variation purement technique sans justification fonctionnelle.

---

## 13. Questions laissées à Codex pour SCC-1A

Codex doit décider après inspection du dépôt :

- s'il existe déjà un propriétaire naturel pour cette nouvelle sémantique ou si un propriétaire distinct est requis;
- la forme exacte du stockage, des clés et de la lignée de révision;
- si une interprétation initiale est unique par source ou si plusieurs alternatives appartiennent à une même entrée;
- comment exprimer l'idempotence sans exposer des erreurs SQLite brutes;
- quel digest/audit/prévol doit inclure l'état interprétatif sans le mélanger au canon;
- quelles références stables employer vers les traces sources;
- comment préserver les migrations existantes et les propriétaires actuels.

Arrêter et escalader si l'implantation exige :

- un second propriétaire d'une croyance, trace, émotion ou relation;
- une migration destructive;
- une lecture des états privés d'autrui;
- un raccordement LLM/runtime pour rendre la structure elle-même possible;
- une contradiction avec les invariants du dépôt.

---

## 14. Verdict

**SCC-1A : prêt pour un work order Luna borné.**

### Amendement SCC-1B interpretation-only (10 août 2026)

Le contrat effectivement livré par SCC-1B conserve `schema_version`,
`understanding_status` et `meaning_hypotheses`. Il ne requiert ni ne produit
`motive_hypotheses`: l'interprétation porte sur le sens communicatif et
n'impose pas d'explication psychologique du locuteur. Les anciennes valeurs
de motif sont conservées uniquement sous une colonne legacy non projetée lors
de la migration du schéma; elles ne sont ni relues ni promues en provenance,
fait, croyance ou conséquence.

La science soutient qu'une expression accessible n'impose pas une compréhension unique et que les attributions d'intention sont des constructions subjectives. Elle ne fournit pas une taxonomie universelle de « sens social » ni un score de confiance que RIC devrait fossiliser.

La prochaine étape sûre est donc une structure privée, sourcée, révisable et sans conséquence. Le LLM viendra seulement après que cette frontière aura été prouvée techniquement.
