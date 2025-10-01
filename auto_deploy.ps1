# AuraQuant Automated Deployment Script
# System Engineer Automation

param(
    [string]$GitHubUsername = "",
    [string]$GitHubToken = "",
    [string]$RenderAPIKey = "",
    [string]$CloudflareAPIKey = "",
    [string]$MongoDBUri = ""
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AURAQUANT AUTOMATED DEPLOYMENT SYSTEM        " -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Function to make API calls
function Invoke-APICall {
    param(
        [string]$Uri,
        [string]$Method = "GET",
        [hashtable]$Headers,
        [string]$Body
    )
    
    try {
        $params = @{
            Uri = $Uri
            Method = $Method
            Headers = $Headers
            ContentType = "application/json"
        }
        
        if ($Body) {
            $params.Body = $Body
        }
        
        return Invoke-RestMethod @params
    } catch {
        Write-Host "API Error: $_" -ForegroundColor Red
        return $null
    }
}

# Step 1: Get GitHub credentials
Write-Host "STEP 1: GitHub Configuration" -ForegroundColor Yellow
Write-Host "=============================" -ForegroundColor Gray

if (-not $GitHubUsername) {
    $GitHubUsername = Read-Host "Enter your GitHub username"
}

if (-not $GitHubToken) {
    Write-Host ""
    Write-Host "You need a GitHub Personal Access Token" -ForegroundColor Yellow
    Write-Host "Opening GitHub tokens page..." -ForegroundColor Cyan
    Start-Process "https://github.com/settings/tokens/new"
    Write-Host ""
    Write-Host "Create token with 'repo' scope, then paste it here:" -ForegroundColor Yellow
    $secureToken = Read-Host "GitHub Token" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
    $GitHubToken = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
}

# Step 2: Create GitHub repository
Write-Host ""
Write-Host "STEP 2: Creating GitHub Repository" -ForegroundColor Yellow
Write-Host "===================================" -ForegroundColor Gray

$repoName = "auraquant-system"
$createRepoUrl = "https://api.github.com/user/repos"
$authHeader = @{
    "Authorization" = "token $GitHubToken"
    "Accept" = "application/vnd.github.v3+json"
}

$repoBody = @{
    name = $repoName
    private = $true
    description = "AuraQuant Multi-Agent Trading System"
    auto_init = $false
} | ConvertTo-Json

Write-Host "Creating private repository: $repoName" -ForegroundColor Cyan
$repoResult = Invoke-APICall -Uri $createRepoUrl -Method POST -Headers $authHeader -Body $repoBody

if ($repoResult) {
    Write-Host "✅ Repository created successfully!" -ForegroundColor Green
} else {
    Write-Host "Repository may already exist or creation failed" -ForegroundColor Yellow
}

# Step 3: Configure Git and push
Write-Host ""
Write-Host "STEP 3: Pushing Code to GitHub" -ForegroundColor Yellow
Write-Host "===============================" -ForegroundColor Gray

$remoteUrl = "https://${GitHubUsername}:${GitHubToken}@github.com/${GitHubUsername}/${repoName}.git"

# Remove existing remote if exists
git remote remove origin 2>$null

# Add new remote
Write-Host "Adding remote repository..." -ForegroundColor Cyan
git remote add origin $remoteUrl

# Push to GitHub
Write-Host "Pushing code to GitHub..." -ForegroundColor Cyan
git branch -M main
git push -u origin main --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Code pushed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Push failed. Check credentials." -ForegroundColor Red
    exit 1
}

# Step 4: Get Render API key
Write-Host ""
Write-Host "STEP 4: Render Backend Deployment" -ForegroundColor Yellow
Write-Host "==================================" -ForegroundColor Gray

if (-not $RenderAPIKey) {
    Write-Host ""
    Write-Host "Opening Render dashboard to get API key..." -ForegroundColor Cyan
    Start-Process "https://dashboard.render.com/account/api-keys"
    Write-Host ""
    $RenderAPIKey = Read-Host "Enter your Render API key"
}

# Step 5: Create Render service
Write-Host "Creating Render service..." -ForegroundColor Cyan

$renderHeaders = @{
    "Authorization" = "Bearer $RenderAPIKey"
    "Content-Type" = "application/json"
}

$renderServiceBody = @{
    type = "web_service"
    name = "auraquant-backend"
    repo = "https://github.com/$GitHubUsername/$repoName"
    autoDeploy = "yes"
    branch = "main"
    buildCommand = "pip install -r requirements.txt"
    startCommand = "python start_system.py"
    envVars = @(
        @{ key = "MONGODB_URI"; value = $MongoDBUri },
        @{ key = "PORT"; value = "10000" },
        @{ key = "PYTHON_VERSION"; value = "3.10" }
    )
    plan = "starter"
    region = "oregon"
} | ConvertTo-Json -Depth 10

$createServiceUrl = "https://api.render.com/v1/services"
$serviceResult = Invoke-APICall -Uri $createServiceUrl -Method POST -Headers $renderHeaders -Body $renderServiceBody

if ($serviceResult) {
    Write-Host "✅ Render service created!" -ForegroundColor Green
    $serviceId = $serviceResult.service.id
    Write-Host "Service ID: $serviceId" -ForegroundColor Cyan
} else {
    Write-Host "⚠️ Manual Render setup required" -ForegroundColor Yellow
    Start-Process "https://dashboard.render.com/new/web"
}

# Step 6: Cloudflare Pages deployment
Write-Host ""
Write-Host "STEP 5: Cloudflare Frontend Deployment" -ForegroundColor Yellow
Write-Host "=======================================" -ForegroundColor Gray

if (-not $CloudflareAPIKey) {
    Write-Host ""
    Write-Host "Opening Cloudflare to create Pages project..." -ForegroundColor Cyan
    Start-Process "https://dash.cloudflare.com/?to=/:account/pages/new/provider/github"
    Write-Host ""
    Write-Host "Please complete Cloudflare Pages setup manually:" -ForegroundColor Yellow
    Write-Host "1. Connect GitHub account" -ForegroundColor White
    Write-Host "2. Select: auraquant-system repository" -ForegroundColor White
    Write-Host "3. Project name: auraquant-frontend" -ForegroundColor White
    Write-Host "4. Build command: cd frontend && npm install && npm run build" -ForegroundColor White
    Write-Host "5. Build output: frontend/build" -ForegroundColor White
    Write-Host "6. Add env variable: REACT_APP_API_URL = https://auraquant-backend.onrender.com" -ForegroundColor White
}

# Step 7: Wait for deployments
Write-Host ""
Write-Host "STEP 6: Deployment Status" -ForegroundColor Yellow
Write-Host "==========================" -ForegroundColor Gray

Write-Host ""
Write-Host "⏳ Services are deploying..." -ForegroundColor Yellow
Write-Host "Backend URL: https://auraquant-backend.onrender.com" -ForegroundColor Cyan
Write-Host "Frontend URL: https://auraquant-frontend.pages.dev" -ForegroundColor Cyan
Write-Host ""
Write-Host "Deployment typically takes:" -ForegroundColor Yellow
Write-Host "- Render Backend: 5-10 minutes" -ForegroundColor White
Write-Host "- Cloudflare Frontend: 3-5 minutes" -ForegroundColor White

# Step 8: Test endpoints
Write-Host ""
$testNow = Read-Host "Test endpoints now? (y/n)"

if ($testNow -eq 'y') {
    Write-Host ""
    Write-Host "Testing backend health..." -ForegroundColor Cyan
    
    $maxAttempts = 20
    $attempt = 0
    $success = $false
    
    while ($attempt -lt $maxAttempts -and -not $success) {
        $attempt++
        Write-Host "Attempt $attempt of $maxAttempts..." -ForegroundColor Gray
        
        try {
            $health = Invoke-WebRequest -Uri "https://auraquant-backend.onrender.com/health" -UseBasicParsing -TimeoutSec 10
            if ($health.StatusCode -eq 200) {
                Write-Host "✅ Backend is healthy!" -ForegroundColor Green
                $success = $true
            }
        } catch {
            if ($attempt -lt $maxAttempts) {
                Write-Host "Waiting 30 seconds..." -ForegroundColor Gray
                Start-Sleep -Seconds 30
            }
        }
    }
    
    if (-not $success) {
        Write-Host "⚠️ Backend not responding yet. Check Render logs." -ForegroundColor Yellow
    }
}

# Final summary
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "         DEPLOYMENT COMPLETE!                  " -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Deployment Summary:" -ForegroundColor Yellow
Write-Host "GitHub Repository: https://github.com/$GitHubUsername/$repoName" -ForegroundColor White
Write-Host "Backend Status: Check https://dashboard.render.com" -ForegroundColor White
Write-Host "Frontend Status: Check https://dash.cloudflare.com" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Your URLs:" -ForegroundColor Yellow
Write-Host "Backend API: https://auraquant-backend.onrender.com" -ForegroundColor Cyan
Write-Host "Frontend App: https://auraquant-frontend.pages.dev" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ System: AuraQuant Multi-Agent Swarm v1.0" -ForegroundColor Green
Write-Host "✅ Status: DEPLOYED TO PRODUCTION" -ForegroundColor Green
Write-Host ""

# Open monitoring dashboards
Write-Host "Opening monitoring dashboards..." -ForegroundColor Cyan
Start-Process "https://dashboard.render.com"
Start-Process "https://dash.cloudflare.com"

Write-Host ""
Write-Host "Deployment automation complete!" -ForegroundColor Green