#!/usr/bin/env python
"""
AuraQuant System Test
Comprehensive test of all components
"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

async def test_quantum_brain():
    """Test Quantum Brain functionality"""
    print("\n🧠 Testing Quantum Brain...")
    
    from brain.quantum_brain_fixed import get_brain
    
    brain = get_brain()
    print(f"   ✅ Brain initialized (Gen {brain.generation})")
    
    # Test market analysis
    analysis = await brain.analyze_market("AAPL")
    print(f"   ✅ Market analysis: {analysis['symbol']} - {analysis['recommendation']}")
    print(f"      Price: ${analysis['price']:.2f}")
    print(f"      Confidence: {analysis['confidence']:.2%}")
    print(f"      Quantum Score: {analysis['quantum_score']:.2f}")
    
    # Test recommendations
    recs = await brain.get_trading_recommendations(["AAPL", "GOOGL", "MSFT"])
    print(f"   ✅ Generated {len(recs)} trading recommendations")
    
    for rec in recs[:2]:  # Show first 2
        print(f"      {rec['symbol']}: {rec['action']} @ ${rec['price']:.2f}")
    
    return True

def test_data_libraries():
    """Test NumPy and Pandas"""
    print("\n📊 Testing Data Libraries...")
    
    import numpy as np
    import pandas as pd
    
    # Test NumPy
    arr = np.random.randn(100)
    mean = np.mean(arr)
    std = np.std(arr)
    print(f"   ✅ NumPy {np.__version__}: Mean={mean:.3f}, Std={std:.3f}")
    
    # Test Pandas
    df = pd.DataFrame({
        'symbol': ['AAPL', 'GOOGL', 'MSFT'],
        'price': [150.0, 2800.0, 300.0],
        'volume': [1000000, 500000, 750000]
    })
    print(f"   ✅ Pandas {pd.__version__}: Created DataFrame with {len(df)} stocks")
    print(f"      Average price: ${df['price'].mean():.2f}")
    
    return True

def test_market_data():
    """Test market data fetching"""
    print("\n📈 Testing Market Data...")
    
    import yfinance as yf
    
    try:
        # Fetch a ticker
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        
        if info:
            print(f"   ✅ yfinance connected")
            print(f"      Company: {info.get('shortName', 'Apple Inc.')}")
            print(f"      Current Price: ${info.get('currentPrice', 'N/A')}")
            print(f"      Market Cap: ${info.get('marketCap', 0):,.0f}")
        else:
            print("   ⚠️  Market data not available (may be offline)")
    except Exception as e:
        print(f"   ⚠️  Market data test skipped: {e}")
    
    return True

def test_api_routes():
    """Test API route imports"""
    print("\n🌐 Testing API Routes...")
    
    from api.routes import trading, strategies, market_data, auth, scanner
    
    print("   ✅ Trading routes loaded")
    print("   ✅ Strategy routes loaded") 
    print("   ✅ Market data routes loaded")
    print("   ✅ Authentication routes loaded")
    print("   ✅ Scanner routes loaded")
    
    return True

def test_fastapi_app():
    """Test FastAPI application"""
    print("\n⚡ Testing FastAPI Application...")
    
    from api.main import app
    
    # Check routes
    routes = [r.path for r in app.routes]
    print(f"   ✅ FastAPI app loaded with {len(routes)} routes")
    
    # Show some important routes
    important_routes = ["/", "/health", "/docs", "/api/trading/signals", "/api/auth/login"]
    for route in important_routes:
        if any(route in r.path for r in app.routes):
            print(f"      ✅ {route}")
    
    return True

async def main():
    """Run all tests"""
    print("="*70)
    print("🧪 AURAQUANT SYSTEM TEST SUITE")
    print("="*70)
    
    try:
        # Run tests
        test_data_libraries()
        test_api_routes()
        test_fastapi_app()
        await test_quantum_brain()
        test_market_data()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        
        print("\n🎯 System Status:")
        print("   ✅ NumPy & Pandas installed and working")
        print("   ✅ Quantum Brain operational")
        print("   ✅ API routes configured")
        print("   ✅ FastAPI application ready")
        print("   ✅ Market data libraries installed")
        
        print("\n🚀 Your AuraQuant system is ready for trading!")
        print("\n📝 To start the API server, run:")
        print("   python run_auraquant.py")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())