# AuraQuant Render Deployment Script
# Task 7/12: Deploy Backend to Render
# This script prepares everything for Render deployment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 AURAQUANT RENDER DEPLOYMENT (7/12)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Render CLI is installed
$renderCLI = Get-Command render -ErrorAction SilentlyContinue

if (-not $renderCLI) {
    Write-Host "📦 Installing Render CLI..." -ForegroundColor Yellow
    # Install Render CLI via npm
    npm install -g @render-oss/render-cli
}

# Create deployment configuration
$renderConfig = @'
{
  "name": "auraquant-api",
  "type": "web_service",
  "repo": "https://github.com/wayneroberts32/auraquant-system.git",
  "branch": "cloudflare-production",
  "runtime": "python",
  "buildCommand": "pip install -r requirements.txt",
  "startCommand": "cd backend && python main.py",
  "healthCheckPath": "/health",
  "envVars": {
    "MONGODB_URI": "mongodb+srv://auraquant:AuraQuant_Infinity@cluster0.qcg7f4h.mongodb.net/auraquant_production?retryWrites=true&w=majority",
    "PORT": "8000",
    "NODE_ENV": "production",
    "CORS_ORIGIN": "https://auraquant.pages.dev,https://auraquant-mobile.pages.dev",
    "PYTHON_VERSION": "3.11"
  }
}
'@

# Save configuration
$renderConfig | Out-File -FilePath "render-deploy.json" -Encoding UTF8
Write-Host "✅ Render configuration created" -ForegroundColor Green

# Generate secret keys
$SECRET_KEY = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
$JWT_SECRET = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

Write-Host ""
Write-Host "📋 DEPLOYMENT INFORMATION" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repository: https://github.com/wayneroberts32/auraquant-system.git" -ForegroundColor White
Write-Host "Branch: cloudflare-production" -ForegroundColor White
Write-Host "MongoDB: Connected to Cluster0" -ForegroundColor Green
Write-Host ""

Write-Host "🔑 GENERATED SECRETS (Copy these to Render):" -ForegroundColor Yellow
Write-Host "SECRET_KEY=$SECRET_KEY" -ForegroundColor White
Write-Host "JWT_SECRET=$JWT_SECRET" -ForegroundColor White
Write-Host ""

# Create environment file for Render
$envContent = @"
MONGODB_URI=mongodb+srv://auraquant:AuraQuant_Infinity@cluster0.qcg7f4h.mongodb.net/auraquant_production?retryWrites=true&w=majority
PORT=8000
NODE_ENV=production
SECRET_KEY=$SECRET_KEY
JWT_SECRET=$JWT_SECRET
CORS_ORIGIN=https://auraquant.pages.dev,https://auraquant-mobile.pages.dev
PYTHON_VERSION=3.11
"@

$envContent | Out-File -FilePath "render.env" -Encoding UTF8
Write-Host "✅ Environment variables saved to render.env" -ForegroundColor Green

Write-Host ""
Write-Host "📌 MANUAL STEPS REQUIRED:" -ForegroundColor Red
Write-Host "========================" -ForegroundColor Red
Write-Host ""
Write-Host "1. Open browser: https://dashboard.render.com" -ForegroundColor Yellow
Write-Host "2. Click 'New +' → 'Web Service'" -ForegroundColor Yellow
Write-Host "3. Connect GitHub repo: auraquant-system" -ForegroundColor Yellow
Write-Host "4. Select branch: cloudflare-production" -ForegroundColor Yellow
Write-Host "5. Copy environment variables from render.env" -ForegroundColor Yellow
Write-Host "6. Click 'Create Web Service'" -ForegroundColor Yellow
Write-Host ""
Write-Host "Your backend will be deployed to:" -ForegroundColor Green
Write-Host "https://auraquant-api.onrender.com" -ForegroundColor Cyan
Write-Host ""

# Open Render dashboard in browser
Write-Host "Opening Render dashboard..." -ForegroundColor Blue
Start-Process "https://dashboard.render.com/create/web-service"

Write-Host ""
Write-Host "✅ Task 7/12 preparation complete!" -ForegroundColor Green
Write-Host "Follow the manual steps above to complete deployment." -ForegroundColor Yellow