# Vivarium social artificiel
## Dossier maître d’implémentation destiné à une IA programmeuse

**Version :** 0.7
**Date :** 5 août 2026
**Statut :** source normative unique du dépôt après fermeture technique de la Phase 3
**Public cible :** IA programmeuse, agent de développement ou développeur humain
**Commit de référence (Phase 3) :** `7e5459eaac5c2ad8ae8dcb53a197863575ab4914`
**Tests de référence :** 228 réussis
**Verdict de fermeture Phase 3 :** `FERMETURE APPROUVABLE`

> Ce dossier est la version consolidée v0.4. Il remplace les versions antérieures et intègre la
> direction normative post-audit. Il décrit ce qui est **implémenté**, ce qui est
> **normatif mais futur**, et ce qui est **historique**. Aucune capacité fictive
> n’est présentée comme déjà codée.

---

## 1. Statut du document

Deux catégories de classification sont distinguées et ne doivent pas être confondues.

### Nature du contenu

- **Normatif** : ce qui doit être respecté (moteur canonique seul autorité, transactions atomiques, lecture sans effet de bord, temps simulé, journal append-only, séparation vérité/perception/croyance/mémoire, confirmation des changements profonds).
- **Descriptif** : ce qui décrit l’implémentation actuelle sans être une règle éternelle (noms de classes, SQLite, nombre de modules, tables, tests, personnages techniques).
- **Historique** : pourquoi une décision a été prise, quel audit l’a motivée, quelles alternatives ont été rejetées, quel lot l’a implémentée.

### Statut de réalisation ou de décision

- **implémenté** ;
- **partiellement implémenté** ;
- **normatif futur** ;
- **supersédé** ;
- **résolu** ;
- **dette** ;
- **limite**.

Un même élément peut avoir une nature documentaire et un statut de réalisation distincts.
Exemple : nature = normative ; statut = normatif futur.

Les deux catégories sont distinguées dans chaque section. Ne pas les mélanger.

## 2. Portée et contrat de lecture

1. Lire ce dossier avant de modifier un fichier.
2. Ne pas commencer par construire le système complet ; travailler par lots approuvés.
3. Ce dossier prévaut sur les documents sources antérieurs ; les sources sont conservées pour la traçabilité.
4. Ne jamais réconcilier silencieusement deux exigences incompatibles : signaler le conflit, son impact et une recommandation.
5. Une phase ne commence pas avant la porte de qualité précédente.
6. Le modèle de langage propose ; le moteur local valide et possède la réalité du monde.
7. Une tâche n’est pas terminée sans tests, preuves, documentation et plan de retour arrière.

### 2.1 Hiérarchie documentaire

1. Ce dossier maître v0.2 et son registre de décisions v0.2.
2. Les demandes de changement approuvées et le changelog postérieurs à cette version.
3. Le code, les migrations et les tests validés, lorsqu’ils matérialisent une exigence approuvée.
4. Les documents sources et post-audit, uniquement comme historique et détail explicatif.

## 3. Glossaire bilingue

| Terme canonique | Définition | Langue |
|---|---|---|
| moteur canonique déterministe | Autorité unique d’écriture du monde ; valide et applique les faits. | FR |
| état canonique | État courant possédé par le moteur. | FR |
| temps canonique / temps simulé | Heure simulée dérivée du moteur. | FR |
| temps mural | Heure réelle d’écriture (`recorded_at`). | FR |
| événement canonique | Fait officiel immuable du journal. | FR |
| journal canonique | Journal append-only des événements. | FR |
| matérialisation | Application d’un intervalle de temps à un état dérivé. | FR |
| projection sémantique | Projection reproductible des faits significatifs du journal. | FR |
| digest | Empreinte déterministe d’état ou de journal. | FR |
| activité / besoin / blessure / régime | Concepts métier du moteur. | FR |
| arête / edge | Passage dirigé du graphe spatial. | FR/EN |
| propriétaire / administrateur / owner | Autorité administrative supérieure. | FR/EN |
| LLM / agent / personnage | Le LLM propose ; l’agent est une entité ; le personnage est une entité du monde. | FR |
| monde / résidence / vivarium | Racine du projet, habitat, projet global. | FR |
| seed / peuplement | Constantes de peuplement ; aucun RNG. | FR/EN |

Convention : **documentation en français, code/classes/événements/champs en anglais, glossaire bilingue pour les termes techniques**.

## 4. Principes d’autorité

- **Moteur canonique seul arbitre** : toute modification de l’état passe par le moteur, dans une transaction, avec sa trace canonique.
- **LLM non autoritaire** : il propose, interprète et formule ; il ne modifie ni base, ni événement, ni composant, ni capacité, ni mémoire, ni émotion, ni relation, ni permission, ni identité.
- **Séparation vérité / perception / interprétation / croyance / mémoire** : aucune couche subjective ne réécrit rétroactivement la réalité.
- **Autorité et perceptibilité indépendantes** : une intervention n’entre dans les perceptions/croyances/souvenirs d’un personnage que si elle est perceptible selon le mode et la situation.
- **Impossibilité contre transgression** : une impossibilité canonique n’est pas une règle de politique ; une norme ou valeur ne devient pas une loi physique.
- **Consentement indépendant** : aucune affection, confiance, intimité, autorité, attirance, promesse ou relation ne constitue un consentement actuel.
- **Changements profonds** : toute modification canonique profonde exige commande métier, validation en couches, rapport d’impact, plan préparé immuable, checkpoint, confirmation liée à un hash et une version, transaction atomique et audit administratif.

## 5. Architecture générale

### 5.1 Composants

| Composant | Responsabilité | Interdiction principale |
| --- | --- | --- |
| Interface Discord | Interface sociale principale. | Modifier directement le monde. |
| Interface web locale | Interface administrative (MVP). | Écrire directement dans SQLite. |
| Routeur | Identifier personnage, scène, mode du propriétaire et niveau d’autorité. | Inventer une conséquence. |
| Orchestrateur | Construire le contexte, appeler le modèle, contrôler cadence et reprise. | Contourner permissions ou invariants. |
| Moteur canonique déterministe | Temps, lieux, actions, validations, transactions, conséquences et vérité. | Accepter un fait généré sans validation. |
| Couche cognitive | Perception subjective, mémoire récupérée, intention, dialogue. | Écrire directement dans la base canonique. |
| Mémoire | Événements, perceptions, croyances, souvenirs, provenance, consolidation. | Fusionner croyance et fait. |
| Planificateur | Routines, échéances, rattrapage, consolidation, notifications. | Déclencher des appels non bornés. |
| Adaptateur de modèle | Contrat uniforme entre fournisseurs, validation de sortie, métriques. | Enfermer le métier dans une API propriétaire. |
| Persistance | SQLite, migrations, snapshots, audit et archives. | Cache/embeddings comme source unique. |
| Technicien | Diagnostic, métriques, preuves et recommandations en lecture seule. | Écrire, migrer ou déployer dans le MVP. |

### 5.2 Boucle d’exécution

Charger l’état canonique → mettre à jour besoins/routines déterministes → détecter les décisions nécessitant interprétation → construire un contexte subjectif minimal → obtenir une intention structurée → valider par le moteur → appliquer dans une transaction atomique → créer l’événement canonique → distribuer les perceptions → mettre à jour croyances/souvenirs/relations/journaux → continuer, résumer ou attendre.

### 5.3 Niveaux de détail

0 déterministe / 1 condensé / 2 décision / 3 scène / 4 réflexion (définis en v0.1, conservés).

## 6. Moteur canonique déterministe (implémenté)

- `world.py` : moteur canonique, horloge, seed, autorité d’écriture unique.
- `character.py` : personnages, position canonique, déplacement (garde C-1).
- `spatial.py` : graphe orienté, BFS, intégrité, modifications administratives atomiques.
- `needs.py` : besoins dérivés et matérialisés.
- `activities.py` : activités, régimes, transitions atomiques.
- `injury.py` : blessures, récupération, causalité.
- `policy.py` : politique déterministe pure.
- `simulation.py` : orchestration `run_to` de borne en borne.
- `repro.py` : digests et audits de reproductibilité.

Toute écriture passe par `db.transaction` + `world._append_event` (helper interne). Aucune API publique ne permet d’écrire un événement brut sans mutation métier (C-3 corrigé).

## 7. Temps et horloge (implémenté)

- Temps réel 1:1 lorsque le monde est actif : `read_canonical_time = simulated_now + (now - real_updated_at)`.
- Monde paused : `read_canonical_time = simulated_now` (gelée, aucun rattrapage en pause).
- `_advance_clock` : helper interne qui pose atomiquement `simulated_now` et `real_updated_at` dans la transaction ; réservé aux transitions temporelles du simulateur ; aucun `clock_updated` pour la progression du run.
- `set_simulated_time` : commande administrative distincte, émet `clock_updated`.
- Redémarrage : reprise depuis les ancres persistées ; délai mural actif compté exactement une fois ; délai mural ignoré en pause.
- Frontière multi-personnages : toutes les opérations utilisent le même instant canonique T ; les microsecondes murales ne sont pas du temps simulé.

## 8. Monde et espace (implémenté)

- 9 lieux initiaux : salon, cuisine, salle de bain, cour, couloir, quatre chambres.
- Graphe orienté `location_link` ; une arête dirigée = un passage ; passage bidirectionnel = deux arêtes réciproques.
- `find_path` (BFS), `can_traverse`, `has_physical_connection`, `adjacent_from`, `check_graph_integrity`.
- Déplacement arête par arête, `character_moved` par arête (`edge_count = 1`), aucune téléportation.
- Énergie : borne basse autorisée à zéro ; surcharge de blessure modérée 500 milli-énergie par arête.
- **Garde C-1** : aucun déplacement pendant une activité active (refus `CharacterError`, rollback complet).

## 9. Personnages (implémenté, provisoire)

- Quatre personnages techniques `character_1..4`, tous adultes, positions canoniques initiales en chambres 1..4.
- **Statut** : placeholders provisoires de test. Le casting MVP définitif compte cinq entités : quatre résidentes sapientes adultes (Sophie et Erika, humaines ; une louve anthro ; une slime à apparence féminine) et un chat domestique non sapient. Elles seront créées ou migrées par le futur gestionnaire d’entités (Phase 4), jamais ajoutées comme un seed spécial.
- `key` immuable ; `name` modifiable ; une seule position canonique active.

## 10. Besoins (implémenté)

- `need_state.value_milli ∈ [0, 100000]` (entier à précision fixe, aucune colonne REAL).
- Taux rationnel entier `rate_num / rate_den` (dénominateur canonique 36) ; `rate_remainder` conserve la fraction.
- Dérivation pure sans écriture ; matérialisation groupée (`needs_materialized`) avec `rate_source`, `activity_type`, `rate_nums`, `rate_dens`.
- Évolution exactement indépendante du découpage.

## 11. Activités (implémenté)

- Une seule activité active par personnage (index partiel `activity_one_active`).
- `start_activity` atomique (validation destination, prévalidation du coût, déplacements pièce par pièce, matérialisations, création, avancement d’horloge).
- `advance_to` clôture à l’heure canonique de fin puis repasse en passif ; `abort_activity` explicite.
- Régimes : `idle`, `eat`, `rest`, `clean`, `sleep` ; taux nets /36.
- Changement de régime : une seule matérialisation à la transition, ancien régime jusqu’à T, nouveau après T.

## 12. Blessures (implémenté)

- Table `injury` : sévérité entière /36, statut `active`/`healed`, une seule active par personnage, historique immuable (terminalité), causalité `UNIQUE(world_id, cause_event_seq)`.
- Récupération : régimes `passive`/`rest`/`sleep` (2/6/12 sur 36), reste rationnel, guérison exacte à zéro.
- Niveaux dérivés : `light ≤ 30000`, `moderate ≤ 60000`, `severe > 60000`.
- Effets : light = aucun coût ; moderate = surcharge 500/arête ; severe = aucun mouvement autonome, activités locales conservées.
- Frontière severe→moderate : `seconds_to_level`, politique réveillée exactement au croisement.

## 13. Politique déterministe (implémenté)

- `DeterministicPolicy` pure : aucune connexion SQLite, aucun RNG, aucune heure murale, aucune mutation.
- Ordre stable des candidats, destination déterministe, idle dynamique borné, réveil exact à la frontière de récupération.
- Aucun LLM ne participe au moteur déterministe.

## 14. Journal et causalité (implémenté)

- `canonical_event` append-only (triggers interdisant UPDATE/DELETE), séquences `UNIQUE(world_id, seq)`.
- `occurred_at` en temps canonique/simulé ; `recorded_at` mural.
- Événements : `world_created`, `world_seeded`, `character_created`, `character_moved`, `needs_materialized`, `activity_started/completed/aborted`, `scripted_accident`, `injury_occurred/materialized/healed`, `world_paused/resumed`, `clock_updated`, `world_renamed`, `link_added/removed`.
- Aucune mutation publique n’antidate le journal (C-2 corrigé).

## 15. Transactions et atomicité (implémenté)

- Toute écriture d’état et son événement canonique dans une seule transaction (`db.transaction`, `BEGIN IMMEDIATE`).
- Rollback annule état, journal et horloge.
- Aucune écriture partielle, aucun événement sans état, aucun état sans événement obligatoire.

## 16. Reproductibilité (implémenté)

- Garantie : même état initial + mêmes règles + mêmes commandes + mêmes valeurs d’horloge injectées aux mêmes points + même ordre canonique = même état et même journal sémantique.
- Objets : `raw_canonical_event_log` (A), `structural_event_audit` (B), `reproducible_semantic_projection` (C), `materialization_chain_audit` (D), `canonical_state_digest`, `max_seq`.
- Runs continu = segmenté = redémarré (mêmes valeurs `Clock.now`) ; délai mural actif compté une fois ; pause ignore le délai.

## 17. Audits et preuves (Phase 3 fermée)

```text
Phase 3 — techniquement fermée
Commit officiel : 7e5459eaac5c2ad8ae8dcb53a197863575ab4914
Tests : 228 réussis
Migrations : 8
Verdict : FERMETURE APPROUVABLE
```

Capacités prouvées : horloge canonique, monde actif/paused, redémarrage, besoins, activités, déplacements, énergie, blessures, politique, journal, reproductibilité, rollback, endurance 24 h / 7 jours, audits structurels, audits de chaînes, digests, projection sémantique.

## 18. Limites connues

- Reconstruction event-sourced complète non garantie.
- Définitions (besoins, activités) actuellement immuables.
- Absence de RNG.
- Personnages encore techniques (placeholders).
- Aucune interface administrative complète.
- Aucun LLM intégré au moteur canonique.
- Phase 4.1 déjà entamée : lectures administratives, commandes sûres, API HTTP locale et premier tableau de bord local. La Phase 4.2 a livré le registre versionné, les gabarits de personnage publiables, leur validateur structurel, leur instanciation canonique à provenance figée et le catalogue minimal de composants MVP; le pipeline de changement profond, les gestionnaires administratifs complets et les résidentes MVP restent futurs.

## 19. Dettes techniques (documentées, non bloquantes)

| ID | Description | Sévérité | Moment recommandé | Bloquante |
| --- | --- | --- | --- | --- |
| D-1 | `upgrade_dev_profiles` sans transaction explicite | mineure | Phase 4 | non |
| D-2 | `destroy_world` incomplet (activity/injury/canonical_event) | mineure | Phase 4 | non |
| D-3 | `README.md` partiellement en retard — **résolue** | résolue | — | non |
| D-4 | documentation des événements init/seed | mineure | consolidation | non |
| D-5 | absence d’outils lint/typecheck/couverture configurés | mineure | Phase 4 | non |
| D-6 | reconstruction event-sourced complète non garantie | limite assumée | — | non |
| D-7 | immutabilité actuelle des définitions | limite | si mutation future | non |

D-3 a été **résolue** par la mise à jour de `README.md` réalisée pendant la
consolidation documentaire v0.2 (fichier concerné : `README.md` ; impact résiduel :
aucun ; bloquante : non). Sa trace historique est conservée. Les autres dettes
D-1, D-2 et D-4 à D-7 restent ouvertes et non bloquantes.

## 20. Systèmes futurs (normatif futur, non implémenté)

Les systèmes suivants sont des **exigences normatives futures**, jamais présentés comme déjà implémentés : perception, croyances, motivation, personnalité, valeurs/limites, objectifs/intentions, arbitrage, mémoire, relations, émotions, ontologie, persistance avancée, administration. Le détail normatif est dans `docs/history/Vivarium_Exigences_Normatives_Post_Audit_v0_1.md` (annexe normative versionnée) et le registre des audits `docs/history/Vivarium_Registre_Audits_v0_9.md`.

## 21. Séquence vers la Phase 4

- **Phase 4 = premier vertical slice administratif** : registre minimal de composants/capacités/unités, pipeline de validation, API `prepare / validate / impact / confirm`, journal administratif, gestionnaire d’univers, gestionnaire de modèles et d’entités, interface web locale, création ou migration de la résidence et des cinq entités définitives.
- L’ancienne définition « actions, scènes, événements, perceptions » est **supersédée** dans la séquence immédiate et devient une étape ultérieure (boucle monde–action–perception).

## 22. Règles de changement

Chaque lot : portée et exclusions, inspection de l’existant, tests de référence, plan, modification minimale, tests, régression, preuves/risques/retour arrière, documentation, acceptation du propriétaire. Un lot n’est conforme que s’il ne contourne aucun invariant, déclare précisément ce qui est implémenté, inclut les migrations nécessaires, conserve la provenance, fournit tests positifs/négatifs/régression/crash, différencie MVP et futur, produit un rapport vérifiable et met à jour la traçabilité.

## 23. Historique des versions

- **v0.1** (3 août 2026) : source normative initiale avant implémentation.
- **v0.2** (4 août 2026) : consolidation après fermeture technique de la Phase 3 ; intégration de la direction post-audit ; distinction implémenté / normatif futur / historique ; casting de référence (femme humaine, louve anthro, slime, chat) ; Phase 4 = vertical slice administratif.
- **v0.3** (5 août 2026) : photographie actualisée de la Phase 4.1 ; casting MVP fixé à Sophie, Erika, une louve anthro, une slime et un chat ; le nombre de résidentes sapientes est quatre, sans limiter le noyau à cette population.
- **v0.4** (5 août 2026) : registre versionné de composants, capacités et unités, puis fondation des gabarits de personnage; aucune instance définitive ni validation structurelle complète n'est encore créée.
- **v0.5** (5 août 2026) : gabarits liés à des versions précises de composants et validation structurelle déterministe de leur configuration; aucune instance définitive n'est encore créée.
- **v0.6** (5 août 2026) : instanciation atomique depuis un gabarit publié, avec provenance et définition initiale figées; aucune résidente MVP n'est encore créée ni migrée.
- **v0.7** (5 août 2026) : catalogue MVP publié (morphologie, profil cognitif, besoins standards), sans confondre contrats descriptifs et mécanismes réellement exécutés.

## 24. Annexes et références

- Registre des décisions : `docs/01_REGISTRE_DECISIONS.md` v0.3.
- Matrice des exigences : `docs/02_MATRICE_EXIGENCES.md` v0.3.
- Décisions ouvertes : `docs/03_DECISIONS_OUVERTES.md` v0.3.
- Gabarits : `docs/05_GABARITS.md` v0.2.
- Exigences normatives post-audit : `docs/history/Vivarium_Exigences_Normatives_Post_Audit_v0_1.md`.
- Demande de changement post-audit : `docs/history/Vivarium_Demande_Changement_Post_Audit_v0_2.md`.
- Feuille de route post-audit : `docs/history/Vivarium_Feuille_Route_Post_Audit_v0_1.md`.
- Registre des audits : `docs/history/Vivarium_Registre_Audits_v0_9.md`.
- Index maître des décisions : `docs/history/Vivarium_Index_Maitre_Decisions_v0_3.md`.
- Mémoire de travail : `docs/history/Vivarium_Memoire_Assistante_v10.md` (non normative).
- Historique des lots : `CHANGELOG.md`.
- Sources historiques : `sources/01..05`.
