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

### Structure

- `src/vivarium/` — paquet Python (package, configuration, journaux).
- `tests/` — tests de fumée, SQLite et infrastructure.
- `config/` — fichiers de configuration (`config/.env.example`).
- `logs/` — répertoire des journaux (non versionné).
- `data/` — données locales (non versionné, généré à l'exécution).

