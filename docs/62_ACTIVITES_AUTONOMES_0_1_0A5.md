# Activités autonomes alpha 0.1.0a5

## Problème observé

Le runtime n'était pas gelé : sa politique déterministe choisissait un `idle`
potentiellement long lorsque les besoins étaient satisfaits. Le contexte LLM
contenait déjà personnalité, valeurs et préférences, mais le contrat ne lui
permettait que `no_action` ou une traversée immédiate. Les résidentes ne
pouvaient donc légalement convertir leurs préférences en activité visible.

## Appui scientifique et limite d'interprétation

Le lot retient deux principes modestes, sans prétendre reproduire un cerveau :

1. les occasions d'action disponibles sont spécifiées avant la sélection entre
   elles. L'hypothèse de compétition des affordances décrit justement le
   comportement comme une compétition entre possibilités d'action actuellement
   disponibles et demandes concurrentes ([Cisek, 2007](https://pubmed.ncbi.nlm.nih.gov/17428779/));
2. une occasion différée peut être réactivée par un indice événementiel plutôt
   que par une surveillance continue. La littérature sur la mémoire prospective
   distingue notamment les indices focaux susceptibles de récupération
   spontanée et la surveillance plus coûteuse
   ([Grandi et Tirapu-Ustárroz, 2017](https://pubmed.ncbi.nlm.nih.gov/28849865/),
   [Peper et Ball, 2023](https://pubmed.ncbi.nlm.nih.gov/37010132/)).

Traduction d'ingénierie : `activity_started: idle` est l'indice explicite qui
ouvre une seule occasion de décision; il n'affirme pas qu'un idle informatique
équivaut à la mémoire prospective humaine. Le moteur calcule les possibilités
réelles, puis le LLM interprète le profil et en choisit une ou attend.

## Contrat livré

- schéma cognitif v8 : `allowed_activities` contient des triplets moteur
  `activity_type`, `target_location_key`, `duration_seconds`;
- contrat d'action v2 : `start_activity` accepte seulement type et destination;
- liste blanche initiale : `gaming`, `photography`, `sport`, `girly_care`,
  `watch_tv`, `socialize`;
- un trajet BFS doit exister au moment de la projection et est recalculé lors
  de l'exécution;
- une activité non-idle active ne peut jamais être interrompue par ce cycle;
- le remplacement de l'idle, le trajet, le démarrage et l'événement de
  provenance forment une transaction. Tout échec restaure exactement l'idle;
- le ledger rend chaque source `idle_<event_seq>` unique et limite le cycle à
  un véritable appel par tick;
- les profils `non_sapient`, dont Patoune, sont exclus.

## Calibration volontairement différée

Les six activités utilisent temporairement les taux passifs de l'idle. C'est
un choix conservateur : le moteur peut attester l'activité sans inventer encore
une dépense énergétique ou un effet émotionnel précis. Les durées de 30 minutes
sont une calibration alpha de cadence, pas une constante psychologique. Le
futur système d'effort physique devra rechercher et tester ses propres règles.

## Essai réel et preuve

Sur un monde mémoire neuf, Gemma 4 12B QAT a choisi `photography` à
`entree_exterieure`. Le modèle a utilisé le raccourci syntaxique
`action: photography`; l'adaptateur l'a converti uniquement parce que cette
paire exacte figurait dans les options du moteur. Le contrat canonique a ensuite
accepté l'activité et inscrit sa provenance. Aucune base persistante n'a été
touchée par cet essai.

La suite complète passe à 704 tests après l'ajout des cas de rollback,
d'idempotence inter-types, d'exclusion de Patoune et de boucle autonome.
