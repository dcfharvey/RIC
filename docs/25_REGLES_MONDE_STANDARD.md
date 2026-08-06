# Règles standard de résidence

**Statut :** socle du lot D implémenté (aucune migration nouvelle).

## Pourquoi ce service existe

Le seed de développement construisait à la fois une maison technique, des
personnages provisoires et les règles de besoins/activités. Un monde
d'intégration ne doit pas dépendre de ce paquet caché.

`WorldRuleService.install_standard_residence_rules` installe explicitement le
jeu actuellement validé : besoins standards, activités standards et lieux où
elles sont permises. Il ne crée ni résident ni histoire.

## Garanties

- exige les lieux compatibles (`salon`, `cuisine`, `salle_de_bain` et au moins
  un lieu de type `bedroom`);
- installe toutes les définitions dans une transaction et produit un unique
  événement `world_rules_installed`;
- un second appel ne fait rien et ne crée aucun événement;
- une définition existante différente est un conflit explicite, jamais une
  correction silencieuse.

Le jeu de règles reste volontairement appelé `standard_residence.v1` : ses
valeurs sont les valeurs de référence actuelles, pas une loi universelle de
tous les futurs univers.

## Ce qui attend encore ta décision

Le monde d'intégration réel ne sera pas instancié avant que les éléments
explicitement ouverts soient fixés : en particulier la répartition initiale des
résidentes. La calibration de Chuu est désormais définie séparément dans
`docs/26_CALIBRATION_CHUU.md`. Le pipeline ne transforme jamais une hypothèse
en histoire officielle.
