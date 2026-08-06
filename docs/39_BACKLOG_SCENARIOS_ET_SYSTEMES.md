# Backlog — scénarios d'intégration et systèmes futurs

**Statut :** idées retenues pour étude ultérieure; aucune n'est un engagement de
MVP ni une autorisation de les implémenter immédiatement.

## Jeux à information contrôlée

- **UNO en cuisine** : premier scénario social à règles publiques, mains privées,
  tours, interaction et petite mémoire sociale. Patoune peut être observatrice,
  perturbatrice ou juge silencieuse selon de futurs comportements animaux.
- **Blackjack** : décision sous incertitude et règles compactes; moins riche pour
  les dynamiques de groupe, car les joueuses affrontent principalement la banque.
- **Poker** : scénario avancé de bluff, mises, croyances, mémoire relationnelle
  et économie. À différer jusqu'aux systèmes de connaissances privées, argent et
  relations dirigées.

Ordre indicatif : UNO, puis blackjack, puis poker. Ces jeux serviront de bancs
d'essai d'intégration : les règles, tours, cartes et conséquences restent
canoniques; les personnages interprètent, parlent et choisissent dans les
limites validées.

## Effort physique et affrontements

Un futur système d'effort est pertinent. Il permet d'arbitrer sport, rivalité,
entraînement, compétition, fuite et confrontation sans déléguer le résultat au
LLM. Son noyau ne doit toutefois pas tenter de reproduire une physique complète.

Modèle envisagé :

```text
action physique proposée
→ préconditions (lieu, équipement, règles de l'épreuve)
→ état canonique (forme, blessure, énergie, ressources, position)
→ résolution déterministe ou pseudo-aléatoire reproductible
→ conséquences canoniques
→ interprétation subjective et narration
```

Les résultats doivent dépendre de capacités déclarées et de l'état présent,
avec un tirage seulement lorsqu'une incertitude réelle est voulue. Chaque tirage
doit être seedé, journalisé et rejouable par le banc d'essai.

### Scénarios proposés

- sport encadré : meilleur premier terrain, avec règles, arbitre et conséquences
  limitées;
- tournoi de MMA : test avancé de fatigue, blessure, consentement, abandon,
  stratégie et spectatrices;
- tournoi de gladiatrices : variante fictionnelle potentiellement utile pour un
  monde différent, mais elle exige avant tout un contrat explicite de violence,
  sécurité, armes, soins et conséquences durables.

### Critères avant implémentation

1. définir les actions physiques et les résultats possibles avant les scores;
2. séparer aptitude stable, condition temporaire, technique, équipement,
   environnement et hasard;
3. ne pas inférer une capacité depuis l'espèce, l'apparence ou une narration;
4. conserver consentement, règles de l'épreuve et arrêt comme faits canoniques;
5. commencer par un sport à conséquences réversibles avant le combat violent;
6. tester les mêmes scénarios avec un seed identique, puis des variations de
   conditions pour détecter les effets émergents.

La conclusion actuelle est donc : très pertinent à terme, mais postérieur au
contrat d'action élargi, aux capacités, à l'équipement et aux règles sociales.
