# Calibration de Chuu — hydratation MVP

**Statut :** définie pour le monde d'intégration; aucune résidente persistante
n'est créée par ce document ni par le module associé.

## Intention

Chuu s'inspire de Suu (*Monster Musume*) pour le principe matériel : l'eau
n'est pas une simple jauge de bien-être, elle conditionne sa forme et sa
capacité à raisonner. Chuu reste toutefois une résidente propre au Vivarium;
le moteur ne reproduit ni histoire ni pouvoirs narratifs du personnage source.

La quantité d'eau est un fait canonique. Les signaux de cognition et les
capacités accessibles sont ses conséquences déclaratives. Le futur LLM devra
les recevoir comme contraintes de contexte, pas les contredire ou les raconter
comme une humeur arbitraire.

## Profil v1

La configuration est dans `vivarium.mvp_chuu.CHUU_HYDRATION_PROFILE` et passe
exclusivement par `ResourceEngine.register_resource_profile`, le même chemin
générique que toute ressource d'un futur personnage ou objet.

| Bande | Valeur | Forme humanoïde | Raisonnement complexe | Signal `cognition.clarity` |
| --- | ---: | --- | --- | ---: |
| `puddle_simple` | 0–14 999 | indisponible | indisponible | −80 000 |
| `dehydrated` | 15 000–39 999 | limité | limité | −40 000 |
| `hydrated` | 40 000–79 999 | disponible | disponible | 0 |
| `brilliant` | 80 000–100 000 | disponible | disponible | +80 000 |

Elle commence à `95 000` et perd `1` milli-unité par seconde si rien ne lui
apporte d'eau : une réserve pleine se vide donc en 27 h 46 min 40 s. Cette
cadence rend l'eau socialement pertinente sans demander une surveillance par
tick ou une décision LLM constante.

## Portée et limites

- Le moteur ne force ni émotion ni dialogue : « simple » réduit ce qu'une
  couche cognitive pourra proposer, sans écrire une personnalité stéréotypée.
- `form.humanoid` et `cognition.complex_reasoning` sont des clés de capacité
  déclaratives. Leur exécution détaillée viendra avec le contrat
  moteur–cognition et les capacités exécutables.
- L'absorption future d'eau utilisera `adjust_resource`, qui dérive d'abord la
  valeur au temps demandé, applique un delta exact, et refuse tout dépassement
  sans écriture partielle.
- La qualité de l'eau (minérale, saline, etc.) reste volontairement hors du
  MVP actuel. Elle sera un attribut de liquide/contenu lorsque le système de
  liquides existera, distinct de la quantité d'hydratation.
