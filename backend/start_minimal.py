#!/usr/bin/env python
"""
AuraQuant Minimal Server - Profile and Journal APIs
"""

import os
import sys
import uvicorn
from pathlib import Path

# Set UTF-8 encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

def main():
    """Launch AuraQuant Minimal API Server"""
    
    print("\n" + "="*70)
    print("AURAQUANT API SERVER")
    print("Profile and Journal Management System")
    print("="*70)
    
    # Configuration
    from dotenv import load_dotenv
    load_dotenv()
    
    port = int(os.getenv("API_PORT", 8000))
    
    print(f"\nConfiguration:")
    print(f"  Port: {port}")
    print(f"  Database: MongoDB Atlas")
    
    print(f"\nAPI Endpoints:")
    print(f"  Documentation: http://localhost:{port}/docs")
    print(f"  Health Check:  http://localhost:{port}/health")
    
    print(f"\nFrontend Pages:")
    print(f"  Profile: file:///D:/New%20AuraQuant/New_Synthetic_System_AuraQuant_Backup_2025/frontend/pages/profile.html")
    print(f"  Journal: file:///D:/New%20AuraQuant/New_Synthetic_System_AuraQuant_Backup_2025/frontend/pages/journal.html")
    
    print("\n" + "="*70)
    print("STARTING SERVER...")
    print("="*70 + "\n")
    
    try:
        # Start the API server
        uvicorn.run(
            "api.main_minimal:app",
            host="0.0.0.0",
            port=port,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()