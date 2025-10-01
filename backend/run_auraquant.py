#!/usr/bin/env python
"""
AuraQuant Trading System - Main Launcher
Complete backend API with status checks
"""

import os
import sys
import uvicorn
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

def print_banner():
    """Print AuraQuant banner"""
    print("\n" + "="*70)
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║     🧠 AURAQUANT QUANTUM BRAIN TRADING SYSTEM 🧠              ║
    ║          Advanced AI-Powered Trading Platform                 ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    print("="*70)

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("\n📦 Checking Dependencies...")
    
    dependencies = {
        "numpy": "NumPy (Mathematical Computing)",
        "pandas": "Pandas (Data Analysis)",
        "fastapi": "FastAPI (Web Framework)",
        "uvicorn": "Uvicorn (ASGI Server)",
        "pymongo": "PyMongo (MongoDB Driver)",
        "motor": "Motor (Async MongoDB)",
        "jose": "Python-JOSE (JWT Tokens)",
        "passlib": "Passlib (Password Hashing)",
        "bs4": "BeautifulSoup4 (HTML Parsing)",
        "yfinance": "yfinance (Market Data)"
    }
    
    all_ok = True
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - Missing")
            all_ok = False
    
    return all_ok

def check_environment():
    """Check environment configuration"""
    print("\n🔧 Environment Configuration...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check MongoDB
    mongodb_uri = os.getenv("MONGODB_URI", "")
    if "localhost" in mongodb_uri:
        print("   ⚠️  MongoDB: Local (may not be running)")
    elif mongodb_uri and "mongodb" in mongodb_uri:
        print("   ✅ MongoDB: Configured")
    else:
        print("   ⚠️  MongoDB: Not configured (using file storage)")
    
    # Check ports
    port = int(os.getenv("API_PORT", 8000))
    print(f"   ✅ API Port: {port}")
    
    # Check admin email
    admin_email = os.getenv("ADMIN_EMAIL", "wayneroberts32@outlook.com.au")
    print(f"   ✅ Admin Email: {admin_email}")
    
    return True

def check_brain_status():
    """Check Quantum Brain status"""
    print("\n🧠 Quantum Brain Status...")
    
    try:
        from brain.quantum_brain_fixed import get_brain
        brain = get_brain()
        print(f"   ✅ Brain Initialized (Generation {brain.generation})")
        print(f"   ✅ Fitness Level: {brain.fitness:.2%}")
        print(f"   ✅ Confidence Threshold: {brain.confidence_threshold:.2%}")
        return True
    except Exception as e:
        print(f"   ⚠️  Brain initialization warning: {e}")
        return False

def main():
    """Main launcher function"""
    print_banner()
    print(f"\n📅 Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Working Directory: {Path.cwd()}")
    
    # Run checks
    deps_ok = check_dependencies()
    env_ok = check_environment()
    brain_ok = check_brain_status()
    
    if not deps_ok:
        print("\n❌ Some dependencies are missing!")
        print("   Run: python setup_backend.py")
        return
    
    print("\n" + "="*70)
    print("🚀 LAUNCHING AURAQUANT API SERVER")
    print("="*70)
    
    print("\n📊 Access Points:")
    print("   🌐 API Root:        http://localhost:8000/")
    print("   📚 Documentation:   http://localhost:8000/docs")
    print("   📈 Redoc:          http://localhost:8000/redoc")
    print("   🏥 Health Check:    http://localhost:8000/health")
    print("   🔍 System Info:     http://localhost:8000/api/system/info")
    
    print("\n💡 API Endpoints:")
    print("   Trading:    /api/trading/*")
    print("   Strategies: /api/strategies/*")
    print("   Market:     /api/market/*")
    print("   Scanner:    /api/scanner/*")
    print("   Auth:       /api/auth/*")
    
    print("\n" + "="*70)
    print("Press CTRL+C to stop the server")
    print("="*70 + "\n")
    
    try:
        # Get port from environment
        port = int(os.getenv("API_PORT", 8000))
        
        # Run the API server
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=port,
            reload=False,  # No auto-reload for stability
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down AuraQuant...")
        print("✅ Server stopped gracefully")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check if port is already in use")
        print("2. Ensure all dependencies are installed")
        print("3. Check firewall settings")

if __name__ == "__main__":
    main()