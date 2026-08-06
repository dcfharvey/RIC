# Vivarium Social — Journal canonique des échanges ChatGPT ↔ DeepSeek

**Version :** 0.1  
**Date de reconstruction :** 5 août 2026  
**Source principale :** chat partagé « 1 milliard de tokens »  
**Période couverte :** 3 août 2026, 09 h 50 → 5 août 2026, 08 h 56 (America/Toronto)  
**Portée :** gouvernance, mandats, rapports, validations, jalons techniques et état de reprise

## 1. Objet du journal

Ce document reconstruit la boucle de travail réelle du Vivarium Social :

1. l’assistante ChatGPT agit comme architecte, chercheuse et auditrice;
2. le propriétaire transmet les mandats;
3. DeepSeek V4 Flash, utilisé dans LM Studio Bionic, agit comme exécutant technique;
4. le propriétaire retransmet les plans, rapports, preuves et captures;
5. l’assistante accepte, refuse ou corrige le lot;
6. le propriétaire effectue les validations perceptives qui exigent l’usage réel de l’interface.

Le journal complète les documents normatifs du dépôt. Il ne remplace ni Git, ni les tests, ni le dossier maître.

## 2. Niveaux de preuve

Chaque information doit conserver son origine.

- **RAPPORTÉ PAR DEEPSEEK** : présent dans un plan ou rapport retransmis par le propriétaire.
- **ACCEPTÉ PAR L’ARCHITECTE** : jugé conforme dans la conversation après revue du rapport ou d’une vérification ciblée.
- **VALIDÉ PAR LE PROPRIÉTAIRE** : test perceptif ou visuel réalisé sur son ordinateur.
- **DOCUMENT FOURNI** : fichier joint à la conversation.
- **NON VÉRIFIÉ DIRECTEMENT ICI** : le code et le dépôt local du propriétaire n’ont pas été inspectés par la présente reconstruction.

Un rapport indiquant « 428 tests réussis » est donc une preuve rapportée et acceptée dans le chat, pas une nouvelle exécution de ces tests dans cet environnement.

## 3. Protocole de gouvernance confirmé

### Assistante architecte

- consulte la littérature scientifique et technique pertinente;
- transforme les résultats robustes en architecture et exigences;
- découpe le travail en lots bornés;
- fixe le point de départ Git, le périmètre autorisé et les interdictions;
- exige des tests et un rapport de livraison précis;
- audite la preuve, pas seulement la phrase « les tests passent »;
- verrouille le lot suivant jusqu’à validation formelle.

### DeepSeek V4 Flash dans LM Studio Bionic

- inspecte le dépôt local;
- propose des plans avant les changements structurants;
- modifie seulement les fichiers autorisés;
- lance les tests et diagnostics;
- crée les commits demandés;
- produit un rapport avec hashes, fichiers, preuves, régression et limites;
- s’arrête avant le lot suivant.

### Propriétaire

- assure le relais obligatoire entre les deux IA;
- tranche les choix créatifs ou personnels;
- transmet les rapports sans les résumer lorsque la preuve détaillée compte;
- teste l’interface réelle dans son navigateur;
- confirme ou refuse la validation visuelle.

## 4. Chronologie des jalons techniques

| Étape | Commit rapporté | Tests rapportés | Résultat reconstruit |
| --- | --- | ---: | --- |
| Phase 0 — socle du projet | `1e92a4b` | 11 | Livrée; correctif documentaire ensuite. |
| Correctif documentaire Phase 0 | `2313367` | — | Documentation corrigée avant Phase 1. |
| Phase 1 — persistance et vérité canonique | `af2823c` | 33 | Acceptée; SQLite, journal canonique et CLI de base. |
| Règle documentaire | `650af37` | — | Ajoutée avant Phase 2. |
| Phase 2.1 — horloge | `9377e18` | 44 | Acceptée; lecture pure, pause et reprise. |
| Phase 2.2 — lieux, objets et graphe spatial | `ef91b7e` | 61 | Acceptée; neuf lieux et trajets dirigés. |
| Phase 3.1 — identités et présence | `3757c05` | 77 | Acceptée; quatre habitantes persistantes. |
| Phase 3.2A — besoins dérivés | `1c87882` | 89 | Acceptée; arithmétique reproductible. |
| Phase 3.2B — activités et effets | `d2a625b` | 104 | Acceptée; dénominateur commun 36 et migrations des restes. |
| Phase 3.2C — politique déterministe | `3f53e62` | 126 | Acceptée; audit de 24 h reproductible. |
| Phase 3.3A — attente dynamique et sommeil | `fc6dfc1` | 143 | Acceptée; arrêt avant blessures. |
| Phase 3.3B1 — modèle de blessure | `f1335ca` | 164 | Acceptée; migration `0008`. |
| Phase 3.3B2 — effets mécaniques | `0ae2f049e7bf843dfce0889cc82af3d2e660b61c` | 188 | Livrée; revue ciblée requise. |
| Correctif 3.3B2 | `1bb93edba7d4b40cf962c1f65b6da1bb6f6defb9` | 188 | Contrats et preuves corrigés. |
| Phase 3.3C — exécution longue | `35ad495e3571c0a74a59998af2c6bb71cfe07ad8` | 207 | Livrée, puis audit de fermeture. |
| Fermeture 3.3C | `a63964976d37397d502dbee101dbb231537ec3f3` | 220 | Scénarios 24 h et 7 jours acceptés. |
| Correctifs de fermeture Phase 3 | `7e5459eaac5c2ad8ae8dcb53a197863575ab4914` | 228 | Phase 3 fermée techniquement. |
| Consolidation documentaire v0.2 | `07b36ccb567ec09641f66dd3c6c7b08c8c5c8454` | 228 | Sept documents actifs consolidés et archives rangées. |
| Phase 4.1A — lectures administratives | `045c5650b768814c2df705a822f54479dd9fc382` | 249 | Livrée; bug de blessure dérivée découvert. |
| Correctifs 4.1A | `4425158d3a1372a35b9abb49f772837cb3ff46dc` | 263 | 4.1A acceptée. |
| Phase 4.1B — commandes sûres | `b064258e9a2a3270c94d66218cf55a8bc0f61c7c` | 296 | Fonctionnellement approuvable; couverture B-1/B-4 insuffisante. |
| Correctifs de couverture 4.1B | `4156d304f26198b8225d1e344b4247581306e700` | 309 | 4.1B officiellement validée. |
| Phase 4.1C — serveur HTTP local | `89f291da6811234ed3d15df9349a553c9ef44d60` | 383 | Livrée; durcissement requis. |
| Correctifs 4.1C | `e59d18ee39e647bdbd743f6bcc70a477cb771549` | 413 | 4.1C officiellement validée. |
| Phase 4.1D — tableau de bord | `079c716b5823d0c554fff8601f05eb8d519cb9c8` | 428 | Techniquement fonctionnelle, mais validation visuelle refusée. |

## 5. Boucles de revue ayant changé le résultat

### 5.1 Les plans ne sont pas approuvés automatiquement

Plusieurs plans de DeepSeek ont été renvoyés avant code pour corriger des choix structurants :

- horloge pure plutôt qu’un événement à chaque lecture;
- graphe spatial dirigé et opérations bidirectionnelles atomiques;
- retrait du piano du seed initial;
- suppression de champs futurs ou redondants;
- division de la Phase 3 en sous-lots;
- correction des calculs fractionnaires pour garantir l’indépendance à la fréquence de matérialisation;
- représentation correcte du sommeil, des changements de régime et des restes;
- transaction unique ou frontières explicites pour les commandes administratives;
- jeton HTTP dans un en-tête plutôt que dans le corps JSON.

### 5.2 Les tests doivent exercer la vraie voie

Le correctif 4.1B B-1/B-4 illustre la règle : un test portant le bon nom ne suffit pas. Il devait provoquer une vraie exception inattendue dans la voie de production, vérifier le masquage du détail sensible, la réutilisabilité de SQLite et l’absence de mutation pour quatorze catégories de refus.

### 5.3 Une livraison verte peut rester refusée

Le tableau de bord 4.1D passait 428 tests et servait correctement ses fichiers. Le propriétaire l’a tout de même refusé après inspection visuelle. La raison est méthodologique : les tests structurels ne peuvent pas approuver seuls la clarté d’une interface.

### 5.4 Les problèmes hors périmètre sont consignés

Lorsque l’audit découvre un site mineur sans couverture ou une idée future, le mandat peut imposer de le reporter. DeepSeek ne doit pas effectuer de correction opportuniste hors du lot autorisé.

## 6. État de reprise exact

### État rapporté au dernier mandat technique

- branche : `main`;
- HEAD : `079c716b5823d0c554fff8601f05eb8d519cb9c8`;
- tests : 428 réussis;
- 4.1A : validé;
- 4.1B : validé;
- 4.1C : validé;
- 4.1D : implémenté, fonctionnel, non approuvé visuellement;
- 4.1E : non commencé et explicitement interdit.

### Verdict actuel

**VALIDATION 4.1D REFUSÉE — CORRECTIONS VISUELLES ET D’AFFICHAGE EN ATTENTE DU RAPPORT DE DEEPSEEK.**

La conversation partagée contient le mandat correctif complet envoyé à DeepSeek, mais aucun rapport ultérieur de son exécution.

### Corrections demandées pour 4.1D

1. **Énergie** : confirmer l’unité interne et afficher `6985` comme `69,85 %` si la convention est bien le centième de pourcentage.
2. **Dates** : convertir les ISO UTC en heure locale lisible, sans millisecondes visibles.
3. **Journal** : limiter à 15 ou 20 entrées, ordre récent confirmé, hauteur contrainte et défilement interne.
4. **Grille** : rééquilibrer le journal et les commandes; supprimer les grands espaces vides.
5. **Succès** : rendre le message temporaire et empêcher les minuteries concurrentes.
6. **Liste des personnages** : structure compacte avec nom principal, lieu secondaire et énergie alignée.
7. **Fiche personnage** : formats cohérents et aucun `null`, `undefined` ou objet brut.
8. **Barre supérieure** : monde, statut lisible, date locale compacte et bouton de rafraîchissement.

### Périmètre du correctif 4.1D

Fichiers autorisés :

- `src/vivarium/static/index.html`;
- `src/vivarium/static/style.css`;
- `src/vivarium/static/app.js`;
- `tests/test_dashboard.py`;
- `CHANGELOG.md`.

Toute nécessité de toucher au moteur, au schéma, aux seeds, au casting ou à `admin.py` doit provoquer un arrêt et une nouvelle approbation.

## 7. Prochaine boucle autorisée

1. Le propriétaire transmet ou a transmis le mandat correctif 4.1D à DeepSeek.
2. DeepSeek inspecte les JSON réels, confirme l’unité d’énergie et l’ordre du journal.
3. DeepSeek modifie seulement le périmètre autorisé, lance la régression et crée un commit correctif unique.
4. Le propriétaire retransmet le rapport intégral.
5. L’assistante audite le rapport et les preuves.
6. Le propriétaire refait la validation visuelle dans le navigateur.
7. 4.1D est approuvé ou une nouvelle correction bornée est demandée.
8. 4.1E reste verrouillé jusqu’à approbation explicite.

## 8. Recherche et architecture poursuivies hors de la boucle de code

Après l’arrêt du chantier technique pour la soirée, la conversation a continué sur la couche cognitive et sociale :

- perception subjective;
- croyances vraies ou fausses;
- mémoire épisodique, sémantique et prospective;
- relations multidimensionnelles et directionnelles;
- activités conjointes;
- conversation de groupe et rôles d’écoute;
- triades, exclusion structurelle et interprétation du rejet;
- intimité comme régulation du contact;
- ennui comme signal de sous-engagement plutôt que commande;
- romance, sexualité, consentement actuel et pouvoir administratif;
- évaluation longitudinale et absence de juge LLM unique.

Le propriétaire a ensuite accordé une autorisation large : les conclusions robustes peuvent être intégrées directement aux documents; seules les décisions qui changent profondément l’identité créative doivent lui être soumises.

Cette autorisation ne permet pas de déclarer le code modifié sans rapport de DeepSeek et ne déverrouille pas 4.1E.

## 9. Documents joints recensés

La conversation partagée référence 35 pièces jointes : 24 images, 10 fichiers Markdown et un fichier texte. Les documents nommés incluent notamment :

- `00_DOSSIER_MAITRE_IA.md`;
- `01_REGISTRE_DECISIONS.md`;
- `02_MATRICE_EXIGENCES.md`;
- `03_DECISIONS_OUVERTES.md`;
- `05_GABARITS.md`;
- plusieurs rapports collés en Markdown ou texte;
- des captures de LM Studio Bionic et du tableau de bord.

Le transcript source conserve leur emplacement et leur nom. Leur contenu binaire n’a pas été fusionné automatiquement dans ce journal.

## 10. Règles pour les futurs ajouts

Chaque nouvelle boucle devrait ajouter une entrée contenant au minimum :

- date et sous-lot;
- HEAD de départ;
- mandat intégral ou référence au mandat;
- rapport intégral ou référence au rapport;
- commit produit;
- fichiers modifiés;
- total exact des tests;
- preuves ciblées;
- verdict de l’assistante;
- validation du propriétaire, si perceptive;
- problèmes reportés;
- prochaine action autorisée;
- travaux explicitement interdits.

Une ancienne exigence remplacée ne doit pas être effacée : elle est marquée **REMPLACÉE**, avec un lien vers la décision nouvelle.

## 11. Conclusion canonique de reprise

Le Vivarium n’est plus au stade des Phases 0 à 3. Le moteur déterministe de base et la documentation v0.2 ont été rapportés comme fermés. La Phase 4.1 a produit les lectures administratives, les commandes sûres, le serveur HTTP et un premier tableau de bord.

Le point de reprise n’est pas « concevoir la Phase 4 ». Il est :

> recevoir et auditer le rapport des correctifs visuels de 4.1D, puis faire réaliser une nouvelle validation visuelle par le propriétaire.

Tant que cela n’est pas fait, 4.1E demeure non commencé.
