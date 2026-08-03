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
```

- `init` initialise un monde de développement.
- `status` inspecte l'état général (intégrité, version de schéma, horloge, compteurs).

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

### Structure

- `src/vivarium/` — paquet Python (package, configuration, journaux).
- `tests/` — tests de fumée, SQLite et infrastructure.
- `config/` — fichiers de configuration (`config/.env.example`).
- `logs/` — répertoire des journaux (non versionné).
- `data/` — données locales (non versionné, généré à l'exécution).

