# États affectifs privés — lot initial

**Statut :** implémenté partiellement au 6 août 2026.

## Séparations garanties

Une humeur diffuse (`mood_state`) sépare valence et activation. Un épisode
émotionnel est ciblé, temporaire et contient une famille, une évaluation
structurée, une intensité, une tendance d'action et une expression. Humeur,
épisode, expression et fait canonique restent donc quatre choses différentes.

Les familles initiales suivent le contrat existant : joie, soulagement,
tristesse, colère, peur, honte, culpabilité et affection. Plusieurs épisodes
actifs peuvent coexister; aucune règle ne déduit une émotion d'un trait de
personnalité ou d'un besoin seul.

## Causalité et intégrité

Le démarrage d'un épisode exige une trace subjective privée de la résidente.
Le moteur ne valide pas encore la sémantique de l'appraisal, mais il refuse
déjà toute cause inaccessible. Humeur et épisode possèdent un événement privé
append-only; chaque mise à jour doit pointer vers un événement plus récent.
Les suppressions et modifications directes sont refusées par SQLite.

Une résolution est elle aussi explicitement journalisée. L'épisode ne disparaît
pas : il cesse seulement d'être actif, afin de préserver son explication et
son usage mémoriel futur.

## Frontière LLM

`CognitionContext` v3 fournit uniquement à la propriétaire de l'état son humeur
et jusqu'à six épisodes actifs. Le LLM ne peut ni lire l'affect d'une autre
résidente, ni l'écrire, ni affirmer seul une résolution.

## Limites assumées

Le lot ne simule pas encore la dynamique temporelle, la transformation d'un
épisode, les stratégies de régulation, l'expression observable, ni les
appraisals calculés. Il ne prétend donc pas satisfaire EMO-001 à EMO-012 au
complet : il garantit seulement les séparations et la provenance nécessaires
pour les ajouter sans réécrire l'histoire.

## Addendum SCC-3A

SCC-3A introduit un premier chemin causal limité depuis une candidate SCC-2A
vers un épisode privé. Il ne valide pas une théorie complète de l'appraisal :
le provider peut répondre `no_change`, et les familles/intensités restent des
choix d'ingénierie bornés. L'humeur, l'expression observable et le
comportement restent inchangés.

## Preuve de sortie

- humeur privée bornée et journalisée ;
- épisode impossible sans source subjective accessible ;
- résolution et état immuables hors service contrôlé ;
- digest et audit affectifs séparés du canon ;
- contexte LLM v3 privé et borné ;
- suite complète : 629 tests réussis.
