# Save this as run_python_loop.ps1
# Replace the path below with your Python script's path
$pythonScript = ".\gamegen.py"

while ($true) {
    Write-Host "Starting Python script..."
    python $pythonScript
    Write-Host "Python script exited. Restarting in 2 seconds..."
    Start-Sleep -Seconds 2
}