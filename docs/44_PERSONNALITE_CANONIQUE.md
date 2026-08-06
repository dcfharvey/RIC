# Première disposition canonique de personnalité

**Statut :** implémenté — premier sous-lot de DEC-041, sans décision autonome

## Portée livrée

Chaque personnage qui porte le composant versionné
`personality.big_five_attachment` reçoit à l'instanciation une disposition
canonique immuable, dérivée de la définition publiée du gabarit :

- Big Five continus : extraversion, agréabilité, conscienciosité, ouverture et
  réactivité au stress;
- pour chaque trait : moyenne, variabilité, inertie et signatures
  situationnelles déclaratives;
- attachement général : anxiété et évitement, distincts des Big Five.

La migration `0026_personality_disposition.sql` conserve ces données à part du
profil physiologique historique. Les gabarits MVP v1 ne sont pas modifiés : les
quatre habitantes sapientes sont créées depuis leurs versions v2. Patoune n'a
pas ce composant, ce qui maintient l'absence de composant comme état valide.

Les valeurs MVP sont une calibration initiale explicite des descriptions gelées
de `docs/08_CASTING_MVP.md`. Elles sont vérifiables, mais ne prétendent pas être
un diagnostic psychologique réel; toute évolution future passe par une révision
protégée, jamais par une mutation de ligne.

## Frontières garanties

`PersonalityService` ne retourne que le profil et les modulations déclarées
d'une situation. Il ne produit ni action, ni dialogue, ni émotion, ni valeur,
ni relation, ni décision. Les traits restent donc des tendances qui modulent
ultérieurement l'évaluation et l'arbitrage, conformément à PER-001.

La disposition apparaît dans le digest d'état canonique et dans le banc
d'essai; sa provenance reste l'événement d'instanciation qui référence la
version de gabarit. Elle n'ajoute pas un second événement à l'histoire, car
aucune modification autonome de disposition n'est permise dans ce lot.

La disposition canonique est la première des trois représentations de PER-003.
La conception de soi attend le système de croyances et la réputation d'autrui
attend les perceptions et relations directionnelles : les enregistrer avant
leurs sources fabriquerait une pseudo-subjectivité sans preuve.

## Tests et suite

Les tests couvrent l'instanciation depuis le gabarit v2, l'absence valide chez
Patoune, l'immuabilité SQLite, la validation négative et l'absence de commande
comportementale. Le prochain lot vivant est valeurs/préférences, puis objectifs
et intentions persistantes; ils consommeront les modulations sans les confondre
avec des ordres.
