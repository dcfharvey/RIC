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

Pour les croyances sourcées, l'audit a relevé qu'un simple statut mutable sur
une ancienne croyance ne suffisait pas à prouver une révision. La migration
exige désormais un successeur déjà audité dans la même transaction, et
interdit les éditions/suppressions silencieuses des preuves et événements.
Le digest et l'audit restent subjectifs, hors vérité canonique. La suite
complète a validé **624 tests**.

Pour les états affectifs, l'audit a vérifié que l'humeur et l'épisode ne sont
pas des faits canoniques, que l'épisode exige une trace privée accessible et
que toute mise à jour pointe vers un événement privé plus récent. La suite
complète a validé **629 tests**.

Pour le social initial, l'audit a vérifié que les vues sont directionnelles,
que leur preuve appartient à la bonne résidente et que les permissions ne sont
pas inférées depuis une relation. Les limites restent des politiques sociales,
pas des blocages physiques. La suite complète a validé **634 tests**.

Pour le cadre décisionnel initial, l'audit a confirmé qu'il reste une
projection pure : il organise les raisons disponibles mais n'écrit ni état,
ni journal canonique, ni décision LLM. La suite complète a validé **636 tests**.

Pour les scènes sociales, l'audit a vérifié que la parole n'est pas promue en
vérité, que seules les participantes co-localisées peuvent ouvrir une scène et
qu'une interruption se ferme sans nouvelle parole inventée. La suite complète
a validé **638 tests**.

Pour l'orchestrateur, l'audit a vérifié le snapshot de séquence (pas de boucle
sur l'action fraîchement produite), la borne par résidente, le curseur
persistant et le mode dégradé du fournisseur. La suite complète a validé
**640 tests**.

Pour le banc vivant, l'audit a vérifié que la base est strictement en mémoire,
que la chaîne complète est exercée avec un fournisseur injectable, et que le
mode dégradé garde un audit canonique propre. La suite complète a validé
**642 tests**.

Pour le tour social LLM, l'audit a vérifié que l'admission technique reste
distincte d'une parole, qu'un retry d'acte ne rappelle pas le modèle, qu'une
destinataire hors scène est refusée et qu'une participante ayant quitté le
lieu ne peut plus produire de parole. Aucun texte n'est promu en fait,
croyance, relation ou permission. La suite complète a validé **658 tests**.

Pour le banc social multi-tours, l'audit a vérifié que la rotation n'est qu'une
occasion de parole, que `no_action` reste possible, que la borne ferme la
boucle et que chaque essai reconstruit un monde en mémoire. La suite complète
a validé **664 tests**.

Pour la porte de prévol MVP, l'audit a vérifié que la CLI ouvre la base en mode
lecture seule, n'applique aucune migration, ne lance aucun LLM et ne tente
aucune réparation. Une base d'intégration propre passe; une identité ajoutée
ou une sélection ambiguë est explicitement refusée. La suite complète a validé
**670 tests**.

Pour les activités autonomes `0.1.0a5`, l'audit a trouvé puis corrigé trois
écarts avant remise : Gemma employait directement le type d'activité comme
verbe JSON malgré le contrat; une adaptation n'est donc admise que pour une
paire exacte déjà proposée par le moteur. L'identifiant d'une proposition
pouvait aussi être réutilisé entre deux familles d'action; la recherche
d'idempotence couvre désormais tous les événements attribués. Enfin, Patoune
était encore incluse dans l'ancien orchestrateur d'événements directs; la
capacité sapiente est maintenant projetée par une lecture commune. Le rollback
du remplacement d'idle, le prévol après essai réel et la suite complète ont
validé **704 tests**.
