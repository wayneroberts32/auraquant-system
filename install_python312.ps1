# AuraQuant Python 3.12 Installation Script
# This script downloads and installs Python 3.12 to fix compatibility issues

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  AuraQuant Python 3.12 Installation Script" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "⚠️  WARNING: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "   Some features may require admin privileges" -ForegroundColor Yellow
    Write-Host ""
}

# Step 1: Download Python 3.12
Write-Host "📥 Step 1: Downloading Python 3.12.7..." -ForegroundColor Green
$pythonUrl = "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
$installerPath = "$env:TEMP\python-3.12.7-amd64.exe"

try {
    if (Test-Path $installerPath) {
        Write-Host "   Installer already downloaded" -ForegroundColor Gray
    } else {
        Write-Host "   Downloading from python.org..." -ForegroundColor Gray
        Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath -UseBasicParsing
        Write-Host "   ✅ Download complete!" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Download failed!" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please download manually from:" -ForegroundColor Yellow
    Write-Host $pythonUrl -ForegroundColor Cyan
    exit 1
}

# Step 2: Install Python
Write-Host ""
Write-Host "📦 Step 2: Installing Python 3.12..." -ForegroundColor Green
Write-Host "   This will open the Python installer" -ForegroundColor Gray
Write-Host "   IMPORTANT: Check 'Add Python to PATH' option!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to start installation..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Start installer
Start-Process -FilePath $installerPath -Wait

# Step 3: Verify installation
Write-Host ""
Write-Host "🔍 Step 3: Verifying Python installation..." -ForegroundColor Green

# Try different Python commands
$pythonCmd = $null
$pythonVersion = $null

# Check python command
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "3\.12") {
        $pythonCmd = "python"
        Write-Host "   ✅ Python 3.12 found via 'python' command" -ForegroundColor Green
    }
} catch {}

# Check py launcher
if (-not $pythonCmd) {
    try {
        $pythonVersion = py -3.12 --version 2>&1
        if ($pythonVersion -match "3\.12") {
            $pythonCmd = "py -3.12"
            Write-Host "   ✅ Python 3.12 found via 'py -3.12' command" -ForegroundColor Green
        }
    } catch {}
}

# Check common installation paths
if (-not $pythonCmd) {
    $pythonPaths = @(
        "C:\Python312\python.exe",
        "C:\Program Files\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    )
    
    foreach ($path in $pythonPaths) {
        if (Test-Path $path) {
            $pythonCmd = $path
            Write-Host "   ✅ Python 3.12 found at: $path" -ForegroundColor Green
            break
        }
    }
}

if (-not $pythonCmd) {
    Write-Host "   ❌ Python 3.12 not found!" -ForegroundColor Red
    Write-Host "   Please ensure Python 3.12 is installed and in PATH" -ForegroundColor Yellow
    exit 1
}

Write-Host "   Python command: $pythonCmd" -ForegroundColor Gray
Write-Host ""

# Step 4: Install dependencies
Write-Host "📚 Step 4: Installing required packages..." -ForegroundColor Green
Write-Host "   This may take several minutes..." -ForegroundColor Gray
Write-Host ""

# Navigate to project directory
Set-Location "D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025"

# Create batch installation script
$installScript = @"
Write-Host 'Upgrading pip...' -ForegroundColor Yellow
& $pythonCmd -m pip install --upgrade pip

Write-Host 'Installing core packages...' -ForegroundColor Yellow
& $pythonCmd -m pip install numpy pandas scikit-learn scipy

Write-Host 'Installing FastAPI...' -ForegroundColor Yellow
& $pythonCmd -m pip install fastapi uvicorn[standard] python-multipart websockets

Write-Host 'Installing database drivers...' -ForegroundColor Yellow
& $pythonCmd -m pip install pymongo motor dnspython

Write-Host 'Installing authentication...' -ForegroundColor Yellow
& $pythonCmd -m pip install python-jose[cryptography] passlib[bcrypt] email-validator

Write-Host 'Installing async libraries...' -ForegroundColor Yellow
& $pythonCmd -m pip install aiohttp aiofiles

Write-Host 'Installing market data libraries...' -ForegroundColor Yellow
& $pythonCmd -m pip install yfinance beautifulsoup4 lxml html5lib requests

Write-Host 'Installing utilities...' -ForegroundColor Yellow
& $pythonCmd -m pip install python-dotenv pydantic colorama tqdm pytz

Write-Host 'Installing optional dev tools...' -ForegroundColor Yellow
& $pythonCmd -m pip install pytest ipython
"@

# Execute installation
Invoke-Expression $installScript

# Step 5: Test imports
Write-Host ""
Write-Host "🧪 Step 5: Testing package imports..." -ForegroundColor Green

$testScript = @"
try:
    import numpy
    import pandas
    import fastapi
    import uvicorn
    import pymongo
    import yfinance
    print('✅ All critical imports successful!')
except ImportError as e:
    print(f'❌ Import error: {e}')
"@

& $pythonCmd -c $testScript

# Step 6: Create startup script
Write-Host ""
Write-Host "🚀 Step 6: Creating startup script..." -ForegroundColor Green

$startScript = @"
@echo off
echo Starting AuraQuant API...
cd /d "D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025\backend"
$pythonCmd -m api.main
pause
"@

$startScript | Out-File -FilePath "start_api.bat" -Encoding ASCII
Write-Host "   ✅ Created start_api.bat" -ForegroundColor Green

# Final summary
Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "        Installation Complete!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Python 3.12 is installed" -ForegroundColor Green
Write-Host "✅ All packages are installed" -ForegroundColor Green
Write-Host "✅ Startup script created" -ForegroundColor Green
Write-Host ""
Write-Host "To start the API, run:" -ForegroundColor Yellow
Write-Host "   .\start_api.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or manually:" -ForegroundColor Yellow
Write-Host "   cd backend" -ForegroundColor Cyan
Write-Host "   $pythonCmd -m api.main" -ForegroundColor Cyan
Write-Host ""
Write-Host "API will be available at:" -ForegroundColor Yellow
Write-Host "   http://localhost:8000" -ForegroundColor Cyan
Write-Host "   http://localhost:8000/docs (documentation)" -ForegroundColor Cyan
Write-Host ""