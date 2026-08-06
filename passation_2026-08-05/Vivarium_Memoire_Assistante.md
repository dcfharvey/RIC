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
