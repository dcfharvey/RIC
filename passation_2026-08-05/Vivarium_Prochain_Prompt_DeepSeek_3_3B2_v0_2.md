# Prompt prêt à envoyer à DeepSeek — Sous-lot 3.3B2

**Projet :** Vivarium social artificiel  
**Type de réponse demandé :** plan détaillé seulement  
**Point de départ confirmé :** commit `f1335ca`  
**Dernier lot livré :** 3.3B1 — état de blessure, causalité et récupération  
**Régression confirmée après 3.3B1 :** 164 tests réussis  
**Prochain lot :** 3.3B2 — effets mécaniques des blessures

---

## 0. Autorité documentaire et méthode

Avant de répondre, inspecte réellement le dépôt, les migrations et les tests.

Ordre d’autorité pour ce travail :

1. code, migrations et tests présents dans le dépôt;
2. dossier maître actuellement présent dans le dépôt;
3. présente instruction de lot;
4. documents post-audit, uniquement pour les invariants pertinents à 3.3B2.

Documents post-audit à consulter s’ils sont présents dans ton contexte ou dans le dépôt :

- `Vivarium_Exigences_Normatives_Post_Audit_v0_1.md`;
- `Vivarium_Demande_Changement_Post_Audit_v0_2.md`;
- `Vivarium_Feuille_Route_Post_Audit_v0_1.md`.

Ces documents décrivent une direction approuvée, mais ne justifient pas une refonte générale pendant 3.3B2. Pour ce lot, retiens surtout :

```text
moteur canonique seul autorisé à modifier le monde
état courant et événements mis à jour atomiquement
lectures sans effets de bord
capacité actuelle dérivée de l’état, sans registre général prématuré
impossibilité canonique distincte d’une règle de politique
intention ou activité maintenue par défaut si elle reste compatible
événements significatifs seulement, pas de journalisation de chaque calcul
rejeu indépendant du LLM
tests positifs, négatifs, de régression et de crash lorsque pertinent
```

Ne présume jamais qu’un résumé remplace le code. Si le dépôt contredit une hypothèse de cette instruction, signale précisément la divergence et propose le changement minimal compatible avec les invariants.

---

## 1. Travail demandé maintenant

Produis uniquement le **plan final détaillé du sous-lot 3.3B2**.

Tu dois :

- inspecter l’existant;
- décrire ce que tu as trouvé;
- proposer les décisions exactes;
- identifier les fichiers probablement touchés;
- définir algorithmes, transactions, événements et tests;
- signaler les choix encore réellement ouverts;
- recommander une option pour chacun.

Tu ne dois pas :

- écrire du code;
- modifier un fichier;
- lancer une migration;
- créer un commit;
- déclarer le lot terminé.

Arrête-toi après le plan et attends l’approbation.

---

## 2. État 3.3B1 à préserver

Vérifie ces éléments dans le dépôt au lieu de les recréer :

- migration de blessure déjà livrée;
- une seule blessure active de mobilité par personnage;
- sévérité entière en milli-unités, bornée entre 0 et 100000;
- reste rationnel sur dénominateur 36;
- ancre temporelle de récupération;
- guérison exacte au premier instant où la sévérité atteint zéro;
- récupération fondée uniquement sur le temps simulé;
- régimes existants fournis par l’appelant :
  - passif = 2/36 milli par seconde;
  - repos = 6/36;
  - sommeil = 12/36;
- lecture dérivée pure;
- événements existants :
  - `scripted_accident`;
  - `injury_occurred`;
  - `injury_materialized`;
  - `injury_healed`;
- aucune colonne `REAL`;
- aucune modification de déplacement, activité, politique ou simulateur en 3.3B1.

Le plan 3.3B2 doit étendre ces mécanismes sans changer la causalité, l’historique ou les mathématiques de récupération.

---

## 3. Inspection préalable obligatoire

Dans la première partie de ta réponse, donne les noms réels trouvés pour :

- service ou moteur de déplacement;
- granularité actuelle d’un déplacement :
  - une arête;
  - chemin complet;
  - autre;
- événement ou événements de déplacement;
- représentation et matérialisation de l’énergie;
- borne basse autorisée de l’énergie;
- ancre et reste rationnel de l’énergie;
- démarrage, maintien, fin et interruption d’activité;
- sélection du régime de récupération de blessure;
- politique déterministe;
- simulateur et file de frontières;
- ordre temporel actuel aux frontières simultanées;
- transaction et mécanisme d’événement canonique;
- tests de référence concernés.

Exécute les tests de référence seulement si ton environnement permet de le faire sans modifier le dépôt. Rapporte le résultat. L’absence d’exécution doit être indiquée explicitement.

---

## 4. Classification des effets de mobilité

Le système doit dériver un **niveau d’effet mécanique** depuis `severity_milli`.

Niveaux requis :

```text
light
→ aucun effet mécanique dans ce lot

moderate
→ déplacement permis avec surcharge énergétique

severe
→ déplacement autonome interdit
```

Le plan doit :

- vérifier si des seuils existent déjà;
- sinon proposer un jeu exact de seuils;
- justifier brièvement ce jeu comme règle de conception, non comme vérité médicale;
- centraliser les seuils dans une seule définition;
- utiliser une fonction pure et testable;
- ne pas persister le niveau s’il est entièrement dérivable;
- ne pas dupliquer les conditions dans moteur, politique et simulateur;
- préciser le comportement exact aux valeurs frontières.

Utilise une seule terminologie canonique dans le code. Si l’existant emploie `grave`, `severe` ou une autre forme, recommande la convention minimale qui évite les traductions contradictoires.

Ne construis pas encore le futur registre général de capacités. Utilise le point d’extension le plus étroit de l’architecture actuelle.

---

## 5. Blessure légère

Exigence :

```text
light injury
→ comportement mécanique identique à l’absence de blessure
```

Le plan doit confirmer qu’aucun coût, blocage, interruption ou événement supplémentaire n’est produit uniquement parce que la blessure est légère.

La récupération continue normalement selon le régime actif.

---

## 6. Blessure modérée : surcharge de déplacement

Règle de conception approuvée pour ce lot :

```text
500 milli-énergie additionnels par arête réellement traversée
```

Cette surcharge s’ajoute aux coûts existants; elle ne remplace aucun coût déjà appliqué.

### 6.1 Matérialisation avant validation

Avant de décider si le déplacement peut être exécuté, le moteur doit disposer, au même instant simulé, de :

- la sévérité matérialisée de la blessure;
- l’énergie matérialisée;
- l’état et l’activité pertinents.

Le plan doit préciser :

- quelles fonctions existantes effectuent ces matérialisations;
- dans quel ordre elles sont appelées;
- quel régime de récupération s’applique jusqu’à cet instant;
- comment éviter qu’une lecture ou une simple prévisualisation écrive dans la base;
- comment éviter une double matérialisation dans la même transition.

### 6.2 Granularité du déplacement

Ne change pas silencieusement la sémantique actuelle du déplacement.

Si l’opération actuelle déplace sur un chemin complet atomiquement :

```text
surcharge = 500 × nombre total d’arêtes du chemin
```

et le moteur doit vérifier le total avant tout déplacement.

Si l’opération actuelle déplace une arête par opération canonique :

```text
surcharge = 500 pour cette arête
```

et chaque arête conserve son atomicité actuelle.

Le plan doit recommander l’intégration minimale selon ce qui existe réellement.

Garantie fonctionnelle :

> Une insuffisance d’énergie due à la surcharge de blessure ne doit jamais produire un débit partiel ni un déplacement partiel qui n’existait pas déjà dans la sémantique du moteur.

### 6.3 Énergie

Le plan doit expliquer :

- comment calculer la surcharge;
- comment l’ajouter aux coûts existants sans double débit;
- comment préserver l’ancre et le reste rationnel de l’énergie;
- comment vérifier la borne basse;
- comment permettre une énergie finale exactement égale à zéro si l’invariant actuel l’autorise;
- ce qui est refusé si l’énergie est insuffisante;
- quel état et quels événements restent inchangés lors d’un refus;
- comment le coût est expliqué dans l’audit.

Recommandation à confirmer après inspection :

```text
matérialiser à sim_now
→ calculer chemin et surcharge
→ vérifier toute l’énergie requise
→ appliquer débit et déplacement dans une même transaction
```

### 6.4 Événement de déplacement

Préfère enrichir l’événement de déplacement existant si son contrat peut porter proprement :

```text
base_energy_cost
injury_energy_surcharge
edge_count
total_energy_cost
injury_effect_level
```

Ne crée un événement séparé que si le contrat actuel rend cet enrichissement incohérent.

Évite :

- deux événements représentant le même débit;
- un événement de coût sans changement d’énergie;
- un changement d’énergie sans événement canonique significatif;
- un événement de refus présenté comme si le déplacement avait eu lieu.

Un refus peut rester une erreur structurée ou un diagnostic. Il ne devient un événement du monde que si le dépôt possède déjà une politique cohérente pour les tentatives refusées.

---

## 7. Blessure sévère : frontière entre moteur et autonomie

Exigence approuvée :

```text
severe injury
→ aucun déplacement choisi ou déclenché par la politique autonome
→ activités locales compatibles toujours possibles
```

La blessure sévère ne signifie pas paralysie générale.

Exemples à préserver selon les activités existantes :

- cuisine : `eat`;
- salle de bain : `clean`;
- chambre : `sleep` ou `rest`;
- salon : `rest`;
- autre activité locale déjà autorisée et mécaniquement compatible.

Aucune téléportation et aucun déplacement automatique vers un lieu de récupération.

### 7.1 Politique autonome

Le plan doit garantir que :

- les destinations nécessitant un déplacement sont exclues;
- une activité locale compatible peut être poursuivie ou choisie;
- la politique ne boucle pas sur une destination impossible;
- l’absence d’activité utile produit un `idle` dynamique;
- la récupération passive continue pendant cet `idle`;
- une nouvelle décision devient possible à l’instant exact du passage `severe → moderate`.

### 7.2 API canonique de déplacement

Ne présume pas la réponse.

Inspecte si l’API actuelle distingue :

- action autonome;
- commande de test;
- commande directe;
- intervention administrative;
- source de commande.

Présente au moins deux frontières possibles :

1. blocage uniquement dans la politique autonome;
2. blocage canonique de tout déplacement volontaire du personnage, avec voie administrative future distincte.

Pour chacune, donne :

- cohérence avec le code actuel;
- risques d’invariant;
- risques de contournement;
- coût de mise en œuvre;
- effet sur les tests.

Recommande une seule frontière pour 3.3B2.

Ne crée pas dans ce lot un système administratif avancé ni un transport assisté.

---

## 8. Activité en cours et changement de régime

Une blessure ne doit pas annuler silencieusement toute activité.

Règles souhaitées :

```text
activité locale encore compatible
→ continue

activité devenue mécaniquement incompatible
→ interruption canonique explicite

aucune incompatibilité réelle
→ aucune interruption
```

Le plan doit inspecter les activités existantes et identifier celles qui seraient réellement incompatibles avec une blessure sévère. N’invente pas une incompatibilité sans règle mécanique.

### 8.1 Frontière de changement d’activité

Lorsqu’une activité commence, finit ou est interrompue au temps `T` :

```text
1. matérialiser la blessure jusqu’à T avec l’ancien régime
2. matérialiser les besoins et l’activité jusqu’à T selon les règles existantes
3. appliquer la transition d’activité
4. sélectionner le nouveau régime pour l’intervalle suivant
```

Le nouveau régime ne doit jamais être appliqué rétroactivement à l’intervalle précédent.

Le plan doit préciser les transactions et événements associés à :

- continuation;
- fin normale;
- interruption éventuelle;
- passage de `sleep` ou `rest` vers passif;
- passage de passif vers `rest` ou `sleep`.

---

## 9. Frontière exacte `severe → moderate`

Le simulateur ne doit pas attendre un tick arbitraire.

Le plan doit définir une fonction pure calculant le premier instant où la sévérité franchit le seuil sévère vers modéré, à partir de :

- `severity_milli`;
- `rate_remainder`;
- régime courant;
- seuil choisi.

Cette fonction doit être l’équivalent généralisé du calcul exact de guérison déjà présent en 3.3B1.

Le plan doit donner :

- la formule entière;
- le comportement quand le personnage est déjà modéré;
- le comportement quand le taux est nul ou invalide;
- la conservation du reste `/36`;
- l’événement ou la matérialisation produit à la frontière;
- la manière dont la politique est réveillée exactement à cette heure;
- l’absence de boucle par minute ou par seconde.

Une guérison complète et un passage de niveau sont deux frontières distinctes, même s’ils peuvent parfois coïncider avec une autre transition.

---

## 10. Politique et simulateur

Le contexte déterministe de politique doit connaître au minimum :

- niveau d’effet dérivé de la blessure;
- activité courante;
- activités localement réalisables;
- destinations actuellement accessibles;
- énergie matérialisée ou bandes déjà utilisées par la politique;
- prochaine frontière pertinente de récupération.

Le plan doit expliquer :

- où ce contexte est construit;
- comment il reste en lecture pure;
- comment une seule fonction de classification est partagée;
- comment les options de mouvement sont supprimées en niveau sévère;
- comment l’intention ou l’activité actuelle est maintenue si elle reste valide;
- comment l’`idle` dynamique programme la prochaine frontière;
- comment le redémarrage reconstruit la même prochaine décision;
- comment la seed et l’ordre stable conservent la reproductibilité.

Aucun LLM ne participe à 3.3B2.

---

## 11. Frontières temporelles simultanées

Commence par documenter l’ordre actuel réellement implémenté.

Puis propose l’extension minimale donnant un ordre unique et testable lorsque plusieurs choses arrivent au même instant, notamment :

- matérialisation de blessure;
- passage `severe → moderate`;
- guérison;
- fin d’activité;
- matérialisation de besoins;
- réveil;
- décision de politique;
- déplacement.

Le plan doit respecter ces principes :

```text
les effets de l’intervalle précédent sont matérialisés avant la transition
un changement d’état n’est appliqué qu’une fois
les postconditions sont visibles avant la nouvelle décision
une décision ne s’exécute pas sur un état périmé
aucune double écriture ni double événement
```

Donne un tableau de priorité ou un algorithme précis.

Ne remplace pas arbitrairement l’ordre existant si une extension locale suffit.

---

## 12. Transactions attendues

Décris les limites transactionnelles exactes pour :

### A. Déplacement modéré réussi

Doit inclure, selon l’architecture existante :

- vérifications de version ou d’état;
- matérialisations nécessaires;
- validation du chemin;
- calcul du coût total;
- vérification de l’énergie;
- débit;
- changement de position;
- événements;
- commit unique.

### B. Déplacement refusé pour énergie insuffisante

Garantie :

```text
aucun débit
aucun mouvement
aucune modification partielle
aucun faux événement de déplacement
```

### C. Mouvement autonome exclu par blessure sévère

Précise si l’exclusion survient :

- à la génération d’options;
- à la sélection;
- à la validation canonique;
- à plusieurs niveaux par défense en profondeur.

Évite de dupliquer une logique contradictoire.

### D. Fin ou interruption d’activité

Matérialiser l’ancien intervalle, appliquer la transition, auditer, puis établir le nouveau régime.

### E. Attente jusqu’à la frontière de récupération

Aucune écriture lors d’une simple lecture de la prochaine frontière. La matérialisation se produit seulement lors de la transition canonique prévue ou d’une autre commande au même instant.

---

## 13. Invariants à préserver

- aucune colonne `REAL`;
- calculs entiers à précision fixe;
- reste rationnel conservé;
- lecture pure sans écriture;
- état courant et événements atomiques;
- aucune énergie négative;
- aucune téléportation;
- une seule position canonique;
- une seule blessure active;
- blessure guérie immuable;
- récupération uniquement par temps simulé;
- pause = aucun progrès temporel;
- redémarrage reproductible;
- aucune décision ou reconstruction par LLM;
- aucun état persistant modifié sans trace canonique significative;
- aucun nouveau registre général de capacités;
- aucune refonte non nécessaire.

---

## 14. Migration

Détermine si une migration est réellement requise.

Préférence :

```text
classification dérivée
+ constantes centralisées
+ enrichissement des contrats existants
→ aucune migration
```

Une migration n’est acceptable que si un nouvel état persistant est indispensable et impossible à dériver correctement.

Interdictions :

- modification destructive de `0008`;
- modification de l’historique de blessures;
- seed de blessures par défaut;
- conversion silencieuse de données;
- nouvelle colonne redondante seulement pour mémoriser `light/moderate/severe`.

---

## 15. Matrice de tests obligatoire

Le plan doit fournir des scénarios chiffrés et reproductibles.

Pour chaque scénario, indique :

- état initial;
- heure simulée;
- sévérité;
- reste de blessure;
- régime;
- énergie et reste d’énergie;
- lieu;
- activité;
- commande ou frontière;
- événements attendus dans l’ordre;
- état final;
- absence d’effets indésirables.

Scénarios minimaux :

1. blessure légère identique à l’absence de blessure;
2. valeur exacte à chaque seuil de classification;
3. blessure modérée, une arête : surcharge exacte de 500;
4. blessure modérée, plusieurs arêtes selon la granularité réelle;
5. surcharge ajoutée au coût existant sans double débit;
6. énergie exactement égale au coût total : déplacement permis et borne basse valide;
7. énergie inférieure d’une milli-unité : refus atomique;
8. refus répété : aucun débit différé et aucune écriture parasite;
9. blessure sévère : politique ne génère ou ne sélectionne aucun mouvement;
10. blessure sévère en cuisine : `eat` reste possible;
11. blessure sévère en chambre : `sleep` ou `rest` reste possible;
12. blessure sévère dans un lieu sans activité utile : `idle` dynamique;
13. passage `severe → moderate` au premier instant exact;
14. politique réveillée à cette frontière et non avant;
15. activité locale compatible poursuivie après apparition de la blessure;
16. activité réellement incompatible interrompue avec événement explicite, seulement si le plan en identifie une;
17. changement de régime à une frontière avec conservation exacte du reste;
18. guérison et fin d’activité au même instant;
19. passage `severe → moderate` et réveil au même instant;
20. pause et reprise;
21. redémarrage au milieu de la récupération;
22. lecture dérivée répétée sans écriture;
23. tentative de déplacement direct sous blessure sévère selon la frontière recommandée;
24. crash ou exception entre validation et commit : rollback complet;
25. simulation accélérée reproductible;
26. régression complète des 164 tests existants.

Ajoute tout test rendu nécessaire par l’inspection du dépôt.

---

## 16. Documentation et traçabilité prévues pour l’implémentation future

Le plan doit prévoir, pour la phase de code ultérieure :

- documentation des seuils comme règle de jeu;
- mise à jour du dossier technique de Phase 3;
- rapport de livraison standard;
- commit dédié;
- liste exacte des tests;
- preuve que la régression passe;
- arrêt après le lot.

Ne modifie toutefois aucun document maintenant.

---

## 17. Exclusions explicites

Ne traite pas dans 3.3B2 :

- douleur comme système distinct;
- perception des blessures;
- émotions;
- mémoire;
- croyances;
- relations;
- consentement;
- maladies;
- blessures multiples;
- mortalité;
- dommages permanents;
- assistance au déplacement;
- transport par une autre personne;
- nouvelles activités non indispensables;
- monde extérieur;
- Discord;
- LLM;
- interface administrative;
- registre général de composants ou capacités;
- migration post-audit globale;
- dossier maître v0.2;
- rééquilibrage général des besoins;
- refonte de l’architecture de mouvement;
- Phase 3.3C.

---

## 18. Format exact de ta réponse

1. **État réel inspecté**
   - commit;
   - tests;
   - fichiers;
   - fonctions;
   - granularité du mouvement;
   - ordre temporel existant;
   - divergences éventuelles.

2. **Décisions proposées**
   - seuils;
   - terminologie;
   - frontière moteur/politique;
   - granularité du coût;
   - stratégie d’événements.

3. **Fichiers probablement touchés**
   - rôle de chaque modification;
   - aucune liste spéculative non justifiée.

4. **Algorithmes purs**
   - classification;
   - coût;
   - temps exact vers seuil;
   - construction du contexte de politique.

5. **Transactions**
   - déplacement réussi;
   - refus;
   - transition d’activité;
   - frontière de récupération.

6. **Ordre des frontières simultanées**

7. **Événements et audit**

8. **Migration ou absence de migration**

9. **Matrice de tests chiffrés**

10. **Risques et cas limites**

11. **Plan de retour arrière**

12. **Éléments explicitement exclus**

13. **Décisions nécessitant encore l’approbation**
    - recommande une option pour chacune;
    - ne laisse pas une question ouverte sans recommandation.

Ne code rien. Termine exactement par une demande d’approbation du plan avant toute modification du dépôt.
