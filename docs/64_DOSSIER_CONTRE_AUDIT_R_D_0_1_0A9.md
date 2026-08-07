# Dossier de contre-audit R&D — Vivarium social `0.1.0a9`

**Destinataire :** instance ChatGPT chargée de la recherche scientifique et de
la conception fonctionnelle du Vivarium.

**Objet :** vérifier si l'implémentation actuelle respecte les intentions
scientifiques et fonctionnelles du projet, si elle simplifie raisonnablement
les phénomènes étudiés, ou si elle est « à côté de la track ».

**Statut de ce document :** descriptif et interrogatif. Il ne demande pas à
ChatGPT de prescrire les tables SQLite, les classes Python ou la plomberie du
dépôt. Il lui demande d'évaluer les comportements modélisés, les séparations
conceptuelles, les hypothèses et les prédictions attendues.

**Référence logicielle :** `0.1.0a9`, commit `560bce7`, 713 tests réussis.

---

## 1. Mandat donné à ChatGPT

Pour chaque système décrit ci-dessous :

1. déterminer si les concepts sont correctement séparés;
2. déterminer si les relations causales choisies sont défendables;
3. signaler les simplifications acceptables pour une alpha;
4. signaler les simplifications qui risquent de produire des comportements
   artificiels ou trompeurs;
5. distinguer ce qui est robuste, raisonnablement établi, hypothétique ou
   purement choisi pour le design;
6. proposer les comportements émergents qui devraient apparaître si le modèle
   est adéquat;
7. identifier les variables, sources ou mécanismes manquants avant le prochain
   lot;
8. ne proposer une formule numérique que si la littérature la justifie
   réellement; autrement, formuler une contrainte qualitative ou un protocole
   de calibration.

ChatGPT doit pouvoir conclure, pour chaque bloc :

- **ALIGNÉ** : fondation conceptuelle adéquate;
- **ALIGNÉ AVEC RÉSERVES** : fondation utilisable, corrections nécessaires;
- **À REVOIR** : abstraction susceptible de fausser le système futur;
- **INSUFFISAMMENT DOCUMENTÉ** : impossible de trancher sans information ou
  littérature supplémentaire.

## 2. Philosophie et autorité

> **Exécution rigoureuse, création flexible.**

Le moteur garantit les faits, les règles, les conséquences et la mémoire du
monde avec une précision vérifiable. Les personnages interprètent ces faits et
y répondent librement, tant que leurs actions restent possibles et cohérentes.

La frontière centrale est :

```text
réalité canonique
    ↓ rend certains faits accessibles
perception factuelle candidate
    ↓ sélection attentionnelle
trace subjective encodée
    ↓ interprétation
croyance / affect / relation / objectif
    ↓ cadre de décision et options possibles
proposition du LLM
    ↓ validation canonique
action acceptée ou refusée
```

Les flèches ne sont jamais des identités. Notamment :

```text
fait ≠ accessible ≠ remarqué ≠ mémorisé ≠ cru
relation ≠ permission ≠ consentement actuel
trait ≠ émotion ≠ intention ≠ action
texte prononcé ≠ vérité du monde
besoin ≠ motif ≠ désir conscient ≠ objectif
```

Le LLM ne possède aucune écriture directe sur la réalité, les croyances, la
mémoire, l'affect, les relations ou les permissions. Il reçoit un contexte
borné et propose une sortie structurée. Un service contrôlé accepte, adapte ou
refuse cette proposition.

## 3. État réel et portée de l'alpha

Le Vivarium peut actuellement :

- créer atomiquement une résidence et cinq résidentes;
- maintenir un temps canonique persistant en rapport 1:1 avec le temps mural;
- gérer lieux, passages, portes, positions, besoins, activités, blessures,
  ressources, objets et possession;
- calculer les actions spatialement et physiquement disponibles;
- fournir au LLM local une vue factuelle et subjective privée;
- laisser quatre résidentes sapientes choisir une activité disponible;
- ouvrir des scènes sociales co-localisées et enregistrer quelques actes de
  parole;
- persister, reprendre, auditer et arrêter protectivement le monde;
- surveiller l'intégrité après chaque progression canonique et au moins une
  fois par heure.

Ce que l'alpha **ne fait pas encore** :

- produire des conséquences sociales automatiques depuis les dialogues;
- consolider une mémoire narrative, oublier ou reconstruire un souvenir;
- calculer l'appraisal émotionnel ou la dynamique affective;
- arbitrer complètement valeurs, objectifs, intentions et plans multiétapes;
- simuler l'effort physique, les combats, l'économie ou les vêtements;
- donner à Patoune une cognition animale riche;
- gérer un consentement opérationnel complet;
- faire de l'interface actuelle un produit final.

Le monde reste volontairement réinitialisable. La bêta `0.1.0b1` ne sera
atteinte qu'après plusieurs exécutions prolongées sans défaut structurel.

## 4. Casting MVP et fonction expérimentale

Les cinq entités ne cherchent pas à représenter un échantillon humain moyen.
Elles servent à exercer des angles différents du moteur générique.

| Résidente | Nature | Fonction de test actuelle |
| --- | --- | --- |
| Sophie | humaine sapiente | personnalité très réservée/sarcastique, photographie, friction sociale et préférences fortes |
| Erika | humaine sapiente | faible inhibition, vie au jour le jour, jeu vidéo, contraste marqué avec Sophie |
| Luna | louve anthro sapiente | capacités corporelles non humaines, sport, dureté affichée et goûts girly cachés |
| Chuu | slime sapiente | cognition et capacités modulées par une ressource générique d'hydratation |
| Patoune | chatte noire non sapiente | absence valide du composant LLM sapient et futur comportement animal |

Contexte partagé unique : elles se sont portées volontaires pour vivre dans la
résidence, toutes dépenses payées, avec une allocation. Elles n'ont aucune
relation préalable imposée et arrivent près de la boîte aux lettres.

**Question d'audit :** ce casting permet-il réellement de révéler des erreurs
de généralisation, ou risque-t-il surtout d'accumuler des exceptions de design?

## 5. Temps, vérité et persistance

### Logique implantée

- SQLite contient l'état courant et un journal canonique append-only.
- Chaque événement a un ordre `seq`, un instant vécu `occurred_at` et un instant
  technique d'enregistrement `recorded_at`.
- Le monde actif avance en temps réel 1:1; le monde en pause ne rattrape pas le
  temps mural.
- Les besoins et autres quantités continues sont dérivés à la lecture, puis
  matérialisés seulement aux transitions pertinentes.
- Une échéance planifiée est traitée à son instant exact, même si le runtime la
  découvre plus tard.
- Le temps de calcul de Gemma n'est pas automatiquement du temps vécu par le
  personnage qui attend sa réponse.
- Une proposition LLM conserve l'instant et la dernière séquence observés. Si
  le monde a changé pendant l'inférence, la proposition devient périmée et est
  refusée sans écriture.
- Les valeurs fractionnaires sont conservées avec des entiers et des restes
  rationnels; le résultat ne dépend pas de la fréquence des ticks.

### Incidents de rodage déjà observés

Trois régressions temporelles réelles ont été trouvées puis transformées en
tests permanents :

1. une action LLM datée après sa latence pouvait dépasser une échéance encore
   pendante;
2. un retry après réponse invalide pouvait commettre le même défaut;
3. une cible murale capturée 1 ms avant la relecture du temps canonique pouvait
   faire reculer les ancres initiales.

Les bases fautives ont été archivées sans réécriture. Le gardien arrête le
runtime si le journal cesse d'être monotone.

### Questions d'audit

- Séparer le temps de calcul du LLM du temps vécu est-il le bon défaut pour une
  simulation sociale, ou faudrait-il modéliser explicitement une latence de
  décision vécue?
- L'approche événementielle par bornes risque-t-elle de manquer des phénomènes
  continus importants?
- Quelles variables psychologiques devraient évoluer continûment, par seuils,
  ou seulement lors d'événements interprétés?

## 6. Espace, environnement et objets

### Logique implantée

- Un monde est un graphe orienté de lieux et de connecteurs.
- Un connecteur possède un type et un état (`available`, `closed`, `blocked`).
- Une traversée utilise un connecteur concret; le BFS ne constitue qu'une
  proposition de chemin.
- Le déplacement est validé arête par arête et journalisé sans téléportation.
- Une porte verrouillée ou un passage impossible produit un refus; le LLM ne
  peut pas inventer qu'il est passé.
- Lieux et connecteurs proviennent de presets versionnés et de blueprints
  atomiques. Le même système doit pouvoir représenter maison, château, île,
  onsen, ventilation, fenêtre, échelle ou récipient habitable.
- Les objets peuvent être fixes, portables, contenus dans d'autres objets ou
  possédés. Leur lieu effectif est dérivé sans cycle de contenance.
- Un personnage ne se déplace pas pendant une activité active, sauf transition
  explicitement orchestrée.

### Simplifications

- Pas encore de champ visuel, acoustique, obscurité, camouflage ou propagation
  du son.
- Pas de posture, distance intra-pièce, encombrement ou concurrence pour une
  installation.
- Liquides, équipements portés, vêtements et transformations de forme restent
  futurs.

### Questions d'audit

- Le graphe lieu-connecteur est-il une abstraction suffisamment générale sans
  devenir trop grossière pour la perception et les interactions sociales?
- La règle « aucune mobilité pendant une activité active » est-elle un garde
  alpha acceptable ou une mauvaise ontologie de l'activité?
- Quels concepts spatiaux devraient être ajoutés avant les conséquences
  sociales : distance, orientation, visibilité, acoustique, zones privées?

## 7. Besoins, ressources, activités et blessures

### Besoins

Quatre besoins canoniques existent : satiété, repos, énergie et hygiène. Ils
sont des quantités entières bornées avec taux rationnels. Une politique pure
compare leur état à des seuils individuels et choisit une activité de survie ou
un `idle` jusqu'à la prochaine frontière pertinente.

### Ressources génériques

Une ressource peut :

- rendre une capacité disponible, limitée ou indisponible;
- produire des signaux de contexte généraux;
- activer des effets par bandes de valeur.

Ce mécanisme vise autant l'hydratation de Chuu que le mana, les munitions, la
charge d'un androïde, la nicotine ou l'attention sociale d'une influenceuse.
Le moteur n'infère aucune émotion depuis la ressource.

Chuu utilise cette famille : son hydratation peut modifier des capacités de
forme et de cognition ainsi qu'un signal de clarté. Il n'existe aucune branche
`if character == chuu` dans le moteur.

### Activités

- Une seule activité active par personnage.
- Activités physiologiques initiales : `idle`, manger, se reposer, se laver,
  dormir.
- Loisirs alpha : jeu vidéo, photographie, sport, soin girly, télévision,
  socialisation.
- Le moteur calcule les destinations et chemins possibles avant que le LLM
  choisisse.
- Les loisirs durent provisoirement 30 minutes et utilisent encore les taux
  passifs de l'idle. Aucune récompense affective n'est inventée.
- Un nouvel `idle` ouvre une occasion unique de choisir un loisir. Une réponse
  LLM invalide ouvre un retry après cinq minutes, sans appel à chaque tick.

### Blessures

- Une blessure possède une sévérité, une cause et un historique immuable.
- Les régimes passif, repos et sommeil ont des taux de récupération distincts.
- Une blessure modérée augmente le coût du déplacement; une blessure sévère
  empêche le mouvement autonome jusqu'au franchissement exact d'un seuil.
- Aucun système d'effort, de collision ou de combat ne crée encore ces
  blessures dans la vie normale.

### Questions d'audit

- La séparation besoin → signal → motif → option → décision est-elle correcte?
- Les quatre besoins sont-ils suffisants comme socle, ou certains concepts
  essentiels sont-ils artificiellement écrasés ensemble?
- Une ressource unique avec bandes et effets couvre-t-elle correctement les cas
  Chuu/mana/munitions/nicotine, ou mélange-t-elle des familles causalement
  différentes?
- Le déclenchement d'une réflexion à l'entrée en `idle` est-il une approximation
  défendable d'une occasion de décision?
- Quelles prédictions permettraient de détecter que les seuils produisent des
  routines robotiques plutôt qu'une régulation crédible?

## 8. Personnalité, valeurs, préférences, objectifs et intentions

### Personnalité

Les quatre sapientes ont une disposition immuable issue d'un gabarit versionné :

- Big Five continus;
- moyenne, variabilité, inertie et signatures situationnelles par trait;
- anxiété et évitement d'attachement séparés des Big Five.

Patoune n'a pas ce composant. Un trait ne produit aucune action, émotion ou
réplique. Il est exposé comme tendance au LLM et pourra moduler des évaluations.

### Valeurs et préférences

- Douze valeurs sont classées par priorité.
- Une préférence associe une cible et une valence.
- Elles ne constituent ni règle physique, ni consentement, ni ordre d'action.
- Les calibrations actuelles traduisent les fiches de casting; elles sont des
  choix de modélisation, pas des diagnostics psychologiques.

### Objectifs et intentions

- Un objectif subjectif possède origine, cible, conditions de succès,
  faisabilité perçue, importance, urgence et statut.
- Une intention persistante est distincte de l'objectif et représente un plan.
- Une nouvelle intention interrompt l'ancienne sans l'effacer.
- Ces structures existent, mais leur adoption autonome, leur arbitrage et leur
  exécution multiétape ne sont pas encore raccordés complètement.

### Cadre décisionnel actuel

Projection explicative pure :

1. intention active;
2. motif physiologique le plus urgent;
3. objectif le plus urgent puis important;
4. aucune raison dominante.

Ce classement n'exécute rien. Il est fourni au contexte LLM avec les options
réellement possibles.

### Questions d'audit

- La représentation Big Five + attachement général est-elle un socle utile ou
  risque-t-elle de surstructurer la personnalité avant l'apprentissage vécu?
- Moyenne, variabilité et inertie par trait ont-elles un sens psychologique
  défendable, et à quel niveau devraient-elles agir?
- Un classement fixe intention > physiologie > objectif est-il trop rigide?
- Comment intégrer conflits de valeurs, habitudes, impulsions, engagement,
  coût de changement et suffisance sans transformer le LLM en calculatrice?
- Quelles différences émergentes devraient apparaître entre Sophie, Erika,
  Luna et Chuu sans scripts propres à leur identité?

## 9. Perception, attention et mémoire

### Perception factuelle

Une résidente reçoit seulement :

- sa localisation;
- les personnages co-présents;
- les objets visibles au niveau supérieur du lieu;
- les connecteurs adjacents et leur état;
- certains événements qui la concernent directement.

Les besoins, ressources, blessures et états privés d'autrui ne fuient pas.
Cette vue indique l'accessibilité objective, pas la perception consciente.

### Attention déterministe

Les candidats accessibles sont classés avec les signaux internes propres à la
résidente : besoins déficitaires, blessure, capacités affectées par ressource et
signaux contextuels. La liste est stable, bornée et généralement limitée à cinq
éléments. La priorité technique ne dit pas ce que le personnage doit ressentir
ou faire.

### Trace subjective

Une trace encodée conserve une source accessible exacte, sa règle d'accès, son
instant et une fidélité fermée (`complete`, `partial`, `ambiguous`,
`signal_only`). Elle est privée, immuable, sourcée et auditée séparément du
canon. Le service recalcule l'accessibilité au lieu de faire confiance à un
payload fabriqué.

### Mémoire encore absente

- consolidation et condensation;
- oubli comme baisse d'accessibilité;
- souvenirs épisodiques narratifs;
- reconsolidation;
- faux souvenirs;
- rappel associatif ou sémantique;
- perception auditive historique des scènes.

### Questions d'audit

- Une attention initialement déterministe est-elle une bonne frontière de
  sécurité, ou risque-t-elle d'encoder trop tôt une théorie naïve de la
  saillance?
- Les niveaux de fidélité sont-ils suffisants pour servir de provenance à la
  croyance sans feindre une mémoire humaine?
- Quels mécanismes de mémoire sont indispensables avant de laisser les
  conséquences sociales s'accumuler?
- Comment tester l'oubli et la consolidation sans exiger une réplique narrative
  déterministe?

## 10. Croyances et épistémologie subjective

### Logique implantée

- Une croyance appartient à une résidente et porte question, proposition,
  polarité, confiance, visibilité et statut.
- Son adoption exige une trace subjective privée du même personnage.
- La preuve conserve orientation, diagnosticité et fiabilité déclarée.
- Le moteur garantit la provenance, mais ne prétend pas que la trace prouve
  sémantiquement la proposition.
- Une révision crée une nouvelle croyance avant de contester l'ancienne.
- Les croyances restent hors du digest de réalité canonique.
- Le LLM voit ses propres croyances explicitement étiquetées comme telles.

### Manques connus

- hypothèses concurrentes;
- contradictions gérées;
- modèles sociaux de fiabilité des sources;
- dépendances entre preuves;
- coût de révision et acceptation pratique;
- inférences et rumeurs.

### Questions d'audit

- Le contrat de provenance est-il suffisant avant toute interprétation LLM?
- La confiance scalaire risque-t-elle de mélanger confiance dans la perception,
  dans la source et dans l'inférence?
- Quel modèle minimal de contradiction et de sources faut-il avant les rumeurs
  et les conséquences sociales?

## 11. Affect

### Logique implantée

- Une humeur diffuse sépare valence et activation.
- Un épisode émotionnel est ciblé, temporaire et porte famille, appraisal
  structuré, intensité, tendance d'action et expression.
- Plusieurs épisodes peuvent coexister.
- Un épisode exige une trace subjective accessible comme cause.
- Une résolution est journalisée; l'épisode n'est jamais effacé.
- Aucun trait ou besoin ne crée automatiquement une émotion.
- Le LLM voit uniquement l'affect privé de sa résidente et ne peut pas l'écrire.

### Ce qui n'est pas encore implanté

- calcul de l'appraisal;
- évolution temporelle et interaction entre épisodes;
- régulation émotionnelle;
- expression observable par autrui;
- effet causal validé sur l'attention ou la décision.

### Questions d'audit

- Valence/activation pour l'humeur et épisodes à appraisal constituent-ils une
  combinaison théorique cohérente?
- Les familles choisies sont-elles trop discrètes ou adéquates comme vocabulaire
  initial fermé?
- Où doivent se situer personnalité, buts, croyances et normes dans la causalité
  de l'appraisal?
- Quelles dynamiques doivent être déterministes, paramétriques ou interprétées
  par le LLM?

## 12. Relations, limites, permissions et consentement

### Logique implantée

- Toute relation est directionnelle : `A → B` n'implique jamais `B → A`.
- Dimensions séparées : familiarité, confiance, affection, respect, sécurité,
  intimité, attraction et irritation.
- Toute variation est petite, bornée, sourcée par une trace privée et ne peut
  être appliquée deux fois depuis la même source.
- Une limite personnelle possède domaine, portée et état révocable. Elle est un
  fait social, pas nécessairement une barrière physique.
- Une permission est explicite, adressée, limitée, révocable ou expirante.
- Relation, attirance, besoin, ancienne permission ou statut ne valent jamais
  consentement actuel.

### Ce qui manque

- interprétation validée des actes sociaux;
- confiance située par domaine;
- réparation et excuses décomposées;
- perception des transgressions;
- réseau social, réputation et appartenances;
- protocole complet de consentement au moment de l'action.

### Questions d'audit

- Les huit dimensions relationnelles sont-elles conceptuellement distinctes et
  suffisantes, ou certaines devraient être dérivées/contextualisées?
- Une variation scalaire bornée par événement est-elle crédible, ou faut-il
  représenter des épisodes et des attentes relationnelles avant les scores?
- Quel est le lot minimal permettant à une parole d'avoir une conséquence
  sociale sans produire une causalité naïve du type « compliment = +confiance »?

## 13. LLM, autonomie et scènes sociales

### Frontière LLM locale

Gemma 4 12B QAT est appelée par l'API locale de LM Studio. Le contexte est
structuré, privé et borné. Les sorties JSON sont validées. Les adaptations
syntaxiques ne sont acceptées que lorsqu'elles correspondent exactement à une
option déjà calculée par le moteur.

Les appels sont événementiels : arrivée initiale, nouvel `idle`, événement
direct perceptible ou tour de scène. Un ledger technique append-only assure
idempotence, debounce et budget. Une panne du modèle dégrade le tour sans
arrêter le moteur.

### Autonomie actuelle

- Le moteur calcule traversées et activités possibles.
- Le LLM choisit une option ou `no_action`.
- L'action est revérifiée au moment de l'exécution.
- Une activité non-idle active n'est pas interrompue par une réflexion libre.
- Les intentions persistantes ne pilotent pas encore une séquence d'actions.

### Scènes sociales

- Deux à cinq participantes doivent être co-localisées.
- Les scènes ont une borne de quatre tours dans l'alpha.
- Actes fermés : saluer, demander, répondre, informer, offrir, décliner,
  s'excuser, reconnaître, quitter.
- Une parole est enregistrée comme expression, jamais comme vérité.
- Le départ d'une participante invalide la scène.
- Les conversations n'ont encore aucune conséquence relationnelle, mémorielle
  ou affective automatique.

### Symptômes observés

Les premiers dialogues réels sont souvent superficiels : « tu es là? », « oui,
je suis là ». Ce n'est pas une corruption du moteur; c'est une limite de
contexte, d'enjeux, de mémoire et de conséquences.

### Questions d'audit

- L'événementiel actuel déclenche-t-il les décisions aux bons moments?
- Quelles occasions cognitives manquent : réflexion spontanée, interruption,
  réévaluation d'objectif, anticipation, ennui, norme sociale?
- Une scène bornée à quatre tours est-elle un bon garde alpha?
- Que faut-il ajouter avant d'allonger les conversations : mémoire, enjeu,
  appraisal, actes sociaux causaux, objectifs de scène?
- Comment éviter que le LLM joue tous les personnages de façon homogène malgré
  les profils différents?

## 14. Gardien, tests et banc d'essai

### Logique implantée

- 713 tests automatisés couvrent règles locales, migrations, refus, rollback,
  audits et scénarios inter-systèmes.
- Un banc crée des mondes jetables à horloge fixe et compare état, événements,
  refus et digests.
- Le monde vivant n'est jamais utilisé comme base de test destructif.
- Le gardien local vérifie après toute progression canonique et au minimum
  chaque heure : intégrité SQLite, journal, causalité, matérialisation,
  échéances, LM Studio et serveur de contrôle.
- Une alerte critique arrête le runtime sans tenter de réécrire la vérité.
- Les bases fautives sont archivées comme preuves.

### Limite méthodologique

Un grand nombre de tests ne prouve pas que le modèle scientifique est juste.
Il prouve surtout que l'implémentation respecte les contrats que nous avons
choisis. Le présent contre-audit sert précisément à remettre ces contrats en
question avant d'empiler les systèmes vivants.

### Questions d'audit

- Quelles propriétés émergentes devraient être mesurées statistiquement plutôt
  que par tests binaires?
- Quels scénarios discrimineraient une dynamique crédible d'un simple script?
- Quels résultats devraient falsifier un choix de modèle et forcer sa révision?

## 15. Simplifications présentant le plus grand risque

ChatGPT est expressément invité à examiner ces points sans complaisance :

1. classement fixe du cadre décisionnel;
2. attention déterministe par priorités techniques;
3. besoins limités à quatre dimensions;
4. activités uniques, exclusives et peu expressives;
5. loisirs de 30 minutes avec taux passifs identiques;
6. absence de conséquences aux dialogues;
7. dimensions relationnelles scalaires;
8. personnalité déclarative encore peu causale;
9. humeur et émotions stockées mais non dynamiques;
10. mémoire sourcée mais non consolidée;
11. absence de comportement animal réel pour Patoune;
12. abstraction spatiale à l'échelle de la pièce;
13. déclenchement cognitif presque uniquement événementiel;
14. dépendance actuelle à un seul modèle local pendant le rodage.

## 16. Questions prioritaires pour décider le prochain lot

ChatGPT doit répondre en priorité à ces cinq questions :

1. **Le socle actuel contient-il une erreur conceptuelle qui rendrait dangereux
   d'ajouter des conséquences sociales?**
2. **Quel est le plus petit système causal à ajouter pour que les dialogues
   puissent modifier la vie sociale sans règles naïves ou déterministes?**
3. **La mémoire actuelle est-elle suffisamment structurée pour soutenir ce
   système, ou faut-il d'abord implanter consolidation/oubli/modèles de source?**
4. **Le cadre personnalité–valeurs–objectifs–affect–relations est-il correctement
   factorisé?**
5. **Quelles prédictions émergentes et quels scénarios de falsification doivent
   être exigés avant d'accepter le prochain lot dans le monde vivant?**

## 17. Format demandé pour la réponse de ChatGPT

Pour chaque système :

```text
SYSTÈME :
VERDICT : ALIGNÉ | ALIGNÉ AVEC RÉSERVES | À REVOIR | INSUFFISAMMENT DOCUMENTÉ

AFFIRMATIONS :
- [A|B|C|D] affirmation
  provenance scientifique ou design

POINTS CORRECTS :
- ...

RISQUES / ERREURS CONCEPTUELLES :
- ...

CORRECTIONS FONCTIONNELLES RECOMMANDÉES :
- comportement recherché, sans imposer la plomberie

PRÉDICTIONS ÉMERGENTES :
- phénomène attendu

SCÉNARIOS DE FALSIFICATION :
- situation qui montrerait que le modèle échoue

SOURCES PRIMAIRES OU REVUES :
- lien, DOI, portée exacte et limite
```

Échelle de confiance :

- **A — robuste :** convergence empirique forte ou résultat largement établi;
- **B — raisonnablement établi :** littérature favorable avec nuances;
- **C — hypothèse de modélisation :** abstraction nécessaire mais non imposée
  par la science;
- **D — choix de design :** décision assumée pour le type de simulation voulu.

Terminer par :

1. verdict global sur l'architecture conceptuelle;
2. erreurs à corriger avant tout nouveau système;
3. prochain lot R&D recommandé;
4. informations manquantes à demander à Codex ou au propriétaire;
5. liste des éléments qui doivent rester explicitement des choix de design.

## 18. Documents de référence complémentaires

Si ChatGPT reçoit aussi le dépôt ou une archive documentaire, lire en priorité :

- `docs/00_DOSSIER_MAITRE_IA.md` — invariants et architecture;
- `docs/01_REGISTRE_DECISIONS.md` — décisions et provenance;
- `docs/15_ROADMAP_ACTIVE.md` — état et jalons;
- `docs/21_TRAJECTOIRE_VERS_COGNITION.md` — ordre des couches;
- `docs/35_ROUTINE_AUDIT_SILENCIEUX.md` — défauts trouvés et méthode;
- `docs/43_MOTIFS_PHYSIOLOGIQUES.md` à
  `docs/52_ORCHESTRATEUR_AUTONOME.md` — couches subjectives;
- `docs/58_MVP_ALPHA_0_1_0A1.md` à
  `docs/63_CORRECTIF_TEMPS_LLM_0_1_0A6.md` — alpha et rodage;
- `docs/99_PASSATION_COURANTE.md` — passation opérationnelle actuelle.

En cas de contradiction, les décisions récentes, le code validé et la
passation courante prévalent sur un document de tranche historique. La réponse
de ChatGPT reste une proposition R&D jusqu'à audit et adoption explicite.
