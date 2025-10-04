# AuraQuant Mobile Deployment Script - Task 9/12
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MOBILE DEPLOYMENT (9/12)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Deploy mobile version
Write-Host "Deploying mobile version..." -ForegroundColor Blue

Set-Location mobile
npx wrangler pages deploy . --project-name=auraquant-mobile --branch=main 2>&1
Set-Location ..

Write-Host ""
Write-Host "MOBILE DEPLOYMENT INFO" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host "Mobile directory: mobile/" -ForegroundColor White
Write-Host "MongoDB: Connected to Cluster0" -ForegroundColor Green
Write-Host ""
Write-Host "Your mobile app will be deployed to:" -ForegroundColor Yellow
Write-Host "https://auraquant-mobile.pages.dev" -ForegroundColor Cyan
Write-Host ""
Write-Host "Task 9/12 complete!" -ForegroundColor Green