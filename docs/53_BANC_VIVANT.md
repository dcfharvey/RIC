# Banc vivant jetable — porte avant Gemma

**Statut :** livré au 6 août 2026.

`run_living_bench(provider, limits)` construit une base SQLite en mémoire,
assemble le monde d’intégration réel, crée un événement de déplacement concret
et fait tourner l’orchestrateur jusqu’à stabilisation. Il ne lit ni n’écrit la
base de développement ou le futur monde MVP.

Le fournisseur est injecté : les tests emploient un faux modèle qui répond
`no_action`, puis un faux modèle indisponible. Le premier prouve le chemin
perception → admission → contexte → proposition → moteur; le second prouve le
mode dégradé, sans corruption canonique. Le rapport contient les outcomes,
le digest canonique final et l’audit structurel.

La prochaine opération autorisée est un essai contrôlé avec `LMStudioProvider`
et Gemma déjà chargée, sur ce banc seulement. Ce ne sera pas encore le lancement
du monde MVP persistant.

La commande `vivarium living-bench` affiche chaque tick, résidente, événement,
verdict et erreur locale directement dans la console. Elle est conçue pour être
lancée dans une fenêtre PowerShell séparée, afin que l'observation humaine reste
distincte du moteur et de son journal.

**Preuve de sortie :** deux scénarios injectés et suite complète : 642 tests
réussis (643 après l'ajout de la console en direct).
