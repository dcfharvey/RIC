# Codex task — WO90

Implémenter et qualifier `docs/90_WORK_ORDER_BOOTSTRAP_RODAGE_V2.md` à partir de la branche `chatgpt/wo90-rodage-v2-bootstrap`.

Base fermée : `9dd02538c54e06a771423e1c00a5272260b2d0d5` (`0.2.0a1`, schéma 55).

Décisions produit à rendre représentables par des mécanismes génériques :

- extérieur au-delà du terrain accessible et extensible vers de vrais lieux hors foyer, sans omniscience des agents;
- `sleep` légal dans tout lieu canonique accessible;
- bain/douche dans la famille d'hygiène personnelle; confort possible mais aucun nouvel état persistant de confort dans ce lot.

T0 produit : Sophie au travail comme photographe journalistique, retour prévu à 16 h; Erika au salon en train de jouer; Patoune endormi au salon blotti contre Erika; Chuu dans le bain, se détend/se réhydrate et s'apprête à sortir; Luna arrive pour la première fois en taxi avec son sac d'effets personnels.

Ne pas inventer les détails non décidés. Ne pas coder de cas spécial par personnage. Préserver les invariants `LLM propose, moteur valide`, canon ≠ perception/croyance, et H/φ/P comme physiologie active propriétaire.

Le T0 exact doit être l'heure EDT réelle du bootstrap persistant finalement autorisé; aucun événement officiel n'existe à 12 h 24, donc ne pas reconstruire ou rétrodater un faux passé.

Avant démarrage persistant : tests ciblés, falsifications, répétition T0 sur SQLite jetable, préflight read-only, observation Hugin, compileall, suite complète, puis consignation du HEAD/version/schéma/migration/tests dans WO90.

WO90 reste pré-rodage : ne pas démarrer l'histoire persistante officielle pendant l'implantation.
