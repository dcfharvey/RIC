# Routine d'audit des erreurs silencieuses

**Statut :** procédure active pour les futurs lots du Vivarium.

## But

Les tests verts prouvent les scénarios couverts; ils ne prouvent pas à eux
seuls qu'une nouvelle donnée est journalisée, reproductible, documentée ou
visible par les outils de diagnostic. Cette routine cherche précisément ces
écarts silencieux avant qu'ils ne contaminent la suite du moteur.

## Déclencheurs

Un audit est obligatoire après :

- une migration ou une nouvelle table canonique;
- une mutation traversant plusieurs systèmes;
- un nouveau contrat entre couches (moteur–cognition, interface–moteur,
  adaptateur LLM);
- un changement du journal, du digest ou du banc;
- un jalon avant d'ouvrir une nouvelle famille de systèmes.

Il reste proportionné : une correction locale sans nouvel état ne déclenche
pas forcément une tournée complète, mais tout lot peut y être soumis au
jugement technique si son rayon de conséquences est incertain.

## Passage minimal

1. relire le diff par responsabilité, pas uniquement par fichier;
2. vérifier mutation, transaction, journal, contraintes SQLite et rollback;
3. vérifier que l'état nouveau apparaît dans le digest, les audits et le banc
   lorsqu'il est pertinent;
4. ajouter un test d'acceptation, un refus atomique et une régression de la
   conséquence inter-systèmes;
5. exécuter les tests ciblés, puis la suite complète avant remise;
6. comparer les documents actifs, roadmap, passation et version aux capacités
   réellement livrées;
7. consigner clairement : « rien trouvé », ou l'écart, son risque et sa
   correction. Une hypothèse ne devient jamais une preuve.

## Résultat de la première application

L'audit précédant le contrat d'action v1 n'a pas trouvé de corruption du moteur
ni de test rouge. Il a toutefois trouvé des documents actifs restés à l'étape
« blueprint/résidentes futurs » malgré leur livraison, et une immutabilité
superficielle du premier `WorldFact`. Les documents ont été corrigés et le fait
retourné est désormais gelé récursivement, avec test de non-mutation.

Lors de la perception factuelle, le premier test supposait à tort que l'entrée
extérieure n'avait qu'une porte visible. L'audit a confronté cette hypothèse au
blueprint réel et conservé le connecteur vers le stationnement dans la vue; le
test a été corrigé au lieu de dégrader la topologie canonique.

Lors de l'attention déterministe, l'audit a d'abord vérifié que le lot ajoutait
une projection pure plutôt qu'un nouvel état canonique : aucune migration,
aucune écriture, aucun événement et aucune extension de digest n'étaient donc
requis. Une première hypothèse de test supposait les valeurs de besoins du seed
technique (70 000) dans le monde d'intégration; les fiches réelles commencent à
100 000. Le scénario a été recalibré à l'heure canonique où les seuils sont
effectivement franchis, au lieu de modifier les données du monde pour faire
passer le test. La suite complète a validé **573 tests**.

La première trace subjective a révélé deux attentes de tests restées figées au
schéma 23; elles ont été mises à jour vers la migration 24. La trace et son
journal restent hors du digest canonique, mais sont immuables et contrôlés par
leur service. La suite complète a validé **578 tests**.

Pour le flux d'événements perceptibles, l'audit a vérifié que le curseur reste
une entrée de lecture, jamais un accusé de réception persisté dans le canon.
Les payloads ont été réduits avant export afin de ne pas transmettre la
provenance d'action, la source administrative ou le motif technique d'un
ajustement. Le cas d'un autre personnage n'est pas inféré depuis sa position
actuelle : faute de chronologie spatiale historique, il reste volontairement
hors de ce lot. La suite complète a validé **576 tests**.

Pour la première disposition de personnalité, l'audit a vérifié que la nouvelle
table est créée dans la même transaction que l'instance et annulée avec elle,
que son origine reste le gabarit publié v2, et qu'elle apparaît dans le digest
et le banc. Aucun événement autonome n'a été ajouté : une disposition initiale
est déjà attribuable à `character_instantiated`, et toute révision future devra
être un protocole distinct et audité. La suite complète a validé **616 tests**.
