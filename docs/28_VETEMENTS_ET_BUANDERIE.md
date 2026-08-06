# Vêtements et buanderie — conception future

**Statut :** décision d'architecture. À planifier avant son implémentation;
aucune gestion de vêtement n'est encore active dans le moteur.

## Pourquoi ce système mérite d'exister

Une buanderie et des vêtements ne sont pas seulement décoratifs. Ils créent des
faits quotidiens simples et observables : se changer, chercher une tenue propre,
emprunter un vêtement, oublier une lessive, attendre la sécheuse ou discuter
dans une pièce partagée. Ils fournissent ainsi de petites causes sociales sans
forcer de drame ni de dialogue.

La résidence initiale comportera donc une **buanderie**. Sa connexion exacte
au plan sera décidée avec le blueprint de la résidence.

## Modèle minimal visé

Un vêtement sera un objet portable ordinaire, jamais une exception codée pour
un personnage ou une espèce. Il pourra posséder, au minimum :

- une identité, un type et un propriétaire initial facultatif;
- une position réelle : porté, dans un rangement, dans une machine ou posé dans
  un lieu;
- des états quantifiés indépendants : saleté, humidité et usure;
- des tags descriptifs (tenue de sport, pyjama, élégant, etc.) qui ne forcent
  pas un goût ou une action.

Un personnage pourra porter plusieurs objets compatibles; un rangement, une
machine à laver et une sécheuse seront des conteneurs ou installations fixes.
Laver et sécher seront des opérations canoniques à durée définie, avec états
avant/après explicites et journalisés.

## Limites de portée

- Pas de simulation textile physique, de taille détaillée ou d'inventaire de
  chaque paire de chaussettes au lancement.
- Les objets ne sont individualisés que s'ils peuvent avoir une histoire ou un
  effet distinct; une tenue ordinaire peut être représentée comme un ensemble.
- Les préférences vestimentaires et la signification sociale des vêtements
  appartiendront à la future cognition. Le moteur ne conclut pas qu'une tenue
  provoque une émotion ou une attirance.
- Chuu n'aura pas de branche spéciale : son hydratation et l'humidité d'un
  vêtement sont deux états distincts. Leurs interactions éventuelles devront
  être définies comme règles génériques de matière/absorption, plus tard.

## Ordre prudent

1. Ajouter la buanderie au blueprint de résidence, avec ses connecteurs.
2. Étendre la contenance existante au port par personnage et aux équipements.
3. Ajouter les états d'objet et les opérations lavage/séchage testées.
4. Seulement ensuite, permettre à la cognition de choisir une tenue ou de
   déclencher une lessive selon les faits réels.

Cela conserve le principe du Vivarium : le moteur garantit qu'un vêtement est
réellement là, porté, mouillé ou propre; les personnages restent libres de se
soucier — ou non — de ces faits.
