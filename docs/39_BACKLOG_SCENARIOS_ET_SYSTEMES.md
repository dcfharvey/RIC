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
spécification, ni une source scientifique, ni un engagement d'architecture.

Le 13 août 2026, un corpus externe de 23 fichiers texte a été produit avec Qwen
pour ratisser volontairement large : espèces réelles et fictives, actions,
environnements, phénomènes naturels, magie, objets, vêtements, véhicules,
ressources, alimentation, technologie, communication, connaissance, métiers,
jeux et règles, art, guerre et structures sociales. Les recouvrements et erreurs
de taxonomie sont conservés comme matériau utile : le but n'est pas de reprendre
les catégories de Qwen, mais de chercher les mécanismes sous-jacents qui doivent
rester stables lorsque les catégories de surface changent.

### Question de falsification

Pour chaque cas du corpus, poser :

> Peut-on représenter ce cas par composition de mécanismes déjà généraux, sans
> ajouter une règle qui dépend de son nom, de son espèce, de son univers ou de
> sa catégorie narrative ?

Une réponse négative ne signifie pas automatiquement qu'un nouveau système est
nécessaire. Elle signale d'abord un trou d'abstraction à qualifier. Une
abstraction n'est retenue que si plusieurs cas indépendants la justifient.

### Décomposition fonctionnelle provisoire

Les catégories de surface du corpus se réduisent actuellement aux familles de
questions suivantes. Ces familles sont conceptuelles; elles ne prescrivent ni
packages, ni tables, ni classes.

1. **identité et composition** — qu'est-ce qui constitue une entité et qu'est-ce
   qui persiste lorsqu'elle change, se divise, fusionne ou change de support;
2. **état** — quelles propriétés objectives peuvent varier dans le temps;
3. **ressource, stock et flux** — quantité disponible, production, consommation,
   transfert et seuils;
4. **capacité effective** — ce que l'entité peut actuellement faire;
5. **faisabilité relationnelle / affordance** — ce qu'une entité donnée peut
   faire avec une cible ou dans un milieu donné, dans son état actuel;
6. **action et processus** — acteur éventuel, cible, moyen, préconditions,
   durée, coûts, effets et observabilité;
7. **transformation** — changement de forme, matière, état, capacités,
   composition ou identité;
8. **espace, topologie et contenance** — position, voisinage, passage,
   inclusion et mobilité des contenants;
9. **milieu, champ et exposition** — lumière, chaleur, pression, atmosphère,
   radiation, eau, vent ou équivalent fictif;
10. **interface, équipement et attachement** — outil, vêtement, armure,
    prothèse, véhicule ou artefact qui modifie l'interaction possible;
11. **signal, information et canal perceptif** — émission, propagation,
    accessibilité sensorielle et décodage;
12. **connaissance, compétence et apprentissage** — savoir, savoir-faire,
    acquisition, pratique, transmission et oubli;
13. **règle sociale ou institutionnelle** — rôle, autorité, permission,
    consentement, propriété, jeu, loi, convention ou rituel;
14. **agence, contrôle et cycle de vie** — qui décide, qui contrôle quoi,
    autonomie, dépendance, création, disparition et continuité;
15. **régime causal du monde** — lois ou mécanismes propres à un univers ou à
    une région, y compris les effets extraordinaires explicitement déclarés.

### Lecture préliminaire de la couverture actuelle

Cette lecture décrit l'état fonctionnel observé sur la branche de Rodage V2;
elle ne constitue pas un plan d'implantation.

- **Fondation forte : gabarits et composants versionnés.** `templates.py` et le
  registre fournissent déjà une grammaire composable avec provenance gelée.
- **Fondation forte : ressources à bandes et effets.** `resources.py` permet
  déjà à un état de ressource d'activer, limiter ou désactiver une capacité. Le
  cas « hydratation influence une capacité » peut donc devenir une composition
  générale plutôt qu'une exception de personnage.
- **Fondation forte : espace.** Lieux, connecteurs, topologie et contenance sont
  déjà distincts. Cette séparation évite d'assimiler « être dans » à « pouvoir
  traverser ».
- **Fondation partielle : capacités.** Le mécanisme existe par endroits, mais il
  n'y a pas encore de vocabulaire général couvrant locomotion, manipulation,
  perception, communication, cognition, compatibilité d'équipement, etc.
- **Fondation partielle : morphologie.** `body.morphology` est encore
  descriptive et limite le MVP à `bipedal`, `quadrupedal` et `amorphous`.
  Cette énumération ne doit pas devenir la frontière causale finale.
- **Fondation partielle : cognition/agency.** L'agence CAT-0 non sapiente est
  volontairement générique et ne connaît aucune espèce, ce qui est un bon
  précédent. En revanche, `sapient` / `non_sapient` ne suffit pas comme axe
  universel de toutes les capacités cognitives.
- **Fondation partielle : perception.** La séparation fait/perception est forte,
  mais la projection actuelle repose surtout sur co-présence, proximité et
  faits propres. Les canaux sensoriels ou techniques hétérogènes restent à
  étudier.
- **Fondation partielle : action.** Le contrat cognition–moteur protège bien le
  canon, mais le vocabulaire exécutable reste volontairement fermé et l'étage
  d'options autonomes contient encore une liste blanche d'activités MVP.
- **Fondation partielle : objets.** Portabilité, possession physique et
  contenance objet-dans-objet existent. Équipement, ajustement morphologique,
  couverture corporelle, dimensions, masse, fluides et passagers restent hors
  portée explicite des contrats actuels.
- **Fondation partielle : social.** Relations directionnelles, limites et
  permissions explicites existent; les institutions, rôles et règles de jeu
  plus générales restent des cas futurs.
- **À étudier : transformations et identité.** Métamorphose, division, fusion,
  changement de support et continuité d'identité ne doivent pas être réduits à
  un changement d'étiquette.
- **À étudier : contrôle multi-support.** Un esprit dans plusieurs corps, un
  corps sous plusieurs contrôles, une IA distribuée ou un parasite intelligent
  dépassent la possession physique d'objet existante.
- **À étudier : milieux et expositions génériques.** La lumière circadienne est
  un premier cas causal, mais température, pression, atmosphère, immersion,
  radiation et équivalents fictifs ne forment pas encore un mécanisme commun.
- **À étudier : véhicules et habitats mobiles.** Le corpus contient des
  véhicules vivants, autonomes ou habitables; ils combinent locomotion,
  contenance, contrôle et parfois agence.
- **À étudier : régimes causaux locaux.** Une magie ou technologie fictive doit
  pouvoir produire des effets déclarés sans que le récit ou le LLM devienne
  lui-même une autorité canonique.

### Résultats scientifiques et techniques pertinents

La littérature ne fournit pas une ontologie universelle prête à coder. Elle
fournit toutefois plusieurs contraintes utiles.

**Résultat empirique borné.** Warren (1984), dans trois expériences de montée
d'escaliers, montre que la frontière perçue entre « franchissable » et « non
franchissable » varie avec l'ajustement entre les propriétés de la personne et
celles de l'environnement. Des travaux ultérieurs ajoutent notamment force et
flexibilité aux seuls rapports de dimensions corporelles. Cela soutient, dans
ce domaine précis, une lecture relationnelle de la faisabilité.

**Théorie concurrente utile comme inspiration.** Chemero (2003) propose de
concevoir les affordances comme des relations entre capacités de l'animal et
caractéristiques de l'environnement. Cette formulation est une théorie de
psychologie écologique, pas une loi à transposer telle quelle dans RIC. Elle
fournit néanmoins une bonne hypothèse de modélisation pour les questions
« X peut-il faire Y avec Z maintenant ? ».

**Résultat technique sur les actions.** Le « qualification problem » est un
problème classique de représentation de l'action : tenter d'énumérer toutes les
circonstances pouvant empêcher une action ne passe pas à l'échelle. Ginsberg et
Smith (1988) proposent de raisonner avec des contraintes générales de domaine
plutôt qu'avec une liste ouverte d'exceptions spécifiques. PDDL2.1 et PDDL+
montrent par ailleurs que temps, ressources, événements et processus continus
peuvent être représentés explicitement dans des modèles d'action, sans conclure
que RIC doit employer ces langages.

**Résultat technique sur les tests.** NIST SP 800-142 décrit le test combinatoire
`t-way`, utile quand les défauts émergent d'interactions entre quelques facteurs
sans pouvoir parcourir tout le produit cartésien. NIST CSWP 26 étend cette idée
aux combinaisons ordonnées pour les systèmes dont l'état dépend de la séquence
des entrées. Raunak et Olsen (2021) montrent aussi l'intérêt des relations
métamorphiques pour la vérification et la validation de simulations lorsque
l'oracle exact est difficile à définir.

Références déterminantes :

- Warren, W. H. Jr. (1984), *Perceiving affordances: visual guidance of stair
  climbing*, J. Exp. Psychol. Human Perception and Performance, 10(5), 683–703,
  DOI `10.1037/0096-1523.10.5.683`;
- Chemero, A. (2003), *An Outline of a Theory of Affordances*, Ecological
  Psychology, 15(2), 181–195, DOI `10.1207/S15326969ECO1502_5`;
- Ginsberg, M. L. & Smith, D. E. (1988), *Reasoning about action II: The
  qualification problem*, Artificial Intelligence, 35(3), 311–342, DOI
  `10.1016/0004-3702(88)90020-3`;
- Fox, M. & Long, D. (2003), *PDDL2.1: An Extension to PDDL for Expressing
  Temporal Planning Domains*, Journal of Artificial Intelligence Research;
- Fox, M. & Long, D. (2006), *Modelling Mixed Discrete-Continuous Domains for
  Planning (PDDL+)*, Journal of Artificial Intelligence Research;
- Kuhn, D. R., Kacker, R. N. & Lei, Y. (2010), *Practical Combinatorial
  Testing*, NIST SP 800-142, DOI `10.6028/NIST.SP.800-142`;
- Kuhn, D. R., Raunak, M. S. & Kacker, R. N. (2022), *Ordered t-way
  Combinations for Testing State-based Systems*, NIST CSWP 26, DOI
  `10.6028/NIST.CSWP.26`;
- Raunak, M. S. & Olsen, M. (2021), *Metamorphic Testing on the Continuum of
  Verification and Validation of Simulation Models*, IEEE/ACM MET 2021, DOI
  `10.1109/MET52542.2021.00015`.

### Hypothèses de modélisation à falsifier

Ces propositions sont des hypothèses R&D, pas des faits scientifiques :

1. une capacité nominale n'est pas nécessairement une capacité effective;
2. la faisabilité d'une action est souvent relationnelle : acteur + état + cible
   + milieu + interface + règle pertinente;
3. espèce, apparence, métier et catégorie d'objet peuvent fournir des presets ou
   des informations descriptives, mais ne doivent pas remplacer les propriétés
   causales quand celles-ci sont disponibles;
4. une transformation doit modifier les propriétés concernées sans réécrire
   rétroactivement la provenance ni l'histoire;
5. un effet extraordinaire reste une cause du monde à déclarer et valider; sa
   description narrative ne lui donne aucune autorité;
6. sens symbolique, croyance, réputation et valeur sociale doivent rester
   séparables des propriétés physiques du même support;
7. la compétence et l'information accessible doivent pouvoir limiter une action
   même si la morphologie et l'énergie la rendent physiquement possible;
8. des capacités peuvent être conjointes ou relationnelles et ne pas appartenir
   exclusivement à une seule entité.

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
  différente.

### Relations métamorphiques candidates

Le futur benchmark de généralité devrait préférer des propriétés invariantes à
une collection de scripts « le personnage X doit faire Y ».

1. renommer l'espèce ou la catégorie narrative sans changer les propriétés
   causales pertinentes ne doit pas changer la faisabilité physique;
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
7. une transformation corporelle doit faire réévaluer les possibilités futures
   sans réécrire les événements antérieurs;
8. un signal non perceptible par un agent ne doit pas apparaître spontanément
   dans sa cognition;
9. une parole fausse peut produire des conséquences sociales, mais ne doit pas
   transformer son contenu propositionnel en fait canonique;
10. une suggestion LLM ne peut jamais rendre exécutable une action refusée par
    les règles canoniques;
11. réordonner deux actions réellement indépendantes devrait conserver le même
    état final; réordonner des actions dépendantes peut légitimement changer le
    résultat;
12. lorsqu'un modèle revendique l'invariance au partitionnement temporel,
    découper un même segment causal en sous-segments doit conserver le résultat;
13. deux chemins de ressource arrivant au même état pertinent doivent produire
    la même affordance si l'historique n'est pas déclaré causal;
14. copier les propriétés physiques d'un objet sans copier sa propriété, son
    histoire ou son statut symbolique doit préserver les effets physiques tout
    en permettant des effets sociaux différents.

### Stratégie de banc proposée, sans choix d'architecture

Le banc existant reste la bonne frontière : base jetable, temps contrôlé,
actions via APIs canoniques, refus observables et digest reproductible.
L'extension de généralité peut être étudiée par niveaux :

1. **cas unitaires représentatifs** pour chaque axe fonctionnel;
2. **combinaisons `t-way`** de propriétés orthogonales afin de chercher les
   interactions sans explosion cartésienne;
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
