# runloop.ps1

$pythonExe      = "python"              # or full path to python.exe
$pythonScript   = ".\gamegen.py"        # adjust if needed
$timeoutSeconds = 600                   # 10 minutes
$restartDelay   = 2                     # seconds

while ($true) {
    Write-Host "Starting $pythonScript..."
    $proc = Start-Process -FilePath $pythonExe -ArgumentList @($pythonScript) -NoNewWindow -PassThru
    $timedOut = $false

    try {
        # Wait up to $timeoutSeconds; throws if timeout hit
        Wait-Process -Id $proc.Id -Timeout $timeoutSeconds -ErrorAction Stop
        python .\updateindex.py
        $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        git add -A
        git commit -m $stamp
        git push
    } catch {
        if (-not $proc.HasExited) {
            $timedOut = $true
            Write-Warning "Timeout reached ($timeoutSeconds s). Killing PID $($proc.Id)..."
            Stop-Process -Id $proc.Id -Force
            Wait-Process -Id $proc.Id -ErrorAction SilentlyContinue
        }
    }
    Write-Host "Restarting in $restartDelay second(s)..."
    Start-Sleep -Seconds $restartDelay
}