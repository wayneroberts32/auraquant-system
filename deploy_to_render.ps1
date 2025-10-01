# Deploy to Render Script
Write-Host "`n🚀 DEPLOYING AURAQUANT TO RENDER" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow

# Step 1: Create deployment branch without history
Write-Host "`n1️⃣ Creating clean deployment branch..." -ForegroundColor White
git checkout --orphan render-deploy 2>$null
git add -A
git commit -m "Clean deployment for Render - IBKR integrated with $500 AUD paper trading"

# Step 2: Force push to render-deploy branch
Write-Host "`n2️⃣ Pushing to render-deploy branch..." -ForegroundColor White
git push origin render-deploy --force

Write-Host "`n✅ DEPLOYMENT READY!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow

Write-Host "`n📋 NEXT STEPS FOR RENDER:" -ForegroundColor Cyan
Write-Host "1. Go to Render Dashboard" -ForegroundColor White
Write-Host "2. Update your service to use branch: render-deploy" -ForegroundColor White
Write-Host "3. Set these environment variables:" -ForegroundColor White
Write-Host "   IBKR_HOST=<your-tunnel-or-vps-ip>" -ForegroundColor Yellow
Write-Host "   IBKR_PORT=4002" -ForegroundColor Yellow
Write-Host "   IBKR_CLIENT_ID=1" -ForegroundColor Yellow
Write-Host "   MIN_ACCOUNT_BALANCE=500" -ForegroundColor Yellow
Write-Host "   PAPER_TRADING_MODE=true" -ForegroundColor Yellow

Write-Host "`n🌐 FOR CLOUDFLARE PAGES:" -ForegroundColor Cyan
Write-Host "The frontend will auto-deploy from GitHub" -ForegroundColor White
Write-Host "No submodule errors anymore!" -ForegroundColor Green