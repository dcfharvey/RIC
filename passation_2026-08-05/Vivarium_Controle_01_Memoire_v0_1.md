# Vivarium Social — Contrôle de cohérence 01

## Mémoire

**Version :** 0.1  
**Date :** 4 août 2026  
**Verdict :** VALIDÉ AVEC CORRECTIONS CIBLÉES

## 1. Conclusion générale

Le système de mémoire conçu précédemment est scientifiquement bien fondé et demeure compatible avec les systèmes audités depuis :

- attention et perception;
- croyances;
- émotions;
- relations;
- objectifs et intentions;
- décision;
- persistance technique.

Il ne doit pas être reconstruit. Les corrections requises portent surtout sur les frontières entre :

```text
réalité canonique
≠ perception
≠ encodage
≠ trace mnésique
≠ consolidation
≠ récupération
≠ reconstruction
≠ récit conscient
≠ croyance
```

La correction la plus importante est la suivante :

> L’« original » conservé par le moteur ne doit jamais être interprété comme une copie parfaite de l’événement réel. Il doit représenter ce que le personnage a effectivement encodé, avec ses limites et erreurs initiales. La vérité externe reste dans le journal canonique.

## 2. Chaîne complète révisée

```text
événement canonique
→ signaux sensoriels
→ perception subjective
→ occasion d’encodage
→ sélection attentionnelle
→ trace encodée
→ segmentation en épisode
→ consolidation et transformation
→ stockage à plusieurs niveaux
→ récupération guidée par des indices
→ reconstruction
→ surveillance de source
→ confiance et rapport conscient
→ mise à jour éventuelle
```

Aucune étape ne doit être sautée.

Un événement peut :

- ne pas être perçu;
- être perçu sans être encodé;
- être encodé partiellement;
- être consolidé surtout sous forme de gist;
- être récupéré sans détails;
- être reconstruit avec une source erronée;
- influencer une habitude ou une relation sans rester rappelable comme épisode.

## 3. Segmentation des épisodes

La segmentation antérieure est validée, avec une extension.

Les frontières d’événement peuvent être déclenchées par des changements externes :

```text
lieu
participants
activité
objet central
interruption
```

Mais aussi par des changements internes :

```text
objectif
intention
émotion
motivation
compréhension
prédiction violée
```

Une scène peut donc rester physiquement dans la même pièce tout en devenir deux épisodes distincts si son but, son sens ou son état affectif change fortement.

```text
conversation ordinaire
→ révélation importante
→ conflit
```

peut produire plusieurs segments liés au sein d’un épisode supérieur.

Le moteur doit autoriser une segmentation hiérarchique :

```text
micro-événement
→ échange particulier

épisode
→ conversation complète

séquence
→ conflit et réparation sur plusieurs scènes
```

Le MVP n’a pas besoin de construire automatiquement toutes les hiérarchies. Il doit toutefois éviter de supposer qu’une scène sociale correspond toujours à un seul bloc mnésique.

## 4. Encodage : ce qui entre réellement en mémoire

Une perception consciente ne devient pas automatiquement une mémoire durable.

```text
EncodingOpportunity
- agent
- percepts disponibles
- foyer attentionnel
- intention actuelle
- nouveauté
- pertinence pour les buts
- importance relationnelle
- émotion
- distinctivité
- répétition
- charge cognitive
- état physiologique
```

Le résultat peut être :

```text
aucun encodage durable
trace fragmentaire
trace riche
gist sans détails
détails isolés sans structure complète
association implicite
```

Le système doit enregistrer les raisons principales de sélection sans fabriquer un « score de mémorabilité » présenté comme une loi psychologique universelle.

## 5. L’enregistrement d’encodage n’est pas la vérité

Nous remplaçons l’expression ambiguë `original_trace` par :

```text
EncodingRecord
```

Il contient ce qui était accessible et encodé au moment de l’expérience :

```text
EncodingRecord
- agent
- épisode source
- percepts encodés
- détails encodés
- gist initial
- contexte
- état émotionnel
- objectifs actifs
- source attribuée au moment de l’encodage
- précision initiale estimée
- accès conscient
- événement de création
```

Cet objet est immuable comme **trace d’audit de l’encodage**, mais il peut déjà être incomplet ou erroné.

```text
CanonicalEvent
→ ce qui s’est réellement produit

EncodingRecord
→ ce que le personnage a encodé

CurrentMemoryRepresentation
→ ce qui lui est maintenant accessible
```

## 6. Niveaux de représentation

Le système conserve plusieurs couches distinctes.

```text
PerceptualBuffer
→ très bref, non durable

CurrentEventModel
→ représentation active de la scène en cours

EncodingRecord
→ contenu initialement encodé

EpisodicRepresentation
→ épisode consolidé avec contexte

SemanticizedKnowledge
→ information extraite sans souvenir nécessaire de l’épisode

Schema
→ structure générale issue d’expériences répétées

ProceduralMemory
→ habitude ou savoir-faire

ProspectiveMemoryTrace
→ rappel d’une intention future

RetrievedReconstruction
→ résultat d’une tentative de rappel

AutobiographicalMeaning
→ lien avec l’identité ou le récit de soi
```

`AutobiographicalMeaning` sera principalement géré avec le futur modèle de soi. La mémoire doit seulement conserver les liens nécessaires.

## 7. Gist et détails

La séparation antérieure entre gist et détails est validée.

```text
MemoryGist
- sens général
- causalité perçue
- résultat
- personnes centrales
- enjeu principal
```

```text
MemoryDetail
- contenu
- type
- précision
- accessibilité
- confiance de source
- centralité à l’encodage
- centralité actuelle
```

La centralité n’est pas une propriété éternelle.

Un détail peut avoir été périphérique pendant l’événement et devenir central plus tard lorsqu’une nouvelle question apparaît.

```text
au moment de la scène :
couleur du sac peu importante

après la disparition d’un objet :
couleur du sac devenue diagnostique
```

Le moteur doit donc distinguer :

```text
encoding_centrality
current_retrieval_relevance
```

## 8. Consolidation

La consolidation reste un processus de stabilisation, réorganisation et transformation.

Elle peut se produire :

- pendant le sommeil;
- pendant le repos;
- pendant des périodes calmes;
- lors du traitement différé;
- pendant le rattrapage hors ligne.

```text
ConsolidationCandidate
- trace
- récence
- importance
- nouveauté
- lien avec les objectifs
- émotion
- répétition
- relation importante
- contradiction
- récupération récente
- possibilité d’intégration à un schéma
```

Le résultat n’est pas obligatoirement « mémoire plus forte ».

Il peut comprendre :

```text
accessibilité renforcée
gist extrait
détails secondaires affaiblis
liens sémantiques créés
source dégradée
schéma mis à jour
habitude influencée
aucun changement notable
```

Le sommeil ne reçoit pas une règle magique du type :

```text
if emotional:
    consolidate_strongly()
```

Le moteur utilise une priorité probabiliste et configurable. Les effets exacts du sommeil sur les souvenirs émotionnels dépendent du type de contenu, de l’encodage, du test et du contexte.

## 9. Récupération comme processus séparé

Une mémoire stockée n’est pas automatiquement accessible.

```text
RetrievalAttempt
- agent
- intention de récupération
- question
- indices
- contexte
- temps disponible
- effort
- état émotionnel
- croyances actuelles
- buts actuels
- souvenirs concurrents
```

Résultats :

```text
successful_specific
successful_gist
partial
familiarity_only
source_uncertain
substitution
intrusion
failure
```

Le moteur peut récupérer :

- le bon épisode avec une mauvaise source;
- un épisode similaire à la place;
- un gist sans détails;
- un détail isolé sans le contexte;
- un sentiment de familiarité sans contenu;
- rien du tout.

## 10. Résultat reconstruit

```text
RetrievedReconstruction
- retrieval_attempt
- memories utilisées
- gist récupéré
- détails récupérés
- détails inférés
- éléments fournis par des croyances actuelles
- éléments venant de connaissances ultérieures
- source attribuée
- source réelle connue du moteur
- accessibilité
- précision estimée
- confiance
- vivacité
- perspective
- statut conscient
```

Les éléments récupérés et les éléments inférés doivent rester distinguables dans l’audit interne, même si le personnage les confond consciemment.

La reconstruction n’est pas automatiquement une falsification. Elle est le fonctionnement normal d’un système qui combine traces, indices, connaissances et contexte actuel.

## 11. Accessibilité, précision, confiance et vivacité

Ces dimensions restent séparées.

```text
accessibility
→ probabilité ou facilité d’obtenir quelque chose

precision
→ résolution et exactitude des détails disponibles

confidence
→ confiance subjective dans le rappel

vividness
→ intensité phénoménologique

source_confidence
→ confiance sur l’origine de l’information
```

Exemples valides :

```text
rappel accessible
+ peu précis
+ très confiant

rappel précis
+ difficile à récupérer
+ faible confiance

souvenir très vif
+ source erronée
```

Le moteur ne déduit jamais l’exactitude depuis la vivacité ou la confiance seules.

## 12. Surveillance de source

Le système de source monitoring est conservé et partagé avec les croyances.

```text
MemorySourceAttribution
- contenu
- source supposée
- source réelle connue du moteur
- mode d’acquisition
- confiance dans le contenu
- confiance dans la source
- indices utilisés
- révision
```

Modes :

```text
perçu directement
entendu
lu
raconté
déduit
imaginé
rêvé
rappelé d’une autre scène
appris après coup
```

La mémoire et le système de croyances ne doivent pas posséder deux vérités séparées sur la provenance. Ils partagent le même objet ou des références explicites.

## 13. Récupération et mise à jour

La formulation précédente « récupérer peut modifier la mémoire » reste valide, mais elle ne doit pas devenir automatique.

La littérature humaine sur la reconsolidation demeure débattue et comporte des conditions limites. Nous utilisons donc une politique conservatrice.

```text
récupération ordinaire
→ ne réécrit pas nécessairement la représentation

récupération + nouveauté ou contradiction importante
→ peut ouvrir une fenêtre de mise à jour

récupération répétée d’une reconstruction
→ peut renforcer l’accessibilité de cette version
```

```text
MemoryUpdateCandidate
- représentation réactivée
- erreur de prédiction
- nouvelle information
- contradiction
- pertinence
- émotion
- répétition
- confiance de source
- type de mise à jour
```

Types :

```text
append_context
revise_detail
revise_source
change_confidence
extract_gist
link_new_episode
semanticize
create_competing_version
```

Le moteur conserve :

```text
EncodingRecord immuable
MemoryRevisionHistory
CurrentAccessibleRepresentation
```

Il ne prétend pas simuler littéralement la biologie de la reconsolidation.

## 14. Oubli

L’oubli ne sera pas une seule décroissance.

```text
ForgettingProcess
- accessibility_loss
- precision_loss
- source_degradation
- interference
- competition
- retrieval_induced_reduction
- schema_assimilation
- context_mismatch
- deliberate_avoidance
```

Un souvenir peut devenir :

```text
inaccessible mais encore influent
accessible seulement avec un indice
réduit à un gist
dépourvu de source
confondu avec un épisode similaire
transformé en connaissance générale
```

La suppression physique d’une trace psychologique n’est pas le mécanisme normal.

La récupération induite peut diminuer l’accès à des souvenirs concurrents, mais les mécanismes théoriques de ce phénomène restent débattus. Nous conservons donc ce mécanisme comme effet borné et optionnel, jamais comme loi universelle.

## 15. Persistance indirecte

Le principe antérieur est confirmé :

> Un événement peut devenir presque impossible à rappeler tout en continuant d’influencer les habitudes, les préférences, les croyances, la sécurité relationnelle ou l’évitement.

Le moteur conserve des liens de provenance :

```text
memory_influence_link
- memory_or_episode
- target_system
- target_record
- influence_type
- strength
- current_accessibility_independent
```

Exemple :

```text
épisode précis inaccessible
→ confiance envers la louve légèrement plus faible

le personnage ne peut plus expliquer clairement pourquoi
```

Le système relationnel conserve l’effet. La mémoire conserve sa provenance lorsque disponible.

## 16. Mémoire prospective

Le contrôle confirme la séparation établie à l’audit 06.

```text
Module objectifs
→ ce qui doit être fait et pourquoi

Module mémoire
→ trace permettant de s’en rappeler

Attention
→ détection du signal

Décision
→ vérification de la pertinence actuelle

Action
→ exécution
```

Types :

```text
event_based
time_based
activity_based
state_based
opportunity_based
```

```text
ProspectiveMemoryTrace
- intention
- action à rappeler
- signal
- fenêtre
- importance
- stratégie de surveillance
- coût de surveillance
- dernier rappel
- échéance
- état
```

La surveillance active coûte de l’attention. Une intention importante peut être manquée. Une intention accomplie doit être désactivée afin d’éviter une exécution en double.

## 17. Mémoire et croyance

```text
souvenir
→ représentation d’une expérience passée

croyance
→ proposition actuellement tenue avec un degré de confiance
```

Un souvenir peut soutenir une croyance, mais ne devient pas automatiquement cette croyance.

```text
Souvenir :
« Je me rappelle l’avoir vue près de la porte. »

Croyance :
« Elle a probablement ouvert la porte. »
```

Le système de croyances reçoit :

```text
contenu récupéré
source attribuée
confiance
précision
incertitudes
```

Il évalue ensuite la preuve.

Une croyance révisée ne réécrit pas automatiquement le souvenir qui l’avait soutenue. Elle peut modifier la reconstruction future ou créer un lien de correction.

## 18. Mémoire et émotion

Le système doit distinguer :

```text
émotion pendant l’événement
émotion encodée comme contexte
émotion ressentie pendant le rappel
émotion actuelle utilisée pour réinterpréter
```

```text
MemoryAffectiveContext
- emotion_at_encoding
- awareness_at_encoding
- bodily_state
- attributed_cause
```

```text
RetrievalAffectiveResponse
- emotion_triggered_now
- target
- appraisal
- regulation
```

Un souvenir peut être rappelé calmement après avoir été vécu sous peur, ou être rappelé avec colère malgré une émotion initiale différente.

Le rappel peut produire un nouvel épisode émotionnel sans modifier automatiquement le contenu historique.

## 19. Mémoire et relations

Une relation ne doit pas recalculer tout son état uniquement depuis les souvenirs actuellement accessibles.

```text
interaction
→ preuve relationnelle
→ mise à jour relationnelle
→ mémoire éventuelle
```

Même si l’épisode devient inaccessible :

```text
la preuve relationnelle
et certains effets appris
peuvent persister
```

Inversement, retrouver un souvenir important peut réactiver ou réévaluer une preuve relationnelle.

Le système doit empêcher une boucle artificielle :

```text
relation modifiée
→ souvenir modifié
→ même relation modifiée une deuxième fois
```

Chaque mise à jour conserve une causalité et un identifiant de preuve.

## 20. Mémoire et modèle de soi

La littérature soutient une relation bidirectionnelle entre mémoire autobiographique et identité : les conceptions actuelles de soi influencent la récupération et l’interprétation du passé, tandis que les souvenirs autobiographiques contribuent à la continuité du soi.

Le futur système de soi recevra donc :

```text
SelfMemoryLink
- memory
- self_claim
- life_period
- identity_relevance
- current_interpretation
- prior_interpretations
```

Mais la mémoire ne déterminera pas seule l’identité.

```text
« J’ai échoué une fois »
≠
« Je suis incapable »
```

Cette seconde proposition appartient au modèle de soi ou aux croyances.

## 21. Le chat et les agents non sapients

Le chat utilise :

- traces associatives;
- souvenirs spatiaux;
- familiarité;
- reconnaissance d’individus;
- événements marquants;
- attentes de routine;
- sécurité et évitement;
- mémoire prospective simple liée à des signaux.

Il n’utilise pas automatiquement :

- récit autobiographique élaboré;
- révision narrative consciente;
- source monitoring verbal;
- identité temporelle abstraite;
- engagements prospectifs formulés symboliquement.

La même infrastructure peut être conservée avec des composants cognitifs réduits.

## 22. Stockage révisé

```text
memory_episode
memory_episode_boundary
current_event_model

memory_encoding_record
memory_encoding_context
memory_gist
memory_detail

memory_consolidation_state
memory_schema_link
memory_semanticization

memory_retrieval_attempt
memory_retrieval_result
memory_retrieval_element
memory_source_attribution

memory_update_candidate
memory_revision
memory_access_state
memory_forgetting_process

prospective_memory_trace
prospective_memory_cue

memory_influence_link
self_memory_link
```

Les contenus textuels riches peuvent utiliser des champs JSON bornés ou des tables de détails, mais aucun personnage ne doit être stocké sous forme d’un unique document opaque.

## 23. Événements

```text
event_boundary_detected
memory_encoding_started
memory_trace_encoded
memory_gist_formed
memory_detail_encoded
memory_consolidation_started
memory_consolidated
memory_semanticized
memory_schema_updated

memory_retrieval_attempted
memory_retrieval_succeeded
memory_retrieval_partial
memory_retrieval_failed
memory_source_attributed
memory_source_revised

memory_update_window_opened
memory_representation_revised
memory_accessibility_changed
memory_precision_changed
memory_became_inaccessible

prospective_memory_cue_detected
prospective_memory_retrieved
prospective_memory_missed
prospective_memory_deactivated
```

Le journal canonique ne conserve pas nécessairement chaque tentative mentale banale. Les événements sont produits lorsqu’ils influencent une décision, une scène, un apprentissage ou un diagnostic important.

## 24. Rôle du LLM

Le LLM peut :

- résumer un épisode récupéré;
- formuler une reconstruction consciente;
- proposer quels souvenirs semblent pertinents;
- produire un récit autobiographique;
- exprimer une hésitation sur la source;
- relier plusieurs souvenirs accessibles;
- proposer un gist.

Il ne peut pas :

```text
accéder au journal canonique comme mémoire du personnage
rappeler un souvenir inaccessible
inventer un détail absent
transformer une inférence en détail encodé
fixer l’exactitude
déterminer la confiance canonique
modifier directement une trace
supprimer une ancienne version
consolider un souvenir
désactiver une intention prospective
```

Le contexte fourni au LLM distingue explicitement :

```text
recalled
inferred
believed
uncertain
source_unknown
```

## 25. Tests obligatoires

```text
événement perçu mais non encodé
encodage partiel
frontière interne sans changement de lieu
gist conservé, détails perdus
détail récupéré avec mauvaise source
substitution d’un épisode similaire
souvenir vif mais erroné
récupération sans mise à jour
mise à jour après contradiction
souvenir inaccessible avec effet relationnel persistant
croyance corrigée sans suppression du souvenir
prospective cue manqué
intention déjà accomplie qui tente de se réactiver
replay technique sans appel au LLM
chat utilisant une mémoire non narrative
```

## 26. Verdict final

Le système antérieur est conservé. Les corrections ciblées sont :

```text
faire de l’EncodingRecord une trace de l’encodage subjectif
étendre les frontières aux changements internes
séparer représentation stockée et résultat de récupération
séparer accessibilité, précision, confiance et vivacité
rendre le rappel guidé par des indices et faillible
ne pas faire de chaque récupération une reconsolidation
rendre la consolidation transformative plutôt que simplement renforçante
conserver un oubli multicausal
relier sans confondre mémoire, croyance, émotion, relation et soi
intégrer proprement la mémoire prospective aux intentions
```

**Statut : MÉMOIRE — VALIDÉ AVEC CORRECTIONS CIBLÉES.**

## 27. Références principales consultées

- Nolden et al., *Prediction error and event segmentation in episodic memory*.
- Wang, Adcock et Egner, *Toward an integrative account of internal and external determinants of event segmentation*.
- Johnson, Hashtroudi et Lindsay, *Source monitoring*.
- Elsey, Van Ast et Kindt, *Human memory reconsolidation: A guiding framework and critical review of the evidence*.
- Fivush et Grysman, *Accuracy and reconstruction in autobiographical memory*.
- Born et Feld, *Sleep — A brain-state serving systems memory consolidation*.
- Klinzing et al., *Sleep’s contribution to memory formation*.
- Berens, Richards et Horner, *Dissociating memory accessibility and precision in forgetting*.
- Peper et Ball, *Strategic monitoring improves prospective memory: A meta-analysis*.
- Anderson et al., *Forgetting as a consequence of retrieval: A meta-analytic review of retrieval-induced forgetting*.
