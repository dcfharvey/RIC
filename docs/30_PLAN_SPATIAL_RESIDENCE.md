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
- cour clôturée.

## Connexions confirmées

| Origine | Destination | Connecteur | État initial |
| --- | --- | --- | --- |
| cuisine | cour | porte patio | `closed` |

La porte patio est un connecteur franchissable et fermable. Sa présence dans le
graphe est distincte de son état : fermée, elle conserve le lien spatial mais
refuse une traversée jusqu'à son ouverture.

## À préciser avant le blueprint publié

- connexions du salon, couloir, chambres, salle de bain et buanderie;
- position de la boîte aux lettres dans la cour par rapport à l'entrée réelle;
- éventuels accès propres à la piscine ou à la remise.
