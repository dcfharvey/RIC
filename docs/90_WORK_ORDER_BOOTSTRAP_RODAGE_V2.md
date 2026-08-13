# Work order 90 — bootstrap Rodage V2

**Statut : OUVERT — correctifs de représentation requis avant le premier événement persistant.**

Base : `9dd02538c54e06a771423e1c00a5272260b2d0d5` (`0.2.0a1`, schéma 55).

## Intention

Lever uniquement les limites découvertes lors de la préparation du vrai T0. Le Rodage V2 officiel reste non démarré jusqu'à qualification complète.

## Décisions produit

### Extérieur hors terrain

L'extérieur au-delà de la propriété est un espace canonique accessible depuis l'extérieur du terrain. Des lieux hors foyer pourront y être raccordés progressivement (travail, commerces, parcs, autres domiciles, etc.).

Le mécanisme doit être générique : un personnage peut réellement se trouver hors foyer sans faux lieu intérieur, mais l'existence de cette topologie ne rend pas tous les lieux extérieurs automatiquement connus ou perceptibles par les agents.

Le T0 doit permettre de représenter Sophie à son lieu de travail et son retour prévu à 16 h. Aucun cas spécial Sophie dans le moteur.

### Sommeil

`sleep` est spatialement autorisé dans tout lieu canonique accessible. Une chambre ou un lit ne sont pas des préconditions de légalité.

WO90 n'ajoute pas encore de modèle de qualité du sommeil. Support, posture, bruit, lumière, température, sécurité et intimité pourront ultérieurement modifier la qualité ou les conséquences.

Tant qu'il n'existe pas de relation générique personnage–support, le moteur peut établir « dort dans le salon » sans prétendre matériellement « sur le divan ».

### Bain, douche et hygiène

Bain et douche appartiennent à la famille fonctionnelle de l'hygiène personnelle et peuvent aussi être associés au confort.

Le gain d'hygiène doit passer par un mécanisme générique d'activité/effet. WO90 ne crée pas silencieusement une jauge persistante de confort.

Toute interaction de l'eau avec une ressource particulière d'un personnage doit passer par les mécanismes génériques de propriétés/ressources, jamais par un test sur l'identité du personnage.

## T0 produit approuvé

Le T0 exact est fixé uniquement lors du bootstrap persistant finalement autorisé. Il doit correspondre à l'heure EDT réelle de ce démarrage; aucun événement officiel n'a été écrit à 12 h 24 et aucun faux passé ne doit être reconstruit.

Conditions initiales à rendre fidèlement représentables :

- Sophie est absente du domicile, à son travail de photographe journalistique, avec retour prévu à 16 h locale. Son métier est déjà canonique. Elle travaille par choix même si les habitantes reçoivent une allocation et que les dépenses ménagères sont couvertes. Employeur, média, affectation, collègues et autres détails non décidés restent indéterminés.
- Erika est assise dans le salon et joue à des jeux vidéo. Le jeu précis reste indéterminé.
- Patoune est endormi dans le salon, blotti contre Erika. Le divan existe canoniquement; « sur le divan » ne doit être matérialisé comme relation physique que si un mécanisme générique réellement supporté le permet.
- Chuu est dans le bain, se détend et se réhydrate, et s'apprête à sortir. Le bain existe canoniquement. Aucune jauge de confort ne doit être inventée; toute hydratation causale doit passer par le propriétaire générique de la ressource correspondante.
- Luna arrive sur les lieux pour la première fois en taxi, avec un sac d'effets personnels en main. Le contenu du sac reste indéterminé. Le taxi n'a pas besoin de devenir une entité persistante s'il n'est pas nécessaire au fait canonique de l'arrivée.

Ces conditions sont volontairement asymétriques. Le bootstrap ne doit pas les neutraliser en remplaçant les activités significatives par un même `idle`, en plaçant tout le monde au même endroit ou en donnant à tous le même contexte circonstanciel.

## Vocabulaire futur d'actions

WO90 ne doit pas cataloguer toutes les actions possibles. Un chantier ultérieur devra faire évoluer la liste plate d'activités vers un vocabulaire composable : famille fonctionnelle, modalité, cible/objet, affordances requises, contraintes spatiales, durée/interruptibilité, charge physique, effets causaux, règles sociales/permission/consentement, signaux subjectifs et conséquences perceptibles.

## Invariants

- réalité/canon ≠ perception ≠ croyance;
- parole ≠ fait;
- LLM propose, moteur valide;
- un seul propriétaire persistant par état;
- mécanismes génériques plutôt que scripts de personnage;
- aucune reprise de l'ancien SQLite;
- aucun événement officiel Rodage V2 avant fermeture de WO90.

## Validation minimale

L'implantation choisie par Codex doit démontrer :

1. sortie de la propriété vers un espace hors terrain puis un lieu hors foyer;
2. absence d'omniscience spatiale induite;
3. `sleep` légal dans une chambre et dans le salon;
4. H/φ/P toujours propriétaires des conséquences physiologiques actives du sommeil;
5. hygiène personnelle représentable dans la salle de bain sans script de personnage;
6. aucun nouvel état persistant de confort inventé;
7. compatibilité des anciens chemins;
8. répétition complète du T0 approuvé sur SQLite jetable avant toute histoire officielle.

Puis tests ciblés, `compileall`, suite complète, état Git propre et photographie exacte du HEAD/version/schéma/migration.

## Porte de fermeture

WO90 ferme seulement si les trois limites sont levées génériquement, les tests sont verts, le T0 est répétable sur base jetable et aucun SQLite officiel n'a encore reçu d'histoire Rodage V2.

La fermeture de WO90 autorise le premier bootstrap persistant réel du Rodage V2.
