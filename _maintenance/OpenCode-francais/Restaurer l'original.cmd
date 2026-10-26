@echo off
rem Remet l'OpenCode officiel (en anglais) sauvegarde par "Patcher en francais.cmd".
setlocal
cd /d "%~dp0"
"%~dp0outils\bun-windows-x64\bun.exe" "%~dp0outils\patcher.ts" --restaurer
echo.
pause
