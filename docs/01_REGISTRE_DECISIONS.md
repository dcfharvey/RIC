# Registre des décisions autoritatives

| ID | Décision |
| --- | --- |
| DEC-001 | Le MVP comporte exactement quatre personnages actifs, tous explicitement adultes. |
| DEC-002 | La résidence détaillée comprend un salon, une cuisine, quatre chambres individuelles, une salle de bain et une cour. |
| DEC-003 | Le temps simulé suit le temps réel lorsque l’application fonctionne; le système est conçu pour tourner en continu. |
| DEC-004 | Après un arrêt ou une veille, le temps écoulé est rattrapé de façon condensée au prochain démarrage; aucun appel par minute manquée. |
| DEC-005 | Les personnages sont assez actifs et peuvent initier activités, projets, conversations, rapprochements, conflits et changements relationnels. |
| DEC-006 | Les contacts spontanés vers le propriétaire sont activables ou désactivables globalement et par personnage. |
| DEC-007 | Les conversations et scènes entre personnages continuent sans le propriétaire; leur affichage peut être direct, résumé ou masqué. |
| DEC-008 | Le propriétaire est une entité supérieure connue des personnages et peut intervenir comme observateur, interlocuteur, manifestation ou administrateur. |
| DEC-009 | Tout élément du vivarium est administrativement modifiable par le propriétaire. Une modification directe d’un personnage exige une analyse d’impact, un snapshot et une confirmation explicite. |
| DEC-010 | Les personnages ne connaissent une intervention que par ses manifestations perceptibles ou par une communication explicite. |
| DEC-011 | Les personnages disposent d’une autonomie complète à l’intérieur des règles du monde. Ils peuvent sortir de la résidence, mais ne peuvent quitter définitivement le vivarium sans discussion et décision du propriétaire. |
| DEC-012 | Le monde extérieur reste abstrait dans le MVP: destinations, horaires, sorties, contacts légers et conséquences condensées. |
| DEC-013 | Les besoins physiques et psychologiques sont détaillés. Les valeurs numériques restent cachées dans l’usage normal et s’expriment par les comportements. |
| DEC-014 | Les personnages peuvent évoluer graduellement. Pour un personnage canonique, les éléments figés, bornés, souples et libres sont définis par le propriétaire. |
| DEC-015 | La mémoire comprend perception, interprétation, croyance, souvenir, consolidation, oubli naturel, inspection et modification administrative auditée. |
| DEC-016 | Le contenu relationnel, romantique et adulte peut émerger naturellement selon les personnages, leurs préférences, leur libido, le contexte et les relations; les événements pertinents sont conservés. |
| DEC-017 | Discord est l’interface principale du MVP: identités distinctes, messages, scènes, événements, résumés, rapports techniques, alertes et commandes. |
| DEC-018 | Une seule application Discord peut publier sous des noms et avatars distincts; l’implémentation exacte des webhooks reste un détail technique. |
| DEC-019 | Aucune interface graphique de jeu n’est requise. Un tableau de bord administratif léger pourra être ajouté plus tard si nécessaire. |
| DEC-020 | Le programme tourne initialement sur l’ordinateur personnel du propriétaire et ne réduit pas automatiquement son activité pendant l’usage normal du PC. |
| DEC-021 | L’architecture doit permettre ultérieurement un ordinateur dédié, un modèle local et un changement de fournisseur sans migration narrative majeure. |
| DEC-022 | Le technicien existe dans le MVP comme assistant de diagnostic et de recommandation en lecture seule; il ne modifie ni code, ni données actives, ni déploiement. |
| DEC-023 | Le MVP ne simule ni vieillissement, ni maladie, ni grossesse, ni mort. Les blessures peuvent exister si elles sont causales et récupérables. |
| DEC-024 | Une conversation interrompue par une panne ou un arrêt est clôturée automatiquement sans inventer la suite. |
| DEC-025 | Le budget API initial n’est pas fixé, mais la mesure des coûts, les alertes et les limites configurables sont obligatoires. |
| DEC-026 | Le modèle de langage et le fournisseur sont des composants remplaçables derrière un adaptateur; le moteur local demeure l’autorité. |
| DEC-027 | LM Studio Bionic est l’environnement de développement initial envisagé, mais ne constitue pas une dépendance du produit ni du dossier. |

## Clarifications approuvées (2026-08-03)

Clarifications émises par le propriétaire en approbation de `docs/AUDIT_INITIAL.md`. Elles précisent le dossier maître sans le contredire et font partie des décisions autoritatives.

| ID | Clarifie | Décision retenue |
| --- | --- | --- |
| CLA-001 | Autorité vs perceptibilité du propriétaire (A1) | Deux dimensions **indépendantes**. **Niveau d’autorité** : observateur, interlocuteur externe, participant, régisseur, administrateur. **Perceptibilité** : perceptible directement, perceptible indirectement par ses conséquences, non perceptible. Une intervention n’entre dans les perceptions/croyances/souvenirs d’un personnage que si elle est perceptible selon le mode et la situation. |
| CLA-002 | Rapport temps simulé/réel (A2) | Rapport **1:1** pendant le fonctionnement. Pause ou avance administrative possible ; **aucune accélération permanente par défaut**. À l’arrêt, rattrapage condensé : routines/besoins déterministes, seuls événements significatifs, nombre d’appels au modèle limité, résumé de période, conséquences importantes conservées dans le canon. |
| CLA-003 | Modification directe d’un personnage (A4) | Modification **directe** = contourner l’évolution normale pour changer une donnée propre au personnage (traits/personnalité, valeurs/intérêts/préférences/libido, besoins/états internes, objectifs, relations, souvenirs/croyances/perceptions, apparence/état physique/blessure, champs protégés canoniques). Protocole obligatoire : interpréter, présenter les champs concernés, expliquer conséquences/effets secondaires, créer un point de restauration, confirmation explicite, journalisation séparée de ce que les personnages peuvent percevoir. Une intervention d’environnement n’est **pas** automatiquement une modification directe (ex. ajouter un piano = modification du monde ; augmenter l’intérêt musical = modification directe). Pour un personnage canonique, toute modification d’un champ **figé** exige une **confirmation renforcée** mentionnant explicitement l’altération de la fidélité canonique. |
| CLA-004 | Sûreté de `init --force` (Phase 1) | `init --force` est une commande **destructive réservée au développement** (reconstruit la base locale de développement). **Refusé par défaut** pour tout monde marqué réel, persistant ou non-développement. Aucune interface Discord ni commande du propriétaire ne pourra l’exécuter implicitement. |