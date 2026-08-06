# Banc d'essai reproductible du moteur

**Version :** 1.0
**Statut :** implémenté — socle minimal sans LLM ni interface
**Code :** `vivarium.bench`

## But et frontière

Le banc exécute une expérience du moteur dans une base SQLite temporaire et
isolée. Il sert aux tests d'intégration, aux diagnostics et aux futurs « what
if ». Il ne lit, ne copie, ne modifie ni ne réinitialise une base de
développement, d'intégration ou MVP.

Il ne constitue pas une deuxième source de vérité : les actions passent par les
API canoniques existantes, et le rapport est non persistant.

## Contrat minimal

Un `BenchScenario` fixe :

- `start_at`, `target_at` et une `BenchClock` injectée ;
- le nom et le seed du monde temporaire ;
- une liste ordonnée de `BenchAction` ;
- une garde maximale de transitions.

Les actions supportées sont fermées et explicitement validées : pause/reprise,
renommage, déplacement, démarrage/abandon d'activité, blessure injectée et
ajout/retrait sûr de passage. Il n'existe aucune action générique SQL ou Python.

Chaque action déclare `expected="applied"` ou `expected="refused"`. Un refus
attendu est conservé dans le rapport; un résultat contraire est une erreur de
contrat du scénario. Une erreur de paramétrage est toujours refusée avant toute
exécution.

`at` est une heure **canonique**. Pendant une pause, le temps canonique est
figé : une reprise doit donc être déclarée à cette même heure avant une nouvelle
progression. Une future extension pourra ajouter une chronologie murale
distincte si un test doit mesurer explicitement une durée de pause.

## Preuves produites

`run_bench(scenario)` retourne un `BenchRunReport`, convertible par `to_json()`
ou `as_dict()`. Il contient :

- les segments de simulation et les résultats des actions, y compris refus ;
- le digest d'état canonique ;
- journal brut et projection sémantique ;
- audit structurel du journal, audit des matérialisations, `integrity_check` et
  `foreign_key_check`.

`compare_bench_runs(a, b)` compare séparément état, journal sémantique,
refus et santé des deux exécutions. Les UUID et identifiants SQLite ne servent
jamais de preuve de reproductibilité.

## Usage Python

```python
from vivarium.bench import BenchAction, BenchScenario, run_bench

scenario = BenchScenario(
    name="blessure de référence",
    start_at="2026-08-01T08:00:00.000+00:00",
    target_at="2026-08-01T12:00:00.000+00:00",
    actions=(
        BenchAction(
            at="2026-08-01T09:00:00.000+00:00",
            kind="inflict_injury",
            params={"character_key": "character_1", "severity_milli": 30000},
        ),
    ),
)
report = run_bench(scenario)
assert report.is_healthy
```

## Suite

Le prochain lot ajoute des scénarios d'acceptation inter-systèmes, pas une
interface. Chaque nouvelle famille du moteur doit fournir au moins un scénario
reproductible avant d'être activée dans le monde d'intégration pré-MVP.
