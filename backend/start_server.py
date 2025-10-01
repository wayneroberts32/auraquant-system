#!/usr/bin/env python
"""
AuraQuant Trading System - Simple Server Launcher
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

def main():
    """Launch AuraQuant Trading System"""
    
    print("\n" + "="*70)
    print("AURAQUANT QUANTUM BRAIN TRADING SYSTEM")
    print("Advanced AI-Powered Trading Platform")
    print("Version 2.0 - Python Backend")
    print("="*70)
    
    # Configuration
    from dotenv import load_dotenv
    load_dotenv()
    
    port = int(os.getenv("API_PORT", 8000))
    
    print(f"\nConfiguration:")
    print(f"  Port: {port}")
    print(f"  Admin: wayneroberts32@outlook.com.au")
    
    print(f"\nAccess Points:")
    print(f"  API Documentation: http://localhost:{port}/docs")
    print(f"  Alternative Docs:  http://localhost:{port}/redoc")
    print(f"  Health Check:      http://localhost:{port}/health")
    print(f"  Profile Page:      file:///D:/New AuraQuant/New_Synthetic_System_AuraQuant_Backup_2025/frontend/pages/profile.html")
    print(f"  Journal Page:      file:///D:/New AuraQuant/New_Synthetic_System_AuraQuant_Backup_2025/frontend/pages/journal.html")
    
    print("\n" + "="*70)
    print("STARTING SERVER...")
    print("="*70)
    print("\nPress CTRL+C to stop the server\n")
    
    try:
        # Start the API server
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=port,
            reload=False,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n\nShutting down AuraQuant...")
        print("Server stopped successfully")
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nTROUBLESHOOTING:")
        print(f"1. Check if port {port} is already in use")
        print("2. Verify all dependencies are installed")
        print("3. Check Windows Firewall settings")

if __name__ == "__main__":
    main()