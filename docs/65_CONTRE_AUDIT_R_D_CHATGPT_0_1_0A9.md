# Contre-audit R&D scientifique et fonctionnel — Vivarium social `0.1.0a9`

**Auteur du contre-audit :** ChatGPT 5.6 Sol — rôle R&D scientifique et conception fonctionnelle  
**Document audité :** `Vivarium_social_contre-audit_R&D_0.1.0a9.md`  
**Référence logicielle déclarée :** `0.1.0a9`, commit `560bce7`, 713 tests réussis  
**Statut :** proposition R&D documentée, soumise à audit architectural et adoption explicite par Codex / propriétaire  
**Date :** 2026-08-07

---

## 0. Résumé exécutif

### Verdict global

**ALIGNÉ AVEC RÉSERVES.**

Le socle conceptuel du Vivarium est globalement sain et, surtout, les séparations les plus difficiles sont déjà présentes :

- réalité canonique ≠ perception;
- accessibilité ≠ attention;
- trace subjective ≠ croyance;
- croyance ≠ vérité;
- trait ≠ état affectif ≠ intention ≠ action;
- relation ≠ permission ≠ consentement;
- parole ≠ fait du monde;
- objectif ≠ intention;
- moteur de possibilités ≠ choix du personnage.

Ces séparations réduisent fortement le risque de construire un agent social qui confonde génération de texte et simulation du monde. Il n'existe pas, dans le dossier audité, d'erreur conceptuelle fondamentale qui oblige à refondre l'architecture avant de continuer.

En revanche, **quatre simplifications ne doivent pas devenir des fondations permanentes** :

1. le classement fixe `intention > physiologie > objectif`;
2. l'attention principalement déterminée par des priorités techniques;
3. les relations réduites à des dimensions scalaires mises à jour directement par événement;
4. l'absence de consolidation/récupération de mémoire avant l'accumulation de conséquences sociales durables.

Le prochain lot peut donc être un lot de **conséquences sociales minimales**, à condition de ne pas coder une causalité directe `speech_act → relation_delta`. Le lot minimal scientifiquement défendable est plutôt :

```text
acte / événement social accessible
→ trace subjective
→ interprétation sociale située
   - contenu compris
   - cible
   - intention attribuée / ambiguïté
   - attente préalable
   - pertinence pour buts / valeurs / limites
   - source et fiabilité
→ appraisal / signification pour le personnage
→ conséquence immédiate éventuelle
   - émotion / humeur
   - croyance / attente
   - saillance mémorielle
   - intention ou but
→ mise à jour relationnelle contextualisée, si justifiée
→ trace permettant révision ultérieure
```

La littérature sur l'intimité, les violations d'attentes, la confiance et la réparation montre précisément pourquoi le même acte peut produire des effets différents selon le contexte, l'historique, la personne et la manière dont l'acte est interprété.

### Réponse aux cinq questions prioritaires

**1. Le socle actuel contient-il une erreur conceptuelle qui rendrait dangereux d'ajouter des conséquences sociales ?**  
Non. Il contient des simplifications risquées, mais pas d'erreur structurelle fatale. La frontière canonique/subjectif et le caractère proposé du LLM sont de bonnes fondations. Les conséquences sociales deviennent dangereuses seulement si elles sont raccordées directement aux actes de parole ou à des scores relationnels sans interprétation intermédiaire.

**2. Quel est le plus petit système causal à ajouter ?**  
Un **interpréteur social situé** produisant une représentation structurée mais révisable de la signification de l'acte pour le personnage : attente confirmée/violée, valence pour buts/valeurs/limites, intention attribuée avec incertitude, crédibilité de la source, caractère volontaire/perçu, et pertinence relationnelle. Cette interprétation peut ensuite alimenter affect, croyance, mémoire et relation. Le moteur doit garantir la provenance et les bornes, pas imposer l'interprétation humaine exacte.

**3. Faut-il d'abord la mémoire complète ?**  
Pas la mémoire humaine complète. Mais il faut **avant accumulation sociale longue** un minimum de consolidation et de récupération : condensation d'épisodes, accessibilité variable, provenance/source, liens vers personnes/événements et possibilité que les souvenirs deviennent difficiles à récupérer sans être effacés. Les faux souvenirs et la reconsolidation sophistiquée peuvent attendre. Une mémoire purement append-only de traces exactes est trop parfaite pour soutenir des relations vivantes sur la durée.

**4. Le cadre personnalité–valeurs–objectifs–affect–relations est-il bien factorisé ?**  
Oui, avec réserves. Big Five + états situationnels est défendable; attachement doit être traité comme relativement stable mais relation/context-dependent; objectifs et intentions doivent rester séparés; affect ne doit pas être déduit directement des traits; relations ne doivent pas être de simples sommes d'événements. Le classement décisionnel fixe doit être remplacé à terme par un mécanisme de compétition/arbitrage souple.

**5. Quelles prédictions/falsifications exiger ?**  
Le modèle doit produire des tendances, pas des scripts : même acte ≠ même conséquence; effets relationnels asymétriques; habitudes et contextes récurrents réduisant la délibération; attentes violées plus saillantes que confirmations banales; oubli/récupération sélective; divergences croissantes entre personnages exposés à des expériences différentes; régulation anticipatrice des besoins; variabilité intra-personne autour d'une signature stable. Un système qui converge vers des routines périodiques, des réactions identiques ou des scores relationnels monotones doit être considéré comme falsifié fonctionnellement.

---

# 1. Casting MVP et fonction expérimentale

**SYSTÈME :** casting de cinq entités hétérogènes  
**VERDICT : ALIGNÉ AVEC RÉSERVES**

## AFFIRMATIONS

- **[B]** Des agents présentant des contraintes corporelles et cognitives différentes sont utiles pour tester si l'architecture abstrait réellement les mécanismes génériques au lieu d'encoder implicitement un humain moyen.
  - Provenance : méthodologie de modélisation et tests de généralisation; principe de variation contrôlée plutôt que loi psychologique.
- **[C]** Un petit casting extrême est un bon banc de stress architectural, mais ne valide pas la représentativité humaine.
  - Provenance : choix de modélisation.
- **[D]** Sophie, Erika, Luna, Chuu et Patoune sont des instruments de test narratifs choisis pour le projet, pas un échantillon scientifique.

## POINTS CORRECTS

- Le dossier reconnaît explicitement que le casting n'est pas représentatif.
- Chuu et Luna imposent de séparer capacités corporelles et cognition/personnalité.
- Patoune force une absence valide du composant LLM sapient.
- L'absence de branches propres aux identités est une bonne contrainte de généralisation.

## RISQUES / ERREURS CONCEPTUELLES

Le principal risque n'est pas le casting lui-même, mais la création progressive d'« exceptions génériques » qui ne seraient génériques que de nom. Si chaque personnage inhabituel exige une nouvelle variable ad hoc, le moteur deviendra une collection de cas particuliers.

Le casting ne peut pas tester seul :
- variabilité entre personnes ordinaires;
- effet de contextes sociaux différents;
- variations culturelles;
- stabilité sur longue durée.

## CORRECTIONS FONCTIONNELLES RECOMMANDÉES

- Conserver les personnages comme cas de stress.
- Exiger que toute nouvelle mécanique propre à un personnage soit formulée d'abord comme une famille abstraite de contraintes ou capacités.
- Ajouter plus tard des **personnages de contrôle moins extrêmes** pour vérifier qu'un système conçu pour les cas particuliers ne produit pas des humains ordinaires caricaturaux.

## PRÉDICTIONS ÉMERGENTES

- Des différences observables doivent apparaître sans règles `if identity`.
- Les mêmes mécanismes doivent produire des effets différents parce que les états, préférences, capacités et expériences diffèrent.
- Changer une capacité physique devrait modifier les options disponibles sans réécrire arbitrairement la personnalité.

## SCÉNARIOS DE FALSIFICATION

- Une nouvelle résidente humaine standard exige de nombreuses exceptions.
- Les quatre sapientes ont des décisions très semblables malgré leurs profils.
- Les différences de personnage disparaissent dès que le prompt de personnalité est raccourci.
- Une ressource générique produit des interprétations émotionnelles identiques dans tous les cas.

## SOURCES / PORTÉE

Cette section repose surtout sur des principes de modélisation et de falsification; voir la section 14 sur le pattern-oriented modeling.

---

# 2. Temps, vérité et persistance

**SYSTÈME :** temps canonique, latence LLM, événements et quantités continues  
**VERDICT : ALIGNÉ**

## AFFIRMATIONS

- **[A]** Séparer l'ordre causal des événements, leur temps vécu et leur temps d'enregistrement est une bonne pratique conceptuelle pour une simulation événementielle auditable.
  - Provenance : simulation discrète / event sourcing; principe technique.
- **[B]** La cognition humaine n'exige pas qu'un délai de calcul informatique soit équivalent au temps subjectivement vécu.
  - Provenance : abstraction de simulation.
- **[B]** Plusieurs processus biologiques pertinents combinent dynamique continue et transitions par seuils; le sommeil est un exemple classique d'interaction entre processus continus et transitions d'état.
  - Borbély et al., modèle à deux processus du sommeil.
- **[C]** Dans le Vivarium, considérer par défaut la latence LLM comme hors temps vécu est un choix de modélisation acceptable, tant que certaines décisions peuvent avoir une durée diégétique explicite lorsqu'elle est socialement ou physiquement pertinente.

## POINTS CORRECTS

- Journal monotone et append-only.
- Distinction `occurred_at` / `recorded_at`.
- Rejet des propositions périmées.
- Calcul indépendant de la fréquence des ticks.
- Échéances exactes plutôt que dépendance au polling.
- Pause sans rattrapage implicite.
- Archivage des bases fautives au lieu de réécriture.

## RISQUES / ERREURS CONCEPTUELLES

L'erreur serait de conclure que **tout état psychologique doit être un événement discret** parce que le moteur est événementiel.

Certaines variables fonctionnelles gagnent à être représentées comme :
- évoluant continûment ou semi-continûment : pression de sommeil, fatigue physiologique, faim/soif selon le modèle, activation générale;
- évoluant principalement après événements interprétés : confiance, croyances spécifiques, épisode émotionnel;
- hybrides : humeur, accessibilité mnésique, motivation, anticipation.

Le moteur peut néanmoins calculer ces dynamiques de façon analytique entre événements, sans ticks fréquents.

## CORRECTIONS FONCTIONNELLES RECOMMANDÉES

- Maintenir la séparation latence machine / temps vécu.
- Ajouter la possibilité qu'une action de cognition ait **une durée diégétique déclarée** lorsqu'elle monopolise réellement le personnage : hésiter, réfléchir longuement, écrire, observer, attendre quelqu'un.
- Ne pas utiliser une horloge continue comme prétexte pour mettre à jour tous les états à chaque tick.
- Classer chaque future variable selon son régime temporel :
  1. dérivable continûment;
  2. frontière/seuil;
  3. événement interprété;
  4. processus hybride.

## PRÉDICTIONS ÉMERGENTES

- Une même simulation donne le même état canonique quelle que soit la fréquence de polling.
- Un personnage privé de sommeil montre une pression croissante même sans événement discret constant.
- Une émotion peut décroître ou être réactivée sans nécessiter un tick arbitraire.

## SCÉNARIOS DE FALSIFICATION

- Changer le tick-rate change la psychologie finale.
- Le personnage « gèle socialement » pendant une inference alors que le monde continue.
- Des actions sont ordonnées après des conséquences qui auraient dû les empêcher.
- Tous les processus psychologiques évoluent uniquement parce qu'une minuterie les pousse.

## SOURCES

- Borbély AA, Daan S, Wirz-Justice A, Deboer T. *The two-process model of sleep regulation: a reappraisal*. Journal of Sleep Research, 2016. DOI: 10.1111/jsr.12371. https://doi.org/10.1111/jsr.12371
- Borbély AA. *The two-process model of sleep regulation: Beginnings and outlook*. Journal of Sleep Research, 2022. DOI: 10.1111/jsr.13598. https://doi.org/10.1111/jsr.13598
- Sterling P. *Allostasis: a model of predictive regulation*. Physiology & Behavior, 2012. DOI: 10.1016/j.physbeh.2011.06.004. https://doi.org/10.1016/j.physbeh.2011.06.004

---

# 3. Espace, environnement et objets

**SYSTÈME :** graphe de lieux, connecteurs et contenance  
**VERDICT : ALIGNÉ AVEC RÉSERVES**

## AFFIRMATIONS

- **[C]** Un graphe lieu-connecteur est une abstraction appropriée pour la locomotion topologique et les contraintes d'accès.
- **[B]** Pour les interactions sociales, la co-présence dans une même pièce n'est pas équivalente à l'accessibilité perceptive ni à l'engagement social : distance, orientation, visibilité, acoustique et attentes de proximité modifient l'interaction.
  - Provenance : proxémie et expectancy violations.
- **[D]** Une pièce comme unité spatiale minimale est un garde alpha de design, pas une théorie de la perception humaine.

## POINTS CORRECTS

- Traversée concrète vérifiée arête par arête.
- Le BFS n'est qu'une proposition.
- Les objets ont une contenance sans cycles.
- Le graphe est assez général pour des mondes très différents.
- Les contraintes physiques restent canoniques et indépendantes du LLM.

## RISQUES / ERREURS CONCEPTUELLES

**La règle “aucune mobilité pendant activité active” doit rester un garde alpha.** Elle ne décrit pas bien l'ontologie d'une activité humaine : parler en marchant, cuisiner en se déplaçant dans la cuisine, photographier dans plusieurs positions, regarder la télévision tout en mangeant, etc.

Avant les conséquences sociales riches, l'échelle de la pièce devient trop grossière si :
- tout le monde dans la pièce est considéré comme voyant/entendant tout;
- le toucher ou l'intrusion dans l'espace personnel n'a pas de distance;
- une conversation privée est impossible dans une grande pièce;
- orientation et obstacles n'existent pas.

## CORRECTIONS FONCTIONNELLES RECOMMANDÉES

Priorité avant social riche :
1. **accessibilité sensorielle**, pas forcément géométrie continue complète;
2. zones ou relations intra-lieu : proche/loin, visible/non visible, audible/non audible;
3. notion de **privacité / exposition**;
4. orientation seulement lorsqu'elle change réellement l'accessibilité ou le sens social;
5. distance plus fine pour toucher, proximité, intimidation, chuchotement.

Il n'est pas nécessaire de transformer le Vivarium en moteur 3D. Une topologie intra-pièce qualitative peut suffire.

## PRÉDICTIONS ÉMERGENTES

- Deux personnes co-présentes peuvent ne pas avoir la même trace d'un événement.
- Un chuchotement peut être privé.
- Une intrusion spatiale peut être perçue différemment selon relation, attente et contexte.
- Une conversation de groupe peut se fractionner en sous-groupes sans changer de pièce.

## SCÉNARIOS DE FALSIFICATION

- Toute personne dans une pièce sait automatiquement tout ce qui s'y produit.
- Une porte fermée n'affecte pas le son ou la visibilité lorsque ces mécanismes existent.
- Le moteur ne peut représenter une action combinée mobilité + activité.
- Les conséquences sociales de proximité sont identiques indépendamment de l'espace.

## SOURCES

- Burgoon JK. *Expectancy Violations Theory*. International Encyclopedia of Interpersonal Communication, 2015. DOI: 10.1002/9781118540190.wbeic102. https://doi.org/10.1002/9781118540190.wbeic102
- Burgoon JK, Walther JB. *Nonverbal Expectancies and the Evaluative Consequences of Violations*. Human Communication Research, 1990. DOI: 10.1111/j.1468-2958.1990.tb00232.x. https://doi.org/10.1111/j.1468-2958.1990.tb00232.x

---

# 4. Besoins, ressources, activités et blessures

**SYSTÈME :** régulation physiologique, ressources, activités, blessure  
**VERDICT : ALIGNÉ AVEC RÉSERVES**

## AFFIRMATIONS

- **[A]** Les signaux corporels/interoceptifs contribuent à la régulation, à la motivation et aux états affectifs, mais sensation corporelle, besoin, motivation consciente et décision ne sont pas identiques.
  - Craig 2002; Khalsa et al. 2018.
- **[A/B]** La régulation biologique est en partie anticipatrice; un agent crédible ne devrait pas attendre systématiquement le franchissement d'un seuil critique avant d'agir.
  - Sterling 2012; Schulkin & Sterling 2019.
- **[A]** Le sommeil n'est pas correctement représenté comme un simple niveau monotone unique; le modèle à deux processus distingue au minimum pression homéostatique et rythme circadien.
- **[B]** Le besoin d'appartenance/socialité est une motivation humaine importante, mais il ne doit pas nécessairement être canonisé comme une jauge simple analogue à la faim.
  - Baumeister & Leary 1995.
- **[B/C]** Autonomie, compétence et relatedness de la Self-Determination Theory sont utiles pour expliquer la qualité motivationnelle et le bien-être, mais ne doivent pas être traduites naïvement en trois barres obligatoires.

## POINTS CORRECTS

La chaîne :

```text
état corporel
→ signal
→ motif
→ option
→ décision
```

est conceptuellement bonne.

La ressource générique est également saine si elle signifie seulement « quantité ou condition qui contraint capacités/possibilités ». Le moteur a raison de ne pas déduire automatiquement une émotion de cette ressource.

## RISQUES / ERREURS CONCEPTUELLES

Les quatre besoins actuels sont suffisants **pour une alpha physique**, mais pas comme théorie générale de motivation.

Points à revoir plus tard :
- `repos` et `énergie` risquent de recouvrir partiellement sommeil, fatigue, effort et activation;
- la satiété seule peut masquer faim, soif et autres régulations;
- l'hygiène est fortement normative/sociale et moins directement homéostatique que sommeil/nutrition;
- les seuils purs produiront des comportements oscillatoires si le personnage ne peut anticiper.

Une seule classe « resource » peut être acceptable au niveau stockage/capacité, mais **ses sémantiques causales ne sont pas interchangeables** :
- munitions = inventaire discret externe;
- nicotine = substance avec effets pharmacologiques, dépendance et retrait;
- mana = ressource fictionnelle;
- hydratation de Chuu = état corporel;
- attention sociale d'une influenceuse = variable sociale/psychologique construite.

Le danger n'est pas une abstraction de données commune; c'est une logique causale commune.

## CORRECTIONS FONCTIONNELLES RECOMMANDÉES

- Conserver quatre besoins pour l'alpha, mais ne pas les présenter comme liste exhaustive des « besoins humains ».
- Introduire à terme **anticipation / préemption** : agir avant seuil selon projection, contexte et coût d'opportunité.
- Pour le sommeil, planifier une séparation pression de sommeil / phase circadienne avant simulation physiologique fine.
- Permettre activités concurrentes ou imbriquées plus tard; l'exclusivité actuelle est un garde alpha.
- Distinguer les familles de ressources par **mécanisme causal**, même si elles partagent une interface générique.

## PRÉDICTIONS ÉMERGENTES

Un bon modèle de régulation devrait produire :
- prise de nourriture ou repos avant urgence absolue;
- variation selon opportunités futures;
- report temporaire d'un besoin lorsque l'objectif/context est important;
- reprise du besoin après l'interruption;
- routines approximatives mais non périodicité parfaite;
- différences individuelles de tolérance et anticipation.

## SCÉNARIOS DE FALSIFICATION

- Chaque personnage mange précisément au même seuil.
- Une journée se transforme en cycle régulier `idle → seuil → réparation → idle`.
- Les besoins plus élevés n'influencent jamais une décision avant seuil.
- « énergie » et « repos » évoluent de façon indiscernable.
- Une ressource de munitions influence cognition de la même manière qu'une hydratation corporelle.

## SOURCES

- Craig AD. *How do you feel? Interoception: the sense of the physiological condition of the body*. Nature Reviews Neuroscience, 2002. DOI: 10.1038/nrn894. https://doi.org/10.1038/nrn894
- Khalsa SS et al. *Interoception and Mental Health: A Roadmap*. Biol Psychiatry Cogn Neurosci Neuroimaging, 2018. DOI: 10.1016/j.bpsc.2017.12.004. https://doi.org/10.1016/j.bpsc.2017.12.004
- Sterling P. *Allostasis: a model of predictive regulation*. Physiology & Behavior, 2012. DOI: 10.1016/j.physbeh.2011.06.004. https://doi.org/10.1016/j.physbeh.2011.06.004
- Schulkin J, Sterling P. *Allostasis: A Brain-Centered, Predictive Mode of Physiological Regulation*. Trends in Neurosciences, 2019. DOI: 10.1016/j.tins.2019.07.010. https://doi.org/10.1016/j.tins.2019.07.010
- Baumeister RF, Leary MR. *The need to belong*. Psychological Bulletin, 1995. DOI: 10.1037/0033-2909.117.3.497. https://doi.org/10.1037/0033-2909.117.3.497
- Borbély AA et al. 2016, op. cit.

---

# 5. Personnalité, valeurs, préférences, objectifs et intentions

**SYSTÈME :** dispositions, états, motivation délibérée et planification  
**VERDICT : ALIGNÉ AVEC RÉSERVES**

## AFFIRMATIONS

- **[A/B]** Le Big Five est un cadre descriptif très établi pour les différences individuelles, mais un score de trait ne doit pas être utilisé comme moteur direct d'actions.
- **[A/B]** Les comportements correspondant aux traits varient fortement intra-individuellement selon les situations; la Whole Trait Theory représente les traits descriptivement comme distributions d'états et cherche des mécanismes sociaux-cognitifs pour expliquer ces variations.
  - Fleeson & Jayawickreme 2015.
- **[B]** Les dimensions d'attachement adulte anxiété/évitement sont utiles mais montrent à la fois stabilité et variation selon relation/temps.
  - Fraley & Shaver 2000; Fraley et al. 2011.
- **[A/B]** But et intention ne garantissent pas l'action; les habitudes, indices contextuels et implementation intentions montrent que l'action peut être déclenchée par des structures différentes de la délibération présente.
  - Gollwitzer 1999; Wood & Rünger 2016.

## POINTS CORRECTS

- Big Five continus plutôt que catégories.
- Traits ne produisent pas directement réplique/émotion/action.
- Valeurs et préférences distinctes des règles physiques et du consentement.
- Objectif distinct de l'intention persistante.
- L'intention peut être interrompue sans être effacée.
- Le moteur expose les options possibles plutôt que permettre au LLM d'en inventer.

## RISQUES / ERREURS CONCEPTUELLES

### Moyenne, variabilité, inertie

**Moyenne + variabilité** est défendable comme description des états de trait.  
**Inertie propre à chaque trait** est plus hypothétique. Une inertie peut être utile pour éviter des sauts arbitraires, mais il ne faut pas lui donner le statut d'un fait établi du Big Five. Elle devrait agir sur la dynamique des états ou sur la continuité comportementale, pas « ralentir » la personnalité abstraite elle-même.

### Attachement

L'attachement ne devrait pas être seulement un attribut global immuable. Une composante générale peut exister, mais des représentations ou attentes spécifiques à une relation doivent pouvoir diverger.

### Cadre décisionnel fixe

`intention > physiologie > objectif` est **À REVOIR comme politique permanente**.

Il est acceptable comme projection alpha explicative, mais humainement :
- une urgence physiologique peut interrompre une intention;
- une habitude peut s'exécuter sans objectif actif;
- un stimulus saillant peut provoquer réorientation;
- un coût de changement peut maintenir l'activité actuelle;
- une impulsion peut concurrencer un plan;
- une norme sociale peut inhiber une option;
- une action « suffisamment bonne » peut être choisie sans maximisation.

Le LLM ne doit pas devenir une calculatrice, mais le moteur peut présenter une **configuration de motifs concurrents** plutôt qu'un gagnant décidé par ordre fixe.

## CORRECTIONS FONCTIONNELLES RECOMMANDÉES

À terme, remplacer le classement fixe par un cadre fonctionnel comprenant :
- motifs actifs;
- urgence/importance;
- faisabilité;
- engagement/intention déjà active;
- coût d'interruption / coût de changement;
- habitudes/cues;
- anticipation;
- normes/permissions;
- affect et saillance;
- possibilité de report;
- seuil de suffisance plutôt que maximisation obligatoire.

Le moteur peut calculer les contraintes et les facteurs; le LLM peut arbitrer quand plusieurs options restent plausibles.

## PRÉDICTIONS ÉMERGENTES

- Sophie doit présenter une distribution de comportements plus réservés sans être réservée à chaque interaction.
- Erika peut agir plus spontanément sans être systématiquement impulsive.
- Luna doit pouvoir manifester des goûts cachés dans les contextes où leur expression est sûre, pas via un script « révéler le secret ».
- Chuu doit varier lorsque son état corporel change, sans que son identité psychologique soit remplacée par une règle de ressource.
- Les personnes doivent parfois persister dans une activité malgré un motif concurrent à cause du coût de changement ou d'une intention forte.
- Des habitudes contextuelles doivent réduire la fréquence de délibération au fil des répétitions.

## SCÉNARIOS DE FALSIFICATION

- Un trait élevé prédit la même conduite dans toutes les situations.
- Deux personnages aux expériences différentes gardent des comportements identiques car leur template est immuable.
- Toute intention active gagne toujours contre la faim, la peur, une limite sociale ou une urgence.
- Chaque décision exige un nouvel appel LLM même pour une habitude stable.
- Les traits deviennent un multiplicateur numérique universel de décision.

## SOURCES

- Fleeson W, Jayawickreme E. *Whole Trait Theory*. Journal of Research in Personality, 2015, 56:82–92. DOI: 10.1016/j.jrp.2014.10.009. https://doi.org/10.1016/j.jrp.2014.10.009
- Fleeson W, Law MK. *TraitEnactments as Density Distributions*. JPSP, 2015. DOI: 10.1037/a0039517. https://doi.org/10.1037/a0039517
- Fraley RC, Shaver PR. *Adult Romantic Attachment: Theoretical Developments, Emerging Controversies, and Unanswered Questions*. Review of General Psychology, 2000. DOI: 10.1037/1089-2680.4.2.132. https://doi.org/10.1037/1089-2680.4.2.132
- Fraley RC et al. *Patterns of stability in adult attachment*. JPSP, 2011. DOI: 10.1037/a0024150. https://doi.org/10.1037/a0024150
- Gollwitzer PM. *Implementation intentions: Strong effects of simple plans*. American Psychologist, 1999. DOI: 10.1037/0003-066X.54.7.493. https://doi.org/10.1037/0003-066X.54.7.493
- Wood W, Rünger D. *Psychology of Habit*. Annual Review of Psychology, 2016. DOI: 10.1146/annurev-psych-122414-033417. https://doi.org/10.1146/annurev-psych-122414-033417

---

# 6. Perception, attention et mémoire

**SYSTÈME :** accessibilité, sélection attentionnelle, traces et mémoire  
**VERDICT : ALIGNÉ AVEC RÉSERVES**

## AFFIRMATIONS

- **[A]** Attention et accessibilité perceptive sont distinctes; tout stimulus accessible n'est pas sélectionné.
- **[A/B]** La sélection attentionnelle ne se réduit pas à « bottom-up salience + top-down goals » : l'historique de sélection et la valeur apprise peuvent aussi biaiser l'attention.
  - Awh, Belopolsky & Theeuwes 2012; Anderson 2013.
- **[A]** La provenance/source est fondamentale pour distinguer mémoire de la perception, de l'imagination et de l'information reçue.
  - Johnson, Hashtroudi & Lindsay 1993.
- **[A/B]** La mémoire humaine n'est ni un journal exact ni une simple base de données; consolidation, accessibilité et interférence modifient ce qui est récupéré.
  - Rasch & Born 2013; littérature source-monitoring.
- **[B]** La reconsolidation humaine est plausible dans certains paradigmes mais demeure conditionnelle et débattue; elle ne doit pas être simulée comme règle universelle « chaque rappel réécrit le souvenir ».
  - Elsey, Van Ast & Kindt 2018.

## POINTS CORRECTS

- Excellente séparation `accessible → attention → trace`.
- Trace privée, sourcée, immuable : très bonne fondation d'audit.
- Le service recalcule l'accessibilité au lieu de croire le payload du LLM.
- Fidelity fermée utile comme qualité de captation, si elle reste une propriété de la trace et non de la mémoire entière.

## RISQUES / ERREURS CONCEPTUELLES

### Attention déterministe

La détermination technique est acceptable pour une alpha **comme garde de sécurité**, mais pas comme théorie de saillance.

Une attention réaliste doit pouvoir être influencée par :
- buts actifs;
- menace / nouveauté;
- valeur apprise;
- habitudes de sélection;
- état corporel;
- émotion;
- attentes;
- pertinence sociale;
- caractéristiques perceptives;
- charge cognitive.

Le top-5 fixe peut faire disparaître systématiquement un élément pourtant socialement important.

### Fidélité

`complete / partial / ambiguous / signal_only` est une bonne provenance de **l'encodage initial**, mais ne doit pas devenir une mesure unique de « qualité du souvenir ». Il faut distinguer :
- qualité de la perception initiale;
- accessibilité ultérieure;
- confiance subjective;
- source attribuée;
- contenu reconstruit.

### Mémoire minimale avant social durable

Il faut ajouter avant accumulation relationnelle longue :
- consolidation/condensation;
- accessibilité variable;
- récupération par indices;
- source/provenance;
- liens entre épisode, personnes et thème;
- possibilité de résumer plusieurs épisodes récurrents.

Pas nécessaire au premier lot :
- faux souvenirs sophistiqués;
- reconsolidation biologique détaillée;
- mémoire sémantique générale complète.

## CORRECTIONS FONCTIONNELLES RECOMMANDÉES

Conserver la trace exacte comme **preuve du moteur**. Construire par-dessus une mémoire subjective distincte qui peut :
- être dérivée d'une ou plusieurs traces;
- devenir plus ou moins accessible;
- condenser plusieurs épisodes;
- perdre certains détails;
- garder une provenance approximative;
- être récupérée selon le contexte.

Le journal exact ne doit jamais être « oublié » par le moteur; c'est l'agent qui perd l'accès.

## PRÉDICTIONS ÉMERGENTES

- Deux personnages présents au même événement n'en gardent pas nécessairement la même mémoire.
- Un événement inhabituel/important est plus accessible qu'une répétition banale.
- Des routines similaires se condensent.
- Une information non rappelée depuis longtemps peut rester récupérable avec un indice approprié.
- Un détail initialement ambigu ne devient pas magiquement certain avec le temps.
- Les souvenirs socialement importants réapparaissent dans des contextes liés.

## SCÉNARIOS DE FALSIFICATION

- Les personnages rappellent toujours exactement les traces canoniques.
- Tout ce qui est accessible est encodé.
- Les cinq mêmes types de stimuli capturent toujours l'attention.
- La mémoire se réduit à une suppression temporelle uniforme.
- Rappeler un souvenir le rend automatiquement faux ou modifié.

## SOURCES

- Awh E, Belopolsky AV, Theeuwes J. *Top-down versus bottom-up attentional control: a failed theoretical dichotomy*. Trends in Cognitive Sciences, 2012. DOI: 10.1016/j.tics.2012.06.010. https://doi.org/10.1016/j.tics.2012.06.010
- Anderson BA. *A value-driven mechanism of attentional selection*. Journal of Vision, 2013. DOI: 10.1167/13.3.7. https://doi.org/10.1167/13.3.7
- Johnson MK, Hashtroudi S, Lindsay DS. *Source monitoring*. Psychological Bulletin, 1993. DOI: 10.1037/0033-2909.114.1.3. https://doi.org/10.1037/0033-2909.114.1.3
- Rasch B, Born J. *About Sleep's Role in Memory*. Physiological Reviews, 2013. DOI: 10.1152/physrev.00032.2012. https://doi.org/10.1152/physrev.00032.2012
- Elsey JWB, Van Ast VA, Kindt M. *Human memory reconsolidation: A guiding framework and critical review of the evidence*. Psychological Bulletin, 2018. DOI: 10.1037/bul0000152. https://doi.org/10.1037/bul0000152

---

# 7. Croyances et épistémologie subjective

**SYSTÈME :** croyances, preuves, confiance et révision  
**VERDICT : ALIGNÉ AVEC RÉSERVES**

## AFFIRMATIONS

- **[A/B]** Les humains tiennent compte de la fiabilité des sources dans la mise à jour des croyances, mais ce processus n'est ni parfait ni réductible à une confiance scalaire unique.
- **[A]** Source de l'information, qualité perceptive et inférence sont des dimensions conceptuellement distinctes.
- **[C]** Une croyance structurée par proposition/polarité/confiance est une abstraction de simulation raisonnable, mais ne doit pas prétendre reproduire une probabilité bayésienne humaine exacte.

## POINTS CORRECTS

- Une croyance n'écrit jamais le canon.
- Provenance privée obligatoire.
- Le moteur ne prétend pas qu'une trace prouve sémantiquement la proposition.
- Révision append-only plutôt qu'écrasement.
- L'étiquette « croyance » dans le contexte LLM réduit la confusion avec les faits.

## RISQUES / ERREURS CONCEPTUELLES

Une confiance scalaire unique peut mélanger :
- confiance que j'ai réellement vu/entendu quelque chose;
- confiance dans le témoin/source;
- diagnosticité de l'information pour la conclusion;
- confiance dans ma propre inférence;
- confiance dans la stabilité de la situation.

Avant rumeurs et conséquences sociales, il faut pouvoir représenter au minimum :
1. **qui est la source**;
2. **comment l'information a été obtenue**;
3. **fiabilité perçue de cette source pour le domaine**;
4. **supporte / contredit / est compatible**;
5. coexistence de propositions concurrentes.

## CORRECTIONS FONCTIONNELLES RECOMMANDÉES

Ne pas chercher à imposer un calcul bayésien complet. Garantir plutôt :
- provenance;
- séparation des niveaux de confiance;
- contradictions explicites;
- possibilité de suspendre le jugement;
- possibilité de réviser la fiabilité d'une source après erreurs/corrections.

## PRÉDICTIONS ÉMERGENTES

- Deux personnages exposés au même témoignage peuvent avoir des croyances différentes à cause de leur historique avec la source.
- Une correction provenant d'une source fiable peut réduire une croyance sans forcément l'annuler.
- Une source souvent contredite perd de la crédibilité.
- Une croyance peut rester ambiguë lorsqu'aucune hypothèse ne domine.

## SCÉNARIOS DE FALSIFICATION

- Une rumeur devient automatiquement vraie subjectivement dès qu'une trace existe.
- Toutes les preuves s'additionnent indépendamment.
- Une confiance à 0.8 signifie à la fois bonne vision, source fiable et bonne inférence.
- Une contradiction force toujours immédiatement le remplacement de l'ancienne croyance.

## SOURCES

- Johnson et al. 1993, op. cit.
- Sanna GA, Lagnado D. *Belief updating in the face of misinformation: The role of source reliability*. Cognition, 2025, 258:106090. DOI: 10.1016/j.cognition.2025.106090. https://doi.org/10.1016/j.cognition.2025.106090

---

# 8. Affect

**SYSTÈME :** humeur dimensionnelle, épisodes émotionnels et appraisal  
**VERDICT : ALIGNÉ**

## AFFIRMATIONS

- **[A/B]** Valence et activation/arousal constituent une représentation classique et empirique de l'affect général.
  - Russell 1980.
- **[B]** Les théories d'appraisal représentent les émotions comme dépendant de l'évaluation de la signification d'un événement pour les buts, capacités, normes, causes, etc.; elles sont particulièrement adaptées à une simulation où le même fait doit pouvoir provoquer des émotions différentes.
  - Scherer 2001/2005.
- **[B]** Il est conceptuellement utile de distinguer affect diffus, épisode émotionnel, tendance d'action, expression et sentiment subjectif.
- **[C]** Une taxonomie fermée de familles émotionnelles peut être utile comme vocabulaire alpha, mais ne doit pas être présentée comme liste scientifiquement définitive.

## POINTS CORRECTS

- Humeur diffuse séparée des épisodes ciblés.
- Plusieurs épisodes simultanés.
- Cause reliée à une trace subjective plutôt qu'au canon omniscient.
- Épisodes jamais effacés historiquement.
- Pas de `trait -> emotion`.
- Affect privé.

## RISQUES / ERREURS CONCEPTUELLES

Le danger principal serait de faire de l'appraisal un mapping :
`event_type → emotion_family`.

Les facteurs pertinents incluent au minimum :
- nouveauté;
- pertinence pour un but;
- congruence/incongruence;
- contrôle/coping potentiel;
- responsabilité/agency;
- normes/valeurs;
- attentes;
- croyances sur les conséquences.

Les traits peuvent **moduler** les appraisals ou la régulation, mais ne doivent pas produire directement une émotion.

Le LLM est probablement utile pour l'interprétation riche et ambiguë, mais l'intensité numérique exacte ne devrait pas être crue sur parole : les travaux récents sur LLM et appraisal montrent une capacité intéressante à raisonner sur certaines appraisals, mais des difficultés sur intensité/coping.

## CORRECTIONS FONCTIONNELLES RECOMMANDÉES

Répartition proposée :

**Moteur garantit**
- événement/trace source;
- variables factuelles nécessaires;
- bornes;
- décroissance ou évolution paramétrique une fois l'épisode créé;
- impossibilités physiques;
- provenance.

**LLM peut proposer**
- interprétation/appraisal ambigu;
- émotion/famille plausible;
- tendance d'action;
- expression voulue;
- coping narratif.

**Service contrôlé**
- valide cohérence;
- refuse contradiction avec croyances/trace;
- borne intensité;
- évite multiplication d'épisodes identiques.

## PRÉDICTIONS ÉMERGENTES

- Même événement, appraisals différents → émotions différentes.
- Un obstacle contrôlable et un obstacle incontrôlable n'entraînent pas les mêmes tendances.
- Une émotion peut persister après disparition du stimulus puis décroître.
- Plusieurs émotions peuvent coexister lors d'événements ambivalents.
- Humeur et épisodes peuvent s'influencer sans être identiques.

## SCÉNARIOS DE FALSIFICATION

- Toute insulte crée la même colère.
- Toute perte crée la même tristesse.
- Un trait élevé suffit à créer une émotion en absence d'événement/appraisal.
- L'humeur devient une moyenne mécanique des émotions sans dynamique propre.
- Le LLM peut déclarer arbitrairement « elle est terrifiée » sans cause subjective accessible.

## SOURCES

- Russell JA. *A circumplex model of affect*. JPSP, 1980. DOI: 10.1037/h0077714. https://doi.org/10.1037/h0077714
- Scherer KR. *Appraisal Processes in Emotion: Theory, Methods, Research*. Oxford University Press, 2001. DOI: 10.1093/oso/9780195130072.001.0001
- Scherer KR. *What are emotions? And how can they be measured?* Social Science Information, 2005. DOI: 10.1177/0539018405058216. https://doi.org/10.1177/0539018405058216
- Tak AN, Gratch J. *Is GPT a Computational Model of Emotion? Detailed Analysis*. 2023 preprint. Utilité limitée : LLM capable de certaines inférences d'appraisal, moins fiable pour intensité/coping. https://arxiv.org/abs/2307.13779

---

# 9. Relations, limites, permissions et consentement

**SYSTÈME :** états relationnels directionnels et conséquences sociales  
**VERDICT : ALIGNÉ AVEC RÉSERVES**

## AFFIRMATIONS

- **[A/B]** Les relations sont asymétriques : A peut faire confiance à B plus que B ne fait confiance à A.
- **[A/B]** La confiance est située : elle concerne un acteur, une cible, une matière/enjeu et une incertitude; un score global unique est souvent insuffisant.
  - Robbins 2016.
- **[A/B]** L'intimité se développe comme un processus interactionnel impliquant divulgation et perception de la réactivité/compréhension du partenaire; elle n'est pas simplement un compteur d'actes positifs.
  - Laurenceau, Barrett & Pietromonaco 1998, test du modèle Reis-Shaver.
- **[B]** Une violation d'attente doit être interprétée : la même déviation peut être positive ou négative selon la personne, la relation et le contexte.
  - Burgoon EVT.
- **[A/B]** Les excuses peuvent réparer la confiance en moyenne, mais l'effet dépend du type de transgression, du contexte et des mécanismes d'interprétation; `apology = +trust` est faux.
- **[A]** Relation, attirance, besoin, passé relationnel et permission antérieure ne constituent pas un consentement actuel.

## POINTS CORRECTS

- Directionnalité.
- Séparation relation / limites / permissions / consentement.
- Révocabilité.
- Petite variation bornée et provenance.
- Une source ne peut être appliquée deux fois.
- Aucun statut n'implique consentement.

## RISQUES / ERREURS CONCEPTUELLES

Les huit dimensions sont utiles comme **résumé d'état**, mais elles risquent d'être surinterprétées si le moteur les met à jour directement depuis les actes.

Certaines dimensions sont contextuelles :
- confiance en compétence ≠ confiance en discrétion ≠ confiance en intentions;
- sécurité peut être physique, émotionnelle, sociale;
- intimité peut varier par domaine;
- respect peut être normatif, compétence, statut, réciprocité.

Les scores doivent donc être des **résumés dérivés d'histoires et attentes**, pas la totalité de l'histoire relationnelle.

## CORRECTIONS FONCTIONNELLES RECOMMANDÉES

Avant d'appliquer des deltas relationnels, introduire un objet fonctionnel d'**épisode social interprété** contenant au minimum :
- acte observé;
- cible;
- contexte;
- attente concernée;
- attribution d'intention / ambiguïté;
- domaine relationnel;
- pertinence pour valeur/limite/but;
- appraisal;
- résultat observé;
- possibilité de réparation.

La relation peut ensuite être modifiée de façon petite et bornée si l'épisode fournit une justification.

**Ne pas dériver toutes les dimensions.** Certaines peuvent rester state summaries explicites. Mais le système doit permettre des états comme :
- « je lui fais confiance pour cuisiner, pas pour garder un secret »;
- « je l'aime mais je ne me sens pas en sécurité avec elle »;
- « je suis attirée mais je ne veux pas de contact aujourd'hui ».

## PRÉDICTIONS ÉMERGENTES

- Un même compliment peut plaire, gêner ou sembler manipulateur.
- Une excuse sincère après accident peut réparer davantage qu'après violation répétée.
- Une bonne relation peut tolérer une petite violation sans effondrement.
- Une série cohérente d'interactions peut modifier progressivement une attente.
- A→B et B→A divergent.
- Une limite explicitement communiquée peut changer l'interprétation d'un acte ultérieur.

## SCÉNARIOS DE FALSIFICATION

- `compliment = +affection`.
- `apology = +trust`.
- `insult = -respect` avec delta identique pour tous.
- Les scores suffisent à reconstruire entièrement la relation.
- Une relation positive augmente automatiquement les permissions ou le consentement.

## SOURCES

- Robbins BG. *What is Trust? A Multidisciplinary Review, Critique, and Synthesis*. Sociology Compass, 2016. DOI: 10.1111/soc4.12391. https://doi.org/10.1111/soc4.12391
- Laurenceau JP, Barrett LF, Pietromonaco PR. *Intimacy as an interpersonal process*. JPSP, 1998. DOI: 10.1037/0022-3514.74.5.1238. https://doi.org/10.1037/0022-3514.74.5.1238
- Burgoon 2015, op. cit.
- Yuan B, Dong Y, Li W. *The trust repair effect of apology: A systematic review and meta-analysis*. Advances in Psychological Science, 2017. DOI: 10.3724/SP.J.1042.2017.01103. https://doi.org/10.3724/SP.J.1042.2017.01103
- Ma F et al. *Apologies Repair Trust via Perceived Trustworthiness and Negative Emotions*. Frontiers in Psychology, 2019. DOI: 10.3389/fpsyg.2019.00758. https://doi.org/10.3389/fpsyg.2019.00758

---

# 10. LLM, autonomie et scènes sociales

**SYSTÈME :** LLM comme proposeur borné et conversations sociales  
**VERDICT : ALIGNÉ AVEC RÉSERVES**

## AFFIRMATIONS

- **[C/D]** Le découpage moteur-déterministe / LLM-proposeur est une architecture de sûreté et de cohérence adaptée au projet.
- **[A/B]** Les habitudes et plans montrent que les occasions de décision ne se limitent pas à un état `idle`.
- **[B]** Les interactions sociales deviennent significatives lorsqu'elles sont liées à buts, attentes, mémoire et conséquences; la simple génération de tours de parole ne suffit pas à créer une dynamique relationnelle.

## POINTS CORRECTS

- Le LLM ne choisit que parmi des options réellement possibles.
- JSON validé, stale-check, idempotence, debounce et budget.
- Une panne du modèle ne détruit pas le monde.
- Le texte prononcé n'est pas vérité.
- Les scènes exigent co-localisation.
- Le départ invalide la scène.
- Une limite de quatre tours est un garde alpha raisonnable.

## RISQUES / ERREURS CONCEPTUELLES

### Déclenchement cognitif

L'événementiel est bon, mais les **occasions** sont trop rares.

Il manque :
- anticipation d'une échéance;
- réévaluation d'un plan;
- interruption par événement important;
- réflexion spontanée à faible fréquence;
- ennui / manque de stimulation;
- conflit entre intention et contexte;
- norme sociale (« quelqu'un entre, dois-je saluer ? »);
- rappel mnésique déclenché par indice;
- opportunité inattendue;
- changement corporel avant seuil critique.

### Quatre tours

Conserver quatre tours tant que les conversations sont pauvres. **Allonger maintenant ne résoudrait rien** et augmenterait seulement le coût et le bavardage. D'abord :
1. enjeu ou but de scène;
2. mémoire;
3. appraisal;
4. conséquences;
5. raisons de continuer ou quitter.

### Homogénéité du LLM

Ne pas compter uniquement sur un prompt de caractère. Les profils doivent influencer les **entrées fonctionnelles** : attentes, croyances, buts, limites, souvenirs, affect, habitudes, style de communication. C'est leur histoire différente qui doit finir par produire le caractère, pas seulement une fiche.

## CORRECTIONS FONCTIONNELLES RECOMMANDÉES

Créer un ensemble d'**occasions cognitives** plutôt qu'un polling mental :
- événement externe pertinent;
- frontière physiologique anticipée;
- fin/début d'activité;
- cue d'intention;
- conflit/obstacle;
- changement d'environnement;
- stimulus social;
- rappel;
- timeout de réflexion rare et borné.

Une intention persistante devrait pouvoir créer des cues d'action sans rappel LLM constant.

## PRÉDICTIONS ÉMERGENTES

- Les conversations deviennent plus longues seulement lorsqu'il existe un enjeu.
- Une interaction peut être courte et pourtant socialement importante.
- Une intention active provoque des actions futures sans être redécidée à chaque étape.
- Un personnage peut interrompre une activité lorsque l'événement dépasse un seuil de pertinence, mais pas à chaque bruit.
- Les styles conversationnels divergent avec les expériences.

## SCÉNARIOS DE FALSIFICATION

- Augmenter 4→20 tours ne fait qu'ajouter du small talk.
- Le LLM appelle constamment `no_action`.
- Tous les personnages répondent au même type d'événement de manière rhétoriquement semblable.
- Les intentions persistantes n'ont aucun effet si le LLM n'est pas rappelé.
- Les conversations n'affectent rien après plusieurs jours.

## SOURCES

- Gollwitzer 1999, op. cit.
- Wood & Rünger 2016, op. cit.
- Laurenceau et al. 1998, op. cit.
- Burgoon 2015, op. cit.

---

# 11. Gardien, tests et banc d'essai

**SYSTÈME :** validation technique et validation émergente  
**VERDICT : ALIGNÉ**

## AFFIRMATIONS

- **[A/B]** Pour les modèles à agents, une implémentation correcte ne valide pas le modèle conceptuel; il faut comparer plusieurs patterns à différentes échelles et tester la robustesse aux paramètres.
  - Grimm et al. 2005.
- **[B/C]** Les systèmes stochastiques/LLM doivent être évalués par distributions, tendances et propriétés, pas seulement résultats exacts.
- **[C]** Le pattern-oriented modeling fournit une très bonne philosophie pour le Vivarium : plusieurs phénomènes émergents simultanés contraignent davantage le modèle qu'un scénario unique.

## POINTS CORRECTS

- Séparation test jetable / monde vivant.
- Gardien conservateur.
- Archivage des bases fautives.
- Tests inter-systèmes.
- Reconnaissance explicite que 713 tests ne prouvent pas la psychologie.

## CORRECTIONS FONCTIONNELLES RECOMMANDÉES

Ajouter quatre niveaux d'évaluation :

### A. Invariants binaires
Ex. personne ne traverse porte bloquée; consentement absent ne peut pas être déduit d'une relation.

### B. Propriétés statistiques
Ex. sous mêmes contraintes, variation des choix; distribution des activités; fréquence d'interruption; temps entre besoins.

### C. Scénarios comparatifs
Modifier une seule variable et vérifier la direction moyenne de l'effet sans imposer un comportement exact.

### D. Patterns longitudinaux
Sur jours/semaines simulés :
- différenciation des relations;
- routines non rigides;
- mémoire sélective;
- habitudes;
- récurrence de conflits;
- réparation;
- divergence individuelle.

## PRÉDICTIONS ÉMERGENTES À MESURER

- **Diversité intra-personne** : un personnage n'est pas un script.
- **Stabilité inter-personne relative** : malgré la variabilité, certaines signatures distinguent les personnages.
- **Sensibilité au contexte** : mêmes profils, contextes différents → réponses différentes.
- **Asymétrie relationnelle**.
- **Path dependence** : histoires différentes produisent états différents.
- **Non-linéarité sociale** : le 10e même comportement n'a pas nécessairement le même effet que le 1er.
- **Récupération mnésique dépendante des indices**.
- **Anticipation** : les besoins ne sont pas seulement corrigés après seuil.
- **Habituation/habitudes**.
- **Rare événements, grand effet** : certaines violations importantes pèsent plus que plusieurs événements banals.

## SCÉNARIOS DE FALSIFICATION TRANSVERSAUX

Réviser le modèle si :
- les routines deviennent périodiques et synchronisées;
- les scores relationnels changent quasi linéairement avec le nombre d'actes;
- les personnages sont séparables seulement par leur style textuel, pas par leurs décisions;
- les personnages se souviennent de tout avec précision;
- un changement de paramètre mineur renverse qualitativement tout le monde;
- les distributions changent fortement avec fréquence des ticks;
- les mêmes événements ont toujours les mêmes conséquences;
- aucune dynamique nouvelle n'apparaît lors des exécutions longues.

## SOURCES

- Grimm V et al. *Pattern-oriented modeling of agent-based complex systems: lessons from ecology*. Science, 2005. DOI: 10.1126/science.1116681. https://doi.org/10.1126/science.1116681

---

# 12. Consentement opérationnel

**SYSTÈME :** distinction relation, permission et consentement  
**VERDICT : ALIGNÉ — À MAINTENIR COMME INVARIANT DE DESIGN**

Cette section est moins une hypothèse scientifique qu'une exigence normative et de sûreté du projet.

## AFFIRMATIONS

- **[D]** Le Vivarium choisit de ne jamais déduire le consentement actuel depuis attirance, relation, statut, besoin, habitude ou permission ancienne.
- **[D]** Une permission peut être spécifique, limitée, révoquée ou expirante.
- **[D]** Une limite personnelle peut exister sans devenir une barrière physique automatique.

## POINTS CORRECTS

Le découpage actuel évite une catégorie d'erreurs grave : transformer un état relationnel positif en droit d'action.

## CORRECTIONS FONCTIONNELLES RECOMMANDÉES

Le futur protocole doit distinguer :
- capacité à consentir;
- information pertinente;
- choix actuel;
- portée précise;
- révocabilité;
- interruption;
- communication/perception de la réponse;
- contraintes/coercition si le projet les modélise.

**Ne jamais utiliser un score de relation comme proxy.**

---

# 13. Patoune et cognition animale

**SYSTÈME :** animal non sapient  
**VERDICT : INSUFFISAMMENT DOCUMENTÉ pour cognition riche; ALIGNÉ pour l'absence actuelle du LLM sapient**

Le document audité fournit trop peu de comportement cible pour déterminer un modèle animal précis.

## POINTS CORRECTS

- Ne pas faire de Patoune un « petit humain silencieux ».
- L'absence de LLM sapient est un test architectural utile.
- Un animal doit pouvoir avoir perception, apprentissage, motivation, préférences et mémoire sans partager toute la couche de cognition narrative humaine.

## RISQUES

- Anthropomorphisme excessif.
- Réduction à une machine réflexe.
- Réutilisation directe des mêmes besoins et objectifs que les humains sans validation.

## RECOMMANDATION

Reporter la cognition animale riche à un dossier R&D spécifique fondé sur :
- éthologie féline;
- apprentissage associatif;
- motivation alimentaire/exploratoire/sociale;
- territoire;
- peur;
- jeu/prédation;
- rythmes d'activité;
- relations humain-chat.

---

# 14. Synthèse des simplifications à risque

| Simplification actuelle | Verdict | Peut rester en alpha ? | Avant conséquences sociales durables ? |
|---|---|---:|---:|
| classement fixe décisionnel | À REVOIR | oui | commencer à desserrer |
| attention déterministe technique | RÉSERVE FORTE | oui | ajouter pertinence sociale / attentes |
| 4 besoins | RÉSERVE | oui | oui, si non présentés comme exhaustifs |
| activité unique exclusive | RÉSERVE | oui | pas bloquant immédiat |
| loisirs 30 min taux idle | DESIGN PROVISOIRE | oui | non bloquant |
| dialogues sans conséquences | MANQUE | oui actuellement | **à corriger prochain lot** |
| relation scalaire | RÉSERVE FORTE | oui | **ajouter épisodes/attentes** |
| personnalité peu causale | MANQUE NORMAL | oui | commencer via appraisal/décision |
| humeur/émotions non dynamiques | MANQUE NORMAL | oui | utile pour social causal |
| mémoire non consolidée | RÉSERVE FORTE | oui court terme | **minimum requis avant accumulation longue** |
| Patoune sans cognition riche | MANQUE ACCEPTABLE | oui | non |
| espace à l'échelle pièce | RÉSERVE | oui | ajouter perception sociale minimale |
| cognition quasi seulement événementielle | RÉSERVE | oui | élargir occasions |
| un seul modèle local | RISQUE TECHNIQUE/ÉVAL | oui | benchmark plus tard |

---

# 15. Prochain lot R&D recommandé

## Nom fonctionnel proposé

**SOCIAL CONSEQUENCE CORE — interprétation située + épisode social + mémoire minimale**

### 15.1 Ce que le lot doit accomplir

Permettre qu'un acte social ait une conséquence **sans coder directement sa valence**.

### 15.2 Entrées conceptuelles

- trace subjective de l'acte;
- participants;
- contenu/acte social;
- contexte;
- croyances pertinentes;
- relation actuelle;
- attentes pertinentes;
- valeurs/préférences/limites;
- but/intention;
- affect courant;
- historique résumé de la relation;
- source / fiabilité si information rapportée.

### 15.3 Sortie conceptuelle proposée

Un **épisode social interprété** contenant :

1. ce que le personnage croit avoir compris;
2. niveau d'ambiguïté;
3. intention attribuée ou inconnue;
4. attente confirmée/violée;
5. domaine touché;
6. pertinence pour but/valeur/limite;
7. appraisal;
8. réponse affective plausible;
9. croyance/attente éventuellement créée ou révisée;
10. importance mémorielle;
11. dimensions relationnelles potentiellement concernées;
12. justification/provenance.

Le LLM peut proposer une partie de cette interprétation. Le moteur/service contrôlé doit valider la provenance, les bornes, les contraintes et empêcher les mises à jour incohérentes.

### 15.4 Mémoire minimale à inclure dans le même lot ou juste avant

- condensation d'épisodes sociaux;
- accessibilité;
- indices de récupération;
- provenance/source;
- lien personnage/thème;
- résumé de répétitions;
- distinction « trace exacte du moteur » / « souvenir accessible au personnage ».

### 15.5 Ce qui reste hors lot

- faux souvenirs sophistiqués;
- reconsolidation biologique détaillée;
- réputation de réseau complète;
- groupes sociaux;
- économie;
- combat;
- vêtements;
- cognition animale riche;
- apprentissage de personnalité longue durée;
- modèle complet de dépendance;
- consentement sexuel/physique complet au-delà des invariants déjà prévus;
- géométrie 3D.

---

# 16. Scénarios d'acceptation du prochain lot

## Scénario A — compliment ambigu

Deux personnages reçoivent le même compliment.

Conditions différentes :
- l'un vient d'une amie de confiance;
- l'autre vient d'une personne ayant récemment manipulé le personnage.

**Attendu :** effets différents possibles; aucune règle `compliment = +relation`.

**Falsification :** même delta dans les deux cas.

---

## Scénario B — refus respectueux

A propose une activité à B. B refuse clairement mais poliment.

**Attendu :**
- aucune transgression automatique;
- déception possible;
- respect peut rester stable ou augmenter;
- affection ne doit pas nécessairement baisser;
- consentement/permission reste distinct.

**Falsification :** `decline = -affection`.

---

## Scénario C — violation de limite après avertissement

A a explicitement appris une limite de B, puis reproduit un acte qui la viole.

**Attendu :**
- la violation est interprétée plus négativement que le même acte avant connaissance de la limite;
- l'intention attribuée peut rester incertaine;
- confiance/sécurité peuvent être affectées;
- l'effet dépend du contexte et de la gravité.

**Falsification :** l'historique de la limite n'affecte pas la conséquence.

---

## Scénario D — excuse et réparation

Après une transgression mineure accidentelle, A s'excuse, reconnaît l'impact et change son comportement.

**Attendu :**
- réparation possible;
- pas de restauration instantanée garantie;
- changement ultérieur doit compter.

**Falsification :** prononcer « désolée » restaure mécaniquement la confiance.

---

## Scénario E — source non fiable

C affirme à A que B a dit quelque chose de blessant. A n'était pas présente et C a un historique de fiabilité faible.

**Attendu :**
- croyance possible mais incertaine;
- effet social limité ou différé;
- possibilité de chercher confirmation.

**Falsification :** la rumeur devient un fait subjectif certain et modifie directement B.

---

## Scénario F — même acte, différentes attentes

Erika fait une blague brusque à deux personnes.

**Attendu :**
- une personne familière avec son style peut l'interpréter légèrement;
- une autre peut l'interpréter comme irrespectueuse;
- relation et contexte influencent l'appraisal.

**Falsification :** acte lexical identique → même émotion/delta.

---

## Scénario G — mémoire sélective

Après de nombreux épisodes banals et un épisode inhabituel important, plusieurs jours passent.

**Attendu :**
- le contenu important reste plus accessible;
- les épisodes banals peuvent se condenser;
- aucun effacement du journal canonique.

**Falsification :** mémoire exacte de tous les événements ou oubli uniforme strictement temporel.

---

## Scénario H — régulation anticipatrice

Un personnage a faim modérément et prévoit une longue activité sans accès à nourriture.

**Attendu :** manger avant le seuil critique devient plausible.

**Falsification :** jamais d'action avant franchissement du seuil.

---

## Scénario I — intention contre urgence

Un personnage photographie avec une intention forte, mais un besoin physiologique devient sévère.

**Attendu :** compétition réelle; aucune priorité absolue universelle.

**Falsification :** intention active gagne toujours.

---

## Scénario J — habitudes

Même contexte et même routine se répètent pendant plusieurs jours.

**Attendu :**
- moins de délibération nécessaire;
- comportement plus facilement déclenché par le contexte;
- interruption possible si conditions changent.

**Falsification :** coût cognitif identique à chaque répétition.

---

# 17. Mesures statistiques recommandées pour le banc d'essai

Ne pas imposer de seuil numérique canonique sans calibration. Mesurer d'abord :

### Diversité comportementale
- entropie / diversité des activités par personnage;
- part des décisions répétées dans contextes identiques;
- fréquence de `no_action`;
- distribution des durées.

### Régulation
- distance moyenne au seuil lors du déclenchement d'une action;
- fraction d'actions anticipatrices;
- périodicité des cycles;
- synchronisation artificielle entre personnages.

### Social
- asymétrie A→B/B→A;
- distribution des deltas relationnels;
- proportion d'actes sans conséquence;
- influence du contexte sur un même acte;
- fréquence de réparations et rechutes;
- divergence des relations au fil du temps.

### Mémoire
- probabilité de récupération selon récence, importance et indice;
- condensation des répétitions;
- proportion de détails accessibles;
- concordance entre confiance subjective et qualité initiale sans exiger perfection.

### Personnalité
- variabilité intra-personne;
- différences moyennes inter-personnes;
- sensibilité situationnelle;
- stabilité longitudinale relative.

### LLM
- taux de propositions invalides;
- homogénéité lexicale/comportementale entre personnages;
- dépendance des choix à l'identité textuelle du personnage versus états fonctionnels;
- robustesse à différents modèles locaux.

---

# 18. Éléments explicitement classés comme choix de design

Les points suivants ne doivent pas être présentés comme « scientifiquement vrais » :

- temps 1:1 avec le temps mural;
- cinq résidentes;
- casting spécifique;
- aucune maladie/vieillissement/mort;
- allocation et dépenses payées;
- fermeture du monde;
- quatre tours par scène;
- loisirs de 30 minutes;
- quatre besoins alpha;
- vocabulaire fermé d'actes sociaux;
- taxonomie exacte des familles émotionnelles;
- nombre exact de dimensions relationnelles;
- seuils numériques;
- poids/deltas;
- fréquence des appels LLM;
- Gemma 4 12B QAT comme modèle local;
- limites UI;
- reset de l'alpha;
- structure précise des presets.

La science peut contraindre leurs conséquences ou révéler des incohérences, mais elle ne les impose pas.

---

# 19. Informations à demander à Codex / au propriétaire si nécessaire

Aucune information n'est bloquante pour le prochain lot conceptuel. Les questions suivantes deviennent utiles au moment de l'implantation :

1. Les huit dimensions relationnelles ont-elles déjà une sémantique formelle détaillée par domaine ?
2. Le moteur possède-t-il déjà un mécanisme générique d'attente/prediction subjective réutilisable ?
3. Les traces peuvent-elles être liées à plusieurs interprétations successives sans modifier la trace source ?
4. La structure de mémoire prévue distingue-t-elle déjà preuve canonique, épisode subjectif et résumé consolidé ?
5. Les « signatures situationnelles » des traits ont-elles des règles implantées ou sont-elles uniquement descriptives ?
6. `repos` et `énergie` ont-ils déjà des définitions non chevauchantes dans le canon documentaire ?
7. Les zones privées / règles de perception spatiale sont-elles prévues avant ou après les conséquences sociales ?
8. Le protocole de scène peut-il porter un but/enjeu sans forcer le personnage à l'atteindre ?

---

# 20. Conclusion

Le contre-audit ne trouve pas de fondation conceptuelle suffisamment mauvaise pour justifier une refonte du Vivarium `0.1.0a9`.

Au contraire, la structure générale — canon déterministe, subjectivité privée, provenance, LLM proposeur, validation, journal immuable — est bien adaptée au problème. Les risques actuels sont surtout des **simplifications d'alpha qui doivent rester explicitement provisoires**.

La priorité R&D est maintenant claire :

> **Ne pas enrichir d'abord la quantité de dialogue. Enrichir la chaîne qui donne une signification subjective et durable aux événements sociaux.**

Le prochain progrès qualitatif ne viendra pas de conversations plus longues, d'un modèle plus gros ou de davantage de dimensions relationnelles. Il viendra du passage :

```text
« elle a dit X »
```

à

```text
« j'ai perçu X, dans ce contexte;
je crois qu'elle voulait probablement dire Y;
cela confirme/contredit telle attente;
cela compte pour moi parce que Z;
j'en ressens / j'en conclus quelque chose;
je m'en souviendrai avec telle importance;
ma relation ou mon comportement futur peut donc changer. »
```

Le moteur doit garder la provenance, les contraintes et les conséquences cohérentes. Le LLM doit conserver l'espace d'interprétation nécessaire pour que deux personnes puissent vivre différemment le même événement.

C'est précisément la frontière « exécution rigoureuse, création flexible ».

---

# Références principales consolidées

1. Anderson BA. A value-driven mechanism of attentional selection. *Journal of Vision*. 2013;13(3):7. DOI 10.1167/13.3.7. https://doi.org/10.1167/13.3.7
2. Awh E, Belopolsky AV, Theeuwes J. Top-down versus bottom-up attentional control: a failed theoretical dichotomy. *Trends Cogn Sci*. 2012;16:437–443. DOI 10.1016/j.tics.2012.06.010. https://doi.org/10.1016/j.tics.2012.06.010
3. Baumeister RF, Leary MR. The need to belong. *Psychological Bulletin*. 1995;117:497–529. DOI 10.1037/0033-2909.117.3.497. https://doi.org/10.1037/0033-2909.117.3.497
4. Borbély AA et al. The two-process model of sleep regulation: a reappraisal. *J Sleep Res*. 2016;25:131–143. DOI 10.1111/jsr.12371. https://doi.org/10.1111/jsr.12371
5. Burgoon JK. Expectancy Violations Theory. 2015. DOI 10.1002/9781118540190.wbeic102. https://doi.org/10.1002/9781118540190.wbeic102
6. Craig AD. How do you feel? Interoception: the sense of the physiological condition of the body. *Nat Rev Neurosci*. 2002;3:655–666. DOI 10.1038/nrn894. https://doi.org/10.1038/nrn894
7. Elsey JWB, Van Ast VA, Kindt M. Human memory reconsolidation: A guiding framework and critical review. *Psychological Bulletin*. 2018;144:797–848. DOI 10.1037/bul0000152. https://doi.org/10.1037/bul0000152
8. Fleeson W, Jayawickreme E. Whole Trait Theory. *Journal of Research in Personality*. 2015;56:82–92. DOI 10.1016/j.jrp.2014.10.009. https://doi.org/10.1016/j.jrp.2014.10.009
9. Fraley RC, Shaver PR. Adult Romantic Attachment. *Review of General Psychology*. 2000;4:132–154. DOI 10.1037/1089-2680.4.2.132. https://doi.org/10.1037/1089-2680.4.2.132
10. Fraley RC et al. Patterns of stability in adult attachment. *JPSP*. 2011;101:974–992. DOI 10.1037/a0024150. https://doi.org/10.1037/a0024150
11. Gollwitzer PM. Implementation intentions: Strong effects of simple plans. *American Psychologist*. 1999;54:493–503. DOI 10.1037/0003-066X.54.7.493. https://doi.org/10.1037/0003-066X.54.7.493
12. Grimm V et al. Pattern-oriented modeling of agent-based complex systems: lessons from ecology. *Science*. 2005. DOI 10.1126/science.1116681. https://doi.org/10.1126/science.1116681
13. Johnson MK, Hashtroudi S, Lindsay DS. Source monitoring. *Psychological Bulletin*. 1993;114:3–28. DOI 10.1037/0033-2909.114.1.3. https://doi.org/10.1037/0033-2909.114.1.3
14. Khalsa SS et al. Interoception and Mental Health: A Roadmap. *Biol Psychiatry Cogn Neurosci Neuroimaging*. 2018;3:501–513. DOI 10.1016/j.bpsc.2017.12.004. https://doi.org/10.1016/j.bpsc.2017.12.004
15. Laurenceau JP, Barrett LF, Pietromonaco PR. Intimacy as an interpersonal process. *JPSP*. 1998;74:1238–1251. DOI 10.1037/0022-3514.74.5.1238. https://doi.org/10.1037/0022-3514.74.5.1238
16. Rasch B, Born J. About Sleep's Role in Memory. *Physiological Reviews*. 2013;93:681–766. DOI 10.1152/physrev.00032.2012. https://doi.org/10.1152/physrev.00032.2012
17. Robbins BG. What is Trust? A Multidisciplinary Review, Critique, and Synthesis. *Sociology Compass*. 2016;10:972–986. DOI 10.1111/soc4.12391. https://doi.org/10.1111/soc4.12391
18. Russell JA. A circumplex model of affect. *JPSP*. 1980;39:1161–1178. DOI 10.1037/h0077714. https://doi.org/10.1037/h0077714
19. Sanna GA, Lagnado D. Belief updating in the face of misinformation: The role of source reliability. *Cognition*. 2025;258:106090. DOI 10.1016/j.cognition.2025.106090. https://doi.org/10.1016/j.cognition.2025.106090
20. Scherer KR. Appraisal Processes in Emotion. Oxford University Press. 2001. DOI 10.1093/oso/9780195130072.001.0001. https://doi.org/10.1093/oso/9780195130072.001.0001
21. Scherer KR. What are emotions? And how can they be measured? *Social Science Information*. 2005;44:695–729. DOI 10.1177/0539018405058216. https://doi.org/10.1177/0539018405058216
22. Schulkin J, Sterling P. Allostasis: A Brain-Centered, Predictive Mode of Physiological Regulation. *Trends Neurosci*. 2019;42:740–752. DOI 10.1016/j.tins.2019.07.010. https://doi.org/10.1016/j.tins.2019.07.010
23. Sterling P. Allostasis: a model of predictive regulation. *Physiology & Behavior*. 2012;106:5–15. DOI 10.1016/j.physbeh.2011.06.004. https://doi.org/10.1016/j.physbeh.2011.06.004
24. Wood W, Rünger D. Psychology of Habit. *Annual Review of Psychology*. 2016;67:289–314. DOI 10.1146/annurev-psych-122414-033417. https://doi.org/10.1146/annurev-psych-122414-033417
25. Yuan B, Dong Y, Li W. The trust repair effect of apology: A systematic review and meta-analysis. *Advances in Psychological Science*. 2017;25:1103–1113. DOI 10.3724/SP.J.1042.2017.01103. https://doi.org/10.3724/SP.J.1042.2017.01103

