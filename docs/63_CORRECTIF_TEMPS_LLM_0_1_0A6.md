# Correctif alpha 0.1.0a6 — temps des décisions LLM

## Défaut observé

Le rodage réel a produit une séquence canonique non monotone. Chuu a démarré
une activité à `03:12:17.630`, puis l'échéance déjà planifiée d'Erika à
`03:12:16.543` a été inscrite au numéro suivant. Les transactions, besoins et
clés étrangères étaient sains; l'audit `occurred_at_monotonic` a correctement
refusé le journal.

Cause : le contexte était construit avant l'appel Gemma, mais l'action utilisait
l'heure dérivée après plusieurs secondes d'inférence. Le tick suivant traitait
ensuite une autre borne devenue antérieure à cette action.

## Contrat corrigé

- `CognitionTurnService` transmet l'instant observé et le dernier numéro
  d'événement de son contexte à `ActionOrchestrator`;
- une traversée, l'abandon d'un idle et le démarrage de l'activité utilisent
  tous ce même instant effectif;
- l'idempotence est vérifiée avant la fraîcheur : un retry d'une action déjà
  acceptée retrouve toujours son fait;
- avant une nouvelle écriture, le moteur compare le dernier numéro d'événement
  courant à celui observé. Toute différence donne
  `stale_decision_context`, sans mutation;
- un instant antérieur au dernier fait canonique est également périmé.

Le temps de calcul du fournisseur est ainsi séparé du temps vécu. Cette règle
n'empêche pas le monde actif de progresser entre les ticks; elle empêche
seulement une réponse tardive de réordonner le passé ou d'agir depuis un monde
qui a changé pendant l'inférence.

## Régression automatisée

Le cas de test place plusieurs idles au même instant, dont une échéance à cinq
secondes. Le faux fournisseur fait avancer l'horloge de dix secondes avant de
répondre. L'action garde son instant observé, l'échéance est ensuite traitée et
`structural_event_audit(...)["occurred_at_monotonic"]` reste vrai. Un second
cas modifie canoniquement le monde pendant l'appel et vérifie le refus périmé.

Suite complète : **706 tests**.

## Base de rodage

La base ayant révélé le défaut reste une preuve utile, mais son journal
append-only ne doit pas être réécrit pour paraître sain. Elle doit être archivée
hors du chemin de lancement normal, puis remplacée par une nouvelle base alpha
créée par `mvp-init` après validation du correctif.
