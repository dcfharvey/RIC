# Idées à implémenter après le MVP

**Version :** 0.1  
**Date :** 5 août 2026  
**Statut :** Liste non normative d’extensions reportées

---

## LOD de simulation des agents extérieurs

**Nom de travail :** Fidélité adaptative des agents  
**Priorité :** Après le MVP  
**État :** Documenté, non planifié pour implémentation  
**Document associé :** `Vivarium_LOD_simulation_agents_v0_1.md`

### Résumé

Simuler les membres du foyer avec une fidélité maximale permanente, mais ajuster dynamiquement la profondeur des visiteurs, figurants et personnages secondaires selon leur pertinence.

Niveaux initiaux envisagés :

- BACKGROUND;
- CONTEXTUAL;
- PERSISTENT;
- RESIDENT.

La pertinence dépendrait de :

- rôle structurel;
- implication actuelle;
- conséquences persistantes;
- fréquence de retour;
- relation avec le foyer;
- intérêt explicite du propriétaire.

### Raison du report

Le système dépend de composants qui ne sont pas encore stabilisés :

- visiteurs;
- scènes;
- perception;
- mémoire;
- relations;
- conséquences persistantes;
- vie hors champ;
- orchestration LLM.

Il ne doit pas retarder la boucle autonome minimale des quatre membres du foyer.

### Critère de reprise

Réévaluer après que le MVP permette :

1. aux quatre résidents de vivre dans le foyer;
2. de percevoir;
3. de se souvenir;
4. de prendre des décisions;
5. d’agir;
6. d’interagir;
7. d’utiliser un premier adaptateur LLM fonctionnel.
