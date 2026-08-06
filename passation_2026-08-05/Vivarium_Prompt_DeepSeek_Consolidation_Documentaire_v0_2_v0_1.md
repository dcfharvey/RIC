# Prompt prêt à envoyer à DeepSeek — Consolidation documentaire v0.2

**Projet :** Vivarium social artificiel  
**Type de réponse demandé :** plan détaillé seulement  
**Point de départ officiel :** commit `7e5459eaac5c2ad8ae8dcb53a197863575ab4914`  
**État confirmé :** Phase 3 techniquement fermée  
**Tests confirmés :** 228 réussis  
**Verdict confirmé :** `FERMETURE APPROUVABLE`  
**Étape demandée :** planification de la consolidation documentaire v0.2 uniquement

---

## 0. Règle d’autorité et méthode

Avant de répondre, inspecte réellement le dépôt et les documents présents à sa racine.

Ordre d’autorité :

1. code, migrations et tests du dépôt au commit officiel;
2. rapport de fermeture technique de la Phase 3;
3. documents post-audit présents à la racine;
4. dossier maître actuellement présent dans le dépôt;
5. présente instruction.

Documents post-audit actuellement non suivis :

- `Vivarium_Exigences_Normatives_Post_Audit_v0_1.md`;
- `Vivarium_Demande_Changement_Post_Audit_v0_2.md`;
- `Vivarium_Feuille_Route_Post_Audit_v0_1.md`.

Autres documents de référence à localiser si présents :

- dossier maître actuel;
- registre d’audits;
- index maître des décisions;
- mémoire d’assistante;
- documentation technique de la Phase 3;
- `README.md`;
- `CHANGELOG.md`.

### Règle méthodologique impérative

Si deux documents :

- se contredisent;
- utilisent des termes incompatibles;
- décrivent des versions différentes;
- donnent des statuts différents à une même décision;
- ou nécessitent une interprétation normative;

alors :

```text
ne fusionne pas silencieusement
→ cite les deux versions
→ explique le conflit
→ recommande une décision
→ attends l’approbation
```

Aucune harmonisation silencieuse n’est autorisée.

---

## 1. But de la consolidation v0.2

L’objectif est de produire une nouvelle version du dossier maître qui reflète fidèlement :

- la fermeture technique de la Phase 3;
- les contrats stabilisés du moteur canonique déterministe;
- les décisions issues des audits;
- les limites connues;
- les dettes reportées;
- la séquence officielle vers la Phase 4;
- les invariants normatifs désormais approuvés.

La consolidation ne doit pas inventer de nouvelle architecture.

Elle doit :

```text
prendre les documents existants
→ identifier ce qui est encore valide
→ intégrer les décisions post-audit
→ retirer ou marquer l’obsolète
→ produire une version maître cohérente
```

---

## 2. Travail demandé maintenant

Produis uniquement le **plan détaillé de consolidation documentaire v0.2**.

Tu dois :

- inspecter tous les documents concernés;
- dresser leur carte;
- identifier leur rôle;
- repérer les doublons;
- repérer les contradictions;
- repérer les passages obsolètes;
- proposer la structure du dossier maître v0.2;
- proposer la stratégie de fusion;
- proposer les règles de traçabilité;
- proposer les fichiers à archiver, remplacer, conserver ou intégrer;
- définir les validations finales;
- signaler les décisions nécessitant une approbation.

Tu ne dois pas :

- modifier un fichier;
- créer le dossier maître v0.2;
- déplacer ou supprimer un document;
- créer un commit;
- commencer la Phase 4;
- changer une décision technique;
- réécrire l’historique;
- intégrer silencieusement un conflit.

Arrête-toi après le plan.

---

## 3. Inspection initiale obligatoire

Commence par confirmer :

### Dépôt

- HEAD exact;
- branche;
- état de l’arbre;
- fichiers non suivis;
- version Python;
- résultat des 228 tests, si tu les exécutes;
- dernier commit de fermeture.

### Documents

Pour chaque document trouvé, donne :

- nom exact;
- chemin;
- statut Git;
- version indiquée;
- date ou période couverte;
- rôle;
- autorité;
- portée;
- état :
  - actif;
  - partiellement obsolète;
  - obsolète;
  - historique;
  - à intégrer;
  - à archiver;
  - inconnu.

N’infère pas l’autorité d’un document uniquement à partir de son nom. Vérifie son contenu.

---

## 4. Carte documentaire attendue

Établis une carte au minimum pour :

### Dossier maître actuel

- structure;
- version;
- portée;
- décisions encore valides;
- passages dépassés par la Phase 3;
- sections absentes.

### Exigences normatives post-audit

- invariants;
- décisions obligatoires;
- interdictions;
- terminologie;
- statuts;
- éléments déjà implémentés;
- éléments futurs.

### Demande de changement post-audit

- changements demandés;
- raison;
- statut;
- éléments acceptés;
- éléments non encore intégrés;
- effets sur le dossier maître.

### Feuille de route post-audit

- ordre des phases;
- jalons;
- dépendances;
- préconditions;
- prochaines étapes;
- éléments devenus obsolètes après fermeture de la Phase 3.

### Registre des audits

- audits réalisés;
- conclusions;
- décisions issues des audits;
- points encore ouverts;
- couverture scientifique et technique.

### Index maître des décisions

- décisions normatives;
- références croisées;
- doublons;
- décisions périmées;
- décisions à renuméroter ou consolider.

### Mémoire d’assistante

- éléments utiles au contexte;
- éléments qui ne doivent pas devenir des exigences normatives;
- risques de mélanger mémoire de travail et documentation officielle.

### Documentation technique

- architecture;
- modules;
- schéma;
- invariants;
- tests;
- limitations;
- état de Phase 3.

### README et CHANGELOG

- rôle;
- niveau de détail;
- mises à jour nécessaires;
- informations à ne pas dupliquer dans le dossier maître.

---

## 5. Structure proposée pour le dossier maître v0.2

Propose une structure claire et versionnée.

La structure devrait probablement inclure :

1. statut du document;
2. portée;
3. glossaire;
4. principes d’autorité;
5. architecture générale;
6. moteur canonique déterministe;
7. temps et horloge;
8. monde et espace;
9. personnages;
10. besoins;
11. activités;
12. blessures;
13. politique déterministe;
14. journal et causalité;
15. transactions et atomicité;
16. reproductibilité;
17. audits et preuves;
18. limites connues;
19. dettes techniques;
20. systèmes futurs;
21. séquence vers Phase 4;
22. règles de changement;
23. historique des versions;
24. annexes et références.

Pour chaque section proposée :

- but;
- contenu source;
- documents d’origine;
- statut normatif ou informatif;
- passages à intégrer;
- passages à éviter;
- liens vers les preuves techniques.

---

## 6. Distinction normative / descriptive / historique

Le dossier maître v0.2 doit distinguer explicitement :

### Normatif

Ce qui doit être respecté.

Exemples :

- moteur canonique seul autorité;
- LLM non autoritaire;
- transactions atomiques;
- lecture sans effet de bord;
- temps simulé;
- journal append-only;
- interdictions de contournement;
- séparation vérité / perception / croyance / mémoire;
- confirmation pour changements profonds.

### Descriptif

Ce qui décrit l’implémentation actuelle sans devenir une règle éternelle.

Exemples :

- noms de classes;
- nombre actuel de modules;
- SQLite;
- noms de tables;
- nombre de tests;
- personnages techniques.

### Historique

Ce qui explique :

- pourquoi une décision a été prise;
- quel audit l’a motivée;
- quelles alternatives ont été rejetées;
- quel lot l’a implémentée.

Ne mélange pas ces trois niveaux.

---

## 7. Statut de la Phase 3

Le dossier maître v0.2 doit refléter exactement :

```text
Phase 3 — techniquement fermée
Commit officiel :
7e5459eaac5c2ad8ae8dcb53a197863575ab4914

Tests :
228 réussis

Verdict :
FERMETURE APPROUVABLE
```

Il doit résumer les capacités prouvées :

- horloge canonique;
- monde actif / paused;
- redémarrage;
- besoins;
- activités;
- déplacements;
- énergie;
- blessures;
- politique;
- journal;
- reproductibilité;
- rollback;
- endurance 24 h / 7 jours;
- audits structurels;
- audits de chaînes;
- digests;
- projection sémantique.

Il doit aussi conserver les limites :

- reconstruction event-sourced complète non garantie;
- définitions actuellement immuables;
- absence de RNG;
- personnages encore techniques;
- aucune interface administrative complète;
- aucun LLM intégré au moteur canonique;
- aucune Phase 4 commencée.

---

## 8. Dettes techniques à documenter

Inclure comme dettes reportées, sans les transformer en bloquants :

- `upgrade_dev_profiles` sans transaction explicite;
- `destroy_world` incomplet;
- `README.md` partiellement en retard;
- éventuelle documentation des événements init/seed;
- absence d’outils lint/typecheck/couverture configurés;
- reconstruction event-sourced complète non garantie;
- immutabilité actuelle des définitions.

Pour chaque dette :

- identifiant;
- description;
- sévérité;
- impact;
- moment recommandé;
- bloquante ou non;
- dépendances.

---

## 9. Terminologie à stabiliser

Inspecte et propose une terminologie unique pour :

- moteur canonique;
- moteur déterministe;
- moteur canonique déterministe;
- état canonique;
- temps mural;
- temps canonique;
- temps simulé;
- événement;
- journal;
- séquence;
- causalité;
- matérialisation;
- projection sémantique;
- digest;
- activité;
- besoin;
- blessure;
- régime;
- arête / edge;
- nœud / node;
- propriétaire / administrateur / owner;
- LLM / agent / personnage;
- monde / résidence / vivarium.

Pour chaque terme :

- terme canonique;
- synonymes tolérés;
- termes à éviter;
- langue officielle du code;
- langue officielle de la documentation.

Recommandation actuelle probable :

```text
documentation principale en français
code, classes, événements et champs en anglais
glossaire bilingue pour les termes techniques
```

Ne change pas cette convention sans approbation.

---

## 10. Décisions d’architecture à intégrer

Vérifie que la v0.2 intègre correctement au minimum :

- moteur canonique seul arbitre;
- LLM limité aux propositions/interprétations/dialogues;
- vérité canonique distincte de perception, interprétation, croyance et mémoire;
- autorité et perceptibilité indépendantes;
- temps réel 1:1 avec pause;
- reprise sans rattrapage en pause;
- pas d’âge, maladie ou mort en MVP;
- blessures non mortelles;
- 4 personnages;
- 9 lieux initiaux;
- impossibilité de quitter sans autorisation;
- admin comme entité supérieure connue;
- changements profonds avec explication, checkpoint et confirmation;
- traits cachés;
- relations évolutives;
- préférences naturelles;
- SQLite;
- append-only;
- snapshots/checkpoints distincts des sauvegardes;
- replay indépendant du LLM;
- interface comme client du moteur;
- aucun accès direct SQLite depuis l’interface;
- Command API future;
- Prepared Change future;
- Phase 4 = vertical slice administratif.

Distingue ce qui est :

- déjà implémenté;
- normatif mais pas encore implémenté;
- futur;
- hors périmètre actuel.

---

## 11. Systèmes scientifiques futurs

Les audits scientifiques doivent être intégrés comme exigences de conception futures, pas comme fonctionnalités déjà présentes.

Au minimum :

- perception;
- croyances;
- motivation;
- personnalité;
- attachement;
- valeurs;
- objectifs;
- décision;
- mémoire;
- relations;
- émotions;
- ontologie;
- persistance;
- administration.

Pour chacun :

- résumé normatif;
- principes établis;
- décisions de conception;
- exclusions;
- dépendances;
- lot futur probable;
- ce qui ne doit pas être implémenté prématurément.

Ne transforme pas les audits en pseudo-code complet dans le dossier maître si ce niveau de détail appartient à des annexes.

---

## 12. Stratégie de fusion

Propose une méthode explicite :

```text
inventaire
→ classification
→ détection de conflits
→ matrice source-cible
→ rédaction v0.2
→ validation croisée
→ comparaison avec code
→ revue finale
→ commit documentaire
```

Pour chaque source :

- sections reprises;
- sections reformulées;
- sections citées;
- sections archivées;
- sections supprimées;
- justification.

Ne supprime jamais une décision historique sans conserver une trace.

---

## 13. Traçabilité

Propose un système minimal de traçabilité.

Chaque décision normative devrait idéalement avoir :

- identifiant;
- titre;
- statut;
- source;
- date;
- phase;
- implémentation;
- tests;
- supersède;
- supersédée par;
- notes.

Exemple :

```text
DEC-TIME-004
Titre : Pause sans rattrapage
Statut : implémenté
Source : audit temporel
Phase : 3
Commit : ...
Tests : ...
```

Ne crée pas une bureaucratie excessive. Le système doit rester utilisable.

---

## 14. Fichiers cibles

Propose quels fichiers devraient exister après consolidation.

Par exemple :

```text
Vivarium_Dossier_Maitre_v0_2.md
Vivarium_Index_Decisions_v0_4.md
Vivarium_Registre_Audits_v1_0.md
Vivarium_Feuille_Route_v0_2.md
Vivarium_Glossaire_v0_1.md
```

Mais ne crée aucun de ces fichiers maintenant.

Pour chaque fichier proposé :

- rôle;
- contenu;
- source;
- statut Git;
- relation avec les anciens documents;
- raison d’exister séparément.

Évite de multiplier les documents sans nécessité.

---

## 15. Archivage et statut des anciens documents

Pour chaque ancien document, propose :

- conserver actif;
- intégrer puis archiver;
- remplacer;
- conserver comme historique;
- supprimer du dépôt futur;
- laisser hors dépôt.

Les documents post-audit ne doivent pas simplement rester éternellement non suivis après consolidation.

Propose une destination claire :

- intégration;
- archive;
- dossier `docs/history`;
- suppression après validation;
- autre.

Aucune action avant approbation.

---

## 16. Validation finale de la v0.2

Propose une checklist de validation :

### Cohérence technique

- commit Phase 3 exact;
- 228 tests;
- 8 migrations;
- contrats d’événements à jour;
- dettes exactes;
- aucune capacité fictive;
- aucune Phase 4 présentée comme implémentée.

### Cohérence normative

- aucun conflit non résolu;
- terminologie stable;
- statuts clairs;
- distinction implémenté / futur;
- autorité des documents claire.

### Cohérence documentaire

- liens internes;
- numérotation;
- références;
- versions;
- dates;
- historique;
- fichiers archivés.

### Relecture

- comparaison avec le code;
- comparaison avec CHANGELOG;
- comparaison avec le rapport de fermeture;
- comparaison avec les documents post-audit.

---

## 17. Périmètre exclu

Ne traite pas encore :

- implémentation Phase 4;
- interface web;
- Discord;
- Command API;
- Prepared Change;
- autorisation;
- confirmations;
- nouveaux personnages;
- remplacement des personnages techniques;
- système psychologique;
- mémoire;
- perception;
- émotions;
- relations;
- LLM;
- export/import;
- sauvegarde utilisateur;
- nouvelle migration;
- refonte du moteur;
- correction des dettes techniques;
- nouveaux tests.

La consolidation peut documenter ces éléments, mais pas les implémenter.

---

## 18. Format exact de la réponse

Réponds avec :

1. **État réel inspecté**
2. **Inventaire documentaire**
3. **Carte d’autorité des documents**
4. **Documents actifs / obsolètes / historiques**
5. **Conflits et ambiguïtés**
6. **Structure proposée du dossier maître v0.2**
7. **Matrice source → section cible**
8. **Terminologie proposée**
9. **Décisions Phase 3 à intégrer**
10. **Audits scientifiques à intégrer**
11. **Dettes et limites à documenter**
12. **Fichiers cibles proposés**
13. **Plan d’archivage**
14. **Système de traçabilité**
15. **Checklist de validation**
16. **Risques documentaires**
17. **Plan de retour arrière**
18. **Décisions nécessitant une approbation**

Pour chaque conflit :

- cite le document;
- cite la section;
- donne les deux formulations;
- explique l’impact;
- recommande une décision.

Ne modifie rien.

---

## 19. Arrêt

Ne crée aucun fichier.

Ne modifie aucun document.

Ne crée aucun commit.

Ne déplace rien.

Ne commence pas la Phase 4.

Termine exactement par :

> Plan de consolidation documentaire v0.2 terminé. Aucun fichier n’a été modifié. J’attends votre approbation avant toute rédaction, intégration, archivage ou préparation de la Phase 4.
