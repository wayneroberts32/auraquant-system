# AuraQuant Deployment Verification Script
Clear-Host
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AURAQUANT DEPLOYMENT VERIFICATION           " -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Function to test endpoint
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$MaxRetries = 3
    )
    
    Write-Host "Testing $Name..." -ForegroundColor Yellow
    $attempt = 0
    $success = $false
    
    while ($attempt -lt $MaxRetries -and -not $success) {
        $attempt++
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ $Name is ONLINE!" -ForegroundColor Green
                $success = $true
                
                # Try to parse and display JSON response
                try {
                    $content = $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
                    Write-Host "Response:" -ForegroundColor Cyan
                    Write-Host $content -ForegroundColor Gray
                } catch {
                    # If not JSON, just show status
                }
            }
        } catch {
            if ($attempt -lt $MaxRetries) {
                Write-Host "  Attempt $attempt failed, retrying..." -ForegroundColor Gray
                Start-Sleep -Seconds 5
            } else {
                Write-Host "❌ $Name is not responding (may still be deploying)" -ForegroundColor Red
                Write-Host "  URL: $Url" -ForegroundColor Gray
            }
        }
    }
    Write-Host ""
    return $success
}

# Test Backend Health
Write-Host "STEP 1: Backend Health Check" -ForegroundColor Yellow
Write-Host "=============================" -ForegroundColor Gray
$backendHealth = Test-Endpoint -Name "Backend Health" -Url "https://auraquant-backend.onrender.com/health"

# Test API Status
if ($backendHealth) {
    Write-Host "STEP 2: API Status Check" -ForegroundColor Yellow
    Write-Host "========================" -ForegroundColor Gray
    Test-Endpoint -Name "API Status" -Url "https://auraquant-backend.onrender.com/api/status"
}

# Test Swarm Status
if ($backendHealth) {
    Write-Host "STEP 3: Multi-Agent Swarm Check" -ForegroundColor Yellow
    Write-Host "================================" -ForegroundColor Gray
    Test-Endpoint -Name "Swarm Status" -Url "https://auraquant-backend.onrender.com/api/swarm/status"
}

# Test Markets
if ($backendHealth) {
    Write-Host "STEP 4: Markets Check" -ForegroundColor Yellow
    Write-Host "=====================" -ForegroundColor Gray
    Test-Endpoint -Name "Markets API" -Url "https://auraquant-backend.onrender.com/api/markets"
}

# Test Frontend
Write-Host "STEP 5: Frontend Check" -ForegroundColor Yellow
Write-Host "======================" -ForegroundColor Gray
$frontendSuccess = Test-Endpoint -Name "Frontend App" -Url "https://auraquant-frontend.pages.dev" -MaxRetries 2

# Summary
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "           VERIFICATION SUMMARY                 " -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$results = @()
if ($backendHealth) {
    $results += "✅ Backend API is running"
    $results += "✅ Health endpoint responding"
} else {
    $results += "⏳ Backend still deploying (5-10 minutes typical)"
}

if ($frontendSuccess) {
    $results += "✅ Frontend is deployed"
} else {
    $results += "⏳ Frontend still building (3-5 minutes typical)"
}

foreach ($result in $results) {
    if ($result -like "*✅*") {
        Write-Host $result -ForegroundColor Green
    } else {
        Write-Host $result -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Your URLs:" -ForegroundColor Cyan
Write-Host "Backend: https://auraquant-backend.onrender.com" -ForegroundColor White
Write-Host "Frontend: https://auraquant-frontend.pages.dev" -ForegroundColor White
Write-Host "Login Page: https://auraquant-frontend.pages.dev/pages/login.html" -ForegroundColor White
Write-Host ""

# Open browsers
$openBrowsers = Read-Host "Open the live sites in browser? (y/n)"
if ($openBrowsers -eq 'y') {
    if ($backendHealth) {
        Start-Process "https://auraquant-backend.onrender.com/health"
    }
    if ($frontendSuccess) {
        Start-Process "https://auraquant-frontend.pages.dev"
    }
    Start-Process "https://dashboard.render.com"
    Start-Process "https://dash.cloudflare.com"
}

Write-Host ""
Write-Host "Monitor deployment progress at:" -ForegroundColor Yellow
Write-Host "Render: https://dashboard.render.com" -ForegroundColor White
Write-Host "Cloudflare: https://dash.cloudflare.com" -ForegroundColor White
Write-Host ""
Write-Host "Verification complete!" -ForegroundColor Green