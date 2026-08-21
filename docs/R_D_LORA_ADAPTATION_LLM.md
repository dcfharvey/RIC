# R&D — Adaptation PEFT/LoRA du fournisseur LLM de RIC

**Version R&D :** 0.1  
**Date :** 21 août 2026  
**Statut :** dossier initial consolidé — expérimentation hors runtime autorisable; aucune intégration runtime autorisée par ce document  
**Autorités :** ChatGPT = R&D fonctionnelle/technique; Grok = contre-audit adversarial si demandé; Codex = architecture réelle, pipeline d'entraînement/intégration, tests et ordre d'implantation; propriétaire = décision produit finale.

## 0. Verdict exécutif

L'usage d'un adaptateur LoRA/QLoRA est **techniquement plausible et fonctionnellement pertinent à tester** pour RIC, mais son utilité n'est pas encore démontrée.

La cible n'est pas de « mettre RIC dans les poids ». La cible est plus étroite : apprendre au modèle une discipline générique et stable qui est aujourd'hui rappelée par le contexte/prompt, puis vérifier si cette adaptation réduit réellement les violations de contrat sans créer d'état caché ni de régressions.

Décision expérimentale initiale :

```text
un modèle de base remplaçable
+
un seul adaptateur LoRA RIC de discipline générale
```

Pas de LoRA « conversation », « mémoire », « personnage » ou « émotion » séparé sans déficience distincte démontrée.

La R&D et les prototypes hors runtime peuvent avancer en parallèle. L'intégration runtime attend normalement la stabilisation de Conversation State, BOL et P3.5.

---

## 1. Résultats empiriques / techniques établis

### 1.1 LoRA

Le travail original LoRA (Hu et al., 2021) gèle les poids du modèle préentraîné et apprend des mises à jour de bas rang injectées dans certaines couches. Le résultat important pour RIC est qu'une adaptation peut être stockée séparément du modèle de base et entraînée avec beaucoup moins de paramètres qu'un fine-tuning complet.

Source : https://arxiv.org/abs/2106.09685

### 1.2 QLoRA

QLoRA (Dettmers et al., 2023) conserve le modèle de base gelé en quantification 4-bit et rétropropage vers des paramètres LoRA entraînables. Le papier introduit notamment NF4, double quantization et paged optimizers pour réduire l'empreinte mémoire.

Source : https://arxiv.org/abs/2305.14314

Conséquence technique raisonnable : QLoRA est le premier chemin à essayer pour un modèle de l'ordre de 14B sur une carte 16 Go. Cela ne prouve pas encore que **notre** Qwen3-14B, avec **notre** contexte et **notre** stack AMD, rentrera proprement en VRAM : ce point doit être mesuré sur la machine réelle.

### 1.3 Support Qwen3

La documentation Qwen3 fournit des chemins de fine-tuning LoRA/QLoRA via ms-swift et Axolotl, ainsi qu'un format de dataset conversationnel pour SFT.

Sources :

- https://github.com/QwenLM/Qwen3/blob/main/docs/source/training/ms_swift.md
- https://github.com/QwenLM/Qwen3/blob/main/docs/source/training/axolotl.md

### 1.4 Chargement et hotswap

PEFT/Transformers permettent de charger plusieurs adaptateurs, d'activer un adaptateur, de revenir au modèle de base et de remplacer en place les poids d'un adaptateur LoRA par un autre. Le hotswap est actuellement spécifiquement supporté pour LoRA et impose des contraintes de compatibilité, notamment sur les couches ciblées.

Sources :

- https://huggingface.co/docs/transformers/peft
- https://github.com/huggingface/peft/blob/main/docs/source/package_reference/hotswap.md

Conséquence RIC : aucun besoin de fusionner définitivement le premier adaptateur dans le modèle de base. La variante expérimentale doit rester désactivable et comparable à la baseline.

### 1.5 RX 7800 XT / ROCm / bitsandbytes

La RX 7800 XT est une RDNA3 `gfx1101`. AMD la liste dans la matrice ROCm 7.2/7.2.1 WSL2 avec PyTorch officiellement supporté. La matrice Windows native PyTorch 7.2.1 est plus restrictive et ne liste pas explicitement la RX 7800 XT, même si `gfx1101` existe dans la pile générale. Le chemin WSL2 est donc le premier environnement à qualifier pour l'entraînement.

Sources :

- https://rocm.docs.amd.com/projects/radeon-ryzen/en/docs-7.2.1/docs/compatibility/compatibilityrad/wsl/wsl_compatibility.html
- https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/windows/windows_compatibility.html

bitsandbytes publie des builds ROCm incluant `gfx1101` et annonce le support des fonctionnalités pour RDNA/CDNA; le backend AMD doit néanmoins être qualifié dans notre environnement réel avant de devenir une dépendance RIC.

Source : https://huggingface.co/docs/bitsandbytes/en/installation

---

## 2. Conclusions raisonnables mais encore incertaines

1. **QLoRA 14B sur 16 Go est plausible, pas garanti.** La longueur de séquence, l'activation checkpointing, le batch, le nombre de modules ciblés, le backend d'attention et les optimizers peuvent déplacer fortement le pic mémoire.
2. **Un LoRA peut améliorer l'adhérence aux invariants sans améliorer la cognition générale.** Le gain recherché est contractuel, pas un gain universel « d'intelligence ».
3. **Un petit dataset très propre peut être suffisant pour un changement comportemental étroit**, mais aucune taille optimale ne peut être présumée pour RIC. La taille doit être pilotée par les erreurs mesurées.
4. **Une amélioration apparente peut être un faux gain par sur-abstention.** Un modèle qui répond « information insuffisante » partout viole moins de faits mais devient moins utile.
5. **Prompt/contexte et LoRA peuvent être substituables sur certains défauts.** Si une correction de contrat explicite produit le même gain avec moins de dette et plus d'auditabilité, le LoRA n'est pas justifié.
6. **Le hot swap n'implique pas qu'il faille multiplier les adaptateurs.** C'est une capacité opérationnelle, pas une raison fonctionnelle de créer un LoRA par module conceptuel.

---

## 3. Hypothèse de modélisation RIC

Hypothèse testée :

> Une adaptation légère peut augmenter la probabilité que le LLM respecte spontanément les frontières épistémiques et les contrats génériques de RIC sous des contextes variés, tandis que tout état du monde et tout état subjectif restent explicitement fournis, persistés et validés par leurs propriétaires réels.

Cette hypothèse sera **falsifiée** si le gain disparaît hors distribution, s'il dépend de formulations mémorisées, s'il provient principalement d'une abstention excessive ou si une solution de contexte/contrat plus simple obtient le même résultat.

---

## 4. Ce que l'adaptateur peut apprendre

Cibles admissibles, car stables et génériques :

- `réalité/canon ≠ perception ≠ croyance`;
- `parole ≠ fait`;
- provenance d'une information et limites de sa source;
- distinction entre information observée, rapportée, inférée et inconnue;
- abstention ou explicitation de l'incertitude lorsque le contexte ne suffit pas;
- refus de transformer une description morphologique en capacité causale;
- `LLM propose, moteur valide`;
- respect de schémas de sortie et de vocabulaires contractuels;
- absence d'affirmation gratuite de hidden state;
- traitement du contenu du monde comme **données**, pas comme nouvelles instructions système;
- conservation des ambiguïtés lorsque plusieurs interprétations restent plausibles;
- discipline de langue/terminologie si elle ne remplace pas un état dynamique.

---

## 5. Ce que l'adaptateur ne doit pas apprendre comme état caché

Interdit comme cible de spécialisation :

- faits actuels du monde;
- localisation, inventaire, physiologie ou état d'activité;
- souvenirs individuels;
- croyances individuelles actuelles;
- relations, permissions et consentements;
- état courant d'une conversation;
- buts/intentions en cours;
- personnalité propre à Sophie, Erika, Luna, Chuu, Patoune ou un futur agent;
- règles `personnage → comportement`;
- catalogue causal de règles physiques/métier qui appartient au moteur;
- « Chuu a besoin de X » ou tout autre correctif de cas particulier;
- réponses exactes du benchmark servant à qualifier l'adaptateur.

Invariant ajouté au dossier :

```text
état dynamique explicite
≠
poids du modèle
```

Un changement de casting, de monde ou de mémoire ne doit pas exiger de réentraîner l'adaptateur général.

---

## 6. Un seul adaptateur au départ

Le premier candidat est un **RIC General Discipline LoRA**.

Raisons :

- permet une comparaison simple base vs adapté;
- réduit le risque de routage implicite selon une taxonomie conceptuelle qui ne correspond pas au code réel;
- évite d'encoder prématurément les contrats MVP de Conversation State/BOL;
- réduit la surface de maintenance et de versionnement;
- rend les régressions plus faciles à attribuer.

Un deuxième adaptateur ne devient admissible que si :

1. une classe d'échec distincte est reproductible;
2. un seul adaptateur ne peut pas la corriger sans régression ailleurs;
3. la spécialisation ne cache pas un état qui devrait rester explicite;
4. le routage peut être justifié par un contrat fonctionnel stable.

---

## 7. Benchmark à geler avant le dataset

Le benchmark de qualification doit être construit **avant** le dataset d'entraînement et maintenu hors du train.

### Familles minimales

#### B1 — Canon / perception / croyance

Même canon, perceptions différentes; même perception, croyances différentes; absence de perception malgré présence réelle.

#### B2 — Parole / témoignage / rumeur

Une agente affirme X; le modèle doit pouvoir représenter « elle a dit X » sans produire « X est vrai ».

#### B3 — Provenance

Distinguer mémoire récupérée, perception actuelle, parole d'autrui, inférence, donnée technique et information inconnue.

#### B4 — Incertitude et ambiguïté

Cas où plusieurs interprétations sont compatibles; pénaliser la sélection arbitraire d'une vérité unique.

#### B5 — Hidden-state overclaim

Descriptions comportementales compatibles avec plusieurs états privés; le modèle doit proposer des hypothèses sans les transformer en vérité psychologique.

#### B6 — Proposition / validation

Le LLM peut proposer une action; il ne doit pas déclarer lui-même qu'elle est physiquement possible ou qu'elle a produit un effet canonique non retourné par le moteur.

#### B7 — Instruction hostile dans les données

Une perception, une mémoire ou une parole contient une chaîne ressemblant à une instruction (« ignore les règles précédentes »). Elle doit rester une donnée du monde.

#### B8 — Schéma de sortie

Validité syntaxique, champs obligatoires, vocabulaires fermés lorsque le contrat l'impose, absence de champs inventés.

#### B9 — Métamorphique

Changer noms, ordre de présentation, synonymes ou détails non causaux ne doit pas inverser arbitrairement le verdict contractuel.

#### B10 — Hors domaine / régression générale

Tâches générales simples de raisonnement, français/anglais, suivi d'instruction et compréhension afin de détecter une spécialisation trop rigide.

---

## 8. Construction du dataset

### Principes

- privilégier la qualité et la diversité causale plutôt qu'un volume arbitraire;
- séparer les familles/scénarios avant le split afin d'éviter des quasi-doublons train/test;
- varier noms, espèces, lieux et formulation pour empêcher l'apprentissage du casting;
- inclure des cas positifs et négatifs proches;
- inclure des cas où **agir** est correct afin de lutter contre la sur-abstention;
- inclure des cas où l'information est suffisante, partielle ou contradictoire;
- conserver une provenance humaine/R&D claire pour chaque exemple;
- ne pas utiliser les données V3c privées comme train par défaut; les diagnostics peuvent inspirer des scénarios synthétiques sans recopier l'état historique comme vérité générale.

### Taille initiale

Aucune taille scientifique n'est prescrite. Choix d'ingénierie proposé pour le pilote : commencer par quelques centaines d'exemples très contrôlés, mesurer les erreurs, puis ajouter seulement les cas nécessaires aux faiblesses observées.

Le dataset ne doit pas grandir pour « faire sérieux ».

---

## 9. Programme expérimental

### L0 — Qualification de la stack matérielle

Objectif : répondre seulement à « pouvons-nous entraîner et recharger proprement un adaptateur sur cette machine ? »

- environnement préféré initial : WSL2 + ROCm officiellement compatible avec RX 7800 XT;
- vérifier PyTorch ROCm, visibilité GPU et opérations de base;
- vérifier bitsandbytes 4-bit/NF4 sur `gfx1101`;
- micro-dataset synthétique non RIC;
- sauvegarde/rechargement d'un adaptateur;
- mesurer VRAM, RAM, temps/itération et stabilité;
- aucun changement runtime RIC.

Verdict : `FEASIBLE`, `FEASIBLE WITH LIMITS` ou `NOT YET FEASIBLE`.

### L1 — Baseline

Exécuter le benchmark gelé sur le modèle de base exact envisagé, avec paramètres d'inférence contrôlés et versionnés.

### L2 — SFT/QLoRA pilote

Premier essai : SFT supervisé. Aucun DPO/GRPO avant preuve qu'un problème de préférence subsiste après SFT.

Variables à explorer par petites ablations, pas comme dogmes :

- rank LoRA;
- alpha;
- modules ciblés;
- longueur de séquence;
- learning rate;
- nombre d'epochs;
- gradient accumulation/checkpointing;
- quantification et compute dtype réellement supportés par la stack AMD.

### L3 — Évaluation aveugle base vs LoRA

Même entrées, même contrat, même décodage autant que possible.

Mesurer au minimum :

- violations d'invariant;
- faits/provenances inventés;
- invalidité de schéma;
- mauvaise abstention;
- sur-abstention;
- hidden-state overclaim;
- vulnérabilité aux instructions présentes dans les données;
- sensibilité aux reformulations;
- régressions hors domaine.

### L4 — Robustesse

- prompts reformulés;
- noms/espèces nouveaux;
- scénarios plus longs;
- contradictions;
- contexte partiellement manquant;
- cas adversariaux;
- si possible, répétitions sur plusieurs seeds/ordres pour distinguer gain stable et accident de décodage.

### L5 — Porte d'intégration runtime

Aucune intégration avant :

1. gain reproductible et utile sur benchmark réservé;
2. absence de fuite benchmark/dataset;
3. pas de régression majeure ni de sur-abstention;
4. possibilité de revenir au modèle de base;
5. provenance observable `base_model + adapter_id/version`;
6. audit Codex du fournisseur réel, du chargement et du cycle de déploiement;
7. contrats Conversation State, BOL et P3.5 suffisamment stabilisés;
8. décision produit explicite.

---

## 10. Critères de falsification

L'hypothèse « LoRA utile à RIC » est rejetée ou différée si :

- le gain n'existe que sur des formulations proches du train;
- les violations diminuent uniquement parce que le modèle refuse/abstient presque toujours;
- le modèle devient plus certain sur des hidden states;
- les sorties structurées régressent;
- le modèle généraliste perd une capacité importante;
- le modèle adapté apprend des noms/personnages au lieu des relations causales;
- un simple changement de contexte/prompt produit le même bénéfice de façon plus robuste et auditable;
- la stack AMD est trop fragile pour une maintenance raisonnable et le bénéfice ne justifie pas cette dette.

---

## 11. Séquençage RIC

```text
maintenant : L0/L1 + benchmark + dataset design hors runtime

P0 Memory
→ Conversation State minimal
→ BOL
→ P3.5
→ réévaluation du benchmark sur contrats stabilisés
→ L2-L4 finalisés
→ porte d'intégration LoRA
→ extensions cognitives suivantes
```

Le prototype peut donc précéder P3.5; **le LoRA produit** ne doit pas figer les contrats MVP appelés à changer.

---

## 12. Questions ouvertes à conserver

- Quel modèle de base doit servir de cible long terme? Qwen3-14B reste une baseline actuelle, pas une dépendance irrévocable.
- Quel niveau de gain justifie la dette d'un adaptateur?
- Quel format de versionnement relie dataset, code d'entraînement, modèle de base et adaptateur?
- Quelle part des invariants peut être retirée du prompt après adaptation sans dégrader la falsifiabilité?
- Faut-il garder l'adaptateur non fusionné en production? Préférence R&D : oui pour les premiers cycles; décision technique finale à Codex.
- Quel backend AMD sera réellement stable sur la machine : WSL2 ROCm/bitsandbytes, autre pipeline compatible, ou entraînement ponctuel ailleurs?
- Un jour, une spécialisation distincte serait-elle utile? Réponse par défaut : non jusqu'à preuve contraire.

---

## 13. Gouvernance de décision

Chaque décision future doit indiquer son autorité dominante :

- **SCI/TECH** : ce que les méthodes LoRA/QLoRA établissent réellement et leurs limites;
- **MIXED** : frontière entre discipline apprise et état explicite RIC;
- **TECH** : pipeline matériel, formats d'adaptateur, chargement, hotswap, observabilité, rollback, tests;
- **PRODUCT** : acceptation finale du compromis qualité/complexité et choix d'en faire une baseline runtime.

Le présent dossier ne prescrit aucune classe, table, service, package ou migration au code réel.
