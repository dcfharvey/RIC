# R&D — Adaptation PEFT/LoRA du fournisseur LLM RIC

**Version R&D :** 0.4  
**Date :** 21 août 2026  
**Statut :** R&D technique et fonctionnelle ouverte — benchmark spécifié et fondé dans la littérature; prototype hors runtime autorisable; aucune intégration runtime autorisée par ce document

## 1. Question de recherche

Un adaptateur PEFT/LoRA peut-il améliorer de façon reproductible la discipline RIC d’un modèle de base sans encoder d’état dynamique, sans réduire indûment ses capacités générales et sans déplacer vers les poids une autorité qui appartient au moteur ?

Ce chantier est transverse : benchmark, dataset et prototypes hors runtime peuvent être préparés pendant que la roadmap fonctionnelle progresse. La porte normale d’intégration runtime reste après Conversation State minimal, BOL et P3.5.

Le but n’est pas de « rendre Qwen plus RIC » comme propriété vague. Le but est de tester des améliorations comportementales précises, falsifiables et transférables.

## 2. Résultats empiriques et techniques pertinents

Cette section rapporte les résultats des sources. Les conséquences RIC sont séparées plus bas.

### 2.1 LoRA — efficacité paramétrique démontrée, équivalence non universelle

Hu et al. (2021/2022) introduisent LoRA : les poids préentraînés restent gelés et des matrices de bas rang entraînables représentent l’adaptation. Sur les tâches et modèles étudiés, LoRA réduit fortement le nombre de paramètres entraînables et l’usage mémoire tout en atteignant une qualité comparable ou parfois supérieure au full fine-tuning.

Source primaire : Hu et al., *LoRA: Low-Rank Adaptation of Large Language Models*, arXiv:2106.09685 — https://arxiv.org/abs/2106.09685

Ce résultat établit la viabilité de l’adaptation de bas rang. Il n’établit pas que tout domaine ou toute tâche peut être appris aussi bien qu’en full fine-tuning.

### 2.2 QLoRA — entraînement d’adaptateurs à travers un modèle 4-bit gelé

Dettmers et al. (2023) montrent qu’un modèle de base quantifié 4-bit et gelé peut servir de support à l’entraînement d’adaptateurs LoRA. QLoRA introduit notamment NF4, double quantization et paged optimizers. Les auteurs obtiennent de fortes performances d’instruction tuning avec des coûts mémoire réduits et rapportent qu’un petit dataset de haute qualité peut être très efficace dans leur cadre.

Ils soulignent aussi que les benchmarks de chatbot utilisés à l’époque peuvent être peu fiables pour estimer la qualité réelle.

Source primaire : Dettmers et al., *QLoRA: Efficient Finetuning of Quantized LLMs*, arXiv:2305.14314 — https://arxiv.org/abs/2305.14314

### 2.3 LoRA peut apprendre moins tout en oubliant moins

Biderman et al. (2024) comparent LoRA et full fine-tuning en programmation et mathématiques, en instruction fine-tuning et continued pretraining. Dans leurs réglages low-rank standards, LoRA apprend moins bien le domaine cible que le full fine-tuning, mais conserve mieux les capacités hors domaine du modèle de base. Les auteurs observent aussi que les perturbations apprises par full fine-tuning ont un rang effectif beaucoup plus élevé que les configurations LoRA habituelles.

Source primaire : Biderman et al., *LoRA Learns Less and Forgets Less*, arXiv:2405.09673 — https://arxiv.org/abs/2405.09673

### 2.4 Même performance cible ≠ même solution ni même généralisation

Shuttleworth et al. (2024) montrent que LoRA et full fine-tuning peuvent obtenir des performances similaires sur la tâche adaptée tout en apprenant des modifications structurellement différentes et en se comportant différemment hors distribution. Ils décrivent des « intruder dimensions » dans certaines adaptations LoRA et montrent que des variantes de rang plus élevé/rank-stabilized peuvent mieux ressembler au full fine-tuning dans leurs expériences.

Source primaire : Shuttleworth et al., *LoRA vs Full Fine-tuning: An Illusion of Equivalence*, arXiv:2410.21228 — https://arxiv.org/abs/2410.21228

### 2.5 Variantes LoRA : gains possibles, pas justification automatique

Liu et al. (2024) proposent DoRA, qui décompose magnitude et direction et utilise LoRA pour la composante directionnelle. Dans leurs tâches, DoRA améliore capacité d’apprentissage et stabilité par rapport à LoRA.

Source primaire : Liu et al., *DoRA: Weight-Decomposed Low-Rank Adaptation*, arXiv:2402.09353 — https://arxiv.org/abs/2402.09353

Ce résultat justifie DoRA comme candidat de comparaison si vanilla LoRA montre une limite. Il ne justifie pas de complexifier le premier essai RIC.

### 2.6 Hyperparamètres : les conclusions peuvent changer avec le tuning

Un préprint récent de Lee et al. (2026) réévalue plusieurs variantes LoRA avec recherche d’hyperparamètres et rapporte que des différences attribuées aux méthodes se réduisent fortement lorsque le learning rate propre à chacune est correctement réglé. Le résultat doit être traité comme littérature récente à confirmer, mais il renforce un principe expérimental classique : ne pas déclarer une variante supérieure à partir d’une seule recette fixe.

Source : Lee et al., *Learning Rate Matters: Vanilla LoRA May Suffice for LLM Fine-tuning*, arXiv:2602.04998 — https://arxiv.org/abs/2602.04998

### 2.7 SFT versus preference optimization

Les études de preference alignment montrent des effets dépendant du modèle, du dataset, de la quantité de données et de la méthode; elles ne soutiennent pas une règle universelle « DPO > SFT ». Pour RIC, aucune preuve actuelle ne montre qu’un objectif de préférence soit nécessaire pour apprendre les contrats visés.

Référence indicative : Thakkar et al. (2024), *A Deep Dive into the Trade-Offs of Parameter-Efficient Preference Alignment Techniques*, arXiv:2406.04879 — https://arxiv.org/abs/2406.04879

## 3. Conclusions raisonnables mais incertaines pour RIC

Les résultats ci-dessus soutiennent les conclusions prudentes suivantes :

1. un LoRA/QLoRA est une voie techniquement crédible pour adapter un LLM sans full fine-tuning;
2. son utilité comportementale pour RIC reste à démontrer;
3. une amélioration in-distribution ne garantit ni maintien des capacités générales ni bonne généralisation OOD;
4. le rang, le learning rate, les modules ciblés et la recette d’entraînement peuvent modifier fortement le verdict;
5. un petit dataset très propre est un point de départ raisonnable, pas une loi sur la taille optimale;
6. vanilla LoRA/QLoRA + SFT est le meilleur contrôle initial parce qu’il est simple et directement falsifiable;
7. DoRA, DPO ou d’autres variantes ne deviennent pertinentes qu’en réponse à une déficience démontrée;
8. le benchmark et sa séparation du dataset sont aussi importants que l’algorithme d’entraînement.

## 4. Hypothèse de modélisation RIC

L’hypothèse testée est :

> Une adaptation légère peut augmenter la probabilité qu’un LLM respecte spontanément des frontières et contrats généraux de RIC, tandis que tout état canonique ou subjectif dynamique reste fourni, possédé et validé par les composants compétents.

Cette hypothèse sera rejetée si les gains ne généralisent pas ou s’ils sont obtenus au prix d’une rigidification, d’une abstention excessive ou d’une perte générale disproportionnée.

## 5. Faisabilité technique actuelle

### 5.1 Qwen3

La documentation officielle Qwen3 fournit des recettes SFT avec LoRA et mentionne explicitement LoRA, QLoRA et DoRA via ms-swift. Elle documente aussi les datasets conversationnels `messages` et des recettes ciblant les couches linéaires.

Source : https://github.com/QwenLM/Qwen3/blob/main/docs/source/training/ms_swift.md

Cela démontre que la famille Qwen3 est techniquement adaptable. Cela ne démontre pas qu’un LoRA améliore RIC.

### 5.2 PEFT et hotswap

Hugging Face PEFT permet de charger, activer et remplacer des adaptateurs. Son mécanisme de hotswap peut remplacer en place un adaptateur compatible sans recharger le modèle de base. Les contraintes exactes dépendent de la configuration et du runtime; RIC ne doit donc pas présumer que tout backend possède le même lifecycle.

Sources :

- https://huggingface.co/docs/peft/main/conceptual_guides/lora
- https://huggingface.co/docs/transformers/peft
- https://huggingface.co/docs/peft/package_reference/hotswap

### 5.3 Matériel AMD cible

La Radeon RX 7800 XT (`gfx1101`, 16 Go) figure dans les matrices de support ROCm actuelles, notamment Linux et WSL selon les versions documentées. Les outils de quantification ont aussi progressé sur ROCm.

Sources :

- https://rocm.docs.amd.com/projects/install-on-linux/en/docs-7.2.2/reference/system-requirements.html
- https://rocm.docs.amd.com/projects/radeon-ryzen/en/docs-7.2.1/docs/compatibility/compatibilityrad/wsl/wsl_compatibility.html
- https://huggingface.co/docs/bitsandbytes/installation

**Conclusion technique prudente :** QLoRA sur le poste cible est plausible mais non qualifié. Les combinaisons exactes PyTorch/ROCm/bitsandbytes, kernels, longueur de contexte, VRAM/RAM, vitesse et stabilité doivent être mesurées sur la machine réelle.

Le dépôt produit ne dépend actuellement d’aucun package PEFT/TRL/bitsandbytes : `pyproject.toml` ne contient que pytest comme dépendance optionnelle de développement. Aucun ajout de dépendance n’est autorisé par ce dossier.

## 6. Invariants appliqués au fine-tuning

```text
réalité/canon ≠ perception ≠ croyance
parole ≠ fait
relation ≠ permission ≠ consentement
LLM propose, moteur valide
provenance d’audit ≠ source subjectivement mémorisée
état dynamique ≠ poids du modèle
```

L’adaptation peut viser un comportement général. Elle ne doit pas créer un deuxième propriétaire caché d’un état RIC.

## 7. Ce qu’un LoRA RIC peut chercher à apprendre

Cibles candidates :

- respecter canon / perception / croyance;
- traiter une parole comme une parole plutôt que comme un fait;
- conserver provenance et incertitude pertinentes;
- produire `unresolved` / abstention lorsque la conclusion n’est pas soutenue;
- éviter psychologisation et hidden-state claims présentés comme certains;
- respecter les schémas de sortie et le rôle propositionnel du LLM;
- résister à une instruction hostile présente dans les données du monde;
- conserver une terminologie opérationnelle stable lorsqu’un contrat l’exige.

## 8. Ce qui doit rester hors des poids

Ne pas entraîner comme vérité persistante :

- faits du monde, localisation, inventaire, physiologie ou état canonique actuel;
- souvenirs individuels;
- relations, permissions ou consentements actuels;
- personnalité/biographie d’un personnage lorsqu’elles doivent venir du contexte;
- Conversation State courant;
- opportunités BOL courantes;
- règles physiques, affordances et validation moteur;
- scripts `personnage → comportement`;
- réponses des benchmarks finaux réservés à l’évaluation.

Un LoRA qui « connaît » Luna, Chuu ou Sophie n’est pas automatiquement un meilleur LoRA RIC. Le comportement recherché doit transférer vers des identités et situations non vues.

## 9. Un seul adaptateur au départ

La première expérience utilise **un seul adaptateur général RIC**.

Un adaptateur conversation séparé n’est justifié que si, après Conversation State, une déficience conversationnelle distincte reste reproductible et si sa correction séparée surpasse un adaptateur unique sans régression.

Les frontières conceptuelles Reality / Interaction / Cognition ne doivent pas être copiées mécaniquement en trois LoRA.

## 10. Audit des mécanismes d’évaluation déjà présents

### 10.1 `src/vivarium/bench.py`

Le banc principal actuel est déterministe et volontairement sans LLM. Il vérifie la reproductibilité et l’intégrité canonique du moteur.

**Choix d’ingénierie :** ne pas le détourner pour noter un LoRA. Il reste un garde-fou de non-régression moteur autour d’expériences LLM.

### 10.2 SCC-1B

Le provider et ses tests fournissent déjà des patterns de falsification utiles :

- contexte subjectif owner-scoped;
- sélection explicite de traces;
- sortie JSON stricte;
- `clear / ambiguous / unresolved` avec cohérence sémantique;
- aucune conséquence canonique du provider;
- provenance modèle + recette + fingerprint de snapshot;
- séparation données du monde / instructions système;
- rejet de champs supplémentaires;
- prompt injection comme donnée non fiable;
- replay/conflit et audit de provenance.

Les tests `tests/test_social_interpretation_provider.py` et les dossiers SCC-1B doivent fournir des **patterns de capacités**, pas être copiés mot pour mot dans le dataset d’entraînement.

### 10.3 Cognition générale

`CognitionDecision` impose déjà une sortie structurée bornée et `LMStudioProvider` limite la décision aux actions explicitement proposées par le moteur. `CognitionProviderTrace` conserve l’identité du modèle et la requête/réponse technique.

Cela fournit deux familles supplémentaires : discipline de sortie/action et résistance à l’invention d’options/destinations/faits.

### 10.4 Provenance future de l’adaptateur

Aujourd’hui, les traces distinguent le modèle de base et, selon le provider, la version de recette/contrat. Aucun adaptateur n’existe encore, donc aucune identité d’adaptateur n’est requise.

Si un LoRA est activé, une qualification doit pouvoir distinguer sans ambiguïté :

```text
base seule
≠ base + adaptateur A version X
≠ base + adaptateur B version Y
```

**Exigence fonctionnelle de porte :** l’état effectif du provider doit identifier l’adaptation active de façon auditable et persistable lorsque la preuve le requiert. La représentation technique — champ séparé, identité effective, manifeste, fingerprint ou autre — relève de Codex.

## 11. Benchmark RIC-LoRA v0 — contrat avant dataset

Le benchmark doit être spécifié et gelé **avant** que ses cas finaux puissent influencer le dataset d’entraînement.

### 11.1 Unité d’évaluation

Une unité contient au minimum :

- identifiant stable;
- famille de capacité;
- contrat/provider visé;
- entrée réellement autorisée au modèle;
- propriétés requises de la sortie;
- propriétés interdites;
- relation métamorphique éventuelle;
- règle de notation;
- partition (`development`, `validation`, `sealed_test`, `OOD`).

Ne pas imposer un texte-oracle unique lorsque plusieurs réponses sont légitimes. Préférer propriétés structurelles et sémantiques bornées.

### 11.2 Familles minimales

| ID | Capacité | Échec recherché |
| --- | --- | --- |
| LRB-01 | canon / perception / croyance | traiter une représentation subjective comme vérité canonique |
| LRB-02 | parole / fait | convertir une assertion prononcée en fait du monde |
| LRB-03 | provenance / source | inventer, fusionner ou attribuer une source non disponible |
| LRB-04 | incertitude / abstention | produire une lecture certaine quand `ambiguous` ou `unresolved` est mieux soutenu |
| LRB-05 | anti-omniscience | utiliser l’état privé d’un autre agent ou une information absente |
| LRB-06 | instruction hostile dans les données | suivre une instruction encodée dans parole/mémoire/donnée du monde |
| LRB-07 | contrat de sortie | Markdown, texte libre, champ inconnu, mauvais schéma, combinaison invalide |
| LRB-08 | options/action | inventer activité, destination, connecteur ou action non offerte |
| LRB-09 | rôle propositionnel | décrire une action comme exécutée ou écrire une conséquence canonique |
| LRB-10 | psychologisation | présenter motif/intention/émotion cachée d’autrui comme fait sans support |
| LRB-11 | robustesse métamorphique | changer à cause d’un renommage, ordre sans effet causal ou paraphrase non pertinente |
| LRB-12 | information pertinente ajoutée | ne pas réviser quand une clarification change réellement ce qui est soutenu |
| LRB-13 | identité/casting OOD | dépendre de noms/personnages vus plutôt que du mécanisme générique |
| LRB-14 | régression générale | devenir inutilement rigide, refuser ou « parler RIC » hors tâche |
| LRB-15 | contexte long/bruit borné | perdre l’invariant avec contenu non pertinent ajouté dans les limites du contrat |
| LRB-16 | duplication/provenance | compter deux représentations liées comme deux preuves indépendantes lorsque leur lien est explicite |

LRB-16 ne suppose pas que la double représentation mémoire actuelle soit un bug. Il teste seulement l’absence de double-compte injustifié lorsque la provenance permet d’identifier le lien.

### 11.3 Cas contrastifs et métamorphiques

Pour les invariants critiques, utiliser des paires/triplets où une seule variable causale change :

- même phrase, entendue vs non accessible;
- même assertion, mais perception directe du fait ajoutée;
- même contenu, source différente;
- même snapshot, noms remplacés;
- même information, paraphrase FR;
- même contenu hostile comme donnée du monde vs vraie instruction système;
- même ambiguïté, puis clarification pertinente;
- même action désirée, option absente vs offerte.

Une adaptation utile doit répondre à la différence causale, pas aux tokens superficiels.

### 11.4 Partitions et anti-fuite

```text
development
→ cas visibles pour développer harness et règles de score

validation
→ cas pour choisir dataset, hyperparamètres et checkpoint

sealed_test
→ cas gelés avant dataset, jamais utilisés pour corriger l’entraînement

OOD
→ mécanismes équivalents avec nouveaux noms, espèces, structures et formulations
```

La proportion exacte dépendra du volume. Le principe de séparation est obligatoire; `80/10/10` n’est pas une loi.

Les cas historiques déjà discutés — carnet rouge, Chuu, Erika/gaming — peuvent servir à la development suite ou définir une capacité, mais ne doivent pas constituer à eux seuls le sealed test.

### 11.5 Notation

Ne pas réduire la sélection à une moyenne unique.

Rapporter par famille :

- taux de sortie structurellement valide;
- violations d’invariants critiques;
- abstentions correctes;
- abstentions excessives;
- hallucinations de source/fait/action;
- cohérence métamorphique;
- régressions OOD/générales;
- latence et empreinte lorsque pertinentes.

Une violation critique — canon, omniscience, action inventée, instruction hostile suivie — peut servir de veto même si une moyenne globale monte. Les seuils chiffrés d’adoption seront fixés après mesure de la baseline.

### 11.6 Répétitions et variance

Pour un modèle non strictement déterministe, répéter les cas suffisamment pour distinguer une amélioration stable d’un tirage favorable. Conserver recette, paramètres, seed lorsqu’il existe, version modèle et identité effective de l’adaptateur.

Même seed n’est pas une garantie universelle de déterminisme si backend, kernels ou recette changent.

## 12. Méthode expérimentale

### L0 — baseline avant entraînement

1. sélectionner modèle de base exact, quantification/runtime et contrat;
2. matérialiser le benchmark;
3. geler `sealed_test` et OOD;
4. mesurer baseline vanilla;
5. conserver sorties brutes et provenance nécessaire au contre-audit.

### L1 — faisabilité technique hors runtime

Smoke-test sur micro-dataset artificiel :

- chargement du modèle quantifié;
- création du LoRA;
- quelques étapes SFT;
- sauvegarde/rechargement;
- base vs base+LoRA;
- activation/désactivation ou hotswap si disponible;
- VRAM/RAM, vitesse et stabilité.

Verdict : `FEASIBLE`, `FEASIBLE WITH LIMITS` ou `NOT YET FEASIBLE`.

Cette étape ne touche aucune DB RIC persistante et n’autorise aucun changement de provider de qualification.

### L2 — dataset SFT

Commencer petit et propre. La taille n’est pas un objectif en soi.

Règles :

- train / validation séparés du test final;
- diversité de noms, espèces, situations et formulations;
- exemples positifs et contrastifs;
- aucune fuite du sealed test;
- provenance de chaque exemple;
- exemples ajoutés en réponse à une déficience mesurée;
- ne pas générer automatiquement les cibles depuis la sortie actuelle du modèle de base : la cible doit être vérifiée selon le contrat RIC.

### L3 — entraînement QLoRA/SFT

Premier candidat : SFT + QLoRA 4-bit, modèle de base gelé, un adaptateur.

Les valeurs de rang, alpha, dropout, modules ciblés, longueur de contexte, batch/accumulation, learning rate et initialisation sont des hyperparamètres expérimentaux.

Le premier protocole doit comparer au moins plusieurs combinaisons rang/learning rate assez différentes pour éviter de conclure sur une recette unique. Le nombre exact relève du budget technique mesuré.

DoRA/DPO ne sont pas inclus par défaut. Ils deviennent des branches d’expérience seulement si vanilla LoRA/SFT laisse une déficience utile et reproductible.

### L4 — évaluation aveugle

Comparer à contexte/contrat identiques :

```text
modèle de base
vs modèle de base + RIC-LoRA
```

L’évaluation finale utilise `sealed_test` et OOD sans modifier ensuite le candidat sur la base de ces résultats. Si le sealed test est inspecté pour réentraîner, il devient validation et une nouvelle partition finale doit être créée.

### L5 — contre-audit

Avant adoption :

- Grok : contre-audit comportemental/scientifique des familles, exclusions et interprétations;
- Codex : reproductibilité, pipeline, dépendances, provenance, chargement/hotswap, rollback et intégration réelle.

### L6 — porte d’intégration runtime

Un essai runtime n’est autorisable qu’après :

- gain reproductible sur cas non vus;
- absence de fuite du benchmark;
- régressions acceptables;
- provenance non ambiguë de l’état effectif `base + adaptation`;
- rollback démontré vers base seule;
- audit architectural Codex;
- arrivée du chantier à son tour dans la roadmap;
- décision produit explicite.

## 13. Falsification de l’idée LoRA

Rejeter ou différer si :

- le gain disparaît hors dataset;
- le modèle devient plus rigide ou omniscient;
- la baisse d’erreurs vient surtout d’une abstention quasi permanente;
- les capacités générales se dégradent de façon inacceptable;
- le résultat est trop sensible à une recette fragile;
- la maintenance/versioning devient disproportionnée;
- le gain est obtenu plus simplement par contrat, contexte, prompt ou meilleur modèle de base.

**Ne pas adopter LoRA parce que la technique est disponible. Il doit acheter un comportement utile, mesurable et généralisable.**

## 14. Relation avec les chantiers existants

- **P0 Memory** : aucune modification du modèle pendant sa qualification.
- **Conversation State** : continuité explicite avant toute tentative de l’apprendre implicitement.
- **BOL** : opportunités explicites; aucune table cachée motif→activité dans les poids.
- **P3.5** : stabilise la frontière perception/action/affordance conditionnant les entrées légitimes.
- **SCC-1B** : fournit des patterns de benchmark pour provenance, abstention, pragmatique et prompt injection sans contaminer le sealed test par simple copie.
- **bench canonique** : garde de non-régression moteur, séparé du score comportemental LLM.

## 15. Gouvernance par décision

- **SCI/TECH** — capacités, règles de score, validité du benchmark et analyse de variance.
- **MIXED** — frontière entre discipline apprenable et état/autorité restant explicite.
- **TECH** — pipeline QLoRA, compatibilité AMD, harness exécutable, hyperparamètres, runtime, hotswap, versioning, provenance, reproductibilité et rollback.
- **PRODUCT** — adoption ou rejet de l’adaptateur et éventuel changement de baseline de qualification.

Codex demeure autorité sur l’architecture réelle. Ce dossier ne prescrit ni package, ni classe, ni table, ni runtime particulier.
