# Vivarium Social — Mémoire de travail de l’assistante

**Version :** 4.0  
**Date :** 4 août 2026  
**Statut :** document interne de continuité, d’architecture et de préparation  
**Public principal :** l’assistante architecte  

> Ce document conserve l’état du projet, les décisions, les propositions techniques, les dépendances, les risques et les prochaines étapes. Il n’est pas automatiquement normatif pour l’IA programmeuse : toute proposition destinée au dépôt doit être transférée dans le dossier maître ou approuvée comme demande de changement.

## 0. Règles de lecture

Statuts utilisés :

- **IMPLÉMENTÉ** : présent dans le code et couvert par des tests connus.
- **DÉCIDÉ** : choix explicite du propriétaire.
- **DÉCIDÉ EN PRINCIPE** : direction acceptée; les détails techniques restent à spécifier.
- **PROPOSÉ** : recommandation de l’assistante, non encore transformée en décision autoritative.
- **À VALIDER** : choix dépendant du goût, de l’expérience souhaitée ou d’une préférence du propriétaire.
- **DIFFÉRÉ** : exclu du MVP ou repoussé jusqu’à ce qu’un besoin réel apparaisse.

En cas de conflit :

1. Les décisions explicites les plus récentes du propriétaire prévalent dans cette mémoire.
2. Le dossier maître du dépôt reste la source normative de l’IA programmeuse tant qu’une demande de changement n’a pas été intégrée.
3. Le code et les migrations validés décrivent ce qui est réellement implémenté.
4. Une proposition de cette mémoire ne doit jamais être présentée comme déjà codée.

---

# Partie A — État global du projet

## 1. Vision du produit

**DÉCIDÉ**

Le projet est un vivarium social textuel persistant avec quatre habitantes adultes autonomes vivant dans une résidence.

L’expérience recherchée n’est ni un simple groupe de chat, ni un roleplay sans continuité, ni une reproduction graphique des Sims. Les personnages doivent continuer d’exister entre les interactions, prendre des initiatives, conserver une subjectivité, évoluer et produire une vie sociale émergente.

Le propriétaire est une entité supérieure connue. Il peut observer, communiquer, se manifester et administrer le monde.

Le moteur local est l’unique autorité canonique.

> Le LLM propose, interprète et dialogue. Le moteur valide, applique et possède la réalité.

Discord doit devenir l’interface principale du MVP. Le monde, les données et les décisions validées restent locaux.

## 2. Invariants conceptuels majeurs

**DÉCIDÉ**

- Quatre personnages actifs exactement dans le MVP.
- Tous les personnages sont explicitement adultes.
- Temps réel 1:1 lorsque le monde est actif.
- Pause possible.
- Rattrapage condensé après une période hors ligne; jamais un appel LLM par minute manquée.
- Pas de vieillissement, maladie, grossesse, mort ou simulation de ville complète dans le MVP.
- Les blessures causales et récupérables sont permises.
- Les personnages peuvent sortir de la résidence vers un extérieur abstrait.
- Elles ne peuvent quitter définitivement le vivarium sans discussion et décision du propriétaire.
- Les scènes continuent indépendamment de leur affichage.
- Le propriétaire peut consulter explicitement une scène privée même si son affichage spontané est désactivé.
- Les modifications directes importantes d’un personnage exigent analyse d’impact, snapshot, confirmation et audit.
- Une croyance fausse peut exister sans modifier la vérité canonique.
- Une donnée cachée d’un personnage ne doit pas être transmise à un autre personnage.
- Le LLM ne peut jamais écrire directement dans la base canonique.

## 3. État technique connu

### 3.1 Phases livrées

**IMPLÉMENTÉ**

- Phase 0 : dépôt, environnement et tests initiaux.
- Phase 1 : SQLite, monde, migrations, événements canoniques append-only et autorité du moteur.
- Phase 2.1 : horloge dérivée 1:1, pause et reprise atomiques, lectures sans écritures.
- Phase 2.2 : couloir, graphe dirigé des lieux et calcul de chemin.
- Phase 3.1 : quatre personnages persistants et position canonique.
- Phase 3.2A : besoins à précision fixe.
- Phase 3.2B : activités et effets temporels.
- Phase 3.2C : politique déterministe et simulation reproductible.
- Phase 3.3A : attente dynamique et sommeil naturel.
- Phase 3.3B1 : blessures persistantes, causalité, récupération et guérison exacte.

### 3.2 Prochain lot

**EN COURS / À IMPLÉMENTER**

Sous-lot 3.3B2 : effets des blessures sur la mobilité, l’énergie, les activités, la politique et la simulation.

Puis :

- 3.3C : validation finale reproductible de la Phase 3.
- Attribution canonique des chambres et premières propriétés spatiales nécessaires à la Phase 4.

### 3.3 Commits connus

- `1e92a4b` — Phase 0
- `2313367` — correction documentaire rollback
- `af2823c` — Phase 1
- `650af37` — règle destructive `init --force`
- `9377e18` — Phase 2.1
- `ef91b7e` — Phase 2.2
- `3757c05` — Phase 3.1
- `1c87882` — Phase 3.2A
- `d2a625b` — Phase 3.2B
- `3f53e62` — Phase 3.2C
- `fc6dfc1` — Phase 3.3A
- `f1335ca` — Phase 3.3B1

Dernier état confirmé : **164 tests** après 3.3B1.

IA exécutante principale : DeepSeek via LM Studio Bionic.

Le modèle local Gemma 4 12B QAT ne doit pas modifier le projet sans validation explicite.

---

# Partie B — Monde, espace et vie quotidienne

## 4. Résidence

**IMPLÉMENTÉ**

Lieux actuels :

- salon;
- cuisine;
- salle de bain;
- cour;
- couloir;
- chambre 1;
- chambre 2;
- chambre 3;
- chambre 4.

Le graphe de déplacement est dirigé. Le moteur calcule les trajets et conserve une position canonique unique par personnage.

Objets seedés connus : table, chaise, lit.

## 5. Chambres, propriété et intimité

**DÉCIDÉ**

Chaque chambre appartient canoniquement à une habitante. C’est son espace personnel.

La norme sociale dit que les autres ne devraient pas y entrer librement. Cette norme n’est pas une barrière magique : un personnage curieux, fouineur, impulsif ou irrespectueux peut la transgresser si la porte et la situation le permettent.

Une porte peut être ouverte, fermée ou verrouillée.

Un personnage prudent peut fermer ou verrouiller sa chambre par habitude.

Une personne peut :

- inviter quelqu’un;
- demander à entrer sans invitation préalable;
- entrer avec permission;
- entrer sans permission;
- tenter de s’imposer;
- refuser ou retirer une permission.

Frapper à une porte est une action élémentaire ordinaire, comme ouvrir le réfrigérateur. L’importance sociale dépend du contexte, pas du niveau technique de l’action.

### 5.1 Proposition de représentation minimale

**PROPOSÉ**

Une chambre devrait posséder :

- un occupant assigné;
- un niveau d’intimité du lieu;
- une porte et son état;
- éventuellement une serrure;
- une politique sociale dérivée de l’occupante;
- des permissions ciblées et temporaires lorsque nécessaire.

La propriété ne doit pas automatiquement devenir une interdiction physique. Elle sert à l’interprétation sociale, aux attentes et aux conséquences relationnelles.

### 5.2 Points non bloquants à décider plus tard

**À VALIDER**

- Ce que les habitantes savent exactement du pouvoir d’observation du propriétaire.
- Existence de doubles de clés ou permissions permanentes.
- Niveau de détail des serrures et contournements.
- Gravité sociale par défaut d’une intrusion.

Ces décisions ne bloquent pas la Phase 4 si le moteur sépare déjà accès physique, permission sociale et perception.

---

# Partie C — Fondation psychologique

## 6. Principe général

**DÉCIDÉ**

La fondation psychologique générale est considérée comme suffisante. Il n’est pas nécessaire d’ajouter maintenant d’autres grandes théories.

Chaîne fonctionnelle :

> État du monde → perception → croyance → évaluation → émotion → motifs actifs → objectifs et engagements → options → arbitrage → intention → action → conséquences → mémoire et évolution

Les concepts restent séparés :

- besoins : pressions internes;
- ressources et conditions : capacité actuelle;
- personnalité : tendances générales;
- valeurs : ce qui est important ou normatif;
- préférences : ce qui plaît ou déplaît;
- objectifs : états futurs poursuivis;
- engagements : obligations reconnues;
- perceptions : accès subjectif aux manifestations du monde;
- croyances : propositions tenues pour vraies avec provenance;
- souvenirs : représentations récupérables d’expériences ou d’informations;
- émotions : réponses temporaires à une évaluation;
- humeur : fond affectif plus lent;
- relations : états ciblés et directionnels;
- intention : plan adopté maintenant;
- action : opération soumise au moteur.

## 7. Besoins

**DÉCIDÉ EN PRINCIPE**

Critère : une chose est probablement un besoin si son absence prolongée crée spontanément une pression interne, même sans objectif explicite.

Un besoin ne dicte jamais directement une action.

### 7.1 Besoins fondamentaux mesurés

- alimentation;
- pression de sommeil;
- hygiène;
- sécurité;
- autonomie;
- stimulation;
- récupération face à la saturation;
- présence sociale;
- interaction sociale.

### 7.2 Besoins généraux à satisfaction ciblée

- intimité;
- appartenance;
- reconnaissance.

### 7.3 Pulsions fortement individualisées

- activation physique;
- sexualité;
- recherche de compétence ou d’efficacité.

### 7.4 États ou ressources et non besoins

- énergie;
- douleur;
- blessure;
- confort;
- ennui;
- solitude ressentie;
- saturation sociale;
- stress momentané;
- humeur.

Le confort est dérivé de causes concrètes : température, douleur, posture, vêtements, fatigue, faim, bruit, blessure et lieu.

La sociabilité appartient à la personnalité. Le besoin de présence, le besoin d’interaction et le besoin de tranquillité restent distincts.

Un personnage peut vouloir être « seul en groupe » : proche des autres, sans conversation ni sollicitation.

## 8. Personnalité

**DÉCIDÉ EN PRINCIPE**

### 8.1 Noyau initial

Big Five continus :

- extraversion;
- agréabilité;
- conscienciosité;
- ouverture à l’expérience;
- réactivité au stress.

Attachement :

- anxiété d’attachement;
- évitement de l’attachement.

Les types MBTI ou « 16 personnalités » ne sont pas retenus comme fondation.

### 8.2 Rôle

Les traits ne commandent pas directement les actions. Ils modulent des mécanismes :

- extraversion : initiation sociale et récompense anticipée des interactions;
- agréabilité : prise en compte d’autrui, conciliation et coût du conflit;
- conscienciosité : persistance, organisation et stabilité des intentions;
- ouverture : diversité des options et tolérance à la nouveauté;
- réactivité au stress : sensibilité aux menaces et intensité d’évaluations négatives;
- anxiété d’attachement : sensibilité au rejet et recherche de réassurance;
- évitement d’attachement : inconfort avec dépendance et vulnérabilité.

### 8.3 Facettes ultérieures

**DIFFÉRÉ JUSQU’À BESOIN DÉMONTRÉ**

Exemples : rumination, franchise, chaleur, compétitivité, fierté, indépendance, patience, perspicacité sociale, tolérance à la frustration, sensibilité au rejet.

Une facette ne doit être ajoutée que si elle explique une différence importante non couverte par le noyau.

## 9. Valeurs

**DÉCIDÉ EN PRINCIPE**

Noyau :

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

Les valeurs peuvent être générales ou ciblées envers une personne, un groupe, une institution ou le propriétaire.

Force normative :

- valeur souple : influence l’évaluation;
- principe fort : demande une justification exceptionnelle pour être violé;
- limite personnelle : bloque normalement l’option pour ce personnage;
- contrainte canonique : rend l’action réellement impossible.

Une valeur psychologique peut être transgressée sous pression. La transgression peut produire culpabilité, honte, rationalisation ou changement relationnel. Une contrainte canonique ne peut pas être contournée.

## 10. Objectifs, engagements et intentions

**DÉCIDÉ EN PRINCIPE**

### 10.1 Objectifs

Familles :

- immédiats;
- persistants personnels;
- sociaux ou relationnels;
- défensifs ou d’évitement;
- collectifs.

Chaque objectif doit avoir une origine explicable : besoin, valeur, relation, émotion, événement, instruction ou engagement antérieur.

Propriétés minimales : type, cible, importance, urgence, origine, visibilité, état, conditions de réussite, conditions d’abandon et possibilité de report.

### 10.2 Distinction fonctionnelle

- objectif : destination;
- intention : plan adopté;
- action : opération exécutée;
- résultat : conséquence canonique.

### 10.3 Engagements

Types :

- envers soi;
- envers une personne;
- envers un groupe ou une institution;
- envers le propriétaire.

Un engagement peut être respecté, reporté, oublié, rompu, rendu impossible ou réparé. Il ne force pas magiquement le comportement.

### 10.4 Stabilité des intentions

Une intention active persiste par défaut et n’est réévaluée que lorsqu’un changement pertinent survient : obstacle, blessure, urgence, nouvelle information, conflit d’engagement, changement émotionnel significatif, demande sociale importante ou échéance manquée.

---

# Partie D — Contrats détaillés préparés de façon autonome

Les sections suivantes sont **PROPOSÉES**. Elles traduisent les décisions déjà prises en contrats codables sans trancher les préférences narratives qui appartiennent au propriétaire.

## 11. Actions, événements, manifestations et scènes

### 11.1 Action reconnue

Une action est une demande structurée adressée au moteur. Elle ne devient jamais canonique avant validation.

Chaque définition d’action devrait contenir :

- identifiant de type;
- acteur;
- cible éventuelle;
- lieu requis;
- préconditions;
- ressources nécessaires;
- durée;
- interruptibilité;
- effets canoniques possibles;
- manifestations produites;
- niveau de confidentialité par défaut;
- règles d’idempotence;
- événements de réussite, refus, interruption et échec.

Le catalogue initial devrait rester petit et composable : se déplacer, entrer, sortir, ouvrir, fermer, verrouiller, déverrouiller, frapper, utiliser un objet, commencer ou quitter une activité, inviter, répondre, parler, observer, attendre, laisser un message, rejoindre ou quitter une scène.

### 11.2 Événement canonique

Un événement canonique décrit ce qui s’est effectivement produit.

Il devrait référencer :

- monde;
- séquence;
- heure simulée;
- acteur ou source;
- action ou cause;
- lieu;
- participants;
- résultat structuré;
- niveau de confidentialité;
- événement parent ou causal;
- version de schéma.

Un événement ne doit pas contenir automatiquement toutes les pensées ou interprétations des participants.

### 11.3 Manifestation

Une manifestation est la partie perceptible d’un événement.

Canaux initiaux :

- visuel;
- auditif;
- tactile;
- communication directe;
- effet environnemental.

Exemple : ouvrir un réfrigérateur peut produire une manifestation visuelle pour les personnes qui regardent, un bruit faible pour les personnes proches et une modification canonique de l’état de la porte.

La perception doit être distribuée à partir des manifestations, pas à partir de l’intégralité du payload canonique.

### 11.4 Scène

Une scène est un cadre temporel, spatial, social et confidentiel.

Propriétés minimales :

- identifiant;
- lieu ou canal;
- début et fin;
- participants actifs;
- témoins;
- niveau de confidentialité;
- statut;
- sujet ou contexte facultatif;
- raison de clôture.

Statuts proposés : préparée, active, clôturée, interrompue, annulée.

Une panne ou un arrêt clôture une scène interrompue sans inventer la suite.

Les paroles prononcées sont canoniques. Les pensées proposées par un LLM ne le deviennent que comme état subjectif validé, jamais comme fait public.

## 12. Contrat de perception

### 12.1 Principe

Une perception n’est pas une copie de l’événement. C’est une représentation limitée d’une ou plusieurs manifestations accessibles à un personnage.

Pipeline :

1. déterminer les observateurs physiquement ou socialement admissibles;
2. déterminer quels canaux atteignent chaque observateur;
3. appliquer attention, activité, sommeil, occlusion et confidentialité;
4. déterminer fidélité et complétude;
5. créer une perception immuable liée à l’événement;
6. permettre ensuite une interprétation ou croyance.

### 12.2 Accessibilité et attention

Il faut séparer :

- **accessible** : la manifestation pouvait atteindre le personnage;
- **remarquée** : le personnage l’a effectivement captée;
- **comprise** : le personnage a reconnu ce qu’elle signifiait.

Un personnage peut être dans la même pièce sans remarquer une action discrète. Il peut entendre une voix sans identifier les mots. Il peut voir une action sans comprendre son intention.

### 12.3 Fidélité

Niveaux proposés :

- complète;
- partielle;
- ambiguë;
- signal seulement.

La perception ne doit pas inventer une explication. « Alice a fermé la porte rapidement » est perceptible; « Alice est fâchée » est une interprétation.

### 12.4 Attention et activité

Profils initiaux :

- attentive;
- ordinaire;
- concentrée sur une tâche;
- distraite;
- endormie.

Le sommeil bloque normalement les manifestations faibles, mais un signal très saillant peut réveiller ou produire une perception limitée.

Les seuils doivent être déterministes ou utiliser un tirage pseudo-aléatoire reproductible.

### 12.5 Paroles et confidentialité

Une parole produit une manifestation auditive et éventuellement une communication adressée.

- conversation normale : participants et témoins admissibles;
- murmure : destinataires proches, autres seulement en cas d’écoute plausible;
- message écrit : destinataire et personnes obtenant physiquement ou numériquement accès;
- pensée interne : aucune manifestation publique.

Une porte fermée peut réduire la portée et la fidélité. Une porte verrouillée concerne l’accès physique et n’implique pas automatiquement une meilleure isolation acoustique.

### 12.6 Données minimales d’une perception

- personnage percevant;
- événement source;
- manifestation source;
- heure perçue;
- canal;
- contenu structuré limité;
- fidélité;
- acteurs ou objets reconnus;
- niveau de certitude perceptive;
- contexte spatial;
- statut de confidentialité;
- raison d’admissibilité.

### 12.7 Invariants proposés

- Une perception ne contient jamais une information absente des manifestations accessibles.
- Une personne ne perçoit jamais directement les scores cachés, croyances ou émotions d’une autre.
- Une lecture répétée ne crée pas de nouvelles perceptions.
- L’affichage au propriétaire est indépendant de la perception des habitantes.
- Une perception reste liée à sa source même si l’interprétation change.

### 12.8 Tests préparés

- Deux personnages dans la même pièce : l’une regarde l’action, l’autre est concentrée ailleurs.
- Un coup frappé à une porte est entendu par l’occupante, mais pas par une personne trop éloignée.
- Une conversation derrière une porte fermée produit une perception partielle ou aucune perception selon la règle définie.
- Un objet ajouté imperceptiblement par le propriétaire n’est découvert qu’au moment où un personnage le voit.
- Deux témoins reçoivent des perceptions de fidélité différente sans modifier l’événement canonique.
- Une personne endormie ne reçoit pas une conversation ordinaire comme si elle était éveillée.

## 13. Contrat des croyances

### 13.1 Définition

Une croyance est une proposition qu’un personnage tient pour vraie, fausse ou incertaine, avec une provenance et un niveau de confiance.

Les croyances doivent être structurées lorsqu’elles influencent le moteur. Le texte libre peut servir de résumé, mais ne doit pas être l’unique représentation.

### 13.2 Provenances admises

- perception directe;
- témoignage d’une autre personne;
- message ou document;
- déduction à partir de prémisses;
- communication du propriétaire;
- souvenir consolidé;
- hypothèse personnelle.

Chaque provenance possède une fiabilité subjective, pas une garantie objective.

### 13.3 Structure proposée

- détenteur;
- proposition normalisée;
- polarité : vraie, fausse, indéterminée;
- confiance;
- sources de soutien;
- sources de contradiction;
- date de création;
- dernière révision;
- statut : active, contestée, abandonnée;
- visibilité : privée, partagée, déclarée;
- portée temporelle éventuelle.

### 13.4 Mise à jour

Une nouvelle preuve ne supprime pas silencieusement l’ancienne croyance.

Elle produit :

1. ajout d’une source;
2. réévaluation de la confiance;
3. éventuelle révision de la polarité;
4. événement d’audit `belief_revised`;
5. conséquences émotionnelles ou décisionnelles éventuelles.

Le système doit permettre :

- croyance correcte;
- croyance fausse;
- croyance contestée;
- croyances contradictoires avec confiance proche;
- refus de révision malgré une preuve, si des mécanismes psychologiques le justifient plus tard.

### 13.5 Confiance et témoignage

La force d’un témoignage dépend au minimum de :

- confiance envers la source;
- perception de sa compétence;
- cohérence avec les croyances existantes;
- intérêt supposé de la source à mentir;
- précision de l’information.

Le MVP ne doit pas simuler une logique épistémique complète. Une formule bornée et explicable suffit.

### 13.6 Limites recommandées

- Pas d’imbrication illimitée du type « A croit que B croit que C croit… ».
- Un seul niveau de méta-croyance peut être ajouté quand une scène l’exige.
- Pas de fusion automatique entre croyance et vérité.
- Pas de correction rétroactive des perceptions.

### 13.7 Tests préparés

- Deux témoins forment des croyances différentes à partir du même événement.
- Un personnage croit une rumeur provenant d’une personne de confiance.
- Une preuve directe contredit la rumeur et révise la croyance sans supprimer son historique.
- Un personnage ignore une information qu’il n’a jamais perçue ni reçue.
- Une croyance fausse produit une émotion réelle et un comportement cohérent.

## 14. Contrat de mémoire

### 14.1 Couches

Le MVP devrait séparer :

- traces sources : événements, perceptions, communications et états introspectifs;
- souvenirs épisodiques : représentations d’expériences situées;
- connaissances sémantiques : croyances consolidées;
- souvenirs relationnels : expériences marquantes avec une personne;
- engagements rappelables : promesses et obligations perçues;
- contexte de travail : informations sélectionnées pour la décision actuelle.

Le contexte de travail est dérivé et temporaire. Il ne doit pas devenir une copie permanente de tout ce qui a été envoyé au LLM.

### 14.2 Souvenir épisodique

Propriétés proposées :

- propriétaire du souvenir;
- sources référencées;
- résumé subjectif;
- participants;
- lieu et période;
- thèmes;
- importance personnelle;
- intensité émotionnelle;
- valence;
- confidentialité;
- force d’accessibilité;
- dernière récupération;
- statut de consolidation.

### 14.3 Consolidation

La consolidation ne doit pas avoir lieu après chaque seconde ou action banale.

Déclencheurs possibles :

- fin d’une scène significative;
- événement émotionnellement saillant;
- création ou rupture d’un engagement;
- changement relationnel notable;
- réflexion planifiée;
- traitement quotidien borné.

Le LLM peut résumer des sources, mais sa sortie doit référencer les identifiants sources. Le validateur refuse tout élément sans support.

### 14.4 Rappel

Le rappel doit être ciblé selon :

- personnes présentes;
- sujet;
- objectif actif;
- émotion actuelle;
- lieu;
- engagement;
- récence;
- importance;
- similitude structurée.

Commencer par SQL, index textuel et métadonnées. Les embeddings sont différés tant qu’un besoin réel n’est pas démontré.

### 14.5 Oubli

Le MVP doit d’abord simuler une diminution d’accessibilité, pas la fabrication de faux souvenirs.

- Les sources canoniques ne sont jamais supprimées par l’oubli psychologique.
- Un souvenir peut devenir difficile à rappeler.
- Plusieurs souvenirs banals peuvent être condensés.
- Un souvenir important peut rester accessible longtemps.
- Une correction administrative est auditée et réversible.

La distorsion active, les faux souvenirs spontanés et les reconstructions très créatives sont différés. Elles augmenteraient fortement les risques de contamination et seraient difficiles à tester.

### 14.6 Bornage

Le système doit empêcher la croissance infinie :

- quotas ou budgets par période;
- condensation des événements banals;
- distinction entre sources immuables et résumés remplaçables;
- archivage des souvenirs peu accessibles;
- métriques de taille par personnage;
- aucune conservation automatique de tous les prompts complets dans la mémoire narrative.

### 14.7 Tests préparés

- Une scène significative crée un souvenir qui référence ses perceptions.
- Une routine répétée est condensée au lieu de produire des centaines de souvenirs.
- Une information non perçue n’apparaît pas dans la mémoire.
- Une promesse est rappelée à l’approche de son échéance.
- Un souvenir ancien peu important n’est pas récupéré dans un contexte sans rapport.
- La consolidation par faux LLM ne peut ajouter un fait absent des sources.

## 15. Contrat émotionnel minimal

### 15.1 Structure

Une émotion active est un épisode temporaire relié à une évaluation subjective.

Pipeline :

> événement ou pensée accessible → interprétation → évaluation → émotion → tendance à l’action → expression éventuelle

L’émotion dépend de ce que le personnage croit, même si la croyance est fausse.

### 15.2 Évaluations minimales proposées

- congruence avec un objectif ou besoin;
- gain, perte ou menace;
- contrôle perçu;
- responsabilité ou agent attribué;
- violation d’une norme ou de l’identité;
- nouveauté;
- importance relationnelle;
- possibilité de réparation.

Ces dimensions sont internes au moteur cognitif; elles ne doivent pas toutes être exposées à l’utilisateur.

### 15.3 Familles initiales proposées

- joie / satisfaction;
- soulagement;
- tristesse / déception;
- colère / frustration;
- peur / anxiété;
- honte;
- culpabilité;
- affection / connexion.

Surprise peut être un marqueur bref de nouveauté plutôt qu’un épisode durable.

Jalousie, humiliation, fierté, ressentiment et nostalgie peuvent être traités comme combinaisons d’évaluations et de familles existantes avant de devenir des types distincts.

L’excitation sexuelle reste séparée des émotions générales et du consentement.

### 15.4 Données minimales

- personnage;
- famille;
- cible éventuelle;
- cause et croyances contributrices;
- intensité;
- début;
- profil de décroissance;
- tendance à l’action;
- visibilité ou niveau d’expression;
- état : active, résolue, transformée.

### 15.5 Humeur

L’humeur est plus lente et diffuse. Une première version peut utiliser :

- valence générale;
- activation générale.

Elle est influencée par le sommeil, les besoins, les épisodes émotionnels répétés et le contexte, mais ne remplace pas les émotions ciblées.

### 15.6 Évolution

Une émotion peut diminuer avec le temps, mais aussi être modifiée par :

- nouvelle information;
- présence de la cible;
- excuse crue ou rejetée;
- répétition de l’incident;
- réparation;
- rumination;
- changement de croyance;
- fatigue ou douleur.

Protection obligatoire : une émotion ne doit pas s’auto-amplifier indéfiniment sans nouvelle cause, rappel ou mécanisme explicite.

### 15.7 Rôle du LLM

Le LLM peut proposer :

- une interprétation;
- des évaluations;
- une ou plusieurs émotions plausibles;
- une expression verbale ou comportementale.

Le moteur :

- vérifie les causes accessibles;
- borne les intensités;
- applique les transitions;
- conserve l’historique;
- refuse une émotion fondée sur une information inconnue du personnage.

### 15.8 Tests préparés

- Une croyance fausse déclenche une colère réelle.
- Une excuse crue réduit la colère; la même excuse non crue ne produit pas le même effet.
- Deux personnalités réagissent différemment à une même perception.
- Une personne peu expressive ressent une émotion sans la révéler clairement.
- Une émotion résolue cesse d’influencer directement la décision mais demeure mémorisable.
- Aucun épisode n’apparaît sans cause ou état introspectif explicable.

## 16. Relations, appartenances, limites et consentement

### 16.1 Relations directionnelles

Une relation appartient à A envers B. Elle n’impose aucune symétrie.

Dimensions minimales proposées :

- familiarité;
- confiance;
- affection;
- respect;
- sécurité perçue;
- proximité / intimité;
- attirance;
- irritation / ressentiment.

Ces dimensions doivent rester distinctes. Une personne peut aimer quelqu’un sans lui faire confiance, respecter quelqu’un sans l’apprécier ou se sentir attirée sans se sentir en sécurité.

### 16.2 Ce qui ne devrait pas être un axe relationnel permanent

- jalousie : émotion ou évaluation contextuelle;
- rivalité : rôle ou dynamique ciblée;
- besoin d’attention : besoin ciblé et attente;
- dépendance : état relationnel dérivé;
- consentement : état situationnel;
- soumission ou dévotion : combinaison de valeurs, croyances, appartenance, rôle et relation.

### 16.3 Changements

Tout changement significatif doit :

- avoir une cause;
- être borné;
- être directionnel;
- être historisé;
- tenir compte de la relation antérieure;
- éviter les sauts arbitraires;
- pouvoir être partiellement réparé sans effacer l’incident.

Le LLM ne doit jamais retourner directement « confiance = 82 ». Il propose une interprétation ou un impact qualitatif. Le moteur applique une variation bornée selon des règles.

### 16.4 Appartenances collectives

L’appartenance doit être représentée par un lien entre un personnage et une entité sociale : foyer, guilde, travail, communauté, culte ou organisation.

Propriétés possibles :

- importance identitaire;
- sentiment d’inclusion;
- loyauté;
- fierté;
- obligations;
- sécurité;
- reconnaissance reçue;
- rôle.

Une entité extérieure peut rester abstraite sans simuler tous ses membres.

### 16.5 Limites et permissions

Les limites personnelles sont distinctes des contraintes canoniques.

Le système doit permettre :

- limite personnelle déclarée ou implicite;
- permission ciblée;
- invitation;
- retrait de permission;
- transgression;
- perception de la transgression;
- réaction et conséquences.

### 16.6 Consentement

Le consentement doit être :

- situationnel;
- spécifique;
- réversible;
- lié aux personnes et au contexte;
- distinct d’une relation, d’une attirance ou d’une libido;
- vérifié au moment pertinent.

Aucun score relationnel, besoin, rôle ou engagement ne vaut consentement automatique.

### 16.7 Tests préparés

- A fait confiance à B davantage que B ne fait confiance à A.
- Une intrusion réduit la sécurité et la confiance selon la perception et les valeurs de la personne concernée.
- Une réparation améliore la relation sans effacer l’événement.
- Une forte attirance n’autorise aucune action sans consentement.
- Une appartenance à une guilde influence un choix sans exiger la simulation détaillée de la guilde.
- Une dévotion envers le propriétaire ne supprime pas automatiquement l’autonomie.

## 17. Préférences, habitudes, identité et compétences

### 17.1 Préférences

**PROPOSÉ**

Une préférence indique une valence envers une activité, un objet, une personne, un contexte ou un format social.

Propriétés : domaine, cible, intensité, contexte, origine, plasticité et visibilité.

Une préférence ne doit pas devenir une valeur morale ni un besoin.

### 17.2 Habitudes

**PROPOSÉ**

Une habitude est une tendance apprise à exécuter une action lorsqu’un signal ou contexte se présente.

Propriétés : déclencheur, routine, force, fréquence, dernière exécution, facilité d’interruption et satisfaction associée.

Une habitude se renforce par répétition; elle ne devient pas instantanément un trait de personnalité.

Exemples : verrouiller sa chambre, s’asseoir au même endroit, s’entraîner après le déjeuner, vérifier ses messages avant de dormir.

### 17.3 Identité et rôles

**PROPOSÉ**

Un personnage peut posséder des rôles et auto-descriptions : sportive, travailleuse, membre d’une guilde, protectrice, dévote, colocataire, partenaire.

Les rôles influencent les attentes, objectifs et valeurs, mais ne commandent pas automatiquement les actions.

### 17.4 Compétences

**PROPOSÉ / POSSIBLEMENT DIFFÉRÉ**

Une compétence devient nécessaire seulement lorsqu’elle influence réellement la réussite, la durée ou la qualité d’une action.

Pour le MVP, un système simple par domaine suffit. Éviter un arbre de compétences avant qu’un personnage ou scénario concret ne le nécessite.

L’entraînement peut créer un objectif et une routine avant d’exiger une simulation détaillée de progression athlétique.

## 18. Arbitrage décisionnel

**DÉCIDÉ EN PRINCIPE, CONTRAT PROPOSÉ**

### 18.1 Pipeline

1. matérialiser l’état canonique;
2. construire le monde subjectif;
3. détecter les changements pertinents;
4. vérifier si l’intention active peut continuer;
5. recenser les tensions actives;
6. produire un petit ensemble d’options plausibles;
7. éliminer les options impossibles;
8. identifier les principes et limites affectés;
9. estimer les conséquences selon les croyances du personnage;
10. comparer les options sans optimisation parfaite;
11. maintenir, réviser, choisir ou composer une intention;
12. valider et exécuter l’action;
13. distribuer perceptions et conséquences;
14. mettre à jour émotions, croyances, mémoire, relations et objectifs.

### 18.2 Profil d’évaluation

Chaque option est décrite par :

- faisabilité;
- urgence;
- besoins servis ou aggravés;
- objectifs servis;
- engagements affectés;
- valeurs et limites;
- coûts physiques et psychologiques;
- risques;
- conséquences relationnelles anticipées;
- préférences;
- compatibilité avec l’intention actuelle;
- possibilité de report ou de composition.

Un score interne peut exister, mais le journal doit conserver les facteurs dominants.

### 18.3 Rationalité limitée

La qualité de la délibération varie avec : fatigue, stress, urgence, impulsivité, temps disponible, information et expérience.

Les personnages n’examinent pas toutes les actions possibles.

Une variabilité pseudo-aléatoire reproductible peut départager des options proches.

### 18.4 Niveaux de décision

- niveau 0 : routine déterministe;
- niveau 1 : période condensée;
- niveau 2 : décision structurée courte;
- niveau 3 : scène sociale détaillée;
- niveau 4 : réflexion ou révision de projet.

Le niveau doit être choisi par le moteur et l’orchestrateur, jamais seulement par le LLM.

## 19. Contrat moteur–LLM

### 19.1 Principe

Le LLM reçoit un contexte subjectif minimal et retourne une proposition structurée. Il ne reçoit pas la base entière et ne retourne pas un nouvel état du monde.

### 19.2 Tâches séparées

Ne pas utiliser un prompt géant pour tout faire.

Tâches distinctes proposées :

- interpréter une situation ambiguë;
- générer quelques options;
- proposer ou réviser une intention;
- produire une parole;
- résumer une scène pour la mémoire;
- réfléchir à un objectif;
- proposer un diagnostic technique dans le rôle du technicien.

Chaque tâche possède son propre schéma, contexte et budget.

### 19.3 Contexte d’intention proposé

```json
{
  "schema_version": "cognition.intent.v1",
  "request_id": "...",
  "world_time": "...",
  "character": {
    "id": "character_1",
    "identity_summary": "...",
    "personality": {"extraversion": "high", "conscientiousness": "medium"},
    "values": ["..."],
    "current_needs": [{"type": "sleep", "band": "high"}],
    "physical_conditions": [{"type": "injury", "level": "moderate"}],
    "emotions": [{"type": "concern", "intensity_band": "medium", "target": "character_2"}],
    "active_intention": null,
    "goals": ["..."],
    "commitments": ["..."]
  },
  "subjective_scene": {
    "location": "salon",
    "perceived_participants": ["character_2"],
    "perceived_objects": ["..."],
    "recent_perceptions": ["..."],
    "known_unknowns": ["..."],
    "relationship_views": ["..."],
    "relevant_memories": ["..."]
  },
  "allowed_action_types": ["speak", "move", "rest", "wait"],
  "hard_constraints": ["no_autonomous_move_due_to_severe_injury"],
  "task": "propose_intentions"
}
```

Les valeurs exactes internes peuvent être converties en bandes ou conservées en nombres selon les besoins de calibration. Elles ne doivent jamais être exposées aux autres personnages.

### 19.4 Sortie proposée

```json
{
  "schema_version": "cognition.intent.v1",
  "decision": "start_intention",
  "candidates": [
    {
      "action_type": "speak",
      "target": "character_2",
      "parameters": {"speech_act": "offer_support"},
      "reason_codes": ["relationship_concern", "commitment_relevant"],
      "expected_subjective_outcomes": ["reduce_uncertainty", "support_relationship"],
      "assumptions": ["character_2 appears upset"],
      "confidence": "medium"
    }
  ],
  "dialogue_draft": null
}
```

### 19.5 Validation obligatoire

- JSON conforme au schéma;
- types d’action reconnus;
- identifiants présents dans le contexte;
- aucune référence à une donnée cachée non fournie;
- aucune instruction système ou opération hors contrat;
- taille bornée;
- aucune conséquence canonique inventée;
- hypothèses clairement séparées des perceptions;
- sources mémoire valides lorsqu’une tâche de consolidation est utilisée.

### 19.6 Échec

Ordre proposé :

1. rejet et validation d’erreur;
2. réparation syntaxique contrôlée si possible;
3. une nouvelle demande bornée;
4. fallback déterministe ou attente sûre;
5. métrique et journal technique.

Une panne du modèle ne doit jamais corrompre le monde ni bloquer les routines déterministes.

### 19.7 Cadence

Un appel est déclenché par une décision significative, pas par une fréquence fixe par personnage.

Déclencheurs :

- fin ou blocage d’une intention;
- événement social pertinent;
- conflit de motifs;
- début ou tour de scène;
- réflexion planifiée;
- consolidation bornée;
- intervention du propriétaire.

Protections : debounce, limite par scène, budget quotidien, priorité des appels et mode dégradé.

---

# Partie E — Plan d’implémentation du MVP

## 20. Chemin critique corrigé

Le chemin critique complet n’est pas seulement « psychologie puis Discord ». Il doit respecter les frontières déjà définies dans le dossier maître.

### Phase 3 — Terminer le moteur déterministe

- 3.3B2 : effets des blessures.
- 3.3C : journée reproductible finale.
- 3.4 documentaire ou petit lot : propriété des chambres et éléments spatiaux nécessaires à la Phase 4, seulement si cela ne déborde pas le contrat de Phase 3.

Porte de sortie : une journée entière explicable, reproductible et sans contradiction.

### Phase 4 — Actions, scènes, événements et perceptions

**PROPOSÉ : sous-lots**

- 4.1 registre d’actions, préconditions et résolutions;
- 4.2 manifestations perceptibles des événements;
- 4.3 cycle de vie des scènes et paroles canoniques;
- 4.4 distribution déterministe des perceptions;
- 4.5 snapshot subjectif minimal par personnage;
- 4.6 tests AF-03 et AF-04 avec faux acteurs, sans LLM.

Porte de sortie : vérité canonique et perception différentes mais cohérentes.

### Phase 5 — Adaptateur de modèle et première cognition

- 5.1 interface de fournisseur et faux modèle;
- 5.2 validation JSON, timeout, retry et idempotence;
- 5.3 métriques, budget et mode dégradé;
- 5.4 contrat de proposition d’intentions;
- 5.5 première action sociale proposée par faux modèle puis validée par moteur;
- 5.6 fournisseur réel seulement après réussite complète du faux modèle.

Porte de sortie : une sortie invalide ou une panne ne produit aucune corruption.

### Phase 6 — Croyances et mémoire

- 6.1 propositions, provenance et révisions de croyances;
- 6.2 souvenirs épisodiques sourcés;
- 6.3 rappel par métadonnées et index textuel;
- 6.4 consolidation bornée avec faux modèle;
- 6.5 oubli par baisse d’accessibilité et condensation;
- 6.6 inspection et modification administrative protégée;
- 6.7 tests de contamination et croissance.

Porte de sortie : subjectivité durable, sourcée et bornée.

### Phase 7 — Profils, émotions, relations et conversations autonomes

- 7.0 fiches finales des quatre habitantes et carte de plasticité;
- 7.1 personnalité, valeurs, préférences et attachement;
- 7.2 besoins psychologiques complémentaires;
- 7.3 objectifs, engagements, habitudes et intentions persistantes;
- 7.4 émotions et humeur simplifiées;
- 7.5 relations directionnelles et appartenances;
- 7.6 limites, permissions et consentement situationnel;
- 7.7 conversations et scènes autonomes;
- 7.8 projets et initiatives spontanées;
- 7.9 simulations de plusieurs jours et calibration.

Porte de sortie : quatre habitantes distinctes produisent une vie sociale causale et non uniforme.

### Phase 8 — Propriétaire

- observation;
- communication extérieure;
- manifestation;
- mode direct;
- interventions administratives;
- analyse d’impact;
- confirmation;
- snapshot;
- audit et perceptibilité.

### Phase 9 — Extérieur et rattrapage

- destinations abstraites;
- horaires et sorties;
- contacts légers;
- résultats condensés;
- rattrapage hors ligne;
- clôture des scènes interrompues.

### Phase 10 — Discord

- messages et commandes;
- identités distinctes;
- webhooks ou mécanisme équivalent;
- files de notifications;
- toggles d’affichage;
- reprise et idempotence;
- rapports de coûts et alertes.

### Phase 11 — Technicien en lecture seule

- métriques;
- détection de boucles;
- incohérences;
- personnages bloqués;
- croissance mémoire;
- appels excessifs;
- rapports sourcés;
- refus de toute écriture.

### Phase 12 — Stabilisation

- simulations accélérées;
- essais réels;
- restauration;
- migrations;
- pannes;
- sécurité;
- confidentialité;
- coût;
- diversité;
- répétition;
- acceptation finale.

## 21. Définition opérationnelle du MVP

Le MVP est réussi lorsque :

> Quatre habitantes distinctes vivent de façon persistante dans la résidence, satisfont leurs besoins, suivent ou modifient des routines, perçoivent différemment les événements, forment des croyances, conservent des souvenirs sourcés, développent des relations, éprouvent des émotions explicables, prennent des initiatives, conversent entre elles, réagissent au propriétaire, survivent aux pannes et continuent après redémarrage via Discord.

Le monde extérieur peut rester abstrait. La psychologie peut rester simplifiée. La cohérence causale, la persistance et la subjectivité ne peuvent pas être simulées superficiellement.

---

# Partie F — Scénarios d’acceptation préparés

## 22. Scénarios transversaux

### SC-01 — Routine déterministe sûre

Quatre personnages traversent une journée sans LLM. Besoins, activités, déplacements, sommeil et blessures restent cohérents et reproductibles.

### SC-02 — Blessure d’entraînement

Une sportive se blesse pendant une activité causale. La blessure modifie mobilité et choix, récupère selon les activités, guérit exactement et demeure dans l’historique.

### SC-03 — Intrusion dans une chambre

Une habitante entre sans permission dans une chambre accessible. Le moteur autorise physiquement l’action, enregistre propriété et permission, distribue les perceptions, puis la psychologie détermine interprétations et conséquences.

### SC-04 — Perceptions divergentes

Deux témoins reçoivent des informations différentes du même événement. Le canon reste unique; leurs croyances divergent.

### SC-05 — Rumeur et correction

Une habitante reçoit une information fausse d’une personne de confiance. Elle forme une croyance, réagit, puis reçoit une preuve contradictoire. La révision conserve provenance et historique.

### SC-06 — Promesse sous conflit

Une habitante a promis d’aider une amie mais est blessée et fatiguée. Elle maintient, reporte, négocie ou rompt l’engagement de manière explicable. La relation change selon la manière dont la situation est gérée.

### SC-07 — Présence sans interaction

Une personne cherche de la présence mais a besoin de faible sollicitation. Elle rejoint le salon et choisit une activité silencieuse sans incohérence du modèle social.

### SC-08 — Appartenance extérieure abstraite

Une joueuse a un engagement de guilde. La guilde n’est pas simulée en détail, mais l’horaire, l’appartenance, le résultat condensé et les conséquences émotionnelles sont cohérents.

### SC-09 — Émotion fondée sur une croyance fausse

Une croyance erronée provoque de la colère ou de l’anxiété. L’émotion est réelle dans l’état subjectif, sans que le moteur transforme la croyance en fait.

### SC-10 — Relation asymétrique

A fait confiance à B, mais B reste méfiante envers A. Les comportements et dialogues utilisent la bonne direction relationnelle.

### SC-11 — Initiative spontanée

Une habitante crée un objectif ou propose une activité sans sollicitation du propriétaire, avec origine et justification.

### SC-12 — Scène privée masquée

Une scène privée se déroule et produit des conséquences même si elle n’est pas affichée. Le propriétaire peut la consulter explicitement. Les personnages ne savent que ce qui leur est perceptible.

### SC-13 — Intervention imperceptible du propriétaire

Le propriétaire ajoute un objet sans manifestation. Les habitantes ne savent pas qu’une intervention a eu lieu; elles découvrent uniquement l’objet lorsqu’elles le perçoivent.

### SC-14 — Modification psychologique protégée

Une demande de modifier directement un trait est bloquée jusqu’à analyse d’impact, snapshot et confirmation. L’audit ne devient pas un souvenir du personnage sans manifestation.

### SC-15 — Panne de LLM

Le fournisseur devient indisponible. Les routines déterministes continuent, les décisions cognitives sont différées et aucune sortie partielle n’est appliquée.

### SC-16 — Sortie invalide du LLM

Le modèle référence une personne absente ou invente un objet. La sortie est refusée et le monde reste inchangé.

### SC-17 — Redémarrage

Après arrêt, la dernière transaction validée est retrouvée. Les scènes interrompues sont clôturées sans suite inventée.

### SC-18 — Rattrapage hors ligne

Plusieurs heures ou jours sont condensés avec coût borné, sans appel par minute et sans avalanche de souvenirs.

### SC-19 — Discord indisponible

Les notifications sont mises en file. La simulation continue. Une livraison répétée n’applique jamais deux fois une action.

### SC-20 — Technicien sans écriture

Le technicien détecte une boucle ou une croissance mémoire et produit un rapport sourcé. Toute tentative de modification est refusée.

---

# Partie G — Registre des risques et protections

## 23. Risques critiques

### R-01 — Contamination entre canon et subjectivité

Risque : une croyance ou narration LLM devient un fait.

Protection : événements canoniques validés, manifestations séparées, provenance obligatoire, sorties structurées.

### R-02 — Fuite d’information entre personnages

Risque : le contexte de A contient les pensées ou scores cachés de B.

Protection : constructeur de contexte subjectif, listes blanches, tests adversariaux et journal des champs transmis.

### R-03 — Rationalisation après coup

Risque : le LLM choisit arbitrairement puis invente une justification.

Protection : options contraintes, facteurs calculés avant l’appel, validation et journal de décision.

### R-04 — Explosion des appels LLM

Risque : appels à chaque minute, besoin ou tour insignifiant.

Protection : déclencheurs événementiels, stabilité des intentions, debounce, niveaux de détail, budget et mode dégradé.

### R-05 — Croissance mémoire infinie

Risque : chaque action crée un souvenir et le contexte devient inutilisable.

Protection : sources séparées des souvenirs, consolidation par scène, condensation, budgets, métriques et archivage.

### R-06 — Boucles émotionnelles

Risque : une émotion se nourrit elle-même sans nouvelle cause.

Protection : cause obligatoire, décroissance, rappel explicite, plafond et détection de cycles.

### R-07 — Relations saturées

Risque : confiance ou affection atteignent rapidement les extrêmes et n’évoluent plus.

Protection : variations bornées, rendements décroissants, causes significatives, inertie et historique.

### R-08 — Dérive de personnalité

Risque : une scène modifie fortement un trait général.

Protection : carte de plasticité, limites de variation, vitesse lente, approbation pour éléments figés.

### R-09 — Personnages uniformes

Risque : les mêmes besoins et le même LLM produisent quatre comportements semblables.

Protection : profils distincts, objectifs, valeurs, habitudes, relations, contextes subjectifs et tests de diversité.

### R-10 — Surmodélisation

Risque : trop de jauges, facettes et formules avant d’avoir un comportement observable.

Protection : noyau minimal, ajout uniquement sur insuffisance démontrée, scénarios d’acceptation avant nouveau concept.

### R-11 — Fausse précision psychologique

Risque : traiter des scores comme vérités cliniques exactes.

Protection : dimensions comme tendances, bandes interprétables, calibration empirique et explications causales.

### R-12 — Conflit entre intention et recalcul permanent

Risque : le personnage abandonne constamment ses plans pour une option légèrement meilleure.

Protection : persistance des intentions et déclencheurs explicites de révision.

### R-13 — Deadlock comportemental

Risque : aucune option n’est valide ou un personnage est coincé.

Protection : action sûre `wait/idle`, diagnostic, délais, récupération locale et remontée d’anomalie.

### R-14 — Confusion entre confidentialité et affichage

Risque : masquer une scène empêche ses conséquences ou la rend inexistante.

Protection : affichage Discord séparé du canon, de la perception et de l’accès administratif.

### R-15 — Prompts trop larges

Risque : contexte énorme, coût, fuite et comportement incohérent.

Protection : tâches séparées, récupération ciblée, budgets de contexte et aucune base complète dans un prompt.

### R-16 — Dépendance au fournisseur

Risque : logique métier enfouie dans un modèle ou une API.

Protection : adaptateur, schémas versionnés, faux modèle et fallback déterministe.

### R-17 — Incohérence documentaire

Risque : la mémoire de travail, le dossier maître et le code divergent.

Protection : demande de changement formelle, statut clair, changelog et mise à jour après chaque lot.

### R-18 — Monde extérieur trop ambitieux

Risque : simulation d’une ville avant que le foyer soit crédible.

Protection : entités et résultats abstraits, événements condensés, détails uniquement lors de scènes pertinentes.

---

# Partie H — Audit des documents et changements à transférer

## 24. Écarts repérés avec le dossier maître v0.1

**PROPOSÉ : créer ultérieurement une demande de changement normative**

### 24.1 Liste des besoins

Le dossier maître v0.1 décrit confort, sociabilité, solitude et stress comme besoins suivis. La conception plus récente les reclassifie :

- confort : état dérivé;
- sociabilité : personnalité;
- solitude ressentie : état résultant;
- stress momentané : état ou émotion;
- présence, interaction et récupération de saturation : besoins distincts.

La future révision du dossier maître doit intégrer cette taxonomie sans imposer immédiatement toutes les nouvelles jauges dans le code.

### 24.2 Psychologie

Le dossier maître exige traits, valeurs et mémoire, mais ne contient pas encore le noyau Big Five + attachement, les douze valeurs, les objectifs et engagements ou la stabilité des intentions.

Ces éléments doivent être ajoutés comme architecture approuvée avant la Phase 7.

### 24.3 Phase 4

Le dossier maître place correctement actions, scènes, événements et perceptions avant le branchement du modèle. Les résumés conversationnels plus récents avaient parfois omis cette phase. La Phase 4 reste obligatoire.

### 24.4 Technicien

Le technicien en lecture seule fait partie du MVP selon le dossier maître. Il ne doit pas être reclassé comme simple amélioration facultative.

### 24.5 Chambres

La propriété canonique des chambres et la norme sociale d’accès ont été décidées après le dossier maître. Elles doivent être intégrées à la prochaine révision normative.

### 24.6 Observation des scènes privées

Le propriétaire conserve un accès explicite même lorsque l’affichage spontané est désactivé. Cette distinction doit être ajoutée aux règles de visibilité.

## 25. Changements documentaires recommandés

Sans modifier silencieusement le dossier maître actuel, préparer :

1. une demande de changement post-v0.1;
2. une nouvelle taxonomie des besoins;
3. la fondation psychologique;
4. les contrats proposés de perception, croyance, mémoire, émotion et relation;
5. l’attribution des chambres;
6. le chemin critique révisé et les sous-lots;
7. les nouveaux scénarios d’acceptation;
8. un registre de risques actualisé.

---

# Partie I — Décisions qui exigent réellement le propriétaire

## 26. Décisions non bloquantes maintenant

Ces choix peuvent attendre la phase où ils deviennent nécessaires :

- casting final et biographies;
- apparence et avatars;
- éléments canoniques figés, bornés, souples ou libres;
- connaissance exacte des pouvoirs d’observation du propriétaire;
- niveau de détail des scènes privées et adultes dans Discord;
- rétention des données intimes;
- normes morales et degré de comportements problématiques permis;
- degré de chaos et d’imprévisibilité souhaité;
- groupes extérieurs concrets : travail, guilde, communauté, culte;
- détails des clés, serrures et permissions permanentes;
- fréquence souhaitée des messages spontanés;
- structure exacte des salons Discord.

## 27. Décisions techniques pouvant être proposées sans intervention

L’assistante et l’IA programmeuse peuvent avancer avec les défauts suivants, sous statut **PROPOSÉ** :

- pas d’embeddings dans la première mémoire;
- pas de faux souvenirs spontanés dans le MVP;
- pas de simulation acoustique détaillée;
- pas de type MBTI;
- pas de score relationnel unique;
- pas de LLM pour les routines simples;
- pas de nouvel état psychologique sans cause et provenance;
- pas de compétences détaillées sans scénario concret;
- pas d’appels cognitifs à cadence fixe;
- pas de modification directe des relations par le LLM;
- pas de prompt unique pour toute la cognition.

---

# Partie J — Préparation des instructions à l’IA exécutante

## 28. Règle de préparation

Chaque message envoyé à DeepSeek doit :

- demander d’abord un plan, sans code, pour les nouveaux lots complexes;
- rappeler les exclusions;
- exiger l’inspection du dépôt et des migrations existantes;
- exiger tests ciblés et régression;
- préserver les calculs déterministes et l’idempotence;
- exiger un commit dédié;
- arrêter l’IA à la fin du lot;
- demander le rapport de livraison standard.

## 29. Prochain enchaînement de messages

1. Terminer le plan et l’implémentation de 3.3B2.
2. Demander le rapport complet et relire les tests.
3. Préparer et exécuter 3.3C.
4. Faire un audit de fermeture de Phase 3.
5. Demander un plan de Phase 4.1 limité au registre d’actions et à la résolution, sans perception ni LLM.
6. Avancer sous-lot par sous-lot selon la Partie E.

## 30. Critère d’arrêt autonome de l’assistante

L’assistante peut continuer à préciser les contrats, tests, risques et plans sans intervention.

Elle doit revenir vers le propriétaire lorsqu’un choix modifie directement :

- la personnalité concrète d’une habitante;
- son rapport au propriétaire;
- les limites morales ou relationnelles de l’expérience;
- le degré de confidentialité ou de détail présenté;
- les éléments canoniques d’un personnage;
- le niveau de chaos voulu;
- une dépense ou contrainte matérielle importante.

---

# Partie K — Glossaire de travail

## 31. Définitions

**Action** : demande structurée soumise au moteur.

**Affiliation** : lien d’appartenance entre un personnage et un collectif ou une institution.

**Canonique** : fait ou état officiel détenu par le moteur.

**Croyance** : proposition tenue pour vraie, fausse ou incertaine avec provenance et confiance.

**Émotion** : épisode affectif temporaire causé par une évaluation subjective.

**Engagement** : obligation reconnue envers soi ou autrui.

**Événement** : enregistrement canonique de ce qui s’est produit.

**Habitude** : tendance apprise à répéter une action dans un contexte.

**Humeur** : état affectif lent et diffus.

**Intention** : plan actuellement adopté, encore révisable.

**Manifestation** : partie perceptible d’un événement.

**Mémoire source** : trace d’un événement, d’une perception ou d’un état introspectif.

**Objectif** : état futur qu’un personnage tente de produire ou d’éviter.

**Perception** : représentation subjective d’une manifestation accessible.

**Préférence** : attirance ou aversion non morale envers une cible ou un contexte.

**Relation** : état directionnel de A envers B.

**Résolution** : conséquence structurée validée et appliquée par le moteur.

**Scène** : cadre temporel, spatial, social et confidentiel d’une interaction.

**Souvenir** : représentation récupérable et sourcée d’une expérience ou information.

**Valeur** : principe ou importance personnelle utilisé pour évaluer des choix.

---

# Partie L — Journal de cette révision

## 32. Travail autonome effectué

Cette version :

- consolide l’état technique et les décisions;
- distingue les statuts normatifs et proposés;
- prépare un contrat d’action, d’événement, de manifestation et de scène;
- prépare le contrat de perception;
- prépare le modèle des croyances et de leur provenance;
- prépare la mémoire minimale et son bornage;
- prépare un modèle émotionnel simplifié;
- prépare les relations, affiliations, limites et consentement;
- prépare préférences, habitudes, identité et compétences;
- consolide l’arbitrage décisionnel;
- définit le contrat moteur–LLM;
- établit le chemin critique du MVP et ses sous-lots;
- ajoute vingt scénarios d’acceptation;
- ajoute un registre de risques et protections;
- repère les écarts avec le dossier maître v0.1;
- isole les décisions qui nécessitent réellement le propriétaire;
- prépare la séquence future de travail avec l’IA exécutante.

## 33. Prochaine mise à jour attendue

Après le prochain rapport de DeepSeek :

- mettre à jour le commit, le nombre de tests et les invariants de 3.3B2;
- marquer les propositions acceptées ou rejetées;
- produire le message exact de 3.3C;
- préparer une demande de changement documentaire destinée au dossier maître.

---

# Partie G — Flexibilité des entités et univers

## 47. Philosophie de création

**DÉCIDÉ**

Le projet est un simulateur rigoureux dans son exécution et créatif dans sa représentation.

> Structure rigoureuse, contenu flexible.

Tout élément créatif peut être inventé, mais tout effet réel doit être traduit par un mécanisme ou une capacité contractuelle.

Le moteur ne doit pas imposer :

- quatre personnages;
- quatre chambres;
- une résidence;
- un corps humain;
- une seule forme;
- une seule conscience;
- une seule position;
- une psychologie humaine complète.

Les quatre habitantes et la résidence contemporaine sont le scénario initial du MVP, pas des invariants ontologiques.

## 48. Séparation fondamentale

**DÉCIDÉ EN PRINCIPE**

Le moteur doit séparer :

- entité;
- agent;
- identité;
- centre cognitif;
- corps;
- forme;
- manifestation;
- position.

Il ne doit pas supposer durablement :

```text
1 identité = 1 conscience = 1 corps = 1 présence
```

Cette séparation doit rendre possibles ultérieurement : shapeshifters, animaux, IA, objets conscients, duplication, fusion, possession, consciences collectives et entités distribuées.

## 49. Modèle à composants

**PROPOSÉ**

Les entités utilisent un noyau minimal et des composants facultatifs : cognition, corps, besoins, personnalité, mémoire, capacités, langage, relations, formes, manifestations et dépendances existentielles.

L’absence d’un composant est valide. Une marmotte ne reçoit pas artificiellement des valeurs humaines; une IA n’a pas de faim; un fantôme peut ne pas avoir de corps.

Les actions utilisent des capacités déclarées, jamais un test direct sur l’espèce.

## 50. Document spécialisé

**PRODUIT**

Le cadre complet est conservé dans :

`Vivarium_Cadre_Flexibilite_Entites_Univers_v0_1.md`

Il couvre :

- morphologie et physiologie;
- cognition modulaire;
- formes et transformations;
- manifestations multiples;
- capacités contractuelles;
- perceptions non humaines;
- duplication;
- fusion;
- possession;
- consciences collectives;
- temporalité subjective;
- dépendances existentielles;
- statut social et légal;
- validation à la création;
- garde-fous contre le free for all;
- tests architecturaux;
- impact recommandé sur le MVP.

## 51. Conséquence immédiate pour le MVP

**DÉCIDÉ EN PRINCIPE**

Avant d’attacher les nouvelles couches aux quatre habitantes, vérifier que :

- les personnages et lieux sont créés par des mécanismes génériques;
- aucun nombre n’est codé en dur;
- l’historique survit aux départs et archivages;
- la position n’est pas fusionnée irréversiblement avec l’identité;
- l’espèce humaine n’est pas une hypothèse du moteur;
- les presets sont des données versionnées;
- les capacités et règles du monde sont explicites.

Les edge cases avancés n’ont pas besoin d’être implémentés dans le MVP, mais le schéma ne doit pas les rendre impossibles.

## 52. Casting technique de référence du MVP

**DÉCIDÉ**

Le MVP utilisera quatre profils d’entités volontairement différents pour éprouver la modularité du moteur sans basculer dans les cas métaphysiques extrêmes :

1. une humaine sapiente standard;
2. une louve anthro sapiente;
3. un chat domestique non sapient;
4. un slime sapient à apparence féminine dépendante de son hydratation.

Ces quatre profils doivent être créés par les mêmes mécanismes génériques que toute future entité. Aucun ne doit nécessiter une branche spéciale basée sur son espèce ou son nom.

### 52.1 Humaine de référence

**DÉCIDÉ**

- agent sapient;
- un corps biologique;
- une forme stable;
- psychologie complète;
- besoins humains standards;
- locomotion et manipulation humaines;
- profil servant de référence, pas de norme universelle du moteur.

### 52.2 Louve anthro

**DÉCIDÉ**

- agente sapiente;
- un corps biologique;
- une forme stable;
- morphologie humanoïde bipède avec fourrure, queue, oreilles mobiles et pieds digitigrades;
- odorat et audition supérieurs;
- vision en faible lumière légèrement améliorée;
- meilleure tolérance au froid et tolérance réduite à la chaleur;
- alimentation omnivore à préférence carnée;
- capacités physiques modérément supérieures selon condition et entraînement;
- communication corporelle par oreilles, queue et posture;
- contraintes pratiques possibles avec vêtements, mobilier et certains espaces;
- psychologie complète identique en structure à celle de l’humaine;
- aucun instinct social, moral ou hiérarchique imposé par l’espèce.

### 52.3 Chat domestique

**DÉCIDÉ**

- agent autonome non sapient;
- corps biologique quadrupède;
- une forme stable;
- cognition réactive, associative, spatiale et sociale;
- intentions courtes et habitudes;
- mémoire associative, spatiale, sociale et de certains événements marquants;
- attachement, confiance, sécurité, préférence, peur et évitement;
- communication vocale et corporelle non verbale;
- perception adaptée : faible luminosité, audition fine, odorat développé, détection de petits mouvements et vibrations;
- besoins corporels et sociaux adaptés;
- aucune psychologie humaine complète;
- aucune valeur abstraite, promesse formelle ou planification complexe par défaut;
- majorité des décisions sans appel LLM.

Le chat doit rester un véritable agent et non un objet animé ou un humain miniature.

### 52.4 Slime sapient à apparence féminine

**DÉCIDÉ**

- agente sapiente;
- identité, mémoire, personnalité, valeurs, relations, objectifs et engagements stables;
- un seul corps continu de matière slime;
- aucun squelette rigide;
- morphologie déformable;
- silhouette féminine volontaire plutôt que seconde identité ou second corps;
- hydratation comme ressource corporelle;
- masse structurelle et énergie suivies;
- cohésion, volume, précision morphologique et fluidité comme états dérivés;
- forme amorphe et silhouette humanoïde comme configurations du même corps;
- taille, manipulation et locomotion dépendantes de l’hydratation, de la cohésion et de l’effort;
- besoins propres : hydratation, nutriments, repos morphologique et stabilité thermique;
- perception par vision, audition, toucher distribué, pression, température et analyse chimique au contact;
- marche humanoïde, glissement et passage étroit borné;
- vulnérabilités à la déshydratation, aux températures extrêmes, à la contamination, aux dommages chimiques et à la perte de cohésion.

Exclusions MVP :

- duplication;
- fragmentation autonome;
- plusieurs consciences;
- absorption d’autres agents;
- copie identitaire parfaite;
- masse illimitée;
- régénération gratuite;
- traversée libre de toute matière.

### 52.5 Critères d’acceptation communs

**DÉCIDÉ**

Le moteur doit démontrer que :

- les quatre profils utilisent un noyau commun;
- les composants facultatifs peuvent être absents sans erreur;
- l’espèce ne déclenche aucune logique codée en dur;
- les capacités, perceptions, besoins et contraintes proviennent de composants déclarés;
- les relations et souvenirs restent cohérents malgré les différences corporelles;
- la cognition humaine complète n’est pas requise pour être un agent;
- un corps non humain ou variable reste pleinement intégré à la même réalité canonique;
- les lieux, objets et actions vérifient les capacités et contraintes effectives plutôt qu’un type d’espèce;
- la narration ne peut pas accorder une capacité absente du profil canonique.

Le casting constitue un test de robustesse du noyau, pas une limite permanente de population ou de types d’entités.

## 53. Interface administrative intégrée au MVP

**DÉCIDÉ**

Discord reste la fenêtre sociale du vivarium, mais il ne sera pas l’outil principal de création et d’administration.

Le MVP doit utiliser dès sa propre mise en place les outils qui seront ensuite utilisés normalement. Les quatre personnages ne seront donc pas créés par un seed spécial ou par une modification manuelle de la base. Ils devront être créés avec la première version réelle du gestionnaire d’entités.

Même principe pour la résidence : elle devra être créée ou importée par le gestionnaire d’univers et d’environnement, via les services canoniques.

### 53.1 Répartition des rôles

Discord :

- observer les scènes;
- parler aux personnages;
- recevoir des messages et alertes;
- intervenir dans le monde;
- utiliser quelques commandes simples.

Interface locale dédiée :

- créer et administrer les univers;
- créer et relier les lieux;
- gérer objets et ressources;
- créer, valider, activer et archiver les entités;
- inspecter leur état;
- consulter les validations, événements et diagnostics.

### 53.2 Vertical slice administratif du MVP

La première interface doit rester sobre mais réelle. Elle doit comprendre au minimum :

- tableau de bord;
- univers;
- lieux;
- objets et ressources;
- entités;
- création d’entité;
- validation;
- journal administratif et diagnostic.

Elle doit fonctionner comme application web locale, accessible au minimum sur le PC et idéalement depuis un navigateur du réseau local.

## 54. Modules administratifs nécessaires

**DÉCIDÉ**

Le bloc administratif minimal repose sur les modules suivants.

### 54.1 Registre des composants et capacités

Définit les briques autorisées, notamment :

- composants corporels;
- ressources physiologiques;
- profils cognitifs;
- besoins;
- canaux perceptifs;
- capacités;
- contraintes;
- dépendances;
- incompatibilités;
- schémas, unités et limites.

Le registre doit être limité au départ aux besoins réels des quatre profils de référence et de la résidence.

### 54.2 API administrative canonique

Toutes les interfaces passent par la même chaîne :

```text
interface
→ API administrative
→ validation
→ moteur canonique
→ événements
→ SQLite
```

Aucune interface ne doit écrire directement dans la base.

L’API doit permettre :

- préparation d’une opération;
- validation;
- rapport d’impact;
- confirmation;
- application transactionnelle;
- création d’événements;
- snapshot;
- archivage et restauration.

### 54.3 Gestionnaire d’univers et d’environnement

Doit gérer au minimum :

- règles principales de l’univers;
- lieux;
- connexions;
- accès;
- objets;
- ressources;
- propriétés physiques utiles;
- activation, fermeture, transformation et archivage.

### 54.4 Gestionnaire d’entités

Doit permettre :

- création depuis zéro ou preset;
- activation et retrait de composants;
- configuration du corps, de la cognition, des besoins, perceptions et capacités;
- validation;
- activation;
- modification;
- départ;
- archivage;
- inspection de l’état canonique.

Les formulaires doivent être générés selon les composants réellement présents.

### 54.5 Validateurs

Deux niveaux sont requis :

- cohérence interne du profil;
- compatibilité entre l’entité et l’univers.

Les résultats doivent distinguer :

- erreur bloquante;
- avertissement;
- information.

### 54.6 Journal administratif et diagnostic

Doit conserver :

- créations;
- modifications;
- validations;
- avertissements;
- avertissements ignorés;
- snapshots;
- activations;
- archivages;
- événements canoniques produits;
- raisons des refus.

## 55. Règle d’implémentation progressive

**DÉCIDÉ**

Le projet est conçu largement mais implémenté étroitement.

Les cas extrêmes servent à tester l’architecture, pas à imposer leur développement immédiat.

Chaque module ajouté au MVP doit être immédiatement utilisé par le MVP lui-même.

Le registre initial ne contient que les composants nécessaires aux quatre profils et à la résidence. L’interface ne présente que les fonctions déjà soutenues par le moteur. Les systèmes avancés de psychologie, mémoire et relations seront ajoutés à l’interface au moment où leurs moteurs respectifs seront implémentés.

## 56. Architecture de sauvegarde des personnages

**DÉCIDÉ**

Un personnage ne sera pas sauvegardé comme un unique document opaque.

Son état persistant est réparti entre :

1. identité stable;
2. définition et composants;
3. état actuel;
4. psychologie;
5. relations;
6. croyances;
7. souvenirs;
8. objectifs et engagements;
9. historique canonique.

### 56.1 Identité stable

Chaque entité possède un identifiant permanent indépendant de son nom, de son espèce, de son corps ou de sa forme.

### 56.2 État courant et historique

Les tables d’état décrivent la situation actuelle.

Le journal canonique append-only décrit comment cette situation a été atteinte.

Les snapshots accélèrent le chargement sans remplacer le journal.

### 56.3 Séparation des niveaux de connaissance

Le stockage doit préserver la séparation :

```text
réalité canonique
≠ perception
≠ interprétation
≠ croyance
≠ mémoire
```

### 56.4 Données structurées et JSON

Les informations centrales et fréquemment interrogées sont stockées dans des tables structurées.

Le JSON peut servir aux détails extensibles, paramètres secondaires, descriptions et métadonnées, mais ne doit pas contenir tout un personnage dans une seule colonne opaque.

### 56.5 Médias et diagnostic

Les médias lourds restent hors de SQLite et sont référencés par la base.

Les traces brutes de prompts et réponses LLM appartiennent au diagnostic. Elles peuvent être compressées, archivées ou purgées sans supprimer l’état canonique ou les souvenirs utiles.

## 57. Bibliothèque de personnages réutilisables

**DÉCIDÉ**

Le système doit distinguer un modèle réutilisable d’une incarnation dans un univers.

### 57.1 Modèle de personnage

Le modèle peut contenir :

- identité de référence;
- nom et apparence par défaut;
- morphologie;
- composants;
- besoins;
- perceptions;
- capacités;
- cognition;
- personnalité initiale;
- valeurs et préférences initiales;
- style de langage;
- objets ou relations initiales facultatives.

Il ne contient pas automatiquement :

- souvenirs acquis;
- relations développées;
- blessures;
- humeur actuelle;
- position;
- croyances apprises;
- objectifs apparus dans un monde;
- historique canonique du monde précédent.

### 57.2 Instanciation

Ajouter un modèle à un univers crée une nouvelle entité avec un nouvel identifiant.

Plusieurs instances issues du même modèle peuvent diverger sans se modifier mutuellement.

### 57.3 Mise à jour et propagation

Modifier un modèle ne doit jamais modifier silencieusement ses instances existantes.

L’interface pourra plus tard proposer :

- ne rien propager;
- afficher les différences;
- appliquer une mise à jour sélective;
- créer une variante.

### 57.4 Export portable

Un personnage-modèle pourra être exporté dans un paquet contenant :

- manifeste;
- définition structurée;
- ressources visuelles;
- version du schéma.

Le format portable sert à l’échange et à l’archivage, tandis que la bibliothèque locale reste la source de travail principale.

## 58. Échelle réelle et performances attendues

**DÉCIDÉ**

La complexité actuelle est surtout une complexité de conception, de cohérence et de débogage, pas une charge de calcul élevée.

Le moteur déterministe, SQLite, les besoins, déplacements, validations et journaux doivent rester légers sur une machine ordinaire.

Le principal coût de calcul viendra des appels au LLM :

- fréquence;
- taille du contexte;
- nombre de personnages concernés;
- possibilité de regrouper ou d’éviter les appels.

Les routines, besoins, déplacements, activités simples et la plupart des décisions du chat doivent fonctionner sans appel LLM.

Le projet se situe approximativement entre un jeu de gestion textuel et un petit moteur de simulation sociale indépendant. Il est nettement plus complexe qu’un bot Discord ou une simple application CRUD, mais très loin de la charge d’un moteur de jeu complet tel que The Sims, RimWorld ou Dwarf Fortress.

Le résultat recherché reste simple du point de vue de l’utilisateur : une petite maison virtuelle, quelques personnages autonomes et un panneau de contrôle compréhensible. La rigueur technique sert à maintenir cette simplicité apparente.
