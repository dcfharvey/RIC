# R&D — Adaptation PEFT/LoRA du fournisseur LLM RIC

**Version R&D :** 0.3  
**Date :** 21 août 2026  
**Statut :** R&D technique et fonctionnelle ouverte — benchmark spécifié; prototype hors runtime autorisable; aucune intégration runtime autorisée par ce document

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

## 3. Audit des mécanismes d’évaluation déjà présents dans RIC

L’objectif est de réutiliser les contrats et preuves existants plutôt que créer un deuxième système d’autorité.

### 3.1 `src/vivarium/bench.py`

Le banc principal actuel est déterministe et volontairement sans LLM. Il vérifie notamment la reproductibilité et l’intégrité canonique du moteur.

**Conclusion :** ne pas le détourner pour noter un LoRA. Il reste un garde-fou de non-régression du moteur autour d’expériences LLM, pas le benchmark comportemental de l’adaptateur.

### 3.2 SCC-1B et provider d’interprétation sociale

Le dépôt possède déjà des contrats directement réutilisables comme familles de falsification :

- contexte subjectif owner-scoped;
- sélection explicite de traces;
- sortie JSON stricte;
- `clear / ambiguous / unresolved` avec cohérence sémantique;
- absence de conséquence canonique du provider;
- provenance modèle + recette + fingerprint de snapshot;
- séparation données du monde / instructions système;
- rejet de champs supplémentaires;
- prompt injection comme donnée non fiable;
- replay/conflit et audit de provenance.

Les tests `tests/test_social_interpretation_provider.py` et les dossiers SCC-1B doivent donc fournir des **patterns de capacités**, pas être copiés mot pour mot dans le dataset d’entraînement.

### 3.3 Cognition générale

`CognitionDecision` impose déjà une sortie structurée bornée et `LMStudioProvider` limite la décision aux actions explicitement proposées par le moteur. `CognitionProviderTrace` conserve actuellement l’identité du modèle et la requête/réponse technique.

Cela fournit deux autres familles de benchmark :

- discipline de sortie/action;
- résistance à l’invention d’options, destinations ou faits.

### 3.4 Conséquence sur la provenance d’un futur adaptateur

Aujourd’hui, la provenance technique distingue le modèle de base configuré et, selon le provider, la version de recette/contrat. Aucun adaptateur n’existe encore, donc aucune identité d’adaptateur n’est requise aujourd’hui.

Si un LoRA est un jour activé, une qualification doit pouvoir distinguer sans ambiguïté :

```text
base seule
≠
base + adaptateur A version X
≠
base + adaptateur B version Y
```

Exigence fonctionnelle de porte : **l’état effectif du provider doit identifier l’adaptation active de façon audit-able et persistable lorsque la preuve le requiert**. La forme technique — champ séparé, identité de modèle effective, manifeste, fingerprint ou autre — relève de Codex.

## 4. Invariants RIC appliqués au fine-tuning

```text
réalité/canon ≠ perception ≠ croyance
parole ≠ fait
relation ≠ permission ≠ consentement
LLM propose, moteur valide
provenance d’audit ≠ source subjectivement mémorisée
état dynamique ≠ poids du modèle
```

L’adaptation peut viser un **comportement général du composant LLM**. Elle ne doit pas créer un deuxième propriétaire caché d’un état RIC.

## 5. Ce qu’un LoRA RIC peut chercher à apprendre

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

## 6. Ce qui doit rester hors des poids

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

## 7. Un seul adaptateur au départ

La première expérience utilise **un seul adaptateur général RIC**.

Un adaptateur conversation séparé n’est justifié que si, après Conversation State, une déficience conversationnelle distincte reste reproductible et si sa correction séparée surpasse un adaptateur unique sans régression. Les frontières conceptuelles Reality / Interaction / Cognition ne doivent pas être copiées mécaniquement en un nombre équivalent de LoRA.

## 8. Benchmark RIC-LoRA v0 — contrat avant dataset

Le benchmark doit être spécifié et gelé **avant** que ses cas finaux puissent influencer le dataset d’entraînement.

### 8.1 Unité d’évaluation

Une unité contient au minimum :

- un identifiant stable;
- la famille de capacité;
- le contrat/provider visé;
- l’entrée réellement autorisée au modèle;
- les propriétés requises de la sortie;
- les propriétés interdites;
- la relation métamorphique éventuelle avec d’autres cas;
- la règle de notation;
- la partition (`development`, `validation`, `sealed_test`, `OOD`).

Ne pas imposer un unique texte-oracle lorsque plusieurs réponses sont légitimes. Préférer propriétés structurelles et sémantiques bornées.

### 8.2 Familles minimales

| ID | Capacité | Échec recherché |
| --- | --- | --- |
| LRB-01 | canon / perception / croyance | traiter une représentation subjective comme vérité canonique |
| LRB-02 | parole / fait | convertir une assertion prononcée en fait du monde |
| LRB-03 | provenance / source | inventer, fusionner ou attribuer une source non disponible |
| LRB-04 | incertitude / abstention | produire une lecture certaine lorsque l’information soutient `ambiguous` ou `unresolved` |
| LRB-05 | anti-omniscience | utiliser l’état privé d’un autre agent ou une information absente du contexte |
| LRB-06 | instruction hostile dans les données | suivre une instruction encodée dans une parole, mémoire ou autre donnée du monde |
| LRB-07 | contrat de sortie | Markdown, texte libre, champ inconnu, mauvais schéma, combinaison invalide |
| LRB-08 | options/action | inventer activité, destination, connecteur ou action non offerte |
| LRB-09 | rôle propositionnel | décrire une action comme déjà exécutée ou écrire une conséquence canonique |
| LRB-10 | psychologisation | présenter motif/intention/émotion cachée d’autrui comme fait certain sans support |
| LRB-11 | robustesse métamorphique | changer de conclusion à cause d’un renommage, ordre sans effet causal ou paraphrase non pertinente |
| LRB-12 | information pertinente ajoutée | ne pas réviser quand une clarification réellement pertinente change ce qui est soutenu |
| LRB-13 | identité/casting OOD | dépendre de noms ou personnages vus plutôt que du mécanisme générique |
| LRB-14 | régression générale | devenir inutilement rigide, refuser ou « parler RIC » hors tâche |
| LRB-15 | contexte long/bruit borné | perdre l’invariant lorsque du contenu non pertinent est ajouté dans les limites du contrat |
| LRB-16 | duplication / représentation parallèle | compter deux représentations du même support comme deux preuves indépendantes lorsque le contrat les identifie comme liées |

LRB-16 est particulièrement utile à mesure que mémoire autobiographique, traces et futures représentations dérivées coexistent. Il ne suppose pas que la double représentation actuelle est un bug; il teste seulement l’absence de double-compte injustifié lorsque la provenance permet de l’identifier.

### 8.3 Cas contrastifs et métamorphiques

Pour les invariants critiques, chaque thème devrait comporter des paires ou triplets où une seule variable causale change :

- même phrase, mais entendue vs non accessible;
- même assertion, mais perception directe du fait ajoutée;
- même contenu, locutrice différente avec provenance différente;
- même snapshot, noms des personnages remplacés;
- même information, formulation FR ↔ paraphrase FR;
- même contenu hostile, placé comme donnée du monde vs véritable instruction système;
- même ambiguïté, puis ajout d’une clarification pertinente;
- même action désirée, option absente vs explicitement offerte.

Une adaptation utile doit répondre à la différence causale, pas aux tokens superficiels.

### 8.4 Partitions et anti-fuite

Séparation recommandée fonctionnellement :

```text
development
→ cas visibles servant à développer le harness et les règles de score

validation
→ cas utilisés pour choisir hyperparamètres / dataset / checkpoints

sealed_test
→ cas gelés avant dataset et jamais utilisés pour corriger l’entraînement

OOD
→ mécanismes équivalents avec nouveaux noms, espèces, structures et formulations
```

La proportion exacte relève du volume final. Le principe de séparation est obligatoire; un `80/10/10` n’est pas une loi ni une décision actuelle.

Les cas historiques déjà largement discutés — par exemple le carnet rouge, Chuu, Erika/gaming — peuvent servir à la **development suite** ou à définir une capacité, mais ne doivent pas constituer à eux seuls le `sealed_test` puisqu’ils sont déjà connus pendant la conception.

### 8.5 Notation

Ne pas réduire la sélection à une moyenne unique.

Rapporter au minimum, par famille :

- taux de sortie structurellement valide;
- violations d’invariants critiques;
- abstentions correctes;
- abstentions excessives;
- hallucinations de source/fait/action;
- cohérence des relations métamorphiques;
- régressions OOD/générales;
- latence et empreinte lorsque pertinentes.

Une **violation critique** (`canon`, omniscience, action inventée, instruction hostile suivie) peut être une condition de veto même si la moyenne globale s’améliore. Les seuils chiffrés d’adoption seront fixés après mesure de la baseline, pas inventés avant.

### 8.6 Répétitions et variance

Pour un modèle non strictement déterministe, répéter les cas suffisamment pour distinguer une amélioration stable d’un tirage favorable. Conserver recette, paramètres, seed lorsqu’il existe, version du modèle et identité effective de l’adaptateur.

Ne pas interpréter `même seed` comme garantie universelle de déterminisme si le backend, les kernels ou la recette changent.

## 9. Méthode expérimentale

### L0 — baseline avant entraînement

Avant de créer le dataset :

1. sélectionner le modèle de base exact, sa quantification/runtime et son contrat;
2. matérialiser le benchmark selon §8;
3. geler `sealed_test` et OOD;
4. mesurer la baseline vanilla;
5. conserver les sorties brutes et la provenance nécessaire au contre-audit.

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

### L2 — dataset SFT

Commencer petit et propre. La taille du dataset n’est pas un objectif en soi.

Règles :

- train / validation / test séparés;
- diversité de noms, espèces, situations et formulations;
- exemples positifs et contrastifs;
- aucun cas réservé du benchmark final dans le train;
- provenance de chaque exemple;
- exemples ajoutés pour corriger une déficience mesurée, pas pour « remplir » le dataset;
- ne pas dériver automatiquement les réponses d’entraînement d’une sortie actuelle du modèle de base : la cible doit être vérifiée selon le contrat RIC.

### L3 — entraînement QLoRA

Première option à tester compte tenu des 16 Go de VRAM : SFT + QLoRA 4-bit, modèle de base gelé, un adaptateur.

Les valeurs de rang, alpha, dropout, modules ciblés, longueur de contexte, batch/accumulation, learning rate et initialisation sont des **hyperparamètres expérimentaux**, pas des décisions fixées par ce dossier. Les recettes officielles servent de point de départ seulement.

### L4 — évaluation aveugle base vs adapté

À contexte et contrat identiques, comparer :

```text
modèle de base
vs
modèle de base + RIC-LoRA
```

L’évaluation finale utilise `sealed_test` et OOD sans modifier ensuite le candidat sur la base de ces résultats. Si l’on réentraîne après inspection du sealed test, cette partition devient de facto une validation et une **nouvelle** partition finale doit être créée.

### L5 — contre-audit

Avant adoption, faire relire :

- les familles de benchmark;
- les exclusions du dataset;
- les violations classées critiques;
- les cas où un « gain » provient simplement d’une abstention excessive;
- les éventuelles regressions générales.

Grok peut servir de contre-audit adversarial comportemental/scientifique; Codex audite la reproductibilité et l’intégration technique réelle.

### L6 — porte d’intégration runtime

Un essai runtime n’est autorisable qu’après :

- gain reproductible sur des cas non vus;
- absence de fuite du benchmark;
- régressions acceptables;
- provenance observable `base model + adapter + version` ou identité effective équivalente non ambiguë;
- rollback démontré vers le modèle de base;
- audit architectural Codex du chargement, lifecycle et observabilité réels;
- arrivée du chantier à son tour dans la roadmap;
- décision produit explicite.

## 10. Falsification de l’idée LoRA

L’hypothèse « LoRA utile à RIC » doit être rejetée ou différée si :

- le gain disparaît hors du dataset;
- le modèle devient plus rigide ou plus omniscient;
- la baisse d’erreurs vient principalement d’une abstention quasi permanente;
- les capacités générales se dégradent de façon inacceptable;
- la maintenance/versioning devient disproportionnée;
- les mêmes gains sont obtenus plus simplement et plus robustement par le contrat, le contexte, le prompt ou un meilleur modèle de base.

**Ne pas créer un LoRA parce que la technique est disponible.** Son adoption doit acheter un comportement discriminable et utile.

## 11. Relation avec les chantiers existants

- **P0 Memory** : aucune modification du modèle pendant sa qualification.
- **Conversation State** : doit d’abord rendre la continuité conversationnelle explicite; ne pas apprendre cette continuité implicitement dans les poids.
- **BOL** : doit produire des opportunités comportementales explicites; ne pas apprendre une table cachée motif→activité.
- **P3.5** : doit stabiliser la frontière perception/action/affordance qui conditionne ce que le LLM peut légitimement recevoir et proposer.
- **SCC-1B** : fournit déjà des principes et patterns de banc pour provenance, abstention, robustesse pragmatique et prompt injection; réutiliser les capacités sans contaminer le sealed test par simple copie des cas historiques.
- **bench canonique** : garde de non-régression déterministe du moteur, séparé du score comportemental LLM.

## 12. Gouvernance par décision

- **SCI/TECH** — choix des capacités à tester, règles de score, validité du benchmark comportemental et analyse de variance.
- **MIXED** — frontière entre discipline apprenable et état/autorité qui doit rester explicite dans RIC.
- **TECH** — pipeline QLoRA, compatibilité AMD, harness exécutable, runtime, hotswap, versioning, provenance, reproductibilité et rollback.
- **PRODUCT** — décision finale d’adopter ou non un adaptateur et de modifier une baseline de qualification.

Codex demeure autorité sur l’architecture réelle. Ce dossier ne prescrit ni package, ni classe, ni table, ni runtime particulier.
