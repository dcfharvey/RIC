# Adaptateur LLM local — LM Studio / Gemma 4 12B

**Statut :** première frontière locale livrée, sans boucle autonome ni écriture
de mémoire par le LLM.

## Ce qui est branché

`vivarium.cognition` parle à l'API native de LM Studio sur
`http://127.0.0.1:1234/api/v1/chat`. Elle permet de demander explicitement
`reasoning: off` à Gemma 4, ce qui évite de brûler le budget de sortie dans une
chaîne de raisonnement avant la décision. Le modèle peut seulement proposer
`no_action` ou une traversée par un connecteur actuellement exposé au personnage.

Le contexte contient une attention factuelle bornée, les événements directs
depuis un curseur donné et les traces subjectives privées du personnage. Il ne
contient ni SQLite, ni journal canonique brut, ni informations cachées d'autrui.
Toute traversée repasse dans `ActionOrchestrator` : les préconditions réelles
restent donc jugées par le moteur. Une réponse malformée, une action inventée
ou un serveur non local est refusé explicitement.
Chaque appel porte aussi un plafond de sortie (`VIVARIUM_LLM_MAX_TOKENS=128` par
défaut), puisqu'il s'agit d'une courte décision JSON et non d'un dialogue.

Ce lot ne prétend pas encore donner personnalité, mémoire narrative ou boucle
de simulation au modèle. Il rend d'abord la connexion et sa frontière testables.

## Installation lorsque le poste sera disponible

Ne place pas le fichier Gemma dans ce dépôt. Les poids restent gérés par LM
Studio, dans son dossier de modèles ou dans tout dossier hors projet que LM
Studio importe/référence. Si tu dois choisir un emplacement, `D:\LLM\Models\Gemma-4-12B\`
est clair; ne copie pas des dizaines de Go dans `C:\AI\Vivarium social`.

1. Dans LM Studio, télécharge ou importe Gemma 4 12B, puis charge-le.
2. Ouvre **Developer** et démarre le serveur local (port par défaut `1234`),
   sans activer le réseau local pour le moment.
3. Copie `config/.env.example` vers `config/.env` (hors Git), sans remplir le
   modèle pour l'instant. Une variable exportée dans le shell garde priorité
   sur ce fichier.

Ensuite, dans un terminal ouvert à la racine du projet, lance :

```powershell
./.venv/Scripts/python.exe -m vivarium llm-status
```

La commande ne lit que LM Studio : elle affiche d'abord la liste des modèles
chargés, même si aucun n'est encore configuré. Copie ensuite l'identifiant
choisi dans `VIVARIUM_LLM_MODEL`, puis relance-la pour confirmation. Elle ne
modifie aucun monde.

Quand le statut est vert, le test réel suivant est :

```powershell
./.venv/Scripts/python.exe -m vivarium llm-smoke
```

Il construit un monde d'intégration dans SQLite **en mémoire**, demande un seul
tour à Gemma pour Sophie, passe la proposition par le moteur canonique et affiche
la décision, le résultat de validation et l'éventuel événement. Il n'utilise ni
la base de développement ni une histoire MVP. Un refus moteur reste un résultat
sain : il prouve que Gemma n'a pas pu contourner les règles.

Le programme n'essaie pas de lancer LM Studio, télécharger un poids ou choisir
une quantification en silence. Tu charges le modèle; le code se connecte au
serveur déjà local.

## Sources et limites

La route et le démarrage du serveur sont documentés par LM Studio :
[serveur local](https://lmstudio.ai/docs/developer/core/server) et
[API native de chat](https://lmstudio.ai/docs/developer/rest/chat). L'API native
documente le réglage `reasoning: off`; le contrat JSON reste vérifié strictement
par le Vivarium après réception.
Google indique que Gemma 4 12B peut utiliser LM Studio et vise des machines avec
16 Go de VRAM ou mémoire unifiée dans son [annonce officielle](https://blog.google/innovation-and-ai/technology/developers-tools/introducing-gemma-4-12b/).

La qualité, vitesse et quantification de Gemma 4 12B sur la machine réelle ne
sont pas encore mesurées. Elles seront testées avec le serveur local et le banc,
jamais déduites de la seule fiche du modèle.

**Premier test réel — 6 août 2026 :** serveur local actif, Gemma 4 12B QAT
Q4_0 chargé avec 32 000 tokens de contexte. Une requête native avec raisonnement
désactivé a produit une décision JSON en 14 jetons; une seconde a proposé la
traversée de Sophie vers le salon, acceptée par le moteur dans une base mémoire
jetable. Aucun monde persistant n'a été modifié.

L'absence du serveur ou une réponse invalide provoque un refus explicite de la
couche cognitive avant toute action; cela ne laisse aucun effet canonique.
