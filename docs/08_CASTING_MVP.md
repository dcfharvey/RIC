# Casting MVP — données de conception gelées

**Statut :** gabarits v1 définis dans `src/vivarium/mvp_templates.py`; aucune
résidente définitive n'est encore instanciée.

## Sophie

- humaine sapiente adulte;
- photoreporter;
- tsundere, sarcasme sec, expression directe;
- son background détaillé reste volontairement hors du MVP.

## Erika

- humaine sapiente adulte;
- vit au jour le jour, sans inhibition marquée et sans suranalyse;
- très investie dans le gaming;
- son background détaillé reste volontairement hors du MVP.

## Luna

- louve anthropomorphe sapiente adulte;
- grande, forte et consciente de l'être;
- posture intentionnellement edgy, sportive et bagarreuse;
- apprécie secrètement les choses girly.

Ces éléments décrivent des dispositions initiales, non une obligation de jouer
toujours un rôle prévisible. Le système futur de personnalité devra les traiter
comme tendances contextualisées, jamais comme scripts.

## Chuu

- slime sapiente adulte à apparence féminine;
- son intelligence dépend de son hydratation;
- pleinement hydratée : brillante;
- lorsqu'elle est une flaque pouvant tenir dans un seau : cognition très
  simplifiée.

**Verrou technique :** le moteur possède maintenant la famille générique de
ressources et de bandes d'état. Avant l'instanciation de Chuu, il reste à fixer
ses seuils et taux d'hydratation, puis à déclarer les effets sur sa forme, ses
capacités accessibles et son profil cognitif. Aucun texte de personnage ne doit
remplacer ou ignorer ces conséquences.

## Patoune

- chatte domestique adulte, non sapiente;
- pelage noir;
- dans le noir, seuls ses yeux sont visibles.

Cette caractéristique est actuellement descriptive. Elle pourra plus tard être
reliée à la perception et à l'éclairage si le monde possède ces systèmes.

## Règles communes

- les cinq entités passent par les mêmes gabarits et le même pipeline
  d'instanciation;
- aucune règle du moteur ne teste le nom, l'espèce ou l'apparence d'un membre
  du casting;
- les éléments non encore soutenus par un mécanisme restent explicitement
  descriptifs ou futurs.
