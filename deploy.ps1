# Deploy script for AuraQuant Frontend to Cloudflare Pages
Write-Host "Deploying AuraQuant Frontend to Cloudflare Pages..." -ForegroundColor Cyan

# Ensure we're deploying to the correct project
$projectName = "auraquant-frontend"

Write-Host "Deploying to project: $projectName" -ForegroundColor Yellow

# Run the deployment
npx wrangler pages deploy ./ --project-name=$projectName

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
    Write-Host "Your site will be available at:" -ForegroundColor Green
    Write-Host "  - https://auraquant-frontend.pages.dev" -ForegroundColor White
    Write-Host "  - https://ai-auraquant.com (once DNS propagates)" -ForegroundColor White
} else {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
}
