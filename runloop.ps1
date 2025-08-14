# run_python_loop.ps1
# Remplace le chemin ci-dessous par celui de ton script Python
$pythonScript   = ".\gamegen.py"
$timeoutSeconds = 600   # 10 minutes
$restartDelay   = 2     # secondes

function Commit-And-Push {
    param(
        [string]$CommitMsgPrefix = "Auto: run finished"
    )

    try {
        # Vérifie que git est dispo
        git --version *>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "git n'est pas disponible. Commit/push ignoré."
            return
        }

        # Trouve la racine du dépôt
        $repoRoot = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($repoRoot)) {
            Write-Warning "Répertoire courant hors d'un dépôt Git. Commit/push ignoré."
            return
        }

        $old = Get-Location
        Set-Location $repoRoot

        # Y a-t-il des changements ?
        $status = git status --porcelain
        if (-not $status) {
            Write-Host "Aucun changement à commit."
            Set-Location $old
            return
        }

        git add -A
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $message = "$CommitMsgPrefix at $timestamp"
        git commit -m $message
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Échec du commit."
            Set-Location $old
            return
        }

        # Push vers l'upstream si définie, sinon origin/<branche>
        $branch = (git rev-parse --abbrev-ref HEAD).Trim()
        $hasUpstream = $true
        git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) { $hasUpstream = $false }

        if ($hasUpstream) {
            git push
        } else {
            if (-not [string]::IsNullOrWhiteSpace($branch) -and $branch -ne "HEAD") {
                git push -u origin $branch
            } else {
                Write-Warning "Branche détachée sans upstream. Push ignoré."
            }
        }

        Set-Location $old
    }
    catch {
        Write-Warning "Erreur pendant commit/push : $($_.Exception.Message)"
        try { if ($old) { Set-Location $old } } catch {}
    }
}

while ($true) {
    Write-Host "Démarrage du script Python..."
    $proc = Start-Process -FilePath "python" -ArgumentList @($pythonScript) -NoNewWindow -PassThru
    $timedOut = $false

    try {
        # Attend au plus $timeoutSeconds
        Wait-Process -Id $proc.Id -Timeout $timeoutSeconds -ErrorAction Stop
        # Si on arrive ici, le script s'est terminé avant le timeout
    }
    catch {
        # Timeout : tuer le process
        if (-not $proc.HasExited) {
            $timedOut = $true
            Write-Warning "Timeout de $($timeoutSeconds/60) minutes atteint. Arrêt du script Python (PID $($proc.Id))..."
            Stop-Process -Id $proc.Id -Force
            Wait-Process -Id $proc.Id -ErrorAction SilentlyContinue
            # Pour tuer tout l'arbre de processus si besoin :
            # Start-Process taskkill -ArgumentList "/PID $($proc.Id) /T /F" -NoNewWindow -Wait
        }
    }

    if (-not $timedOut) {
        $exitCode = $proc.ExitCode
        Write-Host "Le script s'est terminé (code $exitCode). Commit & push des changements..."
        Commit-And-Push -CommitMsgPrefix "Auto-commit: gamegen run exit $exitCode"
    } else {
        Write-Host "Aucun commit (le script a été stoppé pour timeout)."
    }

    Write-Host "Redémarrage dans $restartDelay seconde(s)..."
    Start-Sleep -Seconds $restartDelay
}
