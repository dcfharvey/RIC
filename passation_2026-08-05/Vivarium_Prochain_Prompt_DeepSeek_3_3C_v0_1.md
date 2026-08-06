# Prompt prêt à envoyer à DeepSeek — Phase 3.3C

**Projet :** Vivarium social artificiel  
**Type de réponse demandé :** plan détaillé seulement  
**Point de départ officiel :** commit `1bb93edba7d4b40cf962c1f65b6da1bb6f6defb9`  
**État confirmé :** Phase 3.3B2 fermée, 188 tests réussis, aucune migration  
**Lot demandé :** Phase 3.3C — reproductibilité finale et fermeture technique de la Phase 3

---

## 0. Autorité documentaire et méthode

Avant de répondre, inspecte réellement le dépôt, les migrations, les tests et la documentation technique existante.

Ordre d’autorité :

1. code, migrations et tests du dépôt;
2. dossier maître actuellement présent dans le dépôt;
3. présente instruction de lot;
4. documents post-audit pour les invariants pertinents.

Documents post-audit actuellement non suivis mais présents à la racine :

- `Vivarium_Demande_Changement_Post_Audit_v0_2.md`;
- `Vivarium_Exigences_Normatives_Post_Audit_v0_1.md`;
- `Vivarium_Feuille_Route_Post_Audit_v0_1.md`.

Ces documents décrivent la direction approuvée, mais **3.3C n’est pas le lot d’intégration documentaire globale**. Ne construis aucun nouveau système psychologique, administratif ou social.

Règles pertinentes :

```text
même état initial
+ mêmes entrées
+ même seed
+ même ordre canonique
+ mêmes versions de règles
= même état et même journal sémantique

lectures sans effets de bord
temps simulé seul moteur de progression
pause sans progression
reprise sans rattrapage indésirable
rejeu indépendant du LLM
état courant et événements atomiques
aucune dépendance à l’ordre accidentel des lignes SQLite
aucune dépendance à l’heure murale pour le résultat simulé
```

Ne présume jamais qu’un résumé remplace l’inspection du code.

---

## 1. Travail demandé maintenant

Produis uniquement le **plan final détaillé de la Phase 3.3C**.

Tu dois :

- inspecter l’état réel après 3.3B2;
- identifier les garanties de reproductibilité déjà présentes;
- identifier les lacunes réellement restantes;
- proposer le plus petit lot qui ferme la Phase 3;
- définir les scénarios de simulation longue;
- définir les comparaisons d’état et de journal;
- définir les tests de pause, reprise, redémarrage et reprise après crash;
- définir le rapport de fermeture;
- signaler les décisions encore ouvertes et recommander une option.

Tu ne dois pas :

- écrire du code;
- modifier un fichier;
- lancer une migration;
- créer un commit;
- commencer l’audit documentaire post-Phase 3;
- commencer la Phase 4.

Arrête-toi après le plan et demande l’approbation avant toute modification.

---

## 2. But exact de 3.3C

La Phase 3 doit se fermer sur une démonstration vérifiable :

> Le monde déterministe peut faire vivre les quatre personnages pendant une période prolongée, avec besoins, activités, déplacements, sommeil, blessures, récupération, pause et reprise, tout en produisant le même résultat pour les mêmes conditions initiales.

Porte de sortie attendue :

```text
une journée entière ou davantage
→ explicable
→ reproductible
→ reprenable après redémarrage
→ sans contradiction d’état
→ sans écritures lors des lectures
→ sans dérive numérique
→ sans dépendance au LLM
```

3.3C est principalement un lot de :

- vérification;
- instrumentation déterministe minimale;
- scénarios de référence;
- tests longue durée;
- fermeture documentaire technique.

Il ne doit pas devenir une refonte du simulateur.

---

## 3. Inspection préalable obligatoire

Dans la première section de ta réponse, confirme avec les noms exacts :

### Dépôt

- commit HEAD;
- branche;
- état de l’arbre;
- version Python;
- résultat des 188 tests;
- fichiers non suivis.

### Simulation

- point d’entrée exact de la simulation;
- manière de fixer l’heure de départ et l’heure cible;
- manière de construire ou fournir la seed;
- emplacement de la politique déterministe;
- structure de la file ou du calcul des prochaines frontières;
- ordre stable entre personnages;
- ordre stable entre événements simultanés;
- mécanisme d’arrêt si aucune frontière n’existe;
- protections contre les boucles à durée nulle.

### Temps

- source de `sim_now`;
- relation entre horloge canonique et temps simulé;
- comportement actif, paused et resumed;
- comportement au redémarrage;
- ancres temporelles persistées;
- usage éventuel de l’heure murale dans des décisions.

### État et journal

- tables d’état courant concernées;
- ordre et séquence des événements;
- identifiants ou champs susceptibles d’être non déterministes;
- méthode existante de lecture du journal;
- possibilité actuelle de comparer deux mondes ou deux bases;
- événements contenant des timestamps de commit distincts du temps canonique;
- données diagnostiques à exclure d’une comparaison sémantique.

### Persistance et reprise

- ouverture et fermeture des connexions;
- mécanisme d’initialisation d’un monde de test;
- façon de copier ou restaurer une base de test;
- transactions du simulateur;
- comportement après exception;
- données nécessaires pour reprendre exactement au même instant.

### Tests

Identifie les tests actuels qui prouvent déjà :

- déterminisme;
- pause;
- reprise;
- redémarrage;
- simulation accélérée;
- attente dynamique;
- sommeil;
- blessures;
- énergie;
- absence d’écriture sur lecture.

Exécute la régression seulement si cela ne modifie pas le dépôt. Rapporte explicitement le résultat.

---

## 4. Définition de la reproductibilité

Le plan doit distinguer :

```text
reproductibilité d’état
→ mêmes tables canoniques pertinentes à la fin

reproductibilité sémantique du journal
→ mêmes types, ordre, temps canoniques, acteurs et payloads

reproductibilité octet par octet
→ non exigée si des métadonnées techniques légitimes diffèrent
```

Recommandation normative :

- exiger l’égalité exacte des états canoniques pertinents;
- exiger l’égalité exacte du journal sémantique;
- normaliser ou exclure uniquement les métadonnées explicitement non canoniques;
- ne jamais masquer une divergence de séquence, type, temps simulé, cible ou payload.

Le plan doit proposer une structure de comparaison claire, par exemple :

```text
CanonicalStateDigest
SemanticEventDigest
SimulationRunReport
```

Ne persiste pas obligatoirement ces objets s’ils peuvent rester des outils de test ou de diagnostic.

---

## 5. Seed et ordre stable

Inspecte le rôle réel de la seed.

Le plan doit répondre :

- existe-t-il déjà un RNG?
- quelles décisions utilisent réellement la seed?
- la politique actuelle est-elle entièrement déterministe sans tirage?
- la seed est-elle persistée, fournie ou seulement utilisée dans les tests?
- l’ordre des candidats repose-t-il sur des tris explicites?
- un ensemble, dictionnaire ou résultat SQL non ordonné peut-il modifier un choix?
- les identifiants générés peuvent-ils varier entre deux runs?
- un timestamp mural peut-il entrer dans un payload canonique?

Règle :

```text
aucun faux aléatoire ajouté uniquement pour “tester la seed”
```

Si la seed n’influence encore aucune décision, le plan doit le dire clairement et vérifier qu’elle reste un contrat préparé pour l’avenir, sans inventer un mécanisme inutile.

Tout choix parmi plusieurs options équivalentes doit utiliser :

- un ordre canonique explicite;
- ou un RNG seedé et journalisé;
- jamais l’ordre accidentel de la base ou de Python.

---

## 6. Scénario de référence de fermeture

Propose un scénario de référence autonome, déterministe et reproductible couvrant au minimum :

- les quatre personnages techniques;
- les neuf lieux;
- déplacements;
- besoins;
- activités;
- idle dynamique;
- sommeil naturel;
- réveil;
- une blessure légère;
- une blessure modérée;
- une blessure sévère;
- surcharge énergétique;
- blocage de mouvement sévère;
- activité locale sous blessure sévère;
- récupération `severe → moderate`;
- guérison complète si la durée choisie le permet;
- pause;
- reprise;
- redémarrage;
- plusieurs frontières simultanées.

Le plan doit choisir une durée :

```text
24 heures minimum
```

et recommander si un deuxième scénario plus long est nécessaire :

```text
7 jours
ou
durée suffisante pour détecter les dérives
```

Ne force pas artificiellement chaque événement dans un seul run si cela rend le scénario illisible. Il est acceptable de proposer :

- un scénario principal de 24 h;
- un scénario spécialisé blessures;
- un scénario endurance de plusieurs jours.

Pour chacun, donne :

- état initial;
- heure de départ;
- seed;
- blessures initiales ou accidents scriptés;
- points de pause;
- point de redémarrage;
- heure finale;
- assertions majeures;
- événements attendus ou invariants, sans exiger une liste manuelle fragile de centaines d’événements.

---

## 7. Runs comparatifs obligatoires

Le plan doit prévoir au minimum les comparaisons suivantes.

### RUN A — Exécution continue

```text
base initiale
→ simulation complète jusqu’à T_final
→ état A
→ journal A
```

### RUN B — Même scénario dans une base indépendante

```text
même état initial
+ même configuration
+ même seed
→ état B
→ journal B
```

Assertion :

```text
state_digest(A) == state_digest(B)
semantic_event_digest(A) == semantic_event_digest(B)
```

### RUN C — Redémarrage au milieu

```text
simulation jusqu’à T_split
→ fermeture connexion/processus
→ réouverture depuis SQLite
→ reprise jusqu’à T_final
```

Comparer à RUN A.

### RUN D — Avance en plusieurs segments

```text
run_to(T1)
run_to(T2)
run_to(T3)
```

Comparer à :

```text
run_to(T3)
```

depuis le même état initial.

### RUN E — Pause et reprise

```text
pause à T_pause
→ écoulement mural ou tentative d’avance
→ aucun progrès simulé
→ reprise
→ continuation
```

Comparer l’état final à un run équivalent où l’intervalle de pause n’existe pas dans le temps simulé.

### RUN F — Lecture intensive

Insérer des lectures répétées entre les frontières :

- fiches de monde;
- fiches de personnages;
- besoins;
- blessures;
- activités;
- contexte de politique;
- journal.

Comparer au run sans ces lectures.

### RUN G — Exception et rollback

Injecter une exception contrôlée dans une transition significative, puis vérifier :

- état courant inchangé;
- journal inchangé;
- reprise possible;
- résultat final identique après nouvelle tentative.

Le plan doit recommander le point d’injection le plus réaliste sans ajouter un framework général de chaos testing.

---

## 8. Comparaison de l’état canonique

Définis les tables et champs à inclure.

Le plan doit inspecter les migrations réelles, puis proposer une liste exacte. Elle devrait probablement couvrir :

- monde et statut;
- horloge persistée;
- personnages;
- positions;
- besoins, ancres et restes;
- activités;
- blessures;
- objets ou graphes si modifiés par la simulation;
- séquence canonique.

Pour chaque table, distingue :

```text
champs canoniques à comparer
champs techniques stables à comparer
champs techniques légitimement variables à exclure
```

Ne compare pas seulement quelques valeurs finales visibles. Les restes rationnels et ancres doivent être inclus, car deux états affichant le même pourcentage peuvent diverger au prochain instant.

Le plan doit proposer une sérialisation canonique :

- tris explicites;
- format temporel normalisé;
- JSON déterministe ou tuples;
- aucune dépendance à l’ordre SQL implicite.

---

## 9. Comparaison du journal sémantique

Pour chaque événement, inclure au minimum :

- `world_id` si les runs utilisent le même identifiant contrôlé, sinon normalisation explicitement justifiée;
- `sequence`;
- `event_type`;
- `occurred_at` canonique;
- acteur/source;
- payload normalisé;
- causalité pertinente si présente.

Le plan doit identifier les champs à ne pas comparer s’ils sont non canoniques, par exemple :

- heure de commit murale;
- identifiant de fichier temporaire;
- identifiant de connexion;
- information purement diagnostique.

Attention :

> N’exclus aucun champ simplement parce qu’il diverge. Toute exclusion doit être justifiée par son statut non canonique.

Le plan doit aussi définir les vérifications structurelles :

```text
séquences continues
ordre strict
aucun événement orphelin
aucun doublon
payload conforme
temps canoniques non décroissants selon le contrat
état final cohérent avec le journal
```

Ne prétends pas reconstruire tout l’état depuis le journal si le dépôt ne garantit pas encore une couverture événementielle complète. Distingue :

- audit sémantique du journal;
- reconstruction complète;
- projection partielle.

---

## 10. Frontières simultanées et ordre stable

Le plan doit produire l’ordre réellement implémenté après 3.3B2, notamment pour :

- matérialisation de blessure;
- matérialisation des besoins;
- fin d’activité;
- guérison;
- passage dérivé de niveau;
- réveil;
- décision;
- démarrage d’activité;
- déplacement.

Prévois des tests où plusieurs personnages et plusieurs transitions partagent exactement le même `occurred_at`.

Assertions :

- ordre stable entre personnages;
- ordre stable des types de transitions;
- absence de traitement double;
- aucune décision sur état périmé;
- mêmes séquences entre RUN A, B et C.

Ne modifie l’ordre existant que si une contradiction réelle est démontrée.

---

## 11. Boucles et progression temporelle

Le plan doit vérifier :

- toute nouvelle frontière est strictement postérieure à l’instant courant, sauf transition immédiate bornée et consommée une seule fois;
- aucun `idle(1)` involontaire ne crée une simulation à la seconde;
- aucun personnage sévèrement blessé ne boucle sans progrès;
- aucune activité de durée zéro n’est relancée indéfiniment;
- le simulateur possède une limite de sécurité ou une détection d’absence de progrès;
- un monde stable sans frontière future s’arrête proprement;
- le nombre de transitions pour 24 h et plusieurs jours reste raisonnable.

Propose des seuils de test ou rapports, mais pas une optimisation prématurée.

---

## 12. Pause, reprise et temps réel

Distingue :

```text
temps mural
temps canonique du monde
temps cible du simulateur
temps des événements
```

Le plan doit prouver :

- un monde en pause ne progresse pas;
- les besoins et blessures ne récupèrent pas durant la pause;
- la reprise ne rattrape pas automatiquement le temps mural passé;
- le redémarrage pendant une pause conserve la pause;
- le redémarrage pendant un monde actif reprend depuis les ancres persistées;
- aucune lecture ne matérialise le temps.

Si l’horloge dérivée 1:1 a un comportement différent lors d’un run accéléré de test, documente précisément le contrat au lieu de le masquer.

---

## 13. Redémarrage et reprise

Le redémarrage de test doit représenter une vraie perte d’état en mémoire :

```text
fermer moteurs
fermer connexion
rouvrir SQLite
reconstruire moteurs
reprendre
```

Le plan doit vérifier qu’aucun élément nécessaire ne vit seulement en mémoire :

- seed;
- prochain réveil;
- activité;
- heure planifiée;
- reste rationnel;
- blessure;
- politique;
- séquence;
- ordre stable.

Si une donnée de run existe seulement dans le test, explique pourquoi elle est une entrée externe reproductible plutôt qu’un état du monde à persister.

---

## 14. Rapports de simulation

Propose un rapport stable et lisible, généré par les tests ou un outil diagnostic léger.

Exemple de contenu :

```text
SimulationRunReport
- commit
- schema_version
- world_id
- start_time
- end_time
- seed
- restart_points
- pause_intervals
- transition_count
- event_count_by_type
- final_character_states
- final_need_states
- final_injuries
- canonical_state_digest
- semantic_event_digest
- invariant_findings
```

Le rapport ne doit pas devenir une nouvelle vérité canonique ni exiger une migration.

Précise :

- où il serait généré;
- s’il appartient aux tests, à une commande diagnostic ou aux deux;
- son format;
- quels champs doivent être stables;
- quels champs sont seulement informatifs.

---

## 15. Invariants de fermeture de Phase 3

Le plan doit transformer ces règles en assertions vérifiables :

### Monde et temps

- un seul monde ciblé par chaque transition;
- pause sans progrès;
- temps simulé monotone;
- aucune transition après la cible;
- redémarrage sans saut temporel.

### Personnages et espace

- exactement une position canonique par personnage actif;
- toute arête traversée existe;
- aucun déplacement partiel après rollback;
- aucun mouvement sévère interdit;
- aucune téléportation.

### Besoins et énergie

- valeurs dans `[0,100000]`;
- aucun `REAL`;
- ancres cohérentes;
- restes dans leur plage;
- aucune énergie négative;
- matérialisation idempotente au même instant.

### Activités

- au plus une activité active par personnage;
- début, fin et interruption cohérents;
- ancien régime appliqué jusqu’à la frontière;
- aucune activité terminée deux fois;
- aucune durée négative.

### Blessures

- au plus une blessure active;
- sévérité et reste valides;
- blessures guéries terminales;
- récupération uniquement par temps simulé;
- niveau dérivé cohérent;
- surcharge et blocage appliqués;
- guérison exacte.

### Journal

- séquences continues;
- ordre stable;
- événements cohérents avec l’état;
- aucun événement de succès sur refus;
- payload `character_moved` stable;
- aucune écriture produite par une lecture.

### Reproductibilité

- mêmes conditions → mêmes digests;
- exécution continue = exécution segmentée;
- exécution continue = redémarrage;
- lectures supplémentaires sans effet;
- rollback puis retry = exécution normale.

---

## 16. Matrice de tests attendue

Le plan doit proposer les tests exacts, avec noms suggérés et responsabilités.

Minimum :

1. deux runs indépendants de 24 h donnent le même état;
2. deux runs indépendants donnent le même journal sémantique;
3. run continu = run en segments;
4. run continu = redémarrage au milieu;
5. redémarrage avec activité active;
6. redémarrage avec blessure active;
7. redémarrage en pause;
8. pause sans progression;
9. reprise sans rattrapage mural;
10. lectures répétées sans effet sur le résultat;
11. ordre stable de quatre personnages à frontière simultanée;
12. guérison, fin d’activité et décision au même instant;
13. severe→moderate et réveil au même instant;
14. coût multi-arêtes et événement stable dans un run long;
15. rollback injecté puis retry;
16. aucun pas de temps arbitraire;
17. détection de boucle ou absence de progrès;
18. simulation de plusieurs jours sans dérive de reste;
19. invariants de toutes les tables après run;
20. vérification structurelle du journal;
21. rapport stable;
22. régression complète des 188 tests existants.

Pour chaque test important, donne :

- fixture initiale;
- temps;
- seed;
- point de restart/pause;
- assertions;
- justification.

N’ajoute pas des centaines d’assertions fragiles sur un journal complet si des digests et vérifications ciblées donnent une preuve plus robuste.

---

## 17. Migration et schéma

Préférence forte :

```text
aucune migration
```

3.3C doit normalement ajouter :

- helpers de comparaison;
- tests;
- instrumentation;
- documentation;
- éventuellement une commande diagnostic légère.

Une migration n’est acceptable que si une donnée indispensable à la reprise déterministe manque réellement dans l’état persistant.

Si tu proposes une migration :

- démontre l’impossibilité de fermer la Phase 3 sans elle;
- décris la donnée;
- sa source d’autorité;
- sa valeur initiale;
- sa compatibilité;
- ses tests;
- son rollback.

Ne persiste pas des digests, rapports ou snapshots de test sans nécessité.

---

## 18. Documentation de fermeture

Le plan doit prévoir la mise à jour future, après implémentation, de :

- `CHANGELOG.md`;
- documentation technique de Phase 3;
- nombre de tests;
- commit officiel;
- scénario de référence;
- garanties prouvées;
- limites connues;
- exclusions;
- prochaine étape : audit technique de fermeture, pas Phase 4 automatique.

Le rapport de livraison devra distinguer :

```text
ce qui est prouvé par tests
ce qui est inspecté
ce qui reste une décision d’architecture future
```

---

## 19. Exclusions explicites

Ne traite pas dans 3.3C :

- interface administrative;
- registre général de composants ou capacités;
- actions de Phase 4;
- scènes;
- perception;
- croyances;
- mémoire psychologique;
- émotions;
- relations;
- consentement;
- Discord;
- LLM;
- nouveaux personnages;
- remplacement des personnages techniques;
- propriété canonique des chambres;
- monde extérieur;
- nouvelles activités de gameplay;
- nouvelles blessures ou douleur;
- mortalité;
- sauvegarde utilisateur complète;
- export/import;
- branches temporelles;
- reconstruction event-sourced complète;
- optimisation pour des centaines d’agents;
- fusion du dossier maître v0.2;
- audit technique final lui-même.

---

## 20. Format exact de ta réponse

1. **État réel inspecté**
   - commit, tests, arbre;
   - fonctions et fichiers;
   - garanties existantes;
   - lacunes réelles.

2. **Définition précise de la reproductibilité**
   - état;
   - journal;
   - métadonnées exclues;
   - digests.

3. **Scénarios de référence**
   - 24 h;
   - endurance éventuelle;
   - blessures;
   - pause;
   - restart.

4. **Runs comparatifs A à G**

5. **État canonique comparé**
   - tables;
   - champs;
   - normalisation.

6. **Journal sémantique comparé**
   - champs;
   - exclusions;
   - invariants.

7. **Seed, ordre stable et identifiants**

8. **Frontières simultanées**

9. **Pause, reprise et redémarrage**

10. **Boucles et absence de progrès**

11. **Rapport de simulation**

12. **Fichiers probablement touchés**
    - rôle exact;
    - aucune liste spéculative inutile.

13. **Migration ou absence de migration**

14. **Matrice de tests détaillée**

15. **Risques et cas limites**

16. **Plan de retour arrière**

17. **Documentation de fermeture**

18. **Éléments explicitement exclus**

19. **Décisions nécessitant l’approbation**
    - recommande une option pour chacune.

Ne code rien. Termine exactement par une demande d’approbation du plan avant toute modification du dépôt.
