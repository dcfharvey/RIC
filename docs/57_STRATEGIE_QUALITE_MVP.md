# Stratégie de qualité et prévol MVP

**Statut :** active — porte de qualité pré-MVP, sans appel LLM implicite.

## Décision

La qualité du Vivarium ne sera pas mesurée par un nombre arbitraire de tests
ni par un essai interminable de Gemma. Chaque niveau de risque reçoit une
preuve adaptée, reproductible et aussi peu coûteuse que possible :

| Niveau | Objet vérifié | Coût | Déclenchement |
| --- | --- | --- | --- |
| règles locales | tests unitaires, refus et idempotence | très faible | à chaque lot concerné |
| jonctions de systèmes | banc déterministe en mémoire | faible | avant activation du système dans le monde MVP |
| frontière LLM | fumée, calibration ou scène jetable | appels locaux bornés | explicitement, après changement du contrat/prompt/modèle |
| base candidate | `mvp-preflight`, lecture seule | très faible | avant ouvrir les contrôles opérateur |
| expérience opérateur | parcours web local et inspection visuelle | humain | avant le jalon alpha, puis après changement d'interface |

Un résultat vert à un niveau ne remplace jamais les autres. Un dialogue
convaincant ne prouve pas la santé SQLite; une suite de tests verte ne prouve
pas qu'un panneau est utilisable; un prévol sain ne transforme pas une
fonction future en fonction livrée.

## Porte déterministe : `mvp-preflight`

La commande suivante inspecte une **base existante** en lecture seule. Elle ne
crée pas de fichier, n'applique aucune migration, n'appelle pas Gemma et ne
répare aucune anomalie :

```powershell
.\.venv\Scripts\python.exe -m vivarium mvp-preflight --db C:\chemin\vers\monde.sqlite
```

Si la base contient plusieurs mondes, il faut choisir explicitement la cible :

```powershell
.\.venv\Scripts\python.exe -m vivarium mvp-preflight --db C:\chemin\vers\monde.sqlite --world-id 3
```

Le prévol vérifie actuellement :

- intégrité SQLite et clés étrangères;
- statut du monde et sélection non ambiguë;
- cinq identités du casting courant (Sophie, Erika, Luna, Chuu, Patoune) et
  position canonique de chacune;
- contexte commun initial déclaré;
- continuité, causalité et JSON du journal canonique;
- chaînes de matérialisation des besoins/blessures;
- journaux subjectifs déjà implémentés (traces, croyances, affect, social).

Il produit seulement `OK`/`ECHEC` et un détail technique court. Un échec est
un **arrêt de lancement**, jamais une instruction de contourner une contrainte
ou de modifier SQLite à la main.

## Usage efficace des tests

Pendant le développement, commencer par les fichiers de tests touchés, puis
exécuter la suite complète après un lot matériel ou transversal :

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_mvp_preflight.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest-tmp-verification -p no:cacheprovider
```

La sortie `-q` ne retourne qu'un résumé compact à Codex. Elle garde la
couverture de code sans gonfler inutilement son contexte. Les répertoires
`.pytest-tmp-*` sont jetables et ne font pas partie du dépôt.

Les appels locaux Gemma restent séparés et bornés, par exemple :

```powershell
.\.venv\Scripts\python.exe -m vivarium llm-smoke
.\.venv\Scripts\python.exe -m vivarium scene-bench --max-turns 4
```

Ils n'utilisent pas le quota Codex; ils ne sont lancés que lorsqu'ils apportent
une information nouvelle sur le contrat réel ou la qualité des sorties. Le
contenu généré ne devient pas une preuve de vérité canonique.

## Ce qui reste nécessaire avant `0.1.0a1`

Le prévol couvre un candidat de base, pas encore un MVP alpha. La roadmap
reste honnête : il faut encore raccorder les options d'action légales, les
décisions et conséquences validées, les déclencheurs/fermetures de scènes dans
l'orchestrateur, puis un runtime persistant contrôlable. Les contrôles
opérateur existants (lecture, pause/reprise, commandes simples et premiers
changements préparés) seront utilisés comme fondation; ils ne seront pas
contournés par un script de lancement.

Avant de déclarer l'alpha, chaque capacité ajoutée devra fournir au minimum :

1. un succès déterministe;
2. un refus atomique;
3. une régression inter-systèmes ou un scénario de banc;
4. un mode dégradé lorsque le LLM ou le runtime est indisponible;
5. une preuve d'observation/contrôle dans l'interface locale lorsqu'elle est
   exposée au propriétaire.

Cette stratégie augmente la couverture là où la complexité apparaît, sans
prétendre connaître aujourd'hui toutes les situations émergentes de demain.
