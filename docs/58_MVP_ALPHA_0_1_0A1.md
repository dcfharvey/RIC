# MVP alpha 0.1.0a1 — boucle sociale minimale présentable

**Statut :** livré le 6 août 2026. Cette fiche décrit exactement l'alpha 1;
elle ne transforme pas les fonctions futures en promesses déjà tenues.

## Ce qui est réellement présent

Une résidence neuve peut être créée par `mvp-init`, inspectée sans écriture par
`mvp-preflight`, puis lancée par `mvp-run`. Le runtime :

1. maintient le temps, les besoins et les activités par les services canoniques;
2. si Gemma local est activé, traite l'orchestrateur cognitif déjà borné;
3. détecte une co-présence réelle et ouvre une scène sociale append-only;
4. donne au plus une occasion de parole par tick, avec quatre tours au plus par
   scène;
5. ferme explicitement une scène arrivée à sa borne, interrompue ou arrêtée.

Le démarrage commun est lui-même une source canonique : le premier duo sapient
co-localisé peut recevoir une scène initiale, ancrée dans l'événement
`world_initial_context_set`. Ensuite, seules les co-présences créées par un
déplacement canonique peuvent ouvrir une scène. Patoune est expressément hors
de cette boucle, car elle n'a pas le composant cognitif sapient.

L'interface locale montre les mondes, les résidentes, le journal, les commandes
pause/reprise et les scènes avec leurs paroles enregistrées. Elle n'est pas une
seconde autorité : les commandes passent par les services canoniques existants.

## Frontière LLM

Le LLM ne reçoit qu'un contexte privé, borné et factuel. Il propose une
`no_action` ou une parole unique; l'admission, les participantes, la présence,
le destinataire, la taille et l'enregistrement restent vérifiés par le moteur.
Une phrase n'établit ni fait, ni relation, ni croyance, ni consentement.

Gemma 4 QAT peut employer la variante redondante `action: "greet"` avec
`act_kind: "greet"`. L'adaptateur local la convertit seulement en
`action: "speak"` lorsque tous les autres champs du contrat sont déjà exacts.
Toute autre forme reste rejetée. Le contrat interne `SceneTurnDecision` reste
strict; cette tolérance est isolée à l'adaptateur du modèle local.

## Choix de conception et recherche

La boucle ne tente pas encore de résoudre une planification sociale générale.
Elle sépare une possibilité d'action immédiate d'un choix : les traversées
visibles sont d'abord revérifiées par `TraversalEngine.preview`, puis seules
celles encore légales sont proposées. Cette séparation est cohérente avec les
travaux qui distinguent génération d'options, affordances et évaluation, et
avec les revues de sélection d'action qui opposent explicitement des actions
concurrentes selon contraintes et coût/récompense.

- [Chambon et al., *Why we should talk about option generation in decision-making research*](https://pmc.ncbi.nlm.nih.gov/articles/PMC3750205/)
- [Kable et al., *Choosing Actions*](https://pmc.ncbi.nlm.nih.gov/articles/PMC3669743/)
- [Parkinson et al., revue de la sélection d'action](https://pmc.ncbi.nlm.nih.gov/articles/PMC9139261/)

La conclusion d'ingénierie est volontairement modeste : l'alpha vérifie les
options de déplacement et les conversations co-localisées, sans prétendre que
le moteur possède déjà une théorie complète des motifs ou de la sociabilité.

## Limites connues et prochain palier

- Les dialogues ont des conséquences textuelles seulement; leurs effets sociaux
  causaux restent un futur contrat.
- La politique d'activité est encore déterministe; le LLM ne choisit pas une
  activité de vie générale.
- Pas de mémoire narrative consolidée, d'économie, de vêtements, d'effort
  physique, de Discord ni de publication.
- L'alpha est réinitialisable. Avant `0.1.0b1`, il faudra observer une exécution
  prolongée, consigner les défauts réels et ajouter seulement les règles qui
  répondent à ces défauts.

## Lancement opérateur

```powershell
# Une seule fois pour une nouvelle histoire. Refuse d'écraser une base existante.
.\.venv\Scripts\python.exe -m vivarium mvp-init --db data\vivarium-alpha.sqlite

# Lancement observé dans PowerShell; Ctrl+C ferme proprement les scènes ouvertes.
.\.venv\Scripts\python.exe -m vivarium mvp-run --db data\vivarium-alpha.sqlite --enable-local-llm
```

Le runtime affiche l'URL de la console locale. Sans `--enable-local-llm`, il
continue les routines canoniques mais n'essaie aucune cognition ni scène LLM.
