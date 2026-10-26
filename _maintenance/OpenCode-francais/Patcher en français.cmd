@echo off
rem Met le terminal OpenCode (D:\IA LOCAL) en francais. A relancer apres chaque mise a jour d'OpenCode.
rem Ferme l'agent avant (terminal et web). Detail : LISEZ-MOI.md
setlocal
cd /d "%~dp0"
"%~dp0outils\bun-windows-x64\bun.exe" "%~dp0outils\patcher.ts" %*
echo.
pause
