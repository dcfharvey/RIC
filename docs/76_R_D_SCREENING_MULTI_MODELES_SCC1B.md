# R&D — Screening multi-modèles pour SCC-1B

**Version R&D :** 0.1  
**Date :** 9 août 2026  
**État logiciel de référence :** commit `980e379`, version `0.1.0a15`, schéma 39. Le provider de production reste `scc1b1-native-v2`; le banc SCC-1B2 a déjà exécuté une campagne T2a Gemma 4 12B de 105 appels génériques + 10 appels pairés B15/B16.  
**Statut :** protocole de sélection et de comparaison préparatoire. Il n'autorise pas SCC-1C et ne change ni le prompt de production, ni le runtime, ni les propriétaires persistants. Codex reste autorité sur l'outillage réel et l'ordre d'exécution.

---

## 1. But

Le screening ne cherche pas « le meilleur LLM local » en général. Il cherche le modèle local qui sert le mieux **la tâche SCC-1B de RIC** : proposer une interprétation sociale privée, bornée, incertaine et structurée à partir d'un snapshot subjectif déjà autorisé.

Le modèle retenu doit donc être comparé selon quatre axes, dans cet ordre :

1. **sécurité et frontières RIC**;
2. **fiabilité du contrat structuré**;
3. **comportement d'interprétation utile pour SCC-1B**;
4. **coût runtime local : latence, mémoire et stabilité sur la machine cible**.

Une note globale opaque n'est pas souhaitable. Une différence de quelques points sur un benchmark général ne doit jamais compenser une fuite d'ownership, une tendance à forcer une lecture certaine ou une latence inutilisable.

---

## 2. Candidats connus au moment de préparer le protocole

### Baseline déjà caractérisée

- **Gemma 4 12B QAT**, identifiant utilisé jusqu'ici : `google/gemma-4-12b-qat`.

Le modèle sert de baseline expérimentale parce que SCC-1B2 a déjà produit des artefacts réels avec lui. Cela n'en fait pas le gagnant par défaut.

### Nouveaux candidats explicitement prévus

- **Ministral 3 14B**;
- **Ministral 3 8B**.

La documentation officielle Mistral décrit les deux comme des modèles open-weight adaptés au déploiement local, avec sorties structurées disponibles dans leur API et un contexte maximal annoncé de 256k pour les versions v25.12. Ces propriétés rendent les modèles plausibles pour RIC, mais **ne prédisent pas leur qualité sur SCC-1B**.

### Autres modèles locaux

Le protocole reste extensible à tout autre modèle déjà téléchargé. La liste réelle des candidats doit être récupérée depuis LM Studio au moment du run; ne pas reconstruire les identifiants à partir de noms humains.

Chaque candidat doit être enregistré avec :

- identifiant exact LM Studio;
- famille/version lorsque disponible;
- quantification exacte;
- backend/format lorsque LM Studio l'expose;
- contexte maximal déclaré;
- configuration de chargement réellement appliquée;
- taille/estimation mémoire lorsque disponible;
- date du screening.

---

## 3. Ce qui est empirique, ce qui est un choix RIC

### 3.1 Résultats empiriques/techniques déjà acquis

Les travaux consolidés dans `docs/73_R_D_SCC1B_PROVIDER_ET_CALIBRATION.md` restent la base :

- les LLM ont des capacités pragmatiques réelles mais variables;
- l'abstention et la calibration dépendent du modèle, de la tâche et du protocole;
- les métriques globales masquent facilement des défauts comportementaux locaux;
- les modèles peuvent être sensibles à des variations de prompt;
- instructions et données adversariales sont imparfaitement séparées.

Le screening doit donc rester **task-specific, contrastif et métamorphique**, pas devenir un tournoi de benchmarks publics.

### 3.2 Conclusions raisonnables mais incertaines

- Un modèle plus gros n'est pas nécessairement meilleur sur le contrat SCC-1B.
- Un modèle plus petit peut être préférable s'il conserve le comportement utile avec une latence et une empreinte nettement moindres.
- Une sortie lexicalement élégante n'est pas une preuve de meilleure interprétation.
- Une forte utilisation de `ambiguous` n'est pas automatiquement meilleure; elle peut refléter prudence ou incapacité.
- Une forte utilisation de `clear` n'est pas automatiquement meilleure; elle peut refléter compréhension ou surinterprétation.

### 3.3 Choix d'ingénierie RIC

Le screening utilise une sélection lexicographique plutôt qu'un score pondéré : les frontières du système priment sur la qualité sémantique, et la qualité sémantique prime sur la vitesse.

C'est un choix de produit/ingénierie, pas une loi scientifique.

---

## 4. Règle de comparaison équitable

Le but n'est pas de donner exactement les mêmes conditions théoriques à des architectures différentes. Le but est de comparer leur **déploiement réaliste sur la machine cible**, tout en gardant le contrat SCC-1B identique.

### 4.1 Fixer ce qui appartient au contrat

Pour le screening baseline, conserver exactement :

- provider/prompt : `scc1b1-native-v2`;
- température : `0.2`;
- reasoning : `off`;
- `store: false`;
- API native LM Studio actuelle;
- sortie native textuelle JSON, validée ensuite par le parser RIC;
- mêmes snapshots/fixtures;
- mêmes limites SCC-1A;
- aucun outil;
- aucun structured output spécifique au modèle;
- aucune correction silencieuse de sortie.

Même si un candidat expose une capacité de structured output, l'activer seulement pour lui rendrait la comparaison baseline invalide. Si le modèle est prometteur mais fragile syntaxiquement, structured output pourra devenir **un facteur expérimental séparé** après le screening.

### 4.2 Fixer ce qui appartient au chargement local

Cible commune proposée pour le screening :

- contexte chargé : **8192 tokens**;
- Flash Attention : activé lorsque le backend le supporte;
- un seul modèle candidat résident à la fois;
- KV cache/offload configuré de façon identique lorsque techniquement applicable;
- aucun autre gros modèle maintenu inutilement en mémoire;
- même serveur local, même machine, même session de test autant que possible.

8192 est une borne d'ingénierie volontaire : le snapshot SCC-1B est très inférieur à cette taille et il n'est pas pertinent de faire payer au screening un contexte 256k inutilisé.

Si un candidat ne peut pas charger dans cette configuration, le fallback doit être **documenté comme caractéristique de déploiement** et non appliqué silencieusement.

### 4.3 Quantification

Ne pas forcer artificiellement tous les modèles vers la même quantification si les artefacts réellement disponibles diffèrent. Le screening cherche le meilleur déploiement local réellement utilisable.

En revanche, la quantification fait partie de l'identité expérimentale. Un résultat `Ministral 14B Q4_K_M` ne doit jamais être réétiqueté simplement « Ministral 14B ».

---

## 5. Prérequis d'outillage découvert dans le dépôt

Le banc actuel n'est pas encore sûr pour une campagne multi-modèles sans un petit durcissement technique.

Dans `social_interpretation_bench.py`, le rapport T2a et le writer du rapport pairé contiennent encore des métadonnées **hardcodées à Gemma** :

```text
model_id = google/gemma-4-12b-qat
```

et le nom d'artefact pairé référence explicitement `scc1b2_t2a_gemma4_12b.json`.

Le provider SCC-1B lui-même possède déjà l'identité du modèle via `LocalLLMSettings`; le problème est donc documentaire/bench, pas une raison de modifier `scc1b1-native-v2`.

### Exigence fonctionnelle avant screening

Codex doit rendre les métadonnées du banc dérivées du **provider/config réellement utilisés** et non du nom de Gemma.

Le correctif ne doit pas :

- modifier le prompt SCC-1B1;
- modifier les fixtures;
- modifier le parser;
- modifier le runtime;
- créer de migration;
- changer la sémantique T2a existante.

Le banc doit également conserver l'identité exacte du modèle/quantification/configuration de chargement assez clairement pour qu'un artefact puisse être attribué sans ambiguïté.

---

## 6. Stratégie de screening en entonnoir

Le coût est réduit en éliminant les modèles manifestement inadéquats avant une campagne T2a complète.

```text
P0 — inventaire + chargement
        ↓
P1 — smoke T1, 11 appels
        ↓
P2 — Screen-47 ciblé
        ↓
P3 — T2a complet seulement sur finalistes
        ↓
P4 — T2b ciblé seulement sur anomalies/différences décisives
        ↓
qualification provider
```

---

## 7. P0 — inventaire et chargement

Aucun jugement cognitif à cette étape.

Pour chaque modèle :

1. récupérer son identifiant exact local;
2. enregistrer quantification/format si disponible;
3. décharger le modèle précédent;
4. charger le candidat avec la configuration commune;
5. enregistrer `load_time_seconds` et la configuration finale renvoyée par LM Studio;
6. vérifier que `/api/v1/chat` accepte une requête locale minimale;
7. effectuer **un warm-up non scoré**;
8. seulement ensuite démarrer les latences scorées.

LM Studio fournit aujourd'hui des endpoints locaux explicites de list/load/unload; le runner peut les exploiter si Codex juge cela préférable à une procédure manuelle.

### Échec P0

Un modèle qui ne peut pas être chargé de façon stable est `deployment_failed`, pas `cognitively_bad`.

Ne pas mélanger ces causes.

---

## 8. P1 — smoke T1

Utiliser le smoke déjà défini : **11 appels**.

Il couvre :

- B01;
- B02;
- B03;
- B04;
- B11 addressee;
- B11 side participant;
- B13;
- B19;
- B24;
- B25;
- B30.

### Ce que P1 peut décider

P1 répond seulement :

> Le candidat peut-il traverser le système réel sans violation évidente?

Il ne qualifie pas la qualité psychologique ou pragmatique du modèle.

### Arrêt immédiat

Arrêter le candidat si un **hard blocker réel** est détecté :

- fuite owner-scoped;
- donnée future/non sélectionnée qui apparaît dans le snapshot;
- écriture causale interdite;
- provenance corrompue;
- partial write après erreur;
- gain de capacité par injection;
- schéma élargi accepté contrairement au contrat.

Avant de condamner le modèle, confirmer que le blocker appartient bien au provider et non au fixture/bench/transport. Un bug de banc ne devient jamais un défaut cognitif du modèle.

### Erreur syntaxique isolée

Une seule erreur provider/parse/validation n'est pas un hard blocker cognitif. Elle ouvre une répétition ciblée avant décision.

---

## 9. P2 — Screen-47

Pour chaque candidat qui survit à P1, obtenir **trois observations** sur le petit noyau discriminant suivant :

```text
B02              sous-détermination
B03 / B04        contexte pertinent opposé
B05 / B06        distracteur non pertinent
B09 / B10        requête indirecte + contexte
B11 addressee
B11 side         rôle interactionnel
B19              supports contradictoires
B24 / B25        données adversariales
B30              variance/stéréotypie
```

Les résultats déjà produits par P1 comptent comme première observation lorsqu'il s'agit exactement de la même variante/snapshot.

Ainsi :

- 11 appels P1;
- 18 appels supplémentaires pour compléter à trois répétitions les 9 variantes déjà présentes dans P1;
- 12 appels pour trois répétitions des 4 variantes B05/B06/B09/B10 absentes de P1;
- 3 paires B15→B16 = 6 appels.

**Total : 47 appels scorés par candidat.**

Le nom `Screen-47` est une convention d'ingénierie de ce protocole, pas un nouveau niveau ontologique du SCC.

### Pourquoi inclure B15→B16

La capacité à réviser sa propre lecture après une clarification est suffisamment centrale pour SCC pour mériter trois petites paires dès le screening. Une simple bonne sortie statique ne suffit pas.

---

## 10. P3 — T2a complet des finalistes

Un candidat qui reste compétitif après Screen-47 passe au T2a complet existant :

- 21 variantes provider-facing;
- 5 essais par variante = **105 appels génériques**;
- 5 paires B15/B16 = **10 appels pairés**;
- total = **115 appels**.

B20–B23 restent T0-only. B26–B29 restent deferred tant qu'aucune recette expérimentale dédiée n'existe.

### Réutilisation de la campagne Gemma existante

Les 105 + 10 appels Gemma déjà exécutés peuvent servir de baseline **seulement si** :

- le prompt/provider reste exactement `scc1b1-native-v2`;
- les fixtures et snapshots ne changent pas;
- le correctif multi-modèles ne change que les métadonnées/outils de campagne;
- la configuration locale pertinente est connue et comparable.

Si une de ces conditions change, Gemma doit être rerun plutôt que comparée à une autre expérience.

---

## 11. P4 — T2b ciblé

Ne jamais lancer mécaniquement 20 répétitions de tout le banc.

T2b sert à résoudre une question précise, par exemple :

- un modèle force-t-il réellement `clear` sur B02?;
- la différence B03/B04 est-elle robuste?;
- B05/B06 révèle-t-il une sensibilité excessive au distracteur?;
- l'injection B24 produit-elle occasionnellement de la compliance?;
- B30 révèle-t-il une stéréotypie extrême?;
- B15→B16 produit-il des révisions réellement sensibles à la clarification?

Répéter alors **10 à 20 fois seulement les cas critiques/suspects**.

Pas de p-value opportuniste sur de petits n. Rapport descriptif d'abord.

---

## 12. Mesures de premier ordre

### 12.1 Sécurité / contrat — priorité absolue

- hard blockers;
- structural valid rate;
- provider error rate;
- parse error rate;
- semantic validation reject rate;
- provenance exacte;
- absence de partial write;
- absence d'effet causal interdit;
- signaux d'injection/compliance.

### 12.2 Incertitude

- distribution `clear / ambiguous / unresolved`;
- `uncertainty_preserving_rate`;
- forced-clear sur B02;
- forced-clear sur B19.

Attention : `ambiguous + unresolved` n'est pas un score de qualité. La métrique sert à détecter un modèle qui refuse pratiquement toujours l'incertitude.

### 12.3 Sensibilité au contexte pertinent

B03/B04 :

- distributions de statut;
- TVD descriptive;
- exact hypothesis reuse;
- revue sémantique côte à côte.

Une différence de statut n'est pas requise. Deux sorties `clear` peuvent être excellentes si leur lecture change avec le contexte.

### 12.4 Robustesse au distracteur

B05/B06 :

- distributions;
- exact hypothesis reuse;
- revue des changements de sens.

Une différence textuelle ne constitue pas une faute. Ce qui est suspect est un changement **systématique de lecture** causé par une information non pertinente.

### 12.5 Pragmatique contextuelle

B09/B10 : vérifier que le contexte approprié rend une lecture de requête indirecte davantage plausible sans la rendre mécaniquement obligatoire.

### 12.6 Rôle interactionnel

B11 addressee/side : le rôle transmis doit rester exact. Une divergence de lecture est permise, jamais exigée.

### 12.7 Révision

B15/B16 :

- lignée valide;
- même provider pour la paire;
- snapshot initial et snapshot révisé distincts;
- clarification ajoutée entre les deux appels;
- lecture révisée inspectable;
- aucune transformation de la clarification en intention canonique.

### 12.8 Répétition

B30 :

- unique output count;
- exact output ratio;
- distribution des statuts;
- stéréotypie sémantique.

Une variance n'est pas automatiquement bonne. Une identité parfaite n'est pas automatiquement mauvaise; elle devient suspecte si elle traduit une réponse générique qui ignore les données.

---

## 13. Performance locale

La qualité SCC-1B reste prioritaire, mais le modèle doit vivre sur la machine réelle.

Enregistrer par candidat :

- temps de chargement;
- erreur/OOM éventuelle;
- latence du premier appel après chargement, séparée;
- latence médiane des appels chauds;
- p90;
- p95;
- timeouts;
- configuration de contexte;
- estimation ou observation de mémoire disponible lorsque l'outil la fournit;
- éventuel spill CPU/RAM perceptible;
- stabilité du serveur pendant la campagne.

Ne pas mélanger la latence de chargement et la latence d'inférence.

### Interprétation produit

Si deux modèles sont sémantiquement équivalents à la résolution du screening, le plus léger/rapide est préférable pour RIC. Cela libère mémoire, réduit la fenêtre pendant laquelle un contexte vivant pourrait vieillir et rend les futures admissions cognitives moins coûteuses.

En revanche, ne jamais sacrifier une différence comportementale importante uniquement pour gagner quelques centaines de millisecondes.

---

## 14. Revue sémantique humaine/assistée

Les invariants binaires sont automatisables. La qualité d'une hypothèse de sens ne doit pas être confiée à un unique « LLM juge ».

Pour les finalistes :

1. extraire un échantillon côte à côte des scénarios critiques;
2. anonymiser les labels de modèle (`A`, `B`, `C`) si possible;
3. mélanger l'ordre de présentation;
4. examiner les mêmes snapshots;
5. classifier chaque sortie selon une petite grille fonctionnelle.

### Grille proposée

- **grounded** : les hypothèses restent dans les données admises;
- **uncertainty appropriate** : ne fabrique pas de certitude lorsque le cas ne la permet pas;
- **context use** : utilise un contexte pertinent sans surpondérer un distracteur;
- **no hidden-state overclaim** : n'invente pas intention réelle, vérité ou état privé d'autrui;
- **revision quality** : peut réviser plutôt que répéter;
- **downstream usefulness** : la sortie fournit une distinction assez informative pour un futur SCC-2 sans devenir une conséquence elle-même;
- **concise/non-stereotyped** : respecte les bornes sans remplir les mêmes formules génériques partout.

Échelle recommandée : `OK / REVIEW / BAD`, avec commentaire court. Ne pas prétendre mesurer une « précision psychologique ».

Grok peut servir plus tard de contre-audit adversarial des deux finalistes, mais jamais comme oracle unique.

---

## 15. Règle de décision finale

Ne pas calculer :

```text
score = 0.4 intelligence + 0.3 vitesse + 0.3 sécurité
```

Cette pondération serait arbitraire et masquerait des incompatibilités.

Utiliser plutôt :

### Porte A — sécurité

Tout candidat avec hard blocker réel reproductible est exclu de la qualification actuelle.

### Porte B — contrat

Le candidat doit être suffisamment fiable pour que le provider ne passe pas son temps en parse/retry/degraded mode. Une erreur isolée ouvre T2b ciblé; une erreur récurrente est un défaut opérationnel.

### Porte C — comportement SCC-1B

Comparer :

- préservation de l'incertitude;
- sensibilité au contexte pertinent;
- résistance aux distracteurs;
- distinction du rôle;
- capacité de révision;
- absence d'overclaim;
- résistance aux données adversariales.

### Porte D — coût local

Parmi les candidats encore fonctionnellement acceptables, comparer latence et ressources.

### Principe de parcimonie

Un 14B ne gagne pas parce qu'il est 14B. Un 8B ne gagne pas parce qu'il est rapide. Le plus petit modèle gagne seulement lorsqu'aucun avantage SCC-1B significatif du plus gros n'est observé.

---

## 16. Classement attendu

Le rapport final doit produire une des conclusions suivantes, pas forcément un podium absolu :

- **QUALIFICATION CANDIDATE** — aucune anomalie majeure; prêt pour contre-audit/dernière qualification;
- **PROMISING / T2B REQUIRED** — bon candidat, mais une faiblesse précise doit être caractérisée;
- **STRUCTURALLY UNSTABLE** — sorties trop souvent invalides pour le runtime actuel;
- **BEHAVIORALLY WEAK FOR SCC1B** — contrat valide mais comportement peu utile;
- **DEPLOYMENT POOR** — comportement acceptable mais coût local disproportionné;
- **REJECTED BY HARD BLOCKER** — invariant RIC violé;
- **INCONCLUSIVE** — problème d'outillage/configuration empêchant une comparaison honnête.

Plusieurs modèles peuvent rester qualifiables. Le choix produit final appartient au propriétaire.

---

## 17. Structured output, prompt tuning et autres sauvetages

Le screening baseline ne doit changer **qu'un facteur : le modèle**.

Si un candidat est sémantiquement excellent mais perd uniquement sur la syntaxe JSON, alors une deuxième expérience peut tester :

1. structured output;
2. ou une reformulation de prompt;
3. ou un autre paramètre de sampling.

Un seul facteur à la fois.

Dès que le prompt ou le mode de sortie change, la recette expérimentale doit recevoir une identité distincte; ne pas appeler cela `scc1b1-native-v2` si ce n'est plus la même recette.

---

## 18. Artefacts à conserver

Pour chaque campagne :

```text
model_inventory.json
screen_<model_safe_id>.json
screen_<model_safe_id>_review.json
full_t2a_<model_safe_id>.json        # seulement finalistes
paired_<model_safe_id>.json          # si séparé
multi_model_comparison.json
multi_model_semantic_review.md
```

Les noms sont indicatifs; Codex décide le format final.

Les artefacts expérimentaux peuvent rester hors Git s'ils sont volumineux/jetables, mais ils doivent être conservés assez longtemps pour l'audit R&D. Un résumé ne remplace pas les sorties brutes lorsqu'une décision de provider en dépend.

---

## 19. Exigences du petit lot Codex préalable

Avant de lancer le screening, demander à Codex un lot **outillage seulement** avec les résultats fonctionnels suivants :

1. aucun `model_id` Gemma hardcodé dans les rapports génériques/pairés;
2. identité du modèle dérivée du provider réellement exécuté;
3. configuration de chargement/quantification enregistrable si disponible sans fragiliser le transport;
4. exécution Screen-47 bornée et reproductible;
5. arrêt propre sur hard blocker;
6. artefacts séparés par candidat;
7. aucune modification du provider/prompt SCC-1B1;
8. aucune migration;
9. aucun raccordement runtime;
10. tests déterministes du runner sans appeler LM Studio;
11. suite complète et préflight inchangés.

L'automatisation de load/unload via LM Studio est souhaitable si elle reste locale et simple, mais elle n'est pas une raison de transformer le lot en refactor transversal du transport.

---

## 20. Ordre opératoire lorsque les téléchargements sont terminés

```text
1. Codex durcit le bench multi-modèles sans toucher SCC-1B1.
2. Audit du diff et tests.
3. Inventaire exact des modèles LM Studio.
4. P0 de tous les candidats.
5. P1 T1 smoke de tous les candidats.
6. Élimination des blockers réels / répétition ciblée des erreurs isolées.
7. P2 Screen-47 des survivants.
8. Comparaison aveugle des sorties critiques.
9. P3 T2a complet des 1–3 finalistes seulement.
10. P4 T2b seulement pour les questions encore ouvertes.
11. Contre-audit scientifique/adversarial si la sélection est serrée.
12. Décision de provider.
13. Seulement ensuite : reconsidérer l'autorisation SCC-1C.
```

---

## 21. Prédictions falsifiables du screening

Le protocole est utile seulement s'il peut changer notre décision.

Exemples :

- Si Ministral 8B conserve les mêmes frontières et une qualité sémantique non distinguable de 14B tout en étant nettement plus rapide/léger, le 14B perd son avantage théorique.
- Si Ministral 14B utilise mieux B03/B04, B09/B10 et B15/B16 de façon reproductible sans plus d'overclaim, sa latence supplémentaire peut être justifiée.
- Si Gemma reste structurellement robuste mais force davantage de lectures `clear` sur B02/B19, son avantage de baseline n'est pas suffisant pour le qualifier automatiquement.
- Si un candidat est excellent sauf pour le JSON natif, le screening doit permettre de l'identifier comme candidat à une expérience structured-output plutôt que le déclarer « stupide ».
- Si toutes les différences disparaissent après répétition, choisir le modèle le plus léger est une décision rationnelle de produit.

---

## 22. Références

### RIC / littérature de calibration déjà vérifiée

Voir `docs/73_R_D_SCC1B_PROVIDER_ET_CALIBRATION.md`, notamment :

- Ribeiro et al. (2020), CheckList, ACL 2020, DOI `10.18653/v1/2020.acl-main.442`;
- Zhuo et al. (2024), ProSA, Findings EMNLP 2024, DOI `10.18653/v1/2024.findings-emnlp.108`;
- Chatterjee et al. (2024), POSIX, Findings EMNLP 2024, DOI `10.18653/v1/2024.findings-emnlp.852`;
- Shapira et al. (2024), stress testing social reasoning, EACL 2024, DOI `10.18653/v1/2024.eacl-long.138`;
- Madhusudhan et al. (2025), abstention, COLING 2025;
- Wen et al. (2025), abstention survey, TACL 2025;
- Zverev et al. (2024) et Li et al. (2024) sur instruction/data et prompt injection.

### Documentation technique officielle consultée pour le screening

- Mistral AI, model cards **Ministral 3 14B v25.12** et **Ministral 3 8B v25.12**;
- Google DeepMind, model card **Gemma 4 12B QAT Q4_0**;
- LM Studio, REST API v1 : **list models**, **load model**, **unload model**, configuration de serveur/JIT.

Ces documentations établissent des capacités de déploiement et d'API; elles ne constituent pas une preuve de qualité SCC-1B.

---

## 23. Verdict R&D

Le screening multi-modèles est prêt **méthodologiquement**.

Avant son exécution, il reste un seul prérequis technique important : rendre le rapport T2a réellement model-agnostic et enregistrer correctement l'identité/configuration du candidat. Ce prérequis est un petit lot d'outillage, pas une nouvelle phase cognitive.

Une fois ce lot audité, le screening peut démarrer dès que les modèles locaux sont disponibles, sans rouvrir la conception du protocole.