# Inventaire de la résidence initiale

**Statut :** composition de référence du blueprint de résidence. Les objets
seront créés par le gestionnaire d'objets/blueprint, pas ajoutés par un seed
spécial lié au casting.

## Cuisine / repas

- réfrigérateur;
- four;
- four micro-ondes;
- lave-vaisselle;
- table à manger;
- quatre chaises.

Les quatre chaises correspondent aux quatre résidentes sapientes. Patoune est
une présence autonome, non une cinquième convive humaine.

Il n'existe pas de salle à manger séparée : les repas partagés se déroulent
dans la cuisine.

## Salle de bain

- bain;
- douche;
- toilette;
- litière de Patoune;
- vanité avec miroir et tiroirs.

Le miroir et les tiroirs sont des éléments utiles au futur système de
perception/objets; ils ne donnent pour l'instant aucune information magique au
moteur.

## Chambres des résidentes sapientes

Chacune des quatre chambres reçoit :

- un lit;
- une armoire à linge;
- un bureau;
- une chaise de bureau.

Les chambres ne reçoivent pas encore de mobilier ou style individuel imposé.
Leurs possessions et décorations pourront émerger ou être ajoutées plus tard
par les mécanismes génériques d'objets et les changements administratifs.

## Buanderie

- laveuse;
- sécheuse.

Voir `docs/28_VETEMENTS_ET_BUANDERIE.md` pour la future gestion fonctionnelle
des vêtements, de l'humidité et des cycles de lavage.

## Sous-sol

- chauffe-eau;
- panneau électrique.

Le sous-sol est volontairement lugubre. Son ambiance est descriptive pour
l'instant; les risques, pannes, permissions d'entretien ou peur éventuelle ne
seront ajoutés que lorsqu'ils auront des règles explicites.

## Grenier

Le grenier ne reçoit encore aucun contenu imposé. Il est accessible par un
escalier escamotable à corde, situé dans le couloir près de la porte du
sous-sol. Cet accès ne doit pas être traité comme une simple porte : il faudra
une future règle de connecteur rétracté/déployé.

## Salon / équipements partagés

- divan;
- télévision;
- meuble de télévision;
- console de jeux vidéo;
- ordinateur partagé, disponible au besoin.

L'ordinateur est une ressource commune, non la propriété initiale d'une seule
résidente. Son emplacement détaillé pourra être fixé avec le plan d'aménagement
du salon, sans changer cette propriété fonctionnelle.

## Objets personnels initiaux

- Sophie, Erika, Luna et Chuu possèdent chacune un téléphone;
- Patoune ne reçoit pas de téléphone.

Les téléphones sont des objets portables individuels. Leur communication,
batterie, applications et confidentialité appartiennent à des lots futurs :
leur simple existence ne simule encore aucun réseau social ou message.

## Cour clôturée

- clôture;
- piscine creusée;
- remise;

La boîte aux lettres appartient plutôt à la zone d'entrée extérieure, distincte
de cette cour arrière clôturée.

La piscine et les futurs contenants d'eau seront importants pour Chuu, mais ne
reçoivent pas encore de règle spéciale : l'eau, les liquides et l'absorption
doivent être implémentés comme mécanismes génériques avant toute conséquence.

## Stationnement extérieur

Un espace de stationnement extérieur est prévu, distinct de l'entrée devant la
maison. Son usage par véhicules, ses occupants éventuels et les règles de
circulation restent futurs; le premier blueprint le représentera seulement
comme un lieu extérieur relié à l'entrée.

## Découpage de livraison

Le premier blueprint peut déclarer les lieux et installations fixes dès que le
catalogue de résidence est construit. Les fonctions détaillées viennent ensuite
par couches : port/équipement, vêtements, appareils, eau et cognition. Ainsi,
un objet n'acquiert jamais une fonction fictive simplement parce qu'il porte un
nom familier.
