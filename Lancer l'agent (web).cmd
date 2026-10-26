@echo off
rem Lance l'agent de code local (OpenCode v2 + Qwen3.8-27B sur l'IA locale) dans le navigateur : interface web, en francais.
rem Memes reglages, memes agents et meme historique que "Lancer l'agent.cmd" (version terminal).
rem Le serveur tourne dans une fenetre a part, sur 127.0.0.1 uniquement : la fermer arrete tout.
setlocal
set "BASE=%~dp0"
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"
if not defined OC_WEB_PORT set "OC_WEB_PORT=4096"
set "OC_WEB_URL=http://127.0.0.1:%OC_WEB_PORT%"

rem Garder la vraie valeur pour les MCP (REA, Playwright, Perplexity ont leurs donnees dans le vrai profil).
set "VRAI_USERPROFILE=%USERPROFILE%"

rem OpenCode : reglages, donnees, cache et "maison" isoles dans le dossier (il ne voit pas ~/.claude etc.).
set "XDG_CONFIG_HOME=%BASE%\config"
set "XDG_DATA_HOME=%BASE%\.donnees\data"
set "XDG_CACHE_HOME=%BASE%\.donnees\cache"
set "XDG_STATE_HOME=%BASE%\.donnees\state"
set "USERPROFILE=%BASE%\.donnees\home"
set "HOME=%BASE%\.donnees\home"
set "npm_config_cache=%BASE%\.donnees\cache\npm"

rem Moteur IA locale (llama-swap sur 127.0.0.1:8090) : ne fait rien s'il tourne deja.
call "D:\IA-et-outils\IA-locale\scripts\demarrer.cmd" >nul

cd /d "%BASE%"

rem Serveur deja lance (fenetre encore ouverte) : le navigateur est deja connecte, on rouvre juste la page.
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort %OC_WEB_PORT% -State Listen -ErrorAction SilentlyContinue) { exit 1 }"
if errorlevel 1 (
  start "" "%OC_WEB_URL%/"
  goto :eof
)

rem Mot de passe tire au hasard a chaque lancement, connu seulement de ce lanceur et du serveur.
for /f %%p in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString('N')"') do set "OPENCODE_SERVER_PASSWORD=%%p"

start "OpenCode web - fermer cette fenetre pour arreter l'agent" /min "%BASE%\opencode\node_modules\.bin\opencode.cmd" serve --hostname 127.0.0.1 --port %OC_WEB_PORT%

rem Des que le serveur repond : lien de connexion a usage unique, ouvert dans le navigateur par defaut.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$a = 'Basic ' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('opencode:' + $env:OPENCODE_SERVER_PASSWORD)); for ($i = 0; $i -lt 60; $i++) { try { $r = Invoke-RestMethod -Method Post -Uri '%OC_WEB_URL%/api/pair' -Headers @{ Authorization = $a }; Start-Process ('%OC_WEB_URL%/auth/connect/' + $r.code); exit 0 } catch { Start-Sleep -Milliseconds 500 } }; exit 1"
if errorlevel 1 (
  echo Le serveur OpenCode ne repond pas sur %OC_WEB_URL%. Regarde la fenetre "OpenCode web".
  pause
)
