# R&D — Adaptation PEFT/LoRA du fournisseur LLM RIC

**Version R&D :** 0.1  
**Date :** 21 août 2026  
**Statut :** exploration technique et fonctionnelle — aucune intégration runtime autorisée par ce document

## 1. Question de recherche

Un adaptateur PEFT/LoRA peut-il améliorer de façon mesurable la discipline RIC d’un modèle de base sans encoder d’état dynamique, sans réduire indûment ses capacités générales et sans déplacer vers les poids une autorité qui appartient au moteur ?

## 2. Invariants

```text
réalité/canon ≠ perception ≠ croyance
parole ≠ fait
relation ≠ permission ≠ consentement
LLM propose, moteur valide
provenance d’audit ≠ source subjectivement mémorisée
état dynamique ≠ poids du modèle
```

À exclure des poids comme cible d’apprentissage : souvenirs particuliers, faits canoniques, relations/permissions/consentements actuels, inventaire/position/physiologie, personnalité propre à un personnage lorsqu’elle doit venir du contexte, règles physiques/métier, scripts propres au casting et données de qualification réservées au test.

## 3. Résultats techniques

LoRA gèle le modèle de base et entraîne de petites matrices de bas rang. QLoRA rétropropage à travers un modèle de base 4-bit gelé et est donc le premier chemin à tester sur une carte 16 Go. Les outils PEFT actuels permettent de charger/activer/désactiver/remplacer des adaptateurs; le hotswap est possible sous contraintes de compatibilité. Qwen3 dispose d’un support documenté pour LoRA/QLoRA. La RX 7800 XT (`gfx1101`) est supportée par ROCm; le backend ROCm de certaines briques QLoRA reste à qualifier sur la machine réelle.

Ces éléments établissent une faisabilité technique plausible, pas l’utilité comportementale dans RIC.

## 4. Hypothèse RIC

L’hypothèse testée est qu’une adaptation légère peut augmenter la probabilité de respect des contrats cognitifs généraux de RIC sous des contextes variés, tandis que tout état subjectif et canonique reste fourni et validé par les systèmes propriétaires.

Cibles possibles : distinction canon/perception/croyance; parole≠fait; abstention quand l’information manque; provenance correcte; absence de psychologisation comme vérité; schémas de sortie; rôle propositionnel; frontière données/instructions; terminologie opérationnelle stable.

## 5. Un seul LoRA au départ

La première expérience doit utiliser un seul adaptateur RIC. Un LoRA conversation séparé n’est pas retenu avant preuve d’une déficience distincte et reproductible. Conversation State doit d’abord fournir la continuité explicitement et de façon auditable.

## 6. Risques et contrôles

- **Surapprentissage du benchmark** → benchmark final gelé avant dataset; séparation stricte train/validation/test.
- **Rigidification/abstention excessive** → cas contrastifs et mesure des faux positifs/faux négatifs.
- **Simulation implicite du moteur par le LLM** → exemples apprenant à proposer, jamais à rendre faisable ou à produire les conséquences.
- **Contamination du casting** → identités variées/synthétiques et tests de transfert.
- **Régression générale** → suite hors domaine séparée.
- **Dépendance runtime** → audit Codex du fournisseur réel avant intégration.

## 7. Protocole

### L0 — faisabilité technique hors runtime
Smoke-test QLoRA sur micro-dataset artificiel; sauvegarde/rechargement; base vs base+LoRA; VRAM/RAM/temps; verdict FEASIBLE / FEASIBLE WITH LIMITS / NOT YET FEASIBLE.

### L1 — benchmark avant dataset
Cas canon/perception/croyance, parole/fait, provenance, abstention, interprétation sociale non omnisciente, instruction hostile dans les données du monde, schéma de sortie, hors domaine et cas métamorphiques.

### L2 — dataset SFT
Dataset initialement petit et très propre, diversifié, sans fuite du benchmark. Ajouter des exemples en réponse à des capacités/échecs mesurés, pas pour atteindre une taille arbitraire.

### L3 — entraînement QLoRA
SFT, 4-bit si backend qualifié, un adaptateur, petit rang initial puis ablation, hyperparamètres calibrés expérimentalement.

### L4 — évaluation aveugle
Comparer à contexte identique `Qwen base` vs `Qwen base + RIC-LoRA` sur violations d’invariant, faits/provenance inventés, sortie invalide, abstention, surinterprétation, instruction hostile, régression générale et stabilité aux reformulations.

### L5 — porte d’intégration
N’autoriser un essai runtime qu’après gain reproductible, absence de fuite benchmark, régressions acceptables, audit architectural Codex, rollback démontré et provenance `model + adapter + version` observable.

## 8. Falsification

L’hypothèse « LoRA utile à RIC » doit être rejetée ou différée si le gain ne généralise pas, si le modèle devient plus rigide/omniscient, si la baisse d’erreurs vient d’une abstention quasi permanente, si les régressions générales sont inacceptables ou si les mêmes gains sont obtenus plus simplement et plus robustement par le contrat/contexte/prompt.

## 9. Séquençage

La R&D L0–L2 peut avancer en parallèle du chantier runtime principal. L’intégration runtime attend normalement la stabilisation de Conversation State minimal, BOL et P3.5. Aucun essai LoRA ne doit contaminer une qualification P0 Memory ni réinterpréter un résultat antérieur.

## 10. Gouvernance

- **SCI/TECH** : fondements et benchmark comportemental.
- **MIXED** : limites de ce qui peut être appris sans déplacer l’autorité hors moteur.
- **TECH** : pipeline QLoRA, compatibilité AMD, chargement/hotswap, versioning, observabilité.
- **PRODUCT** : décision finale d’adopter ou non l’adaptateur.

Codex demeure autorité sur l’architecture réelle et l’ordre d’implantation technique.
