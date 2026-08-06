# Matrice des exigences

**Version :** 0.4
**Date :** 6 août 2026
**Statut :** actif — consolidée après fermeture technique de la Phase 3
**Colonne État :** `implémenté` (dans le code et testé) / `futur` (direction approuvée, non implémentée) / `partiel`.

## Fonctionnelles

| ID | Exigence | État |
| --- | --- | --- |
| F-01 | Créer, charger, sauvegarder et restaurer un monde persistant. | partiel (création/chargement ; sauvegarde/restauration futures) |
| F-02 | Créer cinq entités MVP — quatre résidentes sapientes et un chat — avec identité, traits, valeurs, intérêts, besoins, objectifs, relations et mémoire adaptés à leur profil cognitif. | partiel (catalogue et cinq gabarits v1, instanciation générique, identité/besoins techniques; traits/valeurs/relations/mémoire futurs) |
| F-03 | Faire avancer le temps réel, gérer pause/reprise et rattrapage condensé. | partiel (1:1 + pause/reprise ; rattrapage futur) |
| F-04 | Permettre aux personnages de proposer des intentions selon leur état subjectif. | partiel (politique déterministe ; subjectivité future) |
| F-05 | Valider toute intention par le moteur avant modification du monde. | implémenté (moteur seul autorité) |
| F-06 | Distinguer événement canonique, perception, interprétation, croyance et souvenir. | partiel (événement canonique ; perception/croyance/souvenir futurs) |
| F-07 | Gérer conversations privées, de groupe, avec le propriétaire et avec le technicien. | futur |
| F-08 | Permettre au propriétaire d’observer, interagir, se manifester, régir et administrer. | partiel (observation, commandes simples et premier pipeline de changement non sensible; manifestation et administration profonde futures) |
| F-09 | Condenser les routines banales et développer les scènes significatives. | futur |
| F-10 | Produire notifications, résumés périodiques, rapports de coût et alertes. | futur |
| F-11 | Créer des snapshots, restaurer et revenir en arrière. | futur |
| F-12 | Journaliser actions, décisions, appels de modèle, changements et opérations sensibles. | partiel (journal canonique ; appels de modèle futurs) |
| F-13 | Exporter des fiches, rapports et données dans des formats lisibles et documentés. | futur |
| F-14 | Permettre au technicien de diagnostiquer et proposer des changements sans les appliquer. | futur |

## Non fonctionnelles

| ID | Exigence | État |
| --- | --- | --- |
| NF-01 | Fonctionner sans rendu graphique de jeu. | implémenté |
| NF-02 | Permettre le remplacement du modèle et du fournisseur par adaptateur. | futur |
| NF-03 | Conserver les données canoniques localement dans des formats documentés. | implémenté (SQLite) |
| NF-04 | Une panne d’API, de réseau ou de Discord ne doit pas corrompre le monde. | futur |
| NF-05 | Reprendre après redémarrage sans perdre la dernière transaction validée. | implémenté |
| NF-06 | Attribuer chaque fait important à une cause, un acteur et une provenance. | partiel (causalité des blessures ; provenance générale future) |
| NF-07 | Mesurer coûts, jetons, latences, erreurs et charge locale. | futur |
| NF-08 | Appliquer le moindre privilège et des permissions configurables. | futur |
| NF-09 | Faire évoluer les schémas et règles par versions et migrations. | implémenté (20 migrations) |
| NF-10 | Couvrir les comportements essentiels par des tests reproductibles. | implémenté (525 tests) |
| NF-11 | Rester discret sur l’ordinateur personnel : pas de boucle à haute fréquence ni croissance mémoire non bornée. | implémenté (borne de transitions) |
| NF-12 | Être compréhensible et maintenable par une autre IA ou un autre développeur. | implémenté (documentation + code) |

## Invariants

| ID | Invariant | État |
| --- | --- | --- |
| INV-001 | Un seul monde actif est chargé par instance dans le MVP. | implémenté |
| INV-002 | Chaque personnage actif est explicitement adulte. | implémenté (personnages techniques adultes) |
| INV-003 | Un personnage possède une seule position canonique active à un instant donné. | implémenté |
| INV-004 | Un objet possède un seul emplacement ou détenteur canonique actif. | implémenté (lieu effectif et parent-objet optionnel cohérents) |
| INV-005 | Aucun texte généré ne devient directement un événement canonique sans validation. | implémenté (moteur seul autorité) |
| INV-006 | Toute mémoire non introspective référence au moins une source. | futur |
| INV-007 | Une perception ne contient aucune information inaccessible au personnage. | futur |
| INV-008 | Les relations sont dirigées ; aucune symétrie n’est imposée. | futur |
| INV-009 | Les statistiques cachées d’un personnage ne sont pas exposées à un autre. | futur |
| INV-010 | Un changement important de personnalité est borné, justifié et historisé. | futur |
| INV-011 | Toute modification directe d’un personnage exige analyse d’impact, approbation et snapshot. | futur |
| INV-012 | Un élément canonique figé ne dérive pas par mise à jour autonome. | futur |
| INV-013 | Un départ définitif ne peut être appliqué sans décision du propriétaire. | futur |
| INV-014 | Les scènes privées continuent indépendamment de leur affichage sur Discord. | futur |
| INV-015 | Aucun secret ou jeton n’est stocké dans une mémoire narrative, un prompt journalisé ou un message Discord. | futur |
| INV-016 | Une transaction échouée ne laisse aucun état partiellement appliqué. | implémenté |
| INV-017 | Un retry ne duplique pas une action grâce à l’idempotence. | partiel (confirmation idempotente du premier pipeline administratif) |
| INV-018 | Toute restauration ou migration s’exécute en mode maintenance. | futur |
| INV-019 | Les résumés, caches et index dérivés sont reconstructibles depuis leurs sources. | futur |
| INV-020 | Une notification échouée ne modifie jamais l’histoire canonique. | futur |
| INV-021 | Une conversation interrompue est clôturée sans suite inventée. | futur |
| INV-022 | Le MVP ne crée ni vieillissement, ni maladie, ni grossesse, ni mort. | implémenté |
| INV-023 | Toute correction canonique conserve l’ancien enregistrement et un lien de rectification. | implémenté (journal append-only) |
| INV-024 | Les opérations administratives et techniques restent séparées de la mémoire des personnages sauf manifestation explicite. | futur |
| INV-025 | Un cache, un embedding ou une vue dérivée n’est jamais l’unique copie d’une information. | futur |

## Acceptation

| ID | Résultat attendu | État |
| --- | --- | --- |
| AF-01 | Après redémarrage, le monde, l’heure, les personnages, les lieux et la dernière transaction validée sont retrouvés. | implémenté |
| AF-02 | Deux habitantes initient et terminent une conversation sans intervention du propriétaire. | futur |
| AF-03 | Deux témoins d’un même événement conservent des perceptions ou interprétations différentes sans altérer le canon. | futur |
| AF-04 | Un objet ajouté dans un lieu est perçu seulement par les personnes ayant accès à sa manifestation. | futur |
| AF-05 | Une modification psychologique est bloquée avant analyse, snapshot et confirmation. | futur |
| AF-06 | Une relation évolue graduellement à partir d’événements causaux et ne saute pas arbitrairement. | futur |
| AF-07 | Une sortie dans le monde extérieur produit un résultat condensé cohérent et un retour. | futur |
| AF-08 | Le toggle de contact spontané coupe l’envoi Discord sans supprimer les intentions internes. | futur |
| AF-09 | Une scène privée peut être directe, résumée ou masquée sans changer ses conséquences. | futur |
| AF-10 | Un événement adulte peut émerger sans obligation, respecte les états et est mémorisé selon la confidentialité. | futur |
| AF-11 | Une panne d’API reporte les décisions cognitives et laisse les routines déterministes en état sûr. | futur |
| AF-12 | Une période hors ligne est rattrapée sans appel par minute et avec coût borné. | futur |
| AF-13 | Une demande de départ définitif devient une situation à discuter, jamais une suppression automatique. | futur |
| AF-14 | Un élément canonique figé d’un personnage de fiction ne change pas sans approbation. | futur |
| AF-15 | Le technicien produit un diagnostic fondé sur des preuves et toute tentative d’écriture est refusée. | futur |

## Exigences post-audit (référence)

Les invariants normatifs post-audit (GOV, ARC, COG, EPI, MOT, PER, ATT, VAL, BND, GOAL, INT, COM, DEC, MEM, REL, EMO, ONT, CAP, ID, PST, LIB, ADM, CNS, LLM, MVP) sont détaillés dans `docs/history/Vivarium_Exigences_Normatives_Post_Audit_v0_1.md` (annexe normative versionnée). Ils sont **normatifs futurs** : aucun n’est présenté comme déjà implémenté, sauf mention explicite dans le dossier maître v0.2 (ex. journal append-only, transactions atomiques, moteur seul autorité).
