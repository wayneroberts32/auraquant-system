# AuraQuant Deployment Script
# This script helps automate the deployment process

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "    AuraQuant Multi-Agent Swarm Deployment     " -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Function to open URL in browser
function Open-Browser {
    param([string]$url)
    Start-Process $url
}

# Function to display colored status
function Write-Status {
    param([string]$message, [string]$status)
    
    if ($status -eq "SUCCESS") {
        Write-Host "✅ $message" -ForegroundColor Green
    } elseif ($status -eq "WARNING") {
        Write-Host "⚠️  $message" -ForegroundColor Yellow
    } elseif ($status -eq "ERROR") {
        Write-Host "❌ $message" -ForegroundColor Red
    } else {
        Write-Host "ℹ️  $message" -ForegroundColor Cyan
    }
}

# Step 1: Check Git Status
Write-Host "Step 1: Checking Git Status..." -ForegroundColor Yellow
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Status "You have uncommitted changes. Committing..." "WARNING"
    git add -A
    git commit -m "Auto-commit before deployment"
} else {
    Write-Status "Git repository is clean" "SUCCESS"
}

Write-Host ""
Write-Host "Step 2: GitHub Repository Setup" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Gray

# Check if remote exists
$remoteExists = git remote get-url origin 2>$null
if ($remoteExists) {
    Write-Status "GitHub remote already configured: $remoteExists" "SUCCESS"
} else {
    Write-Host ""
    Write-Host "You need to create a GitHub repository first!" -ForegroundColor Red
    Write-Host ""
    Write-Host "1. Opening GitHub in your browser..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2
    Open-Browser "https://github.com/new"
    
    Write-Host ""
    Write-Host "2. Create a new repository with these settings:" -ForegroundColor Yellow
    Write-Host "   - Repository name: auraquant-system" -ForegroundColor White
    Write-Host "   - Set as PRIVATE" -ForegroundColor White
    Write-Host "   - Do NOT initialize with README" -ForegroundColor White
    Write-Host ""
    
    $githubUsername = Read-Host "Enter your GitHub username"
    
    if ($githubUsername) {
        $repoUrl = "https://github.com/$githubUsername/auraquant-system.git"
        Write-Host ""
        Write-Host "Adding GitHub remote..." -ForegroundColor Cyan
        git remote add origin $repoUrl
        Write-Status "Remote added: $repoUrl" "SUCCESS"
    }
}

Write-Host ""
Write-Host "Step 3: Push to GitHub" -ForegroundColor Yellow
Write-Host "======================" -ForegroundColor Gray

$pushConfirm = Read-Host "Ready to push to GitHub? (y/n)"
if ($pushConfirm -eq 'y') {
    Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
    git branch -M main
    git push -u origin main 2>&1 | Out-String
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Code successfully pushed to GitHub!" "SUCCESS"
    } else {
        Write-Status "Push failed. You may need to authenticate." "ERROR"
        Write-Host ""
        Write-Host "If authentication fails, create a Personal Access Token:" -ForegroundColor Yellow
        Write-Host "1. Go to: https://github.com/settings/tokens" -ForegroundColor White
        Write-Host "2. Generate new token (classic)" -ForegroundColor White
        Write-Host "3. Select scope: repo (all)" -ForegroundColor White
        Write-Host "4. Use the token as password when prompted" -ForegroundColor White
        
        # Retry push
        $retry = Read-Host "Try again? (y/n)"
        if ($retry -eq 'y') {
            git push -u origin main
        }
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "          DEPLOYMENT INSTRUCTIONS               " -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 4: Backend Deployment (Render)" -ForegroundColor Yellow
Write-Host "====================================" -ForegroundColor Gray
Write-Host ""
Write-Host "1. Opening Render Dashboard..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
Open-Browser "https://dashboard.render.com"

Write-Host ""
Write-Host "2. Create New Web Service with these settings:" -ForegroundColor Yellow
Write-Host "   Name: auraquant-backend" -ForegroundColor White
Write-Host "   Runtime: Python 3" -ForegroundColor White
Write-Host "   Build Command: pip install -r requirements.txt" -ForegroundColor White
Write-Host "   Start Command: python start_system.py" -ForegroundColor White
Write-Host '   Plan: Starter ($7/month)' -ForegroundColor White
Write-Host ""
Write-Host "3. Add Environment Variables:" -ForegroundColor Yellow
Write-Host "   MONGODB_URI=<your_mongodb_connection>" -ForegroundColor White
Write-Host "   PORT=10000" -ForegroundColor White
Write-Host "   PYTHON_VERSION=3.10" -ForegroundColor White
Write-Host ""

$renderReady = Read-Host "Press Enter when Render deployment is started..."

Write-Host ""
Write-Host "Step 5: Frontend Deployment (Cloudflare)" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Gray
Write-Host ""
Write-Host "1. Opening Cloudflare Dashboard..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
Open-Browser "https://dash.cloudflare.com"

Write-Host ""
Write-Host "2. Create Pages Project with these settings:" -ForegroundColor Yellow
Write-Host "   Project name: auraquant-frontend" -ForegroundColor White
Write-Host '   Build command: cd frontend && npm install && npm run build' -ForegroundColor White
Write-Host "   Build output: frontend/build" -ForegroundColor White
Write-Host "   Root directory: /" -ForegroundColor White
Write-Host ""
Write-Host "3. Add Environment Variable:" -ForegroundColor Yellow
Write-Host "   REACT_APP_API_URL=https://auraquant-backend.onrender.com" -ForegroundColor White
Write-Host ""

$cloudflareReady = Read-Host "Press Enter when Cloudflare deployment is started..."

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "            DEPLOYMENT CHECKLIST                " -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Create checklist
$checklist = @(
    "GitHub repository created and code pushed",
    "Render backend service created",
    "Environment variables added to Render",
    "Cloudflare Pages project created",
    "Environment variables added to Cloudflare",
    "Backend deployment successful",
    "Frontend deployment successful"
)

foreach ($item in $checklist) {
    $completed = Read-Host "✓ $item - Complete? (y/n)"
    if ($completed -eq 'y') {
        Write-Status $item "SUCCESS"
    } else {
        Write-Status $item "WARNING"
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "            VERIFICATION URLS                   " -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Backend Health Check:" -ForegroundColor Yellow
Write-Host "https://auraquant-backend.onrender.com/health" -ForegroundColor White
Write-Host ""
Write-Host "Swarm Status:" -ForegroundColor Yellow
Write-Host "https://auraquant-backend.onrender.com/api/swarm/status" -ForegroundColor White
Write-Host ""
Write-Host "Frontend Application:" -ForegroundColor Yellow
Write-Host "https://auraquant-frontend.pages.dev" -ForegroundColor White
Write-Host ""

$testEndpoints = Read-Host "Would you like to test the endpoints? (y/n)"
if ($testEndpoints -eq 'y') {
    Write-Host ""
    Write-Host "Testing Backend Health..." -ForegroundColor Cyan
    try {
        $health = Invoke-WebRequest -Uri "https://auraquant-backend.onrender.com/health" -UseBasicParsing
        Write-Status "Backend is healthy!" "SUCCESS"
    } catch {
        Write-Status "Backend not responding yet (may still be deploying)" "WARNING"
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "     DEPLOYMENT PROCESS COMPLETE!               " -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your AuraQuant Multi-Agent Swarm is deploying!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Monitor Render logs for backend status" -ForegroundColor White
Write-Host "2. Monitor Cloudflare build for frontend status" -ForegroundColor White
Write-Host "3. Test all endpoints once deployed" -ForegroundColor White
Write-Host "4. Configure custom domain if needed" -ForegroundColor White
Write-Host ""
Write-Status "System: AuraQuant v1.0 - Production Ready" "SUCCESS"
Write-Host ""

# Keep window open
Read-Host "Press Enter to exit"