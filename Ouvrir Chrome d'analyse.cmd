@echo off
rem Ouvre un Chrome SEPARE de ton Chrome habituel, que l'agent peut observer (port 9222, seulement en local).
rem Profil propre a l'agent : D:\IA LOCAL\.donnees\chrome-profil. Ne t'y connecte pas a des comptes sensibles.
rem FERME-LE apres l'analyse : tant qu'il est ouvert, un programme du PC peut le piloter.
set "BASE=%~dp0"
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-debugging-address=127.0.0.1 --user-data-dir="%BASE%.donnees\chrome-profil" --no-first-run --no-default-browser-check %*
