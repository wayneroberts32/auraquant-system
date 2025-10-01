# Configure Python 3.12 as the default Python

Write-Host "Configuring Python 3.12 as default..." -ForegroundColor Cyan

$python312Path = "C:\Users\User\AppData\Local\Programs\Python\Python312"
$python312Scripts = "$python312Path\Scripts"

# Add Python 3.12 to current session PATH
$env:Path = "$python312Path;$python312Scripts;$env:Path"

Write-Host "Python 3.12 paths added to current session" -ForegroundColor Green

# Update system PATH permanently (requires admin)
try {
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    
    # Remove Python 3.13 paths if they exist
    $newPath = $currentPath -replace "C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python313[^;]*;?", ""
    
    # Add Python 3.12 paths at the beginning
    $newPath = "$python312Path;$python312Scripts;$newPath"
    
    # Remove duplicate semicolons
    $newPath = $newPath -replace ";;+", ";"
    
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "User PATH updated permanently" -ForegroundColor Green
} catch {
    Write-Host "Could not update permanent PATH (may need admin rights)" -ForegroundColor Yellow
}

# Test Python installation
Write-Host ""
Write-Host "Testing Python 3.12..." -ForegroundColor Cyan

& "$python312Path\python.exe" --version

Write-Host ""
Write-Host "Configuration complete!" -ForegroundColor Green
Write-Host "Python 3.12 is now available as:" -ForegroundColor Yellow
Write-Host "  $python312Path\python.exe" -ForegroundColor White