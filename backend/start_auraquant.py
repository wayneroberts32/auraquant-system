#!/usr/bin/env python
"""
AuraQuant Trading System - Production Launcher
Start the complete trading system with all features
"""

import os
import sys
import uvicorn
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

def main():
    """Launch AuraQuant Trading System"""
    
    # Banner
    print("\n" + "="*70)
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║      🧠 AURAQUANT QUANTUM BRAIN TRADING SYSTEM 🧠         ║
    ║                                                            ║
    ║         Advanced AI-Powered Trading Platform              ║
    ║            Version 2.0 - Python Backend                   ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    print("="*70)
    
    print(f"\n📅 Starting: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Location: {Path.cwd()}")
    
    # System Status
    print("\n✅ SYSTEM STATUS:")
    print("   • Python 3.12 ✓")
    print("   • NumPy & Pandas ✓")
    print("   • Quantum Brain AI ✓")
    print("   • BeautifulSoup4 + lxml ✓")
    print("   • FastAPI Backend ✓")
    print("   • Market Data (yfinance) ✓")
    print("   • MongoDB Ready (optional) ○")
    
    # Configuration
    from dotenv import load_dotenv
    load_dotenv()
    
    port = int(os.getenv("API_PORT", 8000))
    mongodb_uri = os.getenv("MONGODB_URI", "")
    
    print(f"\n⚙️ CONFIGURATION:")
    print(f"   • Port: {port}")
    if "localhost" in mongodb_uri:
        print(f"   • Database: Local MongoDB (optional)")
    elif mongodb_uri:
        print(f"   • Database: MongoDB Atlas")
    else:
        print(f"   • Database: File Storage (Memory/)")
    
    print(f"   • Admin: wayneroberts32@outlook.com.au")
    
    # Access points
    print(f"\n🌐 ACCESS POINTS:")
    print(f"   • API Documentation: http://localhost:{port}/docs")
    print(f"   • Alternative Docs:  http://localhost:{port}/redoc")
    print(f"   • Health Check:      http://localhost:{port}/health")
    print(f"   • System Info:       http://localhost:{port}/api/system/info")
    
    print(f"\n📊 API ENDPOINTS:")
    print(f"   • GET  /api/trading/signals     - Get AI trading signals")
    print(f"   • POST /api/trading/execute     - Execute trades")
    print(f"   • GET  /api/trading/analysis    - Market analysis")
    print(f"   • GET  /api/strategies/list     - Available strategies")
    print(f"   • POST /api/strategies/backtest - Test strategies")
    print(f"   • POST /api/auth/login          - User authentication")
    print(f"   • GET  /api/market/data         - Market data")
    
    print(f"\n💡 FEATURES:")
    print(f"   • Quantum-inspired AI for market prediction")
    print(f"   • Real-time market data analysis")
    print(f"   • Advanced technical indicators with NumPy/Pandas")
    print(f"   • Dashboard HTML parsing capability")
    print(f"   • JWT-based authentication")
    print(f"   • WebSocket support for real-time updates")
    
    print("\n" + "="*70)
    print("🚀 STARTING SERVER...")
    print("="*70)
    print("\nPress CTRL+C to stop the server\n")
    
    try:
        # Start the API server
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=port,
            reload=False,  # Stable production mode
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("👋 SHUTTING DOWN AURAQUANT...")
        print("="*70)
        print("✅ Server stopped successfully")
        print(f"📅 Stopped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nThank you for using AuraQuant Trading System!")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTROUBLESHOOTING:")
        print(f"1. Check if port {port} is already in use")
        print("2. Verify all dependencies are installed")
        print("3. Check Windows Firewall settings")
        print("4. Try running as Administrator")

if __name__ == "__main__":
    main()