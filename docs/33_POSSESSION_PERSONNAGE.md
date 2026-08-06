# Possession physique par personnage

**Statut :** lot initial implémenté (migration `0023`).

## But et frontière

Un personnage peut maintenant transporter un objet portable. Le moteur affirme
un fait simple et vérifiable : **tel personnage porte tel objet, et l'objet est
au même lieu effectif que lui**. Lors d'un déplacement validé du personnage,
l'objet transporté et l'éventuel contenu de son sac suivent dans la même
transaction. Aucun faux déplacement autonome n'est ajouté au journal.

Cette couche ne confond pas encore :

- possession (`dans son inventaire`, `dans son sac`, `sur lui`) ;
- équipement (`porte cette veste`, `tient cette tasse`) ;
- permission ou intention sociale (`peut-elle prendre l'objet de quelqu'un ?`).

L'équipement et les actions sociales auront leurs propres contrats. Cette
séparation permettra de gérer les vêtements sans faire passer chaque objet
possédé pour une tenue portée.

## Contrat livré

- `PossessionService.pick_up` exige un personnage et un objet portable
  top-level situés au même lieu. Il crée `object_picked_up`.
- `PossessionService.put_down` ne permet à un personnage de poser que son
  propre objet, à son lieu courant. Il crée `object_put_down`.
- Un objet ne peut avoir qu'un porteur direct. Un sac porté peut contenir des
  objets; ceux-ci indiquent le même porteur de manière indirecte.
- Un objet porté ne peut ni être téléporté par `move_object`, ni être rangé
  directement dans un autre conteneur. Il faut d'abord le poser.
- Les tables et déclencheurs SQLite refusent les liens inter-mondes, les objets
  fixes, les objets déjà contenus et une prise initiale hors du lieu du porteur.
- Le digest reproductible inclut le porteur de chaque objet; une divergence de
  possession devient donc visible dans le banc d'essai et les tests.

Les quatre résidentes sapientes du monde d'intégration reçoivent chacune un
téléphone portable canonique à leur arrivée. Patoune n'en reçoit pas : c'est
une chatte non sapiente, non une exception technique du système.

## Suite prudente

1. Ajouter une couche d'équipement explicite (emplacements, compatibilité,
   vêtement porté ou objet tenu) au-dessus de la possession.
2. Ajouter les états et opérations de buanderie.
3. Seulement ensuite, permettre à la cognition de demander une action
   structurée `prendre`, `poser`, `ranger` ou `s'habiller`, que le moteur
   acceptera ou refusera selon ces faits.
