@echo off
rem Lance l'agent de code local (OpenCode v2 + Qwen3.8-27B sur l'IA locale), avec un menu des conversations.
rem Tout reste dans D:\IA LOCAL : reglages (config\), donnees (.donnees\), travail (projets\, outils\).
setlocal
set "BASE=%~dp0"
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"

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

rem --standalone : serveur prive qui s'arrete avec la fenetre (rien ne reste en arriere-plan).
cd /d "%BASE%"

rem Avec des arguments (ex. --version, --session ses_...) : lancement direct, sans menu.
if not "%~1"=="" (
  "%BASE%\opencode\node_modules\.bin\opencode.cmd" --standalone "%BASE%" %*
  goto :eof
)

rem Sans argument : menu pour reprendre une conversation ou en commencer une nouvelle.
powershell -NoProfile -ExecutionPolicy Bypass -File "%BASE%\config\menu-conversations.ps1" -Base "%BASE%"
