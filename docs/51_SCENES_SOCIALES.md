# Scènes sociales et paroles structurées — lot initial

**Statut :** implémenté partiellement au 6 août 2026.

Une scène exige de deux à cinq participantes réellement co-localisées. Elle
porte son statut (`active`, `closed`, `interrupted`) et ses participantes
persistantes. Une parole est un acte fermé (`greet`, `ask`, `answer`, `inform`,
`offer`, `decline`, `apologize`, `acknowledge`, `leave`) avec locutrice,
destinataire optionnelle, texte et payload structuré.

Le texte est une expression consignée, pas une vérité : il ne modifie pas seul
une croyance, une relation, une permission, un engagement ni un fait canonique.
Ces effets demanderont chacun leur contrat et leur validation propres.

Les actes et événements de scène sont append-only. Au redémarrage, les scènes
encore actives sont clôturées `interrupted` sans inventer la réplique suivante,
ce qui applique INV-021.

Restent futurs : perception auditive des témoins, confidentialité spatiale,
tour de parole LLM, effets de parole validés, scènes de groupe élaborées et
résumés mémoire. La couche est néanmoins suffisante pour qu'un orchestrateur
prépare et clôture une conversation sûre.

**Preuve de sortie :** co-localisation, idempotence des actes, fermeture,
interruption après service et refus d'une parole hors scène sont testés; suite
complète : 638 tests réussis.
