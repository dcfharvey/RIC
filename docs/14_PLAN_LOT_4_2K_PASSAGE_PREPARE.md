# Lot 4.2K — Passage d'univers préparé

**Statut :** terminé et vérifié le 6 août 2026

## But

Rendre le premier changement topologique du monde accessible au propriétaire
par le protocole préparé : ajouter un passage entre deux lieux existants.
Il réutilise `GraphEngine`; il ne crée ni second graphe, ni raccourci pour les
déplacements.

## Portée livrée

Action `add_link` :

- origine et destination doivent être deux lieux existants et distincts ;
- `bidirectional=True` crée deux arêtes réciproques; `False` une seule ;
- une arête déjà existante refuse le plan, sans écriture ;
- impact figé : deux lieux, une ou deux arêtes, aucun personnage modifié ;
- à l'application, `link_added` reste le fait canonique et référence le plan
  administratif qui l'a autorisé.

L'API locale ajoute :

```text
POST /api/admin-changes/add-passage/prepare
```

Les routes existantes `validate`, `impact` et `confirm` servent ensuite ce plan
sans variante de protocole.

## Migration 0015

SQLite ne permet pas d'élargir le `CHECK` d'une table en place. La migration
reconstruit donc atomiquement `admin_change_plan` et `admin_audit_event` pour
admettre `add_link`, copie toutes les lignes et recrée leurs déclencheurs
d'immutabilité. Un test part d'une base réellement arrêtée à 0014, crée un
plan/audit, applique 0015 et prouve que les deux enregistrements sont conservés.

## Garanties prouvées

- le plan ne modifie pas le graphe avant confirmation ;
- les deux arêtes et l'événement sont atomiques ;
- boucle, lieu inconnu ou arête existante sont refusés sans plan ;
- le hash, l'expiration, la concurrence et le retry idempotent du pipeline sont
  identiques au renommage ;
- les commandes spatiales existantes et les tests de réouverture restent verts.

## Exclusions

- ne retire aucun passage existant ; une fermeture demande son propre rapport
  d'impact, notamment parce qu'elle peut isoler un lieu ;
- ne crée pas encore de lieu, d'objet ou de propriété sociale de lieu ;
- ne change aucun personnage, ses souvenirs ou sa perception.
