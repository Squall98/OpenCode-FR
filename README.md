# OpenCode-FR — un agent de code 100 % local, en français

Un agent comme Claude Code, mais qui tourne **entièrement sur ton PC** : il crée des fichiers, écrit et lance du code, et peut faire du reverse engineering de sites web.
Il repose sur [OpenCode](https://opencode.ai) (v2.0.29) et sur des modèles locaux (Qwen) servis par [llama-swap](https://github.com/mostlygeek/llama-swap) et llama.cpp.

Ce dépôt rassemble tout ce qui a été fait autour : **traduction française** de l'interface, **guides illustrés**, **lexique**, **réglages commentés**, lanceurs Windows et un **atelier** pour tout régler sans éditer de JSON.

## Ce qu'il y a dedans

| Élément | Rôle |
|---|---|
| `Guide de l'agent.html` | Guide illustré pour débuter avec l'agent. |
| `Wiki OpenCode.html` | Mode d'emploi de l'interface : Ctrl+P, commandes `/`, raccourcis, réglages. |
| `Lexique OpenCode.html` | Les mots et raccourcis d'OpenCode traduits et expliqués. |
| `Plan de l'IA locale.html` | Vue d'ensemble : dossiers, raccourcis, mises à jour. |
| `LISEZ-MOI.md` | La notice complète (utilisation, modèles, sécurité). |
| `Lancer l'agent.cmd` | Démarre le moteur s'il le faut et affiche le menu des conversations. |
| `Agent IA (fenêtre).vbs`, `Lancer l'agent (web).cmd` | L'interface web d'OpenCode, en fenêtre dédiée ou dans le navigateur. |
| `config/opencode/` | `opencode.json` (modèles, MCP, permissions, profils), `AGENTS.md` (consignes lues à chaque session), skills. |
| `config/opencode-commente.jsonc.txt` | Les mêmes réglages, avec des explications. |
| `_maintenance/OpenCode-francais/` | Le **patch français** d'OpenCode : `Patcher en français.cmd` et `Restaurer l'original.cmd`. |
| `_maintenance/Atelier-agent/` | L'**Atelier** : régler agents, équipes, MCP, modèles, commandes, skills et sécurité depuis une page. |
| `_maintenance/Nettoyage-discussions/` | Script pour repartir avec un historique vide. |

## Prérequis

- Windows 10/11, Node.js, Microsoft Edge (pour la fenêtre dédiée).
- Une carte graphique avec assez de mémoire pour un modèle local (testé sur une RTX 5090 : Qwen 27B à ~55 jetons/s).
- Un serveur de modèles compatible OpenAI sur `127.0.0.1:8090` (llama-swap + llama.cpp).

## Installation rapide

1. Installer OpenCode en portable dans un dossier `opencode/` : `npm install @opencode/cli@2.0.29`.
2. Copier ce dépôt à côté, puis **adapter les chemins** : les scripts supposent le dossier `D:\IA LOCAL`.
3. Vérifier `config/opencode/opencode.json` : adresse du serveur de modèles, noms des modèles. Les clés d'API sont remplacées par `XXX` : mets les tiennes si tu utilises un GPU loué.
4. Pour l'interface en français : lancer `_maintenance/OpenCode-francais/Patcher en français.cmd` (à relancer après chaque mise à jour d'OpenCode).
5. Double-clic sur `Lancer l'agent.cmd`.

## Sécurité (réglée dans `opencode.json`)

- Lecture et écriture **hors du dossier de l'agent : bloquées**.
- Ses propres réglages ne sont pas modifiables par ses outils.
- Le terminal **demande avant chaque commande** ; `git push`, `docker` et `format` sont refusés.
- **100 % local** : tous les fournisseurs en ligne sont refusés, sauf le serveur local.

## Remarques

- Fait pour un usage perso, partagé tel quel : certains chemins et noms de modèles sont à adapter.
- OpenCode, llama.cpp, llama-swap et les modèles Qwen appartiennent à leurs auteurs ; ce dépôt ne contient que les réglages, la traduction et la documentation.
