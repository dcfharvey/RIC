# Vivarium social artificiel — paquet destiné à une IA programmeuse

Version documentaire 1.8, 6 août 2026. État logiciel courant : `0.1.0a15`,
schéma SQLite 39, migration `0039_scc1b_provider_provenance.sql`, SCC-1B1 livré,
767 tests validés; baseline SCC-1B1 clôturée avant SCC-1B2.

## Reprise d'un travail existant

Commencer par `docs/99_PASSATION_COURANTE.md`, puis lire
`docs/00_DOSSIER_MAITRE_IA.md`, les documents de lots cités et l'état Git.
La passation courante donne l'état opérationnel; le dossier maître reste la
source normative du dépôt.

Les fichiers du dossier `sources/` proviennent des cinq documents de conception antérieurs. Ils sont fournis pour la traçabilité et le détail historique, mais contiennent des formulations préliminaires qui ont été arbitrées dans le dossier maître. Une IA ne doit pas les utiliser pour contredire le dossier maître.

## Archive historique

Copier le contenu de `docs/history/04_PROMPT_DEMARRAGE.md` dans l’environnement agentique après avoir ouvert le dossier du projet.

## Règle essentielle

Ne pas demander « construis tout ». Exiger d’abord `docs/history/AUDIT_INITIAL.md`, puis travailler par phases approuvées.

## Développement (Phase 0)

### Prérequis

- Python 3.12+ (version de référence 3.12 ; testé sur 3.13 — doit rester compatible avec les versions ultérieures).
- Git.

### Installation

```bash
python -m venv .venv                # créer l'environnement virtuel
# Windows : .venv\Scripts\activate ;  Unix : source .venv/bin/activate
.venv/Scripts/python -m pip install -e ".[dev]"   # installer le paquet + pytest
```

### Tests

```bash
.venv/Scripts/python -m pytest -v
```

### Point d'entrée minimal

```bash
.venv/Scripts/python -m vivarium
```

Affiche la version et la configuration. Aucun service n'est encore démarré.

### Commandes

```bash
.venv/Scripts/python -m vivarium init [--name NOM] [--force]
.venv/Scripts/python -m vivarium status
.venv/Scripts/python -m vivarium upgrade-dev
.venv/Scripts/python -m vivarium mvp-init --db data/vivarium-alpha.sqlite
.venv/Scripts/python -m vivarium mvp-run --db data/vivarium-alpha.sqlite --enable-local-llm
.venv/Scripts/python -m vivarium social-interpretation-bench --level T0
```

- `init` initialise un monde de développement.
- `status` inspecte l'état général (intégrité, version de schéma, horloge, compteurs).
- `mvp-init` crée une résidence alpha sans jamais écraser une base existante;
  `mvp-run` lance son runtime et sa console locale. `Ctrl+C` ferme proprement
  les scènes ouvertes et gèle l'heure simulée. Une fermeture brutale est
  détectée au prochain lancement : le dernier point durable est restauré sans
  faire vieillir le monde pendant l'arrêt. Ajouter `--enable-local-llm` pour employer le modèle
  chargé dans LM Studio; sans ce drapeau, seules les routines canoniques tournent.
- `mvp-preflight --db <base>` inspecte en lecture seule une base candidate au MVP
  (intégrité, journal, casting et journaux subjectifs), sans LLM ni réparation.
- `social-interpretation-bench --level T0` exécute le banc SCC-1B2A déterministe;
  `--level T1` lance un smoke LM Studio borné et `--report <fichier>` écrit un
  rapport JSON technique. `--level T2 --trials 5` lance la campagne T2a réelle
  bornée; T2b et l'admission cognitive restent désactivés.
- `llm-inventory` exporte les model keys et métadonnées réellement exposées par
  LM Studio; `social-interpretation-screen --model-id <key>` est l'opération
  Screen-47 model-specific, limitée aux modèles déjà chargés et sans
  chargement/déchargement automatique.
- `upgrade-dev` ajoute, de façon **non destructive et idempotente**, les 4 identités
  provisoires `character_1..4` au monde local (aucun personnage existant modifié ;
  n'insère que les manquants). `init --force` reste un dernier recours manuel.

> ⚠️ **`init --force` est une commande destructive, réservée au développement.**
> Elle reconstruit entièrement la base locale de développement. Elle devra être
> **refusée par défaut** pour tout monde marqué comme réel, persistant ou
> non-développement. Aucune interface Discord ni commande du propriétaire n'est
> autorisée à l'exécuter implicitement.
>
> *Pratique exceptionnelle :* `init --force` a été utilisé pour le Lot 2.2 afin
> de reconstruire le monde de développement avec le 9ᵉ lieu et le graphe. Elle est
> **exceptionnelle** : toute future modification structurelle de données devra
> normalement passer par une migration ou une procédure de mise à niveau sans
> destruction du monde.

### Horloge canonique temps réel (Lot 2.1)

- L'heure simulée suit le temps réel (rapport 1:1) et est **dérivée** :
  `simulated_now` (ancre) + temps réel écoulé depuis `real_updated_at`.
- Une **lecture** de l'heure ne produit aucune écriture, aucun événement et
  n'ouvre aucune transaction.
- `pause_world` gèle le temps ; `resume_world` reprend sans ajouter la durée
  passée en pause.
- Statuts de monde : `active` / `paused` (contraints par la migration 0002).
- Pas d'accélération permanente et aucun appel par minute (rattrapage différé à
  la phase dédiée).

### Connectivité spatiale (Lot 2.2)

- 9 lieux : salon, cuisine, salle de bain, cour, **couloir** (circulation) et
  4 chambres.
- Graphe **orienté** : une ligne `location_link` = passage `from → to` ; un
  passage bidirectionnel = deux arêtes réciproques (migration 0003).
- API : `can_traverse(A,B)` (arête dirigée), `has_physical_connection(A,B)`
  (au moins un sens), `adjacent_from(A)`, `find_path(A,B)` (BFS dirigé).
- Une simple recherche de trajet/adjacence ne produit aucune écriture ni
  événement ; une modification administrative du graphe est tracée (un
  événement par opération physique) et atomique.

### Personnages et présence canonique (Lot 3.1)

- Table `character` (migration 0004) : `key` (identité technique **immuable**), `name`
  (modifiable), `adult` (= 1), `current_location_id` (position canonique, FK composite
  `(world_id, location_id)` garantissant le même monde).
- 4 habitantes provisoires `character_1..4` (Personnages 1..4) en `chambre_1..4` ;
  clé neutre **définitive** (le remplacement des fiches ne change que `name`).
- `CharacterEngine` : `create_character`, `character_sheet` (lecture pure),
  `move_character` (**une arête dirigée** via `GraphEngine`, refus en pause, refus vers
  le lieu actuel, état + événement `character_moved` dans la même transaction).
- Toutes les écritures passent par le moteur canonique (même infrastructure
  transactionnelle/événementielle) ; `CharacterEngine` n'est pas une seconde autorité.

### Besoins dérivés et matérialisation (Sous-lot 3.2A)

- Valeur entière à précision fixe : `value_milli ∈ [0, 100000]` (0 = très déficient,
  100000 = pleinement satisfait ; affichage = /1000).
- Taux rationnel entier `rate_num / rate_den` (milli / seconde simulée), sans REAL :
  évolution exactement reproductible et **indépendante du découpage** (grâce au
  `rate_remainder` persistant, résidu de division conservé entre matérialisations).
- 4 besoins : `satiete`, `repos`, `energie`, `hygiene` (migration 0005).
- Une **lecture** est pure (aucune écriture, aucun événement). Une matérialisation
  regroupe les 4 besoins d'un personnage dans une transaction et produit **un seul**
  événement `needs_materialized` (ancres, valeurs et restes anciens/nouveaux, raison).
- Pause : matérialise les besoins en même temps que le gel de l'horloge et du statut
  dans **une** transaction atomique ; reprise sans écriture.
- `upgrade-dev` ajoute aussi les besoins manquants (mise à niveau non destructive,
  idempotente, ancrée à l'heure simulée canonique).
- Dénominateur canonique commun **36** pour tous les taux (migration 0006 convertit
  les taux/restes de 3.2A sans perte).

### Activités et effets (Sous-lot 3.2B)

- `activity_definition` (taux nets /36 par besoin), `activity_allowed_location`
  (lieux autorisés par clé **ou** type, deux index uniques partiels),
  `activity` (une seule active par personnage).
- Activités : `idle`, `eat`, `rest`, `clean`, `sleep` (migration 0006).
- `start_activity(world, char, type, target_location)` — destination **explicite**
  et vérifiée (autorisée, existante), **atomique** : trajet pièce par pièce
  (chaque `character_moved` dans la même transaction) + matérialisation + création
  + `activity_started`. Retour à la position initiale si une étape échoue.
- Fin conditionnelle du sommeil : `max(dt_repos, dt_energie)` plafonné à 8 h,
  calcul exact des échéances (avec reste rationnel), refus si inutile.
- `advance_to` clôture une activité échue **à son heure canonique de fin**, puis
  repasse en régime passif ; `abort_activity` abandonne explicitement.
- Toutes les transitions sont atomiques ; une lecture d'activité est pure.

### Politique de décision et simulation (Sous-lot 3.2C)

- `Intent(activity_type, target_location)` (contrat minimal) ;
  `DecisionResult(intent, trigger_need, reason_code)` sépare la justification de
  l'exécution (migration 0007 `character_profile`, entiers, sans REAL).
- Politique **pure et déterministe** sur un `PolicyContext` immuable : urgence
  normalisée = `déficit × 1000 // seuil`, comparaisons par **produits croisés**,
  priorité par déficit normalisé (ordre fixe en égalité), gestion conjointe
  repos/énergie (critique ⇒ sleep ; double-déficit ⇒ sleep ; modéré isolé ⇒ rest,
  `rest_preference` graduée jamais opposée à un état critique), destination
  courante sinon la plus courte (départage par clé), `idle` si rien sous seuil.
- `SimulationEngine.run_to(world, target, max_transitions=2000)` : avance de
  borne en borne, bornes simultanées traitées dans l'ordre de `character.key`,
  heure cible en milieu d'activité sans clôture/décision, garde anti-boucle,
  replis bornés, rapport (`last_time`, `transitions`, activités actives).
- Les 4 profils seedés sont **neutres et identiques** (variations seulement en
  tests). Reproductible : mêmes données + même heure cible ⇒ même état et même journal.

### Attente dynamique et sommeil naturel (Sous-lot 3.3A)

- `Intent` transporte `duration_seconds` : **obligatoire et borné** `1..MAX_IDLE`
  (8 h) pour `idle`, **refusé** pour `eat`/`clean`/`rest`/`sleep` (durées définies ou
  conditionnelles). Le moteur valide toujours la durée reçue de la politique.
- **Attente dynamique** : l'`idle` ne dure plus 15 min fixes. Il se termine à la
  **première seconde où la décision changerait** — franchissement d'un seuil
  d'intervention, dépassement du palier d'urgence, ou franchissement critique —
  calculé mathématiquement (aucun tick par minute), en tenant compte du reste
  rationnel ; sinon plafond de sécurité `idle_safety_boundary` (8 h). Une unique
  longue attente remplace les séries de micro-cycles.
- **Règle de sommeil naturelle** : repos **ou** énergie critique ⇒ `sleep` ; repos
  déficient ⇒ `sleep` ; seule énergie modérée (repos acceptable) ⇒ `rest` ; les deux
  déficients ⇒ `sleep`. `rest_preference` ne peut jamais empêcher le sommeil exigé.
  Aucun retunage de taux.
- Démo 24 h corrigée : **84** transitions (vs 460), **28** idle (vs 168),
  **128** matérialisations (vs 692), ≥ 1 sommeil de 8 h par habitante, aucun besoin
  hors bornes, aucune boucle d'attente, journal et état identiques sur 2 exécutions.

### Blessures de mobilité : état, causalité et récupération (Sous-lot 3.3B1)

- Table `injury` (migration 0008) : une blessure générique `mobility`, sévérité
  entière `severity_milli ∈ [0,100000]` (aucune REAL), statut `active`/`healed`
  (CHECK combiné d'invariants), **une seule active** par personnage (index partiel),
  historique immuable.
- **Cause canonique** : `UNIQUE(world_id, cause_event_seq)` et FK vers
  `canonical_event(world_id, seq)` — une cause ne produit qu'une blessure et ne
  peut être réutilisée après consommation.
- **Terminalité** : déclencheur interdisant toute transition `healed → …` et toute
  modification corporelle d'une blessure guérie ; une nouvelle blessure est une
  nouvelle ligne.
- **Temps** : `started_at = recovery_anchor_at = cause.occurred_at` (`seq` cause <
  `seq` constat) ; `injure_character` restreint aux causes dont `occurred_at` est
  égal à l'heure canonique courante (cause ancienne refusée).
- **Récupération** : régimes typés `passive`/`rest`/`sleep` (taux 2/6/12 sur 36),
  reste rationnel persistant, indépendance au découpage et au changement de régime,
  guérison à l'heure exacte (ancre fixée à cette heure), rejet des cibles
  antérieures ou futures.
- **Événements** : `scripted_accident` (source `owner`), `injury_occurred`,
  `injury_materialized` (audit, seulement si écriture réelle), `injury_healed`.
- API : `script_accident`, `injure_character`, `inflict_injury` (combiné atomique),
  `materialize_injury`, `injury_sheet` (lecture pure).
- Les **effets de mobilité** (déplacements, activités, politique, coût d'énergie)
  sont reportés à 3.3B2.

### Effets mécaniques des blessures (Sous-lot 3.3B2)

- Classification dérivée `light`/`moderate`/`severe` (seuils 30000/60000).
- Blessure légère : aucun coût. Blessure modérée : surcharge de déplacement
  **500 milli-énergie par arête**. Blessure sévère : aucun mouvement autonome,
  activités locales conservées.
- Matérialisation canonique de la blessure avant classification, régime réellement
  actif ; `character_moved` au payload stable (5 champs).
- Garde : aucun déplacement pendant une activité active.

### Reproductibilité et fermeture (Sous-lot 3.3C)

- `repro.py` : `canonical_state_digest`, `raw_canonical_event_log`,
  `structural_event_audit`, `reproducible_semantic_projection`,
  `materialization_chain_audit`, `max_seq`, `SimulationRunReport`.
- Helper interne `_advance_clock` ; progression `run_to` sans `clock_updated`.
- Garantie : même état + mêmes règles + mêmes commandes + mêmes valeurs d'horloge
  injectées + même ordre canonique = même état et même journal sémantique.

### Fermeture technique de la Phase 3

Phase 3 techniquement fermée au commit `7e5459e` : **228 tests réussis**, verdict
`FERMETURE APPROUVABLE`. Le dossier maître est désormais `docs/00_DOSSIER_MAITRE_IA.md`
v1.0. La Phase 4.1 a livré les lectures administratives, les commandes sûres, l’API
HTTP locale et le premier tableau de bord. La Phase 4.2 a désormais posé le
registre versionné, les gabarits génériques de personnage et leur validation
structurelle, puis l'instanciation canonique avec provenance figée; leur
catalogue minimal, les cinq gabarits MVP et le noyau générique de ressources et
leurs effets déclaratifs sont publiés. L'interface et la création des résidentes
dans un monde restent à faire.

### Structure

- `src/vivarium/` — paquet Python (package, configuration, journaux).
- `tests/` — tests de fumée, SQLite et infrastructure.
- `config/` — fichiers de configuration (`config/.env.example`).
- `logs/` — répertoire des journaux (non versionné).
- `data/` — données locales (non versionné, généré à l'exécution).
