# Orchestrateur autonome borné — première version

**Statut :** implémenté pour les événements directs au 6 août 2026.

`VivariumOrchestrator.tick` prend une photo de la dernière séquence canonique,
traite au plus une borne configurée d’événements par résidente, vérifie la
perception réelle, applique la porte d’admission LLM, puis route la proposition
structurée vers le moteur.

Le curseur technique est séparé du monde et de la mémoire subjective. Un nouvel
événement produit par une action acceptée attend le tick suivant. Chaque source
reçoit un résultat append-only (`routed`, `deferred`, `unperceived`,
`provider_degraded`), puis son curseur avance. Une panne locale de Gemma ne
bloque donc ni le moteur, ni les ticks futurs, ni ne répète le même appel.

La version actuelle route seulement `direct_event`, seul déclencheur dont la
source perceptible est déjà prouvable. Les déclencheurs d’intention, de scène,
de réflexion et d’intervention admin restent fermés jusqu’à leur contrat propre.

Le contexte transmis à ce tour contient le cadre décisionnel déterministe
(intention active, objectifs, motifs et raison dominante), en plus des états
subjectifs privés déjà autorisés.

**Preuve de sortie :** source perceptible seulement, snapshot anti-boucle,
avancement persistant du curseur et dégradation LLM testés; suite complète :
640 tests réussis.
