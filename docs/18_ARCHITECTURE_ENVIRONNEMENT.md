# Architecture d'environnement composable

**Statut :** direction approuvée; politique topologique initiale implémentée.

## Principe

Un univers n'est pas une résidence codée en dur. Il est une instance d'un
blueprint versionné qui déclare explicitement ses lieux, connecteurs,
installations et politiques. Les mêmes mécanismes doivent pouvoir produire une
résidence, une île, un château, un onsen ou une bulle hors du temps.

## Concepts distincts

| Concept | Rôle |
| --- | --- |
| lieu | nœud occupable : chambre, couloir, lac, piscine, seau |
| connecteur | relation traversable : porte, arche, fenêtre, échelle, conduit |
| installation | fait local explicite : lit, eau, serrure, échelle |
| contenance | hiérarchie spatiale : seau dans chambre, chambre dans tour |
| topologie | graphe de déplacement, distinct de la contenance |

Un couloir est un lieu; une porte est un connecteur. Un preset ne crée jamais
implicitement ses installations : il propose seulement des fonctions et
contraintes possibles.

## Grammaire commune avec les personnages

Les personnages et l'environnement partagent le pattern : gabarit versionné,
instance canonique, provenance figée, composants, état actuel, validation et
journal. Ils ne deviennent pas une unique classe générique : seul un personnage
porte identité subjective, mémoire, intention et éventuel LLM.

## Traversée future

Le futur `TraversalEngine` recevra une proposition `(entité, connecteur,
origine, destination, mode)`. Il vérifiera l'existence, le sens, l'état du
connecteur, les capacités de l'entité, ses ressources, les permissions et les
coûts, puis seulement appliquera la position et l'événement canonique.

`GraphEngine` reste volontairement plus bas niveau : topologie brute,
intégrité, impact et mutation atomique. Un chemin géométrique n'est jamais à
lui seul une permission de traverser.

## Presets futurs

- `place_archetype` : fonctions, milieu, occupation et emplacements
  d'installations possibles;
- `connector_archetype` : extrémités, directions, modes de traversée et état;
- `environment_blueprint` : lieux, connecteurs, contenance, installations,
  politique topologique et règles mondiales.

Ils seront versionnés, publiés puis instanciés avec provenance figée, comme les
gabarits de personnage. Aucun preset spécifique à Chuu ou à une espèce ne sera
autorisé : un seau est un lieu-conteneur dont l'occupation dépend des capacités
et de l'état de l'entité.

## Politique topologique initiale

La migration `0017` introduit `world_topology_policy` :

- `strong_anchor` : tous les lieux doivent rejoindre une ancre déclarée et
  être joignables depuis elle; le seed technique choisit `salon` comme donnée;
- `none` : aucune connexité globale imposée, pour mondes à zones séparées,
  portails, îles ou cas narratifs explicites.

Les futures politiques supplémentaires ne seront ajoutées qu'avec un cas et un
scénario de banc reproductible.

## Objets et contenance initiale

Le premier gestionnaire d'objets et le premier gestionnaire de contenance sont
livrés (`docs/19_OBJETS_ET_CONTENANCE.md`). Ils fixent une base volontairement
plus petite que le futur système d'environnement : installations fixes,
objets portables et hiérarchie objet‑dans‑objet. La contenance reste distincte
de la topologie; aucun objet ne crée implicitement un lieu ni un passage.

## Ordre de réalisation

1. politique topologique configurable — livré;
2. objets et contenance objet‑dans‑objet — livré;
3. contrats/presets de lieu et connecteur;
4. blueprint et instanciateur de monde propre;
5. connecteurs à état simple;
6. validation de traversée dépendante de l'entité;
7. eau, conteneurs, ventilation et formes de Chuu lorsque leurs règles sont
   concrètes et testables.
