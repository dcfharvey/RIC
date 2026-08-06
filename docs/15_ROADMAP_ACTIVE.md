# Roadmap active — du moteur au Vivarium MVP

**Version :** 1.0
**Mise à jour :** 6 août 2026
**Statut :** trajectoire opérationnelle. Elle remplace l'ordre immédiat des
anciennes feuilles de route historiques, sans effacer leur valeur documentaire.

## Principe de conduite

Chaque capacité importante doit avoir un moyen reproductible d'être mise en
situation, observée et comparée **avant** de contaminer le monde MVP. Le banc
d'essai n'est donc pas une interface de fin de projet : c'est une couche de
validation du moteur qui croît avec lui.

## État actuel

- moteur déterministe, journal canonique, transactions et audits : livrés ;
- contrats/personnages versionnés, ressources et effets déclaratifs : livrés ;
- premiers changements administratifs préparés (renommage, ajout de passage) :
  livrés ;
- cinq gabarits MVP : livrés, mais aucune résidente n'est encore créée dans un
  monde réel ;
- cognition, perception, mémoire et social : futurs ;
- banc d'essai : décidé, à construire avant ces systèmes subjectifs.

## Ordre de travail

### 1. Sûreté de l'univers administratif

Finir les mutations spatiales dont l'impact peut être structurel : fermeture de
passage avec détection d'isolement, puis seulement les premiers lieux/objets si
un cas concret l'exige. Aucune suppression ne doit devenir une voie rapide.

### 2. Banc d'essai minimal du moteur

Construire un outil sans LLM et sans interface graphique qui :

- crée une base isolée et temporaire à partir d'un scénario déclaratif ;
- fixe l'horloge, le monde initial et les actions injectées ;
- exécute le moteur jusqu'à une borne choisie ;
- produit un rapport lisible, le digest d'état, les événements et les refus ;
- compare deux exécutions identiques ou deux variantes ;
- ne modifie jamais une base MVP ou un monde de développement existant.

La première version est un outil pour l'IA et les tests automatisés. Une
interface d'exploration humaine pourra venir ensuite, si elle répond à une
friction observée.

### 3. Scénarios d'acceptation inter-systèmes

Ajouter progressivement des situations de référence : passage ouvert/fermé,
ressource qui bloque une capacité, blessure et trajet, pause/reprise,
intervention admin et redémarrage. Chaque nouveau système devra fournir ses
propres scénarios reproductibles avant d'être activé dans le monde MVP.

### 4. Monde MVP propre

Créer une base séparée de tout monde technique. Construire la résidence et
instancier Sophie, Erika, Luna, Chuu et Patoune par les gestionnaires réels, avec
une validation rapide du propriétaire sur leurs fiches détaillées. Le monde MVP
est le laboratoire vivant; les bancs d'essai restent ses copies isolées.

### 5. Perception, croyance, mémoire puis dynamique sociale

Ajouter ces couches dans cet ordre, avec le banc d'essai comme critère de sortie
de chaque lot. Le LLM n'entre qu'après le contrat moteur–LLM, avec sorties
structurées, validation et coût borné.

## Frontières explicites

- Les tests unitaires actuels restent la preuve des règles locales.
- Le banc d'essai prouve les interactions de systèmes et les "what if".
- Le monde MVP est une histoire persistante, jamais une poubelle de test.
- Un test emergent intéressant n'est pas une règle : il doit être reproduit,
  expliqué et décidé avant de devenir du canon.
