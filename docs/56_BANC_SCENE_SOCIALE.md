# Banc de scène sociale — conversations brèves et jetables

**Statut :** première tranche livrée le 6 août 2026.

`python -m vivarium scene-bench --max-turns 4` construit une scène Sophie-Erika
en mémoire. Un ordonnanceur crée au plus quatre occasions de parole : Sophie,
puis Erika, puis Sophie, etc. Une occasion est une permission de répondre,
jamais une obligation de parler; `no_action` est donc un résultat normal.

La rotation et la borne sont déterministes afin que le banc soit reproductible
et qu'un dialogue ne boucle pas sans contrôle. Le contenu reste proposé par le
LLM et passe par le contrat `scene_turn`. Au premier refus de validation ou à
une panne du fournisseur, le banc s'arrête et rend l'anomalie visible.

Ce n'est pas encore l'orchestrateur du monde vivant : il n'initie pas une scène
de lui-même et ne décide pas qu'une situation mérite une conversation. Il sert
à éprouver le contrat multi-tours, les budgets, les retries et les sorties de
dialogue avant ce raccordement.

**Premier essai réel — 6 août 2026 :** quatre occasions Sophie-Erika ont
produit quatre paroles valides et alternées, sans anomalie. L'exécution a
duré environ 15 secondes sur Gemma local; ce chiffre est une observation
ponctuelle, pas encore une cadence produit.
