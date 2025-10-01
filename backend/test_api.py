#!/usr/bin/env python3
"""
Test script for AuraQuant Backend API
Tests the API locally without needing full deployment
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent))

# Test imports
def test_imports():
    """Test that all required modules can be imported"""
    print("=" * 60)
    print("TESTING IMPORTS")
    print("=" * 60)
    
    results = []
    
    # Test config
    try:
        from config.database import sync_db, async_db
        results.append("✅ Database config imported")
    except Exception as e:
        results.append(f"❌ Database config: {e}")
    
    # Test Quantum Brain
    try:
        from brain.quantum_brain_fixed import QuantumBrain, get_brain
        results.append("✅ Quantum Brain (fixed) imported")
    except Exception as e:
        results.append(f"❌ Quantum Brain: {e}")
    
    # Test API modules
    try:
        from api.routes import trading, strategies, market_data, auth, scanner
        results.append("✅ API routes imported")
    except Exception as e:
        results.append(f"❌ API routes: {e}")
    
    # Test FastAPI
    try:
        from api.main import app
        results.append("✅ FastAPI app imported")
    except Exception as e:
        results.append(f"❌ FastAPI app: {e}")
    
    for result in results:
        print(f"  {result}")
    
    return all("✅" in r for r in results)

async def test_quantum_brain():
    """Test Quantum Brain functionality"""
    print("\n" + "=" * 60)
    print("TESTING QUANTUM BRAIN")
    print("=" * 60)
    
    try:
        from brain.quantum_brain_fixed import get_brain
        
        # Initialize brain
        brain = get_brain()
        print(f"✅ Brain initialized (Generation {brain.generation})")
        
        # Test market analysis
        analysis = await brain.analyze_market("AAPL")
        print(f"✅ Market analysis: {analysis['symbol']} - {analysis['recommendation']}")
        
        # Test recommendations
        recs = await brain.get_trading_recommendations(["AAPL", "GOOGL", "MSFT"])
        print(f"✅ Got {len(recs)} recommendations")
        
        # Save state
        await brain.save_state()
        print("✅ State saved")
        
        return True
        
    except Exception as e:
        print(f"❌ Brain test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_endpoints():
    """Test API endpoints locally"""
    print("\n" + "=" * 60)
    print("TESTING API ENDPOINTS")
    print("=" * 60)
    
    try:
        from fastapi.testclient import TestClient
        from api.main import app
        
        client = TestClient(app)
        
        # Test root endpoint
        response = client.get("/")
        print(f"✅ Root endpoint: {response.status_code}")
        
        # Test health endpoint
        response = client.get("/health")
        print(f"✅ Health endpoint: {response.status_code}")
        data = response.json()
        print(f"   Brain: {data.get('quantum_brain', False)}")
        
        # Test system info
        response = client.get("/api/system/info")
        print(f"✅ System info: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_environment():
    """Test environment setup"""
    print("=" * 60)
    print("TESTING ENVIRONMENT")
    print("=" * 60)
    
    # Check Python version
    print(f"  Python: {sys.version}")
    
    # Check environment variables
    env_vars = [
        "MONGODB_URI",
        "JWT_SECRET_KEY",
        "MEMORY_PATH",
        "API_PORT"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {'*' * 10} (set)")
        else:
            print(f"  ⚠️ {var}: not set")
    
    # Check directories
    backend_dir = Path(__file__).parent
    dirs = [
        backend_dir / "api",
        backend_dir / "brain",
        backend_dir / "config",
        backend_dir / "Memory"
    ]
    
    print("\n  Directories:")
    for dir_path in dirs:
        if dir_path.exists():
            print(f"  ✅ {dir_path.name}/")
        else:
            print(f"  ❌ {dir_path.name}/ (missing)")

async def main():
    """Run all tests"""
    print("\n🧪 AURAQUANT BACKEND TEST SUITE")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directory: {Path.cwd()}")
    print("\n")
    
    # Test environment
    test_environment()
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test Quantum Brain
        brain_ok = await test_quantum_brain()
        
        # Test API
        api_ok = await test_api_endpoints()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        if imports_ok and brain_ok and api_ok:
            print("✅ ALL TESTS PASSED!")
            print("\n🚀 Ready to start the API server:")
            print("   python api/main.py")
        else:
            print("❌ Some tests failed. Check the output above.")
    else:
        print("\n❌ Import tests failed. Fix imports before continuing.")

if __name__ == "__main__":
    # Run async tests
    asyncio.run(main())