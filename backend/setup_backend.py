#!/usr/bin/env python
"""
AuraQuant Backend Setup Script
Verifies Python installation and installs required packages
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Check if we're running Python 3.12"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    print(f"Python executable: {sys.executable}")
    
    if version.major == 3 and version.minor == 12:
        print("✅ Python 3.12 detected!")
        return True
    elif version.major == 3 and version.minor == 13:
        print("⚠️  Python 3.13 detected (you're still using the wrong version)")
        print("   Please complete Python 3.12 installation and run this script with:")
        print("   C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe setup_backend.py")
        return False
    else:
        print(f"⚠️  Python {version.major}.{version.minor} detected")
        print("   Python 3.12 is recommended")
        return False

def upgrade_pip():
    """Upgrade pip to latest version"""
    print("\n📦 Upgrading pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        print("✅ pip upgraded successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to upgrade pip: {e}")
        return False

def install_packages():
    """Install required packages for AuraQuant backend"""
    packages = [
        "fastapi",
        "uvicorn[standard]",
        "pymongo",
        "motor",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "python-dotenv",
        "bcrypt",
        "httpx",  # For testing
        "pytest",  # For testing
        "pytest-asyncio"  # For async testing
    ]
    
    print("\n📦 Installing required packages...")
    print(f"   Packages to install: {', '.join(packages)}")
    
    failed = []
    for package in packages:
        print(f"\n   Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"   ✅ {package} installed")
        except subprocess.CalledProcessError:
            print(f"   ❌ Failed to install {package}")
            failed.append(package)
    
    if failed:
        print(f"\n⚠️  Some packages failed to install: {', '.join(failed)}")
        print("   You can try installing them manually later")
    else:
        print("\n✅ All packages installed successfully!")
    
    return len(failed) == 0

def test_imports():
    """Test if key imports work"""
    print("\n🧪 Testing imports...")
    
    test_modules = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn", 
        "pymongo": "PyMongo (MongoDB)",
        "motor": "Motor (Async MongoDB)",
        "jose": "Python-JOSE (JWT)",
        "passlib": "Passlib (Password hashing)",
        "dotenv": "Python-dotenv"
    }
    
    all_good = True
    for module, name in test_modules.items():
        try:
            __import__(module)
            print(f"   ✅ {name} imported successfully")
        except ImportError:
            print(f"   ❌ {name} not available")
            all_good = False
    
    return all_good

def create_run_script():
    """Create a simple run script"""
    run_script = """@echo off
echo Starting AuraQuant Backend API...
cd /d "D:\\New AuraQuant\\New_Synthetic_System_AuraQuant_Backup_2025\\backend"
python api\\main.py
pause
"""
    
    script_path = Path("run_api.bat")
    script_path.write_text(run_script)
    print(f"\n✅ Created run_api.bat script")
    print(f"   You can start the API by double-clicking: {script_path.absolute()}")

def main():
    print("=" * 60)
    print("    AURAQUANT BACKEND SETUP")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        print("\n⚠️  Please install Python 3.12 first!")
        return
    
    # Upgrade pip
    upgrade_pip()
    
    # Install packages
    packages_ok = install_packages()
    
    # Test imports
    imports_ok = test_imports()
    
    # Create run script
    create_run_script()
    
    # Final summary
    print("\n" + "=" * 60)
    print("    SETUP COMPLETE")
    print("=" * 60)
    
    if packages_ok and imports_ok:
        print("\n✅ Everything is ready!")
        print("\n📚 Next steps:")
        print("1. Update .env file with your MongoDB connection string")
        print("2. Run the API: python api/main.py")
        print("3. Access API docs: http://localhost:8000/docs")
    else:
        print("\n⚠️  Some components need attention")
        print("   Check the output above for details")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()