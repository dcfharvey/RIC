# Lot 4.2G — Ressources, seuils et états dérivés

**Statut :** terminé et vérifié le 5 août 2026

## Contrat

Une ressource est distincte d'un besoin : elle est une quantité canonique
normalisée, associée à un personnage, qui évolue selon un taux rationnel et
produit toujours un état de plage explicite.

```text
resource_state(value, rate, anchor)
  → bandes exhaustives et non chevauchantes
  → state_key dérivé
  → futurs effets déclarés
```

Le présent lot construit uniquement la quantité, les bandes, la dérivation et
la trace canonique. Il ne décide pas encore qu'un état modifie une capacité,
une humeur ou une action : ces effets restent des systèmes ultérieurs.

## Familles consignées pour plus tard

- espace et compatibilité;
- permissions, règles et consentement;
- perception et information accessible;
- connaissance, croyance et incertitude;
- relations et dynamique sociale;
- personnalité, valeurs et limites;
- objectifs, engagements et routines;
- actions, préconditions et conséquences;
- transformations et continuité d'identité;
- événements, temps et causalité.

Elles sont une carte d'architecture, pas une obligation de les implémenter
avant le MVP.

## Critères d'acceptation

- ressource, taux et bandes validés sans REAL;
- bandes exhaustives et non chevauchantes;
- lecture pure, matérialisation atomique et événement auditable;
- rejet sans écriture partielle des clés, taux, temps et bandes invalides;
- état inclus dans le digest de reproductibilité;
- aucune règle spéciale pour Chuu ni aucun effet psychologique inventé.

**Validation :** 458 tests complets réussis.
