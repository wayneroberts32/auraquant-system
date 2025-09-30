# AuraQuant Deployment Wizard
Clear-Host
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "     AURAQUANT DEPLOYMENT WIZARD               " -ForegroundColor Yellow  
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get GitHub Username
Write-Host "Enter your GitHub username:" -ForegroundColor Yellow
$username = Read-Host "GitHub Username"

# Get GitHub Token
Write-Host ""
Write-Host "Enter your GitHub Personal Access Token:" -ForegroundColor Yellow
Write-Host "(The one you just created)" -ForegroundColor Gray
$token = Read-Host "GitHub Token"

# Create repository via GitHub API
Write-Host ""
Write-Host "Creating GitHub repository..." -ForegroundColor Cyan

$headers = @{
    "Authorization" = "token $token"
    "Accept" = "application/vnd.github.v3+json"
}

$body = @{
    "name" = "auraquant-system"
    "private" = $true
    "description" = "AuraQuant Multi-Agent Trading System"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Method Post -Headers $headers -Body $body -ContentType "application/json"
    Write-Host "✅ Repository created successfully!" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 422) {
        Write-Host "Repository already exists, continuing..." -ForegroundColor Yellow
    } else {
        Write-Host "Error creating repository: $_" -ForegroundColor Red
    }
}

# Configure Git remote
Write-Host ""
Write-Host "Configuring Git..." -ForegroundColor Cyan

# Remove old remote if exists
git remote remove origin 2>$null

# Add new remote with embedded credentials
$remoteUrl = "https://${username}:${token}@github.com/${username}/auraquant-system.git"
git remote add origin $remoteUrl

# Push to GitHub
Write-Host "Pushing code to GitHub..." -ForegroundColor Cyan
git branch -M main
git push -u origin main --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Code pushed to GitHub successfully!" -ForegroundColor Green
    Write-Host "Repository: https://github.com/$username/auraquant-system" -ForegroundColor White
} else {
    Write-Host "❌ Failed to push code" -ForegroundColor Red
    exit 1
}

# Now handle Render deployment
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "         RENDER BACKEND DEPLOYMENT              " -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Opening Render dashboard..." -ForegroundColor Cyan
Start-Process "https://dashboard.render.com/new/web"

Write-Host ""
Write-Host "RENDER SETUP INSTRUCTIONS:" -ForegroundColor Yellow
Write-Host "1. Click 'Connect GitHub account'" -ForegroundColor White
Write-Host "2. Authorize Render to access your GitHub" -ForegroundColor White
Write-Host "3. Select repository: auraquant-system" -ForegroundColor White
Write-Host "4. Fill in these settings:" -ForegroundColor White
Write-Host ""
Write-Host "   Name: auraquant-backend" -ForegroundColor Cyan
Write-Host "   Region: Oregon (US West)" -ForegroundColor Cyan
Write-Host "   Branch: main" -ForegroundColor Cyan
Write-Host "   Runtime: Python 3" -ForegroundColor Cyan
Write-Host "   Build Command: pip install -r requirements.txt" -ForegroundColor Cyan
Write-Host "   Start Command: python start_system.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Click Advanced → Add Environment Variables:" -ForegroundColor White
Write-Host "   MONGODB_URI = (your MongoDB connection string)" -ForegroundColor Cyan
Write-Host "   PORT = 10000" -ForegroundColor Cyan
Write-Host "   PYTHON_VERSION = 3.10" -ForegroundColor Cyan
Write-Host ""
Write-Host "6. Select Plan: Starter ($7/month)" -ForegroundColor White
Write-Host "7. Click 'Create Web Service'" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter when Render deployment is started"

# Now handle Cloudflare deployment
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "      CLOUDFLARE FRONTEND DEPLOYMENT           " -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Opening Cloudflare Pages..." -ForegroundColor Cyan
Start-Process "https://dash.cloudflare.com/?to=/:account/pages/new/provider/github"

Write-Host ""
Write-Host "CLOUDFLARE SETUP INSTRUCTIONS:" -ForegroundColor Yellow
Write-Host "1. Connect to GitHub" -ForegroundColor White
Write-Host "2. Select repository: auraquant-system" -ForegroundColor White
Write-Host "3. Configure build settings:" -ForegroundColor White
Write-Host ""
Write-Host "   Project name: auraquant-frontend" -ForegroundColor Cyan
Write-Host "   Production branch: main" -ForegroundColor Cyan
Write-Host "   Framework preset: None" -ForegroundColor Cyan
Write-Host "   Build command: cd frontend && npm install && npm run build" -ForegroundColor Cyan
Write-Host "   Build output directory: frontend/build" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Add Environment Variable:" -ForegroundColor White
Write-Host "   REACT_APP_API_URL = https://auraquant-backend.onrender.com" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Click 'Save and Deploy'" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter when Cloudflare deployment is started"

# Summary
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "        DEPLOYMENT INITIATED!                  " -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "✅ GitHub Repository:" -ForegroundColor Yellow
Write-Host "   https://github.com/$username/auraquant-system" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏳ Services Deploying:" -ForegroundColor Yellow
Write-Host "   Backend: https://auraquant-backend.onrender.com (5-10 min)" -ForegroundColor Cyan
Write-Host "   Frontend: https://auraquant-frontend.pages.dev (3-5 min)" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Monitor Progress:" -ForegroundColor Yellow
Write-Host "   Render: https://dashboard.render.com" -ForegroundColor White
Write-Host "   Cloudflare: https://dash.cloudflare.com" -ForegroundColor White
Write-Host ""
Write-Host "✅ AuraQuant Multi-Agent Swarm v1.0 is deploying!" -ForegroundColor Green
Write-Host ""

# Test deployment
$test = Read-Host "Would you like to test the endpoints when ready? (y/n)"
if ($test -eq 'y') {
    Write-Host ""
    Write-Host "Waiting 2 minutes before testing..." -ForegroundColor Yellow
    Start-Sleep -Seconds 120
    
    Write-Host "Testing backend health..." -ForegroundColor Cyan
    try {
        $health = Invoke-WebRequest -Uri "https://auraquant-backend.onrender.com/health" -UseBasicParsing -TimeoutSec 10
        Write-Host "✅ Backend is responding!" -ForegroundColor Green
    } catch {
        Write-Host '⏳ Backend still deploying. Check in a few minutes.' -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host 'Deployment wizard complete!' -ForegroundColor Green
