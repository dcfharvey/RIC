# Hugin / Munin V0.1 — console de rodage

## Statut

V0.1 est une console locale temporaire de développement, pas la nouvelle UI de
RIC. Elle est disponible sur `/observer` et consomme le read-model V0 via une
route HTTP dédiée. Elle n’ajoute aucun propriétaire d’état et ne persiste
aucun rapport.

## État actuel Hugin

Le focus `current_state` lit les propriétaires canoniques existants: position
des `character`, activité active éventuelle et horloge canonique. Un filtre par
sujet ou lieu permet l’observation individuelle ou de groupe. La durée de
présence n’est produite que lorsqu’un `character_moved` vers le lieu courant est
prouvé et que l’horloge canonique permet le calcul; sinon elle reste inconnue.
Le read-model ne déduit pas « coincé », « planté » ou « en boucle ».

Patoune est une entrée canonique `character` portant un profil non-sapient. V0.1
peut donc exposer son état canonique courant; Munin ne lui invente pas de
cognition sentiente.

## Console et planner

La page austère `/observer` permet mode, sujets, focus, lieu et bornes, puis
affiche récit déterministe, claims, preuves et fingerprint. La route
`POST /api/worlds/{world_id}/observer` reste une lecture et ouvre une connexion
SQLite `mode=ro`.

Le planner naturel est volontairement déterministe et très petit. Il traduit
quelques formulations de rodage en `ObservationQuery`; il ne produit aucun fait
et n’accède jamais à SQL. Une formulation inconnue, un nom absent ou ambigu est
refusé. Les contrôles structurés restent la voie de secours obligatoire.

Le mot « encore » ne crée aucune preuve historique. Les données de parole
restent des paroles et une croyance Munin reste une croyance subjective.

## Niveau de preuve

- Résultat empirique: la console répond aux requêtes bornées sans mutation et
  expose les preuves du rapport.
- Conclusion raisonnable mais incertaine: cette voie est suffisante pour le
  rodage quotidien initial, mais ne constitue pas une interface finale.
- Hypothèse de modélisation: la liste de formulations du planner est un
  vocabulaire de confort, pas une compréhension générale du langage.
- Choix d’ingénierie: route locale, connexion SQLite read-only, page autonome et
  absence de LLM requis.

Pas de RAG, embeddings, détection générale d’anomalies, narration LLM libre,
accès distant ou activation de nouveau domaine SCC.
