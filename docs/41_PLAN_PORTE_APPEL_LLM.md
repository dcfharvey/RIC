# Plan — porte d'appel LLM événementielle

**Statut :** trois premiers étages implantés : politique pure, journal
technique append-only et routeur explicite de `direct_event`, sans ordonnanceur
ni appel automatique.

## Décision de portée

Un appel LLM est une ressource rare de la couche subjective; il n'est ni un tick
ni une conséquence automatique de chaque événement canonique. L'appel actuel
reste explicitement demandé par `CognitionTurnService` ou par `llm-smoke`.
Cette porte définira plus tard si un appel est **admissible**, sans prendre la
décision sociale à la place du personnage.

## Fondations déjà établies

Le dossier historique exige des appels déclenchés par une décision significative,
plutôt qu'une fréquence fixe; il cite la fin ou le blocage d'intention,
l'événement social, le conflit de motifs, le tour de scène, la réflexion
planifiée, la consolidation et l'intervention du propriétaire. Il exige aussi
debounce, limite par scène, budget quotidien, priorités et mode dégradé.
Voir `docs/history/Vivarium_Memoire_Assistante_v10.md`, §19.6–19.7 et R-04;
la norme LLM-006 dans
`docs/history/Vivarium_Exigences_Normatives_Post_Audit_v0_1.md` confirme que
besoins, routines et validations simples restent déterministes.

## Contrat initial proposé

`CognitionCallPolicy` est une lecture pure qui reçoit un personnage, un instant
canonique, un motif fermé, un historique injecté et des limites explicites. Une
trace porte explicitement sa résidente : un mélange d'historiques est refusé.
La politique retourne une décision stable : `eligible` ou `deferred`, plus un
`reason_code`. Elle n'appelle jamais Gemma elle-même.

Motifs fermés prévus :

- `initial_arrival`;
- `direct_event` déjà perceptible par le personnage;
- `action_refused` après une proposition validée mais impossible;
- `intention_blocked` ou `intention_completed` (futurs, après intentions);
- `scene_turn` (futur, après scènes);
- `planned_reflection` (futur, après planificateur);
- `owner_intervention` (futur, après contrat d'administration cognitive).

Un motif ne transmet pas de texte libre et ne déclare pas une émotion, une
relation ou une croyance. Le contexte final reste construit par les projections
déjà autorisées.

## Garde-fous non négociables

1. **Déduplication.** Le même motif et la même source ne doivent pas produire
   deux appels pendant un retry.
2. **Debounce.** Deux signaux proches ne contournent pas la stabilité d'une
   intention future; les valeurs précises seront calibrées au banc, pas fixées
   arbitrairement comme psychologie.
3. **Budget.** Une limite est comptée par personnage et par période canonique;
   l'état de budget est séparé du journal canonique et auditable.
4. **Priorité.** Une intervention explicite ou un blocage réel passe avant une
   réflexion planifiée; une routine n'ouvre pas un appel par défaut.
5. **Mode dégradé.** Modèle absent, réponse invalide, délai dépassé ou budget
   épuisé donnent un résultat explicite et sans mutation canonique. Les règles
   déterministes continuent.
6. **Aucune vérité du modèle.** Une réponse demeure une proposition soumise au
   contrat d'action; le journal technique d'appel ne devient ni mémoire ni
   fait du monde.

## Ordre d'implémentation

1. ~~service pur de politique + cas de banc, sans écriture et sans appel réseau~~;
2. ~~état minimal séparé (dernier déclencheur/budget), append-only et idempotent~~;
3. ~~routeur qui consulte la politique avant `CognitionTurnService`~~;
4. calibrage des seuils sur Gemma local avec rapports de banc;
5. seulement ensuite, intention persistante, scènes et motifs sociaux.

Les nombres de debounce et budget sont intentionnellement ouverts : ils doivent
être mesurés sur la cadence, la latence et la qualité réelles du modèle local,
puis devenir une décision versionnée. Aucune espèce, aucun nom du casting et
aucun trait de personnalité ne reçoit de traitement spécial.

Le seul motif actuellement raccordé est `direct_event`, avec une source au
format `event_<seq>` qui doit être réellement perceptible par la résidente.
Les autres motifs restent fermés mais sont refusés par le routeur tant que leur
contrat source n'existe pas; ils ne reçoivent donc aucune interprétation libre.

## Critères de sortie du lot futur

- même motif rejoué : verdict identique sans nouvel appel;
- entrée non reconnue : refus avant réseau;
- budget atteint ou modèle indisponible : résultat explicite, monde inchangé;
- priorité vérifiable entre motifs concurrents;
- essais de banc distincts du monde persistant;
- audit du journal technique sans mélange avec les événements canoniques ni les
  traces subjectives.
