' Ouvre l'Atelier de l'agent (panneau de gestion d'OpenCode) dans sa fenetre, sans fenetre noire.
' Le serveur de l'Atelier demarre s'il ne tourne pas, et s'arrete seul quelques minutes apres la derniere fenetre fermee.
Option Explicit
Dim shell, fichiers, dossier
Set shell = CreateObject("WScript.Shell")
Set fichiers = CreateObject("Scripting.FileSystemObject")
dossier = fichiers.GetParentFolderName(WScript.ScriptFullName)
shell.Run """C:\Program Files\Python314\pythonw.exe"" """ & dossier & "\atelier\atelier.py"" --fenetre", 0, False
