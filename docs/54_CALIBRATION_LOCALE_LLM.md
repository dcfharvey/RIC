# Calibration locale de Gemma — contrat et stabilité

**Statut :** première tranche livrée le 6 août 2026. Elle ne choisit pas
encore de cadence produit.

`python -m vivarium llm-calibrate --trials 3` répète un contexte identique
dans une base SQLite mémoire neuve par essai. Chaque essai produit un
événement de déplacement directement perceptible par Sophie, passe par la
porte d'admission LLM, puis rapporte :

- durée du tour complet admis ;
- décision structurée reçue ;
- acceptation ou refus du moteur, s'il y a une action ;
- panne, réponse hors contrat ou non-admission de façon explicite.

Le banc ne lit ni n'écrit une base de développement ou MVP. Chaque essai est
isolé des autres : une traversée acceptée au premier ne peut donc pas
changer le contexte du second. Il mesure le comportement de la frontière,
pas la qualité narrative, la personnalité ou une ressemblance humaine.

## Ce que la revue impose ici

La conversation est une activité coordonnée : le contenu d'un tour et l'acte
qu'il accomplit doivent rester distinguables. Le futur contrat de parole
conservera donc un acte structuré, une destinataire et un texte, sans traiter
une affirmation comme un fait ou un savoir mutuel automatique. Les travaux sur
le *common ground* indiquent que ce terrain commun est construit et confirmé
par les participantes; il ne peut pas être déduit du seul texte. Les travaux
sur le tour de parole montrent aussi que l'acte et le sujet contraignent la
réponse pertinente, ce qui justifie un tour explicite et borné plutôt qu'un
dialogue infini.

Sources de travail : [Bovet, Knutsen & Fossard (2023)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10867054/),
[Levinson & Torreira — Timing in Conversation](https://pmc.ncbi.nlm.nih.gov/articles/PMC10077995/),
et les contrats historiques du projet dans `sources/02_PARTIE_II_CONCEPTION_SOURCE.md`
et `sources/04_PARTIE_IV_DONNEES_SOURCE.md`.

## Critère de sortie de cette tranche

Des essais répétés peuvent être lancés et comparés sans histoire
partagée. Une réponse refusée par le moteur est un résultat valide; une panne
ou une réponse hors contrat est visible. La cadence produit reste une décision
future basée sur plusieurs mesures, jamais sur une seule latence.
