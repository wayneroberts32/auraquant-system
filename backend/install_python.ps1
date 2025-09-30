# PowerShell script to download and install Python 3.12
# Run this script as Administrator for best results

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "    Python 3.12 Installation Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Python 3.12.7 is the latest stable version as of late 2024
$pythonVersion = "3.12.7"
$pythonInstaller = "python-$pythonVersion-amd64.exe"
$downloadUrl = "https://www.python.org/ftp/python/$pythonVersion/$pythonInstaller"
$installerPath = "$env:TEMP\$pythonInstaller"

Write-Host "📥 Downloading Python $pythonVersion..." -ForegroundColor Yellow
Write-Host "   URL: $downloadUrl"
Write-Host "   Destination: $installerPath"
Write-Host ""

try {
    # Download Python installer
    Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "✅ Download complete!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to download Python installer" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Download manually from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "🔧 Installing Python $pythonVersion..." -ForegroundColor Yellow
Write-Host "   Installation options:" -ForegroundColor Gray
Write-Host "   - Add Python to PATH" -ForegroundColor Gray
Write-Host "   - Install pip" -ForegroundColor Gray
Write-Host "   - Install for all users" -ForegroundColor Gray
Write-Host ""

# Install Python with options
# /quiet - Silent install
# InstallAllUsers=1 - Install for all users
# PrependPath=1 - Add to PATH
# Include_pip=1 - Install pip
# Include_test=0 - Don't install test suite
$installArgs = @(
    "/quiet",
    "InstallAllUsers=1",
    "PrependPath=1",
    "Include_pip=1",
    "Include_test=0",
    "Include_doc=0",
    "Include_dev=1",
    "Include_launcher=1",
    "InstallLauncherAllUsers=1"
)

try {
    Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -NoNewWindow
    Write-Host "✅ Python installation complete!" -ForegroundColor Green
} catch {
    Write-Host "❌ Installation failed" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Try running the installer manually: $installerPath" -ForegroundColor Yellow
    exit 1
}

# Clean up installer
Remove-Item $installerPath -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "🔍 Verifying installation..." -ForegroundColor Yellow

# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Check if Python is installed
try {
    $pythonPath = (Get-Command python -ErrorAction Stop).Source
    $pythonVersion = & python --version 2>&1
    Write-Host "✅ Python found at: $pythonPath" -ForegroundColor Green
    Write-Host "   Version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Python not found in PATH" -ForegroundColor Yellow
    Write-Host "   You may need to restart your terminal or computer" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "        Installation Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Close and reopen your terminal" -ForegroundColor White
Write-Host "2. Verify with: python --version" -ForegroundColor White
Write-Host "3. Install packages: pip install -r requirements.txt" -ForegroundColor White