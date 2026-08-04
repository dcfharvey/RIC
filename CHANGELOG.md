# Changelog

## 0.2 — 3 août 2026

- Approbation de `docs/AUDIT_INITIAL.md` par le propriétaire.
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
  blessures recomptées depuis le régime, besoins vérifiés par ancres/continuité/
  taux implicite entier ; détecte les erreurs compensées), `max_seq` (invariant
  séparé), `SimulationRunReport`.
  Correction `occurred_at` canonique pour `needs_materialized` et
  `character_moved`. Scénarios 24 h (84 transitions), blessures, endurance 7 j
  (980 transitions) ; runs comparatifs A-G ; tests de pause/reprise/redémarrage,
  crash/rollback, délai mural, absence de frontière, erreurs compensées.
  Aucune migration, aucun RNG. 215 tests passants (188 + 27).

## 0.1 — 3 août 2026

- Création du dossier maître destiné à une IA programmeuse.
- Consolidation des cinq parties.
- Arbitrage des anciennes formulations sur population, habitat, temps, technicien et machine hôte.
- Ajout du contrat de lecture, du prompt de démarrage et des matrices séparées.
