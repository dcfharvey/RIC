# R&D — SCC-1C : admission cognitive sélective des épisodes sociaux

**Version R&D :** 0.1  
**Date :** 9 août 2026  
**État logiciel de référence :** commit `8f16c67`, version `0.1.0a15`, schéma 39; SCC-1B1 `scc1b1-native-v2` inchangé; campagne T2a Gemma exécutée en 105 appels génériques + 10 appels pairés.  
**Statut :** contrat scientifique et fonctionnel préparatoire. **SCC-1C n'est pas autorisé à l'implantation dans ce lot** : SCC-1B2 est fermé, mais la migration `interpretation-only` et l'étude structurelle de provenance imbriquée doivent précéder tout raccordement vivant. Codex demeure l'autorité sur l'architecture réelle, le stockage, l'ordre runtime, les migrations et les tests.

---

## 1. Problème à résoudre

SCC-0 a établi :

```text
parole sociale acceptée
-> accessibilité historique prouvée
-> trace subjective privée
```

SCC-1A/B a établi :

```text
trace SCC-0 explicitement choisie
-> snapshot privé borné
-> proposition LLM
-> interprétation privée validée, persistée et révisable
```

Il manque encore la décision intermédiaire : **pourquoi cette trace-ci devient-elle maintenant une occasion d'interprétation alors que d'autres traces peuvent rester sans pensée explicite?**

Le risque est double :

1. interpréter automatiquement chaque parole transforme l'accessibilité en cognition obligatoire, coûte des appels LLM et rend les agentes artificiellement omniscientes;
2. laisser le LLM parcourir le canon pour choisir lui-même ce qu'il « remarque » contourne précisément la frontière que SCC-0/SCC-1 ont construite.

SCC-1C est donc défini comme une **porte de sélection cognitive**. Il décide quelles sources subjectives deviennent admissibles à une interprétation SCC-1B; il n'interprète pas leur sens et ne produit aucune conséquence.

Principe central :

```text
accessible != encodé != candidat au traitement != sélectionné != interprété
```

---

## 2. État du dépôt pertinent

Le dépôt possède déjà deux mécanismes qu'il faut distinguer conceptuellement de SCC-1C.

### 2.1 `AttentionService` est une attention technique, pas une psychologie de l'attention

`AttentionService.snapshot` classe une vue factuelle locale et des signaux internes propres au personnage selon des priorités techniques stables et une borne explicite. Sa documentation précise déjà qu'il ne s'agit ni d'une pensée, ni d'une connaissance, ni d'une émotion, ni d'une mémoire.

SCC-1C ne doit donc pas transformer silencieusement ces priorités en loi psychologique de saillance. Codex pourra réutiliser de la plomberie existante si l'architecture réelle le justifie, mais la sémantique doit rester distincte.

### 2.2 `CognitionCallPolicy` est une porte de ressource LLM, pas la sélection subjective d'un épisode

La porte d'appel actuelle gère notamment déduplication, budget, debounce, provenance des motifs et mode dégradé. Elle répond à la question :

> « Un appel LLM de ce type est-il techniquement admissible maintenant? »

SCC-1C répond à une question différente :

> « Parmi les épisodes subjectivement encodés, lesquels deviennent effectivement objets d'interprétation? »

Ces deux décisions peuvent être enchaînées sans être confondues. Une trace peut être cognitivement sélectionnée mais son appel différé par budget; inversement, un budget disponible ne rend pas toutes les traces psychologiquement sélectionnées.

---

## 3. Résultats empiriques et techniques pertinents

### 3.1 [A — empirique] Une information présente et accessible peut ne pas être remarquée

Simons & Chabris (1999) montrent, dans une tâche dynamique d'attention visuelle, qu'un événement saillant peut ne pas être détecté lorsque l'attention est engagée ailleurs. La détection dépend notamment de la tâche attentionnelle et des propriétés de l'événement.

**Source :** Simons, D. J. & Chabris, C. F. (1999), *Gorillas in our midst: sustained inattentional blindness for dynamic events*, Perception 28(9), 1059–1074. DOI `10.1068/p281059`.

**Portée :** résultat visuel expérimental. Il soutient fortement la séparation générale `accessible != remarqué/traité`, mais ne fournit ni seuil numérique, ni règle sociale directement transférable à RIC.

### 3.2 [A/B — empirique] La capture attentionnelle dépend du contexte de contrôle

Folk, Remington & Johnston (1992) montrent que l'orientation attentionnelle involontaire dépend de la relation entre les propriétés du signal et les propriétés pertinentes pour la tâche en cours.

**Source :** Folk, C. L., Remington, R. W. & Johnston, J. C. (1992), *Involuntary covert orienting is contingent on attentional control settings*, Journal of Experimental Psychology: Human Perception and Performance 18(4), 1030–1044. DOI `10.1037/0096-1523.18.4.1030`.

**Portée :** paradigme visuel de laboratoire et théorie discutée dans la littérature. Il soutient l'idée que la pertinence courante peut moduler la sélection; il ne justifie pas une formule universelle `priority = relevance * salience` ni une implémentation neurobiologique.

### 3.3 [A/B — empirique] Le rôle interactionnel change les conditions de compréhension

Schober & Clark (1989) trouvent que des destinataires et des overhearers exposés aux mêmes paroles ne comprennent pas nécessairement de la même manière; les destinataires bénéficient du common ground et de la possibilité de collaborer au grounding.

**Source :** Schober, M. F. & Clark, H. H. (1989), *Understanding by addressees and overhearers*, Cognitive Psychology 21(2), 211–232. DOI `10.1016/0010-0285(89)90008-X`.

**Portée :** soutient que `addressee`, `side_participant` et autres rôles sont des indices fonctionnels pertinents. Cela ne justifie jamais `addressee -> toujours sélectionné` ni `side_participant -> jamais sélectionné`.

### 3.4 [A/B — empirique] La compréhension conversationnelle peut nécessiter réparation et révision

Clark & Wilkes-Gibbs (1986) montrent, dans une tâche de référence, que locuteur et destinataire collaborent et réparent/étendent une expression jusqu'à une version mutuellement acceptable. Schegloff, Jefferson & Sacks (1977) décrivent une organisation conversationnelle de réparation pour les problèmes de parler, entendre et comprendre.

**Sources :** Clark, H. H. & Wilkes-Gibbs, D. (1986), *Referring as a collaborative process*, Cognition 22(1), 1–39. DOI `10.1016/0010-0277(86)90010-7`; Schegloff, E. A., Jefferson, G. & Sacks, H. (1977), *The preference for self-correction in the organization of repair in conversation*, Language 53(2), 361–382. DOI `10.2307/413107`.

**Portée :** soutient qu'une clarification/réparation est un indice particulièrement pertinent pour reconsidérer une compréhension antérieure. Elle ne rend jamais la clarification vraie au niveau canonique et ne garantit pas qu'une nouvelle interprétation soit correcte.

### 3.5 [B — empirique général] Les humains structurent les flux continus en événements

Zacks, Tversky & Iyer (2001) montrent que des observateurs segmentent spontanément des activités continues en unités grossières et fines, avec une organisation hiérarchique liée aux objets/actions.

**Source :** Zacks, J. M., Tversky, B. & Iyer, G. (2001), *Perceiving, remembering, and communicating structure in events*, Journal of Experimental Psychology: General 130(1), 29–58. DOI `10.1037/0096-3445.130.1.29`.

**Portée :** soutient l'idée générale d'un traitement événementiel plutôt qu'un flux uniforme de polling. Ce travail n'établit pas que les frontières d'événements de RIC doivent correspondre aux événements SQLite ni qu'un événement canonique doit déclencher une cognition.

### 3.6 [C — modèle computationnel] Le gating est une abstraction plausible de sélection d'updates

O'Reilly & Frank (2006) proposent un modèle computationnel où des mécanismes frontostriataux appris contrôlent la mise à jour et le maintien de contenu en mémoire de travail.

**Source :** O'Reilly, R. C. & Frank, M. J. (2006), *Making working memory work: a computational model of learning in the prefrontal cortex and basal ganglia*, Neural Computation 18(2), 283–328. DOI `10.1162/089976606775093909`.

**Portée :** utile comme analogie de **porte sélective**, pas comme preuve que RIC doit reproduire les ganglions de la base, utiliser un réseau de gating appris ou employer ses variables.

---

## 4. Conclusions raisonnables mais incertaines

### [B/C] 4.1 L'admission doit être distincte de l'interprétation

Une source peut être encodée sans être immédiatement interprétée. Cette séparation est cohérente avec les résultats d'attention sélective et évite que le simple stockage subjectif devienne une pensée obligatoire.

### [B/C] 4.2 La sélection peut dépendre d'indices structurels sans connaître déjà le sens

Le rôle interactionnel, la présence d'une réparation/clarification reliée à un épisode antérieur et la structure événementielle sont des indices exploitables **avant** une interprétation sémantique riche. Ils peuvent modifier la probabilité/priorité d'une admission sans déterminer le résultat.

### [B/C] 4.3 Une source non sélectionnée ne doit pas nécessairement être « rattrapée » plus tard

Un backlog exhaustif où toute parole finit par être interprétée recréerait une mémoire/attention quasi omnisciente avec délai. Il est raisonnable que certaines traces restent durablement sans interprétation explicite.

### [C] 4.4 Une clarification est un bon candidat à la reconsidération, pas un oracle

Lorsqu'une nouvelle trace privée est clairement reliée à un problème de compréhension ou à une interprétation précédente, elle peut ouvrir une occasion de révision. Cela reste une nouvelle preuve subjective; elle ne révèle pas l'intention réelle du locuteur.

### [C] 4.5 Les budgets exacts sont de l'ingénierie

La science soutient une cognition sélective et limitée, mais ne fournit pas un nombre universel d'« interprétations sociales par minute ». Les bornes de RIC doivent être calibrées sur cadence, coût, latence et qualité du provider, puis versionnées comme décisions d'ingénierie.

---

## 5. Hypothèses de modélisation RIC pour SCC-1C

1. **Source obligatoire.** Une occasion SCC-1C part uniquement d'une `subjective_trace` SCC-0 appartenant au personnage. Aucun scan du canon brut ou de l'historique de scène ne peut créer une admission.
2. **Sélection sans sémantique cachée.** SCC-1C peut utiliser des métadonnées/provenances déjà prouvées (rôle, source, instant, liens de révision) mais ne doit pas prétendre connaître le motif réel ou la vérité du contenu.
3. **Résultat nul légitime.** Une trace peut être encodée et ne jamais recevoir d'interprétation SCC-1.
4. **Rôle = indice, pas règle.** Être destinataire peut rendre une source plus pertinente; cela ne garantit pas l'admission. Une participante latérale peut être sélectionnée lorsque le contexte le justifie.
5. **Réparation = occasion de révision, pas vérité.** Une clarification explicitement encodée peut rendre une interprétation antérieure candidate à la révision sans l'écraser.
6. **Borne explicite.** Le nombre d'occasions traitées par intervalle/épisode est limité pour des raisons de coût et de stabilité; aucune borne ne sera présentée comme capacité humaine mesurée.
7. **Pas de rattrapage exhaustif.** Redémarrage, panne modèle ou saturation budgétaire ne doivent pas déclencher automatiquement l'interprétation rétrospective de tout le passé.
8. **Événementiel.** Une nouvelle source ou une nouvelle preuve pertinente peut créer une occasion; le système ne scanne pas périodiquement toutes les traces.
9. **Admission != appel réussi.** Une occasion sélectionnée peut échouer/différer au niveau de la porte LLM. Cet état technique ne doit pas devenir une interprétation subjective.
10. **Aucune conséquence.** SCC-1C ne modifie croyance, affect, relation, permission, limite, consentement, but/intention, action ou canon.

---

## 6. Contrat fonctionnel minimal proposé

### 6.1 Entrée admissible

Au niveau fonctionnel, une occasion contient l'équivalent de :

- propriétaire/observatrice;
- clé stable de la trace SCC-0 source;
- identité/provenance de l'acte social déjà prouvé;
- rôle interactionnel dérivable;
- instant source et instant d'encodage;
- type d'occasion fermé, sans texte libre d'autorité;
- référence éventuelle à une interprétation antérieure lorsqu'il s'agit d'une reconsidération;
- référence aux nouvelles traces privées qui justifient cette reconsidération.

Les noms de champs et leur stockage appartiennent à Codex.

### 6.2 Sortie fonctionnelle de la porte

La porte doit pouvoir représenter au minimum :

```text
selected
not_selected / deferred
invalid_source
technical_degraded
```

La taxonomie exacte est une décision d'ingénierie. L'important est qu'un refus/non-sélection ne soit pas confondu avec une interprétation `unresolved` :

```text
non sélectionné
= aucune pensée SCC-1 n'a été produite

unresolved
= une interprétation a effectivement eu lieu et conclut qu'aucune lecture ne peut être retenue
```

Cette distinction est essentielle.

### 6.3 Indices admissibles en première tranche

Pour éviter une pseudo-psychologie prématurée, SCC-1C v1 devrait se limiter à des indices structurels dont la source est prouvable :

- rôle interactionnel (`addressee`, `side_participant`, `speaker` ou équivalent réel);
- nouvelle trace sociale effectivement encodée;
- lien explicite de clarification/réparation ou support vers une interprétation existante, lorsque ce lien peut être établi sans deviner le sens;
- état technique d'une occasion déjà sélectionnée (retry/deferred) pour idempotence;
- budget/cadence de traitement comme garde d'ingénierie.

Volontairement exclus de la première tranche :

- score lexical de « drama » ou mots-clés émotionnels;
- lecture brute de la personnalité pour décider qu'une parole « doit » compter;
- relation/attachement comme raccourci automatique de saillance;
- humeur/émotion comme multiplicateur non étudié;
- vérité du contenu;
- état privé d'autrui;
- LLM chargé de choisir dans tout le canon ce qu'il aurait remarqué;
- embeddings ou similarité sémantique comme oracle de sélection;
- rattrapage FIFO exhaustif de toutes les traces.

Ces éléments pourront être étudiés plus tard, notamment avec SCC-2 et une mémoire/récupération plus riche.

---

## 7. Interaction avec les composants existants

### 7.1 Avec SCC-0

SCC-0 reste la seule preuve qu'une parole sociale a été encodée subjectivement. SCC-1C ne doit jamais recréer une trace depuis `social_speech_act` simplement parce qu'elle existe.

### 7.2 Avec SCC-1B

SCC-1C ne construit pas un nouveau format d'interprétation. Une occasion sélectionnée utilise le provider/context builder SCC-1B déjà qualifié et laisse `SocialInterpretationService` valider/persister.

### 7.3 Avec `CognitionCallPolicy`

La porte de ressource LLM peut rester responsable de budget, débit, déduplication technique et mode dégradé. SCC-1C ne doit pas dupliquer silencieusement ces responsabilités.

Codex doit décider si la sélection cognitive et la porte d'appel sont deux étapes d'un même flux, deux services, ou une autre composition. Ce document fixe la sémantique, pas les classes.

### 7.4 Avec `AttentionService`

Les priorités techniques existantes ne deviennent pas des probabilités psychologiques. Si Codex réutilise une projection ou un type existant, le contrat doit conserver explicitement cette séparation.

### 7.5 Avec le futur Conversation State

SCC-1C ne doit pas devenir un état de conversation caché. Repair, adressage, floor, engagement et clôture appartiennent à une tranche fonctionnelle distincte. SCC-1C peut consommer plus tard un indice explicitement validé de Conversation State sans en être propriétaire.

---

## 8. Flux cible minimal

```text
social_speech_act
        ↓
preuve d'accès SCC-0
        ↓
subjective_trace privée
        ↓
occasion SCC-1C
        ↓
porte de sélection cognitive
   ┌────┴───────────┐
   │                │
non sélectionné   sélectionné
   │                ↓
   │         porte ressource LLM
   │                ↓
   │         snapshot SCC-1B fermé
   │                ↓
   │         provider propose
   │                ↓
   │    SocialInterpretationService
   │                ↓
   └────── aucune conséquence SCC-2/SCC-3
```

Ce flux ne signifie pas qu'une nouvelle table ou un nouveau service est requis.

---

## 9. Scénarios d'acceptation/falsification SCC-1C

### C1 — destinataire directe

Sophie parle à Erika; Erika encode la parole. Une occasion d'admission peut exister pour Erika.

**À ne pas conclure :** Erika doit nécessairement l'interpréter immédiatement.

### C2 — participante latérale

Luna a encodé la même parole en tant que `side_participant`.

**Attendu :** la source est valide et peut être sélectionnée; le rôle est conservé. Un système qui interdit toujours les participantes latérales est trop rigide.

### C3 — co-présente hors scène

Une résidente n'a aucune trace SCC-0 de la parole.

**Attendu :** aucune occasion SCC-1C ne peut être créée depuis cette parole.

### C4 — accessible mais non encodée

Une parole était accessible sous la sémantique de scène mais aucune trace SCC-0 n'a été créée.

**Attendu :** SCC-1C ne la récupère pas depuis l'historique brut.

### C5 — encodée mais non sélectionnée

Une trace SCC-0 existe, mais la porte ne la sélectionne pas.

**Attendu :** aucune `social_interpretation`; cet état peut rester permanent.

### C6 — rafale d'actes

Plusieurs paroles sont encodées dans un court intervalle alors que le budget de traitement est borné.

**Attendu :** le système reste stable/idempotent et ne promet pas de traiter exhaustivement toute la rafale plus tard.

### C7 — clarification/réparation

Une première interprétation existe. Une nouvelle trace privée de clarification est encodée et reliée de manière admissible.

**Attendu :** elle peut créer une occasion de révision de l'interprétation antérieure. L'ancienne entrée reste append-only; la clarification ne devient pas vérité de l'intention réelle.

### C8 — clarification sans interprétation antérieure

Une clarification est encodée mais aucune interprétation précédente n'existe.

**Attendu :** pas de `revision_of` inventé. La trace peut être traitée comme nouvel épisode ou rester non sélectionnée selon le contrat futur.

### C9 — panne provider après sélection

Une occasion a été sélectionnée, puis LM Studio est indisponible.

**Attendu :** résultat technique explicite, aucune interprétation partielle, aucune conséquence, retry idempotent selon la porte technique. Le système n'interprète pas d'autres sources « pour compenser ».

### C10 — isolation propriétaire

Une trace privée de Luna apparaît pendant qu'Erika a une occasion en attente.

**Attendu :** aucune modification du snapshot, de la sélection ou de l'interprétation d'Erika par simple existence de l'état privé de Luna.

### C11 — arrêt et reprise runtime

Des traces historiques existent après une période hors ligne.

**Attendu :** aucune campagne de rattrapage cognitif exhaustif n'est déclenchée uniquement parce que le runtime redémarre.

### C12 — aucun effet causal

Après admission sélectionnée/non sélectionnée, retry ou dégradation : croyances, affect, relations, permissions, limites, buts/intention, action et canon restent inchangés, sauf les états techniques/audits strictement nécessaires au propriétaire réel choisi par Codex.

---

## 10. Falsifications importantes

SCC-1C doit être considéré fonctionnellement mauvais s'il produit durablement un des patterns suivants :

- toute trace SCC-0 finit automatiquement interprétée;
- toute parole adressée est toujours sélectionnée;
- toute parole latérale est toujours ignorée;
- un mot-clé (« danger », « amour », « désolé ») devient une règle de sélection universelle;
- une priorité technique d'`AttentionService` est présentée comme saillance psychologique vraie;
- le LLM voit tout le canon pour décider ce que le personnage aurait remarqué;
- une panne/reprise déclenche le rattrapage de tout le passé;
- la non-sélection est encodée comme `unresolved`;
- une clarification est considérée comme preuve de l'intention réelle;
- l'admission modifie directement affect, croyance, relation, permission ou canon;
- les états privés d'un autre personnage influencent la sélection sans source accessible;
- des retries créent plusieurs interprétations pour la même occasion technique sans intention explicite de révision.

---

## 11. Métriques de banc recommandées

SCC-1C doit être testé d'abord sans runtime vivant et sans prétendre mesurer une psychologie humaine exacte.

Mesures utiles :

- nombre de traces SCC-0 candidates;
- nombre d'occasions créées;
- nombre sélectionné / non sélectionné / différé;
- distribution par rôle interactionnel;
- nombre d'appels LLM réellement consommés;
- déduplication/retry;
- délai canonique entre source, encodage, admission et interprétation;
- nombre de révisions déclenchées par nouvelles preuves;
- nombre de traces restant sans interprétation;
- aucune fuite owner-scoped;
- aucun effet SCC-2/SCC-3;
- latence et saturation du budget comme métriques d'ingénierie.

**Ne pas optimiser un « taux d'interprétation » vers 100 %.** Un taux élevé peut précisément signaler une sélection trop exhaustive.

Aucun nombre de sélection idéal n'est fixé par la science à ce stade.

---

## 12. Questions laissées à Codex

Avant implantation, Codex doit inspecter le dépôt et décider :

- si la sémantique d'occasion/admission peut réutiliser ou étendre l'infrastructure de `CognitionCallPolicy` sans fusionner sélection subjective et budget technique;
- s'il faut un état persistant propre ou si les journaux/cursors existants suffisent;
- comment représenter idempotence et retry sans créer un second propriétaire d'interprétation;
- à quel endroit du runtime une trace SCC-0 devient candidate sans violer l'ordre événementiel actuel;
- comment éviter le scan O(personnages × événements) déjà observé dans l'orchestrateur alpha;
- comment un lien de clarification/réparation est prouvé sans heuristique sémantique fragile;
- quelle politique de non-rattrapage après redémarrage préserve à la fois causalité vécue et opérabilité;
- quels audits/prévols doivent couvrir l'état technique ajouté;
- si une migration additive est réellement nécessaire.

Arrêter et escalader si l'implantation exige :

- lecture du canon brut pour contourner SCC-0;
- accès aux états privés d'autrui;
- second propriétaire de `social_interpretation`;
- modification du provider SCC-1B pour rendre l'admission possible;
- écriture de conséquences SCC-2/SCC-3;
- migration destructive;
- couplage à une taxonomie psychologique non justifiée.

---

## 13. Porte de promotion

**Préparation R&D : OUI.**  
**Autorisation d'implantation immédiate : NON.**

Avant un work order SCC-1C :

1. qualifier séparément la représentation de provenance/attribution imbriquée;
2. vérifier que la frontière SCC-1B reste stable après comparaison multi-modèles;
3. faire auditer par Codex l'intersection avec `CognitionCallPolicy`, l'orchestrateur et les propriétaires persistants;
4. figer uniquement le contrat fonctionnel minimal d'admission;
5. garder SCC-2/SCC-3 explicitement hors lot.

Le premier lot SCC-1C devra prouver seulement :

```text
trace subjective sociale valide
-> occasion événementielle bornée
-> sélection ou non-sélection explicite
-> si sélectionnée, interprétation SCC-1B existante
-> aucune autre conséquence
```

---

## 14. Références

- Simons, D. J. & Chabris, C. F. (1999). *Gorillas in our midst: sustained inattentional blindness for dynamic events*. Perception 28(9), 1059–1074. DOI `10.1068/p281059`.
- Folk, C. L., Remington, R. W. & Johnston, J. C. (1992). *Involuntary covert orienting is contingent on attentional control settings*. Journal of Experimental Psychology: Human Perception and Performance 18(4), 1030–1044. DOI `10.1037/0096-1523.18.4.1030`.
- Schober, M. F. & Clark, H. H. (1989). *Understanding by addressees and overhearers*. Cognitive Psychology 21(2), 211–232. DOI `10.1016/0010-0285(89)90008-X`.
- Clark, H. H. & Wilkes-Gibbs, D. (1986). *Referring as a collaborative process*. Cognition 22(1), 1–39. DOI `10.1016/0010-0277(86)90010-7`.
- Schegloff, E. A., Jefferson, G. & Sacks, H. (1977). *The preference for self-correction in the organization of repair in conversation*. Language 53(2), 361–382. DOI `10.2307/413107`.
- Zacks, J. M., Tversky, B. & Iyer, G. (2001). *Perceiving, remembering, and communicating structure in events*. Journal of Experimental Psychology: General 130(1), 29–58. DOI `10.1037/0096-3445.130.1.29`.
- O'Reilly, R. C. & Frank, M. J. (2006). *Making working memory work: a computational model of learning in the prefrontal cortex and basal ganglia*. Neural Computation 18(2), 283–328. DOI `10.1162/089976606775093909`.

---

## 15. Verdict R&D

RIC a déjà correctement séparé l'expression, l'accès, la trace et l'interprétation. La prochaine erreur facile serait de recoller ces couches en faisant de chaque trace une pensée obligatoire.

SCC-1C doit au contraire préserver une propriété centrale d'un agent non omniscient : **une chose peut lui être arrivée, avoir été encodée, et pourtant ne jamais devenir l'objet d'une interprétation explicite.**

La porte d'admission est donc justifiée comme abstraction fonctionnelle. Sa politique exacte doit rester minimale, falsifiable et calibrée; aucun mécanisme neurobiologique particulier n'est imposé à l'architecture RIC.
---

## Addendum du lot SCC-1B interpretation-only — 10 août 2026

SCC-1B2 est fermé. SCC-1C reste **NON AUTORISÉ À L'IMPLANTATION dans ce lot** : la migration `interpretation-only` est livrée séparément et l'étude structurelle de provenance/attribution imbriquée doit précéder tout raccordement vivant.
