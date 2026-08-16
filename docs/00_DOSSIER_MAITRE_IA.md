# RIC — Dossier maître normatif

**Version :** 2.0  
**Date :** 16 août 2026  
**Statut :** noyau normatif stable du projet

RIC — **Reality · Interaction · Cognition** — est un moteur de simulation sociale persistante. Ce document fixe les principes qui doivent rester vrais malgré l'évolution du code. Il n'est volontairement plus une photographie détaillée d'un commit, d'un nombre de tests ou d'un rodage particulier.

Pour l'état opérationnel courant, lire `docs/99_PASSATION_COURANTE.md`. Pour les décisions autoritatives, lire `docs/01_REGISTRE_DECISIONS.md`. Pour l'ordre des travaux, lire `docs/15_ROADMAP_ACTIVE.md`. Pour la référence Git, lire `docs/GOUVERNANCE_GIT.md`.

## 1. Portée documentaire

Ce dossier contient les invariants, frontières d'autorité, règles de méthode et contrats conceptuels durables.

Il ne doit pas contenir comme vérité permanente :

- le HEAD courant;
- un compteur de tests;
- une session de rodage;
- une liste exhaustive de classes/modules;
- une architecture technique supposée à partir des noms conceptuels;
- le statut d'un WO volatil.

### Hiérarchie de vérité

Lorsqu'une réponse dépend de l'état réel du produit, utiliser cet ordre :

1. `product/current`, le code, les migrations et tests réellement intégrés;
2. `docs/01_REGISTRE_DECISIONS.md` et les décisions approuvées postérieures;
3. le présent dossier pour les invariants durables;
4. `docs/99_PASSATION_COURANTE.md` pour la photographie opérationnelle;
5. `docs/15_ROADMAP_ACTIVE.md` pour l'ordre des prochains travaux;
6. docs de lots/R&D, `docs/history/` et `sources/` pour provenance et détail historique.

Ne jamais réconcilier silencieusement deux sources incompatibles. Signaler le conflit et vérifier le dépôt réel.

## 2. Architecture conceptuelle RIC

Les trois moteurs sont des responsabilités conceptuelles. Ils ne correspondent pas automatiquement à des packages, services ou processus.

### Reality Engine

Ce qui est objectivement vrai, possible et causal dans la simulation :

- état canonique;
- temps canonique;
- espace et topologie;
- corps et capacités causalement actives;
- activités et conséquences;
- règles physiques et contraintes;
- transactions et journal canonique.

### Interaction Engine

Ce qui rend les agents et la réalité mutuellement accessibles et structure leurs interactions :

- perceptibilité;
- canaux et scènes;
- accès à des objets/personnes/signaux;
- affordances physiques;
- permissions d'interaction;
- médiation entre une proposition cognitive et une opération moteur validable.

### Cognitive Engine

Ce que chaque agent traite subjectivement :

- perception reçue/détectée;
- attention;
- interprétation;
- croyances;
- mémoire;
- affect;
- valeurs et préférences;
- motifs, buts et intentions;
- choix et langage.

Cette séparation est une discipline causale, pas une instruction de créer exactement trois sous-systèmes techniques.

## 3. Invariants fondamentaux

Ces règles priment sur toute commodité d'implémentation.

```text
réalité/canon ≠ perception ≠ croyance
parole ≠ fait
relation ≠ permission ≠ consentement
LLM propose, moteur valide
aucun composant cognitif n'écrit directement la réalité canonique
provenance d'audit ≠ source subjectivement mémorisée
un seul propriétaire persistant par état
pas d'omniscience implicite des agents
mécanisme générique > script propre à un personnage
```

### 3.1 Réalité, perception et croyance

Un fait canonique peut être inaccessible à un agent. Une perception peut être partielle ou erronée. Une croyance peut être fausse. Une mémoire peut être reconstructive. Aucun de ces états subjectifs ne réécrit rétroactivement la réalité.

### 3.2 Parole

Une phrase prononcée est d'abord un acte social/perceptible. Son contenu propositionnel n'est pas automatiquement vrai.

Exemple : « le carnet est dans la cuisine » peut devenir une information mémorisée ou crue, mais ne déplace ni ne crée un carnet dans le canon.

### 3.3 Relations, permissions et consentement

Affection, confiance, désir, intimité, statut, rôle, promesse ou relation ne constituent pas un consentement actuel. Les permissions et consentements doivent rester des contrats distincts des relations.

### 3.4 LLM non autoritaire

Le modèle peut interpréter, proposer, formuler ou sélectionner dans un contrat donné. Il ne peut pas :

- créer directement un fait canonique;
- contourner une impossibilité physique;
- s'attribuer une perception non accessible;
- écrire directement une croyance, mémoire ou relation persistante hors du propriétaire prévu;
- transformer sa propre narration en preuve.

## 4. Propriété persistante et causalité

Chaque état persistant doit avoir un propriétaire technique unique et identifiable.

Un composant peut projeter ou dériver une vue d'un état qu'il ne possède pas, mais ne doit pas créer un deuxième propriétaire silencieux du même concept.

La persistance doit permettre de distinguer :

- état canonique;
- événements/audit;
- état subjectif;
- projections dérivées;
- caches/observabilité.

L'audit sert à expliquer ce qui s'est produit. Il ne doit pas être injecté tel quel dans la mémoire subjective comme si l'agent connaissait la provenance interne du moteur.

## 5. Boucle de runtime normative

La boucle cible est :

```text
réalité canonique
→ sous-ensemble physiquement/accessiblement perceptible
→ détection / attention / accès cognitif selon le système disponible
→ état subjectif pertinent
→ opportunités / intentions / décision proposée
→ validation moteur
→ conséquence canonique
→ nouvelles perceptions
```

Les raccourcis qui fusionnent plusieurs étapes doivent rester explicitement temporaires et ne pas effacer leurs distinctions conceptuelles.

## 6. Perception et attention

Le projet doit conserver la distinction suivante :

```text
signal accessible
≠ signal détecté
≠ signal sélectionné par l'attention
≠ contenu cognitivement accessible
```

Une implémentation MVP peut simplifier cette chaîne, mais elle ne doit pas redéfinir la simplification comme une loi générale.

L'agent ne reçoit que ce qui est accessible par une voie causale reconnue. Le moteur ou la couche d'interaction doit être l'autorité sur cette accessibilité; le LLM ne décide pas qu'il « a vu » quelque chose.

L'active sensing est permis conceptuellement : une cognition peut choisir d'orienter une capacité sensorielle disponible, mais le résultat perceptif reste calculé/validé par le système compétent.

## 7. Corps, capacités et affordances

Une description corporelle n'est pas automatiquement une capacité causale.

Exemples :

```text
body_plan = amorphous        # description
form.humanoid = available    # capacité/état opérationnel
```

Les capacités réellement actives doivent dériver de propriétaires canoniques ou owner-backed reconnus.

Une **affordance physique** est une relation située entre un corps/capacité et le monde. Elle répond à une question comme : « cette action est-elle possible ici, maintenant ? »

Elle ne dit pas encore si l'action est comportementalement pertinente pour l'agent.

## 8. Motivation, opportunité et décision

RIC doit maintenir les distinctions :

```text
motif ≠ but ≠ intention ≠ opportunité ≠ action exécutée
```

Une activité techniquement faisable n'est pas encore une opportunité comportementale pertinente.

Le futur Behavioral Opportunity Layer doit être conçu comme un mécanisme générique reliant, selon le contrat approuvé :

- motifs;
- préférences;
- objectifs/intention;
- contexte subjectivement accessible;
- capacités;
- environnement;

à un petit ensemble d'opportunités comportementales candidates. Le moteur garde ensuite l'autorité sur leur faisabilité et leurs conséquences.

Ne pas remplacer cette couche par des scripts propres à un personnage ou une table universelle rigide `motif → activité` sauf si une règle déterministe particulière est scientifiquement/techniquement justifiée et explicitement bornée.

## 9. Mémoire subjective

La mémoire doit rester distincte du journal canonique et de la télémétrie d'audit.

Le modèle conceptuel actuel distingue au minimum :

- **L0 — canon exact** : vérité du moteur, pas mémoire subjective;
- **L1 — trace encodée** : représentation subjective initiale d'une expérience;
- **L2 — épisode autobiographique** : organisation d'une expérience propre à l'agent;
- **L3 — représentations dérivées** : généralisation, attente, résumé, connaissance subjective;
- **L4 — working/retrieval set** : contenu temporairement récupéré pour la cognition courante.

Règles :

- perceptibilité ne garantit pas encodage;
- attention peut influencer l'encodage sans devoir être un interrupteur universel binaire;
- un contenu jamais admis ne doit pas réapparaître plus tard comme souvenir subjectif détaillé sans source causale;
- une récupération est une reconstruction subjective, pas une lecture omnisciente du canon;
- les révisions de mémoire ne doivent pas effacer silencieusement l'historique d'audit;
- la provenance technique de l'encodage et la source dont l'agent se souvient sont deux choses différentes.

Les choix précis de consolidation, oubli, familiarité, recollection et reconsolidation exigent leur propre fondation scientifique et leurs propres tests. Une structure de données permettant des révisions ne suffit pas à les déclarer implémentés.

## 10. Cognition LLM

Le LLM est un composant d'interprétation/décision remplaçable, pas l'autorité du monde.

Le système normal ne doit pas être conçu autour d'un quota arbitraire du type `N appels par personnage par heure` comme principe cognitif. La maîtrise de charge doit privilégier :

- pertinence;
- déduplication/coalescence;
- fraîcheur;
- backpressure;
- fairness entre agents/catégories;
- annulation de travail devenu stale;
- protection anti-runaway;
- observabilité.

Un budget financier externe peut exister comme contrainte opérateur distincte si un fournisseur payant est utilisé; il ne doit pas devenir silencieusement une théorie de la cognition.

Le contexte envoyé au modèle doit être borné, subjectivement légitime et traçable pour l'audit technique.

## 11. Social et conversation

Une scène sociale est un support d'interaction, pas une mémoire partagée omnisciente.

Chaque participante conserve son propre accès, interprétation et mémoire.

Le futur Conversation State peut stocker un état partagé nécessaire à la continuité de la scène, mais il ne doit pas fusionner cet état avec les croyances ou souvenirs privés.

Une conversation interrompue doit pouvoir être clôturée sans inventer rétroactivement ce qui aurait été dit.

## 12. Entités et généricité

Le casting de référence comprend Sophie, Erika, Luna, Chuu et Patoune. Leur diversité sert notamment à falsifier les hypothèses trop anthropocentriques ou trop spécifiques à un personnage.

Le moteur ne doit pas être limité globalement à ces cinq entités.

Lorsque le même mécanisme peut expliquer une capacité, une préférence, une transformation, une limitation ou une réaction pour plusieurs types d'agents, préférer ce mécanisme générique à une branche codée au nom du personnage.

Un personnage fictionnel peut nécessiter des hypothèses de transfert ou des paramètres spécifiques de canon, mais ces hypothèses doivent être provenancées et ne doivent pas se déguiser en données empiriques humaines/animales.

## 13. Administration et intervention du propriétaire

Le propriétaire possède une autorité administrative supérieure, mais **autorité** et **perceptibilité** sont indépendantes.

Une intervention administrative peut être :

- non perceptible;
- perceptible indirectement par ses conséquences;
- explicitement manifestée/communiquée.

Une modification profonde d'un personnage ou de la réalité persistante doit passer par des commandes métier, validations, analyse d'impact, checkpoint/snapshot lorsque requis, confirmation explicite et audit — jamais par écriture SQLite directe d'une interface.

## 14. Méthode R&D

Tout modèle comportemental, cognitif, social ou physiologique doit commencer par la littérature scientifique ou technique pertinente.

Chaque dossier R&D doit séparer :

1. **résultats empiriques** — ce que les sources soutiennent directement;
2. **conclusions raisonnables mais incertaines** — inférences avec limites;
3. **hypothèses de modélisation** — simplifications choisies pour RIC;
4. **choix de design/ingénierie** — manière de rendre le modèle opérationnel.

Chercher activement :

- théories concurrentes;
- échecs de réplication;
- limites de population/tâche;
- risques de surinterprétation;
- conditions de falsification.

Ne jamais présenter un compromis d'ingénierie comme une découverte scientifique.

## 15. Gouvernance des acteurs

- **ChatGPT** : recherche scientifique/technique, conception fonctionnelle, cohérence conceptuelle et documentation R&D.
- **Grok** : contre-audit scientifique adversarial indépendant.
- **Codex** : autorité sur l'architecture réelle, le code, les migrations, les propriétaires persistants, les invariants techniques, les tests et l'ordre d'implantation.
- **Propriétaire** : autorité finale sur les choix produit/design.

ChatGPT ne doit pas prescrire silencieusement l'architecture technique à Codex. Un work order peut fixer un contrat fonctionnel et des invariants; Codex choisit l'implantation compatible avec le dépôt réel et signale toute divergence importante.

## 16. Discipline de développement

Avant une modification importante :

- vérifier les hypothèses;
- vérifier les dépendances;
- vérifier les propriétaires d'état;
- vérifier les invariants;
- vérifier les conséquences/migrations;
- définir les tests et falsifications;
- isoler le travail de tout runtime historique actif.

Une fonctionnalité n'est pas « fermée » parce qu'elle fonctionne sur une branche de travail. Elle doit être validée, intégrée et reconnue sur `product/current` selon `docs/GOUVERNANCE_GIT.md`.

## 17. Discipline documentaire

Les documents actifs ont des rôles distincts :

- `00_DOSSIER_MAITRE_IA.md` : invariants durables;
- `01_REGISTRE_DECISIONS.md` : décisions autoritatives et leur statut;
- `03_DECISIONS_OUVERTES.md` : arbitrages non fermés;
- `15_ROADMAP_ACTIVE.md` : séquence des travaux;
- `99_PASSATION_COURANTE.md` : photographie opérationnelle;
- `GOUVERNANCE_GIT.md` : référence produit et cycle d'intégration.

Les détails historiques appartiennent aux documents de lots et archives. Ne pas recopier chaque nouvelle photographie technique dans le dossier maître : cela le rendrait faux à chaque avancée.

## 18. Principe final

RIC cherche une simulation suffisamment générale pour laisser émerger des comportements différents sans écrire un scénario pour chaque exception.

La conception reste ouverte tant que la décision n'est pas engagée. Dès qu'elle devient exécutable ou canonique, elle doit devenir rigoureuse, vérifiable et traçable.

> **Flexible creativity. Rigorous execution.**
>
> **Verify twice. Commit once.**
