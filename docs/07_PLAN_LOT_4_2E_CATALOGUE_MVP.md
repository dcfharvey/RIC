# Lot 4.2E — Catalogue initial de composants MVP

**Statut :** terminé et vérifié le 5 août 2026
**But :** rendre le registre immédiatement utilisable par les futurs gabarits,
sans faire croire au moteur qu'une fonction cognitive ou sociale existe déjà.

## Catalogue publié

- `body.morphology` : morphologie bipedal, quadrupedal ou amorphous;
- `cognition.profile` : distinction explicite sapient / non_sapient;
- `needs.standard` : rattachement déclaré aux besoins déjà pris en charge par
  le moteur MVP.

Les deux premiers sont descriptifs pour l'instant. Ils ne déclenchent aucune
capacité ni branchement par espèce. Le troisième reflète l'infrastructure de
besoins effectivement implémentée, sans prétendre couvrir les besoins futurs
spécifiques d'une slime ou d'un autre univers.

## Garanties

- installation atomique et idempotente;
- aucune correction silencieuse d'un contrat existant incompatible;
- contrats publiés immuables en version 1;
- aucune création de résident, migration de placeholder, interface ou LLM;
- 453 tests complets réussis.
