# R&D — Conversation State : structure interactionnelle, engagement, repair et clôture

**Version R&D :** 0.1  
**Date :** 9 août 2026  
**État logiciel de référence :** commit `2f28a44`, version `0.1.0a15`, schéma 39. La scène sociale alpha est encore principalement dyadique, bornée à quatre tours et déclenchée par des proxies simples de rencontre/co-attente.  
**Statut :** dossier scientifique et fonctionnel préparatoire. Il ne constitue pas une autorisation d'implantation immédiate et ne prescrit aucune classe/table. Codex reste autorité sur l'architecture réelle.

---

## 1. Pourquoi ce dossier existe

Le rodage a montré un paradoxe utile : les scènes sociales alpha sont techniquement valides et les formulations exactes sont souvent différentes, mais leur dynamique reste pauvre — salutations, « ça va? », « quoi de beau? », retour « et toi? » — et les scènes se terminent surtout parce qu'un budget de quatre tours est atteint.

Le problème n'est donc pas seulement la qualité de génération du texte. Une conversation vivante possède une **structure interactionnelle** : qui participe, à qui une contribution est adressée, qui possède le floor, quelle séquence est encore ouverte, si une compréhension est en réparation, si le groupe continue le même échange, bifurque, se scinde ou se dirige vers une clôture.

RIC a besoin d'un concept fonctionnel de **Conversation State** qui structure ces possibilités sans prétendre connaître les pensées privées des participantes.

Principe :

```text
scène / co-présence
!= conversation engagée
!= floor courant
!= adressage
!= compréhension
!= accord
!= relation
```

Le Conversation State appartient conceptuellement surtout à l'Interaction Engine : il organise l'accessibilité et la coordination interactionnelle. Les compréhensions, croyances, émotions et intentions restent privées au Cognitive Engine.

---

## 2. État actuel du projet à ne pas fossiliser

Les simplifications alpha utiles au démarrage ne doivent pas devenir le modèle final :

- scène essentiellement dyadique;
- maximum quatre occasions de parole;
- alternance technique des tours;
- simple co-attente comme occasion sociale possible;
- petite taxonomie fermée d'actes;
- niveau pièce comme principale topologie sociale;
- absence d'état explicite de repair, engagement, floor ou trajectoire de clôture;
- exactitude textuelle utilisée historiquement comme approximation insuffisante de diversité.

Le Conversation State ne doit pas être conçu comme un correctif cosmétique au « small talk ». Son rôle est plus fondamental : fournir au moteur et aux agentes une structure interactionnelle assez riche pour que continuer, répondre, clarifier, laisser tomber, changer de sujet ou fermer soient des possibilités distinctes.

---

## 3. Résultats empiriques et théoriques pertinents

### 3.1 [A/B — observation conversationnelle] Le turn-taking est localement organisé, pas une alternance fixe

Sacks, Schegloff & Jefferson (1974) proposent un modèle de turn-taking fondé sur des régularités observables de conversation : gestion locale, contrôle interactionnel, sensibilité au destinataire et mécanismes de sélection du prochain locuteur. Leur modèle vise à expliquer comment la conversation peut présenter peu de silences et de chevauchements sans horloge centrale rigide.

**Source :** Sacks, H., Schegloff, E. A. & Jefferson, G. (1974), *A simplest systematics for the organization of turn-taking for conversation*, Language 50(4), 696–735. DOI `10.2307/412243`.

**Portée :** travail fondateur de Conversation Analysis, descriptif et théorique; il ne doit pas être transcrit littéralement en automate universel. Il soutient néanmoins fortement qu'un compteur alterné fixe est une simplification, pas une théorie suffisante.

### 3.2 [A — comparatif] La coordination rapide des tours est largement partagée mais varie culturellement

Stivers et al. (2009) comparent des conversations dans dix langues et trouvent un pattern général de réponses rapides avec peu de chevauchement, accompagné de variation culturelle systématique dans le timing.

**Source :** Stivers, T. et al. (2009), *Universals and cultural variation in turn-taking in conversation*, Proceedings of the National Academy of Sciences 106(26), 10587–10592. DOI `10.1073/pnas.0903616106`.

**Portée :** soutient un mécanisme souple de coordination des occasions de parole. Les délais humains mesurés ne doivent pas être copiés comme timers de RIC, dont l'interface textuelle et le temps simulé sont différents.

### 3.3 [A/B — empirique] Le grounding se construit et peut être réparé

Clark & Wilkes-Gibbs (1986) montrent, dans une tâche collaborative de référence, que locuteur et destinataire peuvent réparer, étendre ou remplacer une expression jusqu'à une forme mutuellement acceptée.

**Source :** Clark, H. H. & Wilkes-Gibbs, D. (1986), *Referring as a collaborative process*, Cognition 22(1), 1–39. DOI `10.1016/0010-0277(86)90010-7`.

**Portée :** une conversation ne devrait pas traiter chaque tour comme un texte indépendant. Mais une « acceptation mutuelle » observée dans une tâche ne devient pas dans RIC un fait canonique disant que les deux personnages ont réellement compris la même chose.

### 3.4 [A/B — observation conversationnelle] Repair est une organisation récurrente de la conversation

Schegloff, Jefferson & Sacks (1977) décrivent une organisation de repair qui traite les problèmes de parler, entendre et comprendre, avec une forte préférence empirique pour certaines formes d'auto-réparation.

**Source :** Schegloff, E. A., Jefferson, G. & Sacks, H. (1977), *The preference for self-correction in the organization of repair in conversation*, Language 53(2), 361–382. DOI `10.2307/413107`.

**Portée :** justifie de représenter qu'une séquence est en réparation plutôt que de lancer immédiatement un nouveau sujet. Elle ne justifie pas de scripter toutes les erreurs selon une taxonomie exhaustive de Conversation Analysis.

### 3.5 [B — analyse conversationnelle] Une clôture est une trajectoire interactionnelle, pas seulement l'arrêt d'un compteur

Schegloff & Sacks (1973) analysent les procédés par lesquels les participants amènent une conversation vers une clôture coordonnée. Fermer une conversation est donc lui-même un accomplissement séquentiel possible.

**Source :** Schegloff, E. A. & Sacks, H. (1973), *Opening up Closings*, Semiotica 8(4), 289–327. DOI `10.1515/semi.1973.8.4.289`.

**Portée :** soutient l'abandon du « quatre tours = fin normale » comme modèle final. RIC conservera néanmoins un hard cap de sécurité d'ingénierie tant que nécessaire.

### 3.6 [A/B — empirique] Adressage et participation ne sont pas équivalents

Schober & Clark (1989) montrent que destinataires et overhearers exposés aux mêmes mots n'ont pas les mêmes conditions de compréhension. Clark & Carlson (1982) distinguent également, dans les échanges multiparty, les addressees et les autres participants ratifiés.

**Sources :** Schober, M. F. & Clark, H. H. (1989), *Understanding by addressees and overhearers*, Cognitive Psychology 21(2), 211–232. DOI `10.1016/0010-0285(89)90008-X`; Clark, H. H. & Carlson, T. B. (1982), *Hearers and Speech Acts*, Language 58(2), 332–373. DOI `10.2307/414102`.

**Portée :** justifie qu'une scène multiparty conserve qui est adressé et qui participe, sans supposer que chaque participante reçoit le même engagement ou la même compréhension.

### 3.7 [B/C — étude appliquée] Une conversation multiparty peut contenir plusieurs floors simultanés

Aoki et al. (2006) analysent des conversations sociables en petit groupe et décrivent comment plusieurs floors conversationnels peuvent émerger et comment les participants manifestent leur affiliation à l'un ou l'autre.

**Source :** Aoki, P. M., Szymanski, M. H., Plurkowski, L. D., Thornton, J. D., Woodruff, A. & Yi, W. (2006), *Where's the “Party” in “Multi-Party”? Analyzing the Structure of Small-Group Sociable Talk*, CSCW 2006, 393–402. DOI `10.1145/1180875.1180934`.

**Portée :** étude appliquée et qualitative; elle soutient l'idée que « une pièce = une conversation = un floor » est trop grossier pour le futur. Elle ne commande pas d'implanter plusieurs floors dans la première tranche.

---

## 4. Conclusions raisonnables mais incertaines

### [B/C] 4.1 La scène et la conversation doivent rester distinguables

Une scène peut fournir la participation/accessibilité de base sans garantir qu'une conversation active unique existe. Plusieurs conversations peuvent un jour coexister dans le même lieu, et une scène peut contenir des pauses ou une sortie d'engagement.

### [B/C] 4.2 Le budget de tours doit devenir un garde-fou, pas la cause normale de clôture

Un maximum technique reste utile contre les boucles LLM. Mais si la majorité des scènes finissent par `turn_budget_exhausted`, le moteur délègue la structure conversationnelle à un compteur plutôt qu'à l'interaction.

### [B/C] 4.3 Une réponse n'est pas obligatoire après chaque parole

Silence, abandon, changement d'activité, non-prise de floor ou réponse d'une autre participante sont des résultats légitimes. Forcer un utterance à chaque opportunité produit précisément le small talk de remplissage observé au rodage.

### [B/C] 4.4 Repair et clôture sont des états interactionnels utiles, mais ne prouvent aucun état mental

Le système peut savoir qu'un acte a été proposé comme clarification ou clôture sans savoir que l'autre a compris, accepté ou veut réellement partir. Ces derniers éléments sont cognitifs et privés.

### [C] 4.5 La première version n'a pas besoin de résoudre immédiatement le multiparty complet

Il est raisonnable de faire évoluer d'abord la scène dyadique avec état séquentiel, repair et clôture significative, à condition de ne pas inscrire dans le contrat des invariants impossibles à généraliser à trois participantes et plus.

---

## 5. Séparations conceptuelles à préserver

### 5.1 Conversation State ≠ mémoire de conversation

Le Conversation State porte ce qui structure l'interaction actuelle ou récemment ouverte. L'historique exact/audit et les souvenirs subjectifs restent ailleurs.

### 5.2 Conversation State ≠ common ground subjectif

Le moteur peut prouver que deux personnages ont participé à une séquence et que certaines paroles ont été acceptées. Il ne peut pas en conclure qu'elles partagent la même croyance ou compréhension.

### 5.3 Conversation State ≠ Social Interpretation

SCC-1 interprète ce qu'une parole pourrait signifier pour un personnage. Conversation State structure à quoi la parole répond, qui est engagé dans quel floor et quelles transitions interactionnelles sont possibles.

### 5.4 Conversation State ≠ relation

Une conversation longue n'implique ni affection ni intimité. Une clôture rapide n'implique ni rejet ni hostilité.

### 5.5 Conversation State ≠ permission/consentement

Une séquence sociale ne crée aucune permission d'action, de contact ou de sexualité par simple continuité conversationnelle.

---

## 6. Contrat fonctionnel cible

Les champs exacts et la persistance appartiennent à Codex. Fonctionnellement, le système futur doit pouvoir répondre à des questions comme :

- quelles personnes participent actuellement à cet échange/floor?;
- qui a produit la dernière contribution acceptée?;
- à qui était-elle explicitement adressée, si quelqu'un?;
- à quelle contribution antérieure répond-elle ou qu'est-ce qu'elle répare, si cette relation est explicitement structurée?;
- une séquence de repair est-elle ouverte?;
- une transition de clôture a-t-elle été proposée/acceptée au niveau interactionnel sans inférer les états mentaux?;
- une participante a-t-elle encore une occasion légitime de répondre, céder le floor ou ne rien faire?;
- la scène doit-elle rester ouverte, être suspendue ou être fermée pour une raison validée?;
- la fermeture est-elle normale, volontaire, due à une contrainte du monde ou due au hard cap de sécurité?;
- dans une future scène multiparty, quelles participantes sont affiliées à quel floor?

Le système ne doit pas répondre :

- « elle a compris »;
- « elle est fâchée »;
- « elle veut continuer parce qu'elle l'aime »;
- « elles sont maintenant d'accord »;

sans passer par les propriétaires subjectifs appropriés.

---

## 7. État interactionnel minimal envisagé

Sans prescrire son stockage, une première tranche pourrait avoir besoin de l'équivalent fonctionnel de :

1. **identité de l'échange**
   - scène/source stable;
   - participantes ratifiées;
   - floor courant unique en v1 si le multiparty complet est différé.

2. **ancrage séquentiel**
   - dernière contribution acceptée;
   - relation explicite à une contribution antérieure lorsque l'action proposée est une réponse/clarification/repair;
   - destinataire explicite éventuelle.

3. **état d'ouverture**
   - échange ouvert;
   - repair ouvert éventuel;
   - clôture en cours éventuelle;
   - raison de suspension/fermeture lorsqu'elle est technique ou canonique.

4. **occasion suivante**
   - personne(s) admissible(s) à prendre le floor selon les règles structurelles;
   - possibilité explicite de ne pas parler;
   - budget de sécurité séparé de la raison interactionnelle de continuer.

Cette liste est une hypothèse de modélisation. Codex peut obtenir le comportement requis avec une représentation différente.

---

## 8. Proposition LLM : ce que le modèle peut et ne peut pas décider

Le LLM peut proposer une contribution sociale structurée comprenant, lorsque le contrat futur le permet :

- parler ou ne pas parler;
- destinataire explicite parmi les participantes admissibles;
- type d'acte autorisé;
- contenu;
- relation interactionnelle proposée avec un tour précédent : réponse, clarification, repair, poursuite, transition de clôture ou autre catégorie fermée réellement adoptée.

Mais le moteur doit valider :

- participation;
- présence/accessibilité;
- cible autorisée;
- existence du tour référencé;
- état du floor;
- compatibilité avec la scène;
- budget/hard cap;
- fraîcheur de l'occasion.

Le LLM ne peut pas déclarer comme faits :

- compréhension mutuelle;
- engagement interne;
- accord réel;
- relation;
- consentement;
- émotion;
- intention réelle d'autrui.

---

## 9. Clôture : du hard cap à une raison explicite

Le hard cap reste utile comme garde de sécurité. La cible fonctionnelle est toutefois que les scènes ordinaires puissent se fermer pour des raisons distinguables :

- clôture interactionnelle proposée et complétée;
- personne ne prend le floor / non-engagement;
- contrainte canonique : déplacement, activité incompatible, perte d'accessibilité;
- intervention opérateur;
- erreur/dégradation;
- **hard cap de sécurité**, qui doit rester visible comme telle et non déguisée en clôture naturelle.

Aucun taux cible n'est fixé aujourd'hui. Le rodage futur doit simplement permettre de mesurer si le hard cap reste le mécanisme dominant.

---

## 10. Repair : priorité fonctionnelle élevée

Repair est particulièrement important pour RIC parce qu'il relie Interaction et Cognition sans les fusionner.

Exemple :

```text
Sophie : « C'est réglé. »
Erika : « Réglé comment? »
Sophie : « Je voulais dire que la fuite est contenue, pas réparée. »
```

Le Conversation State peut savoir :

- que le second tour sollicite une clarification du premier;
- que le troisième tour répond à cette séquence de repair;
- quelles contributions sont liées.

SCC-1 peut alors, séparément, permettre à Erika de réviser sa lecture subjective.

Le moteur ne conclut toujours pas que la troisième phrase est vraie.

Cette articulation est une amélioration directe par rapport à des tours indépendants : elle donne un support structurel à la révision sans transformer la conversation en omniscience.

---

## 11. Multiparty : préparer sans surconstruire

La résidence contient plusieurs habitantes; une architecture qui suppose ontologiquement « exactement deux personnes par conversation » deviendrait rapidement une dette.

Cependant, le multiparty complet introduit :

- sélection du prochain locuteur;
- destinataires multiples ou ambigus;
- participantes ratifiées vs overhearers;
- entrées/sorties de floor;
- sous-conversations simultanées;
- interruptions et chevauchements;
- affiliation à plusieurs floors.

La première tranche peut donc rester dyadique **comme limitation d'implantation**, mais les invariants fonctionnels doivent éviter :

```text
conversation_id == pair unique pour toujours
next_speaker == autre participante obligatoirement
room == unique floor
```

Le multiparty doit être une extension naturelle, pas une réécriture conceptuelle.

---

## 12. Scénarios d'acceptation

### D1 — conversation courte mais complète

Deux personnages échangent une information, obtiennent la réponse nécessaire et ferment après deux ou trois contributions.

**Attendu :** pas de tours de remplissage jusqu'au cap.

### D2 — conversation engagée > quatre tours

Une séquence cohérente de question, réponse, précision et prolongement reste active.

**Attendu :** un ancien cap de quatre tours ne doit pas être présenté comme une raison naturelle de fermeture. Un hard cap supérieur peut toujours arrêter le bench pour sécurité.

### D3 — repair

Une participante demande une clarification et l'autre répond.

**Attendu :** les contributions sont structurellement reliées; SCC-1 peut ensuite utiliser la nouvelle preuve pour révision sans vérité automatique.

### D4 — silence légitime

Une participante reçoit une occasion mais choisit/ne produit aucune parole valide.

**Attendu :** pas de filler forcé; le floor peut rester libre, être repris ou mener à clôture selon le contrat.

### D5 — adressage

Dans une scène future à trois personnes, Sophie adresse Erika pendant que Luna participe.

**Attendu :** Erika et Luna ne sont pas confondues; Luna peut néanmoins rester ratifiée dans le floor.

### D6 — changement de sujet

Une séquence est close ou abandonnée puis une nouvelle séquence commence sans effacer l'historique.

**Attendu :** le système ne traite pas tout le dialogue comme une seule chaîne sémantique infinie.

### D7 — interruption canonique

Une participante doit partir parce qu'une contrainte du monde rend la scène invalide.

**Attendu :** fermeture/suspension pour raison canonique, distincte d'une clôture volontaire.

### D8 — hard cap

Un provider boucle et produit toujours une continuation valide.

**Attendu :** le hard cap arrête la scène, journalise clairement `safety_cap` ou équivalent et ne prétend pas que les personnages ont décidé de finir.

### D9 — parole ≠ accord

A dit « D'accord » ou B ne répond pas.

**Attendu :** Conversation State peut enregistrer la séquence produite, mais aucune croyance/accord subjectif n'est créé sans le propriétaire cognitif.

### D10 — restart

Le runtime redémarre avec une scène persistée ou un historique récemment fermé.

**Attendu :** aucune reprise artificielle d'une conversation terminée et aucune perte de l'historique nécessaire aux audits/révisions.

---

## 13. Falsifications

Le modèle doit être considéré insuffisant si :

- les conversations ordinaires se ferment presque toujours uniquement par hard cap;
- chaque opportunité produit obligatoirement une parole;
- le prochain locuteur est une alternance A/B rigide sans possibilité de silence, sélection ou multiparty futur;
- chaque nouveau tour est traité comme indépendant de la séquence précédente;
- repair devient un simple nouveau sujet;
- une demande de clarification est convertie en preuve que le premier tour était faux;
- une clôture explicite est ignorée jusqu'au compteur maximum;
- une conversation longue est automatiquement interprétée comme relation positive;
- « destinataire » et « participante » sont confondus;
- la pièce devient ontologiquement un floor unique;
- le LLM peut déclarer `understood=true`, `agreement=true` ou `consent=true` comme état interactionnel canonique;
- les motifs privés ou émotions d'un tiers apparaissent dans l'état de conversation sans source subjective.

---

## 14. Métriques de rodage futures

Les métriques doivent décrire la dynamique, pas créer un score universel de « qualité conversationnelle ».

À suivre :

- distribution des longueurs de scènes;
- raisons de fermeture;
- fraction fermée par hard cap;
- fréquence de `no_speech`/yield légitime;
- nombre de repairs ouverts et résolus/abandonnés;
- nombre de contributions avec lien séquentiel explicite;
- changements de destinataire;
- répétition sémantique par familles de séquences, pas seulement doublons exacts;
- fréquence des boucles question-réponse miroir;
- temps canonique engagé dans les scènes;
- interruptions dues au monde;
- en multiparty futur : taille des floors, entrées/sorties, bifurcations.

Un faible nombre de paroles n'est pas automatiquement mauvais; un taux élevé de silence n'est pas automatiquement réaliste. Les distributions doivent être interprétées avec les scénarios et le comportement observé.

---

## 15. Questions laissées à Codex

Avant implantation, Codex doit décider :

- si le propriétaire naturel est `SocialSceneService`, un objet d'état interactionnel distinct, ou une autre composition existante;
- quelle partie doit être persistante versus dérivable du journal append-only;
- comment référencer les tours/actes de manière stable;
- comment représenter un floor et une relation de repair sans dépendance circulaire avec SCC-1;
- comment le runtime arbitre conversation, activité et déplacement;
- si le hard cap actuel peut devenir un garde configurable sans ouvrir de boucle infinie;
- comment préserver idempotence et reprise après crash;
- comment préparer multiparty sans implémenter prématurément plusieurs floors;
- quelles migrations/audits sont réellement nécessaires;
- comment intégrer la sélection de parole à `CognitionCallPolicy` sans faire d'un budget LLM une loi interactionnelle.

Escalader si la solution exige :

- stocker une compréhension privée dans l'état interactionnel;
- créer un second propriétaire de croyance/relation/permission;
- laisser le LLM écrire directement l'état de conversation;
- transformer les règles de Conversation Analysis en scripts déterministes de personnage;
- migration destructive;
- réécriture globale du social avant d'avoir falsifié une tranche plus petite.

---

## 16. Séquençage recommandé

Ce dossier n'est pas sur le chemin immédiat avant la fin de SCC-1B2 et de SCC-1C. Il prépare la suite afin d'éviter de figer le modèle alpha de scène.

Ordre R&D proposé :

```text
provider SCC-1B qualifié
→ SCC-1C admission cognitive
→ premier rodage social interprété court
→ Conversation State v1 dyadique : séquence + repair + clôture + no-speech
→ rodage/falsification
→ seulement ensuite multiparty/floors avancés
```

Cette séquence est un choix d'ingénierie visant à isoler les causes. Une urgence produit ou un audit Codex peut justifier un ordre différent.

---

## 17. Références

- Sacks, H., Schegloff, E. A. & Jefferson, G. (1974). *A simplest systematics for the organization of turn-taking for conversation*. Language 50(4), 696–735. DOI `10.2307/412243`.
- Stivers, T. et al. (2009). *Universals and cultural variation in turn-taking in conversation*. Proceedings of the National Academy of Sciences 106(26), 10587–10592. DOI `10.1073/pnas.0903616106`.
- Clark, H. H. & Wilkes-Gibbs, D. (1986). *Referring as a collaborative process*. Cognition 22(1), 1–39. DOI `10.1016/0010-0277(86)90010-7`.
- Schegloff, E. A., Jefferson, G. & Sacks, H. (1977). *The preference for self-correction in the organization of repair in conversation*. Language 53(2), 361–382. DOI `10.2307/413107`.
- Schegloff, E. A. & Sacks, H. (1973). *Opening up Closings*. Semiotica 8(4), 289–327. DOI `10.1515/semi.1973.8.4.289`.
- Schober, M. F. & Clark, H. H. (1989). *Understanding by addressees and overhearers*. Cognitive Psychology 21(2), 211–232. DOI `10.1016/0010-0285(89)90008-X`.
- Clark, H. H. & Carlson, T. B. (1982). *Hearers and Speech Acts*. Language 58(2), 332–373. DOI `10.2307/414102`.
- Aoki, P. M., Szymanski, M. H., Plurkowski, L. D., Thornton, J. D., Woodruff, A. & Yi, W. (2006). *Where's the “Party” in “Multi-Party”? Analyzing the Structure of Small-Group Sociable Talk*. CSCW 2006, 393–402. DOI `10.1145/1180875.1180934`.

---

## 18. Verdict R&D

Le rodage n'indique pas seulement « Gemma fait du small talk ». Il montre que la scène alpha ne fournit presque aucune structure qui permette à un modèle de savoir **ce qui est encore en train d'être accompli ensemble**.

Le Conversation State doit donc devenir une couche interactionnelle explicite et minimale : assez riche pour soutenir réponse, repair, silence, transition et clôture; assez pauvre pour ne jamais devenir le propriétaire des croyances, émotions, relations ou intentions.

Le but n'est pas d'écrire le script d'une bonne conversation. Le but est de donner aux agentes les conditions dans lesquelles une conversation cohérente peut émerger sans être forcée par un compteur de tours.