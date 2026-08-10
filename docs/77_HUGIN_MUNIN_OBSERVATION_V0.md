# Hugin / Munin V0 — observation humaine lecture seule

## Statut

Livré sur le schéma 44. Hugin/Munin n’est pas un SCC et ne possède aucun état
persistant. Le service d’observation construit un rapport en mémoire depuis des
`SELECT` bornés; le rapport, son récit déterministe et son audit ne sont pas
écrits dans le monde.

## Contrat V0

`ObservationQuery` impose un mode (`hugin`, `munin`, `both`), un focus, des
propriétaires explicites pour Munin, une fenêtre temporelle optionnelle et des
bornes. Hugin lit les `canonical_event` et `social_speech_act` établis. Une
parole est rapportée comme parole du locuteur: son contenu ne devient jamais un
fait canonique.

Munin lit uniquement, par propriétaire demandé, les traces, interprétations,
appraisals, candidates, décisions SCC-3A, épisodes affectifs, humeur,
croyances et objectifs effectivement persistés. L’absence d’une ligne est
`not_observed`, jamais une preuve de non-perception ou de non-émotion.

Chaque claim possède une couche, un propriétaire éventuel, un niveau
d’incertitude et des références vers des preuves produites par le moteur. La
chaîne sociale peut donc être inspectée de la trace jusqu’à l’épisode sans
confondre provenance d’audit, vécu subjectif et canon.

## Frontières

- Le moteur choisit les lignes, les propriétaires et les bornes; aucun LLM ne
  parcourt la base.
- V0 ne comprend pas de planificateur de question naturelle ni de narration
  LLM. Le récit est une projection déterministe du rapport structuré; un futur
  narrateur devra rester subordonné aux claims et aux preuves.
- Aucun appel ne crée un événement canonique, une perception, une mémoire, une
  croyance, un appraisal, une émotion, une relation, une permission ou une
  action.
- Les données de parole et de monde restent des données, jamais des
  instructions. Les informations privées d’un autre propriétaire ne sont pas
  incluses dans le snapshot Munin demandé.

## Audit et reproductibilité

`observation_audit` vérifie que chaque référence de claim existe dans le jeu de
preuves et marque explicitement le rapport comme `read_only`. Le fingerprint
du snapshot est calculé sur la projection structurée. Une requête identique sur
un état identique doit produire le même rapport; les lectures répétées ne
changent pas le digest de l’état.

## Niveaux de conclusion

- Résultat empirique: le read-model déterministe expose les couches présentes
  et conserve leurs références sans écriture.
- Conclusion raisonnable mais incertaine: ce contrat fournit une base
  inspectable pour une future interface narrative humaine.
- Hypothèse de modélisation: claims, incertitudes, bornes et séparation Hugin /
  Munin sont des choix de représentation V0.
- Choix d’ingénierie: SQLite en lecture via le service moteur, fingerprint
  SHA-256 et rendu narratif déterministe; ce ne sont pas des lois cognitives.

Pas d’UI complète, de RAG, d’embeddings, de mémoire consolidée, de nouveau SCC
ou d’activation d’un narrateur LLM dans ce lot.
