# Ouvre l'agent local (OpenCode v2) dans sa propre fenetre, sans console : serveur cache + fenetre Edge dediee.
# Appele par "Agent IA (fenetre).vbs" (raccourci "Agent IA" du bureau). Fermer la fenetre arrete le serveur.
# Memes reglages, memes agents et meme historique que "Lancer l'agent.cmd" (version terminal).
#   -Base / -Port : pour tester sur une autre installation (ex. D:\IA LOCAL\_maintenance\OpenCode-web-test).
param([string]$Base = (Split-Path $PSScriptRoot -Parent), [int]$Port = 4096)

$ErrorActionPreference = 'Stop'
$url = "http://127.0.0.1:$Port"
$profil = Join-Path $Base '.donnees\fenetre-edge'
$edge = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
          "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1

function Alerte([string]$texte) {
    Add-Type -AssemblyName System.Windows.Forms
    [void][System.Windows.Forms.MessageBox]::Show($texte, 'Agent IA', 'OK', 'Warning')
    exit 1
}
if (-not $edge) { Alerte "Microsoft Edge est introuvable : impossible d'ouvrir la fenetre de l'agent." }

# Garder la vraie valeur pour les MCP (REA, Playwright, Perplexity ont leurs donnees dans le vrai profil).
$env:VRAI_USERPROFILE = $env:USERPROFILE
# OpenCode : reglages, donnees, cache et "maison" isoles dans le dossier (il ne voit pas ~/.claude etc.).
$env:XDG_CONFIG_HOME = "$Base\config"
$env:XDG_DATA_HOME = "$Base\.donnees\data"
$env:XDG_CACHE_HOME = "$Base\.donnees\cache"
$env:XDG_STATE_HOME = "$Base\.donnees\state"
$env:USERPROFILE = "$Base\.donnees\home"
$env:HOME = "$Base\.donnees\home"
$env:npm_config_cache = "$Base\.donnees\cache\npm"

# Moteur IA locale (llama-swap sur 127.0.0.1:8090) : ne fait rien s'il tourne deja.
& cmd.exe /c "call `"D:\IA-et-outils\IA-locale\scripts\demarrer.cmd`" >nul 2>&1"

# Fenetre "application" Edge avec son propre profil (ni extensions ni onglets du navigateur habituel).
function Fenetre([string]$adresse) {
    $arguments = "--user-data-dir=`"$profil`" --app=`"$adresse`" --no-first-run --no-default-browser-check --disable-sync --disable-features=Translate --window-size=1400,950"
    Start-Process -FilePath $edge -ArgumentList $arguments | Out-Null
}
function FenetreOuverte {
    $motif = [regex]::Escape($profil)
    [bool](Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" | Where-Object { $_.CommandLine -match $motif })
}

# Serveur deja lance (fenetre deja ouverte, ou "Lancer l'agent (web).cmd") : on rouvre juste une fenetre.
if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    Fenetre "$url/"
    exit 0
}

# Mot de passe tire au hasard a chaque lancement, connu seulement de ce script et du serveur.
$env:OPENCODE_SERVER_PASSWORD = XXX).ToString('N')
$exe = Join-Path $Base 'opencode\node_modules\@opencode\cli\bin\opencode.exe'
$serveur = Start-Process -FilePath $exe -ArgumentList "serve --hostname 127.0.0.1 --port $Port" `
    -WorkingDirectory $Base -WindowStyle Hidden -PassThru

# Des que le serveur repond : lien de connexion a usage unique, ouvert dans la fenetre.
$auth = 'Basic ' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('opencode:' + $env:OPENCODE_SERVER_PASSWORD))
$code = $null
for ($i = 0; $i -lt 60 -and -not $serveur.HasExited; $i++) {
    try { $code = (Invoke-RestMethod -Method Post -Uri "$url/api/pair" -Headers @{ Authorization = $auth }).code; break }
    catch { Start-Sleep -Milliseconds 500 }
}
if (-not $code) {
    if (-not $serveur.HasExited) { Stop-Process -Id $serveur.Id -Force }
    Alerte "Le serveur OpenCode n'a pas demarre sur $url.`nEssaie `"Lancer l'agent (web).cmd`" pour voir le message d'erreur."
}
# Le cache hors-ligne (service worker) garde d'un lancement a l'autre bloque la page au demarrage suivant :
# on le vide (profil dedie a cette fenetre, rien d'autre). L'interface tourne en local, elle n'en a pas besoin.
if (-not (FenetreOuverte)) {
    Remove-Item -LiteralPath (Join-Path $profil 'Default\Service Worker') -Recurse -Force -ErrorAction SilentlyContinue
}
Fenetre "$url/auth/connect/$code"

# Atelier (panneau de gestion) : on lui donne l'adresse et le mot de passe de ce serveur pour qu'il recharge
# la config sans fermer l'agent (fichier dans _maintenance, que l'agent n'a pas le droit de lire), et on le demarre
# en fond s'il ne tourne pas. Il s'arrete seul quelques minutes apres la fermeture de l'agent.
$reel = (Resolve-Path -LiteralPath $Base).Path.TrimEnd('\') -eq 'D:\IA LOCAL'
$atelier = 'D:\IA LOCAL\_maintenance\Atelier-agent'
$session = Join-Path $atelier ("etat\" + $(if ($reel) { 'opencode.json' } else { 'opencode-test.json' }))
if (Test-Path -LiteralPath "$atelier\atelier\atelier.py") {
    New-Item -ItemType Directory -Force -Path (Split-Path $session) | Out-Null
    $contenu = (@{ url = $url; mot_de_passe = $env:OPENCODE_SERVER_PASSWORD } | ConvertTo-Json -Compress)
    [IO.File]::WriteAllText($session, $contenu, (New-Object Text.UTF8Encoding $false))
    $portAtelier = if ($reel) { 4110 } else { 4111 }
    if (-not (Get-NetTCPConnection -LocalPort $portAtelier -State Listen -ErrorAction SilentlyContinue)) {
        $profilAgent = $env:USERPROFILE
        $env:USERPROFILE = $env:VRAI_USERPROFILE; $env:HOME = $env:VRAI_USERPROFILE
        if (-not $reel) { $env:ATELIER_BASE = $Base }
        Start-Process -FilePath 'C:\Program Files\Python314\pythonw.exe' -ArgumentList "`"$atelier\atelier\atelier.py`"" -WindowStyle Hidden | Out-Null
        $env:USERPROFILE = $profilAgent; $env:HOME = $profilAgent; Remove-Item Env:ATELIER_BASE -ErrorAction SilentlyContinue
    }
}

# Tant que la fenetre est ouverte, le serveur tourne ; a sa fermeture, on l'arrete.
Start-Sleep -Seconds 5
while ((FenetreOuverte) -and -not $serveur.HasExited) { Start-Sleep -Seconds 3 }
if (-not $serveur.HasExited) { Stop-Process -Id $serveur.Id -Force }
if ($session) { Remove-Item -LiteralPath $session -Force -ErrorAction SilentlyContinue }
