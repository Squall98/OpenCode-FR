# Agent de code local (OpenCode + Qwen3.8)

**État :** installé et testé le 15/10/2026 (reverse web, dev Python, blocages de sécurité : OK).

Un agent comme Claude Code, mais **100 % local** sur la RTX 5090 : il crée des fichiers, écrit et lance du code,
et fait du **reverse engineering de sites web** avec le MCP REA. Nykaro lui donne ses missions directement.
Guide illustré : **`Guide de l'agent.html`** · mode d'emploi de l'interface (Ctrl+P, commandes /, raccourcis, Settings) : **`Wiki OpenCode.html`**.

Plan de tout ce qui touche à l'IA locale (dossiers, raccourcis, mises à jour) : **`Plan de l'IA locale.html`**.

## En fenêtre, en français (depuis le 22/10/2026)

- Raccourci **« Agent IA »** du bureau (`Agent IA (fenêtre).vbs` → `config\fenetre-agent.ps1`) : démarre le moteur et
  le serveur OpenCode cachés (`127.0.0.1:4096`), puis ouvre l'interface dans une fenêtre Edge dédiée (profil
  `.donnees\fenetre-edge`), déjà connectée. Fermer la fenêtre arrête le serveur. Même config, mêmes agents, même historique.
- `Lancer l'agent (web).cmd` : la même chose dans le navigateur habituel.
- Le terminal est lui aussi en français (exe recompilé) : voir `_maintenance\OpenCode-francais\LISEZ-MOI.md`.
  **Après une mise à jour d'OpenCode**, relancer `_maintenance\OpenCode-francais\Patcher en français.cmd`.
- Mots et raccourcis traduits : **`Lexique OpenCode.html`**.
- **Atelier de l'agent** (raccourci bureau, ou bouton « Atelier » en bas de la colonne de la fenêtre) : régler agents,
  équipes, MCP, modèles, commandes, skills et sécurité sans éditer `opencode.json`. Voir `_maintenance\Atelier-agent\LISEZ-MOI.md`.

## Utilisation (terminal)

1. Double-clic sur **`Lancer l'agent.cmd`** : il démarre le moteur IA locale s'il le faut, puis affiche le **menu de tes conversations** (les 15 plus récentes, avec « il y a … »). **Entrée** = reprendre la dernière, **un numéro** = reprendre celle-là, **N** = nouvelle conversation, **Q** = quitter.
2. Écris ta mission. Le profil par défaut (`build`) fait tout : dev **et** reverse avec les 207 outils REA. Pas besoin de changer de profil.
3. Pour analyser un site : double-clic sur **`Ouvrir Chrome d'analyse.cmd`**, ouvre le site dedans, puis demande l'analyse à l'agent.
   **Ferme ce Chrome après.**
4. Le terminal demande ton accord à chaque commande (sauf `ls`, `dir`, `git status/diff/log`).
5. `/models` pour changer de modèle, `/exit` (ou Ctrl+C deux fois) pour quitter : tout s'arrête, le modèle se décharge après 10 min.
6. Pour des titres clairs dans le menu, renomme la conversation dans OpenCode avec **Ctrl+R** (ex. `Play-bubble · 2 · API`).

## Contenu

| Élément | Rôle |
|---|---|
| `projets\` | Une mission = un dossier. Repart vide le 22/10/2026 (les anciens projets ont été rangés ailleurs par Nykaro) |
| `_maintenance\` | Patch français (`OpenCode-francais\`), OpenCode de test à données vides (`OpenCode-web-test\`), GPU loué (`RunPod-GPU\`). **Pas de `.ignore` ici** : Tailwind le lirait et casserait la mise en page de la fenêtre à la recompilation |
| `outils\` | Outils que l'agent installe lui-même (skill `installer-outil`) |
| `config\opencode\opencode.json` | Réglages : modèle, MCP, permissions, profils. **JSON pur** (OpenCode 2.0.29 refuse les commentaires) |
| `config\opencode-commente.jsonc.txt` | Les mêmes réglages **avec explications** (copie de lecture) |
| `config\opencode\AGENTS.md` | Consignes + **fiche d'aiguillage** (tâche → outil), lue à chaque session |
| `config\opencode\skills\reverse-web\` | Fiche des outils REA web les plus utiles + Playwright |
| `config\opencode\skills\installer-outil\` | Règles d'installation (tout dans `outils\`, version précise, source vérifiée) |
| `opencode\` | OpenCode **v2.0.29** (npm `@opencode/cli`, portable) |
| `.donnees\` | Sessions, cache, journaux d'OpenCode, profils de la fenêtre et du Chrome d'analyse (ne pas toucher). Repart vide le 22/10/2026 (anciennes conversations rangées ailleurs par Nykaro) |
| `Lancer l'agent.cmd`, `Ouvrir Chrome d'analyse.cmd` | Lanceurs (le premier affiche le menu des conversations : `config\menu-conversations.ps1`) |
| `Agent IA (fenêtre).vbs`, `Lancer l'agent (web).cmd` | Interface en fenêtre / dans le navigateur (`config\fenetre-agent.ps1`) |

## Modèles (moteur `D:\IA-et-outils\IA-locale`, llama-swap 127.0.0.1:8090)

| Nom | Modèle | Vitesse | Contexte | Rôle |
|---|---|---|---|---|
| `ia-locale/agent` (**défaut**) | Qwen3.8-27B UD-Q4_K_XL, réflexion moyenne, MTP | ~55 tok/s | 96 k | Agent : plus fiable, suit mieux les consignes |
| `ia-locale/code` | Qwen3.6-35B-A3B | ~150 tok/s | 32 k | Plus rapide, pour les petites tâches simples |
| `ia-locale/heretic` | Qwen3.8-27B **Heretic** Q4_K_M (sans censure), réflexion moyenne | ~35 tok/s | 128 k | Même modèle qu'`agent` sans les refus ; pas de MTP donc plus lent. Ajouté le 19/10/2026 |

Comparaison sur la même mission (script Python + tests) : `agent` 104 s, 14 tests OK, consignes suivies (LISEZ-MOI créé) ;
`code` 55 s, 10 tests OK, mais a oublié le LISEZ-MOI et renommé un fichier.
VRAM avec `agent` chargé : ~22 Go sur 24 → **pas de Dofus en même temps**.

## Sécurité (testé)

- Lecture/écriture **hors de `D:\IA LOCAL` : bloquée** (`external_directory: deny`).
- Ses réglages (`config\`, `opencode\`, `.donnees\`) : **non modifiables** par ses outils d'édition.
- Terminal : **demande avant chaque commande** ; `git push`, `docker`, `format` refusés.
  ⚠️ Une commande terminal que tu acceptes peut, elle, toucher n'importe où : lis-la avant de dire oui.
- REA : **les 207 outils**, dans tous les profils, via le « Code Mode » d'OpenCode (outil `execute` → `tools.rea.<outil>`). Ses analyses se font sur des fichiers **copiés dans `projets\`**.
- Skills de Claude (`~/.claude/skills`) invisibles pour lui : sa « maison » est `.donnees\home`.
- **100 % local** : règle `policies` = tout fournisseur refusé sauf `ia-locale`. Les modèles gratuits en ligne d'OpenCode (`opencode/…`) n'apparaissent plus dans `/models`.

## MCP branchés

| MCP | Pour | Remarque |
|---|---|---|
| `rea` (`C:\MCP\rea-mcp`) | Reverse web | Réutilisé tel quel (même installation que pour Claude) |
| `playwright` | Naviguer, cliquer, captures | `npx @playwright/mcp@latest` |
| `perplexity` | Recherche web | Utilise ton abonnement Perplexity (Comet) |

Volontairement **non branchés** : `discord-admin`, `perso-deploy`, `cloud` (agissent ou dépensent), `history`, `steam`, `discord-search`.

## Pièges rencontrés (15/10/2026)

- OpenCode **2.x** : `providers`/`permissions`/`mcp.servers` (≠ v1). Le fichier de config **ne doit pas contenir de commentaires**.
- `{env:VAR}` dans la config est remplacé **avant** la lecture du JSON : un chemin Windows (`C:\Users`) casse le fichier → chemins écrits en dur.
- Les permissions `edit` se comparent au chemin **relatif** au dossier (`config/*`), pas au chemin absolu.
- Changer de profil : **Shift+Tab** (Tab seul ne fait rien en 2.0.29). REA est de toute façon activé dans tous les profils.
- REA = 207 outils, ~3,3 Mo de descriptions : impossible en appel direct → **Code Mode** (défaut d'OpenCode 2), l'agent appelle `tools.rea.xxx` dans `execute`.
- Sans `--standalone`, OpenCode laisse un service en arrière-plan (`opencode service stop` pour l'arrêter) : le lanceur utilise `--standalone`.
- `.cmd` avec fins de ligne Unix (LF) + accents : erreurs « 'ucun' n'est pas reconnu » quand on les appelle depuis un autre script → CRLF.
- **Déplacer ou recopier `.donnees` (23/10/2026)** : agent fermé, et toujours le dossier entier. `opencode.db` va avec ses
  fichiers `opencode.db-wal` et `opencode.db-shm` : ne jamais poser une ancienne base à côté des `-wal`/`-shm` d'une autre,
  SQLite les mélange et casse la base (« Le serveur OpenCode n'a pas démarré »). Réparé ce jour-là avec l'outil officiel
  `_maintenance\outils-sqlite\`, puis tout effacé pour repartir à zéro avec
  `_maintenance\Nettoyage-discussions\repartir-a-zero.ps1` (efface discussions, historique, journaux et profil de la fenêtre ;
  garde réglages, agents et Chrome d'analyse). Réutilisable tel quel, agent fermé.

## Hors de ce dossier

- Le modèle Qwen3.8-27B (17,6 Go) et sa ligne dans `config-llama-swap.yaml` sont dans **`D:\IA-et-outils\IA-locale`** (moteur partagé).
- REA garde son cache dans `C:\Users\<toi>\.rea` (déjà le cas avec Claude).
- `config\opencode\service.json` : mot de passe local généré par OpenCode pour son service (127.0.0.1 seulement).

## Désinstaller

1. Fermer OpenCode, puis supprimer le dossier `D:\IA LOCAL`.
2. Optionnel : dans `D:\IA-et-outils\IA-locale`, retirer le bloc `agent:` de `config-llama-swap.yaml`
   (sauvegarde d'avant : `config-llama-swap.yaml.avant-agent-2026-10-15`) et le fichier `modeles\Qwen3.8-27B-UD-Q4_K_XL.gguf`.
