# Tour social LLM — acte borné dans une scène

**Statut :** première tranche livrée le 6 août 2026.

`SceneTurnService` permet à une participante d'une scène active de produire
au plus une parole ou de ne rien dire. Le tour passe obligatoirement par :

```text
scène active et participantes co-localisées
→ contexte subjectif privé + derniers actes de cette scène
→ admission LLM append-only (`scene_turn`)
→ JSON de parole strict
→ validation destinataire / scène
→ acte de parole append-only
```

La tâche possède son schéma `scene_turn.v1`, distinct du schéma de
déplacement. Les seuls choix sont `no_action` ou `speak`, avec un type parmi
les actes déjà soutenus, un texte de 320 caractères maximum et une
destinataire participante ou `null`. Un retry qui a déjà produit une parole
retourne l'acte existant sans rappeler le modèle.

Le service refusera avant tout appel une scène fermée, une locutrice absente
ou des participantes qui ne sont plus co-localisées. Un texte n'est pas une
preuve : il ne modifie seul ni croyance, ni relation, ni permission, ni
consentement, ni fait canonique. Une panne ou une réponse hors contrat reste
visible dans le résultat technique et laisse la scène intacte.

`python -m vivarium scene-smoke` construit Sophie et Erika dans le salon,
ouvre une scène mémoire et demande exactement un tour à Gemma local. Cette
commande ne crée aucun monde persistant.

**Premier essai réel — 6 août 2026 :** Gemma 4 12B QAT a produit l'acte
`greet` « Salut Erika, je viens d'arriver. », validé et consigné dans la
base mémoire. Aucune anomalie ni écriture persistante n'a été observée.

## Portée et limites

La littérature sur la conversation indique que la fonction d'un tour et son
contenu sont distincts, et que le terrain commun se construit par interaction
plutôt qu'il ne découle automatiquement d'une phrase. Le contrat conserve
donc explicitement acte, locutrice, destinataire et texte. Il n'imite pas la
milliseconde du tour de parole humain : le Vivarium textuel déclenche des tours
significatifs et bornés, selon ses propres règles d'orchestration.

Sources : [Timing in Conversation](https://pmc.ncbi.nlm.nih.gov/articles/PMC10077995/),
[revue sur le common ground](https://pmc.ncbi.nlm.nih.gov/articles/PMC10867054/),
et `sources/02_PARTIE_II_CONCEPTION_SOURCE.md` / `sources/04_PARTIE_IV_DONNEES_SOURCE.md`.

Restent futurs : sélection autonome du prochain tour, confidentialité et
perception auditive, effets sociaux causaux validés, tours de groupe, mémoire
de scène et dialogue prolongé. Aucun de ces éléments n'est inféré par le
texte seul.
