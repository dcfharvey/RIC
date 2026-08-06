# Lot 4.2D — Instances de personnages depuis gabarit

**Statut :** terminé et vérifié le 5 août 2026
**But :** créer une entité canonique réelle à partir d'un gabarit publié, avec
une provenance immuable, sans modifier les placeholders ni injecter une voie
spéciale par espèce ou par nom.

## Contrat retenu

L'instanciation reçoit un monde, un gabarit/version publiés, une clé technique
neuve et un lieu initial existant. Dans une unique transaction elle crée :

1. le personnage canonique;
2. son enregistrement de provenance, avec une copie figée de la définition du
   gabarit;
3. les états de besoins compatibles avec les définitions déjà présentes dans le
   monde, initialisés à leur maximum canonique;
4. le profil technique requis par le simulateur actuel;
5. l'événement canonique `character_instantiated`.

La copie de définition rend l'instance indépendante d'une évolution future du
gabarit. Le gabarit ne contient ni relation vécue, ni mémoire acquise, ni
position courante; le lieu est un choix explicite de l'instanciation.

## Exclusions

- aucune migration, suppression ou renommage automatique de placeholder;
- aucun héritage/overlay, actif, import/export ou changement profond;
- aucune déduction de capacité, cognition, espèce, personnalité ou relation;
- aucune API administrative publique ni interface;
- aucun LLM.

## Critères d'acceptation

- seul un gabarit publié et structurellement valide peut être instancié;
- clé, nom adulte explicite, lieu et monde sont vérifiés avant écriture durable;
- toute erreur laisse personnage, provenance, besoins, profil et journal
  inchangés;
- l'origine conserve la version précise et la définition résolue;
- persistance après réouverture et suite complète de 451 tests vertes.
