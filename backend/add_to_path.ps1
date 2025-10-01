# Add Python 3.12 to PATH permanently

$python312Path = "C:\Users\User\AppData\Local\Programs\Python\Python312"
$python312Scripts = "C:\Users\User\AppData\Local\Programs\Python\Python312\Scripts"

# Get current user PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

# Check if Python 3.12 is already in PATH
if ($currentPath -notlike "*$python312Path*") {
    # Add Python 3.12 to PATH
    $newPath = "$python312Path;$python312Scripts;$currentPath"
    
    # Clean up any duplicate semicolons
    $newPath = $newPath -replace ";;+", ";"
    
    # Set the new PATH
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    
    Write-Host "✅ Python 3.12 added to PATH successfully!" -ForegroundColor Green
    Write-Host "   Python: $python312Path" -ForegroundColor Cyan
    Write-Host "   Scripts: $python312Scripts" -ForegroundColor Cyan
} else {
    Write-Host "Python 3.12 is already in PATH" -ForegroundColor Yellow
}

# Update current session
$env:Path = "$python312Path;$python312Scripts;$env:Path"

Write-Host ""
Write-Host "Please restart your terminal for changes to take effect" -ForegroundColor Yellow
Write-Host "Or use: python api\main.py to start the API now" -ForegroundColor Cyan