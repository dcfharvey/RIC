# Correctif alpha `0.1.0a11` — arbitrage social avant autonomie

## Fait observé

Le monde restait structurellement sain et les activités autonomes progressaient,
mais aucune scène nouvelle n'avait été ouverte pendant environ deux heures. Les
quatre sapientes partageaient pourtant le salon.

Le cycle social sait employer le début canonique d'un `idle` comme occasion
unique de rencontre. Or le runtime exécutait d'abord `AutonomyCycle`, qui
remplaçait cet `idle` par une activité choisie. Lorsque `SocialSceneCycle`
cherchait ensuite les attentes encore actives, leur source avait légalement
disparu. Les deux composants étaient corrects isolément; leur ordre créait une
famine d'occasion sociale.

## Correction

Après les transitions déterministes, le runtime donne d'abord au cycle social
la possibilité de découvrir et traiter une occasion déjà vraie. Il exécute
ensuite l'autonomie d'activité, puis l'orchestrateur d'événements directs.

```text
transition déterministe due
→ découverte/avancement social borné
→ décision autonome d'activité bornée
→ événements directs perceptibles bornés
```

Ce changement ne crée aucune minuterie sociale. La scène exige toujours un
événement source unique, des participantes sapientes réellement co-localisées
et une attente encore active au moment de sa découverte. Une activité reste
libre de remplacer l'attente après cette observation. Si elle entraîne plus
tard un départ, la scène sera interrompue par les règles existantes.

## Contrat de régression

Dans un monde ayant déjà consommé sa scène initiale, deux sapientes commencent
une attente commune. Le runtime doit :

1. ouvrir une nouvelle scène sourcée;
2. offrir son premier tour borné;
3. permettre ensuite au choix autonome valide de remplacer l'`idle`;
4. ne produire ni seconde scène pour la même source, ni appel non borné.
