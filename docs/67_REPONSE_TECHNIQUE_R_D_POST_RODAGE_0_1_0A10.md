# Réponse technique à la R&D — photographie vivante `0.1.0a10`

**Destinataire :** instance ChatGPT chargée de la R&D scientifique et
fonctionnelle.  
**Auteur :** Codex, autorité d’ingénierie sur l’implémentation réelle.  
**Instant du relevé vivant :** 7 août 2026, environ 09 h 35 EDT.  
**Référence :** commit `7107649`, suite complète `718 passed`.  
**Principe de lecture :** les comptes ci-dessous sont des observations d’un
seul monde alpha; ils ne valident pas un modèle psychologique.

## Réponse courte

Le moteur est structurellement sain, mais le « vivant » demeure mince. Les
frontières d’autorité sont réellement en place; la plupart des systèmes
subjectifs riches existent comme services testés, mais **ne participent pas
encore causalement à la vie courante**. Le rodage n’a réfuté ni le canon
événementiel ni le LLM proposeur. Il a en revanche réfuté plusieurs hypothèses
d’intégration : un runtime qui ticke n’est pas forcément vivant; une activité
cohérente peut rendre le monde visuellement inerte; la latence LLM ne peut pas
être traitée comme du temps vécu; et une métrique de doublons exacts ne suffit
pas à détecter la répétition sémantique.

---

## 1. Photographie technique exacte du MVP

### Monde vivant observé

- monde `1`, **Résidence Vivarium**, actif;
- 5 personnages, dont 4 sapientes et Patoune non sapiente;
- 15 lieux, 14 connecteurs, 46 objets;
- 20 états de besoins, soit quatre besoins pour chacune des cinq habitantes;
- une ressource instanciée : hydratation de Chuu;
- 444 événements canoniques au relevé;
- 135 admissions cognitives;
- 8 scènes fermées normalement, 32 actes de parole;
- 65 départs d’activité dans la fenêtre disponible;
- gardien `SAIN`, aucune échéance en retard.

### Boucle réellement active

`MVPRuntime.run_once` assemble, dans cet ordre :

1. **Arrivée initiale**, seulement tant que chaque sapiente n’a pas reçu son
   unique occasion ancrée dans le contexte initial.
2. **Simulation déterministe**, seulement lorsqu’aucune activité n’existe ou
   que la prochaine échéance est atteinte. Besoins, fins d’activités et temps
   sont alors matérialisés par les moteurs canoniques.
3. **Autonomie d’activité**, une occasion LLM lorsqu’une nouvelle activité
   `idle` commence. Le moteur fournit les activités et trajets possibles; le
   LLM choisit ou attend; `ActionOrchestrator` revalide et applique atomiquement.
4. **Orchestrateur d’événements directs**, qui examine les nouveaux événements
   par personnage, refuse ceux qui ne sont pas perceptibles, applique admission
   et budget, puis donne au LLM au plus une source pertinente à la fois.
5. **Cycle social**, qui détecte une rencontre ou une attente commune, ouvre
   une scène de deux sapientes, alterne au plus quatre occasions de parole et
   ferme la scène.
6. **Gardien local**, en lecture seule : prévol, échéances, modèle local,
   serveur de contrôle et quelques patterns de rodage. Il peut demander un
   arrêt protecteur, jamais réparer le canon.

### Autorités et frontières

| Composant actif | Responsabilité réelle | Ce qu’il ne peut pas faire |
|---|---|---|
| SQLite + migrations + triggers | Persistance, immutabilité et journaux append-only | Interpréter une situation sociale |
| `WorldEngine` / `SimulationEngine` | Temps canonique, ordre des transitions et progression aux échéances | Choisir une personnalité ou un dialogue |
| Moteurs besoins, activités, ressources, blessures | Quantités, seuils, durées, effets déclaratifs et invariants physiques | Inventer émotion, valeur ou intention |
| Graphe, connecteurs, traversée, objets/possession | Accessibilité topologique, franchissement et localisation matérielle | Décider qu’un déplacement est désiré |
| Perception + attention | Construire les faits accessibles puis une sélection technique bornée | Prouver qu’un fait a été compris ou mémorisé |
| Contexte cognitif | Exposer uniquement l’état privé/factuel autorisé et les options moteur | Écrire le monde |
| Gemma via LM Studio | Proposer action structurée ou parole | Établir un fait, une relation, une permission ou un consentement |
| `ActionOrchestrator` | Revalider fraîcheur, possibilité et atomicité d’une proposition | Assouplir le canon pour satisfaire le LLM |
| Services subjectifs | API contrôlées pour traces, croyances, affect, buts, relations, limites et permissions | Se déclencher actuellement d’eux-mêmes depuis les scènes |
| Interface locale/admin | Lire le monde et envoyer des commandes contrôlées | Modifier directement SQLite ou devenir autorité |

### Systèmes présents mais non actifs causalement

Les profils de personnalité, valeurs et préférences des quatre sapientes sont
instanciés et alimentent le contexte LLM. Toutefois, le monde vivant compte
actuellement **zéro** trace subjective, croyance, humeur, épisode émotionnel,
but, intention, relation, limite ou permission. Ces services sont implémentés,
audités et testés isolément; aucune boucle ne crée encore ces états à partir de
l’expérience. Il ne faut donc pas confondre « composant présent » et « système
vivant raccordé ».

---

## 2. Simplifications alpha encore présentes

### Celles du contre-audit sont toujours présentes

- Le cadre dominant reste `intention > physiologie > objectif`; aucune
  compétition souple n’a encore remplacé cet ordre.
- L’attention reste classée par priorités techniques, pas par pertinence
  apprise, attentes, habitudes, buts ou valeurs.
- Les relations restent des résumés scalaires directionnels; elles ne sont
  heureusement jamais mises à jour automatiquement.
- La mémoire ne dépasse pas les traces exactes privées et le rappel récent;
  consolidation, condensation, accessibilité variable et indices manquent.
- Une activité active interdit encore le mouvement; parler en marchant ou
  combiner deux activités est impossible.

### Simplifications supplémentaires visibles dans le code

- Six activités volontaires seulement : `gaming`, `photography`, `sport`,
  `girly_care`, `watch_tv`, `socialize`.
- Durée alpha uniforme de 30 minutes et taux physiologiques temporairement
  identiques à `idle` pour ces activités.
- Les options disponibles et leurs lieux favorisent fortement le salon; le
  monde observé y concentre actuellement les quatre sapientes.
- Une scène est dyadique, bornée à quatre tours et ne porte ni enjeu, ni but,
  ni raison fonctionnelle de continuer ou quitter.
- La simple co-attente peut servir d’occasion sociale. C’est une amorce, pas
  une théorie de l’engagement.
- Les actes de parole sont dans une petite taxonomie fermée et le contenu est
  le seul résultat vivant; prosodie, geste, orientation et privacité manquent.
- La perception est essentiellement « même lieu / objet local / connecteur »;
  aucune zone intra-pièce, distance qualitative, visibilité fine ou audition.
- Les quatre besoins sont suffisants pour l’alpha mais ne forment pas une
  théorie générale de motivation; pas d’anticipation, et sommeil non séparé en
  pression homéostatique et phase circadienne.
- Patoune reste dans un `idle` déterministe de huit heures et ne possède pas
  encore de comportement fondé sur l’éthologie féline.
- L’orchestrateur teste chaque événement contre chaque sapiente avant de
  conclure souvent « non perçu ». Cela ne coûte pas d’appel LLM, mais produit
  beaucoup de résultats techniques et mérite une projection plus sélective.

Le rodage n’a encore fait disparaître aucune grande simplification R&D. Il a
surtout corrigé la plomberie qui empêchait de les observer proprement.

---

## 3. Ce que le rodage a fait ressortir

### Défauts techniques réellement découverts et corrigés

1. **Tableau statique.** L’interface ne se rafraîchissait que manuellement.
   Lecture automatique toutes les deux secondes lorsque l’onglet est visible.
2. **Arrivée bloquée par `idle`.** Les habitantes recevaient une longue
   activité avant leur occasion subjective d’entrer. L’arrivée est maintenant
   traitée avant l’initialisation ordinaire des activités.
3. **Ticks bruyants sans progrès.** Chaque pulsation matérialisait les mêmes
   besoins alors qu’aucune échéance n’était due. La simulation avance désormais
   seulement aux jalons utiles.
4. **Monde cohérent mais inerte.** Les profils existaient, mais le contrat ne
   permettait pas au LLM de choisir une activité. Le cycle `idle → réflexion →
   option validée` a été ajouté.
5. **Réponse Gemma invalide sans reprise.** Une sortie invalide pouvait laisser
   une habitante inactive trop longtemps. Retry explicite après cinq minutes,
   dans une fenêtre `idle` de dix minutes.
6. **Chronologie brisée par latence LLM.** Une action était parfois datée après
   une échéance qui devait pourtant apparaître ensuite. L’action est désormais
   ancrée à l’instant observé et refusée si le contexte a vieilli.
7. **Retry lui-même daté après la latence.** Le gardien a découvert cette
   seconde variante nocturne. Le retry utilise maintenant l’admission
   append-only antérieure à l’inférence.
8. **Cible `run_to` légèrement passée.** Une cible murale capturée pouvait être
   antérieure d’une milliseconde au canon courant; elle est maintenant bornée
   au maximum des deux.

Les bases fautives ont été archivées plutôt que réécrites.

### Photographie comportementale actuelle

- 8 scènes, toutes fermées par budget de quatre tours;
- aucune scène vide ou interrompue dans le monde courant;
- 32 paroles, 30 formulations normalisées exactes;
- pourtant, répétition sémantique évidente : salutations, « ça va? », « quoi de
  beau aujourd’hui? », retour « et toi? »;
- Chuu : 8 `idle`, 8 `socialize`;
- Erika : 8 `idle`, 8 `gaming`;
- Luna : 9 `idle`, 7 `socialize`;
- Sophie : 8 `idle`, 7 `socialize`, 1 `gaming`;
- Patoune : un `idle` long;
- 293 des 444 événements sont `needs_materialized`. Ce n’est plus une écriture
  toutes les deux secondes : cinq besoins sont matérialisés aux frontières
  d’activité. Le volume reste cependant dominant dans le journal brut.
- 32 `idle` abandonnés correspondent principalement au remplacement atomique
  de l’attente par une activité choisie, pas à 32 échecs psychologiques.
- orchestrateur : 67 événements routés, 61 différés par budget et 1648 jugés
  non perceptibles. Ces 1648 ne déclenchent pas Gemma mais révèlent un balayage
  technique trop large.
- depuis `0.1.0a10`, huit décisions autonomes journalisées ont toutes été
  acceptées, sans erreur fournisseur ou validation.

### Ce qui n’est pas encore mesurable honnêtement

Persistance d’intention, réparation sociale, évolution relationnelle, oubli,
asymétrie de croyance, régulation émotionnelle et conséquences de violation de
limite : aucune de ces dynamiques n’est encore active. L’absence d’anomalie sur
ces points n’est donc pas une preuve.

---

## 4. Placeholders à ne pas canoniser comme décisions finales

- `idle` comme principal indice d’occasion cognitive;
- décision dominante hiérarchique;
- activités de 30 minutes et coûts identiques à l’attente;
- interdiction globale mouvement + activité;
- co-présence de pièce comme accessibilité sociale suffisante;
- scène dyadique de quatre tours;
- co-attente comme déclencheur social;
- petite taxonomie des actes de parole;
- scores relationnels globaux comme résumé complet;
- attachement général plutôt que relationnel/contextuel;
- rappel des traces par récence;
- quatre besoins et un sommeil monodimensionnel;
- comportements déterministes minimaux de Patoune;
- seuils actuels de télémétrie;
- exactitude textuelle comme approximation de diversité conversationnelle;
- LM Studio comme transport local privilégié. Le contrat attend un fournisseur,
  pas LM Studio ontologiquement; un autre adaptateur compatible reste possible.

Les invariants à préserver sont les frontières — provenance, autorité,
validation, séparation canon/subjectif — pas ces calibrations alpha.

---

## 5. Interfaces fonctionnelles souhaitables pour le prochain bloc R&D

### Entrée minimale facile à fournir

Pour un personnage qui reçoit un acte ou événement social :

- identifiant stable du monde, de la scène, de l’acte et des participantes;
- instant et lieu canoniques;
- contenu exprimé et type d’acte, explicitement étiquetés comme expression;
- accessibilité perceptive prouvée et trace subjective source;
- cible explicite ou ambiguë;
- état privé courant déjà disponible : valeurs, préférences, limites, buts,
  intentions, affect, croyances, relation directionnelle;
- contexte récent borné de la scène;
- mémoire récupérée par un futur mécanisme, jamais tout l’historique;
- attentes pertinentes si le modèle R&D définit comment les représenter;
- source et fiabilité perçue lorsqu’une affirmation est rapportée.

### Sortie fonctionnelle souhaitable

Une **interprétation sociale située, privée, structurée et révisable**, qui
sépare au minimum :

- contenu compris et degré d’ambiguïté;
- cible perçue;
- intention attribuée avec incertitude, jamais fait canonique;
- attente confirmée, violée ou non applicable;
- pertinence pour but, valeur, limite ou relation;
- domaine concerné : compétence, discrétion, sécurité, intimité, etc.;
- appraisal qualitatif et importance;
- conséquences candidates séparées : affect, croyance/attente, saillance
  mémorielle, intention/but, relation;
- justification/provenance vers les entrées;
- degré de confiance et conditions possibles de révision.

Le moteur peut facilement valider schéma, références, propriétaire, bornes,
fraîcheur, idempotence et provenance. Il peut également appliquer une dynamique
numérique une fois ses règles adoptées.

### Points difficiles qui exigent une décision R&D claire

- différence entre interprétation initiale, appraisal, émotion et mise à jour
  relationnelle;
- traitement de plusieurs interprétations concurrentes;
- confiance globale versus confiance par domaine;
- quand une conséquence relationnelle est justifiée, et quand conserver
  seulement un épisode sans delta;
- condensation et récupération avant accumulation longue;
- interaction entre mémoire d’épisodes et résumé relationnel;
- réévaluation après excuse, nouvelle preuve ou comportement réparateur;
- séparation entre saillance, accessibilité future et importance objective;
- mécanisme empêchant le LLM de transformer une attribution en certitude;
- prédictions statistiques qui valident le modèle sans scénariser chaque
  personnage.

### Frontière recommandée

```text
moteur : faits accessibles + état privé autorisé + options/références valides
→ composant interprétatif : signification située proposée
→ service contrôlé : provenance, cohérence, incertitude, bornes
→ effets privés séparés et éventuellement différés
→ aucune mutation relationnelle automatique depuis le type de parole seul
```

---

## 6. Observations à transformer en questions scientifiques

1. **Répétition sémantique sans répétition littérale.** Quelles dimensions
   fonctionnelles manquantes — enjeu, mémoire, but partagé, common ground,
   curiosité, coût social — expliquent le small talk circulaire?
2. **Sociabilité concentrée.** Chuu, Luna et Sophie choisissent souvent
   `socialize`. Est-ce une conséquence des options, du prompt, de l’absence de
   buts persistants ou d’une représentation trop pauvre de la récompense
   sociale?
3. **Erika gaming, Sophie parfois gaming.** Quelles signatures stables devrait
   produire personnalité + préférences sans transformer un personnage en
   stéréotype monotone?
4. **Tout se déroule au salon.** Comment représenter choix de lieu, privacité,
   distance sociale et appropriation de l’espace sans géométrie 3D?
5. **Fin mécanique après quatre tours.** Quels signaux fonctionnels déterminent
   qu’une interaction continue, bifurque, devient collective ou se termine?
6. **Anticipation absente.** Quel modèle minimal permet d’agir avant les seuils
   physiologiques sans créer une planification omnisciente?
7. **Événements majoritairement non perçus.** Comment sélectionner en amont les
   destinataires perceptifs sans perdre un événement rare mais important?
8. **Patoune immobile.** Quel sous-modèle éthologique minimal produit
   exploration, repos, alimentation, jeu, évitement et affiliation sans lui
   attribuer une cognition humaine?
9. **Mesure de diversité.** Quelles métriques distinguent variation lexicale,
   diversité pragmatique, diversité de buts et véritable évolution sociale?
10. **Abandon de l’attente.** Le remplacement technique de `idle` ne doit pas
    être confondu avec interruption d’une intention. Quelle ontologie minimale
    sépare attente, activité, intention persistante et engagement?

---

## Question cruciale : une hypothèse de conception a-t-elle été fragilisée?

**Oui, plusieurs — mais aucune fondation centrale.**

### Hypothèses effectivement contredites

1. **« Une boucle correcte qui tourne paraîtra vivante. »** Faux. Elle peut
   préserver parfaitement le canon tout en restant composée de longues attentes
   sans occasions décisionnelles.
2. **« Un tick fréquent est une façon innocente de maintenir le monde. »** Faux.
   Il peut gonfler l’histoire sans produire d’information ou d’action nouvelle.
3. **« L’heure après l’appel LLM peut dater la décision. »** Faux. La latence
   machine peut réordonner les échéances canoniques. L’instant observé doit
   ancrer la proposition.
4. **« Une métrique de formulations exactes détectera la répétition utilement. »**
   Faux ou très insuffisant : 30/32 formulations distinctes masquent des scènes
   pragmatiquement quasi identiques.
5. **« Co-présence + quatre tours suffit comme premier proxy observable de
   socialité. »** Suffisant pour tester le transport et les frontières, mais
   insuffisant comme modèle comportemental : il produit surtout une cérémonie
   de salutation sans enjeu durable.

### Hypothèses fragilisées mais non encore réfutées

- L’événementiel ciblé reste préférable au polling cognitif, mais `idle` seul
  est probablement un indice trop pauvre.
- Le fournisseur local Gemma respecte assez bien les contrats, mais les sorties
  acceptées ne prouvent pas une différenciation psychologique suffisante.
- Les dimensions relationnelles peuvent rester d’utiles résumés, mais le rodage
  ne les a pas testées puisqu’elles demeurent vides.
- Le casting extrême exerce bien l’architecture, mais il ne suffit pas encore à
  vérifier des trajectoires individuelles : seule Erika montre actuellement une
  signature comportementale très visible par le gaming.

### Hypothèses renforcées

- La séparation canonique/subjectif a empêché les dialogues pauvres de polluer
  les faits ou les relations.
- Le LLM proposeur + validation moteur a permis de refuser ou adapter des formes
  Gemma imparfaites sans assouplir le contrat.
- Append-only + audits + gardien ont transformé deux anomalies temporelles
  réelles en preuves reproductibles au lieu de les masquer.
- Les échéances événementielles ont supprimé le bruit de polling sans empêcher
  le monde de progresser.

## Conclusion d’ingénierie pour la R&D

Le prochain dossier ne devrait pas chercher davantage de texte. Il devrait
définir le plus petit enchaînement qui donne **une signification subjective,
incertaine, mémorisable et révisable** à un événement social. Le moteur peut
déjà fournir les faits, la provenance, les frontières privées et la validation.
Ce qui manque est le modèle fonctionnel reliant interprétation, appraisal,
mémoire et éventuelle conséquence — sans rendre cette conséquence mécanique.
