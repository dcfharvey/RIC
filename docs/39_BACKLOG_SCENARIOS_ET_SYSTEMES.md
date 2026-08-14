# Backlog — scénarios d'intégration et systèmes futurs

**Statut :** idées retenues pour étude ultérieure; aucune n'est un engagement de
MVP ni une autorisation de les implémenter immédiatement.

## Jeux à information contrôlée

- **UNO en cuisine** : premier scénario social à règles publiques, mains privées,
  tours, interaction et petite mémoire sociale. Patoune peut être observatrice,
  perturbatrice ou juge silencieuse selon de futurs comportements animaux.
- **Blackjack** : décision sous incertitude et règles compactes; moins riche pour
  les dynamiques de groupe, car les joueuses affrontent principalement la banque.
- **Poker** : scénario avancé de bluff, mises, croyances, mémoire relationnelle
  et économie. À différer jusqu'aux systèmes de connaissances privées, argent et
  relations dirigées.

Ordre indicatif : UNO, puis blackjack, puis poker. Ces jeux serviront de bancs
d'essai d'intégration : les règles, tours, cartes et conséquences restent
canoniques; les personnages interprètent, parlent et choisissent dans les
limites validées.

## Effort physique et affrontements

Un futur système d'effort est pertinent. Il permet d'arbitrer sport, rivalité,
entraînement, compétition, fuite et confrontation sans déléguer le résultat au
LLM. Son noyau ne doit toutefois pas tenter de reproduire une physique complète.

Modèle envisagé :

```text
action physique proposée
→ préconditions (lieu, équipement, règles de l'épreuve)
→ état canonique (forme, blessure, énergie, ressources, position)
→ résolution déterministe ou pseudo-aléatoire reproductible
→ conséquences canoniques
→ interprétation subjective et narration
```

Les résultats doivent dépendre de capacités déclarées et de l'état présent,
avec un tirage seulement lorsqu'une incertitude réelle est voulue. Chaque tirage
doit être seedé, journalisé et rejouable par le banc d'essai.

### Scénarios proposés

- sport encadré : meilleur premier terrain, avec règles, arbitre et conséquences
  limitées;
- tournoi de MMA : test avancé de fatigue, blessure, consentement, abandon,
  stratégie et spectatrices;
- tournoi de gladiatrices : variante fictionnelle potentiellement utile pour un
  monde différent, mais elle exige avant tout un contrat explicite de violence,
  sécurité, armes, soins et conséquences durables.

### Critères avant implémentation

1. définir les actions physiques et les résultats possibles avant les scores;
2. séparer aptitude stable, condition temporaire, technique, équipement,
   environnement et hasard;
3. ne pas inférer une capacité depuis l'espèce, l'apparence ou une narration;
4. conserver consentement, règles de l'épreuve et arrêt comme faits canoniques;
5. commencer par un sport à conséquences réversibles avant le combat violent;
6. tester les mêmes scénarios avec un seed identique, puis des variations de
   conditions pour détecter les effets émergents.

La conclusion actuelle est donc : très pertinent à terme, mais postérieur au
contrat d'action élargi, aux capacités, à l'équipement et aux règles sociales.

## Programme de généralité — corpus transversal Qwen

**Statut R&D :** programme de falsification conceptuelle. Ce corpus n'est ni une
spécification, ni une source scientifique, ni une ontologie à importer, ni un
engagement d'architecture ou d'implantation.

Le 13 août 2026, un corpus externe de 23 fichiers texte a été produit avec Qwen
pour ratisser volontairement large : espèces réelles et fictives, actions,
environnements, phénomènes naturels, magie, objets, vêtements, véhicules,
ressources, alimentation, technologie, communication, connaissance, métiers,
jeux et règles, art, guerre et structures sociales. Les recouvrements, erreurs
factuelles et incohérences de taxonomie sont conservés comme matériau de stress :
le but n'est pas de reprendre les catégories de Qwen, mais de chercher les
mécanismes sous-jacents qui doivent rester stables lorsque les catégories de
surface changent.

### Lecture critique du corpus

La passe transversale confirme que les catégories dites « universelles » du
corpus ne sont justement pas des primitives fiables. Elles mélangent souvent :

- entité, matière, état et propriété;
- rôle, fonction et usage contextuel;
- action intentionnelle, réaction, processus autonome et événement;
- lieu, milieu, ressource, danger et institution;
- capacité objective, capacité perçue et compétence;
- propriété physique, signification sociale, valeur symbolique et croyance;
- connaissances scientifiques, spéculations fictives et parfois
  pseudoscientifiques.

Cette instabilité est utile : elle montre pourquoi une généralisation par
**catégories nominales** produirait vite des exceptions. Les catégories peuvent
rester des vues, index, presets ou vocabulaires narratifs; elles ne doivent pas
porter une causalité cachée lorsqu'une propriété ou relation causale explicite
peut l'exprimer.

Cette règle n'interdit pas à une catégorie d'être causale. Un monde peut déclarer
explicitement une règle portant sur une classe juridique, une espèce véritable,
un statut rituel ou une autre catégorie. Dans ce cas, c'est **la règle déclarée**
qui rend la catégorie causale; le moteur ne doit pas inventer cet effet parce que
le nom « ressemble » à quelque chose qui devrait en avoir un.

### Question de falsification

Pour chaque cas du corpus, poser :

> Peut-on représenter ce cas par composition de mécanismes déjà généraux, sans
> ajouter une règle qui dépend implicitement de son nom, de son espèce, de son
> univers ou de sa catégorie narrative ?

Une réponse négative ne signifie pas automatiquement qu'un nouveau système est
nécessaire. Elle signale d'abord un trou d'abstraction à qualifier. Une nouvelle
abstraction n'est retenue que si plusieurs cas causalement indépendants la
justifient et si elle produit des prédictions ou invariants falsifiables.

### Critère R&D candidat : causalité explicite + invariance

Pour une future feature, deux questions de revue doivent devenir systématiques :

1. **si tous les labels descriptifs non causaux changent mais que les causes
   pertinentes restent identiques, le résultat moteur reste-t-il identique ?**
2. **si une cause pertinente change alors que le label reste identique, le
   résultat moteur change-t-il comme prévu ?**

Cette paire détecte deux défauts symétriques : le couplage nominal caché et la
causalité réellement pertinente que le moteur ignore.

Il s'agit ici d'un **critère R&D candidat**, cohérent avec DEC-049 à DEC-051; ce
texte n'ajoute pas silencieusement une nouvelle décision autoritative au registre.

### Axes de stress fonctionnels provisoires

Les quinze familles suivantes sont des **axes de stress qui se recouvrent**. Ce
ne sont pas quinze primitives, ni une ontologie universelle, ni une prescription
de packages, tables ou classes. Un même cas peut légitimement traverser plusieurs
axes.

1. **identité et composition** — qu'est-ce qui constitue une entité et qu'est-ce
   qui persiste lorsqu'elle change, se divise, fusionne ou change de support;
2. **état** — quelles propriétés objectives peuvent varier dans le temps;
3. **ressource, stock et flux** — quantité disponible, production, consommation,
   transfert et seuils;
4. **capacité effective** — ce que l'entité peut effectivement faire dans son
   état présent, indépendamment de son étiquette nominale;
5. **faisabilité objective relationnelle** — ce qui est réellement possible
   pour cet acteur avec cette cible, ce milieu, cette interface et ces règles;
6. **action, processus et transition** — distinguer action initiée par un agent,
   processus autonome sans intention, et changement/événement d'état;
7. **transformation** — changement de forme, matière, état, capacités,
   composition ou identité;
8. **espace, topologie et contenance** — position, voisinage, passage,
   inclusion et mobilité des contenants;
9. **milieu, champ et exposition** — lumière, chaleur, pression, atmosphère,
   radiation, eau, vent ou équivalent fictif;
10. **interface, équipement et attachement** — outil, vêtement, armure,
    prothèse, véhicule ou artefact qui modifie l'interaction possible;
11. **signal, information et canal perceptif** — émission, propagation,
    accessibilité sensorielle ou technique, réception et décodage;
12. **connaissance, compétence et apprentissage** — savoir, savoir-faire,
    acquisition, pratique, transmission et oubli;
13. **règle sociale ou institutionnelle** — rôle, autorité, permission,
    consentement, propriété, jeu, loi, convention, engagement ou rituel;
14. **agence, contrôle et cycle de vie** — qui décide, qui contrôle quoi,
    autonomie, dépendance, création, disparition et continuité;
15. **régime causal du monde** — lois ou mécanismes propres à un univers ou à
    une région, y compris les effets extraordinaires explicitement déclarés.

**Important : faisabilité objective ≠ affordance perçue.** Dans RIC, la première
relève de ce qui est réellement possible dans le monde; la seconde relève de ce
qu'un agent peut détecter, interpréter ou croire possible à partir de ses propres
canaux et connaissances. Un personnage peut croire une action possible alors
qu'elle ne l'est pas, ou ne pas percevoir une possibilité réellement disponible.
La terminologie d'affordance issue de la psychologie écologique ne doit donc pas
fusionner Reality et Cognition.

### Décomposition transversale de catégories narratives

La passe des 23 fichiers fournit plusieurs exemples où un gros label narratif est
une mauvaise unité causale :

- **`girly_care`** : agrège coiffure, soin de peau, maquillage, manucure,
  habillement ou autres activités qui n'ont ni les mêmes objets, ni les mêmes
  préconditions, ni les mêmes cibles corporelles, ni les mêmes effets; le genre
  du label ne constitue aucune précondition physique générale;
- **`work` / métier** : un emploi n'est pas une action atomique; il peut combiner
  rôle institutionnel, compétences, engagements temporels, lieu, tâches,
  permissions, ressources et compensation;
- **aliment** : être mangeable, nutritif, toxique, allergène, rituel ou répugnant
  peut dépendre de l'acteur, de son état, du contexte social et éventuellement
  d'une loi de monde;
- **arme** : un marteau, un couteau ou un véhicule peut devenir moyen de combat
  par l'usage sans changer d'identité physique; « arme » est souvent un rôle
  contextuel plutôt qu'une essence matérielle;
- **vêtement** : couverture, attachement, ajustement morphologique, protection,
  contrainte de mouvement et signification sociale sont séparables;
- **véhicule** : peut être simultanément contenant mobile, interface de contrôle,
  équipement, habitat, source de mouvement et parfois agent autonome;
- **jeu** : combine règles, rôles, ordre de tour, permissions, ressources,
  information publique/privée, conditions de fin et actions physiques ou
  numériques;
- **objet sacré** : ses propriétés physiques, son statut social/symbolique, les
  croyances des agents et un éventuel pouvoir surnaturel objectif doivent rester
  séparables;
- **espèce** : peut fournir un preset descriptif ou déclaratif, mais une capacité
  ne doit pas apparaître simplement parce qu'un nom d'espèce la suggère, sauf
  règle causale du monde explicitement attachée à cette catégorie;
- **météo, feu, inondation** : montrent qu'un changement causal n'a pas toujours
  d'acteur ni d'intention;
- **magie, télépathie, portail** : doivent être exprimables comme capacités,
  canaux, ressources, préconditions ou régimes causaux explicites; une narration
  du LLM ne suffit jamais à produire leur effet canonique.

Ces exemples ne sont pas une liste de features à implémenter. Ils servent à
vérifier qu'une abstraction candidate réduit réellement plusieurs exceptions au
lieu de déplacer leurs noms.

### Lecture de la couverture actuelle

Cette lecture décrit l'état fonctionnel observé sur la branche de Rodage V2;
elle ne constitue pas un plan d'implantation.

- **Représentation/composition : fondation forte.** `templates.py` et le registre
  fournissent déjà une grammaire composable avec provenance gelée. Cela ne
  signifie pas que tous les composants ont déjà une sémantique causale runtime.
- **Ressources : représentation forte, consommation causale partielle.**
  `resources.py` sait porter des états, bandes et effets de capacité; la
  généralisation de leurs conséquences à tous les domaines reste incomplète.
- **Espace : séparation conceptuelle forte, couverture causale encore bornée.**
  Lieux, connecteurs, topologie et contenance sont distincts, mais les espaces
  mobiles, partagés entre dimensions ou physiquement atypiques restent des cas
  de stress futurs.
- **Capacités : partiel.** Le mécanisme existe par endroits, mais il n'y a pas
  encore de vocabulaire général couvrant locomotion, manipulation, perception,
  communication, cognition, compatibilité d'équipement, etc.
- **Morphologie : partiel.** `body.morphology` est encore descriptif et le
  vocabulaire MVP est très borné. Une énumération nominale ne doit pas devenir
  la frontière causale finale.
- **Cognition/agency : partiel.** L'agence non sapiente générique est un bon
  précédent, mais `sapient` / `non_sapient` ne suffit pas comme axe universel de
  toutes les capacités cognitives.
- **Perception : partiel.** La séparation fait/perception est forte; les canaux
  sensoriels ou techniques hétérogènes et l'évaluation subjective des
  possibilités restent à étudier.
- **Action : partiel.** Le contrat cognition–moteur protège le canon, mais le
  vocabulaire exécutable autonome contient encore des catégories d'activité MVP
  codées en dur; `girly_care` est un cas concret de dette nominale.
- **Objets : partiel.** Portabilité, possession physique et contenance
  objet-dans-objet existent; équipement, ajustement morphologique, couverture,
  dimensions, masse, fluides et passagers restent incomplets.
- **Social/institutionnel : partiel.** Relations directionnelles, limites et
  permissions existent; rôles, institutions, engagements et règles de jeu plus
  générales restent des cas futurs.
- **À étudier : transformations et identité.** Métamorphose, division, fusion,
  changement de support et continuité d'identité ne doivent pas être réduits à
  un changement d'étiquette.
- **À étudier : contrôle multi-support.** Un esprit dans plusieurs corps, un
  corps sous plusieurs contrôles, une IA distribuée ou un parasite intelligent
  dépassent la possession physique d'objet existante.
- **À étudier : milieux et expositions génériques.** La lumière circadienne est
  un premier cas causal, mais température, pression, atmosphère, immersion,
  radiation et équivalents fictifs ne forment pas encore un mécanisme commun.
- **À étudier : véhicules et habitats mobiles.** Ils combinent locomotion,
  contenance, contrôle et parfois agence.
- **À étudier : régimes causaux locaux.** Une magie ou technologie fictive doit
  pouvoir produire des effets déclarés sans que le récit ou le LLM devienne
  lui-même une autorité canonique.

### Résultats empiriques et précédents techniques pertinents

La littérature ne fournit pas une ontologie universelle prête à coder. Elle
fournit toutefois des résultats bornés et des précédents techniques utiles.

**Résultat empirique borné — perception d'action.** Warren (1984), dans trois
expériences de montée d'escaliers, relie les frontières perceptives de
franchissabilité à l'ajustement entre propriétés corporelles et environnement.
Des travaux ultérieurs ont montré que des variables fonctionnelles comme la
force et la flexibilité peuvent aussi compter. Ce résultat soutient une lecture
relationnelle dans ce domaine précis; il ne démontre pas une loi universelle de
toutes les possibilités d'action.

**Théorie concurrente — affordances.** Chemero (2003) propose les affordances
comme relations entre capacités de l'animal et caractéristiques de
l'environnement. C'est une théorie de psychologie écologique, utile comme
inspiration mais non comme loi à transposer. RIC doit en plus maintenir sa
séparation explicite entre faisabilité objective et possibilité subjectivement
perçue.

**Précédent technique — qualification des actions.** Ginsberg et Smith (1988)
montrent le problème de l'énumération ouverte des qualifications susceptibles de
faire échouer une action et proposent de raisonner avec des contraintes générales
de domaine. Pour RIC, cela soutient l'objectif d'éviter une suite de « sauf si X »
nominales; cela ne fournit pas à lui seul le modèle d'action à implémenter.

**Précédent technique — fonction d'artefact.** Hirtz, Stone, McAdams, Szykman et
Wood (2002) montrent l'intérêt, en conception mécanique, d'une représentation
fonctionnelle abstraite et d'un vocabulaire de fonctions pour décomposer les
artefacts. Ce travail soutient l'analyse « que fait/permets cet objet ? » plutôt
que « de quelle catégorie narrative est-il ? », mais sa Functional Basis n'est
pas une ontologie universelle à importer dans RIC.

**Précédent technique — temps, actions et processus.** PDDL2.1 formalise des
actions duratives et des ressources numériques; PDDL+ ajoute notamment des
processus autonomes et des effets dépendant du temps dans des domaines mixtes
discrets-continus. Ils montrent qu'action volontaire et processus autonome
peuvent être représentés séparément. RIC n'a aucune obligation d'utiliser PDDL.

**Précédent technique — intervalles et récurrence.** Allen (1983) fournit un
formalisme classique de relations entre intervalles temporels. RFC 5545 montre,
dans un autre domaine pratique, qu'une récurrence est composée explicitement
d'un début, de règles, d'occurrences supplémentaires et d'exceptions (`DTSTART`,
`RRULE`, `RDATE`, `EXDATE`). Ces références soutiennent la séparation entre
« activité » et « structure temporelle », sans prescrire le stockage de RIC.

**Résultat technique — tests combinatoires et métamorphiques.** NIST SP 800-142
décrit le test `t-way` pour couvrir efficacement des interactions de facteurs;
NIST CSWP 26 étend le raisonnement à l'ordre des entrées pour les systèmes à
état. Raunak et Olsen (2021) montrent l'intérêt du test métamorphique pour la
vérification et la validation de simulations lorsque l'oracle exact est difficile
à établir.

Références déterminantes :

- Warren, W. H. Jr. (1984), *Perceiving affordances: visual guidance of stair
  climbing*, J. Exp. Psychol. Human Perception and Performance, 10(5), 683–703,
  DOI `10.1037/0096-1523.10.5.683`;
- Chemero, A. (2003), *An Outline of a Theory of Affordances*, Ecological
  Psychology, 15(2), 181–195, DOI `10.1207/S15326969ECO1502_5`;
- Ginsberg, M. L. & Smith, D. E. (1988), *Reasoning about action II: The
  qualification problem*, Artificial Intelligence, 35(3), 311–342, DOI
  `10.1016/0004-3702(88)90020-3`;
- Hirtz, J., Stone, R. B., McAdams, D. A., Szykman, S. & Wood, K. L. (2002),
  *A Functional Basis for Engineering Design: Reconciling and Evolving Previous
  Efforts*, Research in Engineering Design, DOI `10.1007/s00163-001-0008-3`;
- Allen, J. F. (1983), *Maintaining Knowledge about Temporal Intervals*,
  Communications of the ACM, 26(11), 832–843, DOI `10.1145/182.358434`;
- Desruisseaux, B. (2009), *Internet Calendaring and Scheduling Core Object
  Specification (iCalendar)*, RFC 5545;
- Fox, M. & Long, D. (2003), *PDDL2.1: An Extension to PDDL for Expressing
  Temporal Planning Domains*, Journal of Artificial Intelligence Research 20,
  61–124, DOI `10.1613/jair.1129`;
- Fox, M. & Long, D. (2006), *Modelling Mixed Discrete-Continuous Domains for
  Planning (PDDL+)*, Journal of Artificial Intelligence Research 27, 235–297,
  DOI `10.1613/jair.2044`;
- Kuhn, D. R., Kacker, R. N. & Lei, Y. (2010), *Practical Combinatorial
  Testing*, NIST SP 800-142, DOI `10.6028/NIST.SP.800-142`;
- Kuhn, D. R., Raunak, M. S. & Kacker, R. N. (2022), *Ordered t-way
  Combinations for Testing State-based Systems*, NIST CSWP 26, DOI
  `10.6028/NIST.CSWP.26`;
- Raunak, M. S. & Olsen, M. (2021), *Metamorphic Testing on the Continuum of
  Verification and Validation of Simulation Models*, IEEE/ACM MET 2021, DOI
  `10.1109/MET52542.2021.00015`.

### Conclusions raisonnables mais incertaines

Ces conclusions dépassent les résultats directs des sources et doivent rester
révisables :

1. une grande part de la généralité utile à RIC semble venir de la composition
   de propriétés, relations et processus plutôt que d'une taxonomie exhaustive;
2. les catégories narratives peuvent rester utiles pour l'interface, la
   génération de contenu et les presets sans devenir automatiquement des causes;
3. séparer action agentive, processus autonome et transition d'état devrait
   réduire les cas spéciaux dans des domaines aussi différents que météo,
   physiologie, machines et magie;
4. les rôles fonctionnels des objets devraient pouvoir varier selon l'action et
   le contexte sans changer leur identité physique;
5. les engagements temporels semblent constituer un trou transversal distinct
   des activités elles-mêmes.

### Hypothèses de modélisation à falsifier

Ces propositions sont des hypothèses R&D, pas des faits scientifiques :

1. une capacité nominale n'est pas nécessairement une capacité effective;
2. la faisabilité objective d'une action est souvent relationnelle : acteur +
   état + cible + milieu + interface + règle pertinente;
3. la perception qu'a l'agent de cette faisabilité est une autre variable et
   peut être incomplète ou fausse;
4. espèce, apparence, métier et catégorie d'objet peuvent fournir des presets ou
   des informations descriptives, mais ne doivent pas remplacer les propriétés
   causales quand celles-ci sont disponibles;
5. un label ne doit exercer aucune causalité cachée; une catégorie peut toutefois
   devenir causale lorsqu'une règle de monde explicite le déclare;
6. une transformation doit modifier les propriétés concernées sans réécrire
   rétroactivement provenance ni histoire;
7. un effet extraordinaire reste une cause du monde à déclarer et valider; sa
   description narrative ne lui donne aucune autorité;
8. sens symbolique, croyance, réputation et valeur sociale doivent rester
   séparables des propriétés physiques du même support;
9. compétence et information accessible doivent pouvoir limiter une décision ou
   une action même si morphologie et énergie la rendent physiquement possible;
10. des capacités peuvent être conjointes ou relationnelles et ne pas appartenir
    exclusivement à une seule entité.

### Trou transversal exposé par le rodage : engagements temporels

Le scénario de Sophie a révélé un cas concret : commencer le monde avec Sophie
`work` et prévoir un retour ponctuel ne constitue pas un système d'emploi ou
d'horaire. Il ne faut pas corriger ce trou par un script « Sophie part travailler
à 8 h ».

**Hypothèse fonctionnelle à explorer :** représenter séparément au moins les
notions suivantes, sans préjuger de leur implémentation technique :

- **rôle/institution** : pourquoi une obligation peut exister;
- **engagement ou obligation** : ce qui doit ou devrait être satisfait;
- **spécification temporelle** : instant, fenêtre, durée, échéance, récurrence,
  exceptions;
- **lieu/cible/conditions** : où et sous quelles contraintes l'engagement compte;
- **priorité et conséquences** : ce qui se passe s'il entre en conflit ou est
  manqué;
- **représentation subjective** : ce que l'agent sait, croit, accepte ou prévoit;
- **plan/intention** : comment l'agent essaie éventuellement de le satisfaire;
- **actions exécutables** : se préparer, traverser, travailler, attendre, etc.,
  toujours validées par le moteur.

Cas de falsification communs : quart de travail, cours récurrent, rendez-vous,
réservation, cérémonie, corvée périodique, train à heure fixe, échéance de
projet, prise de médicament prescrite, visite planifiée. Une abstraction qui ne
sert qu'au travail de Sophie est insuffisamment générale.

Ce sujet reste **R&D futur**. Il ne doit pas être implanté pendant le rodage en
cours et ce document ne choisit ni schéma, ni scheduler, ni service propriétaire.

### Cas adversariaux initiaux

Ces cas ne demandent pas tous une prise en charge immédiate. Ils servent à
chercher quelles abstractions cassent.

- un même agent contrôle plusieurs corps simultanément;
- un même corps reçoit plusieurs sources de contrôle distinctes;
- une créature se divise en deux puis fusionne;
- un gaz sentient occupe plusieurs lieux à la fois;
- une maison sentiente contient d'autres agents;
- un parasite intelligent agit à travers le corps de son hôte;
- une IA sans corps agit via plusieurs machines;
- une capacité n'existe que tant qu'une relation ou un serment tient;
- deux entités n'ont une capacité que lorsqu'elles coopèrent;
- un vêtement confère une capacité seulement à une morphologie compatible;
- une transformation corporelle rend l'équipement porté incompatible;
- un objet physiquement ordinaire est sacré pour certains agents seulement;
- le même aliment nourrit A, empoisonne B et est indigestible pour C;
- le même marteau est outil, arme improvisée ou objet rituel selon l'action et
  le contexte, sans changer d'identité physique;
- un espace est plus grand à l'intérieur qu'à l'extérieur;
- un objet occupe partiellement deux espaces ou dimensions;
- une créature perçoit une modalité absente chez l'humain sans devenir
  omnisciente;
- un signal existe physiquement mais le récepteur manque du capteur, de la
  langue ou de la clé nécessaires;
- une transformation change les capacités sans changer l'identité;
- une transformation produit au contraire une nouvelle identité;
- un portail exige simultanément heure, météo, ressource, objet et permission;
- deux régions d'un même monde appliquent des régimes causaux différents;
- un véhicule est à la fois agent autonome, contenant de passagers et moyen de
  déplacement;
- un organisme non sapient possède une compétence très spécialisée supérieure
  à celle de certains agents sapients;
- un agent sapient subit temporairement une forte réduction d'une capacité
  cognitive sans changer d'espèce;
- une colonie biologique rend la frontière de l'« individu » contextuelle;
- deux clones partagent la même mémoire initiale puis divergent;
- une copie de mémoire transfère de l'information sans nécessairement transférer
  l'identité;
- un feu, une inondation ou un autre processus autonome produit des effets sans
  intention d'agent;
- une malédiction ou un piège dormant réagit à un événement futur sans LLM;
- un environnement rend une capacité disponible ou indisponible : parole sous
  l'eau, respiration en atmosphère incompatible, locomotion sous gravité
  différente;
- un rôle professionnel reste identique alors que les tâches, horaires et lieux
  changent totalement;
- deux agents ont le même rendez-vous objectif, mais un seul en a connaissance;
- une occurrence d'un engagement récurrent est annulée sans supprimer les
  occurrences futures;
- un objet change de rôle fonctionnel au cours d'une même scène sans changer de
  type ni d'identité.

### Relations métamorphiques candidates

Le futur benchmark de généralité devrait préférer des propriétés invariantes à
une collection de scripts « le personnage X doit faire Y ».

1. renommer une espèce ou catégorie **explicitement non causale** sans changer
   les propriétés causales pertinentes ne doit pas changer la faisabilité
   objective;
2. modifier uniquement une description d'apparence ne doit pas conférer ou
   retirer une capacité;
3. ajouter une signification religieuse ou symbolique à un objet ne doit pas
   modifier sa physique, sauf loi de monde explicitement causale;
4. retirer une capacité requise doit faire refuser l'action sans mutation
   canonique partielle;
5. deux configurations causalement équivalentes doivent produire le même
   résultat moteur, même si leurs templates nominaux diffèrent;
6. ajouter une propriété non pertinente à un scénario ne doit pas en changer le
   résultat;
7. changer une propriété causalement pertinente en conservant tous les labels
   doit modifier le résultat lorsque le contrat le prévoit;
8. une transformation corporelle doit faire réévaluer les possibilités futures
   sans réécrire les événements antérieurs;
9. un signal non perceptible par un agent ne doit pas apparaître spontanément
   dans sa cognition;
10. une parole fausse peut produire des conséquences sociales, mais ne doit pas
    transformer son contenu propositionnel en fait canonique;
11. une suggestion LLM ne peut jamais rendre exécutable une action refusée par
    les règles canoniques;
12. réordonner deux actions réellement indépendantes devrait conserver le même
    état final; réordonner des actions dépendantes peut légitimement changer le
    résultat;
13. lorsqu'un modèle revendique l'invariance au partitionnement temporel,
    découper un même segment causal en sous-segments doit conserver le résultat;
14. deux chemins de ressource arrivant au même état pertinent doivent produire
    la même faisabilité si l'historique n'est pas déclaré causal;
15. copier les propriétés physiques d'un objet sans copier sa propriété, son
    histoire ou son statut symbolique doit préserver les effets physiques tout
    en permettant des effets sociaux différents;
16. supprimer une occurrence d'un engagement récurrent ne doit pas supprimer les
    autres occurrences si la règle de récurrence reste inchangée;
17. deux agents exposés au même signal objectif peuvent légitimement former des
    perceptions différentes si leurs canaux ou connaissances diffèrent.

### Grille de revue de généralité

Avant de transformer une nouvelle feature en spécification ou en code, la revue
R&D peut poser les questions suivantes :

1. quelles propriétés sont réellement causales et lesquelles sont seulement des
   labels, descriptions ou vues ?
2. quelle partie relève de Reality, de l'accès/interaction, ou de la cognition
   subjective ?
3. la possibilité objective dépend-elle d'une relation acteur–cible–milieu plutôt
   que d'une propriété isolée ?
4. s'agit-il d'une action initiée, d'un processus autonome, d'un événement ou
   d'une transformation ?
5. le même mécanisme explique-t-il au moins deux ou trois cas indépendants ?
6. quel cas adversarial le casse immédiatement ?
7. quelle relation métamorphique devrait rester vraie après un renommage ou une
   variation non causale ?
8. quelle modification causale devrait au contraire changer le résultat ?
9. quelles informations un agent peut-il réellement percevoir ou connaître ?
10. une règle sociale, symbolique ou magique exerce-t-elle un effet objectif, et
    si oui où cette causalité est-elle explicitement déclarée ?

### Stratégie de test proposée, sans choix d'architecture

Le programme ne doit pas canoniser un fichier `bench.py` ou un outil particulier.
La frontière fonctionnelle recherchée est : état jetable ou reproductible, temps
contrôlé, actions passant par les contrats canoniques, refus observables,
provenance et digest/rejeu vérifiables.

L'étude de généralité peut ensuite procéder par niveaux :

1. **cas unitaires représentatifs** pour chaque axe de stress;
2. **combinaisons `t-way`** de propriétés relativement orthogonales afin de
   chercher les interactions sans explosion cartésienne;
3. **combinaisons ordonnées** lorsque la séquence crée l'état qui déclenche le
   défaut;
4. **relations métamorphiques** lorsque l'oracle exact est inconnu mais qu'une
   transformation du scénario devrait préserver ou modifier un résultat connu;
5. **cas adversariaux composés** issus du corpus et de générations nouvelles;
6. **cas-limites déclarés non supportés** lorsque le modèle causal de RIC ne
   peut pas représenter honnêtement un univers donné.

La représentation technique de ces cas, leur stockage, leur schéma, le niveau
de génération automatique et leur ordre d'intégration relèvent d'une décision
Codex ultérieure. Cette note ne choisit aucune architecture.
