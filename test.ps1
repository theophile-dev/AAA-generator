
git add -A
git commit -m "Auto update $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-Null

# Push
git push