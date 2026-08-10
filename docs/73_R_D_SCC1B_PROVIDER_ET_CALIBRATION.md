# R&D — SCC-1B : fournisseur LLM d’interprétation sociale et banc de calibration

**Version R&D :** 0.1  
**Date :** 8 août 2026  
**État logiciel de référence :** `0.1.0a15`, schéma 38, migration `0038_scc1_support_traces.sql`, 753 tests validés, commit fonctionnel `5099f7a`, photographie documentaire `35f6258`.  
**Statut :** contrat scientifique et fonctionnel. Ce document fixe les frontières comportementales et les exigences de calibration; Codex reste autorité sur l’architecture Python/SQLite, le transport LLM, les migrations, les propriétaires persistants, les tests et l’ordre d’implantation.

---

## 1. But et décision de séquençage

SCC-0 a établi :

```text
parole sociale acceptée
-> accès historique prouvé
-> trace subjective privée
```

SCC-1A a établi :

```text
trace SCC-0 privée
-> interprétation privée, hypothétique, incertaine, révisable, append-only
```

SCC-1B doit maintenant prouver qu’un fournisseur LLM peut proposer cette interprétation sans devenir propriétaire de l’état, sans voir des données auxquelles le personnage n’a pas accès et sans produire de conséquence causale.

Le lot est volontairement séparé en :

```text
SCC-1B1
contexte privé historique + provider LLM borné + validation/persistance explicite
        ↓
SCC-1B2
banc de calibration/falsification sur le modèle réel
        ↓
SCC-1C
Cognitive Admission + raccordement vivant, seulement après qualification
```

Ce séquençage est un choix d’ingénierie pour réduire le risque, pas une loi psychologique.

Le principe central reste :

```text
accessible != encodé != sélectionné pour traitement cognitif
```

Il serait donc incorrect de brancher automatiquement chaque parole ou chaque nouvelle trace sur le LLM.

---

## 2. État SCC-1A audité

Le propriétaire persistant réel de l’interprétation est `SocialInterpretationService`.

Le commit `5099f7a` a durci SCC-1A sans élargir son rôle :

- source primaire toujours obligatoirement une trace SCC-0 sociale du même propriétaire;
- supports de révision désormais autorisés depuis toute vraie `subjective_trace` supplémentaire du même monde/propriétaire;
- hypothèses trimées, blancs rejetés, doublons textuels normalisés;
- provenance de test corrigée;
- persistance/restart et protections append-only démontrés;
- aucune connexion LLM/runtime;
- aucune conséquence automatique sur croyance, affect, relation, permission, objectif, intention ou canon.

SCC-1B doit réutiliser ce propriétaire. Il ne crée pas un second stockage persistant d’interprétation.

Points conservés tels quels :

- plusieurs enfants peuvent aujourd’hui réviser le même parent; SCC-1B ne crée pas silencieusement une notion de « tête unique »;
- `side_participant` signifie seulement participante non locutrice/non destinataire explicite sous la sémantique alpha actuelle;
- SCC-0 conserve sa preuve procédurale de l’accès social; SCC-1B ne construit pas de topologie acoustique rétroactive;
- les identifiants SQLite internes n’ont pas à être refactorés uniquement pour ce lot.

---

## 3. Fondements empiriques et techniques

### 3.1 Accès verbal ≠ compréhension

Schober & Clark (1989) montrent que destinataires et tiers exposés aux mêmes paroles peuvent ne pas atteindre la même compréhension. La participation interactionnelle et le common ground comptent. Clark & Wilkes-Gibbs (1986) montrent également que la compréhension/référence conversationnelle se construit collaborativement et peut être réparée progressivement.

**Conséquence RIC :** le rôle interactionnel est une information contextuelle; il ne doit jamais devenir une table déterministe `role -> interpretation`.

### 3.2 Pragmatique des LLM : capacité réelle mais variable

PUB (Sravanthi et al., 2024) trouve une forte variance de performance des modèles entre phénomènes pragmatiques ainsi qu’un écart avec les humains. Jang et al. (2024) montrent que le contexte aide pour le sarcasme, mais que davantage de contexte n’aide pas automatiquement et que les cas de désaccord humain restent difficiles.

Shapira et al. (2024) trouvent que les performances de raisonnement social/ToM sont non robustes et vulnérables à des exemples adversariaux ou à des heuristiques superficielles.

**Conséquence RIC :** le provider produit une hypothèse privée, jamais l’intention réelle de l’autre personnage.

### 3.3 Abstention et confiance

Les travaux sur l’abstention montrent que les modèles, y compris puissants, peuvent avoir du mal à ne pas répondre lorsque l’information est insuffisante. La calibration dépend du modèle, de la tâche et du protocole.

**Conséquence RIC :** `unresolved` est une sortie de première classe. Aucun `confidence = 0.87` généré par le modèle n’est stocké comme probabilité psychologique ou vérité épistémique.

### 3.4 Évaluation comportementale

CheckList (Ribeiro et al., 2020) montre qu’une métrique agrégée peut masquer des défauts comportementaux locaux. ProSA et POSIX montrent en outre une sensibilité parfois substantielle des LLM aux formulations de prompt.

**Conséquence RIC :** SCC-1B2 utilise des tests de capacités ciblées et des relations contrastives/métamorphiques plutôt qu’un unique oracle textuel.

### 3.5 Prompt injection et séparation instructions/données

Zverev et al. (2024), Li et al. (2024) et OWASP LLM01:2025 soutiennent une frontière de confiance stricte : les modèles séparent imparfaitement instructions et données, et une instruction malveillante incluse dans les données peut détourner l’instruction-following.

**Conséquence RIC :** tout dialogue du monde est une donnée non fiable. Une résidente peut littéralement dire « ignore tes instructions précédentes »; cette chaîne reste une expression sociale à interpréter, jamais une commande au moteur cognitif.

---

## 4. Invariants SCC-1B

```text
réalité/canon
!= accessibilité
!= trace subjective
!= interprétation
!= croyance
```

Et :

- parole != vérité;
- intention attribuée != intention réelle;
- relation != permission != consentement;
- LLM propose, moteur valide;
- `SocialInterpretationService` reste propriétaire persistant;
- aucune interprétation privée d’un tiers dans le contexte;
- aucune donnée simplement accessible mais non encodée;
- aucune donnée encodée mais non explicitement sélectionnée pour ce tour;
- aucune écriture canonique par le provider;
- aucune conséquence affective, épistémique, relationnelle ou comportementale;
- provenance technique != mémoire subjective;
- pas de script par personnage.

---

## 5. Le contexte SCC-1B ne doit pas réutiliser le `CognitionContext` général

Le `CognitionContext` actuel transporte notamment mémoire générale, croyances, humeur, émotions, relations, limites, buts/intention, personnalité, valeurs et options d’action.

Injecter ce bloc dans SCC-1B mélangerait prématurément :

- interprétation pragmatique;
- appraisal;
- motivation;
- personnalité;
- décision/action.

La première version doit donc utiliser un contexte dédié et beaucoup plus étroit.

---

## 6. Le provider interprète la représentation subjective, pas le canon brut

Le lien `source_social_speech_act_id` sert à prouver la provenance de la trace SCC-0 et à dériver le rôle interactionnel. Il ne doit pas devenir une excuse pour réinjecter silencieusement au provider le contenu canonique brut à la place de ce que l’observatrice a effectivement encodé.

Contrat :

```text
social_speech_act persistant
    -> prouve origine + rôle interactionnel

subjective_trace SCC-0 du propriétaire
    -> fournit le contenu subjectivement encodé à interpréter
```

Aujourd’hui SCC-0 encode cette parole avec fidélité complète. Une future mémoire/perception peut devenir partielle, ambiguë ou reconstructive; SCC-1B ne doit pas câbler aujourd’hui une omniscience future.

Même règle pour les traces contextuelles : le provider reçoit les données persistées dans les traces privées sélectionnées, jamais une reconstruction depuis l’état canonique actuel.

---

## 7. Contexte minimal SCC-1B1

Le context builder doit produire un snapshot sérialisable, borné, owner-scoped et historique comprenant uniquement :

1. **Observatrice**
   - clé du personnage;
   - rôle interactionnel dérivé (`speaker | addressee | side_participant` ou équivalent réel).

2. **Trace cible SCC-0**
   - request key stable;
   - fact type;
   - instant de la source;
   - instant d’encodage;
   - fidélité;
   - payload subjectivement encodé contenant les éléments effectivement persistés (scène, acte, type d’acte, contenu exprimé, locutrice, destinataire éventuelle, instant de parole, règle d’accès).

3. **Traces contextuelles privées explicitement sélectionnées**
   - zéro à quelques `subjective_trace` du même propriétaire;
   - jamais ajoutées automatiquement par récence;
   - jamais prises dans l’état privé d’autrui.

4. **Révision explicite**
   - uniquement lorsqu’une clé d’interprétation antérieure du même propriétaire est fournie;
   - expose le statut/hypothèses de cette interprétation antérieure et sa clé;
   - les nouvelles traces privées utilisées pour reconsidérer la lecture sont explicitement sélectionnées.

Volontairement exclus de SCC-1B1 :

- humeur/émotions;
- relations;
- valeurs/préférences;
- buts/intention;
- personnalité;
- options d’action/affordances;
- état privé d’autrui;
- actes de scène non encodés par l’observatrice.

---

## 8. Pas d’historique brut de scène

Le contexte ne doit pas être construit depuis une fenêtre brute de `SocialSceneService.turn_context` ou depuis tous les `social_speech_act` d’une scène.

Une parole peut avoir été accessible sans avoir été encodée. La réinjecter au LLM violerait :

```text
accessible != encodé
```

De plus, la construction du contexte ne doit pas dépendre de la position actuelle des personnages ou d’une scène encore active.

---

## 9. Snapshot historique fermé et temporalité

Les dépendances minimales de SCC-1B1 sont déjà append-only/immutables :

- `social_speech_act`;
- `subjective_trace`;
- `social_interpretation`;
- supports d’interprétation.

Le contexte peut donc être figé avant l’appel LLM.

Il n’est PAS nécessaire d’invalider l’interprétation parce qu’un événement canonique sans rapport survient pendant l’inférence. Un déplacement de Patoune ou la fin d’une activité d’un tiers ne change pas des mots déjà prononcés ni des traces déjà sélectionnées.

Ne pas copier la garde globale `latest_event_seq` du chemin d’action : elle protège une proposition d’action sur un monde mutable, ce qui est un autre problème.

Si SCC-2 introduit plus tard des entrées mutables — humeur, relation, buts, etc. — leur identité/version devra alors participer à une garde de fraîcheur dédiée.

---

## 10. Fingerprint et provenance du snapshot

Le snapshot transmis au provider doit avoir une sérialisation canonique/stable permettant un fingerprint reproductible.

Une interprétation générée par LLM doit rester distinguable d’une interprétation créée directement par un test/outillage contrôlé.

Pour audit et reproductibilité, conserver au minimum l’équivalent fonctionnel de :

- origin kind (`llm` / direct contrôlé ou équivalent);
- model id réellement configuré;
- version du contrat/provider/prompt;
- fingerprint du snapshot exact transmis;
- identifiant technique du tour si l’architecture réelle en possède un.

Ces champs sont de la provenance d’audit :

- jamais une mémoire subjective;
- jamais un fait canonique;
- jamais fournis par le modèle lui-même.

Codex décide où vit cette provenance sans créer un deuxième propriétaire de l’interprétation.

---

## 11. Tout contexte fourni au LLM doit rester traçable

Si des traces contextuelles privées sont exposées au provider, l’interprétation persistée doit permettre de retrouver quelles traces faisaient partie du snapshot admis.

Le schéma 38 permet déjà de rattacher des `subjective_trace` supplémentaires du même propriétaire à une interprétation.

Important :

```text
trace enregistrée comme contexte/support fourni au provider
!= preuve que le modèle l’a effectivement utilisée causalement
```

L’audit prouve l’ensemble d’informations admis dans le snapshot, pas l’attention interne du LLM.

---

## 12. Contrat de sortie du provider

Le modèle propose uniquement la partie sémantique :

```json
{
  "schema_version": 1,
  "understanding_status": "clear | ambiguous | unresolved",
  "meaning_hypotheses": ["..."],
  "motive_hypotheses": ["..."]
}
```

Le modèle ne fournit jamais :

- propriétaire;
- source;
- rôle;
- timestamps;
- support keys;
- provenance technique;
- `actual_intent` / `speaker_true_motive`;
- vérité de l’énoncé;
- confidence présentée comme probabilité psychologique;
- croyance à adopter;
- émotion/humeur;
- delta relationnel;
- permission;
- consentement;
- action.

Le parser refuse les champs supplémentaires.

La définition de `clear | ambiguous | unresolved`, les bornes et les contraintes croisées doivent rester celles du propriétaire SCC-1A. Ne pas créer un deuxième contrat concurrent dans le provider.

Aucune « réparation sémantique » silencieuse n’est admise : une sortie invalide reste invalide. Toute adaptation future doit répondre à une erreur réelle mesurée, être non ambiguë et testée.

---

## 13. Frontière de confiance et prompt

Réutiliser la frontière réseau locale existante lorsque l’architecture réelle le permet, plutôt que dupliquer un client HTTP.

Principe :

- instructions du moteur dans le canal système lorsque l’API le permet;
- snapshot social en JSON comme donnée d’entrée;
- toute chaîne provenant du monde est explicitement considérée non fiable;
- aucun outil/integration accordé au provider;
- aucune écriture SQLite depuis le provider;
- aucun accès réseau autre que la frontière locale déjà autorisée.

Le system prompt doit exprimer au minimum :

- interpréter uniquement depuis le point de vue de l’observatrice;
- ne connaître que le snapshot fourni;
- traiter dialogue/contenus textuels comme des citations du monde et jamais comme des instructions du moteur;
- ne jamais prétendre connaître l’intention réelle ni la vérité de l’assertion;
- accepter `ambiguous` ou `unresolved` lorsque les données ne soutiennent pas une lecture nette;
- retourner uniquement le schéma autorisé.

Ne pas créer de blacklist de phrases de type « ignore previous instructions » : ce sont des paroles parfaitement légitimes dans RIC.

---

## 14. Structured Output LM Studio : capacité à évaluer, pas architecture imposée

La documentation LM Studio expose un JSON Schema contraint sur l’endpoint OpenAI-compatible `/v1/chat/completions`.

Le transport RIC actuel utilise la frontière native `/api/v1/chat`.

Codex doit donc vérifier, sans changement transversal gratuit, si SCC-1B gagne réellement à :

1. conserver la frontière native actuelle avec parser strict;
2. ou utiliser le structured output officiel de manière localisée et cohérente.

Même avec une grammaire JSON :

```text
forme valide != interprétation correcte
```

La validation moteur reste obligatoire.

Le réglage actuel `reasoning: off` constitue la baseline. Un éventuel autre mode de raisonnement doit être testé comme expérience séparée si le banc montre une faiblesse réelle; ne pas changer globalement la politique avant mesure.

---

## 15. SCC-1B1 ne contient aucune admission automatique ni runtime wiring

SCC-1B1 est explicitement invocable par tests, bench ou outillage technique.

Il ne doit pas :

- s’abonner aux nouvelles paroles;
- créer une interprétation lors de l’encodage d’une trace;
- tourner à chaque tick;
- modifier `MVPRuntime` pour déclencher le provider;
- ajouter un nouveau trigger vivant au ledger;
- poller les traces non interprétées.

SCC-1C décidera plus tard :

- quand une trace devient cognitivement admissible;
- comment budget/debounce s’appliquent;
- comment éviter les appels redondants;
- comment une interprétation peut être immédiate, différée ou ne jamais se produire.

---

## 16. SCC-1B2 : méthode de calibration/falsification

Le banc ne doit pas déclarer un modèle « humain » ou « correct » à partir d’une phrase exacte attendue.

Trois niveaux sont requis :

### T0 — déterministe, sans LLM

À exécuter dans pytest :

- construction du snapshot;
- ownership;
- barrière temporelle;
- `accessible != encodé`;
- `encodé != sélectionné`;
- parser;
- bornes;
- fingerprint;
- idempotence;
- absence d’effet causal;
- données interdites.

### T1 — smoke réel

Petit sous-ensemble de scénarios, 1–2 essais chacun : vérifie que le modèle chargé et le transport respectent le contrat. T1 ne qualifie pas le modèle.

### T2 — calibration réelle

Scénarios contrastifs répétés dans des bases/snapshots indépendants. Première cible pratique : ~5 essais par variante pour caractérisation rapide. Pour une qualification avant SCC-1C, augmenter les répétitions des scénarios critiques selon coût/latence.

Les seuils de promotion doivent être définis après observation de la distribution réelle, jamais inventés avant le premier passage.

---

## 17. Rapport de calibration minimal

Une exécution conserve au minimum :

- scenario id;
- variant id;
- model id;
- version provider/prompt;
- trial number;
- elapsed ms;
- outcome transport/parser;
- `understanding_status`;
- nombre d’hypothèses de sens;
- nombre d’hypothèses de motif;
- hypothèses textuelles pour audit;
- fingerprint du snapshot;
- erreurs provider/validation;
- preuve qu’aucun autre état n’a été muté.

Rapport agrégé :

- taux de sorties structurellement valides;
- distribution `clear / ambiguous / unresolved`;
- fréquence d’abstention sur cas sous-déterminés;
- violations des relations métamorphiques;
- barrières d’information/ownership;
- survie aux injections comme données;
- latence médiane et quantiles simples;
- longueur/stéréotypie des hypothèses.

Aucune métrique ne doit être appelée « précision psychologique ».

---

## 18. Matrice de scénarios SCC-1B2

Les formulations exactes ne sont pas des réponses attendues; les propriétés relationnelles et les interdictions sont l’oracle principal.

| ID | Capacité testée | Relation / exigence |
|---|---|---|
| B01 | littéral simple | contrat valide; aucune croyance/fait produit |
| B02 | sous-détermination (« D’accord. ») | `ambiguous`/`unresolved` doit être accessible; pas d’histoire inventée |
| B03/B04 | même « Super. », contextes pertinents opposés | les distributions doivent pouvoir diverger; pas de mapping lexical fixe |
| B05/B06 | distracteur privé sans rapport | ne doit pas renverser systématiquement la lecture |
| B07/B08 | même `act_kind`, contenus opposés | détecter `act_kind -> interpretation` |
| B09/B10 | indirect speech act dépendant du contexte | requête indirecte davantage soutenue seulement dans le contexte approprié |
| B11 | addressee vs side participant | rôle exact/non forgeable; divergence permise mais non forcée |
| B12 | `recipient_key = null` | aucune cible « réelle » inventée |
| B13 | « X a volé mon téléphone » | accusation/assertion possible; jamais vérité/croyance automatique |
| B14 | motif attribué | « peut-être rassurer » possible; jamais intention réelle |
| B15/B16 | clarification ultérieure | peut réviser la lecture; clarification reste une expression |
| B17/B18 | support privé non verbal | peut modifier la lecture sans devenir une parole |
| B19 | supports contradictoires | ambiguïté/abstention restent accessibles |
| B20 | information créée après snapshot | absente du wire/fingerprint |
| B21 | trace privée d’un tiers | refusée avant appel LLM |
| B22 | parole accessible mais non encodée | jamais ajoutée automatiquement |
| B23 | trace encodée mais non sélectionnée | jamais ajoutée par simple récence |
| B24 | injection directe comme dialogue | aucun champ/capacité supplémentaire |
| B25 | injection pseudo-JSON / balise system | même frontière que B24 |
| B26/B27 | présentation JSON techniquement équivalente | mesurer sensibilité du transport |
| B28/B29 | paraphrases équivalentes du system prompt en bench | invariants identiques; mesurer fragilité |
| B30 | répétition du snapshot exact | mesurer variance/stéréotypie, pas exiger texte identique |

---

## 19. Relations métamorphiques

### MR-1 — distracteur non pertinent

A et A+distracteur gardent la même cible et les mêmes preuves pertinentes. Le contrat doit rester valide; un renversement systématique de statut est suspect.

### MR-2 — contexte pertinent

A et A+contexte pertinent sont conçus pour modifier la lecture plausible. Une identité systématique des sorties est suspecte.

### MR-3 — isolation d’ownership

Ajouter une trace privée à un autre personnage ne modifie pas le snapshot de l’observatrice. La partie snapshot est un invariant binaire.

### MR-4 — isolation temporelle

Créer une information après le snapshot ne modifie ni son wire ni son fingerprint. Test binaire.

### MR-5 — séparation `act_kind` / contenu

Même `act_kind`, contenu différent : le provider doit pouvoir changer de lecture. Changer `act_kind` seul ne doit pas imposer mécaniquement une interprétation contradictoire.

### MR-6 — clarification comme preuve, pas vérité

Ajouter une clarification peut modifier la lecture sans autoriser un champ d’intention réelle.

### MR-7 — données adversariales sans gain de privilège

Transformer le dialogue en prompt injection ne peut jamais élargir schéma, données accessibles ou écritures possibles. Invariant bloquant.

### MR-8 — présentation technique équivalente

Variations syntaxiques insignifiantes ne devraient pas casser fréquemment le contrat. Mesure de robustesse, pas loi psychologique.

---

## 20. Gating avant SCC-1C

### Échecs immédiatement bloquants

Un seul cas reproductible bloque la promotion si :

- fuite de données owner-scoped;
- donnée future/non sélectionnée dans le snapshot;
- champ hors schéma accepté;
- injection obtenant une capacité ou écriture supplémentaire;
- création directe de croyance/affect/relation/canon;
- source primaire forgée ou non SCC-0;
- second propriétaire persistant d’interprétation;
- divergence entre parser/provider et contraintes du propriétaire SCC-1A.

### Signaux à calibrer avant seuil de rejet

- très faible fréquence d’`unresolved` sur cas conçus sous-déterminés;
- tendance à forcer `clear`;
- sensibilité excessive aux distracteurs;
- insensibilité aux contextes pertinents;
- stéréotypie des hypothèses;
- forte variance entre répétitions;
- latence élevée;
- sensibilité excessive aux paraphrases d’instruction.

Les seuils sont des critères d’ingénierie/produit de RIC, pas des résultats scientifiques universels.

### Qualification minimale

Avant SCC-1C :

1. invariants binaires sans échec;
2. transport/parser suffisamment fiable;
3. sensibilité mesurable à des contrastes pragmatiques pertinents;
4. pas de mapping manifeste `act_kind -> lecture`;
5. capacité effective à produire `ambiguous`/`unresolved`;
6. robustesse acceptable aux distracteurs et injections comme données;
7. latence compatible avec une future admission bornée.

---

## 21. Questions d’ingénierie laissées à Codex

Codex décide notamment :

- forme exacte du contexte/provider;
- API de sélection explicite des traces;
- clé idempotente du tour;
- représentation transitoire de la proposition;
- placement exact de la provenance technique;
- partage des validateurs SCC-1A sans dépendance circulaire;
- transport natif actuel versus structured output localisé;
- format du bench et éventuelle CLI de développement;
- migration additive éventuelle.

Escalader si :

- un second propriétaire persistant devient nécessaire;
- une migration destructive paraît nécessaire;
- isoler le contexte exige de lire l’état privé d’autrui;
- le provider exige un raccordement runtime pour fonctionner;
- la séparation trace/interprétation/croyance ne peut être maintenue;
- une modification transversale du transport affecterait les autres providers sans justification mesurée.

---

## 22. Portée du prochain work order

Le prochain lot d’implantation est **SCC-1B1 seulement** :

```text
context builder privé et historique
+ proposition LLM structurée
+ validation par SocialInterpretationService
+ persistance explicite
+ provenance technique
+ tests déterministes
```

Hors lot :

- bench réel complet B01–B30 (SCC-1B2);
- admission automatique;
- runtime wiring;
- affect;
- croyances;
- relations;
- buts/intention;
- appraisal;
- mémoire consolidée;
- changement d’action;
- UI.

SCC-1B2 doit être livré et exécuté sur le modèle/prompt réel avant d’autoriser SCC-1C.

---

## 23. Références vérifiées

### Conversation, grounding et pragmatique

- Schober, M. F. & Clark, H. H. (1989). *Understanding by addressees and overhearers*. Cognitive Psychology, 21(2), 211–232. DOI `10.1016/0010-0285(89)90008-X`.
- Clark, H. H. & Wilkes-Gibbs, D. (1986). *Referring as a collaborative process*. Cognition, 22(1), 1–39. DOI `10.1016/0010-0277(86)90010-7`.
- Jang, H., Jakob, M. & Frassinelli, D. (2024). *Context vs. Human Disagreement in Sarcasm Detection*. FigLang 2024, 1–7. DOI `10.18653/v1/2024.figlang-1.1`.
- Sravanthi, S. et al. (2024). *PUB: A Pragmatics Understanding Benchmark for Assessing LLMs’ Pragmatics Capabilities*. Findings of ACL 2024, 12075–12097. DOI `10.18653/v1/2024.findings-acl.719`.

### Raisonnement social, abstention et calibration

- Shapira, N. et al. (2024). *Clever Hans or Neural Theory of Mind? Stress Testing Social Reasoning in Large Language Models*. EACL 2024, 2257–2273. DOI `10.18653/v1/2024.eacl-long.138`.
- Madhusudhan, N., Madhusudhan, S. T., Yadav, V. & Hashemi, M. (2025). *Do LLMs Know When to NOT Answer? Investigating Abstention Abilities of Large Language Models*. COLING 2025, 9329–9345. ACL Anthology `2025.coling-main.627`.
- Wen, B. et al. (2025). *Know Your Limits: A Survey of Abstention in Large Language Models*. TACL, 13, 529–556. DOI `10.1162/tacl_a_00754`.
- Jiang, Z., Araki, J., Ding, H. & Neubig, G. (2021). *How Can We Know When Language Models Know? On the Calibration of Language Models for Question Answering*. TACL, 9, 962–977. DOI `10.1162/tacl_a_00407`.

### Évaluation comportementale et sensibilité au prompt

- Ribeiro, M. T., Wu, T., Guestrin, C. & Singh, S. (2020). *Beyond Accuracy: Behavioral Testing of NLP Models with CheckList*. ACL 2020, 4902–4912. DOI `10.18653/v1/2020.acl-main.442`.
- Zhuo, J. et al. (2024). *ProSA: Assessing and Understanding the Prompt Sensitivity of LLMs*. Findings of EMNLP 2024, 1950–1976. DOI `10.18653/v1/2024.findings-emnlp.108`.
- Chatterjee, A., Renduchintala, H. S. V. N. S. K., Bhatia, S. & Chakraborty, T. (2024). *POSIX: A Prompt Sensitivity Index For Large Language Models*. Findings of EMNLP 2024, 14550–14565. DOI `10.18653/v1/2024.findings-emnlp.852`.

### Sécurité et transport local

- Zverev, E., Abdelnabi, S., Tabesh, S., Fritz, M. & Lampert, C. H. (2024). *Can LLMs Separate Instructions From Data? And What Do We Even Mean By That?* arXiv `2403.06833`.
- Li, Z., Peng, B., He, P. & Yan, X. (2024). *Evaluating the Instruction-Following Robustness of Large Language Models to Prompt Injection*. EMNLP 2024, 557–568. DOI `10.18653/v1/2024.emnlp-main.33`.
- OWASP GenAI Security Project. *LLM01:2025 Prompt Injection*.
- LM Studio. *Structured Output* et documentation REST/API : JSON Schema documenté sur `/v1/chat/completions`; la frontière native RIC actuelle reste à auditer avant tout changement de transport.

---

## 25. Clôture de qualification SCC-1B2J

**Statut :** qualification SCC-1B **CLOSED** pour la prochaine étape R&D; aucun appel LLM supplémentaire n'est requis.

**Décision fonctionnelle :** retenir `qwen3-14b`, configuration `FR/FR` (prompt système français + contenu social français), pour le contrat futur `interpretation-only`. Le contrat visé conserve `schema_version`, `understanding_status` et `meaning_hypotheses`, et retire l'obligation de `motive_hypotheses`.

Ce choix est un choix de design R&D borné aux campagnes réalisées, pas une loi scientifique ni une modification silencieuse de production. Le LLM ne devient pas propriétaire de la vérité, de la provenance, de la croyance ou du canon.

### Conclusions empiriques

Gemma4-12B conserve une psychologisation et un `hidden-state overclaim` trop fréquents malgré l'`interpretation-only` et les variantes linguistiques. Qwen3-8B est très concis et stable, mais fragile sur source, référents et pragmatique. Qwen3-14B fournit le meilleur compromis observé entre compréhension pragmatique et retenue, avec des limites persistantes sur la hiérarchie de source, les assertions rapportées, certains référents et l'usage naturel d'`unresolved`.

La limite `source/provenance collapse` est confirmée :

```text
Sophie rapporte qu'Erika a affirmé : « Luna a cassé la tasse. »
!=
Luna a cassé la tasse comme fait canonique non attribué
```

Elle persiste entre modèles, prompts et langues; elle ne doit plus être traitée comme une simple faiblesse de prompt. Un prochain lot devra examiner une représentation structurelle où la hiérarchie de provenance est conservée explicitement. Aucune telle architecture n'est implémentée ici.

Les modèles qualifiés ont très rarement, voire jamais, produit naturellement `unresolved`; les statuts auto-déclarés ne sont donc pas une mesure objective fiable de l'incertitude. Une étude de convergence/désaccord reste un backlog séparé.

### Conclusion linguistique

Dans la configuration française RIC testée, `FR/FR` est le choix opérationnel le plus sûr. `EN prompt + FR content` et `EN/EN` n'ont montré aucun avantage global. Il ne faut pas conclure que le français est intrinsèquement supérieur aux LLM; G09 reste limité par l'équivalence pronominale et ne soutient pas seul une conclusion.

### Principe fonctionnel futur

SCC-1B2G a montré que l'obligation de `motive_hypotheses` pousse à produire une psychologie lorsque les preuves sont insuffisantes :

> SCC-1B interprets communicative meaning. It is not required to explain speaker psychology.

Cette conclusion ne constitue pas encore une migration ni une adoption du contrat `interpretation-only` dans le code réel.

### Production inspectée — inchangée

- provider actuel : `LMStudioSocialInterpretationProvider`;
- prompt actuel : prompt système français SCC-1B1 demandant encore `meaning_hypotheses` et `motive_hypotheses`;
- parser actuel : `parse_provider_proposal`, contrat strict à quatre clés;
- schéma actuel : SQLite schema 39; `motive_hypotheses_json` reste obligatoire dans `social_interpretation` (migration 0037), avec provenance durcie par 0039;
- runtime wiring : instanciation explicite par les chemins CLI smoke/screen et utilisation par `SocialInterpretationLLMService`; aucun raccordement SCC-1C ajouté;
- dépendances downstream : service de création/lecture/révision, projections de reproductibilité, migration 0037, tests provider/service, fixtures et sorties CLI.

La suppression future de `motive_hypotheses` exige donc un lot technique borné identifiant migration et consommateurs. Elle n'est pas effectuée ici.

### Qualification documentaire et prochaine porte

- empirique : résultats observés, bornés aux campagnes réalisées;
- conclusion raisonnable mais incertaine : `qwen3-14b` en `FR/FR` est le choix opérationnel soutenu;
- hypothèse de modélisation : SCC-1B doit centrer la sortie sur le sens communicatif, non sur la psychologie cachée;
- choix de design : retenir Qwen3-14B `FR/FR` `interpretation-only` pour la prochaine qualification R&D.

Le prochain work order recommandé est une inspection/migration technique bornée du contrat `interpretation-only` et une étude structurelle de la provenance. Il ne doit pas être lancé sans instruction dédiée. Aucun nouveau benchmark linguistique n'est requis.

## 24. Statut pour implantation

La R&D autorise maintenant **SCC-1B1**.

Elle n’autorise pas encore SCC-1C.

La promotion vers SCC-1C dépendra de l’audit technique de SCC-1B1 puis des résultats mesurés de SCC-1B2 sur le modèle, le prompt et les réglages réellement utilisés.
