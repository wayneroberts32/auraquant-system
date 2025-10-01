# Push AuraQuant to GitHub
Clear-Host
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   PUSHING AURAQUANT TO GITHUB                 " -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Your GitHub username is wayneroberts32
$username = "wayneroberts32"
Write-Host "GitHub Username: $username" -ForegroundColor Green
Write-Host ""

# First, create the repository on GitHub
Write-Host "Step 1: Creating repository on GitHub..." -ForegroundColor Yellow
Write-Host "Opening GitHub to create new repository..." -ForegroundColor Cyan
Start-Process "https://github.com/new"

Write-Host ""
Write-Host "CREATE THE REPOSITORY WITH THESE SETTINGS:" -ForegroundColor Red
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Repository name: auraquant-system" -ForegroundColor Yellow
Write-Host "Description: AuraQuant Multi-Agent Trading System" -ForegroundColor White
Write-Host "Set as: PRIVATE" -ForegroundColor Yellow
Write-Host "DO NOT check any boxes (no README, no .gitignore, no license)" -ForegroundColor Red
Write-Host "Click: Create repository" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter AFTER you've created the repository on GitHub"

# Add the remote
Write-Host ""
Write-Host "Step 2: Adding GitHub remote..." -ForegroundColor Yellow
$remoteUrl = "https://github.com/$username/auraquant-system.git"
git remote add origin $remoteUrl
Write-Host "Remote added: $remoteUrl" -ForegroundColor Green

# Push the code
Write-Host ""
Write-Host "Step 3: Pushing code to GitHub..." -ForegroundColor Yellow
Write-Host "You'll need to enter your GitHub credentials:" -ForegroundColor Cyan
Write-Host "Username: $username" -ForegroundColor White
Write-Host "Password: Use your Personal Access Token (NOT your password)" -ForegroundColor Red
Write-Host ""

git branch -M main
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "   ✅ CODE PUSHED SUCCESSFULLY!                " -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your repository is now at:" -ForegroundColor Cyan
    Write-Host "https://github.com/$username/auraquant-system" -ForegroundColor White
    Write-Host ""
    Write-Host "NOW GO BACK TO CLOUDFLARE AND:" -ForegroundColor Yellow
    Write-Host "1. Refresh the repository list" -ForegroundColor White
    Write-Host "2. Select: auraquant-system" -ForegroundColor Green
    Write-Host "3. Continue with deployment" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "Push failed. You may need a Personal Access Token:" -ForegroundColor Red
    Write-Host "1. Go to: https://github.com/settings/tokens" -ForegroundColor Yellow
    Write-Host "2. Generate new token (classic)" -ForegroundColor White
    Write-Host "3. Check 'repo' scope" -ForegroundColor White
    Write-Host "4. Use the token as your password" -ForegroundColor White
}

Write-Host ""
Read-Host "Press Enter to continue"