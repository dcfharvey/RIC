# Plan spatial — résidence initiale

**Statut :** plan de travail du futur blueprint. Seuls les liens explicitement
confirmés sont canoniques; aucune connexion manquante ne doit être devinée au
moment de l'instanciation.

## Lieux prévus

- salon;
- cuisine;
- salle de bain;
- quatre chambres;
- couloir;
- buanderie;
- cour arrière clôturée;
- entrée extérieure.
- sous-sol;
- grenier;
- stationnement extérieur.

## Connexions confirmées

| Origine | Destination | Connecteur | État initial |
| --- | --- | --- | --- |
| cuisine | cour arrière | porte patio | `available` |
| entrée extérieure | salon | porte d'entrée | `available` |
| couloir | sous-sol | porte de sous-sol | `available` |
| entrée extérieure | stationnement extérieur | passage extérieur ouvert | `available` |

La porte patio, la porte d'entrée et les autres portes sont des connecteurs
franchissables et fermables. Leur présence dans le graphe est distincte de leur
état. Elles commencent disponibles : aucun état fermé initial n'a été demandé.

L'entrée extérieure contient la boîte aux lettres : les cinq résidentes y
apparaissent ensemble au premier instant. La cour arrière contient la clôture,
la piscine et la remise; ce n'est pas le point d'arrivée.

La porte du sous-sol est au bout du couloir. L'accès au grenier se trouve près
de cette porte, via un escalier escamotable commandé par corde. Il ne peut pas
encore être codé comme une porte `closed` : le futur preset de connecteur devra
exprimer au minimum les états physiques `retracted` et `deployed`.

## Décisions retenues pour le blueprint v1

- salon ↔ cuisine et salon ↔ couloir : arches ouvertes;
- couloir ↔ quatre chambres, salle de bain et buanderie : portes;
- cour arrière ↔ remise : porte; cour arrière ↔ piscine : échelle;
- le grenier reste hors du blueprint jusqu'au support du connecteur rétractable.
