# Limite de précision de l’environnement

**Version :** 0.1  
**Date :** 5 août 2026  
**Statut :** Principe d’architecture

## 1. Règle centrale

Un détail est simulé seulement s’il peut modifier une action disponible, être perçu et interprété, produire une conséquence persistante, créer une pénurie, un conflit ou un retard, distinguer réellement un personnage ou une relation, ou intéresser raisonnablement l’administration du Vivarium.

Un détail qui ne réussit aucun de ces tests doit rester abstrait.

> La fidélité maximale ne signifie pas tout simuler. Elle signifie simuler précisément ce qui compte et résumer agressivement le reste.

## 2. Trois niveaux de représentation

### 2.1 État agrégé

Niveau par défaut : ustensiles propres suffisants, nourriture disponible moyenne, propreté acceptable.

### 2.2 Ressource ou objet fonctionnel

Utilisé lorsqu’un élément peut manquer, être consommé, être déplacé ou produire une conséquence.

### 2.3 Objet individuel distinct

Réservé aux objets ayant une identité fonctionnelle, sociale ou affective.

La majorité de l’environnement reste agrégée. Une minorité devient fonctionnelle. Très peu d’objets doivent être individualisés.

## 3. Exemples

### Ustensiles

Ne pas suivre chaque fourchette par défaut. Préférer des états tels que `suffisants`, `faibles` ou `épuisés`. Le comptage précis devient pertinent seulement en cas de manque, casse, dissimulation, préférence particulière ou conflit.

### Nourriture

Ne pas suivre chaque tranche individuellement. Suivre plutôt le type, la quantité approximative, la fraîcheur, l’emplacement et la possibilité d’être consommée ou jetée.

Une viande qui grisonne devient pertinente si elle peut être remarquée, mangée, jetée, provoquer un conflit ou rendre quelqu’un malade.

### Toilettes

Conserver seulement le besoin physiologique abstrait, l’urgence, la disponibilité de la salle de bain, l’inconfort si le besoin est repoussé et les incidents exceptionnels justifiés.

Ne pas simuler systématiquement chaque passage, les détails biologiques, la durée exacte, les déchets corporels ou les variations digestives ordinaires.

### Douche

La douche mérite davantage de représentation parce qu’elle peut affecter l’hygiène, le confort, l’intimité, l’occupation de la salle de bain, les vêtements, les serviettes, l’eau chaude, les interruptions et les routines sociales.

L’activité reste représentée comme une action cohérente, pas comme une série de microgestes.

## 4. Matérialisation et recompression

```text
état agrégé
→ détail rendu pertinent
→ matérialisation
→ interaction et conséquences
→ maintien si persistant
→ recompression si banal
```

Le système ne doit pas remplir rétroactivement tout l’environnement de détails inutiles.

## 5. Risques d’un excès de précision

Bruit dans le contexte LLM, multiplication des tests, interface illisible, événements importants noyés, calcul inutile, comportements absurdes produits par des jauges insignifiantes et moteur domestique ressemblant à un logiciel d’inventaire.

## 6. Décision actuelle

Le Vivarium vise une psychologie fine, un corps crédible, un espace socialement concret, des ressources fonctionnelles et des objets persistants lorsqu’ils comptent.

Il ne vise pas une reproduction exhaustive de chaque détail domestique.
