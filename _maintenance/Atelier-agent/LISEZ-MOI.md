# Atelier de l'agent

**État :** en service depuis le 22/10/2026 (installé sur l'agent réel, testé sur l'environnement de test).

Panneau de gestion de l'agent OpenCode de `D:\IA LOCAL` : agents, équipes, bibliothèque de 69 modèles, MCP, modèles
et GPU RunPod, commandes `/`, skills, consignes communes, sécurité, sauvegardes — sans éditer `opencode.json` à la main.
Mode d'emploi illustré : **`guide\index.html`** (aussi dans l'Atelier, écran Guide).

## Ouvrir

- Bouton **Atelier** en bas de la colonne de gauche de la fenêtre de l'agent. La colonne n'existe qu'en onglets
  verticaux : le patch règle la fenêtre ainsi, avec le menu des agents affiché, une fois par profil au premier lancement
  (repère `atelier.reglages.v1` dans le stockage de la page). Retour possible dans Paramètres → Général → Apparence → Onglets.
- Raccourci bureau **« Atelier de l'agent »** (`Atelier.vbs`), même agent fermé.
- Le « ? » à côté du menu des agents ouvre la fiche de l'agent choisi.

Le serveur (`atelier\atelier.py`, 127.0.0.1:**4110**) démarre avec la fenêtre de l'agent (`D:\IA LOCAL\config\fenetre-agent.ps1`)
ou par `Atelier.vbs`, et s'arrête seul 5 min après la dernière page fermée quand l'agent est fermé.

## Ce que fait chaque enregistrement

1. relit la config (refus si elle a changé ailleurs) ;
2. **fait vérifier la config candidate par OpenCode** sur une copie (`atelier\verification.py` : OpenCode jetable,
   dossiers temporaires, MCP désactivés) — OpenCode ignore en silence ce qui est invalide, d'où cette vérification ;
3. sauvegarde l'ancienne version dans `sauvegardes\` (20 par fichier) ;
4. écrit, puis **recharge l'agent ouvert** (`POST /api/location/reload`, adresse et mot de passe dans `etat\opencode.json`,
   écrit par le lanceur de la fenêtre et effacé à sa fermeture).

## Sécurité

- Écoute seulement sur 127.0.0.1, en-tête Host vérifié (pas de « DNS rebinding »).
- Toute lecture de config et toute modification exigent un **jeton** tiré au démarrage et glissé dans la page servie.
- Seules `/api/etat-court` (pastille) et `/ouvrir` (ouvrir la fenêtre) répondent à la fenêtre de l'agent (CORS
  127.0.0.1:4096/4097), jamais à un site web.
- Les clés (RunPod, variables des MCP) ne sont jamais envoyées à la page ; une variable laissée vide garde sa valeur.
- Les règles qui protègent l'installation (sortie du dossier, config, opencode, .donnees, _maintenance) ne peuvent pas
  être retirées depuis l'écran Sécurité. L'agent n'a pas le droit de lire ni de modifier `_maintenance\`.

## Dossiers

| Élément | Rôle |
|---|---|
| `atelier\atelier.py` | Serveur et routes |
| `atelier\config_io.py`, `verification.py` | Lecture, vérification par OpenCode, écriture, sauvegardes |
| `atelier\agents.py` | Agents d'origine (textes français), calcul des droits réels, équipes, modèles |
| `atelier\services.py` | GPU RunPod, IA locale, rechargement d'OpenCode, catalogue et test des MCP |
| `atelier\web\` | Interface (`index.html`, `app.js`, `style.css`, `biblio.js` = bibliothèque de modèles) |
| `guide\` | Guide avec captures |
| `tests\` | `test_serveur.py` (37 vérifications) et `preparer_config_test.py` (copie de la vraie config, clés remplacées) |
| `cadrage\`, `maquette\` | Cadrage validé et maquette d'origine |
| `sauvegardes\`, `sauvegardes-test\`, `etat\` | Versions des fichiers ; état d'exécution (sessions, profils de fenêtre) |

## Mode test

`set ATELIER_BASE=D:\IA LOCAL\_maintenance\OpenCode-web-test` avant de lancer `atelier.py` : port 4111, bandeau
« Mode test », copie de config de l'environnement de test. La fenêtre d'agent de test (`fenetre-agent.ps1 -Base …
-Port 4097`) démarre aussi l'Atelier de test.

## Dans la fenêtre de l'agent (patch)

Les boutons de la colonne (pastille, Atelier, Paramètres, Aide), les descriptions du menu des agents et le « ? » font
partie du patch `_maintenance\OpenCode-francais` (fichier `packages/app/src/shell/titlebar/atelier-column.tsx` +
quelques lignes). Après une mise à jour d'OpenCode : `Patcher en français.cmd`. L'Atelier lui-même ne dépend pas
de la version d'OpenCode.
