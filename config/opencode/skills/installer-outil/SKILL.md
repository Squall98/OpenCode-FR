---
name: installer-outil
description: Installer un outil (dépôt GitHub, paquet npm, paquet pip, programme portable) dans D:\IA LOCAL\outils. À charger avant toute installation.
---

# Installer un outil

Tout s'installe dans **`D:\IA LOCAL\outils\<nom-de-l-outil>\`**. Jamais ailleurs (pas d'installation globale, pas de `C:\`).

## Avant d'installer : vérifier la source

1. Le dépôt est-il **l'officiel** ? (nom de l'auteur, nombre d'étoiles, date de la dernière mise à jour, lien depuis le site du projet).
   En cas de doute, **demande à Nykaro** et propose-lui de faire vérifier par Claude.
2. Méfiance : dépôts récents avec un « zip à télécharger », un `.exe` sans code source, un script qui demande des droits administrateur.
3. Annonce à Nykaro : **quoi**, **d'où**, **taille approximative**, **commande exacte**. Attends son accord.

## Comment installer (une commande à la fois, chacune validée par Nykaro)

| Type | Commande |
|---|---|
| Dépôt GitHub | `git clone --depth 1 <url> "D:\IA LOCAL\outils\<nom>"` |
| Paquet npm | `npm install --prefix "D:\IA LOCAL\outils\<nom>" <paquet>@<version>` (jamais `-g`) |
| Paquet Python | `python -m venv "D:\IA LOCAL\outils\<nom>\.venv"` puis `"D:\IA LOCAL\outils\<nom>\.venv\Scripts\pip.exe" install <paquet>==<version>` |
| Programme portable (zip) | Télécharger dans `outils\<nom>\`, vérifier le SHA256 s'il est publié (`certutil -hashfile fichier SHA256`), décompresser au même endroit |

- Toujours **une version précise** (`@1.2.3`, `==1.2.3`) plutôt que « la dernière ».
- Python : `C:\Program Files\Python314\python.exe`. Node : déjà installé (`node`, `npm`).
- Pas d'installeur `.msi` / `.exe` qui s'installe dans Windows, pas de `winget`, pas de Docker : si c'est le seul moyen, **arrête-toi et dis-le à Nykaro**.

## Après l'installation

Crée `outils\<nom>\LISEZ-MOI-INSTALL.md` :

```
# <nom>
- Source : <url officielle>
- Version : <x.y.z>   Installé le : <date>
- Commande d'installation : <commande>
- Comment le lancer : <commande>
- Pour le retirer : supprimer ce dossier
```

Puis teste-le avec la commande la plus simple (`--version` ou `--help`) et montre le résultat à Nykaro.

## Si l'outil est un serveur MCP

Tu ne peux **pas** modifier ta propre configuration (bloqué). Prépare dans le LISEZ-MOI-INSTALL.md le bloc à ajouter
dans `D:\IA LOCAL\config\opencode\opencode.jsonc` (section `mcp.servers`, format :
`"nom": { "type": "local", "command": ["chemin\\vers\\exe", "arg"] }`) et demande à Nykaro de le copier lui-même.
