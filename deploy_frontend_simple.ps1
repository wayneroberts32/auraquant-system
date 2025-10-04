# AuraQuant Frontend Deployment - Simple Version
# Links to Backend: https://auraquant-backend.onrender.com

$BackendURL = "https://auraquant-backend.onrender.com"
$FrontendPath = "D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025\frontend"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "AURAQUANT FRONTEND DEPLOYMENT" -ForegroundColor Cyan
Write-Host "Backend: $BackendURL" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan

# Update production config
Set-Location $FrontendPath

# Create environment file
$envContent = "VITE_API_URL=$BackendURL
REACT_APP_API_URL=$BackendURL
API_URL=$BackendURL"

$envContent | Out-File -FilePath ".env.production" -Encoding UTF8
Write-Host "Updated .env.production" -ForegroundColor Green

# Deploy to Cloudflare
Write-Host "Deploying to Cloudflare Pages..." -ForegroundColor Yellow
npx wrangler pages deploy . --project-name auraquant-frontend --compatibility-date 2025-01-10

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "Frontend: https://auraquant-frontend.pages.dev" -ForegroundColor Blue
Write-Host "Backend: $BackendURL" -ForegroundColor Blue
Write-Host "============================================" -ForegroundColor Cyan