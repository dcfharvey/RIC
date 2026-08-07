# Correctif alpha 0.1.0a3 — cadence utile et rencontre d'attente

**Statut :** livré après le second retour de rodage opérateur du 6 août 2026.

## Faits observés

Après l'arrivée, les quatre résidentes sapientes avaient une activité `idle`
de plusieurs heures. À chaque tick de deux secondes, le runtime rejouait la
simulation jusqu'à l'heure courante. Cela matérialisait les mêmes besoins et
ajoutait cinq événements `needs_materialized`, sans nouvelle décision, action
ni scène. Les activités restaient donc correctement cohérentes, mais le journal
visible masquait les événements utiles et l'observation donnait l'impression
d'un monde bloqué.

Les anciennes scènes étaient explicitement `interrupted` parce que l'arrêt
normal par `Ctrl+C` les clôture sans inventer de paroles. Elles ne constituent
pas une scène active à reprendre.

## Correction limitée

1. Le runtime ne lance `SimulationEngine.run_to` que lorsqu'il n'existe aucune
   activité active ou que la première `planned_end_at` est atteinte. Entre ces
   jalons, l'heure et les besoins restent calculables en lecture pure : aucune
   écriture canonique ne survient.
2. Une attente (`idle`) active, commencée dans un lieu où une autre résidente
   sapiente est présente, peut créer **une** occasion sociale bornée. Sa clé est
   dérivée de la séquence canonique `activity_started`; elle ne peut pas être
   rouverte après fermeture, redémarrage ou rafraîchissement.
3. Patoune reste exclue : l'occasion requiert le composant
   `cognition.profile = sapient`.
4. Le tableau demande les événements significatifs les plus récents et filtre
   seulement, à la lecture, `needs_materialized`. L'événement append-only reste
   entier dans SQLite; cette lecture n'écrit et ne supprime rien.

## Raisonnement et limites scientifiques

La littérature sur la mémoire prospective distingue les indices liés à un
événement, au temps et à une activité, et décrit l'exécution comme dépendante
d'un indice identifiable plutôt que d'un réveil narratif sans cause. Cela ne
prouve pas une cognition artificielle; cela soutient uniquement le choix
d'ingénierie modeste : faire naître une occasion sociale d'un fait canonique
daté (`activity_started`) plutôt que d'un polling social périodique.

- [Revue systématique sur la mémoire prospective](https://pmc.ncbi.nlm.nih.gov/articles/PMC11965160/)
  : distinction des indices temporels et événementiels.
- [Revue sur la neuroanatomie fonctionnelle de la mémoire prospective](https://pmc.ncbi.nlm.nih.gov/articles/PMC13269919/)
  : formation, maintien et récupération orientée par indice.

Cette version ne construit toujours pas de système de buts, motivations,
préférences, sélection générale d'activité ni mouvements autonomes répétés.
Ces capacités demandent leurs propres contrats, recherches, options validées
et banc d'essai. Elle enlève une impasse observable sans fabriquer une fausse
autonomie.

## Contrôles de régression

- tick intermédiaire : aucune nouvelle écriture ni matérialisation de besoins ;
- activité arrivée à échéance : le simulateur reste admissible ;
- scène d'attente : deux participantes sapientes co-localisées seulement,
  exactement une provenance, aucune réouverture ;
- API : seul le filtre de lecture `needs_materialized` est accepté ;
- tableau : journal compact sans muter la source canonique.

## Conséquence opérateur

Après redémarrage du runtime, le monde déjà en rodage ouvrira au plus deux
nouvelles scènes bornées entre les quatre résidentes qui attendent au salon.
Elles pourront produire jusqu'à quatre tours chacune, puis se fermeront. Le
prochain comportement durable supplémentaire dépendra d'un vrai système de
choix d'activité, pas d'une boucle cachée.
