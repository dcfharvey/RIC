# R&D — Social Consequence Core (SCC)

**Version R&D :** 0.1  
**Date :** 8 août 2026  
**État logiciel vérifié :** `0.1.0a15`, schéma 35, 734 tests  
**Statut :** proposition scientifique et fonctionnelle. Ce document ne prescrit pas l'architecture Python/SQLite; Codex reste autorité sur l'implantation réelle.

---

## 1. But

Définir le plus petit enchaînement permettant à un événement social d'avoir une signification subjective et, plus tard, des conséquences affectives, épistémiques, mémorielles, intentionnelles ou relationnelles **sans** coder une causalité naïve du type :

```text
compliment -> +affection
refus -> -affection
excuse -> +confiance
inform -> croyance vraie
relation positive -> permission/consentement
```

Le SCC est un **concept fonctionnel**. Il ne suppose ni package unique, ni table unique, ni service unique.

---

## 2. Invariants non négociables

```text
réalité/canon ≠ accessibilité ≠ perception/encodage ≠ interprétation ≠ croyance
parole prononcée ≠ vérité du contenu prononcé
relation ≠ permission ≠ consentement
intention attribuée ≠ intention réelle
appraisal ≠ émotion ≠ action
mémoire d'audit ≠ souvenir subjectivement accessible
LLM propose, service/moteur valide
un seul propriétaire persistant par état
```

Une conséquence sociale ne peut jamais être créée uniquement à partir du `act_kind` d'une parole.

---

## 3. Consolidation des travaux R&D antérieurs

Les conclusions principales de `64`, `65`, `66` et `67` restent valides après `0.1.0a15` :

- le socle n'exige pas de refonte conceptuelle avant le social causal;
- l'interprétation située doit précéder une conséquence relationnelle automatique;
- les dimensions relationnelles actuelles peuvent rester des résumés, mais ne doivent pas devenir la totalité de l'histoire relationnelle;
- la mémoire exacte append-only du moteur ne doit pas devenir une mémoire humaine parfaite;
- la hiérarchie décisionnelle alpha, l'attention technique et la scène à quatre tours sont des gardes provisoires, pas des théories psychologiques.

Les correctifs `a11` à `a15` renforcent plutôt les contraintes du futur SCC :

- `a11` : une occasion sociale doit être découverte avant qu'une autre couche ne détruise légalement sa source;
- `a12` : une interprétation ou conséquence doit rester ancrée à l'instant/contexte source, pas à la fin d'une inférence lente;
- `a13` : l'agence non sapiente confirme la règle « mécanisme générique > script par identité »;
- `a14` : un travail subjectif différé doit être événementiel/idempotent, jamais repollé inutilement;
- `a15` : temps canonique vécu et temps mural d'exécution restent séparés; aucune absence du runtime ne doit créer rétrospectivement une vie sociale fictive.

---

## 4. Résultats empiriques pertinents

### 4.1 [A/B] Le label d'un acte ne détermine pas sa conséquence

Les recherches sur les attentes interpersonnelles et leur violation montrent que l'effet d'un comportement dépend des attentes préalables et de l'évaluation de l'écart; une déviation peut être évaluée positivement ou négativement selon le contexte et la relation.

**Source :** Judee K. Burgoon (1993), *Interpersonal Expectations, Expectancy Violations, and Emotional Communication*, Journal of Language and Social Psychology, 12, 30–48. DOI `10.1177/0261927X93121003`.

**Source empirique complémentaire :** Burgoon & Le Poire (1993), *Effects of Communication Expectancies, Actual Communication, and Expectancy Disconfirmation...*, Human Communication Research, 20, 67–96. DOI `10.1111/j.1468-2958.1993.tb00316.x`.

**Portée :** soutient l'importance des attentes et du contexte. Ne justifie pas une équation universelle de « violation ».

### 4.2 [B] La signification relationnelle passe par la perception de la réponse du partenaire

Dans des journaux d'interactions réelles, divulgation et perception de la réactivité du partenaire contribuent à l'expérience d'intimité; la réactivité perçue médie partiellement le processus.

**Source :** Laurenceau, Barrett & Pietromonaco (1998), *Intimacy as an interpersonal process...*, Journal of Personality and Social Psychology, 74, 1238–1251. DOI `10.1037/0022-3514.74.5.1238`.

**Portée :** particulièrement pertinent pour intimité/divulgation; ne doit pas être transformé en règle universelle applicable à toute parole.

### 4.3 [B] La confiance doit conserver un objet/contexte

La littérature sur la confiance est fragmentée; une synthèse utile recommande de représenter au minimum l'acteur qui fait confiance, la cible, la matière/enjeu concerné et l'incertitude du résultat plutôt qu'une collection de « types de confiance » indifférenciés.

**Source :** Robbins (2016), *What is Trust? A Multidisciplinary Review, Critique, and Synthesis*, Sociology Compass, 10, 972–986. DOI `10.1111/soc4.12391`.

**Portée :** revue conceptuelle, pas loi quantitative. Elle soutient surtout l'interdiction de traiter `trust_milli` comme explication exhaustive.

### 4.4 [A/B] Une excuse peut réparer sans constituer une opération déterministe

Une méta-analyse de 18 articles / 36 tailles d'effet / 4731 participants trouve un effet positif moyen de l'excuse sur la réparation de confiance (`d = 0.44`), avec modération notamment par le type de violation.

**Source :** Yuan, Dong & Li (2017), *The trust repair effect of apology: A systematic review and meta-analysis*, Advances in Psychological Science, 25, 1103–1113. DOI `10.3724/SP.J.1042.2017.01103`.

**Portée :** l'effet moyen n'autorise jamais `apologize -> +trust`; le contexte et la nature de la transgression comptent.

### 4.5 [A/B] L'intention attribuée est une variable sociale distincte et incertaine

Les humains distinguent les actions intentionnelles et non intentionnelles. Le modèle empirique de Malle & Knobe identifie désir, croyance, intention, conscience et habileté comme composantes du concept ordinaire d'intentionnalité. Une réplication préenregistrée de 2022 soutient le résultat de base sur la cohérence des jugements d'intentionnalité.

**Sources :** Malle & Knobe (1997), *The Folk Concept of Intentionality*, Journal of Experimental Social Psychology, 33, 101–121. DOI `10.1006/jesp.1996.1314`; réplication 2022, DOI `10.1016/j.jesp.2022.104372`.

**Portée :** justifie que l'intention perçue puisse compter; ne justifie jamais de traiter cette attribution comme accès à l'état mental réel de l'autre.

### 4.6 [B] L'appraisal est une bonne famille de mécanismes intermédiaires, pas une taxonomie finale imposée

Les théories d'appraisal relient un événement aux réactions affectives via sa signification pour l'individu : pertinence pour buts, congruence, contrôle/coping, agency/responsabilité, normes/valeurs, nouveauté/incertitude figurent parmi les dimensions courantes. Les théories concurrentes diffèrent sur les dimensions et leur ordre.

**Sources :** Scherer (2005), *What are emotions? And how can they be measured?*, Social Science Information, DOI `10.1177/0539018405058216`; Smith & Kirby (2009), *Putting appraisal in context: Toward a relational model of appraisal and emotion*, Cognition and Emotion, DOI `10.1080/02699930902860386`.

**Portée :** le SCC peut employer des dimensions d'évaluation communes comme structure fonctionnelle; il ne doit pas déclarer qu'une théorie unique est « la psychologie vraie ».

### 4.7 [A/B] Source et contenu mémorisé doivent rester distincts

Le source monitoring est un processus reconstructif et faillible; l'origine attribuée à un souvenir dépend d'indices perceptifs et réflexifs et peut être mal attribuée.

**Source :** Johnson, Hashtroudi & Lindsay (1993), *Source monitoring*, Psychological Bulletin, 114, 3–28. DOI `10.1037/0033-2909.114.1.3`.

**Portée :** fondation forte pour préserver `provenance d'audit ≠ source subjectivement remémorée`.

### 4.8 [B] Accessibilité mnésique ≠ existence d'une trace

La récupération dépend des indices et du contexte d'encodage; une information peut devenir difficile à récupérer sans être « supprimée » de façon simple.

**Sources :** Tulving & Thomson (1973), *Encoding Specificity and Retrieval Processes in Episodic Memory*, Psychological Review, 80, 352–373; Bjork & Bjork (1992), *A New Theory of Disuse and an Old Theory of Stimulus Fluctuation*.

**Portée :** soutient un futur mécanisme d'accessibilité/récupération. Ne justifie pas de copier littéralement les variables théoriques de Bjork dans RIC.

---

## 5. Conclusions raisonnables mais incertaines

### [B/C] 5.1 Un « épisode social interprété » est une abstraction utile

La littérature ne fournit pas un objet universel nommé SCC. Pour RIC, il est raisonnable de conserver une unité privée qui relie une ou plusieurs observations sociales à leur interprétation située et à leurs conséquences candidates.

Cette unité doit pouvoir rester :

- ambiguë;
- partielle;
- sans conséquence;
- révisable après nouvelle information;
- différente entre deux observatrices du même événement.

### [B/C] 5.2 L'intention attribuée doit être facultative et incertaine

Un personnage peut penser « elle l'a fait exprès », « accident », « je ne sais pas » ou ne pas juger l'intention pertinente. L'architecture ne doit pas forcer une théorie de l'esprit complète pour chaque interaction.

### [C] 5.3 Les attentes sont une entrée importante mais non obligatoire

Une interaction peut confirmer/violer une attente explicite, une habitude, une limite connue ou une attente relationnelle; beaucoup d'actes n'ont aucune attente saillante. `not_applicable` doit rester une sortie valide.

### [C] 5.4 Les conséquences doivent être indépendantes

Une interprétation peut produire de l'affect sans changement relationnel, une croyance sans émotion forte, une mémoire saillante sans nouvelle croyance, ou rien du tout. Le SCC ne doit pas exiger un « paquet » de conséquences.

---

## 6. Hypothèses de modélisation RIC

Ces choix sont proposés parce qu'ils respectent les résultats ci-dessus et les invariants du projet; ils ne sont pas des lois scientifiques.

1. Une observation sociale peut produire **zéro, un ou plusieurs** épisodes interprétés selon la granularité future.
2. Une interprétation initiale n'est jamais écrasée silencieusement; une réévaluation pointe vers ce qu'elle révise/supersède.
3. Les conséquences sont des **candidates séparées** avant application : affect, croyance/attente, mémoire, objectif/intention, relation.
4. Une attribution d'intention transporte explicitement son incertitude.
5. Une relation globale peut rester un résumé pratique, mais une conséquence relationnelle doit pouvoir remonter à un historique/épisode/domaines justificatifs.
6. L'importance mémorielle et l'importance objective sont distinctes.
7. L'absence de conséquence est un résultat valide.

---

## 7. Contrat fonctionnel cible du SCC

### 7.1 Chaîne conceptuelle

```text
événement / acte social objectivement enregistré
-> accessibilité interactionnelle prouvée pour l'observatrice
-> encodage subjectif
-> interprétation sociale privée et incertaine
-> appraisal / signification située
-> conséquences candidates indépendantes
-> validation par le propriétaire de chaque état
-> éventuelles mises à jour privées
-> récupération/réévaluation ultérieure
```

### 7.2 Entrées minimales d'une interprétation

- observatrice/propriétaire;
- source sociale accessible et son instant vécu;
- actrice, cible explicite éventuelle, participantes;
- contenu exprimé et type d'acte **étiquetés comme expression**;
- état subjectif pertinent autorisé : croyances, limites, valeurs/préférences, but/intention, affect, relation;
- contexte social récent borné;
- souvenirs récupérés pertinents lorsqu'ils existeront;
- source/fiabilité lorsqu'une information rapportée est en jeu.

### 7.3 Sortie fonctionnelle minimale

Les champs exacts et leur stockage restent à décider par Codex, mais le système doit pouvoir représenter :

- contenu compris / incompris / ambigu;
- cible perçue;
- intention attribuée : intentionnelle / accidentelle / incertaine / non pertinente, avec incertitude explicite;
- attente : confirmée / violée / inconnue / non applicable, avec source si disponible;
- domaine social concerné lorsque pertinent;
- pertinence pour but, valeur, préférence ou limite;
- appraisal qualitatif minimal lorsque pertinent;
- conséquences candidates séparées;
- justification/provenance;
- possibilité de révision future.

Aucune conséquence n'est obligatoire et aucun score numérique n'est exigé par la science à ce stade.

---

## 8. Constat de dépôt `0.1.0a15` qui change le séquençage

Le dépôt fournit déjà :

- `SocialSceneService.speak` : persiste une expression structurée (`social_speech_act`) après validation de scène et co-localisation;
- `SceneTurnContextService` : rend les actes récents de la scène accessibles aux participantes dans leur contexte de tour;
- `SubjectiveMemoryService` : encode une trace privée seulement depuis un candidat d'attention d'état ou un événement canonique direct;
- `SocialService` : sait appliquer un impact relationnel borné depuis une trace privée;
- `AffectService` et `BeliefService` : propriétaires contrôlés de leurs états privés;
- tests anti-inférence : parler ne modifie actuellement ni croyance, relation, permission ni affect.

**Lacune immédiate :** il n'existe pas encore de chemin contrôlé qui transforme une parole persistée et effectivement accessible dans une scène en **trace subjective de cette parole**. Une parole peut être visible dans `recent_acts` au prochain tour, mais `SubjectiveMemoryService` ne peut pas en prouver/encoder la source.

Il serait donc prématuré de créer un interpréteur social causal avant d'avoir cette provenance subjective.

---

## 9. Décision de séquençage R&D

### SCC-0 — pont d'encodage social

Premier work order recommandé : permettre l'encodage privé d'un `social_speech_act` réellement accessible à une participante, sans interprétation et sans conséquence.

**Pourquoi maintenant :** cela ferme le trou `expression enregistrée -> source subjective prouvée` tout en conservant tous les contrats anti-inférence.

### SCC-1 — épisode social interprété

Après validation de SCC-0 : introduire le contrat d'interprétation privée/révisable et son audit, d'abord testable avec fournisseur contrôlé. Ne pas encore modifier automatiquement relations/affect/croyances.

### SCC-2 — mémoire minimale et conséquences candidates

Ajouter récupération/condensation minimale pertinente et produire des conséquences candidates indépendantes.

### SCC-3 — raccordement causal borné

Seulement après falsification/acceptation : permettre aux propriétaires d'affect, croyances, intentions et relations d'accepter des conséquences justifiées. Aucun `speech_act -> delta` direct.

Ce séquençage est un **choix de réduction de risque d'ingénierie**, pas une loi scientifique.

---

## 10. Contrat fonctionnel SCC-0

Le premier lot doit offrir le comportement suivant, sans imposer sa plomberie :

1. L'appelant désigne un monde, une observatrice, une scène/un acte social existant et une clé idempotente.
2. Le système relit la parole persistée; il ne fait confiance à aucun payload fourni par l'appelant/LLM.
3. Il prouve que l'observatrice faisait partie de la scène qui a accepté la parole.
4. Sous la sémantique alpha actuelle, toutes les participantes d'une scène ont accès aux paroles acceptées de cette scène, même si `recipient_key` cible une participante. Une cible explicite n'est pas encore un canal privé.
5. Une personne simplement co-présente dans la pièce mais hors de la scène **n'obtient pas** cette parole par magie.
6. La trace encode uniquement le fait d'expression : scène, acte, type d'acte, contenu exprimé, locutrice, destinataire éventuelle, instant de parole et règle d'accès pertinente.
7. Le contenu d'un `inform` reste une assertion prononcée, jamais un fait canonique ni une croyance automatiquement adoptée.
8. La locutrice elle-même peut encoder son propre acte; les autres participantes peuvent encoder l'acte selon la même preuve d'accès.
9. L'encodage doit rester possible après fermeture de la scène si le registre durable suffit à prouver l'accès au moment de la parole; ne pas utiliser la position actuelle pour reconstruire naïvement le passé.
10. Même demande + même source = idempotence; même clé + source différente = refus.
11. Aucun write dans croyance, affect, relation, limite, permission, intention ou canon.
12. Aucun appel LLM et aucun raccordement runtime dans SCC-0.
13. Les chemins existants d'encodage `state` / événement direct continuent de fonctionner inchangés.

### Limite alpha assumée

La scène actuelle sert de frontière d'audibilité. Cette hypothèse est cohérente avec le contexte de scène déjà exposé par le code, mais **n'est pas** une théorie finale de la perception sociale. Le futur lot socio-spatial devra distinguer distance, orientation, audition, porte, whisper, overhearing et privacité.

---

## 11. Scénarios d'acceptation SCC-0

### S0-A — destinataire directe

Sophie parle à Erika dans une scène. Erika peut encoder une trace exacte de l'expression.

**Échec :** la trace invente une croyance ou une conséquence.

### S0-B — participante non ciblée

Scène à trois participantes. Sophie adresse Erika; Luna participe à la scène. Sous le contrat alpha actuel, Luna peut encoder l'expression, mais la trace conserve `recipient=Erika`.

**Échec :** le système transforme « participante » en « destinataire ».

### S0-C — co-présente hors scène

Une résidente est dans le même lieu mais ne participe pas à la scène.

**Attendu :** aucune trace de cette parole par le chemin SCC-0.

### S0-D — propre parole

Sophie peut encoder une trace de ce qu'elle a elle-même effectivement dit.

### S0-E — scène fermée après coup

Une parole a été acceptée lorsque toutes les participantes étaient co-localisées, puis la scène est fermée et les personnages se déplacent.

**Attendu :** l'accès historique peut être prouvé depuis le registre de scène/acte; la position présente ne doit pas rendre rétroactivement la parole inaccessible ou accessible.

### S0-F — payload forgé

Un appelant fournit contenu/locutrice/destinataire différents de la parole stockée.

**Attendu :** le système relit la source réelle ou refuse; il ne persiste jamais le faux payload.

### S0-G — idempotence

Même source + même clé => même trace; même clé + autre acte => conflit explicite.

### S0-H — anti-inférence

Après l'encodage, les comptes/états des croyances, relations, permissions, humeurs et épisodes affectifs sont identiques à avant.

---

## 12. Falsifications du SCC futur

Le modèle devra être considéré fonctionnellement mauvais s'il produit durablement l'un des patterns suivants :

- même type de parole => même conséquence;
- excuse => restauration mécanique;
- relation positive => consentement/permission;
- attribution d'intention toujours certaine;
- toutes les observations accessibles deviennent automatiquement mémorisées/interprétées;
- deux observatrices du même acte construisent toujours la même interprétation;
- les scores relationnels évoluent quasi linéairement avec le nombre d'actes;
- une nouvelle preuve ne permet jamais de réviser une interprétation;
- oubli = suppression uniforme par âge;
- contenu d'une assertion prononcée devient vérité du monde.

---

## 13. Questions laissées volontairement à Codex

Pour SCC-0, Codex doit décider après inspection du dépôt :

- comment étendre la provenance subjective sans créer un second propriétaire de `subjective_trace`;
- si le schéma actuel exige une migration additive et, si oui, sa forme exacte;
- quelle référence stable vers `social_speech_act` préserve le mieux l'intégrité;
- quels index/contraintes/événements d'audit sont requis;
- comment conserver compatibilité avec le prévol, les digests/audits subjectifs et les tests existants.

Si une de ces décisions révèle un conflit d'autorité persistant ou une migration non additive dangereuse, Luna doit arrêter et produire une escalade plutôt que deviner.

---

## 14. Hors SCC-0

Ne pas ajouter dans le premier lot :

- interprétation LLM;
- appraisal automatique;
- émotion automatique;
- croyance automatique;
- delta relationnel automatique;
- consolidation/oubli;
- privacité acoustique fine;
- conversation state avancé;
- Behavioral Opportunity Layer;
- nouvelle taxonomie d'actes;
- comportement CAT-0;
- UI.

---

## Addendum normatif — SCC-2A (10 août 2026)

SCC-0, SCC-1C et SCC-1B sont maintenant vivants. SCC-2A est limité à un
appraisal social situé, privé, owner-scoped et append-only, suivi de zéro ou
plusieurs candidates génériques. Une candidate invite un futur propriétaire à
examiner un domaine; elle ne contient aucune mutation.

Le provider ne produit ni motif, ni intention cachée, ni émotion réelle, ni
vérité sur autrui. Le snapshot est fermé et construit par le moteur à partir
de l'interprétation SCC-1B et d'états propres explicitement disponibles. La
mémoire riche, l'attribution imbriquée et SCC-3 restent différés. Aucune
candidate n'est appliquée dans SCC-2A.

Les statuts, échelles qualitatives, cardinalités, cadence et stockage sont des
choix d'ingénierie falsifiables, pas des lois psychologiques.

## 15. Verdict

**SCC : ALIGNÉ AVEC RÉSERVES, prêt à entrer en implantation par tranches.**

La première tranche ne doit pas « rendre les dialogues plus intelligents ». Elle doit d'abord rendre leur **provenance subjective incontestable**. C'est la plus petite avancée qui ferme un trou réel du dépôt sans fossiliser une psychologie prématurée.
