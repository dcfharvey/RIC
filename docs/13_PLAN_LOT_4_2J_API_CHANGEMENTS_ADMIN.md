# Lot 4.2J — API locale des changements administratifs

**Statut :** terminé et vérifié le 6 août 2026

## But

Exposer le pipeline déjà validé de `AdminChangeService` au client HTTP local,
sans recréer de logique métier, sans SQL dans `web.py` et sans modifier
l'interface.

## Contrat prévu

| Méthode | Route | Jeton local | Rôle |
| --- | --- | --- | --- |
| POST | `/api/admin-changes/rename-world/prepare` | requis | Prépare un renommage. |
| POST | `/api/admin-changes/add-passage/prepare` | requis | Prépare l'ajout d'un passage. |
| GET | `/api/admin-changes/{plan_id}/validate` | requis | Relit les préconditions. |
| GET | `/api/admin-changes/{plan_id}/impact` | requis | Lit l'impact figé et la validité. |
| POST | `/api/admin-changes/{plan_id}/confirm` | requis | Confirme le hash exact. |

Les routes restent fermées : un UUID canonique est requis, les corps sont des
objets JSON bornés sans paramètre inconnu et les codes métier deviennent des
statuts HTTP stables. Les lectures de plan demandent aussi le jeton parce que le
contrat est administratif, pas une vue publique du monde.

## Exclusions

- aucun nouveau bouton ou écran ;
- aucune commande de personnage ;
- aucun contournement du service de changement préparé ;
- aucune logique d'autorisation multi-rôles.

## Garanties prouvées

- le serveur ne contient ni SQL métier ni voie d'écriture parallèle ;
- les cinq routes utilisent l'enveloppe JSON et les protections Host/Origin
  existantes ;
- le jeton est exigé pour préparer, confirmer, valider ou lire l'impact ;
- UUID invalide, paramètre inconnu et hash erroné sont refusés avec un statut
  HTTP stable ;
- la confirmation répétée reste idempotente via la même API.
