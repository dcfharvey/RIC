# Vivarium Social — Mémoire de travail de l’assistante

> Document interne de continuité.
> Statuts : **PROPOSÉ**, **DÉCIDÉ**, **IMPLÉMENTÉ**, **À VALIDER**.

Dernière mise à jour : 2026-08-04

## Vision

**DÉCIDÉ**

Vivarium social textuel persistant avec quatre habitantes adultes autonomes dans une résidence. Le propriétaire est une entité supérieure connue. Le moteur local est l’unique autorité canonique. Le LLM propose des intentions, interprétations et dialogues, mais ne modifie jamais directement le monde. Discord viendra plus tard comme interface principale.

## Principe central

> Réalité canonique → perception → interprétation ou croyance → mémoire → émotion → décision → comportement observable

Un personnage ne doit jamais décider à partir d’informations qu’il ne possède pas.

## Monde

**DÉCIDÉ**

- Temps réel 1:1 lorsque le monde est actif.
- Monde actif ou en pause.
- Autonomie complète, sauf quitter entièrement le vivarium sans en parler au propriétaire.
- Monde extérieur abstrait plus tard.
- Pas de vieillissement, maladie, mort ou grossesse dans le MVP.
- Blessures permises.
- Relations possibles : amitié, romance, colocation.
- Traits cachés révélés par le comportement.

## Résidence

**IMPLÉMENTÉ**

Lieux : salon, cuisine, salle de bain, cour, couloir et quatre chambres.

Le graphe des déplacements est dirigé et le moteur calcule les trajets.

## Chambres et intimité

**DÉCIDÉ**

Chaque chambre appartient canoniquement à une habitante et constitue son espace personnel.

La norme sociale dit que les autres ne devraient pas y entrer librement, mais ce n’est pas une barrière magique. Un personnage fouineur ou irrespectueux peut transgresser cette norme.

Une porte peut être ouverte, fermée ou verrouillée. Un personnage prudent aura tendance à fermer ou verrouiller sa chambre.

Une habitante peut inviter quelqu’un, se présenter sans invitation ou s’inviter selon sa personnalité et le contexte.

Frapper à une porte est une action élémentaire ordinaire, comme ouvrir le frigo.

Désactiver l’affichage des scènes privées empêche leur affichage spontané, mais le propriétaire conserve un accès explicite.

**À VALIDER**

- Ce que les habitantes savent des capacités d’observation du propriétaire.
- Permissions temporaires ou permanentes.
- Clés et règles de verrouillage.
- Distinction entre audace sociale, intrusion et violation grave.

## Personnages déterministes

**IMPLÉMENTÉ**

Quatre personnages adultes persistants possèdent une position canonique.

Besoins : satiété, repos, énergie, hygiène.

Activités : manger, dormir, se reposer, se laver, attendre.

Les calculs utilisent des entiers à précision fixe. La politique déterministe choisit des activités selon les besoins. Les simulations sont reproductibles.

## Blessures

**IMPLÉMENTÉ — 3.3B1**

Une blessure possède une cause canonique, une sévérité, un instant d’apparition, un régime de récupération, une guérison exacte et un historique conservé.

Une seule blessure active par personnage. Les blessures guéries sont immuables.

La récupération varie selon l’activité : passive, repos, sommeil.

**EN COURS — 3.3B2**

- effets sur la mobilité;
- coût énergétique d’une blessure modérée;
- blocage du déplacement autonome en blessure grave;
- activités locales encore possibles;
- attente dynamique lorsqu’un personnage est coincé;
- intégration à la politique;
- ordre exact des frontières temporelles simultanées.

**BUT ARCHITECTURAL**

La blessure sert de banc d’essai :

> cause → état persistant → évolution temporelle → effets mécaniques → résolution → historique

Les maladies sont volontairement mises de côté. Usage concret prévu : blessures d’entraînement et accidents temporaires.

## Émotions

**PROPOSÉ — NON DÉCIDÉ**

Les émotions ne doivent pas être une seule jauge d’humeur.

Structure envisagée :

1. événement perçu;
2. interprétation subjective;
3. évaluation selon personnalité, besoins, relation, souvenirs et contexte;
4. modification émotionnelle;
5. influence sur les décisions;
6. expression comportementale et verbale.

Distinctions envisagées :

- émotions actives : temporaires, ciblées, causales;
- humeur : lente, diffuse, cumulative;
- dispositions stables : personnalité et tempérament.

Plusieurs émotions peuvent coexister. Une émotion doit être expliquée par ce que le personnage a perçu et cru, pas par la vérité omnisciente du moteur.

Le LLM peut proposer une interprétation structurée et des émotions plausibles. Le moteur valide, borne, applique et journalise.

Familles initiales possibles : joie, tristesse, colère, peur, honte, affection.

**À DÉCIDER**

- taxonomie;
- représentation numérique;
- durée et décroissance;
- cibles et causes multiples;
- interaction avec humeur, personnalité et souvenirs;
- rôle exact du LLM;
- prévention des réactions excessives;
- rumination, excuses, rappels et changements d’interprétation.

## Fiches des habitantes

**À FAIRE AVANT LA COGNITION LLM COMPLÈTE**

Séparer :

- identité;
- personnalité;
- préférences;
- valeurs;
- habitudes;
- physiologie;
- limites;
- objectifs;
- relations;
- conditions temporaires;
- éléments canoniques verrouillés.

La personnalité ne doit pas être un simple texte libre. Les traits structurés influencent les décisions dans des limites connues.

## Perception, croyances et mémoire

**À FAIRE**

Ordre recommandé :

1. perception limitée;
2. intentions LLM structurées;
3. croyances et interprétations;
4. mémoire persistante;
5. relations et vie sociale.

Un personnage peut croire quelque chose de faux sans modifier la réalité canonique.

La mémoire devra conserver au minimum les événements perçus, conversations, promesses, conflits, informations reçues, souvenirs marquants, ainsi que leur source et leur fiabilité.

## Relations et consentement

**À FAIRE**

Dimensions possibles : confiance, familiarité, affection, attirance, respect, ressentiment, jalousie, sécurité et limites personnelles.

Les relations peuvent être asymétriques.

Le consentement doit être situationnel, réversible et lié au contexte, jamais traité comme une permission globale permanente.

## Propriétaire

**DÉCIDÉ EN PRINCIPE**

Le propriétaire peut observer, parler, passer en mode direct, intervenir et modifier le monde.

Toute modification importante d’un personnage doit :

1. expliquer les impacts;
2. créer un snapshot;
3. demander confirmation explicite;
4. journaliser l’intervention.

## Ordre de développement

1. terminer 3.3B2;
2. terminer 3.3C;
3. définir les fiches minimales;
4. ajouter la perception limitée;
5. brancher les intentions LLM structurées;
6. ajouter croyances et interprétations;
7. ajouter mémoire persistante;
8. intégrer mémoire et relations;
9. ajouter émotions sociales et limites;
10. ajouter conversations et scènes;
11. ajouter présence et interventions du propriétaire;
12. brancher Discord;
13. ajouter monde extérieur abstrait;
14. ajouter rattrapage condensé;
15. ajouter technicien diagnostique;
16. longues simulations de stabilisation.

## État technique connu

Commits :

- `1e92a4b` — Phase 0
- `2313367` — correction documentaire rollback
- `af2823c` — Phase 1
- `650af37` — règle `init --force`
- `9377e18` — Phase 2.1
- `ef91b7e` — Phase 2.2
- `3757c05` — Phase 3.1
- `1c87882` — Phase 3.2A
- `d2a625b` — Phase 3.2B
- `3f53e62` — Phase 3.2C
- `fc6dfc1` — Phase 3.3A
- `f1335ca` — Phase 3.3B1

Dernier état confirmé : 164 tests après 3.3B1.

IA exécutante principale : DeepSeek via LM Studio Bionic.

Gemma 4 12B QAT ne doit pas toucher au projet sans validation explicite.

## Méthode de travail

Le propriétaire décide du comportement souhaité et transmet les messages.

L’assistante traduit les décisions en architecture, prépare les instructions, relit les rapports, repère les angles morts et maintient la cohérence.

L’IA exécutante modifie le dépôt, écrit les migrations, code, teste et produit les commits.

## Règles de mise à jour

- Une idée discutée reste **PROPOSÉE**.
- Une règle acceptée devient **DÉCIDÉE**.
- Une fonction codée et testée devient **IMPLÉMENTÉE**.
- Un manque devient **À VALIDER**.
- Chaque implémentation doit ajouter le commit, les invariants et les limites.
- Une explication informelle ne devient jamais une règle officielle sans validation.

## Revue des besoins

**DÉCIDÉ EN PRINCIPE**

Critère général :

> Une chose est probablement un besoin si son absence prolongée crée spontanément une pression interne, même sans objectif explicite.

Un besoin ne dicte jamais directement une action. Il produit une pression. La personnalité, les préférences, les habitudes, les relations, les croyances et le contexte déterminent comment le personnage tente de la satisfaire.

### Besoins fondamentaux mesurés

- **Alimentation** : besoin corporel universel. Les préférences déterminent comment il est satisfait. L’hydratation reste implicite.
- **Sommeil** : pression distincte de l’énergie. Le repos peut restaurer de l’énergie sans effacer toute la dette de sommeil.
- **Hygiène** : pression corporelle et sociale dont les seuils sont individualisés.
- **Sécurité** : physique, sociale, émotionnelle, résidentielle et relationnelle. Peut être globale ou ciblée.
- **Autonomie** : sentiment de contrôler sa vie et de pouvoir faire des choix significatifs. Céder volontairement du contrôle reste une expression possible de l’autonomie.
- **Stimulation** : nouveauté, défi, jeu, apprentissage, création ou exploration. Son manque produit l’ennui.
- **Récupération face à la saturation** : besoin de faible stimulation, d’absence de sollicitation et de contrôle de son attention. Ne signifie pas nécessairement être seul.
- **Présence sociale** : avoir d’autres personnes autour de soi sans obligation d’interagir. La satisfaction dépend de qui est présent.
- **Interaction sociale** : besoin d’échange réel, distinct de la simple présence.

### Besoins généraux avec satisfaction ciblée

- **Intimité** : proximité personnelle et vulnérabilité partagée. Peut être émotionnelle, romantique, physique ou sexuelle, et reste liée à des personnes précises.
- **Appartenance** : besoin général de faire partie de quelque chose, plus liens ciblés envers le foyer, une guilde, un travail, une communauté, une relation, le propriétaire ou un culte.
- **Reconnaissance** : besoin de se sentir considérée, visible et estimée, souvent par des personnes ou institutions précises.

### Pulsions fortement individualisées

- **Activation physique** : agitation ou inconfort lié à l’inactivité, fort chez certains profils et presque absent chez d’autres.
- **Sexualité** : pulsion distincte de l’attirance et du consentement. Une intensité élevée ne produit jamais automatiquement une action envers autrui.
- **Recherche de compétence ou d’efficacité** : se sentir capable d’agir, d’apprendre et d’obtenir des résultats. La progression elle-même appartient aux objectifs.

### États ou ressources, pas des besoins

- énergie;
- douleur;
- blessure;
- confort;
- ennui;
- solitude ressentie;
- saturation sociale;
- humeur.

Le confort est un état dérivé de facteurs comme la température, la douleur, la posture, les vêtements, la fatigue, la faim, le bruit, la blessure et le lieu.

### Éléments classés ailleurs

- progression → objectifs;
- routine sportive → habitudes;
- ambition → personnalité et valeurs;
- aimer être seule → préférence et style social;
- sociabilité → personnalité;
- dévotion envers le propriétaire → valeurs, croyances, relation et appartenance ciblée.

### Distinction sociale fondamentale

La sociabilité et le besoin de solitude ne sont pas les deux extrémités d’un même axe.

Il faut distinguer :

- style social;
- besoin de présence;
- besoin d’interaction;
- besoin de tranquillité ou de faible sollicitation;
- préférence pour certains formats sociaux.

Un personnage peut vouloir être « seul en groupe » : rester dans la même pièce que les autres sans parler ni être sollicité.

## Fondation psychologique générale

**DÉCIDÉ EN PRINCIPE**

Le modèle psychologique de base est désormais considéré comme suffisant pour poursuivre la conception.

Il repose sur les couches suivantes :

- besoins et pressions internes;
- ressources et conditions physiques;
- personnalité;
- attachement;
- valeurs;
- préférences;
- identité;
- objectifs;
- engagements;
- perceptions;
- croyances;
- souvenirs;
- émotions et humeur;
- relations;
- intentions;
- arbitrage décisionnel.

Chaîne générale :

> État du monde → perception → croyance → évaluation → émotion → motifs actifs → objectifs et engagements → options → arbitrage → intention → action → conséquences → mémoire et évolution

Les grandes catégories sont maintenant fixées. Les travaux suivants devront surtout préciser les contrats détaillés de chaque couche plutôt qu’ajouter de nouvelles théories générales.

## Personnalité

**DÉCIDÉ EN PRINCIPE**

La personnalité doit reposer d’abord sur des facteurs larges et bien établis, puis être enrichie seulement lorsqu’une différence comportementale importante ne peut pas être expliquée par le noyau.

### Noyau initial

Big Five :

- extraversion;
- agréabilité;
- conscienciosité;
- ouverture à l’expérience;
- réactivité au stress, utilisée comme formulation pratique du neuroticisme.

Attachement :

- anxiété d’attachement;
- évitement de l’attachement.

Les dimensions sont continues, pas catégorielles.

Les modèles de type MBTI ou « 16 personnalités » ne sont pas retenus comme fondation du système.

### Rôle causal limité

Les Big Five ne doivent pas être traités comme des commandes directes.

Ils modulent des mécanismes plus précis :

- extraversion → initiation sociale et valeur anticipée des interactions;
- conscienciosité → persistance, stabilité des intentions et respect des engagements;
- réactivité au stress → sensibilité aux menaces et intensité des évaluations négatives;
- agréabilité → disposition conciliante, prise en compte d’autrui et coût subjectif du conflit;
- ouverture → variété des options envisagées et tolérance à la nouveauté;
- anxiété d’attachement → sensibilité au rejet et besoin de réassurance;
- évitement d’attachement → coût subjectif de la dépendance et de la vulnérabilité.

L’attachement peut varier partiellement selon la relation.

### Facettes ultérieures

Des facettes plus étroites peuvent être ajoutées plus tard lorsqu’elles expliquent un comportement important que le noyau ne distingue pas assez bien.

Exemples possibles :

- rumination;
- franchise;
- chaleur;
- compétitivité;
- fierté;
- indépendance;
- patience;
- perspicacité sociale;
- tolérance à la frustration;
- sensibilité au rejet.

Aucune facette ne doit être ajoutée seulement pour enrichir une fiche de manière décorative.

## Valeurs

**DÉCIDÉ EN PRINCIPE**

Les valeurs représentent ce que le personnage considère important, juste, admirable ou inacceptable.

Elles sont distinctes des besoins et de la personnalité.

Noyau retenu :

1. autonomie;
2. loyauté;
3. bienveillance;
4. justice;
5. honnêteté;
6. respect des limites;
7. devoir et responsabilité;
8. accomplissement;
9. sécurité et stabilité;
10. exploration et liberté;
11. tradition et appartenance;
12. pouvoir et statut.

Les valeurs peuvent avoir une importance générale et des formes ciblées envers une personne, un groupe ou une institution.

Exemples :

- loyauté générale élevée;
- loyauté exceptionnelle envers le propriétaire;
- faible loyauté envers un employeur;
- respect élevé de l’intimité d’autrui;
- forte valeur de stabilité appliquée au foyer.

Les personnages peuvent être incohérents, appliquer une valeur différemment selon les cibles ou protéger davantage leur propre autonomie que celle des autres.

### Force normative

Les valeurs ne sont pas toutes de simples bonus ou pénalités.

Il faut distinguer :

- valeur souple → influence une évaluation;
- principe fort → exige une justification exceptionnelle pour être violé;
- limite personnelle → bloque normalement l’option pour ce personnage;
- contrainte canonique → rend réellement l’action impossible dans le moteur.

Une valeur ou limite psychologique peut être transgressée sous pression, avec conséquences émotionnelles et relationnelles. Une contrainte canonique ne peut pas être contournée par le LLM.

## Objectifs et engagements

**DÉCIDÉ EN PRINCIPE**

Un objectif représente un état futur qu’un personnage cherche activement à provoquer ou éviter.

Familles retenues :

- objectifs immédiats;
- objectifs personnels persistants;
- objectifs sociaux ou relationnels;
- objectifs défensifs ou d’évitement;
- projets collectifs.

Chaque objectif doit avoir une provenance explicable :

- besoin;
- valeur;
- relation;
- émotion;
- événement;
- instruction;
- engagement antérieur.

Propriétés minimales :

- type;
- cible;
- importance;
- urgence;
- origine;
- visibilité;
- état;
- date de création;
- conditions de réussite;
- conditions d’abandon;
- possibilité de report.

L’importance et l’urgence sont distinctes.

### Objectif, intention et action

- objectif → destination poursuivie;
- intention → plan adopté maintenant;
- action → opération réellement exécutée.

Le LLM peut proposer des intentions et actions compatibles avec les objectifs existants, mais ne doit pas inventer constamment de nouveaux objectifs persistants sans justification.

### Engagements

Un engagement représente une obligation envers soi-même, une personne, un groupe, une institution ou le propriétaire.

Exemples :

- promesse;
- rendez-vous;
- tâche domestique acceptée;
- horaire de travail;
- séance planifiée;
- règle acceptée;
- secret à garder;
- faveur à rendre.

Propriétés minimales :

- parties concernées;
- contenu;
- échéance;
- niveau d’obligation;
- conditions;
- statut;
- conséquences anticipées d’une rupture.

Un engagement ne force jamais magiquement une action.

Le personnage peut :

- le respecter;
- le reporter;
- l’oublier;
- être incapable de le remplir;
- le rompre volontairement;
- prévenir l’autre;
- mentir sur la raison;
- tenter de réparer ensuite.

Le moteur conserve le fait de l’engagement et son résultat. La psychologie décide de la conduite.

## Arbitrage décisionnel

**DÉCIDÉ EN PRINCIPE**

Le modèle doit éviter :

- qu’un seul besoin élevé gagne toujours;
- qu’un score opaque décide de tout;
- qu’un LLM choisisse librement puis rationalise après coup.

### Architecture corrigée

1. matérialiser l’état canonique;
2. construire le monde subjectif du personnage;
3. détecter les changements pertinents;
4. vérifier si une intention active peut continuer;
5. recenser besoins, émotions, objectifs, engagements et tensions;
6. générer un petit ensemble d’options plausibles;
7. éliminer les options canoniquement impossibles;
8. identifier les violations de principes et limites personnelles;
9. estimer coûts, bénéfices, risques et conséquences selon les croyances du personnage;
10. comparer les options sans exiger une optimisation parfaite;
11. maintenir, réviser, choisir ou composer une intention;
12. valider et exécuter l’action dans le moteur;
13. produire perceptions, conséquences, émotions et souvenirs.

### Stabilité des intentions

Une intention adoptée persiste par défaut.

Elle n’est réouverte que lorsqu’un déclencheur pertinent survient :

- obstacle;
- blessure;
- urgence;
- nouvelle information;
- conflit d’engagement;
- changement émotionnel important;
- demande sociale significative;
- échéance manquée.

Cela évite de recalculer entièrement la vie du personnage à chaque instant.

### Contraintes dures

Avant toute psychologie, le moteur élimine les actions impossibles :

- action physiquement impossible;
- lieu inaccessible;
- porte verrouillée sans moyen d’accès;
- ressource nécessaire absente;
- blessure incompatible;
- consentement requis mais absent;
- règle canonique bloquante.

Le LLM ne peut pas justifier une impossibilité.

### Profil d’évaluation

Chaque option doit être décrite par un profil explicable plutôt que par un seul score visible :

- faisabilité;
- urgence;
- besoins concernés;
- objectifs servis;
- engagements affectés;
- principes respectés ou violés;
- coût physique;
- coût psychologique;
- risques;
- conséquences relationnelles anticipées;
- préférences;
- compatibilité avec l’intention active.

Un score technique interne peut servir au départage, mais ne doit pas masquer une violation importante.

### Émotions

Les émotions interviennent avant et après la décision.

Chaîne :

> événement perçu → évaluation subjective → émotion → options et priorités modifiées → décision → résultat → nouvelle évaluation émotionnelle

Une émotion peut :

- attirer l’attention;
- créer une urgence subjective;
- produire une tendance à l’action;
- modifier les risques perçus;
- générer un objectif;
- modifier les options envisagées.

### Rationalité limitée

Le personnage ne connaît pas tout et n’examine pas toutes les possibilités.

Le nombre d’options et la qualité de la délibération peuvent être réduits par :

- fatigue;
- stress;
- urgence;
- impulsivité;
- information incomplète;
- croyances erronées.

Entre deux options proches, une variabilité pseudo-aléatoire reproductible peut intervenir.

### Niveaux de délibération

Réactions routinières :

- généralement sans LLM;
- besoins corporels;
- routines simples;
- actions répétitives.

Choix ordinaires :

- politique structurée;
- appel LLM facultatif et limité.

Décisions importantes :

- contexte plus large;
- appel LLM plus riche;
- audit renforcé.

Exemples :

- rompre une promesse importante;
- révéler un secret;
- confronter quelqu’un;
- commencer ou arrêter une relation;
- modifier un objectif persistant;
- accepter une demande majeure du propriétaire.

### Rôle du LLM

Le LLM intervient surtout pour :

- générer quelques options sociales plausibles;
- interpréter une situation ambiguë;
- composer une solution nuancée;
- proposer une intention structurée;
- formuler paroles et comportement.

Le moteur :

- fournit les motifs actifs;
- fixe les contraintes;
- conserve les objectifs et intentions;
- valide les options;
- évalue;
- sélectionne ou autorise;
- exécute;
- journalise.

Le LLM n’a jamais le dernier mot sur la réalité canonique.

## État de la conception après cette étape

**DÉCIDÉ**

La fondation psychologique et décisionnelle générale est considérée comme suffisante.

Il n’est pas nécessaire d’ajouter maintenant d’autres grandes théories.

Les prochaines étapes doivent transformer les blocs existants en contrats précis et codables, en commençant par :

1. perception;
2. croyances;
3. mémoire;
4. émotions;
5. relations;
6. profils réels des quatre habitantes;
7. calibration des pondérations;
8. règles exactes d’appel au LLM.
