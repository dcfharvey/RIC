# Lot 4.2I — Changements administratifs préparés

**Statut :** terminé et vérifié le 6 août 2026
**But :** poser le premier chemin d'intervention du propriétaire qui ne soit ni
un CRUD SQLite ni une simple confirmation d'interface.

## Portée livrée

Le service `AdminChangeService` prend en charge une première opération
volontairement non sensible : `rename_world`.

```text
prepare -> validate (lecture) -> impact (lecture) -> confirm -> application atomique
```

Un plan préparé fige : action, paramètres normalisés, impact, dernière
séquence canonique du monde, expiration et hash SHA-256. La confirmation doit
fournir l'identifiant public **et** ce hash exact. Une séquence canonique
nouvelle, même sans lien avec le renommage, rend le plan obsolète : il faut
alors en préparer un autre.

Le contenu d'un plan est immuable; son statut ne peut effectuer qu'une seule
transition `prepared -> applied`. Les événements de `admin_audit_event` sont
append-only. Cet ensemble constitue l'audit administratif, distinct du journal
canonique. Lorsqu'un plan est appliqué, `world_renamed` reste l'événement
canonique du fait et contient l'identifiant du plan qui l'a autorisé.

## Garanties prouvées

- préparer, valider et lire l'impact ne modifient pas le monde ni son journal ;
- le plan contient un impact sémantique explicite, pas un diff SQL ;
- expiration, hash incorrect et concurrence refusent sans mutation ;
- application, transition du plan, audit et événement canonique forment une
  seule transaction ;
- un retry de la confirmation exacte retourne le résultat déjà appliqué sans
  répéter le renommage ni l'événement ;
- une erreur artificielle pendant l'application rollback le monde, le journal,
  l'audit et le statut du plan.

## Exclusions assumées

- aucune mutation de personnage, aucune psychologie, aucun snapshot ou retour
  arrière ;
- aucune exposition HTTP/UI du nouveau pipeline pour l'instant ;
- les anciennes commandes admin simples restent disponibles pour ne pas casser
  l'interface actuelle ; elles seront basculées ou retirées dans un lot dédié ;
- le contrôle d'autorisation multi-rôles reste futur : le MVP local a un seul
  propriétaire, mais le service est déjà une frontière serveur unique.

## Suite recommandée

Avant toute mutation profonde d'une habitante, étendre ce protocole avec les
versions de cibles, snapshots et impact sur la fiche/personnalité. Le prochain
cas utile, mais encore à choisir, est un gestionnaire d'univers (lieu, passage,
objet) plutôt qu'une édition directe de personnage.
