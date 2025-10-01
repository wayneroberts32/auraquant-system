# Python 3.12 Setup Guide for AuraQuant

## Current Status
- ❌ Python 3.13t (free-threaded) is installed but incompatible with our requirements
- ⏳ Python 3.12 installer downloaded to: `C:\Users\User\AppData\Local\Temp\python-3.12.7-amd64.exe`

## Installation Steps

### Option 1: Run the Downloaded Installer
1. **Open the installer** (should be running or in your temp folder)
   ```powershell
   Start-Process "$env:TEMP\python-3.12.7-amd64.exe"
   ```

2. **IMPORTANT: Check these options:**
   - ✅ **"Add python.exe to PATH"** (at the bottom of first screen)
   - ✅ Click "Customize installation"
   - ✅ Ensure "pip" is checked
   - ✅ Ensure "py launcher" is checked
   - ✅ Click "Next"
   - ✅ Check "Install Python 3.12 for all users" (optional)
   - ✅ Click "Install"

3. **Wait for completion** and click "Close"

### Option 2: Download Fresh Installer
If the above doesn't work:
1. Go to: https://www.python.org/downloads/release/python-3127/
2. Download: **Windows installer (64-bit)**
3. Run and follow steps above

## After Installation

### 1. Verify Installation
Close your current terminal and open a new one, then run:
```powershell
python --version
```
Should show: `Python 3.12.7`

### 2. Install Required Packages
```powershell
cd "D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025\backend"
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn pymongo motor python-jose passlib python-multipart python-dotenv bcrypt
```

### 3. Test the API
```powershell
cd "D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025\backend"
python start_api.py
```

## Removing Python 3.13t (Optional)

If you want to remove Python 3.13t completely:

1. **Via Settings:**
   - Open Windows Settings
   - Go to Apps → Apps & features
   - Search for "Python 3.13"
   - Click it and select "Uninstall"

2. **Remove from PATH:**
   ```powershell
   # This will remove Python 3.13 from your user PATH
   $path = [Environment]::GetEnvironmentVariable("Path", "User")
   $newPath = $path -replace "C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python313[^;]*;?", ""
   [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
   ```

## Quick Test Script

Save this as `test_python.py` and run it:
```python
import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Test if we can import required modules
try:
    import fastapi
    print("✅ FastAPI is installed")
except ImportError:
    print("❌ FastAPI not installed - run: pip install fastapi")

try:
    import uvicorn
    print("✅ Uvicorn is installed")
except ImportError:
    print("❌ Uvicorn not installed - run: pip install uvicorn")
```

## Troubleshooting

### "Python not found" error
- Make sure you checked "Add python.exe to PATH" during installation
- Restart your terminal
- Try using full path: `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`

### Package installation fails
```powershell
# Use python -m pip instead of just pip
python -m pip install packagename

# Or use the full path
C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe -m pip install packagename
```

### Port 8000 already in use
```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Change port in .env file
API_PORT=8080
```

## Next Steps

Once Python 3.12 is properly installed:

1. **Install all dependencies**
2. **Start the API server**
3. **Access the API at:** http://localhost:8000/docs
4. **Connect your MongoDB Atlas** (update .env with your connection string)
5. **Update frontend** to use the new API endpoints

---

Need help? The installer is already downloaded and ready to run!