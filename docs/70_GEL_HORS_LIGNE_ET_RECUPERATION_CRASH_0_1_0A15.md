# Gel hors ligne et récupération de crash — 0.1.0a15

## Problème observé

Le monde restait administrativement `active` lorsque la console était fermée
brutalement. Comme l'heure courante était dérivée de l'ancre SQLite et de
l'heure murale, toute la période sans moteur était ajoutée au temps vécu au
prochain lancement. Aucun runtime n'avait pourtant arbitré les conséquences.

## Contrat retenu pour l'alpha

- `worlds.status` conserve son sens administratif : `active` ou `paused`.
- `canonical_clock.runtime_state` dit uniquement si un runtime fait avancer
  l'horloge : `running` ou `stopped`.
- Un arrêt propre matérialise l'heure courante, pose `runtime_state=stopped` et
  ferme la session dans la même transaction.
- Un lancement ne rattrape jamais la période hors ligne. Il réancre l'heure
  réelle sur l'instant simulé durable avant de poser `runtime_state=running`.
- Une session encore ouverte signale un arrêt brutal. Sa récupération choisit
  le maximum entre l'ancre canonique, le dernier événement canonique et le
  dernier battement persistant : l'horloge ne peut donc jamais reculer derrière
  un fait déjà commis.

## Frontière d'autorité

`runtime_session` est un registre opérationnel compact. Son battement est mis à
jour sur place et ne constitue pas un fait du monde. Les seuls faits techniques
durables à auditer — démarrage, arrêt propre, arrêt protecteur et récupération
de crash — sont copiés dans `runtime_session_event`, append-only.

La future politique de simulation condensée d'une absence volontaire reste une
fonction distincte. Elle ne doit jamais être confondue avec le rattrapage
accidentel d'une panne ou d'une fermeture de processus.
