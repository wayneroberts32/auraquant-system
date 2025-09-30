# Python 3.12 Installation & Migration Guide
**Date:** 2025-09-30  
**Engineer:** Professor's AI Software Engineer  
**Purpose:** Install Python 3.12 to fix compatibility issues

---

## 🔴 CURRENT ISSUE
You have Python 3.13t (free-threaded experimental build) which causes:
- ❌ CFFI doesn't support it
- ❌ yfinance won't install
- ❌ lxml won't build
- ❌ NumPy has import issues

## ✅ SOLUTION: Install Python 3.12

---

## 📥 STEP 1: Download Python 3.12

### Option A: Direct Download Link
Visit: https://www.python.org/downloads/release/python-3127/

**Download:** Windows installer (64-bit)
- File: `python-3.12.7-amd64.exe`

### Option B: Use PowerShell
```powershell
# Download Python 3.12.7 installer
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe" -OutFile "$env:USERPROFILE\Downloads\python-3.12.7-amd64.exe"
```

---

## 📦 STEP 2: Install Python 3.12

### Installation Steps:
1. Run the installer
2. ✅ CHECK "Add Python 3.12 to PATH" (IMPORTANT!)
3. Click "Customize installation"
4. Keep all options checked
5. Advanced Options:
   - ✅ Install for all users (optional)
   - ✅ Add Python to environment variables
   - ✅ Precompile standard library
6. Install location: `C:\Python312` (or default)
7. Click Install

### Verify Installation:
```powershell
# Check Python version
python --version
# Should show: Python 3.12.7

# Check pip
python -m pip --version
```

---

## 🔧 STEP 3: Install All Dependencies

### Run this PowerShell script:
```powershell
# Navigate to project
cd "D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025"

# Upgrade pip
python -m pip install --upgrade pip

# Install core dependencies
python -m pip install numpy pandas scikit-learn scipy

# Install web framework
python -m pip install fastapi uvicorn[standard] python-multipart websockets

# Install database
python -m pip install pymongo motor dnspython

# Install authentication
python -m pip install python-jose[cryptography] passlib[bcrypt] email-validator

# Install async
python -m pip install aiohttp aiofiles asyncio

# Install market data
python -m pip install yfinance beautifulsoup4 lxml html5lib requests

# Install utilities
python -m pip install python-dotenv pydantic colorama tqdm pytz

# Optional: Install development tools
python -m pip install pytest pytest-asyncio black pylint ipython
```

---

## 🎯 STEP 4: Test the Installation

### Test script:
```powershell
# Test imports
python -c "import numpy; import pandas; import fastapi; import yfinance; print('✅ All imports successful!')"
```

---

## 🚀 STEP 5: Run the API

```powershell
# Navigate to backend
cd "D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025\backend"

# Run the main API
python -m api.main
```

---

## 📝 TROUBLESHOOTING

### If "python" command not found:
```powershell
# Use py launcher
py -3.12 --version

# Or use full path
C:\Python312\python.exe --version
```

### If multiple Python versions:
```powershell
# List all Python versions
py -0

# Use specific version
py -3.12 -m pip install -r requirements.txt
```

### PATH Issues:
Add to System PATH:
1. Win + X → System → Advanced system settings
2. Environment Variables
3. System variables → Path → Edit
4. Add: `C:\Python312\` and `C:\Python312\Scripts\`
5. OK → OK → OK
6. Restart PowerShell

---

## ✅ EXPECTED OUTCOME

After installation, you should have:
- Python 3.12.7 (standard version, not experimental)
- All packages installed successfully
- API running without errors
- Full Quantum Brain integration working

---

## 🔄 MIGRATION COMPLETE CHECKLIST

- [ ] Python 3.12 downloaded
- [ ] Python 3.12 installed
- [ ] PATH configured
- [ ] pip upgraded
- [ ] All dependencies installed
- [ ] Test imports successful
- [ ] API starts without errors
- [ ] Documentation accessible at http://localhost:8000/docs

---

**Next: Run the installation script to fix everything!**