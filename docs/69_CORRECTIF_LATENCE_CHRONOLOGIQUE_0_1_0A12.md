# Correctif alpha `0.1.0a12` — latence LLM et chronologie canonique

## Observation de rodage

Le gardien a arrêté le runtime après avoir observé une action subjective de
Sophie à `15:01:19` suivie dans le journal d'une conséquence déterministe de
Luna à `15:01:15`. Le correctif social précédent fonctionnait; il a seulement
exposé un autre interleaving.

## Cause

Une phase LLM peut prendre plusieurs secondes. Pendant cette attente, une fin
d'activité peut devenir exigible sans créer immédiatement un événement. La
séquence canonique reste donc inchangée, mais le contexte construit à la phase
suivante peut déjà se situer après cette échéance.

## Contrat appliqué

1. Après le cycle social et après le cycle autonome, le runtime relit l'heure
   canonique et vérifie la prochaine fin d'activité.
2. Si une échéance est exigible, aucune autre phase subjective n'est lancée;
   le tick suivant commence par le simulateur déterministe.
3. Dans la transaction d'exécution finale, toute intention dont l'instant
   effectif est égal ou postérieur à une échéance encore pendante est refusée
   avec `deterministic_boundary_pending`.
4. Le refus ne modifie ni activité, ni position, ni journal canonique.

Cette double barrière protège à la fois l'économie d'appels LLM et l'invariant
fondamental, y compris si une action contourne un jour la boucle MVP.

## Validation

- test de franchissement d'échéance entre deux phases vivantes;
- test transactionnel d'une activité proposée après une échéance pendante;
- suite complète : **721 tests réussis**.

Le monde fautif demeure une preuve d'exploitation et ne doit pas être réparé
silencieusement. Le rodage reprend dans une nouvelle base propre.
