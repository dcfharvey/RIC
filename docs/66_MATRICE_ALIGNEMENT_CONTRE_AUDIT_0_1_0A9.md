# Matrice d’alignement du contre-audit — `0.1.0a9`

**Statut :** décision d’ingénierie préparatoire; aucune recommandation R&D ne
devient canon par sa seule présence ici.  
**Source :** `docs/65_CONTRE_AUDIT_R_D_CHATGPT_0_1_0A9.md`.  
**But :** préserver les bonnes frontières pendant le rodage et préparer le
prochain lot sans implanter prématurément une psychologie incomplète.

## Verdict

Le contre-audit classe le socle **aligné avec réserves**. Aucun refactoring
fondamental n’est requis. Le risque principal est de laisser quatre gardes alpha
devenir des théories permanentes : hiérarchie décisionnelle fixe, attention
principalement technique, relation réduite à des deltas scalaires et mémoire
sans consolidation/récupération.

## Matrice exécutable

| Recommandation | État réel | Décision d’ingénierie | Échéance |
|---|---|---|---|
| Canon ≠ perception ≠ croyance | Conforme et testé | Verrou permanent | Maintenant |
| Parole ≠ fait, croyance, relation ou permission | Conforme; contrats renforcés dans `test_social_non_inference_contracts.py` | Verrou permanent | Maintenant |
| Relation ≠ permission ≠ consentement | Conforme; absence d’inférence testée même avec relation positive | Verrou permanent | Maintenant |
| LLM propose; moteur valide | Conforme | Verrou permanent | Maintenant |
| Mesurer répétition, scènes vides et monoculture d’activités | Livré par `vivarium.telemetry`; gardien en lecture seule | Signal d’attention, jamais vérité psychologique | Rodage courant |
| Conserver les résultats invalides/dégradés des appels | Partiel : orchestrateur en base, arrivée/autonomie/social en JSONL technique | Compléter sans écrire le canon | Rodage courant |
| Hiérarchie `intention > physiologie > objectif` | Simplification alpha connue | Ne pas étendre; remplacer par compétition souple après R&D | Lot décisionnel futur |
| Attention orientée buts, valeurs, habitudes et pertinence apprise | Manquant | Ne pas bricoler pendant le rodage | Lot attention/mémoire |
| Anticipation des besoins avant seuil critique | Manquant | Modèle scientifique requis avant code | Lot physiologie |
| Pression de sommeil ≠ phase circadienne | Manquant | Conserver le besoin alpha; ne pas prétendre simuler le sommeil fin | Lot physiologie |
| Accessibilité sensorielle intra-lieu | Manquant | Topologie qualitative avant social riche; pas de moteur 3D nécessaire | Lot spatial social |
| Activité et mobilité concurrentes | Garde alpha : mouvement interdit pendant activité | Ne pas transformer en ontologie permanente | Après observations |
| Interprétation sociale située avant conséquence | Manquant | Précondition du prochain noyau social causal | Prochain gros lot R&D |
| Épisode social avec attente, attribution, ambiguïté et domaine | Manquant | Précondition aux deltas relationnels automatiques | Prochain gros lot R&D |
| Mémoire minimale : condensation, accessibilité, indices, provenance | Manquant | Requise avant accumulation sociale durable | Même tranche que noyau social |
| Confiance contextuelle par domaine | Les dimensions actuelles sont des résumés globaux | Ne pas supprimer; ajouter contexte/histoire avant automatisation | Noyau social |
| Attachement relation/context-dependent | Disposition générale seulement | Ne pas surinterpréter le champ actuel | Lot personnalité sociale |
| Patoune selon éthologie féline | Cognition sapiente correctement absente | R&D distincte obligatoire avant enrichissement | Futur |
| Validation par distributions et patterns longitudinaux | Bancs présents, métriques encore minimales | Étendre à partir des données de rodage | Progressif |

## Contrats anti-raccourcis

Ces propositions sont explicitement interdites tant qu’un interpréteur social
situé et sa provenance révisable n’existent pas :

- compliment → confiance ou affection positive;
- refus → affection négative;
- excuse → confiance réparée;
- relation positive → permission ou consentement;
- parole → croyance vraie;
- trace subjective → fait canonique.

Les tests actuels prouvent l’absence de mutation automatique. Ils ne prétendent
pas encore prouver que la future interprétation humaine sera crédible.

## Télémétrie de rodage

`inspect_rodage` lit une fenêtre bornée et produit : séquence canonique, nombre
d’admissions cognitives, scènes totales/vides/interrompues, paroles et
formulations distinctes, ainsi que la distribution des départs d’activités par
personnage. Trois heuristiques prudentes signalent répétition, scènes souvent
vides et monoculture d’activité seulement après un minimum d’observations.

Le gardien inscrit ces signaux dans `logs/guardian.jsonl`. Les résultats
d’arrivée, d’autonomie et de scène sont ajoutés dans
`logs/runtime_outcomes.jsonl`; l’orchestrateur conserve déjà ses résultats dans
son journal technique SQLite. Aucun de ces diagnostics n’est canonique.

## Prochain lot autorisé après rodage

Ne pas augmenter d’abord le nombre de tours de dialogue. Le candidat est un
**Social Consequence Core** conçu en R&D comme une tranche cohérente :

```text
événement social accessible
→ trace subjective
→ interprétation sociale située et incertaine
→ appraisal / signification
→ conséquence immédiate éventuelle
→ mémoire minimale récupérable
→ mise à jour relationnelle contextualisée, seulement si justifiée
```

Avant implantation, les sources scientifiques décisives du dossier devront
être vérifiées et le contrat fonctionnel devra préciser les prédictions et
scénarios de falsification, sans prescrire la plomberie SQLite/Python.
