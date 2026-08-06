# Croyances subjectives sourcées — lot initial

**Statut :** implémenté partiellement au 6 août 2026.

## Contrat livré

Une `subjective_belief` appartient à une résidente et contient une question,
une proposition structurée, une polarité (`true`, `false`, `uncertain`), une
confiance, une visibilité et un statut. Elle n'est ni un fait canonique, ni
une permission d'agir.

Chaque adoption exige une `subjective_trace` du **même personnage et monde**.
L'évidence en conserve l'orientation, la diagnosticité et la fiabilité de
source déclarée. Le service ne déduit pas que le contenu de la trace prouve
sémantiquement la proposition : cette interprétation appartient au futur
contrat cognitif et ne doit pas être feinte par le moteur.

Une correction crée une nouvelle croyance avec `revision_of_id`, son évidence
et son événement `belief_revised`; seulement ensuite l'ancienne devient
`contested`, dans la même transaction. Les triggers SQLite interdisent les
suppression et édition silencieuse de la croyance, de sa preuve ou de son
événement.

## Ce que le LLM peut voir

`CognitionContext` v2 porte au plus dix croyances de sa seule résidente. Elles
sont explicitement nommées `beliefs`, à côté des souvenirs et des faits
perçus : une croyance reste donc distinguable de la réalité que le moteur
valide. Le LLM ne peut toujours proposer qu'une action du contrat fermé.

## Audit et limites assumées

`subjective_belief_digest` et `subjective_belief_audit` sont hors digest
canonique. Ils contrôlent qu'une croyance possède une preuve et l'événement
attendu, et qu'une croyance contestée a un successeur audité.

Restent futurs : hypothèses avant adoption (EPI-001), alternatives `other` et
questions concurrentes (EPI-002), confiance perceptive, pertinence causale,
recence et dépendances de preuves (EPI-003), modèles sociaux de source
(EPI-004), acceptation pratique/coût de révision (EPI-005), ainsi que la
coexistence gérée des contradictions (EPI-006). Le lot ne les déclare pas
livrés.

## Preuve de sortie

- adoption refusée sans trace privée accessible ;
- révision, preuve et événement atomiques ;
- refus SQLite de mutation et de suppression silencieuses ;
- digest/audit subjectifs propres ;
- contexte LLM v2 borné et gelé ;
- suite complète : 624 tests réussis après ce lot.
