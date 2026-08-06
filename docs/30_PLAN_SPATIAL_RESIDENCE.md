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

## Connexions confirmées

| Origine | Destination | Connecteur | État initial |
| --- | --- | --- | --- |
| cuisine | cour arrière | porte patio | `closed` |
| entrée extérieure | salon | porte d'entrée | `closed` |

La porte patio et la porte d'entrée sont des connecteurs franchissables et
fermables. Leur présence dans le graphe est distincte de leur état : fermées,
elles conservent le lien spatial mais refusent une traversée jusqu'à leur
ouverture.

L'entrée extérieure contient la boîte aux lettres : les cinq résidentes y
apparaissent ensemble au premier instant. La cour arrière contient la clôture,
la piscine et la remise; ce n'est pas le point d'arrivée.

## À préciser avant le blueprint publié

- connexions du salon, couloir, chambres, salle de bain et buanderie;
- éventuels accès propres à la piscine ou à la remise.
