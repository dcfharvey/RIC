# Prompt prêt à envoyer à DeepSeek — Sous-lot 3.3B2

Tu poursuis le projet **Vivarium social artificiel** à partir du commit confirmé `f1335ca`, qui livre le sous-lot **3.3B1 — état de blessure, causalité et récupération** avec 164 tests réussis.

Avant toute chose : lis le dossier maître, les migrations, le code des besoins, activités, déplacements, politique déterministe, simulateur et blessures. Inspecte l’état réel du dépôt; ne suppose pas que le résumé ci-dessous remplace le code.

## Travail demandé maintenant

Produis uniquement le **plan final détaillé du sous-lot 3.3B2 — effets mécaniques des blessures**.

**N’écris aucun code, ne modifie aucun fichier, ne crée aucun commit.** Arrête-toi après le plan et attends l’approbation.

## Portée obligatoire

Le sous-lot doit intégrer les blessures actives aux systèmes existants sans changer le modèle de causalité et de récupération livré en 3.3B1.

### 1. Niveaux d’effet

Propose et documente une classification déterministe de la blessure de mobilité en au moins trois états d’effet :

- légère : aucun effet mécanique sur le déplacement ou les activités;
- modérée : déplacement permis avec coût énergétique additionnel;
- grave : déplacement autonome bloqué.

Les seuils exacts doivent être explicités dans le plan, centralisés et testables. Vérifie d’abord s’ils existent déjà dans le dépôt ou la documentation.

### 2. Blessure modérée

Règle de conception retenue : coût additionnel provisoire de **500 milli-énergie par arête traversée**.

Le plan doit expliquer :

- à quel moment la blessure et l’énergie sont matérialisées;
- comment calculer le coût d’un trajet de plusieurs arêtes;
- si le coût est appliqué arête par arête ou pour l’opération complète;
- comment garantir que l’énergie ne devient jamais négative;
- ce qui arrive si l’énergie disponible est inférieure au coût;
- comment préserver l’ancre et le reste rationnel du besoin d’énergie;
- comment assurer l’atomicité entre coût et déplacement;
- comment auditer le coût dans `character_moved` ou un événement associé sans duplication.

Recommandation à évaluer : matérialiser les états au temps simulé courant avant validation; refuser le déplacement si l’énergie matérialisée est insuffisante; appliquer coût et mouvement dans la même transaction.

### 3. Blessure grave

Une blessure grave bloque le **déplacement autonome**, mais ne paralyse pas toute activité.

Le plan doit préserver les activités réalisables au lieu actuel :

- cuisine : `eat`;
- salle de bain : `clean`;
- chambre : `sleep` et `rest`;
- salon : `rest`;
- toute autre activité déjà autorisée localement, sauf incompatibilité mécanique explicitement justifiée.

Aucune téléportation et aucun déplacement automatique vers un lieu de récupération.

Si le personnage devient gravement blessé dans un lieu où aucune activité utile n’est disponible, la politique doit choisir un `idle` dynamique et laisser la récupération passive progresser jusqu’au retour au niveau modéré. Elle doit alors pouvoir réévaluer et se déplacer normalement.

Le plan doit distinguer clairement :

- déplacement autonome de la politique;
- appel direct à l’API de déplacement;
- éventuelle intervention administrative du propriétaire, qui reste hors de ce sous-lot sauf nécessité d’invariant.

Ne présume pas qu’une blessure grave bloque une API canonique si la règle souhaitée ne vise que l’autonomie : analyse les implications et recommande une frontière explicite.

### 4. Activité active et changement de niveau

Le plan doit traiter une activité déjà en cours lorsque la blessure est créée ou change de niveau.

Règles souhaitées à analyser :

- si l’activité ne nécessite aucun déplacement et reste compatible avec le lieu, elle peut continuer;
- une blessure ne doit pas annuler silencieusement toute activité;
- si une activité devient mécaniquement incompatible, l’interruption doit être canonique, auditée et atomique;
- la récupération doit utiliser le régime réellement actif sur chaque intervalle.

### 5. Politique et simulateur

Le contexte de décision déterministe doit connaître au minimum le niveau d’effet de la blessure et les options localement réalisables.

Le plan doit indiquer :

- où le niveau est calculé;
- comment éviter de dupliquer la logique entre moteur, politique et simulateur;
- comment la politique exclut les destinations inaccessibles;
- comment elle maintient une activité locale compatible;
- comment elle sort de l’attente au premier instant exact où le niveau redevient modéré;
- comment le simulateur programme cette frontière sans tick par minute;
- comment garantir la reproductibilité.

### 6. Frontières temporelles simultanées

Définis un ordre exact et testable lorsque plusieurs transitions arrivent au même instant, par exemple :

- guérison ou passage grave → modéré;
- fin d’activité;
- matérialisation d’un besoin;
- décision de politique;
- déplacement;
- sommeil ou réveil.

Le plan doit proposer un ordre unique, expliquer pourquoi il évite les doubles écritures et préciser quels événements sont émis.

### 7. Atomicité, lecture pure et audit

Préserve les invariants existants :

- aucune colonne REAL;
- calculs à précision fixe;
- lectures dérivées sans écriture;
- aucune modification partielle;
- aucune énergie négative;
- aucune téléportation;
- aucune seconde blessure active;
- aucune modification silencieuse d’un état persistant;
- récupération fondée uniquement sur le temps simulé;
- pause = aucun progrès temporel.

Explique les transactions exactes nécessaires pour :

- déplacement modéré réussi;
- déplacement refusé pour énergie insuffisante;
- déplacement autonome refusé pour blessure grave;
- fin ou interruption d’activité;
- attente jusqu’à une frontière de récupération.

### 8. Compatibilité et migrations

Le plan doit indiquer si une migration est réellement nécessaire. Préfère des constantes et règles moteur si aucun état persistant supplémentaire n’est requis.

Aucune modification destructive du seed ou de l’historique de blessures.

### 9. Tests obligatoires

Prépare des scénarios chiffrés et reproductibles couvrant au minimum :

1. blessure légère : comportement identique à l’absence de blessure;
2. blessure modérée, une arête : coût exact de 500;
3. blessure modérée, plusieurs arêtes : coût exact et transaction unique cohérente;
4. énergie exactement égale au coût : déplacement permis, énergie à zéro;
5. énergie inférieure au coût : refus sans mouvement ni débit partiel;
6. blessure grave : politique ne choisit aucun déplacement;
7. blessure grave en cuisine : `eat` reste possible;
8. blessure grave en chambre : `sleep` ou `rest` reste possible;
9. blessure grave dans un lieu sans activité utile : `idle` dynamique, récupération passive, reprise au seuil modéré exact;
10. activité locale active qui continue pendant la blessure;
11. activité incompatible interrompue avec événement explicite, si le plan en prévoit une;
12. pause et reprise;
13. redémarrage au milieu de la récupération;
14. frontières simultanées dans l’ordre retenu;
15. lecture pure répétée sans écriture;
16. journée ou scénario accéléré reproductible;
17. régression complète des 164 tests existants.

Pour chaque scénario, donne les valeurs initiales, les heures, les seuils, les événements attendus et les états finaux.

## Exclusions explicites

Ne traite pas dans 3.3B2 :

- maladies;
- blessures multiples;
- douleur psychologique;
- perception des blessures;
- mémoire ou relations;
- LLM;
- Discord;
- monde extérieur;
- interventions administratives avancées;
- nouvelles activités non nécessaires au lot;
- rééquilibrage général des besoins;
- refonte de l’architecture existante.

## Format de réponse attendu

1. compréhension de l’existant inspecté;
2. décisions et seuils proposés;
3. fichiers probablement touchés;
4. algorithmes et transactions;
5. ordre des frontières temporelles;
6. événements et audit;
7. migration ou absence de migration;
8. matrice de tests chiffrés;
9. risques et cas limites;
10. plan de retour arrière;
11. éléments explicitement exclus.

Ne code rien. Termine en demandant l’approbation du plan.
