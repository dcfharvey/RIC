# R&D — Adaptation PEFT/LoRA du fournisseur LLM RIC

**Version R&D :** 0.2  
**Date :** 21 août 2026  
**Statut :** R&D technique et fonctionnelle ouverte — prototype hors runtime autorisable; aucune intégration runtime autorisée par ce document

## 1. Question de recherche

Un adaptateur PEFT/LoRA peut-il améliorer de façon reproductible la discipline RIC d’un modèle de base sans encoder d’état dynamique, sans réduire indûment ses capacités générales et sans déplacer vers les poids une autorité qui appartient au moteur ?

Ce chantier est transverse : il peut préparer benchmark, dataset et prototypes hors runtime pendant que la roadmap fonctionnelle progresse. La porte d’intégration runtime reste placée après Conversation State minimal, BOL et P3.5.

## 2. Résultats techniques établis

### 2.1 PEFT et LoRA

PEFT adapte un modèle préentraîné en entraînant une petite quantité de paramètres supplémentaires plutôt que tous les poids. LoRA représente les mises à jour par des matrices de bas rang tandis que les poids du modèle de base restent gelés.

Conséquences techniques utiles pour RIC :

- le modèle de base peut rester intact;
- l’adaptateur est sauvegardable séparément;
- plusieurs adaptateurs peuvent être chargés et activés/désactivés selon le runtime;
- PEFT expose aussi un mécanisme de hotswap qui remplace en place les poids d’un adaptateur compatible, sans recharger le modèle de base;
- le hotswap a des contraintes de compatibilité et ne doit pas être présumé identique dans tous les runtimes.

Sources techniques :

- Hugging Face PEFT — LoRA : https://huggingface.co/docs/peft/main/conceptual_guides/lora
- Transformers — intégration PEFT et gestion de plusieurs adaptateurs : https://huggingface.co/docs/transformers/peft
- Hugging Face PEFT — hotswap : https://huggingface.co/docs/peft/package_reference/hotswap

### 2.2 QLoRA

QLoRA entraîne un adaptateur LoRA au-dessus d’un modèle de base quantifié et gelé. La documentation PEFT recommande, pour un entraînement de style QLoRA, de pouvoir cibler toutes les couches linéaires (`target_modules="all-linear"`); la quantification 4-bit et le choix exact de l’initialisation restent à calibrer expérimentalement.

Sources :

- PEFT — quantization / QLoRA-style training : https://huggingface.co/docs/peft/en/developer_guides/quantization
- TRL — PEFT / QLoRA : https://huggingface.co/docs/trl/en/peft_integration

### 2.3 Qwen3

La documentation officielle Qwen3 fournit des recettes SFT avec LoRA et mentionne explicitement LoRA, QLoRA et DoRA via ms-swift. Elle documente aussi les datasets conversationnels `messages` et un exemple LoRA avec `target_modules=all-linear`.

Source : https://github.com/QwenLM/Qwen3/blob/main/docs/source/training/ms_swift.md

Cela démontre que la famille Qwen3 est techniquement adaptable par LoRA. Cela ne démontre pas qu’un LoRA améliore RIC.

### 2.4 Matériel AMD cible

La Radeon RX 7800 XT est une RDNA3 `gfx1101` 16 Go officiellement supportée par ROCm sur Linux. AMD la liste aussi dans la matrice WSL ROCm 7.2.1. La documentation bitsandbytes actuelle fournit des builds ROCm couvrant `gfx1101` et indique le support des fonctionnalités de quantification pour les GPU RDNA compatibles.

Sources :

- AMD ROCm — RX 7800 XT / `gfx1101` : https://rocm.docs.amd.com/projects/install-on-linux/en/docs-7.2.2/reference/system-requirements.html
- AMD ROCm — WSL compatibility : https://rocm.docs.amd.com/projects/radeon-ryzen/en/docs-7.2.1/docs/compatibility/compatibilityrad/wsl/wsl_compatibility.html
- bitsandbytes — installation / AMD ROCm : https://huggingface.co/docs/bitsandbytes/installation

**Conclusion prudente :** QLoRA sur cette machine est techniquement plausible, particulièrement sous Linux/WSL, mais doit être qualifié sur le poste réel. Les combinaisons exactes PyTorch/ROCm/bitsandbytes, la mémoire réellement disponible, les kernels, la longueur de contexte et la stabilité ne doivent pas être déduits des seules matrices de support.

## 3. Invariants RIC appliqués au fine-tuning

```text
réalité/canon ≠ perception ≠ croyance
parole ≠ fait
relation ≠ permission ≠ consentement
LLM propose, moteur valide
provenance d’audit ≠ source subjectivement mémorisée
état dynamique ≠ poids du modèle
```

L’adaptation peut viser un **comportement général du composant LLM**. Elle ne doit pas créer un deuxième propriétaire caché d’un état RIC.

## 4. Ce qu’un LoRA RIC peut chercher à apprendre

Cibles candidates, à confirmer par benchmark :

- respecter canon / perception / croyance;
- traiter une parole comme une parole plutôt que comme un fait;
- conserver la provenance et l’incertitude pertinentes;
- produire `unresolved` / abstention lorsqu’une conclusion n’est pas soutenue;
- éviter la psychologisation et les hidden-state claims présentés comme certains;
- respecter les schémas de sortie et le rôle propositionnel du LLM;
- résister à une instruction hostile présente dans les données du monde;
- utiliser une terminologie RIC stable quand le contrat l’exige.

Ces cibles prolongent les bancs SCC-1B existants : la sécurité/frontière RIC et la fiabilité du contrat restent prioritaires sur l’élégance textuelle.

## 5. Ce qui doit rester hors des poids

Ne pas entraîner comme vérité persistante :

- faits du monde, localisation, inventaire, physiologie ou état canonique actuel;
- souvenirs individuels;
- relations, permissions ou consentements actuels;
- personnalité ou biographie d’un personnage lorsqu’elles doivent venir du contexte;
- Conversation State courant;
- opportunités BOL courantes;
- règles physiques, affordances et validation moteur;
- scripts `personnage → comportement`;
- réponses des benchmarks finaux réservés à l’évaluation.

Un LoRA qui « connaît » Luna, Chuu ou Sophie n’est pas automatiquement un meilleur LoRA RIC. Le comportement recherché doit transférer vers des identités et situations non vues.

## 6. Un seul adaptateur au départ

La première expérience utilise **un seul adaptateur général RIC**.

Un adaptateur conversation séparé n’est justifié que si, après Conversation State, une déficience conversationnelle distincte reste reproductible et si sa correction séparée surpasse un adaptateur unique sans régression. Les frontières conceptuelles Reality / Interaction / Cognition ne doivent pas être copiées mécaniquement en un nombre équivalent de LoRA.

## 7. Méthode expérimentale

### L0 — baseline avant entraînement

Avant de créer le dataset :

1. sélectionner le modèle de base exact, sa quantification/runtime et son contrat;
2. figer un benchmark de falsification;
3. mesurer la baseline vanilla;
4. conserver une partition finale jamais utilisée pour choisir les exemples d’entraînement.

Le benchmark précède le dataset pour réduire la fuite expérimentale.

### L1 — faisabilité technique hors runtime

Smoke-test sur micro-dataset artificiel :

- chargement du modèle quantifié;
- création du LoRA;
- quelques étapes SFT;
- sauvegarde/rechargement;
- base vs base+LoRA;
- activation/désactivation ou hotswap si le runtime choisi le permet;
- VRAM/RAM, vitesse et stabilité.

Verdict : `FEASIBLE`, `FEASIBLE WITH LIMITS` ou `NOT YET FEASIBLE`.

Cette étape ne touche aucune DB RIC persistante et n’autorise aucun changement de provider de qualification.

### L2 — benchmark RIC

Familles minimales :

- canon/perception/croyance;
- parole/fait;
- provenance/source;
- information insuffisante et abstention;
- interprétation sociale non omnisciente;
- instruction hostile incluse dans le dialogue/données;
- sortie structurée;
- contrastes et reformulations métamorphiques;
- cas hors distribution;
- suite générale hors RIC pour détecter une rigidification.

Mesurer les erreurs par capacité plutôt qu’un score unique opaque.

### L3 — dataset SFT

Commencer petit et propre. La taille du dataset n’est pas un objectif en soi.

Règles :

- train / validation / test séparés;
- diversité de noms, espèces, situations et formulations;
- exemples positifs et contrastifs;
- aucun cas réservé du benchmark final dans le train;
- provenance de chaque exemple;
- exemples ajoutés pour corriger une déficience mesurée, pas pour « remplir » le dataset.

### L4 — entraînement QLoRA

Première option à tester compte tenu des 16 Go de VRAM : SFT + QLoRA 4-bit, modèle de base gelé, un adaptateur.

Les valeurs de rang, alpha, dropout, modules ciblés, longueur de contexte, batch/accumulation, learning rate et initialisation sont des **hyperparamètres expérimentaux**, pas des décisions fixées par ce dossier. Les recettes officielles servent de point de départ seulement.

### L5 — évaluation aveugle base vs adapté

À contexte et contrat identiques, comparer :

```text
modèle de base
vs
modèle de base + RIC-LoRA
```

Mesures prioritaires :

- violations d’invariant;
- faits/provenances inventés;
- sortie invalide;
- abstention correcte et abstention excessive;
- surinterprétation;
- sensibilité aux reformulations;
- résistance à l’instruction hostile dans les données;
- régressions générales;
- latence/mémoire/stabilité.

### L6 — porte d’intégration runtime

Un essai runtime n’est autorisable qu’après :

- gain reproductible sur des cas non vus;
- absence de fuite du benchmark;
- régressions acceptables;
- provenance observable `base model + adapter + version`;
- rollback démontré vers le modèle de base;
- audit architectural Codex du chargement, lifecycle et observabilité réels;
- arrivée du chantier à son tour dans la roadmap;
- décision produit explicite.

## 8. Falsification de l’idée LoRA

L’hypothèse « LoRA utile à RIC » doit être rejetée ou différée si :

- le gain disparaît hors du dataset;
- le modèle devient plus rigide ou plus omniscient;
- la baisse d’erreurs vient principalement d’une abstention quasi permanente;
- les capacités générales se dégradent de façon inacceptable;
- la maintenance/versioning devient disproportionnée;
- les mêmes gains sont obtenus plus simplement et plus robustement par le contrat, le contexte, le prompt ou un meilleur modèle de base.

**Ne pas créer un LoRA parce que la technique est disponible.** Son adoption doit acheter un comportement discriminable et utile.

## 9. Relation avec les chantiers existants

- **P0 Memory** : aucune modification du modèle pendant sa qualification.
- **Conversation State** : doit d’abord rendre la continuité conversationnelle explicite; ne pas apprendre cette continuité implicitement dans les poids.
- **BOL** : doit produire des opportunités comportementales explicites; ne pas apprendre une table cachée motif→activité.
- **P3.5** : doit stabiliser la frontière perception/action/affordance qui conditionne ce que le LLM peut légitimement recevoir et proposer.
- **SCC-1B** : fournit déjà des principes et bancs utiles pour provenance, abstention, robustesse pragmatique et prompt injection; réutiliser plutôt que dupliquer.

## 10. Gouvernance par décision

- **SCI/TECH** — choix des capacités à tester et validité du benchmark comportemental.
- **MIXED** — frontière entre discipline apprenable et état/autorité qui doit rester explicite dans RIC.
- **TECH** — pipeline QLoRA, compatibilité AMD, runtime, hotswap, versioning, provenance et rollback.
- **PRODUCT** — décision finale d’adopter ou non un adaptateur et de modifier une baseline de qualification.

Codex demeure autorité sur l’architecture réelle. Ce dossier ne prescrit ni package, ni classe, ni table, ni runtime particulier.
