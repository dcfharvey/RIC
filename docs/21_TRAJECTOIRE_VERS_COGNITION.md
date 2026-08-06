# Trajectoire vers les systèmes cognitifs

**Statut :** plan actif — 6 août 2026.

## Décision directrice

Le Vivarium ne doit pas attendre une simulation physique exhaustive avant de
devenir vivant. Il doit seulement posséder un monde **assemblable, observable
et traversable de manière fiable**. Après ce seuil, la cognition peut être
construite en parallèle avec les extensions concrètes (eau, inventaires,
formes de Chuu, etc.).

Les lots ci-dessous sont des portes de qualité, pas des dates. On ne passe
jamais à la suivante parce qu'elle est prévue : il faut les preuves de sortie.

## Porte 1 — monde composable

### Lot A : blueprint et instanciateur atomique

**But :** créer un monde neuf à partir de presets publiés, sans faire du seed
technique la règle cachée du projet.

- blueprint versionné : lieux, connecteurs, installations, objets initiaux et
  politique topologique;
- références exactes aux versions publiées des presets;
- instanciation tout-ou-rien dans une base ou un monde neuf;
- provenance figée : blueprint et contrats résolus conservés avec le monde;
- aucun personnage, LLM ou interface ajouté dans ce lot.

**Sortie requise :** une résidence et un second monde non domestique minimal
peuvent être crés de façon reproductible; un blueprint invalide ne laisse
aucun monde partiel.

### Lot B : connecteurs concrets à état simple

**But :** distinguer enfin une relation du graphe d'une vraie instance de
connecteur.

- identité canonique pour un connecteur de monde;
- état fini explicite seulement lorsque son archetype le déclare;
- premier modèle minimal : disponible, fermé ou bloqué, sans inventer de
  serrure, clé ou force physique;
- les arcs sans état (arche ouverte, chemin) restent simplement disponibles;
- changement d'état transactionnel, journalisé et testé.

**Sortie requise :** fermer un connecteur bloque réellement le passage concerné
sans modifier un autre passage, et un refus ne laisse aucune trace partielle.

### Lot C : traversée validée — socle initial livré

**But :** remplacer le déplacement qui ne connaît qu'une arête par une action
canonique « tenter de traverser ce connecteur ».

```
proposition d'action -> validation moteur -> position canonique + événement
                         | refus motivé, aucun changement
```

- origine, destination, sens et état du connecteur vérifiés;
- premier contrat d'entité extensible : les capacités et ressources pourront
  devenir des validateurs additionnels, sans être simulées d'avance;
- `GraphEngine` reste la lecture topologique; `TraversalEngine` devient la
  décision de permission et de mutation;
- aucun LLM ne peut déplacer quelqu'un directement.

**Sortie requise :** chaque déplacement dans un monde blueprint a un connecteur
causal identifiable; un itinéraire possible mais fermé est refusé proprement.
Ces critères sont livrés pour les états et directions initiaux; les capacités
et ressources restent des validateurs futurs.

## Porte 2 — monde d'intégration, pas encore cognition

### Lot D : règles de base et monde d'intégration

**But :** obtenir une véritable zone d'essai des cinq résidentes sans utiliser
le monde technique ni commencer une histoire officielle trop tôt.

- un installateur explicite des règles mondiales de base (besoins et activités
  déjà validés), distinct du vieux seed de développement;
- une résidence instanciée par blueprint;
- Sophie, Erika, Luna, Chuu et Patoune instanciées par les services réels;
- fiches de contrôle lisibles pour valider les configurations, sans interface
  finale obligatoire;
- scénarios de banc : pause/reprise, besoins, passage ouvert/fermé,
  blessure, ressources et redémarrage.

**Sortie requise :** le monde peut être recréé et comparé; les cinq fiches
sont validées; aucun test ne dépend d'une histoire laissée dans une base.

## Porte 3 — démarrage de la cognition

La cognition commence ici. Elle reste d'abord déterministe et testable; le LLM
vient plus tard comme interprète, jamais comme autorité.

### Lot E : contrat moteur–cognition

- `WorldFact` : fait canonique minimal exportable;
- `PerceptionCandidate` : fait potentiellement accessible à une entité;
- `IntentProposal` : intention structurée, jamais une mutation;
- `ValidationResult` : acceptée, adaptée ou refusée avec raison stable;
- provenance, version de schéma et budget de calcul explicités.

**Sortie requise :** une intention de test peut traverser le contrat complet,
être refusée ou appliquée, sans texte libre ni LLM.

### Lot F : perception factuelle

- projection d'événements et d'état canonique vers ce qu'une entité peut
  objectivement remarquer;
- filtres de lieu, de présence et de portée; pas encore d'interprétation;
- une absence de perception est aussi un résultat valide;
- tests de non-fuite : Patoune ou une résidente ne reçoit pas un fait hors de
  son accès.

**Première tranche livrée :** vue factuelle locale (`self_location`,
co-présence, objets visibles, connecteurs adjacents) sans écriture, attention,
interprétation ou mémoire. Voir `docs/36_PERCEPTION_FACTUELLE.md`.

**Deuxième tranche livrée :** flux d'événements directs cursé et réduit. Une
résidente peut recevoir ses propres changements confirmés depuis une séquence,
mais aucun événement passé d'autrui n'est reconstruit sans preuve historique de
visibilité. Voir `docs/36_PERCEPTION_FACTUELLE.md`.

### Lot G : état interne, attention et priorités

- les besoins, blessures et ressources existants deviennent des signaux pour
  une entité, sans lui imposer une émotion ou une phrase;
- sélection d'un petit nombre de points d'attention;
- règles déterministes de priorité de secours et d'inactivité;
- le LLM futur ne sera appelé qu'à un vrai point de choix.

**Première tranche livrée :** les besoins sous seuil, blessures et effets de
ressources propres à l'observateur alimentent une liste d'attention pure,
ordonnée et bornée. Elle ne contient encore ni émotion, ni mémoire, ni
décision. Voir `docs/37_ATTENTION_DETERMINISTE.md`.

### Lot H : mémoire et interprétation subjective

La première trace subjective, son journal append-only, son audit et son rappel
privé borné sont livrés (`docs/38_PLAN_PREMIERE_MEMOIRE_SUBJECTIVE.md`). Ils
conservent la séparation entre fait, accès, encodage et croyance.

- souvenirs avec sources, portée, confiance et politique de révision;
- croyances distinctes des faits canoniques;
- chaque personnage peut retenir ou interpréter différemment un même fait;
- jamais de secret admin dans cette mémoire.

### Lot I : relations et décision sociale

- relations dirigées et contextuelles;
- motivations, objectifs limités et choix sociaux;
- scénarios de dyades puis de groupes de cinq; le banc d'essai mesure les
  effets avant qu'une règle soit admise dans le canon.

### Lot J : adaptateur LLM et dialogue

- première frontière locale livrée : entrée structurée bornée, sortie JSON
  validée, fournisseur interchangeable et LM Studio sur boucle locale;
- une décision proposée ne peut encore être qu'une attente ou une traversée
  perçue, qui repasse obligatoirement dans `ActionOrchestrator`;
- budgets, temporisations, reprise après erreur et absence de réseau;
- le modèle propose intention, interprétation ou dialogue; le moteur reste le
  seul à appliquer un fait;
- tests avec faux modèle avant tout appel API ou modèle local.

## Ce qui n'est pas un prérequis à la cognition

- une interface finale;
- Discord;
- eau et formes de Chuu;
- inventaires de personnages, argent, combat, magie ou monde extérieur;
- tous les cas de physique ou de biologie imaginables.

Ils seront ajoutés quand une scène ou un test concret les rendra nécessaires.
Les abstractions déjà posées (ressources, objets, contenance, connecteurs et
validateurs) permettent de les brancher sans les inventer prématurément.

## Point de départ actuel

Les lots E et F sont livrés; le lot G est amorcé avec une attention pure et
bornée. Mémoire, social et LLM restent futurs.

Les portes 1 et 2 sont livrées : blueprint, connecteurs à état, traversée,
règles de résidence et monde d'intégration atomique. Le contrat fermé du lot E,
la perception factuelle du lot F et la première tranche du lot G sont livrés;
voir `docs/34_CONTRAT_ACTION_COGNITION.md`, `docs/36_PERCEPTION_FACTUELLE.md`
et `docs/37_ATTENTION_DETERMINISTE.md`.
