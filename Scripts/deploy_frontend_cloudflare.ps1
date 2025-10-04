# AuraQuant Frontend Deployment to Cloudflare
# This script updates frontend to connect to your Render backend
# NO REBUILD - NO RESTYLE - ADD-ONLY

param(
    [string]$BackendURL = ""
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "AURAQUANT FRONTEND DEPLOYMENT TO CLOUDFLARE" -ForegroundColor Cyan
Write-Host "Linking to Backend - NO REBUILD" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Step 1: Get Backend URL
if (-not $BackendURL) {
    Write-Host "`n📍 Enter your Render backend URL" -ForegroundColor Yellow
    Write-Host "Example: https://auraquant-backend.onrender.com" -ForegroundColor Gray
    $BackendURL = Read-Host "Backend URL"
}

if (-not $BackendURL) {
    Write-Host "❌ Backend URL is required!" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Using Backend URL: $BackendURL" -ForegroundColor Green

# Step 2: Create environment configuration for Cloudflare
$frontendPath = "D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025\frontend"

# Create _worker.js for Cloudflare Pages to inject environment variables
$workerContent = @"
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // Inject configuration into HTML
    if (url.pathname.endsWith('.html') || url.pathname === '/') {
      const response = await env.ASSETS.fetch(request);
      const html = await response.text();
      
      // Inject API configuration
      const configScript = `<script>
        // AuraQuant Production Configuration
        window.API_URL = '$BackendURL';
        window.WS_URL = '${BackendURL.Replace('https://', 'wss://').Replace('http://', 'ws://')}';
        window.TRADING_MODE = 'FULL_SYSTEM';
        window.NODE_ENV = 'production';
        window.ENABLE_PAPER_TRADING = true;
        window.ENABLE_LIVE_TRADING = false;
        window.PAPER_BALANCE = 500;
        window.CURRENCY = 'AUD';
        console.log('✅ AuraQuant Backend Connected: $BackendURL');
      </script>`;
      
      const modifiedHtml = html.replace('<head>', '<head>' + configScript);
      
      return new Response(modifiedHtml, {
        headers: response.headers
      });
    }
    
    return env.ASSETS.fetch(request);
  }
};
"@

$workerContent | Out-File -FilePath "$frontendPath\_worker.js" -Encoding UTF8
Write-Host "✅ Created Cloudflare worker configuration" -ForegroundColor Green

# Step 3: Update .env.production
$envContent = @"
VITE_API_URL=$BackendURL
REACT_APP_API_URL=$BackendURL
API_URL=$BackendURL
WS_URL=$($BackendURL.Replace('https://', 'wss://').Replace('http://', 'ws://'))
VITE_MONGODB_URI=mongodb+srv://auraquant:AuraQuant_Infinity@cluster0.qcg7f4h.mongodb.net/
"@

$envContent | Out-File -FilePath "$frontendPath\.env.production" -Encoding UTF8
Write-Host "✅ Updated .env.production" -ForegroundColor Green

# Step 4: Check if wrangler is installed
$wranglerInstalled = Get-Command wrangler -ErrorAction SilentlyContinue

if (-not $wranglerInstalled) {
    Write-Host "`n⚠️  Wrangler CLI not installed" -ForegroundColor Yellow
    Write-Host "Installing wrangler..." -ForegroundColor Yellow
    npm install -g wrangler
}

# Step 5: Deploy to Cloudflare Pages
Write-Host "`n🚀 Deploying to Cloudflare Pages..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor White

Set-Location $frontendPath

# Deploy using wrangler
Write-Host "Deploying frontend to Cloudflare..." -ForegroundColor Yellow
npx wrangler pages deploy . --project-name auraquant-frontend --compatibility-date 2025-01-10

# Return to original directory
Set-Location "D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025"

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "✅ FRONTEND DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Frontend URL: https://auraquant-frontend.pages.dev" -ForegroundColor Blue
Write-Host "Backend URL: $BackendURL" -ForegroundColor Blue
Write-Host "`nThe frontend is now connected to your backend!" -ForegroundColor Green
Write-Host "Test the connection by visiting your frontend URL" -ForegroundColor Yellow