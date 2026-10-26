# Efface les discussions de l'agent local et tout ce qui s'y rapporte, pour repartir a zero.
# A lancer agent ferme (fenetre et terminal). Garde : reglages (config\), profil du Chrome d'analyse,
# cache, "maison" de l'agent, choix du modele. Prepare le 23/10/2026 apres la base cassee par un deplacement.
$d = 'D:\IA LOCAL\.donnees'
if (Get-Process opencode -ErrorAction SilentlyContinue) {
    Write-Host "L'agent est ouvert : ferme-le (fenetre et terminal), puis relance ce script." -ForegroundColor Red; return
}
$motif = [regex]::Escape("$d\fenetre-edge")
if (Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" | Where-Object { $_.CommandLine -match $motif }) {
    Write-Host "La fenetre de l'agent est encore ouverte : ferme-la, puis relance ce script." -ForegroundColor Red; return
}
$cibles = @(
    "$d\data\opencode\opencode.db", "$d\data\opencode\opencode.db-wal", "$d\data\opencode\opencode.db-shm",  # discussions
    "$d\data\opencode\abimee-2026-10-23",           # base cassee et etapes de la reparation
    "$d\data\opencode\log", "$d\data\opencode\tool-output", "$d\data\opencode\shell", "$d\data\opencode\repos",
    "$d\state\opencode\prompt-history.jsonl",       # historique des messages tapes
    "$d\state\opencode\latest",
    "$d\fenetre-edge",                              # profil de la fenetre (onglets des anciennes discussions)
    "$d\sauvegarde-sessions-test-2026-10-15"        # anciennes discussions de test du 15/10
)
$total = 0
foreach ($c in $cibles) {
    if (-not (Test-Path -LiteralPath $c)) { Write-Host "  deja absent : $c" -ForegroundColor DarkGray; continue }
    $taille = (Get-ChildItem -LiteralPath $c -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    if ((Get-Item -LiteralPath $c -Force).PSIsContainer) { cmd /c "rmdir /s /q `"\\?\$c`"" } else { Remove-Item -LiteralPath $c -Force }
    if (Test-Path -LiteralPath $c) { Write-Host "  ECHEC : $c" -ForegroundColor Red }
    else { $total += $taille; Write-Host ("  efface ({0:N1} Mo) : {1}" -f ($taille / 1MB), $c) -ForegroundColor Green }
}
Write-Host ("Termine : {0:N1} Mo liberes. Au prochain lancement, l'agent repart avec une liste de discussions vide." -f ($total / 1MB))
