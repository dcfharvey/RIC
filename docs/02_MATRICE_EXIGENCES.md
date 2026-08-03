# Matrice des exigences

## Fonctionnelles

| ID | Exigence |
| --- | --- |
| F-01 | Créer, charger, sauvegarder et restaurer un monde persistant. |
| F-02 | Créer quatre personnages avec identité, traits, valeurs, intérêts, besoins, objectifs, relations et mémoire. |
| F-03 | Faire avancer le temps réel, gérer pause/reprise et rattrapage condensé. |
| F-04 | Permettre aux personnages de proposer des intentions selon leur état subjectif. |
| F-05 | Valider toute intention par le moteur avant modification du monde. |
| F-06 | Distinguer événement canonique, perception, interprétation, croyance et souvenir. |
| F-07 | Gérer conversations privées, de groupe, avec le propriétaire et avec le technicien. |
| F-08 | Permettre au propriétaire d’observer, interagir, se manifester, régir et administrer. |
| F-09 | Condenser les routines banales et développer les scènes significatives. |
| F-10 | Produire notifications, résumés périodiques, rapports de coût et alertes. |
| F-11 | Créer des snapshots, restaurer et revenir en arrière. |
| F-12 | Journaliser actions, décisions, appels de modèle, changements et opérations sensibles. |
| F-13 | Exporter des fiches, rapports et données dans des formats lisibles et documentés. |
| F-14 | Permettre au technicien de diagnostiquer et proposer des changements sans les appliquer. |

## Non fonctionnelles

| ID | Exigence |
| --- | --- |
| NF-01 | Fonctionner sans rendu graphique de jeu. |
| NF-02 | Permettre le remplacement du modèle et du fournisseur par adaptateur. |
| NF-03 | Conserver les données canoniques localement dans des formats documentés. |
| NF-04 | Une panne d’API, de réseau ou de Discord ne doit pas corrompre le monde. |
| NF-05 | Reprendre après redémarrage sans perdre la dernière transaction validée. |
| NF-06 | Attribuer chaque fait important à une cause, un acteur et une provenance. |
| NF-07 | Mesurer coûts, jetons, latences, erreurs et charge locale. |
| NF-08 | Appliquer le moindre privilège et des permissions configurables. |
| NF-09 | Faire évoluer les schémas et règles par versions et migrations. |
| NF-10 | Couvrir les comportements essentiels par des tests reproductibles. |
| NF-11 | Rester discret sur l’ordinateur personnel: pas de boucle à haute fréquence ni croissance mémoire non bornée. |
| NF-12 | Être compréhensible et maintenable par une autre IA ou un autre développeur. |

## Invariants

| ID | Invariant |
| --- | --- |
| INV-001 | Un seul monde actif est chargé par instance dans le MVP. |
| INV-002 | Chaque personnage actif est explicitement adulte. |
| INV-003 | Un personnage possède une seule position canonique active à un instant donné. |
| INV-004 | Un objet possède un seul emplacement ou détenteur canonique actif. |
| INV-005 | Aucun texte généré ne devient directement un événement canonique sans validation. |
| INV-006 | Toute mémoire non introspective référence au moins une source. |
| INV-007 | Une perception ne contient aucune information inaccessible au personnage. |
| INV-008 | Les relations sont dirigées; aucune symétrie n’est imposée. |
| INV-009 | Les statistiques cachées d’un personnage ne sont pas exposées à un autre. |
| INV-010 | Un changement important de personnalité est borné, justifié et historisé. |
| INV-011 | Toute modification directe d’un personnage exige analyse d’impact, approbation et snapshot. |
| INV-012 | Un élément canonique figé ne dérive pas par mise à jour autonome. |
| INV-013 | Un départ définitif ne peut être appliqué sans décision du propriétaire. |
| INV-014 | Les scènes privées continuent indépendamment de leur affichage sur Discord. |
| INV-015 | Aucun secret ou jeton n’est stocké dans une mémoire narrative, un prompt journalisé ou un message Discord. |
| INV-016 | Une transaction échouée ne laisse aucun état partiellement appliqué. |
| INV-017 | Un retry ne duplique pas une action grâce à l’idempotence. |
| INV-018 | Toute restauration ou migration s’exécute en mode maintenance. |
| INV-019 | Les résumés, caches et index dérivés sont reconstructibles depuis leurs sources. |
| INV-020 | Une notification échouée ne modifie jamais l’histoire canonique. |
| INV-021 | Une conversation interrompue est clôturée sans suite inventée. |
| INV-022 | Le MVP ne crée ni vieillissement, ni maladie, ni grossesse, ni mort. |
| INV-023 | Toute correction canonique conserve l’ancien enregistrement et un lien de rectification. |
| INV-024 | Les opérations administratives et techniques restent séparées de la mémoire des personnages sauf manifestation explicite. |
| INV-025 | Un cache, un embedding ou une vue dérivée n’est jamais l’unique copie d’une information. |

## Acceptation

| ID | Résultat attendu |
| --- | --- |
| AF-01 | Après redémarrage, le monde, l’heure, les personnages, les lieux et la dernière transaction validée sont retrouvés. |
| AF-02 | Deux habitantes initient et terminent une conversation sans intervention du propriétaire. |
| AF-03 | Deux témoins d’un même événement conservent des perceptions ou interprétations différentes sans altérer le canon. |
| AF-04 | Un objet ajouté dans un lieu est perçu seulement par les personnes ayant accès à sa manifestation. |
| AF-05 | Une modification psychologique est bloquée avant analyse, snapshot et confirmation. |
| AF-06 | Une relation évolue graduellement à partir d’événements causaux et ne saute pas arbitrairement. |
| AF-07 | Une sortie dans le monde extérieur produit un résultat condensé cohérent et un retour. |
| AF-08 | Le toggle de contact spontané coupe l’envoi Discord sans supprimer les intentions internes. |
| AF-09 | Une scène privée peut être directe, résumée ou masquée sans changer ses conséquences. |
| AF-10 | Un événement adulte peut émerger sans obligation, respecte les états et est mémorisé selon la confidentialité. |
| AF-11 | Une panne d’API reporte les décisions cognitives et laisse les routines déterministes en état sûr. |
| AF-12 | Une période hors ligne est rattrapée sans appel par minute et avec coût borné. |
| AF-13 | Une demande de départ définitif devient une situation à discuter, jamais une suppression automatique. |
| AF-14 | Un élément canonique figé d’un personnage de fiction ne change pas sans approbation. |
| AF-15 | Le technicien produit un diagnostic fondé sur des preuves et toute tentative d’écriture est refusée. |