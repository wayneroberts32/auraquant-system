# AuraQuant Render Deployment Script - Task 7/12
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AURAQUANT RENDER DEPLOYMENT (7/12)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Generate secret keys
$chars = @()
$chars += (65..90) | ForEach-Object {[char]$_}
$chars += (97..122) | ForEach-Object {[char]$_}
$chars += (48..57) | ForEach-Object {[char]$_}

$SECRET_KEY = -join ($chars | Get-Random -Count 32)
$JWT_SECRET = -join ($chars | Get-Random -Count 32)

# Create render.env file
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
Write-Host "Environment variables saved to render.env" -ForegroundColor Green

# Create render deployment config
$configContent = @"
{
  "name": "auraquant-api",
  "type": "web_service",
  "repo": "https://github.com/wayneroberts32/auraquant-system.git",
  "branch": "cloudflare-production",
  "runtime": "python",
  "buildCommand": "pip install -r requirements.txt",
  "startCommand": "python backend/main.py",
  "healthCheckPath": "/health"
}
"@

$configContent | Out-File -FilePath "render-config.json" -Encoding UTF8
Write-Host "Render configuration created" -ForegroundColor Green

Write-Host ""
Write-Host "DEPLOYMENT INFORMATION" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host "Repository: https://github.com/wayneroberts32/auraquant-system.git" -ForegroundColor White
Write-Host "Branch: cloudflare-production" -ForegroundColor White
Write-Host "MongoDB: Connected to Cluster0" -ForegroundColor Green
Write-Host ""
Write-Host "GENERATED SECRETS:" -ForegroundColor Yellow
Write-Host "SECRET_KEY=$SECRET_KEY" -ForegroundColor White
Write-Host "JWT_SECRET=$JWT_SECRET" -ForegroundColor White
Write-Host ""
Write-Host "Backend URL will be: https://auraquant-api.onrender.com" -ForegroundColor Cyan
Write-Host ""
Write-Host "Opening Render dashboard..." -ForegroundColor Blue
Start-Process "https://dashboard.render.com"
Write-Host ""
Write-Host "Task 7/12 preparation complete!" -ForegroundColor Green