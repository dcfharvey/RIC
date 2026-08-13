# Roadmap active — du moteur au Vivarium MVP

**Version :** 1.5
**Mise à jour :** 13 août 2026
**Statut :** trajectoire opérationnelle. Elle remplace l'ordre immédiat des
anciennes feuilles de route historiques, sans effacer leur valeur documentaire.

> **Mise au point prioritaire — WO90 fermé (13 août 2026) :** préparation du bootstrap Rodage V2 **FERMÉE**. Version `0.2.0a2`, schéma 56, migration `0056_location_plan.sql`, FUNCTIONAL_HEAD `989188fb01087878a581bd51f861014a82554a20`. Validation complète : **1033 passed, 1 skipped, 0 failed en 236,58 s**; skip attendu `tests/test_dev_bridge.py:59`. WO89 reste fermé; WO90 qualifie la topologie externe générique, le sommeil dans tout lieu canonique accessible, les plans de retour et le bootstrap T0 jetable. Aucun ancien SQLite n'a été migré et aucune histoire officielle Rodage V2 n'a commencé. **Prochain jalon immédiat : construction du vrai T0 neuf et démarrage explicite du Rodage V2 après décision du propriétaire.** Les photographies techniques antérieures ci-dessous restent historiques lorsqu'elles contredisent ce bloc.

## Principe de conduite

Chaque capacité importante doit avoir un moyen reproductible d'être mise en
situation, observée et comparée **avant** de contaminer le monde MVP. Le banc
d'essai n'est donc pas une interface de fin de projet : c'est une couche de
validation du moteur qui croît avec lui.

Avant de concevoir un nouveau système vivant, cognitif, social ou physique,
une revue de la littérature scientifique ou technique appropriée est requise.
Elle doit distinguer ce qui est robuste, ce qui demeure débattu et ce qui est
un choix d'ingénierie du Vivarium; les sources et limites doivent être consignées
dans le document de lot. Une intuition utile peut ouvrir une piste, jamais
tenir lieu de fondation. Cette règle applique DEC-036.

La routine `docs/35_ROUTINE_AUDIT_SILENCIEUX.md` est une porte de qualité
complémentaire : elle recherche les écarts entre état, journal, audits, banc,
tests et documentation après un lot à conséquences étendues.

## État actuel

**Version logicielle actuelle :** `0.2.0a2` — schéma de code 56, migration
`0056_location_plan.sql`, FUNCTIONAL_HEAD
`989188fb01087878a581bd51f861014a82554a20`, validation complète **1033 passed,
1 skipped, 0 failed en 236,58 s**. WO89 et WO90 sont fermés; le bootstrap T0
jetable est qualifié. Aucun ancien SQLite n'a été migré et aucune histoire
officielle Rodage V2 n'a commencé.

- moteur déterministe, journal canonique, transactions et audits : livrés ;
- contrats/personnages versionnés, ressources et effets déclaratifs : livrés ;
- premiers changements administratifs préparés (renommage, ajout de passage) :
  livrés ;
- cinq résidentes MVP et leur contexte d'arrivée : assemblables atomiquement
  dans le monde d'intégration ;
- objets portables, installations fixes, contenance objet‑dans‑objet et
  possession par personnage : livrés; équipement, liquides et formes restent
  futurs ;
- presets de lieux et connecteurs versionnés : livrés; leur instanciation
  propre par blueprint est livrée; les connecteurs à état simple sont livrés;
  la traversée validée initiale est livrée; le monde d'intégration devient le
  prochain jalon avant la cognition ;
- règles standard de résidence installables hors du seed technique : livrées;
  la calibration déclarative de Chuu et l'arrivée initiale commune à la boîte
  aux lettres sont définies; l'instanciation réelle peut être préparée ;
- contrat fermé moteur–cognition v2, perception factuelle locale, attention
  déterministe et première trace subjective : livrés; relations et décision
  sociale restent futures ;
- SCC-0 : encodage privé idempotent des paroles sociales depuis leur source
  persistante; SCC-1A : interprétations sociales privées, bornées et révisables,
  sans LLM ni raccordement runtime ;
- SCC-1B2A : banc de calibration/falsification jetable livré avec 30 IDs,
  31 variantes déclarées, 27 fixtures T0 vérifiées, cas deferred explicites et
  smoke T1 borné; campagne T2a réelle exécutée en deux segments (105 appels
  génériques + 10 appels pairés B15/B16), sans admission cognitive ; SCC-1B2C
  ajoute l'outillage d'inventaire et Screen-47 multi-modèles, sans campagne
  comparative exécutée ;
- première frontière LLM locale LM Studio : livrée, avec contexte borné,
  réponse JSON validée, admission événementielle append-only et routeur de
  source perceptible; l'action reste soumise au moteur. La première boucle
  autonome choisit maintenant une activité à chaque nouvel `idle`; les
  intentions longues et la planification multi-étapes restent futures ;
- première disposition de personnalité canonique : livrée (Big Five,
  attachement général, versions de gabarits immuables); valeurs, conception de
  soi, réputation, relations et émotions restent futurs ;
- croyances subjectives initiales : livrées partiellement (source privée,
  preuve, révision auditée et contexte LLM v2); hypothèses concurrentes,
  modèles de source et contradictions gérées restent futurs ;
- affect subjectif initial : livré partiellement (humeur, épisodes causés,
  résolution auditée et contexte LLM v3); dynamique, expression et régulation
  restent futurs ;
- social initial : livré partiellement (relations directionnelles sourcées,
  limites et permissions explicites, contexte LLM v4); réparation, réseau,
  consentement opérationnel et actes sociaux restent futurs ;
- premier orchestrateur : livré pour les événements directs perceptibles,
  avec snapshot borné, curseur persistant et dégradation LLM; déclencheurs de
  scènes, intentions et réflexion restent futurs ;
- premier tour social LLM : livré pour une scène active et co-localisée,
  avec admission technique, schéma propre, validation de destinataire et acte
  append-only; sa sélection automatique par l'orchestrateur reste future ;
- banc social multi-tours : livré, avec occasions de parole alternées,
  déterministes et bornées dans un monde jetable; il ne remplace pas encore
  le déclenchement autonome d'une scène ;
- boucle alpha : livrée. Les options de traversée visibles sont revérifiées par
  le moteur, les rencontres canoniques ouvrent des scènes bornées, le contexte
  initial commun peut amorcer une première rencontre, et le runtime local
  persistant offre le contrôle opérateur; voir `docs/58_MVP_ALPHA_0_1_0A1.md` ;
- banc d'essai minimal : livré (`vivarium.bench`), avant ces systèmes subjectifs.
- porte de prévol MVP : livrée (`mvp-preflight`) pour inspecter une base candidate
  sans écriture ni appel LLM; elle ne remplace ni les scénarios vivants ni les
  contrôles opérateur qui restent à raccorder.

## Jalons de version produit

| Version | Place dans la roadmap | Signification |
| --- | --- | --- |
| `0.2.0a1` | Atteint | Base alpha du Rodage V2 : physiologie active owner-backed H/φ/P, observabilité opérateur et bootstrap T0 neuf qualifiés; histoire officielle non encore démarrée. |
| `0.2.0a2` | Atteint | Bootstrap WO90 : topologie externe générique, sommeil dans tout lieu canonique accessible, plans de retour et T0 jetable complet qualifiés; histoire officielle non encore démarrée. |
| `0.0.0.dev0` | État actuel | Pré-alpha : fondations rigoureuses, mais pas encore de boucle sociale complète. |
| `0.0.1.dev0` | Jalon atteint après le banc minimal | Les interactions du moteur peuvent être mises en situation et comparées de façon reproductible. |
| `0.0.2.dev0` | État actuel, après le monde d'intégration | Les cinq vraies configurations peuvent être assemblées et réinitialisées sans histoire officielle. |
| `0.1.0a1` | Atteint | **Premier MVP alpha** : boucle sociale minimale complète et présentable, encore réinitialisable. |
| `0.1.0a2` | Atteint | Correctif d'observation et d'arrivée : le tableau se rafraîchit, et l'occasion initiale de traversée est bornée et validée. |
| `0.1.0a3` | Atteint | Cadence runtime sans écritures intermédiaires, rencontre unique pendant une attente commune et filtre de lecture du bruit de journal. |
| `0.1.0a4` | Atteint | Le runtime ne transmet plus de plafond de sortie à LM Studio; le modèle suit sa configuration locale. |
| `0.1.0a5` | Atteint | Un nouvel `idle` ouvre une décision autonome unique parmi des activités canoniquement disponibles; le moteur exécute ou refuse atomiquement. |
| `0.1.0a6` | Atteint | La latence LLM ne peut plus désordonner le journal; une proposition issue d'un contexte devenu périmé est refusée sans écriture. |
| `0.1.0b1` | Après essais prolongés | Bêta : le MVP tourne durablement; les défauts restants sont recherchés par observation réelle. |
| `1.0.0` | Lancement | Usage normal et persistance suffisamment fiables pour que l'histoire compte durablement. |

Les suffixes suivent la convention Python/PEP 440 : `dev0` = développement,
`a1` = alpha 1 et `b1` = bêta 1. Un jalon est publié seulement lorsque ses
critères sont réellement atteints, jamais parce qu'un calendrier l'exige.

## Ordre de travail

La trajectoire détaillée jusqu'aux premiers systèmes cognitifs est dans
`docs/21_TRAJECTOIRE_VERS_COGNITION.md`. Elle fixe les portes de qualité :
blueprint, connecteurs à état, traversée validée, monde d'intégration, puis
contrat moteur–cognition, perception, état interne, mémoire, social et LLM.

### 1. Sûreté de l'univers administratif — fermeture de passage livrée

La fermeture de passage détecte maintenant l'isolement dans les deux sens du
graphe et suit le protocole préparé. Les premiers lieux/objets attendent encore
un cas concret; aucune suppression ne doit devenir une voie rapide. Voir
`docs/17_PLAN_LOT_4_2L_FERMETURE_PASSAGE.md`.

### 2. Banc d'essai minimal du moteur — livré

Construire un outil sans LLM et sans interface graphique qui :

- crée une base isolée et temporaire à partir d'un scénario déclaratif ;
- fixe l'horloge, le monde initial et les actions injectées ;
- exécute le moteur jusqu'à une borne choisie ;
- produit un rapport lisible, le digest d'état, les événements et les refus ;
- compare deux exécutions identiques ou deux variantes ;
- ne modifie jamais une base MVP ou un monde de développement existant.

La première version est un outil pour l'IA et les tests automatisés. Voir
`docs/16_BANC_ESSAI_MOTEUR.md`. Une interface d'exploration humaine pourra
venir ensuite, si elle répond à une friction observée.

### 3. Scénarios d'acceptation inter-systèmes

Ajouter progressivement des situations de référence : passage ouvert/fermé,
ressource qui bloque une capacité, blessure et trajet, pause/reprise,
intervention admin et redémarrage. Chaque nouveau système devra fournir ses
propres scénarios reproductibles avant d'être activé dans le monde MVP.

### 4. Monde d'intégration pré-MVP propre — livré

Une base séparée de tout monde technique construit la résidence et
instancier Sophie, Erika, Luna, Chuu et Patoune par les gestionnaires réels, avec
une validation rapide du propriétaire sur leurs fiches détaillées. Ce monde
d'intégration permet de tester les vraies configurations sans transformer des
bugs précoces en histoire officielle. Les téléphones initiaux sont maintenant
portés par leurs propriétaires; l'équipement et la buanderie restent des lots
ultérieurs.

### 5. Couches vivantes puis MVP présentable

Ajouter ces couches dans cet ordre, avec le banc d'essai comme critère de sortie
de chaque lot. Le LLM n'entre qu'après le contrat moteur–LLM, avec sorties
structurées, validation et coût borné. Le **MVP** est atteint seulement lorsque
le simulateur social est suffisamment cohérent, stable et lisible pour être
présenté : il ne se confond pas avec le simple monde d'intégration. Ce jalon
correspond à `0.1.0a1`, pas à une date arbitraire.

### Addendum opérationnel — Hugin / Munin V0

Le read-model lecture seule Hugin/Munin est livré sur le schéma 44. Il expose
des rapports structurés bornés: Hugin pour les faits canoniques établis et les
actes de parole, Munin pour les états subjectifs explicitement demandés et
effectivement persistés. Aucun rapport n’est persisté, aucun LLM n’accède à la
base, et aucune requête ne produit de conséquence. Une interface narrative LLM,
une UI complète et les extensions de mémoire restent différées.

### Addendum opérationnel — console de rodage Hugin / Munin V0.1

Une console locale temporaire est maintenant disponible sur `/observer`. Elle
consomme le read-model sans SQL dans le transport et fournit le focus canonique
`current_state` ainsi qu’un planner naturel déterministe très borné. Les
contrôles structurés restent la voie fiable; aucune narration LLM, détection
d’anomalies ou interface finale n’est engagée.

### Addendum opérationnel — rodage vivant et instrumentation diagnostique

Le rodage vivant est en cours. Le burn-in nocturne a réussi techniquement; il a
révélé deux défauts de classe A, les retries cognitifs et le polling excessif de
l’autonomie, corrigés dans `da30d5d` (`fix: bound cognitive retry storms`) et
contre-vérifiés. Deux signaux de classe C restent ouverts : la répétition
dialogique et les sorties SCC-2A `invalid_appraisal` dont la réponse provider
brute n’était pas conservée.

Le prochain jalon est une instrumentation diagnostique locale, optionnelle et
bornée, puis un burn-in court. Aucun nouveau mécanisme cognitif ni changement
de contrat n’est décidé par ce jalon.

## Frontières explicites

- Les tests unitaires actuels restent la preuve des règles locales.
- Le banc d'essai prouve les interactions de systèmes et les "what if".
- Le monde MVP est une histoire persistante, jamais une poubelle de test.
- Un test emergent intéressant n'est pas une règle : il doit être reproduit,
  expliqué et décidé avant de devenir du canon.
## État à vérifier après le lot SCC-1B

La migration `0040_scc1b_interpretation_only.sql` porte le schéma SCC-1B à 40. Le provider actif produit uniquement `schema_version`, `understanding_status` et `meaning_hypotheses`. Le raccordement SCC-1C vivant est décrit par l'état courant ci-dessous.

État courant vérifié après ce jalon : les migrations forward-only
`0041_scc1c_admission.sql`, `0042_social_interpretation_call_trigger.sql` et
`0043_scc2a_appraisal.sql` et `0044_scc3a_affect_owner.sql`
portent le schéma à 44. Le raccordement événementiel SCC-0 -> SCC-1C -> SCC-1B
est livré dans le runtime social; SCC-2A ajoute un appraisal privé et SCC-3A
examine exclusivement les candidates affect, avec arrêt avant les autres domaines. Les retries
techniques restent bornés et l'attribution imbriquée reste explicitement
reportée après son échec structurel en R&D.
