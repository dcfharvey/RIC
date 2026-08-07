# Correctif alpha 0.1.0a2 — observation active et arrivée bornée

**Statut :** livré après le premier rodage opérateur du 6 août 2026.

## Problème observé

Le premier lancement présentait un tableau de bord qui était une photo : sans
clic sur `Rafraîchir`, l'opérateur ne voyait pas les nouvelles écritures du
runtime. En plus, les résidentes pouvaient recevoir une activité déterministe
`idle` de longue durée avant d'avoir eu une occasion subjective d'entrer dans
la résidence. Une activité active protège correctement la cohérence
position--activité, mais ce choix d'ordre rendait le premier lancement
visuellement inerte.

Le correctif ne prétend pas résoudre la vie autonome générale. Il traite
seulement une transition établie : les volontaires viennent d'arriver au lieu
où elles ont accepté d'habiter.

## Décision d'ingénierie

Le déclencheur `initial_arrival` existait déjà dans le contrat d'admission,
mais était volontairement fermé. Il est maintenant raccordé avec ce contrat :

```text
world_initial_context_set (séquence canonique S)
→ source technique arrival_S, une fois par résidente sapiente
→ admission append-only, budget et déduplication
→ contexte privé + faits initiaux communs + passages réellement disponibles
→ proposition LLM no_action ou traverse
→ ActionOrchestrator / TraversalEngine valide ou refuse
```

L'occasion n'est disponible que si aucun déplacement postérieur ne l'a déjà
dépassée, sauf lorsqu'elle a elle-même commencé et doit finir de distribuer les
occasions restantes. Patoune n'a pas le composant `cognition.profile` sapient
et est donc exclue. Une admission réussie, une panne LLM ou une réponse
`no_action` consomme l'occasion : il n'existe ni retry caché ni polling cognitif.

Le runtime traite au plus une résidente par tick et diffère le démarrage des
activités tant que cette courte phase reste en attente. Après la dernière
occasion, la simulation déterministe reprend normalement. Une traversée reste
possible seulement si le connecteur est réellement visible, disponible et
compatible; le LLM ne reçoit jamais SQLite ni le droit d'écrire un fait.

## Pourquoi ce déclencheur, et non une marche aléatoire

La littérature sur la mémoire prospective distingue les indices liés à un
événement, au temps et à la fin d'une activité. Elle décrit aussi le besoin de
garder et de détecter explicitement l'indice avant d'exécuter l'intention. Ces
résultats ne prescrivent pas l'architecture du Vivarium; ils soutiennent ici un
choix limité : modéliser une occasion identifiable, bornée et traçable plutôt
qu'un réveil périodique qui inventerait une raison d'agir.

- La revue sur les indices temporels et événementiels décrit ces deux formes
  d'intention prospective et la charge de monitoring propre aux indices de
  temps : [Exercise and Prospective Memory](https://pmc.ncbi.nlm.nih.gov/articles/PMC6239140/).
- Une revue systématique décrit une séquence qui comprend formation, maintien,
  détection de l'indice puis exécution : [Prospective Memory in HIV](https://pmc.ncbi.nlm.nih.gov/articles/PMC6205723/).

**Limite :** les études portent sur la cognition humaine et souvent des
populations cliniques; elles ne valident pas une personnalité artificielle. Le
raccordement `initial_arrival` reste donc un choix d'ingénierie prudent, à
observer dans le banc et le monde alpha.

## Tableau d'observation

`app.js` effectue maintenant une lecture API toutes les deux secondes seulement
lorsque l'onglet est visible. Le garde `refreshing` évite les requêtes qui se
chevauchent. La routine emploie les mêmes `GET` locaux que le bouton manuel,
ne transmet aucun jeton supplémentaire et ne peut exécuter aucune commande.

## Preuves de sortie

- arrivée sourcée, contexte commun limité, rejet après départ et déduplication
  après mouvement : tests du routeur;
- une occasion par résidente sapiente, jamais Patoune : test de cycle;
- le runtime diffère l'activité jusqu'à la dernière occasion et conserve le
  verrou activité--position ensuite : test d'intégration;
- rafraîchissement visible local, sans écriture : test du tableau;
- tests ciblés et suite complète : **692 passed**; l'inspection visuelle reste
  requise avant de déclarer le lot stable.

## Hors portée

- sélection autonome générale de buts, d'activités, de déplacements ou de
  scènes prolongées;
- conséquences sociales tirées des paroles;
- simulation hors ligne pendant que le runtime est arrêté.

Ces capacités gardent leurs contrats et leur recherche propres. Le correctif
ne les simule pas par du texte, du hasard ou une boucle de réveil cachée.
