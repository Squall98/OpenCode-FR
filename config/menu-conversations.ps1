# Menu de reprise des conversations de l'agent local.
# Appelé par "Lancer l'agent.cmd", qui prépare l'environnement (dossiers isolés, moteur IA locale).
#   -Essai : affiche la commande qui serait lancée au lieu d'ouvrir OpenCode (pour tester le menu).
param([string]$Base = (Split-Path $PSScriptRoot -Parent), [switch]$Essai)

try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
try { $Host.UI.RawUI.WindowTitle = 'Agent local' } catch {}
$oc = Join-Path $Base 'opencode\node_modules\.bin\opencode.cmd'
# Les conversations sont rangées par dossier : on se place toujours dans D:\IA LOCAL.
Set-Location -LiteralPath $Base

function Depuis([long]$ms) {
    $d = [DateTimeOffset]::FromUnixTimeMilliseconds($ms).LocalDateTime
    $ecart = (Get-Date) - $d
    if ($ecart.TotalMinutes -lt 1) { return "à l'instant" }
    if ($ecart.TotalMinutes -lt 60) { return "il y a {0} min" -f [int][Math]::Floor($ecart.TotalMinutes) }
    if ($d.Date -eq (Get-Date).Date) { return "il y a {0} h" -f [int][Math]::Floor($ecart.TotalHours) }
    if ($d.Date -eq (Get-Date).Date.AddDays(-1)) { return "hier " + $d.ToString('HH:mm') }
    return $d.ToString('dd/MM HH:mm')
}

function Lancer([string]$id) {
    if ($id) { $arguments = @('--standalone', $Base, '--session', $id) } else { $arguments = @('--standalone', $Base) }
    if ($Essai) { Write-Host ("ESSAI -> opencode " + ($arguments -join ' ')); return }
    & $oc @arguments
}

Write-Host ''
Write-Host '  Chargement de tes conversations...' -ForegroundColor DarkGray
$sessions = @()
try {
    $json = & $oc session list --standalone --max-count 15 --format json 2>$null
    if ($json) {
        # PowerShell 5.1 renvoie le tableau JSON d'un seul bloc : on le déplie, et on ignore les entrées sans identifiant.
        $liste = ($json -join "`n") | ConvertFrom-Json
        $sessions = @($liste | ForEach-Object { $_ } | Where-Object { $_.id })
    }
} catch { $sessions = @() }

while ($true) {
    if (-not $Essai) { Clear-Host }
    Write-Host ''
    Write-Host '  ╔══════════════ AGENT LOCAL · tes conversations ══════════════╗' -ForegroundColor Magenta
    Write-Host ''
    if ($sessions.Count -eq 0) {
        Write-Host '   (aucune conversation pour l''instant)' -ForegroundColor DarkGray
    } else {
        for ($i = 0; $i -lt $sessions.Count; $i++) {
            $titre = $sessions[$i].title
            if (-not $titre) { $titre = '(sans titre)' }
            if ($titre.Length -gt 46) { $titre = $titre.Substring(0, 45) + '…' }
            $num = '{0,3}.' -f ($i + 1)
            Write-Host "  $num " -NoNewline -ForegroundColor Cyan
            Write-Host ('{0,-47}' -f $titre) -NoNewline
            Write-Host (Depuis $sessions[$i].updated) -ForegroundColor DarkGray
        }
    }
    Write-Host ''
    Write-Host '    N. Nouvelle conversation' -ForegroundColor Green
    Write-Host ''
    if ($sessions.Count -gt 0) {
        Write-Host '   Entrée = reprendre la n°1   ·   Q = quitter' -ForegroundColor DarkGray
    } else {
        Write-Host '   Entrée = nouvelle conversation   ·   Q = quitter' -ForegroundColor DarkGray
    }
    Write-Host '   Astuce : dans OpenCode, Ctrl+R renomme la conversation (ex. « Play-bubble · 2 · API »).' -ForegroundColor DarkGray
    Write-Host ''
    $choix = Read-Host '  Ton choix'
    if ($null -eq $choix) { return }
    $choix = $choix.Trim()

    if ($choix -eq '') {
        if ($sessions.Count -gt 0) { Lancer $sessions[0].id } else { Lancer '' }
        return
    }
    if ($choix -match '^[nN]$') { Lancer ''; return }
    if ($choix -match '^[qQ]$') { return }
    $n = 0
    if ([int]::TryParse($choix, [ref]$n) -and $n -ge 1 -and $n -le $sessions.Count) { Lancer $sessions[$n - 1].id; return }

    Write-Host "  « $choix » ne correspond à rien : tape un numéro, N, Q ou juste Entrée." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
}
