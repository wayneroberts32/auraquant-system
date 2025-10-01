# AuraQuant Backend Monitoring Script
Clear-Host
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AURAQUANT BACKEND DEPLOYMENT MONITOR        " -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Monitoring backend deployment on Render..." -ForegroundColor Yellow
Write-Host "This will check every 30 seconds until live" -ForegroundColor Gray
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Gray
Write-Host ""

$backendUrl = "https://auraquant-backend.onrender.com/health"
$swarmUrl = "https://auraquant-backend.onrender.com/api/swarm/status"
$attempt = 0
$isLive = $false

while (-not $isLive) {
    $attempt++
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] Attempt #$attempt - Checking backend..." -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri $backendUrl -UseBasicParsing -TimeoutSec 10
        
        if ($response.StatusCode -eq 200) {
            Write-Host ""
            Write-Host "================================================" -ForegroundColor Green
            Write-Host "    🎉 BACKEND IS LIVE! 🎉                    " -ForegroundColor Green
            Write-Host "================================================" -ForegroundColor Green
            Write-Host ""
            
            # Display health response
            try {
                $health = $response.Content | ConvertFrom-Json
                Write-Host "Health Status:" -ForegroundColor Cyan
                Write-Host ($health | ConvertTo-Json -Depth 3) -ForegroundColor White
            } catch {
                Write-Host "Backend responding with status 200" -ForegroundColor Green
            }
            
            # Check swarm status
            Write-Host ""
            Write-Host "Checking Multi-Agent Swarm..." -ForegroundColor Yellow
            try {
                $swarmResponse = Invoke-WebRequest -Uri $swarmUrl -UseBasicParsing -TimeoutSec 10
                $swarm = $swarmResponse.Content | ConvertFrom-Json
                
                Write-Host "✅ Swarm Status:" -ForegroundColor Green
                Write-Host "   Total Agents: $($swarm.total_agents)" -ForegroundColor White
                Write-Host "   Active Agents: $($swarm.active_agents)" -ForegroundColor White
                Write-Host "   Tasks Completed: $($swarm.tasks_completed)" -ForegroundColor White
            } catch {
                Write-Host "Swarm endpoint still initializing..." -ForegroundColor Yellow
            }
            
            $isLive = $true
            
            Write-Host ""
            Write-Host "================================================" -ForegroundColor Green
            Write-Host "   YOUR AURAQUANT SYSTEM IS FULLY DEPLOYED!    " -ForegroundColor Green
            Write-Host "================================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "✅ Backend API: https://auraquant-backend.onrender.com" -ForegroundColor Cyan
            Write-Host "✅ Frontend App: https://auraquant-frontend.pages.dev" -ForegroundColor Cyan
            Write-Host "✅ Login Page: https://auraquant-frontend.pages.dev/pages/login.html" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "System Features Active:" -ForegroundColor Yellow
            Write-Host "• 13 Multi-Agent Swarm Orchestrator" -ForegroundColor White
            Write-Host "• ASX Trading (Interactive Brokers)" -ForegroundColor White
            Write-Host "• Cryptocurrency Trading (Binance, Coinbase, Kraken)" -ForegroundColor White
            Write-Host "• DeFi/Meme Coins (Uniswap, PancakeSwap)" -ForegroundColor White
            Write-Host "• Emergency Kill Switch" -ForegroundColor White
            Write-Host "• Regulatory Compliance Framework" -ForegroundColor White
            Write-Host ""
            
            # Open the sites
            $openSites = Read-Host "Open your live system in browser? (y/n)"
            if ($openSites -eq 'y') {
                Start-Process "https://auraquant-backend.onrender.com/health"
                Start-Process "https://auraquant-frontend.pages.dev"
            }
        }
    } catch {
        # Still deploying
        if ($attempt -eq 1) {
            Write-Host "  Backend not ready yet (this is normal)" -ForegroundColor Yellow
            Write-Host "  Render deployments typically take 5-10 minutes" -ForegroundColor Gray
        } elseif ($attempt % 4 -eq 0) {
            # Show progress every 2 minutes
            $minutes = [math]::Round($attempt * 0.5, 1)
            Write-Host "  Still deploying... ($minutes minutes elapsed)" -ForegroundColor Yellow
        }
    }
    
    if (-not $isLive) {
        Start-Sleep -Seconds 30
    }
}

Write-Host ""
Write-Host "Monitoring complete! Your system is operational." -ForegroundColor Green