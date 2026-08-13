# Work order 91 — porte de démarrage réel du Rodage V2

**Statut : FERMÉ — WO91 satisfait; le démarrage officiel est préparé mais non exécuté.**

**Base :** `ce3bec5d7d9825784f397c8db9c77239f3886b13` (`0.2.0a2`, schéma 56, WO90 fermé).

**HEAD fonctionnel WO91 :** `20291d4b8b9a72ceab786eb7f4dc37312cc4d5c8` (`0.2.0a3`, schéma 57).

## 1. Pourquoi WO91 existe

WO90 a correctement rendu représentables la topologie hors propriété, le sommeil hors chambre, les plans de lieu et un bootstrap T0 jetable. La vérification pré-lancement a toutefois montré trois écarts entre « représentable » et « histoire officielle correcte ».

1. `character_location_plan` persiste actuellement un plan append-only, mais WO90 n'a pas raccordé son échéance au runtime. Le test vérifie que le retour de Sophie à 16 h est enregistré; il ne prouve pas qu'elle rentre réellement à 16 h.
2. Le banc jetable WO90 représente « Sophie travaille » par `photography`. Le canon dit seulement qu'elle est photographe journalistique et qu'elle travaille actuellement; son sous-geste exact à T0 n'est pas décidé.
3. Le banc physiologique jetable assigne volontairement le profil humain aux cinq personnages. Cette commodité de qualification n'est pas un canon biologique acceptable pour le vrai T0. Le catalogue quantitatif actuel ne fournit que `human_reference_candidate.v1` et `generic_feline_hypothesis.v1`, alors que le casting comprend deux humaines, une louve anthropomorphe, une slime et une chatte domestique.

WO91 ferme uniquement ces écarts et fournit un point d'entrée opérateur sûr. Il ne doit pas devenir le chantier général d'ontologie des actions ou de physiologie comparée.

## Clarification temporelle — contrat générique de frontières

`character_location_plan` n'est pas un cas particulier Sophie : il constitue la
première instance d'un mécanisme générique d'engagements temporels. Le scheduler
réutilise l'horloge canonique et les frontières déjà présentes des activités et
checkpoints. Une action en cours expose sa prochaine frontière (`planned_end_at`,
réévaluation ou checkpoint); un plan futur expose `planned_at`, une cible, une
provenance et une résolution append-only. À l'échéance, le moteur revalide la
transition et produit `fulfilled`, `refused`, `cancelled` ou `deferred`; un plan
prévu n'est jamais considéré comme un fait accompli avant cette résolution.

La résolution est idempotente et déterministe : elle ne dépend ni du LLM, ni d'un
polling subjectif, ni d'une seconde horloge. Une traversée refusée produit un
diagnostic explicite sans téléportation ni écriture partielle.

## 2. Faits produit du T0 à préserver

- Sophie : hors domicile, au travail comme photographe journalistique; retour au foyer à 16 h EDT. Ne pas inventer employeur, média, affectation, collègue ni sous-tâche précise.
- Erika : au salon, joue à des jeux vidéo; jeu non spécifié.
- Patoune : dort dans le salon, blotti contre Erika; ne matérialiser « sur le divan » ou le contact physique que si un mécanisme générique réellement supporté existe.
- Chuu : dans le bain / contexte d'hygiène, se détend et se réhydrate, s'apprête à sortir; aucune jauge de confort inventée; l'hydratation reste owned par le mécanisme générique de ressource.
- Luna : arrive pour la première fois en taxi avec un sac d'effets personnels; contenu indéterminé; le taxi n'a pas à devenir une entité persistante.
- L'heure canonique suit l'heure réelle EDT.

Le T0 exact est capturé une seule fois au démarrage persistant. Aucun passé n'est reconstruit avant cet instant.

Si l'opération de démarrage est tentée à ou après 16 h EDT le jour du scénario, elle doit refuser avant toute création du SQLite officiel : le fait « Sophie est encore au travail et revient à 16 h » serait alors temporellement incohérent et devra être rafraîchi par le propriétaire.

## 3. Contrat A — un engagement temporel doit devenir causal

Un plan de lieu `planned` arrivé à échéance ne peut rester une simple note.

Exigences fonctionnelles :

- le runtime possède une frontière déterministe pour les plans de lieu dus;
- l'échéance est évaluée sur le temps canonique, jamais sur la latence LLM;
- un plan dû et encore valide est exécuté via les moteurs canoniques de déplacement/activité, pas par écriture SQL cognitive directe;
- l'exécution est idempotente et observable;
- l'état append-only du plan est préservé : une résolution/transition explicite remplace toute mutation destructive si nécessaire;
- une impossibilité réelle n'est jamais avalée silencieusement : elle produit un résultat explicable/diagnostic plutôt qu'une téléportation mensongère;
- aucun personnage n'est codé en dur;
- le test d'acceptation doit prouver que Sophie, placée au travail avec retour à 16 h, atteint l'entrée extérieure du foyer à 16 h canonique sans appel LLM nécessaire.

Codex décide comment raccorder cette frontière au scheduler existant et comment représenter la résolution append-only.

## 4. Contrat B — représenter « travailler » sans inventer le sous-geste

Le T0 doit pouvoir affirmer canoniquement qu'un personnage est engagé dans son travail sans conclure qu'il photographie précisément à cet instant.

WO91 autorise le plus petit mécanisme générique requis : activité `work`, famille/propriété d'activité, engagement canonique de rôle ou autre représentation cohérente avec l'architecture réelle.

Contraintes :

- mécanisme générique, non lié à Sophie ni au métier de photographe;
- la profession « photographe journalistique » reste un fait distinct de l'action courante;
- aucune tâche, commande ou affectation inventée;
- les propriétés nécessaires au préflight actif (veille soutenue, charge physique, interruptibilité, etc.) doivent être explicites et identifiées comme choix d'ingénierie lorsque la science ne fixe pas une valeur unique;
- ne pas lancer le chantier complet du vocabulaire composable d'actions dans WO91.

## 5. Contrat C — physiologie T0 sans fausse biologie ni faux passé

### 5.1 Ce qui est fondé

Le modèle veille-sommeil RIC et sa séparation H / φ / P sont déjà fondés dans `docs/79_R_D_CYCLE_DIURNE_CIRCADIEN_SOMMEIL.md` et les work orders 85–88. Le catalogue actuel fournit :

- `human_reference_candidate.v1` : candidat humain [C/D], non constante biologique;
- `generic_feline_hypothesis.v1` : hypothèse féline [C], non physiologie féline littérale.

### 5.2 Affectation au casting

- Sophie et Erika : candidat humain existant.
- Patoune : candidat félin existant.
- Luna et Chuu : ne pas leur attribuer silencieusement une étiquette biologique humaine. En l'absence d'un profil empirique/canonique suffisant pour une louve anthropomorphe ou une slime, WO91 retient une **hypothèse de transfert explicite** : un profil de base `fictional_sapient_baseline` peut reprendre provisoirement la dynamique quantitative du candidat humain tout en portant une identité/provenance `fictional_canon` distincte. Cela signifie « baseline fonctionnelle faute de données discriminantes », pas « physiologie humaine ».

Cette baseline doit être data-driven et réutilisable; aucun `if character == luna/chuu`. Toute future calibration canine, lupine ou slime est un travail R&D distinct et pourra remplacer l'assignation sans changer le moteur générique.

### 5.3 Condition initiale sans histoire pré-T0

Le vrai T0 ne reconstruit ni sommeil antérieur, ni exposition lumineuse antérieure, ni fatigue antérieure.

Règle de design [D] :

- H est choisi déterministement au centre de la région T0 neutre approuvée par la politique enregistrée;
- P est choisi déterministement au centre de la région T0 normale/haute approuvée;
- φ est choisi par une règle T0 versionnée compatible avec l'état lumineux canonique à T0, et non copié d'une fixture;
- résidus H/φ et reste P = zéro;
- `previous_band` est dérivée/validée par le modèle à partir des causes T0; elle n'est pas choisie librement;
- les valeurs finales et leur provenance sont consignées dans le manifeste officiel;
- aucune valeur de fixture WO89/WO90 n'est promue par simple copie.

Si l'architecture actuelle ne peut pas calculer proprement cette condition initiale à partir des politiques versionnées, Codex peut ajouter le plus petit helper déterministe testable. Toute nouvelle équation ou calibration substantielle doit être signalée plutôt qu'inventée.

Les circonstances asymétriques du T0 commencent à faire diverger les états après T0; il n'est pas nécessaire d'inventer des histoires physiologiques différentes avant T0 pour casser la symétrie.

## 6. Contrat D — point d'entrée opérateur officiel

Le démarrage réel ne doit pas dépendre d'un copier-coller Python ad hoc.

Créer ou utiliser un point d'entrée opérateur supporté qui :

- cible une nouvelle base `data/vivarium-rodage-v2.sqlite`;
- refuse si cette cible existe déjà;
- ne modifie, ne renomme, ne migre et ne supprime jamais `data/vivarium-rodage.sqlite` ni ses WAL/SHM;
- capture une seule fois le T0 EDT réel;
- refuse avant écriture si le scénario est devenu temporellement incohérent (notamment T0 >= 16 h EDT sans rafraîchissement produit);
- applique schéma/migrations sur base neuve;
- construit le monde, le casting et les conditions asymétriques par les services canoniques;
- installe/assigne les politiques nécessaires et active H/φ/P depuis un manifeste officiel scellé;
- exécute le préflight read-only et l'observation Hugin avant l'ouverture de la première session runtime;
- vérifie que le provider LLM opérationnel attendu est disponible avant d'ouvrir l'histoire autonome;
- ne démarre la session runtime qu'après tous les contrôles verts;
- échoue atomiquement ou laisse une base explicitement non démarrée/diagnostiquable; aucune demi-histoire silencieuse.

Le bridge actuel déclare `RUNTIME_CONTROL=DENY` et `REAL_WORLD_WRITE=DENY`. WO91 ne doit pas affaiblir cette frontière de sécurité. Le lancement officiel restera donc une intervention locale explicite via le point d'entrée supporté.

## 7. LLM attendu pour le rodage

Le modèle retenu demeure `Qwen3-14B` quantifié `Q4_K_M`, en FR/FR, contrat `interpretation-only`. Le point d'entrée ne doit pas substituer silencieusement un autre modèle si celui attendu n'est pas disponible.

## 8. Validation minimale

Avant fermeture :

1. test d'échéance : un plan dû s'exécute exactement à la frontière canonique et une fois;
2. test latence : aucun LLM ne peut faire passer l'action après une échéance déterministe;
3. test échec : plan impossible produit un résultat explicite sans corruption/écriture partielle;
4. test `work`/équivalent : état « travaille » sans sous-geste inventé;
5. test profils : humains, félin, baseline fictionnelle distinctement provenancés;
6. test manifeste : condition initiale dérivée de la politique, résidus zéro, aucune fixture recopiée par convention cachée;
7. test bootstrap : cible absente -> création neuve; cible présente -> refus sans écriture;
8. test ancien rodage : ancien SQLite et sidecars inchangés;
9. test horaire : tentative après 16 h refuse avant création pour ce scénario;
10. répétition complète sur SQLite jetable avec préflight + Hugin;
11. tests ciblés, `compileall`, suite complète.

Le code réel, les migrations éventuelles, la version et l'ordre d'implantation restent de l'autorité de Codex.

## Verdict de fermeture WO91

La porte de fermeture est **SATISFAITE**. Le scheduler actif raccorde les plans
de lieu aux frontières canoniques existantes : Sophie reste au travail avant
16 h EDT et atteint causalement l'entrée du foyer à l'échéance, une seule fois.
`work` exprime l'engagement professionnel sans inventer une photographie; les
profils T0 sont `human_reference` pour Sophie/Erika, `generic_feline` pour
Patoune et `fictional_canon` pour Luna/Chuu, avec H/P aux centres des politiques,
phi dérivée de la lumière et résidus nuls. Le point d'entrée local exact est :

```text
.venv\Scripts\python.exe -m vivarium.rodage_v2_official --db data/vivarium-rodage-v2.sqlite
```

Il refuse une cible existante ou un T0 devenu obsolète, vérifie Qwen3-14B, le
préflight et Hugin, puis ouvre la session seulement après ces contrôles. La
répétition jetable, la compilation et la suite complète sont vertes; aucun
SQLite officiel n'a été créé.

## 9. Porte de fermeture

WO91 est fermé :

- le retour à 16 h est causal, pas seulement enregistré;
- « travailler » est représenté sans surspécification;
- la physiologie T0 du casting est explicitement provenancée sans fausse histoire;
- un point d'entrée local sûr et répétable existe;
- la répétition jetable est verte;
- aucune base officielle V2 n'a encore été créée;
- tests ciblés, compilation et suite complète sont verts;
- HEAD/version/schéma/migration sont consignés.

**Après fermeture seulement**, l'opérateur local peut exécuter une fois le point d'entrée officiel et démarrer le Rodage V2.
