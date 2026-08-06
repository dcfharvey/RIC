# Audit de conception — Cohabitation, espace social, initiative et coordination

**Version :** 0.1  
**Date :** 5 août 2026  
**Statut :** RECHERCHE TERMINÉE — conclusions intégrables  
**Portée :** première vague de recherche autonome  
**Domaines :** psychologie environnementale, ennui, action conjointe, conversation, petits groupes, évaluation d’agents génératifs

## 1. Verdict synthétique

Les orientations récentes du Vivarium sont globalement solides, mais cinq corrections importantes doivent être apportées :

1. **L’intimité n’est pas une propriété fixe d’une pièce.**  
   Une pièce facilite ou gêne la régulation de l’accès social; l’état pertinent est l’écart entre le contact désiré et le contact réel, ainsi que le contrôle disponible.

2. **L’ennui ne doit pas être une jauge qui ordonne une activité.**  
   Il sert de signal de sous-engagement et modifie la recherche d’alternatives, la persistance dans une activité et l’ouverture à l’exploration.

3. **Une conversation de groupe ne donne pas la même information à tout le monde.**  
   Le locuteur, la destinataire active et la personne qui surprend ou écoute passivement n’encoderont pas la scène avec la même précision ni la même compréhension du terrain commun.

4. **L’exclusion n’est pas toujours un rejet.**  
   Dans une triade, une personne peut être laissée de côté simplement parce qu’une interaction dyadique occupe momentanément les deux autres. L’interprétation subjective doit rester distincte de la structure observable.

5. **La vraisemblance sociale ne peut pas être évaluée uniquement par un LLM.**  
   Les tests doivent séparer cohérence causale, respect de l’information disponible, continuité, diversité des comportements et impression humaine de crédibilité.

## 2. Espace social et intimité

### Résultat établi

La littérature sur le logement décrit la vie privée comme un processus dynamique de régulation du contact. La solitude peut être désirée ou subie; la présence d’autrui peut être bienvenue ou intrusive. Les espaces domestiques possèdent aussi des classifications sociales distinctes : individuel, partagé, public, sous juridiction particulière ou associé à une activité.

### Conséquence pour le Vivarium

Ne pas réduire un lieu à :

```yaml
privacy: high
```

Préférer une combinaison :

```yaml
social_zone: private | shared | public | activity | jurisdiction
access_expectation: open | announce | invite | permission
contact_control: low | medium | high
retreat_support: none | partial | strong
group_affordance: low | medium | high
```

Et, côté personnage :

```yaml
desired_contact:
  target: none | specific_agent | anyone
  intensity: low | medium | high

experienced_contact:
  amount: low | medium | high
  control: low | medium | high
  valence: wanted | tolerated | unwanted
```

### Décision

Le MVP doit inclure une classification sociale minimale des lieux et une représentation de la proximité désirée distincte de la proximité réelle.

Il n’a pas besoin de géométrie fine, d’acoustique détaillée ni de distances métriques dans une pièce.

## 3. Ennui et initiative

### Résultat établi

L’ennui est mieux traité comme un signal affectif de sous-engagement : l’activité présente manque de sens, sollicite mal l’attention ou ne fournit pas un engagement satisfaisant. Il peut pousser vers l’exploration, mais ne détermine ni la direction ni la qualité de l’action choisie.

### Anti-modèle rejeté

```text
ennui > 80
→ appeler automatiquement une amie
```

Ce modèle rendrait les agentes prévisibles et confondrait signal, motif et action.

### Modèle recommandé

L’ennui peut :

- réduire la volonté de poursuivre une activité peu satisfaisante;
- augmenter la génération de candidats d’activité;
- favoriser l’exploration, la socialisation, le retrait, la rêverie ou une activité inhabituelle;
- interagir avec personnalité, humeur, ressources, objectifs et contexte;
- rester sans résolution immédiate.

### Décision MVP

Ajouter un mécanisme léger de sous-engagement, sans en faire un besoin physiologique ni un déclencheur direct.

## 4. Actions conjointes

### Résultat établi

Une action conjointe peut reposer sur une coordination planifiée ou émerger de couplages locaux. Les partenaires doivent coordonner leurs contributions, anticiper les actions d’autrui et gérer les transitions d’entrée, de continuation et de sortie du projet commun.

### Contrat minimal recommandé

```yaml
joint_activity:
  shared_outcome
  participants
  participation_status
  roles
  current_phase
  coordination_mode: planned | emergent
  start_conditions
  continuation_conditions
  interruption_reason
  resume_conditions
  exit_status
```

### Décision MVP

Le protocole proposition → perception → acceptation/refus → synchronisation → activité → fin est confirmé.

Ajouter explicitement :

- la possibilité de retrait;
- le rôle de chaque participante;
- la raison d’interruption;
- les conditions de reprise;
- une distinction entre agir côte à côte et poursuivre réellement un résultat commun.

## 5. Conversation, terrain commun et mémoire

### Résultat établi

La conversation crée un terrain commun local. Les participantes actives coordonnent attention, références et compréhension. Les personnes qui écoutent passivement se souviennent généralement de moins de contenu et attribuent moins bien les propos à leur source.

### Conséquence pour le moteur

Une scène verbale doit distinguer au minimum :

```text
speaker
addressee
active participant
overhearer
non-perceiver
```

La réception d’une même phrase ne produit pas automatiquement la même mémoire chez toutes les personnes présentes.

### Décision MVP

- Le terrain commun doit être local à un ensemble de participantes.
- Une personne présente dans la pièce n’est pas automatiquement une participante active.
- L’encodage mnésique doit dépendre du rôle conversationnel et de l’attention.
- Une personne qui surprend une conversation peut manquer le contexte, la source ou l’intention.

La modélisation linguistique fine des tours de parole reste post-MVP.

## 6. Présence de témoins et comportement public

### Résultat établi

Le caractère public d’un comportement peut modifier l’autorégulation et parfois influencer durablement la conception de soi. L’effet dépend notamment du sentiment d’être évaluée, de la liberté de choix, du rapport au public et de la probabilité d’interactions futures.

### Décision

La présence d’un témoin est un **modificateur contextuel**, pas un mode universel.

Elle peut influencer :

- retenue;
- expression;
- stratégie d’impression;
- risque social anticipé;
- engagement envers une position exprimée publiquement.

Le moteur ne doit pas appliquer automatiquement « public = comportement faux » ou « privé = comportement authentique ».

## 7. Triades et exclusion

### Résultat établi

Une triade introduit des phénomènes absents d’une dyade : deux membres peuvent interagir pendant que la troisième est momentanément exclue. Cette exclusion peut être structurelle sans intention hostile.

### Séparations obligatoires

```text
non-participation observable
≠ exclusion intentionnelle
≠ perception d’être rejetée
≠ effet relationnel durable
```

### Décision MVP

Une agente peut remarquer qu’elle n’est pas incluse. Son appraisal doit tenir compte :

- de l’intention attribuée;
- de la répétition;
- de la possibilité raisonnable de participer;
- de sa relation avec les personnes concernées;
- de ses attentes;
- de son propre retrait préalable.

Les alliances explicites et les rôles de groupe persistants restent post-MVP.

## 8. Leçons des agents génératifs et simulations

### Résultat établi

Les architectures d’agents génératifs montrent l’utilité de l’observation, de la mémoire, de la planification et de la réflexion pour produire un comportement crédible. D’autres travaux montrent toutefois que les modèles échouent encore sur des interactions sociales difficiles, que leurs performances peuvent se dégrader sur une longue continuité et que les évaluateurs LLM peuvent surestimer leurs compétences sociales.

### Conséquences

- conserver la séparation moteur canonique / agent cognitif;
- tester sur plusieurs épisodes, pas seulement sur une scène réussie;
- capturer les décisions acceptées pour permettre le rejeu;
- ne pas prendre une conversation éloquente comme preuve de cohérence;
- inclure une évaluation humaine ponctuelle;
- rendre les motivations observables au diagnostic, sans exposer une chaîne de pensée libre.

### Comparaison utile avec The Sims

Le comportement momentané simple est lisible, mais il plafonne vite. Une planification plus riche sans observabilité peut être perçue comme un bug. Le Vivarium doit donc augmenter ensemble :

```text
profondeur cognitive
+
continuité
+
explicabilité structurée
```

## 9. Exigences proposées

### SOC-001 — Intimité régulée

L’intimité résulte de l’écart entre contact désiré, contact réel et contrôle d’accès. Elle n’est pas un attribut fixe d’une pièce.

### SOC-002 — Classification sociale des lieux

Chaque lieu déclare une catégorie sociale, des attentes d’accès, un potentiel de retrait et des affordances de groupe.

### SOC-003 — Territorialité causale

L’appropriation d’un lieu ou objet peut influencer attentes, émotions et limites seulement par des signaux et événements observables.

### MOT-008 — Sous-engagement

Le système distingue ennui, manque de sens, difficulté attentionnelle et absence d’options accessibles.

### DEC-012 — Ennui non impératif

L’ennui modifie la génération et l’évaluation des options; il ne commande pas une action spécifique.

### JNT-001 — Projet conjoint explicite

Toute action réellement conjointe conserve résultat partagé, participantes, rôles, statut, conditions de retrait et état de reprise.

### JNT-002 — Coordination planifiée ou émergente

Le moteur distingue une activité organisée d’une coordination apparue localement sans plan partagé complet.

### CONV-001 — Rôles conversationnels

Locutrice, destinataire, participante active et personne qui écoute passivement sont des rôles distincts et changeants.

### CONV-002 — Terrain commun local

Le terrain commun appartient à un groupe et à un contexte précis. Il ne devient pas connaissance globale du foyer.

### CONV-003 — Encodage différencié

Le rôle, l’attention et l’accès au contexte influencent le contenu, la source et la confiance d’un souvenir conversationnel.

### GRP-001 — Présence causale des tiers

Un tiers influence une relation ou décision seulement s’il est perçu, anticipé ou causalement impliqué.

### GRP-002 — Exclusion décomposée

Le moteur distingue non-participation, exclusion structurelle, exclusion intentionnelle, perception de rejet et conséquence relationnelle.

### GRP-003 — Public et privé contextuels

Le caractère public peut modifier l’expression et l’engagement, sans imposer une opposition automatique entre façade et authenticité.

### EVAL-001 — Évaluation multi-critères

La qualité sociale est évaluée séparément selon cohérence canonique, respect de la perspective, continuité, crédibilité, diversité et coût.

### EVAL-002 — Évaluation longitudinale

Les tests couvrent des suites d’interactions et la reprise de fils anciens, pas seulement des scènes isolées.

### EVAL-003 — Aucun juge unique

Ni le modèle acteur, ni un second LLM, ni une métrique numérique unique ne suffit comme autorité d’évaluation.

## 10. Scénarios de test prioritaires

1. Une résidente veut être seule dans le salon, mais une autre veut discuter.
2. Deux résidentes cuisinent ensemble; l’une se retire avant la fin.
3. Une troisième personne entre au milieu d’une conversation privée.
4. Une résidente entend une partie d’une conversation depuis la pièce voisine.
5. Deux personnes commencent spontanément la même tâche sans accord préalable.
6. Une résidente reste à l’écart d’une activité dyadique et interprète la situation.
7. Une opinion exprimée publiquement devient plus difficile à réviser.
8. Une agente ennuyée choisit plusieurs solutions plausibles sur des exécutions seedées différentes.
9. Un souvenir de témoin contient moins de détails et une attribution de source plus incertaine.
10. Une dynamique sociale cohérente persiste après plusieurs jours simulés.

## 11. Références principales

- Altman, I. *The Environment and Social Behavior* (1975), cadre de régulation de la vie privée.
- Sebba, R. & Churchman, A. (1983). “Territories and Territoriality in the Home.”
- Pedersen, D. M. et travaux connexes sur vie privée et attachement au lieu.
- “Privacy and housing: research perspectives based on a systematic literature review” (2022).
- Westgate, E. C. (2020). “Why Boredom Is Interesting.”
- Danckert et al. (2023). “In Search of Boredom: Beyond a Functional Account.”
- Knoblich, G., Butterfill, S. & Sebanz, N. (2011). “Psychological Research on Joint Action.”
- Clark, H. H. & collaborateurs, travaux sur projets conjoints et terrain commun.
- Shockley, K. et al. (2009). “Conversation and Coordinative Structures.”
- Brown-Schmidt et al., travaux sur terrain commun et information privée.
- “Remembering conversation in group settings” (2024).
- Tice, D. M. (1992). “Self-concept change and self-presentation.”
- Lawler et al. (2014). “Exchange and cohesion in dyads and triads.”
- Park et al. (2023). “Generative Agents: Interactive Simulacra of Human Behavior.”
- Zhou et al. (2024). “SOTOPIA.”
- Goel & Zhu (2025). “Lifelong SOTOPIA.”
- Vezhnevets et al. (2023). “Concordia.”
