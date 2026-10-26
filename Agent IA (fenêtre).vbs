' Ouvre l'agent local dans sa propre fenetre (interface en francais), sans fenetre noire.
' Le raccourci "Agent IA" du bureau pointe sur ce fichier. Fermer la fenetre arrete l'agent.
Option Explicit
Dim shell, fichiers, dossier
Set shell = CreateObject("WScript.Shell")
Set fichiers = CreateObject("Scripting.FileSystemObject")
dossier = fichiers.GetParentFolderName(WScript.ScriptFullName)

' 0 = fenetre cachee, False = on n'attend pas : le script s'arrete tout seul a la fermeture de la fenetre.
shell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & dossier & "\config\fenetre-agent.ps1""", 0, False
