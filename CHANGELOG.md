# Changelog

## 0.17 — 4 août 2026

- **Phase 4.1B — Commandes administratives sûres et durcissement des frontières**.
- `WorldError` (world.py) avec `code` stable : `invalid_name`, `already_paused`,
  `already_active`.
- `WorldEngine.rename_world` : validation autoritative (chaîne, non vide après
  suppression des espaces, longueur ≤ `WORLD_NAME_MAX_LEN=120`), valeur
  normalisée enregistrée et dans le payload, refus avant toute mutation/événement.
- `WorldEngine.pause_world` / `resume_world` : refus autoritatif des répétitions
  (`already_paused` / `already_active`) dans la même transaction (aucune fenêtre
  lecture-validation-écriture séparée), aucune mutation d'horloge ni événement.
- `CharacterError` porte un `code` stable (world_not_found, world_paused,
  character_not_found, invalid_destination, activity_active, injury_severe,
  insufficient_energy) ; construction historique (message seul) préservée.
- `AdminCommandService` (admin.py) : dispatcher fermé à pause/resume/rename/move,
  format stable `{ok, command, data, error}`, validation des paramètres
  (world_id réel, bool refusé, chaînes non vides), traduction des erreurs par
  type/code (jamais par texte), `unknown_command`, `internal` masqué.
- Aucune migration, aucun changement de seed, de casting, de serveur HTTP ou de
  tableau de bord.
- Tests : 296 réussis (263 + 33 nouveaux).

## 0.16 — 4 août 2026

- **Correctifs 4.1A (A-1, A-2, A-3)** — lecture blessure au régime actif.
- `InjuryEngine.injury_sheet_at(world_id, character_key, target_at, regime)` :
  dérivation pure d'une blessure à un instant donné sous un régime explicite
  (passive/rest/sleep), sans écriture ni matérialisation ; frontières exactes
  (guérison à zéro, changement de niveau).
- `AdminReadService.character_view` : dérive la blessure au régime de
  récupération réellement applicable (régime de l'activité active via
  `recovery_regime`, `passive` sinon) ; plus de blessure obsolète pendant
  rest/sleep.
- `AdminReadService.list_character_views` : un seul snapshot de lecture, un seul
  `observed_canonical_at` pour toute la liste.
- A-3 documenté : pagination par `OFFSET` acceptable pour le petit journal local
  du MVP ; pagination par curseur reportée (non construite).
- Aucune migration, aucun changement de seed, de casting, de commande ou
  d'interface web.
- Tests : 263 réussis (249 + 14 nouveaux).

## 0.15 — 4 août 2026

- **Phase 4.1A — Couche de lecture administrative** (lecture seule).
- `src/vivarium/admin.py` : `AdminReadService` (frontière de lecture SQL confinée),
  `list_worlds`, `dashboard`, `list_character_views`, `character_view`,
  `journal_view` (pagination bornée par `seq`, payload masqué par défaut,
  résumés déterministes, type inconnu → résumé générique).
- Vues composées sous transaction de lecture SQLite (snapshot cohérent),
  `observed_canonical_at` capturé une seule fois, besoins/blessures dérivés à cet
  instant, aucune écriture ni matérialisation.
- Aucune migration, aucun changement de seed, de casting, de `world.py`, de
  commande ou d'interface web.
- Tests : 249 réussis (228 existants + 21 nouveaux dans `tests/test_admin_read.py`).

## 0.14 — 4 août 2026

- **Consolidation documentaire v0.2** — Phase 3 techniquement fermée (`7e5459e`,
  228 tests, `FERMETURE APPROUVABLE`). Aucun changement de code, seed, migration ou test.
- `docs/00_DOSSIER_MAITRE_IA.md` v0.2 : dossier maître consolidé (implémenté /
  normatif futur / historique), moteur canonique déterministe, contrats stabilisés,
  limites, dettes, séquence vers Phase 4 (vertical slice administratif).
- `docs/01_REGISTRE_DECISIONS.md` v0.2 : DEC-001..060 + CLA-001..004 avec statuts
  (implémenté / normatif futur / supersédée) ; casting de référence (femme humaine,
  louve anthro, slime, chat) ; Phase 4 = vertical slice administratif.
- `docs/02_MATRICE_EXIGENCES.md` v0.2 : F/NF/INV/AF avec colonne d'état.
- `docs/03_DECISIONS_OUVERTES.md` v0.2 : OD révisées (OD-009 partiellement fermée).
- `docs/05_GABARITS.md` v0.2 : ajout du contrat de lot standard.
- `README.md` : mise à jour minimale (3.3B2/3.3C et fermeture Phase 3).
- Intégration documentaire des documents post-audit et de traçabilité
  (Exigences v0.1, Demande v0.2, Feuille de route v0.1, Registre des audits v0.9,
  Index maître v0.3, Mémoire v10) ; documents archivés dans `docs/history/` (voir commit de consolidation v0.2).

## 0.13 — 4 août 2026

- **Correctifs de fermeture de la Phase 3 (C-1, C-2, C-3)** — aucun bloquant
  résiduel, aucune migration.
- **C-1** : garde dans `CharacterEngine._move` — aucun déplacement pendant une
  activité active (refus `CharacterError` avant toute matérialisation ou débit,
  sans interruption silencieuse ; position, énergie, blessure, horloge et
  journal inchangés). Le déplacement préparatoire de `start_activity` (avant la
  création de l'activité) et le déplacement direct sans activité restent
  fonctionnels.
- **C-2** : `occurred_at` des mutations administratives situé dans le temps
  canonique du monde (`read_canonical_time`), jamais à l'heure murale :
  `rename_world`, `add_link`, `remove_link`, `create_character`. `recorded_at`
  reste mural et distinct. `pause_world`, `resume_world`, `set_simulated_time`
  et les événements du simulateur sont inchangés (déjà canoniques).
- **C-3** : retrait de l'API publique `WorldEngine.append_event` ; seule
  `_append_event` (interne, dans une transaction métier) subsiste. Plus aucune
  API publique ne peut injecter un `event_type`/`payload`/`occurred_at`
  arbitraire ni un événement sans mutation correspondante.
- Tests : 228 passants (220 + 8 nouveaux, 1 remplacé).

## 0.2 — 3 août 2026

- Approbation de `docs/history/AUDIT_INITIAL.md` par le propriétaire.
- Décisions : Python 3.12 comme référence (OD-001 fermé) ; clarifications CLA-001 (autorité/perceptibilité), CLA-002 (temps 1:1 et rattrapage), CLA-003 (modification directe d’un personnage).
- **Phase 0** réalisée : dépôt Git initialisé, paquet Python minimal (`src/vivarium`), configuration (`config/`), journaux (`logs/`), accès SQLite vérifié, tests de fumée (11 tests passants). Aucune logique métier (personnage, simulation, LLM, Discord, mémoire, technicien) ajoutée.
- Règle de sûreté CLA-004 : `init --force` est destructif, réservé au développement, refusé par défaut pour tout monde réel/persistant/non-développement et non exécutable implicitement par Discord ou une commande propriétaire.

## 0.3 — 3 août 2026

- **Phase 2 — Lot 2.1** : horloge canonique en temps réel 1:1 (dérivée, lecture sans écriture), pause/reprise avec gel exact et reprise sans rattrapage de la pause, horloge injectable déterministe (`Clock`), migration 0002 (contrainte du statut `active`/`paused` par déclencheurs). 44 tests passants.

## 0.4 — 3 août 2026

- **Phase 2 — Lot 2.2** : connectivité spatiale. 9ᵉ lieu `couloir` (circulation),
  graphe orienté `location_link` (migration 0003), BFS dirigé (`find_path`),
  `can_traverse`/`has_physical_connection`/`adjacent_from`, intégrité du graphe,
  modifications administratives atomiques et tracées (un événement par opération
  physique). `init --force` utilisé exceptionnellement pour reconstruire le monde
  de développement ; pratique documentée comme exceptionnelle. 61 tests passants.
- Note d'évolution future EVO-001 : détection d'un saut anormal de l'horloge
  système vers l'avant avant un grand rattrapage (non implémenté).

## 0.5 — 3 août 2026

- **Phase 3 — Lot 3.1** : identités et présence canonique. Table `character`
  (migration 0004, sans `is_dev` ; `key` immuable par déclencheur ; `adult=1` ;
  FK composite `(world_id, location_id)`), 4 habitantes provisoires `character_1..4`
  en `chambre_1..4`, `CharacterEngine` (`create_character`, `character_sheet`,
  `move_character` une arête dirigée, refus en pause/vers le lieu actuel, atomicité),
  procédure non destructive et idempotente `upgrade-dev`. 77 tests passants.

## 0.6 — 3 août 2026

- **Phase 3 — Sous-lot 3.2A** : besoins dérivés et matérialisation. Migration 0005
  (`need_definition`, `need_state` avec `rate_remainder`, FK composites inter-mondes),
  valeur entière `value_milli` 0..100000, taux rationnels entiers, équivalence
  indépendante du découpage, lectures pures, matérialisation groupée (un événement
  `needs_materialized`), pause atomique avec matérialisation, mise à niveau
  non destructive `upgrade-dev`. 89 tests passants.

## 0.7 — 3 août 2026

- **Phase 3 — Sous-lot 3.2B** : activités et effets. Migration 0006 : passage au
  dénominateur canonique 36 (conversion sans perte des taux et restes de 3.2A) +
  `activity_definition`, `activity_allowed_location` (index uniques partiels),
  `activity` (une active/personnage). `start_activity` atomique (déplacements
  pièce par pièce + matérialisation + création), fin conditionnelle du sommeil
  (`max` puis `min` avec reste), clôture d'activité échue à son heure canonique,
  abandon, lecture pure. 104 tests passants.

## 0.8 — 3 août 2026

- **Phase 3 — Sous-lot 3.2C** : politique de décision déterministe et simulation.
  Migration 0007 `character_profile` (entiers, sans REAL ; profils neutres seedés),
  `DeterministicPolicy` pure (`Intent`/`DecisionResult`), `PolicyContext` immuable,
  urgence normalisée par produits croisés, gestion conjointe repos/énergie,
  destination déterministe, `SimulationEngine.run_to` (bornes canoniques, bornes
  simultanées ordonnées, heure cible en milieu d'activité, garde configurable,
  replis bornés). Démo 24 h : ~460 transitions (garde 2000), reproducible. 126 tests passants.

## 0.9 — 3 août 2026

- **Phase 3 — Sous-lot 3.3A** : correction de l'attente et accessibilité du sommeil.
  Attente **dynamique** : `Intent.duration_seconds` obligatoire et borné `1..MAX_IDLE`
  (8 h) pour `idle`, refusé pour `eat`/`clean`/`rest`/`sleep`. L'`idle` se termine à la
  première seconde où la décision changerait (franchissement d'un seuil / palier
  d'urgence / critique), calculée mathématiquement avec le reste rationnel (aucun
  tick par minute), sinon plafond `idle_safety_boundary`. Règle de sommeil naturelle :
  repos/énergie critique ⇒ sleep ; repos déficient ⇒ sleep ; seule énergie modérée
  ⇒ rest ; `rest_preference` ne bloque jamais le sommeil exigé. Aucun retunage de taux.
  Démo 24 h : **84** transitions (vs 460), **28** idle (vs 168), **128** matérialisations
  (vs 692), ≥ 1 sommeil de 8 h par habitante, aucune boucle, reproductible. 143 tests passants.

## 0.10 — 3 août 2026

- **Phase 3 — Sous-lot 3.3B1** : blessures de mobilité — état, causalité et
  récupération. Migration 0008 `injury` (sévérité entière /36, CHECK d'invariants
  `active`/`healed`, une seule active par index partiel, historique immuable), FK +
  `UNIQUE(world_id, cause_event_seq)` vers `canonical_event`, déclencheur de
  terminalité `healed`, `script_accident`/`injure_character`/`inflict_injury`
  (combiné atomique), `started_at = cause.occurred_at`, régimes de récupération
  typés `passive`/`rest`/`sleep`, reste rationnel, guérison à l'heure exacte,
  événements `scripted_accident`/`injury_occurred`/`injury_materialized`/
  `injury_healed`. Effets de mobilité reportés à 3.3B2. 164 tests passants.

## 0.11 — 3 août 2026

- **Phase 3 — Sous-lot 3.3B2** : effets mécaniques des blessures. Classification
  dérivée réutilisée (`level`/`SEV_LIGHT_MAX`/`SEV_MODERATE_MAX`), surcharge de
  déplacement modérée **500 milli-énergie par arête** (`MOVEMENT_SURCHARGE_MILLI`),
  matérialisation canonique de la blessure avant classification dans
  `CharacterEngine._move` (régime réellement actif), blocage canonique du
  déplacement en blessure sévère, `character_moved` enrichi
  (`base_energy_cost`/`injury_energy_surcharge`/`edge_count`/`total_energy_cost`/
  `injury_effect_level`), `seconds_to_level` (généralisation de `seconds_to_heal`),
  `recovery_regime` dans `activities.py`, matérialisation de la blessure aux
  frontières d'activité (`start_activity`/`advance_to`/`abort_activity`), politique
  avertie exactement à la frontière `severe→moderate` (idle dynamique borné),
  filtrage des destinations en niveau sévère (`_accessible`). Aucune migration.
  188 tests passants (164 existants + 24 nouveaux).

## 0.12 — 3 août 2026

- **Phase 3 — Sous-lot 3.3C** : reproductibilité finale et fermeture technique.
  Helper interne `WorldEngine._advance_clock` : chaque transition temporelle
  (`start_activity`, `advance_to`, `abort_activity`) pose atomiquement
  `simulated_now = cible` et `real_updated_at = Clock.now` dans sa transaction
  (rollback annule aussi l'horloge ; aucun `clock_updated`). Outils de
  comparaison `src/vivarium/repro.py` : `canonical_state_digest` (références par
  clés logiques, `character.name` inclus, rowids/UUID/muraux exclus),
  `raw_canonical_event_log` (journal brut complet), `structural_event_audit`
  (séquences continues, aucun trou/doublon, `occurred_at` monotones, JSON et
  causalités valides), `reproducible_semantic_projection` (faits significatifs,
  matérialisation exclue, `seq` absolu renuméroté, causalité normalisée vers la
  position relative de l'événement causal), `materialization_chain_audit`
  (objet D : exactitude mathématique de chaque chaîne de matérialisation —
  blessures recomptées depuis le régime, besoins recomptés depuis le taux
  déclaré et vérifiés contre le taux canonique des règles ; détecte les erreurs
  compensées de valeur et de reste), `max_seq` (invariant séparé),
  `SimulationRunReport`.
  Contrat `needs_materialized` enrichi : `rate_source` (`need_definition`/
  `activity`), `activity_type` (null en passif), `rate_nums`/`rate_dens` par
  besoin — le taux réellement appliqué est porté par l'événement pour une
  vérification non circulaire.
  Correction `occurred_at` canonique pour `needs_materialized` et
  `character_moved`. Scénarios 24 h (84 transitions), blessures, endurance 7 j
  (980 transitions) ; runs comparatifs A-G ; tests de pause/reprise/redémarrage,
  crash/rollback, délai mural, absence de frontière, erreurs compensées.
  Aucune migration, aucun RNG. 220 tests passants (188 + 32).

## 0.1 — 3 août 2026

- Création du dossier maître destiné à une IA programmeuse.
- Consolidation des cinq parties.
- Arbitrage des anciennes formulations sur population, habitat, temps, technicien et machine hôte.
- Ajout du contrat de lecture, du prompt de démarrage et des matrices séparées.
