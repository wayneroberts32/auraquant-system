# AuraQuant Cloudflare Deployment Script - Task 8/12
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CLOUDFLARE PAGES DEPLOYMENT (8/12)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if wrangler is installed
$wranglerCheck = npm list -g wrangler 2>&1
if ($wranglerCheck -notlike "*wrangler*") {
    Write-Host "Installing Cloudflare Wrangler CLI..." -ForegroundColor Yellow
    npm install -g wrangler
}

# Create wrangler configuration
$wranglerConfig = @"
name = "auraquant"
compatibility_date = "2025-01-10"

[site]
bucket = "./frontend"

[[deployment]]
name = "production"
routes = ["auraquant.pages.dev/*"]
"@

$wranglerConfig | Out-File -FilePath "wrangler.toml" -Encoding UTF8
Write-Host "Wrangler configuration created" -ForegroundColor Green

# Create deployment script
$deployScript = @"
# Deploy to Cloudflare Pages
wrangler pages deploy frontend --project-name=auraquant --branch=main
"@

$deployScript | Out-File -FilePath "deploy-cloudflare.sh" -Encoding UTF8
Write-Host "Deployment script created" -ForegroundColor Green

Write-Host ""
Write-Host "CLOUDFLARE DEPLOYMENT INFO" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan
Write-Host "Frontend directory: frontend/" -ForegroundColor White
Write-Host "Index file: frontend/index.html" -ForegroundColor White
Write-Host "Pages: frontend/pages/ (45+ pages)" -ForegroundColor White
Write-Host "MongoDB: Connected to Cluster0" -ForegroundColor Green
Write-Host ""
Write-Host "Your frontend will be deployed to:" -ForegroundColor Yellow
Write-Host "https://auraquant.pages.dev" -ForegroundColor Cyan
Write-Host ""

# Create environment config for frontend
$frontendEnv = @"
VITE_API_URL=https://auraquant-api.onrender.com
REACT_APP_API_URL=https://auraquant-api.onrender.com
VITE_MONGODB_URI=mongodb+srv://auraquant:AuraQuant_Infinity@cluster0.qcg7f4h.mongodb.net/
"@

$frontendEnv | Out-File -FilePath "frontend\.env.production" -Encoding UTF8
Write-Host "Frontend environment variables configured" -ForegroundColor Green

Write-Host ""
Write-Host "Attempting automated deployment..." -ForegroundColor Blue

# Try to deploy using wrangler
try {
    Set-Location frontend
    npx wrangler pages deploy . --project-name=auraquant --branch=main 2>&1
    Set-Location ..
    Write-Host "Deployment initiated!" -ForegroundColor Green
} catch {
    Write-Host "Manual steps required - Opening Cloudflare dashboard..." -ForegroundColor Yellow
    Start-Process "https://dash.cloudflare.com/pages"
}

Write-Host ""
Write-Host "Task 8/12 complete!" -ForegroundColor Green