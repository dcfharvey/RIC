# Attention déterministe minimale

**Statut :** première tranche implémentée, avant la cognition subjective.

## Rôle

`AttentionService.snapshot` transforme une vue factuelle locale et les seuls
signaux propres au personnage en une liste ordonnée et bornée d'entrées
potentielles. Ce n'est pas encore une émotion, une pensée, une connaissance,
une décision ou une mémoire. La sélection sert uniquement à borner et rendre
reproductible l'entrée d'une future couche cognitive.

## Entrées v1

Les faits perceptibles restent ceux de `PerceptionService` : localisation
propre, co-présence, objet local visible et connecteur adjacent. Les signaux
internes ne sont lus que pour l'observateur :

- besoin sous son seuil effectif de profil ;
- blessure active, avec gravité dérivée et régime de récupération courant ;
- capacité limitée ou indisponible par une ressource ;
- signal de contexte non nul d'une ressource.

Ainsi, Chuu reçoit sa propre hydratation, ses limites de forme/cognition et
son signal de clarté via le système générique de ressources. Sophie, Erika,
Luna et Patoune ne reçoivent jamais ces données internes de Chuu.

## Ordre et limites

La limite par défaut est cinq entrées (entre 1 et 20 possible explicitement).
Les priorités sont des nombres stables et techniques : gravité de blessure,
capacité indisponible/limitée, ampleur d'un besoin ou signal, puis indices
locaux. Les égalités sont départagées de façon stable.

Une priorité ne dit pas qu'un personnage *doit* ressentir, croire ou faire
quelque chose. Elle ne devient subjective qu'après les futures couches
d'interprétation et de décision.

## Garanties

- lecture pure : aucun état, journal, souvenir ou horloge n'est modifié ;
- ordre déterministe, résultats immuables ;
- pas de fuite de besoins, blessures ou ressources d'autrui ;
- aucune branche codée spécifique à Chuu.

`tests/test_attention.py` couvre le bornage, la non-fuite, le profil
d'hydratation de Chuu, la priorité d'une capacité perdue et les refus sans
écriture.
