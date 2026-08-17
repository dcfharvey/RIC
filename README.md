# RIC — Reality · Interaction · Cognition

RIC est un moteur de simulation sociale persistante où la réalité canonique, l'accès perceptif et la cognition subjective restent séparés.

Le projet s'appelait auparavant **Vivarium Social**. Les noms techniques historiques sont conservés lorsqu'ils font partie du code ou du packaging :

- distribution Python : `vivarium-social`
- import : `vivarium`

## État produit courant

La seule référence produit autoritative est la branche `product/current`.

Ne pas conserver de SHA, compteur de tests, session de rodage ou autre photographie volatile dans ce README. Pour connaître l'état courant :

1. résoudre le SHA réel de `product/current`;
2. consulter `docs/INDEX_DOCUMENTAIRE.md`;
3. lire `docs/99_PASSATION_COURANTE.md` pour la photographie opérationnelle la plus récente.

Le README décrit le projet et ses invariants; il n'est pas un journal de release.

## Architecture conceptuelle

Les trois moteurs sont des catégories conceptuelles. Ils ne doivent pas être projetés automatiquement sur des packages ou services précis.

**Reality Engine** — ce qui est objectivement vrai, possible et causal dans la simulation.

**Interaction Engine** — ce qui rend les agents et la réalité mutuellement accessibles et structure leurs interactions.

**Cognitive Engine** — ce que chaque agent perçoit, interprète, mémorise, priorise et décide subjectivement.

La boucle cible est :

```text
réalité canonique
→ sous-ensemble perceptible
→ état subjectif / mémoire / préférences / besoins
→ intention ou décision proposée
→ validation moteur
→ conséquence canonique
→ nouvelles perceptions
```

## Invariants fondamentaux

```text
réalité/canon ≠ perception ≠ croyance
parole ≠ fait
relation ≠ permission ≠ consentement
LLM propose, moteur valide
aucun composant cognitif n'écrit directement la réalité canonique
provenance d'audit ≠ source subjectivement mémorisée
un seul propriétaire persistant par état
pas d'omniscience implicite des agents
mécanisme générique > script propre à un personnage
```

## État fonctionnel général

Le produit comprend notamment :

- monde canonique persistant et temps 1:1;
- lieux, connecteurs, traversées et plans de localisation;
- objets, contenance et possession;
- activités et conséquences canoniques;
- physiologie et ressources owner-backed;
- population de référence Sophie, Erika, Luna, Chuu et Patoune;
- perception locale, attention et structures cognitives subjectives;
- cognition LLM locale derrière un adaptateur et une file avec fairness/backpressure;
- scènes sociales bornées;
- fondations de mémoire autobiographique;
- observabilité du contexte cognitif avec provenance technique séparée du souvenir subjectif;
- grounding opérationnel du soi et projection read-only de faisabilité avant exposition d'une activité au modèle.

Cela ne signifie pas que tous les systèmes sont complets. Le projet reste en alpha et les frontières de qualification sont documentées explicitement dans les documents actifs.

## Développement local

Prérequis : Python 3.12+ et Git.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest
```

Sous Unix :

```bash
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest
```

Point d'entrée minimal :

```bash
python -m vivarium
```

Les commandes opérateur existantes doivent être utilisées selon leur documentation et leur portée. Ne pas lancer un ancien protocole de rodage à partir d'un document historique sans vérifier la passation courante.

## Reprendre le projet

Lire dans cet ordre :

1. `docs/INDEX_DOCUMENTAIRE.md` — hiérarchie documentaire et statut des familles de documents;
2. `docs/99_PASSATION_COURANTE.md` — photographie opérationnelle et blocages actuels;
3. `docs/00_DOSSIER_MAITRE_IA.md` — noyau normatif stable;
4. `docs/01_REGISTRE_DECISIONS.md` — décisions autoritatives;
5. `docs/03_DECISIONS_OUVERTES.md` — arbitrages encore ouverts;
6. `docs/15_ROADMAP_ACTIVE.md` — ordre des prochains travaux;
7. `docs/GOUVERNANCE_GIT.md` — discipline de référence produit et d'intégration.

Les documents de lots, `docs/history/`, `sources/` et la passation du 5 août sont des sources de provenance. Ils ne remplacent pas silencieusement les documents actifs ni le code réellement intégré.

## Gouvernance de développement

- **ChatGPT** : recherche scientifique/technique, conception fonctionnelle, cohérence conceptuelle, documentation R&D.
- **Grok** : contre-audit scientifique adversarial indépendant.
- **Codex** : autorité sur l'architecture réelle, le code, les migrations, les invariants techniques, les tests et l'ordre d'implantation.
- **Propriétaire** : autorité finale produit/design.

La méthode de travail est :

> **Flexible creativity. Rigorous execution.**
>
> **Verify twice. Commit once.**

Tout modèle comportemental, cognitif, social ou physiologique doit être fondé d'abord sur la littérature scientifique ou technique pertinente, puis traduit explicitement en système opérationnel. Les résultats empiriques, conclusions incertaines, hypothèses de modélisation et choix d'ingénierie doivent rester distingués.
