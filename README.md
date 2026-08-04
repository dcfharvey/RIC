# Vivarium social artificiel — paquet destiné à une IA programmeuse

Version 0.1, 3 août 2026.

## Fichier à lire en premier

`docs/00_DOSSIER_MAITRE_IA.md` est la seule source normative initiale.

Les fichiers du dossier `sources/` proviennent des cinq documents de conception antérieurs. Ils sont fournis pour la traçabilité et le détail historique, mais contiennent des formulations préliminaires qui ont été arbitrées dans le dossier maître. Une IA ne doit pas les utiliser pour contredire le dossier maître.

## Première commande

Copier le contenu de `docs/04_PROMPT_DEMARRAGE.md` dans l’environnement agentique après avoir ouvert le dossier du projet.

## Règle essentielle

Ne pas demander « construis tout ». Exiger d’abord `AUDIT_INITIAL.md`, puis travailler par phases approuvées.

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
```

- `init` initialise un monde de développement.
- `status` inspecte l'état général (intégrité, version de schéma, horloge, compteurs).
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

### Structure

- `src/vivarium/` — paquet Python (package, configuration, journaux).
- `tests/` — tests de fumée, SQLite et infrastructure.
- `config/` — fichiers de configuration (`config/.env.example`).
- `logs/` — répertoire des journaux (non versionné).
- `data/` — données locales (non versionné, généré à l'exécution).

