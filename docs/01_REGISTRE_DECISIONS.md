# Registre des décisions autoritatives

**Version :** 0.5
**Date :** 6 août 2026
**Statut :** actif — registre consolidé après fermeture technique de la Phase 3
**Source :** dossier maître v0.1, clarifications CLA-001..004, demande de changement post-audit v0.2, index maître des décisions v0.3

> Une décision remplacée conserve son identifiant et reçoit un statut `supersédée`, avec la référence `supersédée par`. Aucune décision historique n’est supprimée.

Statuts : `implémenté` (présent dans le code et testé), `normatif futur` (direction approuvée, non implémentée), `supersédée` (remplacée, trace conservée), `actif` (direction en vigueur).

---

## A. Décisions du dossier maître v0.1 (DEC-001..027)

| ID | Décision | Statut |
| --- | --- | --- |
| DEC-001 | Le MVP comporte exactement quatre personnages actifs, tous explicitement adultes. | **supersédée** — par DEC-001 v0.2 (casting de référence, moteur non limité à quatre) |
| DEC-002 | La résidence détaillée comprend un salon, une cuisine, quatre chambres individuelles, une salle de bain et une cour. | **implémenté** (9 lieux) |
| DEC-003 | Le temps simulé suit le temps réel lorsque l’application fonctionne ; le système est conçu pour tourner en continu. | **implémenté** (1:1) |
| DEC-004 | Après un arrêt ou une veille, le temps écoulé est rattrapé de façon condensée au prochain démarrage ; aucun appel par minute manquée. | **normatif futur** (rattrapage non implémenté) |
| DEC-005 | Les personnages sont assez actifs et peuvent initier activités, projets, conversations, rapprochements, conflits et changements relationnels. | **normatif futur** |
| DEC-006 | Les contacts spontanés vers le propriétaire sont activables ou désactivables globalement et par personnage. | **normatif futur** |
| DEC-007 | Les conversations et scènes entre personnages continuent sans le propriétaire ; leur affichage peut être direct, résumé ou masqué. | **normatif futur** |
| DEC-008 | Le propriétaire est une entité supérieure connue des personnages et peut intervenir comme observateur, interlocuteur, manifestation ou administrateur. | **normatif futur** (autorité/ perceptibilité : CLA-001) |
| DEC-009 | Tout élément du vivarium est administrativement modifiable. Une modification directe d’un personnage exige une analyse d’impact, un snapshot et une confirmation explicite. | **supersédée** — par DEC-009 v0.2 (protocole renforcé) |
| DEC-010 | Les personnages ne connaissent une intervention que par ses manifestations perceptibles ou par une communication explicite. | **normatif futur** |
| DEC-011 | Les personnages disposent d’une autonomie complète à l’intérieur des règles du monde. Ils peuvent sortir de la résidence, mais ne peuvent quitter définitivement le vivarium sans discussion et décision du propriétaire. | **normatif futur** |
| DEC-012 | Le monde extérieur reste abstrait dans le MVP : destinations, horaires, sorties, contacts légers et conséquences condensées. | **normatif futur** |
| DEC-013 | Les besoins physiques et psychologiques sont détaillés. Les valeurs numériques restent cachées dans l’usage normal et s’expriment par les comportements. | **supersédée** — par DEC-013 v0.2 (catégories distinctes) |
| DEC-014 | Les personnages peuvent évoluer graduellement. Pour un personnage canonique, les éléments figés, bornés, souples et libres sont définis par le propriétaire. | **normatif futur** |
| DEC-015 | La mémoire comprend perception, interprétation, croyance, souvenir, consolidation, oubli naturel, inspection et modification administrative auditée. | **supersédée** — par DEC-015 v0.2 (mémoire reconstructive) |
| DEC-016 | Le contenu relationnel, romantique et adulte peut émerger naturellement selon les personnages, leurs préférences, leur libido, le contexte et les relations ; les événements pertinents sont conservés. | **supersédée** — par DEC-016 v0.2 (consentement actuel requis) |
| DEC-017 | Discord est l’interface principale du MVP : identités distinctes, messages, scènes, événements, résumés, rapports techniques, alertes et commandes. | **supersédée** — par DEC-017 v0.2 (interface sociale principale) |
| DEC-018 | Une seule application Discord peut publier sous des noms et avatars distincts ; l’implémentation exacte des webhooks reste un détail technique. | **normatif futur** |
| DEC-019 | Aucune interface graphique de jeu n’est requise. Un tableau de bord administratif léger pourra être ajouté plus tard si nécessaire. | **supersédée** — par DEC-019 v0.2 (interface web locale = MVP) |
| DEC-020 | Le programme tourne initialement sur l’ordinateur personnel du propriétaire et ne réduit pas automatiquement son activité pendant l’usage normal du PC. | **actif** |
| DEC-021 | L’architecture doit permettre ultérieurement un ordinateur dédié, un modèle local et un changement de fournisseur sans migration narrative majeure. | **actif** |
| DEC-022 | Le technicien existe dans le MVP comme assistant de diagnostic et de recommandation en lecture seule ; il ne modifie ni code, ni données actives, ni déploiement. | **normatif futur** |
| DEC-023 | Le MVP ne simule ni vieillissement, ni maladie, ni grossesse, ni mort. Les blessures peuvent exister si elles sont causales et récupérables. | **implémenté** (blessures non mortelles récupérables) |
| DEC-024 | Une conversation interrompue par une panne ou un arrêt est clôturée automatiquement sans inventer la suite. | **normatif futur** |
| DEC-025 | Le budget API initial n’est pas fixé, mais la mesure des coûts, les alertes et les limites configurables sont obligatoires. | **normatif futur** |
| DEC-026 | Le modèle de langage et le fournisseur sont des composants remplaçables derrière un adaptateur ; le moteur local demeure l’autorité. | **actif** |
| DEC-027 | LM Studio Bionic est l’environnement de développement initial envisagé, mais ne constitue pas une dépendance du produit ni du dossier. | **actif** |

## B. Clarifications approuvées (CLA-001..004)

| ID | Clarifie | Décision retenue | Statut |
| --- | --- | --- | --- |
| CLA-001 | Autorité vs perceptibilité du propriétaire | Deux dimensions indépendantes : niveau d’autorité (observateur, interlocuteur, participant, régisseur, administrateur) et perceptibilité (directe, indirecte par conséquences, non perceptible). | **actif** |
| CLA-002 | Rapport temps simulé/réel | Rapport 1:1 pendant le fonctionnement ; pause ou avance administrative possible ; aucune accélération permanente par défaut ; rattrapage condensé à l’arrêt. | **implémenté** (1:1 + pause) / rattrapage **normatif futur** |
| CLA-003 | Modification directe d’un personnage | Protocole obligatoire : analyse d’impact, snapshot, confirmation explicite, transaction, audit. | **normatif futur** |
| CLA-004 | Sûreté de `init --force` | Commande destructive réservée au développement ; refusée par défaut pour tout monde réel/persistant ; non exécutable implicitement par Discord. | **implémenté** |

## C. Décisions du dossier maître v0.2–v0.3 (remplacements)

| ID | Décision | Statut |
| --- | --- | --- |
| DEC-001 v0.2 | Le scénario de référence du MVP comporte quatre entités actives : une femme humaine sapiente adulte, une louve anthro sapiente adulte, une slime sapiente adulte à apparence féminine et un chat domestique non sapient. Le moteur ne fixe pas globalement la population à quatre. | **supersédée** par DEC-001 v0.3 |
| DEC-001 v0.3 | Le scénario de référence du MVP comporte cinq entités actives : Sophie et Erika, humaines sapientes adultes ; une louve anthro sapiente adulte ; une slime sapiente adulte à apparence féminine ; un chat domestique non sapient. Le moteur ne fixe pas globalement la population à cinq. | **normatif futur** |
| DEC-009 v0.2 | Toute modification canonique profonde exige une commande métier, une validation en couches, un rapport d’impact, un plan préparé immuable, un checkpoint lorsque requis, une confirmation liée à un hash et une version, une transaction atomique et un audit administratif. | **normatif futur** |
| DEC-013 v0.2 | Les variables physiologiques, besoins psychologiques, motifs, désirs, ressources et états dérivés sont des catégories distinctes. Les valeurs numériques restent normalement cachées et s’expriment par les comportements. | **normatif futur** |
| DEC-015 v0.2 | La mémoire distingue événement canonique, perception, encodage subjectif, épisode, consolidation, représentation courante, récupération reconstructive, provenance et oubli multicausal. Le moteur conserve l’historique des révisions. | **normatif futur** |
| DEC-016 v0.2 | Le contenu relationnel, romantique et adulte peut émerger seulement entre entités sapientes explicitement adultes, selon leurs états, préférences, relations, permissions et consentements actuels. Aucun score relationnel, désir, rôle ou engagement ne constitue un consentement. | **normatif futur** |
| DEC-017 v0.2 | Discord est l’interface sociale principale. Une application web locale minimale est l’interface administrative et appartient au MVP. Aucune interface ne modifie directement SQLite. | **normatif futur** |
| DEC-019 v0.2 | L’application web locale minimale est l’interface administrative du MVP. | **normatif futur** |
| DEC-023 v0.2 | L’univers initial interdit la mort, l’amputation et les dommages corporels involontaires permanents. Les blessures non fatales et récupérables restent permises selon des règles causales. | **implémenté** (blessures non mortelles récupérables) |

## D. Nouvelles décisions post-audit (DEC-036..060)

| ID | Décision | Statut |
| --- | --- | --- |
| DEC-036 | Méthode de conception : revue scientifique ou technique préalable, puis système opérationnel testable. | **normatif futur** |
| DEC-037 | Cognition subjective : réalité, perception, interprétation, hypothèses, croyances, encodage, souvenirs et récit conscient restent séparés. | **normatif futur** |
| DEC-038 | Perception faillible : enregistrement implicite, détection, attention, conscience, intégration multisensorielle ; omissions et fausses alertes possibles. | **normatif futur** |
| DEC-039 | Épistémologie structurée : hypothèses concurrentes, preuves, provenance, modèles de source, contradictions, révisions. | **normatif futur** |
| DEC-040 | Motivation restructurée : régulation physiologique, besoins psychologiques, motifs, incitations, désirs, objectifs, apprentissage de valeur. | **normatif futur** |
| DEC-041 | Personnalité mécanistique : traits continus modulant des mécanismes, évolution lente ; attachement contextuel, dimensionnel, propre aux relations. | **normatif futur** |
| DEC-042 | Valeurs, principes et limites : structures distinctes (valeurs, principes, convictions morales, limites, normes, lois, contraintes physiques). | **normatif futur** |
| DEC-043 | Objectifs et intentions : graphe de fins et de moyens ; intentions persistantes par défaut avec contexte de reprise. | **normatif futur** |
| DEC-044 | Décision bornée et explicable : peu d’options, impossibilité distincte de transgression, profils multidimensionnels, suffisance. | **normatif futur** |
| DEC-045 | Mémoire reconstructive : encodage subjectif, récupération faillible, distincte de la vérité canonique. | **normatif futur** |
| DEC-046 | Relations multidimensionnelles : directionnelles, propres aux domaines, fondées sur des preuves, réseau social ; confiance/intimité/pouvoir/engagement/réparation décomposés. | **normatif futur** |
| DEC-047 | Émotions processuelles : multi-composants, appraisals ; humeur, sentiment, étiquette, expression, régulation séparés. | **normatif futur** |
| DEC-048 | Régulation interpersonnelle : tentatives de réguler autrui, effet dépendant de la perception de la cible, interventions intrusives soumises aux permissions. | **normatif futur** |
| DEC-049 | Ontologie composable : identité, type, phase, rôle, sujet cognitif, contrôleur, corps, manifestation, forme, apparence séparés. | **normatif futur** |
| DEC-050 | Capacités et affordances : capacités dérivées des composants et de l’état ; affordances relationnelles situées. | **normatif futur** |
| DEC-051 | Transitions d’identité : politique explicite pour copie, transformation, séparation, fusion, reconstitution, remplacement ; cas avancés différés au MVP. | **normatif futur** |
| DEC-052 | Event sourcing sélectif : journal des changements significatifs ; tables d’état pour les lectures ; projections reconstruisibles. | **normatif futur** (le journal append-only actuel est un fondement) |
| DEC-053 | Sauvegardes spécialisées : snapshot de projection, checkpoint administratif, backup physique, export portable distincts. | **normatif futur** |
| DEC-054 | Modèles et instances : modèles publiés versionnés et immuables ; instanciation indépendante ; aucune propagation silencieuse. | **normatif futur** |
| DEC-055 | Administration canonique : application web locale = client d’une API canonique ; commandes métier pour les changements sensibles. | **normatif futur** |
| DEC-056 | Registres et validation : composants, capacités, unités, événements, validateurs versionnés ; JSON Schema ne remplace pas les validateurs sémantiques. | **normatif futur** |
| DEC-057 | Préparation et confirmation : plan préparé, hash, version de base, rapport d’impact ; changement concurrent invalide le plan. | **normatif futur** |
| DEC-058 | Séparation des journaux : journal canonique, audit administratif, diagnostics techniques distincts. | **normatif futur** |
| DEC-059 | LLM sans autorité : propose et formule ; ne fixe ni vérité, ni capacité, ni mémoire, ni émotion, ni relation, ni consentement, ni résultat canonique. | **normatif futur** |
| DEC-060 | Consentement indépendant : aucune affection, confiance, intimité, autorité, attirance, promesse ou relation ne constitue un consentement actuel. | **normatif futur** |

## E. Clarifications du 6 août 2026

| ID | Décision | Statut |
| --- | --- | --- |
| CLA-005 | Le monde MVP sera une base propre, distincte des mondes temporaires de tests automatisés et du monde technique de développement. Les mondes de test peuvent être clonés ou éphémères; ils ne modifient jamais l'histoire MVP. | **actif** |
| DEC-061 | Un banc d'essai reproductible devient un outil central de validation du moteur. Il définit des conditions contrôlées, exécute des variantes isolées et compare leurs résultats. La première version, sans LLM, précède les systèmes de perception, cognition et social. | **actif** |
| DEC-062 | Le MVP désigne le simulateur social dans un état présentable, pas la seule création de la résidence et des cinq entités. Cette première base est un monde d'intégration pré-MVP, réinitialisable; perception, mémoire, relations et décision sociale sont nécessaires pour atteindre le MVP. | **actif** |
| DEC-063 | La chronologie logicielle utilise `0.0.0.dev0` pour le pré-alpha actuel; `0.1.0a1` sera le premier MVP alpha et `0.1.0b1` son passage en bêta après essais prolongés. Les versions documentaires restent indépendantes. | **actif** |
