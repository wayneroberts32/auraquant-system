@echo off
REM ============================================================
REM AuraQuant Complete Installation Script
REM Installs all dependencies for the Quantum Brain System
REM Professor's Engineering Setup
REM ============================================================

echo.
echo ====================================================================
echo        AuraQuant Quantum Brain - Complete Installation
echo               Professor's Engineering Setup Script
echo ====================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python first:
    echo 1. Download from: https://www.python.org/downloads/
    echo 2. Make sure to check "Add Python to PATH"
    echo 3. Run this script again
    pause
    exit /b 1
)

echo [✓] Python is installed
python --version
echo.

REM Upgrade pip
echo [1/7] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install core dependencies
echo [2/7] Installing core dependencies...
python -m pip install numpy pandas scikit-learn python-dateutil pytz colorama tqdm ipython

REM Install deep learning frameworks
echo.
echo [3/7] Installing deep learning frameworks...
echo Note: This may take several minutes...

REM Install TensorFlow
python -m pip install tensorflow

REM Install PyTorch (CPU version for compatibility)
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

REM Install Keras (if not included with TensorFlow)
python -m pip install keras

REM Install MongoDB drivers
echo.
echo [4/7] Installing MongoDB drivers...
python -m pip install pymongo motor dnspython

REM Install technical analysis libraries
echo.
echo [5/7] Installing technical analysis libraries...
python -m pip install yfinance beautifulsoup4 requests aiohttp aiofiles

REM Try to install TA-Lib (may fail on Windows without build tools)
echo.
echo Attempting to install TA-Lib (may require additional setup)...
python -m pip install TA-Lib 2>nul || (
    echo.
    echo [WARNING] TA-Lib installation failed.
    echo To install TA-Lib on Windows:
    echo 1. Download the appropriate .whl file from:
    echo    https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
    echo 2. Install using: pip install TA_Lib-0.4.24-cpXX-cpXX-win_amd64.whl
    echo    where XX matches your Python version
    echo.
)

REM Install web and API frameworks
echo.
echo [6/7] Installing web frameworks...
python -m pip install fastapi uvicorn websockets python-dotenv pydantic

REM Install visualization libraries (optional)
echo.
echo [7/7] Installing visualization libraries...
python -m pip install matplotlib plotly

REM Install testing frameworks
python -m pip install pytest pytest-asyncio

REM Install development tools
python -m pip install black pylint

echo.
echo ====================================================================
echo                    Installation Summary
echo ====================================================================
echo.

REM Create requirements verification script
echo import sys > check_requirements.py
echo print("Checking installed packages...") >> check_requirements.py
echo print() >> check_requirements.py
echo packages = { >> check_requirements.py
echo     'numpy': 'Core computations', >> check_requirements.py
echo     'pandas': 'Data manipulation', >> check_requirements.py
echo     'sklearn': 'Machine learning', >> check_requirements.py
echo     'tensorflow': 'Deep learning', >> check_requirements.py
echo     'torch': 'PyTorch neural networks', >> check_requirements.py
echo     'pymongo': 'MongoDB driver', >> check_requirements.py
echo     'motor': 'Async MongoDB', >> check_requirements.py
echo     'yfinance': 'Market data', >> check_requirements.py
echo     'bs4': 'Web scraping', >> check_requirements.py
echo     'fastapi': 'API framework', >> check_requirements.py
echo     'uvicorn': 'ASGI server', >> check_requirements.py
echo } >> check_requirements.py
echo. >> check_requirements.py
echo for package, description in packages.items(): >> check_requirements.py
echo     try: >> check_requirements.py
echo         __import__(package) >> check_requirements.py
echo         print(f"✓ {package:15} - {description}") >> check_requirements.py
echo     except ImportError: >> check_requirements.py
echo         print(f"✗ {package:15} - {description} [NOT INSTALLED]") >> check_requirements.py

python check_requirements.py
del check_requirements.py

echo.
echo ====================================================================
echo                    MongoDB Setup Instructions
echo ====================================================================
echo.
echo For Local MongoDB:
echo 1. Download MongoDB Community Server:
echo    https://www.mongodb.com/try/download/community
echo.
echo 2. Install and start MongoDB service:
echo    - Windows: Run as service or use "mongod" command
echo    - Default connection: mongodb://localhost:27017/
echo.
echo For Cloud MongoDB (Recommended for Production):
echo 1. Create free account at: https://cloud.mongodb.com
echo 2. Create a free M0 cluster
echo 3. Get your connection string from "Connect" button
echo 4. Add your IP address to whitelist
echo.
echo ====================================================================
echo                    Next Steps
echo ====================================================================
echo.
echo 1. Test the brain system:
echo    cd backend\brain
echo    python test_scanner_demo.py
echo.
echo 2. Run the dashboard scanner:
echo    python dashboard_scanner.py
echo.
echo 3. When ready to deploy to cloud:
echo    python migrate_to_cloud.py
echo.
echo ====================================================================
echo.
echo Installation complete! Press any key to exit...
pause >nul