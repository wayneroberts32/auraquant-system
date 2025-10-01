# Simple Python 3.12 Installation Script

Write-Host "Installing Python 3.12..." -ForegroundColor Cyan

$pythonVersion = "3.12.7"
$pythonInstaller = "python-$pythonVersion-amd64.exe"
$downloadUrl = "https://www.python.org/ftp/python/$pythonVersion/$pythonInstaller"
$installerPath = "$env:TEMP\$pythonInstaller"

Write-Host "Downloading from: $downloadUrl"

# Download Python installer
Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing

Write-Host "Download complete. Installing..."

# Install Python with basic options
$installArgs = "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_pip=1"
Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -NoNewWindow

Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "Please restart your terminal to use Python" -ForegroundColor Yellow