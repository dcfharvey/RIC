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
- boîte aux lettres, point d'arrivée commun des cinq résidentes.

La piscine et les futurs contenants d'eau seront importants pour Chuu, mais ne
reçoivent pas encore de règle spéciale : l'eau, les liquides et l'absorption
doivent être implémentés comme mécanismes génériques avant toute conséquence.

## Découpage de livraison

Le premier blueprint peut déclarer les lieux et installations fixes dès que le
catalogue de résidence est construit. Les fonctions détaillées viennent ensuite
par couches : port/équipement, vêtements, appareils, eau et cognition. Ainsi,
un objet n'acquiert jamais une fonction fictive simplement parce qu'il porte un
nom familier.
