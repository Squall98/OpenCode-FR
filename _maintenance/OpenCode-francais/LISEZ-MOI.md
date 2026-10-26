# OpenCode en français (terminal et fenêtre)

**État :** en service sur OpenCode **v2.0.29** (installé dans `D:\IA LOCAL\opencode`) depuis le 22/10/2026.
Traduction complète du terminal et de l'interface web/fenêtre depuis le 22/10/2026 (voir « Ce qui est traduit »).
La v2.1.2 n'est pas encore prise en charge (voir plus bas).

## Ce que c'est

Le terminal d'OpenCode n'existe qu'en anglais. Une traduction (62 langues, dont le français) attend d'être acceptée
sur GitHub : [PR anomalyco/opencode#52000](https://github.com/anomalyco/opencode/pull/52000)
(demande d'origine : [anomalyco/opencode#37216](https://github.com/anomalyco/opencode/issues/37216)).

Ce dossier recompile **la même version** d'OpenCode que celle installée, avec cette traduction, des compléments
(textes que la PR et la traduction officielle de l'interface web avaient laissés en anglais) et le français par défaut,
puis remplace l'exe. Même version, même canal : réglages, agents et historique des conversations restent les mêmes.
`opencode.json` et `cli.json` ne sont pas modifiés.

## Utilisation

1. Ferme l'agent (fenêtre, web et terminal). S'il est ouvert, le script le détecte et s'arrête sans rien toucher.
2. Double-clic sur **`Patcher en français.cmd`** (≈ 2 min ; s'il doit d'abord télécharger les sources ou les ≈ 3 Go de
   dépendances, compter ≈ 8 min de plus).
3. Relance l'agent comme d'habitude.

- **Revenir à l'anglais :** `Restaurer l'original.cmd` (remet l'exe officiel, empreinte vérifiée).
- **Relancer alors que c'est déjà fait :** le script le voit et ne fait rien (`--forcer` pour recompiler quand même).
  S'il a été amélioré depuis (patch, traductions, script : empreinte « recette » dans `etat.json`), il recompile tout seul.
- **Contrôle avant installation :** après la compilation, `outils\captures-fr.test.tsx` dessine 22 écrans du terminal
  avec un faux serveur (accueil, palette, `/`, agents, modèles, sessions, état, réglages, thèmes…) dans
  `travail\captures-v<version>.txt`. Un écran qui plante bloque l'installation.
- **Ne pas utiliser le choix de langue dans les réglages du terminal** : il écrirait `"language"` dans `cli.json`,
  un réglage que l'OpenCode officiel ne connaît pas. Le français est déjà le choix par défaut, il n'y a rien à régler.

## Ce qui est traduit (vérifié le 22/10/2026)

| Partie | Couverture | Reste en anglais |
|---|---|---|
| Terminal | 1062 textes ; tous les écrans et dialogues | Panneau développeur « Theme performance » ; interface `opencode mini` (non utilisée) |
| Fenêtre / web (`packages/app`) | 1006 textes | Noms propres (OpenCode Console…) |
| Messages (`packages/ui`) | 256 textes | — |
| Extensions de la fenêtre (`packages/gui-extensions`) | 13 extensions (navigateur intégré, appairage, aperçus Office, `/btw`, SSH…) | Noms propres |
| Partout | — | Textes des licences open source (À propos) : à garder tels quels |

Les messages qui viennent du **modèle** ou du **serveur** (réponses, erreurs techniques) ne passent pas par ces traductions.

## Historique

- **22/10/2026 — Atelier :** la fenêtre reçoit en bas de sa colonne de gauche la pastille d'état, les boutons Atelier,
  Paramètres et Aide (`packages/app/src/shell/titlebar/atelier-column.tsx`), et le menu des agents affiche la description
  de chaque agent avec un « ? » vers sa fiche dans l'Atelier (`_maintenance\Atelier-agent`). La fenêtre se met d'elle-même,
  une fois par profil, en onglets verticaux avec le menu des agents affiché (`packages/app/src/settings/model.tsx`,
  repère `atelier.reglages.v1`) : sans ça, un profil neuf restait en onglets horizontaux, donc sans la colonne.
- **22/10/2026 — fenêtre sans mise en page :** un fichier `.ignore` placé dans `_maintenance\` (pour cacher ce dossier aux
  recherches de l'agent) était aussi lu par Tailwind, qui ignorait alors les sources : la feuille de style de la fenêtre
  perdait ses classes (≈ 77 Ko). Fichier vidé ; le script vérifie désormais les styles avant d'installer.
  **Ne jamais remettre de `.ignore` / `.gitignore` au-dessus de `travail\`.**
- **22/10/2026 — correctif :** les Réglages du terminal (`/settings`) plantaient (réglage « Release highlights » de la
  v2.0.29 absent de la PR). Corrigé, et le traducteur affiche désormais le texte d'origine au lieu de planter si une clé
  manque.
- **22/10/2026 — traduction complète :** 33 textes du terminal écrits en dur branchés sur la traduction
  (`/btw`, `/clear`, `/reload`, panneau de code, nouveautés, encadré « Pour commencer »…), 156 textes de la fenêtre
  et 110 textes des extensions traduits. Vouvoiement partout, comme les traductions officielles.
- **22/10/2026 — sûreté :** détection de l'agent ouvert avant toute action ; la référence « officiel » est la copie
  d'origine posée par npm (`@opencode\cli-windows-x64\bin\opencode.exe`), une sauvegarde n'est jamais écrasée par autre
  chose ; restes temporaires (`.ancien`, `.nouveau`) nettoyés au passage suivant.

## Après une mise à jour d'OpenCode

Une mise à jour remet l'exe officiel en anglais : relance `Patcher en français.cmd`.

- Si `patch\fr-v<version>.diff` existe, il est appliqué. Les compléments de traduction sont toujours réappliqués.
- Sinon, le script essaie la dernière version de la PR #52000. Si elle ne s'applique pas proprement, il **s'arrête sans rien
  toucher** (OpenCode reste en anglais, en état de marche). Il faut alors adapter le patch : demander à Claude
  « adapte le patch français d'OpenCode à la v X.Y.Z » (refaire ce qui a été fait pour la v2.0.29 — y compris le
  branchement des textes en dur, modèle : `outils\reference-brancher-tui-v2.0.29.py`, repérage :
  `outils\chercher-anglais.ts` — puis enregistrer `patch\fr-vX.Y.Z.diff`).
- Vérifié le 22/10/2026 : sur la **v2.1.2**, la PR ne s'applique plus (45 fichiers en conflit, gros remaniement du terminal).
  Pour garder le français, rester en v2.0.29 (ne pas faire `/update`) jusqu'à ce que la PR soit mise à jour.

## Contenu

| Élément | Rôle |
|---|---|
| `Patcher en français.cmd` | Lance le patch |
| `Restaurer l'original.cmd` | Remet l'exe officiel |
| `outils\patcher.ts` | Le script (sources, traduction, compilation, contrôle, sauvegarde, remplacement) |
| `outils\appliquer-complements.ts` | Écrit un fichier `complements-*.json` dans un dictionnaire `fr.ts` |
| `outils\appliquer-extensions.ts` | Écrit `complements-extensions-fr.json` dans les extensions et y déclare le français |
| `outils\captures-fr.test.tsx` | Contrôle des 22 écrans du terminal (faux serveur, aucune vraie donnée) |
| `outils\comparer-fr.ts` | Liste les textes pas encore traduits du terminal (`bun comparer-fr.ts <dossier i18n> --json`) |
| `outils\chercher-anglais.ts` | Repère les textes anglais écrits en dur dans le code (`bun chercher-anglais.ts <dossier src> [--tout]`) |
| `outils\reference-brancher-tui-v2.0.29.py` | Ce qui a été branché à la main en v2.0.29 (modèle pour une version suivante) |
| `outils\bun-windows-x64\` | Bun 1.4.2 portable (version exigée par OpenCode), empreinte SHA256 vérifiée |
| `patch\fr-v2.0.29.diff` | La PR #52000 adaptée à la v2.0.29, correctif des Réglages, textes en dur branchés, français par défaut |
| `patch\fr-v2.0.29.diff.avant-*` | Versions précédentes du patch (retour arrière possible) |
| `patch\complements-fr.json` | 67 traductions du terminal |
| `patch\complements-app-fr.json`, `complements-ui-fr.json` | 149 + 8 traductions de la fenêtre |
| `patch\complements-extensions-fr.json` | 110 traductions des extensions de la fenêtre |
| `sauvegardes\` | Exe officiels, un par version |
| `etat.json` | Version patchée, empreintes (officiel / patché / recette) |
| `travail\` | Sources, compilation, captures (peut être supprimé, il se refait) |

## Détails techniques

- L'exe installé est un **lien physique** (le même fichier à 3 endroits, dont le cache npm) : le script renomme
  l'ancien et pose le nouveau à côté, sans jamais écrire dans le fichier d'origine. Un exe en cours d'exécution peut être
  renommé mais pas ouvert en écriture : c'est ce test qui détecte l'agent ouvert.
- Compilation : `bun script/build.ts --single --skip-install` dans `packages/cli`, avec `OPENCODE_VERSION=<version>`
  et `OPENCODE_CHANNEL=latest` (comme l'officiel). L'interface web est incluse.
- Français par défaut : `?? "en"` remplacé par `?? "fr"` dans `app.tsx`, `context/language.ts`, `ui/toast.tsx`,
  `component/error-component.tsx`.
- Textes hors composants (extensions internes du terminal, listes de raccourcis) : `translateLoaded()` ajouté à
  `packages/tui/src/i18n/translate.ts` (lit le dictionnaire déjà chargé).
- Vérifications faites : `tsgo` (types) sur `tui`, `gui-extensions`, `ui` ; `app` a une seule erreur préexistante
  (`custom-elements.d.ts`, lien symbolique du dépôt enregistré comme texte sous Windows).
- Tests faits dans un environnement à part (`D:\IA LOCAL\_maintenance\OpenCode-web-test`, config et données vides).

## Contribuer sur GitHub

Plutôt qu'une nouvelle PR : soutenir #52000 (👍, retour sur le français) et éventuellement proposer les compléments
(`patch\complements-*.json`, le correctif des Réglages, `translateLoaded`) comme améliorations de la PR.
